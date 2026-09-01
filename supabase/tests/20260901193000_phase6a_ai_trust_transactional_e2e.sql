begin;

select set_config('phase6a.user1', gen_random_uuid()::text, true);
select set_config('phase6a.user2', gen_random_uuid()::text, true);
select set_config('phase6a.req.consent1', gen_random_uuid()::text, true);
select set_config('phase6a.req.consent2', gen_random_uuid()::text, true);
select set_config('phase6a.req.withdraw', gen_random_uuid()::text, true);
select set_config('phase6a.req.regrant', gen_random_uuid()::text, true);
select set_config('phase6a.req.summary1', gen_random_uuid()::text, true);
select set_config('phase6a.req.summary2', gen_random_uuid()::text, true);
select set_config('phase6a.req.run1', gen_random_uuid()::text, true);
select set_config('phase6a.req.run2', gen_random_uuid()::text, true);
select set_config('phase6a.thread1', gen_random_uuid()::text, true);

insert into auth.users(id, aud, role, email, raw_user_meta_data, created_at, updated_at)
values
  (current_setting('phase6a.user1')::uuid, 'authenticated', 'authenticated', 'phase6a-fixture-a@example.invalid', '{"role":"client"}'::jsonb, now(), now()),
  (current_setting('phase6a.user2')::uuid, 'authenticated', 'authenticated', 'phase6a-fixture-b@example.invalid', '{"role":"client"}'::jsonb, now(), now());

insert into public.profiles(id, role, name, email)
values
  (current_setting('phase6a.user1')::uuid, 'client', 'Phase 6A fixture A', 'phase6a-fixture-a@example.invalid'),
  (current_setting('phase6a.user2')::uuid, 'client', 'Phase 6A fixture B', 'phase6a-fixture-b@example.invalid');

insert into public.entitlements(user_id, entitlement_code, status, source, starts_at, ends_at)
values
  (current_setting('phase6a.user1')::uuid, 'ai', 'active', 'phase6a_fixture', now() - interval '1 day', now() + interval '29 days'),
  (current_setting('phase6a.user2')::uuid, 'free', 'active', 'phase6a_free', now() - interval '1 day', null),
  (current_setting('phase6a.user2')::uuid, 'pro', 'active', 'phase6a_pro', now() - interval '1 day', null),
  (current_setting('phase6a.user2')::uuid, 'ai', 'inactive', 'phase6a_inactive', now() - interval '1 day', null),
  (current_setting('phase6a.user2')::uuid, 'ai', 'active', 'phase6a_future', now() + interval '1 day', now() + interval '2 days'),
  (current_setting('phase6a.user2')::uuid, 'ai', 'expired', 'phase6a_expired', now() - interval '30 days', now() - interval '1 day');

select set_config('request.jwt.claim.sub', current_setting('phase6a.user1'), true);
set local role authenticated;

do $member$
declare
  v_status jsonb;
  v_first jsonb;
  v_replay jsonb;
begin
  v_status := public.fmz_phase6a_get_trust_status('private_chat');
  if v_status->>'deny_reason' <> 'ai_consent_required'
     or (v_status->>'structurally_eligible')::boolean then
    raise exception 'no-consent gate failed';
  end if;

  v_first := public.fmz_phase6a_record_consent(
    'ai_processing', 'granted', 'phase6a-ai-processing-v1', 'nl', true,
    current_setting('phase6a.req.consent1')::uuid
  );
  v_replay := public.fmz_phase6a_record_consent(
    'ai_processing', 'granted', 'phase6a-ai-processing-v1', 'nl', true,
    current_setting('phase6a.req.consent1')::uuid
  );
  if not (v_replay->>'replay')::boolean
     or v_replay#>>'{consent,id}' is distinct from v_first#>>'{consent,id}' then
    raise exception 'consent idempotency failed';
  end if;
  begin
    perform public.fmz_phase6a_record_consent(
      'ai_processing', 'withdrawn', 'phase6a-ai-processing-v1', 'nl', true,
      current_setting('phase6a.req.consent1')::uuid
    );
    raise exception 'changed consent replay accepted';
  exception when unique_violation then null;
  end;

  v_status := public.fmz_phase6a_get_trust_status('private_chat');
  if not (v_status->>'structurally_eligible')::boolean
     or (v_status->>'operationally_allowed')::boolean
     or v_status->>'deny_reason' <> 'ai_feature_disabled'
     or (v_status->>'automatic_billing')::boolean then
    raise exception 'structural eligibility or feature-off gate failed';
  end if;

  perform public.fmz_phase6a_record_consent(
    'ai_processing', 'withdrawn', 'phase6a-ai-processing-v1', 'nl', true,
    current_setting('phase6a.req.withdraw')::uuid
  );
  v_status := public.fmz_phase6a_get_trust_status('private_chat');
  if v_status->>'deny_reason' <> 'ai_consent_required' then
    raise exception 'withdrawal did not block';
  end if;
  perform public.fmz_phase6a_record_consent(
    'ai_processing', 'granted', 'phase6a-ai-processing-v1', 'nl', true,
    current_setting('phase6a.req.regrant')::uuid
  );

  perform public.fmz_phase6a_record_consent(
    'trainer_summary_sharing', 'granted', 'phase6a-trainer-summary-v1', 'nl', true,
    current_setting('phase6a.req.summary1')::uuid
  );
  perform public.fmz_phase6a_record_consent(
    'trainer_summary_sharing', 'withdrawn', 'phase6a-trainer-summary-v1', 'nl', true,
    current_setting('phase6a.req.summary2')::uuid
  );

  begin
    execute 'select count(*) from public.ai_messages';
    raise exception 'direct AI table read allowed';
  exception when insufficient_privilege then null;
  end;
  begin
    perform ai_private.can_share_trainer_summary(current_setting('phase6a.user1')::uuid);
    raise exception 'private helper executable';
  exception when insufficient_privilege then null;
  end;
  begin
    perform public.fmz_phase6a_service_begin_run(
      current_setting('phase6a.user1')::uuid, gen_random_uuid(), null,
      'private_chat','mock','luna','phase6a-policy-v1','phase6a.response.v1',
      repeat('a',64),0,'{}'::jsonb,'{}'::text[]
    );
    raise exception 'service RPC executable by member';
  exception when insufficient_privilege then null;
  end;
end
$member$;

reset role;
select set_config('request.jwt.claim.sub', current_setting('phase6a.user2'), true);
set local role authenticated;

do $entitlements$
declare v_status jsonb;
begin
  perform public.fmz_phase6a_record_consent(
    'ai_processing', 'granted', 'phase6a-ai-processing-v1', 'en', true,
    current_setting('phase6a.req.consent2')::uuid
  );
  v_status := public.fmz_phase6a_get_trust_status('private_chat');
  if v_status->>'deny_reason' <> 'ai_entitlement_required' then
    raise exception 'Free/Pro/inactive/future/expired gate failed';
  end if;
end
$entitlements$;

reset role;

insert into public.entitlements(user_id, entitlement_code, status, source, starts_at, ends_at)
values (current_setting('phase6a.user2')::uuid, 'personal_coaching', 'active', 'phase6a_pt', now() - interval '1 day', now() + interval '29 days');

select set_config('request.jwt.claim.sub', current_setting('phase6a.user2'), true);
set local role authenticated;
do $pt$
declare v_status jsonb;
begin
  v_status := public.fmz_phase6a_get_trust_status('private_chat');
  if not (v_status->>'structurally_eligible')::boolean
     or v_status->>'entitlement_code' <> 'personal_coaching'
     or v_status->>'deny_reason' <> 'ai_feature_disabled' then
    raise exception 'personal coaching structural eligibility failed';
  end if;
end
$pt$;

reset role;

update ai_private.feature_flags set enabled = true
where flag_code in ('ai_coach_enabled','staging_mock_enabled');

do $service$
declare
  v_begin jsonb;
  v_replay jsonb;
  v_run_id uuid;
  v_output jsonb := '{
    "schema_version":"phase6a.response.v1",
    "feature_code":"private_chat",
    "summary":"Deterministic transaction fixture.",
    "observations":["fixture"],
    "uncertainties":["fixture"],
    "recommendations":["fixture"],
    "actions":[],
    "safety":{"status":"clear","category":"none","message_key":"safety.clear","automatic_execution_blocked":false}
  }'::jsonb;
  v_status jsonb;
begin
  v_begin := public.fmz_phase6a_service_begin_run(
    current_setting('phase6a.user1')::uuid,
    current_setting('phase6a.req.run1')::uuid,
    null,
    'private_chat','mock','luna','phase6a-policy-v1','phase6a.response.v1',
    repeat('b',64),0,
    '{"training":{"authority":"training_plans","copied":false}}'::jsonb,
    array['health_sync','progress_photos']
  );
  v_run_id := (v_begin->>'run_id')::uuid;
  v_replay := public.fmz_phase6a_service_begin_run(
    current_setting('phase6a.user1')::uuid,
    current_setting('phase6a.req.run1')::uuid,
    null,
    'private_chat','mock','luna','phase6a-policy-v1','phase6a.response.v1',
    repeat('b',64),0,
    '{"training":{"authority":"training_plans","copied":false}}'::jsonb,
    array['health_sync','progress_photos']
  );
  if not (v_replay->>'replay')::boolean or (v_replay->>'run_id')::uuid <> v_run_id then
    raise exception 'run idempotency failed';
  end if;
  begin
    perform public.fmz_phase6a_service_begin_run(
      current_setting('phase6a.user1')::uuid,
      current_setting('phase6a.req.run1')::uuid,
      null,
      'private_chat','mock','luna','phase6a-policy-v1','phase6a.response.v1',
      repeat('b',64),1,
      '{"training":{"authority":"training_plans","copied":false}}'::jsonb,
      array['health_sync','progress_photos']
    );
    raise exception 'run replay conflict was accepted';
  exception when unique_violation then null;
  end;
  perform public.fmz_phase6a_service_complete_run(v_run_id, v_output, 0, 100, 50);
  v_replay := public.fmz_phase6a_service_complete_run(v_run_id, v_output, 0, 100, 50);
  if not (v_replay->>'replay')::boolean then raise exception 'completion replay failed'; end if;
  begin
    perform public.fmz_phase6a_service_complete_run(v_run_id, v_output, 0, 101, 50);
    raise exception 'completion replay conflict was accepted';
  exception when unique_violation then null;
  end;

  if (ai_private.evaluate_budget(2399999,0,0,'luna')->>'fair_use_status') <> 'normal'
     or (ai_private.evaluate_budget(2400000,0,0,'luna')->>'fair_use_status') <> 'warning'
     or not (ai_private.evaluate_budget(3000000,0,1,'luna')->>'allowed')::boolean
     or (ai_private.evaluate_budget(3000000,0,1,'terra')->>'allowed')::boolean
     or (ai_private.evaluate_budget(4000000,0,1,'luna')->>'allowed')::boolean then
    raise exception 'budget contract failed';
  end if;
  if not (ai_private.validate_action_contract(
    'training_volume_adjustment',
    '{"delta_percent":20,"explanation":"bounded","reversible":true}'::jsonb
  )->>'allowed')::boolean
  or (ai_private.validate_action_contract(
    'training_volume_adjustment',
    '{"delta_percent":21,"explanation":"too large","reversible":true}'::jsonb
  )->>'allowed')::boolean
  or (ai_private.validate_action_contract(
    'medication_change',
    '{"explanation":"forbidden","reversible":true}'::jsonb
  )->>'allowed')::boolean then
    raise exception 'action policy failed';
  end if;

  perform public.fmz_phase6a_service_record_safety_event(
    current_setting('phase6a.user1')::uuid, v_run_id,
    'unclear_health', 'hard_stop', 'phase6a-safety-v1'
  );
  v_status := ai_private.trust_status(current_setting('phase6a.user1')::uuid, 'private_chat', 'mock', now());
  if v_status->>'deny_reason' <> 'safety_hard_stop' then raise exception 'safety hard stop failed'; end if;
  perform public.fmz_phase6a_service_record_safety_event(
    current_setting('phase6a.user1')::uuid, v_run_id,
    'unclear_health', 'resolved', 'phase6a-safety-v1'
  );

  begin
    perform public.fmz_phase6a_service_begin_run(
      current_setting('phase6a.user1')::uuid, gen_random_uuid(), null,
      'private_chat','provider','luna','phase6a-policy-v1','phase6a.response.v1',
      repeat('c',64),1000,'{}'::jsonb,'{}'::text[]
    );
    raise exception 'provider run allowed while provider flag off';
  exception when insufficient_privilege then
    if sqlerrm <> 'provider_disabled' then raise; end if;
  end;

  if ai_private.validate_structured_response('{"unexpected":true}'::jsonb) then
    raise exception 'malformed output accepted';
  end if;
end
$service$;

insert into public.ai_threads(id, user_id, feature_code, locale)
values (current_setting('phase6a.thread1')::uuid, current_setting('phase6a.user2')::uuid, 'private_chat', 'en');
insert into public.ai_messages(
  id, user_id, thread_id, message_role, feature_code, content_text, status, request_id
) values (
  gen_random_uuid(), current_setting('phase6a.user2')::uuid, current_setting('phase6a.thread1')::uuid,
  'user', 'private_chat', 'Retention fixture', 'active', gen_random_uuid()
);

delete from public.entitlements
where user_id = current_setting('phase6a.user2')::uuid
  and entitlement_code = 'personal_coaching' and source = 'phase6a_pt';

do $retention$
declare
  v_result jsonb;
  v_started timestamptz := now();
begin
  v_result := public.fmz_phase6a_service_reconcile_retention(current_setting('phase6a.user2')::uuid, v_started);
  if (v_result->>'grace_started')::integer <> 1 then raise exception 'retention grace failed'; end if;
  v_result := public.fmz_phase6a_service_reconcile_retention(current_setting('phase6a.user2')::uuid, v_started + interval '91 days');
  if (v_result->>'threads_content_deleted')::integer <> 1
     or exists(select 1 from public.ai_messages where thread_id=current_setting('phase6a.thread1')::uuid and content_text is not null) then
    raise exception 'retention deletion failed';
  end if;
end
$retention$;

select set_config('request.jwt.claim.sub', current_setting('phase6a.user1'), true);
set local role authenticated;
do $isolation$
begin
  begin
    perform public.fmz_phase6a_read_thread_history(current_setting('phase6a.thread1')::uuid, 50, null);
    raise exception 'cross-member thread read allowed';
  exception when insufficient_privilege then null;
  end;
end
$isolation$;

reset role;
rollback;

select jsonb_build_object(
  'scope', 'phase6a_ai_trust_transactional_e2e',
  'overall_pass', true,
  'external_ai_calls', 0,
  'external_ai_cost_eur', 0,
  'fixtures_persisted', false
) as result;
