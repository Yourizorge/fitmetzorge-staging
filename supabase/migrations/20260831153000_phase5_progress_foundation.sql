-- FitMetZorge Phase 5 Progress foundation (STAGING first)
-- Additive own-user storage, revision-safe writes, bounded reads and no trainer access.

begin;

create table if not exists public.progress_preferences (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  timezone_name text not null default 'UTC',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint progress_preferences_timezone_name_check
    check (char_length(btrim(timezone_name)) between 1 and 64)
);

create table if not exists public.progress_goals (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  goal_code text not null,
  baseline_weight_kg numeric(6,2),
  target_weight_kg numeric(6,2),
  target_date date,
  notes text,
  status text not null default 'active',
  request_id uuid not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint progress_goals_goal_code_check check (
    goal_code in (
      'fat_loss', 'muscle_gain', 'strength', 'conditioning',
      'running', 'healthier_living', 'weight_maintenance'
    )
  ),
  constraint progress_goals_weight_bounds_check check (
    (baseline_weight_kg is null or baseline_weight_kg between 25 and 400)
    and (target_weight_kg is null or target_weight_kg between 25 and 400)
  ),
  constraint progress_goals_notes_check
    check (notes is null or char_length(notes) <= 1000),
  constraint progress_goals_status_check
    check (status in ('active', 'superseded', 'archived')),
  constraint progress_goals_archive_state_check check (
    (status = 'active' and archived_at is null)
    or (status <> 'active' and archived_at is not null)
  ),
  constraint progress_goals_user_request_unique unique (user_id, request_id)
);

create table if not exists public.weight_logs (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  log_date date not null,
  measured_at timestamptz not null,
  timezone_name text not null,
  timezone_offset_minutes smallint not null,
  weight_kg numeric(6,2) not null,
  notes text,
  source text not null default 'manual_phase5',
  status text not null default 'active',
  request_id uuid not null,
  supersedes_weight_log_id uuid references public.weight_logs(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint weight_logs_timezone_name_check
    check (char_length(btrim(timezone_name)) between 1 and 64),
  constraint weight_logs_timezone_offset_check
    check (timezone_offset_minutes between -840 and 840),
  constraint weight_logs_weight_check check (weight_kg between 25 and 400),
  constraint weight_logs_notes_check
    check (notes is null or char_length(notes) <= 500),
  constraint weight_logs_source_check check (source in ('manual_phase5', 'onboarding_bootstrap')),
  constraint weight_logs_status_check check (status in ('active', 'superseded', 'archived')),
  constraint weight_logs_archive_state_check check (
    (status = 'active' and archived_at is null)
    or (status <> 'active' and archived_at is not null)
  ),
  constraint weight_logs_user_request_unique unique (user_id, request_id)
);

create table if not exists public.body_measurements (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  log_date date not null,
  measured_at timestamptz not null,
  timezone_name text not null,
  timezone_offset_minutes smallint not null,
  waist_cm numeric(6,2),
  chest_cm numeric(6,2),
  hips_cm numeric(6,2),
  upper_arm_left_cm numeric(6,2),
  upper_arm_right_cm numeric(6,2),
  thigh_left_cm numeric(6,2),
  thigh_right_cm numeric(6,2),
  notes text,
  source text not null default 'manual_phase5',
  status text not null default 'active',
  request_id uuid not null,
  supersedes_body_measurement_id uuid references public.body_measurements(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint body_measurements_timezone_name_check
    check (char_length(btrim(timezone_name)) between 1 and 64),
  constraint body_measurements_timezone_offset_check
    check (timezone_offset_minutes between -840 and 840),
  constraint body_measurements_values_check check (
    (waist_cm is null or waist_cm between 30 and 250)
    and (chest_cm is null or chest_cm between 40 and 250)
    and (hips_cm is null or hips_cm between 40 and 250)
    and (upper_arm_left_cm is null or upper_arm_left_cm between 10 and 120)
    and (upper_arm_right_cm is null or upper_arm_right_cm between 10 and 120)
    and (thigh_left_cm is null or thigh_left_cm between 20 and 150)
    and (thigh_right_cm is null or thigh_right_cm between 20 and 150)
  ),
  constraint body_measurements_at_least_one_check check (
    num_nonnulls(
      waist_cm, chest_cm, hips_cm, upper_arm_left_cm,
      upper_arm_right_cm, thigh_left_cm, thigh_right_cm
    ) > 0
  ),
  constraint body_measurements_notes_check
    check (notes is null or char_length(notes) <= 500),
  constraint body_measurements_source_check check (source = 'manual_phase5'),
  constraint body_measurements_status_check check (status in ('active', 'superseded', 'archived')),
  constraint body_measurements_archive_state_check check (
    (status = 'active' and archived_at is null)
    or (status <> 'active' and archived_at is not null)
  ),
  constraint body_measurements_user_request_unique unique (user_id, request_id)
);

create unique index if not exists progress_goals_one_active_per_user_idx
  on public.progress_goals(user_id)
  where status = 'active';
create index if not exists progress_goals_user_history_idx
  on public.progress_goals(user_id, created_at desc);
create unique index if not exists weight_logs_one_active_day_idx
  on public.weight_logs(user_id, log_date)
  where status = 'active';
create index if not exists weight_logs_user_history_idx
  on public.weight_logs(user_id, log_date desc, created_at desc);
create unique index if not exists body_measurements_one_active_day_idx
  on public.body_measurements(user_id, log_date)
  where status = 'active';
create index if not exists body_measurements_user_history_idx
  on public.body_measurements(user_id, log_date desc, created_at desc);

alter table public.progress_preferences enable row level security;
alter table public.progress_goals enable row level security;
alter table public.weight_logs enable row level security;
alter table public.body_measurements enable row level security;

drop policy if exists progress_preferences_select_own on public.progress_preferences;
create policy progress_preferences_select_own on public.progress_preferences
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists progress_preferences_insert_own on public.progress_preferences;
create policy progress_preferences_insert_own on public.progress_preferences
  for insert to authenticated
  with check ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists progress_preferences_update_own on public.progress_preferences;
create policy progress_preferences_update_own on public.progress_preferences
  for update to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()))
  with check ((select auth.uid()) is not null and user_id = (select auth.uid()));

drop policy if exists progress_goals_select_own on public.progress_goals;
create policy progress_goals_select_own on public.progress_goals
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists progress_goals_insert_own on public.progress_goals;
create policy progress_goals_insert_own on public.progress_goals
  for insert to authenticated
  with check ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists progress_goals_update_own on public.progress_goals;
create policy progress_goals_update_own on public.progress_goals
  for update to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()))
  with check ((select auth.uid()) is not null and user_id = (select auth.uid()));

drop policy if exists weight_logs_select_own on public.weight_logs;
create policy weight_logs_select_own on public.weight_logs
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists weight_logs_insert_own on public.weight_logs;
create policy weight_logs_insert_own on public.weight_logs
  for insert to authenticated
  with check ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists weight_logs_update_own on public.weight_logs;
create policy weight_logs_update_own on public.weight_logs
  for update to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()))
  with check ((select auth.uid()) is not null and user_id = (select auth.uid()));

drop policy if exists body_measurements_select_own on public.body_measurements;
create policy body_measurements_select_own on public.body_measurements
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists body_measurements_insert_own on public.body_measurements;
create policy body_measurements_insert_own on public.body_measurements
  for insert to authenticated
  with check ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists body_measurements_update_own on public.body_measurements;
create policy body_measurements_update_own on public.body_measurements
  for update to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()))
  with check ((select auth.uid()) is not null and user_id = (select auth.uid()));

create or replace function public.fmz_phase5_touch_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create or replace function public.fmz_phase5_sync_archive_state()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
begin
  if new.status = 'active' then
    new.archived_at := null;
  else
    new.archived_at := coalesce(new.archived_at, now());
  end if;
  return new;
end;
$$;

create or replace function public.fmz_phase5_has_full_progress_access(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path = pg_catalog, public, pg_temp
as $$
  select exists (
    select 1
    from public.entitlements e
    where e.user_id = p_user_id
      and e.status = 'active'
      and e.entitlement_code in ('pro', 'ai', 'personal_coaching')
      and e.starts_at <= now()
      and (e.ends_at is null or e.ends_at > now())
  );
$$;

create or replace function public.fmz_phase5_set_progress_timezone(p_timezone_name text)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_timezone text := btrim(p_timezone_name);
  v_row public.progress_preferences%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required' using errcode = '42501';
  end if;
  if v_timezone is null or not exists (
    select 1 from pg_catalog.pg_timezone_names tz where tz.name = v_timezone
  ) then
    raise exception 'valid IANA timezone required' using errcode = '22023';
  end if;

  insert into public.progress_preferences(user_id, timezone_name)
  values (v_user_id, v_timezone)
  on conflict (user_id) do update
    set timezone_name = excluded.timezone_name
  returning * into v_row;

  return to_jsonb(v_row);
end;
$$;

create or replace function public.fmz_phase5_save_progress_goal(
  p_goal_code text,
  p_baseline_weight_kg numeric,
  p_target_weight_kg numeric,
  p_target_date date,
  p_notes text,
  p_request_id uuid,
  p_expected_updated_at timestamptz default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_goal_code text := btrim(p_goal_code);
  v_notes text := nullif(btrim(p_notes), '');
  v_current public.progress_goals%rowtype;
  v_replay public.progress_goals%rowtype;
  v_created public.progress_goals%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required' using errcode = '42501';
  end if;
  if p_request_id is null then
    raise exception 'request_id required' using errcode = '22023';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('fmz_phase5_goal:' || v_user_id::text, 0)
  );

  select * into v_replay
  from public.progress_goals
  where user_id = v_user_id and request_id = p_request_id;
  if found then
    if v_replay.goal_code is distinct from v_goal_code
       or v_replay.baseline_weight_kg is distinct from p_baseline_weight_kg
       or v_replay.target_weight_kg is distinct from p_target_weight_kg
       or v_replay.target_date is distinct from p_target_date
       or v_replay.notes is distinct from v_notes then
      raise exception 'progress_request_conflict' using errcode = 'P0001';
    end if;
    return to_jsonb(v_replay);
  end if;

  select * into v_current
  from public.progress_goals
  where user_id = v_user_id and status = 'active'
  for update;

  if v_current.id is not null then
    if p_expected_updated_at is null or v_current.updated_at is distinct from p_expected_updated_at then
      raise exception 'progress_stale_conflict' using errcode = 'P0001';
    end if;
    update public.progress_goals
    set status = 'superseded', archived_at = now()
    where id = v_current.id;
  elsif p_expected_updated_at is not null then
    raise exception 'progress_stale_conflict' using errcode = 'P0001';
  end if;

  insert into public.progress_goals(
    id, user_id, goal_code, baseline_weight_kg, target_weight_kg,
    target_date, notes, status, request_id
  ) values (
    p_request_id, v_user_id, v_goal_code, p_baseline_weight_kg,
    p_target_weight_kg, p_target_date, v_notes, 'active', p_request_id
  ) returning * into v_created;

  return to_jsonb(v_created);
end;
$$;

create or replace function public.fmz_phase5_save_weight_log(
  p_log_date date,
  p_weight_kg numeric,
  p_notes text,
  p_timezone_name text,
  p_timezone_offset_minutes smallint,
  p_request_id uuid,
  p_expected_updated_at timestamptz default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_timezone text := btrim(p_timezone_name);
  v_notes text := nullif(btrim(p_notes), '');
  v_saved_timezone text;
  v_anchor timestamptz;
  v_expected_offset integer;
  v_today date;
  v_current public.weight_logs%rowtype;
  v_replay public.weight_logs%rowtype;
  v_created public.weight_logs%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required' using errcode = '42501';
  end if;
  if p_request_id is null or p_log_date is null then
    raise exception 'request_id and log_date required' using errcode = '22023';
  end if;
  if v_timezone is null or not exists (
    select 1 from pg_catalog.pg_timezone_names tz where tz.name = v_timezone
  ) then
    raise exception 'valid IANA timezone required' using errcode = '22023';
  end if;

  select timezone_name into v_saved_timezone
  from public.progress_preferences where user_id = v_user_id;
  if v_saved_timezone is null then
    insert into public.progress_preferences(user_id, timezone_name)
    values (v_user_id, v_timezone);
  elsif v_saved_timezone is distinct from v_timezone then
    raise exception 'timezone differs from Progress preference' using errcode = '22023';
  end if;

  v_today := (now() at time zone v_timezone)::date;
  if p_log_date > v_today then
    raise exception 'future Progress dates are not allowed' using errcode = '22023';
  end if;
  if not public.fmz_phase5_has_full_progress_access(v_user_id)
     and p_log_date < v_today - 29 then
    raise exception 'progress_history_locked' using errcode = '42501';
  end if;

  v_anchor := (p_log_date::timestamp + interval '12 hours') at time zone v_timezone;
  v_expected_offset := extract(epoch from (
    (v_anchor at time zone v_timezone) - (v_anchor at time zone 'UTC')
  ))::integer / 60;
  if p_timezone_offset_minutes is null or p_timezone_offset_minutes::integer <> v_expected_offset then
    raise exception 'timezone offset does not match Progress date' using errcode = '22023';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase5_weight:' || v_user_id::text || ':' || p_log_date::text, 0
    )
  );

  select * into v_replay from public.weight_logs
  where user_id = v_user_id and request_id = p_request_id;
  if found then
    if v_replay.log_date is distinct from p_log_date
       or v_replay.weight_kg is distinct from p_weight_kg
       or v_replay.notes is distinct from v_notes
       or v_replay.timezone_name is distinct from v_timezone
       or v_replay.timezone_offset_minutes is distinct from p_timezone_offset_minutes then
      raise exception 'progress_request_conflict' using errcode = 'P0001';
    end if;
    return to_jsonb(v_replay);
  end if;

  select * into v_current from public.weight_logs
  where user_id = v_user_id and log_date = p_log_date and status = 'active'
  for update;
  if v_current.id is not null then
    if p_expected_updated_at is null or v_current.updated_at is distinct from p_expected_updated_at then
      raise exception 'progress_stale_conflict' using errcode = 'P0001';
    end if;
    update public.weight_logs
    set status = 'superseded', archived_at = now()
    where id = v_current.id;
  elsif p_expected_updated_at is not null then
    raise exception 'progress_stale_conflict' using errcode = 'P0001';
  end if;

  insert into public.weight_logs(
    id, user_id, log_date, measured_at, timezone_name,
    timezone_offset_minutes, weight_kg, notes, source, status,
    request_id, supersedes_weight_log_id
  ) values (
    p_request_id, v_user_id, p_log_date, v_anchor, v_timezone,
    p_timezone_offset_minutes, p_weight_kg, v_notes, 'manual_phase5', 'active',
    p_request_id, v_current.id
  ) returning * into v_created;

  return to_jsonb(v_created);
end;
$$;

create or replace function public.fmz_phase5_save_body_measurement(
  p_log_date date,
  p_waist_cm numeric,
  p_chest_cm numeric,
  p_hips_cm numeric,
  p_upper_arm_left_cm numeric,
  p_upper_arm_right_cm numeric,
  p_thigh_left_cm numeric,
  p_thigh_right_cm numeric,
  p_notes text,
  p_timezone_name text,
  p_timezone_offset_minutes smallint,
  p_request_id uuid,
  p_expected_updated_at timestamptz default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_timezone text := btrim(p_timezone_name);
  v_notes text := nullif(btrim(p_notes), '');
  v_saved_timezone text;
  v_anchor timestamptz;
  v_expected_offset integer;
  v_today date;
  v_current public.body_measurements%rowtype;
  v_replay public.body_measurements%rowtype;
  v_created public.body_measurements%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required' using errcode = '42501';
  end if;
  if p_request_id is null or p_log_date is null then
    raise exception 'request_id and log_date required' using errcode = '22023';
  end if;
  if v_timezone is null or not exists (
    select 1 from pg_catalog.pg_timezone_names tz where tz.name = v_timezone
  ) then
    raise exception 'valid IANA timezone required' using errcode = '22023';
  end if;

  select timezone_name into v_saved_timezone
  from public.progress_preferences where user_id = v_user_id;
  if v_saved_timezone is null then
    insert into public.progress_preferences(user_id, timezone_name)
    values (v_user_id, v_timezone);
  elsif v_saved_timezone is distinct from v_timezone then
    raise exception 'timezone differs from Progress preference' using errcode = '22023';
  end if;

  v_today := (now() at time zone v_timezone)::date;
  if p_log_date > v_today then
    raise exception 'future Progress dates are not allowed' using errcode = '22023';
  end if;
  if not public.fmz_phase5_has_full_progress_access(v_user_id)
     and p_log_date < v_today - 29 then
    raise exception 'progress_history_locked' using errcode = '42501';
  end if;

  v_anchor := (p_log_date::timestamp + interval '12 hours') at time zone v_timezone;
  v_expected_offset := extract(epoch from (
    (v_anchor at time zone v_timezone) - (v_anchor at time zone 'UTC')
  ))::integer / 60;
  if p_timezone_offset_minutes is null or p_timezone_offset_minutes::integer <> v_expected_offset then
    raise exception 'timezone offset does not match Progress date' using errcode = '22023';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase5_measurement:' || v_user_id::text || ':' || p_log_date::text, 0
    )
  );

  select * into v_replay from public.body_measurements
  where user_id = v_user_id and request_id = p_request_id;
  if found then
    if v_replay.log_date is distinct from p_log_date
       or v_replay.waist_cm is distinct from p_waist_cm
       or v_replay.chest_cm is distinct from p_chest_cm
       or v_replay.hips_cm is distinct from p_hips_cm
       or v_replay.upper_arm_left_cm is distinct from p_upper_arm_left_cm
       or v_replay.upper_arm_right_cm is distinct from p_upper_arm_right_cm
       or v_replay.thigh_left_cm is distinct from p_thigh_left_cm
       or v_replay.thigh_right_cm is distinct from p_thigh_right_cm
       or v_replay.notes is distinct from v_notes
       or v_replay.timezone_name is distinct from v_timezone
       or v_replay.timezone_offset_minutes is distinct from p_timezone_offset_minutes then
      raise exception 'progress_request_conflict' using errcode = 'P0001';
    end if;
    return to_jsonb(v_replay);
  end if;

  select * into v_current from public.body_measurements
  where user_id = v_user_id and log_date = p_log_date and status = 'active'
  for update;
  if v_current.id is not null then
    if p_expected_updated_at is null or v_current.updated_at is distinct from p_expected_updated_at then
      raise exception 'progress_stale_conflict' using errcode = 'P0001';
    end if;
    update public.body_measurements
    set status = 'superseded', archived_at = now()
    where id = v_current.id;
  elsif p_expected_updated_at is not null then
    raise exception 'progress_stale_conflict' using errcode = 'P0001';
  end if;

  insert into public.body_measurements(
    id, user_id, log_date, measured_at, timezone_name, timezone_offset_minutes,
    waist_cm, chest_cm, hips_cm, upper_arm_left_cm, upper_arm_right_cm,
    thigh_left_cm, thigh_right_cm, notes, source, status, request_id,
    supersedes_body_measurement_id
  ) values (
    p_request_id, v_user_id, p_log_date, v_anchor, v_timezone,
    p_timezone_offset_minutes, p_waist_cm, p_chest_cm, p_hips_cm,
    p_upper_arm_left_cm, p_upper_arm_right_cm, p_thigh_left_cm,
    p_thigh_right_cm, v_notes, 'manual_phase5', 'active', p_request_id,
    v_current.id
  ) returning * into v_created;

  return to_jsonb(v_created);
end;
$$;

create or replace function public.fmz_phase5_archive_weight_log(
  p_weight_log_id uuid,
  p_expected_updated_at timestamptz
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_row public.weight_logs%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required' using errcode = '42501';
  end if;
  select * into v_row from public.weight_logs
  where id = p_weight_log_id and user_id = v_user_id
  for update;
  if v_row.id is null or v_row.status <> 'active'
     or p_expected_updated_at is null
     or v_row.updated_at is distinct from p_expected_updated_at then
    raise exception 'progress_stale_conflict' using errcode = 'P0001';
  end if;
  update public.weight_logs
  set status = 'archived', archived_at = now()
  where id = v_row.id
  returning * into v_row;
  return to_jsonb(v_row);
end;
$$;

create or replace function public.fmz_phase5_archive_body_measurement(
  p_body_measurement_id uuid,
  p_expected_updated_at timestamptz
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_row public.body_measurements%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required' using errcode = '42501';
  end if;
  select * into v_row from public.body_measurements
  where id = p_body_measurement_id and user_id = v_user_id
  for update;
  if v_row.id is null or v_row.status <> 'active'
     or p_expected_updated_at is null
     or v_row.updated_at is distinct from p_expected_updated_at then
    raise exception 'progress_stale_conflict' using errcode = 'P0001';
  end if;
  update public.body_measurements
  set status = 'archived', archived_at = now()
  where id = v_row.id
  returning * into v_row;
  return to_jsonb(v_row);
end;
$$;

create or replace function public.fmz_phase5_get_progress_dashboard(
  p_before_date date default null,
  p_requested_days integer default 90
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_timezone text;
  v_unit_system text;
  v_today date;
  v_end_date date;
  v_start_date date;
  v_requested_days integer := greatest(7, least(coalesce(p_requested_days, 90), 3650));
  v_has_full_access boolean;
  v_history_locked boolean := false;
  v_goal jsonb;
  v_weights jsonb;
  v_measurements jsonb;
  v_strength jsonb;
  v_consistency jsonb;
  v_recovery jsonb;
  v_nutrition jsonb;
  v_height_cm numeric;
  v_current_weight numeric;
  v_bmi numeric;
begin
  if v_user_id is null then
    raise exception 'authenticated user required' using errcode = '42501';
  end if;

  select coalesce(pp.timezone_name, np.timezone_name, 'UTC')
  into v_timezone
  from (select v_user_id as user_id) u
  left join public.progress_preferences pp on pp.user_id = u.user_id
  left join public.nutrition_preferences np on np.user_id = u.user_id;
  v_timezone := coalesce(v_timezone, 'UTC');

  select coalesce(us.unit_system, 'metric') into v_unit_system
  from public.user_settings us where us.user_id = v_user_id;
  v_unit_system := case when v_unit_system = 'imperial' then 'imperial' else 'metric' end;

  v_today := (now() at time zone v_timezone)::date;
  v_end_date := least(coalesce(p_before_date, v_today), v_today);
  v_has_full_access := public.fmz_phase5_has_full_progress_access(v_user_id);
  if v_has_full_access then
    v_start_date := v_end_date - (v_requested_days - 1);
  else
    v_start_date := v_today - 29;
    if v_end_date < v_start_date then
      v_history_locked := true;
      v_end_date := v_start_date - 1;
    end if;
  end if;

  select to_jsonb(g) into v_goal
  from public.progress_goals g
  where g.user_id = v_user_id and g.status = 'active';

  select coalesce(jsonb_agg(to_jsonb(rows) order by rows.log_date), '[]'::jsonb)
  into v_weights
  from (
    select
      w.id, w.log_date, w.weight_kg, w.notes, w.updated_at,
      round((
        select avg(recent.weight_kg)
        from (
          select w2.weight_kg
          from public.weight_logs w2
          where w2.user_id = v_user_id
            and w2.status = 'active'
            and w2.log_date <= w.log_date
          order by w2.log_date desc
          limit 7
        ) recent
      )::numeric, 2) as trend_kg
    from public.weight_logs w
    where w.user_id = v_user_id
      and w.status = 'active'
      and w.log_date between v_start_date and v_end_date
    order by w.log_date
  ) rows;

  select coalesce(jsonb_agg(to_jsonb(m) order by m.log_date), '[]'::jsonb)
  into v_measurements
  from (
    select id, log_date, waist_cm, chest_cm, hips_cm,
      upper_arm_left_cm, upper_arm_right_cm, thigh_left_cm, thigh_right_cm,
      notes, updated_at
    from public.body_measurements
    where user_id = v_user_id and status = 'active'
      and log_date between v_start_date and v_end_date
    order by log_date
  ) m;

  select coalesce(jsonb_agg(to_jsonb(s) order by s.estimated_one_rep_max_kg desc), '[]'::jsonb)
  into v_strength
  from (
    select
      coalesce(sl.exercise_id::text, sl.exercise_slug) as exercise_key,
      max(sl.exercise_name_snapshot) as exercise_name,
      max(sl.actual_weight) as max_weight_kg,
      max(sl.actual_reps) as max_reps,
      round(max(sl.actual_weight * (1 + sl.actual_reps::numeric / 30)), 2) as estimated_one_rep_max_kg,
      count(*)::integer as completed_sets,
      max(sl.completed_at) as last_completed_at
    from public.workout_set_logs sl
    join public.workout_sessions ws on ws.id = sl.workout_session_id
    where sl.user_id = v_user_id
      and ws.user_id = v_user_id
      and ws.status = 'completed'
      and sl.actual_weight is not null
      and sl.actual_weight > 0
      and sl.actual_reps is not null
      and sl.actual_reps > 0
      and (sl.completed_at at time zone v_timezone)::date between v_start_date and v_end_date
    group by coalesce(sl.exercise_id::text, sl.exercise_slug)
    order by estimated_one_rep_max_kg desc
    limit 8
  ) s;

  select jsonb_build_object(
    'completed_sessions', count(*)::integer,
    'last_7_days', count(*) filter (
      where (completed_at at time zone v_timezone)::date >= v_today - 6
    )::integer,
    'last_30_days', count(*) filter (
      where (completed_at at time zone v_timezone)::date >= v_today - 29
    )::integer,
    'first_completed_at', min(completed_at),
    'last_completed_at', max(completed_at)
  ) into v_consistency
  from public.workout_sessions
  where user_id = v_user_id and status = 'completed'
    and (completed_at at time zone v_timezone)::date between v_start_date and v_end_date;

  select jsonb_build_object(
    'days_logged', count(*)::integer,
    'average_sleep_hours', round(avg(sleep_hours)::numeric, 2),
    'average_steps', round(avg(steps)::numeric, 0),
    'average_recovery_feeling', round(avg(recovery_feeling)::numeric, 2)
  ) into v_recovery
  from public.recovery_logs
  where user_id = v_user_id and log_date between v_start_date and v_end_date;

  select jsonb_build_object(
    'days_logged', count(*)::integer,
    'average_energy_kcal', round(avg(day_energy)::numeric, 0),
    'average_protein_grams', round(avg(day_protein)::numeric, 1)
  ) into v_nutrition
  from (
    select l.log_date,
      sum(i.energy_kcal_snapshot) as day_energy,
      sum(i.protein_grams_snapshot) as day_protein
    from public.food_logs l
    join public.food_log_items i
      on i.food_log_id = l.id and i.user_id = l.user_id and i.status = 'active'
    where l.user_id = v_user_id and l.status = 'active'
      and l.log_date between v_start_date and v_end_date
    group by l.log_date
  ) nutrition_days;

  select u.height_cm into v_height_cm
  from public.user_onboarding u where u.user_id = v_user_id;
  select w.weight_kg into v_current_weight
  from public.weight_logs w
  where w.user_id = v_user_id and w.status = 'active'
  order by w.log_date desc limit 1;
  if v_height_cm between 100 and 250 and v_current_weight is not null then
    v_bmi := round(v_current_weight / power(v_height_cm / 100, 2), 1);
  end if;

  return jsonb_build_object(
    'access', case when v_has_full_access then 'full' else 'free' end,
    'history_window_days', case when v_has_full_access then null else 30 end,
    'history_locked', v_history_locked,
    'timezone_name', v_timezone,
    'unit_system', v_unit_system,
    'today', v_today,
    'window_start', v_start_date,
    'window_end', v_end_date,
    'goal', v_goal,
    'weights', v_weights,
    'measurements', v_measurements,
    'strength', v_strength,
    'consistency', coalesce(v_consistency, '{}'::jsonb),
    'recovery_context', coalesce(v_recovery, '{}'::jsonb),
    'nutrition_context', coalesce(v_nutrition, '{}'::jsonb),
    'bmi_context', v_bmi,
    'running', jsonb_build_object(
      'authoritative_source_available', false,
      'activities', '[]'::jsonb
    )
  );
end;
$$;

drop trigger if exists progress_preferences_touch_updated_at on public.progress_preferences;
create trigger progress_preferences_touch_updated_at
before update on public.progress_preferences
for each row execute function public.fmz_phase5_touch_updated_at();

drop trigger if exists progress_goals_sync_archive_state on public.progress_goals;
create trigger progress_goals_sync_archive_state
before insert or update on public.progress_goals
for each row execute function public.fmz_phase5_sync_archive_state();
drop trigger if exists progress_goals_touch_updated_at on public.progress_goals;
create trigger progress_goals_touch_updated_at
before update on public.progress_goals
for each row execute function public.fmz_phase5_touch_updated_at();

drop trigger if exists weight_logs_sync_archive_state on public.weight_logs;
create trigger weight_logs_sync_archive_state
before insert or update on public.weight_logs
for each row execute function public.fmz_phase5_sync_archive_state();
drop trigger if exists weight_logs_touch_updated_at on public.weight_logs;
create trigger weight_logs_touch_updated_at
before update on public.weight_logs
for each row execute function public.fmz_phase5_touch_updated_at();

drop trigger if exists body_measurements_sync_archive_state on public.body_measurements;
create trigger body_measurements_sync_archive_state
before insert or update on public.body_measurements
for each row execute function public.fmz_phase5_sync_archive_state();
drop trigger if exists body_measurements_touch_updated_at on public.body_measurements;
create trigger body_measurements_touch_updated_at
before update on public.body_measurements
for each row execute function public.fmz_phase5_touch_updated_at();

revoke all on table public.progress_preferences from public, anon, authenticated;
revoke all on table public.progress_goals from public, anon, authenticated;
revoke all on table public.weight_logs from public, anon, authenticated;
revoke all on table public.body_measurements from public, anon, authenticated;

revoke all on function public.fmz_phase5_touch_updated_at() from public, anon, authenticated;
revoke all on function public.fmz_phase5_sync_archive_state() from public, anon, authenticated;
revoke all on function public.fmz_phase5_has_full_progress_access(uuid) from public, anon, authenticated;
revoke all on function public.fmz_phase5_set_progress_timezone(text) from public, anon, authenticated;
revoke all on function public.fmz_phase5_save_progress_goal(text,numeric,numeric,date,text,uuid,timestamptz) from public, anon, authenticated;
revoke all on function public.fmz_phase5_save_weight_log(date,numeric,text,text,smallint,uuid,timestamptz) from public, anon, authenticated;
revoke all on function public.fmz_phase5_save_body_measurement(date,numeric,numeric,numeric,numeric,numeric,numeric,numeric,text,text,smallint,uuid,timestamptz) from public, anon, authenticated;
revoke all on function public.fmz_phase5_archive_weight_log(uuid,timestamptz) from public, anon, authenticated;
revoke all on function public.fmz_phase5_archive_body_measurement(uuid,timestamptz) from public, anon, authenticated;
revoke all on function public.fmz_phase5_get_progress_dashboard(date,integer) from public, anon, authenticated;

grant execute on function public.fmz_phase5_set_progress_timezone(text) to authenticated;
grant execute on function public.fmz_phase5_save_progress_goal(text,numeric,numeric,date,text,uuid,timestamptz) to authenticated;
grant execute on function public.fmz_phase5_save_weight_log(date,numeric,text,text,smallint,uuid,timestamptz) to authenticated;
grant execute on function public.fmz_phase5_save_body_measurement(date,numeric,numeric,numeric,numeric,numeric,numeric,numeric,text,text,smallint,uuid,timestamptz) to authenticated;
grant execute on function public.fmz_phase5_archive_weight_log(uuid,timestamptz) to authenticated;
grant execute on function public.fmz_phase5_archive_body_measurement(uuid,timestamptz) to authenticated;
grant execute on function public.fmz_phase5_get_progress_dashboard(date,integer) to authenticated;

commit;
