"""Three-statement synthetic session canary, shared by local/CI/hosted runners."""
import hashlib,json,uuid
import audit

def plan_summary(raw):
    plan=json.loads(raw)
    if len(plan)!=1:raise ValueError('probe_plan_shape')
    item=plan[0]
    def check(node):
        if node.get('Temp Read Blocks',0) or node.get('Temp Written Blocks',0):raise ValueError('probe_own_temp_io')
        for child in node.get('Plans',[]):check(child)
    check(item['Plan'])
    if item['Execution Time']>1000:raise ValueError('probe_latency')
    return {'queryid':str(item.get('Query Identifier')),'execution_ms':item['Execution Time'],
            'own_temp_read_blocks':0,'own_temp_written_blocks':0,
            'trigger_calls':sum(t['Calls'] for t in item.get('Triggers',[]))}

def sql_sequence(session,actor):
    if any(str(uuid.UUID(v))!=v for v in (session,actor)):raise ValueError('probe_identity')
    return [
        f"insert into auth.sessions(id,user_id,created_at,updated_at) values('{session}','{actor}',clock_timestamp(),clock_timestamp())",
        f"update auth.sessions set updated_at=clock_timestamp() where id='{session}' and user_id='{actor}'",
        f"delete from auth.sessions where id='{session}' and user_id='{actor}'"]

def validate(events,action,session,actor):
    if len(events)!=3 or [e['operation'] for e in events]!=['INSERT','UPDATE','DELETE']:raise ValueError('probe_write_multiset')
    if len({e['xid'] for e in events})!=1 or len({e['backend'] for e in events})!=1:raise ValueError('probe_transaction')
    for e in events:
        if e['table_name']!='auth.sessions' or e['action_id']!=action or e['actor_sha']!=hashlib.sha256(actor.encode()).hexdigest() or e['key_sha']!=hashlib.sha256(session.encode()).hexdigest():raise ValueError('probe_scope')
    return {'inserts':1,'updates':1,'deletes':1,'same_transaction':True,'delete_retained':True,'extra_writes':0}

def snapshot(ids,session):
    audit.g.scope(str(uuid.uuid4()),ids)
    if str(uuid.UUID(session))!=session:raise ValueError('probe_identity')
    expected=','.join(audit.g.literal(v)+'::uuid' for v in ids.values())
    # Only three test identities; no member data or session secrets are returned.
    return f"select jsonb_build_object('fixture_rows',(select count(*) from auth.sessions where id='{session}'),'existing_sessions',(select coalesce(jsonb_agg(encode(sha256(convert_to(jsonb_build_array(id,user_id,created_at,updated_at)::text,'UTF8')),'hex') order by id),'[]') from auth.sessions where user_id in ({expected})))::text"
