with function_meta as (
  select
    p.oid,
    p.prosecdef,
    p.provolatile,
    p.proconfig,
    pg_get_function_identity_arguments(p.oid) as identity_arguments,
    lower(pg_get_functiondef(p.oid)) as definition
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname = 'fmz_phase5_set_unit_system'
), function_acl as (
  select
    coalesce(bool_or(e.grantee = 0 and e.privilege_type = 'EXECUTE'), false) as public_execute,
    coalesce(bool_or(r.rolname = 'anon' and e.privilege_type = 'EXECUTE'), false) as anon_execute,
    coalesce(bool_or(r.rolname = 'authenticated' and e.privilege_type = 'EXECUTE'), false) as authenticated_execute
  from function_meta f
  join pg_proc p on p.oid = f.oid
  left join lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) e on true
  left join pg_roles r on r.oid = e.grantee
), constraint_meta as (
  select
    c.convalidated,
    lower(pg_get_constraintdef(c.oid, true)) as definition
  from pg_constraint c
  join pg_class t on t.oid = c.conrelid
  join pg_namespace n on n.oid = t.relnamespace
  where n.nspname = 'public'
    and t.relname = 'user_settings'
    and c.conname = 'user_settings_unit_system_check'
    and c.contype = 'c'
), column_meta as (
  select data_type, is_nullable, column_default
  from information_schema.columns
  where table_schema = 'public'
    and table_name = 'user_settings'
    and column_name = 'unit_system'
), table_meta as (
  select c.relrowsecurity
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname = 'user_settings'
    and c.relkind = 'r'
), policy_meta as (
  select
    count(*) filter (where cmd = 'SELECT' and qual like '%auth.uid()%') as own_select,
    count(*) filter (where cmd = 'INSERT' and with_check like '%auth.uid()%') as own_insert,
    count(*) filter (where cmd = 'UPDATE' and qual like '%auth.uid()%' and with_check like '%auth.uid()%') as own_update
  from pg_policies
  where schemaname = 'public'
    and tablename = 'user_settings'
), checks as (
  select 'column_contract'::text as check_name,
    exists (select 1 from column_meta where data_type = 'text' and is_nullable = 'NO' and column_default = '''metric''::text') as pass
  union all
  select 'validated_metric_imperial_constraint',
    (select count(*) = 1 and bool_and(convalidated and definition like '%unit_system%' and definition like '%metric%' and definition like '%imperial%') from constraint_meta)
  union all
  select 'existing_values_supported',
    not exists (select 1 from public.user_settings where unit_system not in ('metric', 'imperial'))
  union all
  select 'setter_signature_and_security',
    (select count(*) = 1 and bool_and(identity_arguments = 'p_unit_system text' and prosecdef and provolatile = 'v') from function_meta)
  union all
  select 'setter_safe_search_path',
    (select count(*) = 1 and bool_and(proconfig @> array['search_path=pg_catalog, public, pg_temp']::text[]) from function_meta)
  union all
  select 'setter_ownership_and_allowlist',
    (select count(*) = 1 and bool_and(definition like '%auth.uid()%' and definition like '%metric%' and definition like '%imperial%' and definition not like '%p_user%') from function_meta)
  union all
  select 'setter_acl',
    (select authenticated_execute and not anon_execute and not public_execute from function_acl)
  union all
  select 'user_settings_rls',
    coalesce((select relrowsecurity from table_meta), false)
  union all
  select 'own_user_policies',
    (select own_select >= 1 and own_insert >= 1 and own_update >= 1 from policy_meta)
), result as (
  select jsonb_build_object(
    'scope', 'phase5_unit_system_constraint_fix',
    'project_ref', 'mokxyyullfhkfalopbzd',
    'overall_pass', bool_and(pass),
    'pass_count', count(*) filter (where pass),
    'fail_count', count(*) filter (where not pass),
    'checks', jsonb_agg(jsonb_build_object('check', check_name, 'pass', pass) order by check_name)
  ) as verification_result
  from checks
)
select verification_result from result;
