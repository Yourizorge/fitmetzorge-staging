"""Disposable local PG17 only; preserve files and stop the owned process."""
import contextlib,datetime,importlib.util,json,os,pathlib,subprocess,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'fingerprint_v1'))
from local_cluster import Cluster
sys.path.insert(0,str(HERE))
import audit
spec=importlib.util.spec_from_file_location('auth_metadata_checks',HERE/'checks.py')
checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
IDS={r:'68000000-0000-4000-8000-'+str(i).zfill(12) for i,r in enumerate(audit.g.ROLES,1)}

def main():
    cluster=Cluster();result={'status':'NO_GO','hosted_calls':0}
    psql='C:/Program Files/PostgreSQL/18/bin/psql.exe'
    def args(role):return [psql,'-X','-h','127.0.0.1','-p',str(cluster.port),'-U',role,'-d','postgres','-qAt','-v','ON_ERROR_STOP=1']
    def sql(q,role='postgres'):
        if role in ('anon','authenticated','service_role'):q='set role '+role+';'+q;role='postgres'
        return subprocess.run(args(role),input="set statement_timeout='5s';set lock_timeout='200ms';"+q,capture_output=True,text=True,timeout=10,creationflags=0x08000000)
    @contextlib.contextmanager
    def hold(q):
        p=subprocess.Popen(args('postgres'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=0x08000000)
        try:
            p.stdin.write(q+"select 'held';\n");p.stdin.flush()
            while p.stdout.readline().strip()!='held':
                if p.poll() is not None:raise RuntimeError('hold_failed')
            yield
        finally:p.communicate('rollback;\n',timeout=5)
    try:
        db=cluster.start();db.close()
        ddl="""create role anon;create role authenticated;create role service_role;create role supabase_auth_admin login;
create schema auth authorization supabase_auth_admin;
create table auth.users(id uuid primary key,email text,is_sso_user boolean default false,last_sign_in_at timestamptz);
create table auth.sessions(id uuid primary key,user_id uuid references auth.users,created_at timestamptz,updated_at timestamptz);
create table auth.mfa_amr_claims(id uuid primary key,session_id uuid references auth.sessions on delete cascade,authentication_method text,created_at timestamptz,updated_at timestamptz);
create table auth.identities(id uuid primary key,user_id uuid references auth.users);
create table auth.refresh_tokens(id bigint primary key,user_id text,session_id uuid references auth.sessions on delete cascade);
create table auth.one_time_tokens(id uuid primary key,user_id uuid references auth.users);
create table auth.audit_log_entries(id uuid primary key,payload jsonb);
create role fmz_local_bootstrap superuser login;
"""
        for t in audit.TABLES:ddl+='alter table auth.'+t+' owner to supabase_auth_admin;'
        if sql(ddl).returncode:raise RuntimeError('local_setup')
        ddl='alter role postgres rename to fmz_original_bootstrap;create role postgres login createdb;alter database postgres owner to postgres;grant anon,authenticated,service_role to postgres;grant usage on schema auth to postgres;grant select,insert,update,delete,trigger on all tables in schema auth to postgres;'
        if sql(ddl,'fmz_local_bootstrap').returncode:raise RuntimeError('local_roles')
        for role,uid in IDS.items():
            if sql('insert into auth.users(id,email) values('+audit.g.literal(uid)+','+audit.g.literal(audit.g.ALIASES[role])+')').returncode:raise RuntimeError('local_seed')
        sql("insert into auth.users(id,email) values('68000000-0000-4000-8000-000000000004','outside@example.invalid')")
        result=checks.run(sql,hold,IDS)
        from pq import LocalDB
        from failure import safe_reason
        import probe
        spec=importlib.util.spec_from_file_location('metadata_native_transport',HERE.parent/'textfree_v1/native.py')
        native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
        db=LocalDB(cluster.port)
        try:
            db.query('BEGIN')
            try:db.query('explain(analyze,verbose,buffers,format json) select 1')
            except Exception as error:
                if safe_reason(error)!='terminal_row_count':raise RuntimeError('native_original_not_reproduced')
                result['original_native_explain']='terminal_row_count'
            else:raise RuntimeError('original_native_unexpected_pass')
        finally:db.close()
        run_id=str(uuid.uuid4());session=str(uuid.uuid4());action=str(uuid.uuid4())
        deadline=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=120)).isoformat()
        def success(text):
            p=sql(text)
            if p.returncode:raise RuntimeError('native_probe_setup')
            return p.stdout.strip()
        success(audit.install(run_id,IDS,deadline));receipt=audit.validate(json.loads(success(audit.inspect(run_id,IDS))),run_id,IDS,deadline)
        db=LocalDB(cluster.port)
        try:
            before=success(probe.snapshot(IDS,session));success(audit.arm(run_id,IDS,action,'a_member','verify'))
            db.query('BEGIN');reader=native.Native(db);plans=[]
            for text in probe.sql_sequence(session,IDS['a_member']):
                plans.append(probe.plan_summary(reader.query('explain (analyze,verbose,buffers,format json) '+text)[0][0]))
            db.query('COMMIT')
            observed=json.loads(success(audit.events(run_id,IDS,action)))
            result['native_probe']=probe.validate(observed,action,session,IDS['a_member'])
            if success(probe.snapshot(IDS,session))!=before:raise RuntimeError('native_probe_drift')
            result['native_probe'].update(status='PASS',plans=plans,data_equal=True)
        finally:
            db.close();success(audit.remove(run_id,IDS,receipt))
    except Exception as e:result['error']=str(e) if isinstance(e,(ValueError,RuntimeError)) else type(e).__name__
    finally:
        cluster.stop();(cluster.path/'metadata-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({**result,'evidence':str(cluster.path/'metadata-audit.json')}))
    return 0 if result['status']=='AUTH_METADATA_DATABASE_PASS' else 2
if __name__=='__main__':sys.exit(main())
