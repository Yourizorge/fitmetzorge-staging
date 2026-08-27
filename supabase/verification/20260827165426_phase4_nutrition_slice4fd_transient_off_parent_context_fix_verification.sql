-- FitMetZorge Phase 4 Nutrition - Slice 4F-D transient OFF parent context fix
-- Read-only verifier: one SELECT/CTE, no application RPC execution.

with function_catalog as (
  select
    p.oid,
    p.proowner,
    n.nspname::text as schema_name,
    p.proname::text as function_name,
    pg_catalog.pg_get_function_identity_arguments(p.oid) as identity_arguments,
    p.prosecdef,
    p.provolatile,
    p.proacl,
    pg_catalog.pg_get_functiondef(p.oid) as definition,
    pg_catalog.array_to_string(p.proconfig, ',') as configuration
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname in (
      'fmz_phase4_enforce_food_log_owner',
      'fmz_phase4_enforce_food_log_item_owner',
      'fmz_phase4_transient_off_food_item_mutation',
      'fmz_phase4_log_transient_off_food_item',
      'fmz_phase4_replace_transient_off_food_item'
    )
), function_acl as (
  select
    f.function_name,
    f.identity_arguments,
    coalesce(r.rolname, 'PUBLIC')::text as grantee,
    a.privilege_type::text
  from function_catalog f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) a
  left join pg_catalog.pg_roles r on r.oid = a.grantee
), trigger_catalog as (
  select
    t.tgname::text as trigger_name,
    t.tgenabled,
    p.proname::text as function_name
  from pg_catalog.pg_trigger t
  join pg_catalog.pg_proc p on p.oid = t.tgfoid
  where t.tgrelid = 'public.food_logs'::regclass
    and not t.tgisinternal
), table_guard as (
  select
    c.relname::text as table_name,
    c.relrowsecurity
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname in (
      'nutrition_preferences', 'foods', 'food_portions',
      'nutrition_targets', 'food_logs', 'food_log_items',
      'nutrition_off_catalog_releases', 'nutrition_off_products',
      'nutrition_off_product_names', 'nutrition_provider_food_cache',
      'nutrition_provider_rate_buckets', 'nutrition_provider_runtime_state'
    )
), checks as (
  select 'owner_guard_exists_and_hardened'::text as check_name,
    exists (
      select 1 from function_catalog f
      where f.function_name = 'fmz_phase4_enforce_food_log_owner'
        and f.identity_arguments = ''
        and f.prosecdef
        and f.configuration like '%search_path=pg_catalog, public, pg_temp%'
    ) as pass
  union all
  select 'owner_guard_accepts_transient_context', exists (
    select 1 from function_catalog f
    where f.function_name = 'fmz_phase4_enforce_food_log_owner'
      and position('fmz.phase4_transient_off_snapshot_user_id' in f.definition) > 0
      and position('v_transient_off_user_id is distinct from v_user_id' in f.definition) > 0
      and position('new.user_id is distinct from v_user_id' in f.definition) > 0
  )
  union all
  select 'owner_guard_preserves_member_and_provider_contexts', exists (
    select 1 from function_catalog f
    where f.function_name = 'fmz_phase4_enforce_food_log_owner'
      and position('auth.uid()' in f.definition) > 0
      and position('fmz.phase4_provider_snapshot_user_id' in f.definition) > 0
      and position('member food log source is fixed server-side' in f.definition) > 0
      and position('food log identity and target snapshots are immutable' in f.definition) > 0
  )
  union all
  select 'food_log_owner_trigger_active', exists (
    select 1 from trigger_catalog t
    where t.function_name = 'fmz_phase4_enforce_food_log_owner'
      and t.tgenabled <> 'D'
  )
  union all
  select 'transient_log_wrapper_hardened', exists (
    select 1 from function_catalog f
    where f.function_name = 'fmz_phase4_log_transient_off_food_item'
      and f.prosecdef
      and f.provolatile = 'v'
      and f.configuration like '%search_path=pg_catalog, public, pg_temp%'
  )
  union all
  select 'transient_context_set_before_mutation', exists (
    select 1 from function_catalog f
    where f.function_name = 'fmz_phase4_log_transient_off_food_item'
      and position('fmz.phase4_transient_off_snapshot_user_id' in f.definition) > 0
      and position('fmz.phase4_transient_off_snapshot_user_id' in f.definition)
          < position('fmz_phase4_transient_off_food_item_mutation' in f.definition)
      and position('true' in f.definition) > 0
  )
  union all
  select 'transient_log_wrapper_service_role_only',
    exists (
      select 1 from function_acl a
      where a.function_name = 'fmz_phase4_log_transient_off_food_item'
        and a.grantee = 'service_role'
        and a.privilege_type = 'EXECUTE'
    )
    and not exists (
      select 1 from function_acl a
      where a.function_name = 'fmz_phase4_log_transient_off_food_item'
        and a.grantee in ('PUBLIC', 'anon', 'authenticated')
        and a.privilege_type = 'EXECUTE'
    )
  union all
  select 'trigger_functions_not_directly_executable', not exists (
    select 1 from function_acl a
    where a.function_name in (
      'fmz_phase4_enforce_food_log_owner',
      'fmz_phase4_enforce_food_log_item_owner'
    )
      and a.grantee in ('PUBLIC', 'anon', 'authenticated', 'service_role')
      and a.privilege_type = 'EXECUTE'
  )
  union all
  select 'transient_mutation_contract_preserved', exists (
    select 1 from function_catalog f
    where f.function_name = 'fmz_phase4_transient_off_food_item_mutation'
      and position('fmz_phase4_validate_transient_off_candidate' in f.definition) > 0
      and position('transient OFF quantity unit must match its nutrition basis' in f.definition) > 0
      and position('transient OFF request UUID was reused with a different payload' in f.definition) > 0
      and position('historical food log item snapshots are immutable' in (
        select i.definition from function_catalog i
        where i.function_name = 'fmz_phase4_enforce_food_log_item_owner'
        limit 1
      )) > 0
  )
  union all
  select 'replace_wrapper_frozen_and_service_role_only',
    exists (
      select 1 from function_catalog f
      where f.function_name = 'fmz_phase4_replace_transient_off_food_item'
        and f.prosecdef
        and f.configuration like '%search_path=pg_catalog, public, pg_temp%'
    )
    and exists (
      select 1 from function_acl a
      where a.function_name = 'fmz_phase4_replace_transient_off_food_item'
        and a.grantee = 'service_role'
        and a.privilege_type = 'EXECUTE'
    )
    and not exists (
      select 1 from function_acl a
      where a.function_name = 'fmz_phase4_replace_transient_off_food_item'
        and a.grantee in ('PUBLIC', 'anon', 'authenticated')
        and a.privilege_type = 'EXECUTE'
    )
  union all
  select 'frozen_tables_present_with_rls',
    (select count(*) from table_guard) = 12
    and not exists (select 1 from table_guard where not relrowsecurity)
  union all
  select 'no_delete_or_trainer_policy_expansion', not exists (
    select 1
    from pg_catalog.pg_policy p
    join pg_catalog.pg_class c on c.oid = p.polrelid
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname in ('food_logs', 'food_log_items')
      and (
        p.polcmd = 'd'
        or lower(p.polname) like '%trainer%'
        or lower(p.polname) like '%coach%'
      )
  )
), result as (
  select
    count(*)::integer as check_count,
    count(*) filter (where pass)::integer as pass_count,
    count(*) filter (where not pass)::integer as fail_count,
    bool_and(pass) as overall_pass,
    jsonb_agg(
      jsonb_build_object(
        'check', check_name,
        'pass', pass,
        'result', case when pass then 'PASS' else 'FAIL' end
      ) order by check_name
    ) as checks
  from checks
)
select jsonb_build_object(
  'overall_pass', overall_pass,
  'check_count', check_count,
  'pass_count', pass_count,
  'fail_count', fail_count,
  'checks', checks
) as verification_result
from result;
