-- Phase 4F-D transient OFF barcode foundation - STAGING read-only verifier.
-- One SELECT/CTE statement. No application RPC is executed.

with expected_functions(signature, security_definer, volatility, allowed_role) as (
  values
    ('public.fmz_phase4_resolve_member_barcode(uuid,text)', true, 's'::"char", 'service_role'::text),
    ('public.fmz_phase4_upsert_custom_food_with_barcode(uuid,text,text,text,numeric,text,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,timestamp with time zone)', true, 'v'::"char", 'authenticated'::text),
    ('public.fmz_phase4_validate_transient_off_candidate(jsonb)', true, 's'::"char", null::text),
    ('public.fmz_phase4_transient_off_food_item_mutation(text,uuid,uuid,uuid,uuid,timestamp with time zone,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb)', true, 'v'::"char", null::text),
    ('public.fmz_phase4_log_transient_off_food_item(uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb)', true, 'v'::"char", 'service_role'::text),
    ('public.fmz_phase4_replace_transient_off_food_item(uuid,uuid,uuid,uuid,timestamp with time zone,text,numeric,text,text,jsonb)', true, 'v'::"char", 'service_role'::text),
    ('public.fmz_phase4_resolve_transient_off_food_log_item(uuid,uuid)', true, 's'::"char", 'service_role'::text),
    ('public.fmz_phase4_enforce_food_log_item_owner()', true, 'v'::"char", null::text),
    ('public.fmz_phase4_provider_consume_rate_limits(text,text,uuid)', true, 'v'::"char", 'service_role'::text),
    ('public.fmz_phase4_provider_transition_runtime_state(text,text,integer,text,integer,integer,timestamp with time zone,jsonb)', true, 'v'::"char", 'service_role'::text)
),
function_catalog as (
  select
    e.*,
    p.oid,
    p.prosecdef,
    p.provolatile,
    lower(coalesce(p.prosrc, '')) as source,
    lower(coalesce(array_to_string(p.proconfig, ','), '')) as config,
    p.proacl,
    p.proowner
  from expected_functions e
  left join pg_catalog.pg_proc p on p.oid = to_regprocedure(e.signature)
),
function_acl as (
  select
    f.signature,
    coalesce(r.rolname, 'PUBLIC') as grantee,
    a.privilege_type
  from function_catalog f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) a
  left join pg_catalog.pg_roles r on r.oid = a.grantee
),
constraint_sources as (
  select c.conname, lower(pg_catalog.pg_get_constraintdef(c.oid, true)) as definition
  from pg_catalog.pg_constraint c
  where c.conrelid in (
    'public.nutrition_provider_food_cache'::regclass,
    'public.nutrition_provider_rate_buckets'::regclass,
    'public.nutrition_provider_runtime_state'::regclass
  )
),
index_sources as (
  select i.relname as index_name,
    lower(pg_catalog.pg_get_indexdef(i.oid)) as definition,
    lower(coalesce(pg_catalog.pg_get_expr(x.indpred, x.indrelid), '')) as predicate,
    pg_catalog.regexp_replace(
      lower(coalesce(pg_catalog.pg_get_expr(x.indpred, x.indrelid), '')),
      '([[:space:]()]|::text)', '', 'g'
    ) as normalized_predicate,
    x.indisvalid,
    x.indisready,
    x.indisunique
  from pg_catalog.pg_class i
  join pg_catalog.pg_index x on x.indexrelid = i.oid
  join pg_catalog.pg_namespace n on n.oid = i.relnamespace
  where n.nspname = 'public'
),
table_acl as (
  select c.relname as table_name, coalesce(r.rolname, 'PUBLIC') as grantee, a.privilege_type
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  cross join lateral pg_catalog.aclexplode(
    coalesce(c.relacl, pg_catalog.acldefault('r', c.relowner))
  ) a
  left join pg_catalog.pg_roles r on r.oid = a.grantee
  where n.nspname = 'public'
    and c.relname in (
      'nutrition_provider_food_cache', 'nutrition_provider_rate_buckets',
      'nutrition_provider_runtime_state', 'nutrition_off_products',
      'nutrition_off_product_names', 'nutrition_off_catalog_releases',
      'foods', 'food_logs', 'food_log_items'
    )
),
rls_tables as (
  select c.relname, c.relrowsecurity
  from pg_catalog.pg_class c join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public' and c.relname in (
    'nutrition_provider_food_cache', 'nutrition_provider_rate_buckets',
    'nutrition_provider_runtime_state', 'nutrition_off_products',
    'nutrition_off_product_names', 'nutrition_off_catalog_releases',
    'foods', 'food_logs', 'food_log_items'
  )
),
checks(check_name, pass, details) as (
  select 'all_functions_present', bool_and(oid is not null),
    jsonb_build_object('missing', coalesce(jsonb_agg(signature) filter (where oid is null), '[]'::jsonb))
  from function_catalog
  union all
  select 'function_security_and_search_path', bool_and(
    oid is not null and prosecdef = security_definer and provolatile = volatility
    and config in ('search_path=pg_catalog', 'search_path=pg_catalog, public, pg_temp')
  ), '{}'::jsonb from function_catalog
  union all
  select 'function_acl_exact', not exists (
    select 1 from function_catalog f
    where exists (
      select 1 from function_acl a
      where a.signature = f.signature and a.privilege_type = 'EXECUTE'
        and a.grantee in ('PUBLIC', 'anon', 'authenticated', 'service_role')
        and a.grantee is distinct from f.allowed_role
    ) or (
      f.allowed_role is not null and not exists (
        select 1 from function_acl a where a.signature = f.signature
          and a.grantee = f.allowed_role and a.privilege_type = 'EXECUTE'
      )
    )
  ), '{}'::jsonb
  union all
  select 'provider_constraints_source_distinct',
    exists (select 1 from constraint_sources where conname = 'nutrition_provider_food_cache_provider_check' and definition like '%usda_fdc%' and definition like '%open_food_facts%')
    and exists (select 1 from constraint_sources where conname = 'nutrition_provider_food_cache_data_type_check' and definition like '%off_branded%' and definition like '%foundation%')
    and exists (select 1 from constraint_sources where conname = 'nutrition_provider_rate_buckets_provider_check' and definition like '%open_food_facts%')
    and exists (select 1 from constraint_sources where conname = 'nutrition_provider_runtime_state_provider_check' and definition like '%open_food_facts%'), '{}'::jsonb
  union all
  select 'custom_barcode_unique_index', exists (
    select 1 from index_sources where index_name = 'foods_active_custom_gtin_owner_uidx'
      and indisvalid and indisready and indisunique
      and definition like '%owner_user_id%fmz_phase4_normalize_gtin14%barcode%'
      and normalized_predicate like '%catalog_scope=''custom''%status=''active''%fmz_phase4_normalize_gtin14(barcode)isnotnull%'
  ), '{}'::jsonb
  union all
  select 'local_lookup_is_local_first', exists (
    select 1 from function_catalog where signature like 'public.fmz_phase4_resolve_member_barcode%'
      and source like '%nutrition_off_products%nutrition_off_catalog_releases%'
      and source like '%quality_status in (''complete'', ''reviewed'')%'
      and source like '%catalog_scope = ''custom''%owner_user_id = p_user_id%'
      and source not like '%http%' and source not like '%net.http%'
  ), '{}'::jsonb
  union all
  select 'custom_barcode_owner_and_stale_guard', exists (
    select 1 from function_catalog where signature like 'public.fmz_phase4_upsert_custom_food_with_barcode%'
      and source like '%auth.uid()%fmz_phase4_normalize_gtin14%'
      and source like '%p_expected_updated_at%custom food changed; refresh before saving%'
      and source like '%fmz_phase4_custom_food_barcode:%'
  ), '{}'::jsonb
  union all
  select 'candidate_identity_and_odbl', exists (
    select 1 from function_catalog where signature like 'public.fmz_phase4_validate_transient_off_candidate%'
      and source like '%open_food_facts:%fmz_phase4_provider_candidate_uuid_v5%'
      and source like '%phase4_off_barcode_v1%off_branded%'
      and source like '%odbl-1.0%opendatacommons.org/licenses/odbl/1-0/%'
      and source like '%en:netherlands%source_checksum%'
  ), '{}'::jsonb
  union all
  select 'explicit_100g_100ml_contract', exists (
    select 1 from function_catalog where signature like 'public.fmz_phase4_transient_off_food_item_mutation%'
      and source like '%p_consumed_unit is distinct from v_reference_unit%'
      and source like '%per_100_ml%per_100_g%'
      and source not like '%density_g_per_ml%=%'
  ), '{}'::jsonb
  union all
  select 'transient_mutation_idempotent_atomic', exists (
    select 1 from function_catalog where signature like 'public.fmz_phase4_transient_off_food_item_mutation%'
      and source like '%pg_advisory_xact_lock%fmz_phase4_food_log_request:%'
      and source like '%request uuid was reused with a different payload%'
      and source like '%updated_at is distinct from p_expected_original_updated_at%'
      and source like '%set status = ''archived''%atomic replacement rolled back%'
      and source like '%fmz_phase4_day_payload%'
  ), '{}'::jsonb
  union all
  select 'fresh_candidate_can_replace_any_active_own_item', exists (
    select 1 from function_catalog where signature like 'public.fmz_phase4_transient_off_food_item_mutation%'
      and source like '%active food log item is unavailable for replacement%'
      and source like '%p_candidate%fmz_phase4_validate_transient_off_candidate%'
      and source not like '%replacement accepts transient off snapshots only%'
  ), '{}'::jsonb
  union all
  select 'transient_write_context_isolated', exists (
    select 1 from function_catalog where signature = 'public.fmz_phase4_enforce_food_log_item_owner()'
      and source like '%fmz.phase4_transient_off_snapshot_user_id%'
      and source like '%transient_off_log%transient_off_replace%'
      and source like '%v_authenticated_user_id is not null%'
      and source like '%trusted backend context%'
      and source like '%historical food log item snapshots are immutable%'
  ), '{}'::jsonb
  union all
  select 'historical_snapshot_resolver_immutable', exists (
    select 1 from function_catalog where signature like 'public.fmz_phase4_resolve_transient_off_food_log_item%'
      and source like '%i.status = ''active''%l.status = ''active''%'
      and source like '%transient_off_request%transient_off_replacement_request%'
      and source like '%provenance_snapshot is distinct from%'
      and source like '%historical transient off snapshot failed immutable identity validation%'
  ), '{}'::jsonb
  union all
  select 'no_persistent_catalog_mutation', not exists (
    select 1 from function_catalog where signature in (
      'public.fmz_phase4_resolve_member_barcode(uuid,text)',
      'public.fmz_phase4_validate_transient_off_candidate(jsonb)',
      'public.fmz_phase4_transient_off_food_item_mutation(text,uuid,uuid,uuid,uuid,timestamp with time zone,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb)',
      'public.fmz_phase4_log_transient_off_food_item(uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb)',
      'public.fmz_phase4_replace_transient_off_food_item(uuid,uuid,uuid,uuid,timestamp with time zone,text,numeric,text,text,jsonb)'
    ) and lower(source) ~ '(insert into|update|delete from)[[:space:]]+public[.](nutrition_off_products|nutrition_off_product_names|nutrition_off_catalog_releases)'
  ), '{}'::jsonb
  union all
  select 'operational_table_acl_isolated',
    not exists (select 1 from table_acl where table_name in ('nutrition_provider_food_cache','nutrition_provider_rate_buckets','nutrition_provider_runtime_state') and grantee in ('PUBLIC','anon','authenticated'))
    and not exists (select 1 from table_acl where table_name = 'nutrition_provider_rate_buckets' and grantee = 'service_role')
    and exists (select 1 from table_acl where table_name = 'nutrition_provider_food_cache' and grantee = 'service_role' and privilege_type = 'SELECT')
    and exists (select 1 from table_acl where table_name = 'nutrition_provider_runtime_state' and grantee = 'service_role' and privilege_type = 'SELECT'), '{}'::jsonb
  union all
  select 'rls_preserved', count(*) = 9 and bool_and(relrowsecurity),
    jsonb_build_object('tables', count(*)) from rls_tables
  union all
  select 'no_delete_or_trainer_policy', not exists (
    select 1 from pg_catalog.pg_policy p
    join pg_catalog.pg_class c on c.oid = p.polrelid
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relname in ('food_logs','food_log_items','foods','nutrition_off_products')
      and (p.polcmd = 'd' or lower(p.polname) ~ '(trainer|coach)')
  ), '{}'::jsonb
  union all
  select 'frozen_paths_present',
    to_regprocedure('public.fmz_phase4_log_food_item(uuid,uuid,date,text,smallint,text,uuid,uuid,numeric,text,text,timestamp with time zone)') is not null
    and to_regprocedure('public.fmz_phase4_replace_food_log_item(uuid,uuid,uuid,timestamp with time zone,text,uuid,uuid,numeric,text,text)') is not null
    and to_regprocedure('public.fmz_phase4_log_provider_food_item(uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb)') is not null
    and to_regprocedure('public.fmz_phase4_replace_provider_food_log_item(uuid,uuid,uuid,uuid,timestamp with time zone,text,numeric,text,text,jsonb)') is not null
    and to_regprocedure('public.fmz_phase4_log_off_food_item(uuid,uuid,date,text,smallint,text,uuid,numeric,text,text,timestamp with time zone)') is not null
    and to_regprocedure('public.fmz_phase4_replace_off_food_log_item(uuid,uuid,uuid,timestamp with time zone,text,uuid,numeric,text,text)') is not null
    and to_regprocedure('public.fmz_phase4_archive_food_log_item(uuid,timestamp with time zone)') is not null,
    '{}'::jsonb
),
result as (
  select
    bool_and(pass) as overall_pass,
    count(*) filter (where pass) as pass_count,
    count(*) filter (where not pass) as fail_count,
    jsonb_agg(jsonb_build_object(
      'check', check_name, 'pass', pass, 'result', case when pass then 'PASS' else 'FAIL' end,
      'details', details
    ) order by check_name) as checks
  from checks
)
select jsonb_pretty(jsonb_build_object(
  'verification', 'phase4_slice4fd_transient_off_barcode',
  'target', 'mokxyyullfhkfalopbzd',
  'read_only', true,
  'overall_pass', overall_pass,
  'pass_count', pass_count,
  'fail_count', fail_count,
  'checks', checks
)) as verification_result
from result;
