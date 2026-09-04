-- FitMetZorge legacy Phase 1-3 source baseline.
-- STAGING ONLY: mokxyyullfhkfalopbzd
--
-- Forward-only migration reconciliation baseline for empty database rebuilds.
-- Reconstructed from live read-only schema metadata, historical status docs and
-- frozen verifier contracts after the original Phase 1-3 SQL artifacts could not
-- be recovered from Git history. This migration creates schema/function/policy
-- contracts only: no seed data, no member-data backfill and no history repair.
-- Production is forbidden.

begin;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  role text not null,
  name text not null default '',
  email text not null default '',
  trainer_id uuid references public.profiles(id) on delete set null,
  client_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint profiles_role_check check (role in ('trainer', 'client'))
);

create table if not exists public.coach_workspaces (
  trainer_id uuid primary key references public.profiles(id) on delete cascade,
  state jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists public.user_settings (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  language text not null default 'nl',
  country text not null default 'Nederland',
  unit_system text not null default 'metric',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint user_settings_language_check check (language in ('nl', 'en', 'de')),
  constraint user_settings_unit_system_check check (unit_system in ('metric', 'imperial'))
);

create table if not exists public.user_onboarding (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  client_id text,
  first_name text,
  last_name text,
  display_name text,
  age integer,
  height_cm numeric(6,2),
  weight_kg numeric(6,2),
  gender text,
  fitness_goal text,
  goal_direction text,
  target_weight_kg numeric(6,2),
  training_experience text,
  available_days integer,
  nutrition_preferences text,
  practical_constraints text,
  bmi numeric(5,2),
  goal_safety_status text not null default 'needs_input',
  goal_safety_note text,
  goal_timeline_weeks integer,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint user_onboarding_age_check check (age is null or (age >= 18 and age <= 120)),
  constraint user_onboarding_height_cm_check check (height_cm is null or (height_cm >= 100 and height_cm <= 250)),
  constraint user_onboarding_weight_kg_check check (weight_kg is null or (weight_kg >= 30 and weight_kg <= 300)),
  constraint user_onboarding_target_weight_kg_check check (target_weight_kg is null or (target_weight_kg >= 30 and target_weight_kg <= 300)),
  constraint user_onboarding_gender_check check (
    gender is null or gender in ('female', 'male', 'non_binary', 'prefer_not_to_say', 'not_relevant')
  ),
  constraint user_onboarding_goal_direction_check check (
    goal_direction is null or goal_direction in ('lose_weight', 'gain_muscle', 'recomposition', 'fitness', 'health', 'other')
  ),
  constraint user_onboarding_available_days_check check (available_days is null or (available_days >= 0 and available_days <= 7)),
  constraint user_onboarding_goal_safety_status_check check (goal_safety_status in ('needs_input', 'realistic_foundation', 'needs_review')),
  constraint user_onboarding_goal_timeline_weeks_check check (goal_timeline_weeks is null or goal_timeline_weeks >= 0)
);

create table if not exists public.entitlements (
  user_id uuid not null references public.profiles(id) on delete cascade,
  entitlement_code text not null,
  status text not null default 'active',
  source text not null default 'phase1_default',
  starts_at timestamptz not null default now(),
  ends_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint entitlements_pkey primary key (user_id, entitlement_code, source),
  constraint entitlements_entitlement_code_check check (entitlement_code in ('free', 'pro', 'ai', 'personal_coaching')),
  constraint entitlements_status_check check (status in ('active', 'inactive', 'expired'))
);

create table if not exists public.recovery_logs (
  user_id uuid not null references public.profiles(id) on delete cascade,
  log_date date not null,
  sleep_hours numeric(4,2),
  sleep_quality integer,
  steps integer,
  wellbeing_energy integer,
  wellbeing_stress integer,
  wellbeing_motivation integer,
  wellbeing_mood text,
  recovery_feeling integer,
  recovery_note text,
  training_load_status text not null default 'unknown',
  training_load_source text not null default 'phase2_placeholder',
  source text not null default 'manual_phase2',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint recovery_logs_pkey primary key (user_id, log_date),
  constraint recovery_logs_sleep_hours_check check (sleep_hours is null or (sleep_hours >= 0 and sleep_hours <= 24)),
  constraint recovery_logs_sleep_quality_check check (sleep_quality is null or (sleep_quality >= 1 and sleep_quality <= 10)),
  constraint recovery_logs_steps_check check (steps is null or (steps >= 0 and steps <= 200000)),
  constraint recovery_logs_wellbeing_energy_check check (wellbeing_energy is null or (wellbeing_energy >= 1 and wellbeing_energy <= 10)),
  constraint recovery_logs_wellbeing_stress_check check (wellbeing_stress is null or (wellbeing_stress >= 1 and wellbeing_stress <= 10)),
  constraint recovery_logs_wellbeing_motivation_check check (wellbeing_motivation is null or (wellbeing_motivation >= 1 and wellbeing_motivation <= 10)),
  constraint recovery_logs_wellbeing_mood_check check (wellbeing_mood is null or char_length(wellbeing_mood) <= 60),
  constraint recovery_logs_recovery_feeling_check check (recovery_feeling is null or (recovery_feeling >= 1 and recovery_feeling <= 10)),
  constraint recovery_logs_recovery_note_check check (recovery_note is null or char_length(recovery_note) <= 500),
  constraint recovery_logs_training_load_status_check check (training_load_status in ('unknown', 'rest', 'light', 'moderate', 'heavy')),
  constraint recovery_logs_training_load_source_check check (training_load_source in ('phase2_placeholder', 'legacy_attendance')),
  constraint recovery_logs_source_check check (source in ('manual_phase2', 'legacy_bridge'))
);

create table if not exists public.exercises (
  id uuid primary key,
  canonical_slug text not null unique,
  canonical_name text not null,
  name_en text not null,
  name_de text,
  primary_muscle text not null,
  secondary_muscles text[] not null default '{}'::text[],
  body_region text not null,
  equipment text not null,
  equipment_group text not null,
  movement_pattern text not null,
  instructions_nl text,
  instructions_en text not null,
  instructions_de text,
  animation_url text,
  legacy_animation_url text,
  animation_source text not null default 'placeholder',
  animation_status text not null default 'placeholder',
  source_reference text,
  metadata jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint exercises_canonical_slug_check check (canonical_slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  constraint exercises_canonical_name_check check (char_length(canonical_name) >= 1 and char_length(canonical_name) <= 180),
  constraint exercises_name_en_check check (char_length(name_en) >= 1 and char_length(name_en) <= 180),
  constraint exercises_name_de_check check (name_de is null or (char_length(name_de) >= 1 and char_length(name_de) <= 180)),
  constraint exercises_primary_muscle_check check (primary_muscle in (
    'chest', 'back', 'shoulders', 'biceps', 'triceps', 'quadriceps',
    'hamstrings', 'glutes', 'calves', 'core', 'forearms', 'trapezius',
    'adductors', 'abductors', 'lower-back', 'full-body', 'neck', 'hip-flexors'
  )),
  constraint exercises_secondary_muscles_check check (secondary_muscles <@ array[
    'chest', 'back', 'shoulders', 'biceps', 'triceps', 'quadriceps',
    'hamstrings', 'glutes', 'calves', 'core', 'forearms', 'trapezius',
    'adductors', 'abductors', 'lower-back', 'full-body', 'neck', 'hip-flexors'
  ]),
  constraint exercises_body_region_check check (body_region in ('upper', 'lower', 'core', 'posterior', 'full')),
  constraint exercises_equipment_check check (char_length(equipment) >= 1 and char_length(equipment) <= 100),
  constraint exercises_equipment_group_check check (equipment_group in (
    'machine', 'cable', 'dumbbell', 'barbell', 'smith-machine', 'bodyweight',
    'ez-bar', 'kettlebell', 'resistance-band', 'suspension', 'landmine',
    'plate', 'other'
  )),
  constraint exercises_movement_pattern_check check (char_length(movement_pattern) >= 1 and char_length(movement_pattern) <= 80),
  constraint exercises_instructions_nl_check check (instructions_nl is null or (char_length(instructions_nl) >= 1 and char_length(instructions_nl) <= 1200)),
  constraint exercises_instructions_en_check check (char_length(instructions_en) >= 1 and char_length(instructions_en) <= 1200),
  constraint exercises_instructions_de_check check (instructions_de is null or (char_length(instructions_de) >= 1 and char_length(instructions_de) <= 1200)),
  constraint exercises_animation_url_check check (animation_url is null or char_length(animation_url) <= 600),
  constraint exercises_legacy_animation_url_check check (legacy_animation_url is null or char_length(legacy_animation_url) <= 600),
  constraint exercises_animation_source_check check (animation_source in ('placeholder', 'legacy', 'youri_avatar', 'external_reviewed')),
  constraint exercises_animation_status_check check (animation_status in ('placeholder', 'legacy', 'youri_avatar_pending', 'youri_avatar_ready')),
  constraint exercises_source_reference_check check (source_reference is null or char_length(source_reference) <= 240)
);

create table if not exists public.training_plans (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  title text not null,
  status text not null default 'active',
  source text not null default 'phase3_client',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint training_plans_title_check check (char_length(title) >= 1 and char_length(title) <= 140),
  constraint training_plans_status_check check (status in ('active', 'archived', 'inactive')),
  constraint training_plans_source_check check (source = 'phase3_client')
);

create table if not exists public.training_plan_days (
  id uuid primary key,
  training_plan_id uuid not null references public.training_plans(id) on delete cascade,
  day_label text not null,
  day_order integer not null,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  status text not null default 'active',
  archived_at timestamptz,
  constraint training_plan_days_day_label_check check (char_length(day_label) >= 1 and char_length(day_label) <= 40),
  constraint training_plan_days_day_order_check check (day_order >= 0 and day_order <= 20),
  constraint training_plan_days_notes_check check (notes is null or char_length(notes) <= 500),
  constraint training_plan_days_status_check check (status in ('active', 'archived', 'inactive'))
);

create table if not exists public.training_plan_exercises (
  id uuid primary key,
  training_plan_day_id uuid not null references public.training_plan_days(id) on delete cascade,
  exercise_slug text not null,
  exercise_name_snapshot text not null,
  exercise_order integer not null,
  target_sets integer not null default 3,
  target_reps text not null default '8-10',
  target_weight numeric(7,2),
  target_rir integer,
  target_rpe numeric(3,1),
  rest_seconds integer not null default 90,
  tempo text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  status text not null default 'active',
  archived_at timestamptz,
  exercise_id uuid references public.exercises(id) on delete set null,
  constraint training_plan_exercises_exercise_slug_check check (char_length(exercise_slug) >= 1 and char_length(exercise_slug) <= 100),
  constraint training_plan_exercises_exercise_name_snapshot_check check (char_length(exercise_name_snapshot) >= 1 and char_length(exercise_name_snapshot) <= 160),
  constraint training_plan_exercises_exercise_order_check check (exercise_order >= 0 and exercise_order <= 200),
  constraint training_plan_exercises_target_sets_check check (target_sets >= 1 and target_sets <= 20),
  constraint training_plan_exercises_target_reps_check check (char_length(target_reps) >= 1 and char_length(target_reps) <= 40),
  constraint training_plan_exercises_target_weight_check check (target_weight is null or (target_weight >= 0 and target_weight <= 1000)),
  constraint training_plan_exercises_target_rir_check check (target_rir is null or (target_rir >= 0 and target_rir <= 10)),
  constraint training_plan_exercises_target_rpe_check check (target_rpe is null or (target_rpe >= 1 and target_rpe <= 10)),
  constraint training_plan_exercises_rest_seconds_check check (rest_seconds >= 0 and rest_seconds <= 3600),
  constraint training_plan_exercises_tempo_check check (tempo is null or char_length(tempo) <= 40),
  constraint training_plan_exercises_notes_check check (notes is null or char_length(notes) <= 500),
  constraint training_plan_exercises_status_check check (status in ('active', 'archived'))
);

create table if not exists public.workout_sessions (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  training_plan_id uuid references public.training_plans(id) on delete set null,
  training_plan_day_id uuid references public.training_plan_days(id) on delete set null,
  local_session_key text not null,
  status text not null default 'active',
  title_snapshot text not null,
  day_label text,
  started_at timestamptz not null default now(),
  paused_at timestamptz,
  resumed_at timestamptz,
  completed_at timestamptz,
  source text not null default 'phase3_client',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint workout_sessions_user_id_local_session_key_key unique (user_id, local_session_key),
  constraint workout_sessions_local_session_key_check check (char_length(local_session_key) >= 8 and char_length(local_session_key) <= 160),
  constraint workout_sessions_status_check check (status in ('active', 'paused', 'completed', 'cancelled')),
  constraint workout_sessions_title_snapshot_check check (char_length(title_snapshot) >= 1 and char_length(title_snapshot) <= 180),
  constraint workout_sessions_day_label_check check (day_label is null or char_length(day_label) <= 40),
  constraint workout_sessions_source_check check (source in ('phase3_client', 'legacy_bridge')),
  constraint workout_sessions_check check ((status = 'completed' and completed_at is not null) or status <> 'completed')
);

create table if not exists public.workout_set_logs (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  workout_session_id uuid not null references public.workout_sessions(id) on delete cascade,
  training_plan_exercise_id uuid references public.training_plan_exercises(id) on delete set null,
  planned_exercise_key text not null,
  exercise_slug text not null,
  exercise_name_snapshot text not null,
  set_index integer not null,
  target_reps text,
  target_weight numeric(7,2),
  actual_reps integer,
  actual_weight numeric(7,2),
  rir integer,
  rpe numeric(3,1),
  notes text,
  completed_at timestamptz not null default now(),
  source text not null default 'phase3_client',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  exercise_id uuid references public.exercises(id) on delete set null,
  constraint workout_set_logs_workout_session_id_planned_exercise_key_se_key unique (workout_session_id, planned_exercise_key, set_index),
  constraint workout_set_logs_planned_exercise_key_check check (char_length(planned_exercise_key) >= 1 and char_length(planned_exercise_key) <= 160),
  constraint workout_set_logs_exercise_slug_check check (char_length(exercise_slug) >= 1 and char_length(exercise_slug) <= 100),
  constraint workout_set_logs_exercise_name_snapshot_check check (char_length(exercise_name_snapshot) >= 1 and char_length(exercise_name_snapshot) <= 160),
  constraint workout_set_logs_set_index_check check (set_index >= 1 and set_index <= 50),
  constraint workout_set_logs_target_reps_check check (target_reps is null or char_length(target_reps) <= 40),
  constraint workout_set_logs_target_weight_check check (target_weight is null or (target_weight >= 0 and target_weight <= 1000)),
  constraint workout_set_logs_actual_reps_check check (actual_reps is null or (actual_reps >= 0 and actual_reps <= 1000)),
  constraint workout_set_logs_actual_weight_check check (actual_weight is null or (actual_weight >= 0 and actual_weight <= 1000)),
  constraint workout_set_logs_rir_check check (rir is null or (rir >= 0 and rir <= 10)),
  constraint workout_set_logs_rpe_check check (rpe is null or (rpe >= 1 and rpe <= 10)),
  constraint workout_set_logs_notes_check check (notes is null or char_length(notes) <= 500),
  constraint workout_set_logs_source_check check (source in ('phase3_client', 'legacy_bridge', 'offline_recovery'))
);

create index if not exists profiles_role_idx on public.profiles(role);
create index if not exists profiles_trainer_id_idx on public.profiles(trainer_id);
create index if not exists coach_workspaces_updated_at_idx on public.coach_workspaces(updated_at);
create index if not exists user_settings_language_idx on public.user_settings(language);
create index if not exists user_onboarding_goal_direction_idx on public.user_onboarding(goal_direction);
create index if not exists entitlements_code_status_idx on public.entitlements(entitlement_code, status);
create index if not exists entitlements_user_status_idx on public.entitlements(user_id, status);
create index if not exists recovery_logs_log_date_idx on public.recovery_logs(log_date);
create index if not exists recovery_logs_training_load_idx on public.recovery_logs(training_load_status);
create index if not exists exercises_active_filter_idx on public.exercises(is_active, primary_muscle, equipment_group, movement_pattern);
create index if not exists exercises_body_region_idx on public.exercises(body_region) where is_active = true;
create index if not exists exercises_name_en_lower_idx on public.exercises(lower(name_en)) where is_active = true;
create index if not exists exercises_name_de_lower_idx on public.exercises(lower(name_de)) where is_active = true and name_de is not null;
create index if not exists exercises_secondary_muscles_gin_idx on public.exercises using gin (secondary_muscles);
create index if not exists training_plans_user_status_idx on public.training_plans(user_id, status);
create unique index if not exists training_plan_days_active_plan_order_uidx
  on public.training_plan_days(training_plan_id, day_order) where status = 'active';
create index if not exists training_plan_days_plan_idx on public.training_plan_days(training_plan_id, day_order);
create index if not exists training_plan_days_status_plan_idx on public.training_plan_days(status, training_plan_id);
create unique index if not exists training_plan_exercises_active_day_order_uidx
  on public.training_plan_exercises(training_plan_day_id, exercise_order) where status = 'active';
create index if not exists training_plan_exercises_day_idx on public.training_plan_exercises(training_plan_day_id, exercise_order);
create index if not exists training_plan_exercises_exercise_id_idx
  on public.training_plan_exercises(exercise_id) where exercise_id is not null;
create index if not exists training_plan_exercises_status_day_idx
  on public.training_plan_exercises(status, training_plan_day_id, exercise_order);
create unique index if not exists workout_sessions_one_open_per_user_idx
  on public.workout_sessions(user_id) where status in ('active', 'paused');
create index if not exists workout_sessions_started_at_idx on public.workout_sessions(started_at);
create index if not exists workout_sessions_user_status_idx on public.workout_sessions(user_id, status);
create index if not exists workout_set_logs_session_idx on public.workout_set_logs(workout_session_id);
create index if not exists workout_set_logs_user_exercise_idx on public.workout_set_logs(user_id, exercise_slug);
create index if not exists workout_set_logs_user_exercise_id_idx
  on public.workout_set_logs(user_id, exercise_id, completed_at desc) where exercise_id is not null;

create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $function$
begin
  new.updated_at = now();
  return new;
end;
$function$;

create or replace function public.fmz_current_profile_role()
returns text
language sql
stable
security definer
set search_path = pg_catalog, pg_temp
as $function$
  select p.role
  from public.profiles p
  where p.id = auth.uid()
  limit 1
$function$;

create or replace function public.fmz_current_profile_trainer_id()
returns uuid
language sql
stable
security definer
set search_path = pg_catalog, pg_temp
as $function$
  select p.trainer_id
  from public.profiles p
  where p.id = auth.uid()
  limit 1
$function$;

create or replace function public.fmz_is_trainer()
returns boolean
language sql
stable
security definer
set search_path = pg_catalog, pg_temp
as $function$
  select coalesce(public.fmz_current_profile_role() = 'trainer', false)
$function$;

create or replace function public.fmz_can_select_profile(
  target_id uuid,
  target_role text,
  target_trainer_id uuid
)
returns boolean
language plpgsql
stable
security definer
set search_path = pg_catalog, pg_temp
as $function$
declare
  current_user_id uuid := auth.uid();
  v_current_role text;
  current_trainer_id uuid;
begin
  if current_user_id is null then
    return false;
  end if;

  if target_id = current_user_id then
    return true;
  end if;

  v_current_role := public.fmz_current_profile_role();
  current_trainer_id := public.fmz_current_profile_trainer_id();

  if v_current_role = 'trainer' then
    return target_role = 'client'
      and target_trainer_id = current_user_id;
  end if;

  if v_current_role = 'client' then
    return target_role = 'trainer'
      and target_id = current_trainer_id;
  end if;

  return false;
end;
$function$;

create or replace function public.fmz_can_access_workspace(target_trainer_id uuid)
returns boolean
language plpgsql
stable
security definer
set search_path = pg_catalog, pg_temp
as $function$
declare
  current_user_id uuid := auth.uid();
  v_current_role text;
  current_trainer_id uuid;
begin
  if current_user_id is null or target_trainer_id is null then
    return false;
  end if;

  v_current_role := public.fmz_current_profile_role();
  current_trainer_id := public.fmz_current_profile_trainer_id();

  if v_current_role = 'trainer' then
    return target_trainer_id = current_user_id;
  end if;

  if v_current_role = 'client' then
    return target_trainer_id = current_trainer_id;
  end if;

  return false;
end;
$function$;

create or replace function public.fmz_phase1_upsert_account_foundation(
  p_role text default 'client',
  p_name text default null,
  p_language text default 'nl',
  p_onboarding jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $function$
declare
  v_user_id uuid := auth.uid();
  v_email text;
  -- p_role is kept for API compatibility only. It is never an authority source.
  v_name text := nullif(trim(coalesce(p_name, '')), '');
  v_language text := case when p_language in ('nl', 'en', 'de') then p_language else 'nl' end;
  v_onboarding jsonb := coalesce(p_onboarding, '{}'::jsonb);
  v_existing_profile public.profiles;
  v_profile public.profiles;
  v_age integer := null;
  v_height numeric := null;
  v_weight numeric := null;
  v_target_weight numeric := null;
  v_available_days integer := null;
  v_bmi numeric := null;
  v_goal_direction text := null;
  v_goal_text text := null;
  v_goal_safety_status text := 'needs_input';
  v_goal_safety_note text := 'Vul je huidige situatie en einddoel in. Een weektempo wordt niet vrij gekozen.';
  v_goal_timeline_weeks integer := null;
  v_delta numeric;
  v_abs_delta numeric;
  v_safe_weekly_change numeric;
  v_entitlements jsonb;
  v_age_input text;
  v_height_input text;
  v_weight_input text;
  v_target_weight_input text;
  v_available_days_input text;
begin
  if v_user_id is null then
    raise exception 'Authenticated user is required.';
  end if;

  select lower(trim(email))
  into v_email
  from auth.users
  where id = v_user_id;

  select *
  into v_existing_profile
  from public.profiles
  where id = v_user_id;

  v_age_input := nullif(v_onboarding ->> 'age', '');
  v_height_input := nullif(v_onboarding ->> 'height_cm', '');
  v_weight_input := nullif(v_onboarding ->> 'weight_kg', '');
  v_target_weight_input := nullif(v_onboarding ->> 'target_weight_kg', '');
  v_available_days_input := nullif(v_onboarding ->> 'available_days', '');
  v_goal_direction := nullif(v_onboarding ->> 'goal_direction', '');
  v_goal_text := nullif(trim(coalesce(v_onboarding ->> 'fitness_goal', '')), '');

  if v_age_input is not null then
    if v_age_input !~ '^[0-9]+$' then
      raise exception 'Leeftijd moet numeriek zijn.';
    end if;
    v_age := v_age_input::integer;
  end if;

  if v_height_input is not null then
    if v_height_input !~ '^[0-9]+(\.[0-9]+)?$' then
      raise exception 'Lengte moet numeriek zijn.';
    end if;
    v_height := v_height_input::numeric;
  end if;

  if v_weight_input is not null then
    if v_weight_input !~ '^[0-9]+(\.[0-9]+)?$' then
      raise exception 'Gewicht moet numeriek zijn.';
    end if;
    v_weight := v_weight_input::numeric;
  end if;

  if v_target_weight_input is not null then
    if v_target_weight_input !~ '^[0-9]+(\.[0-9]+)?$' then
      raise exception 'Doelgewicht moet numeriek zijn.';
    end if;
    v_target_weight := v_target_weight_input::numeric;
  end if;

  if v_available_days_input is not null then
    if v_available_days_input !~ '^[0-9]+$' then
      raise exception 'Beschikbare dagen moet numeriek zijn.';
    end if;
    v_available_days := v_available_days_input::integer;
  end if;

  if v_age is not null and (v_age < 18 or v_age > 120) then
    raise exception 'FitMetZorge V1 is 18+. Controleer de leeftijd.';
  end if;

  if v_height is not null and (v_height < 100 or v_height > 250) then
    raise exception 'Lengte valt buiten de veilige invoergrenzen.';
  end if;

  if v_weight is not null and (v_weight < 30 or v_weight > 300) then
    raise exception 'Gewicht valt buiten de veilige invoergrenzen.';
  end if;

  if v_target_weight is not null and (v_target_weight < 30 or v_target_weight > 300) then
    raise exception 'Doelgewicht valt buiten de veilige invoergrenzen.';
  end if;

  if v_available_days is not null and (v_available_days < 0 or v_available_days > 7) then
    raise exception 'Beschikbare dagen moet tussen 0 en 7 liggen.';
  end if;

  if v_height is not null and v_weight is not null and v_height > 0 then
    v_bmi := round(v_weight / power(v_height / 100, 2), 2);
  end if;

  if v_goal_direction in ('fitness', 'health', 'other', 'recomposition') and v_goal_text is not null then
    v_goal_safety_status := 'realistic_foundation';
    v_goal_safety_note := 'Doel opgeslagen zonder vrij weektempo. Verdere fasering komt in latere coachingstappen.';
  elsif v_goal_direction in ('lose_weight', 'gain_muscle') and v_weight is not null and v_target_weight is not null then
    v_delta := v_target_weight - v_weight;
    v_abs_delta := abs(v_delta);
    v_safe_weekly_change := case
      when v_goal_direction = 'gain_muscle' then greatest(0.15, v_weight * 0.0025)
      else greatest(0.25, v_weight * 0.005)
    end;
    v_goal_timeline_weeks := ceil(v_abs_delta / v_safe_weekly_change);

    if v_goal_direction = 'lose_weight' and v_delta >= 0 then
      v_goal_safety_status := 'needs_review';
      v_goal_safety_note := 'Doelrichting is afvallen, maar het doelgewicht ligt niet lager dan het huidige gewicht.';
    elsif v_goal_direction = 'gain_muscle' and v_delta <= 0 then
      v_goal_safety_status := 'needs_review';
      v_goal_safety_note := 'Doelrichting is spiermassa opbouwen, maar het doelgewicht ligt niet hoger dan het huidige gewicht.';
    elsif v_abs_delta > (v_weight * 0.35) then
      v_goal_safety_status := 'needs_review';
      v_goal_safety_note := 'Dit doel vraagt waarschijnlijk om extra fasering en latere bewuste beoordeling.';
    else
      v_goal_safety_status := 'realistic_foundation';
      v_goal_safety_note := 'Realistische basisrichting. Vrij weektempo wordt niet opgeslagen.';
    end if;
  end if;

  if v_existing_profile.id is null then
    insert into public.profiles (
      id,
      role,
      name,
      email,
      trainer_id,
      client_id
    )
    values (
      v_user_id,
      'client',
      coalesce(v_name, nullif(split_part(coalesce(v_email, ''), '@', 1), ''), 'Gebruiker'),
      coalesce(v_email, ''),
      null,
      null
    )
    on conflict (id) do update
    set
      name = coalesce(v_name, nullif(public.profiles.name, ''), nullif(split_part(coalesce(v_email, ''), '@', 1), ''), 'Gebruiker'),
      email = coalesce(nullif(v_email, ''), public.profiles.email),
      updated_at = now()
    returning * into v_profile;
  else
    update public.profiles
    set
      name = coalesce(v_name, nullif(public.profiles.name, ''), nullif(split_part(coalesce(v_email, ''), '@', 1), ''), 'Gebruiker'),
      email = coalesce(nullif(v_email, ''), public.profiles.email),
      updated_at = now()
    where id = v_user_id
    returning * into v_profile;
  end if;

  if v_existing_profile.id is not null
    and v_existing_profile.role = 'trainer'
    and v_profile.role = 'trainer'
  then
    insert into public.coach_workspaces (
      trainer_id,
      state,
      updated_at
    )
    values (
      v_profile.id,
      '{}'::jsonb,
      now()
    )
    on conflict (trainer_id) do nothing;
  end if;

  insert into public.user_settings (
    user_id,
    language,
    country,
    unit_system
  )
  values (
    v_profile.id,
    v_language,
    coalesce(nullif(trim(v_onboarding ->> 'country'), ''), 'Nederland'),
    'metric'
  )
  on conflict (user_id) do update
  set
    language = excluded.language,
    country = excluded.country,
    unit_system = excluded.unit_system,
    updated_at = now();

  insert into public.user_onboarding (
    user_id,
    client_id,
    first_name,
    last_name,
    display_name,
    age,
    height_cm,
    weight_kg,
    gender,
    fitness_goal,
    goal_direction,
    target_weight_kg,
    training_experience,
    available_days,
    nutrition_preferences,
    practical_constraints,
    bmi,
    goal_safety_status,
    goal_safety_note,
    goal_timeline_weeks,
    completed_at
  )
  values (
    v_profile.id,
    -- Relationship identifiers are not accepted from client-side onboarding JSON.
    null,
    nullif(trim(coalesce(v_onboarding ->> 'first_name', '')), ''),
    nullif(trim(coalesce(v_onboarding ->> 'last_name', '')), ''),
    v_profile.name,
    v_age,
    v_height,
    v_weight,
    nullif(v_onboarding ->> 'gender', ''),
    v_goal_text,
    v_goal_direction,
    v_target_weight,
    nullif(trim(coalesce(v_onboarding ->> 'training_experience', '')), ''),
    v_available_days,
    nullif(trim(coalesce(v_onboarding ->> 'nutrition_preferences', '')), ''),
    nullif(trim(coalesce(v_onboarding ->> 'practical_constraints', '')), ''),
    v_bmi,
    v_goal_safety_status,
    v_goal_safety_note,
    v_goal_timeline_weeks,
    case
      when v_age is not null
        and v_height is not null
        and v_weight is not null
        and nullif(v_onboarding ->> 'gender', '') is not null
        and v_goal_direction is not null
        and v_goal_text is not null
      then now()
      else null
    end
  )
  on conflict (user_id) do update
  set
    first_name = excluded.first_name,
    last_name = excluded.last_name,
    display_name = excluded.display_name,
    age = excluded.age,
    height_cm = excluded.height_cm,
    weight_kg = excluded.weight_kg,
    gender = excluded.gender,
    fitness_goal = excluded.fitness_goal,
    goal_direction = excluded.goal_direction,
    target_weight_kg = excluded.target_weight_kg,
    training_experience = excluded.training_experience,
    available_days = excluded.available_days,
    nutrition_preferences = excluded.nutrition_preferences,
    practical_constraints = excluded.practical_constraints,
    bmi = excluded.bmi,
    goal_safety_status = excluded.goal_safety_status,
    goal_safety_note = excluded.goal_safety_note,
    goal_timeline_weeks = excluded.goal_timeline_weeks,
    completed_at = coalesce(public.user_onboarding.completed_at, excluded.completed_at),
    updated_at = now();

  insert into public.entitlements (
    user_id,
    entitlement_code,
    status,
    source,
    metadata
  )
  values (
    v_profile.id,
    'free',
    'active',
    'phase1_default',
    jsonb_build_object('created_by', 'phase1_account_foundation')
  )
  on conflict (user_id, entitlement_code, source) do update
  set
    status = 'active',
    updated_at = now();

  select coalesce(jsonb_agg(to_jsonb(e) order by e.entitlement_code), '[]'::jsonb)
  into v_entitlements
  from public.entitlements e
  where e.user_id = v_profile.id;

  return jsonb_build_object(
    'profile', to_jsonb(v_profile),
    'settings', (
      select to_jsonb(s)
      from public.user_settings s
      where s.user_id = v_profile.id
    ),
    'onboarding', (
      select to_jsonb(o)
      from public.user_onboarding o
      where o.user_id = v_profile.id
    ),
    'entitlements', v_entitlements
  );
end;
$function$;

create or replace function public.fmz_phase3_sync_training_archive_state()
returns trigger
language plpgsql
set search_path = pg_catalog, public, pg_temp
as $function$
begin
  if new.status = 'archived' then
    if tg_op = 'UPDATE' then
      new.archived_at := coalesce(new.archived_at, old.archived_at, now());
    else
      new.archived_at := coalesce(new.archived_at, now());
    end if;
  else
    new.archived_at := null;
  end if;

  return new;
end;
$function$;

create or replace function public.fmz_phase3_enforce_training_plan_limit()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $function$
declare
  v_active_day_count integer;
  v_has_unlimited_training boolean;
begin
  if auth.uid() is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if new.user_id is distinct from auth.uid() then
    raise exception 'training plan owner must match authenticated user'
      using errcode = '42501';
  end if;

  if tg_op = 'UPDATE' and new.user_id is distinct from old.user_id then
    raise exception 'training plan ownership cannot be changed'
      using errcode = '42501';
  end if;

  if new.status = 'active' then
    perform pg_catalog.pg_advisory_xact_lock(
      pg_catalog.hashtextextended('fmz_phase3_training_day_limit:' || new.user_id::text, 0)
    );

    select exists (
      select 1
      from public.entitlements e
      where e.user_id = new.user_id
        and e.status = 'active'
        and e.entitlement_code in ('pro', 'personal_coaching')
        and e.starts_at <= now()
        and (e.ends_at is null or e.ends_at > now())
    )
    into v_has_unlimited_training;

    if not coalesce(v_has_unlimited_training, false) then
      select count(*)
      from public.training_plan_days d
      join public.training_plans p on p.id = d.training_plan_id
      where p.user_id = new.user_id
        and d.status = 'active'
        and (
          (p.id = new.id and new.status = 'active')
          or (p.id <> new.id and p.status = 'active')
        )
      into v_active_day_count;

      if v_active_day_count > 4 then
        raise exception 'Free training limit reached: maximum 4 active training days'
          using errcode = '23514';
      end if;
    end if;
  end if;

  return new;
end;
$function$;

create or replace function public.fmz_phase3_enforce_training_day_limit()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $function$
declare
  v_user_id uuid;
  v_old_user_id uuid;
  v_parent_status text;
  v_active_day_count integer;
  v_has_unlimited_training boolean;
begin
  if auth.uid() is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  select p.user_id
  into v_user_id
  from public.training_plans p
  where p.id = new.training_plan_id;

  if not found then
    raise exception 'training day parent plan is required'
      using errcode = '23503';
  end if;

  if v_user_id is distinct from auth.uid() then
    raise exception 'training day parent plan must belong to authenticated user'
      using errcode = '42501';
  end if;

  if tg_op = 'UPDATE' then
    select p.user_id
    into v_old_user_id
    from public.training_plans p
    where p.id = old.training_plan_id;

    if not found then
      raise exception 'training day previous parent plan is required'
        using errcode = '23503';
    end if;

    if v_old_user_id is distinct from auth.uid() then
      raise exception 'training day previous parent plan must belong to authenticated user'
        using errcode = '42501';
    end if;

    if v_old_user_id is distinct from v_user_id then
      raise exception 'training day cannot move between users'
        using errcode = '42501';
    end if;
  end if;

  if new.status = 'active' then
    perform pg_catalog.pg_advisory_xact_lock(
      pg_catalog.hashtextextended('fmz_phase3_training_day_limit:' || v_user_id::text, 0)
    );

    select p.status
    into v_parent_status
    from public.training_plans p
    where p.id = new.training_plan_id
      and p.user_id = v_user_id;

    if not found then
      raise exception 'training day parent plan is required'
        using errcode = '23503';
    end if;
  end if;

  if new.status = 'active' and v_parent_status = 'active' then
    select exists (
      select 1
      from public.entitlements e
      where e.user_id = v_user_id
        and e.status = 'active'
        and e.entitlement_code in ('pro', 'personal_coaching')
        and e.starts_at <= now()
        and (e.ends_at is null or e.ends_at > now())
    )
    into v_has_unlimited_training;

    if not coalesce(v_has_unlimited_training, false) then
      select count(*)
      from public.training_plan_days d
      join public.training_plans p on p.id = d.training_plan_id
      where p.user_id = v_user_id
        and p.status = 'active'
        and d.status = 'active'
        and d.id <> new.id
      into v_active_day_count;

      if v_active_day_count >= 4 then
        raise exception 'Free training limit reached: maximum 4 active training days'
          using errcode = '23514';
      end if;
    end if;
  end if;

  return new;
end;
$function$;

create or replace function public.fmz_phase3_enforce_workout_session_owner()
returns trigger
language plpgsql
set search_path = pg_catalog, public, pg_temp
as $function$
begin
  if new.user_id is distinct from auth.uid() then
    raise exception 'workout session owner must match authenticated user'
      using errcode = '42501';
  end if;

  if tg_op = 'UPDATE' and new.user_id is distinct from old.user_id then
    raise exception 'workout session ownership cannot be changed'
      using errcode = '42501';
  end if;

  if new.training_plan_day_id is not null and new.training_plan_id is null then
    raise exception 'workout session day requires matching training plan'
      using errcode = '23514';
  end if;

  if new.training_plan_id is not null and not exists (
    select 1
    from public.training_plans p
    where p.id = new.training_plan_id
      and p.user_id = new.user_id
  ) then
    raise exception 'workout session plan must belong to authenticated user'
      using errcode = '42501';
  end if;

  if new.training_plan_day_id is not null and not exists (
    select 1
    from public.training_plan_days d
    join public.training_plans p on p.id = d.training_plan_id
    where d.id = new.training_plan_day_id
      and d.training_plan_id = new.training_plan_id
      and p.user_id = new.user_id
  ) then
    raise exception 'workout session day must belong to the same plan and user'
      using errcode = '42501';
  end if;

  return new;
end;
$function$;

create or replace function public.fmz_phase3_enforce_set_log_owner()
returns trigger
language plpgsql
set search_path = pg_catalog, public, pg_temp
as $function$
declare
  v_session record;
begin
  if new.user_id is distinct from auth.uid() then
    raise exception 'set log owner must match authenticated user'
      using errcode = '42501';
  end if;

  if tg_op = 'UPDATE' and new.user_id is distinct from old.user_id then
    raise exception 'set log ownership cannot be changed'
      using errcode = '42501';
  end if;

  select
    s.id,
    s.user_id,
    s.training_plan_id,
    s.training_plan_day_id
  into v_session
  from public.workout_sessions s
  where s.id = new.workout_session_id
    and s.user_id = new.user_id;

  if not found then
    raise exception 'set log session must belong to authenticated user'
      using errcode = '42501';
  end if;

  if new.training_plan_exercise_id is not null then
    if v_session.training_plan_id is null or v_session.training_plan_day_id is null then
      raise exception 'planned set log exercise requires a normalized workout session plan and day'
        using errcode = '23514';
    end if;

    if not exists (
      select 1
      from public.training_plan_exercises e
      join public.training_plan_days d on d.id = e.training_plan_day_id
      join public.training_plans p on p.id = d.training_plan_id
      where e.id = new.training_plan_exercise_id
        and e.training_plan_day_id = v_session.training_plan_day_id
        and d.training_plan_id = v_session.training_plan_id
        and p.user_id = new.user_id
    ) then
      raise exception 'set log planned exercise must belong to the same session plan, day, and user'
        using errcode = '42501';
    end if;
  end if;

  return new;
end;
$function$;

create or replace function public.fmz_phase3_create_training_plan(
  p_plan_id uuid,
  p_day_id uuid,
  p_plan_exercise_id uuid,
  p_title text,
  p_day_label text,
  p_day_order integer,
  p_exercise_slug text,
  p_exercise_name text,
  p_target_sets integer,
  p_target_reps text,
  p_target_weight numeric,
  p_target_rir integer,
  p_target_rpe numeric,
  p_rest_seconds integer,
  p_notes text
)
returns jsonb
language plpgsql
set search_path = pg_catalog, public, pg_temp
as $function$
declare
  v_user_id uuid := auth.uid();
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  insert into public.training_plans (
    id,
    user_id,
    title,
    status,
    source,
    metadata
  )
  values (
    p_plan_id,
    v_user_id,
    nullif(trim(p_title), ''),
    'active',
    'phase3_client',
    jsonb_build_object('phase', 3, 'created_by', 'fmz_phase3_create_training_plan')
  );

  insert into public.training_plan_days (
    id,
    training_plan_id,
    day_label,
    day_order
  )
  values (
    p_day_id,
    p_plan_id,
    nullif(trim(p_day_label), ''),
    p_day_order
  );

  insert into public.training_plan_exercises (
    id,
    training_plan_day_id,
    exercise_slug,
    exercise_name_snapshot,
    exercise_order,
    target_sets,
    target_reps,
    target_weight,
    target_rir,
    target_rpe,
    rest_seconds,
    notes
  )
  values (
    p_plan_exercise_id,
    p_day_id,
    nullif(trim(p_exercise_slug), ''),
    nullif(trim(p_exercise_name), ''),
    0,
    p_target_sets,
    nullif(trim(p_target_reps), ''),
    p_target_weight,
    p_target_rir,
    p_target_rpe,
    p_rest_seconds,
    nullif(trim(p_notes), '')
  );

  return jsonb_build_object(
    'plan_id', p_plan_id,
    'day_id', p_day_id,
    'plan_exercise_id', p_plan_exercise_id,
    'user_id', v_user_id
  );
end;
$function$;

create trigger profiles_touch_updated_at
before update on public.profiles
for each row execute function public.touch_updated_at();

create trigger coach_workspaces_touch_updated_at
before update on public.coach_workspaces
for each row execute function public.touch_updated_at();

create trigger user_settings_touch_updated_at
before update on public.user_settings
for each row execute function public.touch_updated_at();

create trigger user_onboarding_touch_updated_at
before update on public.user_onboarding
for each row execute function public.touch_updated_at();

create trigger entitlements_touch_updated_at
before update on public.entitlements
for each row execute function public.touch_updated_at();

create trigger recovery_logs_touch_updated_at
before update on public.recovery_logs
for each row execute function public.touch_updated_at();

create trigger exercises_touch_updated_at
before update on public.exercises
for each row execute function public.touch_updated_at();

create trigger training_plans_touch_updated_at
before update on public.training_plans
for each row execute function public.touch_updated_at();

create trigger training_plans_enforce_free_limit
before insert or update on public.training_plans
for each row execute function public.fmz_phase3_enforce_training_plan_limit();

create trigger training_plan_days_touch_updated_at
before update on public.training_plan_days
for each row execute function public.touch_updated_at();

create trigger training_plan_days_sync_archive_state
before insert or update on public.training_plan_days
for each row execute function public.fmz_phase3_sync_training_archive_state();

create trigger training_plan_days_enforce_free_limit
before insert or update on public.training_plan_days
for each row execute function public.fmz_phase3_enforce_training_day_limit();

create trigger training_plan_exercises_touch_updated_at
before update on public.training_plan_exercises
for each row execute function public.touch_updated_at();

create trigger training_plan_exercises_sync_archive_state
before insert or update on public.training_plan_exercises
for each row execute function public.fmz_phase3_sync_training_archive_state();

create trigger workout_sessions_touch_updated_at
before update on public.workout_sessions
for each row execute function public.touch_updated_at();

create trigger workout_sessions_enforce_owner
before insert or update on public.workout_sessions
for each row execute function public.fmz_phase3_enforce_workout_session_owner();

create trigger workout_set_logs_touch_updated_at
before update on public.workout_set_logs
for each row execute function public.touch_updated_at();

create trigger workout_set_logs_enforce_owner
before insert or update on public.workout_set_logs
for each row execute function public.fmz_phase3_enforce_set_log_owner();

alter table public.profiles enable row level security;
alter table public.coach_workspaces enable row level security;
alter table public.user_settings enable row level security;
alter table public.user_onboarding enable row level security;
alter table public.entitlements enable row level security;
alter table public.recovery_logs enable row level security;
alter table public.exercises enable row level security;
alter table public.training_plans enable row level security;
alter table public.training_plan_days enable row level security;
alter table public.training_plan_exercises enable row level security;
alter table public.workout_sessions enable row level security;
alter table public.workout_set_logs enable row level security;

create policy "profiles select own or linked"
on public.profiles
for select
using (public.fmz_can_select_profile(id, role, trainer_id));

create policy "profiles update own"
on public.profiles
for update
using (id = auth.uid())
with check (id = auth.uid());

create policy "profiles insert own trainer"
on public.profiles
for insert
with check (id = auth.uid() and role = 'trainer');

create policy "workspace insert trainer"
on public.coach_workspaces
for insert
with check (trainer_id = auth.uid() and public.fmz_is_trainer());

create policy "workspace read trainer or linked client"
on public.coach_workspaces
for select
using (public.fmz_can_access_workspace(trainer_id));

create policy "workspace update trainer or linked client"
on public.coach_workspaces
for update
using (trainer_id = auth.uid() and public.fmz_is_trainer())
with check (trainer_id = auth.uid() and public.fmz_is_trainer());

create policy user_settings_select_own
on public.user_settings
for select
using (user_id = auth.uid());

create policy user_settings_insert_own
on public.user_settings
for insert
with check (user_id = auth.uid());

create policy user_settings_update_own
on public.user_settings
for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy user_onboarding_select_own
on public.user_onboarding
for select
using (user_id = auth.uid());

create policy user_onboarding_insert_own
on public.user_onboarding
for insert
with check (user_id = auth.uid());

create policy user_onboarding_update_own
on public.user_onboarding
for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy entitlements_select_own
on public.entitlements
for select
using (user_id = auth.uid());

create policy recovery_logs_select_own
on public.recovery_logs
for select
using (user_id = auth.uid());

create policy recovery_logs_insert_own
on public.recovery_logs
for insert
with check (user_id = auth.uid());

create policy recovery_logs_update_own
on public.recovery_logs
for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy exercises_select_active_authenticated
on public.exercises
for select to authenticated
using (is_active = true);

create policy training_plans_select_own
on public.training_plans
for select
using (user_id = auth.uid());

create policy training_plans_insert_own
on public.training_plans
for insert
with check (user_id = auth.uid());

create policy training_plans_update_own
on public.training_plans
for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy training_plan_days_select_own
on public.training_plan_days
for select
using (
  exists (
    select 1
    from public.training_plans p
    where p.id = training_plan_days.training_plan_id
      and p.user_id = auth.uid()
  )
);

create policy training_plan_days_insert_own
on public.training_plan_days
for insert
with check (
  exists (
    select 1
    from public.training_plans p
    where p.id = training_plan_days.training_plan_id
      and p.user_id = auth.uid()
  )
);

create policy training_plan_days_update_own
on public.training_plan_days
for update
using (
  exists (
    select 1
    from public.training_plans p
    where p.id = training_plan_days.training_plan_id
      and p.user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from public.training_plans p
    where p.id = training_plan_days.training_plan_id
      and p.user_id = auth.uid()
  )
);

create policy training_plan_exercises_select_own
on public.training_plan_exercises
for select
using (
  exists (
    select 1
    from public.training_plan_days d
    join public.training_plans p on p.id = d.training_plan_id
    where d.id = training_plan_exercises.training_plan_day_id
      and p.user_id = auth.uid()
  )
);

create policy training_plan_exercises_insert_own
on public.training_plan_exercises
for insert
with check (
  exists (
    select 1
    from public.training_plan_days d
    join public.training_plans p on p.id = d.training_plan_id
    where d.id = training_plan_exercises.training_plan_day_id
      and p.user_id = auth.uid()
  )
);

create policy training_plan_exercises_update_own
on public.training_plan_exercises
for update
using (
  exists (
    select 1
    from public.training_plan_days d
    join public.training_plans p on p.id = d.training_plan_id
    where d.id = training_plan_exercises.training_plan_day_id
      and p.user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from public.training_plan_days d
    join public.training_plans p on p.id = d.training_plan_id
    where d.id = training_plan_exercises.training_plan_day_id
      and p.user_id = auth.uid()
  )
);

create policy workout_sessions_select_own
on public.workout_sessions
for select
using (user_id = auth.uid());

create policy workout_sessions_insert_own
on public.workout_sessions
for insert
with check (user_id = auth.uid());

create policy workout_sessions_update_own
on public.workout_sessions
for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy workout_set_logs_select_own
on public.workout_set_logs
for select
using (user_id = auth.uid());

create policy workout_set_logs_insert_own
on public.workout_set_logs
for insert
with check (user_id = auth.uid());

create policy workout_set_logs_update_own
on public.workout_set_logs
for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

revoke all on table public.profiles from public, anon, authenticated;
grant select, insert, update on table public.profiles to authenticated;
grant all on table public.profiles to service_role;

revoke all on table public.coach_workspaces from public, anon, authenticated;
grant select, insert, update on table public.coach_workspaces to authenticated;
grant all on table public.coach_workspaces to service_role;

grant all on table public.user_settings to anon, authenticated, service_role;
grant all on table public.user_onboarding to anon, authenticated, service_role;
grant all on table public.entitlements to anon, authenticated, service_role;

revoke all on table public.recovery_logs from public, anon, authenticated;
grant select, insert, update on table public.recovery_logs to authenticated;
grant all on table public.recovery_logs to service_role;

revoke all on table public.exercises from public, anon, authenticated;
grant select on table public.exercises to authenticated;
grant all on table public.exercises to service_role;

revoke all on table public.training_plans from public, anon, authenticated;
revoke all on table public.training_plan_days from public, anon, authenticated;
revoke all on table public.training_plan_exercises from public, anon, authenticated;
revoke all on table public.workout_sessions from public, anon, authenticated;
revoke all on table public.workout_set_logs from public, anon, authenticated;

grant select, insert, update on table public.training_plans to authenticated;
grant select, insert, update on table public.training_plan_days to authenticated;
grant select, insert, update on table public.training_plan_exercises to authenticated;
grant select, insert, update on table public.workout_sessions to authenticated;
grant select, insert, update on table public.workout_set_logs to authenticated;
grant all on table public.training_plans to service_role;
grant all on table public.training_plan_days to service_role;
grant all on table public.training_plan_exercises to service_role;
grant all on table public.workout_sessions to service_role;
grant all on table public.workout_set_logs to service_role;

revoke all on function public.fmz_phase1_upsert_account_foundation(text, text, text, jsonb) from public, anon, authenticated;
grant execute on function public.fmz_phase1_upsert_account_foundation(text, text, text, jsonb) to authenticated, service_role;

revoke all on function public.fmz_phase3_create_training_plan(
  uuid, uuid, uuid, text, text, integer, text, text, integer, text, numeric, integer, numeric, integer, text
) from public, anon, authenticated;
grant execute on function public.fmz_phase3_create_training_plan(
  uuid, uuid, uuid, text, text, integer, text, text, integer, text, numeric, integer, numeric, integer, text
) to authenticated, service_role;

revoke all on function public.fmz_phase3_sync_training_archive_state() from public, anon, authenticated;
revoke all on function public.fmz_phase3_enforce_training_plan_limit() from public, anon, authenticated;
revoke all on function public.fmz_phase3_enforce_training_day_limit() from public, anon, authenticated;
revoke all on function public.fmz_phase3_enforce_workout_session_owner() from public, anon, authenticated;
revoke all on function public.fmz_phase3_enforce_set_log_owner() from public, anon, authenticated;

commit;
