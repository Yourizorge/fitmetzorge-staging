"""Bounded native suffix for confirmed mint prefixes; never a failure-to-PASS path.

Unknown/incomplete verify is observed, not repaired. In particular an advisory
lock is NOT proof that a delayed HTTP request cannot start minting later.
Only a fully validated step-4 prefix permits exact session-key deletion here.
"""
from collections import Counter
import hashlib,json,re,uuid
from integral_io import check_plan,delta
from integral_stream import ALL_STATS
from utility_binding import UtilityBindings

ROLES=('a_member','a_trainer','b_member')
HASH=re.compile(r'[0-9a-f]{64}')


def sha(value):return hashlib.sha256(value.encode()).hexdigest()


def rows_expression(ids):
    users=','.join("'"+str(uuid.UUID(ids[r]))+"'" for r in ROLES)
    key=lambda value:"encode(sha256(convert_to("+value+"::text,'UTF8')),'hex')"
    branches=[
        "select 'auth.sessions' t,"+key('s.id')+' k,'+key('s.user_id')+' a,'+key('s.id')+
        ' s from auth.sessions s where s.user_id::text in('+users+')',
        "select 'auth.refresh_tokens',"+key('r.id')+','+key('r.user_id')+','+key('r.session_id')+
        ' from auth.refresh_tokens r where r.user_id::text in('+users+')',
        "select 'auth.mfa_amr_claims',"+key('m.id')+','+key('s.user_id')+','+key('m.session_id')+
        ' from auth.mfa_amr_claims m join auth.sessions s on s.id=m.session_id where s.user_id::text in('+users+')']
    return "(select coalesce(jsonb_agg(x order by t,k,a,s),'[]') from ("+' union all '.join(branches)+' limit 13) x)'


def read_sql(r):
    schema=r.audit.scope(r.run_id,r.ids)
    inspection=r.audit.inspect(r.run_id,r.ids).rstrip(';')
    return """select jsonb_build_object(
 'lock',pg_try_advisory_xact_lock(6110043,3),
 'statement_timeout',current_setting('statement_timeout'),
 'lock_timeout',current_setting('lock_timeout'),
 'live',clock_timestamp()<"""+"'"+r.expiry.replace("'","''")+"'::timestamptz,"+"""
 'audit',("""+inspection+""" )::jsonb,
 'rows',"""+rows_expression(r.ids)+""",
 'events',(select coalesce(jsonb_agg(e order by seq),'[]') from
  (select seq,action_id,table_name,operation,xid,backend,key_sha,actor_sha,session_sha
   from """+schema+""".events order by seq limit 513) e),
 'io',("""+ALL_STATS+"""))::text"""


def allowed_rows(ids,keys):
    allowed=set()
    for role in ROLES:
        k=keys[role];actor=sha(ids[role]);session=k['session']
        for name in ('session','refresh','fresh','amr'):
            if not isinstance(k.get(name),str) or not HASH.fullmatch(k[name]):
                raise ValueError('safety_native_contract_keys')
        allowed.add(('auth.sessions',session,actor,session))
        allowed.add(('auth.mfa_amr_claims',k['amr'],actor,session))
        for name in ('refresh','fresh'):allowed.add(('auth.refresh_tokens',k[name],actor,session))
    if len(allowed)!=12:raise ValueError('safety_native_duplicate_contract_keys')
    return allowed


def row_key(row):return tuple(row[k] for k in ('t','k','a','s'))


def validate_snapshot(r,value,keys=None):
    if value['lock'] is not True or value['live'] is not True:
        raise ValueError('safety_native_lease_or_inflight')
    if value['statement_timeout'] not in ('5s','5000ms') or value['lock_timeout'] not in ('1s','1000ms'):
        raise ValueError('safety_native_time_limits')
    r.audit.validate(value['audit'],r.run_id,r.ids,r.expiry)
    if len(value['events'])>512 or len(value['rows'])>12 or len(value['io']['statements'])>5000:
        raise ValueError('safety_native_capacity')
    if keys is not None:
        rows=[row_key(x) for x in value['rows']]
        if len(set(rows))!=len(rows) or not set(rows)<=allowed_rows(r.ids,keys):
            raise ValueError('safety_native_unowned_rows')


def revoke_sql(r,keys,before):
    schema=r.audit.scope(r.run_id,r.ids)
    actions={role:str(uuid.uuid5(uuid.UUID(r.run_id),'safety-auth-native:'+role)) for role in ROLES}
    expected=json.dumps(before['rows'],sort_keys=True,separators=(',',':')).replace("'","''")
    pieces=[]
    for role in ROLES:
        actor=sha(r.ids[role]);session=keys[role]['session'];action=actions[role]
        # Match the primary key via its fixed, already-proven hash AND actor.
        pieces.append(f"""
 INSERT INTO {schema}.actions(action_id,actor_sha,route) VALUES('{action}','{actor}','safety_logout');
 UPDATE {schema}.control SET action_id='{action}',actor_sha='{actor}',route='safety_logout',armed=true WHERE singleton;
 DELETE FROM auth.sessions WHERE user_id='{r.ids[role]}'::uuid
  AND encode(sha256(convert_to(id::text,'UTF8')),'hex')='{session}';
 UPDATE {schema}.control SET armed=false WHERE singleton;
""")
    sql=f"""DO $safety_auth$ BEGIN
 IF NOT pg_try_advisory_xact_lock(6110043,3) THEN RAISE EXCEPTION 'safety_native_inflight'; END IF;
 IF (obj_description('{schema}'::regnamespace,'pg_namespace')::jsonb->>'expires_at')::timestamptz<=clock_timestamp()
 THEN RAISE EXCEPTION 'safety_native_expired'; END IF;
 IF {rows_expression(r.ids)} IS DISTINCT FROM '{expected}'::jsonb
 THEN RAISE EXCEPTION 'safety_native_rows_changed'; END IF;
"""+''.join(pieces)+"END $safety_auth$;"
    return sql,set(actions.values())


def validate_deletes(before,after,actions):
    old=[e for e in after['events'] if e['action_id'] not in actions]
    if old!=before['events']:raise ValueError('safety_native_original_events_changed')
    events=[e for e in after['events'] if e['action_id'] in actions]
    expected=Counter(row_key(x) for x in before['rows'])
    actual=Counter((e['table_name'],e['key_sha'],e['actor_sha'],e['session_sha']) for e in events)
    if actual!=expected or any(e['operation']!='DELETE' for e in events):
        raise ValueError('safety_native_delete_multiset')
    if events and len({(e['xid'],e['backend']) for e in events})!=1:
        raise ValueError('safety_native_delete_transaction')
    if after['rows']:raise ValueError('safety_native_not_zero')


def native_suffix(r,save,keys,mint_terminal):
    count=0;transaction=False;commit_attempted=False;commit_confirmed=False;profiles=[]
    result={'run_id':r.run_id,'status':'NO_GO','revocation_confirmed':False,'global_zero_claim':False,
        'original_pair_unchanged':True,'retry':False,'mint_terminal':mint_terminal}
    def q(sql):
        nonlocal count
        count+=1
        if count>12:raise ValueError('safety_native_command_limit')
        return r.sql(sql)
    def read():return json.loads(q(source))
    try:
        source=read_sql(r)
        reader=check_plan(json.loads(q('EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+source)))
        initial=read()
        save('native-observed.json',initial)
        validate_snapshot(r,initial,keys if mint_terminal else None)
        if not mint_terminal:
            result['reason']='incomplete_auth_mint_outcome_unknown'
            return result
        bindings=UtilityBindings()
        def utility(sql,before):
            q(sql);after=read();validate_snapshot(r,after,keys)
            observed=bindings.observe(sha(sql),before['io'],after['io'],reader)
            bindings.confirm(sha(sql),observed)
            readonly={reader}
            if sql in ('BEGIN','COMMIT'):readonly.add(observed['queryid'])
            profile=delta(before['io'],after['io'],{reader:1,observed['queryid']:1},readonly=readonly)
            profiles.append({'source_sha256':sha(sql),'binding':observed,'profile':profile})
            return after
        # Mark before dispatch: a lost BEGIN response still needs one rollback.
        transaction=True
        before=utility('BEGIN',initial)
        save('native-before.json',before)
        sql,actions=revoke_sql(r,keys,before)
        after=utility(sql,before)
        validate_deletes(before,after,actions)
        save('native-after.json',after)
        commit_attempted=True
        witness=utility('COMMIT',after);transaction=False;commit_confirmed=True
        validate_deletes(before,witness,actions)
        closing=json.loads(q('EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) '+source))
        if check_plan(closing,True)!=reader:raise ValueError('safety_native_closing_identity')
        # VERBOSE plans can contain SQL expressions and literals: keep them in
        # memory, export only the checked numeric closing witness.
        closing_safe={'queryid':reader,'source_sha256':sha(source),'actual_rows':1,
            'execution_ms':closing[0]['Execution Time'],'temp_written':0,'read_wal':0,'query_text_exported':False}
        save('native-committed.json',{'witness':witness,'profiles':profiles,'closing':closing_safe})
        result.update(revocation_confirmed=True,reason='exact_three_account_session_zero')
        return result
    except Exception as error:
        result.update(reason='native_revocation_unconfirmed',error_class=type(error).__name__)
        return result
    finally:
        if transaction:
            try:q('ROLLBACK')
            except Exception:result['rollback_confirmed']=False
            else:result['rollback_confirmed']=True
        result['native_commands']=count
        result.update(commit_attempted=commit_attempted,commit_confirmed=commit_confirmed)
