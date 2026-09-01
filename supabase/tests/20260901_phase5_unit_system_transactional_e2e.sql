begin;

select set_config('phase5.unit_user1', gen_random_uuid()::text, true);
select set_config('phase5.unit_user2', gen_random_uuid()::text, true);

insert into auth.users(id, aud, role, email, raw_user_meta_data, created_at, updated_at)
values
  (current_setting('phase5.unit_user1')::uuid, 'authenticated', 'authenticated',
    'phase5-unit-a@example.invalid', '{"role":"client"}'::jsonb, now(), now()),
  (current_setting('phase5.unit_user2')::uuid, 'authenticated', 'authenticated',
    'phase5-unit-b@example.invalid', '{"role":"client"}'::jsonb, now(), now());

insert into public.profiles(id, role, name, email)
values
  (current_setting('phase5.unit_user1')::uuid, 'client', 'Phase 5 unit fixture A', 'phase5-unit-a@example.invalid'),
  (current_setting('phase5.unit_user2')::uuid, 'client', 'Phase 5 unit fixture B', 'phase5-unit-b@example.invalid');

select set_config('request.jwt.claim.sub', current_setting('phase5.unit_user1'), true);
set local role authenticated;

do $member_one$
declare
  v_result jsonb;
  v_dashboard jsonb;
  v_rows bigint;
begin
  v_result := public.fmz_phase5_set_unit_system('imperial');
  if v_result->>'unit_system' <> 'imperial' then
    raise exception 'imperial preference save failed';
  end if;

  v_dashboard := public.fmz_phase5_get_progress_dashboard(null, 90);
  if v_dashboard->>'unit_system' <> 'imperial' then
    raise exception 'imperial preference hydration failed';
  end if;

  v_result := public.fmz_phase5_set_unit_system('metric');
  if v_result->>'unit_system' <> 'metric' then
    raise exception 'metric round trip failed';
  end if;

  begin
    execute format(
      'update public.user_settings set unit_system = %L where user_id = %L::uuid',
      'imperial', current_setting('phase5.unit_user2')
    );
    get diagnostics v_rows = row_count;
    if v_rows <> 0 then
      raise exception 'cross-member direct update allowed';
    end if;
  exception when insufficient_privilege then null;
  end;
end
$member_one$;

reset role;
select set_config('request.jwt.claim.sub', current_setting('phase5.unit_user2'), true);
set local role authenticated;

do $member_two$
declare
  v_dashboard jsonb;
begin
  v_dashboard := public.fmz_phase5_get_progress_dashboard(null, 90);
  if v_dashboard->>'unit_system' <> 'metric' then
    raise exception 'cross-member preference leakage';
  end if;

  perform public.fmz_phase5_set_unit_system('imperial');
  v_dashboard := public.fmz_phase5_get_progress_dashboard(null, 90);
  if v_dashboard->>'unit_system' <> 'imperial' then
    raise exception 'second member own preference failed';
  end if;
end
$member_two$;

reset role;

do $canonical$
begin
  if (select unit_system from public.user_settings where user_id = current_setting('phase5.unit_user1')::uuid) <> 'metric'
     or (select unit_system from public.user_settings where user_id = current_setting('phase5.unit_user2')::uuid) <> 'imperial' then
    raise exception 'member preferences not isolated';
  end if;
end
$canonical$;

rollback;

select jsonb_build_object(
  'scope', 'phase5_unit_system_transactional_e2e',
  'overall_pass', true,
  'fixtures_persisted', false
) as result;
