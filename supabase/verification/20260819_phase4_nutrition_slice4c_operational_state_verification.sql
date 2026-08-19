-- FitMetZorge Phase 4 Nutrition Slice 4C post-migration verification.
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- One SELECT/CTE statement. It invokes no application function and changes no data.

with
expected_tables(table_name) as (
  values
    ('nutrition_provider_query_cache'::text),
    ('nutrition_provider_food_cache'),
    ('nutrition_provider_rate_buckets'),
    ('nutrition_provider_runtime_state')
),
actual_tables as (
  select c.oid, c.relname::text as table_name, c.relrowsecurity, c.relacl, c.relowner
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and c.relname like 'nutrition_provider_%'
),
table_mismatches as (
  select e.table_name as expected_table, a.table_name as actual_table
  from expected_tables e
  full join actual_tables a using (table_name)
  where e.table_name is null or a.table_name is null
),
expected_columns(table_name, ordinal_position, column_name, formatted_type, not_null, default_fragment) as (
  values
    ('nutrition_provider_query_cache'::text, 1, 'provider_code'::text, 'text'::text, true, null::text),
    ('nutrition_provider_query_cache', 2, 'query_hmac', 'text', true, null),
    ('nutrition_provider_query_cache', 3, 'locale', 'text', true, null),
    ('nutrition_provider_query_cache', 4, 'country_code', 'text', true, null),
    ('nutrition_provider_query_cache', 5, 'page_number', 'smallint', true, null),
    ('nutrition_provider_query_cache', 6, 'page_size', 'smallint', true, null),
    ('nutrition_provider_query_cache', 7, 'data_type_filter', 'text[]', true, null),
    ('nutrition_provider_query_cache', 8, 'filter_key', 'text', true, null),
    ('nutrition_provider_query_cache', 9, 'filter_identity', 'jsonb', true, '''{}'''),
    ('nutrition_provider_query_cache', 10, 'mapping_version', 'text', true, null),
    ('nutrition_provider_query_cache', 11, 'result_payload', 'jsonb', true, null),
    ('nutrition_provider_query_cache', 12, 'payload_checksum', 'text', true, null),
    ('nutrition_provider_query_cache', 13, 'result_count', 'smallint', true, null),
    ('nutrition_provider_query_cache', 14, 'cache_status', 'text', true, null),
    ('nutrition_provider_query_cache', 15, 'source_version', 'text', false, null),
    ('nutrition_provider_query_cache', 16, 'fetched_at', 'timestamp with time zone', true, null),
    ('nutrition_provider_query_cache', 17, 'expires_at', 'timestamp with time zone', true, null),
    ('nutrition_provider_query_cache', 18, 'created_at', 'timestamp with time zone', true, 'now()'),
    ('nutrition_provider_query_cache', 19, 'updated_at', 'timestamp with time zone', true, 'now()'),
    ('nutrition_provider_food_cache', 1, 'provider_code', 'text', true, null),
    ('nutrition_provider_food_cache', 2, 'provider_food_id', 'text', true, null),
    ('nutrition_provider_food_cache', 3, 'provider_data_type', 'text', true, null),
    ('nutrition_provider_food_cache', 4, 'mapping_version', 'text', true, null),
    ('nutrition_provider_food_cache', 5, 'candidate_id', 'uuid', true, null),
    ('nutrition_provider_food_cache', 6, 'normalized_payload', 'jsonb', true, null),
    ('nutrition_provider_food_cache', 7, 'payload_checksum', 'text', true, null),
    ('nutrition_provider_food_cache', 8, 'quality_state', 'text', true, '''candidate'''),
    ('nutrition_provider_food_cache', 9, 'rejection_code', 'text', false, null),
    ('nutrition_provider_food_cache', 10, 'source_version', 'text', false, null),
    ('nutrition_provider_food_cache', 11, 'source_updated_at', 'timestamp with time zone', false, null),
    ('nutrition_provider_food_cache', 12, 'provenance', 'jsonb', true, '''{}'''),
    ('nutrition_provider_food_cache', 13, 'metadata', 'jsonb', true, '''{}'''),
    ('nutrition_provider_food_cache', 14, 'fetched_at', 'timestamp with time zone', true, null),
    ('nutrition_provider_food_cache', 15, 'expires_at', 'timestamp with time zone', true, null),
    ('nutrition_provider_food_cache', 16, 'created_at', 'timestamp with time zone', true, 'now()'),
    ('nutrition_provider_food_cache', 17, 'updated_at', 'timestamp with time zone', true, 'now()'),
    ('nutrition_provider_rate_buckets', 1, 'provider_code', 'text', true, null),
    ('nutrition_provider_rate_buckets', 2, 'bucket_scope', 'text', true, null),
    ('nutrition_provider_rate_buckets', 3, 'subject_hmac', 'text', true, null),
    ('nutrition_provider_rate_buckets', 4, 'window_start', 'timestamp with time zone', true, null),
    ('nutrition_provider_rate_buckets', 5, 'window_end', 'timestamp with time zone', true, null),
    ('nutrition_provider_rate_buckets', 6, 'window_seconds', 'integer', true, null),
    ('nutrition_provider_rate_buckets', 7, 'limit_value', 'integer', true, null),
    ('nutrition_provider_rate_buckets', 8, 'request_count', 'integer', true, '0'),
    ('nutrition_provider_rate_buckets', 9, 'consumed_request_ids', 'uuid[]', true, '''{}'''),
    ('nutrition_provider_rate_buckets', 10, 'created_at', 'timestamp with time zone', true, 'now()'),
    ('nutrition_provider_rate_buckets', 11, 'updated_at', 'timestamp with time zone', true, 'now()'),
    ('nutrition_provider_runtime_state', 1, 'provider_code', 'text', true, null),
    ('nutrition_provider_runtime_state', 2, 'circuit_state', 'text', true, '''closed'''),
    ('nutrition_provider_runtime_state', 3, 'consecutive_failures', 'integer', true, '0'),
    ('nutrition_provider_runtime_state', 4, 'opened_at', 'timestamp with time zone', false, null),
    ('nutrition_provider_runtime_state', 5, 'next_probe_at', 'timestamp with time zone', false, null),
    ('nutrition_provider_runtime_state', 6, 'last_success_at', 'timestamp with time zone', false, null),
    ('nutrition_provider_runtime_state', 7, 'last_failure_at', 'timestamp with time zone', false, null),
    ('nutrition_provider_runtime_state', 8, 'last_error_class', 'text', false, null),
    ('nutrition_provider_runtime_state', 9, 'upstream_rate_limit', 'integer', false, null),
    ('nutrition_provider_runtime_state', 10, 'upstream_rate_remaining', 'integer', false, null),
    ('nutrition_provider_runtime_state', 11, 'upstream_rate_reset_at', 'timestamp with time zone', false, null),
    ('nutrition_provider_runtime_state', 12, 'metadata', 'jsonb', true, '''{}'''),
    ('nutrition_provider_runtime_state', 13, 'created_at', 'timestamp with time zone', true, 'now()'),
    ('nutrition_provider_runtime_state', 14, 'updated_at', 'timestamp with time zone', true, 'now()')
),
actual_columns as (
  select
    c.relname::text as table_name,
    a.attnum::integer as ordinal_position,
    a.attname::text as column_name,
    pg_catalog.format_type(a.atttypid, a.atttypmod)::text as formatted_type,
    a.attnotnull as not_null,
    pg_catalog.pg_get_expr(d.adbin, d.adrelid)::text as default_expression
  from pg_catalog.pg_attribute a
  join pg_catalog.pg_class c on c.oid = a.attrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  left join pg_catalog.pg_attrdef d on d.adrelid = a.attrelid and d.adnum = a.attnum
  where n.nspname = 'public'
    and c.relname in (select table_name from expected_tables)
    and c.relkind = 'r'
    and a.attnum > 0
    and not a.attisdropped
),
column_mismatches as (
  select
    coalesce(e.table_name, a.table_name) as table_name,
    e.column_name as expected_column,
    a.column_name as actual_column,
    e.formatted_type as expected_type,
    a.formatted_type as actual_type,
    e.not_null as expected_not_null,
    a.not_null as actual_not_null,
    e.default_fragment,
    a.default_expression
  from expected_columns e
  full join actual_columns a using (table_name, ordinal_position)
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
expected_constraints(table_name, constraint_name, constraint_type, required_fragments) as (
  values
    ('nutrition_provider_query_cache'::text, 'nutrition_provider_query_cache_pkey'::text, 'p'::text, array['provider_code','query_hmac','locale','country_code','page_number','page_size','filter_key','mapping_version']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_provider_check', 'c', array['provider_code','usda_fdc']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_query_hmac_check', 'c', array['query_hmac','64']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_locale_check', 'c', array['locale','nl','en','de']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_country_check', 'c', array['country_code','A-Z','2']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_page_check', 'c', array['page_number','page_size','3','10']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_data_types_check', 'c', array['data_type_filter','Foundation','Survey (FNDDS)','SR Legacy']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_filter_key_check', 'c', array['filter_key','64']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_filter_identity_check', 'c', array['filter_identity','jsonb_typeof','4096','raw_query','user_id','auth_uid']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_mapping_version_check', 'c', array['mapping_version','80']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_payload_check', 'c', array['result_payload','array','131072']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_checksum_check', 'c', array['payload_checksum','64']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_result_count_check', 'c', array['result_count','10','jsonb_array_length']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_status_check', 'c', array['cache_status','positive','empty','quarantined']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_status_payload_check', 'c', array['cache_status','result_count']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_source_version_check', 'c', array['source_version','120']::text[]),
    ('nutrition_provider_query_cache', 'nutrition_provider_query_cache_expiry_check', 'c', array['expires_at','fetched_at','7 days']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_pkey', 'p', array['provider_code','provider_food_id','mapping_version']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_provider_check', 'c', array['provider_code','usda_fdc']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_provider_food_id_check', 'c', array['provider_food_id','160']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_data_type_check', 'c', array['provider_data_type','Foundation','Survey (FNDDS)','SR Legacy']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_mapping_version_check', 'c', array['mapping_version','80']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_payload_check', 'c', array['normalized_payload','object','131072']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_checksum_check', 'c', array['payload_checksum','64']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_quality_check', 'c', array['quality_state','candidate','validated','quarantined','rejected']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_rejection_check', 'c', array['quality_state','rejection_code','80']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_source_version_check', 'c', array['source_version','120']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_json_objects_check', 'c', array['provenance','metadata','32768','8192']::text[]),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_expiry_check', 'c', array['expires_at','fetched_at','180 days']::text[]),
    ('nutrition_provider_rate_buckets', 'nutrition_provider_rate_buckets_pkey', 'p', array['provider_code','bucket_scope','subject_hmac','window_start']::text[]),
    ('nutrition_provider_rate_buckets', 'nutrition_provider_rate_buckets_provider_check', 'c', array['provider_code','usda_fdc']::text[]),
    ('nutrition_provider_rate_buckets', 'nutrition_provider_rate_buckets_scope_check', 'c', array['user_30_seconds','user_10_minutes','user_day','provider_hour']::text[]),
    ('nutrition_provider_rate_buckets', 'nutrition_provider_rate_buckets_contract_check', 'c', array['subject_hmac','30','3','600','12','86400','100','3600','800','global']::text[]),
    ('nutrition_provider_rate_buckets', 'nutrition_provider_rate_buckets_window_check', 'c', array['window_end','window_start','window_seconds','make_interval','to_timestamp']::text[]),
    ('nutrition_provider_rate_buckets', 'nutrition_provider_rate_buckets_count_check', 'c', array['request_count','limit_value','cardinality','1000']::text[]),
    ('nutrition_provider_runtime_state', 'nutrition_provider_runtime_state_pkey', 'p', array['provider_code']::text[]),
    ('nutrition_provider_runtime_state', 'nutrition_provider_runtime_state_provider_check', 'c', array['provider_code','usda_fdc']::text[]),
    ('nutrition_provider_runtime_state', 'nutrition_provider_runtime_state_circuit_check', 'c', array['circuit_state','closed','open','half_open']::text[]),
    ('nutrition_provider_runtime_state', 'nutrition_provider_runtime_state_failure_count_check', 'c', array['consecutive_failures','1000000']::text[]),
    ('nutrition_provider_runtime_state', 'nutrition_provider_runtime_state_transition_shape_check', 'c', array['circuit_state','opened_at','next_probe_at']::text[]),
    ('nutrition_provider_runtime_state', 'nutrition_provider_runtime_state_error_class_check', 'c', array['last_error_class','80']::text[]),
    ('nutrition_provider_runtime_state', 'nutrition_provider_runtime_state_upstream_rate_check', 'c', array['upstream_rate_limit','upstream_rate_remaining','1000000']::text[]),
    ('nutrition_provider_runtime_state', 'nutrition_provider_runtime_state_metadata_check', 'c', array['metadata','object','4096']::text[])
),
actual_constraints as (
  select
    rel.relname::text as table_name,
    c.conname::text as constraint_name,
    c.contype::text as constraint_type,
    case
      when c.contype = 'p' then coalesce((
        select array_to_string(array_agg(a.attname::text order by u.ord), ',')
        from unnest(c.conkey) with ordinality as u(attnum, ord)
        join pg_catalog.pg_attribute a on a.attrelid = c.conrelid and a.attnum = u.attnum
      ), '')
      else pg_catalog.pg_get_expr(c.conbin, c.conrelid)::text
    end as definition
  from pg_catalog.pg_constraint c
  join pg_catalog.pg_class rel on rel.oid = c.conrelid
  join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
  where n.nspname = 'public'
    and rel.relname in (select table_name from expected_tables)
),
constraint_mismatches as (
  select e.table_name, e.constraint_name, a.constraint_type, a.definition
  from expected_constraints e
  left join actual_constraints a using (table_name, constraint_name)
  where a.constraint_name is null
     or a.constraint_type <> e.constraint_type
     or exists (
       select 1
       from unnest(e.required_fragments) as f(value)
       where position(lower(f.value) in lower(a.definition)) = 0
     )
  union all
  select a.table_name, a.constraint_name, a.constraint_type, a.definition
  from actual_constraints a
  left join expected_constraints e using (table_name, constraint_name)
  where e.constraint_name is null
),
expected_indexes(index_name, table_name, is_unique, required_fragments) as (
  values
    ('nutrition_provider_food_cache_candidate_mapping_uidx'::text, 'nutrition_provider_food_cache'::text, true, array['candidate_id','mapping_version']::text[]),
    ('nutrition_provider_query_cache_expires_idx', 'nutrition_provider_query_cache', false, array['expires_at']::text[]),
    ('nutrition_provider_query_cache_status_expires_idx', 'nutrition_provider_query_cache', false, array['provider_code','cache_status','expires_at']::text[]),
    ('nutrition_provider_food_cache_expires_idx', 'nutrition_provider_food_cache', false, array['expires_at']::text[]),
    ('nutrition_provider_food_cache_quality_expires_idx', 'nutrition_provider_food_cache', false, array['provider_code','quality_state','expires_at','provider_food_id']::text[]),
    ('nutrition_provider_rate_buckets_window_end_idx', 'nutrition_provider_rate_buckets', false, array['window_end']::text[])
),
actual_indexes as (
  select
    idx.relname::text as index_name,
    rel.relname::text as table_name,
    i.indisunique as is_unique,
    i.indisvalid as is_valid,
    i.indisready as is_ready,
    pg_catalog.pg_get_indexdef(idx.oid)::text as definition
  from pg_catalog.pg_index i
  join pg_catalog.pg_class idx on idx.oid = i.indexrelid
  join pg_catalog.pg_class rel on rel.oid = i.indrelid
  join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
  where n.nspname = 'public'
    and rel.relname in (select table_name from expected_tables)
    and not i.indisprimary
),
index_mismatches as (
  select e.index_name, a.table_name, a.definition
  from expected_indexes e
  left join actual_indexes a using (index_name)
  where a.index_name is null
     or a.table_name <> e.table_name
     or a.is_unique <> e.is_unique
     or not a.is_valid
     or not a.is_ready
     or exists (
       select 1
       from unnest(e.required_fragments) as f(value)
       where position(lower(f.value) in lower(a.definition)) = 0
     )
  union all
  select a.index_name, a.table_name, a.definition
  from actual_indexes a
  left join expected_indexes e using (index_name)
  where e.index_name is null
),
table_acl as (
  select
    t.table_name,
    case when acl.grantee = 0 then 'PUBLIC' else coalesce(r.rolname::text, '<missing-role>') end as grantee_name,
    acl.privilege_type::text
  from actual_tables t
  cross join lateral pg_catalog.aclexplode(
    coalesce(t.relacl, pg_catalog.acldefault('r', t.relowner))
  ) acl
  left join pg_catalog.pg_roles r on r.oid = acl.grantee
),
operational_policies as (
  select p.tablename::text as table_name, p.policyname::text as policy_name, p.cmd::text
  from pg_catalog.pg_policies p
  where p.schemaname = 'public'
    and p.tablename in (select table_name from expected_tables)
),
expected_functions(function_name, argument_types) as (
  values
    ('fmz_phase4_provider_consume_rate_limits'::text, 'text, text, uuid'::text),
    ('fmz_phase4_provider_transition_runtime_state', 'text, text, integer, text, integer, integer, timestamp with time zone, jsonb')
),
actual_functions as (
  select
    p.oid,
    p.proname::text as function_name,
    pg_catalog.oidvectortypes(p.proargtypes)::text as argument_types,
    p.prosecdef as security_definer,
    p.provolatile,
    p.prorettype,
    p.proconfig,
    p.proacl,
    p.proowner,
    p.prosrc::text as source
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname like 'fmz_phase4_provider_%'
),
function_acl as (
  select
    f.function_name,
    case when acl.grantee = 0 then 'PUBLIC' else coalesce(r.rolname::text, '<missing-role>') end as grantee_name,
    acl.privilege_type::text
  from actual_functions f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) acl
  left join pg_catalog.pg_roles r on r.oid = acl.grantee
),
function_mismatches as (
  select e.function_name as expected_function, a.function_name as actual_function, a.argument_types
  from expected_functions e
  full join actual_functions a using (function_name, argument_types)
  where e.function_name is null or a.function_name is null
),
operational_triggers as (
  select
    rel.relname::text as table_name,
    t.tgname::text as trigger_name,
    p.proname::text as function_name,
    t.tgenabled
  from pg_catalog.pg_trigger t
  join pg_catalog.pg_class rel on rel.oid = t.tgrelid
  join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
  join pg_catalog.pg_proc p on p.oid = t.tgfoid
  where n.nspname = 'public'
    and rel.relname in (select table_name from expected_tables)
    and not t.tgisinternal
),
expected_triggers(table_name, trigger_name) as (
  values
    ('nutrition_provider_query_cache'::text, 'nutrition_provider_query_cache_90_touch_updated_at'::text),
    ('nutrition_provider_food_cache', 'nutrition_provider_food_cache_90_touch_updated_at'),
    ('nutrition_provider_rate_buckets', 'nutrition_provider_rate_buckets_90_touch_updated_at'),
    ('nutrition_provider_runtime_state', 'nutrition_provider_runtime_state_90_touch_updated_at')
),
trigger_mismatches as (
  select e.table_name, e.trigger_name, a.function_name, a.tgenabled
  from expected_triggers e
  left join operational_triggers a using (table_name, trigger_name)
  where a.trigger_name is null
     or a.function_name <> 'fmz_phase4_touch_updated_at'
     or a.tgenabled <> 'O'
  union all
  select a.table_name, a.trigger_name, a.function_name, a.tgenabled
  from operational_triggers a
  left join expected_triggers e using (table_name, trigger_name)
  where e.trigger_name is null
),
slice4b_state as (
  select
    exists (
      select 1
      from pg_catalog.pg_extension e
      join pg_catalog.pg_namespace n on n.oid = e.extnamespace
      where e.extname = 'pg_trgm' and n.nspname = 'extensions'
    ) as trgm_ok,
    exists (
      select 1 from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public' and c.relname = 'food_aliases' and c.relkind = 'r' and c.relrowsecurity
    ) as aliases_ok,
    (select count(*) from pg_catalog.pg_policies where schemaname = 'public' and tablename = 'food_aliases') as alias_policy_count,
    (select count(*) from public.food_aliases) as alias_row_count,
    (
      select count(*)
      from pg_catalog.pg_indexes
      where schemaname = 'public'
        and indexname in (
          'food_aliases_active_identity_uidx',
          'food_aliases_food_status_idx',
          'food_aliases_active_prefix_idx',
          'food_aliases_active_trgm_idx',
          'food_aliases_market_priority_idx',
          'foods_active_name_trgm_idx',
          'foods_active_brand_trgm_idx'
        )
    ) as slice4b_index_count
),
guard_tables(table_name) as (
  values
    ('profiles'::text), ('coach_workspaces'), ('user_settings'), ('user_onboarding'), ('entitlements'),
    ('recovery_logs'), ('training_plans'), ('training_plan_days'), ('training_plan_exercises'),
    ('workout_sessions'), ('workout_set_logs'), ('exercises'), ('nutrition_preferences'), ('foods'),
    ('food_portions'), ('nutrition_targets'), ('food_logs'), ('food_log_items'), ('food_aliases')
),
guard_table_state as (
  select g.table_name, c.relrowsecurity
  from guard_tables g
  left join pg_catalog.pg_class c on c.relname = g.table_name and c.relkind = 'r'
  left join pg_catalog.pg_namespace n on n.oid = c.relnamespace and n.nspname = 'public'
  where n.oid is not null
),
guard_functions as (
  select
    pg_catalog.to_regprocedure('public.fmz_phase4_replace_food_log_item(uuid,uuid,uuid,timestamp with time zone,text,uuid,uuid,numeric,text,text)') as replacement_rpc,
    pg_catalog.to_regprocedure('public.fmz_phase4_search_foods(text,integer,text,uuid)') as search_rpc
),
row_counts as (
  select
    (select count(*) from public.nutrition_provider_query_cache) as query_cache_count,
    (select count(*) from public.nutrition_provider_food_cache) as food_cache_count,
    (select count(*) from public.nutrition_provider_rate_buckets) as rate_bucket_count,
    (select count(*) from public.nutrition_provider_runtime_state) as runtime_state_count,
    (
      select count(*)
      from public.foods
      where catalog_scope = 'canonical'
        and source_provider in ('usda_fdc', 'open_food_facts')
    ) as provider_canonical_food_count
),
checks(check_name, pass, details) as (
  select 'exact_operational_tables', not exists (select 1 from table_mismatches),
    jsonb_build_object('mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from table_mismatches m), '[]'::jsonb))
  union all
  select 'exact_columns', not exists (select 1 from column_mismatches),
    jsonb_build_object('expected', (select count(*) from expected_columns), 'actual', (select count(*) from actual_columns), 'mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from column_mismatches m), '[]'::jsonb))
  union all
  select 'constraints', not exists (select 1 from constraint_mismatches),
    jsonb_build_object('mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from constraint_mismatches m), '[]'::jsonb))
  union all
  select 'indexes', not exists (select 1 from index_mismatches),
    jsonb_build_object('mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from index_mismatches m), '[]'::jsonb))
  union all
  select 'rls_enabled_zero_policies',
    (select count(*) from actual_tables) = 4
      and not exists (select 1 from actual_tables where not relrowsecurity)
      and not exists (select 1 from operational_policies),
    jsonb_build_object('policies', coalesce((select jsonb_agg(to_jsonb(p)) from operational_policies p), '[]'::jsonb))
  union all
  select 'member_anon_public_table_acl_none',
    not exists (select 1 from table_acl where grantee_name in ('authenticated', 'anon', 'PUBLIC')),
    jsonb_build_object('unexpected', coalesce((select jsonb_agg(to_jsonb(a)) from table_acl a where grantee_name in ('authenticated','anon','PUBLIC')), '[]'::jsonb))
  union all
  select 'service_role_table_acl_minimal',
    coalesce((select array_agg(privilege_type order by privilege_type)::text[] from table_acl where table_name = 'nutrition_provider_query_cache' and grantee_name = 'service_role'), array[]::text[]) = array['INSERT','SELECT','UPDATE']::text[]
      and coalesce((select array_agg(privilege_type order by privilege_type)::text[] from table_acl where table_name = 'nutrition_provider_food_cache' and grantee_name = 'service_role'), array[]::text[]) = array['INSERT','SELECT','UPDATE']::text[]
      and coalesce((select array_agg(privilege_type order by privilege_type)::text[] from table_acl where table_name = 'nutrition_provider_rate_buckets' and grantee_name = 'service_role'), array[]::text[]) = array[]::text[]
      and coalesce((select array_agg(privilege_type order by privilege_type)::text[] from table_acl where table_name = 'nutrition_provider_runtime_state' and grantee_name = 'service_role'), array[]::text[]) = array['SELECT']::text[],
    jsonb_build_object('service_role_acl', coalesce((select jsonb_agg(to_jsonb(a)) from table_acl a where grantee_name = 'service_role'), '[]'::jsonb))
  union all
  select 'internal_functions_exact_security',
    not exists (select 1 from function_mismatches)
      and (select count(*) from actual_functions) = 2
      and not exists (
        select 1 from actual_functions
        where not security_definer
          or provolatile <> 'v'
          or prorettype <> 'jsonb'::regtype
          or not coalesce('search_path=pg_catalog' = any(proconfig), false)
      )
      and not exists (select 1 from function_acl where grantee_name in ('authenticated','anon','PUBLIC'))
      and not exists (
        select 1 from actual_functions f
        where coalesce((select array_agg(a.privilege_type order by a.privilege_type)::text[] from function_acl a where a.function_name = f.function_name and a.grantee_name = 'service_role'), array[]::text[]) <> array['EXECUTE']::text[]
      ),
    jsonb_build_object('functions', coalesce((select jsonb_agg(jsonb_build_object('name',function_name,'args',argument_types,'security_definer',security_definer,'config',proconfig)) from actual_functions), '[]'::jsonb), 'acl', coalesce((select jsonb_agg(to_jsonb(a)) from function_acl a), '[]'::jsonb))
  union all
  select 'atomic_rate_limit_source_contract',
    exists (
      select 1 from actual_functions
      where function_name = 'fmz_phase4_provider_consume_rate_limits'
        and position('pg_advisory_xact_lock' in source) > 0
        and position('fmz_phase4_provider_rate:' in source) > 0
        and position('user_30_seconds' in source) > 0
        and position('user_10_minutes' in source) > 0
        and position('user_day' in source) > 0
        and position('provider_hour' in source) > 0
        and position('array[3, 12, 100, 800]' in source) > 0
        and position('v_replay_count not in (0, 4)' in source) > 0
        and position('v_failed_until is not null' in source) > 0
        and position('request_count = request_count + 1' in source) > 0
        and position('consumed_request_ids' in source) > 0
    ),
    '{}'::jsonb
  union all
  select 'runtime_transition_source_contract',
    exists (
      select 1 from actual_functions
      where function_name = 'fmz_phase4_provider_transition_runtime_state'
        and position('pg_advisory_xact_lock' in source) > 0
        and position('begin_probe' in source) > 0
        and position('half_open' in source) > 0
        and position('rate_limited' in source) > 0
        and position('consecutive_failures' in source) > 0
        and position('next_probe_at' in source) > 0
    ),
    '{}'::jsonb
  union all
  select 'updated_at_triggers', not exists (select 1 from trigger_mismatches),
    jsonb_build_object('mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from trigger_mismatches m), '[]'::jsonb))
  union all
  select 'ingestion_ledger_deferred',
    pg_catalog.to_regclass('public.nutrition_provider_ingestion_ledger') is null,
    '{}'::jsonb
  union all
  select 'operational_tables_initially_empty',
    query_cache_count = 0 and food_cache_count = 0 and rate_bucket_count = 0 and runtime_state_count = 0,
    to_jsonb(row_counts)
  from row_counts
  union all
  select 'no_provider_canonical_import', provider_canonical_food_count = 0,
    jsonb_build_object('provider_canonical_food_count', provider_canonical_food_count)
  from row_counts
  union all
  select 'slice4b_live_guard',
    trgm_ok and aliases_ok and alias_policy_count = 1 and alias_row_count = 0 and slice4b_index_count = 7,
    to_jsonb(slice4b_state)
  from slice4b_state
  union all
  select 'frozen_guard_tables',
    (select count(*) from guard_table_state) = (select count(*) from guard_tables)
      and not exists (select 1 from guard_table_state where not relrowsecurity),
    jsonb_build_object('expected', (select count(*) from guard_tables), 'actual', (select count(*) from guard_table_state), 'non_rls', coalesce((select jsonb_agg(table_name) from guard_table_state where not relrowsecurity), '[]'::jsonb))
  union all
  select 'frozen_slice3_and_search_functions', replacement_rpc is not null and search_rpc is not null,
    to_jsonb(guard_functions)
  from guard_functions
)
select jsonb_build_object(
  'scope', 'phase4_nutrition_slice4c_operational_state',
  'staging_project_ref', 'mokxyyullfhkfalopbzd',
  'overall_pass', bool_and(pass),
  'checks', jsonb_agg(
    jsonb_build_object('check', check_name, 'pass', pass, 'details', details)
    order by check_name
  )
) as verification_result
from checks;
