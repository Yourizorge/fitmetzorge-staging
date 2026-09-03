with expected_columns(table_name,column_name,data_type) as (
  values
    ('ai_threads','client_request_id','uuid'),('ai_threads','revision','int8'),('ai_threads','last_message_sequence','int8'),
    ('ai_messages','sequence_number','int8'),('ai_data_lifecycle_requests','scope_thread_id','uuid'),
    ('runs','source_message_id','uuid')
), columns_actual as (
  select table_schema,table_name,column_name,udt_name::text as data_type,is_nullable,column_default
  from information_schema.columns
  where (table_schema='public' and table_name in ('ai_threads','ai_messages','ai_data_lifecycle_requests'))
     or (table_schema='ai_private' and table_name='runs')
), funcs as (
  select n.nspname::text as schema_name,p.proname::text as function_name,
    pg_get_function_identity_arguments(p.oid) as args,p.prosecdef,p.provolatile,
    coalesce(array_to_string(p.proconfig,','),'') as config,p.prosrc,
    coalesce(p.proacl,acldefault('f',p.proowner)) as acl
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where (n.nspname='public' and p.proname like 'fmz_phase6c_%')
     or (n.nspname='ai_private' and p.proname like 'phase6c_%')
), function_acl as (
  select f.schema_name,f.function_name,f.args,
    case when a.grantee=0 then 'PUBLIC' else r.rolname::text end as grantee,a.privilege_type
  from funcs f cross join lateral aclexplode(f.acl) a
  left join pg_roles r on r.oid=a.grantee
), indexes as (
  select schemaname::text,tablename::text,indexname::text,indexdef
  from pg_indexes where schemaname in ('public','ai_private')
), triggers as (
  select c.relname::text as table_name,t.tgname::text as trigger_name,p.proname::text as function_name
  from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_proc p on p.oid=t.tgfoid
  join pg_namespace n on n.oid=c.relnamespace
  where not t.tgisinternal and n.nspname='public' and c.relname in ('ai_messages','ai_threads')
), policies as (
  select schemaname,tablename,policyname,roles,cmd,qual,with_check
  from pg_policies where schemaname in ('public','ai_private') and tablename like 'ai_%'
), cron_job as (
  select jobname,schedule,command,active from cron.job where jobname='fmz-phase6c-retention-sweep'
), frozen_counts as (
  select
    (select count(*) from ai_private.feature_flags where enabled) as enabled_6a_flags,
    (select count(*) from ai_private.provider_configurations where real_member_processing_enabled) as enabled_6b_member_processing,
    (select count(*) from public.ai_threads) as thread_count,
    (select count(*) from public.ai_messages) as message_count
), checks(check_name,pass,detail) as (
  values
    ('expected_columns',not exists(select 1 from expected_columns e left join columns_actual a on a.table_name=e.table_name and a.column_name=e.column_name and a.data_type=e.data_type where a.column_name is null),'six additive columns'),
    ('sequence_not_null',exists(select 1 from columns_actual where table_name='ai_messages' and column_name='sequence_number' and is_nullable='NO'),'message sequence required'),
    ('thread_defaults',exists(select 1 from columns_actual where table_name='ai_threads' and column_name='revision' and is_nullable='NO' and column_default like '%1%') and exists(select 1 from columns_actual where table_name='ai_threads' and column_name='last_message_sequence' and is_nullable='NO' and column_default like '%0%'),'thread revision defaults'),
    ('runtime_config_private',to_regclass('ai_private.phase6c_runtime_config') is not null and (select relrowsecurity from pg_class where oid='ai_private.phase6c_runtime_config'::regclass),'private RLS config'),
    ('mock_only_live',exists(select 1 from ai_private.phase6c_runtime_config where singleton and mock_chat_enabled and not external_provider_enabled),'6C mock on, provider off'),
    ('sequence_indexes',exists(select 1 from indexes where indexname='ai_messages_thread_sequence_idx') and exists(select 1 from indexes where indexname='ai_threads_user_client_request_idx'),'deterministic order/idempotency'),
    ('run_source_index',exists(select 1 from indexes where indexname='ai_runs_source_message_idx'),'retry correlation'),
    ('message_sequence_trigger',exists(select 1 from triggers where trigger_name='ai_messages_assign_sequence' and function_name='phase6c_assign_message_sequence'),'sequence trigger'),
    ('message_immutability_trigger',exists(select 1 from triggers where trigger_name='ai_messages_protect_content' and function_name='phase6c_protect_message_content'),'content immutable except scrub'),
    ('member_rpc_set',(select count(*) from funcs where schema_name='public' and function_name in ('fmz_phase6c_get_chat_status','fmz_phase6c_create_thread','fmz_phase6c_list_threads','fmz_phase6c_read_thread','fmz_phase6c_submit_message','fmz_phase6c_export_chat','fmz_phase6c_delete_thread'))=7,'seven member RPCs'),
    ('service_rpc',exists(select 1 from funcs where schema_name='public' and function_name='fmz_phase6c_service_begin_mock_run' and prosecdef),'service mock begin'),
    ('safe_search_paths',not exists(select 1 from funcs where config not like '%search_path=pg_catalog, public, ai_private, pg_temp%'),'fixed search paths'),
    ('member_rpc_acl',(select count(distinct function_name) from function_acl where function_name in ('fmz_phase6c_get_chat_status','fmz_phase6c_create_thread','fmz_phase6c_list_threads','fmz_phase6c_read_thread','fmz_phase6c_submit_message','fmz_phase6c_export_chat','fmz_phase6c_delete_thread') and grantee='authenticated' and privilege_type='EXECUTE')=7 and not exists(select 1 from function_acl where function_name in ('fmz_phase6c_get_chat_status','fmz_phase6c_create_thread','fmz_phase6c_list_threads','fmz_phase6c_read_thread','fmz_phase6c_submit_message','fmz_phase6c_export_chat','fmz_phase6c_delete_thread') and privilege_type='EXECUTE' and grantee in ('PUBLIC','anon')),'authenticated browser execute; PUBLIC/anon blocked'),
    ('service_rpc_acl',exists(select 1 from function_acl where function_name='fmz_phase6c_service_begin_mock_run' and grantee='service_role' and privilege_type='EXECUTE') and not exists(select 1 from function_acl where function_name='fmz_phase6c_service_begin_mock_run' and grantee in ('PUBLIC','anon','authenticated') and privilege_type='EXECUTE'),'service-only execute'),
    ('private_function_acl',not exists(select 1 from function_acl where schema_name='ai_private' and grantee in ('PUBLIC','anon','authenticated') and privilege_type='EXECUTE'),'private helpers blocked'),
    ('auth_uid_ownership',exists(select 1 from funcs where function_name='fmz_phase6c_submit_message' and prosrc like '%auth.uid()%') and exists(select 1 from funcs where function_name='fmz_phase6c_delete_thread' and prosrc like '%auth.uid()%'),'auth ownership'),
    ('age_18_gate',exists(select 1 from funcs where function_name='phase6c_age_eligible' and prosrc like '%age >= 18%'),'age minimum'),
    ('entitlement_gate',exists(select 1 from funcs where function_name='phase6c_chat_status' and prosrc like '%current_entitlement%'),'frozen AI/PT entitlement'),
    ('consent_gate',exists(select 1 from funcs where function_name='phase6c_chat_status' and prosrc like '%ai_processing%' and prosrc like '%document_active%'),'versioned consent'),
    ('safety_gate',exists(select 1 from funcs where function_name='phase6c_chat_status' and prosrc like '%hard_stop%' and prosrc like '%review_required%'),'hard stop'),
    ('message_bounds',exists(select 1 from funcs where function_name='fmz_phase6c_submit_message' and prosrc like '%message_max_characters%' and prosrc like '%max_messages_per_thread%'),'bounded messages'),
    ('thread_bounds',exists(select 1 from funcs where function_name='fmz_phase6c_create_thread' and prosrc like '%max_active_threads%'),'bounded threads'),
    ('rate_limit',exists(select 1 from funcs where function_name='fmz_phase6c_submit_message' and prosrc like '%rate_buckets%' and prosrc like '%ai_rate_limit_reached%'),'atomic server rate'),
    ('stale_revision',exists(select 1 from funcs where function_name='fmz_phase6c_submit_message' and prosrc like '%ai_thread_stale_conflict%'),'stale write guard'),
    ('idempotent_message',exists(select 1 from funcs where function_name='fmz_phase6c_submit_message' and prosrc like '%ai_message_request_conflict%' and prosrc like '%replay%'),'duplicate submit replay'),
    ('idempotent_mock_attempt',exists(select 1 from funcs where function_name='fmz_phase6c_service_begin_mock_run' and prosrc like '%ai_run_request_conflict%' and prosrc like '%replay%'),'mock attempt replay'),
    ('export_minimized',exists(select 1 from funcs where function_name='fmz_phase6c_export_chat' and prosrc like '%phase6c.chat-export.v1%') and not exists(select 1 from funcs where function_name='fmz_phase6c_export_chat' and prosrc ~* 'budget|provider_model|payload_hash'),'own JSON excludes internal data'),
    ('delete_scrubs_raw',exists(select 1 from funcs where function_name='fmz_phase6c_delete_thread' and prosrc like '%content_text=null%' and prosrc like '%structured_output=null%'),'raw content scrub'),
    ('retention_90',exists(select 1 from funcs where function_name='phase6c_apply_retention' and prosrc like '%interval ''90 days''%' and prosrc like '%content_text = null%'),'90-day raw deletion'),
    ('retention_delete_before_restore',exists(select 1 from funcs where function_name='phase6c_apply_retention' and strpos(prosrc,'retention_due_at <= p_at') < strpos(prosrc,'current_entitlement')),'overdue scrub precedes restore'),
    ('retention_cron',exists(select 1 from cron_job where schedule='* * * * *' and active and command like '%phase6c_retention_sweep%'),'minute sweep'),
    ('no_trainer_policy',not exists(select 1 from policies where coalesce(policyname,'') ilike '%trainer%' or coalesce(array_to_string(roles,','),'') ilike '%trainer%'),'no trainer policy'),
    ('no_delete_policy',not exists(select 1 from policies where cmd='DELETE'),'no AI delete policy'),
    ('frozen_flags_off',(select enabled_6a_flags=0 and enabled_6b_member_processing=0 from frozen_counts),'6A member flags and 6B real-member processing off'),
    ('no_external_provider_path',exists(select 1 from ai_private.phase6c_runtime_config where not external_provider_enabled) and exists(select 1 from funcs where function_name='phase6c_chat_status' and prosrc like '%external_ai_calls%' and prosrc like '%external_ai_cost_eur%'),'zero provider boundary'),
    ('all_ai_public_rls',not exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname like 'ai_%' and c.relkind='r' and not c.relrowsecurity),'all public AI RLS'),
    ('frozen_tables_present',to_regclass('public.profiles') is not null and to_regclass('public.recovery_logs') is not null and to_regclass('public.training_plans') is not null and to_regclass('public.food_logs') is not null and to_regclass('public.progress_goals') is not null,'Phase 1-5 guards')
), result as (
  select jsonb_build_object(
    'overall_pass',bool_and(pass),
    'pass_count',count(*) filter(where pass),
    'fail_count',count(*) filter(where not pass),
    'checks',jsonb_agg(jsonb_build_object('check',check_name,'pass',pass,'detail',detail) order by check_name),
    'baseline_counts',(select to_jsonb(frozen_counts) from frozen_counts)
  ) as verification_result from checks
)
select verification_result from result;
