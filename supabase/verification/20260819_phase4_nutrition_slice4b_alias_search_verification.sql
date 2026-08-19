-- FitMetZorge Phase 4 Nutrition Slice 4B post-migration verification.
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- One SELECT/CTE statement. No application RPC is invoked and no data is changed.

with
expected_columns(ordinal_position, column_name, formatted_type, not_null, default_fragment) as (
  values
    (1, 'id'::text, 'uuid'::text, true, null::text),
    (2, 'food_id', 'uuid', true, null),
    (3, 'language_code', 'text', true, null),
    (4, 'alias', 'text', true, null),
    (5, 'normalized_alias', 'text', true, null),
    (6, 'alias_type', 'text', true, null),
    (7, 'review_status', 'text', true, '''pending'''),
    (8, 'source_provider', 'text', false, null),
    (9, 'source_version', 'text', false, null),
    (10, 'license_code', 'text', false, null),
    (11, 'market_code', 'text', false, null),
    (12, 'priority', 'smallint', true, '0'),
    (13, 'provenance', 'jsonb', true, '''{}'''),
    (14, 'source_updated_at', 'timestamp with time zone', false, null),
    (15, 'metadata', 'jsonb', true, '''{}'''),
    (16, 'status', 'text', true, '''active'''),
    (17, 'created_at', 'timestamp with time zone', true, 'now()'),
    (18, 'updated_at', 'timestamp with time zone', true, 'now()'),
    (19, 'archived_at', 'timestamp with time zone', false, null)
),
actual_columns as (
  select
    a.attnum::integer as ordinal_position,
    a.attname::text as column_name,
    pg_catalog.format_type(a.atttypid, a.atttypmod)::text as formatted_type,
    a.attnotnull as not_null,
    pg_catalog.pg_get_expr(ad.adbin, ad.adrelid)::text as default_expression
  from pg_catalog.pg_attribute a
  join pg_catalog.pg_class c on c.oid = a.attrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  left join pg_catalog.pg_attrdef ad
    on ad.adrelid = a.attrelid
   and ad.adnum = a.attnum
  where n.nspname = 'public'
    and c.relname = 'food_aliases'
    and c.relkind = 'r'
    and a.attnum > 0
    and not a.attisdropped
),
column_mismatches as (
  select
    e.column_name as expected_column,
    a.column_name as actual_column,
    e.formatted_type as expected_type,
    a.formatted_type as actual_type,
    e.not_null as expected_not_null,
    a.not_null as actual_not_null,
    e.default_fragment,
    a.default_expression
  from expected_columns e
  full join actual_columns a using (ordinal_position)
  where e.column_name is null
     or a.column_name is null
     or e.column_name <> a.column_name
     or e.formatted_type <> a.formatted_type
     or e.not_null <> a.not_null
     or (
       e.default_fragment is null
       and a.default_expression is not null
     )
     or (
       e.default_fragment is not null
       and (
         a.default_expression is null
         or position(lower(e.default_fragment) in lower(a.default_expression)) = 0
       )
     )
),
expected_foods_columns(ordinal_position, column_name, formatted_type, not_null, default_fragment) as (
  values
    (1, 'id'::text, 'uuid'::text, true, null::text),
    (2, 'owner_user_id', 'uuid', false, null),
    (3, 'catalog_scope', 'text', true, null),
    (4, 'canonical_slug', 'text', false, null),
    (5, 'name', 'text', true, null),
    (6, 'brand', 'text', false, null),
    (7, 'barcode', 'text', false, null),
    (8, 'source_provider', 'text', true, null),
    (9, 'provider_food_id', 'text', false, null),
    (10, 'source_version', 'text', false, null),
    (11, 'license_code', 'text', false, null),
    (12, 'provenance', 'jsonb', true, '''{}'''),
    (13, 'quality_status', 'text', true, '''pending'''),
    (14, 'reference_amount', 'numeric(12,3)', true, null),
    (15, 'reference_unit', 'text', true, null),
    (16, 'reference_mass_grams', 'numeric(12,3)', false, null),
    (17, 'reference_volume_ml', 'numeric(12,3)', false, null),
    (18, 'density_g_per_ml', 'numeric(12,6)', false, null),
    (19, 'energy_kcal', 'numeric(12,3)', true, null),
    (20, 'protein_grams', 'numeric(12,3)', true, null),
    (21, 'carbohydrate_grams', 'numeric(12,3)', true, null),
    (22, 'fat_grams', 'numeric(12,3)', true, null),
    (23, 'fiber_grams', 'numeric(12,3)', false, null),
    (24, 'status', 'text', true, '''active'''),
    (25, 'source_updated_at', 'timestamp with time zone', false, null),
    (26, 'metadata', 'jsonb', true, '''{}'''),
    (27, 'created_at', 'timestamp with time zone', true, 'now()'),
    (28, 'updated_at', 'timestamp with time zone', true, 'now()'),
    (29, 'archived_at', 'timestamp with time zone', false, null)
),
actual_foods_columns as (
  select
    a.attnum::integer as ordinal_position,
    a.attname::text as column_name,
    pg_catalog.format_type(a.atttypid, a.atttypmod)::text as formatted_type,
    a.attnotnull as not_null,
    pg_catalog.pg_get_expr(ad.adbin, ad.adrelid)::text as default_expression
  from pg_catalog.pg_attribute a
  join pg_catalog.pg_class c on c.oid = a.attrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  left join pg_catalog.pg_attrdef ad
    on ad.adrelid = a.attrelid
   and ad.adnum = a.attnum
  where n.nspname = 'public'
    and c.relname = 'foods'
    and c.relkind = 'r'
    and a.attnum > 0
    and not a.attisdropped
),
foods_column_mismatches as (
  select
    e.column_name as expected_column,
    a.column_name as actual_column,
    e.formatted_type as expected_type,
    a.formatted_type as actual_type,
    e.not_null as expected_not_null,
    a.not_null as actual_not_null,
    e.default_fragment,
    a.default_expression
  from expected_foods_columns e
  full join actual_foods_columns a using (ordinal_position)
  where e.column_name is null
     or a.column_name is null
     or e.column_name <> a.column_name
     or e.formatted_type <> a.formatted_type
     or e.not_null <> a.not_null
     or (e.default_fragment is null and a.default_expression is not null)
     or (
       e.default_fragment is not null
       and (
         a.default_expression is null
         or position(lower(e.default_fragment) in lower(a.default_expression)) = 0
       )
     )
),
expected_foods_constraints(constraint_name) as (
  values
    ('foods_pkey'::text),
    ('foods_owner_user_id_fkey'),
    ('foods_catalog_scope_check'),
    ('foods_scope_owner_check'),
    ('foods_canonical_slug_check'),
    ('foods_name_check'),
    ('foods_brand_check'),
    ('foods_barcode_check'),
    ('foods_provider_food_id_check'),
    ('foods_source_version_check'),
    ('foods_license_code_check'),
    ('foods_json_objects_check'),
    ('foods_quality_status_check'),
    ('foods_reference_unit_check'),
    ('foods_reference_amount_check'),
    ('foods_reference_mass_check'),
    ('foods_reference_volume_check'),
    ('foods_density_check'),
    ('foods_energy_check'),
    ('foods_protein_check'),
    ('foods_carbohydrate_check'),
    ('foods_fat_check'),
    ('foods_fiber_check'),
    ('foods_status_check'),
    ('foods_archive_state_check')
),
actual_foods_constraints as (
  select c.conname::text as constraint_name
  from pg_catalog.pg_constraint c
  join pg_catalog.pg_class rel on rel.oid = c.conrelid
  join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
  where n.nspname = 'public'
    and rel.relname = 'foods'
),
foods_constraint_mismatches as (
  select e.constraint_name as expected_constraint, a.constraint_name as actual_constraint
  from expected_foods_constraints e
  full join actual_foods_constraints a using (constraint_name)
  where e.constraint_name is null or a.constraint_name is null
),
key_constraints as (
  select
    c.conname::text as constraint_name,
    c.contype,
    nr.nspname::text as referenced_schema,
    cr.relname::text as referenced_table,
    c.confdeltype,
    coalesce((
      select array_agg(a.attname::text order by u.ord)::text[]
      from unnest(c.conkey) with ordinality as u(attnum, ord)
      join pg_catalog.pg_attribute a
        on a.attrelid = c.conrelid
       and a.attnum = u.attnum
    ), array[]::text[]) as columns,
    coalesce((
      select array_agg(a.attname::text order by u.ord)::text[]
      from unnest(c.confkey) with ordinality as u(attnum, ord)
      join pg_catalog.pg_attribute a
        on a.attrelid = c.confrelid
       and a.attnum = u.attnum
    ), array[]::text[]) as referenced_columns
  from pg_catalog.pg_constraint c
  join pg_catalog.pg_class rel on rel.oid = c.conrelid
  join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
  left join pg_catalog.pg_class cr on cr.oid = c.confrelid
  left join pg_catalog.pg_namespace nr on nr.oid = cr.relnamespace
  where n.nspname = 'public'
    and rel.relname = 'food_aliases'
    and c.contype in ('p', 'f')
),
expected_checks(constraint_name, required_fragments) as (
  values
    ('food_aliases_language_code_check'::text, array['language_code', '''nl''', '''en''', '''de''']::text[]),
    ('food_aliases_alias_check', array['alias', 'btrim', '240']::text[]),
    ('food_aliases_normalized_alias_check', array['normalized_alias', 'lower', 'btrim', '240', 'alnum', 'space']::text[]),
    ('food_aliases_alias_type_check', array['alias_type', '''primary''', '''synonym''', '''provider''', '''search''', '''brand_variant''']::text[]),
    ('food_aliases_review_status_check', array['review_status', '''pending''', '''reviewed''', '''verified''']::text[]),
    ('food_aliases_source_provider_check', array['source_provider', '80']::text[]),
    ('food_aliases_source_version_check', array['source_version', '120']::text[]),
    ('food_aliases_license_code_check', array['license_code', '120']::text[]),
    ('food_aliases_source_contract_check', array['source_provider', 'source_version', 'license_code', 'source_updated_at', 'provenance']::text[]),
    ('food_aliases_market_code_check', array['market_code', '[A-Z]{2}']::text[]),
    ('food_aliases_priority_check', array['priority', '-100', '100']::text[]),
    ('food_aliases_json_objects_check', array['jsonb_typeof', 'provenance', 'metadata', '''object''']::text[]),
    ('food_aliases_status_check', array['status', '''active''', '''archived''']::text[]),
    ('food_aliases_archive_state_check', array['status', '''archived''', 'archived_at']::text[])
),
actual_checks as (
  select
    c.conname::text as constraint_name,
    pg_catalog.pg_get_expr(c.conbin, c.conrelid)::text as expression
  from pg_catalog.pg_constraint c
  join pg_catalog.pg_class rel on rel.oid = c.conrelid
  join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
  where n.nspname = 'public'
    and rel.relname = 'food_aliases'
    and c.contype = 'c'
),
check_mismatches as (
  select e.constraint_name, a.expression
  from expected_checks e
  left join actual_checks a using (constraint_name)
  where a.constraint_name is null
     or exists (
       select 1
       from unnest(e.required_fragments) as fragment(value)
       where position(lower(fragment.value) in lower(a.expression)) = 0
     )
  union all
  select a.constraint_name, a.expression
  from actual_checks a
  left join expected_checks e using (constraint_name)
  where e.constraint_name is null
),
expected_indexes(index_name, table_name, access_method, is_unique, required_key_fragments, required_predicate_fragments, required_opclass) as (
  values
    ('food_aliases_active_identity_uidx'::text, 'food_aliases'::text, 'btree'::text, true,
      array['food_id', 'language_code', 'normalized_alias', 'coalesce', 'market_code']::text[], array['status', '''active''']::text[], null::text),
    ('food_aliases_food_status_idx', 'food_aliases', 'btree', false,
      array['food_id', 'status', 'priority desc', 'id']::text[], array[]::text[], null),
    ('food_aliases_active_prefix_idx', 'food_aliases', 'btree', false,
      array['language_code', 'market_code', 'normalized_alias', 'priority desc', 'id']::text[], array['status', '''active''', 'review_status', '''reviewed''', '''verified''']::text[], 'text_pattern_ops'),
    ('food_aliases_active_trgm_idx', 'food_aliases', 'gin', false,
      array['normalized_alias']::text[], array['status', '''active''', 'review_status', '''reviewed''', '''verified''']::text[], 'gin_trgm_ops'),
    ('food_aliases_market_priority_idx', 'food_aliases', 'btree', false,
      array['market_code', 'language_code', 'priority desc', 'food_id']::text[], array['status', '''active''', 'review_status', '''reviewed''', '''verified''']::text[], null),
    ('foods_active_name_trgm_idx', 'foods', 'gin', false,
      array['lower(name)']::text[], array['status', '''active''']::text[], 'gin_trgm_ops'),
    ('foods_active_brand_trgm_idx', 'foods', 'gin', false,
      array['lower', 'coalesce', 'brand']::text[], array['status', '''active''', 'brand', 'is not null']::text[], 'gin_trgm_ops')
),
actual_indexes as (
  select
    idx.oid as index_oid,
    idx.relname::text as index_name,
    rel.relname::text as table_name,
    am.amname::text as access_method,
    i.indisunique as is_unique,
    i.indisvalid as is_valid,
    i.indisready as is_ready,
    coalesce(pg_catalog.pg_get_expr(i.indpred, i.indrelid), '')::text as predicate,
    coalesce((
      select array_agg(pg_catalog.pg_get_indexdef(i.indexrelid, k.position, true)::text order by k.position)::text[]
      from pg_catalog.generate_series(1, i.indnkeyatts) as k(position)
    ), array[]::text[]) as keys,
    coalesce((
      select array_agg(opc.opcname::text order by opc.opcname)::text[]
      from pg_catalog.pg_opclass opc
      where opc.oid = any(i.indclass::oid[])
    ), array[]::text[]) as opclasses
  from pg_catalog.pg_index i
  join pg_catalog.pg_class idx on idx.oid = i.indexrelid
  join pg_catalog.pg_class rel on rel.oid = i.indrelid
  join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
  join pg_catalog.pg_am am on am.oid = idx.relam
  where n.nspname = 'public'
    and idx.relname in (select index_name from expected_indexes)
),
index_mismatches as (
  select
    e.index_name,
    a.table_name,
    a.access_method,
    a.is_unique,
    a.is_valid,
    a.is_ready,
    a.keys,
    a.predicate,
    a.opclasses
  from expected_indexes e
  left join actual_indexes a using (index_name)
  where a.index_name is null
     or a.table_name <> e.table_name
     or a.access_method <> e.access_method
     or a.is_unique <> e.is_unique
     or not a.is_valid
     or not a.is_ready
     or exists (
       select 1
       from unnest(e.required_key_fragments) as fragment(value)
       where position(lower(fragment.value) in lower(array_to_string(a.keys, ' '))) = 0
     )
     or exists (
       select 1
       from unnest(e.required_predicate_fragments) as fragment(value)
       where position(lower(fragment.value) in lower(a.predicate)) = 0
     )
     or (
       e.required_opclass is not null
       and not (e.required_opclass = any(a.opclasses))
     )
),
alias_relation as (
  select c.oid, c.relrowsecurity, c.relacl, c.relowner
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname = 'food_aliases'
    and c.relkind = 'r'
),
alias_acl as (
  select
    acl.grantee,
    case
      when acl.grantee = 0 then 'PUBLIC'
      else coalesce(r.rolname::text, '<missing-role>')
    end as grantee_name,
    acl.privilege_type::text
  from alias_relation rel
  cross join lateral pg_catalog.aclexplode(
    coalesce(rel.relacl, pg_catalog.acldefault('r', rel.relowner))
  ) acl
  left join pg_catalog.pg_roles r on r.oid = acl.grantee
),
alias_policies as (
  select
    p.polname::text as policy_name,
    p.polcmd,
    p.polpermissive,
    coalesce(pg_catalog.pg_get_expr(p.polqual, p.polrelid), '')::text as using_expression,
    coalesce(pg_catalog.pg_get_expr(p.polwithcheck, p.polrelid), '')::text as check_expression,
    coalesce((
      select array_agg(r.rolname::text order by r.rolname)::text[]
      from unnest(p.polroles) as role_oid(role_id)
      join pg_catalog.pg_roles r on r.oid = role_oid.role_id
    ), array[]::text[]) as roles
  from pg_catalog.pg_policy p
  join alias_relation rel on rel.oid = p.polrelid
),
alias_triggers as (
  select
    t.tgname::text as trigger_name,
    p.proname::text as function_name,
    t.tgenabled,
    t.tgtype
  from pg_catalog.pg_trigger t
  join alias_relation rel on rel.oid = t.tgrelid
  join pg_catalog.pg_proc p on p.oid = t.tgfoid
  where not t.tgisinternal
),
helper_functions as (
  select
    p.proname::text as function_name,
    p.prosecdef as security_definer,
    p.proconfig,
    pg_catalog.oidvectortypes(p.proargtypes)::text as argument_types
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname in ('fmz_phase4_sync_archive_state', 'fmz_phase4_touch_updated_at')
),
atomic_function as (
  select
    p.oid,
    p.prosecdef as security_definer,
    p.proconfig,
    p.proacl,
    p.proowner,
    pg_catalog.oidvectortypes(p.proargtypes)::text as argument_types,
    p.prosrc::text as source
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname = 'fmz_phase4_replace_food_log_item'
),
atomic_acl as (
  select
    acl.grantee,
    case
      when acl.grantee = 0 then 'PUBLIC'
      else coalesce(r.rolname::text, '<missing-role>')
    end as grantee_name,
    acl.privilege_type::text
  from atomic_function f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) acl
  left join pg_catalog.pg_roles r on r.oid = acl.grantee
),
search_function as (
  select
    p.oid,
    p.prosecdef as security_definer,
    p.provolatile,
    p.proretset,
    p.prorettype,
    p.proconfig,
    p.proacl,
    p.proowner,
    pg_catalog.oidvectortypes(p.proargtypes)::text as argument_types,
    p.prosrc::text as source
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname = 'fmz_phase4_search_foods'
),
search_acl as (
  select
    acl.grantee,
    case
      when acl.grantee = 0 then 'PUBLIC'
      else coalesce(r.rolname::text, '<missing-role>')
    end as grantee_name,
    acl.privilege_type::text
  from search_function f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) acl
  left join pg_catalog.pg_roles r on r.oid = acl.grantee
),
provider_operational_relations as (
  select n.nspname::text as schema_name, c.relname::text as relation_name, c.relkind
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname in ('public', 'private')
    and c.relkind in ('r', 'p', 'v', 'm', 'f')
    and (
      c.relname in (
        'provider_cache',
        'provider_query_cache',
        'provider_import_jobs',
        'provider_rate_limits',
        'food_provider_cache',
        'food_provider_query_cache',
        'food_provider_import_jobs',
        'food_provider_rate_limits'
      )
      or c.relname like 'food_provider_%cache%'
      or c.relname like 'food_provider_%import%'
      or c.relname like 'food_provider_%rate%limit%'
    )
),
deferred_phase4_functions as (
  select n.nspname::text as schema_name, p.proname::text as function_name
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname in ('public', 'private')
    and (
      p.proname = 'fmz_phase4_search_foods_v2'
      or p.proname like 'fmz_phase4_%provider%'
      or p.proname like 'fmz_phase4_%import%'
    )
),
expected_guard_tables(table_name) as (
  values
    ('profiles'::text),
    ('coach_workspaces'),
    ('user_settings'),
    ('user_onboarding'),
    ('entitlements'),
    ('recovery_logs'),
    ('training_plans'),
    ('training_plan_days'),
    ('training_plan_exercises'),
    ('workout_sessions'),
    ('workout_set_logs'),
    ('nutrition_preferences'),
    ('foods'),
    ('food_portions'),
    ('nutrition_targets'),
    ('food_logs'),
    ('food_log_items')
),
guard_tables as (
  select c.relname::text as table_name, c.relrowsecurity
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and c.relname in (select table_name from expected_guard_tables)
),
catalog_counts as (
  select
    (select count(*) from public.food_aliases) as alias_count,
    (select count(*) from public.foods where catalog_scope = 'canonical') as canonical_food_count,
    (select count(*) from public.foods where source_provider <> 'custom_user') as provider_food_count
),
checks(check_name, pass, details) as (
  select
    'staging_project_guard',
    current_database() = 'postgres',
    jsonb_build_object(
      'expected_project_ref', 'mokxyyullfhkfalopbzd',
      'note', 'Run only in the owner-confirmed staging project; project ref is not exposed by PostgreSQL metadata.'
    )
  union all
  select
    'pg_trgm_extension',
    exists (
      select 1
      from pg_catalog.pg_extension e
      join pg_catalog.pg_namespace n on n.oid = e.extnamespace
      where e.extname = 'pg_trgm'
        and n.nspname = 'extensions'
    ),
    coalesce((
      select jsonb_build_object('schema', n.nspname, 'version', e.extversion)
      from pg_catalog.pg_extension e
      join pg_catalog.pg_namespace n on n.oid = e.extnamespace
      where e.extname = 'pg_trgm'
    ), '{}'::jsonb)
  union all
  select
    'food_aliases_table',
    exists (select 1 from alias_relation),
    jsonb_build_object('exists', exists (select 1 from alias_relation))
  union all
  select
    'food_aliases_columns',
    not exists (select 1 from column_mismatches)
      and (select count(*) from actual_columns) = 19,
    jsonb_build_object(
      'expected_count', 19,
      'actual_count', (select count(*) from actual_columns),
      'mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from column_mismatches m), '[]'::jsonb)
    )
  union all
  select
    'food_aliases_primary_key',
    exists (
      select 1 from key_constraints
      where constraint_name = 'food_aliases_pkey'
        and contype = 'p'
        and columns = array['id']::text[]
    ),
    coalesce((select to_jsonb(k) from key_constraints k where constraint_name = 'food_aliases_pkey'), '{}'::jsonb)
  union all
  select
    'food_aliases_foreign_key',
    exists (
      select 1 from key_constraints
      where constraint_name = 'food_aliases_food_id_fkey'
        and contype = 'f'
        and columns = array['food_id']::text[]
        and referenced_schema = 'public'
        and referenced_table = 'foods'
        and referenced_columns = array['id']::text[]
        and confdeltype = 'c'
    ),
    coalesce((select to_jsonb(k) from key_constraints k where constraint_name = 'food_aliases_food_id_fkey'), '{}'::jsonb)
  union all
  select
    'food_aliases_check_constraints',
    not exists (select 1 from check_mismatches)
      and (select count(*) from actual_checks) = 14,
    jsonb_build_object(
      'expected_count', 14,
      'actual_count', (select count(*) from actual_checks),
      'mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from check_mismatches m), '[]'::jsonb)
    )
  union all
  select
    'slice4b_indexes',
    not exists (select 1 from index_mismatches)
      and (select count(*) from actual_indexes) = 7,
    jsonb_build_object(
      'expected_count', 7,
      'actual_count', (select count(*) from actual_indexes),
      'mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from index_mismatches m), '[]'::jsonb)
    )
  union all
  select
    'food_aliases_rls',
    coalesce((select relrowsecurity from alias_relation), false),
    jsonb_build_object('enabled', coalesce((select relrowsecurity from alias_relation), false))
  union all
  select
    'food_aliases_select_policy',
    (select count(*) from alias_policies) = 1
      and exists (
        select 1
        from alias_policies
        where policy_name = 'food_aliases_select_visible'
          and polcmd = 'r'
          and polpermissive
          and roles = array['authenticated']::text[]
          and check_expression = ''
          and position('status' in lower(using_expression)) > 0
          and position('review_status' in lower(using_expression)) > 0
          and position('reviewed' in lower(using_expression)) > 0
          and position('verified' in lower(using_expression)) > 0
          and position('catalog_scope' in lower(using_expression)) > 0
          and position('canonical' in lower(using_expression)) > 0
          and position('custom' in lower(using_expression)) > 0
          and position('auth.uid' in lower(using_expression)) > 0
      ),
    coalesce((select jsonb_agg(to_jsonb(p)) from alias_policies p), '[]'::jsonb)
  union all
  select
    'food_aliases_no_write_or_trainer_policy',
    not exists (
      select 1
      from alias_policies
      where polcmd <> 'r'
         or lower(policy_name) like '%trainer%'
         or lower(using_expression) like '%trainer%'
         or lower(check_expression) like '%trainer%'
    ),
    jsonb_build_object('policy_count', (select count(*) from alias_policies))
  union all
  select
    'food_aliases_authenticated_select_only',
    coalesce((
      select array_agg(privilege_type order by privilege_type)::text[]
      from alias_acl
      where grantee_name = 'authenticated'
    ), array[]::text[]) = array['SELECT']::text[],
    jsonb_build_object(
      'privileges', coalesce((
        select jsonb_agg(privilege_type order by privilege_type)
        from alias_acl
        where grantee_name = 'authenticated'
      ), '[]'::jsonb)
    )
  union all
  select
    'food_aliases_anon_public_none',
    not exists (
      select 1 from alias_acl
      where grantee_name in ('anon', 'PUBLIC')
    ),
    coalesce((
      select jsonb_agg(to_jsonb(a))
      from alias_acl a
      where grantee_name in ('anon', 'PUBLIC')
    ), '[]'::jsonb)
  union all
  select
    'food_aliases_triggers',
    (select count(*) from alias_triggers) = 2
      and exists (
        select 1 from alias_triggers
        where trigger_name = 'food_aliases_10_sync_archive_state'
          and function_name = 'fmz_phase4_sync_archive_state'
          and tgenabled = 'O'
          and (tgtype::integer & 1) = 1
          and (tgtype::integer & 2) = 2
          and (tgtype::integer & 4) = 4
          and (tgtype::integer & 16) = 16
      )
      and exists (
        select 1 from alias_triggers
        where trigger_name = 'food_aliases_90_touch_updated_at'
          and function_name = 'fmz_phase4_touch_updated_at'
          and tgenabled = 'O'
          and (tgtype::integer & 1) = 1
          and (tgtype::integer & 2) = 2
          and (tgtype::integer & 16) = 16
      ),
    coalesce((select jsonb_agg(to_jsonb(t)) from alias_triggers t), '[]'::jsonb)
  union all
  select
    'food_aliases_helper_security',
    (select count(*) from helper_functions) = 2
      and not exists (
        select 1 from helper_functions
        where security_definer
          or argument_types <> ''
          or not coalesce('search_path=pg_catalog, public, pg_temp' = any(proconfig), false)
      ),
    coalesce((select jsonb_agg(to_jsonb(f)) from helper_functions f), '[]'::jsonb)
  union all
  select
    'foods_frozen_column_contract',
    not exists (select 1 from foods_column_mismatches)
      and (select count(*) from actual_foods_columns) = 29,
    jsonb_build_object(
      'expected_count', 29,
      'actual_count', (select count(*) from actual_foods_columns),
      'mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from foods_column_mismatches m), '[]'::jsonb)
    )
  union all
  select
    'foods_frozen_constraint_contract',
    not exists (select 1 from foods_constraint_mismatches)
      and (select count(*) from actual_foods_constraints) = 25,
    jsonb_build_object(
      'expected_count', 25,
      'actual_count', (select count(*) from actual_foods_constraints),
      'mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from foods_constraint_mismatches m), '[]'::jsonb)
    )
  union all
  select
    'frozen_search_rpc_guard',
    (select count(*) from search_function) = 1
      and exists (
        select 1
        from search_function
        where not security_definer
          and provolatile = 's'
          and proretset
          and prorettype = 'public.foods'::regtype
          and argument_types = 'text, integer, text, uuid'
          and coalesce('search_path=pg_catalog, public, pg_temp' = any(proconfig), false)
          and position('auth.uid()' in source) > 0
          and position('lower(f.name) like v_query' in source) > 0
          and position('lower(coalesce(f.brand' in source) > 0
          and position('f.barcode = btrim' in source) > 0
          and position('(lower(f.name), f.id) > (lower(p_after_name), p_after_id)' in source) > 0
          and position('order by lower(f.name), f.id' in source) > 0
          and position('least(coalesce(p_page_size, 25), 50)' in source) > 0
      )
      and coalesce((
        select array_agg(privilege_type order by privilege_type)::text[]
        from search_acl
        where grantee_name = 'authenticated'
      ), array[]::text[]) = array['EXECUTE']::text[]
      and not exists (
        select 1 from search_acl
        where grantee_name in ('anon', 'PUBLIC')
      ),
    jsonb_build_object(
      'function_count', (select count(*) from search_function),
      'authenticated_privileges', coalesce((
        select jsonb_agg(privilege_type order by privilege_type)
        from search_acl
        where grantee_name = 'authenticated'
      ), '[]'::jsonb),
      'anon_public_privileges', coalesce((
        select jsonb_agg(to_jsonb(a))
        from search_acl a
        where grantee_name in ('anon', 'PUBLIC')
      ), '[]'::jsonb)
    )
  union all
  select
    'provider_operations_deferred',
    not exists (select 1 from provider_operational_relations)
      and not exists (select 1 from deferred_phase4_functions),
    jsonb_build_object(
      'relations', coalesce((select jsonb_agg(to_jsonb(r)) from provider_operational_relations r), '[]'::jsonb),
      'functions', coalesce((select jsonb_agg(to_jsonb(f)) from deferred_phase4_functions f), '[]'::jsonb)
    )
  union all
  select
    'no_catalog_or_alias_rows_imported',
    alias_count = 0
      and canonical_food_count = 0
      and provider_food_count = 0,
    to_jsonb(catalog_counts)
  from catalog_counts
  union all
  select
    'slice1_phase_guards',
    (select count(*) from guard_tables) = (select count(*) from expected_guard_tables)
      and not exists (select 1 from guard_tables where not relrowsecurity),
    jsonb_build_object(
      'expected_count', (select count(*) from expected_guard_tables),
      'actual_count', (select count(*) from guard_tables),
      'missing', coalesce((
        select jsonb_agg(e.table_name)
        from expected_guard_tables e
        left join guard_tables g using (table_name)
        where g.table_name is null
      ), '[]'::jsonb),
      'rls_disabled', coalesce((
        select jsonb_agg(table_name)
        from guard_tables
        where not relrowsecurity
      ), '[]'::jsonb)
    )
  union all
  select
    'atomic_replacement_rpc_guard',
    (select count(*) from atomic_function) = 1
      and exists (
        select 1
        from atomic_function
        where security_definer
          and argument_types = 'uuid, uuid, uuid, timestamp with time zone, text, uuid, uuid, numeric, text, text'
          and 'search_path=pg_catalog, public, pg_temp' = any(proconfig)
          and position('auth.uid()' in source) > 0
          and position('pg_advisory_xact_lock' in source) > 0
          and position('fmz_phase4_day_payload' in source) > 0
      )
      and coalesce((
        select array_agg(privilege_type order by privilege_type)::text[]
        from atomic_acl
        where grantee_name = 'authenticated'
      ), array[]::text[]) = array['EXECUTE']::text[]
      and not exists (
        select 1 from atomic_acl
        where grantee_name in ('anon', 'PUBLIC')
      ),
    jsonb_build_object(
      'function_count', (select count(*) from atomic_function),
      'authenticated_privileges', coalesce((
        select jsonb_agg(privilege_type order by privilege_type)
        from atomic_acl
        where grantee_name = 'authenticated'
      ), '[]'::jsonb),
      'anon_public_privileges', coalesce((
        select jsonb_agg(to_jsonb(a))
        from atomic_acl a
        where grantee_name in ('anon', 'PUBLIC')
      ), '[]'::jsonb)
    )
),
result as (
  select
    coalesce(bool_and(pass), false) as overall_pass,
    jsonb_agg(
      jsonb_build_object(
        'check', check_name,
        'pass', pass,
        'details', details
      )
      order by check_name
    ) as checks
  from checks
)
select jsonb_pretty(
  jsonb_build_object(
    'project_ref', 'mokxyyullfhkfalopbzd',
    'scope', 'phase4_nutrition_slice4b_alias_search',
    'read_only', true,
    'overall_pass', overall_pass,
    'checks', checks
  )
) as verification_result
from result;
