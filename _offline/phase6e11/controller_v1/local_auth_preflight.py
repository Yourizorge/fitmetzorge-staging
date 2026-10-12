"""SQL and fail-closed admission on disposable PG17, with explicit Auth stubs."""
import hashlib,json,sys
import auth_preflight as a
sys.path.insert(0,str(a.m.HERE.parent/'readiness_v1/targeted'))
from test_server_boundary import ServerBoundary as s,uid


def main():
    s.setUpClass();result={'status':'NO_GO','hosted_calls':0,'auth':'local stubs only','checks':0}
    try:
        s.sql("alter table auth.users add column email_confirmed_at timestamptz default now();")
        for name in ('20260924130052_phase6e11_private_transaction_audit.sql',
                     '20260924155822_phase6e11_rpc_bridge.sql','20260928120846_phase6e11_request_binding.sql'):
            s.sql((a.m.ROOT/'supabase/migrations'/name).read_text(encoding='utf-8-sig'))
        s.sql("create schema supabase_migrations;create table supabase_migrations.schema_migrations(version text);"
              "insert into supabase_migrations.schema_migrations select n::text from generate_series(1,43) n;")
        ids={r:uid(i) for i,r in enumerate(('a_member','a_trainer','b_member'),1)}
        query=a.query(ids)
        read=lambda:json.loads(s.sql('begin transaction read only;'+query+';rollback;').stdout.splitlines()[1])
        value=read()
        if value['windows']['live']!=1:raise RuntimeError('active_fixture_not_seen')
        result['checks']+=1
        try:a.validate(value,{'sessions_single_per_user':False})
        except a.m.Stop as e:
            if str(e)!='existing_live_window':raise
        else:raise RuntimeError('active_window_admitted')
        result['checks']+=1
        s.sql("update fmz6e11_private.windows set status='revoked',feature_enabled=false;")
        value=read();a.validate(value,{'sessions_single_per_user':False});result['checks']+=1
        if value['managed_audit_observers'] or value['triggers']:raise RuntimeError('unexpected_auth_observer')
        result['checks']+=1
        result.update(status='LOCAL_AUTH_PREFLIGHT_PG17_PASS',postgres='17.6',
            query_sha256=hashlib.sha256(query.encode()).hexdigest(),
            source_sha256=hashlib.sha256((a.m.HERE/'auth_preflight.py').read_bytes()).hexdigest())
    finally:
        s.tearDownClass();a.m.save(s.cluster.path/'auth-preflight-local.json',result)
    print(json.dumps({**result,'evidence':str(s.cluster.path/'auth-preflight-local.json')}))


if __name__=='__main__':main()
