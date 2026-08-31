begin;

select set_config('phase5.test_user1', gen_random_uuid()::text, true);
select set_config('phase5.test_user2', gen_random_uuid()::text, true);
select set_config('phase5.req_goal1', gen_random_uuid()::text, true);
select set_config('phase5.req_goal2', gen_random_uuid()::text, true);
select set_config('phase5.req_weight1', gen_random_uuid()::text, true);
select set_config('phase5.req_weight2', gen_random_uuid()::text, true);
select set_config('phase5.req_measure1', gen_random_uuid()::text, true);
select set_config('phase5.req_measure2', gen_random_uuid()::text, true);

insert into auth.users(id, aud, role, email, raw_user_meta_data, created_at, updated_at)
values
  (current_setting('phase5.test_user1')::uuid, 'authenticated', 'authenticated',
    'phase5-fixture-a@example.invalid', '{"role":"client"}'::jsonb, now(), now()),
  (current_setting('phase5.test_user2')::uuid, 'authenticated', 'authenticated',
    'phase5-fixture-b@example.invalid', '{"role":"client"}'::jsonb, now(), now());

insert into public.profiles(id, role, name, email)
values
  (current_setting('phase5.test_user1')::uuid, 'client', 'Phase 5 fixture A', 'phase5-fixture-a@example.invalid'),
  (current_setting('phase5.test_user2')::uuid, 'client', 'Phase 5 fixture B', 'phase5-fixture-b@example.invalid');

select set_config('request.jwt.claim.sub', current_setting('phase5.test_user1'), true);
set local role authenticated;

do $test$
declare
  v_today date := (now() at time zone 'Europe/Amsterdam')::date;
  v_anchor timestamptz;
  v_offset smallint;
  v_goal1 jsonb;
  v_goal2 jsonb;
  v_weight1 jsonb;
  v_weight2 jsonb;
  v_measure1 jsonb;
  v_measure2 jsonb;
  v_replay jsonb;
  v_dashboard jsonb;
begin
  v_anchor := (v_today::timestamp + interval '12 hours') at time zone 'Europe/Amsterdam';
  v_offset := (extract(epoch from (
    (v_anchor at time zone 'Europe/Amsterdam') - (v_anchor at time zone 'UTC')
  ))::integer / 60)::smallint;

  perform public.fmz_phase5_set_progress_timezone('Europe/Amsterdam');

  v_goal1 := public.fmz_phase5_save_progress_goal(
    'fat_loss', 90, 82, v_today + 120, 'Fixture goal',
    current_setting('phase5.req_goal1')::uuid, null
  );
  v_replay := public.fmz_phase5_save_progress_goal(
    'fat_loss', 90, 82, v_today + 120, 'Fixture goal',
    current_setting('phase5.req_goal1')::uuid, null
  );
  if v_replay->>'id' is distinct from v_goal1->>'id' then
    raise exception 'goal replay failed';
  end if;

  begin
    perform public.fmz_phase5_save_progress_goal(
      'fat_loss', 90, 81, v_today + 120, 'Changed replay',
      current_setting('phase5.req_goal1')::uuid, null
    );
    raise exception 'changed goal replay accepted';
  exception when sqlstate 'P0001' then
    if sqlerrm <> 'progress_request_conflict' then raise; end if;
  end;

  v_goal2 := public.fmz_phase5_save_progress_goal(
    'fat_loss', 90, 81, v_today + 120, 'Corrected goal',
    current_setting('phase5.req_goal2')::uuid,
    (v_goal1->>'updated_at')::timestamptz
  );

  v_weight1 := public.fmz_phase5_save_weight_log(
    v_today, 90, 'Fixture initial', 'Europe/Amsterdam', v_offset,
    current_setting('phase5.req_weight1')::uuid, null
  );
  v_replay := public.fmz_phase5_save_weight_log(
    v_today, 90, 'Fixture initial', 'Europe/Amsterdam', v_offset,
    current_setting('phase5.req_weight1')::uuid, null
  );
  if v_replay->>'id' is distinct from v_weight1->>'id' then
    raise exception 'weight replay failed';
  end if;

  begin
    perform public.fmz_phase5_save_weight_log(
      v_today, 89.5, 'Stale', 'Europe/Amsterdam', v_offset,
      current_setting('phase5.req_weight2')::uuid, now() - interval '1 day'
    );
    raise exception 'stale weight correction accepted';
  exception when sqlstate 'P0001' then
    if sqlerrm <> 'progress_stale_conflict' then raise; end if;
  end;

  v_weight2 := public.fmz_phase5_save_weight_log(
    v_today, 89.5, 'Valid correction', 'Europe/Amsterdam', v_offset,
    current_setting('phase5.req_weight2')::uuid,
    (v_weight1->>'updated_at')::timestamptz
  );
  v_replay := public.fmz_phase5_save_weight_log(
    v_today, 89.5, 'Valid correction', 'Europe/Amsterdam', v_offset,
    current_setting('phase5.req_weight2')::uuid,
    (v_weight1->>'updated_at')::timestamptz
  );
  if v_replay->>'id' is distinct from v_weight2->>'id' then
    raise exception 'corrected weight replay failed';
  end if;

  begin
    perform public.fmz_phase5_save_weight_log(
      v_today - 40, 89, null, 'Europe/Amsterdam', v_offset, gen_random_uuid(), null
    );
    raise exception 'free history boundary bypassed';
  exception when insufficient_privilege then
    if sqlerrm <> 'progress_history_locked' then raise; end if;
  end;

  begin
    perform public.fmz_phase5_save_weight_log(
      v_today + 1, 89, null, 'Europe/Amsterdam', v_offset, gen_random_uuid(), null
    );
    raise exception 'future date accepted';
  exception when invalid_parameter_value then null;
  end;

  v_measure1 := public.fmz_phase5_save_body_measurement(
    v_today, 90, 105, 100, 38, 38.5, 60, 60.5, 'Fixture measurement',
    'Europe/Amsterdam', v_offset, current_setting('phase5.req_measure1')::uuid, null
  );
  v_replay := public.fmz_phase5_save_body_measurement(
    v_today, 90, 105, 100, 38, 38.5, 60, 60.5, 'Fixture measurement',
    'Europe/Amsterdam', v_offset, current_setting('phase5.req_measure1')::uuid, null
  );
  if v_replay->>'id' is distinct from v_measure1->>'id' then
    raise exception 'measurement replay failed';
  end if;

  v_measure2 := public.fmz_phase5_save_body_measurement(
    v_today, 89, 105, 100, 38, 38.5, 60, 60.5, 'Fixture correction',
    'Europe/Amsterdam', v_offset, current_setting('phase5.req_measure2')::uuid,
    (v_measure1->>'updated_at')::timestamptz
  );

  v_dashboard := public.fmz_phase5_get_progress_dashboard(null, 90);
  if v_dashboard->>'access' <> 'free'
     or (v_dashboard->>'history_window_days')::integer <> 30
     or jsonb_array_length(v_dashboard->'weights') <> 1
     or (v_dashboard#>>'{weights,0,weight_kg}')::numeric <> 89.5
     or jsonb_array_length(v_dashboard->'measurements') <> 1
     or (v_dashboard#>>'{goal,target_weight_kg}')::numeric <> 81
     or (v_dashboard#>>'{running,authoritative_source_available}')::boolean then
    raise exception 'dashboard contract failed';
  end if;

  perform public.fmz_phase5_archive_weight_log(
    (v_weight2->>'id')::uuid, (v_weight2->>'updated_at')::timestamptz
  );
  perform public.fmz_phase5_archive_body_measurement(
    (v_measure2->>'id')::uuid, (v_measure2->>'updated_at')::timestamptz
  );
  v_dashboard := public.fmz_phase5_get_progress_dashboard(null, 90);
  if jsonb_array_length(v_dashboard->'weights') <> 0
     or jsonb_array_length(v_dashboard->'measurements') <> 0 then
    raise exception 'archive visibility failed';
  end if;

  begin
    execute 'select count(*) from public.weight_logs';
    raise exception 'direct table read allowed';
  exception when insufficient_privilege then null;
  end;
  begin
    perform public.fmz_phase5_has_full_progress_access(current_setting('phase5.test_user1')::uuid);
    raise exception 'internal helper executable';
  exception when insufficient_privilege then null;
  end;
end
$test$;

reset role;
select set_config('request.jwt.claim.sub', current_setting('phase5.test_user2'), true);
set local role authenticated;

do $isolation$
declare v_dashboard jsonb;
begin
  v_dashboard := public.fmz_phase5_get_progress_dashboard(null, 90);
  if jsonb_array_length(v_dashboard->'weights') <> 0
     or jsonb_array_length(v_dashboard->'measurements') <> 0
     or v_dashboard->>'goal' is not null then
    raise exception 'cross-member isolation failed';
  end if;
end
$isolation$;

reset role;
do $history$
begin
  if (select count(*) from public.weight_logs
      where user_id=current_setting('phase5.test_user1')::uuid and status='superseded') <> 1
     or (select count(*) from public.body_measurements
      where user_id=current_setting('phase5.test_user1')::uuid and status='superseded') <> 1
     or (select count(*) from public.progress_goals
      where user_id=current_setting('phase5.test_user1')::uuid and status='superseded') <> 1 then
    raise exception 'revision history failed';
  end if;
end
$history$;

rollback;

select jsonb_build_object(
  'scope', 'phase5_progress_transactional_e2e',
  'overall_pass', true,
  'fixtures_persisted', false
) as result;
