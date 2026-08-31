with expected_tables(table_name) as (
  values
    ('nutrition_preferences'), ('foods'), ('food_portions'), ('nutrition_targets'),
    ('food_logs'), ('food_log_items'), ('food_aliases'), ('nutrition_food_ingestions'),
    ('nutrition_provider_query_cache'), ('nutrition_provider_food_cache'),
    ('nutrition_provider_rate_buckets'), ('nutrition_provider_runtime_state'),
    ('nutrition_off_catalog_releases'), ('nutrition_off_products'),
    ('nutrition_off_product_names')
),
table_state as (
  select
    e.table_name,
    c.oid is not null as exists,
    coalesce(c.relrowsecurity, false) as rls_enabled
  from expected_tables e
  left join pg_catalog.pg_class c
    on c.oid = pg_catalog.to_regclass('public.' || e.table_name)
),
browser_table_acl as (
  select tp.table_name, tp.grantee, tp.privilege_type
  from information_schema.table_privileges tp
  join expected_tables e on e.table_name = tp.table_name
  where tp.table_schema = 'public'
    and tp.grantee in ('authenticated', 'anon', 'PUBLIC')
),
policy_state as (
  select p.tablename, p.policyname, p.cmd, p.qual, p.with_check
  from pg_catalog.pg_policies p
  join expected_tables e on e.table_name = p.tablename
  where p.schemaname = 'public'
),
service_functions(name) as (
  values
    ('fmz_phase4_provider_consume_rate_limits'),
    ('fmz_phase4_provider_transition_runtime_state'),
    ('fmz_phase4_log_provider_food_item'),
    ('fmz_phase4_replace_provider_food_log_item'),
    ('fmz_phase4_resolve_provider_food_log_item'),
    ('fmz_phase4_resolve_member_barcode'),
    ('fmz_phase4_log_transient_off_food_item'),
    ('fmz_phase4_replace_transient_off_food_item'),
    ('fmz_phase4_resolve_transient_off_food_log_item')
),
authenticated_functions(name) as (
  values
    ('fmz_phase4_set_nutrition_timezone'),
    ('fmz_phase4_search_foods'),
    ('fmz_phase4_search_nutrition_catalog'),
    ('fmz_phase4_lookup_off_product_by_barcode'),
    ('fmz_phase4_upsert_custom_food'),
    ('fmz_phase4_upsert_custom_food_with_barcode'),
    ('fmz_phase4_archive_custom_food'),
    ('fmz_phase4_save_member_target'),
    ('fmz_phase4_get_current_nutrition_target'),
    ('fmz_phase4_get_nutrition_day'),
    ('fmz_phase4_get_nutrition_history'),
    ('fmz_phase4_log_food_item'),
    ('fmz_phase4_replace_food_log_item'),
    ('fmz_phase4_archive_food_log_item'),
    ('fmz_phase4_log_off_food_item'),
    ('fmz_phase4_replace_off_food_log_item')
),
internal_functions(name) as (
  values
    ('fmz_phase4_resolve_off_food_snapshot'),
    ('fmz_phase4_validate_transient_off_candidate'),
    ('fmz_phase4_transient_off_food_item_mutation')
),
phase4_functions as (
  select
    p.oid,
    p.proname,
    p.proowner,
    p.proacl,
    p.prosecdef,
    p.proconfig,
    lower(p.prosrc) as source
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname like 'fmz_phase4_%'
),
function_acl as (
  select
    f.proname,
    case when a.grantee = 0 then 'PUBLIC' else coalesce(r.rolname, a.grantee::text) end as grantee,
    a.privilege_type
  from phase4_functions f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) a
  left join pg_catalog.pg_roles r on r.oid = a.grantee
  where a.privilege_type = 'EXECUTE'
),
catalog_counts as (
  select
    (select count(*) from public.foods where catalog_scope = 'canonical' and status = 'active') as canonical_foods,
    (select count(*) from public.food_aliases where status = 'active') as active_aliases,
    (select count(*) from public.nutrition_off_products where lifecycle_status = 'active') as off_products,
    (select count(*) from public.nutrition_off_product_names where lifecycle_status = 'active') as off_names,
    (select count(*) from public.nutrition_off_products where lifecycle_status = 'active' and nutrition_basis = 'per_100_g') as off_g,
    (select count(*) from public.nutrition_off_products where lifecycle_status = 'active' and nutrition_basis = 'per_100_ml') as off_ml
),
catalog_integrity as (
  select
    count(*) filter (
      where energy_kcal is null or protein_grams is null
         or carbohydrate_grams is null or fat_grams is null
    ) as canonical_missing_required,
    count(*) filter (
      where source_provider <> 'usda_fdc' or quality_status <> 'reviewed'
         or coalesce(provenance, '{}'::jsonb) = '{}'::jsonb
    ) as canonical_bad_authority
  from public.foods
  where catalog_scope = 'canonical' and status = 'active'
),
off_integrity as (
  select
    count(*) filter (
      where normalized_gtin14 !~ '^[0-9]{14}$'
         or provider_identity_name <> 'open_food_facts:' || normalized_gtin14
    ) as bad_identity,
    count(*) - count(distinct normalized_gtin14) as duplicate_gtin,
    count(*) filter (
      where energy_kcal_100 is null or protein_grams_100 is null
         or carbohydrate_grams_100 is null or fat_grams_100 is null
    ) as missing_required,
    count(*) filter (
      where license_code <> 'ODbL-1.0'
         or license_url <> 'https://opendatacommons.org/licenses/odbl/1-0/'
         or attribution_text <> 'Open Food Facts contributors'
         or coalesce(provenance, '{}'::jsonb) = '{}'::jsonb
    ) as bad_odbl
  from public.nutrition_off_products
  where lifecycle_status = 'active'
),
pair_state as (
  select
    (max(food_id::text) filter (where normalized_alias = 'kipfilet rauw'))::uuid as chicken_raw,
    (max(food_id::text) filter (where normalized_alias = 'kipfilet bereid'))::uuid as chicken_cooked,
    (max(food_id::text) filter (where normalized_alias = 'rijst droog'))::uuid as rice_dry,
    (max(food_id::text) filter (where normalized_alias = 'rijst gekookt'))::uuid as rice_cooked,
    (max(food_id::text) filter (where normalized_alias = 'pasta droog'))::uuid as pasta_dry,
    (max(food_id::text) filter (where normalized_alias = 'pasta gekookt'))::uuid as pasta_cooked,
    (max(food_id::text) filter (where normalized_alias = 'aardappel rauw'))::uuid as potato_raw,
    (max(food_id::text) filter (where normalized_alias = 'aardappel gekookt'))::uuid as potato_cooked
  from public.food_aliases
  where status = 'active'
),
log_integrity as (
  select
    count(*) filter (where i.user_id <> l.user_id) as cross_owner_rows,
    count(*) filter (
      where i.food_id is null
        and i.source_provider_snapshot not in ('usda_fdc', 'open_food_facts')
    ) as unknown_transient_source,
    count(*) filter (
      where i.food_id is null
        and (i.food_name_snapshot is null or i.reference_amount_snapshot is null
          or i.reference_unit_snapshot is null or i.energy_kcal_snapshot is null
          or i.protein_grams_snapshot is null or i.carbohydrate_grams_snapshot is null
          or i.fat_grams_snapshot is null or i.provenance_snapshot is null)
    ) as incomplete_transient_snapshot
  from public.food_log_items i
  join public.food_logs l on l.id = i.food_log_id
),
history_sources as (
  select
    max(source) filter (where proname = 'fmz_phase4_get_nutrition_history') as history_source,
    max(source) filter (where proname = 'fmz_phase4_has_full_nutrition_access') as entitlement_source,
    max(source) filter (where proname = 'fmz_phase4_day_payload') as day_source,
    max(source) filter (where proname = 'fmz_phase4_log_off_food_item') as off_log_source,
    max(source) filter (where proname = 'fmz_phase4_replace_off_food_log_item') as off_replace_source
  from phase4_functions
),
checks(check_name, pass, details) as (
  select 'all_nutrition_tables_live',
    bool_and(exists),
    jsonb_build_object('missing', coalesce(jsonb_agg(table_name) filter (where not exists), '[]'::jsonb))
  from table_state
  union all
  select 'rls_enabled_on_all_nutrition_tables',
    bool_and(rls_enabled),
    jsonb_build_object('without_rls', coalesce(jsonb_agg(table_name) filter (where not rls_enabled), '[]'::jsonb))
  from table_state
  union all
  select 'browser_table_acl_minimal',
    not exists (
      select 1 from browser_table_acl a
      where not (
        a.grantee = 'authenticated' and a.privilege_type = 'SELECT'
        and a.table_name in ('foods', 'food_portions', 'food_aliases')
      )
    ),
    jsonb_build_object('acl_rows', (select count(*) from browser_table_acl))
  union all
  select 'no_delete_or_trainer_policy',
    not exists (
      select 1 from policy_state
      where upper(cmd) = 'DELETE'
         or lower(policyname) ~ '(trainer|coach|admin|broad)'
    ), '{}'::jsonb
  union all
  select 'personal_own_user_policies',
    (select count(*) from policy_state
      where tablename in ('nutrition_preferences', 'nutrition_targets', 'food_logs', 'food_log_items')
        and lower(coalesce(qual, '') || ' ' || coalesce(with_check, '')) like '%auth.uid()%') >= 8,
    jsonb_build_object('own_policy_count', (
      select count(*) from policy_state
      where tablename in ('nutrition_preferences', 'nutrition_targets', 'food_logs', 'food_log_items')
        and lower(coalesce(qual, '') || ' ' || coalesce(with_check, '')) like '%auth.uid()%'
    ))
  union all
  select 'custom_food_visibility_is_owner_bound',
    exists (
      select 1 from policy_state
      where tablename = 'foods' and policyname = 'foods_select_visible'
        and lower(coalesce(qual, '')) like '%owner_user_id%'
        and lower(coalesce(qual, '')) like '%auth.uid()%'
    ), '{}'::jsonb
  union all
  select 'operational_tables_isolated',
    not exists (
      select 1 from browser_table_acl
      where table_name in (
        'nutrition_food_ingestions', 'nutrition_provider_query_cache',
        'nutrition_provider_food_cache', 'nutrition_provider_rate_buckets',
        'nutrition_provider_runtime_state', 'nutrition_off_catalog_releases'
      )
    ) and not exists (
      select 1 from policy_state
      where tablename in (
        'nutrition_food_ingestions', 'nutrition_provider_query_cache',
        'nutrition_provider_food_cache', 'nutrition_provider_rate_buckets',
        'nutrition_provider_runtime_state', 'nutrition_off_catalog_releases'
      )
    ), '{}'::jsonb
  union all
  select 'no_public_or_anon_phase4_execute',
    not exists (select 1 from function_acl where grantee in ('PUBLIC', 'anon')),
    jsonb_build_object('violations', coalesce((
      select jsonb_agg(distinct proname) from function_acl where grantee in ('PUBLIC', 'anon')
    ), '[]'::jsonb))
  union all
  select 'service_functions_are_service_only',
    not exists (
      select 1 from service_functions s
      where not exists (select 1 from phase4_functions f where f.proname = s.name)
         or not exists (select 1 from function_acl a where a.proname = s.name and a.grantee = 'service_role')
         or exists (select 1 from function_acl a where a.proname = s.name and a.grantee in ('authenticated', 'anon', 'PUBLIC'))
    ), '{}'::jsonb
  union all
  select 'authenticated_member_api_exactly_exposed',
    not exists (
      select 1 from authenticated_functions a
      where not exists (select 1 from phase4_functions f where f.proname = a.name)
         or not exists (select 1 from function_acl x where x.proname = a.name and x.grantee = 'authenticated')
         or exists (select 1 from function_acl x where x.proname = a.name and x.grantee in ('anon', 'PUBLIC'))
    ), '{}'::jsonb
  union all
  select 'internal_helpers_not_browser_executable',
    not exists (
      select 1 from internal_functions i
      join function_acl a on a.proname = i.name
      where a.grantee in ('authenticated', 'anon', 'PUBLIC')
    ), '{}'::jsonb
  union all
  select 'security_definer_search_paths_safe',
    not exists (
      select 1 from phase4_functions
      where prosecdef
        and not exists (
          select 1
          from unnest(coalesce(proconfig, '{}'::text[])) as setting(value)
          where setting.value ~ '^search_path=pg_catalog(, (public|extensions|pg_temp))*$'
        )
    ), '{}'::jsonb
  union all
  select 'canonical_catalog_counts',
    canonical_foods = 64 and active_aliases = 197,
    jsonb_build_object('foods', canonical_foods, 'aliases', active_aliases)
  from catalog_counts
  union all
  select 'canonical_catalog_authority_complete',
    canonical_missing_required = 0 and canonical_bad_authority = 0,
    to_jsonb(catalog_integrity)
  from catalog_integrity
  union all
  select 'raw_cooked_identities_are_distinct',
    chicken_raw is not null and chicken_cooked is not null and chicken_raw <> chicken_cooked
      and rice_dry is not null and rice_cooked is not null and rice_dry <> rice_cooked
      and pasta_dry is not null and pasta_cooked is not null and pasta_dry <> pasta_cooked
      and potato_raw is not null and potato_cooked is not null and potato_raw <> potato_cooked,
    to_jsonb(pair_state)
  from pair_state
  union all
  select 'off_catalog_counts_and_basis',
    off_products = 24458 and off_names = 74184 and off_g = 20355 and off_ml = 4103,
    to_jsonb(catalog_counts)
  from catalog_counts
  union all
  select 'off_identity_and_required_macros',
    bad_identity = 0 and duplicate_gtin = 0 and missing_required = 0,
    to_jsonb(off_integrity)
  from off_integrity
  union all
  select 'off_odbl_provenance_complete',
    bad_odbl = 0,
    jsonb_build_object('bad_odbl', bad_odbl)
  from off_integrity
  union all
  select 'log_parent_and_snapshot_integrity',
    cross_owner_rows = 0 and unknown_transient_source = 0 and incomplete_transient_snapshot = 0,
    to_jsonb(log_integrity)
  from log_integrity
  union all
  select 'free_history_and_full_entitlements_frozen',
    history_source like '%generate_series(0, 6)%'
      and history_source like '%window_days%7%'
      and entitlement_source like '%status = ''active''%'
      and entitlement_source like '%(''pro'', ''ai'', ''personal_coaching'')%'
      and entitlement_source like '%starts_at <= now()%'
      and entitlement_source like '%ends_at is null or e.ends_at > now()%'
      and entitlement_source not like '%trainer%',
    '{}'::jsonb
  from history_sources
  union all
  select 'authoritative_totals_use_snapshots',
    day_source like '%sum(i.energy_kcal_snapshot)%'
      and day_source like '%sum(i.protein_grams_snapshot)%'
      and day_source like '%sum(i.carbohydrate_grams_snapshot)%'
      and day_source like '%sum(i.fat_grams_snapshot)%',
    '{}'::jsonb
  from history_sources
  union all
  select 'off_logging_is_idempotent_atomic_and_unit_safe',
    off_log_source like '%fmz_phase4_food_log_request:%'
      and off_log_source like '%p_consumed_unit is distinct from v_reference_unit%'
      and off_replace_source like '%fmz_phase4_food_log_item_request:%'
      and off_replace_source like '%p_consumed_unit is distinct from v_reference_unit%'
      and off_replace_source like '%status = ''archived''%'
      and off_replace_source not like '%delete from public.food_log_items%',
    '{}'::jsonb
  from history_sources
),
summary as (
  select
    bool_and(pass) as overall_pass,
    count(*) filter (where pass) as pass_count,
    count(*) filter (where not pass) as fail_count,
    jsonb_agg(
      jsonb_build_object(
        'check', check_name,
        'pass', pass,
        'result', case when pass then 'PASS' else 'FAIL' end,
        'details', details
      ) order by check_name
    ) as checks
  from checks
)
select jsonb_pretty(jsonb_build_object(
  'verification', 'phase4_nutrition_4fe_final',
  'target', 'mokxyyullfhkfalopbzd',
  'read_only', true,
  'overall_pass', overall_pass,
  'pass_count', pass_count,
  'fail_count', fail_count,
  'checks', checks
)) as verification_result
from summary;
