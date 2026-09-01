with
expected_tables(table_schema, table_name, columns) as (
  values
    ('public','ai_consent_events',array['id:uuid','user_id:uuid','consent_kind:text','consent_state:text','document_version:text','purpose_code:text','categories:_text','locale:text','explicit_confirmation:bool','request_id:uuid','created_at:timestamptz','event_sequence:int8']::text[]),
    ('public','ai_threads',array['id:uuid','user_id:uuid','feature_code:text','locale:text','status:text','retention_state:text','retention_started_at:timestamptz','retention_due_at:timestamptz','content_deleted_at:timestamptz','created_at:timestamptz','updated_at:timestamptz','archived_at:timestamptz']::text[]),
    ('public','ai_messages',array['id:uuid','user_id:uuid','thread_id:uuid','message_role:text','feature_code:text','content_text:text','structured_output:jsonb','schema_version:text','status:text','request_id:uuid','run_id:uuid','created_at:timestamptz']::text[]),
    ('public','ai_context_manifests',array['id:uuid','user_id:uuid','feature_code:text','manifest_version:text','context_hash:text','sources:jsonb','unavailable_sources:_text','source_cutoff_at:timestamptz','created_at:timestamptz']::text[]),
    ('public','ai_action_proposals',array['id:uuid','user_id:uuid','context_manifest_id:uuid','action_code:text','proposed_change:jsonb','expected_source_versions:jsonb','explanation:text','safety_class:text','status:text','expires_at:timestamptz','created_at:timestamptz','updated_at:timestamptz']::text[]),
    ('public','ai_action_decisions',array['id:uuid','user_id:uuid','proposal_id:uuid','decision_type:text','decision_source:text','reason_code:text','request_id:uuid','created_at:timestamptz']::text[]),
    ('public','ai_member_safety_state',array['user_id:uuid','safety_status:text','risk_category:text','blocked_at:timestamptz','resolved_at:timestamptz','resolution_code:text','revision:int8','updated_at:timestamptz']::text[]),
    ('public','ai_data_lifecycle_requests',array['id:uuid','user_id:uuid','request_type:text','status:text','request_id:uuid','requested_at:timestamptz','completed_at:timestamptz','safe_result_code:text']::text[]),
    ('ai_private','consent_documents',array['consent_kind:text','document_version:text','locale:text','purpose_code:text','categories:_text','content_text:text','content_sha256:text','status:text','effective_at:timestamptz','created_at:timestamptz']::text[]),
    ('ai_private','feature_flags',array['flag_code:text','enabled:bool','environment:text','reason_code:text','updated_at:timestamptz']::text[]),
    ('ai_private','budget_policies',array['policy_version:text','currency_code:text','included_micros:int8','warning_micros:int8','grace_micros:int8','hard_cap_micros:int8','terra_stop_micros:int8','active:bool','created_at:timestamptz']::text[]),
    ('ai_private','rate_policies',array['feature_code:text','window_seconds:int4','max_requests:int4','active:bool']::text[]),
    ('ai_private','action_policies',array['action_code:text','enabled:bool','max_increase_percent:numeric','max_decrease_percent:numeric','max_absolute_delta:numeric','requires_explanation:bool','requires_reversible:bool','policy_metadata:jsonb']::text[]),
    ('ai_private','structured_schemas',array['schema_code:text','schema_version:text','schema_body:jsonb','active:bool','created_at:timestamptz']::text[]),
    ('ai_private','runs',array['id:uuid','user_id:uuid','request_id:uuid','thread_id:uuid','context_manifest_id:uuid','feature_code:text','adapter_code:text','model_tier:text','policy_version:text','schema_version:text','payload_hash:text','status:text','reserved_cost_micros:int8','actual_cost_micros:int8','input_tokens:int4','output_tokens:int4','response_hash:text','safe_error_code:text','started_at:timestamptz','completed_at:timestamptz']::text[]),
    ('ai_private','budget_accounts',array['user_id:uuid','period_start:timestamptz','period_end:timestamptz','policy_version:text','consumed_micros:int8','reserved_micros:int8','warning_issued_at:timestamptz','hard_stopped_at:timestamptz','updated_at:timestamptz']::text[]),
    ('ai_private','usage_ledger',array['id:uuid','user_id:uuid','run_id:uuid','request_id:uuid','feature_code:text','model_tier:text','ledger_type:text','amount_micros:int8','created_at:timestamptz']::text[]),
    ('ai_private','rate_buckets',array['user_id:uuid','feature_code:text','window_started_at:timestamptz','window_seconds:int4','request_count:int4','updated_at:timestamptz']::text[]),
    ('ai_private','safety_events',array['id:uuid','user_id:uuid','run_id:uuid','risk_category:text','safety_outcome:text','policy_version:text','created_at:timestamptz']::text[]),
    ('ai_private','audit_events',array['id:uuid','user_id:uuid','run_id:uuid','event_code:text','safe_metadata:jsonb','created_at:timestamptz']::text[])
),
actual_tables as (
  select n.nspname::text as table_schema, c.relname::text as table_name,
    array_agg((a.attname::text || ':' || t.typname::text) order by a.attnum)::text[] as columns
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  join pg_attribute a on a.attrelid = c.oid and a.attnum > 0 and not a.attisdropped
  join pg_type t on t.oid = a.atttypid
  where c.relkind = 'r'
    and (n.nspname, c.relname) in (select table_schema, table_name from expected_tables)
  group by n.nspname, c.relname
),
table_diff as (
  (select * from expected_tables except select * from actual_tables)
  union all
  (select * from actual_tables except select * from expected_tables)
),
constraints as (
  select n.nspname::text as table_schema, c.relname::text as table_name,
    con.conname::text as name, con.contype::text as type,
    regexp_replace(lower(pg_get_constraintdef(con.oid, true)), '\s+', ' ', 'g') as definition
  from pg_constraint con
  join pg_class c on c.oid = con.conrelid
  join pg_namespace n on n.oid = c.relnamespace
  where (n.nspname, c.relname) in (select table_schema, table_name from expected_tables)
),
indexes as (
  select n.nspname::text as table_schema, c.relname::text as table_name,
    i.relname::text as name,
    regexp_replace(lower(pg_get_indexdef(i.oid)), '\s+', ' ', 'g') as definition
  from pg_index x
  join pg_class c on c.oid = x.indrelid
  join pg_class i on i.oid = x.indexrelid
  join pg_namespace n on n.oid = c.relnamespace
  where (n.nspname, c.relname) in (select table_schema, table_name from expected_tables)
),
policies as (
  select schemaname::text as table_schema, tablename::text as table_name,
    policyname::text as name, cmd::text,
    roles::text[] as roles, coalesce(qual, '')::text as qual,
    coalesce(with_check, '')::text as with_check
  from pg_policies
  where schemaname = 'public' and tablename like 'ai_%'
),
functions as (
  select n.nspname::text as function_schema, p.oid, p.proname::text as name,
    pg_get_function_identity_arguments(p.oid)::text as args,
    p.prosecdef as security_definer, p.provolatile::text as volatility,
    coalesce(p.proconfig, array[]::text[])::text[] as config,
    regexp_replace(lower(p.prosrc), '\s+', ' ', 'g') as source,
    p.proacl, p.proowner
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where (n.nspname = 'public' and p.proname like 'fmz_phase6a_%')
     or n.nspname = 'ai_private'
),
function_acl as (
  select f.function_schema, f.name, f.args,
    case when a.grantee = 0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end::text as grantee,
    a.privilege_type::text
  from functions f
  cross join lateral aclexplode(coalesce(f.proacl, acldefault('f', f.proowner))) a
),
table_acl as (
  select table_schema::text, table_name::text, grantee::text, privilege_type::text
  from information_schema.table_privileges
  where (table_schema, table_name) in (select table_schema, table_name from expected_tables)
    and grantee in ('PUBLIC','anon','authenticated')
),
schema_acl as (
  select case when a.grantee = 0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end::text as grantee,
    a.privilege_type::text
  from pg_namespace n
  cross join lateral aclexplode(coalesce(n.nspacl, acldefault('n', n.nspowner))) a
  where n.nspname = 'ai_private'
),
triggers as (
  select n.nspname::text as table_schema, c.relname::text as table_name,
    t.tgname::text as name, p.proname::text as function_name
  from pg_trigger t
  join pg_class c on c.oid = t.tgrelid
  join pg_namespace n on n.oid = c.relnamespace
  join pg_proc p on p.oid = t.tgfoid
  where not t.tgisinternal
    and (n.nspname, c.relname) in (select table_schema, table_name from expected_tables)
),
flags as (
  select flag_code, enabled, environment from ai_private.feature_flags
),
checks(check_name, pass, detail) as (
  values
    ('target_is_staging_contract', 'mokxyyullfhkfalopbzd' = 'mokxyyullfhkfalopbzd', 'staging ref locked in artifact'),
    ('twenty_exact_tables', not exists(select 1 from table_diff), coalesce((select jsonb_agg(to_jsonb(d))::text from table_diff d), '[]')),
    ('public_table_count', (select count(*) = 8 from actual_tables where table_schema='public'), '8 public own-user foundations'),
    ('private_table_count', (select count(*) = 12 from actual_tables where table_schema='ai_private'), '12 private contract/operational tables'),
    ('rls_all_twenty', (select count(*) = 20 from pg_class c join pg_namespace n on n.oid=c.relnamespace where (n.nspname,c.relname) in (select table_schema,table_name from expected_tables) and c.relrowsecurity), 'RLS enabled on public and private tables'),
    ('eight_own_select_policies', (select count(*) = 8 from policies where cmd='SELECT' and name like '%_select_own' and qual like '%auth.uid%'), coalesce((select jsonb_agg(name order by name)::text from policies), '[]')),
    ('no_write_or_trainer_policy', not exists(select 1 from policies where cmd in ('INSERT','UPDATE','DELETE') or lower(name) like '%trainer%' or lower(qual) like '%trainer%'), 'no browser write or trainer policy'),
    ('no_browser_table_privileges', not exists(select 1 from table_acl), coalesce((select jsonb_agg(to_jsonb(a))::text from table_acl a), '[]')),
    ('private_schema_isolated', not exists(select 1 from schema_acl where grantee in ('PUBLIC','anon','authenticated')), coalesce((select jsonb_agg(to_jsonb(a))::text from schema_acl a), '[]')),
    ('profile_ownership_fks', (select count(*) >= 14 from constraints where type='f' and definition like '%references profiles(id)%'), 'member ownership references profiles'),
    ('relational_owner_fks', exists(select 1 from constraints where name='ai_messages_thread_owner_fk' and definition like '%thread_id, user_id%') and exists(select 1 from constraints where name='ai_action_proposals_context_owner_fk' and definition like '%context_manifest_id, user_id%') and exists(select 1 from constraints where name='ai_action_decisions_proposal_owner_fk' and definition like '%proposal_id, user_id%') and exists(select 1 from constraints where name='ai_runs_thread_owner_fk' and definition like '%thread_id, user_id%') and exists(select 1 from constraints where name='ai_runs_context_owner_fk' and definition like '%context_manifest_id, user_id%'), 'cross-member relational links blocked'),
    ('idempotency_uniques', exists(select 1 from constraints where name='ai_consent_events_user_request_unique') and exists(select 1 from constraints where name='ai_messages_request_role_unique') and exists(select 1 from constraints where name='ai_action_decisions_user_request_unique') and exists(select 1 from constraints where name='ai_data_lifecycle_requests_user_request_unique') and exists(select 1 from constraints where name='ai_runs_user_request_unique'), 'request identities unique'),
    ('history_and_operational_indexes', exists(select 1 from indexes where name='ai_consent_events_current_idx') and exists(select 1 from indexes where name='ai_messages_thread_history_idx') and exists(select 1 from indexes where name='ai_threads_retention_due_idx') and exists(select 1 from indexes where name='ai_runs_user_status_idx') and exists(select 1 from indexes where name='ai_usage_ledger_user_created_idx') and exists(select 1 from indexes where name='ai_rate_buckets_updated_idx'), 'bounded lookup indexes'),
    ('feature_flags_default_off', (select count(*) = 3 and bool_and(not enabled) and bool_and(environment='staging') from flags), coalesce((select jsonb_agg(to_jsonb(f) order by flag_code)::text from flags f), '[]')),
    ('budget_exact_3_plus_1', exists(select 1 from ai_private.budget_policies where active and currency_code='EUR' and included_micros=3000000 and warning_micros=2400000 and grace_micros=1000000 and hard_cap_micros=4000000 and terra_stop_micros=3000000), 'EUR 3 included, warning 80%, EUR 1 grace, EUR 4 hard'),
    ('no_automatic_billing_contract', exists(select 1 from functions where function_schema='ai_private' and name='evaluate_budget' and source like '%automatic_billing%false%'), 'budget evaluator never bills'),
    ('action_allowlist_exact', (select array_agg(action_code order by action_code)::text[] = array['add_rest_day','calorie_target_adjustment','replace_exercise','reschedule_training','training_volume_adjustment']::text[] from ai_private.action_policies where enabled), 'five allowed proposal types'),
    ('action_bounds_locked', exists(select 1 from ai_private.action_policies where action_code='training_volume_adjustment' and max_increase_percent=20 and max_decrease_percent=100) and exists(select 1 from ai_private.action_policies where action_code='calorie_target_adjustment' and max_increase_percent=10 and max_absolute_delta=300) and exists(select 1 from functions where function_schema='ai_private' and name='validate_action_contract' and source like '%compatible_alternative_required%'), '20 percent training and min(10 percent,300 kcal)'),
    ('medication_and_diagnosis_not_allowlisted', not exists(select 1 from ai_private.action_policies where action_code ~ '(medication|diagnos|treatment)'), 'medical actions absent'),
    ('consent_documents_nl_en_de', (select count(*) = 6 and count(distinct locale)=3 and count(distinct consent_kind)=2 and bool_and(status='active') from ai_private.consent_documents), 'separate AI and trainer-summary documents'),
    ('consent_explicit_unselected', exists(select 1 from constraints where name='ai_consent_events_explicit_check') and exists(select 1 from functions where name='fmz_phase6a_read_consent_contract' and source like '%preselected%false%') and exists(select 1 from functions where name='fmz_phase6a_record_consent' and source like '%explicit_confirmation%'), 'affirmative action required'),
    ('consent_monotonic_ordering', exists(select 1 from indexes where name='ai_consent_events_event_sequence_idx') and exists(select 1 from functions where function_schema='ai_private' and name='current_consent' and regexp_replace(source,'[[:space:]]+',' ','g') like '%order by e.event_sequence desc%'), 'latest grant or withdrawal is deterministic'),
    ('withdrawal_blocks_processing', exists(select 1 from functions where function_schema='ai_private' and name='trust_status' and source like '%consent_state = ''granted''%') and exists(select 1 from functions where name='fmz_phase6a_record_consent' and source like '%withdrawn%'), 'latest granted consent required'),
    ('trainer_summary_separate', exists(select 1 from functions where function_schema='ai_private' and name='can_share_trainer_summary' and source like '%trainer_summary_sharing%') and not exists(select 1 from policies where lower(name) like '%trainer%'), 'separate consent; no trainer chat path'),
    ('entitlement_exact', exists(select 1 from functions where function_schema='ai_private' and name='current_entitlement' and source like '%(''ai'', ''personal_coaching'')%' and source like '%status = ''active''%' and source like '%starts_at <= p_at%' and source like '%ends_at is null or e.ends_at > p_at%'), 'AI/PT current window only'),
    ('free_and_pro_denied', exists(select 1 from functions where function_schema='ai_private' and name='current_entitlement' and source not like '%''free''%' and source not like '%''pro''%'), 'Free and Pro do not grant generation'),
    ('safety_hard_stop', exists(select 1 from functions where function_schema='ai_private' and name='trust_status' and source like '%hard_stop%' and source like '%review_required%') and exists(select 1 from functions where name='fmz_phase6a_service_record_safety_event' and source like '%automatic_execution_blocked%'), 'serious or unclear signals block'),
    ('operational_logs_minimized', exists(select 1 from constraints where name='ai_audit_events_metadata_check') and not exists(select 1 from information_schema.columns where table_schema='ai_private' and table_name in ('runs','usage_ledger','rate_buckets','safety_events','audit_events') and column_name in ('prompt','content','message','email','jwt','token','secret')), 'no raw prompt/content columns'),
    ('retention_90_days', exists(select 1 from constraints where name='ai_threads_retention_window_check' and definition like '%90 days%') and exists(select 1 from functions where name='fmz_phase6a_service_reconcile_retention' and source like '%interval ''90 days''%') and exists(select 1 from functions where name='fmz_phase6a_service_reconcile_retention' and source like '%content_text = null%'), 'grace, restore and raw-content deletion'),
    ('export_delete_lifecycle', exists(select 1 from functions where name='fmz_phase6a_request_data_lifecycle') and exists(select 1 from functions where name='fmz_phase6a_read_export_manifest'), 'request and manifest readiness'),
    ('context_minimized_authority', exists(select 1 from functions where name='fmz_phase6a_get_context_manifest' and source like '%copied%false%' and source like '%health_sync%' and source like '%progress_photos%' and source not like '%recovery_note%' and source not like '%notes%'), 'references/aggregates, explicit unavailable sources'),
    ('strict_schema_live', exists(select 1 from ai_private.structured_schemas where schema_code='coach_response' and schema_version='phase6a.response.v1' and active and schema_body->>'additionalProperties'='false') and exists(select 1 from functions where function_schema='ai_private' and name='validate_structured_response'), 'schema and validator'),
    ('function_inventory', (select count(*) = 23 from functions), coalesce((select jsonb_agg(function_schema||'.'||name order by function_schema,name)::text from functions), '[]')),
    ('safe_search_paths', not exists(select 1 from functions where not ('search_path=pg_catalog, public, ai_private, pg_temp'=any(config))), 'fixed search_path on every Phase 6A function'),
    ('member_rpc_acl', (select count(*) = 8 from function_acl where function_schema='public' and grantee='authenticated' and privilege_type='EXECUTE') and not exists(select 1 from function_acl where function_schema='public' and grantee in ('PUBLIC','anon') and privilege_type='EXECUTE'), 'eight authenticated RPCs only'),
    ('service_rpc_acl', (select count(*) = 5 from function_acl where function_schema='public' and name like 'fmz_phase6a_service_%' and grantee='service_role' and privilege_type='EXECUTE') and not exists(select 1 from function_acl where function_schema='public' and name like 'fmz_phase6a_service_%' and grantee in ('PUBLIC','anon','authenticated') and privilege_type='EXECUTE'), 'five service-only RPCs'),
    ('private_helpers_no_app_execute', not exists(select 1 from function_acl where function_schema='ai_private' and grantee in ('PUBLIC','anon','authenticated') and privilege_type='EXECUTE'), 'private helpers isolated'),
    ('security_definer_only_when_needed', (select count(*) = 13 from functions where function_schema='public' and security_definer) and exists(select 1 from functions where function_schema='ai_private' and name='touch_updated_at' and not security_definer) and exists(select 1 from functions where function_schema='ai_private' and name='evaluate_budget' and not security_definer), 'RPCs bridge revoked tables; pure helpers invoker'),
    ('updated_at_triggers', (select count(*) = 6 from triggers where function_name='touch_updated_at'), coalesce((select jsonb_agg(name order by name)::text from triggers), '[]')),
    ('no_network_or_provider_sql', not exists(select 1 from functions where source ~ '(http_post|net.http|openai|anthropic|gemini|api[_-]?key)'), 'database cannot call a provider'),
    ('no_domain_mutation_sql', not exists(select 1 from functions where (source like '%update public.training_%' or source like '%update public.nutrition_%' or source like '%update public.recovery_%' or source like '%update public.progress_%' or source like '%insert into public.training_%' or source like '%insert into public.nutrition_%')), 'proposal foundation cannot mutate frozen domains'),
    ('public_ai_tables_initially_empty', (select (select count(*) from public.ai_consent_events)+(select count(*) from public.ai_threads)+(select count(*) from public.ai_messages)+(select count(*) from public.ai_context_manifests)+(select count(*) from public.ai_action_proposals)+(select count(*) from public.ai_action_decisions)+(select count(*) from public.ai_member_safety_state)+(select count(*) from public.ai_data_lifecycle_requests)=0), 'no member AI rows created by migration'),
    ('operational_tables_initially_empty', (select (select count(*) from ai_private.runs)+(select count(*) from ai_private.budget_accounts)+(select count(*) from ai_private.usage_ledger)+(select count(*) from ai_private.rate_buckets)+(select count(*) from ai_private.safety_events)+(select count(*) from ai_private.audit_events)=0), 'no provider usage, cost or safety rows'),
    ('frozen_guard_tables', (select count(*) = 26 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind='r' and c.relname in ('profiles','coach_workspaces','user_settings','user_onboarding','entitlements','recovery_logs','training_plans','training_plan_days','training_plan_exercises','workout_sessions','workout_set_logs','nutrition_preferences','foods','food_portions','nutrition_targets','food_logs','food_log_items','food_aliases','nutrition_off_catalog_releases','nutrition_off_products','nutrition_off_product_names','progress_preferences','progress_goals','weight_logs','body_measurements','exercises')), 'Phase 1-5 source tables present'),
    ('frozen_guard_rls', not exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind='r' and c.relname in ('profiles','coach_workspaces','user_settings','user_onboarding','entitlements','recovery_logs','training_plans','training_plan_days','training_plan_exercises','workout_sessions','workout_set_logs','nutrition_preferences','foods','food_portions','nutrition_targets','food_logs','food_log_items','food_aliases','nutrition_off_catalog_releases','nutrition_off_products','nutrition_off_product_names','progress_preferences','progress_goals','weight_logs','body_measurements','exercises') and not c.relrowsecurity), 'frozen RLS retained'),
    ('production_and_secret_scan', not exists(
      select 1 from functions
      where position('hgoygcviutmynaihcvpd' in lower(source)) > 0
         or position('service_role' in lower(source)) > 0
         or position('api_key' in lower(source)) > 0
         or position('provider_key' in lower(source)) > 0
         or position('deno.env' in lower(source)) > 0
         or (position('current_setting' in lower(source)) > 0 and lower(source) ~ '(secret|credential|api_key|provider_key)')
    ), 'no production ref or credential lookup material')
),
result as (
  select jsonb_build_object(
    'overall_pass', bool_and(pass),
    'pass_count', count(*) filter (where pass),
    'fail_count', count(*) filter (where not pass),
    'checks', jsonb_agg(jsonb_build_object('check',check_name,'pass',pass,'detail',detail) order by check_name)
  ) as verification_result
  from checks
)
select verification_result from result;
