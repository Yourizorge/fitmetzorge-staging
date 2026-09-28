"""Negative transaction tests; only a disposable synthetic PG17 cluster."""
import copy,json,time,uuid
from request_local import lit,js,uid,save,Stop,A
R='fmz6e11_request_private'
def run(w):
    tests=[]
    def count(table):
        return int(w.sql('select count(*) from '+table+';').stdout.strip())
    def state():
        return {'business':w.snapshot(),'private':{t:count(t) for t in
          [R+'.receipts',A+'.runs',A+'.actions',A+'.bindings',A+'.writes']}}
    def record(name,ok):
        tests.append({'name':name,'pass':bool(ok)})
        if not ok:raise Stop('negative:'+name)
    def claims():
        return {'sub':uid(1),'session_id':uid(101),'role':'authenticated','aud':'authenticated',
          'iss':'https://mokxyyullfhkfalopbzd.supabase.co/auth/v1','exp':int(time.time())+3600}
    def context(c):
        return ("select set_config('request.jwt.claims',"+js(c)+"::text,true);select set_config('request.headers',"+
          js({'x-fmz6e11-proof':'synthetic-only-local-proof'})+"::text,true);")
    def denied(name,q=None,c=None,sql_before='',sql_after='',reason=None):
        before=state();q=q or w.body('propose');rid=str(uuid.uuid4())
        p=w.sql('begin;'+context(c or claims())+sql_before+'select '+R+'.call('+js(q)+','+lit(rid)+');'+sql_after+'commit;',success=False)
        record(name,p.returncode!=0 and state()==before and (reason is None or reason in p.stderr))
    for role in ('anon','authenticated','service_role'):
        for target in ('select * from '+R+'.receipts','select '+R+".call('{}',gen_random_uuid())"):
            p=w.sql('begin;set local role '+role+';'+target+';rollback;',success=False)
            record('ACL '+role+' '+target.split()[1],p.returncode!=0 and 'permission denied' in p.stderr)
    for name,change in [('issuer',{'iss':'https://invalid.example'}),('audience',{'aud':'anon'}),
      ('expired',{'exp':0}),('privileged role',{'role':'service_role'}),('unknown session',{'session_id':uid(900)}),
      ('wrong actor session',{'sub':uid(2)}),('ordinary identity',{'sub':uid(999),'session_id':uid(999)}),
      ('editable metadata',{'user_metadata':{'role':'trainer'}})]:
        denied(name,c={**claims(),**change})
    denied('cross workspace',q=w.body('restore',{'plan_version':1},x=w.b))
    denied('unknown workspace',q=w.body('restore',{'plan_version':1},x=uid(999)))
    denied('missing audit trigger',sql_before='alter table fmz6e11_private.windows disable trigger fmz6e11_tx_observer;',
      reason='audit_trigger_coverage')
    denied('before mutation interrupted',sql_before="do $$ begin raise exception 'injected_before';end $$;",reason='injected_before')
    denied('after mutation interrupted',sql_after="do $$ begin raise exception 'injected_after';end $$;",reason='injected_after')
    denied('extra forbidden write',sql_after="update public.profiles set updated_at=now() where id="+lit(uid(1))+';',reason='audit_binding_inactive')
    row=w.rows('select * from '+R+'.receipts order by created_at limit 1')[0]
    q=w.body('restore',{'plan_version':1})
    before=state()
    p=w.sql('begin;'+context(claims())+'select '+R+'.call('+js(q)+','+lit(row['request_id'])+');commit;',success=False)
    record('duplicate request different hash',p.returncode!=0 and 'request_id_conflict' in p.stderr and state()==before)
    managed=w.rows("select table_name from "+A+".relations where table_name ~ '^(auth|storage|realtime)\\.'")
    record('no managed observers',managed==[])
    funcs=w.rows("select p.proname,p.prosecdef,p.proconfig from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname="+lit(R))
    record('invoker fixed paths',len(funcs)==5 and all(not f['prosecdef'] and f['proconfig']==['search_path=pg_catalog, pg_temp'] for f in funcs))
    # A committed mutation without an independently committed seal blocks the next.
    q=w.body('propose');rid=str(uuid.uuid4())
    w.sql('begin;'+context(claims())+'select '+R+'.call('+js(q)+','+lit(rid)+');commit;')
    pending=w.rows('select state,selected_branch from '+R+'.receipts where request_id='+lit(rid))[0]
    record('committed action awaiting seal',pending=={'state':'confirmed','selected_branch':'committed'})
    denied('missing after seal blocks next',reason='request_previous_pair_incomplete')
    w.sql('select '+R+'.seal('+lit(rid)+');')
    record('separate seal resumes',w.rows('select state from '+R+'.receipts where request_id='+lit(rid))[0]['state']=='pair_validated')
    # Same HTTP request is replayed without adding an intent, mutation or audit row.
    before=state()
    replay=w.sql('begin;'+context(claims())+'select '+R+'.call('+js(q)+','+lit(rid)+');commit;').stdout
    record('exact request replay no second apply',state()==before and '"replay": true' in replay)
    # Wrong same-key payload cannot reuse an existing approval/application.
    altered={**q,'data':{'plan_version':999}}
    rid2=str(uuid.uuid4())
    answer=w.sql('begin;'+context(claims())+'select '+R+'.call('+js(altered)+','+lit(rid2)+');commit;').stdout
    result=json.loads([line for line in answer.splitlines() if line.startswith('{')][-1])
    save(w.folder/'idempotency-negative.json',result)
    record('idempotency key payload conflict', result.get('error')=='synthetic_idempotency_conflict')
    w.sql('select '+R+'.seal('+lit(rid2)+');')
    # Cleanup is server-only and requires the original operator and a revoked window.
    denied('cleanup active window denied',q=w.body('cleanup_batch',{'table':'events'}),reason='request_cleanup_guard')
    revoke=w.body('revoke');rid3=str(uuid.uuid4())
    w.invoke(revoke,'trainer',rid3)
    row=w.rows('select * from '+R+'.receipts where request_id='+lit(rid3))[0]
    writes=w.rows('select operation,table_name from '+A+'.writes where action_id='+lit(row['action_id']))
    record('revoke exact four writes',len(writes)==4 and sum(z['operation']=='UPDATE' for z in writes)==2)
    denied('revoked window blocks member',reason='synthetic_window_inactive')
    q=w.body('cleanup_batch',{'table':'events'});rid4=str(uuid.uuid4())
    old_events=count('fmz6e11_private.events');protected={k:v for k,v in w.snapshot().items() if k.startswith(('auth.','public.'))}
    value=w.invoke(q,'trainer',rid4)
    row=w.rows('select * from '+R+'.receipts where request_id='+lit(rid4))[0]
    writes=w.rows('select * from '+A+'.writes where action_id='+lit(row['action_id']))
    record('cleanup deletes retained',value['deleted']>0 and len(writes)==value['deleted']
      and count('fmz6e11_private.events')==old_events-value['deleted']
      and all(z['operation']=='DELETE' and z['old_key_sha'] and z['new_key_sha'] is None
      and str(z['xid'])==str(row['xid']) for z in writes))
    record('cleanup protected rows unchanged',protected=={k:v for k,v in w.snapshot().items() if k.startswith(('auth.','public.'))})
    save(w.folder/'request-security.json',{'tests':tests,'count':len(tests),'status':'LOCAL_PASS','hosted_auth':False})
    return tests

def main():
    from request_local import Requests,ServerBoundary,ROOT
    folder=ROOT/'supabase/.temp'/('phase6e11-request-security-'+uuid.uuid4().hex);folder.mkdir()
    try:
        ServerBoundary.setUpClass();w=Requests(folder)
        times=w.rows('select starts_at,ends_at from fmz6e11_private.windows where id='+lit(w.w))[0]
        template=ServerBoundary.api('trainer',{'op':'read','window':w.w,'workspace':w.x})['source_template']
        q=w.body('source_append',{'body':template,'valid_from':times['starts_at'],'valid_until':times['ends_at']})
        w.perform('source v1','trainer',q,[('source_versions','INSERT',[w.x,1]),('source_heads','INSERT',[w.x])])
        tests=run(w)
        print(json.dumps({'status':'LOCAL_SECURITY_PASS','tests':len(tests),'directory':str(folder)}))
        return 0
    except BaseException as e:
        save(folder/'HALT.json',{'type':type(e).__name__,'reason':str(e)[:600]})
        print(json.dumps({'status':'LOCAL_FAIL','reason':str(e),'directory':str(folder)}))
        return 1
    finally:
        if getattr(ServerBoundary,'cluster',None):ServerBoundary.tearDownClass()
if __name__=='__main__':
    import sys
    sys.exit(main())
