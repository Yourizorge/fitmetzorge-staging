"""Exact temporary three-identity guard. SQL rendering only; no network or secrets."""
import datetime,hashlib,re,uuid

ALIASES={'a_member':'zorgeyouri+6e9-a-lid@gmail.com','a_trainer':'zorgeyouri+6e9-a-trainer@gmail.com','b_member':'zorgeyouri+6e9-b-lid@gmail.com'}
PREFIX='fmz6e11_guard_'
ROLES=tuple(ALIASES)
def literal(v):return "'"+str(v).replace("'","''")+"'"
def scope(run,ids):
    if str(uuid.UUID(run))!=run or set(ids)!=set(ROLES):raise ValueError('guard_scope')
    if len(set(ids.values()))!=3 or any(str(uuid.UUID(v))!=v for v in ids.values()):raise ValueError('guard_identity')
    return PREFIX+run.replace('-','')

def install(run,ids,seconds=540):
    s=scope(run,ids)
    if type(seconds)!=int or not 1<=seconds<=600:raise ValueError('guard_lifetime')
    entries=','.join('('+literal(ids[r])+'::uuid,'+literal(ALIASES[r])+')' for r in ROLES)
    ua='ARRAY['+','.join(literal(ids[r])+'::uuid' for r in ROLES)+']'
    ea='ARRAY['+','.join(literal(ALIASES[r]) for r in ROLES)+']::text[]'
    body=f"""DECLARE
 ids CONSTANT uuid[] := {ua};
 emails CONSTANT text[] := {ea};
 deadline CONSTANT timestamptz := %L::timestamptz;
 old_scope boolean := false; new_scope boolean := false;
BEGIN
 IF clock_timestamp() >= deadline THEN
  IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
 END IF;
 IF TG_OP<>'INSERT' THEN old_scope := OLD.id=ANY(ids) OR lower(OLD.email)=ANY(emails); END IF;
 IF TG_OP<>'DELETE' THEN new_scope := NEW.id=ANY(ids) OR lower(NEW.email)=ANY(emails); END IF;
 IF TG_OP='INSERT' AND new_scope THEN RAISE EXCEPTION 'fmz_guard_account_creation_denied' USING ERRCODE='P0001'; END IF;
 IF TG_OP='DELETE' AND old_scope THEN RAISE EXCEPTION 'fmz_guard_identity_delete_denied' USING ERRCODE='P0001'; END IF;
 IF TG_OP='UPDATE' AND (old_scope OR new_scope) AND
  (NEW.id IS DISTINCT FROM OLD.id OR NEW.email IS DISTINCT FROM OLD.email OR NEW.is_sso_user IS DISTINCT FROM OLD.is_sso_user)
 THEN RAISE EXCEPTION 'fmz_guard_identity_change_denied' USING ERRCODE='P0001'; END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END"""
    function=f'CREATE FUNCTION {s}.identity_guard() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $body${body}$body$'
    return f"""/* fmz6e11:controller_guard_v1:install */
BEGIN;
SET LOCAL lock_timeout='1s'; SET LOCAL statement_timeout='5s';
LOCK TABLE auth.users IN SHARE ROW EXCLUSIVE MODE NOWAIT;
DO $install$
DECLARE deadline timestamptz := clock_timestamp()+interval '{seconds} seconds';
BEGIN
 IF NOT pg_try_advisory_xact_lock(6110043,1) THEN RAISE EXCEPTION 'guard_busy'; END IF;
 IF EXISTS(SELECT 1 FROM pg_namespace WHERE left(nspname,{len(PREFIX)})='{PREFIX}') THEN RAISE EXCEPTION 'guard_already_exists'; END IF;
 IF (SELECT count(*) FROM (VALUES {entries}) e(id,email) JOIN auth.users u ON u.id=e.id AND u.email=e.email AND u.is_sso_user=false)<>3
 OR (SELECT count(*) FROM auth.users WHERE id=ANY({ua}) OR lower(email)=ANY({ea}))<>3
 THEN RAISE EXCEPTION 'guard_identity_mismatch'; END IF;
 CREATE SCHEMA {s};
 REVOKE ALL ON SCHEMA {s} FROM PUBLIC,anon,authenticated,service_role;
 EXECUTE format($function${function}$function$,deadline);
 REVOKE ALL ON FUNCTION {s}.identity_guard() FROM PUBLIC,anon,authenticated,service_role;
 CREATE TRIGGER {s}_i BEFORE INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION {s}.identity_guard();
 CREATE TRIGGER {s}_u BEFORE UPDATE OF id,email,is_sso_user ON auth.users FOR EACH ROW EXECUTE FUNCTION {s}.identity_guard();
 CREATE TRIGGER {s}_d BEFORE DELETE ON auth.users FOR EACH ROW EXECUTE FUNCTION {s}.identity_guard();
 EXECUTE format('COMMENT ON FUNCTION {s}.identity_guard() IS %L',json_build_object('run','{run}','expires_at',deadline,'sql_deadline',deadline::text,'seconds',{seconds},'version',1)::text);
END $install$;
COMMIT;"""

def inspect(run,ids):
    s=scope(run,ids)
    return f"""/* fmz6e11:controller_guard_v1:inspect */
SELECT jsonb_build_object('schema','{s}','server_time',clock_timestamp(),
 'functions',(SELECT coalesce(jsonb_agg(jsonb_build_object('oid',p.oid,'name',p.proname,
 'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'search_path',p.proconfig,
 'definition_sha',encode(sha256(convert_to(pg_get_functiondef(p.oid),'UTF8')),'hex'),
 'body_sha',encode(sha256(convert_to(p.prosrc,'UTF8')),'hex'),
 'acl',p.proacl::text,'lease',obj_description(p.oid,'pg_proc')::jsonb)),'[]')
 FROM pg_proc p WHERE p.pronamespace=to_regnamespace('{s}')),
 'triggers',(SELECT coalesce(jsonb_agg(jsonb_build_object('name',t.tgname,'table',t.tgrelid::regclass::text,
 'enabled',t.tgenabled,'type',t.tgtype,'function',t.tgfoid::regprocedure::text,
 'definition_sha',encode(sha256(convert_to(pg_get_triggerdef(t.oid),'UTF8')),'hex')) ORDER BY t.tgname),'[]')
 FROM pg_trigger t JOIN pg_proc p ON p.oid=t.tgfoid WHERE p.pronamespace=to_regnamespace('{s}')),
 'other_relations',(SELECT count(*) FROM pg_class WHERE relnamespace=to_regnamespace('{s}')),
 'dependencies',(SELECT coalesce(jsonb_agg(jsonb_build_object('class',d.classid::regclass::text,
 'name',t.tgname,'table',t.tgrelid::regclass::text,'type',d.deptype)),'[]')
 FROM pg_depend d JOIN pg_proc p ON d.refclassid='pg_proc'::regclass AND d.refobjid=p.oid
 LEFT JOIN pg_trigger t ON d.classid='pg_trigger'::regclass AND d.objid=t.oid
 WHERE p.pronamespace=to_regnamespace('{s}')))::text;"""

def validate(state,run,ids,active=True):
    s=scope(run,ids);f=state.get('functions',[]);ts=state.get('triggers',[]);ds=state.get('dependencies',[])
    if state.get('schema')!=s or len(f)!=1 or len(ts)!=3 or len(ds)!=3 or state.get('other_relations')!=0:raise ValueError('guard_objects')
    x=f[0];lease=x.get('lease',{})
    if x['name']!='identity_guard' or x['owner']!='postgres' or x['definer'] or x['search_path']!=['search_path=pg_catalog, pg_temp']:raise ValueError('guard_function')
    if x['acl']!='{postgres=X/postgres}':raise ValueError('guard_acl')
    if lease.get('run')!=run or lease.get('version')!=1 or type(lease.get('seconds'))!=int or not 1<=lease['seconds']<=600:raise ValueError('guard_lease')
    expected={s+'_i':7,s+'_u':19,s+'_d':11}
    if {t['name']:t['type'] for t in ts}!=expected:raise ValueError('guard_triggers')
    if any(t['table']!='auth.users' or t['enabled']!='O' or t['function']!=s+'.identity_guard()' for t in ts):raise ValueError('guard_trigger_binding')
    if {d['name'] for d in ds}!=set(expected) or any(d['class']!='pg_trigger' or d['table']!='auth.users' or d['type']!='n' for d in ds):raise ValueError('guard_dependency')
    expiry=datetime.datetime.fromisoformat(lease['expires_at']);now=datetime.datetime.fromisoformat(state['server_time'])
    if datetime.datetime.fromisoformat(lease['sql_deadline'])!=expiry:raise ValueError('guard_deadline_binding')
    body=install(run,ids,lease['seconds']).split('$body$')[1].replace('%L',literal(lease['sql_deadline']))
    if hashlib.sha256(body.encode()).hexdigest()!=x.get('body_sha'):raise ValueError('guard_source_binding')
    if active and (expiry<=now or (expiry-now).total_seconds()>600):raise ValueError('guard_expired')
    return {'schema':s,'run':run,'function_sha':x['definition_sha'],
            'trigger_shas':{t['name']:t['definition_sha'] for t in ts},'expires_at':lease['expires_at']}

def remove(run,ids,recorded):
    s=scope(run,ids)
    if recorded.get('schema')!=s or recorded.get('run')!=run or not re.fullmatch('[0-9a-f]{64}',recorded.get('function_sha','')):raise ValueError('guard_removal_scope')
    shas=recorded.get('trigger_shas',{})
    if set(shas)!={s+suffix for suffix in ('_i','_u','_d')} or any(not re.fullmatch('[0-9a-f]{64}',h) for h in shas.values()):raise ValueError('guard_removal_triggers')
    entries=','.join('('+literal(n)+','+literal(h)+')' for n,h in sorted(shas.items()))
    return f"""/* fmz6e11:controller_guard_v1:safety_remove */
BEGIN;
SET LOCAL lock_timeout='1s'; SET LOCAL statement_timeout='5s';
DO $remove$
DECLARE f oid := to_regprocedure('{s}.identity_guard()');
BEGIN
 IF f IS NULL OR (SELECT encode(sha256(convert_to(pg_get_functiondef(f),'UTF8')),'hex'))<>'{recorded['function_sha']}'
 OR (SELECT count(*) FROM pg_proc WHERE pronamespace=to_regnamespace('{s}'))<>1
 OR EXISTS(SELECT 1 FROM pg_class WHERE relnamespace=to_regnamespace('{s}'))
 OR (SELECT count(*) FROM pg_depend WHERE refclassid='pg_proc'::regclass AND refobjid=f)<>3
 OR (SELECT count(*) FROM (VALUES {entries}) e(name,sha) JOIN pg_trigger t ON t.tgname=e.name AND t.tgfoid=f AND t.tgrelid='auth.users'::regclass
 AND encode(sha256(convert_to(pg_get_triggerdef(t.oid),'UTF8')),'hex')=e.sha)<>3
 THEN RAISE EXCEPTION 'guard_removal_identity_mismatch'; END IF;
 DROP FUNCTION {s}.identity_guard() CASCADE;
 DROP SCHEMA {s} RESTRICT;
END $remove$;
COMMIT;"""
