-- FitMetZorge Phase 4 Nutrition - Slice 4F OFF Catalog + Search Verification
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- One SELECT/CTE statement. Metadata inspection only; no application RPC calls.

with
expected_columns(table_name, columns) as (
  values
    (
      'nutrition_off_catalog_releases'::text,
      array[
        'id','source_provider','source_revision','source_snapshot_at',
        'source_file_sha256','normalized_artifact_sha256','license_code',
        'license_url','attribution_text','netherlands_source_count',
        'eligible_product_count','imported_product_count','mapping_version',
        'predecessor_release_id','status','reviewed_by','reviewed_at',
        'imported_at','provenance','metadata','created_at','updated_at'
      ]::text[]
    ),
    (
      'nutrition_off_products'::text,
      array[
        'id','release_id','source_provider','off_code','barcode_original',
        'normalized_gtin14','provider_identity_name','product_name',
        'product_name_nl','generic_name','brand','normalized_brand',
        'quantity_text','serving_size_text','nutrition_basis','energy_kcal_100',
        'protein_grams_100','carbohydrate_grams_100','fat_grams_100',
        'fiber_grams_100','countries_tags','is_netherlands_associated',
        'off_revision','source_updated_at','source_checksum','provenance',
        'license_code','license_url','attribution_text','image_reference_url',
        'image_license_code','image_attribution','completeness','quality_status',
        'lifecycle_status','imported_at','refreshed_at','metadata','created_at',
        'updated_at','archived_at'
      ]::text[]
    ),
    (
      'nutrition_off_product_names'::text,
      array[
        'id','product_id','language_code','name_type','name','normalized_name',
        'is_preferred','source_provider','source_revision','license_code',
        'provenance','quality_status','lifecycle_status','metadata','created_at',
        'updated_at','archived_at'
      ]::text[]
    )
),
actual_columns as (
  select
    c.table_name::text,
    array_agg(c.column_name::text order by c.ordinal_position)::text[] as columns
  from information_schema.columns c
  where c.table_schema = 'public'
    and c.table_name in (
      'nutrition_off_catalog_releases',
      'nutrition_off_products',
      'nutrition_off_product_names'
    )
  group by c.table_name
),
column_contract as (
  select
    e.table_name,
    coalesce(a.columns, array[]::text[]) = e.columns as pass,
    e.columns,
    coalesce(a.columns, array[]::text[]) as actual
  from expected_columns e
  left join actual_columns a using (table_name)
),
typed_columns as (
  select
    c.table_name::text,
    c.column_name::text,
    c.data_type::text,
    c.udt_name::text,
    c.is_nullable::text,
    c.column_default::text
  from information_schema.columns c
  where c.table_schema = 'public'
    and (
      (c.table_name = 'nutrition_off_catalog_releases' and c.column_name in ('id','source_snapshot_at','eligible_product_count','status','provenance'))
      or
      (c.table_name = 'nutrition_off_products' and c.column_name in ('id','release_id','normalized_gtin14','nutrition_basis','energy_kcal_100','countries_tags','quality_status','lifecycle_status'))
      or
      (c.table_name = 'nutrition_off_product_names' and c.column_name in ('id','product_id','language_code','normalized_name','quality_status','lifecycle_status'))
    )
),
constraints as (
  select
    con.conname::text as constraint_name,
    cls.relname::text as table_name,
    con.contype,
    pg_catalog.pg_get_constraintdef(con.oid, true) as definition
  from pg_catalog.pg_constraint con
  join pg_catalog.pg_class cls on cls.oid = con.conrelid
  join pg_catalog.pg_namespace n on n.oid = cls.relnamespace
  where n.nspname = 'public'
    and cls.relname in (
      'nutrition_off_catalog_releases',
      'nutrition_off_products',
      'nutrition_off_product_names'
    )
),
indexes as (
  select
    idx.relname::text as index_name,
    tbl.relname::text as table_name,
    i.indisunique,
    i.indisvalid,
    i.indisready,
    i.indpred is not null as is_partial,
    coalesce(pg_catalog.pg_get_expr(i.indpred, i.indrelid), '') as predicate,
    pg_catalog.pg_get_indexdef(i.indexrelid) as definition
  from pg_catalog.pg_index i
  join pg_catalog.pg_class idx on idx.oid = i.indexrelid
  join pg_catalog.pg_class tbl on tbl.oid = i.indrelid
  join pg_catalog.pg_namespace n on n.oid = tbl.relnamespace
  where n.nspname = 'public'
    and tbl.relname in (
      'nutrition_off_catalog_releases',
      'nutrition_off_products',
      'nutrition_off_product_names'
    )
),
table_security as (
  select
    c.relname::text as table_name,
    c.relrowsecurity,
    c.relforcerowsecurity
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname in (
      'nutrition_off_catalog_releases',
      'nutrition_off_products',
      'nutrition_off_product_names'
    )
),
policies as (
  select
    p.tablename::text,
    p.policyname::text,
    p.cmd::text,
    p.roles::text[] as roles,
    coalesce(p.qual, '')::text as using_expression,
    coalesce(p.with_check, '')::text as check_expression
  from pg_catalog.pg_policies p
  where p.schemaname = 'public'
    and p.tablename in (
      'nutrition_off_catalog_releases',
      'nutrition_off_products',
      'nutrition_off_product_names'
    )
),
table_acl as (
  select
    c.relname::text as table_name,
    coalesce(r.rolname, 'PUBLIC')::text as grantee,
    acl.privilege_type::text
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  cross join lateral pg_catalog.aclexplode(
    coalesce(c.relacl, pg_catalog.acldefault('r', c.relowner))
  ) acl
  left join pg_catalog.pg_roles r on r.oid = acl.grantee
  where n.nspname = 'public'
    and c.relname in (
      'nutrition_off_catalog_releases',
      'nutrition_off_products',
      'nutrition_off_product_names'
    )
),
expected_authenticated_columns(table_name, columns) as (
  values
    (
      'nutrition_off_products'::text,
      array[
        'attribution_text','barcode_original','brand','carbohydrate_grams_100',
        'energy_kcal_100','fat_grams_100','fiber_grams_100','generic_name','id',
        'image_attribution','image_license_code','image_reference_url','license_code',
        'license_url','lifecycle_status','normalized_brand','normalized_gtin14',
        'nutrition_basis','product_name','product_name_nl','protein_grams_100',
        'quality_status','quantity_text','serving_size_text','source_provider'
      ]::text[]
    ),
    (
      'nutrition_off_product_names'::text,
      array[
        'id','is_preferred','language_code','lifecycle_status','name','name_type',
        'normalized_name','product_id','quality_status'
      ]::text[]
    )
),
column_acl as (
  select
    c.relname::text as table_name,
    a.attname::text as column_name,
    coalesce(r.rolname, 'PUBLIC')::text as grantee,
    acl.privilege_type::text
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  join pg_catalog.pg_attribute a on a.attrelid = c.oid
  cross join lateral pg_catalog.aclexplode(
    coalesce(a.attacl, '{}'::aclitem[])
  ) acl
  left join pg_catalog.pg_roles r on r.oid = acl.grantee
  where n.nspname = 'public'
    and c.relname in (
      'nutrition_off_catalog_releases',
      'nutrition_off_products',
      'nutrition_off_product_names'
    )
    and a.attnum > 0
    and not a.attisdropped
),
authenticated_column_state as (
  select
    table_name,
    array_agg(column_name order by column_name)::text[] as columns
  from column_acl
  where grantee = 'authenticated'
    and privilege_type = 'SELECT'
  group by table_name
),
functions as (
  select
    p.oid,
    p.proname::text,
    pg_catalog.pg_get_function_identity_arguments(p.oid)::text as arguments,
    pg_catalog.pg_get_function_result(p.oid)::text as result_type,
    p.prosecdef,
    p.provolatile,
    coalesce(p.proconfig, array[]::text[])::text[] as configuration,
    p.prosrc::text as source
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname in (
      'fmz_phase4_normalize_gtin14',
      'fmz_phase4_normalize_catalog_text',
      'fmz_phase4_provider_candidate_uuid_v5',
      'fmz_phase4_enforce_off_release_state',
      'fmz_phase4_prevent_off_catalog_removal',
      'fmz_phase4_sync_off_archive_state',
      'fmz_phase4_enforce_off_product_identity',
      'fmz_phase4_enforce_off_product_name_identity',
      'fmz_phase4_search_nutrition_catalog',
      'fmz_phase4_lookup_off_product_by_barcode'
    )
),
function_acl as (
  select
    f.proname,
    f.arguments,
    coalesce(r.rolname, 'PUBLIC')::text as grantee,
    acl.privilege_type::text
  from functions f
  join pg_catalog.pg_proc p on p.oid = f.oid
  cross join lateral pg_catalog.aclexplode(
    coalesce(p.proacl, pg_catalog.acldefault('f', p.proowner))
  ) acl
  left join pg_catalog.pg_roles r on r.oid = acl.grantee
),
triggers as (
  select
    c.relname::text as table_name,
    t.tgname::text as trigger_name,
    p.proname::text as function_name,
    t.tgenabled::text
  from pg_catalog.pg_trigger t
  join pg_catalog.pg_class c on c.oid = t.tgrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  join pg_catalog.pg_proc p on p.oid = t.tgfoid
  where n.nspname = 'public'
    and not t.tgisinternal
    and c.relname in (
      'nutrition_off_catalog_releases',
      'nutrition_off_products',
      'nutrition_off_product_names'
    )
),
frozen_tables(table_name) as (
  values
    ('profiles'::text),('coach_workspaces'),('user_settings'),('user_onboarding'),
    ('entitlements'),('recovery_logs'),('training_plans'),('training_plan_days'),
    ('training_plan_exercises'),('workout_sessions'),('workout_set_logs'),
    ('foods'),('food_portions'),('food_aliases'),('nutrition_food_ingestions'),
    ('nutrition_preferences'),('nutrition_targets'),('food_logs'),('food_log_items'),
    ('nutrition_provider_query_cache'),('nutrition_provider_food_cache'),
    ('nutrition_provider_rate_buckets'),('nutrition_provider_runtime_state')
),
frozen_table_state as (
  select
    ft.table_name,
    exists (
      select 1
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public'
        and c.relname = ft.table_name
        and c.relkind = 'r'
    ) as exists,
    coalesce((
      select c.relrowsecurity
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public'
        and c.relname = ft.table_name
        and c.relkind = 'r'
      limit 1
    ), false) as rls_enabled
  from frozen_tables ft
),
frozen_functions(signature) as (
  values
    ('public.fmz_phase4_touch_updated_at()'::text),
    ('public.fmz_phase4_search_foods(text,integer,text,uuid)'::text),
    ('public.fmz_phase4_log_food_item(uuid,uuid,date,text,smallint,text,uuid,uuid,numeric,text,text,timestamp with time zone)'),
    ('public.fmz_phase4_replace_food_log_item(uuid,uuid,uuid,timestamp with time zone,text,uuid,uuid,numeric,text,text)'),
    ('public.fmz_phase4_archive_food_log_item(uuid,timestamp with time zone)'),
    ('public.fmz_phase4_log_provider_food_item(uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb)'),
    ('public.fmz_phase4_replace_provider_food_log_item(uuid,uuid,uuid,uuid,timestamp with time zone,text,numeric,text,text,jsonb)'),
    ('public.fmz_phase4_resolve_provider_food_log_item(uuid,uuid)')
),
frozen_function_state as (
  select signature, pg_catalog.to_regprocedure(signature) is not null as exists
  from frozen_functions
),
row_counts as (
  select
    (select count(*) from public.nutrition_off_catalog_releases) as release_count,
    (select count(*) from public.nutrition_off_products) as product_count,
    (select count(*) from public.nutrition_off_product_names) as name_count
),
checks(check_name, pass, details) as (
  values
    (
      'off_tables_exist',
      (select count(*) = 3 from table_security),
      jsonb_build_object('expected', 3, 'actual', (select count(*) from table_security))
    ),
    (
      'off_columns_exact',
      (select bool_and(pass) from column_contract),
      (select jsonb_agg(jsonb_build_object('table', table_name, 'pass', pass, 'expected', columns, 'actual', actual) order by table_name) from column_contract)
    ),
    (
      'off_key_column_types',
      (select count(*) = 19 from typed_columns)
      and exists (select 1 from typed_columns where table_name = 'nutrition_off_products' and column_name = 'countries_tags' and data_type = 'ARRAY' and udt_name = '_text')
      and exists (select 1 from typed_columns where table_name = 'nutrition_off_products' and column_name = 'energy_kcal_100' and data_type = 'numeric')
      and exists (select 1 from typed_columns where table_name = 'nutrition_off_catalog_releases' and column_name = 'id' and data_type = 'uuid'),
      (select jsonb_agg(to_jsonb(t) order by table_name, column_name) from typed_columns t)
    ),
    (
      'off_primary_and_foreign_keys',
      exists (select 1 from constraints where constraint_name = 'nutrition_off_catalog_releases_pkey' and contype = 'p')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_products_pkey' and contype = 'p')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_product_names_pkey' and contype = 'p')
      and exists (select 1 from constraints where table_name = 'nutrition_off_products' and contype = 'f' and definition ilike '%nutrition_off_catalog_releases%ON DELETE RESTRICT%')
      and exists (select 1 from constraints where table_name = 'nutrition_off_product_names' and contype = 'f' and definition ilike '%nutrition_off_products%ON DELETE RESTRICT%'),
      '{}'::jsonb
    ),
    (
      'off_release_forward_lifecycle',
      exists (select 1 from constraints where constraint_name = 'nutrition_off_releases_status_check' and definition like '%reviewed%imported%superseded%rejected%')
      and exists (select 1 from functions where proname = 'fmz_phase4_enforce_off_release_state' and source like '%must enter the forward lifecycle as reviewed%' and source like '%invalid OFF release status transition%' and source like '%imported count must equal active loggable products%')
      and exists (select 1 from indexes where index_name = 'nutrition_off_releases_current_uidx' and indisunique and is_partial and predicate like '%status = ''imported''%')
      and exists (select 1 from triggers where trigger_name = 'nutrition_off_releases_20_prevent_removal'),
      '{}'::jsonb
    ),
    (
      'off_release_audit_identity',
      exists (select 1 from constraints where constraint_name = 'nutrition_off_releases_artifact_sha_key' and contype = 'u')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_releases_source_sha_check' and definition like '%[A-F0-9]{64}%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_releases_artifact_sha_check' and definition like '%[A-F0-9]{64}%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_releases_count_check')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_releases_mapping_check')
      and exists (select 1 from functions where proname = 'fmz_phase4_enforce_off_release_state' and source like '%OFF release audit identity is immutable; use a successor release%')
      and exists (select 1 from indexes where index_name = 'nutrition_off_releases_predecessor_uidx' and indisunique),
      '{}'::jsonb
    ),
    (
      'off_odbl_metadata_contract',
      exists (select 1 from constraints where constraint_name = 'nutrition_off_releases_license_check' and definition like '%ODbL-1.0%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_products_license_check' and definition like '%ODbL-1.0%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_products_image_check' and definition like '%CC-BY-SA-4.0%'),
      '{}'::jsonb
    ),
    (
      'off_gtin_and_identity_contract',
      exists (select 1 from functions where proname = 'fmz_phase4_normalize_gtin14' and provolatile = 'i' and not prosecdef and source like '%char_length(v_barcode) not in (8, 12, 13, 14)%' and source like '%lpad(v_barcode, 14, ''0'')%')
      and exists (select 1 from functions where proname = 'fmz_phase4_normalize_catalog_text' and provolatile = 'i' and not prosecdef and source like '%regexp_replace%' and source like '%[^[:alnum:]]+%')
      and exists (select 1 from functions where proname = 'fmz_phase4_provider_candidate_uuid_v5' and provolatile = 'i' and not prosecdef and source like '%23440733-7e58-4c21-ad15-591eae6ab8ac%' and source like '%digest%' and source like '%sha1%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_products_barcode_check' and definition like '%fmz_phase4_normalize_gtin14%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_products_brand_check' and definition like '%fmz_phase4_normalize_catalog_text%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_product_names_normalized_check' and definition like '%fmz_phase4_normalize_catalog_text%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_products_identity_check' and definition like '%open_food_facts:%' and definition like '%fmz_phase4_provider_candidate_uuid_v5%'),
      '{}'::jsonb
    ),
    (
      'off_gtin_uniqueness',
      exists (select 1 from constraints where constraint_name = 'nutrition_off_products_gtin_key' and contype = 'u')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_products_identity_name_key' and contype = 'u'),
      '{}'::jsonb
    ),
    (
      'off_basis_and_macro_contract',
      exists (select 1 from constraints where constraint_name = 'nutrition_off_products_basis_check' and definition like '%per_100_g%per_100_ml%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_products_loggable_check' and definition like '%energy_kcal_100 IS NOT NULL%' and definition like '%protein_grams_100 IS NOT NULL%' and definition like '%carbohydrate_grams_100 IS NOT NULL%' and definition like '%fat_grams_100 IS NOT NULL%')
      and not exists (select 1 from constraints where table_name = 'nutrition_off_products' and definition ~* 'density|1[^0-9]*ml[^0-9]*=[^0-9]*1[^0-9]*g'),
      '{}'::jsonb
    ),
    (
      'off_quality_and_archive_contract',
      exists (select 1 from constraints where constraint_name = 'nutrition_off_products_quality_check' and definition like '%incomplete%complete%reviewed%quarantined%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_products_lifecycle_check' and definition like '%active%archived%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_off_products_quarantine_check' and definition like '%quarantine_reason%')
      and exists (select 1 from triggers where trigger_name = 'nutrition_off_products_20_sync_archive_state' and function_name = 'fmz_phase4_sync_off_archive_state')
      and exists (select 1 from triggers where trigger_name = 'nutrition_off_names_10_enforce_identity' and function_name = 'fmz_phase4_enforce_off_product_name_identity')
      and exists (select 1 from functions where proname = 'fmz_phase4_enforce_off_product_name_identity' and source like '%must match its product source revision and licence%'),
      '{}'::jsonb
    ),
    (
      'off_search_indexes',
      (select count(*) = 11 from indexes where index_name in (
        'nutrition_off_products_gtin_key',
        'nutrition_off_releases_current_uidx',
        'nutrition_off_products_active_name_prefix_idx',
        'nutrition_off_products_active_nl_name_prefix_idx',
        'nutrition_off_products_active_brand_prefix_idx',
        'nutrition_off_product_names_active_identity_uidx',
        'nutrition_off_product_names_preferred_uidx',
        'nutrition_off_product_names_active_exact_idx',
        'nutrition_off_product_names_active_prefix_idx',
        'nutrition_off_product_names_active_trgm_idx',
        'nutrition_off_product_names_product_idx'
      ))
      and exists (
        select 1 from indexes
        where index_name = 'nutrition_off_product_names_active_prefix_idx'
          and definition like '%(normalized_name text_pattern_ops, language_code%'
      )
      and not exists (
        select 1 from indexes
        where index_name = 'nutrition_off_products_active_search_trgm_idx'
      )
      and (select bool_and(indisvalid and indisready) from indexes where index_name like 'nutrition_off_%'),
      (select jsonb_agg(jsonb_build_object('name', index_name, 'unique', indisunique, 'partial', is_partial, 'predicate', predicate) order by index_name) from indexes where index_name like 'nutrition_off_%')
    ),
    (
      'off_rls_enabled',
      (select count(*) = 3 and bool_and(relrowsecurity) from table_security),
      (select jsonb_agg(to_jsonb(s) order by table_name) from table_security s)
    ),
    (
      'off_select_policies_exact',
      (select count(*) = 2 from policies)
      and exists (select 1 from policies where policyname = 'nutrition_off_products_select_loggable' and cmd = 'SELECT' and roles @> array['authenticated']::text[] and using_expression like '%complete%reviewed%')
      and exists (select 1 from policies where policyname = 'nutrition_off_product_names_select_loggable' and cmd = 'SELECT' and roles @> array['authenticated']::text[] and using_expression like '%nutrition_off_products%'),
      (select jsonb_agg(to_jsonb(p) order by policyname) from policies p)
    ),
    (
      'off_no_mutating_or_trainer_policy',
      not exists (select 1 from policies where cmd <> 'SELECT')
      and not exists (select 1 from policies where lower(policyname) like '%trainer%' or lower(using_expression) like '%trainer%'),
      '{}'::jsonb
    ),
    (
      'off_table_acl_least_privilege',
      not exists (select 1 from table_acl where grantee in ('anon','authenticated','PUBLIC','service_role'))
      and not exists (select 1 from column_acl where grantee in ('anon','PUBLIC','service_role'))
      and not exists (
        select 1 from column_acl
        where grantee = 'authenticated'
          and privilege_type <> 'SELECT'
      )
      and (select count(*) = 2 from authenticated_column_state)
      and (
        select count(*) = 2
          and bool_and(a.columns = e.columns)
        from expected_authenticated_columns e
        join authenticated_column_state a using (table_name)
      ),
      jsonb_build_object(
        'table_acl', (select jsonb_agg(to_jsonb(a) order by table_name, grantee, privilege_type) from table_acl a where grantee in ('anon','authenticated','PUBLIC','service_role')),
        'authenticated_columns', (select jsonb_agg(to_jsonb(a) order by table_name) from authenticated_column_state a)
      )
    ),
    (
      'typed_unified_search_signature',
      exists (
        select 1 from functions
        where proname = 'fmz_phase4_search_nutrition_catalog'
          and arguments = 'p_query text, p_locale text, p_page_size integer, p_after_rank integer, p_after_score numeric, p_after_name text, p_after_source text, p_after_id uuid'
          and result_type like 'TABLE(result_type text, source_provider text, source_id uuid, barcode text, display_name text, brand text, nutrition_basis text%'
          and not prosecdef
          and provolatile = 's'
          and configuration @> array['search_path=pg_catalog, public, extensions, pg_temp']::text[]
          and configuration @> array['pg_trgm.similarity_threshold=0.3']::text[]
      ),
      '{}'::jsonb
    ),
    (
      'typed_unified_search_sources_separate',
      exists (
        select 1 from functions
        where proname = 'fmz_phase4_search_nutrition_catalog'
          and source like '%custom_food%'
          and source like '%off_branded_food%'
          and source like '%generic_food%'
          and source like '%nutrition_off_products%'
          and source like '%food_aliases%'
      ),
      '{}'::jsonb
    ),
    (
      'typed_unified_search_quality_and_ranking',
      exists (
        select 1 from functions
        where proname = 'fmz_phase4_search_nutrition_catalog'
          and position('select ''off_branded_food'', p.id, 0' in source) > 0
          and position('select ''custom_food'', f.id, 10' in source) > position('select ''off_branded_food'', p.id, 0' in source)
          and position('select ''off_branded_food'', n.product_id, 20' in source) > position('select ''custom_food'', f.id, 10' in source)
          and position('select ''generic_food'', a.food_id, 50' in source) > position('select ''off_branded_food'', n.product_id, 20' in source)
          and source like '%quality_status in (''complete'', ''reviewed'')%'
          and source like '%normalized_name operator(extensions.%) v_query%'
          and source like '%normalized_alias operator(extensions.%) v_query%'
          and source like '%row_number() over%partition by bc.source_type, bc.candidate_id%'
      ),
      '{}'::jsonb
    ),
    (
      'typed_unified_search_keyset_and_bounds',
      exists (
        select 1 from functions
        where proname = 'fmz_phase4_search_nutrition_catalog'
          and source like '%complete catalog cursor required%'
          and source like '%empty_food_candidates%limit 100%'
          and source like '%prefix_off_name_candidates%limit 150%'
          and source like '%trigram_off_name_candidates%limit 200%'
          and source like '%trigram_generic_alias_candidates%limit 200%'
          and source like '%limit 1000%'
          and source like '%limit v_page_size%'
          and source like '%least(coalesce(p_page_size, 25), 25)%'
          and source like '%lower(btrim(h.display_name)) as page_name%'
          and source like '%(lower(btrim(h.display_name)), h.result_type, h.source_id)%'
          and source not like '%(lower(h.display_name), h.result_type, h.source_id)%'
          and source not like '%offset%'
      ),
      '{}'::jsonb
    ),
    (
      'local_barcode_lookup_contract',
      exists (
        select 1 from functions
        where proname = 'fmz_phase4_lookup_off_product_by_barcode'
          and arguments = 'p_barcode text'
          and not prosecdef
          and provolatile = 's'
          and source like '%fmz_phase4_normalize_gtin14%'
          and source like '%nutrition_off_products%'
          and source like '%quality_status in (''complete'', ''reviewed'')%'
          and source not like '%http%'
          and source not like '%nutrition-provider%'
      ),
      '{}'::jsonb
    ),
    (
      'off_function_acl',
      exists (select 1 from function_acl where proname = 'fmz_phase4_search_nutrition_catalog' and grantee = 'authenticated' and privilege_type = 'EXECUTE')
      and exists (select 1 from function_acl where proname = 'fmz_phase4_lookup_off_product_by_barcode' and grantee = 'authenticated' and privilege_type = 'EXECUTE')
      and exists (select 1 from function_acl where proname = 'fmz_phase4_normalize_gtin14' and grantee = 'authenticated' and privilege_type = 'EXECUTE')
      and exists (select 1 from function_acl where proname = 'fmz_phase4_normalize_catalog_text' and grantee = 'authenticated' and privilege_type = 'EXECUTE')
      and not exists (select 1 from function_acl where grantee in ('anon','PUBLIC'))
      and not exists (select 1 from function_acl where grantee = 'service_role')
      and not exists (
        select 1 from function_acl
        where proname in (
          'fmz_phase4_provider_candidate_uuid_v5',
          'fmz_phase4_enforce_off_release_state',
          'fmz_phase4_prevent_off_catalog_removal',
          'fmz_phase4_sync_off_archive_state',
          'fmz_phase4_enforce_off_product_identity',
          'fmz_phase4_enforce_off_product_name_identity'
        )
          and grantee in ('anon','authenticated','PUBLIC','service_role')
      )
      and not exists (
        select 1 from function_acl
        where grantee = 'authenticated'
          and proname not in ('fmz_phase4_normalize_gtin14','fmz_phase4_normalize_catalog_text','fmz_phase4_search_nutrition_catalog','fmz_phase4_lookup_off_product_by_barcode')
      ),
      (select jsonb_agg(to_jsonb(a) order by proname, grantee) from function_acl a where grantee in ('anon','authenticated','PUBLIC','service_role'))
    ),
    (
      'off_schema_starts_empty',
      (select release_count = 0 and product_count = 0 and name_count = 0 from row_counts),
      (select to_jsonb(r) from row_counts r)
    ),
    (
      'frozen_tables_present_with_rls',
      (select bool_and(exists and rls_enabled) from frozen_table_state),
      (select jsonb_agg(to_jsonb(s) order by table_name) from frozen_table_state s)
    ),
    (
      'frozen_functions_present',
      (select bool_and(exists) from frozen_function_state),
      (select jsonb_agg(to_jsonb(s) order by signature) from frozen_function_state s)
    ),
    (
      'off_no_remote_or_member_log_logic',
      not exists (
        select 1 from functions
        where source ~* '(world[.]openfoodfacts|fetch[(]|food_log_items|fmz_phase4_log_food_item|fmz_phase4_log_provider_food_item)'
      ),
      '{}'::jsonb
    )
),
result as (
  select jsonb_build_object(
    'overall_pass', bool_and(pass),
    'pass_count', count(*) filter (where pass),
    'fail_count', count(*) filter (where not pass),
    'checks', jsonb_agg(
      jsonb_build_object('check', check_name, 'pass', pass, 'details', details)
      order by check_name
    )
  ) as payload
  from checks
)
select pg_catalog.jsonb_pretty(payload) as verification_result
from result;
