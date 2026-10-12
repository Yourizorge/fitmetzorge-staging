"""Same bounded synthetic guard checks for local PG17 and disposable Supabase CI."""
import json,time,uuid
from guard import ALIASES,ROLES,install,inspect,validate,remove,scope,literal

IDS={r:'68000000-0000-4000-8000-'+str(i).zfill(12) for i,r in enumerate(ROLES,1)}
OTHER='68000000-0000-4000-8000-000000000004'
def run(sql,hold):
    passed=[];runs=[]
    def check(name,condition):
        if not condition:raise RuntimeError(name)
        passed.append(name)
    def success(q,actor='postgres'):
        p=sql(q,actor)
        if p.returncode:raise RuntimeError('guard_sql_'+str(p.returncode))
        return p.stdout.strip()
    def deny(name,q,code,actor='supabase_auth_admin'):
        p=sql(q,actor);check(name,p.returncode!=0 and code in p.stderr)
    def state(r):return json.loads(success(inspect(r,IDS)))
    def begin(seconds=120):
        r=str(uuid.uuid4());success(install(r,IDS,seconds));runs.append(r)
        return r,validate(state(r),r,IDS)
    def end(r,receipt):
        success(remove(r,IDS,receipt));check('removed_'+str(len(passed)),state(r)['functions']==[])
        runs.remove(r)
    def catalog():
        return success("select coalesce(jsonb_agg(x order by x::text),'[]') from (select t.tgname,t.tgtype,t.tgenabled,pg_get_triggerdef(t.oid) definition from pg_trigger t where tgrelid='auth.users'::regclass and not tgisinternal) x")
    # All rows are new local/CI fixtures. Never call this against hosted staging.
    for role in ROLES:
        success('insert into auth.users(id,email,is_sso_user) values('+literal(IDS[role])+','+literal(ALIASES[role])+',false)')
    success('insert into auth.users(id,email,is_sso_user) values('+literal(OTHER)+",'unrelated@example.invalid',false)")
    before=catalog()
    try:
        check('actual_auth_database_role',success('select current_user','supabase_auth_admin')=='supabase_auth_admin')
        r,receipt=begin();check('three_exact_triggers_invoker_acl',len(state(r)['triggers'])==3)
        # Dedicated open transaction holds the old row-lock scheme while a
        # separate Auth connection proves the new trigger catches the race.
        with hold('begin;select id from auth.users where id='+literal(IDS['a_member'])+' for key share;'):
            for name,assignment in [('email',"email='changed@example.invalid'"),('uuid',"id='68000000-0000-4000-8000-000000000099'"),('sso','is_sso_user=true')]:
                deny('concurrent_'+name,'update auth.users set '+assignment+' where id='+literal(IDS['a_member']),
                     'fmz_guard_identity_change_denied' if name!='uuid' else 'lock timeout')
            success("update auth.users set recovery_token='local-fixture-token',last_sign_in_at=clock_timestamp() where id="+literal(IDS['a_member']),'supabase_auth_admin')
            check('concurrent_auth_token_updates_allowed',True)
        deny('uuid_change_denied','update auth.users set id='+literal(str(uuid.uuid4()))+' where id='+literal(IDS['a_member']),'fmz_guard_identity_change_denied')
        deny('delete_protected','delete from auth.users where id='+literal(IDS['a_member']),'fmz_guard_identity_delete_denied')
        deny('replacement_insert','insert into auth.users(id,email,is_sso_user) values('+literal(str(uuid.uuid4()))+','+literal(ALIASES['a_member'])+',false)','fmz_guard_account_creation_denied')
        deny('case_alias_collision','insert into auth.users(id,email,is_sso_user) values('+literal(str(uuid.uuid4()))+','+literal(ALIASES['a_member'].upper())+',true)','fmz_guard_account_creation_denied')
        deny('outside_to_protected_alias','update auth.users set email='+literal(ALIASES['b_member'])+' where id='+literal(OTHER),'fmz_guard_identity_change_denied')
        for role in ['anon','authenticated','service_role']:
            deny('direct_execute_'+role,'select '+scope(r,IDS)+'.identity_guard()','permission denied',role)
        extra=str(uuid.uuid4())
        success('insert into auth.users(id,email,is_sso_user) values('+literal(extra)+",'outside-new@example.invalid',false);"
                'update auth.users set email=\'outside-edited@example.invalid\' where id='+literal(extra)+';delete from auth.users where id='+literal(extra),'supabase_auth_admin')
        check('outside_insert_update_delete_unchanged',True)
        deny('second_guard_denied',install(str(uuid.uuid4()),IDS),'guard_already_exists','postgres')
        bad={**receipt,'function_sha':'0'*64}
        deny('changed_definition_blocks_removal',remove(r,IDS,bad),'guard_removal_identity_mismatch','postgres')
        # A new dependent object must never be silently removed with CASCADE.
        success('create table '+scope(r,IDS)+'.unexpected(id int)')
        deny('unexpected_object_blocks_removal',remove(r,IDS,receipt),'guard_removal_identity_mismatch','postgres')
        success('drop table '+scope(r,IDS)+'.unexpected')
        end(r,receipt);check('catalog_restored',catalog()==before)
        success('delete from auth.users where id='+literal(IDS['b_member']),'supabase_auth_admin')
        deny('missing_account_no_guard',install(str(uuid.uuid4()),IDS),'guard_identity_mismatch','postgres')
        success('insert into auth.users(id,email,is_sso_user) values('+literal(IDS['b_member'])+','+literal(ALIASES['b_member'])+',false)')
        success('update auth.users set email='+literal(ALIASES['a_member'].upper())+',is_sso_user=true where id='+literal(OTHER),'supabase_auth_admin')
        deny('preexisting_conflict_no_guard',install(str(uuid.uuid4()),IDS),'guard_identity_mismatch','postgres')
        success('update auth.users set email=\'unrelated@example.invalid\',is_sso_user=false where id='+literal(OTHER),'supabase_auth_admin')
        r,receipt=begin(seconds=1);time.sleep(1.1)
        try:validate(state(r),r,IDS)
        except ValueError as e:check('expired_admission_denied',str(e)=='guard_expired')
        else:raise RuntimeError('expiry_not_denied')
        success('update auth.users set email=\'after-expiry@example.invalid\' where id='+literal(IDS['a_member']),'supabase_auth_admin')
        check('expired_trigger_inert',True)
        end(r,receipt)
        success('update auth.users set email='+literal(ALIASES['a_member'])+' where id='+literal(IDS['a_member']),'supabase_auth_admin')
        check('final_original_catalog',catalog()==before)
        return {'status':'GUARD_DATABASE_PASS','checks':len(passed),'passed':passed,'hosted_calls':0,'guard_objects_remaining':0}
    finally:
        # Only exact objects this local test created. Never fixture cleanup here.
        for r in runs:
            try:
                v=validate(state(r),r,IDS,active=False);success(remove(r,IDS,v))
            except Exception:pass
