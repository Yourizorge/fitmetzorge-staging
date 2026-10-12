"""Bounded local row-lock proof, including the explicit partial-index limitation."""
import hashlib,json,os,subprocess,sys
import auth_preflight as a
sys.path.insert(0,str(a.m.HERE.parent/'readiness_v1/targeted'))
from test_server_boundary import ServerBoundary as s,uid,lit
from pq import LocalDB


def main():
    s.setUpClass();db=None;result={'status':'NO_GO','hosted_calls':0,'checks':0,'limitations':[]}
    try:
        s.sql("alter table auth.users add column recovery_token text,add column is_sso_user boolean not null default false;"
              "create unique index users_email_partial_key on auth.users(email) where is_sso_user=false;")
        p=subprocess.run([os.environ['FMZ_NODE'],'--input-type=module','-e',
            "import {LOCK_IDENTITY} from './_offline/phase6e11/controller_v1/auth_guard.mjs';process.stdout.write(LOCK_IDENTITY);"],
            cwd=a.m.ROOT,text=True,capture_output=True,timeout=10,creationflags=0x08000000)
        if p.returncode:raise RuntimeError('guard_source_import')
        sql=p.stdout
        db=LocalDB(s.cluster.port);db.query('BEGIN')
        db.query('prepare identity_guard as '+sql)
        row=db.query('execute identity_guard('+lit(uid(1))+','+lit('zorgeyouri+6e9-a-lid@gmail.com')+')')
        if len(row)!=1 or row[0][0]!=uid(1):raise RuntimeError('identity_lock')
        result['checks']+=1
        if row[0][7]!='f':raise RuntimeError('partial_index_must_not_admit_auth')
        result['checks']+=1
        def other(statement,expect_blocked):
            p=s.sql("set lock_timeout='150ms';"+statement,success=False)
            if expect_blocked:
                if not p.returncode or 'lock timeout' not in p.stderr:raise RuntimeError('expected_lock_not_blocked')
            elif p.returncode:raise RuntimeError('nonkey_update_blocked')
        other('update auth.users set recovery_token='+lit('local-fixture-only')+' where id='+lit(uid(1))+';',False)
        result['checks']+=1
        other('delete from auth.users where id='+lit(uid(1))+';',True);result['checks']+=1
        other('update public.profiles set trainer_id=null where id='+lit(uid(1))+';',True);result['checks']+=1
        other('update auth.users set email='+lit('changed@example.invalid')+' where id='+lit(uid(1))+';',False)
        result['limitations'].append('partial_email_unique_index_does_not_prevent_concurrent_alias_change')
        db.query('ROLLBACK');db.close();db=None
        other('update public.profiles set trainer_id=null where id='+lit(uid(1))+';',False);result['checks']+=1
        result.update(status='LOCAL_DELETE_GUARD_PASS_ALIAS_STABILITY_UNPROVEN',postgres='17.6',
            hosted_auth_admitted=False,query_sha256=hashlib.sha256(sql.encode()).hexdigest(),
            source_sha256=hashlib.sha256((a.m.HERE/'auth_guard.mjs').read_bytes()).hexdigest())
    finally:
        if db:db.close()
        s.tearDownClass();a.m.save(s.cluster.path/'auth-guard-local.json',result)
    print(json.dumps({**result,'evidence':str(s.cluster.path/'auth-guard-local.json')}))


if __name__=='__main__':main()
