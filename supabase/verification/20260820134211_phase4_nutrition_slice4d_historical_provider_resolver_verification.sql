-- FitMetZorge Phase 4 Nutrition Slice 4D historical provider resolver verification.
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- One SELECT/CTE statement. It invokes no application function and changes no data.

with
resolver as (
  select
    p.oid,
    p.proname::text as function_name,
    pg_catalog.oidvectortypes(p.proargtypes)::text as argument_types,
    pg_catalog.format_type(p.prorettype, null)::text as return_type,
    p.prosecdef as security_definer,
    p.provolatile::text as volatility,
    p.proconfig,
    p.proacl,
    p.proowner,
    p.prosrc::text as source,
    pg_catalog.regexp_replace(lower(p.prosrc::text), '[[:space:]]+', '', 'g') as source_compact
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname = 'fmz_phase4_resolve_provider_food_log_item'
),
resolver_acl as (
  select
    case when a.grantee = 0 then 'PUBLIC' else coalesce(r.rolname::text, '<missing-role>') end as grantee,
    a.privilege_type::text as privilege_type
  from resolver f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) a
  left join pg_catalog.pg_roles r on r.oid = a.grantee
),
frozen_functions as (
  select
    p.proname::text as function_name,
    pg_catalog.oidvectortypes(p.proargtypes)::text as argument_types,
    p.prosecdef as security_definer,
    p.proacl,
    p.proowner,
    pg_catalog.regexp_replace(lower(p.prosrc::text), '[[:space:]]+', '', 'g') as source_compact
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname in (
      'fmz_phase4_log_provider_food_item',
      'fmz_phase4_replace_provider_food_log_item',
      'fmz_phase4_archive_food_log_item',
      'fmz_phase4_log_food_item',
      'fmz_phase4_replace_food_log_item',
      'fmz_phase4_search_foods',
      'fmz_phase4_provider_consume_rate_limits',
      'fmz_phase4_provider_transition_runtime_state'
    )
),
frozen_acl as (
  select
    f.function_name,
    case when a.grantee = 0 then 'PUBLIC' else coalesce(r.rolname::text, '<missing-role>') end as grantee,
    a.privilege_type::text as privilege_type
  from frozen_functions f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) a
  left join pg_catalog.pg_roles r on r.oid = a.grantee
),
guard_tables(table_name) as (
  values
    ('profiles'::text),
    ('coach_workspaces'),
    ('user_settings'),
    ('user_onboarding'),
    ('entitlements'),
    ('recovery_logs'),
    ('foods'),
    ('food_portions'),
    ('food_aliases'),
    ('nutrition_targets'),
    ('food_logs'),
    ('food_log_items'),
    ('nutrition_provider_query_cache'),
    ('nutrition_provider_food_cache'),
    ('nutrition_provider_rate_buckets'),
    ('nutrition_provider_runtime_state')
),
guard_table_state as (
  select c.relname::text as table_name, c.relrowsecurity
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  join guard_tables g on g.table_name = c.relname::text
  where n.nspname = 'public' and c.relkind = 'r'
),
nutrition_policies as (
  select tablename::text, policyname::text, cmd::text
  from pg_catalog.pg_policies
  where schemaname = 'public'
    and tablename in ('foods', 'food_portions', 'food_aliases', 'nutrition_targets', 'food_logs', 'food_log_items')
),
checks(check_name, pass, details) as (
  select
    'resolver_exact_signature',
    (select count(*) from resolver) = 1
      and exists (
        select 1 from resolver
        where argument_types = 'uuid, uuid'
          and return_type = 'jsonb'
      ),
    coalesce((select jsonb_agg(to_jsonb(r)) from resolver r), '[]'::jsonb)
  union all
  select
    'resolver_security_definer_stable_safe_path',
    exists (
      select 1 from resolver
      where security_definer
        and volatility = 's'
        and proconfig @> array['search_path=pg_catalog, public, pg_temp']::text[]
    ),
    '{}'::jsonb
  union all
  select
    'resolver_service_role_only_execute',
    exists (
      select 1 from resolver_acl
      where grantee = 'service_role' and privilege_type = 'EXECUTE'
    )
      and not exists (
        select 1 from resolver_acl
        where grantee in ('PUBLIC', 'anon', 'authenticated')
          and privilege_type = 'EXECUTE'
      ),
    coalesce((select jsonb_agg(to_jsonb(a) order by grantee) from resolver_acl a), '[]'::jsonb)
  union all
  select
    'resolver_active_item_only',
    exists (
      select 1 from resolver
      where source_compact like '%i.status=''active''%'
        and source_compact like '%l.status=''active''%'
    ),
    '{}'::jsonb
  union all
  select
    'resolver_exact_user_ownership',
    exists (
      select 1 from resolver
      where source_compact like '%wherei.id=p_original_item_idandi.user_id=p_user_id%'
        and source_compact like '%l.user_id=p_user_id%'
    ),
    '{}'::jsonb
  union all
  select
    'resolver_null_food_isolation',
    exists (
      select 1 from resolver
      where source_compact like '%v_item.food_idisnotnull%'
        and source_compact like '%v_item.food_portion_idisnotnull%'
    ),
    '{}'::jsonb
  union all
  select
    'resolver_usda_provider_identity',
    exists (
      select 1 from resolver
      where source_compact like '%source_provider_snapshotisdistinctfrom''usda_fdc''%'
        and source_compact like '%provider_food_id_snapshot%'
        and source_compact like '%candidate_id%'
        and source_compact like '%phase4_usda_v1%'
        and source_compact like '%foundation%'
        and source_compact like '%survey(fndds)%'
        and source_compact like '%srlegacy%'
    ),
    '{}'::jsonb
  union all
  select
    'resolver_100g_snapshot_contract',
    exists (
      select 1 from resolver
      where source_compact like '%reference_amount_snapshotisdistinctfrom100::numeric%'
        and source_compact like '%reference_unit_snapshotisdistinctfrom''g''%'
        and source_compact like '%consumed_unitisdistinctfrom''g''%'
        and source_compact like '%calculation_basisisdistinctfrom''direct_reference''%'
    ),
    '{}'::jsonb
  union all
  select
    'resolver_snapshot_provenance_validation',
    exists (
      select 1 from resolver
      where source_compact like '%transient_provider_snapshot%'
        and source_compact like '%provider_data_type%'
        and source_compact like '%reference_basis%per_100_g%'
        and source_compact like '%derivation%'
        and source_compact like '%attribution%'
        and source_compact like '%phase4_provider_snapshot_v1%'
        and source_compact like '%usdafooddatacentral%'
        and source_compact like '%cc01.0%'
        and source_compact like '%https://fdc.nal.usda.gov/%'
        and source_compact like '%retrieved_at%'
        and source_compact like '%v_metadata_retrieved_atisdistinctfromv_retrieved_at%'
        and source_compact like '%v_metadata_source_updated_atisdistinctfromv_source_updated_at%'
        and source_compact like '%source_version_snapshot%source_version%'
    ),
    '{}'::jsonb
  union all
  select
    'resolver_minimum_internal_payload',
    exists (
      select 1 from resolver
      where source_compact like '%jsonb_build_object(''provider'',''usda_fdc'',''provider_food_id'',v_provider_food_id,''candidate_id'',v_candidate_id,''mapping_version'',''phase4_usda_v1'',''provider_data_type'',v_provider_data_type)%'
        and source_compact not like '%candidate_token%'
    ),
    '{}'::jsonb
  union all
  select
    'resolver_read_only_no_canonical_promotion',
    exists (
      select 1 from resolver
      where source !~* '\m(insert|update|delete|truncate|alter|create|drop|grant|revoke)\M'
        and source_compact not like '%public.foods%'
        and source_compact not like '%public.food_portions%'
        and source_compact not like '%public.food_aliases%'
    ),
    '{}'::jsonb
  union all
  select
    'provider_log_rpc_frozen',
    exists (
      select 1 from frozen_functions
      where function_name = 'fmz_phase4_log_provider_food_item'
        and argument_types = 'uuid, uuid, uuid, date, text, smallint, text, numeric, text, text, timestamp with time zone, jsonb'
        and security_definer
    ),
    '{}'::jsonb
  union all
  select
    'provider_replace_rpc_frozen',
    exists (
      select 1 from frozen_functions
      where function_name = 'fmz_phase4_replace_provider_food_log_item'
        and argument_types = 'uuid, uuid, uuid, uuid, timestamp with time zone, text, numeric, text, text, jsonb'
        and security_definer
        and source_compact like '%forupdate%'
        and source_compact like '%atomicreplacementrolledback%'
    ),
    '{}'::jsonb
  union all
  select
    'provider_mutation_rpcs_remain_service_role_only',
    not exists (
      select 1 from frozen_acl
      where function_name in ('fmz_phase4_log_provider_food_item', 'fmz_phase4_replace_provider_food_log_item')
        and grantee in ('PUBLIC', 'anon', 'authenticated')
        and privilege_type = 'EXECUTE'
    )
      and (select count(*) from frozen_acl where function_name in ('fmz_phase4_log_provider_food_item', 'fmz_phase4_replace_provider_food_log_item') and grantee = 'service_role' and privilege_type = 'EXECUTE') = 2,
    '{}'::jsonb
  union all
  select
    'canonical_and_archive_rpcs_frozen',
    exists (select 1 from frozen_functions where function_name = 'fmz_phase4_archive_food_log_item' and argument_types = 'uuid, timestamp with time zone')
      and exists (select 1 from frozen_functions where function_name = 'fmz_phase4_log_food_item')
      and exists (select 1 from frozen_functions where function_name = 'fmz_phase4_replace_food_log_item')
      and exists (select 1 from frozen_functions where function_name = 'fmz_phase4_search_foods'),
    '{}'::jsonb
  union all
  select
    'slice4b_4c_operational_guards_frozen',
    exists (select 1 from frozen_functions where function_name = 'fmz_phase4_provider_consume_rate_limits')
      and exists (select 1 from frozen_functions where function_name = 'fmz_phase4_provider_transition_runtime_state')
      and (select count(*) from guard_table_state) = (select count(*) from guard_tables)
      and not exists (select 1 from guard_table_state where not relrowsecurity),
    jsonb_build_object(
      'expected_tables', (select count(*) from guard_tables),
      'actual_tables', (select count(*) from guard_table_state),
      'rls_disabled', coalesce((select jsonb_agg(table_name) from guard_table_state where not relrowsecurity), '[]'::jsonb)
    )
  union all
  select
    'no_delete_or_trainer_policy_expansion',
    not exists (
      select 1 from nutrition_policies
      where cmd = 'DELETE'
         or lower(policyname) like '%trainer%'
         or lower(policyname) like '%coach%'
    ),
    coalesce((select jsonb_agg(to_jsonb(p) order by tablename, policyname) from nutrition_policies p), '[]'::jsonb)
  union all
  select
    'forbidden_reference_scan',
    not exists (
      select 1 from resolver
      where source_compact like '%hgoygcviutmynaihcvpd%'
         or source_compact like '%service_role_key%'
         or source_compact like '%secret_key%'
         or source_compact like '%trainer_id%'
         or source_compact like '%coach_workspaces%'
    ),
    '{}'::jsonb
)
select jsonb_build_object(
  'scope', 'phase4_nutrition_slice4d_historical_provider_resolver',
  'staging_project_ref', 'mokxyyullfhkfalopbzd',
  'overall_pass', bool_and(pass),
  'checks', jsonb_agg(
    jsonb_build_object('check', check_name, 'pass', pass, 'details', details)
    order by check_name
  )
) as verification_result
from checks;
