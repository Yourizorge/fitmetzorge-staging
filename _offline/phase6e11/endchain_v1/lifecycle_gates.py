"""Read-only lifecycle gates. Technical metadata only, no hosted transport."""
import hashlib,json,re

CATALOG="""select jsonb_build_object(
 'functions',(select coalesce(jsonb_object_agg(p.oid::text,jsonb_build_object(
   'hash',encode(sha256(convert_to(pg_get_functiondef(p.oid),'UTF8')),'hex'),
   'owner',p.proowner,'acl',p.proacl,'path',p.proconfig,'definer',p.prosecdef)),'{}')
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where p.prokind in('f','p') and (n.nspname in('public','auth') or n.nspname like 'fmz6e11%')
     and n.nspname<>all($1::text[])),
 'relations',(select coalesce(jsonb_object_agg(c.oid::text,jsonb_build_object('schema',n.nspname,
   'name',c.relname,'owner',c.relowner,'acl',c.relacl,'rls',c.relrowsecurity,'force',c.relforcerowsecurity)),'{}')
   from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where (n.nspname in('public','auth') or n.nspname like 'fmz6e11%') and n.nspname<>all($1::text[])),
 'triggers',(select coalesce(jsonb_object_agg(t.oid::text,encode(sha256(convert_to(pg_get_triggerdef(t.oid)||t.tgenabled,'UTF8')),'hex')),'{}')
   from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace
   join pg_proc p on p.oid=t.tgfoid join pg_namespace f on f.oid=p.pronamespace
   where (n.nspname in('public','auth') or n.nspname like 'fmz6e11%') and f.nspname<>all($1::text[])),
 'policies',(select coalesce(jsonb_object_agg(p.oid::text,to_jsonb(p)),'{}') from pg_policy p
   join pg_class c on c.oid=p.polrelid join pg_namespace n on n.oid=c.relnamespace
   where (n.nspname in('public','auth') or n.nspname like 'fmz6e11%') and n.nspname<>all($1::text[]))) value"""

MIGRATIONS="""select version,name,encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex') sql_sha
 from supabase_migrations.schema_migrations order by version"""

ACCESS="""select current_database()='postgres' database_ok,current_user='postgres' role_ok,
 current_setting('server_version_num')::integer between 170000 and 179999 pg17,
 (select ssl from pg_stat_ssl where pid=pg_backend_pid()) ssl,
 (select count(*)=3 from fmz6e11_private.identities where user_id=any($1::uuid[]) and enabled) registered,
 (select not exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  cross join (values('anon'),('authenticated'),('service_role')) roles(name)
  where n.nspname in('fmz6e11_audit_private','fmz6e11_request_private','fmz6e11_controller_private')
   and (p.prosecdef or p.proconfig is distinct from array['search_path=pg_catalog, pg_temp']
       or has_function_privilege(roles.name,p.oid,'EXECUTE')))) private_functions_safe"""

ABSENCE="""select
 (select count(*) from pg_namespace where nspname=any($1::text[])) temporary_schemas,
 (select count(*) from auth.sessions where user_id=any($2::uuid[])) sessions,
 (select count(*) from auth.refresh_tokens where user_id::text=any($2::text[])) refresh_tokens,
 (select count(*) from fmz6e11_private.windows where id=$3::uuid) windows,
 (select count(*) from fmz6e11_private.workspaces where window_id=$3::uuid) workspaces,
 (select count(*) from fmz6e11_private.participants where window_id=$3::uuid) participants"""

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def check_access(value):
    if set(value)!=set(('database_ok','role_ok','pg17','ssl','registered','private_functions_safe')) or any(v is not True for v in value.values()):
        raise ValueError('lifecycle_access_denied')

def check_absence(value):
    if set(value)!=set(('temporary_schemas','sessions','refresh_tokens','windows','workspaces','participants')) or any(type(v) is not int or v!=0 for v in value.values()):
        raise ValueError('lifecycle_cleanup_incomplete')

def check_migrations(rows,expected):
    if len(rows)!=44 or rows[-1]['version']!='20261012185121' or any(not re.fullmatch('[a-f0-9]{64}',r['sql_sha']) for r in rows):
        raise ValueError('lifecycle_migration_identity')
    if expected is not None and rows!=expected:raise ValueError('lifecycle_migration_drift')

