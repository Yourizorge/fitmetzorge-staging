"""Actual minimal-slice PG/Auth proof, before the optional outbox migration."""
import concurrent.futures,collections,json,uuid
from store import domain,digest,SCHEMA,Denied
from registration_store import RegistrationStore

def run(ctx):
    admin,claims,tokens=ctx['admin'],ctx['claims'],ctx['tokens'];events=[];checks=[]
    def ok(name,value):
        if not value:raise AssertionError(name)
        checks.append(name)
    def deny(name,fn):
        try:fn()
        except Denied:checks.append(name);return
        raise AssertionError(name)
    subjects=[claims[k]['sub'] for k in ('a','trainer','b')]
    for actor in subjects:admin.execute('insert into '+SCHEMA+'.subjects values(%s,true,true,now()+interval \'15 minutes\')',[actor])
    def bind():
        admin.execute("select set_config('fmz6e.verified_session',%s,false),set_config('request.jwt.claims',%s,false),set_config('fmz6e.request_id',%s,false)",
            [claims['a']['session_id'],json.dumps(claims['a']),str(uuid.uuid4())])
    bind();workspace=str(uuid.uuid4());state=domain('registration_initial');raw=json.dumps(state,separators=(',',':'))
    admin.execute('insert into '+SCHEMA+'.workspaces(id,fixture_run,member_id,trainer_id,owner_id,route,expires_at,state_text,state_sha) values(%s,%s,%s,%s,%s,\'A\',now()+interval \'10 minutes\',%s,%s)',
        [workspace,str(uuid.uuid4()),subjects[0],subjects[1],subjects[0],raw,digest(raw)])
    admin.execute('insert into '+SCHEMA+'.revisions(workspace_id,version,state_text,state_sha) values(%s,0,%s,%s)',[workspace,raw,digest(raw)])
    bindings={workspace:subjects[0]}
    store=RegistrationStore(ctx['dsn'],ctx['auth'],bindings,enabled=True,observer=events.append)
    read=lambda:store.read(workspace,tokens['a'])
    def act(key=None,expected=None,input=None,fault=None,action='register12'):
        current=read()
        return store.execute(workspace,tokens['a'],key or str(uuid.uuid4()),current['version'] if expected is None else expected,
            {'action':action,'data':{'input':input or current['state']['draft']} if action=='register12' else {}},fault)
    deny('default_off',lambda:RegistrationStore(ctx['dsn'],ctx['auth'],bindings))
    for role in ('b','trainer','owner','outsider'):deny('exact_member_only_'+role,lambda:store.read(workspace,tokens[role]))
    initial=read();request=str(uuid.uuid4());draft=initial['state']['draft'];draft['sets'][0]['rir']=0;draft['sets'][0]['rpe']=None
    first=act(request,0,draft)
    ok('receipt_replay',act(request,0,draft)['idempotent'])
    changed=json.loads(json.dumps(draft));changed['sets'][0]['reps']=3
    deny('changed_payload_replay',lambda:act(request,0,changed))
    deny('stale_version',lambda:act(expected=0))
    for fault in ('after_head','after_revision','after_receipt'):
        before=read();deny(fault,lambda:act(fault=fault));ok('rollback_'+fault,read()==before)
    before=read();candidate=before['state']['draft']
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(act,expected=before['version'],input=candidate) for _ in range(2)];passed=0;denied=0
        for f in futures:
            try:f.result();passed+=1
            except Denied:denied+=1
    ok('concurrent_CAS',passed==1 and denied==1)
    restarted=RegistrationStore(ctx['dsn'],ctx['auth'],bindings,enabled=True,observer=events.append)
    ok('restart_history',restarted.read(workspace,tokens['a'])==read())
    token=ctx['auth'].call('/token?grant_type=password',data=ctx['accounts']['a'])['access_token']
    ok('relogin_history',store.read(workspace,token)==read())
    state=read()['state'];ok('original_snapshot_retained',state['snapshot']==initial['state']['snapshot'])
    ok('independent_null_zero',state['registrations'][0]['sets'][0]['rir']==0 and state['registrations'][0]['sets'][0]['rpe'] is None)
    ok('three_exact_bound_writes',len(first['writes'])==3 and len({w['xid'] for w in first['writes']})==1)
    bind();old=admin.execute('select expires_at from '+SCHEMA+'.workspaces where id=%s',[workspace]).fetchone()['expires_at']
    admin.execute("update "+SCHEMA+".workspaces set expires_at=clock_timestamp()-interval '1 second' where id=%s",[workspace])
    deny('real_clock_expiry',read);admin.execute('update '+SCHEMA+'.workspaces set expires_at=%s where id=%s',[old,workspace])
    act(action='revoke');deny('consent_stops',act);ok('revocation_keeps_history',len(read()['state']['registrations'])==2)
    bind();cleanup=str(uuid.uuid4());admin.execute("select set_config('fmz6e.request_id',%s,false)",[cleanup]);counts={}
    with admin.transaction():
        for table in ('requests','revisions','workspaces'):
            column='id' if table=='workspaces' else 'workspace_id'
            counts[table]=len(admin.execute('delete from '+SCHEMA+'.'+table+' where '+column+'=%s returning '+column,[workspace]).fetchall())
    audit=admin.execute('select table_name,operation,key_sha,xid from '+SCHEMA+'.audit where request_id=%s order by id',[cleanup]).fetchall()
    ok('delete_proof_retained',dict(collections.Counter(w['table_name'].split('.')[-1] for w in audit))==counts and len({w['xid'] for w in audit})==1 and all(w['operation']=='DELETE' and len(w['key_sha'])==64 for w in audit))
    # Revoke subjects only after all exact child deletes have been proven.
    admin.execute('delete from '+SCHEMA+'.subjects where user_id=any(%s::uuid[])',[subjects])
    completed=[e for e in events if e['phase']=='completed']
    groups=collections.defaultdict(list)
    for e in completed:groups[e['call_id']].append(e)
    ok('all_protocol_terminals',all(v[-1]['confirmed'] and v[-1]['template_sha256'] in (digest('COMMIT'),digest('ROLLBACK')) for v in groups.values()))
    return {'status':'PASS_LOCAL_REGISTRATION12','checks':checks,'count':len(checks),'commands':len(completed),
        'register':completed,'cleanup_counts':counts,'delete_proof':audit,'hosted':False,
        'scope':'M45 only; frozen12 registration/facts; no outbox/day21/plan application'}
