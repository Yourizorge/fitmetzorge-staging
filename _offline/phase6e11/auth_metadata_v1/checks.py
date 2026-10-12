"""Same synthetic SQL checks in isolated PG17 and the clean Supabase CI stack."""
import datetime,hashlib,json,time,uuid
import audit

def run(sql,hold,ids):
    passed=[];run_id=str(uuid.uuid4());s=audit.scope(run_id,ids);receipt=None
    deadline=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=120)).isoformat()
    member=ids['a_member'];other='68000000-0000-4000-8000-000000000004'
    def ok(name,value):
        if not value:raise RuntimeError('metadata_'+name)
        passed.append(name)
    def q(text,actor='postgres'):
        p=sql(text,actor)
        if p.returncode:raise RuntimeError('metadata_sql_failed_'+(p.stderr.split('ERROR:')[-1][:100] if actor=='local_debug' else str(p.returncode)))
        return p.stdout.strip()
    def deny(name,text,code='permission denied',actor='supabase_auth_admin'):
        p=sql(text,actor);ok(name,p.returncode!=0 and code in p.stderr)
    def arm(role='a_member',route='verify'):
        action=str(uuid.uuid4());q(audit.arm(run_id,ids,action,role,route));return action
    def get(action):return json.loads(q(audit.events(run_id,ids,action)))
    def close(action):q(audit.disarm(run_id,ids,action))
    def change(uid):return "update auth.users set last_sign_in_at=clock_timestamp() where id='"+uid+"'"
    try:
        q(audit.install(run_id,ids,deadline));receipt=audit.validate(json.loads(q(audit.inspect(run_id,ids))),run_id,ids,deadline)
        ok('exact_seven_triggers',len(receipt['triggers'])==7)
        deny('unarmed_synthetic_write',change(member),'metadata_action_not_armed')
        q(change(other),'supabase_auth_admin');ok('unrelated_user_not_observed',q('select count(*) from '+s+'.events')=='0')
        for role in ('anon','authenticated','service_role'):
            deny('private_read_'+role,'select * from '+s+'.events',actor=role)
            deny('private_control_'+role,'update '+s+'.control set armed=true',actor=role)
        deny('auth_cannot_arm','update '+s+'.control set armed=true')
        deny('auth_cannot_change_events','delete from '+s+'.events')
        action=arm()
        deny('second_action',audit.arm(run_id,ids,str(uuid.uuid4()),'b_member','issue'),'metadata_already_armed','postgres')
        deny('wrong_actor',change(ids['b_member']),'metadata_action_not_armed')
        with hold('begin; select singleton from '+s+'.control for update;'):
            deny('concurrent_control',audit.disarm(run_id,ids,action),'could not obtain lock','postgres')
        with hold('begin;'+change(member)+';'):
            deny('inflight_write_cannot_relabel',audit.disarm(run_id,ids,action),'metadata_write_inflight','postgres')
        q('begin;'+change(member)+';rollback;','supabase_auth_admin');ok('rolled_back_write_absent',get(action)==[])
        session=str(uuid.uuid4());claim=str(uuid.uuid4())
        q("begin;insert into auth.sessions(id,user_id,created_at,updated_at) values('"+session+"','"+member+"',now(),now());"
          "insert into auth.mfa_amr_claims(id,session_id,authentication_method,created_at,updated_at) values('"+claim+"','"+session+"','password',now(),now());"
          +change(member)+";delete from auth.sessions where id='"+session+"';commit;",'supabase_auth_admin')
        rows=get(action)
        ok('insert_update_delete_count',len(rows)==5)
        ok('one_transaction',len({e['xid'] for e in rows})==1)
        ok('same_actor',all(e['actor_sha']==hashlib.sha256(member.encode()).hexdigest() for e in rows))
        ok('same_action',all(e['action_id']==action for e in rows))
        deletes={e['table_name']:e['key_sha'] for e in rows if e['operation']=='DELETE'}
        ok('session_delete_retained',deletes.get('auth.sessions')==hashlib.sha256(session.encode()).hexdigest())
        ok('cascade_amr_delete_retained',deletes.get('auth.mfa_amr_claims')==hashlib.sha256(claim.encode()).hexdigest())
        ok('no_row_content',all(set(e)=={'seq','action_id','table_name','operation','xid','backend','key_sha','actor_sha','session_sha','at'} for e in rows))
        ok('null_session_not_invented',next(e for e in rows if e['table_name']=='auth.users')['session_sha'] is None)
        q(change(member)+';'+change(member),'supabase_auth_admin')
        ok('repeated_updates_not_deduplicated',len(get(action))==7)
        close(action)
        deny('reused_action',audit.arm(run_id,ids,action,'a_member','verify'),'duplicate key','postgres')
        # Failures do not permit broad removal of unexpected objects.
        q('create table '+s+'.unexpected(id int)')
        deny('unexpected_object_kept',audit.remove(run_id,ids,receipt),'metadata_removal_mismatch','postgres')
        q('drop table '+s+'.unexpected')
        q(audit.remove(run_id,ids,receipt));receipt=None
        ok('removed_exactly',q("select count(*) from pg_namespace where nspname='"+s+"'")=='0')
        q(change(member),'supabase_auth_admin');ok('original_auth_operation_after_removal',True)
        deadline=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=1)).isoformat()
        q(audit.install(run_id,ids,deadline));receipt=audit.validate(json.loads(q(audit.inspect(run_id,ids))),run_id,ids,deadline)
        time.sleep(1.1)
        deny('expired_admission',audit.arm(run_id,ids,str(uuid.uuid4()),'a_member','issue'),'metadata_expired','postgres')
        q(change(member),'supabase_auth_admin');ok('expired_observer_inert',q('select count(*) from '+s+'.events')=='0')
        q(audit.remove(run_id,ids,receipt));receipt=None
        ok('expired_removed',q("select count(*) from pg_namespace where nspname='"+s+"'")=='0')
        return {'status':'AUTH_METADATA_DATABASE_PASS','checks':len(passed),'passed':passed,'hosted_calls':0}
    finally:
        if receipt:q(audit.remove(run_id,ids,receipt))
