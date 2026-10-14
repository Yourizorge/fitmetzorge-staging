"""Shared actual PostgreSQL tests; caller supplies mock-local or real CI Auth."""
import concurrent.futures,json,uuid
from store import Store,Denied,domain,digest,SCHEMA


def run(dsn,auth,tokens,claims,admin,auth_kind,inspect=None):
    results=[]
    def ok(name,condition):
        if not condition:raise AssertionError(name)
        results.append(name)
    def denied(name,call):
        try:call()
        except (Denied,Exception) as e:
            # Expected denials must be an explicit contract or SQL permission failure.
            if not isinstance(e,Denied) and getattr(e,'sqlstate',None) not in ('42501','23505'):raise
            results.append(name);return
        raise AssertionError(name)
    fixture=str(uuid.uuid4());workspaces={r:str(uuid.uuid4()) for r in ('A','B','control')}
    for value in claims.values():
        admin.execute('insert into '+SCHEMA+'.subjects values(%s,true,true,now()+interval \'20 minutes\')',[value['sub']])
    def bind(role):
        admin.execute("select set_config('fmz6e.verified_session',%s,false)",[claims[role]['session_id']])
        admin.execute("select set_config('request.jwt.claims',%s,false),set_config('fmz6e.request_id',%s,false)",
            [json.dumps(claims[role]),str(uuid.uuid4())])
    for route,member,trainer,owner in [('A','a','trainer','owner'),('B','b',None,'owner'),('control','outsider',None,'outsider')]:
        bind(member);state=domain('initial',route='A' if route=='A' else 'B');raw=json.dumps(state,separators=(',',':'))
        admin.execute('insert into '+SCHEMA+'.workspaces(id,fixture_run,member_id,trainer_id,owner_id,route,expires_at,state_text,state_sha) values(%s,%s,%s,%s,%s,%s,now()+interval \'15 minutes\',%s,%s)',
            [workspaces[route],fixture if route!='control' else str(uuid.uuid4()),claims[member]['sub'],
             claims[trainer]['sub'] if trainer else None,claims[owner]['sub'],'A' if route=='A' else 'B',raw,digest(raw)])
        admin.execute('insert into '+SCHEMA+'.revisions(workspace_id,version,state_text,state_sha) values(%s,0,%s,%s)',
            [workspaces[route],raw,digest(raw)])
    baseline=admin.execute('select state_sha from '+SCHEMA+'.workspaces where id=%s',[workspaces['control']]).fetchone()['state_sha']
    store=Store(dsn,auth,enabled=True)
    if inspect:inspect(store,workspaces)
    def read(route,role=None):return store.read(workspaces[route],tokens[role or route.lower()])
    def act(route,action,data=None,role=None,fault=None,key=None,version=None):
        role=role or route.lower();snapshot=read(route,role)
        return store.execute(workspaces[route],tokens[role],key or str(uuid.uuid4()),
            snapshot['version'] if version is None else version,{'action':action,'data':data or {}},fault)
    for route in ('A','B'):
        before=read(route);row=before['state']['recovery']['rows'][-1]
        act(route,'recovery',{'id':row['id'],'version':row['version'],'value':6})
        denied(route+'_apply_requires_member',lambda:act(route,'apply'))
        act(route,'confirm')
        if route=='A':
            denied('A_requires_trainer',lambda:act(route,'apply'))
            denied('A_member_cannot_approve',lambda:act(route,'approve'))
            act(route,'approve',role='trainer')
        else:denied('B_has_no_trainer_step',lambda:act(route,'approve'))
        for fault in ('after_head','after_revision','after_receipt'):
            snapshot=read(route)
            denied(route+'_'+fault,lambda:act(route,'apply',fault=fault))
            ok(route+'_rollback_'+fault,read(route)==snapshot)
        key=str(uuid.uuid4());version=read(route)['version'];result=act(route,'apply',key=key,version=version)
        replay=act(route,'apply',key=key,version=version)
        ok(route+'_idempotency',replay['idempotent'] and replay['version']==result['version'])
        denied(route+'_changed_replay',lambda:act(route,'reject',key=key,version=version))
        ok(route+'_original_preserved',read(route)['state']['history'][0]==before['state']['history'][0])
        act(route,'edit',{'domain':'time','value':'20:00'});act(route,'confirm')
        if route=='A':act(route,'approve',role='trainer')
        act(route,'apply');act(route,'restore',{'version':2});act(route,'confirm')
        if route=='A':act(route,'approve',role='trainer')
        act(route,'apply')
        ok(route+'_restore_new_version',read(route)['state']['active']['version']==4)
        restarted=Store(dsn,auth,enabled=True)
        ok(route+'_new_connection_persistence',restarted.read(workspaces[route],tokens[route.lower()])==read(route))
    denied('cross_member',lambda:read('A','b'))
    denied('trainer_cannot_read_B',lambda:read('B','trainer'))
    denied('outsider_cannot_read_A',lambda:read('A','outsider'))
    ok('owner_read',read('A','owner')['role']=='owner')
    ok('trainer_minimal_view',not ({'recovery','pair','records','health','initialSource'} & set(read('A','trainer')['state'])))
    denied('owner_cannot_approve',lambda:act('A','approve',role='owner'))
    for table,key,column,value in [('subjects','user_id','enabled',False),
                                   ('subjects','user_id','expires_at','2000-01-01'),
                                   ('workspaces','id','expires_at','2000-01-01')]:
        target=claims['a']['sub'] if table=='subjects' else workspaces['A']
        old=admin.execute('select '+column+' v from '+SCHEMA+'.'+table+' where '+key+'=%s',[target]).fetchone()['v']
        bind('a')
        admin.execute('update '+SCHEMA+'.'+table+' set '+column+'=%s where '+key+'=%s',[value,target])
        denied(table+'_'+column+'_expired_or_revoked',lambda:read('A'))
        # Restore only this exact local fixture; no application restoration claim.
        bind('trainer')
        admin.execute('update '+SCHEMA+'.'+table+' set '+column+'=%s where '+key+'=%s',[old,target])
    old=admin.execute('select not_after from auth.sessions where id=%s',[claims['a']['session_id']]).fetchone()['not_after']
    admin.execute("update auth.sessions set not_after='2000-01-01' where id=%s",[claims['a']['session_id']])
    denied('expired_session',lambda:read('A'))
    admin.execute('update auth.sessions set not_after=%s where id=%s',[old,claims['a']['session_id']])
    state=read('B');row=state['state']['records'][0]
    data={'id':row['id'],'version':row['revision'],'planVersion':row['planVersion'],
          'unit':row['unit'],'source':row['source'],'actual':{'load':0,'reps':0,'rir':0,'rpe':None}}
    def concurrent_write():return act('B','record',data,version=state['version'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(concurrent_write) for _ in range(2)];passes=denials=0
        for f in futures:
            try:f.result();passes+=1
            except Denied as e:
                if str(e)!='version_conflict':raise
                denials+=1
    ok('concurrent_CAS',passes==1 and denials==1)
    ok('null_zero_distinct',read('B')['state']['records'][0]['actual']==data['actual'])
    stale=read('B');row=stale['state']['records'][0]
    act('B','finish_workout',{'workout':row['workout']})
    ok('explicit_completion_persisted',len(read('B')['state']['workoutClosures'])==1)
    act('B','revoke');history=read('B')['state']['history']
    denied('consent_blocks',lambda:act('B','build'))
    ok('consent_keeps_history',read('B')['state']['history']==history)
    # The server role cannot bypass table RLS or mutate immutable versions.
    with store.connect() as db,db.transaction():
        store.bind(db,claims['b'],str(uuid.uuid4()))
        ok('RLS_cross_member_zero',db.execute('select id from '+SCHEMA+'.workspaces where id=%s',[workspaces['A']]).fetchall()==[])
    for role in ('anon','authenticated','service_role'):
        try:
            with admin.transaction():
                admin.execute('set local role '+role)
                admin.execute('select * from '+SCHEMA+'.workspaces')
        except Exception as e:
            if getattr(e,'sqlstate',None)!='42501':raise
            results.append('private_denied_'+role)
        else:raise AssertionError('private_schema_exposed')
    before_cleanup={w:admin.execute('select state_sha from '+SCHEMA+'.workspaces where id=%s',[w]).fetchone()['state_sha']
                    for w in (workspaces['A'],workspaces['B'])}
    bind('trainer');delete_request=str(uuid.uuid4())
    admin.execute("select set_config('fmz6e.request_id',%s,false)",[delete_request])
    counts={}
    with admin.transaction():
        for table in ('requests','revisions','workspaces'):
            column='id' if table=='workspaces' else 'workspace_id'
            deleted=admin.execute('delete from '+SCHEMA+'.'+table+' where '+column+'=any(%s::uuid[]) returning '+column,
                [[workspaces['A'],workspaces['B']]]).fetchall()
            counts[SCHEMA+'.'+table]=len(deleted)
    observed=admin.execute('select table_name,count(*) n,count(distinct xid) tx from '+SCHEMA+".audit where request_id=%s and operation='DELETE' group by table_name",[delete_request]).fetchall()
    ok('delete_audit_exact',{x['table_name']:x['n'] for x in observed}==counts and all(x['tx']==1 for x in observed))
    ok('own_workspaces_absent',admin.execute('select count(*) n from '+SCHEMA+'.workspaces where id=any(%s::uuid[])',[[workspaces['A'],workspaces['B']]]).fetchone()['n']==0)
    ok('control_preserved',admin.execute('select state_sha from '+SCHEMA+'.workspaces where id=%s',[workspaces['control']]).fetchone()['state_sha']==baseline)
    return {'status':'LOCAL_DATABASE_PASS','tests':len(results),'cases':results,'auth':auth_kind,
            'before_cleanup':before_cleanup,'deletes':counts,'protected_control_sha':baseline,
            'hosted_requests':0,'scope':'synthetic local candidate; not hosted or owner acceptance'}
