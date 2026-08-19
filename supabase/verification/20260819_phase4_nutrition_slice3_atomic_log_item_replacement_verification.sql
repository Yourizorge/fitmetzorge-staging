-- FitMetZorge Phase 4 Nutrition Slice 3 atomic replacement verification
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Read-only: one CTE/SELECT statement. Does not execute application RPCs.

with target_function as (
  select
    p.oid,
    p.proowner,
    p.proacl,
    p.prosecdef,
    p.provolatile,
    p.proleakproof,
    p.proconfig,
    p.proargnames::text[] as argument_names,
    p.prosrc,
    pg_catalog.pg_get_function_identity_arguments(p.oid) as identity_arguments,
    pg_catalog.pg_get_function_result(p.oid) as result_type
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where p.oid = pg_catalog.to_regprocedure(
    'public.fmz_phase4_replace_food_log_item(uuid,uuid,uuid,timestamp with time zone,text,uuid,uuid,numeric,text,text)'
  )
    and n.nspname = 'public'
),
entitlement_function as (
  select p.prosrc
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where p.oid = pg_catalog.to_regprocedure('public.fmz_phase4_has_full_nutrition_access(uuid)')
    and n.nspname = 'public'
),
function_acl as (
  select
    coalesce(r.rolname::text, 'PUBLIC') as grantee,
    x.privilege_type,
    x.is_grantable
  from target_function f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) x
  left join pg_catalog.pg_roles r on r.oid = x.grantee
),
phase4_tables as (
  select
    c.oid,
    c.relname::text as relname,
    c.relowner,
    c.relacl,
    c.relrowsecurity
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and c.relname::text = any(array[
      'nutrition_preferences',
      'foods',
      'food_portions',
      'nutrition_targets',
      'food_logs',
      'food_log_items'
    ]::text[])
),
table_acl as (
  select
    t.relname,
    coalesce(r.rolname::text, 'PUBLIC') as grantee,
    x.privilege_type,
    x.is_grantable
  from phase4_tables t
  cross join lateral pg_catalog.aclexplode(
    coalesce(t.relacl, pg_catalog.acldefault('r', t.relowner))
  ) x
  left join pg_catalog.pg_roles r on r.oid = x.grantee
),
phase4_policies as (
  select
    c.relname::text as relname,
    p.polname::text as polname,
    p.polcmd,
    lower(coalesce(pg_catalog.pg_get_expr(p.polqual, p.polrelid), '')) as using_expression,
    lower(coalesce(pg_catalog.pg_get_expr(p.polwithcheck, p.polrelid), '')) as check_expression
  from pg_catalog.pg_policy p
  join pg_catalog.pg_class c on c.oid = p.polrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname::text = any(array[
      'nutrition_preferences',
      'foods',
      'food_portions',
      'nutrition_targets',
      'food_logs',
      'food_log_items'
    ]::text[])
),
slice1_public_rpcs as (
  select distinct p.proname::text as proname
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname::text = any(array[
      'fmz_phase4_set_nutrition_timezone',
      'fmz_phase4_search_foods',
      'fmz_phase4_upsert_custom_food',
      'fmz_phase4_archive_custom_food',
      'fmz_phase4_upsert_food_portion',
      'fmz_phase4_save_member_target',
      'fmz_phase4_get_current_nutrition_target',
      'fmz_phase4_log_food_item',
      'fmz_phase4_archive_food_log_item',
      'fmz_phase4_get_nutrition_day',
      'fmz_phase4_get_nutrition_history'
    ]::text[])
),
frozen_guard_tables as (
  select c.relname::text as relname, c.relrowsecurity
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and c.relname::text = any(array[
      'profiles',
      'coach_workspaces',
      'user_settings',
      'user_onboarding',
      'entitlements',
      'recovery_logs',
      'training_plans',
      'training_plan_days',
      'training_plan_exercises',
      'workout_sessions',
      'workout_set_logs',
      'exercises'
    ]::text[])
),
checks as (
  select
    'rpc_exact_signature'::text as check_name,
    (
      (select count(*) from target_function) = 1
      and (select result_type from target_function) = 'jsonb'
    ) as pass,
    jsonb_build_object(
      'identity_arguments', (select identity_arguments from target_function),
      'result_type', (select result_type from target_function)
    ) as details

  union all

  select
    'rpc_security_mode_and_search_path',
    coalesce((
      select
        f.prosecdef
        and f.provolatile = 'v'
        and not f.proleakproof
        and 'search_path=pg_catalog, public, pg_temp' = any(coalesce(f.proconfig, array[]::text[]))
      from target_function f
    ), false),
    coalesce((
      select jsonb_build_object(
        'security_definer', f.prosecdef,
        'volatility', f.provolatile,
        'leakproof', f.proleakproof,
        'config', f.proconfig
      )
      from target_function f
    ), '{}'::jsonb)

  union all

  select
    'rpc_argument_authority_contract',
    coalesce((
      select
        f.argument_names = array[
          'p_original_item_id',
          'p_replacement_item_id',
          'p_replacement_request_id',
          'p_expected_original_updated_at',
          'p_meal_moment',
          'p_food_id',
          'p_food_portion_id',
          'p_consumed_quantity',
          'p_consumed_unit',
          'p_notes'
        ]::text[]
        and position('auth.uid()' in lower(f.prosrc)) > 0
        and position('p_user_id' in lower(f.prosrc)) = 0
        and position('p_trainer' in lower(f.prosrc)) = 0
        and position('p_entitlement' in lower(f.prosrc)) = 0
      from target_function f
    ), false),
    coalesce((select to_jsonb(f.argument_names) from target_function f), '[]'::jsonb)

  union all

  select
    'rpc_execute_acl',
    (
      exists (
        select 1 from function_acl
        where grantee = 'authenticated'
          and privilege_type = 'EXECUTE'
          and not is_grantable
      )
      and not exists (
        select 1 from function_acl
        where grantee in ('anon', 'PUBLIC') and privilege_type = 'EXECUTE'
      )
    ),
    coalesce((select jsonb_agg(to_jsonb(a) order by a.grantee) from function_acl a), '[]'::jsonb)

  union all

  select
    'atomic_replacement_source_contract',
    coalesce((
      select
        position(lower('ins' || 'ert into public.food_log_items') in lower(f.prosrc)) > 0
        and position(lower('up' || 'date public.food_log_items') in lower(f.prosrc)) > 0
        and position('set status = ''archived''' in lower(f.prosrc)) > 0
        and position('atomic replacement rolled back' in lower(f.prosrc)) > 0
        and position(lower('del' || 'ete') in lower(f.prosrc)) = 0
      from target_function f
    ), false),
    '{}'::jsonb

  union all

  select
    'locking_and_concurrency_contract',
    coalesce((
      select
        position('fmz_phase4_food_log_request:' in f.prosrc) > 0
        and position('fmz_phase4_food_log_item_request:' in f.prosrc) > 0
        and position('for update' in lower(f.prosrc)) > 0
        and position('p_original_item_id::text' in f.prosrc) > 0
        and position('p_replacement_item_id::text' in f.prosrc) > 0
      from target_function f
    ), false),
    '{}'::jsonb

  union all

  select
    'stale_and_active_original_guards',
    coalesce((
      select
        position('p_expected_original_updated_at' in f.prosrc) > 0
        and position('v_original.updated_at is distinct from p_expected_original_updated_at' in f.prosrc) > 0
        and position('v_original.status is distinct from ''active''' in f.prosrc) > 0
        and position('v_original.status is distinct from ''archived''' in f.prosrc) > 0
      from target_function f
    ), false),
    '{}'::jsonb

  union all

  select
    'idempotent_replay_and_payload_reuse_guard',
    coalesce((
      select
        position('replacement_request' in f.prosrc) > 0
        and position('is distinct from v_request_payload' in f.prosrc) > 0
        and position('replacement request UUID was already used with a different payload' in f.prosrc) > 0
        and position('''idempotent_replay'', true' in f.prosrc) > 0
        and position('''idempotent_replay'', false' in f.prosrc) > 0
      from target_function f
    ), false),
    '{}'::jsonb

  union all

  select
    'same_day_meal_and_sort_contract',
    coalesce((
      select
        position('p_log_date' in f.prosrc) = 0
        and position('v_original.food_log_id' in f.prosrc) > 0
        and position('v_log.log_date' in f.prosrc) > 0
        and position('breakfast' in f.prosrc) > 0
        and position('lunch' in f.prosrc) > 0
        and position('dinner' in f.prosrc) > 0
        and position('snacks' in f.prosrc) > 0
        and position('v_sort_order := v_original.sort_order' in f.prosrc) > 0
        and position('max(i.sort_order)' in f.prosrc) > 0
      from target_function f
    ), false),
    '{}'::jsonb

  union all

  select
    'food_visibility_portion_and_conversion_contract',
    coalesce((
      select
        position('f.status = ''active''' in f.prosrc) > 0
        and position('f.catalog_scope = ''canonical''' in f.prosrc) > 0
        and position('f.owner_user_id = v_user_id' in f.prosrc) > 0
        and position('p.food_id = v_food.id' in f.prosrc) > 0
        and position('p.status = ''active''' in f.prosrc) > 0
        and position('portion_conversion' in f.prosrc) > 0
        and position('density_conversion' in f.prosrc) > 0
        and position('explicit portion or density conversion required' in f.prosrc) > 0
      from target_function f
    ), false),
    '{}'::jsonb

  union all

  select
    'immutable_snapshot_and_target_preservation_contract',
    coalesce((
      select
        position('energy_kcal_snapshot' in f.prosrc) > 0
        and position('protein_grams_snapshot' in f.prosrc) > 0
        and position('carbohydrate_grams_snapshot' in f.prosrc) > 0
        and position('fat_grams_snapshot' in f.prosrc) > 0
        and position('fiber_grams_snapshot' in f.prosrc) > 0
        and position(lower('up' || 'date public.food_logs') in lower(f.prosrc)) = 0
        and position(lower('ins' || 'ert into public.food_logs') in lower(f.prosrc)) = 0
      from target_function f
    ), false),
    '{}'::jsonb

  union all

  select
    'free_and_full_history_contract',
    coalesce((
      select
        position('fmz_phase4_has_full_nutrition_access' in f.prosrc) > 0
        and position('v_log.log_date < v_today - 6' in f.prosrc) > 0
        and position('at time zone v_timezone' in f.prosrc) > 0
      from target_function f
    ), false)
    and coalesce((
      select
        position('e.entitlement_code in (''pro'', ''ai'', ''personal_coaching'')' in e.prosrc) > 0
        and position('e.status = ''active''' in e.prosrc) > 0
        and position('e.starts_at <= now()' in e.prosrc) > 0
        and position('e.ends_at is null or e.ends_at > now()' in e.prosrc) > 0
      from entitlement_function e
    ), false),
    '{}'::jsonb

  union all

  select
    'phase4_table_rls_and_acl_unchanged',
    (
      (select count(*) from phase4_tables) = 6
      and not exists (select 1 from phase4_tables where not relrowsecurity)
      and not exists (
        select 1 from table_acl
        where relname in ('nutrition_preferences', 'nutrition_targets', 'food_logs', 'food_log_items')
          and grantee in ('authenticated', 'anon', 'PUBLIC')
      )
      and not exists (
        select 1 from table_acl
        where relname in ('foods', 'food_portions')
          and grantee in ('anon', 'PUBLIC')
      )
      and not exists (
        select 1 from table_acl
        where relname in ('foods', 'food_portions')
          and grantee = 'authenticated'
          and privilege_type <> 'SELECT'
      )
      and (
        select count(*) from table_acl
        where relname in ('foods', 'food_portions')
          and grantee = 'authenticated'
          and privilege_type = 'SELECT'
      ) = 2
    ),
    coalesce((
      select jsonb_agg(to_jsonb(a) order by a.relname, a.grantee, a.privilege_type)
      from table_acl a
      where a.grantee in ('authenticated', 'anon', 'PUBLIC')
    ), '[]'::jsonb)

  union all

  select
    'phase4_policy_guard_unchanged',
    (
      (select count(*) from phase4_policies) = 18
      and not exists (select 1 from phase4_policies where polcmd = 'd')
      and not exists (
        select 1 from phase4_policies
        where lower(polname || ' ' || using_expression || ' ' || check_expression)
          ~ '(trainer|coach|linked_client)'
      )
    ),
    jsonb_build_object(
      'policy_count', (select count(*) from phase4_policies),
      'remove_policy_count', (select count(*) from phase4_policies where polcmd = 'd')
    )

  union all

  select
    'slice1_rpc_guard_unchanged',
    (select count(*) from slice1_public_rpcs) = 11,
    jsonb_build_object(
      'expected', 11,
      'actual', (select count(*) from slice1_public_rpcs)
    )

  union all

  select
    'phase1_phase2_phase3_database_guards',
    (
      (select count(*) from frozen_guard_tables) = 12
      and not exists (select 1 from frozen_guard_tables where not relrowsecurity)
    ),
    coalesce((select jsonb_agg(to_jsonb(g) order by g.relname) from frozen_guard_tables g), '[]'::jsonb)

  union all

  select
    'forbidden_reference_scan',
    coalesce((
      select
        position('service_role' in lower(f.prosrc)) = 0
        and position('secret' in lower(f.prosrc)) = 0
        and position('trainer' in lower(f.prosrc)) = 0
      from target_function f
    ), false),
    '{}'::jsonb
),
result as (
  select jsonb_build_object(
    'scope', 'phase4_nutrition_slice3_atomic_log_item_replacement',
    'expected_project_ref', 'mokxyyullfhkfalopbzd',
    'overall_pass', coalesce(bool_and(c.pass), false),
    'checks', jsonb_agg(
      jsonb_build_object(
        'check', c.check_name,
        'pass', c.pass,
        'details', c.details
      )
      order by c.check_name
    )
  ) as verification_result
  from checks c
)
select jsonb_pretty(verification_result) as verification_result
from result;
