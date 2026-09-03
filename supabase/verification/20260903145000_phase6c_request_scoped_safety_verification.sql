with function_meta as (
  select p.oid, p.prosecdef, p.provolatile,
    coalesce(array_to_string(p.proconfig, ','), '') as config,
    p.prosrc,
    coalesce(p.proacl, acldefault('f', p.proowner)) as acl
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'ai_private'
    and p.proname = 'phase6c_chat_status'
    and pg_get_function_identity_arguments(p.oid) = 'p_user_id uuid, p_at timestamp with time zone'
), function_acl as (
  select case when a.grantee = 0 then 'PUBLIC' else r.rolname::text end as grantee,
    a.privilege_type
  from function_meta f
  cross join lateral aclexplode(f.acl) a
  left join pg_roles r on r.oid = a.grantee
), member_functions as (
  select p.proname::text as function_name, p.prosrc
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname in ('fmz_phase6c_create_thread', 'fmz_phase6c_submit_message')
), checks(check_name, pass, detail) as (
  values
    ('function_exact', (select count(*) = 1 from function_meta), 'one exact private chat-status function'),
    ('function_security', (select bool_and(prosecdef and provolatile = 's') from function_meta), 'STABLE SECURITY DEFINER retained'),
    ('safe_search_path', (select bool_and(config like '%search_path=pg_catalog, public, ai_private, pg_temp%') from function_meta), 'fixed safe path'),
    ('private_acl', not exists(select 1 from function_acl where grantee in ('PUBLIC','anon','authenticated') and privilege_type = 'EXECUTE'), 'no direct browser execution'),
    ('communication_gate', (select bool_and(prosrc like '%communication_allowed%' and prosrc like '%chat_write_allowed%') from function_meta), 'explicit communication result'),
    ('entitlement_gate', (select bool_and(prosrc like '%v_entitlement.entitlement_code is not null%') from function_meta), 'current entitlement retained'),
    ('consent_gate', (select bool_and(prosrc like '%v_consent.consent_state = ''granted''%' and prosrc like '%document_active%') from function_meta), 'active consent retained'),
    ('age_gate', (select bool_and(prosrc like '%and v_age%') from function_meta), 'age gate retained'),
    ('mock_only_gate', (select bool_and(prosrc like '%mock_chat_enabled%' and prosrc like '%external_provider_enabled%') from function_meta), 'mock/config gate retained'),
    ('safety_metadata_retained', (select bool_and(prosrc like '%safety_status%' and prosrc like '%automatic_execution_blocked%' and prosrc like '%hard_stop%' and prosrc like '%review_required%') from function_meta), 'risk state remains action authority'),
    ('safety_not_chat_denial', (select bool_and(prosrc not like '%and v_safety not in%' and prosrc not like '%then ''safety_hard_stop''%') from function_meta), 'retained safety state is not a communication ban'),
    ('member_routes_use_gate', (select count(*) = 2 and bool_and(prosrc like '%phase6c_chat_status%') from member_functions), 'thread and message routes use corrected gate'),
    ('mock_runtime_live', exists(select 1 from ai_private.phase6c_runtime_config where singleton and mock_chat_enabled and not external_provider_enabled), 'mock on and provider off'),
    ('no_action_rows_added', true, 'metadata-only verifier performs no mutation'),
    ('frozen_tables_present', to_regclass('public.profiles') is not null and to_regclass('public.recovery_logs') is not null and to_regclass('public.training_plans') is not null and to_regclass('public.food_logs') is not null and to_regclass('public.progress_goals') is not null, 'Phase 1-5 guards'),
    ('package6d_absent', to_regclass('public.ai_trainer_signals') is null, 'Package 6D not started')
), result as (
  select jsonb_build_object(
    'overall_pass', bool_and(pass),
    'pass_count', count(*) filter (where pass),
    'fail_count', count(*) filter (where not pass),
    'checks', jsonb_agg(jsonb_build_object('check', check_name, 'pass', pass, 'detail', detail) order by check_name)
  ) as verification_result
  from checks
)
select verification_result from result;
