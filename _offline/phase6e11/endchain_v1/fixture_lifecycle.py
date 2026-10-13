"""Exact new synthetic fixture rows; unchanged product functions thereafter.

Preallocated keys make setup auditable before INSERT. This initializes the
same prepared fixture state, not a new member-facing prepare workflow.
"""
import hashlib,json,uuid

SEED="""/* fmz6e11:endchain_v1:fixture_seed */
with f as(select fmz6e11_private.fixture('kg') body),
principal as(select fmz6e11_private.principal() p),
w as(insert into fmz6e11_private.windows(id,operator_id,package_version,scenario,starts_at,ends_at,revision)
 select $1::uuid,$4::uuid,'6e11@1','kg',$8::timestamptz,$9::timestamptz,1 from principal
 where p->>'uid'=$4::text and p->>'role'='a_trainer'
 and exists(select 1 from fmz6e11_private.operators where user_id=$4::uuid and enabled)
 and not exists(select 1 from fmz6e11_private.windows where id=$1::uuid)
 returning id),
p as(insert into fmz6e11_private.participants(window_id,user_id,role)
 select w.id,v.id,v.role from w cross join(values($5::uuid,'a_member'),($4::uuid,'a_trainer'),($6::uuid,'b_member'))v(id,role) returning *),
a as(insert into fmz6e11_private.workspaces(id,window_id,route,member_id,trainer_id,observations)
 select $2::uuid,w.id,'A',$5::uuid,$4::uuid,f.body->'observations' from w,f where (select count(*) from p)=3 returning id),
b as(insert into fmz6e11_private.workspaces(id,window_id,route,member_id,observations)
 select $3::uuid,w.id,'B',$6::uuid,'[]' from w where exists(select 1 from a) returning id),
plan as(insert into fmz6e11_private.plans(workspace_id,version,content,hash)
 select a.id,1,f.body->'plan',fmz6e11_private.sha(f.body->'plan') from a,f returning workspace_id),
bs as(insert into fmz6e11_private.b_states(workspace_id) select id from b returning workspace_id),
receipt as(select jsonb_build_object('window',w.id,'status','prepared','revision',1,'action','prepare',
 'synthetic_only',true,'automatic_actions_allowed',false) body from w where exists(select 1 from plan) and exists(select 1 from bs)),
au as(insert into fmz6e11_private.audit(window_id,actor,action,receipt)
 select $1::uuid,$4::uuid,'prepare',body from receipt returning id),
rq as(insert into fmz6e11_private.requests(actor,key,payload_hash,window_id,receipt)
 select $4::uuid,$7::uuid,fmz6e11_private.sha($10::jsonb),$1::uuid,body from receipt where exists(select 1 from au) returning key)
select body value from receipt where exists(select 1 from rq)"""

REGISTER="""/* fmz6e11:endchain_v1:lifecycle_intent */
with r as(insert into fmz6e11_audit_private.runs(id,enabled,expires_at)
 values($1::uuid,true,clock_timestamp()+interval '3 minutes') returning id),
p as(insert into fmz6e11_audit_private.actors(id,run_id,provenance)
 select $3::uuid,r.id,'synthetic_fixture_only' from r
 on conflict(id) do update set run_id=excluded.run_id returning id),
a as(insert into fmz6e11_audit_private.actions(id,run_id,actor,workspace,expected,before_sha)
 select $2::uuid,$1::uuid,p.id,$4::uuid,
 (select coalesce(jsonb_agg(fmz6e11_request_private.entry($1::uuid,e->>0,e->>1,e->2)->0),'[]') from jsonb_array_elements($5::jsonb)e),$6
 from p returning id)
select id::text from a"""

SNAPSHOT="""/* fmz6e11:endchain_v1:lifecycle_pair */
select jsonb_build_object('state',jsonb_build_array(fmz6e11_request_private.snapshot($1::uuid,$2::uuid),fmz6e11_request_private.snapshot($1::uuid,$3::uuid)),
 'action',(select to_jsonb(a) from fmz6e11_audit_private.actions a where id=$4::uuid),
 'writes',coalesce((select jsonb_agg(to_jsonb(w) order by ordinal) from fmz6e11_audit_private.writes w where action_id=$4::uuid),'[]'),
 'profiles',(select fmz6e11_private.sha(coalesce(jsonb_agg(to_jsonb(p) order by id),'[]')) from public.profiles p where id=any($5::uuid[])),
 'accounts',(select fmz6e11_private.sha(coalesce(jsonb_agg(to_jsonb(u) order by id),'[]')) from auth.users u where id=any($5::uuid[])),
 'coverage',not exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
 left join fmz6e11_audit_private.relations r on r.rel=c.oid
 left join pg_trigger t on t.tgrelid=c.oid and t.tgname='fmz6e11_tx_observer'
 where n.nspname in('public','fmz6e11_private') and c.relkind='r'
 and(r.rel is null or t.oid is null or t.tgenabled<>'O' or t.tgfoid<>'fmz6e11_audit_private.observe()'::regprocedure))) value"""

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()

def seed_writes(c):
    w,a,b,t,m,bm,k=(c[n] for n in ('window','a','b','trainer','member','b_member','key'))
    return [['windows','INSERT',[w]],*([['participants','INSERT',[w,u]] for u in (m,t,bm)]),
      ['workspaces','INSERT',[a]],['workspaces','INSERT',[b]],['plans','INSERT',[a,1]],
      ['b_states','INSERT',[b]],['audit','INSERT',[w,t,'prepare']],['requests','INSERT',[t,k]]]

def validate(before,after,expected):
    if not before['coverage'] or not after['coverage']:raise ValueError('lifecycle_observer_coverage')
    if any(before[k]!=after[k] for k in ('profiles','accounts')):raise ValueError('lifecycle_protected_drift')
    a=after['action'];writes=after['writes']
    if not a or a['state']!='action_confirmed' or len(a['expected'])!=len(expected):raise ValueError('lifecycle_confirmation')
    actual=[{'table':v['table_name'],'op':v['operation'],'old':v['old_key_sha'],'new':v['new_key_sha']} for v in writes]
    if sorted(actual,key=digest)!=sorted(a['expected'],key=digest):raise ValueError('lifecycle_write_multiset')
    if any(str(v['xid'])!=str(a['xid']) or v['backend']!=a['backend'] or
        v['actor']!=a['actor'] or v['workspace']!=a['workspace'] for v in writes):raise ValueError('lifecycle_transaction_binding')
    return {'pair_complete':True,'protected_equal':True,'xid':str(a['xid']),
        'expected':len(expected),'actual':len(writes),'inserts':sum(v['operation']=='INSERT' for v in writes),
        'updates':sum(v['operation']=='UPDATE' for v in writes),'deletes':sum(v['operation']=='DELETE' for v in writes),
        'before_sha':digest(before),'after_sha':digest(after),'audit_sha':digest(writes)}

def perform(query,save,c,name,effects,sql,args,claims,headers):
    run,action=c['runs'][name],str(uuid.uuid4())
    def read():return query('reader','lifecycle_measure',SNAPSHOT,[c['window'],c['a'],c['b'],action,
        '{'+','.join(c[n] for n in ('trainer','member','b_member'))+'}'])[0]['value']
    before=read()
    if not before['coverage']:raise ValueError('lifecycle_observer_coverage')
    save('lifecycle-'+name+'-before.json',{'state':before,'contract':effects,'run':run,'action':action})
    registered=query('setup','lifecycle_register',REGISTER,[run,action,c['trainer'],c['a'],effects,digest(before)])
    if registered!=[{'id':action}]:raise ValueError('lifecycle_intent_missing')
    query('setup','lifecycle_begin','BEGIN')
    try:
        query('setup','lifecycle_start','select fmz6e11_audit_private.start_action($1::uuid)',[action])
        query('setup','lifecycle_bind',"select set_config('request.jwt.claims',$1,true),set_config('request.headers',$2,true)",
            [json.dumps(claims),json.dumps(headers)])
        result=query('setup','lifecycle_action',sql,args)
        query('setup','lifecycle_confirm','select fmz6e11_audit_private.confirm_action($1::uuid)',[action])
        query('setup','lifecycle_commit','COMMIT')
    except BaseException:
        query('setup','lifecycle_rollback','ROLLBACK');raise
    after=read();save('lifecycle-'+name+'-after.json',after)
    proof=validate(before,after,effects)
    save('lifecycle-'+name+'-pair.json',proof)
    query('setup','lifecycle_seal','select fmz6e11_audit_private.seal_pair($1::uuid,$2,$3)',[action,digest(after),digest(proof)])
    return result
