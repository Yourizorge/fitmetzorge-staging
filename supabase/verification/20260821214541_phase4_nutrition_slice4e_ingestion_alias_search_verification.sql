-- FitMetZorge Phase 4 Nutrition Slice 4E post-migration verifier
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- One SELECT/CTE statement. Metadata and row-count inspection only.

with
expected_ledger_columns(column_name, data_type, is_nullable) as (
  values
    ('id'::text, 'uuid'::text, 'NO'::text),
    ('artifact_version', 'text', 'NO'),
    ('artifact_sha256', 'text', 'NO'),
    ('source_provider', 'text', 'NO'),
    ('mapping_version', 'text', 'NO'),
    ('status', 'text', 'NO'),
    ('predecessor_ingestion_id', 'uuid', 'YES'),
    ('manifest_food_count', 'integer', 'NO'),
    ('manifest_alias_count', 'integer', 'NO'),
    ('reviewed_by', 'text', 'NO'),
    ('reviewed_at', 'timestamp with time zone', 'NO'),
    ('imported_at', 'timestamp with time zone', 'YES'),
    ('provenance', 'jsonb', 'NO'),
    ('metadata', 'jsonb', 'NO'),
    ('created_at', 'timestamp with time zone', 'NO'),
    ('updated_at', 'timestamp with time zone', 'NO')
),
ledger_columns as (
  select
    c.column_name::text,
    c.data_type::text,
    c.is_nullable::text,
    coalesce(c.column_default, '')::text as column_default
  from information_schema.columns c
  where c.table_schema = 'public'
    and c.table_name = 'nutrition_food_ingestions'
),
ledger_column_mismatches as (
  select
    e.column_name,
    e.data_type as expected_type,
    a.data_type as actual_type,
    e.is_nullable as expected_nullable,
    a.is_nullable as actual_nullable
  from expected_ledger_columns e
  left join ledger_columns a using (column_name)
  where a.column_name is null
     or a.data_type is distinct from e.data_type
     or a.is_nullable is distinct from e.is_nullable
  union all
  select a.column_name, null, a.data_type, null, a.is_nullable
  from ledger_columns a
  left join expected_ledger_columns e using (column_name)
  where e.column_name is null
),
relations as (
  select
    c.oid,
    c.relname::text as table_name,
    c.relrowsecurity,
    c.relowner
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and c.relname in ('nutrition_food_ingestions', 'foods', 'food_aliases')
),
constraints as (
  select
    rel.relname::text as table_name,
    con.conname::text as constraint_name,
    con.contype,
    con.confdeltype,
    pg_catalog.pg_get_constraintdef(con.oid, true)::text as definition,
    coalesce((
      select array_agg(att.attname::text order by key_columns.ord)::text[]
      from unnest(con.conkey) with ordinality key_columns(attnum, ord)
      join pg_catalog.pg_attribute att
        on att.attrelid = con.conrelid
       and att.attnum = key_columns.attnum
    ), array[]::text[]) as columns,
    coalesce((
      select array_agg(att.attname::text order by foreign_columns.ord)::text[]
      from unnest(con.confkey) with ordinality foreign_columns(attnum, ord)
      join pg_catalog.pg_attribute att
        on att.attrelid = con.confrelid
       and att.attnum = foreign_columns.attnum
    ), array[]::text[]) as foreign_columns,
    case when con.confrelid = 0 then null else con.confrelid::regclass::text end as foreign_table
  from pg_catalog.pg_constraint con
  join pg_catalog.pg_class rel on rel.oid = con.conrelid
  join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
  where n.nspname = 'public'
    and rel.relname in ('nutrition_food_ingestions', 'foods', 'food_aliases')
),
indexes as (
  select
    rel.relname::text as table_name,
    idx.relname::text as index_name,
    i.indisunique,
    i.indisvalid,
    i.indisready,
    pg_catalog.pg_get_indexdef(i.indexrelid)::text as definition,
    coalesce(pg_catalog.pg_get_expr(i.indpred, i.indrelid), '')::text as predicate
  from pg_catalog.pg_index i
  join pg_catalog.pg_class idx on idx.oid = i.indexrelid
  join pg_catalog.pg_class rel on rel.oid = i.indrelid
  join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
  where n.nspname = 'public'
    and rel.relname in ('nutrition_food_ingestions', 'foods', 'food_aliases')
),
policies as (
  select
    c.relname::text as table_name,
    p.polname::text as policy_name,
    p.polcmd,
    p.polpermissive,
    coalesce(array(
      select r.rolname::text
      from unnest(p.polroles) role_oid
      join pg_catalog.pg_roles r on r.oid = role_oid
      order by r.rolname::text
    ), array[]::text[]) as roles,
    coalesce(pg_catalog.pg_get_expr(p.polqual, p.polrelid), '')::text as using_expression,
    coalesce(pg_catalog.pg_get_expr(p.polwithcheck, p.polrelid), '')::text as check_expression
  from pg_catalog.pg_policy p
  join pg_catalog.pg_class c on c.oid = p.polrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname in ('nutrition_food_ingestions', 'foods', 'food_aliases')
),
table_acl as (
  select
    r.table_name,
    case
      when acl.grantee = 0 then 'PUBLIC'
      else coalesce(role_name.rolname::text, '<missing-role>')
    end as grantee_name,
    acl.privilege_type::text
  from relations r
  cross join lateral pg_catalog.aclexplode(
    coalesce((select c.relacl from pg_catalog.pg_class c where c.oid = r.oid), pg_catalog.acldefault('r', r.relowner))
  ) acl
  left join pg_catalog.pg_roles role_name on role_name.oid = acl.grantee
),
functions as (
  select
    p.oid,
    p.proname::text as function_name,
    pg_catalog.oidvectortypes(p.proargtypes)::text as argument_types,
    p.prosecdef as security_definer,
    p.provolatile,
    p.proretset,
    p.proconfig,
    p.proacl,
    p.proowner,
    p.prosrc::text as source,
    pg_catalog.regexp_replace(lower(p.prosrc::text), '[[:space:]]+', '', 'g') as compact_source
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname in (
      'fmz_phase4_enforce_food_ingestion_state',
      'fmz_phase4_prevent_food_ingestion_removal',
      'fmz_phase4_search_foods',
      'fmz_phase4_log_provider_food_item',
      'fmz_phase4_replace_provider_food_log_item',
      'fmz_phase4_resolve_provider_food_log_item'
    )
),
function_acl as (
  select
    f.function_name,
    f.argument_types,
    case
      when acl.grantee = 0 then 'PUBLIC'
      else coalesce(role_name.rolname::text, '<missing-role>')
    end as grantee_name,
    acl.privilege_type::text
  from functions f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) acl
  left join pg_catalog.pg_roles role_name on role_name.oid = acl.grantee
),
triggers as (
  select
    rel.relname::text as table_name,
    trg.tgname::text as trigger_name,
    proc.proname::text as function_name,
    trg.tgenabled
  from pg_catalog.pg_trigger trg
  join pg_catalog.pg_class rel on rel.oid = trg.tgrelid
  join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
  join pg_catalog.pg_proc proc on proc.oid = trg.tgfoid
  where n.nspname = 'public'
    and rel.relname = 'nutrition_food_ingestions'
    and not trg.tgisinternal
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
    ('food_aliases'),
    ('nutrition_targets'),
    ('food_logs'),
    ('food_log_items'),
    ('nutrition_provider_query_cache'),
    ('nutrition_provider_food_cache'),
    ('nutrition_provider_rate_buckets'),
    ('nutrition_provider_runtime_state'),
    ('nutrition_food_ingestions')
),
guard_tables as (
  select c.relname::text as table_name, c.relrowsecurity
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and c.relname in (select table_name from expected_guard_tables)
),
checks as (
  select
    'ledger_table_and_columns'::text as check_name,
    (select count(*) from relations where table_name = 'nutrition_food_ingestions') = 1
      and not exists (select 1 from ledger_column_mismatches)
      and (select count(*) from ledger_columns) = (select count(*) from expected_ledger_columns) as pass,
    jsonb_build_object(
      'actual_count', (select count(*) from ledger_columns),
      'expected_count', (select count(*) from expected_ledger_columns),
      'mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from ledger_column_mismatches m), '[]'::jsonb)
    ) as detail
  union all
  select
    'ledger_defaults_and_constraints',
    exists (select 1 from ledger_columns where column_name = 'status' and lower(column_default) like '%reviewed%')
      and exists (select 1 from constraints where table_name = 'nutrition_food_ingestions' and constraint_name = 'nutrition_food_ingestions_pkey' and contype = 'p' and columns = array['id']::text[])
      and exists (select 1 from constraints where table_name = 'nutrition_food_ingestions' and constraint_name = 'nutrition_food_ingestions_artifact_sha256_key' and contype = 'u' and columns = array['artifact_sha256']::text[])
      and exists (select 1 from constraints where table_name = 'nutrition_food_ingestions' and constraint_name = 'nutrition_food_ingestions_provider_version_key' and contype = 'u' and columns = array['source_provider', 'artifact_version']::text[])
      and exists (select 1 from constraints where table_name = 'nutrition_food_ingestions' and constraint_name = 'nutrition_food_ingestions_predecessor_ingestion_id_fkey' and contype = 'f' and foreign_table = 'nutrition_food_ingestions' and confdeltype = 'r')
      and (select count(*) from constraints where table_name = 'nutrition_food_ingestions' and contype = 'c') = 11,
    jsonb_build_object('constraints', (select count(*) from constraints where table_name = 'nutrition_food_ingestions'))
  union all
  select
    'ledger_constraint_semantics',
    exists (select 1 from constraints where constraint_name = 'nutrition_food_ingestions_artifact_sha256_check' and definition like '%64%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_food_ingestions_status_check' and lower(definition) like '%reviewed%' and lower(definition) like '%imported%' and lower(definition) like '%superseded%' and lower(definition) like '%rejected%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_food_ingestions_predecessor_check' and lower(definition) like '%predecessor_ingestion_id%' and definition like '%<>%id%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_food_ingestions_manifest_counts_check' and lower(definition) like '%manifest_food_count%' and lower(definition) like '%manifest_alias_count%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_food_ingestions_status_timestamps_check' and lower(definition) like '%imported_at%' and lower(definition) like '%reviewed_at%')
      and exists (select 1 from constraints where constraint_name = 'nutrition_food_ingestions_json_objects_check' and lower(definition) like '%jsonb_typeof%'),
    '{}'::jsonb
  union all
  select
    'ledger_indexes',
    exists (select 1 from indexes where index_name = 'nutrition_food_ingestions_status_created_idx' and indisvalid and indisready)
      and exists (select 1 from indexes where index_name = 'nutrition_food_ingestions_predecessor_uidx' and indisunique and indisvalid and indisready and lower(predicate) like '%predecessor_ingestion_id is not null%'),
    coalesce((select jsonb_agg(to_jsonb(i)) from indexes i where table_name = 'nutrition_food_ingestions'), '[]'::jsonb)
  union all
  select
    'ledger_rls_acl_and_no_policies',
    coalesce((select relrowsecurity from relations where table_name = 'nutrition_food_ingestions'), false)
      and not exists (select 1 from policies where table_name = 'nutrition_food_ingestions')
      and not exists (select 1 from table_acl where table_name = 'nutrition_food_ingestions' and grantee_name in ('PUBLIC', 'anon', 'authenticated', 'service_role')),
    jsonb_build_object(
      'policy_count', (select count(*) from policies where table_name = 'nutrition_food_ingestions'),
      'app_acl_count', (select count(*) from table_acl where table_name = 'nutrition_food_ingestions' and grantee_name in ('PUBLIC', 'anon', 'authenticated', 'service_role'))
    )
  union all
  select
    'ledger_state_and_removal_guards',
    (select count(*) from triggers) = 3
      and exists (select 1 from triggers where trigger_name = 'nutrition_food_ingestions_10_enforce_state' and function_name = 'fmz_phase4_enforce_food_ingestion_state' and tgenabled = 'O')
      and exists (select 1 from triggers where trigger_name = 'nutrition_food_ingestions_20_prevent_removal' and function_name = 'fmz_phase4_prevent_food_ingestion_removal' and tgenabled = 'O')
      and exists (select 1 from triggers where trigger_name = 'nutrition_food_ingestions_90_touch_updated_at' and function_name = 'fmz_phase4_touch_updated_at' and tgenabled = 'O')
      and not exists (select 1 from functions where function_name in ('fmz_phase4_enforce_food_ingestion_state', 'fmz_phase4_prevent_food_ingestion_removal') and security_definer)
      and not exists (select 1 from function_acl where function_name in ('fmz_phase4_enforce_food_ingestion_state', 'fmz_phase4_prevent_food_ingestion_removal') and grantee_name in ('PUBLIC', 'anon', 'authenticated', 'service_role')),
    coalesce((select jsonb_agg(to_jsonb(t)) from triggers t), '[]'::jsonb)
  union all
  select
    'ledger_predecessor_chain_and_lock',
    exists (
      select 1 from functions
      where function_name = 'fmz_phase4_enforce_food_ingestion_state'
        and lower(source) like '%pg_advisory_xact_lock%'
        and lower(source) like '%fmz_phase4_food_ingestion_chain:%'
        and lower(source) like '%subsequent food ingestion artifact requires predecessor%'
        and lower(source) like '%predecessor must use the same source provider%'
    ),
    '{}'::jsonb
  union all
  select
    'foods_ingestion_link',
    exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'foods' and column_name = 'ingestion_id' and data_type = 'uuid' and is_nullable = 'YES')
      and exists (select 1 from constraints where table_name = 'foods' and constraint_name = 'foods_ingestion_id_fkey' and contype = 'f' and columns = array['ingestion_id']::text[] and foreign_table = 'nutrition_food_ingestions' and foreign_columns = array['id']::text[] and confdeltype = 'r')
      and exists (select 1 from constraints where table_name = 'foods' and constraint_name = 'foods_ingestion_scope_check' and lower(definition) like '%canonical%')
      and exists (select 1 from constraints where table_name = 'foods' and constraint_name = 'foods_canonical_ingestion_quality_check' and lower(definition) like '%reviewed%' and lower(definition) like '%verified%')
      and exists (select 1 from indexes where index_name = 'foods_ingestion_id_idx' and indisvalid and indisready and lower(predicate) like '%ingestion_id is not null%'),
    '{}'::jsonb
  union all
  select
    'aliases_ingestion_and_preferred_rule',
    exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'food_aliases' and column_name = 'ingestion_id' and data_type = 'uuid' and is_nullable = 'YES')
      and exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'food_aliases' and column_name = 'is_preferred' and data_type = 'boolean' and is_nullable = 'NO')
      and exists (select 1 from constraints where table_name = 'food_aliases' and constraint_name = 'food_aliases_ingestion_id_fkey' and contype = 'f' and columns = array['ingestion_id']::text[] and foreign_table = 'nutrition_food_ingestions' and foreign_columns = array['id']::text[] and confdeltype = 'r')
      and exists (select 1 from constraints where table_name = 'food_aliases' and constraint_name = 'food_aliases_reviewed_ingestion_check' and lower(definition) like '%review_status%' and lower(definition) like '%pending%')
      and exists (select 1 from constraints where table_name = 'food_aliases' and constraint_name = 'food_aliases_preferred_review_check' and lower(definition) like '%language_code%' and lower(definition) like '%market_code%')
      and exists (select 1 from indexes where index_name = 'food_aliases_ingestion_id_idx' and indisvalid and indisready and lower(predicate) like '%ingestion_id is not null%')
      and exists (select 1 from indexes where index_name = 'food_aliases_preferred_nl_market_uidx' and indisunique and indisvalid and indisready and lower(predicate) like '%is_preferred%' and lower(predicate) like '%language_code%' and lower(predicate) like '%nl%'),
    '{}'::jsonb
  union all
  select
    'canonical_quality_visibility',
    exists (
      select 1 from policies
      where table_name = 'foods'
        and policy_name = 'foods_select_visible'
        and polcmd = 'r'
        and roles = array['authenticated']::text[]
        and lower(using_expression) like '%canonical%'
        and lower(using_expression) like '%quality_status%'
        and lower(using_expression) like '%reviewed%'
        and lower(using_expression) like '%verified%'
        and lower(using_expression) like '%ingestion_id%'
        and lower(using_expression) like '%custom%'
        and lower(using_expression) like '%owner_user_id%'
        and lower(using_expression) like '%auth.uid%'
    ),
    coalesce((select to_jsonb(p) from policies p where table_name = 'foods' and policy_name = 'foods_select_visible'), '{}'::jsonb)
  union all
  select
    'alias_quality_and_parent_visibility',
    exists (
      select 1 from policies
      where table_name = 'food_aliases'
        and policy_name = 'food_aliases_select_visible'
        and polcmd = 'r'
        and roles = array['authenticated']::text[]
        and lower(using_expression) like '%review_status%'
        and lower(using_expression) like '%reviewed%'
        and lower(using_expression) like '%verified%'
        and lower(using_expression) like '%quality_status%'
        and lower(using_expression) like '%ingestion_id%'
        and lower(using_expression) like '%owner_user_id%'
    ),
    coalesce((select to_jsonb(p) from policies p where table_name = 'food_aliases' and policy_name = 'food_aliases_select_visible'), '{}'::jsonb)
  union all
  select
    'search_signature_security_and_acl',
    exists (
      select 1 from functions
      where function_name = 'fmz_phase4_search_foods'
        and argument_types = 'text, integer, text, uuid'
        and not security_definer
        and provolatile = 's'
        and proretset
        and coalesce('search_path=pg_catalog, public, pg_temp' = any(proconfig), false)
    )
      and coalesce((
        select array_agg(grantee_name order by grantee_name)::text[]
        from function_acl
        where function_name = 'fmz_phase4_search_foods'
          and privilege_type = 'EXECUTE'
          and grantee_name in ('PUBLIC', 'anon', 'authenticated')
      ), array[]::text[]) = array['authenticated']::text[],
    '{}'::jsonb
  union all
  select
    'search_alias_table_participation',
    exists (
      select 1 from functions
      where function_name = 'fmz_phase4_search_foods'
        and compact_source like '%frompublic.food_aliasesa%'
    ),
    jsonb_build_object('source_form', 'compact_source', 'expected_fragment', 'frompublic.food_aliasesa')
  union all
  select
    'search_alias_reviewed_verified_gate',
    exists (
      select 1 from functions
      where function_name = 'fmz_phase4_search_foods'
        and compact_source like '%a.status=''active''%'
        and compact_source like '%a.review_statusin(''reviewed'',''verified'')%'
    ),
    jsonb_build_object(
      'source_form', 'compact_source',
      'expected_fragments', jsonb_build_array('a.status=''active''', 'a.review_statusin(''reviewed'',''verified'')')
    )
  union all
  select
    'search_canonical_reviewed_verified_quality_gate',
    exists (
      select 1 from functions
      where function_name = 'fmz_phase4_search_foods'
        and compact_source like '%f.status=''active''%'
        and compact_source like '%f.catalog_scope=''canonical''%'
        and compact_source like '%f.quality_statusin(''reviewed'',''verified'')%'
        and compact_source like '%f.ingestion_idisnotnull%'
    ),
    jsonb_build_object(
      'source_form', 'compact_source',
      'expected_fragments', jsonb_build_array(
        'f.status=''active''',
        'f.catalog_scope=''canonical''',
        'f.quality_statusin(''reviewed'',''verified'')',
        'f.ingestion_idisnotnull'
      )
    )
  union all
  select
    'search_preferred_alias_ranking',
    exists (
      select 1 from functions
      where function_name = 'fmz_phase4_search_foods'
        and compact_source like '%a.is_preferred%'
    ),
    jsonb_build_object('source_form', 'compact_source', 'expected_fragment', 'a.is_preferred')
  union all
  select
    'search_nl_language_priority',
    exists (
      select 1 from functions
      where function_name = 'fmz_phase4_search_foods'
        and compact_source like '%a.language_code=''nl''%'
    ),
    jsonb_build_object('source_form', 'compact_source', 'expected_fragment', 'a.language_code=''nl''')
  union all
  select
    'search_nl_market_priority',
    exists (
      select 1 from functions
      where function_name = 'fmz_phase4_search_foods'
        and compact_source like '%a.market_code=''nl''%'
    ),
    jsonb_build_object('source_form', 'compact_source', 'expected_fragment', 'a.market_code=''nl''')
  union all
  select
    'search_alias_pg_trgm_contract',
    exists (
      select 1 from functions
      where function_name = 'fmz_phase4_search_foods'
        and compact_source like '%extensions.similarity%'
        and compact_source like '%operator(extensions.%)%'
    ),
    jsonb_build_object(
      'source_form', 'compact_source',
      'expected_fragments', jsonb_build_array('extensions.similarity', 'operator(extensions.%)')
    )
  union all
  select
    'search_food_id_dedupe',
    exists (
      select 1 from functions
      where function_name = 'fmz_phase4_search_foods'
        and compact_source like '%distincton(c.food_id)%'
    ),
    jsonb_build_object('source_form', 'compact_source', 'expected_fragment', 'distincton(c.food_id)')
  union all
  select
    'search_stable_bounded_keyset',
    exists (
      select 1 from functions
      where function_name = 'fmz_phase4_search_foods'
        and lower(source) like '%p_after_name%'
        and lower(source) like '%p_after_id%'
        and lower(source) like '%cursor_key%'
        and lower(source) like '%limit 250%'
        and lower(source) like '%limit v_page_size%'
        and lower(source) not like '%offset%'
    ),
    '{}'::jsonb
  union all
  select
    'catalog_table_acl_and_no_browser_writes',
    coalesce((select array_agg(privilege_type order by privilege_type)::text[] from table_acl where table_name = 'foods' and grantee_name = 'authenticated'), array[]::text[]) = array['SELECT']::text[]
      and coalesce((select array_agg(privilege_type order by privilege_type)::text[] from table_acl where table_name = 'food_aliases' and grantee_name = 'authenticated'), array[]::text[]) = array['SELECT']::text[]
      and not exists (select 1 from table_acl where table_name in ('foods', 'food_aliases') and grantee_name in ('anon', 'PUBLIC')),
    '{}'::jsonb
  union all
  select
    'no_trainer_or_removal_policy',
    not exists (
      select 1 from policies
      where table_name in ('nutrition_food_ingestions', 'foods', 'food_aliases')
        and (
          polcmd = 'd'
          or lower(policy_name) like '%trainer%'
          or lower(using_expression) like '%trainer%'
          or lower(check_expression) like '%trainer%'
        )
    ),
    '{}'::jsonb
  union all
  select
    'frozen_slice4b_4c_4d_contracts',
    exists (select 1 from indexes where index_name = 'food_aliases_active_trgm_idx' and indisvalid and indisready)
      and exists (select 1 from indexes where index_name = 'foods_active_name_trgm_idx' and indisvalid and indisready)
      and (select count(*) from guard_tables where table_name in ('nutrition_provider_query_cache', 'nutrition_provider_food_cache', 'nutrition_provider_rate_buckets', 'nutrition_provider_runtime_state') and relrowsecurity) = 4
      and exists (select 1 from functions where function_name = 'fmz_phase4_log_provider_food_item')
      and exists (select 1 from functions where function_name = 'fmz_phase4_replace_provider_food_log_item')
      and exists (select 1 from functions where function_name = 'fmz_phase4_resolve_provider_food_log_item'),
    '{}'::jsonb
  union all
  select
    'all_guard_tables_present_with_rls',
    not exists (
      select 1
      from expected_guard_tables e
      left join guard_tables g using (table_name)
      where g.table_name is null or not g.relrowsecurity
    )
      and (select count(*) from guard_tables) = (select count(*) from expected_guard_tables),
    jsonb_build_object(
      'expected_count', (select count(*) from expected_guard_tables),
      'actual_count', (select count(*) from guard_tables)
    )
  union all
  select
    'no_catalog_import_in_migration',
    (select count(*) from public.nutrition_food_ingestions) = 0,
    jsonb_build_object('ingestion_count', (select count(*) from public.nutrition_food_ingestions))
  union all
  select
    'forbidden_reference_scan',
    not exists (
      select 1 from functions
      where lower(source) like '%' || 'hgoygcvi' || 'utmynaihcvpd' || '%'
         or lower(source) like '%' || 'service_role' || '_key' || '%'
         or lower(source) like '%' || 'supabase_' || 'service_role' || '%'
         or lower(source) like '%' || 'openai_' || 'api_key' || '%'
    ),
    '{}'::jsonb
),
result as (
  select
    coalesce(bool_and(pass), false) as overall_pass,
    count(*) filter (where pass) as pass_count,
    count(*) filter (where not pass) as fail_count,
    jsonb_agg(
      jsonb_build_object(
        'check', check_name,
        'pass', pass,
        'detail', detail
      )
      order by check_name
    ) as checks
  from checks
)
select jsonb_pretty(
  jsonb_build_object(
    'overall_pass', overall_pass,
    'pass_count', pass_count,
    'fail_count', fail_count,
    'checks', checks
  )
) as verification_result
from result;
