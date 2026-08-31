with
expected_tables(table_name) as (
  values
    ('progress_preferences'::text),
    ('progress_goals'::text),
    ('weight_logs'::text),
    ('body_measurements'::text)
),
expected_columns(table_name, column_name, udt_name, is_nullable) as (
  values
    ('progress_preferences','user_id','uuid','NO'),
    ('progress_preferences','timezone_name','text','NO'),
    ('progress_preferences','created_at','timestamptz','NO'),
    ('progress_preferences','updated_at','timestamptz','NO'),
    ('progress_goals','id','uuid','NO'),
    ('progress_goals','user_id','uuid','NO'),
    ('progress_goals','goal_code','text','NO'),
    ('progress_goals','baseline_weight_kg','numeric','YES'),
    ('progress_goals','target_weight_kg','numeric','YES'),
    ('progress_goals','target_date','date','YES'),
    ('progress_goals','notes','text','YES'),
    ('progress_goals','status','text','NO'),
    ('progress_goals','request_id','uuid','NO'),
    ('progress_goals','created_at','timestamptz','NO'),
    ('progress_goals','updated_at','timestamptz','NO'),
    ('progress_goals','archived_at','timestamptz','YES'),
    ('weight_logs','id','uuid','NO'),
    ('weight_logs','user_id','uuid','NO'),
    ('weight_logs','log_date','date','NO'),
    ('weight_logs','measured_at','timestamptz','NO'),
    ('weight_logs','timezone_name','text','NO'),
    ('weight_logs','timezone_offset_minutes','int2','NO'),
    ('weight_logs','weight_kg','numeric','NO'),
    ('weight_logs','notes','text','YES'),
    ('weight_logs','source','text','NO'),
    ('weight_logs','status','text','NO'),
    ('weight_logs','request_id','uuid','NO'),
    ('weight_logs','supersedes_weight_log_id','uuid','YES'),
    ('weight_logs','created_at','timestamptz','NO'),
    ('weight_logs','updated_at','timestamptz','NO'),
    ('weight_logs','archived_at','timestamptz','YES'),
    ('body_measurements','id','uuid','NO'),
    ('body_measurements','user_id','uuid','NO'),
    ('body_measurements','log_date','date','NO'),
    ('body_measurements','measured_at','timestamptz','NO'),
    ('body_measurements','timezone_name','text','NO'),
    ('body_measurements','timezone_offset_minutes','int2','NO'),
    ('body_measurements','waist_cm','numeric','YES'),
    ('body_measurements','chest_cm','numeric','YES'),
    ('body_measurements','hips_cm','numeric','YES'),
    ('body_measurements','upper_arm_left_cm','numeric','YES'),
    ('body_measurements','upper_arm_right_cm','numeric','YES'),
    ('body_measurements','thigh_left_cm','numeric','YES'),
    ('body_measurements','thigh_right_cm','numeric','YES'),
    ('body_measurements','notes','text','YES'),
    ('body_measurements','source','text','NO'),
    ('body_measurements','status','text','NO'),
    ('body_measurements','request_id','uuid','NO'),
    ('body_measurements','supersedes_body_measurement_id','uuid','YES'),
    ('body_measurements','created_at','timestamptz','NO'),
    ('body_measurements','updated_at','timestamptz','NO'),
    ('body_measurements','archived_at','timestamptz','YES')
),
actual_columns as (
  select c.table_name::text, c.column_name::text, c.udt_name::text, c.is_nullable::text
  from information_schema.columns c
  join expected_tables e on e.table_name = c.table_name
  where c.table_schema = 'public'
),
column_diff as (
  (select * from expected_columns except select * from actual_columns)
  union all
  (select * from actual_columns except select * from expected_columns)
),
constraints as (
  select con.conname::text as name,
    rel.relname::text as table_name,
    con.contype,
    lower(pg_get_constraintdef(con.oid, true)) as definition
  from pg_constraint con
  join pg_class rel on rel.oid = con.conrelid
  join pg_namespace n on n.oid = rel.relnamespace
  where n.nspname = 'public'
    and rel.relname in (select table_name from expected_tables)
),
indexes as (
  select i.tablename::text as table_name, i.indexname::text as name,
    lower(i.indexdef) as definition
  from pg_indexes i
  where i.schemaname = 'public'
    and i.tablename in (select table_name from expected_tables)
),
policies as (
  select tablename::text as table_name, policyname::text as name,
    cmd::text, roles::text[] as roles, coalesce(qual, '')::text as qual,
    coalesce(with_check, '')::text as with_check
  from pg_policies
  where schemaname = 'public'
    and tablename in (select table_name from expected_tables)
),
functions as (
  select p.oid, p.proname::text as name,
    pg_get_function_identity_arguments(p.oid)::text as args,
    p.prosecdef as security_definer,
    p.provolatile::text as volatility,
    coalesce(p.proconfig, array[]::text[])::text[] as config,
    regexp_replace(lower(p.prosrc), '\s+', ' ', 'g') as source,
    p.proacl, p.proowner
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname like 'fmz_phase5_%'
),
function_acl as (
  select f.name, f.args,
    case when a.grantee = 0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end as grantee,
    a.privilege_type::text as privilege_type
  from functions f
  cross join lateral aclexplode(coalesce(f.proacl, acldefault('f', f.proowner))) a
),
table_privileges as (
  select table_name::text, grantee::text, privilege_type::text
  from information_schema.table_privileges
  where table_schema = 'public'
    and table_name in (select table_name from expected_tables)
    and grantee in ('PUBLIC', 'anon', 'authenticated')
),
checks(check_name, pass, detail) as (
  values
    ('project_guard',
      current_database() = 'postgres',
      current_database()),
    ('four_progress_tables',
      (select count(*) = 4 from pg_class c join pg_namespace n on n.oid=c.relnamespace
       where n.nspname='public' and c.relkind='r'
         and c.relname in (select table_name from expected_tables)),
      'progress_preferences, progress_goals, weight_logs, body_measurements'),
    ('column_contract',
      not exists (select 1 from column_diff),
      coalesce((select jsonb_agg(to_jsonb(d))::text from column_diff d), '[]')),
    ('primary_keys',
      (select count(*) = 4 from constraints where contype='p'),
      'four primary keys'),
    ('profile_foreign_keys',
      (select count(*) >= 4 from constraints
       where contype='f' and definition like '%references profiles(id)%on delete cascade%'),
      'all user ownership references profiles(id) on delete cascade'),
    ('revision_foreign_keys',
      exists (select 1 from constraints where name='weight_logs_supersedes_weight_log_id_fkey' and definition like '%on delete restrict%')
      and exists (select 1 from constraints where name='body_measurements_supersedes_body_measurement_id_fkey' and definition like '%on delete restrict%'),
      'self-revision history uses on delete restrict'),
    ('validation_constraints',
      exists (select 1 from constraints where name='weight_logs_weight_check')
      and exists (select 1 from constraints where name='body_measurements_values_check')
      and exists (select 1 from constraints where name='body_measurements_at_least_one_check')
      and exists (select 1 from constraints where name='progress_goals_goal_code_check'),
      'weight, measurement and goal bounds'),
    ('active_unique_indexes',
      exists (select 1 from indexes where name='progress_goals_one_active_per_user_idx' and definition like '%where (status = ''active''::text)%')
      and exists (select 1 from indexes where name='weight_logs_one_active_day_idx' and definition like '%where (status = ''active''::text)%')
      and exists (select 1 from indexes where name='body_measurements_one_active_day_idx' and definition like '%where (status = ''active''::text)%'),
      'partial active-row uniqueness'),
    ('history_indexes',
      exists (select 1 from indexes where name='progress_goals_user_history_idx')
      and exists (select 1 from indexes where name='weight_logs_user_history_idx')
      and exists (select 1 from indexes where name='body_measurements_user_history_idx'),
      'user/date history indexes'),
    ('revision_fk_indexes',
      exists (select 1 from indexes where name='weight_logs_supersedes_idx' and definition like '%(supersedes_weight_log_id)%' and definition like '%where (supersedes_weight_log_id is not null)%')
      and exists (select 1 from indexes where name='body_measurements_supersedes_idx' and definition like '%(supersedes_body_measurement_id)%' and definition like '%where (supersedes_body_measurement_id is not null)%'),
      'immutable revision foreign keys have covering partial indexes'),
    ('rls_enabled',
      (select count(*) = 4 from pg_class c join pg_namespace n on n.oid=c.relnamespace
       where n.nspname='public' and c.relname in (select table_name from expected_tables)
         and c.relrowsecurity),
      'RLS enabled on all four tables'),
    ('own_user_policies',
      (select count(*) = 12 from policies where name like '%_own')
      and not exists (select 1 from policies where qual !~ 'auth.uid' and with_check !~ 'auth.uid'),
      'select/insert/update own only'),
    ('no_delete_or_trainer_policy',
      not exists (select 1 from policies where cmd='DELETE' or lower(name) like '%trainer%' or lower(qual) like '%trainer%'),
      'no DELETE or trainer-like policy'),
    ('no_browser_table_privileges',
      not exists (select 1 from table_privileges),
      coalesce((select jsonb_agg(to_jsonb(p))::text from table_privileges p), '[]')),
    ('function_inventory',
      (select count(*) = 11 from functions),
      coalesce((select jsonb_agg(name order by name)::text from functions), '[]')),
    ('definer_security_and_search_path',
      (select count(*) = 9 from functions where security_definer)
      and not exists (
        select 1 from functions where security_definer
          and not ('search_path=pg_catalog, public, pg_temp' = any(config))
      ),
      'nine definer API/internal functions with fixed search_path'),
    ('trigger_functions_invoker_only',
      (select count(*) = 2 from functions
       where name in ('fmz_phase5_touch_updated_at','fmz_phase5_sync_archive_state')
         and not security_definer),
      'trigger helpers are SECURITY INVOKER'),
    ('authenticated_rpc_acl',
      (select count(*) = 8 from function_acl
       where grantee='authenticated' and privilege_type='EXECUTE')
      and not exists (
        select 1 from function_acl
        where grantee in ('PUBLIC','anon') and privilege_type='EXECUTE'
      )
      and not exists (
        select 1 from function_acl
        where name in ('fmz_phase5_touch_updated_at','fmz_phase5_sync_archive_state','fmz_phase5_has_full_progress_access')
          and grantee='authenticated' and privilege_type='EXECUTE'
      ),
      'eight member RPCs; internal helpers blocked'),
    ('auth_uid_ownership',
      not exists (
        select 1 from functions
        where name in (
          'fmz_phase5_set_progress_timezone','fmz_phase5_save_progress_goal',
          'fmz_phase5_save_weight_log','fmz_phase5_save_body_measurement',
          'fmz_phase5_archive_weight_log','fmz_phase5_archive_body_measurement',
          'fmz_phase5_get_progress_dashboard','fmz_phase5_set_unit_system'
        ) and source not like '%auth.uid()%'
      ),
      'all member RPCs derive user from auth.uid()'),
    ('idempotency_and_stale_guards',
      (select count(*) = 3 from functions
       where name in ('fmz_phase5_save_progress_goal','fmz_phase5_save_weight_log','fmz_phase5_save_body_measurement')
         and source like '%progress_request_conflict%'
         and source like '%progress_stale_conflict%'
         and source like '%pg_advisory_xact_lock%'),
      'request equality, optimistic stale check and advisory locks'),
    ('revision_and_archive_contract',
      (select count(*) = 3 from functions
       where name in ('fmz_phase5_save_progress_goal','fmz_phase5_save_weight_log','fmz_phase5_save_body_measurement')
         and source like '%superseded%')
      and (select count(*) = 2 from functions
       where name in ('fmz_phase5_archive_weight_log','fmz_phase5_archive_body_measurement')
         and source like '%archived%'),
      'no destructive correction path'),
    ('entitlement_contract',
      exists (select 1 from functions where name='fmz_phase5_has_full_progress_access'
        and source like '%status = ''active''%'
        and source like '%''pro'', ''ai'', ''personal_coaching''%'
        and source like '%starts_at <= now()%'
        and source like '%ends_at is null or e.ends_at > now()%')
      and exists (select 1 from functions where name='fmz_phase5_get_progress_dashboard'
        and source like '%v_today - 29%'
        and source like '%history_window_days%'),
      'current Pro/AI/PT full; Free 30-day server window'),
    ('timezone_and_canonical_units',
      exists (select 1 from functions where name='fmz_phase5_save_weight_log'
        and source like '%pg_timezone_names%'
        and source like '%timezone offset does not match progress date%')
      and exists (select 1 from functions where name='fmz_phase5_save_body_measurement'
        and source like '%pg_timezone_names%'
        and source like '%timezone offset does not match progress date%'),
      'IANA date validation; kg/cm storage'),
    ('dashboard_frozen_sources',
      exists (select 1 from functions where name='fmz_phase5_get_progress_dashboard'
        and source like '%workout_set_logs%'
        and source like '%workout_sessions%'
        and source like '%recovery_logs%'
        and source like '%food_log_items%'
        and source like '%authoritative_source_available%false%'),
      'strength, consistency, descriptive context and truthful running state'),
    ('unit_system_reused',
      exists (select 1 from functions where name='fmz_phase5_get_progress_dashboard'
        and source like '%user_settings%unit_system%')
      and exists (select 1 from functions where name='fmz_phase5_set_unit_system'
        and source like '%metric%imperial%user_settings%'),
      'existing metric/imperial preference reused and own-user persisted'),
    ('photo_gate_closed',
      to_regclass('public.progress_photos') is null
      and not exists (select 1 from storage.buckets where id like '%progress%'),
      'no incomplete photo table or bucket'),
    ('frozen_guard_tables',
      (select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace
       where n.nspname='public' and c.relkind='r' and c.relname in (
         'profiles','coach_workspaces','user_settings','user_onboarding','entitlements',
         'recovery_logs','training_plans','workout_sessions','workout_set_logs',
         'food_logs','food_log_items','nutrition_targets'
       )) = 12,
      'Phase 1-4 guard tables present'),
    ('frozen_rls_guard',
      (select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace
       where n.nspname='public' and c.relname in (
         'profiles','coach_workspaces','user_settings','user_onboarding','entitlements',
         'recovery_logs','training_plans','workout_sessions','workout_set_logs',
         'food_logs','food_log_items','nutrition_targets'
       ) and c.relrowsecurity) = 12,
      'Phase 1-4 RLS remains enabled'),
    ('phase4_catalog_preserved',
      (select count(*) = 24458 from public.nutrition_off_products)
      and (select count(*) = 74184 from public.nutrition_off_product_names)
      and (select count(*) = 64 from public.foods where catalog_scope='canonical' and source_provider='usda_fdc'),
      '24,458 OFF / 74,184 names / 64 canonical USDA'),
    ('no_production_or_secret_refs',
      not exists (
        select 1 from functions
        where source ~ '(hgoygcviutmynaihcvpd|service[_-]?role|api[_-]?key|secret)'
      ),
      'Phase 5 function source is staging-neutral and secret-free')
),
result as (
  select jsonb_build_object(
    'scope', 'phase5_progress_foundation',
    'overall_pass', bool_and(pass),
    'pass_count', count(*) filter (where pass),
    'fail_count', count(*) filter (where not pass),
    'checks', jsonb_agg(
      jsonb_build_object('check', check_name, 'pass', pass, 'detail', detail)
      order by check_name
    )
  ) as verification_result
  from checks
)
select verification_result from result;
