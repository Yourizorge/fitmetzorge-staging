-- FitMetZorge Phase 4 Nutrition Slice 4D post-migration verification.
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- One SELECT/CTE statement. It invokes no application function and changes no data.

with
expected_functions(function_name, argument_types) as (
  values
    (
      'fmz_phase4_log_provider_food_item'::text,
      'uuid, uuid, uuid, date, text, smallint, text, numeric, text, text, timestamp with time zone, jsonb'::text
    ),
    (
      'fmz_phase4_replace_provider_food_log_item',
      'uuid, uuid, uuid, uuid, timestamp with time zone, text, numeric, text, text, jsonb'
    )
),
actual_functions as (
  select
    p.oid,
    p.proname::text as function_name,
    pg_catalog.oidvectortypes(p.proargtypes)::text as argument_types,
    p.prosecdef as security_definer,
    p.provolatile::text as volatility,
    p.prorettype,
    p.proconfig,
    p.proacl,
    p.proowner,
    p.prosrc::text as source,
    pg_catalog.regexp_replace(
      p.prosrc::text,
      '[[:space:]]+',
      '',
      'g'
    ) as source_compact
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname in (
      'fmz_phase4_log_provider_food_item',
      'fmz_phase4_replace_provider_food_log_item'
    )
),
function_mismatches as (
  select e.function_name as expected_name, a.function_name as actual_name,
         e.argument_types as expected_args, a.argument_types as actual_args
  from expected_functions e
  full join actual_functions a using (function_name, argument_types)
  where e.function_name is null or a.function_name is null
),
function_acl as (
  select
    f.function_name,
    case
      when acl.grantee = 0 then 'PUBLIC'
      else coalesce(r.rolname::text, '<missing-role>')
    end as grantee_name,
    acl.privilege_type::text
  from actual_functions f
  cross join lateral pg_catalog.aclexplode(
    coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))
  ) acl
  left join pg_catalog.pg_roles r on r.oid = acl.grantee
),
compatibility_columns as (
  select
    a.attname::text as column_name,
    pg_catalog.format_type(a.atttypid, a.atttypmod)::text as formatted_type,
    a.attnotnull
  from pg_catalog.pg_attribute a
  where a.attrelid = to_regclass('public.food_log_items')
    and a.attnum > 0
    and not a.attisdropped
    and a.attname in (
      'food_id', 'food_portion_id', 'food_name_snapshot', 'brand_snapshot',
      'reference_amount_snapshot', 'reference_unit_snapshot',
      'calculation_basis', 'energy_kcal_snapshot', 'protein_grams_snapshot',
      'carbohydrate_grams_snapshot', 'fat_grams_snapshot',
      'fiber_grams_snapshot', 'source_provider_snapshot',
      'provider_food_id_snapshot', 'source_version_snapshot',
      'provenance_snapshot', 'notes', 'request_id', 'metadata', 'status',
      'archived_at', 'updated_at'
    )
),
support_functions as (
  select
    p.proname::text as function_name,
    pg_catalog.oidvectortypes(p.proargtypes)::text as argument_types,
    p.prosecdef as security_definer,
    p.proconfig,
    p.prosrc::text as source,
    pg_catalog.regexp_replace(
      p.prosrc::text,
      '[[:space:]]+',
      '',
      'g'
    ) as source_compact
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname in (
      'fmz_phase4_enforce_food_log_owner',
      'fmz_phase4_enforce_food_log_item_owner',
      'fmz_phase4_archive_food_log_item',
      'fmz_phase4_has_full_nutrition_access',
      'fmz_phase4_day_payload'
    )
),
member_write_functions as (
  select
    p.proname::text as function_name,
    pg_catalog.oidvectortypes(p.proargtypes)::text as argument_types,
    p.prosrc::text as source,
    pg_catalog.regexp_replace(
      p.prosrc::text,
      '[[:space:]]+',
      '',
      'g'
    ) as source_compact
  from pg_catalog.pg_proc p
  join pg_catalog.pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and (
      (
        p.proname = 'fmz_phase4_log_food_item'
        and pg_catalog.oidvectortypes(p.proargtypes)::text =
          'uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamp with time zone'
      )
      or (
        p.proname = 'fmz_phase4_replace_food_log_item'
        and pg_catalog.oidvectortypes(p.proargtypes)::text =
          'uuid, uuid, uuid, timestamp with time zone, text, uuid, uuid, numeric, text, text'
      )
    )
),
phase4_triggers as (
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
    and not t.tgisinternal
    and t.tgname in (
      'food_logs_20_enforce_owner',
      'food_log_items_10_sync_archive_state',
      'food_log_items_20_enforce_owner',
      'food_log_items_90_touch_updated_at'
    )
),
personal_table_acl as (
  select
    c.relname::text as table_name,
    case
      when acl.grantee = 0 then 'PUBLIC'
      else coalesce(r.rolname::text, '<missing-role>')
    end as grantee_name,
    acl.privilege_type::text
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  cross join lateral pg_catalog.aclexplode(
    coalesce(c.relacl, pg_catalog.acldefault('r', c.relowner))
  ) acl
  left join pg_catalog.pg_roles r on r.oid = acl.grantee
  where n.nspname = 'public'
    and c.relname in ('food_logs', 'food_log_items')
    and c.relkind = 'r'
),
nutrition_policies as (
  select p.tablename::text, p.policyname::text, p.cmd::text
  from pg_catalog.pg_policies p
  where p.schemaname = 'public'
    and p.tablename in ('food_logs', 'food_log_items')
),
guard_tables(table_name) as (
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
    ('food_log_items'),
    ('food_aliases'),
    ('nutrition_provider_query_cache'),
    ('nutrition_provider_food_cache'),
    ('nutrition_provider_rate_buckets'),
    ('nutrition_provider_runtime_state')
),
guard_table_state as (
  select c.relname::text as table_name, c.relrowsecurity
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and c.relname in (select table_name from guard_tables)
),
guard_functions as (
  select
    to_regprocedure('public.fmz_phase4_log_food_item(uuid,uuid,date,text,smallint,text,uuid,uuid,numeric,text,text,timestamp with time zone)') as canonical_log_rpc,
    to_regprocedure('public.fmz_phase4_replace_food_log_item(uuid,uuid,uuid,timestamp with time zone,text,uuid,uuid,numeric,text,text)') as canonical_replace_rpc,
    to_regprocedure('public.fmz_phase4_archive_food_log_item(uuid,timestamp with time zone)') as archive_rpc,
    to_regprocedure('public.fmz_phase4_search_foods(text,integer,text,uuid)') as search_rpc,
    to_regprocedure('public.fmz_phase4_provider_consume_rate_limits(text,text,uuid)') as rate_rpc,
    to_regprocedure('public.fmz_phase4_provider_transition_runtime_state(text,text,integer,text,integer,integer,timestamp with time zone,jsonb)') as circuit_rpc
),
checks(check_name, pass, details) as (
  select
    'provider_functions_exact_signature',
    not exists (select 1 from function_mismatches)
      and (select count(*) from actual_functions) = 2,
    jsonb_build_object(
      'actual', coalesce((select jsonb_agg(jsonb_build_object(
        'name', function_name, 'args', argument_types
      ) order by function_name) from actual_functions), '[]'::jsonb),
      'mismatches', coalesce((select jsonb_agg(to_jsonb(m)) from function_mismatches m), '[]'::jsonb)
    )
  union all
  select
    'provider_functions_security',
    not exists (
      select 1 from actual_functions
      where not security_definer
         or volatility <> 'v'
         or prorettype <> 'jsonb'::regtype
         or not coalesce(
           'search_path=pg_catalog, public, pg_temp' = any(proconfig),
           false
         )
    ),
    coalesce((select jsonb_agg(jsonb_build_object(
      'name', function_name, 'security_definer', security_definer,
      'volatility', volatility, 'config', proconfig
    ) order by function_name) from actual_functions), '[]'::jsonb)
  union all
  select
    'provider_functions_acl_service_role_only',
    not exists (
      select 1 from function_acl
      where grantee_name in ('PUBLIC', 'anon', 'authenticated')
    )
      and not exists (
        select 1
        from actual_functions f
        where coalesce((
          select array_agg(a.privilege_type order by a.privilege_type)::text[]
          from function_acl a
          where a.function_name = f.function_name
            and a.grantee_name = 'service_role'
        ), array[]::text[]) <> array['EXECUTE']::text[]
      ),
    coalesce((select jsonb_agg(to_jsonb(a) order by function_name, grantee_name) from function_acl a), '[]'::jsonb)
  union all
  select
    'food_log_items_nullable_provider_compatibility',
    (select count(*) from compatibility_columns) = 22
      and exists (
        select 1 from compatibility_columns
        where column_name = 'food_id' and formatted_type = 'uuid' and not attnotnull
      )
      and exists (
        select 1 from compatibility_columns
        where column_name = 'food_portion_id' and formatted_type = 'uuid' and not attnotnull
      ),
    coalesce((select jsonb_agg(to_jsonb(c) order by column_name) from compatibility_columns c), '[]'::jsonb)
  union all
  select
    'provider_trigger_compatibility',
    (select count(*) from phase4_triggers) = 4
      and not exists (select 1 from phase4_triggers where tgenabled <> 'O')
      and exists (
        select 1 from phase4_triggers
        where table_name = 'food_logs'
          and trigger_name = 'food_logs_20_enforce_owner'
          and function_name = 'fmz_phase4_enforce_food_log_owner'
      )
      and exists (
        select 1 from phase4_triggers
        where table_name = 'food_log_items'
          and trigger_name = 'food_log_items_10_sync_archive_state'
          and function_name = 'fmz_phase4_sync_archive_state'
      )
      and exists (
        select 1 from phase4_triggers
        where table_name = 'food_log_items'
          and trigger_name = 'food_log_items_20_enforce_owner'
          and function_name = 'fmz_phase4_enforce_food_log_item_owner'
      )
      and exists (
        select 1 from phase4_triggers
        where table_name = 'food_log_items'
          and trigger_name = 'food_log_items_90_touch_updated_at'
          and function_name = 'fmz_phase4_touch_updated_at'
      )
      and exists (
        select 1 from support_functions
        where function_name = 'fmz_phase4_enforce_food_log_owner'
          and security_definer
          and coalesce(
            'search_path=pg_catalog, public, pg_temp' = any(proconfig),
            false
          )
          and position('fmz.phase4_provider_snapshot_user_id' in source_compact) > 0
          and position('coalesce(v_authenticated_user_id,v_internal_user_id)' in source_compact) > 0
      )
      and exists (
        select 1 from support_functions
        where function_name = 'fmz_phase4_enforce_food_log_item_owner'
          and security_definer
          and coalesce(
            'search_path=pg_catalog, public, pg_temp' = any(proconfig),
            false
          )
          and position('new.food_idisnull' in source_compact) > 0
          and position('v_authenticated_user_idisnotnull' in source_compact) > 0
          and position('new.food_portion_idisnotnull' in source_compact) > 0
          and position('trustedUSDAbackendcontext' in source_compact) > 0
          and position('historicalfoodlogitemsnapshotsareimmutable' in source_compact) > 0
      ),
    jsonb_build_object(
      'triggers', coalesce((select jsonb_agg(to_jsonb(t) order by trigger_name) from phase4_triggers t), '[]'::jsonb),
      'support_functions', coalesce((select jsonb_agg(function_name order by function_name) from support_functions), '[]'::jsonb)
    )
  union all
  select
    'canonical_member_write_paths_preserved',
    (select count(*) from member_write_functions) = 2
      and not exists (
        select 1 from member_write_functions
        where position('v_user_iduuid:=auth.uid()' in source_compact) = 0
           or position('p_food_idisnull' in source_compact) = 0
           or position('frompublic.foods' in source_compact) = 0
           or position('f.status=''active''' in source_compact) = 0
           or position('f.catalog_scope=''canonical''' in source_compact) = 0
           or position('f.catalog_scope=''custom''' in source_compact) = 0
           or position('f.owner_user_id=v_user_id' in source_compact) = 0
           or position('frompublic.food_portions' in source_compact) = 0
      )
      and exists (
        select 1 from support_functions
        where function_name = 'fmz_phase4_enforce_food_log_item_owner'
          and position('ifnew.food_idisnullthen' in source_compact) > 0
          and position('v_authenticated_user_idisnotnull' in source_compact) > 0
          and position('f.catalog_scope=''canonical''' in source_compact) > 0
          and position('f.catalog_scope=''custom''' in source_compact) > 0
          and position('f.owner_user_id=v_user_id' in source_compact) > 0
          and position('p.food_id=new.food_id' in source_compact) > 0
      ),
    coalesce((select jsonb_agg(jsonb_build_object(
      'name', function_name, 'args', argument_types
    ) order by function_name) from member_write_functions), '[]'::jsonb)
  union all
  select
    'provider_log_gram_snapshot_contract',
    exists (
      select 1 from actual_functions
      where function_name = 'fmz_phase4_log_provider_food_item'
        and position('p_consumed_unitisdistinctfrom''g''' in source_compact) > 0
        and position('providerfoodloggingsupportsgramsonly' in source_compact) > 0
        and position('p_candidate->>''reference_amount''isdistinctfrom''100''' in source_compact) > 0
        and position('p_candidate->>''reference_unit''isdistinctfrom''g''' in source_compact) > 0
        and position('v_factor:=p_consumed_quantity/100' in source_compact) > 0
        and position('v_log.id,null,null' in source_compact) > 0
        and position('p_consumed_quantity,''g'',v_food_name' in source_compact) > 0
        and position('100,''g'',null,null,null,null,''direct_reference''' in source_compact) > 0
        and position('phase4_provider_snapshot_v1' in source_compact) > 0
        and position('transient_provider_snapshot' in source_compact) > 0
        and position('per_100_g' in source_compact) > 0
        and position('p_candidate->>''provider''isdistinctfrom''usda_fdc''' in source_compact) > 0
        and position('phase4_usda_v1' in source_compact) > 0
        and position('Foundation' in source_compact) > 0
        and position('Survey(FNDDS)' in source_compact) > 0
        and position('SRLegacy' in source_compact) > 0
        and position('p_consumed_unitin(' in source_compact) = 0
    ),
    '{}'::jsonb
  union all
  select
    'provider_numeric_and_snapshot_bounds',
    not exists (
      select 1 from actual_functions
      where position('p_consumed_quantityisnull' in source_compact) = 0
         or position('p_consumed_quantity<=0' in source_compact) = 0
         or position('p_consumed_quantity>100000' in source_compact) = 0
         or position('v_kcal<0orv_kcal>1500' in source_compact) = 0
         or position('v_protein<0orv_protein>100' in source_compact) = 0
         or position('v_carbohydrates<0orv_carbohydrates>100' in source_compact) = 0
         or position('v_fat<0orv_fat>100' in source_compact) = 0
         or position('v_fiber<0orv_fiber>100' in source_compact) = 0
         or position('v_provider_data_typenotin(''Foundation'',''Survey(FNDDS)'',''SRLegacy'')' in source_compact) = 0
         or position('v_provider_food_id!~''^[1-9][0-9]{0,15}$''' in source_compact) = 0
         or position('p_candidate->>''mapping_version''isdistinctfrom''phase4_usda_v1''' in source_compact) = 0
         or position('v_retrieved_atisnull' in source_compact) = 0
         or position('v_retrieved_at>now()+interval''5minutes''' in source_compact) = 0
         or position('v_source_updated_at>now()+interval''5minutes''' in source_compact) = 0
         or position('v_provenance->>''provider''isdistinctfrom''usda_fdc''' in source_compact) = 0
         or position('v_provenance->>''provider_food_id''isdistinctfromv_provider_food_id' in source_compact) = 0
         or position('v_provenance->>''candidate_id''isdistinctfromv_candidate_id::text' in source_compact) = 0
         or position('v_provenance->>''mapping_version''isdistinctfrom''phase4_usda_v1''' in source_compact) = 0
         or position('v_provenance->>''reference_basis''isdistinctfrom''per_100_g''' in source_compact) = 0
         or position('v_provenance->>''retrieved_at''isdistinctfromp_candidate->>''retrieved_at''' in source_compact) = 0
         or position('v_provenance->''derivation''isnull' in source_compact) = 0
         or position('v_provenance->''attribution''isnull' in source_compact) = 0
         or position('food_name_snapshot' in source_compact) = 0
         or position('source_provider_snapshot' in source_compact) = 0
         or position('provider_food_id_snapshot' in source_compact) = 0
         or position('source_version_snapshot' in source_compact) = 0
         or position('provenance_snapshot' in source_compact) = 0
         or position('calculation_version' in source_compact) = 0
    ),
    '{}'::jsonb
  union all
  select
    'provider_log_idempotency_and_atomicity',
    exists (
      select 1 from actual_functions
      where function_name = 'fmz_phase4_log_provider_food_item'
        and position('fmz_phase4_food_log_request:' in source_compact) > 0
        and position('fmz_phase4_food_log:' in source_compact) > 0
        and position('wherei.user_id=v_user_idandi.request_id=p_request_id' in source_compact) > 0
        and position('v_existing_item.idisdistinctfromp_item_id' in source_compact) > 0
        and position('v_existing_item.metadata->''provider_request''isdistinctfromv_request_payload' in source_compact) > 0
        and position('providerrequestUUIDwasalreadyusedwithadifferentpayload' in source_compact) > 0
        and position('wherei.id=p_item_id' in source_compact) > 0
        and position('onconflict(user_id,log_date)donothing' in source_compact) > 0
        and position('''idempotent_replay'',true' in source_compact) > 0
        and position('fmz_phase4_day_payload' in source_compact) > 0
    ),
    '{}'::jsonb
  union all
  select
    'provider_day_payload_compatibility',
    exists (
      select 1 from support_functions
      where function_name = 'fmz_phase4_day_payload'
        and position('frompublic.food_log_items' in source_compact) > 0
        and position('i.status=''active''' in source_compact) > 0
        and position('sum(i.energy_kcal_snapshot)' in source_compact) > 0
        and position('sum(i.protein_grams_snapshot)' in source_compact) > 0
        and position('sum(i.carbohydrate_grams_snapshot)' in source_compact) > 0
        and position('sum(i.fat_grams_snapshot)' in source_compact) > 0
        and position('food_id' in source_compact) = 0
    ),
    '{}'::jsonb
  union all
  select
    'provider_history_and_entitlements',
    not exists (
      select 1 from actual_functions
      where position('fmz_phase4_has_full_nutrition_access' in source_compact) = 0
         or position('v_today-6' in source_compact) = 0
         or position('attimezone' in source_compact) = 0
    )
      and exists (
        select 1 from support_functions
        where function_name = 'fmz_phase4_has_full_nutrition_access'
          and position('e.user_id=p_user_id' in source_compact) > 0
          and position('e.entitlement_codein(''pro'',''ai'',''personal_coaching'')' in source_compact) > 0
          and position('e.status=''active''' in source_compact) > 0
          and position('e.starts_at<=now()' in source_compact) > 0
          and position('(e.ends_atisnullore.ends_at>now())' in source_compact) > 0
      ),
    '{}'::jsonb
  union all
  select
    'provider_replace_atomic_contract',
    exists (
      select 1 from actual_functions
      where function_name = 'fmz_phase4_replace_provider_food_log_item'
        and position('p_expected_original_updated_at' in source_compact) > 0
        and position('fmz_phase4_food_log_request:' in source_compact) > 0
        and position('fmz_phase4_food_log_item_request:' in source_compact) > 0
        and position('wherei.id=p_original_item_idandi.user_id=v_user_idforupdate' in source_compact) > 0
        and position('wherel.id=v_original.food_log_idandl.user_id=v_user_idandl.status=''active''forupdate' in source_compact) > 0
        and position('wherei.user_id=v_user_idandi.request_id=p_replacement_request_id' in source_compact) > 0
        and position('v_replacement.idisdistinctfromp_replacement_item_id' in source_compact) > 0
        and position('v_replacement.food_log_idisdistinctfromv_original.food_log_id' in source_compact) > 0
        and position('v_replacement.metadata->''provider_replacement_request''isdistinctfromv_request_payload' in source_compact) > 0
        and position('providerreplacementrequestUUIDwasalreadyusedwithadifferentpayload' in source_compact) > 0
        and position('v_original.food_idisnotnull' in source_compact) > 0
        and position('v_original.source_provider_snapshotisdistinctfrom''usda_fdc''' in source_compact) > 0
        and position('providerreplacementacceptsprovidersnapshotitemsonly' in source_compact) > 0
        and position('v_original.updated_atisdistinctfromp_expected_original_updated_at' in source_compact) > 0
        and position('p_replacement_item_id,v_user_id,v_original.food_log_id,null,null' in source_compact) > 0
        and position('''operation'',''provider_replace''' in source_compact) > 0
        and position('''replacement_item''' in source_compact) > 0
        and position('''archived_original''' in source_compact) > 0
        and position('updatepublic.food_log_itemssetstatus=''archived''' in source_compact) > 0
        and position('andupdated_at=p_expected_original_updated_at' in source_compact) > 0
        and position('atomicreplacementrolledback' in source_compact) > 0
        and position('''idempotent_replay'',true' in source_compact) > 0
        and position('fmz_phase4_day_payload' in source_compact) > 0
    ),
    '{}'::jsonb
  union all
  select
    'existing_archive_provider_compatible',
    (select count(*) from support_functions
      where function_name = 'fmz_phase4_archive_food_log_item') = 1
      and exists (
      select 1 from support_functions
      where function_name = 'fmz_phase4_archive_food_log_item'
        and argument_types = 'uuid, timestamp with time zone'
        and position('food_id' in source_compact) = 0
        and position('status=''archived''' in source_compact) > 0
        and position('fmz_phase4_day_payload' in source_compact) > 0
    ),
    jsonb_build_object(
      'expected_signature', 'fmz_phase4_archive_food_log_item(uuid,timestamp with time zone)',
      'actual_signatures', coalesce((
        select jsonb_agg(argument_types order by argument_types)
        from support_functions
        where function_name = 'fmz_phase4_archive_food_log_item'
      ), '[]'::jsonb)
    )
  union all
  select
    'no_canonical_provider_promotion',
    not exists (
      select 1 from actual_functions
      where position('insert' || 'intopublic.foods' in lower(source_compact)) > 0
         or position('insert' || 'intopublic.food_portions' in lower(source_compact)) > 0
         or position('insert' || 'intopublic.food_aliases' in lower(source_compact)) > 0
         or position('updatepublic.foods' in lower(source_compact)) > 0
         or position('updatepublic.food_portions' in lower(source_compact)) > 0
         or position('updatepublic.food_aliases' in lower(source_compact)) > 0
         or position('de' || 'letefrompublic.' in lower(source_compact)) > 0
    ),
    '{}'::jsonb
  union all
  select
    'personal_tables_remain_rpc_only',
    not exists (
      select 1 from personal_table_acl
      where grantee_name in ('PUBLIC', 'anon', 'authenticated')
    ),
    coalesce((select jsonb_agg(to_jsonb(a) order by table_name, grantee_name) from personal_table_acl a), '[]'::jsonb)
  union all
  select
    'no_broad_delete_or_trainer_policy',
    not exists (
      select 1 from nutrition_policies
      where cmd = 'DELETE'
         or lower(policyname) like '%trainer%'
         or lower(policyname) like '%coach%'
    ),
    coalesce((select jsonb_agg(to_jsonb(p) order by tablename, policyname) from nutrition_policies p), '[]'::jsonb)
  union all
  select
    'frozen_guard_tables_present_with_rls',
    (select count(*) from guard_table_state) = (select count(*) from guard_tables)
      and not exists (select 1 from guard_table_state where not relrowsecurity),
    jsonb_build_object(
      'expected', (select count(*) from guard_tables),
      'actual', (select count(*) from guard_table_state),
      'non_rls', coalesce((select jsonb_agg(table_name) from guard_table_state where not relrowsecurity), '[]'::jsonb)
    )
  union all
  select
    'frozen_function_guards',
    canonical_log_rpc is not null
      and canonical_replace_rpc is not null
      and archive_rpc is not null
      and search_rpc is not null
      and rate_rpc is not null
      and circuit_rpc is not null,
    to_jsonb(guard_functions)
  from guard_functions
  union all
  select
    'forbidden_reference_scan',
    not exists (
      select 1 from actual_functions
      where position('hgoygcviutmynaihcvpd' in lower(source)) > 0
         or position('service_role_key' in lower(source)) > 0
         or position('secret_key' in lower(source)) > 0
         or position('trainer_id' in lower(source)) > 0
         or position('coach_workspaces' in lower(source)) > 0
    ),
    '{}'::jsonb
)
select jsonb_build_object(
  'scope', 'phase4_nutrition_slice4d_provider_snapshot_logging',
  'staging_project_ref', 'mokxyyullfhkfalopbzd',
  'overall_pass', bool_and(pass),
  'checks', jsonb_agg(
    jsonb_build_object('check', check_name, 'pass', pass, 'details', details)
    order by check_name
  )
) as verification_result
from checks;
