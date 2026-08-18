-- FitMetZorge Phase 4 Nutrition Schema Slice 1 post-migration verification.
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- This artifact is one SELECT/CTE statement and does not invoke application RPCs.

with
expected_tables(table_name) as (
  values
    ('nutrition_preferences'::text),
    ('foods'::text),
    ('food_portions'::text),
    ('nutrition_targets'::text),
    ('food_logs'::text),
    ('food_log_items'::text)
),
actual_phase4_tables(table_name) as (
  select c.relname::text
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and (
      c.relname like 'nutrition_%'
      or c.relname in ('foods', 'food_portions', 'food_logs', 'food_log_items')
    )
),
expected_columns(table_name, ordinal_position, column_name, formatted_type, not_null, default_fragment) as (
  values
    ('nutrition_preferences', 1, 'user_id', 'uuid', true, null),
    ('nutrition_preferences', 2, 'timezone_name', 'text', true, '''UTC'''),
    ('nutrition_preferences', 3, 'created_at', 'timestamp with time zone', true, 'now()'),
    ('nutrition_preferences', 4, 'updated_at', 'timestamp with time zone', true, 'now()'),

    ('foods', 1, 'id', 'uuid', true, null),
    ('foods', 2, 'owner_user_id', 'uuid', false, null),
    ('foods', 3, 'catalog_scope', 'text', true, null),
    ('foods', 4, 'canonical_slug', 'text', false, null),
    ('foods', 5, 'name', 'text', true, null),
    ('foods', 6, 'brand', 'text', false, null),
    ('foods', 7, 'barcode', 'text', false, null),
    ('foods', 8, 'source_provider', 'text', true, null),
    ('foods', 9, 'provider_food_id', 'text', false, null),
    ('foods', 10, 'source_version', 'text', false, null),
    ('foods', 11, 'license_code', 'text', false, null),
    ('foods', 12, 'provenance', 'jsonb', true, '''{}'''),
    ('foods', 13, 'quality_status', 'text', true, '''pending'''),
    ('foods', 14, 'reference_amount', 'numeric(12,3)', true, null),
    ('foods', 15, 'reference_unit', 'text', true, null),
    ('foods', 16, 'reference_mass_grams', 'numeric(12,3)', false, null),
    ('foods', 17, 'reference_volume_ml', 'numeric(12,3)', false, null),
    ('foods', 18, 'density_g_per_ml', 'numeric(12,6)', false, null),
    ('foods', 19, 'energy_kcal', 'numeric(12,3)', true, null),
    ('foods', 20, 'protein_grams', 'numeric(12,3)', true, null),
    ('foods', 21, 'carbohydrate_grams', 'numeric(12,3)', true, null),
    ('foods', 22, 'fat_grams', 'numeric(12,3)', true, null),
    ('foods', 23, 'fiber_grams', 'numeric(12,3)', false, null),
    ('foods', 24, 'status', 'text', true, '''active'''),
    ('foods', 25, 'source_updated_at', 'timestamp with time zone', false, null),
    ('foods', 26, 'metadata', 'jsonb', true, '''{}'''),
    ('foods', 27, 'created_at', 'timestamp with time zone', true, 'now()'),
    ('foods', 28, 'updated_at', 'timestamp with time zone', true, 'now()'),
    ('foods', 29, 'archived_at', 'timestamp with time zone', false, null),

    ('food_portions', 1, 'id', 'uuid', true, null),
    ('food_portions', 2, 'food_id', 'uuid', true, null),
    ('food_portions', 3, 'label', 'text', true, null),
    ('food_portions', 4, 'amount', 'numeric(12,3)', true, '1'),
    ('food_portions', 5, 'unit', 'text', true, null),
    ('food_portions', 6, 'equivalent_amount', 'numeric(12,3)', true, null),
    ('food_portions', 7, 'equivalent_unit', 'text', true, null),
    ('food_portions', 8, 'is_default', 'boolean', true, 'false'),
    ('food_portions', 9, 'sort_order', 'integer', true, '0'),
    ('food_portions', 10, 'status', 'text', true, '''active'''),
    ('food_portions', 11, 'metadata', 'jsonb', true, '''{}'''),
    ('food_portions', 12, 'created_at', 'timestamp with time zone', true, 'now()'),
    ('food_portions', 13, 'updated_at', 'timestamp with time zone', true, 'now()'),
    ('food_portions', 14, 'archived_at', 'timestamp with time zone', false, null),

    ('nutrition_targets', 1, 'id', 'uuid', true, null),
    ('nutrition_targets', 2, 'user_id', 'uuid', true, null),
    ('nutrition_targets', 3, 'target_context', 'text', true, '''daily'''),
    ('nutrition_targets', 4, 'energy_kcal', 'numeric(8,2)', true, null),
    ('nutrition_targets', 5, 'protein_grams', 'numeric(8,2)', true, null),
    ('nutrition_targets', 6, 'carbohydrate_grams', 'numeric(8,2)', true, null),
    ('nutrition_targets', 7, 'fat_grams', 'numeric(8,2)', true, null),
    ('nutrition_targets', 8, 'fiber_grams', 'numeric(8,2)', false, null),
    ('nutrition_targets', 9, 'source_type', 'text', true, null),
    ('nutrition_targets', 10, 'created_by_user_id', 'uuid', false, null),
    ('nutrition_targets', 11, 'status', 'text', true, null),
    ('nutrition_targets', 12, 'effective_from', 'date', true, null),
    ('nutrition_targets', 13, 'effective_to', 'date', false, null),
    ('nutrition_targets', 14, 'accepted_by_user_id', 'uuid', false, null),
    ('nutrition_targets', 15, 'accepted_at', 'timestamp with time zone', false, null),
    ('nutrition_targets', 16, 'supersedes_target_id', 'uuid', false, null),
    ('nutrition_targets', 17, 'request_id', 'uuid', true, null),
    ('nutrition_targets', 18, 'notes', 'text', false, null),
    ('nutrition_targets', 19, 'metadata', 'jsonb', true, '''{}'''),
    ('nutrition_targets', 20, 'created_at', 'timestamp with time zone', true, 'now()'),
    ('nutrition_targets', 21, 'updated_at', 'timestamp with time zone', true, 'now()'),
    ('nutrition_targets', 22, 'archived_at', 'timestamp with time zone', false, null),

    ('food_logs', 1, 'id', 'uuid', true, null),
    ('food_logs', 2, 'user_id', 'uuid', true, null),
    ('food_logs', 3, 'log_date', 'date', true, null),
    ('food_logs', 4, 'timezone_name', 'text', true, null),
    ('food_logs', 5, 'timezone_offset_minutes', 'smallint', true, null),
    ('food_logs', 6, 'target_id', 'uuid', false, null),
    ('food_logs', 7, 'target_energy_kcal_snapshot', 'numeric(8,2)', false, null),
    ('food_logs', 8, 'target_protein_grams_snapshot', 'numeric(8,2)', false, null),
    ('food_logs', 9, 'target_carbohydrate_grams_snapshot', 'numeric(8,2)', false, null),
    ('food_logs', 10, 'target_fat_grams_snapshot', 'numeric(8,2)', false, null),
    ('food_logs', 11, 'target_fiber_grams_snapshot', 'numeric(8,2)', false, null),
    ('food_logs', 12, 'status', 'text', true, '''active'''),
    ('food_logs', 13, 'source', 'text', true, '''phase4_member'''),
    ('food_logs', 14, 'metadata', 'jsonb', true, '''{}'''),
    ('food_logs', 15, 'created_at', 'timestamp with time zone', true, 'now()'),
    ('food_logs', 16, 'updated_at', 'timestamp with time zone', true, 'now()'),
    ('food_logs', 17, 'archived_at', 'timestamp with time zone', false, null),

    ('food_log_items', 1, 'id', 'uuid', true, null),
    ('food_log_items', 2, 'user_id', 'uuid', true, null),
    ('food_log_items', 3, 'food_log_id', 'uuid', true, null),
    ('food_log_items', 4, 'food_id', 'uuid', false, null),
    ('food_log_items', 5, 'food_portion_id', 'uuid', false, null),
    ('food_log_items', 6, 'meal_moment', 'text', true, null),
    ('food_log_items', 7, 'sort_order', 'integer', true, null),
    ('food_log_items', 8, 'consumed_quantity', 'numeric(12,3)', true, null),
    ('food_log_items', 9, 'consumed_unit', 'text', true, null),
    ('food_log_items', 10, 'food_name_snapshot', 'text', true, null),
    ('food_log_items', 11, 'brand_snapshot', 'text', false, null),
    ('food_log_items', 12, 'reference_amount_snapshot', 'numeric(12,3)', true, null),
    ('food_log_items', 13, 'reference_unit_snapshot', 'text', true, null),
    ('food_log_items', 14, 'portion_label_snapshot', 'text', false, null),
    ('food_log_items', 15, 'portion_equivalent_amount_snapshot', 'numeric(12,3)', false, null),
    ('food_log_items', 16, 'portion_equivalent_unit_snapshot', 'text', false, null),
    ('food_log_items', 17, 'density_g_per_ml_snapshot', 'numeric(12,6)', false, null),
    ('food_log_items', 18, 'calculation_basis', 'text', true, null),
    ('food_log_items', 19, 'energy_kcal_snapshot', 'numeric(12,3)', true, null),
    ('food_log_items', 20, 'protein_grams_snapshot', 'numeric(12,3)', true, null),
    ('food_log_items', 21, 'carbohydrate_grams_snapshot', 'numeric(12,3)', true, null),
    ('food_log_items', 22, 'fat_grams_snapshot', 'numeric(12,3)', true, null),
    ('food_log_items', 23, 'fiber_grams_snapshot', 'numeric(12,3)', false, null),
    ('food_log_items', 24, 'source_provider_snapshot', 'text', true, null),
    ('food_log_items', 25, 'provider_food_id_snapshot', 'text', false, null),
    ('food_log_items', 26, 'source_version_snapshot', 'text', false, null),
    ('food_log_items', 27, 'provenance_snapshot', 'jsonb', true, '''{}'''),
    ('food_log_items', 28, 'notes', 'text', false, null),
    ('food_log_items', 29, 'status', 'text', true, '''active'''),
    ('food_log_items', 30, 'request_id', 'uuid', true, null),
    ('food_log_items', 31, 'consumed_at', 'timestamp with time zone', false, null),
    ('food_log_items', 32, 'metadata', 'jsonb', true, '''{}'''),
    ('food_log_items', 33, 'created_at', 'timestamp with time zone', true, 'now()'),
    ('food_log_items', 34, 'updated_at', 'timestamp with time zone', true, 'now()'),
    ('food_log_items', 35, 'archived_at', 'timestamp with time zone', false, null)
),
actual_columns as (
  select
    c.relname::text as table_name,
    a.attnum::integer as ordinal_position,
    a.attname::text as column_name,
    pg_catalog.format_type(a.atttypid, a.atttypmod)::text as formatted_type,
    a.attnotnull as not_null,
    pg_catalog.pg_get_expr(ad.adbin, ad.adrelid)::text as default_expr
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  join pg_catalog.pg_attribute a on a.attrelid = c.oid
  left join pg_catalog.pg_attrdef ad
    on ad.adrelid = a.attrelid and ad.adnum = a.attnum
  where n.nspname = 'public'
    and c.relname in (select table_name from expected_tables)
    and c.relkind = 'r'
    and a.attnum > 0
    and not a.attisdropped
),
column_mismatches as (
  select
    e.table_name,
    e.column_name,
    e.ordinal_position,
    e.formatted_type as expected_type,
    a.formatted_type as actual_type,
    e.not_null as expected_not_null,
    a.not_null as actual_not_null,
    e.default_fragment,
    a.default_expr
  from expected_columns e
  left join actual_columns a
    on a.table_name = e.table_name
   and a.column_name = e.column_name
   and a.ordinal_position = e.ordinal_position
  where a.column_name is null
     or a.formatted_type is distinct from e.formatted_type
     or a.not_null is distinct from e.not_null
     or (
       (e.default_fragment is null and a.default_expr is not null)
       or (e.default_fragment is not null and position(e.default_fragment in coalesce(a.default_expr, '')) = 0)
     )
),
unexpected_columns as (
  select a.*
  from actual_columns a
  left join expected_columns e
    on e.table_name = a.table_name
   and e.column_name = a.column_name
   and e.ordinal_position = a.ordinal_position
  where e.column_name is null
),
expected_constraint_names(constraint_name) as (
  values
    ('nutrition_preferences_pkey'::text),
    ('nutrition_preferences_timezone_name_check'),
    ('foods_pkey'),
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
    ('foods_archive_state_check'),
    ('food_portions_pkey'),
    ('food_portions_label_check'),
    ('food_portions_amount_check'),
    ('food_portions_unit_check'),
    ('food_portions_equivalent_amount_check'),
    ('food_portions_equivalent_unit_check'),
    ('food_portions_sort_order_check'),
    ('food_portions_status_check'),
    ('food_portions_metadata_check'),
    ('food_portions_archive_state_check'),
    ('nutrition_targets_pkey'),
    ('nutrition_targets_context_check'),
    ('nutrition_targets_energy_check'),
    ('nutrition_targets_protein_check'),
    ('nutrition_targets_carbohydrate_check'),
    ('nutrition_targets_fat_check'),
    ('nutrition_targets_fiber_check'),
    ('nutrition_targets_source_type_check'),
    ('nutrition_targets_status_check'),
    ('nutrition_targets_effective_range_check'),
    ('nutrition_targets_notes_check'),
    ('nutrition_targets_metadata_check'),
    ('nutrition_targets_acceptance_check'),
    ('nutrition_targets_member_authority_check'),
    ('nutrition_targets_archive_state_check'),
    ('food_logs_pkey'),
    ('food_logs_timezone_name_check'),
    ('food_logs_timezone_offset_check'),
    ('food_logs_target_energy_check'),
    ('food_logs_target_protein_check'),
    ('food_logs_target_carbohydrate_check'),
    ('food_logs_target_fat_check'),
    ('food_logs_target_fiber_check'),
    ('food_logs_status_check'),
    ('food_logs_source_check'),
    ('food_logs_metadata_check'),
    ('food_logs_archive_state_check'),
    ('food_logs_user_date_unique'),
    ('food_log_items_pkey'),
    ('food_log_items_meal_moment_check'),
    ('food_log_items_sort_order_check'),
    ('food_log_items_consumed_quantity_check'),
    ('food_log_items_consumed_unit_check'),
    ('food_log_items_food_name_check'),
    ('food_log_items_brand_check'),
    ('food_log_items_reference_amount_check'),
    ('food_log_items_reference_unit_check'),
    ('food_log_items_portion_snapshot_check'),
    ('food_log_items_density_check'),
    ('food_log_items_calculation_basis_check'),
    ('food_log_items_calculation_snapshot_check'),
    ('food_log_items_energy_check'),
    ('food_log_items_protein_check'),
    ('food_log_items_carbohydrate_check'),
    ('food_log_items_fat_check'),
    ('food_log_items_fiber_check'),
    ('food_log_items_provider_id_check'),
    ('food_log_items_source_version_check'),
    ('food_log_items_json_objects_check'),
    ('food_log_items_notes_check'),
    ('food_log_items_status_check'),
    ('food_log_items_archive_state_check')
),
actual_constraints as (
  select
    con.conname::text as constraint_name,
    c.relname::text as table_name,
    con.contype,
    pg_catalog.pg_get_constraintdef(con.oid, true)::text as definition
  from pg_catalog.pg_constraint con
  join pg_catalog.pg_class c on c.oid = con.conrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname in (select table_name from expected_tables)
),
missing_constraints as (
  select e.constraint_name
  from expected_constraint_names e
  left join actual_constraints a using (constraint_name)
  where a.constraint_name is null
),
unexpected_non_fk_constraints as (
  select a.constraint_name, a.table_name, a.contype, a.definition
  from actual_constraints a
  left join expected_constraint_names e using (constraint_name)
  where a.contype <> 'f'
    and e.constraint_name is null
),
constraint_type_mismatches as (
  select a.constraint_name, a.table_name, a.contype, a.definition
  from actual_constraints a
  join expected_constraint_names e using (constraint_name)
  where a.contype is distinct from case
    when a.constraint_name like '%\_pkey' escape '\' then 'p'::"char"
    when a.constraint_name = 'food_logs_user_date_unique' then 'u'::"char"
    else 'c'::"char"
  end
),
expected_key_constraints(constraint_name, table_name, key_columns) as (
  values
    ('nutrition_preferences_pkey'::text, 'nutrition_preferences'::text, array['user_id']::text[]),
    ('foods_pkey', 'foods', array['id']::text[]),
    ('food_portions_pkey', 'food_portions', array['id']::text[]),
    ('nutrition_targets_pkey', 'nutrition_targets', array['id']::text[]),
    ('food_logs_pkey', 'food_logs', array['id']::text[]),
    ('food_logs_user_date_unique', 'food_logs', array['user_id', 'log_date']::text[]),
    ('food_log_items_pkey', 'food_log_items', array['id']::text[])
),
actual_key_constraints as (
  select
    con.conname::text as constraint_name,
    c.relname::text as table_name,
    array(
      select a.attname::text
      from unnest(con.conkey) with ordinality as k(attnum, ord)
      join pg_catalog.pg_attribute a
        on a.attrelid = con.conrelid and a.attnum = k.attnum
      order by k.ord
    )::text[] as key_columns
  from pg_catalog.pg_constraint con
  join pg_catalog.pg_class c on c.oid = con.conrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname in (select table_name from expected_tables)
    and con.contype in ('p', 'u')
),
key_constraint_mismatches as (
  select e.constraint_name, e.table_name, e.key_columns, a.key_columns as actual_key_columns
  from expected_key_constraints e
  left join actual_key_constraints a
    on a.constraint_name = e.constraint_name
   and a.table_name = e.table_name
  where a.constraint_name is null
     or a.key_columns is distinct from e.key_columns
),
expected_constraint_fragments(constraint_name, required_fragments) as (
  values
    ('nutrition_preferences_timezone_name_check'::text, array['timezone_name', 'char_length', '1', '64']::text[]),
    ('foods_catalog_scope_check', array['catalog_scope', '''canonical''', '''custom''']::text[]),
    ('foods_scope_owner_check', array['catalog_scope', 'owner_user_id', 'canonical_slug', 'source_provider', '''canonical''', '''custom''', '''custom_user''']::text[]),
    ('foods_quality_status_check', array['quality_status', '''pending''', '''community''', '''user_entered''', '''reviewed''', '''verified''']::text[]),
    ('foods_reference_unit_check', array['reference_unit', '''g''', '''ml''', '''serving''', '''piece''']::text[]),
    ('foods_reference_amount_check', array['reference_amount', '> 0', '<= 100000']::text[]),
    ('foods_reference_mass_check', array['reference_mass_grams', 'is null', '> 0', '<= 100000']::text[]),
    ('foods_reference_volume_check', array['reference_volume_ml', 'is null', '> 0', '<= 100000']::text[]),
    ('foods_density_check', array['density_g_per_ml', 'is null', '> 0', '<= 100']::text[]),
    ('foods_energy_check', array['energy_kcal', '>= 0', '<= 1000000']::text[]),
    ('foods_protein_check', array['protein_grams', '>= 0', '<= 100000']::text[]),
    ('foods_carbohydrate_check', array['carbohydrate_grams', '>= 0', '<= 100000']::text[]),
    ('foods_fat_check', array['fat_grams', '>= 0', '<= 100000']::text[]),
    ('foods_fiber_check', array['fiber_grams', 'is null', '>= 0', '<= 100000']::text[]),
    ('foods_status_check', array['status', '''active''', '''archived''']::text[]),
    ('foods_archive_state_check', array['status', '''archived''', 'archived_at', 'is not null']::text[]),
    ('food_portions_unit_check', array['unit', '''serving''', '''piece''']::text[]),
    ('food_portions_equivalent_unit_check', array['equivalent_unit', '''g''', '''ml''', '''serving''', '''piece''']::text[]),
    ('food_portions_status_check', array['status', '''active''', '''archived''']::text[]),
    ('food_portions_archive_state_check', array['status', '''archived''', 'archived_at', 'is not null']::text[]),
    ('nutrition_targets_context_check', array['target_context', '''daily''', '''training''', '''rest''']::text[]),
    ('nutrition_targets_source_type_check', array['source_type', '''member''', '''calculator''', '''trainer''', '''future_ai_suggestion''', '''legacy_bridge''']::text[]),
    ('nutrition_targets_status_check', array['status', '''recommended''', '''active''', '''superseded''', '''archived''']::text[]),
    ('nutrition_targets_effective_range_check', array['effective_to', 'effective_from', 'is null', '>=']::text[]),
    ('nutrition_targets_acceptance_check', array['status', '''recommended''', '''active''', '''superseded''', '''archived''', 'accepted_by_user_id', 'accepted_at']::text[]),
    ('nutrition_targets_member_authority_check', array['source_type', '''member''', 'created_by_user_id', 'accepted_by_user_id', 'user_id', '''active''', '''superseded''', '''archived''']::text[]),
    ('nutrition_targets_archive_state_check', array['status', '''archived''', 'archived_at', 'is not null']::text[]),
    ('food_logs_timezone_offset_check', array['timezone_offset_minutes', '-840', '840']::text[]),
    ('food_logs_status_check', array['status', '''active''', '''archived''']::text[]),
    ('food_logs_source_check', array['source', '''phase4_member''', '''legacy_bridge''']::text[]),
    ('food_logs_archive_state_check', array['status', '''archived''', 'archived_at', 'is not null']::text[]),
    ('food_log_items_meal_moment_check', array['meal_moment', '^[a-z][a-z0-9_]{0,39}$']::text[]),
    ('food_log_items_consumed_unit_check', array['consumed_unit', '''g''', '''ml''', '''serving''', '''piece''']::text[]),
    ('food_log_items_reference_unit_check', array['reference_unit_snapshot', '''g''', '''ml''', '''serving''', '''piece''']::text[]),
    ('food_log_items_portion_snapshot_check', array['portion_label_snapshot', 'portion_equivalent_amount_snapshot', 'portion_equivalent_unit_snapshot', 'calculation_basis', '''portion_conversion''']::text[]),
    ('food_log_items_calculation_basis_check', array['calculation_basis', '''direct_reference''', '''portion_conversion''', '''density_conversion''']::text[]),
    ('food_log_items_calculation_snapshot_check', array['calculation_basis', 'density_g_per_ml_snapshot', '''direct_reference''', '''portion_conversion''', '''density_conversion''']::text[]),
    ('food_log_items_status_check', array['status', '''active''', '''archived''']::text[]),
    ('food_log_items_archive_state_check', array['status', '''archived''', 'archived_at', 'is not null']::text[])
),
constraint_semantic_mismatches as (
  select e.constraint_name, fragment.required_fragment, a.definition
  from expected_constraint_fragments e
  left join actual_constraints a using (constraint_name)
  cross join lateral unnest(e.required_fragments) as fragment(required_fragment)
  where a.constraint_name is null
     or position(
       lower(pg_catalog.regexp_replace(
         replace(replace(replace(replace(fragment.required_fragment, '::text', ''), '::numeric', ''), '::jsonb', ''), '::date', ''),
         '[[:space:]()]',
         '',
         'g'
       ))
       in lower(pg_catalog.regexp_replace(
         replace(replace(replace(replace(coalesce(a.definition, ''), '::text', ''), '::numeric', ''), '::jsonb', ''), '::date', ''),
         '[[:space:]()]',
         '',
         'g'
       ))
     ) = 0
),
expected_fks(table_name, source_columns, foreign_table, foreign_columns, delete_action) as (
  values
    ('nutrition_preferences', array['user_id']::text[], 'profiles', array['id']::text[], 'c'::"char"),
    ('foods', array['owner_user_id']::text[], 'profiles', array['id']::text[], 'c'::"char"),
    ('food_portions', array['food_id']::text[], 'foods', array['id']::text[], 'c'::"char"),
    ('nutrition_targets', array['user_id']::text[], 'profiles', array['id']::text[], 'c'::"char"),
    ('nutrition_targets', array['created_by_user_id']::text[], 'profiles', array['id']::text[], 'n'::"char"),
    ('nutrition_targets', array['accepted_by_user_id']::text[], 'profiles', array['id']::text[], 'n'::"char"),
    ('nutrition_targets', array['supersedes_target_id']::text[], 'nutrition_targets', array['id']::text[], 'n'::"char"),
    ('food_logs', array['user_id']::text[], 'profiles', array['id']::text[], 'c'::"char"),
    ('food_logs', array['target_id']::text[], 'nutrition_targets', array['id']::text[], 'n'::"char"),
    ('food_log_items', array['user_id']::text[], 'profiles', array['id']::text[], 'c'::"char"),
    ('food_log_items', array['food_log_id']::text[], 'food_logs', array['id']::text[], 'c'::"char"),
    ('food_log_items', array['food_id']::text[], 'foods', array['id']::text[], 'n'::"char"),
    ('food_log_items', array['food_portion_id']::text[], 'food_portions', array['id']::text[], 'n'::"char")
),
actual_fks as (
  select
    c.relname::text as table_name,
    array(
      select a.attname::text
      from unnest(con.conkey) with ordinality as k(attnum, ord)
      join pg_catalog.pg_attribute a
        on a.attrelid = con.conrelid and a.attnum = k.attnum
      order by k.ord
    )::text[] as source_columns,
    fc.relname::text as foreign_table,
    array(
      select a.attname::text
      from unnest(con.confkey) with ordinality as k(attnum, ord)
      join pg_catalog.pg_attribute a
        on a.attrelid = con.confrelid and a.attnum = k.attnum
      order by k.ord
    )::text[] as foreign_columns,
    con.confdeltype as delete_action
  from pg_catalog.pg_constraint con
  join pg_catalog.pg_class c on c.oid = con.conrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  join pg_catalog.pg_class fc on fc.oid = con.confrelid
  where n.nspname = 'public'
    and c.relname in (select table_name from expected_tables)
    and con.contype = 'f'
),
missing_fks as (
  select e.*
  from expected_fks e
  left join actual_fks a
    on a.table_name = e.table_name
   and a.source_columns = e.source_columns
   and a.foreign_table = e.foreign_table
   and a.foreign_columns = e.foreign_columns
   and a.delete_action = e.delete_action
  where a.table_name is null
),
expected_indexes(index_name, table_name, unique_expected, key_expressions, predicate_compact) as (
  values
    ('foods_canonical_slug_uidx'::text, 'foods'::text, true, array['canonical_slug']::text[], 'catalog_scope=''canonical'''::text),
    ('foods_provider_identity_uidx', 'foods', true, array['source_provider', 'provider_food_id']::text[], 'provider_food_idisnotnull'),
    ('foods_barcode_idx', 'foods', false, array['barcode']::text[], 'barcodeisnotnullandstatus=''active'''),
    ('foods_active_name_idx', 'foods', false, array['lower(name) text_pattern_ops', 'id']::text[], 'status=''active'''),
    ('foods_owner_status_idx', 'foods', false, array['owner_user_id', 'status']::text[], 'catalog_scope=''custom'''),
    ('foods_source_provenance_idx', 'foods', false, array['source_provider', 'source_updated_at desc']::text[], 'catalog_scope=''canonical'''),
    ('food_portions_active_label_uidx', 'food_portions', true, array['food_id', 'lower(label)']::text[], 'status=''active'''),
    ('food_portions_one_active_default_uidx', 'food_portions', true, array['food_id']::text[], 'status=''active''andis_default'),
    ('food_portions_food_status_order_idx', 'food_portions', false, array['food_id', 'status', 'sort_order', 'id']::text[], null),
    ('nutrition_targets_user_request_uidx', 'nutrition_targets', true, array['user_id', 'request_id']::text[], null),
    ('nutrition_targets_one_active_context_uidx', 'nutrition_targets', true, array['user_id', 'target_context']::text[], 'status=''active'''),
    ('nutrition_targets_user_history_idx', 'nutrition_targets', false, array['user_id', 'target_context', 'effective_from desc', 'created_at desc']::text[], null),
    ('food_logs_user_date_unique', 'food_logs', true, array['user_id', 'log_date']::text[], null),
    ('food_logs_user_history_idx', 'food_logs', false, array['user_id', 'log_date desc']::text[], 'status=''active'''),
    ('food_log_items_user_request_uidx', 'food_log_items', true, array['user_id', 'request_id']::text[], null),
    ('food_log_items_log_meal_order_idx', 'food_log_items', false, array['user_id', 'food_log_id', 'meal_moment', 'sort_order', 'id']::text[], 'status=''active'''),
    ('food_log_items_recent_food_idx', 'food_log_items', false, array['user_id', 'created_at desc', 'food_id']::text[], 'status=''active''andfood_idisnotnull'),
    ('food_log_items_food_idx', 'food_log_items', false, array['food_id', 'created_at desc']::text[], 'food_idisnotnull')
),
actual_indexes as (
  select
    ic.relname::text as index_name,
    tc.relname::text as table_name,
    i.indisunique,
    i.indisvalid,
    i.indisready,
    pg_catalog.pg_get_expr(i.indpred, i.indrelid)::text as predicate,
    lower(
      pg_catalog.regexp_replace(
        replace(pg_catalog.pg_get_expr(i.indpred, i.indrelid)::text, '::text', ''),
        '[[:space:]()]',
        '',
        'g'
      )
    ) as predicate_compact,
    array(
      select lower(pg_catalog.regexp_replace(pg_catalog.pg_get_indexdef(i.indexrelid, key_position, true), '[[:space:]]+', ' ', 'g'))
      from pg_catalog.generate_series(1, i.indnkeyatts) as key_position
      order by key_position
    )::text[] as key_expressions,
    pg_catalog.pg_get_indexdef(i.indexrelid)::text as definition
  from pg_catalog.pg_index i
  join pg_catalog.pg_class ic on ic.oid = i.indexrelid
  join pg_catalog.pg_class tc on tc.oid = i.indrelid
  join pg_catalog.pg_namespace n on n.oid = tc.relnamespace
  where n.nspname = 'public'
    and tc.relname in (select table_name from expected_tables)
),
missing_or_invalid_indexes as (
  select
    e.index_name,
    e.table_name,
    e.unique_expected,
    e.key_expressions as expected_key_expressions,
    a.key_expressions as actual_key_expressions,
    e.predicate_compact as expected_predicate,
    a.predicate_compact as actual_predicate
  from expected_indexes e
  left join actual_indexes a
    on a.index_name = e.index_name
   and a.table_name = e.table_name
  where a.index_name is null
     or not a.indisvalid
     or not a.indisready
     or a.indisunique is distinct from e.unique_expected
     or a.key_expressions is distinct from e.key_expressions
     or a.predicate_compact is distinct from e.predicate_compact
),
expected_policies(
  table_name,
  policy_name,
  command_code,
  using_required,
  check_required,
  using_fragments,
  check_fragments
) as (
  values
    ('nutrition_preferences'::text, 'nutrition_preferences_select_own'::text, 'r'::"char", true, false, array['user_id', 'auth.uid()']::text[], array[]::text[]),
    ('nutrition_preferences', 'nutrition_preferences_insert_own', 'a'::"char", false, true, array[]::text[], array['user_id', 'auth.uid()']::text[]),
    ('nutrition_preferences', 'nutrition_preferences_update_own', 'w'::"char", true, true, array['user_id', 'auth.uid()']::text[], array['user_id', 'auth.uid()']::text[]),
    ('foods', 'foods_select_visible', 'r'::"char", true, false, array['catalog_scope', '''canonical''', '''custom''', 'status', '''active''', 'owner_user_id', 'auth.uid()']::text[], array[]::text[]),
    ('foods', 'foods_insert_own_custom', 'a'::"char", false, true, array[]::text[], array['catalog_scope', '''custom''', 'owner_user_id', 'auth.uid()', 'source_provider', '''custom_user''']::text[]),
    ('foods', 'foods_update_own_custom', 'w'::"char", true, true, array['catalog_scope', '''custom''', 'owner_user_id', 'auth.uid()']::text[], array['catalog_scope', '''custom''', 'owner_user_id', 'auth.uid()', 'source_provider', '''custom_user''']::text[]),
    ('food_portions', 'food_portions_select_visible', 'r'::"char", true, false, array['foods', 'food_id', 'catalog_scope', '''canonical''', '''custom''', 'status', '''active''', 'owner_user_id', 'auth.uid()']::text[], array[]::text[]),
    ('food_portions', 'food_portions_insert_own_custom', 'a'::"char", false, true, array[]::text[], array['foods', 'food_id', 'catalog_scope', '''custom''', 'owner_user_id', 'auth.uid()']::text[]),
    ('food_portions', 'food_portions_update_own_custom', 'w'::"char", true, true, array['foods', 'food_id', 'catalog_scope', '''custom''', 'owner_user_id', 'auth.uid()']::text[], array['foods', 'food_id', 'catalog_scope', '''custom''', 'owner_user_id', 'auth.uid()']::text[]),
    ('nutrition_targets', 'nutrition_targets_select_own', 'r'::"char", true, false, array['user_id', 'auth.uid()']::text[], array[]::text[]),
    ('nutrition_targets', 'nutrition_targets_insert_own', 'a'::"char", false, true, array[]::text[], array['user_id', 'auth.uid()']::text[]),
    ('nutrition_targets', 'nutrition_targets_update_own', 'w'::"char", true, true, array['user_id', 'auth.uid()']::text[], array['user_id', 'auth.uid()']::text[]),
    ('food_logs', 'food_logs_select_own', 'r'::"char", true, false, array['user_id', 'auth.uid()']::text[], array[]::text[]),
    ('food_logs', 'food_logs_insert_own', 'a'::"char", false, true, array[]::text[], array['user_id', 'auth.uid()']::text[]),
    ('food_logs', 'food_logs_update_own', 'w'::"char", true, true, array['user_id', 'auth.uid()']::text[], array['user_id', 'auth.uid()']::text[]),
    ('food_log_items', 'food_log_items_select_own', 'r'::"char", true, false, array['user_id', 'auth.uid()']::text[], array[]::text[]),
    ('food_log_items', 'food_log_items_insert_own', 'a'::"char", false, true, array[]::text[], array['user_id', 'auth.uid()']::text[]),
    ('food_log_items', 'food_log_items_update_own', 'w'::"char", true, true, array['user_id', 'auth.uid()']::text[], array['user_id', 'auth.uid()']::text[])
),
actual_policies as (
  select
    c.relname::text as table_name,
    p.polname::text as policy_name,
    p.polcmd as command_code,
    p.polpermissive,
    p.polroles,
    pg_catalog.pg_get_expr(p.polqual, p.polrelid)::text as using_expression,
    pg_catalog.pg_get_expr(p.polwithcheck, p.polrelid)::text as check_expression
  from pg_catalog.pg_policy p
  join pg_catalog.pg_class c on c.oid = p.polrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname in (select table_name from expected_tables)
),
policy_mismatches as (
  select
    e.table_name,
    e.policy_name,
    e.command_code,
    a.polpermissive,
    a.polroles,
    a.using_expression,
    a.check_expression
  from expected_policies e
  left join actual_policies a
    on a.table_name = e.table_name
   and a.policy_name = e.policy_name
  where a.policy_name is null
     or a.command_code is distinct from e.command_code
     or not a.polpermissive
     or a.polroles is distinct from array[0]::oid[]
     or ((a.using_expression is not null) is distinct from e.using_required)
     or ((a.check_expression is not null) is distinct from e.check_required)
     or exists (
       select 1
       from unnest(e.using_fragments) as fragment(value)
       where position(lower(fragment.value) in lower(coalesce(a.using_expression, ''))) = 0
     )
     or exists (
       select 1
       from unnest(e.check_fragments) as fragment(value)
       where position(lower(fragment.value) in lower(coalesce(a.check_expression, ''))) = 0
     )
     or lower(coalesce(a.using_expression, '')) ~ '(^|[^a-z_])true([^a-z_]|$)'
     or lower(coalesce(a.check_expression, '')) ~ '(^|[^a-z_])true([^a-z_]|$)'
),
role_oids as (
  select
    (select oid from pg_catalog.pg_roles where rolname = 'authenticated') as authenticated_oid,
    (select oid from pg_catalog.pg_roles where rolname = 'anon') as anon_oid
),
table_acl as (
  select
    c.relname::text as table_name,
    acl.grantee,
    acl.privilege_type::text as privilege_type,
    acl.is_grantable
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  cross join lateral pg_catalog.aclexplode(
    coalesce(c.relacl, pg_catalog.acldefault('r', c.relowner))
  ) acl
  where n.nspname = 'public'
    and c.relname in (select table_name from expected_tables)
),
expected_table_acl(table_name, authenticated_privileges) as (
  values
    ('nutrition_preferences'::text, array[]::text[]),
    ('foods', array['SELECT']::text[]),
    ('food_portions', array['SELECT']::text[]),
    ('nutrition_targets', array[]::text[]),
    ('food_logs', array[]::text[]),
    ('food_log_items', array[]::text[])
),
table_acl_mismatches as (
  select
    e.table_name,
    e.authenticated_privileges,
    actual.privileges as actual_privileges,
    actual.any_grantable
  from expected_table_acl e
  cross join role_oids r
  cross join lateral (
    select
      coalesce(array_agg(a.privilege_type order by a.privilege_type), array[]::text[])::text[] as privileges,
      coalesce(bool_or(a.is_grantable), false) as any_grantable
    from table_acl a
    where a.table_name = e.table_name
      and a.grantee = r.authenticated_oid
  ) actual
  where actual.privileges is distinct from e.authenticated_privileges
     or actual.any_grantable
),
expected_functions(
  function_name,
  argument_types,
  security_definer,
  authenticated_rpc,
  language_name,
  volatility,
  return_type,
  returns_set
) as (
  values
    ('fmz_phase4_touch_updated_at'::text, ''::text, false, false, 'plpgsql'::text, 'v'::"char", 'pg_catalog.trigger'::text, false),
    ('fmz_phase4_sync_archive_state', '', false, false, 'plpgsql', 'v'::"char", 'pg_catalog.trigger', false),
    ('fmz_phase4_has_full_nutrition_access', 'uuid', true, false, 'sql', 's'::"char", 'pg_catalog.bool', false),
    ('fmz_phase4_enforce_custom_food_limit', '', true, false, 'plpgsql', 'v'::"char", 'pg_catalog.trigger', false),
    ('fmz_phase4_enforce_food_portion_owner', '', true, false, 'plpgsql', 'v'::"char", 'pg_catalog.trigger', false),
    ('fmz_phase4_enforce_target_owner', '', true, false, 'plpgsql', 'v'::"char", 'pg_catalog.trigger', false),
    ('fmz_phase4_enforce_food_log_owner', '', true, false, 'plpgsql', 'v'::"char", 'pg_catalog.trigger', false),
    ('fmz_phase4_enforce_food_log_item_owner', '', true, false, 'plpgsql', 'v'::"char", 'pg_catalog.trigger', false),
    ('fmz_phase4_day_payload', 'uuid, date', true, false, 'plpgsql', 's'::"char", 'pg_catalog.jsonb', false),
    ('fmz_phase4_set_nutrition_timezone', 'text', true, true, 'plpgsql', 'v'::"char", 'pg_catalog.jsonb', false),
    ('fmz_phase4_search_foods', 'text, integer, text, uuid', false, true, 'plpgsql', 's'::"char", 'public.foods', true),
    ('fmz_phase4_upsert_custom_food', 'uuid, text, text, numeric, text, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, timestamp with time zone', true, true, 'plpgsql', 'v'::"char", 'pg_catalog.jsonb', false),
    ('fmz_phase4_archive_custom_food', 'uuid, timestamp with time zone', true, true, 'plpgsql', 'v'::"char", 'pg_catalog.jsonb', false),
    ('fmz_phase4_upsert_food_portion', 'uuid, uuid, text, numeric, text, numeric, text, boolean, timestamp with time zone', true, true, 'plpgsql', 'v'::"char", 'pg_catalog.jsonb', false),
    ('fmz_phase4_save_member_target', 'uuid, uuid, numeric, numeric, numeric, numeric, numeric, date', true, true, 'plpgsql', 'v'::"char", 'pg_catalog.jsonb', false),
    ('fmz_phase4_get_current_nutrition_target', '', true, true, 'plpgsql', 's'::"char", 'pg_catalog.jsonb', false),
    ('fmz_phase4_log_food_item', 'uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamp with time zone', true, true, 'plpgsql', 'v'::"char", 'pg_catalog.jsonb', false),
    ('fmz_phase4_archive_food_log_item', 'uuid, timestamp with time zone', true, true, 'plpgsql', 'v'::"char", 'pg_catalog.jsonb', false),
    ('fmz_phase4_get_nutrition_day', 'date', true, true, 'plpgsql', 's'::"char", 'pg_catalog.jsonb', false),
    ('fmz_phase4_get_nutrition_history', 'date, integer', true, true, 'plpgsql', 's'::"char", 'pg_catalog.jsonb', false)
),
actual_functions as (
  select
    p.oid,
    p.proname::text as function_name,
    pg_catalog.oidvectortypes(p.proargtypes)::text as argument_types,
    p.prosecdef as security_definer,
    p.provolatile,
    p.proretset,
    p.prorettype,
    p.prokind,
    p.proargnames,
    p.proconfig,
    p.proacl,
    p.proowner,
    l.lanname::text as language_name,
    p.prosrc::text as source
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  join pg_catalog.pg_language l on l.oid = p.prolang
  where n.nspname = 'public'
    and p.proname like 'fmz_phase4_%'
),
function_mismatches as (
  select e.*
  from expected_functions e
  left join actual_functions a
    on a.function_name = e.function_name
   and a.argument_types = e.argument_types
  where a.oid is null
     or a.security_definer is distinct from e.security_definer
     or a.language_name is distinct from e.language_name
     or a.provolatile is distinct from e.volatility
     or a.proretset is distinct from e.returns_set
     or a.prorettype is distinct from pg_catalog.to_regtype(e.return_type)::oid
     or a.prokind is distinct from 'f'::"char"
     or coalesce(a.proconfig, array[]::text[])
        is distinct from array['search_path=pg_catalog, public, pg_temp']::text[]
),
expected_function_source_fragments(function_name, argument_types, required_fragments) as (
  values
    ('fmz_phase4_has_full_nutrition_access'::text, 'uuid'::text, array['from public.entitlements', 'e.user_id = p_user_id', 'e.status = ''active''', 'e.entitlement_code in (''pro'', ''ai'', ''personal_coaching'')', 'e.starts_at <= now()', 'e.ends_at is null or e.ends_at > now()']::text[]),
    ('fmz_phase4_enforce_custom_food_limit', '', array['auth.uid()', 'ownership and catalog scope are immutable', 'canonical foods are database-managed', 'owner_user_id is distinct from v_user_id', 'fmz_phase4_custom_food_limit:', 'fmz_phase4_has_full_nutrition_access', 'catalog_scope = ''custom''', 'status = ''active''', 'v_active_count >= 10']::text[]),
    ('fmz_phase4_enforce_food_portion_owner', '', array['auth.uid()', 'food portion parent is immutable', 'from public.foods', 'canonical food portions are database-managed', 'v_food.owner_user_id is distinct from v_user_id']::text[]),
    ('fmz_phase4_enforce_target_owner', '', array['auth.uid()', 'new.user_id is distinct from v_user_id', 'new.target_context <> ''daily''', 'new.source_type <> ''member''', 'new.created_by_user_id is distinct from v_user_id', 'new.accepted_by_user_id is distinct from v_user_id', 'supersedes_target_id']::text[]),
    ('fmz_phase4_enforce_food_log_owner', '', array['auth.uid()', 'new.user_id is distinct from v_user_id', 'food log identity and target snapshots are immutable', 'new.source <> ''phase4_member''', 'pg_timezone_names', 't.user_id = v_user_id']::text[]),
    ('fmz_phase4_enforce_food_log_item_owner', '', array['auth.uid()', 'historical food log item snapshots are immutable', 'l.user_id = v_user_id', 'l.status = ''active''', 'f.status = ''active''', 'f.owner_user_id = v_user_id', 'p.food_id = new.food_id', 'p.status = ''active''']::text[]),
    ('fmz_phase4_day_payload', 'uuid, date', array['l.user_id = p_user_id', 'l.log_date = p_log_date', 'i.user_id = p_user_id', 't.user_id = p_user_id', 't.target_context = ''daily''', 't.effective_from <= p_log_date']::text[]),
    ('fmz_phase4_set_nutrition_timezone', 'text', array['auth.uid()', 'pg_timezone_names', 'nutrition_preferences(user_id, timezone_name)', 'values (v_user_id, v_timezone)', 'on conflict (user_id)', 'timezone_name = excluded.timezone_name']::text[]),
    ('fmz_phase4_search_foods', 'text, integer, text, uuid', array['auth.uid()', 'from public.foods', 'f.status = ''active''', 'limit v_page_size']::text[]),
    ('fmz_phase4_upsert_custom_food', 'uuid, text, text, numeric, text, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, timestamp with time zone', array['auth.uid()', 'fmz_phase4_custom_food_request:', 'v_existing.owner_user_id is distinct from v_user_id', 'p_expected_updated_at', '''custom''', '''custom_user''', '''user_entered''']::text[]),
    ('fmz_phase4_archive_custom_food', 'uuid, timestamp with time zone', array['auth.uid()', 'fmz_phase4_custom_food_request:', 'f.catalog_scope = ''custom''', 'f.owner_user_id = v_user_id', 'set status = ''archived''']::text[]),
    ('fmz_phase4_upsert_food_portion', 'uuid, uuid, text, numeric, text, numeric, text, boolean, timestamp with time zone', array['auth.uid()', 'fmz_phase4_food_portion_request:', 'f.catalog_scope = ''custom''', 'f.owner_user_id = v_user_id', 'f.status = ''active''', 'p_expected_updated_at']::text[]),
    ('fmz_phase4_save_member_target', 'uuid, uuid, numeric, numeric, numeric, numeric, numeric, date', array['auth.uid()', 'fmz_phase4_nutrition_target:', 't.request_id = p_request_id', 't.status = ''active''', 'for update', 'status = ''superseded''', '''daily''', '''member''']::text[]),
    ('fmz_phase4_get_current_nutrition_target', '', array['auth.uid()', 't.user_id = v_user_id', 't.target_context = ''daily''', 't.status = ''active''']::text[]),
    ('fmz_phase4_log_food_item', 'uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamp with time zone', array['auth.uid()', 'fmz_phase4_food_log_request:', 'p_log_date < v_today - 6', 'pg_timezone_names', 'timezone offset does not match', 'f.status = ''active''', 'f.owner_user_id = v_user_id', 'p.food_id = v_food.id', 'explicit portion or density conversion required', 'fmz_phase4_food_log:', 't.effective_from <= p_log_date', 'round(v_food.energy_kcal * v_factor, 3)', 'provenance_snapshot', 'calculation_version']::text[]),
    ('fmz_phase4_archive_food_log_item', 'uuid, timestamp with time zone', array['auth.uid()', 'fmz_phase4_food_log_item_request:', 'i.user_id = v_user_id', 'l.user_id = v_user_id', 'v_log_date < v_today - 6', 'set status = ''archived''']::text[]),
    ('fmz_phase4_get_nutrition_day', 'date', array['auth.uid()', 'p_log_date > v_today', 'p_log_date < v_today - 6', 'fmz_phase4_day_payload']::text[]),
    ('fmz_phase4_get_nutrition_history', 'date, integer', array['auth.uid()', 'fmz_phase4_has_full_nutrition_access', 'generate_series(0, 6)', '''window_days'', 7', 'limit v_page_size']::text[])
),
function_source_mismatches as (
  select e.function_name, e.argument_types, fragment.required_fragment
  from expected_function_source_fragments e
  left join actual_functions a
    on a.function_name = e.function_name
   and a.argument_types = e.argument_types
  cross join lateral unnest(e.required_fragments) as fragment(required_fragment)
  where a.oid is null
     or position(lower(fragment.required_fragment) in lower(coalesce(a.source, ''))) = 0
),
public_rpc_authority_parameter_mismatches as (
  select e.function_name, e.argument_types, a.proargnames
  from expected_functions e
  join actual_functions a
    on a.function_name = e.function_name
   and a.argument_types = e.argument_types
  where e.authenticated_rpc
    and exists (
      select 1
      from unnest(coalesce(a.proargnames, array[]::text[])) as argument_name(value)
      where lower(argument_name.value) in (
        'p_user_id', 'p_owner_user_id', 'p_role', 'p_trainer_id',
        'p_client_id', 'p_entitlement_code', 'p_entitlement_status'
      )
    )
),
function_acl as (
  select
    f.oid,
    f.function_name,
    f.argument_types,
    acl.grantee,
    acl.privilege_type::text as privilege_type,
    acl.is_grantable
  from actual_functions f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) acl
),
function_acl_mismatches as (
  select e.function_name, e.argument_types
  from expected_functions e
  join actual_functions f
    on f.function_name = e.function_name
   and f.argument_types = e.argument_types
  cross join role_oids r
  cross join lateral (
    select
      exists (
        select 1 from function_acl a
        where a.oid = f.oid and a.grantee = r.authenticated_oid and a.privilege_type = 'EXECUTE'
      ) as authenticated_execute,
      exists (
        select 1 from function_acl a
        where a.oid = f.oid and a.grantee = r.authenticated_oid
          and a.privilege_type = 'EXECUTE' and a.is_grantable
      ) as authenticated_grantable,
      exists (
        select 1 from function_acl a
        where a.oid = f.oid and a.grantee = r.anon_oid and a.privilege_type = 'EXECUTE'
      ) as anon_execute,
      exists (
        select 1 from function_acl a
        where a.oid = f.oid and a.grantee = 0 and a.privilege_type = 'EXECUTE'
      ) as public_execute
  ) privilege_state
  where privilege_state.authenticated_execute is distinct from e.authenticated_rpc
     or privilege_state.authenticated_grantable
     or privilege_state.anon_execute
     or privilege_state.public_execute
),
expected_triggers(table_name, trigger_name, function_name, trigger_type, update_columns) as (
  values
    ('foods'::text, 'foods_10_sync_archive_state'::text, 'fmz_phase4_sync_archive_state'::text, 23, array['status']::text[]),
    ('foods', 'foods_20_enforce_custom_limit', 'fmz_phase4_enforce_custom_food_limit', 23, array['owner_user_id', 'catalog_scope', 'status']::text[]),
    ('foods', 'foods_90_touch_updated_at', 'fmz_phase4_touch_updated_at', 19, array[]::text[]),
    ('food_portions', 'food_portions_10_sync_archive_state', 'fmz_phase4_sync_archive_state', 23, array['status']::text[]),
    ('food_portions', 'food_portions_20_enforce_owner', 'fmz_phase4_enforce_food_portion_owner', 23, array[]::text[]),
    ('food_portions', 'food_portions_90_touch_updated_at', 'fmz_phase4_touch_updated_at', 19, array[]::text[]),
    ('nutrition_preferences', 'nutrition_preferences_90_touch_updated_at', 'fmz_phase4_touch_updated_at', 19, array[]::text[]),
    ('nutrition_targets', 'nutrition_targets_10_sync_archive_state', 'fmz_phase4_sync_archive_state', 23, array['status']::text[]),
    ('nutrition_targets', 'nutrition_targets_20_enforce_owner', 'fmz_phase4_enforce_target_owner', 23, array[]::text[]),
    ('nutrition_targets', 'nutrition_targets_90_touch_updated_at', 'fmz_phase4_touch_updated_at', 19, array[]::text[]),
    ('food_logs', 'food_logs_10_sync_archive_state', 'fmz_phase4_sync_archive_state', 23, array['status']::text[]),
    ('food_logs', 'food_logs_20_enforce_owner', 'fmz_phase4_enforce_food_log_owner', 23, array[]::text[]),
    ('food_logs', 'food_logs_90_touch_updated_at', 'fmz_phase4_touch_updated_at', 19, array[]::text[]),
    ('food_log_items', 'food_log_items_10_sync_archive_state', 'fmz_phase4_sync_archive_state', 23, array['status']::text[]),
    ('food_log_items', 'food_log_items_20_enforce_owner', 'fmz_phase4_enforce_food_log_item_owner', 23, array[]::text[]),
    ('food_log_items', 'food_log_items_90_touch_updated_at', 'fmz_phase4_touch_updated_at', 19, array[]::text[])
),
actual_triggers as (
  select
    c.relname::text as table_name,
    t.tgname::text as trigger_name,
    p.proname::text as function_name,
    t.tgenabled,
    t.tgtype::integer as trigger_type,
    array(
      select a.attname::text
      from unnest(
        pg_catalog.string_to_array(nullif(t.tgattr::text, ''), ' ')::smallint[]
      ) with ordinality as trigger_column(attnum, ord)
      join pg_catalog.pg_attribute a
        on a.attrelid = t.tgrelid and a.attnum = trigger_column.attnum
      order by trigger_column.ord
    )::text[] as update_columns
  from pg_catalog.pg_trigger t
  join pg_catalog.pg_class c on c.oid = t.tgrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  join pg_catalog.pg_proc p on p.oid = t.tgfoid
  where n.nspname = 'public'
    and c.relname in (select table_name from expected_tables)
    and not t.tgisinternal
),
trigger_mismatches as (
  select e.*
  from expected_triggers e
  left join actual_triggers a
    on a.table_name = e.table_name
   and a.trigger_name = e.trigger_name
   and a.function_name = e.function_name
  where a.trigger_name is null
     or a.tgenabled <> 'O'
     or a.trigger_type is distinct from e.trigger_type
     or a.update_columns is distinct from e.update_columns
),
phase4_sources as (
  select coalesce(string_agg(lower(source), E'\n'), '') as source
  from actual_functions
),
phase4_policy_text as (
  select coalesce(
    string_agg(
      lower(policy_name || ' ' || coalesce(using_expression, '') || ' ' || coalesce(check_expression, '')),
      E'\n'
    ),
    ''
  ) as source
  from actual_policies
),
phase4_definition_text as (
  select coalesce(string_agg(lower(object_text), E'\n'), '') as source
  from (
    select source as object_text from actual_functions
    union all
    select definition from actual_constraints
    union all
    select definition from actual_indexes
    union all
    select policy_name || ' ' || coalesce(using_expression, '') || ' ' || coalesce(check_expression, '')
    from actual_policies
  ) object_definitions
),
normalized_row_counts(table_name, row_count) as (
  select 'nutrition_preferences'::text, count(*)::bigint from public.nutrition_preferences
  union all select 'foods', count(*)::bigint from public.foods
  union all select 'food_portions', count(*)::bigint from public.food_portions
  union all select 'nutrition_targets', count(*)::bigint from public.nutrition_targets
  union all select 'food_logs', count(*)::bigint from public.food_logs
  union all select 'food_log_items', count(*)::bigint from public.food_log_items
),
legacy_guard_tables(table_name) as (
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
    ('exercises')
),
legacy_guard_state as (
  select
    g.table_name,
    c.oid is not null as table_exists,
    coalesce(c.relrowsecurity, false) as rls_enabled
  from legacy_guard_tables g
  left join (
    select c.oid, c.relname, c.relrowsecurity
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relkind = 'r'
  ) c on c.relname = g.table_name
),
legacy_guard_columns(table_name, column_name) as (
  values
    ('profiles'::text, 'id'::text),
    ('profiles', 'role'),
    ('profiles', 'trainer_id'),
    ('profiles', 'client_id'),
    ('coach_workspaces', 'trainer_id'),
    ('coach_workspaces', 'state'),
    ('user_settings', 'user_id'),
    ('user_settings', 'language'),
    ('user_onboarding', 'user_id'),
    ('user_onboarding', 'completed_at'),
    ('entitlements', 'user_id'),
    ('entitlements', 'entitlement_code'),
    ('entitlements', 'status'),
    ('entitlements', 'starts_at'),
    ('entitlements', 'ends_at'),
    ('recovery_logs', 'user_id'),
    ('recovery_logs', 'log_date'),
    ('training_plans', 'id'),
    ('training_plans', 'user_id'),
    ('training_plans', 'status'),
    ('training_plan_days', 'id'),
    ('training_plan_days', 'training_plan_id'),
    ('training_plan_days', 'status'),
    ('training_plan_exercises', 'id'),
    ('training_plan_exercises', 'training_plan_day_id'),
    ('training_plan_exercises', 'exercise_id'),
    ('workout_sessions', 'id'),
    ('workout_sessions', 'user_id'),
    ('workout_set_logs', 'id'),
    ('workout_set_logs', 'user_id'),
    ('exercises', 'id'),
    ('exercises', 'canonical_slug'),
    ('exercises', 'is_active')
),
missing_legacy_guard_columns as (
  select g.table_name, g.column_name
  from legacy_guard_columns g
  left join information_schema.columns c
    on c.table_schema = 'public'
   and c.table_name = g.table_name
   and c.column_name = g.column_name
  where c.column_name is null
),
checks(check_name, pass, details) as (
  select
    'exact_six_tables_exist',
    (select count(*) = 6 from actual_phase4_tables)
      and not exists (
        select table_name from expected_tables
        except
        select table_name from actual_phase4_tables
      )
      and not exists (
        select table_name from actual_phase4_tables
        except
        select table_name from expected_tables
      ),
    jsonb_build_object(
      'expected', (select jsonb_agg(table_name order by table_name) from expected_tables),
      'actual', (select jsonb_agg(table_name order by table_name) from actual_phase4_tables)
    )

  union all
  select
    'exact_columns_types_nullability_defaults',
    not exists (select 1 from column_mismatches)
      and not exists (select 1 from unexpected_columns)
      and (select count(*) from actual_columns) = (select count(*) from expected_columns),
    jsonb_build_object(
      'expected_count', (select count(*) from expected_columns),
      'actual_count', (select count(*) from actual_columns),
      'mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from column_mismatches m), '[]'::jsonb),
      'unexpected', coalesce((select jsonb_agg(to_jsonb(u)) from unexpected_columns u), '[]'::jsonb)
    )

  union all
  select
    'named_structural_constraints',
    not exists (select 1 from missing_constraints)
      and not exists (select 1 from unexpected_non_fk_constraints)
      and not exists (select 1 from constraint_type_mismatches)
      and not exists (select 1 from key_constraint_mismatches)
      and not exists (select 1 from constraint_semantic_mismatches),
    jsonb_build_object(
      'missing', coalesce((select jsonb_agg(constraint_name order by constraint_name) from missing_constraints), '[]'::jsonb),
      'unexpected_non_fk', coalesce((select jsonb_agg(to_jsonb(c)) from unexpected_non_fk_constraints c), '[]'::jsonb),
      'type_mismatches', coalesce((select jsonb_agg(to_jsonb(c)) from constraint_type_mismatches c), '[]'::jsonb),
      'key_mismatches', coalesce((select jsonb_agg(to_jsonb(c)) from key_constraint_mismatches c), '[]'::jsonb),
      'semantic_mismatches', coalesce((select jsonb_agg(to_jsonb(c)) from constraint_semantic_mismatches c), '[]'::jsonb),
      'actual', coalesce((select jsonb_agg(constraint_name order by constraint_name) from actual_constraints), '[]'::jsonb)
    )

  union all
  select
    'foreign_keys_and_delete_actions',
    not exists (select 1 from missing_fks)
      and (select count(*) from actual_fks) = (select count(*) from expected_fks),
    jsonb_build_object(
      'expected_count', (select count(*) from expected_fks),
      'actual_count', (select count(*) from actual_fks),
      'missing', coalesce((select jsonb_agg(to_jsonb(f)) from missing_fks f), '[]'::jsonb)
    )

  union all
  select
    'required_indexes_valid_ready_and_scoped',
    not exists (select 1 from missing_or_invalid_indexes),
    jsonb_build_object(
      'missing_or_invalid', coalesce((select jsonb_agg(to_jsonb(i) order by index_name) from missing_or_invalid_indexes i), '[]'::jsonb),
      'actual', coalesce((select jsonb_agg(jsonb_build_object(
        'name', index_name,
        'table', table_name,
        'unique', indisunique,
        'valid', indisvalid,
        'ready', indisready,
        'keys', key_expressions,
        'predicate', predicate_compact
      ) order by index_name) from actual_indexes where index_name in (select index_name from expected_indexes)), '[]'::jsonb)
    )

  union all
  select
    'rls_enabled_all_six',
    (
      select count(*) = 6 and bool_and(c.relrowsecurity)
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public'
        and c.relname in (select table_name from expected_tables)
    ),
    jsonb_build_object(
      'tables', (
        select jsonb_agg(jsonb_build_object('table', c.relname, 'rls', c.relrowsecurity) order by c.relname)
        from pg_catalog.pg_class c
        join pg_catalog.pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public'
          and c.relname in (select table_name from expected_tables)
      )
    )

  union all
  select
    'exact_own_user_and_catalog_policies',
    not exists (select 1 from policy_mismatches)
      and (select count(*) from actual_policies) = (select count(*) from expected_policies)
      and not exists (select 1 from actual_policies where command_code = 'd'),
    jsonb_build_object(
      'expected_count', (select count(*) from expected_policies),
      'actual_count', (select count(*) from actual_policies),
      'missing', coalesce((select jsonb_agg(to_jsonb(p)) from policy_mismatches p), '[]'::jsonb)
    )

  union all
  select
    'no_broad_trainer_policy',
    not exists (
      select 1 from actual_policies
      where lower(policy_name || ' ' || coalesce(using_expression, '') || ' ' || coalesce(check_expression, ''))
        like '%trainer%'
    ),
    jsonb_build_object('policy_count', (select count(*) from actual_policies))

  union all
  select
    'table_acl_least_privilege',
    (select authenticated_oid is not null and anon_oid is not null from role_oids)
      and not exists (select 1 from table_acl_mismatches)
      and not exists (select 1 from table_acl where grantee = 0)
      and not exists (
        select 1 from table_acl a cross join role_oids r
        where a.grantee = r.anon_oid
      ),
    jsonb_build_object(
      'authenticated_mismatches', coalesce((select jsonb_agg(to_jsonb(a)) from table_acl_mismatches a), '[]'::jsonb),
      'public_privileges', (select count(*) from table_acl where grantee = 0),
      'anon_privileges', (
        select count(*) from table_acl a cross join role_oids r where a.grantee = r.anon_oid
      )
    )

  union all
  select
    'functions_security_and_search_path',
    not exists (select 1 from function_mismatches)
      and (select count(*) from actual_functions) = (select count(*) from expected_functions),
    jsonb_build_object(
      'expected_count', (select count(*) from expected_functions),
      'actual_count', (select count(*) from actual_functions),
      'mismatches', coalesce((select jsonb_agg(to_jsonb(f)) from function_mismatches f), '[]'::jsonb)
    )

  union all
  select
    'function_source_contracts_and_rpc_authority',
    not exists (select 1 from function_source_mismatches)
      and not exists (select 1 from public_rpc_authority_parameter_mismatches),
    jsonb_build_object(
      'source_mismatches', coalesce((select jsonb_agg(to_jsonb(f)) from function_source_mismatches f), '[]'::jsonb),
      'authority_parameter_mismatches', coalesce((select jsonb_agg(to_jsonb(f)) from public_rpc_authority_parameter_mismatches f), '[]'::jsonb)
    )

  union all
  select
    'function_acl_exact',
    not exists (select 1 from function_acl_mismatches),
    jsonb_build_object(
      'mismatches', coalesce((select jsonb_agg(to_jsonb(f)) from function_acl_mismatches f), '[]'::jsonb)
    )

  union all
  select
    'triggers_present_and_enabled',
    not exists (select 1 from trigger_mismatches)
      and (select count(*) from actual_triggers) = (select count(*) from expected_triggers),
    jsonb_build_object(
      'expected_count', (select count(*) from expected_triggers),
      'actual_count', (select count(*) from actual_triggers),
      'mismatches', coalesce((select jsonb_agg(to_jsonb(t)) from trigger_mismatches t), '[]'::jsonb)
    )

  union all
  select
    'rpc_authority_derived_from_auth_uid',
    not exists (select 1 from public_rpc_authority_parameter_mismatches)
      and not exists (
        select 1
        from expected_functions e
        join actual_functions a
          on a.function_name = e.function_name and a.argument_types = e.argument_types
        where e.authenticated_rpc
          and position('auth.uid()' in lower(a.source)) = 0
      ),
    jsonb_build_object('authority', 'auth.uid', 'client_authority_parameters', false)

  union all
  select
    'entitlement_current_pro_ai_pt_only',
    position('entitlement_code in (''pro'', ''ai'', ''personal_coaching'')' in coalesce((
      select lower(source) from actual_functions
      where function_name = 'fmz_phase4_has_full_nutrition_access' and argument_types = 'uuid'
    ), '')) > 0
      and position('e.status = ''active''' in coalesce((
        select lower(source) from actual_functions
        where function_name = 'fmz_phase4_has_full_nutrition_access' and argument_types = 'uuid'
      ), '')) > 0
      and position('e.starts_at <= now()' in coalesce((
        select lower(source) from actual_functions
        where function_name = 'fmz_phase4_has_full_nutrition_access' and argument_types = 'uuid'
      ), '')) > 0
      and position('e.ends_at is null or e.ends_at > now()' in coalesce((
        select lower(source) from actual_functions
        where function_name = 'fmz_phase4_has_full_nutrition_access' and argument_types = 'uuid'
      ), '')) > 0,
    jsonb_build_object('missing_or_invalid_entitlement_defaults_to_free', true)

  union all
  select
    'free_custom_food_limit_and_concurrency',
    position('fmz_phase4_custom_food_limit:' in coalesce((
      select lower(source) from actual_functions where function_name = 'fmz_phase4_enforce_custom_food_limit' and argument_types = ''
    ), '')) > 0
      and position('pg_advisory_xact_lock' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_enforce_custom_food_limit' and argument_types = ''
      ), '')) > 0
      and position('f.catalog_scope = ''custom''' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_enforce_custom_food_limit' and argument_types = ''
      ), '')) > 0
      and position('f.status = ''active''' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_enforce_custom_food_limit' and argument_types = ''
      ), '')) > 0
      and position('v_active_count >= 10' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_enforce_custom_food_limit' and argument_types = ''
      ), '')) > 0,
    jsonb_build_object('free_active_custom_food_limit', 10)

  union all
  select
    'free_seven_local_calendar_day_history',
    position('generate_series(0, 6)' in coalesce((
      select lower(source) from actual_functions where function_name = 'fmz_phase4_get_nutrition_history' and argument_types = 'date, integer'
    ), '')) > 0
      and position('''window_days'', 7' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_get_nutrition_history' and argument_types = 'date, integer'
      ), '')) > 0
      and position('p_log_date < v_today - 6' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_get_nutrition_day' and argument_types = 'date'
      ), '')) > 0
      and position('p_log_date < v_today - 6' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_log_food_item' and argument_types = 'uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamp with time zone'
      ), '')) > 0
      and position('v_log_date < v_today - 6' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_archive_food_log_item' and argument_types = 'uuid, timestamp with time zone'
      ), '')) > 0,
    jsonb_build_object('free_window_days', 7, 'calendar_basis', 'stored_valid_iana_timezone')

  union all
  select
    'member_daily_target_server_authority',
    position('fmz_phase4_nutrition_target:' in coalesce((
      select lower(source) from actual_functions where function_name = 'fmz_phase4_save_member_target' and argument_types = 'uuid, uuid, numeric, numeric, numeric, numeric, numeric, date'
    ), '')) > 0
      and position('''daily''' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_save_member_target' and argument_types = 'uuid, uuid, numeric, numeric, numeric, numeric, numeric, date'
      ), '')) > 0
      and position('''member''' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_save_member_target' and argument_types = 'uuid, uuid, numeric, numeric, numeric, numeric, numeric, date'
      ), '')) > 0
      and position('status = ''superseded''' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_save_member_target' and argument_types = 'uuid, uuid, numeric, numeric, numeric, numeric, numeric, date'
      ), '')) > 0
      and exists (
        select 1 from actual_indexes
        where index_name = 'nutrition_targets_one_active_context_uidx'
          and indisunique and predicate is not null
      ),
    jsonb_build_object('initial_context', 'daily', 'initial_source', 'member')

  union all
  select
    'portion_unit_and_conversion_contract',
    position('explicit portion or density conversion required' in coalesce((
      select lower(source) from actual_functions where function_name = 'fmz_phase4_log_food_item' and argument_types = 'uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamp with time zone'
    ), '')) > 0
      and position('v_food.density_g_per_ml' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_log_food_item' and argument_types = 'uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamp with time zone'
      ), '')) > 0
      and position('p_consumed_unit not in (''g'', ''ml'', ''serving'', ''piece'')' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_log_food_item' and argument_types = 'uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamp with time zone'
      ), '')) > 0,
    jsonb_build_object('units', jsonb_build_array('g', 'ml', 'serving', 'piece'), 'generic_liter_kilogram_rule', false)

  union all
  select
    'immutable_food_log_snapshots',
    position('historical food log item snapshots are immutable' in coalesce((
      select lower(source) from actual_functions where function_name = 'fmz_phase4_enforce_food_log_item_owner' and argument_types = ''
    ), '')) > 0
      and position('food_name_snapshot' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_log_food_item' and argument_types = 'uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamp with time zone'
      ), '')) > 0
      and position('provenance_snapshot' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_log_food_item' and argument_types = 'uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamp with time zone'
      ), '')) > 0
      and position('calculation_version' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_log_food_item' and argument_types = 'uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamp with time zone'
      ), '')) > 0,
    jsonb_build_object('catalog_edits_rewrite_history', false)

  union all
  select
    'idempotent_request_and_day_identity',
    exists (select 1 from actual_indexes where index_name = 'nutrition_targets_user_request_uidx' and indisunique)
      and exists (select 1 from actual_indexes where index_name = 'food_log_items_user_request_uidx' and indisunique)
      and exists (select 1 from actual_constraints where constraint_name = 'food_logs_user_date_unique')
      and position('fmz_phase4_custom_food_request:' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_upsert_custom_food' and argument_types = 'uuid, text, text, numeric, text, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, timestamp with time zone'
      ), '')) > 0
      and position('fmz_phase4_food_portion_request:' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_upsert_food_portion' and argument_types = 'uuid, uuid, text, numeric, text, numeric, text, boolean, timestamp with time zone'
      ), '')) > 0
      and position('fmz_phase4_food_log_request:' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_log_food_item' and argument_types = 'uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamp with time zone'
      ), '')) > 0
      and position('fmz_phase4_food_log_item_request:' in coalesce((
        select lower(source) from actual_functions where function_name = 'fmz_phase4_archive_food_log_item' and argument_types = 'uuid, timestamp with time zone'
      ), '')) > 0,
    jsonb_build_object(
      'target_request_unique', true,
      'item_request_unique', true,
      'user_date_unique', true,
      'stable_object_request_locks', true
    )

  union all
  select
    'normalized_tables_empty_after_schema_only_execution',
    (select bool_and(row_count = 0) from normalized_row_counts),
    jsonb_build_object(
      'counts', (select jsonb_object_agg(table_name, row_count order by table_name) from normalized_row_counts)
    )

  union all
  select
    'phase1_phase2_phase3_legacy_guards',
    (select bool_and(table_exists and rls_enabled) from legacy_guard_state)
      and not exists (select 1 from missing_legacy_guard_columns)
      and exists (
        select 1
        from information_schema.columns
        where table_schema = 'public'
          and table_name = 'coach_workspaces'
          and column_name = 'state'
      ),
    jsonb_build_object(
      'tables', (select jsonb_agg(to_jsonb(g) order by table_name) from legacy_guard_state g),
      'missing_guard_columns', coalesce((select jsonb_agg(to_jsonb(g)) from missing_legacy_guard_columns g), '[]'::jsonb),
      'coach_workspaces_state_exists', exists (
        select 1
        from information_schema.columns
        where table_schema = 'public'
          and table_name = 'coach_workspaces'
          and column_name = 'state'
      )
    )

  union all
  select
    'no_forbidden_runtime_reference',
    (select source from phase4_definition_text) !~ (
      '(' || 'hgoygc' || 'viutmynaihcvpd'
      || '|service' || '_role'
      || '|supabase' || '_service' || '_role'
      || '|secret' || '_key'
      || '|openai|stripe' || '_secret|https?://)'
    )
      and (select source from phase4_policy_text) !~ '(trainer_id|linked_trainer|coach_client)',
    jsonb_build_object('production_or_secret_or_remote_reference_present', false)
)
select jsonb_build_object(
  'project_guard', 'mokxyyullfhkfalopbzd',
  'verification_scope', 'phase4_nutrition_schema_slice1',
  'overall_pass', bool_and(pass),
  'checks', jsonb_agg(
    jsonb_build_object('check', check_name, 'pass', pass, 'details', details)
    order by check_name
  )
) as verification_result
from checks;
