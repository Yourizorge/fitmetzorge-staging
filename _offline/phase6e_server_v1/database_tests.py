"""Shared actual PostgreSQL tests; caller supplies mock-local or real CI Auth."""
import collections,concurrent.futures,json,uuid
from protocol import transaction
from store import Store,Denied,domain,digest,SCHEMA


def run(dsn,auth,tokens,claims,admin,auth_kind,inspect=None):
    results=[];protocol=[]
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
    fixture=str(uuid.uuid4());workspaces={r:str(uuid.uuid4()) for r in ('A','B','control','uiA','uiB','joinedB','historical')}
    for value in claims.values():
        admin.execute('insert into '+SCHEMA+'.subjects values(%s,true,true,now()+interval \'20 minutes\')',[value['sub']])
    def bind(role):
        admin.execute("select set_config('fmz6e.verified_session',%s,false)",[claims[role]['session_id']])
        admin.execute("select set_config('request.jwt.claims',%s,false),set_config('fmz6e.request_id',%s,false)",
            [json.dumps(claims[role]),str(uuid.uuid4())])
    fixtures=[('A','A','a','trainer','owner'),('B','B','b',None,'owner'),('control','B','outsider',None,'outsider')]
    if inspect:fixtures += [('uiA','A','a','trainer','owner'),('uiB','B','b',None,'owner'),('joinedB','B','b',None,'owner'),('historical','B','b',None,'owner')]
    for key,route,member,trainer,owner in fixtures:
        bind(member);state=domain('registration_initial',scenario='no_trainer') if key=='historical' else domain('initial',route=route);raw=json.dumps(state,separators=(',',':'))
        admin.execute('insert into '+SCHEMA+'.workspaces(id,fixture_run,member_id,trainer_id,owner_id,route,expires_at,state_text,state_sha) values(%s,%s,%s,%s,%s,%s,now()+interval \'15 minutes\',%s,%s)',
            [workspaces[key],fixture if key!='control' else str(uuid.uuid4()),claims[member]['sub'],
             claims[trainer]['sub'] if trainer else None,claims[owner]['sub'],route,raw,digest(raw)])
        admin.execute('insert into '+SCHEMA+'.revisions(workspace_id,version,state_text,state_sha) values(%s,0,%s,%s)',
            [workspaces[key],raw,digest(raw)])
    baseline=admin.execute('select state_sha from '+SCHEMA+'.workspaces where id=%s',[workspaces['control']]).fetchone()['state_sha']
    store=Store(dsn,auth,enabled=True,observer=protocol.append,full_day21=True)
    if inspect:inspect(store,{'A':workspaces['uiA'],'B':workspaces['uiB'],'joinedB':workspaces['joinedB'],'historical':workspaces['historical']})
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
        for fault in ('after_head','after_revision','after_receipt','after_outbox'):
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
        restarted=Store(dsn,auth,enabled=True,observer=protocol.append,full_day21=True)
        ok(route+'_new_connection_persistence',restarted.read(workspaces[route],tokens[route.lower()])==read(route))
    denied('cross_member',lambda:read('A','b'))
    denied('trainer_cannot_read_B',lambda:read('B','trainer'))
    denied('outsider_cannot_read_A',lambda:read('A','outsider'))
    ok('owner_read',read('A','owner')['role']=='owner')
    ok('trainer_minimal_view',not ({'recovery','pair','records','health','initialSource'} & set(read('A','trainer')['state'])))
    ok('missing_entitlement_not_invented',read('B')['access']=={'status':'source_missing','read_only':True})
    ok('trainer_no_member_entitlement',read('A','trainer')['access'] is None)
    denied('owner_cannot_approve',lambda:act('A','approve',role='owner'))
    default=Store(dsn,auth,enabled=True,observer=protocol.append)
    denied('21_default_off',lambda:default.execute(workspaces['B'],tokens['b'],str(uuid.uuid4()),read('B')['version'],{'action':'record','data':{}}))
    bundle=read('B')['state']['comparisonExample'];act('B','compare_window',{'bundle':bundle})
    ok('comparison_persisted',len(read('B')['state']['comparison']['facts'])==4)
    before=read('B');act('B','compare_window',{'bundle':bundle})
    ok('comparison_deduplicated',read('B')==before)
    bad=json.loads(json.dumps(bundle));bad['rows'].pop()
    denied('incomplete_comparison',lambda:act('B','compare_window',{'bundle':bad}))
    compared=default.read(workspaces['B'],tokens['b'])
    for action in ('build','confirm','apply'):
        current=default.read(workspaces['B'],tokens['b'])
        default.execute(workspaces['B'],tokens['b'],str(uuid.uuid4()),current['version'],{'action':action,'data':{}})
    applied=default.read(workspaces['B'],tokens['b'])
    ok('21_off_apply_expires_comparison',applied['capabilities']['full_day21'] is False
       and applied['state']['active']['version']==compared['state']['active']['version']+1
       and applied['state']['comparison'] is None and applied['state']['facts']==[])
    ok('apply_retains_comparison_history',applied['state']['comparisonHistory']==compared['state']['comparisonHistory'])
    restarted=Store(dsn,auth,enabled=True,observer=protocol.append)
    ok('applied_comparison_expiry_survives_new_connection',restarted.read(workspaces['B'],tokens['b'])==applied)
    denied('old_plan_comparison_cannot_replay',lambda:default.execute(workspaces['B'],tokens['b'],
        str(uuid.uuid4()),applied['version'],{'action':'compare_window','data':{'bundle':bundle}}))
    default.execute(workspaces['B'],tokens['b'],str(uuid.uuid4()),applied['version'],
        {'action':'compare_window','data':{'bundle':applied['state']['comparisonExample']}})
    refreshed=default.read(workspaces['B'],tokens['b'])
    ok('new_plan_comparison_can_be_created',len(refreshed['state']['facts'])==4
       and refreshed['state']['comparison']['revision']==compared['state']['comparison']['revision']+1
       and refreshed['state']['comparisonHistory'][:-1]==compared['state']['comparisonHistory'])
    comparison_history=read('B')['state']['comparisonHistory']
    active=read('B')['state']['active']
    default.execute(workspaces['B'],tokens['b'],str(uuid.uuid4()),read('B')['version'],
        {'action':'edit','data':{'domain':'nutrition_portion','value':{'meal':0,'item':0,'grams':225}}})
    edited=default.read(workspaces['B'],tokens['b'])
    ok('21_off_edit_invalidates_current_facts',edited['capabilities']['full_day21'] is False
       and edited['state']['comparison'] is None and edited['state']['facts']==[])
    ok('comparison_history_retained_after_edit',edited['state']['comparisonHistory']==comparison_history)
    ok('comparison_invalidation_does_not_apply',edited['state']['active']==active
       and edited['state']['review']['member'] is False)
    denied('invalidated_facts_do_not_grant_apply',lambda:default.execute(workspaces['B'],tokens['b'],
        str(uuid.uuid4()),edited['version'],{'action':'apply','data':{}}))
    restarted=Store(dsn,auth,enabled=True,observer=protocol.append)
    ok('invalidated_facts_survive_new_connection',restarted.read(workspaces['B'],tokens['b'])==edited)
    ok('planning_explicit_source',read('B')['planning']['occurrence']['zone']=='UTC' and not read('B')['planning']['background_delivery'])
    out=read('A')['notices'];ok('outbox_durable_history',bool(out) and any(e['status']=='applied' for e in out))
    ok('trainer_no_notice_details',read('A','trainer')['notices']==[])
    act('A','edit',{'domain':'time','value':'20:00'})
    pending=next(e for e in read('A')['notices'] if e['status']=='pending')
    act('A','notice_seen',{'id':pending['id']})
    ok('outbox_seen',next(e for e in read('A')['notices'] if e['id']==pending['id'])['status']=='seen')
    act('A','reject')
    ok('outbox_declined',next(e for e in read('A')['notices'] if e['id']==pending['id'])['status']=='declined')
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
    with transaction(store.connect,protocol.append,'rls_negative') as db:
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
    owned=[workspaces[k] for k,_,_,_,_ in fixtures if k!='control']
    before_cleanup={w:admin.execute('select state_sha from '+SCHEMA+'.workspaces where id=%s',[w]).fetchone()['state_sha'] for w in owned}
    bind('trainer');delete_request=str(uuid.uuid4())
    admin.execute("select set_config('fmz6e.request_id',%s,false)",[delete_request])
    counts={}
    with admin.transaction():
        for table in ('outbox','requests','revisions','workspaces'):
            column='id' if table=='workspaces' else 'workspace_id'
            deleted=admin.execute('delete from '+SCHEMA+'.'+table+' where '+column+'=any(%s::uuid[]) returning '+column,
                [owned]).fetchall()
            counts[SCHEMA+'.'+table]=len(deleted)
    observed=admin.execute('select table_name,count(*) n,count(distinct xid) tx from '+SCHEMA+".audit where request_id=%s and operation='DELETE' group by table_name",[delete_request]).fetchall()
    ok('delete_audit_exact',{x['table_name']:x['n'] for x in observed}==counts and all(x['tx']==1 for x in observed))
    ok('own_workspaces_absent',admin.execute('select count(*) n from '+SCHEMA+'.workspaces where id=any(%s::uuid[])',[owned]).fetchone()['n']==0)
    ok('control_preserved',admin.execute('select state_sha from '+SCHEMA+'.workspaces where id=%s',[workspaces['control']]).fetchone()['state_sha']==baseline)
    groups=collections.defaultdict(list)
    for event in protocol:
        if event['phase']=='completed':groups[event['call_id']].append(event)
    costs=collections.defaultdict(list)
    for events in groups.values():
        costs[events[0]['operation']].append(len(events))
        if events[-1]['template_sha256'] not in (digest('COMMIT'),digest('ROLLBACK')) or not events[-1]['confirmed']:
            raise AssertionError('protocol_terminal_unconfirmed')
    accounting={'commands':sum(map(len,groups.values())),'transactions':len(groups),
        'operations':{k:{'calls':len(v),'minimum':min(v),'maximum':max(v),'commands':sum(v)} for k,v in costs.items()},
        'scope':'native Store protocol including BEGIN/COMMIT/ROLLBACK; separate fixture/admin and managed Auth accounting required',
        'template_hashes':sorted({e['template_sha256'] for e in protocol}),
        'row_values_logged':False}
    return {'status':'LOCAL_DATABASE_PASS','tests':len(results),'cases':results,'auth':auth_kind,'protocol':accounting,
            'before_cleanup':before_cleanup,'deletes':counts,'protected_control_sha':baseline,
            'hosted_requests':0,'scope':'synthetic local candidate; not hosted or owner acceptance'}
