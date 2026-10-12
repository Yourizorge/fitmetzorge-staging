"""Disposable PG17 guard tests. No credentials or hosted connection route."""
import contextlib,hashlib,json,os,pathlib,subprocess,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'fingerprint_v1'))
from local_cluster import Cluster
sys.path.insert(0,str(HERE))
# fingerprint_v1 also has guard.py. Load this exact local candidate explicitly.
import importlib.util
spec=importlib.util.spec_from_file_location('guard',HERE/'guard.py')
g=importlib.util.module_from_spec(spec);sys.modules['guard']=g;spec.loader.exec_module(g)
from checks import run

def main():
    cluster=Cluster();db=None;result={'status':'NO_GO','hosted_calls':0}
    psql='C:/Program Files/PostgreSQL/18/bin/psql.exe'
    def args(actor):return [psql,'-X','-h','127.0.0.1','-p',str(cluster.port),'-U',actor,'-d','postgres','-qAt','-v','ON_ERROR_STOP=1']
    def sql(q,actor='postgres'):
        if actor in ('anon','authenticated','service_role'):
            q='set role '+actor+';'+q;actor='postgres'
        return subprocess.run(args(actor),input="set lock_timeout='200ms';set statement_timeout='5s';"+q,
            text=True,capture_output=True,timeout=10,creationflags=0x08000000)
    @contextlib.contextmanager
    def hold(q):
        p=subprocess.Popen(args('postgres'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=0x08000000)
        try:
            p.stdin.write(q+"\nselect 'fmz_guard_held';\n");p.stdin.flush()
            while p.stdout.readline().strip()!='fmz_guard_held':
                if p.poll() is not None:raise RuntimeError('hold_failed')
            yield
        finally:
            try:p.communicate('rollback;\n',timeout=5)
            except subprocess.TimeoutExpired:p.kill();p.communicate()
    try:
        db=cluster.start();db.close();db=None
        setup="""create role anon;create role authenticated;create role service_role;
create role supabase_auth_admin login;create schema auth authorization supabase_auth_admin;
create table auth.users(id uuid primary key,email text,is_sso_user boolean not null default false,recovery_token text,last_sign_in_at timestamptz);
alter table auth.users owner to supabase_auth_admin;
create unique index users_email_partial_key on auth.users(email) where is_sso_user=false;
grant usage on schema auth to postgres;grant select,insert,update,delete,trigger on auth.users to postgres;
create role fmz_local_bootstrap superuser login;
"""
        if sql(setup).returncode:raise RuntimeError('local_setup')
        # The immutable initdb bootstrap role itself cannot lose SUPERUSER.
        # A separate local bootstrap connection creates the real test role.
        setup="""alter role postgres rename to fmz_original_bootstrap;
create role postgres login createdb;
alter database postgres owner to postgres;
grant usage on schema auth to postgres;
grant select,insert,update,delete,trigger on auth.users to postgres;"""
        setup+='grant anon,authenticated,service_role to postgres;'
        if sql(setup,'fmz_local_bootstrap').returncode:raise RuntimeError('local_privilege_setup')
        result=run(sql,hold)
        from pq import LocalDB
        spec=importlib.util.spec_from_file_location('guard_native_local_lifecycle',HERE/'lifecycle.py')
        life=importlib.util.module_from_spec(spec);spec.loader.exec_module(life)
        from checks import IDS
        db=LocalDB(cluster.port)
        def native_query(q,cost):
            for command in life.ddl_commands(q):db.query(command,timeout=5)
        def native_read(q):
            db.query('BEGIN TRANSACTION READ ONLY')
            try:
                if db.query("select current_setting('transaction_read_only')")!=[['on']]:raise RuntimeError('native_readonly')
                return db.query(q,timeout=5)
            finally:db.query('ROLLBACK')
        evidence={}
        def native_save(name,value):
            if name in evidence:raise RuntimeError('overwrite')
            evidence[name]=value
        native=life.execute(run=str(uuid.uuid4()),ids=IDS,query=native_query,read=native_read,save=native_save)
        (cluster.path/'native-guard-lifecycle.json').write_text(json.dumps(evidence,indent=2)+'\n')
        if native['status']!='GUARD_LIFECYCLE_PASS' or not native['guard_removed']:raise RuntimeError('native_lifecycle_failed')
        result['native_lifecycle']='PASS'
        result['postgres']='17.6';result['sources']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')}
    except Exception as e:result['reason']=str(e) if isinstance(e,(RuntimeError,ValueError)) else type(e).__name__
    finally:
        if db:db.close()
        cluster.stop()
        (cluster.path/'temporary-guard.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({**result,'evidence':str(cluster.path/'temporary-guard.json')}))
    return 0 if result['status']=='GUARD_DATABASE_PASS' else 2
if __name__=='__main__':sys.exit(main())
