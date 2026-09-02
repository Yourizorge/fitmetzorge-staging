with
expected_tables(table_schema, table_name, columns) as (
  values
    ('ai_private','provider_configurations',array['provider_code:text','environment:text','execution_mode:text','provider_enabled:bool','synthetic_calls_enabled:bool','real_member_processing_enabled:bool','zdr_status:text','dpa_status:text','dpia_status:text','eu_route_status:text','privacy_notice_status:text','consent_copy_status:text','transfer_assessment_status:text','lifecycle_verification_status:text','owner_real_member_activation:bool','synthetic_endpoint:text','real_member_endpoint:text','checked_at:timestamptz','updated_at:timestamptz']::text[]),
    ('ai_private','provider_models',array['provider_code:text','model_route:text','model_id:text','availability_status:text','responses_supported:bool','structured_outputs_supported:bool','input_usd_micros_per_million:int8','cached_input_usd_micros_per_million:int8','output_usd_micros_per_million:int8','max_test_input_tokens:int4','max_test_output_tokens:int4','max_test_attempts:int4','enabled_for_synthetic:bool','enabled_for_real_member:bool','official_checked_on:date']::text[]),
    ('ai_private','provider_payload_fields',array['contract_version:text','field_path:text','purpose:text','classification:text','required:bool']::text[]),
    ('ai_private','provider_test_budget',array['policy_code:text','currency_code:text','max_total_eur_micros:int8','conservative_eur_per_usd_ppm:int8','max_external_calls:int4','reserved_eur_micros:int8','consumed_eur_micros:int8','reserved_calls:int4','completed_calls:int4','updated_at:timestamptz']::text[]),
    ('ai_private','provider_test_runs',array['id:uuid','request_id:uuid','fixture_code:text','request_purpose:text','provider_code:text','model_route:text','model_id:text','payload_hash:text','status:text','reserved_eur_micros:int8','max_attempts:int4','attempt_count:int4','input_tokens:int4','cached_input_tokens:int4','output_tokens:int4','actual_usd_micros:int8','actual_eur_micros:int8','response_hash:text','provider_request_hash:text','safe_error_code:text','created_at:timestamptz','completed_at:timestamptz']::text[])
),
actual_tables as (
  select n.nspname::text as table_schema, c.relname::text as table_name,
    array_agg((a.attname::text || ':' || t.typname::text) order by a.attnum)::text[] as columns
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  join pg_attribute a on a.attrelid = c.oid and a.attnum > 0 and not a.attisdropped
  join pg_type t on t.oid = a.atttypid
  where c.relkind = 'r' and (n.nspname,c.relname) in (select table_schema,table_name from expected_tables)
  group by n.nspname,c.relname
),
table_diff as (
  (select * from expected_tables except select * from actual_tables)
  union all
  (select * from actual_tables except select * from expected_tables)
),
constraints as (
  select c.relname::text as table_name, con.conname::text as name, con.contype::text as type,
    regexp_replace(lower(pg_get_constraintdef(con.oid,true)),'\s+',' ','g') as definition
  from pg_constraint con
  join pg_class c on c.oid=con.conrelid
  join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='ai_private' and c.relname in (select table_name from expected_tables)
),
indexes as (
  select c.relname::text as table_name, i.relname::text as name,
    regexp_replace(lower(pg_get_indexdef(i.oid)),'\s+',' ','g') as definition
  from pg_index x
  join pg_class c on c.oid=x.indrelid
  join pg_class i on i.oid=x.indexrelid
  join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='ai_private' and c.relname in (select table_name from expected_tables)
),
functions as (
  select n.nspname::text as function_schema, p.oid, p.proname::text as name,
    pg_get_function_identity_arguments(p.oid)::text as args,
    p.prosecdef as security_definer, p.provolatile::text as volatility,
    coalesce(p.proconfig,array[]::text[])::text[] as config,
    regexp_replace(lower(p.prosrc),'\s+',' ','g') as source,
    p.proacl,p.proowner
  from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  where (n.nspname='public' and p.proname like 'fmz_phase6b_%')
     or (n.nspname='ai_private' and p.proname in ('phase6b_estimate_test_cost','phase6b_real_member_gate'))
),
function_acl as (
  select f.function_schema,f.name,f.args,
    case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end::text as grantee,
    a.privilege_type::text
  from functions f
  cross join lateral aclexplode(coalesce(f.proacl,acldefault('f',f.proowner))) a
),
table_acl as (
  select table_name::text,grantee::text,privilege_type::text
  from information_schema.table_privileges
  where table_schema='ai_private'
    and table_name in (select table_name from expected_tables)
    and grantee in ('PUBLIC','anon','authenticated')
),
policies as (
  select tablename::text,policyname::text,cmd::text,roles::text[],coalesce(qual,'')::text as qual
  from pg_policies
  where schemaname='ai_private' and tablename in (select table_name from expected_tables)
),
triggers as (
  select c.relname::text as table_name,t.tgname::text as name,p.proname::text as function_name
  from pg_trigger t
  join pg_class c on c.oid=t.tgrelid
  join pg_namespace n on n.oid=c.relnamespace
  join pg_proc p on p.oid=t.tgfoid
  where not t.tgisinternal and n.nspname='ai_private' and c.relname in (select table_name from expected_tables)
),
frozen_tables(table_name) as (
  select unnest(array[
    'profiles','coach_workspaces','user_settings','user_onboarding','entitlements','recovery_logs',
    'training_plans','training_plan_days','training_plan_exercises','workout_sessions','workout_set_logs',
    'nutrition_preferences','foods','food_portions','nutrition_targets','food_logs','food_log_items','food_aliases',
    'nutrition_off_catalog_releases','nutrition_off_products','nutrition_off_product_names',
    'progress_preferences','progress_goals','weight_logs','body_measurements','exercises'
  ]::text[])
),
checks(check_name,pass,detail) as (
  values
    ('target_is_staging_contract','mokxyyullfhkfalopbzd'='mokxyyullfhkfalopbzd','staging project ref locked'),
    ('five_exact_private_tables',not exists(select 1 from table_diff),coalesce((select jsonb_agg(to_jsonb(d))::text from table_diff d),'[]')),
    ('rls_all_five',(select count(*)=5 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='ai_private' and c.relname in (select table_name from expected_tables) and c.relrowsecurity),'RLS enabled'),
    ('no_provider_table_policies',not exists(select 1 from policies),coalesce((select jsonb_agg(to_jsonb(p))::text from policies p),'[]')),
    ('no_browser_table_acl',not exists(select 1 from table_acl),coalesce((select jsonb_agg(to_jsonb(a))::text from table_acl a),'[]')),
    ('provider_configuration_exact',exists(select 1 from ai_private.provider_configurations where provider_code='openai' and environment='staging' and execution_mode='synthetic_only' and provider_enabled and synthetic_calls_enabled and not real_member_processing_enabled and zdr_status='unverified' and dpa_status='incomplete' and dpia_status='incomplete' and eu_route_status='unverified' and privacy_notice_status='draft' and consent_copy_status='draft' and transfer_assessment_status='incomplete' and lifecycle_verification_status='incomplete' and not owner_real_member_activation and synthetic_endpoint='https://api.openai.com/v1/responses' and real_member_endpoint is null),'synthetic only; legal/privacy gates incomplete'),
    ('real_member_constraint_fail_closed',exists(select 1 from constraints where name='ai_provider_config_real_member_gate_check' and definition like '%zdr_status = ''verified''%' and definition like '%dpa_status = ''complete''%' and definition like '%dpia_status = ''complete''%' and definition like '%eu_route_status = ''verified''%' and definition like '%owner_real_member_activation%' and definition like '%https://eu.api.openai.com/v1/responses%'),'all real-member prerequisites required'),
    ('model_inventory_exact',(select count(*)=2 and bool_and(enabled_for_synthetic) and bool_and(not enabled_for_real_member) from ai_private.provider_models where provider_code='openai'),'two exact provider routes'),
    ('luna_contract',exists(select 1 from ai_private.provider_models where provider_code='openai' and model_route='luna' and model_id='gpt-5.6-luna' and responses_supported and structured_outputs_supported and input_usd_micros_per_million=200000 and cached_input_usd_micros_per_million=20000 and output_usd_micros_per_million=1200000 and max_test_input_tokens=4096 and max_test_output_tokens=512 and max_test_attempts=2),'official locked Luna route'),
    ('terra_contract',exists(select 1 from ai_private.provider_models where provider_code='openai' and model_route='terra' and model_id='gpt-5.6-terra' and responses_supported and structured_outputs_supported and input_usd_micros_per_million=2000000 and cached_input_usd_micros_per_million=200000 and output_usd_micros_per_million=12000000 and max_test_input_tokens=4096 and max_test_output_tokens=512 and max_test_attempts=2),'official locked Terra route'),
    ('payload_allowlist_exact',(select array_agg(field_path order by field_path)::text[]=array['feature_code','locale','request_purpose','schema_version','snapshot.goal_code','snapshot.nutrition.average_energy_kcal_7d','snapshot.recovery.average_sleep_hours_7d','snapshot.training.completed_sessions_7d','synthetic_subject_token']::text[] and bool_and(required) from ai_private.provider_payload_fields where contract_version='phase6b.synthetic-payload.v1'),'nine synthetic fields only'),
    ('payload_contains_no_direct_identity',not exists(select 1 from ai_private.provider_payload_fields where field_path ~* '(email|name|address|phone|user_id|trainer|chat|injury|medication)'),'no member identity or private text'),
    ('budget_contract_exact',exists(select 1 from ai_private.provider_test_budget where policy_code='phase6b-staging-v1' and currency_code='EUR' and max_total_eur_micros=5000000 and conservative_eur_per_usd_ppm=1250000 and max_external_calls=6),'EUR 5 and six attempts absolute cap'),
    ('budget_state_consistent',exists(select 1 from ai_private.provider_test_budget where policy_code='phase6b-staging-v1' and reserved_eur_micros>=0 and consumed_eur_micros>=0 and reserved_eur_micros+consumed_eur_micros<=max_total_eur_micros and reserved_calls>=0 and completed_calls>=0 and reserved_calls+completed_calls<=max_external_calls),'live ledger within caps'),
    ('test_run_idempotency',exists(select 1 from constraints where table_name='provider_test_runs' and type='u' and definition like '%request_id%') and exists(select 1 from functions where name='fmz_phase6b_service_begin_synthetic_test' and source like '%ai_provider_test_request_conflict%'),'request replay equality enforced'),
    ('test_run_minimized',not exists(select 1 from information_schema.columns where table_schema='ai_private' and table_name='provider_test_runs' and column_name in ('prompt','content','content_text','message','message_text','email','jwt','token','secret','user_id')),'only hashes, usage and safe codes'),
    ('test_run_integrity',exists(select 1 from constraints where name='ai_provider_test_runs_model_fixture_check') and exists(select 1 from constraints where name='ai_provider_test_runs_completion_check') and exists(select 1 from constraints where name='ai_provider_test_runs_safe_error_check'),'model, lifecycle and safe-code checks'),
    ('test_run_indexes',exists(select 1 from indexes where name='ai_provider_test_runs_status_created_idx') and exists(select 1 from indexes where name='ai_provider_test_runs_model_created_idx'),'bounded operational lookups'),
    ('function_inventory',(select count(*)=6 from functions),coalesce((select jsonb_agg(function_schema||'.'||name order by function_schema,name)::text from functions),'[]')),
    ('service_functions_security_definer',(select count(*)=4 and bool_and(security_definer) from functions where function_schema='public'),'four service bridges only'),
    ('private_helpers_invoker',(select count(*)=2 and bool_and(not security_definer) from functions where function_schema='ai_private'),'pure helpers are invoker'),
    ('safe_function_search_paths',not exists(select 1 from functions where not ('search_path=pg_catalog, ai_private, pg_temp'=any(config) or 'search_path=pg_catalog, extensions, public, ai_private, pg_temp'=any(config))),'fixed trusted namespaces'),
    ('service_rpc_acl',(select count(*)=4 from function_acl where function_schema='public' and grantee='service_role' and privilege_type='EXECUTE') and not exists(select 1 from function_acl where function_schema='public' and grantee in ('PUBLIC','anon','authenticated') and privilege_type='EXECUTE'),'service role only'),
    ('private_helper_acl',not exists(select 1 from function_acl where function_schema='ai_private' and grantee in ('PUBLIC','anon','authenticated') and privilege_type='EXECUTE'),'no app execution'),
    ('real_member_gate_always_false',exists(select 1 from functions where name='phase6b_real_member_gate' and source like '%''allowed'', false%' and source like '%real_member_provider_processing_blocked_phase6b%'),'6B cannot process member data'),
    ('synthetic_begin_gate',exists(select 1 from functions where name='fmz_phase6b_service_begin_synthetic_test' and source like '%execution_mode <> ''synthetic_only''%' and source like '%real_member_processing_enabled%' and source like '%ai_provider_synthetic_disabled%'),'synthetic mode only'),
    ('atomic_budget_reservation',exists(select 1 from functions where name='fmz_phase6b_service_begin_synthetic_test' and source like '%pg_advisory_xact_lock%' and source like '%fmz_phase6b_test_budget:phase6b-staging-v1%' and source like '%reserved_eur_micros + v_reserve.eur_micros > v_budget.max_total_eur_micros%' and source like '%completed_calls + v_budget.reserved_calls + v_model.max_test_attempts > v_budget.max_external_calls%'),'currency and call caps locked before call'),
    ('conservative_unknown_cost',exists(select 1 from functions where name='fmz_phase6b_service_fail_synthetic_test' and source like '%p_cost_unknown and p_attempt_count > 0 then v_run.reserved_eur_micros%' and source like '%v_run.actual_eur_micros <> v_charge%'),'unknown paid attempt consumes full reservation and replay proves equality'),
    ('cost_reconciliation',exists(select 1 from functions where name='fmz_phase6b_service_complete_synthetic_test' and source like '%v_cost.eur_micros > v_run.reserved_eur_micros%' and source like '%consumed_eur_micros = consumed_eur_micros + v_cost.eur_micros%'),'actual usage reconciled'),
    ('cost_formula_uses_cached_rate',exists(select 1 from functions where name='phase6b_estimate_test_cost' and source like '%cached_input_usd_micros_per_million%' and source like '%conservative_eur_per_usd_ppm%'),'cached tokens and EUR conversion included'),
    ('updated_at_triggers',(select count(*)=2 from triggers where function_name='touch_updated_at'),coalesce((select jsonb_agg(to_jsonb(t))::text from triggers t),'[]')),
    ('phase6a_flags_remain_off',(select count(*)=3 and bool_and(not enabled) from ai_private.feature_flags where flag_code in ('ai_coach_enabled','provider_calls_enabled','staging_mock_enabled')),'6A member/mock/provider flags remain off'),
    ('frozen_guard_tables',(select count(*)=26 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind='r' and c.relname in (select table_name from frozen_tables)),'Phase 1-5 authorities present'),
    ('frozen_guard_rls',not exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind='r' and c.relname in (select table_name from frozen_tables) and not c.relrowsecurity),'frozen source RLS retained'),
    ('no_network_or_domain_sql',not exists(select 1 from functions where source ~ '(http_post|net.http|insert into public.training_|insert into public.nutrition_|insert into public.progress_|update public.training_|update public.nutrition_|update public.progress_)'),'database cannot call provider or mutate domains'),
    ('no_production_or_secret_source',not exists(select 1 from functions where source ~ '(hgoygcviutmynaihcvpd|sk-[a-z0-9]|sb_secret_|deno.env|api[_-]?key|provider[_-]?key)'),'no production ref or credential material')
),
result as (
  select jsonb_build_object(
    'overall_pass',bool_and(pass),
    'pass_count',count(*) filter (where pass),
    'fail_count',count(*) filter (where not pass),
    'provider_test_run_count',(select count(*) from ai_private.provider_test_runs),
    'checks',jsonb_agg(jsonb_build_object('check',check_name,'pass',pass,'detail',detail) order by check_name)
  ) as verification_result
  from checks
)
select verification_result from result;
