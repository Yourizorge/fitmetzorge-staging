begin;

select set_config('phase6d.user1', gen_random_uuid()::text, true);
select set_config('phase6d.user2', gen_random_uuid()::text, true);
select set_config('phase6d.user3', gen_random_uuid()::text, true);
select set_config('phase6d.user4', gen_random_uuid()::text, true);
select set_config('phase6d.trainer', gen_random_uuid()::text, true);
select set_config('phase6d.req.consent1', gen_random_uuid()::text, true);
select set_config('phase6d.req.consent2', gen_random_uuid()::text, true);
select set_config('phase6d.req.consent3', gen_random_uuid()::text, true);
select set_config('phase6d.req.consent4', gen_random_uuid()::text, true);
select set_config('phase6d.req.pref1', gen_random_uuid()::text, true);
select set_config('phase6d.req.pref2', gen_random_uuid()::text, true);
select set_config('phase6d.req.pref3', gen_random_uuid()::text, true);
select set_config('phase6d.req.daily', gen_random_uuid()::text, true);
select set_config('phase6d.req.daily2', gen_random_uuid()::text, true);
select set_config('phase6d.req.post1', gen_random_uuid()::text, true);
select set_config('phase6d.req.post2', gen_random_uuid()::text, true);
select set_config('phase6d.req.weekly_sparse', gen_random_uuid()::text, true);
select set_config('phase6d.req.export', gen_random_uuid()::text, true);
select set_config('phase6d.req.delete', gen_random_uuid()::text, true);
select set_config('phase6d.workout1', gen_random_uuid()::text, true);
select set_config('phase6d.foodlog1', gen_random_uuid()::text, true);
select set_config('phase6d.item1', gen_random_uuid()::text, true);
select set_config('phase6d.weight1', gen_random_uuid()::text, true);

insert into auth.users(id, aud, role, email, raw_user_meta_data, created_at, updated_at)
values
  (current_setting('phase6d.user1')::uuid, 'authenticated', 'authenticated', 'phase6d-fixture-a@example.invalid', '{"role":"client"}'::jsonb, now(), now()),
  (current_setting('phase6d.user2')::uuid, 'authenticated', 'authenticated', 'phase6d-fixture-b@example.invalid', '{"role":"client"}'::jsonb, now(), now()),
  (current_setting('phase6d.user3')::uuid, 'authenticated', 'authenticated', 'phase6d-fixture-c@example.invalid', '{"role":"client"}'::jsonb, now(), now()),
  (current_setting('phase6d.user4')::uuid, 'authenticated', 'authenticated', 'phase6d-fixture-d@example.invalid', '{"role":"client"}'::jsonb, now(), now()),
  (current_setting('phase6d.trainer')::uuid, 'authenticated', 'authenticated', 'phase6d-trainer@example.invalid', '{"role":"trainer"}'::jsonb, now(), now());

insert into public.profiles(id, role, name, email)
values
  (current_setting('phase6d.user1')::uuid, 'client', 'Phase 6D fixture A', 'phase6d-fixture-a@example.invalid'),
  (current_setting('phase6d.user2')::uuid, 'client', 'Phase 6D fixture B', 'phase6d-fixture-b@example.invalid'),
  (current_setting('phase6d.user3')::uuid, 'client', 'Phase 6D fixture C', 'phase6d-fixture-c@example.invalid'),
  (current_setting('phase6d.user4')::uuid, 'client', 'Phase 6D fixture D', 'phase6d-fixture-d@example.invalid'),
  (current_setting('phase6d.trainer')::uuid, 'trainer', 'Phase 6D trainer', 'phase6d-trainer@example.invalid');

insert into public.user_onboarding(user_id, age, completed_at)
values
  (current_setting('phase6d.user1')::uuid, 34, now()),
  (current_setting('phase6d.user2')::uuid, 35, now()),
  (current_setting('phase6d.user4')::uuid, 38, now());

insert into public.entitlements(user_id, entitlement_code, status, source, starts_at, ends_at)
values
  (current_setting('phase6d.user1')::uuid, 'ai', 'active', 'phase6d_fixture', now() - interval '1 day', now() + interval '29 days'),
  (current_setting('phase6d.user2')::uuid, 'free', 'active', 'phase6d_free', now() - interval '1 day', null),
  (current_setting('phase6d.user2')::uuid, 'pro', 'active', 'phase6d_pro', now() - interval '1 day', null),
  (current_setting('phase6d.user3')::uuid, 'ai', 'active', 'phase6d_underage', now() - interval '1 day', null),
  (current_setting('phase6d.user4')::uuid, 'personal_coaching', 'active', 'phase6d_sparse', now() - interval '1 day', now() + interval '29 days');

select set_config('request.jwt.claim.sub', current_setting('phase6d.user1'), true);

insert into public.workout_sessions(
  id, user_id, local_session_key, status, title_snapshot, started_at, completed_at, source, metadata
) values (
  current_setting('phase6d.workout1')::uuid,
  current_setting('phase6d.user1')::uuid,
  'phase6d-local-session',
  'completed',
  'Phase 6D full body',
  now() - interval '2 hours',
  now() - interval '1 hour',
  'phase3_client',
  '{}'::jsonb
);

insert into public.workout_set_logs(
  id, user_id, workout_session_id, planned_exercise_key, exercise_slug, exercise_name_snapshot,
  set_index, actual_reps, actual_weight, rir, rpe, completed_at, source, metadata
)
select
  gen_random_uuid(),
  current_setting('phase6d.user1')::uuid,
  current_setting('phase6d.workout1')::uuid,
  'fixture-' || gs::text,
  'phase6d-exercise',
  'Phase 6D Exercise',
  gs,
  8 + gs,
  40 + gs,
  2,
  7,
  now() - interval '1 hour',
  'phase3_client',
  '{}'::jsonb
from generate_series(1, 3) gs;

insert into public.food_logs(
  id, user_id, log_date, timezone_name, timezone_offset_minutes, status, source, metadata
) values (
  current_setting('phase6d.foodlog1')::uuid,
  current_setting('phase6d.user1')::uuid,
  (now() at time zone 'Europe/Amsterdam')::date,
  'Europe/Amsterdam',
  120,
  'active',
  'phase4_member',
  '{}'::jsonb
);

insert into public.recovery_logs(
  user_id, log_date, sleep_hours, sleep_quality, steps, wellbeing_energy,
  wellbeing_stress, wellbeing_motivation, recovery_feeling, training_load_status,
  training_load_source, source, metadata
) values (
  current_setting('phase6d.user1')::uuid,
  (now() at time zone 'Europe/Amsterdam')::date,
  7.5,
  4,
  8200,
  4,
  2,
  4,
  4,
  'moderate',
  'phase2_placeholder',
  'manual_phase2',
  '{}'::jsonb
);

insert into public.weight_logs(
  id, user_id, log_date, measured_at, timezone_name, timezone_offset_minutes,
  weight_kg, source, status, request_id
) values (
  current_setting('phase6d.weight1')::uuid,
  current_setting('phase6d.user1')::uuid,
  (now() at time zone 'Europe/Amsterdam')::date,
  now(),
  'Europe/Amsterdam',
  120,
  82.4,
  'manual_phase5',
  'active',
  gen_random_uuid()
);

select set_config('request.jwt.claim.sub', current_setting('phase6d.user1'), true);
set local role authenticated;

do $member$
declare
  v_status jsonb;
  v_contract jsonb;
  v_consent jsonb;
  v_pref jsonb;
  v_pref2 jsonb;
  v_prepare jsonb;
  v_replay jsonb;
  v_result_id uuid;
  v_before_workouts integer;
begin
  v_status := public.fmz_phase6d_get_status();
  if v_status#>>'{kinds,daily,deny_reason}' <> 'ai_analysis_consent_required' then
    raise exception 'analysis consent gate failed';
  end if;
  v_contract := public.fmz_phase6d_read_analysis_contract('nl');
  if jsonb_array_length(v_contract->'contracts') <> 1
     or v_contract#>>'{contracts,0,consent_kind}' <> 'ai_analysis' then
    raise exception 'analysis contract missing';
  end if;
  v_consent := public.fmz_phase6d_record_analysis_consent(
    'granted', 'phase6d-analysis-v1', 'nl', true, current_setting('phase6d.req.consent1')::uuid
  );
  v_replay := public.fmz_phase6d_record_analysis_consent(
    'granted', 'phase6d-analysis-v1', 'nl', true, current_setting('phase6d.req.consent1')::uuid
  );
  if not (v_replay->>'replay')::boolean then raise exception 'analysis consent idempotency failed'; end if;
  begin
    perform public.fmz_phase6d_record_analysis_consent(
      'withdrawn', 'phase6d-analysis-v1', 'nl', true, current_setting('phase6d.req.consent1')::uuid
    );
    raise exception 'changed analysis consent replay accepted';
  exception when unique_violation then null;
  end;

  v_pref := public.fmz_phase6d_update_preferences(
    'Europe/Amsterdam'::text, true, '07:45'::text, true, true, 5::smallint, '08:15'::text, null::bigint, current_setting('phase6d.req.pref1')::uuid
  );
  if v_pref->>'daily_time' <> '07:45' or (v_pref->>'weekly_day')::integer <> 5 then
    raise exception 'preferences did not save';
  end if;
  v_pref2 := public.fmz_phase6d_update_preferences(
    'Europe/Amsterdam'::text, true, '08:00'::text, true, true, 5::smallint, '08:15'::text,
    (v_pref->>'revision')::bigint, current_setting('phase6d.req.pref2')::uuid
  );
  begin
    perform public.fmz_phase6d_update_preferences(
      'Europe/Amsterdam'::text, true, '08:30'::text, true, true, 5::smallint, '08:15'::text,
      (v_pref->>'revision')::bigint, current_setting('phase6d.req.pref3')::uuid
    );
    raise exception 'stale preferences accepted';
  exception when serialization_failure then null;
  end;

  begin
    execute 'select count(*) from public.ai_analysis_results';
    raise exception 'direct analysis table read allowed';
  exception when insufficient_privilege then null;
  end;
  begin
    perform public.fmz_phase6d_service_begin_analysis(
      current_setting('phase6d.user1')::uuid, gen_random_uuid(), gen_random_uuid(), 'daily',
      repeat('a', 64), '{}'::jsonb, '{}'::text[]
    );
    raise exception 'service analysis RPC executable by member';
  exception when insufficient_privilege then null;
  end;

  v_before_workouts := (select count(*) from public.workout_sessions where user_id = current_setting('phase6d.user1')::uuid);
  v_prepare := public.fmz_phase6d_prepare_analysis(current_setting('phase6d.req.daily')::uuid, 'daily', 'nl', null);
  if v_prepare->>'status' <> 'prepared'
     or v_prepare->>'model_tier' <> 'luna'
     or v_prepare#>>'{context,quality,reliable}' <> 'true'
     or v_prepare#>>'{context,privacy,private_chat_included}' <> 'false' then
    raise exception 'daily prepare failed';
  end if;
  v_result_id := (v_prepare->>'result_id')::uuid;
  v_replay := public.fmz_phase6d_prepare_analysis(current_setting('phase6d.req.daily')::uuid, 'daily', 'nl', null);
  if not (v_replay->>'replay')::boolean then raise exception 'daily request replay failed'; end if;
  v_replay := public.fmz_phase6d_prepare_analysis(current_setting('phase6d.req.daily2')::uuid, 'daily', 'nl', null);
  if not (v_replay->>'replay')::boolean or v_replay#>>'{result,id}' <> v_result_id::text then
    raise exception 'daily event exactly-once failed';
  end if;
  if (select count(*) from public.workout_sessions where user_id = current_setting('phase6d.user1')::uuid) <> v_before_workouts then
    raise exception 'domain workout data changed during prepare';
  end if;
end
$member$;

reset role;

do $service$
declare
  v_result_id uuid := (select id from public.ai_analysis_results where user_id = current_setting('phase6d.user1')::uuid and request_id = current_setting('phase6d.req.daily')::uuid);
  v_context jsonb := ai_private.phase6d_build_context(current_setting('phase6d.user1')::uuid, 'daily', null, now());
  v_begin jsonb;
  v_complete jsonb;
  v_run_id uuid;
  v_output jsonb;
  v_workouts integer := (select count(*) from public.workout_sessions where user_id = current_setting('phase6d.user1')::uuid);
begin
  v_begin := public.fmz_phase6d_service_begin_analysis(
    current_setting('phase6d.user1')::uuid,
    v_result_id,
    current_setting('phase6d.req.daily')::uuid,
    'daily',
    repeat('b',64),
    v_context,
    array(select jsonb_array_elements_text(v_context->'unavailable_sources'))
  );
  if v_begin->>'status' <> 'reserved' then raise exception 'service begin did not reserve'; end if;
  v_run_id := (v_begin->>'run_id')::uuid;
  v_output := jsonb_build_object(
    'schema_version','phase6d.analysis.v1',
    'analysis_kind','daily',
    'feature_code','daily_analysis',
    'status','ready',
    'summary','Deterministic phase6d read-only analysis.',
    'observations',jsonb_build_array(jsonb_build_object('source','training','text','Aggregate training was available.','evidence',jsonb_build_array('aggregate_training'))),
    'uncertainties','[]'::jsonb,
    'suggestions',jsonb_build_array(jsonb_build_object('kind','read_only_reflection','text','No domain changes were made.')),
    'actions','[]'::jsonb,
    'safety',jsonb_build_object('status','clear','category','none','message_key','safety.clear','automatic_execution_blocked',false),
    'data_quality',v_context->'quality',
    'period',v_context->'period',
    'privacy',jsonb_build_object('chat_history_used_as_context',false,'raw_prompts_logged',false,'raw_notes_included',false,'trainer_visible',false,'domain_writes_allowed',false)
  );
  v_complete := public.fmz_phase6d_service_complete_analysis(v_run_id, v_result_id, v_output, 0, 0, 0);
  if v_complete->>'status' <> 'ready' then raise exception 'service complete failed'; end if;
  perform set_config('phase6d.result.daily', v_result_id::text, true);
  if exists (
    select 1
    from public.ai_action_proposals p
    where p.user_id = current_setting('phase6d.user1')::uuid
      and p.context_manifest_id = (select r.context_manifest_id from public.ai_analysis_results r where r.id = v_result_id)
  ) then
    raise exception 'analysis created action proposal';
  end if;
  if (select count(*) from public.workout_sessions where user_id = current_setting('phase6d.user1')::uuid) <> v_workouts then
    raise exception 'domain workout data changed during completion';
  end if;
  if not exists (
    select 1 from ai_private.usage_ledger
    where run_id = v_run_id and ledger_type in ('reserve','actual') and amount_micros = 0
  ) then
    raise exception 'zero-cost usage ledger missing';
  end if;
end
$service$;

select set_config('request.jwt.claim.sub', current_setting('phase6d.user1'), true);
set local role authenticated;

do $member_after$
declare
  v_list jsonb;
  v_post jsonb;
  v_post_replay jsonb;
  v_export jsonb;
  v_result_id uuid := current_setting('phase6d.result.daily')::uuid;
  v_revision bigint;
begin
  v_list := public.fmz_phase6d_list_analyses(20, null, null);
  if jsonb_array_length(v_list->'results') < 1 or v_list#>>'{results,0,status}' <> 'ready' then
    raise exception 'analysis list missing ready result';
  end if;
  v_revision := (v_list#>>'{results,0,revision}')::bigint;
  v_post := public.fmz_phase6d_prepare_analysis(
    current_setting('phase6d.req.post1')::uuid, 'post_workout', 'nl', current_setting('phase6d.workout1')::uuid
  );
  if v_post->>'status' <> 'prepared' or v_post->>'model_tier' <> 'luna' then
    raise exception 'post workout prepare failed';
  end if;
  v_post_replay := public.fmz_phase6d_prepare_analysis(
    current_setting('phase6d.req.post2')::uuid, 'post_workout', 'nl', current_setting('phase6d.workout1')::uuid
  );
  if not (v_post_replay->>'replay')::boolean then raise exception 'post workout exactly-once failed'; end if;
  v_export := public.fmz_phase6d_export_analyses(current_setting('phase6d.req.export')::uuid);
  if v_export->>'schema_version' <> 'phase6d.analysis-export.v1'
     or (v_export#>>'{retention,result_days}')::integer <> 90 then
    raise exception 'analysis export failed';
  end if;
  perform public.fmz_phase6d_delete_analysis(v_result_id, v_revision, current_setting('phase6d.req.delete')::uuid);
end
$member_after$;

reset role;

do $delete_audit$
declare
  v_result_id uuid := current_setting('phase6d.result.daily')::uuid;
begin
  if exists (
    select 1 from public.ai_analysis_results
    where id = v_result_id
      and (result_payload is not null or summary_text is not null or status <> 'deleted')
  ) then
    raise exception 'analysis delete did not scrub content';
  end if;
end
$delete_audit$;

select set_config('request.jwt.claim.sub', current_setting('phase6d.user2'), true);
set local role authenticated;

do $free_gate$
declare v_status jsonb;
begin
  perform public.fmz_phase6d_record_analysis_consent(
    'granted', 'phase6d-analysis-v1', 'nl', true, current_setting('phase6d.req.consent2')::uuid
  );
  v_status := public.fmz_phase6d_get_status();
  if v_status#>>'{kinds,daily,deny_reason}' <> 'ai_entitlement_required' then
    raise exception 'Free/Pro entitlement gate failed';
  end if;
end
$free_gate$;

reset role;
select set_config('request.jwt.claim.sub', current_setting('phase6d.user3'), true);
set local role authenticated;

do $age_gate$
declare v_status jsonb;
begin
  perform public.fmz_phase6d_record_analysis_consent(
    'granted', 'phase6d-analysis-v1', 'nl', true, current_setting('phase6d.req.consent3')::uuid
  );
  v_status := public.fmz_phase6d_get_status();
  if v_status#>>'{kinds,daily,deny_reason}' <> 'ai_age_required' then
    raise exception 'underage gate failed';
  end if;
end
$age_gate$;

reset role;
select set_config('request.jwt.claim.sub', current_setting('phase6d.user4'), true);
set local role authenticated;

do $quality_gate$
declare
  v_result jsonb;
begin
  perform public.fmz_phase6d_record_analysis_consent(
    'granted', 'phase6d-analysis-v1', 'nl', true, current_setting('phase6d.req.consent4')::uuid
  );
  v_result := public.fmz_phase6d_prepare_analysis(current_setting('phase6d.req.weekly_sparse')::uuid, 'weekly', 'nl', null);
  if v_result->>'status' <> 'insufficient_data'
     or v_result#>>'{result,status}' <> 'insufficient_data' then
    raise exception 'insufficient data did not stop locally';
  end if;
end
$quality_gate$;

reset role;

do $quality_service_check$
begin
  if exists (
    select 1 from ai_private.runs
    where user_id = current_setting('phase6d.user4')::uuid
      and request_id = current_setting('phase6d.req.weekly_sparse')::uuid
  ) then
    raise exception 'insufficient data created provider run';
  end if;
end
$quality_service_check$;

do $budget_safety$
declare
  v_period record;
  v_policy ai_private.budget_policies%rowtype;
  v_status jsonb;
begin
  select * into v_period from ai_private.subscription_period(now() - interval '1 day', now());
  select * into v_policy from ai_private.budget_policies where active order by created_at desc limit 1;
  insert into ai_private.budget_accounts(user_id, period_start, period_end, policy_version, consumed_micros, reserved_micros)
  values (current_setting('phase6d.user1')::uuid, v_period.period_start, v_period.period_end, v_policy.policy_version, 3000001, 0)
  on conflict (user_id, period_start) do update
  set consumed_micros = 3000001, reserved_micros = 0, updated_at = now();
  v_status := ai_private.phase6d_analysis_status(current_setting('phase6d.user1')::uuid, 'weekly', now());
  if v_status->>'deny_reason' <> 'terra_grace_forbidden' then
    raise exception 'Terra grace budget gate failed';
  end if;
  update ai_private.budget_accounts
  set consumed_micros = 0, reserved_micros = 0, updated_at = now()
  where user_id = current_setting('phase6d.user1')::uuid and period_start = v_period.period_start;

  insert into public.ai_member_safety_state(user_id, safety_status, risk_category, blocked_at)
  values (current_setting('phase6d.user1')::uuid, 'hard_stop', 'serious_health', now())
  on conflict (user_id) do update
  set safety_status = 'hard_stop', risk_category = 'serious_health', blocked_at = now(), resolved_at = null, resolution_code = null, revision = public.ai_member_safety_state.revision + 1, updated_at = now();
  v_status := ai_private.phase6d_analysis_status(current_setting('phase6d.user1')::uuid, 'daily', now());
  if v_status->>'deny_reason' <> 'safety_hard_stop'
     or v_status->>'automatic_execution_blocked' <> 'true' then
    raise exception 'safety stop gate failed';
  end if;
end
$budget_safety$;

reset role;
select set_config('request.jwt.claim.sub', current_setting('phase6d.trainer'), true);
set local role authenticated;

do $trainer$
begin
  begin
    perform public.fmz_phase6d_get_status();
    raise exception 'trainer could read analysis status';
  exception when insufficient_privilege then null;
  end;
  begin
    execute 'select count(*) from public.ai_analysis_results';
    raise exception 'trainer direct analysis read allowed';
  exception when insufficient_privilege then null;
  end;
end
$trainer$;

reset role;

rollback;
