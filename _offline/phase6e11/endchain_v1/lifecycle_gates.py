"""Read-only lifecycle gates. Technical metadata only, no hosted transport."""
import hashlib,json,os,re,subprocess,time
from migration_boundary import TARGET,CONSTRAINTS

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
 'triggers',(select coalesce(jsonb_object_agg(t.oid::text,encode(sha256(convert_to(pg_get_triggerdef(t.oid)||t.tgenabled::text,'UTF8')),'hex')),'{}')
   from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace
   join pg_proc p on p.oid=t.tgfoid join pg_namespace f on f.oid=p.pronamespace
   where (n.nspname in('public','auth') or n.nspname like 'fmz6e11%') and f.nspname<>all($1::text[])),
 'policies',(select coalesce(jsonb_object_agg(p.oid::text,to_jsonb(p)),'{}') from pg_policy p
   join pg_class c on c.oid=p.polrelid join pg_namespace n on n.oid=c.relnamespace
   where (n.nspname in('public','auth') or n.nspname like 'fmz6e11%') and n.nspname<>all($1::text[])),
 'constraints',"""+CONSTRAINTS+", 'm44',"+TARGET+") value"

MIGRATIONS="""select version,name,encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex') sql_sha
 from supabase_migrations.schema_migrations order by version"""

ACCESS="""select current_database()='postgres' database_ok,current_user='postgres' role_ok,
 current_setting('server_version_num')::integer between 170000 and 179999 pg17,
 (select ssl from pg_stat_ssl where pid=pg_backend_pid()) ssl,
 (select count(*)=3 and bool_and(i.enabled and u.email=case i.role
   when 'a_member' then 'zorgeyouri+6e9-a-lid@gmail.com' when 'a_trainer' then 'zorgeyouri+6e9-a-trainer@gmail.com'
   when 'b_member' then 'zorgeyouri+6e9-b-lid@gmail.com' else '' end
   and u.email_confirmed_at is not null and p.email=u.email
   and p.role=case when i.role='a_trainer' then 'trainer' else 'client' end
   and case when i.role='a_member' then p.trainer_id=(select user_id from fmz6e11_private.identities where role='a_trainer' and user_id=any($1::uuid[])) else p.trainer_id is null end
   and case when i.role='a_trainer' then o.enabled is true else o.user_id is null end)
   and count(distinct i.role)=3
  from fmz6e11_private.identities i join auth.users u on u.id=i.user_id join public.profiles p on p.id=i.user_id
  left join fmz6e11_private.operators o on o.user_id=i.user_id where i.user_id=any($1::uuid[])) registered,
 (select not exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  cross join (values('anon'),('authenticated'),('service_role')) roles(name)
  where n.nspname in('fmz6e11_audit_private','fmz6e11_request_private','fmz6e11_controller_private')
   and ((p.prosecdef and p.oid<>to_regprocedure('fmz6e11_audit_private.observe()'))
       or pg_get_userbyid(p.proowner)<>'postgres'
       or p.proconfig is distinct from array['search_path=pg_catalog, pg_temp']
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

def check_migrations(rows,expected,pending=False):
    count,last=(43,'20261012104331') if pending else (44,'20261012185121')
    if len(rows)!=count or rows[-1]['version']!=last or any(not re.fullmatch('[a-f0-9]{64}',r['sql_sha']) for r in rows):
        raise ValueError('lifecycle_migration_identity')
    if expected is not None and rows!=expected:raise ValueError('lifecycle_migration_drift')

def ci_preflight(gate):
    """Actual four-command native preflight immediately before candidate M44."""
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging':raise RuntimeError('ci_only')
    from native_runtime import NativeRuntime
    return preflight(NativeRuntime.disposable(gate),gate.save,getattr(gate,'cli_namespace',''))

def preflight(runtime,save,prefix=''):
    """Same four-command identity/history gate in CI and exact staging."""
    from integral_stream import GUARD
    from sql_protocol import statements
    connection=runtime.connect();trace=[];migrations=[];opened=False
    def query(sql):
        trace.append({'sql_sha256':statements(sql)[0]['sha256'],'confirmed':False})
        started=time.monotonic();cursor=connection.execute(sql);rows=cursor.fetchall() if cursor.description else []
        trace[-1].update(confirmed=True,duration_ms=round(1000*(time.monotonic()-started)));return rows
    try:
        query('BEGIN TRANSACTION READ ONLY');opened=True
        identity=query(GUARD)[0]
        if identity['ro']!='on' or identity['db']!='postgres' or identity['role']!='postgres' or identity['ssl'] is not True:
            raise ValueError('preflight_identity')
        if runtime.environment=='staging' and identity['instance_sha']!='d165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15':
            raise ValueError('preflight_wrong_project_instance')
        migrations=query(MIGRATIONS)
        if len(migrations)!=43 or migrations[-1]['version']!='20261012104331':raise ValueError('preflight_not_43')
    finally:
        if opened:query('ROLLBACK')
        connection.close()
        value={'commands':trace,'migrations':migrations,'hosted_calls':0}
        save(prefix+'integral-preflight.json',value)
    return value
