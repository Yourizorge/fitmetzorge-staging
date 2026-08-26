-- FitMetZorge Phase 4 Package 4F-C OFF authoritative logging verification
-- One read-only SELECT/CTE. It does not invoke application RPCs or mutate data.

with expected_functions(signature, expected_security_definer, expected_volatility) as (
  values
    ('public.fmz_phase4_resolve_off_food_snapshot(uuid)', true, 's'),
    ('public.fmz_phase4_log_off_food_item(uuid,uuid,date,text,smallint,text,uuid,numeric,text,text,timestamp with time zone)', true, 'v'),
    ('public.fmz_phase4_replace_off_food_log_item(uuid,uuid,uuid,timestamp with time zone,text,uuid,numeric,text,text)', true, 'v'),
    ('public.fmz_phase4_enforce_food_log_item_owner()', true, 'v')
),
function_catalog as (
  select
    e.signature,
    p.oid,
    p.prosecdef,
    p.provolatile::text as provolatile,
    coalesce(p.proconfig, '{}'::text[]) as proconfig,
    lower(pg_catalog.regexp_replace(pg_catalog.pg_get_functiondef(p.oid), '[[:space:]]+', '', 'g')) as compact_definition
  from expected_functions e
  left join pg_catalog.pg_proc p on p.oid = pg_catalog.to_regprocedure(e.signature)
),
function_acl as (
  select
    p.oid,
    case when a.grantee = 0 then 'PUBLIC' else r.rolname end as grantee,
    a.privilege_type
  from pg_catalog.pg_proc p
  cross join lateral pg_catalog.aclexplode(
    coalesce(p.proacl, pg_catalog.acldefault('f', p.proowner))
  ) a
  left join pg_catalog.pg_roles r on r.oid = a.grantee
  where p.oid in (select oid from function_catalog where oid is not null)
),
table_state as (
  select c.relname, c.relrowsecurity
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname in (
      'nutrition_off_catalog_releases', 'nutrition_off_products',
      'nutrition_off_product_names', 'foods', 'food_portions',
      'nutrition_preferences', 'nutrition_targets', 'food_logs',
      'food_log_items', 'food_aliases', 'nutrition_food_ingestions',
      'profiles', 'coach_workspaces', 'user_settings', 'user_onboarding',
      'entitlements', 'recovery_logs', 'training_plans'
    )
),
policy_state as (
  select tablename, policyname, cmd
  from pg_catalog.pg_policies
  where schemaname = 'public'
    and tablename in ('food_logs', 'food_log_items', 'nutrition_off_products')
),
trigger_state as (
  select t.tgname, p.proname
  from pg_catalog.pg_trigger t
  join pg_catalog.pg_class c on c.oid = t.tgrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  join pg_catalog.pg_proc p on p.oid = t.tgfoid
  where not t.tgisinternal
    and n.nspname = 'public'
    and c.relname = 'food_log_items'
),
definitions as (
  select
    max(compact_definition) filter (where signature like '%resolve_off_food_snapshot%') as resolver_def,
    max(compact_definition) filter (where signature like '%log_off_food_item%') as log_def,
    max(compact_definition) filter (where signature like '%replace_off_food_log_item%') as replace_def,
    max(compact_definition) filter (where signature like '%enforce_food_log_item_owner%') as guard_def
  from function_catalog
),
checks(check_name, passed, details) as (
  select 'functions_exist', count(*) = 4 and count(oid) = 4,
    jsonb_build_object('expected', 4, 'actual', count(oid))
  from function_catalog

  union all
  select 'function_security_and_search_path', bool_and(
      oid is not null
      and prosecdef = expected_security_definer
      and provolatile = expected_volatility
      and proconfig @> array['search_path=pg_catalog, public, pg_temp']::text[]
    ), jsonb_agg(jsonb_build_object('signature', e.signature, 'security_definer', f.prosecdef, 'volatility', f.provolatile, 'config', f.proconfig))
  from expected_functions e
  join function_catalog f using (signature)

  union all
  select 'authenticated_execute_exact',
    coalesce(bool_and(
      case
        when f.signature like '%log_off_food_item%' or f.signature like '%replace_off_food_log_item%'
          then exists (select 1 from function_acl a where a.oid = f.oid and a.grantee = 'authenticated' and a.privilege_type = 'EXECUTE')
        else not exists (select 1 from function_acl a where a.oid = f.oid and a.grantee = 'authenticated')
      end
    ), false),
    jsonb_agg(jsonb_build_object('signature', f.signature, 'authenticated_privileges', coalesce((select jsonb_agg(a.privilege_type order by a.privilege_type) from function_acl a where a.oid = f.oid and a.grantee = 'authenticated'), '[]'::jsonb)))
  from function_catalog f

  union all
  select 'no_public_anon_or_service_role_execute',
    not exists (
      select 1 from function_acl a
      where a.grantee in ('PUBLIC', 'anon', 'service_role')
        and a.privilege_type = 'EXECUTE'
    ),
    coalesce((select jsonb_agg(jsonb_build_object('grantee', a.grantee, 'privilege', a.privilege_type)) from function_acl a where a.grantee in ('PUBLIC', 'anon', 'service_role')), '[]'::jsonb)

  union all
  select 'trusted_server_catalog_resolution',
    resolver_def like '%frompublic.nutrition_off_productsp%'
      and resolver_def like '%joinpublic.nutrition_off_catalog_releasesr%'
      and resolver_def like '%p.lifecycle_status=''active''%'
      and resolver_def like '%p.quality_statusin(''complete'',''reviewed'')%'
      and resolver_def like '%r.status=''imported''%'
      and resolver_def like '%p.source_provider=''open_food_facts''%'
      and resolver_def like '%char_length(p.off_revision)between1and120%'
      and resolver_def like '%p.license_code=''odbl-1.0''%'
      and resolver_def not like '%auth.uid()%'
      and position('p_energy_' in resolver_def) = 0,
    jsonb_build_object('server_resolver', true)
  from definitions

  union all
  select 'no_browser_nutrient_authority',
    log_def not like '%p_energy_%'
      and log_def not like '%p_protein_%'
      and log_def not like '%p_carbohydrate_%'
      and log_def not like '%p_fat_%'
      and replace_def not like '%p_energy_%'
      and replace_def not like '%p_protein_%'
      and replace_def not like '%p_carbohydrate_%'
      and replace_def not like '%p_fat_%'
      and log_def like '%fmz_phase4_resolve_off_food_snapshot(p_off_product_id)%'
      and replace_def like '%fmz_phase4_resolve_off_food_snapshot(p_off_product_id)%',
    jsonb_build_object('browser_supplies', jsonb_build_array('off_product_id', 'quantity', 'unit', 'meal', 'notes', 'time controls'))
  from definitions

  union all
  select 'basis_and_unit_isolation',
    resolver_def like '%whenp.nutrition_basis=''per_100_ml''then''ml''else''g''end%'
      and log_def like '%p_consumed_unitisdistinctfromv_reference_unit%'
      and replace_def like '%p_consumed_unitisdistinctfromv_reference_unit%'
      and log_def not like '%p_density_g_per_ml%'
      and replace_def not like '%p_density_g_per_ml%'
      and log_def like '%v_factor:=p_consumed_quantity/100%'
      and replace_def like '%v_factor:=p_consumed_quantity/100%',
    jsonb_build_object('ml_equals_g_assumption', false)
  from definitions

  union all
  select 'immutable_odbl_snapshot_contract',
    resolver_def like '%''provider'',p.source_provider%'
      and resolver_def like '%''license_code'',p.license_code%'
      and resolver_def like '%''license_url'',p.license_url%'
      and resolver_def like '%''attribution_text'',p.attribution_text%'
      and resolver_def like '%''source_checksum'',p.source_checksum%'
      and resolver_def like '%''source_revision'',p.off_revision%'
      and resolver_def like '%''derivation'',jsonb_build_object%'
      and guard_def like '%historicalfoodlogitemsnapshotsareimmutable%',
    jsonb_build_object('provider', 'open_food_facts', 'license', 'ODbL-1.0')
  from definitions

  union all
  select 'snapshot_guard_separates_usda_and_off',
    guard_def like '%new.source_provider_snapshot=''usda_fdc''%'
      and guard_def like '%phase4_usda_v1%'
      and guard_def like '%new.source_provider_snapshot=''open_food_facts''%'
      and guard_def like '%fmz.phase4_off_snapshot_user_id%'
      and guard_def like '%off_log%'
      and guard_def like '%off_replace%'
      and guard_def like '%odbl-1.0%'
      and guard_def like '%new.consumed_unitisdistinctfromnew.reference_unit_snapshot%',
    jsonb_build_object('usda_preserved', true, 'off_isolated', true)
  from definitions

  union all
  select 'log_idempotency_and_day_authority',
    log_def like '%fmz_phase4_food_log_request:%'
      and log_def like '%fmz_phase4_food_log:%'
      and log_def like '%metadata->>''operation''isdistinctfrom''off_log''%'
      and log_def like '%''idempotent_replay'',true%'
      and log_def like '%fmz_phase4_day_payload(v_user_id,%'
      and log_def like '%onconflict(user_id,log_date)donothing%',
    jsonb_build_object('request_lock', true, 'day_payload', true)
  from definitions

  union all
  select 'replacement_atomicity_and_stale_guard',
    replace_def like '%fmz_phase4_food_log_request:%'
      and replace_def like '%fmz_phase4_food_log_item_request:%'
      and replace_def like '%v_original.updated_atisdistinctfromp_expected_original_updated_at%'
      and replace_def like '%insertintopublic.food_log_items%'
      and replace_def like '%updatepublic.food_log_itemssetstatus=''archived''%'
      and replace_def like '%atomicreplacementrolledback%'
      and replace_def like '%''idempotent_replay'',true%',
    jsonb_build_object('new_snapshot_then_archive_same_transaction', true)
  from definitions

  union all
  select 'timezone_and_free_history_preserved',
    log_def like '%pg_catalog.pg_timezone_names%'
      and log_def like '%p_log_date<v_today-6%'
      and log_def like '%fmz_phase4_has_full_nutrition_access(v_user_id)%'
      and replace_def like '%v_log.log_date<v_today-6%'
      and replace_def like '%fmz_phase4_has_full_nutrition_access(v_user_id)%',
    jsonb_build_object('free_days', 7)
  from definitions

  union all
  select 'item_trigger_attached',
    exists (
      select 1 from trigger_state
      where tgname = 'food_log_items_20_enforce_owner'
        and proname = 'fmz_phase4_enforce_food_log_item_owner'
    ),
    coalesce((select jsonb_agg(jsonb_build_object('trigger', tgname, 'function', proname)) from trigger_state), '[]'::jsonb)

  union all
  select 'rls_remains_enabled',
    count(*) = 18 and bool_and(relrowsecurity),
    jsonb_object_agg(relname, relrowsecurity)
  from table_state

  union all
  select 'no_delete_or_trainer_policy_expansion',
    not exists (
      select 1 from policy_state
      where cmd = 'DELETE'
         or lower(policyname) like '%trainer%'
         or lower(policyname) like '%coach%'
    ),
    coalesce((select jsonb_agg(jsonb_build_object('table', tablename, 'policy', policyname, 'command', cmd)) from policy_state where cmd = 'DELETE' or lower(policyname) like '%trainer%' or lower(policyname) like '%coach%'), '[]'::jsonb)

  union all
  select 'off_catalog_counts_preserved',
    (select count(*) from public.nutrition_off_catalog_releases where status = 'imported') = 1
      and (select count(*) from public.nutrition_off_products) = 24458
      and (select count(*) from public.nutrition_off_product_names) = 74184
      and (select count(*) from public.nutrition_off_products where nutrition_basis = 'per_100_g') = 20355
      and (select count(*) from public.nutrition_off_products where nutrition_basis = 'per_100_ml') = 4103,
    jsonb_build_object(
      'imported_releases', (select count(*) from public.nutrition_off_catalog_releases where status = 'imported'),
      'products', (select count(*) from public.nutrition_off_products),
      'names', (select count(*) from public.nutrition_off_product_names),
      'per_100_g', (select count(*) from public.nutrition_off_products where nutrition_basis = 'per_100_g'),
      'per_100_ml', (select count(*) from public.nutrition_off_products where nutrition_basis = 'per_100_ml')
    )

  union all
  select 'slice4e_catalog_preserved',
    (select count(*) from public.foods where catalog_scope = 'canonical' and source_provider = 'usda_fdc' and status = 'active') = 64
      and (select count(*) from public.food_aliases where status = 'active') = 197,
    jsonb_build_object(
      'canonical_usda_foods', (select count(*) from public.foods where catalog_scope = 'canonical' and source_provider = 'usda_fdc' and status = 'active'),
      'active_aliases', (select count(*) from public.food_aliases where status = 'active')
    )

  union all
  select 'frozen_logging_functions_present',
    to_regprocedure('public.fmz_phase4_log_food_item(uuid,uuid,date,text,smallint,text,uuid,uuid,numeric,text,text,timestamp with time zone)') is not null
      and to_regprocedure('public.fmz_phase4_replace_food_log_item(uuid,uuid,uuid,timestamp with time zone,text,uuid,uuid,numeric,text,text)') is not null
      and to_regprocedure('public.fmz_phase4_archive_food_log_item(uuid,timestamp with time zone)') is not null
      and to_regprocedure('public.fmz_phase4_log_provider_food_item(uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb)') is not null
      and to_regprocedure('public.fmz_phase4_replace_provider_food_log_item(uuid,uuid,uuid,uuid,timestamp with time zone,text,numeric,text,text,jsonb)') is not null,
    jsonb_build_object('custom_generic', true, 'usda', true, 'archive', true)
)
select jsonb_pretty(jsonb_build_object(
  'overall_pass', coalesce(bool_and(coalesce(passed, false)), false),
  'pass_count', count(*) filter (where passed is true),
  'fail_count', count(*) filter (where passed is not true),
  'checks', jsonb_agg(jsonb_build_object(
    'check', check_name,
    'pass', passed,
    'details', details
  ) order by check_name)
)) as verification_result
from checks;
