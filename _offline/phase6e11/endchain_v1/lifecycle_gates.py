"""Read-only lifecycle gates. Technical metadata only, no hosted transport."""
import hashlib,json,os,re,subprocess,time
from quota_boundary import TARGET,CONSTRAINTS,VERSION

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
CATALOG=CATALOG.replace("(n.nspname in('public','auth') or n.nspname like 'fmz6e11%')",
    "(n.nspname not like 'pg_%' and n.nspname<>'information_schema')")

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
 (select count(*) from fmz6e11_private.participants where window_id=$3::uuid) participants,
 (select count(*) from fmz6e11_private.windows) all_test_windows,
 (select count(*) from fmz6e11_private.workspaces) all_test_workspaces,
 (select count(*) from fmz6e11_private.participants) all_test_participants,
 (select count(*) from auth.sessions where user_id in(select user_id from fmz6e11_private.identities)) all_registered_sessions,
 (select count(*) from auth.refresh_tokens where user_id::text in(select user_id::text from fmz6e11_private.identities)) all_registered_refresh_tokens"""

# Only fixed source fragments are renumbered; runtime values remain driver binds.
FINAL="""with final_access as ("""+ACCESS.replace('$1','$2')+"""),
 final_migrations as ("""+MIGRATIONS+"""),
 final_catalog as ("""+CATALOG+"""),
 final_absence as ("""+ABSENCE.replace('$1','$4')+""")
 select jsonb_build_object(
 'access',(select to_jsonb(a) from final_access a),
 'migrations',(select jsonb_agg(to_jsonb(m) order by version) from final_migrations m),
 'catalog',(select value from final_catalog),
 'absence',(select to_jsonb(a) from final_absence a),
 'temporary_schema_names',(select coalesce(jsonb_agg(nspname order by nspname),'[]')
   from pg_namespace where nspname=any($4::text[])),
 'readonly',current_setting('transaction_read_only')='on',
 'statement_timeout',current_setting('statement_timeout'),
 'lock_timeout',current_setting('lock_timeout')) value"""

def final_parameters(ids,context,stage):
    schemas=context['temporary_schemas']
    if stage not in ('pre','post') or len(schemas)!=2 or len(set(schemas))!=2:
        raise ValueError('final_schema_scope')
    guard=next((s for s in schemas if re.fullmatch('fmz6e11_guard_[a-f0-9]{32}',s)),None)
    audit=next((s for s in schemas if re.fullmatch('fmz6e11_am_[a-f0-9]{32}',s)),None)
    if not guard or not audit or guard[-32:]!=audit[-32:]:raise ValueError('final_schema_scope')
    return [list(schemas) if stage=='pre' else [],list(ids.values()),context['window'],list(schemas)]

def check_final(value,baseline,schemas,stage):
    if set(value)!=set(('access','migrations','catalog','absence','temporary_schema_names',
                       'readonly','statement_timeout','lock_timeout')) or stage not in ('pre','post'):
        raise ValueError('final_metadata_shape')
    if value['readonly'] is not True or value['statement_timeout'] not in ('5s','5000ms') or value['lock_timeout'] not in ('1s','1000ms'):
        raise ValueError('final_readonly_limits')
    check_access(value['access'])
    check_migrations(value['migrations'],baseline['migrations'])
    stable=lambda c:{k:v for k,v in c.items() if k!='m44'}
    if stable(value['catalog'])!=stable(baseline['catalog']):raise ValueError('ci_object_or_acl_drift')
    expected=sorted(schemas) if stage=='pre' else []
    if value['temporary_schema_names']!=expected or type(value['absence'].get('temporary_schemas')) is not int or value['absence']['temporary_schemas']!=len(expected):
        raise ValueError('final_temporary_schema_state')
    # PRE expects exactly our two schemas; all fixture/session fields stay zero.
    check_absence({**value['absence'],'temporary_schemas':0})

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def check_access(value):
    if set(value)!=set(('database_ok','role_ok','pg17','ssl','registered','private_functions_safe')) or any(v is not True for v in value.values()):
        raise ValueError('lifecycle_access_denied')

def check_absence(value):
    if set(value)!=set(('temporary_schemas','sessions','refresh_tokens','windows','workspaces','participants',
        'all_test_windows','all_test_workspaces','all_test_participants','all_registered_sessions','all_registered_refresh_tokens')) or any(type(v) is not int or v!=0 for v in value.values()):
        raise ValueError('lifecycle_cleanup_incomplete')

def check_migrations(rows,expected,pending=False):
    count,last=(44,'20261012185121') if pending else (45,VERSION)
    if len(rows)!=count or rows[-1]['version']!=last or any(not re.fullmatch('[a-f0-9]{64}',r['sql_sha']) for r in rows):
        raise ValueError('lifecycle_migration_identity')
    if expected is not None and rows!=expected:raise ValueError('lifecycle_migration_drift')

def ci_preflight(gate):
    """Actual four-command native preflight before the one-run quota boundary."""
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
        from history_pin import validate
        validate(migrations,runtime.environment)
        if (len(migrations),migrations[-1]['version']) not in ((44,'20261012185121'),(45,VERSION)):
            raise ValueError('preflight_quota_history')
    finally:
        if opened:query('ROLLBACK')
        connection.close()
        value={'commands':trace,'migrations':migrations,'hosted_calls':int(runtime.environment=='staging')}
        save(prefix+'integral-preflight.json',value)
    return value
