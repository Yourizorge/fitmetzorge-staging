-- Package 6C request-scoped safety: retained risk state blocks automatic actions, not private communication.
begin;

create or replace function ai_private.phase6c_chat_status(p_user_id uuid, p_at timestamptz default now())
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_entitlement record;
  v_consent record;
  v_age boolean;
  v_safety text;
  v_config ai_private.phase6c_runtime_config%rowtype;
  v_allowed boolean;
  v_reason text;
begin
  perform ai_private.assert_member(p_user_id);
  select * into v_entitlement from ai_private.current_entitlement(p_user_id, p_at);
  select * into v_consent from ai_private.current_consent(p_user_id, 'ai_processing');
  v_age := ai_private.phase6c_age_eligible(p_user_id);
  select coalesce(s.safety_status, 'clear') into v_safety
  from public.ai_member_safety_state s where s.user_id = p_user_id;
  v_safety := coalesce(v_safety, 'clear');
  select * into v_config from ai_private.phase6c_runtime_config where singleton;

  -- Safety remains authoritative for automatic execution, but communication stays open.
  v_allowed := v_entitlement.entitlement_code is not null
    and v_consent.consent_state = 'granted'
    and coalesce(v_consent.document_active, false)
    and v_age
    and coalesce(v_config.mock_chat_enabled, false)
    and not coalesce(v_config.external_provider_enabled, true);
  v_reason := case
    when v_entitlement.entitlement_code is null then 'ai_entitlement_required'
    when v_consent.consent_state is distinct from 'granted' or not coalesce(v_consent.document_active, false) then 'ai_consent_required'
    when not v_age then 'ai_age_required'
    when not coalesce(v_config.mock_chat_enabled, false) then 'mock_disabled'
    when coalesce(v_config.external_provider_enabled, true) then 'external_provider_forbidden'
    else 'allowed'
  end;

  return jsonb_build_object(
    'chat_write_allowed', v_allowed,
    'communication_allowed', v_allowed,
    'deny_reason', v_reason,
    'entitlement_code', v_entitlement.entitlement_code,
    'consent_state', coalesce(v_consent.consent_state, 'missing'),
    'consent_document_version', v_consent.document_version,
    'age_eligible', v_age,
    'safety_status', v_safety,
    'automatic_execution_blocked', v_safety in ('hard_stop', 'review_required'),
    'mock_mode', coalesce(v_config.mock_chat_enabled, false),
    'external_ai_enabled', false,
    'external_ai_calls', 0,
    'external_ai_cost_eur', 0
  );
end;
$$;

commit;
