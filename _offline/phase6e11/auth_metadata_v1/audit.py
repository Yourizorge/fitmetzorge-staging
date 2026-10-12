"""Temporary exact-three-identity Auth audit. SQL renderer, no secret input."""
import datetime,hashlib,importlib.util,json,pathlib,re,uuid
spec=importlib.util.spec_from_file_location('metadata_guard',pathlib.Path(__file__).resolve().parent.parent/'controller_guard_v1/guard.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
TABLES=('users','identities','sessions','refresh_tokens','audit_log_entries','one_time_tokens','mfa_amr_claims')
ROUTES=('issue','verify','getUser','refresh','logout','revoked_denial')
PREFIX='fmz6e11_am_'
RELATIONS=sorted(['control','control_pkey','actions','actions_pkey','session_keys','session_keys_pkey','events','events_pkey','events_seq_seq'])

def scope(run,ids):
    g.scope(run,ids)
    return PREFIX+run.replace('-','')

def function_body(s,ids,deadline):
    allowed='ARRAY['+','.join(g.literal(ids[r]) for r in g.ROLES)+']::text[]'
    return f"""DECLARE
 deadline CONSTANT timestamptz := {g.literal(deadline)}::timestamptz;
 ids CONSTANT text[] := {allowed};
 actor text; previous_actor text; row_key text; previous_key text; session_key text;
 ah text; sh text; expected_actor text; active_action uuid;
BEGIN
 IF clock_timestamp()>=deadline THEN RETURN NULL; END IF;
 IF TG_TABLE_SCHEMA<>'auth' OR TG_TABLE_NAME NOT IN ({','.join(g.literal(x) for x in TABLES)}) OR TG_WHEN<>'AFTER' THEN RAISE EXCEPTION 'metadata_trigger_binding'; END IF;
 IF TG_TABLE_NAME='users' THEN
  IF TG_OP<>'DELETE' THEN actor:=NEW.id::text; row_key:=NEW.id::text; END IF;
  IF TG_OP<>'INSERT' THEN previous_actor:=OLD.id::text; previous_key:=OLD.id::text; END IF;
 ELSIF TG_TABLE_NAME='audit_log_entries' THEN
  IF TG_OP<>'DELETE' THEN actor:=NEW.payload->>'actor_id'; row_key:=NEW.id::text; END IF;
  IF TG_OP<>'INSERT' THEN previous_actor:=OLD.payload->>'actor_id'; previous_key:=OLD.id::text; END IF;
 ELSIF TG_TABLE_NAME='mfa_amr_claims' THEN
  session_key:=CASE WHEN TG_OP='DELETE' THEN OLD.session_id::text ELSE NEW.session_id::text END;
  sh:=encode(sha256(convert_to(session_key,'UTF8')),'hex');
  SELECT actor_sha INTO ah FROM {s}.session_keys WHERE key_sha=sh;
  IF ah IS NULL THEN RETURN NULL; END IF;
  IF TG_OP='UPDATE' AND OLD.session_id IS DISTINCT FROM NEW.session_id THEN RAISE EXCEPTION 'metadata_actor_change'; END IF;
  row_key:=CASE WHEN TG_OP='DELETE' THEN OLD.id::text ELSE NEW.id::text END;
  previous_key:=CASE WHEN TG_OP='INSERT' THEN NULL ELSE OLD.id::text END;
 ELSE
  IF TG_OP<>'DELETE' THEN actor:=NEW.user_id::text; row_key:=NEW.id::text; END IF;
  IF TG_OP<>'INSERT' THEN previous_actor:=OLD.user_id::text; previous_key:=OLD.id::text; END IF;
  IF TG_TABLE_NAME='sessions' THEN session_key:=coalesce(row_key,previous_key);
  ELSIF TG_TABLE_NAME='refresh_tokens' THEN session_key:=CASE WHEN TG_OP='DELETE' THEN OLD.session_id::text ELSE NEW.session_id::text END;
  END IF;
 END IF;
 IF TG_TABLE_NAME<>'mfa_amr_claims' THEN
  IF NOT(coalesce(actor=ANY(ids),false) OR coalesce(previous_actor=ANY(ids),false)) THEN RETURN NULL; END IF;
  IF TG_OP='UPDATE' AND actor IS DISTINCT FROM previous_actor THEN RAISE EXCEPTION 'metadata_actor_change'; END IF;
  ah:=encode(sha256(convert_to(coalesce(actor,previous_actor),'UTF8')),'hex');
 END IF;
 IF TG_OP='UPDATE' AND row_key IS DISTINCT FROM previous_key THEN RAISE EXCEPTION 'metadata_key_change'; END IF;
 IF NOT pg_try_advisory_xact_lock_shared(6110043,3) THEN RAISE EXCEPTION 'metadata_control_busy'; END IF;
 SELECT action_id,actor_sha INTO active_action,expected_actor FROM {s}.control WHERE singleton AND armed;
 IF active_action IS NULL OR ah IS DISTINCT FROM expected_actor THEN RAISE EXCEPTION 'metadata_action_not_armed'; END IF;
 row_key:=coalesce(row_key,previous_key);
 IF row_key IS NULL THEN RAISE EXCEPTION 'metadata_key_absent'; END IF;
 sh:=coalesce(sh,encode(sha256(convert_to(session_key,'UTF8')),'hex'));
 IF TG_TABLE_NAME='sessions' THEN
  INSERT INTO {s}.session_keys(key_sha,actor_sha) VALUES(sh,ah) ON CONFLICT(key_sha) DO NOTHING;
  IF NOT EXISTS(SELECT 1 FROM {s}.session_keys WHERE key_sha=sh AND actor_sha=ah) THEN RAISE EXCEPTION 'metadata_session_conflict'; END IF;
 END IF;
 IF (SELECT count(*) FROM {s}.events)>=512 THEN RAISE EXCEPTION 'metadata_event_budget'; END IF;
 INSERT INTO {s}.events(action_id,table_name,operation,xid,backend,key_sha,actor_sha,session_sha)
 VALUES(active_action,'auth.'||TG_TABLE_NAME,TG_OP,pg_current_xact_id()::text,pg_backend_pid(),encode(sha256(convert_to(row_key,'UTF8')),'hex'),ah,sh);
 RETURN NULL;
END"""

def install(run,ids,deadline):
    s=scope(run,ids);expiry=datetime.datetime.fromisoformat(deadline)
    if expiry.tzinfo is None:raise ValueError('audit_deadline')
    entries=','.join('('+g.literal(ids[r])+'::uuid,'+g.literal(g.ALIASES[r])+')' for r in g.ROLES)
    seed=','.join(g.literal(ids[r])+'::uuid' for r in g.ROLES)
    triggers='\n'.join(f'CREATE TRIGGER {s}_{i} AFTER INSERT OR UPDATE OR DELETE ON auth.{t} FOR EACH ROW EXECUTE FUNCTION {s}.observe();' for i,t in enumerate(TABLES))
    return f"""/* fmz6e11:auth_metadata_v1:install */
BEGIN; SET LOCAL lock_timeout='1s'; SET LOCAL statement_timeout='5s';
DO $install$ BEGIN
 IF {g.literal(deadline)}::timestamptz<=clock_timestamp() OR {g.literal(deadline)}::timestamptz>clock_timestamp()+interval '600 seconds' THEN RAISE EXCEPTION 'metadata_deadline'; END IF;
 IF NOT pg_try_advisory_xact_lock(6110043,2) THEN RAISE EXCEPTION 'metadata_busy'; END IF;
 IF EXISTS(SELECT 1 FROM pg_namespace WHERE left(nspname,{len(PREFIX)})='{PREFIX}') THEN RAISE EXCEPTION 'metadata_already_exists'; END IF;
 IF (SELECT count(*) FROM (VALUES {entries}) e(id,email) JOIN auth.users u ON u.id=e.id AND u.email=e.email AND NOT u.is_sso_user)<>3 THEN RAISE EXCEPTION 'metadata_identity_mismatch'; END IF;
 IF (SELECT count(*) FROM auth.sessions WHERE user_id IN ({seed}))>100 THEN RAISE EXCEPTION 'metadata_seed_budget'; END IF;
 CREATE SCHEMA {s}; REVOKE ALL ON SCHEMA {s} FROM PUBLIC,anon,authenticated,service_role;
 CREATE TABLE {s}.control(singleton boolean PRIMARY KEY CHECK(singleton),action_id uuid,actor_sha text,route text,armed boolean NOT NULL DEFAULT false);
 INSERT INTO {s}.control(singleton) VALUES(true);
 CREATE TABLE {s}.actions(action_id uuid PRIMARY KEY,actor_sha text NOT NULL,route text NOT NULL);
 CREATE TABLE {s}.session_keys(key_sha text PRIMARY KEY,actor_sha text NOT NULL);
 CREATE TABLE {s}.events(seq bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,action_id uuid NOT NULL,table_name text NOT NULL,operation text NOT NULL CHECK(operation IN ('INSERT','UPDATE','DELETE')),xid text NOT NULL,backend integer NOT NULL,key_sha text NOT NULL,actor_sha text NOT NULL,session_sha text,at timestamptz NOT NULL DEFAULT clock_timestamp());
 INSERT INTO {s}.session_keys SELECT encode(sha256(convert_to(id::text,'UTF8')),'hex'),encode(sha256(convert_to(user_id::text,'UTF8')),'hex') FROM auth.sessions WHERE user_id IN ({seed});
 ALTER TABLE {s}.control ENABLE ROW LEVEL SECURITY; ALTER TABLE {s}.actions ENABLE ROW LEVEL SECURITY;
 ALTER TABLE {s}.session_keys ENABLE ROW LEVEL SECURITY; ALTER TABLE {s}.events ENABLE ROW LEVEL SECURITY;
 CREATE POLICY auth_read ON {s}.control FOR SELECT TO supabase_auth_admin USING(true);
 CREATE POLICY auth_read ON {s}.session_keys FOR SELECT TO supabase_auth_admin USING(true);
 CREATE POLICY auth_append ON {s}.session_keys FOR INSERT TO supabase_auth_admin WITH CHECK(true);
 CREATE POLICY auth_read ON {s}.events FOR SELECT TO supabase_auth_admin USING(true);
 CREATE POLICY auth_append ON {s}.events FOR INSERT TO supabase_auth_admin WITH CHECK(true);
 GRANT USAGE ON SCHEMA {s} TO supabase_auth_admin;
 GRANT SELECT ON {s}.control TO supabase_auth_admin;
 GRANT SELECT,INSERT ON {s}.session_keys,{s}.events TO supabase_auth_admin;
 GRANT USAGE ON SEQUENCE {s}.events_seq_seq TO supabase_auth_admin;
 CREATE FUNCTION {s}.observe() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $body${function_body(s,ids,deadline)}$body$;
 REVOKE ALL ON FUNCTION {s}.observe() FROM PUBLIC,anon,authenticated,service_role,supabase_auth_admin;
 {triggers}
 COMMENT ON SCHEMA {s} IS {g.literal(json.dumps({'run':run,'expires_at':deadline,'version':1},separators=(',',':')))};
END $install$; COMMIT;"""

def arm(run,ids,action,role,route):
    s=scope(run,ids)
    if str(uuid.UUID(action))!=action or role not in ids or route not in ROUTES:raise ValueError('audit_action')
    ah=hashlib.sha256(ids[role].encode()).hexdigest()
    return f"""BEGIN; SET LOCAL lock_timeout='1s';
DO $arm$ BEGIN
 IF NOT pg_try_advisory_xact_lock(6110043,3) THEN RAISE EXCEPTION 'metadata_write_inflight'; END IF;
 IF NOT EXISTS(SELECT 1 FROM {s}.control WHERE singleton AND NOT armed FOR UPDATE NOWAIT) THEN RAISE EXCEPTION 'metadata_already_armed'; END IF;
 IF (obj_description('{s}'::regnamespace,'pg_namespace')::jsonb->>'expires_at')::timestamptz<=clock_timestamp() THEN RAISE EXCEPTION 'metadata_expired'; END IF;
 INSERT INTO {s}.actions VALUES('{action}','{ah}','{route}');
 UPDATE {s}.control SET action_id='{action}',actor_sha='{ah}',route='{route}',armed=true WHERE singleton;
END $arm$; COMMIT;"""

def disarm(run,ids,action):
    s=scope(run,ids)
    if str(uuid.UUID(action))!=action:raise ValueError('audit_action')
    return f"DO $close$ BEGIN IF NOT pg_try_advisory_xact_lock(6110043,3) THEN RAISE EXCEPTION 'metadata_write_inflight'; END IF; IF NOT EXISTS(SELECT 1 FROM {s}.control WHERE action_id='{action}' AND armed FOR UPDATE NOWAIT) THEN RAISE EXCEPTION 'metadata_wrong_action'; END IF; UPDATE {s}.control SET armed=false; END $close$;"

def events(run,ids,action):
    s=scope(run,ids)
    if str(uuid.UUID(action))!=action:raise ValueError('audit_action')
    return f"select coalesce(jsonb_agg(e order by e.seq),'[]')::text from (select seq,action_id,table_name,operation,xid,backend,key_sha,actor_sha,session_sha,at from {s}.events where action_id='{action}' order by seq limit 513) e"

def inspect(run,ids):
    s=scope(run,ids)
    return f"""select jsonb_build_object('schema','{s}','lease',obj_description(to_regnamespace('{s}'),'pg_namespace')::jsonb,
 'function_sha',(select encode(sha256(convert_to(pg_get_functiondef(p.oid),'UTF8')),'hex') from pg_proc p where p.oid=to_regprocedure('{s}.observe()')),
 'body_sha',(select encode(sha256(convert_to(prosrc,'UTF8')),'hex') from pg_proc where oid=to_regprocedure('{s}.observe()')),
 'secure_function',(select not prosecdef and proconfig=ARRAY['search_path=pg_catalog, pg_temp'] and proacl::text='{{postgres=X/postgres}}' from pg_proc where oid=to_regprocedure('{s}.observe()')),
 'function_count',(select count(*) from pg_proc where pronamespace=to_regnamespace('{s}')),
 'relations',(select coalesce(jsonb_agg(relname order by relname),'[]') from pg_class where relnamespace=to_regnamespace('{s}')),
 'triggers',(select coalesce(jsonb_agg(jsonb_build_object('name',tgname,'table',tgrelid::regclass::text,'sha',encode(sha256(convert_to(pg_get_triggerdef(oid),'UTF8')),'hex'),'enabled',tgenabled,'type',tgtype) order by tgname),'[]') from pg_trigger where tgfoid=to_regprocedure('{s}.observe()')),
 'dependencies',(select count(*) from pg_depend where refclassid='pg_proc'::regclass and refobjid=to_regprocedure('{s}.observe()')))::text"""

def validate(state,run,ids,deadline):
    s=scope(run,ids)
    if state.get('schema')!=s or state.get('lease')!={'run':run,'expires_at':deadline,'version':1}:raise ValueError('audit_lease')
    if not state.get('secure_function') or state['function_count']!=1 or state['relations']!=RELATIONS or state['dependencies']!=7:raise ValueError('audit_objects')
    if state['body_sha']!=hashlib.sha256(function_body(s,ids,deadline).encode()).hexdigest():raise ValueError('audit_source')
    if len(state['triggers'])!=7 or any(t['name']!=s+'_'+str(i) or t['table']!='auth.'+TABLES[i] or t['enabled']!='O' or t['type']!=29 for i,t in enumerate(state['triggers'])):raise ValueError('audit_triggers')
    return state

def remove(run,ids,receipt):
    s=scope(run,ids);validate(receipt,run,ids,receipt['lease']['expires_at'])
    if not re.fullmatch('[a-f0-9]{64}',receipt['function_sha']):raise ValueError('audit_hash')
    entries=','.join('('+g.literal(t['name'])+','+g.literal(t['table'])+','+g.literal(t['sha'])+')' for t in receipt['triggers'])
    expected=','.join(g.literal(x) for x in RELATIONS)
    return f"""BEGIN; SET LOCAL lock_timeout='1s'; SET LOCAL statement_timeout='5s';
DO $remove$ BEGIN
 IF (select count(*) from pg_proc where pronamespace=to_regnamespace('{s}'))<>1
 OR (select encode(sha256(convert_to(pg_get_functiondef(to_regprocedure('{s}.observe()')),'UTF8')),'hex')) IS DISTINCT FROM '{receipt['function_sha']}'
 OR (select count(*) from pg_depend where refclassid='pg_proc'::regclass and refobjid=to_regprocedure('{s}.observe()'))<>7
 OR (select array_agg(relname::text order by relname) from pg_class where relnamespace=to_regnamespace('{s}')) IS DISTINCT FROM ARRAY[{expected}]::text[]
 OR (select count(*) from (values {entries}) e(name,tbl,sha) join pg_trigger t on t.tgname=e.name and t.tgrelid=e.tbl::regclass and t.tgfoid=to_regprocedure('{s}.observe()') and encode(sha256(convert_to(pg_get_triggerdef(t.oid),'UTF8')),'hex')=e.sha)<>7
 THEN RAISE EXCEPTION 'metadata_removal_mismatch'; END IF;
 DROP FUNCTION {s}.observe() CASCADE;
 DROP TABLE {s}.events,{s}.session_keys,{s}.actions,{s}.control RESTRICT;
 DROP SCHEMA {s} RESTRICT;
END $remove$; COMMIT;"""
