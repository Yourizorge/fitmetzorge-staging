begin;

alter table public.ai_consent_events drop constraint if exists ai_consent_events_kind_check;
alter table public.ai_consent_events
  add constraint ai_consent_events_kind_check
  check (consent_kind in ('ai_processing', 'trainer_summary_sharing', 'ai_analysis'));

alter table ai_private.consent_documents drop constraint if exists ai_consent_documents_kind_check;
alter table ai_private.consent_documents
  add constraint ai_consent_documents_kind_check
  check (consent_kind in ('ai_processing', 'trainer_summary_sharing', 'ai_analysis'));

create table if not exists ai_private.phase6d_runtime_config (
  singleton boolean primary key default true,
  mock_analyses_enabled boolean not null default true,
  external_provider_enabled boolean not null default false,
  scheduled_generation_enabled boolean not null default true,
  daily_enabled boolean not null default true,
  post_workout_enabled boolean not null default true,
  weekly_enabled boolean not null default true,
  retention_sweep_enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint phase6d_runtime_singleton_check check (singleton is true),
  constraint phase6d_runtime_provider_off_check check (external_provider_enabled is false)
);

alter table ai_private.phase6d_runtime_config enable row level security;
revoke all on table ai_private.phase6d_runtime_config from public, anon, authenticated;

insert into ai_private.phase6d_runtime_config(singleton)
values (true)
on conflict (singleton) do nothing;

create trigger phase6d_runtime_config_touch_updated_at
before update on ai_private.phase6d_runtime_config
for each row execute function ai_private.touch_updated_at();

create table if not exists public.ai_analysis_preferences (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  timezone_name text not null default 'Europe/Amsterdam',
  daily_enabled boolean not null default true,
  daily_time time not null default time '07:30',
  post_workout_enabled boolean not null default true,
  weekly_enabled boolean not null default true,
  weekly_day smallint not null default 1,
  weekly_time time not null default time '08:00',
  last_request_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  revision bigint not null default 1,
  constraint ai_analysis_preferences_weekday_check check (weekly_day between 1 and 7)
);

alter table public.ai_analysis_preferences enable row level security;
drop policy if exists ai_analysis_preferences_select_own on public.ai_analysis_preferences;
create policy ai_analysis_preferences_select_own on public.ai_analysis_preferences
  for select to authenticated using (auth.uid() = user_id);
revoke all on table public.ai_analysis_preferences from public, anon, authenticated;

create trigger ai_analysis_preferences_touch_updated_at
before update on public.ai_analysis_preferences
for each row execute function ai_private.touch_updated_at();

create table if not exists public.ai_analysis_results (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  analysis_kind text not null,
  feature_code text not null,
  event_key text not null,
  request_id uuid not null,
  status text not null default 'pending',
  locale text not null default 'nl',
  adapter_code text,
  model_tier text,
  policy_version text,
  schema_version text,
  context_manifest_id uuid references public.ai_context_manifests(id) on delete restrict,
  run_id uuid references ai_private.runs(id) on delete set null,
  source_cutoff_at timestamptz not null default now(),
  period_start_local date,
  period_end_local date,
  timezone_name text not null default 'Europe/Amsterdam',
  quality jsonb not null default '{}'::jsonb,
  unavailable_sources text[] not null default '{}',
  result_payload jsonb,
  summary_text text,
  safe_error_code text,
  result_expires_at timestamptz not null default now() + interval '90 days',
  metadata_expires_at timestamptz not null default now() + interval '180 days',
  content_deleted_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz,
  revision bigint not null default 1,
  constraint ai_analysis_results_kind_check check (analysis_kind in ('daily', 'post_workout', 'weekly')),
  constraint ai_analysis_results_feature_check check (feature_code in ('daily_analysis', 'post_workout', 'weekly_checkin')),
  constraint ai_analysis_results_feature_kind_check check (
    (analysis_kind = 'daily' and feature_code = 'daily_analysis')
    or (analysis_kind = 'post_workout' and feature_code = 'post_workout')
    or (analysis_kind = 'weekly' and feature_code = 'weekly_checkin')
  ),
  constraint ai_analysis_results_status_check check (status in (
    'pending', 'ready', 'partial', 'insufficient_data', 'hard_stop', 'review_required', 'failed', 'deleted', 'stale'
  )),
  constraint ai_analysis_results_locale_check check (locale in ('nl', 'en', 'de')),
  constraint ai_analysis_results_adapter_check check (adapter_code is null or adapter_code in ('mock', 'provider')),
  constraint ai_analysis_results_model_check check (model_tier is null or model_tier in ('luna', 'terra')),
  constraint ai_analysis_results_event_key_check check (char_length(btrim(event_key)) between 1 and 160),
  constraint ai_analysis_results_schema_check check (schema_version is null or schema_version = 'phase6d.analysis.v1'),
  constraint ai_analysis_results_quality_check check (jsonb_typeof(quality) = 'object' and pg_column_size(quality) <= 8192),
  constraint ai_analysis_results_payload_check check (
    (status in ('pending', 'insufficient_data', 'failed', 'stale') and (result_payload is null or jsonb_typeof(result_payload) = 'object'))
    or (status in ('ready', 'partial', 'hard_stop', 'review_required') and jsonb_typeof(result_payload) = 'object' and summary_text is not null)
    or (status = 'deleted' and result_payload is null and summary_text is null)
  ),
  constraint ai_analysis_results_summary_check check (summary_text is null or char_length(summary_text) between 1 and 1600),
  constraint ai_analysis_results_error_check check (
    safe_error_code is null
    or (
      safe_error_code ~ '^[a-z0-9_]{1,80}$'
      and safe_error_code !~ '(prompt|content|message|email|jwt|token|secret)'
    )
  ),
  constraint ai_analysis_results_user_request_unique unique (user_id, request_id),
  constraint ai_analysis_results_user_event_unique unique (user_id, analysis_kind, event_key)
);

create index if not exists ai_analysis_results_user_created_idx
  on public.ai_analysis_results(user_id, created_at desc, id desc);
create index if not exists ai_analysis_results_user_status_idx
  on public.ai_analysis_results(user_id, status, result_expires_at);
create index if not exists ai_analysis_results_retention_idx
  on public.ai_analysis_results(result_expires_at, metadata_expires_at);

alter table public.ai_analysis_results enable row level security;
drop policy if exists ai_analysis_results_select_own on public.ai_analysis_results;
create policy ai_analysis_results_select_own on public.ai_analysis_results
  for select to authenticated using (auth.uid() = user_id);
revoke all on table public.ai_analysis_results from public, anon, authenticated;

create trigger ai_analysis_results_touch_updated_at
before update on public.ai_analysis_results
for each row execute function ai_private.touch_updated_at();

create table if not exists public.ai_analysis_lifecycle_requests (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  result_id uuid references public.ai_analysis_results(id) on delete set null,
  request_type text not null,
  status text not null default 'completed',
  request_id uuid not null,
  requested_at timestamptz not null default now(),
  completed_at timestamptz not null default now(),
  safe_result_code text not null,
  metadata_expires_at timestamptz not null default now() + interval '180 days',
  constraint ai_analysis_lifecycle_type_check check (request_type in ('export', 'delete')),
  constraint ai_analysis_lifecycle_status_check check (status in ('completed', 'failed')),
  constraint ai_analysis_lifecycle_result_check check (
    safe_result_code ~ '^[a-z0-9_]{1,80}$'
    and safe_result_code !~ '(prompt|content|message|email|jwt|token|secret)'
  ),
  constraint ai_analysis_lifecycle_user_request_unique unique (user_id, request_id)
);

alter table public.ai_analysis_lifecycle_requests enable row level security;
drop policy if exists ai_analysis_lifecycle_requests_select_own on public.ai_analysis_lifecycle_requests;
create policy ai_analysis_lifecycle_requests_select_own on public.ai_analysis_lifecycle_requests
  for select to authenticated using (auth.uid() = user_id);
revoke all on table public.ai_analysis_lifecycle_requests from public, anon, authenticated;

with docs(consent_kind, document_version, locale, purpose_code, categories, content_text) as (
  values
  (
    'ai_analysis',
    'phase6d-analysis-v1',
    'nl',
    'read_only_ai_analyses',
    array['training','nutrition','progress','recovery','activity']::text[],
    'Ik geef expliciet toestemming dat FitMetZorge in staging mijn trainings-, voedings-, voortgangs- en herstelgegevens gebruikt voor read-only AI-analyses. De analyses veranderen geen schema, doelen, trainingen, voeding, rollen of coachkoppelingen. Ik kan deze toestemming intrekken; nieuwe analyses stoppen dan direct en bestaande resultaten verlopen uiterlijk na 90 dagen.'
  ),
  (
    'ai_analysis',
    'phase6d-analysis-v1',
    'en',
    'read_only_ai_analyses',
    array['training','nutrition','progress','recovery','activity']::text[],
    'I explicitly consent to FitMetZorge using my training, nutrition, progress, and recovery data in staging for read-only AI analyses. These analyses do not change plans, goals, workouts, nutrition, roles, or coach links. I can withdraw consent; new analyses stop immediately and existing results expire within 90 days.'
  ),
  (
    'ai_analysis',
    'phase6d-analysis-v1',
    'de',
    'read_only_ai_analyses',
    array['training','nutrition','progress','recovery','activity']::text[],
    'Ich willige ausdruecklich ein, dass FitMetZorge in Staging meine Trainings-, Ernaehrungs-, Fortschritts- und Erholungsdaten fuer read-only KI-Analysen nutzt. Diese Analysen aendern keine Plaene, Ziele, Trainings, Ernaehrung, Rollen oder Coach-Verknuepfungen. Ich kann die Einwilligung widerrufen; neue Analysen stoppen sofort und bestehende Ergebnisse verfallen spaetestens nach 90 Tagen.'
  )
)
insert into ai_private.consent_documents(
  consent_kind, document_version, locale, purpose_code, categories,
  content_text, content_sha256, status, effective_at
)
select
  consent_kind, document_version, locale, purpose_code, categories,
  content_text, encode(extensions.digest(convert_to(content_text, 'UTF8'), 'sha256'), 'hex'),
  'active', timestamp with time zone '2026-09-04 00:00:00+00'
from docs
on conflict (consent_kind, document_version, locale) do update
set purpose_code = excluded.purpose_code,
    categories = excluded.categories,
    content_text = excluded.content_text,
    content_sha256 = excluded.content_sha256,
    status = excluded.status,
    effective_at = excluded.effective_at;

insert into ai_private.structured_schemas(schema_code, schema_version, schema_body, active)
values (
  'read_only_ai_analysis',
  'phase6d.analysis.v1',
  jsonb_build_object(
    'type', 'object',
    'required', jsonb_build_array('schema_version','analysis_kind','feature_code','status','summary','observations','uncertainties','suggestions','actions','safety','data_quality','period'),
    'additionalProperties', false,
    'properties', jsonb_build_object(
      'schema_version', jsonb_build_object('const','phase6d.analysis.v1'),
      'analysis_kind', jsonb_build_object('enum', jsonb_build_array('daily','post_workout','weekly')),
      'feature_code', jsonb_build_object('enum', jsonb_build_array('daily_analysis','post_workout','weekly_checkin')),
      'status', jsonb_build_object('enum', jsonb_build_array('ready','partial','hard_stop','review_required')),
      'summary', jsonb_build_object('type','string','maxLength',1600),
      'actions', jsonb_build_object('type','array','maxItems',0)
    )
  ),
  true
)
on conflict (schema_code, schema_version) do update
set schema_body = excluded.schema_body,
    active = excluded.active;

create or replace function ai_private.phase6d_feature_code(p_analysis_kind text)
returns text
language plpgsql
immutable
security invoker
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
begin
  if p_analysis_kind = 'daily' then return 'daily_analysis'; end if;
  if p_analysis_kind = 'post_workout' then return 'post_workout'; end if;
  if p_analysis_kind = 'weekly' then return 'weekly_checkin'; end if;
  raise exception 'analysis_kind_invalid' using errcode = '22023';
end;
$$;

create or replace function ai_private.phase6d_model_tier(p_analysis_kind text)
returns text
language plpgsql
immutable
security invoker
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
begin
  if p_analysis_kind = 'weekly' then return 'terra'; end if;
  if p_analysis_kind in ('daily', 'post_workout') then return 'luna'; end if;
  raise exception 'analysis_kind_invalid' using errcode = '22023';
end;
$$;

create or replace function ai_private.phase6d_age_eligible(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
  select coalesce((select u.age >= 18 from public.user_onboarding u where u.user_id = p_user_id), false);
$$;

create or replace function ai_private.phase6d_budget_snapshot(
  p_user_id uuid,
  p_model_tier text,
  p_at timestamptz default now()
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_entitlement record;
  v_period record;
  v_policy ai_private.budget_policies%rowtype;
  v_account ai_private.budget_accounts%rowtype;
  v_eval jsonb;
begin
  if p_model_tier not in ('luna', 'terra') then
    raise exception 'analysis_model_route_invalid' using errcode = '22023';
  end if;
  select * into v_entitlement from ai_private.current_entitlement(p_user_id, p_at);
  select * into v_policy from ai_private.budget_policies where active order by created_at desc limit 1;
  if v_entitlement.entitlement_code is null or v_policy.policy_version is null then
    return jsonb_build_object(
      'allowed', false,
      'reason', 'ai_entitlement_required',
      'fair_use_status', 'blocked',
      'included_micros', coalesce(v_policy.included_micros, 3000000),
      'warning_micros', coalesce(v_policy.warning_micros, 2400000),
      'grace_micros', coalesce(v_policy.grace_micros, 1000000),
      'hard_cap_micros', coalesce(v_policy.hard_cap_micros, 4000000),
      'terra_stop_micros', coalesce(v_policy.terra_stop_micros, 3000000),
      'consumed_micros', 0,
      'reserved_micros', 0,
      'automatic_billing', false
    );
  end if;
  select * into v_period from ai_private.subscription_period(v_entitlement.entitlement_started_at, p_at);
  select * into v_account
  from ai_private.budget_accounts a
  where a.user_id = p_user_id and a.period_start = v_period.period_start;
  v_eval := ai_private.evaluate_budget(
    coalesce(v_account.consumed_micros, 0),
    coalesce(v_account.reserved_micros, 0),
    0,
    p_model_tier
  );
  return v_eval || jsonb_build_object(
    'policy_version', v_policy.policy_version,
    'included_micros', v_policy.included_micros,
    'warning_micros', v_policy.warning_micros,
    'grace_micros', v_policy.grace_micros,
    'hard_cap_micros', v_policy.hard_cap_micros,
    'terra_stop_micros', v_policy.terra_stop_micros,
    'consumed_micros', coalesce(v_account.consumed_micros, 0),
    'reserved_micros', coalesce(v_account.reserved_micros, 0),
    'period_start', v_period.period_start,
    'period_end', v_period.period_end,
    'automatic_billing', false
  );
end;
$$;

create or replace function ai_private.phase6d_current_preferences(p_user_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_pref public.ai_analysis_preferences%rowtype;
begin
  select * into v_pref from public.ai_analysis_preferences where user_id = p_user_id;
  return jsonb_build_object(
    'timezone_name', coalesce(v_pref.timezone_name, 'Europe/Amsterdam'),
    'daily_enabled', coalesce(v_pref.daily_enabled, true),
    'daily_time', to_char(coalesce(v_pref.daily_time, time '07:30'), 'HH24:MI'),
    'post_workout_enabled', coalesce(v_pref.post_workout_enabled, true),
    'weekly_enabled', coalesce(v_pref.weekly_enabled, true),
    'weekly_day', coalesce(v_pref.weekly_day, 1),
    'weekly_time', to_char(coalesce(v_pref.weekly_time, time '08:00'), 'HH24:MI'),
    'updated_at', v_pref.updated_at,
    'revision', coalesce(v_pref.revision, 0)
  );
end;
$$;

create or replace function ai_private.phase6d_analysis_status(
  p_user_id uuid,
  p_analysis_kind text default 'daily',
  p_at timestamptz default now()
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_feature text;
  v_model text;
  v_entitlement record;
  v_consent record;
  v_safety public.ai_member_safety_state%rowtype;
  v_config ai_private.phase6d_runtime_config%rowtype;
  v_budget jsonb;
  v_age boolean;
  v_allowed boolean;
  v_reason text := 'allowed';
begin
  perform ai_private.assert_member(p_user_id);
  v_feature := ai_private.phase6d_feature_code(p_analysis_kind);
  v_model := ai_private.phase6d_model_tier(p_analysis_kind);
  select * into v_entitlement from ai_private.current_entitlement(p_user_id, p_at);
  select * into v_consent from ai_private.current_consent(p_user_id, 'ai_analysis');
  select * into v_safety from public.ai_member_safety_state where user_id = p_user_id;
  select * into v_config from ai_private.phase6d_runtime_config where singleton;
  v_age := ai_private.phase6d_age_eligible(p_user_id);
  v_budget := ai_private.phase6d_budget_snapshot(p_user_id, v_model, p_at);

  if v_config.singleton is null or not v_config.mock_analyses_enabled then
    v_reason := 'mock_disabled';
  elsif v_config.external_provider_enabled then
    v_reason := 'external_provider_forbidden';
  elsif p_analysis_kind = 'daily' and not v_config.daily_enabled then
    v_reason := 'analysis_kind_disabled';
  elsif p_analysis_kind = 'post_workout' and not v_config.post_workout_enabled then
    v_reason := 'analysis_kind_disabled';
  elsif p_analysis_kind = 'weekly' and not v_config.weekly_enabled then
    v_reason := 'analysis_kind_disabled';
  elsif v_entitlement.entitlement_code is null then
    v_reason := 'ai_entitlement_required';
  elsif coalesce(v_consent.consent_state, 'missing') <> 'granted' or not coalesce(v_consent.document_active, false) then
    v_reason := 'ai_analysis_consent_required';
  elsif not v_age then
    v_reason := 'ai_age_required';
  elsif coalesce(v_safety.safety_status, 'clear') in ('hard_stop', 'review_required') then
    v_reason := 'safety_hard_stop';
  elsif not coalesce((v_budget ->> 'allowed')::boolean, false) then
    v_reason := coalesce(v_budget ->> 'reason', 'budget_hard_stop');
  end if;
  v_allowed := v_reason = 'allowed';

  return jsonb_build_object(
    'analysis_allowed', v_allowed,
    'deny_reason', v_reason,
    'analysis_kind', p_analysis_kind,
    'feature_code', v_feature,
    'model_tier', v_model,
    'adapter_code', 'mock',
    'entitlement_code', v_entitlement.entitlement_code,
    'consent_state', coalesce(v_consent.consent_state, 'missing'),
    'document_active', coalesce(v_consent.document_active, false),
    'age_eligible', v_age,
    'safety_status', coalesce(v_safety.safety_status, 'clear'),
    'automatic_execution_blocked', coalesce(v_safety.safety_status, 'clear') in ('hard_stop', 'review_required'),
    'mock_mode', coalesce(v_config.mock_analyses_enabled, false),
    'external_ai_enabled', false,
    'external_ai_calls', 0,
    'external_ai_cost_eur', 0,
    'budget', v_budget,
    'provider_status', jsonb_build_object(
      'real_provider_enabled', false,
      'dpa_dpia_eu_route_zdr_approved', false,
      'store', false,
      'background', false,
      'tools', '[]'::jsonb,
      'tool_choice', 'none'
    )
  );
end;
$$;

create or replace function ai_private.phase6d_build_context(
  p_user_id uuid,
  p_analysis_kind text,
  p_event_id uuid default null,
  p_at timestamptz default now()
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_feature text := ai_private.phase6d_feature_code(p_analysis_kind);
  v_pref jsonb := ai_private.phase6d_current_preferences(p_user_id);
  v_tz text := coalesce(v_pref ->> 'timezone_name', 'Europe/Amsterdam');
  v_today date;
  v_period_start date;
  v_period_end date;
  v_window_start date;
  v_event_key text;
  v_workout public.workout_sessions%rowtype;
  v_recovery jsonb := '{}'::jsonb;
  v_nutrition jsonb := '{}'::jsonb;
  v_training jsonb := '{}'::jsonb;
  v_progress jsonb := '{}'::jsonb;
  v_recovery_count integer := 0;
  v_food_days integer := 0;
  v_food_items integer := 0;
  v_workout_count integer := 0;
  v_set_count integer := 0;
  v_weight_count integer := 0;
  v_measure_count integer := 0;
  v_domain_count integer := 0;
  v_observation_count integer := 0;
  v_missing text[] := '{}';
  v_reliable boolean;
  v_quality_level text;
begin
  perform ai_private.assert_member(p_user_id);
  if not exists (select 1 from pg_timezone_names where name = v_tz) then
    v_tz := 'Europe/Amsterdam';
  end if;
  v_today := (p_at at time zone v_tz)::date;

  if p_analysis_kind = 'daily' then
    v_period_start := v_today;
    v_period_end := v_today;
    v_window_start := v_today - 6;
    v_event_key := 'daily:' || v_today::text;
  elsif p_analysis_kind = 'weekly' then
    v_period_end := v_today;
    v_period_start := v_today - 6;
    v_window_start := v_period_start;
    v_event_key := 'weekly:' || v_period_start::text || ':' || v_period_end::text;
  elsif p_analysis_kind = 'post_workout' then
    select * into v_workout
    from public.workout_sessions w
    where w.user_id = p_user_id
      and w.status = 'completed'
      and w.completed_at is not null
      and (p_event_id is null or w.id = p_event_id)
    order by case when p_event_id is null then w.completed_at end desc nulls last, w.created_at desc
    limit 1;
    if v_workout.id is null then
      v_period_start := v_today;
      v_period_end := v_today;
      v_window_start := v_today - 29;
      v_event_key := 'post_workout:none:' || v_today::text;
    else
      v_period_start := (v_workout.completed_at at time zone v_tz)::date;
      v_period_end := v_period_start;
      v_window_start := v_period_start - 29;
      v_event_key := 'post_workout:' || v_workout.id::text;
    end if;
  else
    raise exception 'analysis_kind_invalid' using errcode = '22023';
  end if;

  select
    count(*)::integer,
    jsonb_strip_nulls(jsonb_build_object(
      'days_logged', count(*),
      'avg_sleep_hours', round(avg(sleep_hours), 1),
      'avg_sleep_quality', round(avg(sleep_quality)::numeric, 1),
      'avg_steps', round(avg(steps)::numeric, 0),
      'avg_energy', round(avg(wellbeing_energy)::numeric, 1),
      'avg_stress', round(avg(wellbeing_stress)::numeric, 1),
      'avg_motivation', round(avg(wellbeing_motivation)::numeric, 1),
      'avg_recovery_feeling', round(avg(recovery_feeling)::numeric, 1),
      'load_statuses', coalesce(jsonb_agg(distinct training_load_status) filter (where training_load_status is not null), '[]'::jsonb)
    ))
  into v_recovery_count, v_recovery
  from public.recovery_logs r
  where r.user_id = p_user_id
    and r.log_date between v_window_start and v_period_end;

  with daily as (
    select
      fl.log_date,
      sum(i.energy_kcal_snapshot) as energy_kcal,
      sum(i.protein_grams_snapshot) as protein_grams,
      sum(i.carbohydrate_grams_snapshot) as carbohydrate_grams,
      sum(i.fat_grams_snapshot) as fat_grams,
      sum(coalesce(i.fiber_grams_snapshot, 0)) as fiber_grams,
      count(i.id) as items
    from public.food_logs fl
    join public.food_log_items i on i.food_log_id = fl.id and i.user_id = fl.user_id and i.status = 'active'
    where fl.user_id = p_user_id
      and fl.status = 'active'
      and fl.archived_at is null
      and i.archived_at is null
      and fl.log_date between v_window_start and v_period_end
    group by fl.log_date
  )
  select
    coalesce(count(*), 0)::integer,
    coalesce(sum(items), 0)::integer,
    jsonb_strip_nulls(jsonb_build_object(
      'days_logged', count(*),
      'items_logged', coalesce(sum(items), 0),
      'avg_energy_kcal', round(avg(energy_kcal), 0),
      'avg_protein_grams', round(avg(protein_grams), 1),
      'avg_carbohydrate_grams', round(avg(carbohydrate_grams), 1),
      'avg_fat_grams', round(avg(fat_grams), 1),
      'avg_fiber_grams', round(avg(fiber_grams), 1)
    ))
  into v_food_days, v_food_items, v_nutrition
  from daily;

  if p_analysis_kind = 'post_workout' and v_workout.id is not null then
    select
      1,
      coalesce(count(*), 0)::integer,
      jsonb_strip_nulls(jsonb_build_object(
        'completed_workouts', 1,
        'selected_workout_title', left(v_workout.title_snapshot, 120),
        'completed_at', v_workout.completed_at,
        'exercise_count', count(distinct s.exercise_slug),
        'set_count', count(s.id),
        'total_volume_kg', round(sum(coalesce(s.actual_reps, 0) * coalesce(s.actual_weight, 0)), 1),
        'avg_rpe', round(avg(s.rpe), 1),
        'avg_rir', round(avg(s.rir)::numeric, 1),
        'sets_with_reps', count(*) filter (where s.actual_reps is not null),
        'sets_with_weight', count(*) filter (where s.actual_weight is not null)
      ))
    into v_workout_count, v_set_count, v_training
    from public.workout_set_logs s
    where s.user_id = p_user_id and s.workout_session_id = v_workout.id;
  else
    select
      count(*)::integer,
      coalesce(sum(set_count), 0)::integer,
      jsonb_strip_nulls(jsonb_build_object(
        'completed_workouts', count(*),
        'set_count', coalesce(sum(set_count), 0),
        'avg_sets_per_workout', round(avg(set_count)::numeric, 1)
      ))
    into v_workout_count, v_set_count, v_training
    from (
      select w.id, count(s.id) as set_count
      from public.workout_sessions w
      left join public.workout_set_logs s on s.workout_session_id = w.id and s.user_id = w.user_id
      where w.user_id = p_user_id
        and w.status = 'completed'
        and w.completed_at is not null
        and (w.completed_at at time zone v_tz)::date between v_window_start and v_period_end
      group by w.id
    ) workouts;
  end if;

  select
    count(*)::integer,
    jsonb_strip_nulls(jsonb_build_object(
      'weight_logs', count(*),
      'latest_weight_kg', (array_agg(weight_kg order by measured_at desc))[1],
      'first_weight_kg', (array_agg(weight_kg order by measured_at asc))[1],
      'latest_log_date', max(log_date),
      'first_log_date', min(log_date)
    ))
  into v_weight_count, v_progress
  from public.weight_logs wl
  where wl.user_id = p_user_id
    and wl.status = 'active'
    and wl.archived_at is null
    and wl.log_date between v_window_start and v_period_end;

  select count(*)::integer into v_measure_count
  from public.body_measurements bm
  where bm.user_id = p_user_id
    and bm.status = 'active'
    and bm.archived_at is null
    and bm.log_date between v_window_start and v_period_end;

  v_progress := v_progress || jsonb_build_object('body_measurement_logs', v_measure_count);

  if v_recovery_count = 0 then v_missing := array_append(v_missing, 'recovery'); end if;
  if v_food_days = 0 then v_missing := array_append(v_missing, 'nutrition'); end if;
  if v_workout_count = 0 then v_missing := array_append(v_missing, 'training'); end if;
  if v_weight_count + v_measure_count = 0 then v_missing := array_append(v_missing, 'progress'); end if;

  v_domain_count :=
    (case when v_recovery_count > 0 then 1 else 0 end)
    + (case when v_food_days > 0 then 1 else 0 end)
    + (case when v_workout_count > 0 then 1 else 0 end)
    + (case when v_weight_count + v_measure_count > 0 then 1 else 0 end);
  v_observation_count := v_recovery_count + v_food_days + v_workout_count + v_weight_count + v_measure_count;

  if p_analysis_kind = 'daily' then
    v_reliable := v_domain_count >= 1 and v_observation_count >= 1;
  elsif p_analysis_kind = 'weekly' then
    v_reliable := v_domain_count >= 2 and v_observation_count >= 3;
  else
    v_reliable := v_workout.id is not null;
  end if;
  v_quality_level := case
    when not v_reliable then 'insufficient'
    when p_analysis_kind = 'post_workout' and v_set_count = 0 then 'partial'
    when v_domain_count >= 3 then 'sufficient'
    else 'partial'
  end;

  return jsonb_build_object(
    'schema_version', 'phase6d.context.v1',
    'analysis_kind', p_analysis_kind,
    'feature_code', v_feature,
    'event_key', v_event_key,
    'source_cutoff_at', p_at,
    'period', jsonb_build_object(
      'start_local', v_period_start,
      'end_local', v_period_end,
      'timezone_name', v_tz,
      'max_lookback_days', 30
    ),
    'quality', jsonb_build_object(
      'level', v_quality_level,
      'reliable', v_reliable,
      'domain_count', v_domain_count,
      'observation_count', v_observation_count,
      'missing_sources', to_jsonb(v_missing),
      'stop_before_provider', not v_reliable
    ),
    'sources', jsonb_build_object(
      'training', v_training,
      'nutrition', v_nutrition,
      'recovery', v_recovery,
      'progress', v_progress
    ),
    'unavailable_sources', to_jsonb(v_missing),
    'privacy', jsonb_build_object(
      'private_chat_included', false,
      'raw_prompts_included', false,
      'raw_notes_included', false,
      'trainer_visible', false,
      'domain_writes_allowed', false
    )
  );
end;
$$;

create or replace function ai_private.phase6d_validate_analysis_output(p_payload jsonb)
returns boolean
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_kind text;
  v_feature text;
begin
  if jsonb_typeof(p_payload) <> 'object'
     or pg_column_size(p_payload) > 32768
     or p_payload::text ~* '"(raw_prompt|prompt|message_content|email|jwt|token|secret|service_role|action_code)"\s*:'
     or p_payload ->> 'schema_version' <> 'phase6d.analysis.v1'
     or p_payload ->> 'analysis_kind' not in ('daily', 'post_workout', 'weekly')
     or p_payload ->> 'status' not in ('ready', 'partial', 'hard_stop', 'review_required')
     or jsonb_typeof(p_payload -> 'observations') <> 'array'
     or jsonb_array_length(p_payload -> 'observations') > 12
     or jsonb_typeof(p_payload -> 'uncertainties') <> 'array'
     or jsonb_array_length(p_payload -> 'uncertainties') > 12
     or jsonb_typeof(p_payload -> 'suggestions') <> 'array'
     or jsonb_array_length(p_payload -> 'suggestions') > 12
     or jsonb_typeof(p_payload -> 'actions') <> 'array'
     or jsonb_array_length(p_payload -> 'actions') <> 0
     or jsonb_typeof(p_payload -> 'safety') <> 'object'
     or p_payload -> 'safety' ->> 'status' not in ('clear', 'hard_stop', 'review_required')
     or jsonb_typeof(p_payload -> 'data_quality') <> 'object'
     or jsonb_typeof(p_payload -> 'period') <> 'object'
     or char_length(btrim(coalesce(p_payload ->> 'summary', ''))) not between 1 and 1600 then
    return false;
  end if;
  v_kind := p_payload ->> 'analysis_kind';
  v_feature := ai_private.phase6d_feature_code(v_kind);
  if p_payload ->> 'feature_code' <> v_feature then return false; end if;
  if (p_payload -> 'safety' ->> 'status') in ('hard_stop', 'review_required')
     and coalesce((p_payload -> 'safety' ->> 'automatic_execution_blocked')::boolean, false) is not true then
    return false;
  end if;
  return true;
exception
  when others then
    return false;
end;
$$;

create or replace function public.fmz_phase6d_read_analysis_contract(p_locale text default 'nl')
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_locale text := case when p_locale in ('nl','en','de') then p_locale else 'nl' end;
  v_current record;
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  select * into v_current from ai_private.current_consent(v_user_id, 'ai_analysis');
  return jsonb_build_object(
    'contracts', coalesce((
      select jsonb_agg(jsonb_build_object(
        'consent_kind', d.consent_kind,
        'document_version', d.document_version,
        'locale', d.locale,
        'purpose_code', d.purpose_code,
        'categories', d.categories,
        'content_text', d.content_text,
        'content_sha256', d.content_sha256,
        'effective_at', d.effective_at
      ) order by d.locale)
      from ai_private.consent_documents d
      where d.consent_kind = 'ai_analysis'
        and d.status = 'active'
        and d.effective_at <= now()
        and d.locale = v_locale
    ), '[]'::jsonb),
    'current', jsonb_build_object(
      'ai_analysis', jsonb_build_object(
        'consent_state', coalesce(v_current.consent_state, 'missing'),
        'document_version', v_current.document_version,
        'purpose_code', v_current.purpose_code,
        'categories', v_current.categories,
        'locale', v_current.locale,
        'consented_at', v_current.consented_at,
        'document_active', coalesce(v_current.document_active, false)
      )
    )
  );
end;
$$;

create or replace function public.fmz_phase6d_record_analysis_consent(
  p_action text,
  p_document_version text,
  p_locale text,
  p_explicit_confirmation boolean,
  p_request_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_doc ai_private.consent_documents%rowtype;
  v_existing public.ai_consent_events%rowtype;
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  if p_action not in ('granted','withdrawn')
     or p_locale not in ('nl','en','de')
     or p_request_id is null
     or p_explicit_confirmation is not true then
    raise exception 'ai_analysis_consent_input_invalid' using errcode = '22023';
  end if;
  select * into v_doc
  from ai_private.consent_documents d
  where d.consent_kind = 'ai_analysis'
    and d.document_version = p_document_version
    and d.locale = p_locale
    and d.status = 'active'
    and d.effective_at <= now();
  if v_doc.document_version is null then
    raise exception 'ai_analysis_consent_document_invalid' using errcode = '22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_consent:' || v_user_id::text || ':' || p_request_id::text, 0));
  select * into v_existing from public.ai_consent_events e where e.user_id = v_user_id and e.request_id = p_request_id;
  if v_existing.id is not null then
    if v_existing.consent_kind <> 'ai_analysis'
       or v_existing.consent_state <> p_action
       or v_existing.document_version <> p_document_version then
      raise exception 'ai_analysis_consent_request_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'consent_state', v_existing.consent_state, 'created_at', v_existing.created_at);
  end if;
  insert into public.ai_consent_events(
    id, user_id, consent_kind, consent_state, document_version, purpose_code,
    categories, locale, explicit_confirmation, request_id
  ) values (
    gen_random_uuid(), v_user_id, 'ai_analysis', p_action, v_doc.document_version,
    v_doc.purpose_code, v_doc.categories, v_doc.locale, true, p_request_id
  ) returning * into v_existing;
  return jsonb_build_object('replay', false, 'consent_state', v_existing.consent_state, 'created_at', v_existing.created_at);
end;
$$;

create or replace function public.fmz_phase6d_get_status()
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_latest public.workout_sessions%rowtype;
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  select * into v_latest
  from public.workout_sessions w
  where w.user_id = v_user_id and w.status = 'completed' and w.completed_at is not null
  order by w.completed_at desc, w.created_at desc
  limit 1;
  return jsonb_build_object(
    'schema_version', 'phase6d.status.v1',
    'preferences', ai_private.phase6d_current_preferences(v_user_id),
    'contract', public.fmz_phase6d_read_analysis_contract('nl'),
    'kinds', jsonb_build_object(
      'daily', ai_private.phase6d_analysis_status(v_user_id, 'daily', now()),
      'post_workout', ai_private.phase6d_analysis_status(v_user_id, 'post_workout', now()),
      'weekly', ai_private.phase6d_analysis_status(v_user_id, 'weekly', now())
    ),
    'latest_completed_workout', case when v_latest.id is null then null else jsonb_build_object(
      'id', v_latest.id,
      'title', v_latest.title_snapshot,
      'completed_at', v_latest.completed_at
    ) end,
    'result_counts', jsonb_build_object(
      'active', (select count(*) from public.ai_analysis_results r where r.user_id = v_user_id and r.status <> 'deleted'),
      'deleted', (select count(*) from public.ai_analysis_results r where r.user_id = v_user_id and r.status = 'deleted')
    ),
    'privacy', jsonb_build_object(
      'private_chat_used_as_context', false,
      'trainer_access', false,
      'raw_prompt_logging', false,
      'domain_writes_allowed', false,
      'retention_days', 90,
      'audit_metadata_days', 180
    )
  );
end;
$$;

create or replace function public.fmz_phase6d_update_preferences(
  p_timezone_name text,
  p_daily_enabled boolean,
  p_daily_time text,
  p_post_workout_enabled boolean,
  p_weekly_enabled boolean,
  p_weekly_day smallint,
  p_weekly_time text,
  p_expected_revision bigint default null,
  p_request_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_existing public.ai_analysis_preferences%rowtype;
  v_daily_time time;
  v_weekly_time time;
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  if p_request_id is null or p_weekly_day not between 1 and 7
     or not exists (select 1 from pg_timezone_names where name = p_timezone_name) then
    raise exception 'analysis_preferences_input_invalid' using errcode = '22023';
  end if;
  v_daily_time := p_daily_time::time;
  v_weekly_time := p_weekly_time::time;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_preferences:' || v_user_id::text, 0));
  select * into v_existing from public.ai_analysis_preferences where user_id = v_user_id for update;
  if v_existing.user_id is not null and v_existing.last_request_id = p_request_id then
    return ai_private.phase6d_current_preferences(v_user_id) || jsonb_build_object('replay', true);
  end if;
  if v_existing.user_id is not null and p_expected_revision is not null and v_existing.revision <> p_expected_revision then
    raise exception 'analysis_preferences_stale_conflict' using errcode = '40001';
  end if;
  insert into public.ai_analysis_preferences(
    user_id, timezone_name, daily_enabled, daily_time, post_workout_enabled,
    weekly_enabled, weekly_day, weekly_time, last_request_id, revision
  ) values (
    v_user_id, p_timezone_name, coalesce(p_daily_enabled, true), v_daily_time,
    coalesce(p_post_workout_enabled, true), coalesce(p_weekly_enabled, true),
    p_weekly_day, v_weekly_time, p_request_id, 1
  )
  on conflict (user_id) do update
  set timezone_name = excluded.timezone_name,
      daily_enabled = excluded.daily_enabled,
      daily_time = excluded.daily_time,
      post_workout_enabled = excluded.post_workout_enabled,
      weekly_enabled = excluded.weekly_enabled,
      weekly_day = excluded.weekly_day,
      weekly_time = excluded.weekly_time,
      last_request_id = excluded.last_request_id,
      revision = public.ai_analysis_preferences.revision + 1,
      updated_at = now();
  return ai_private.phase6d_current_preferences(v_user_id) || jsonb_build_object('replay', false);
end;
$$;

create or replace function public.fmz_phase6d_prepare_analysis(
  p_request_id uuid,
  p_analysis_kind text,
  p_locale text default 'nl',
  p_event_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_locale text := case when p_locale in ('nl','en','de') then p_locale else 'nl' end;
  v_status jsonb;
  v_context jsonb;
  v_existing public.ai_analysis_results%rowtype;
  v_result public.ai_analysis_results%rowtype;
  v_feature text;
  v_model text;
  v_event_key text;
  v_quality jsonb;
  v_missing text[];
  v_local_payload jsonb;
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  if p_request_id is null or p_analysis_kind not in ('daily','post_workout','weekly') then
    raise exception 'analysis_request_invalid' using errcode = '22023';
  end if;
  v_feature := ai_private.phase6d_feature_code(p_analysis_kind);
  v_model := ai_private.phase6d_model_tier(p_analysis_kind);
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_request:' || v_user_id::text || ':' || p_request_id::text, 0));
  select * into v_existing from public.ai_analysis_results r where r.user_id = v_user_id and r.request_id = p_request_id;
  if v_existing.id is not null then
    return jsonb_build_object('replay', true, 'status', v_existing.status, 'result', jsonb_build_object(
      'id', v_existing.id,
      'analysis_kind', v_existing.analysis_kind,
      'status', v_existing.status,
      'summary', v_existing.summary_text,
      'result_payload', v_existing.result_payload,
      'revision', v_existing.revision
    ));
  end if;
  v_status := ai_private.phase6d_analysis_status(v_user_id, p_analysis_kind, now());
  if not coalesce((v_status ->> 'analysis_allowed')::boolean, false) then
    raise exception '%', v_status ->> 'deny_reason' using errcode = '42501';
  end if;
  v_context := ai_private.phase6d_build_context(v_user_id, p_analysis_kind, p_event_id, now());
  v_event_key := v_context ->> 'event_key';
  v_quality := v_context -> 'quality';
  v_missing := coalesce(array(select jsonb_array_elements_text(v_context -> 'unavailable_sources')), '{}');
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_event:' || v_user_id::text || ':' || p_analysis_kind || ':' || v_event_key, 0));
  select * into v_existing
  from public.ai_analysis_results r
  where r.user_id = v_user_id and r.analysis_kind = p_analysis_kind and r.event_key = v_event_key;
  if v_existing.id is not null then
    return jsonb_build_object('replay', true, 'status', v_existing.status, 'result', jsonb_build_object(
      'id', v_existing.id,
      'analysis_kind', v_existing.analysis_kind,
      'status', v_existing.status,
      'summary', v_existing.summary_text,
      'result_payload', v_existing.result_payload,
      'revision', v_existing.revision
    ));
  end if;
  if not coalesce((v_quality ->> 'reliable')::boolean, false) then
    v_local_payload := jsonb_build_object(
      'schema_version', 'phase6d.analysis.v1',
      'analysis_kind', p_analysis_kind,
      'feature_code', v_feature,
      'status', 'partial',
      'summary', 'Er is nog niet genoeg betrouwbare data voor deze read-only analyse. Vul eerst recente training, voeding, herstel of voortgang aan.',
      'observations', '[]'::jsonb,
      'uncertainties', jsonb_build_array('insufficient_reliable_data'),
      'suggestions', jsonb_build_array(jsonb_build_object('kind','data_quality','text','Voeg recente meetpunten toe en probeer de analyse daarna opnieuw.')),
      'actions', '[]'::jsonb,
      'safety', jsonb_build_object('status','clear','category','none','message_key','safety.clear','automatic_execution_blocked',false),
      'data_quality', v_quality,
      'period', v_context -> 'period',
      'privacy', v_context -> 'privacy'
    );
    insert into public.ai_analysis_results(
      id, user_id, analysis_kind, feature_code, event_key, request_id, status, locale,
      schema_version, source_cutoff_at, period_start_local, period_end_local, timezone_name,
      quality, unavailable_sources, result_payload, summary_text, completed_at
    ) values (
      gen_random_uuid(), v_user_id, p_analysis_kind, v_feature, v_event_key, p_request_id,
      'insufficient_data', v_locale, 'phase6d.analysis.v1', (v_context ->> 'source_cutoff_at')::timestamptz,
      (v_context -> 'period' ->> 'start_local')::date, (v_context -> 'period' ->> 'end_local')::date,
      v_context -> 'period' ->> 'timezone_name', v_quality, v_missing, v_local_payload,
      v_local_payload ->> 'summary', now()
    ) returning * into v_result;
    return jsonb_build_object('replay', false, 'status', 'insufficient_data', 'result', jsonb_build_object(
      'id', v_result.id,
      'analysis_kind', v_result.analysis_kind,
      'status', v_result.status,
      'summary', v_result.summary_text,
      'result_payload', v_result.result_payload,
      'revision', v_result.revision
    ));
  end if;
  insert into public.ai_analysis_results(
    id, user_id, analysis_kind, feature_code, event_key, request_id, status, locale,
    schema_version, source_cutoff_at, period_start_local, period_end_local, timezone_name,
    quality, unavailable_sources
  ) values (
    gen_random_uuid(), v_user_id, p_analysis_kind, v_feature, v_event_key, p_request_id, 'pending',
    v_locale, 'phase6d.analysis.v1', (v_context ->> 'source_cutoff_at')::timestamptz,
    (v_context -> 'period' ->> 'start_local')::date, (v_context -> 'period' ->> 'end_local')::date,
    v_context -> 'period' ->> 'timezone_name', v_quality, v_missing
  ) returning * into v_result;
  return jsonb_build_object(
    'replay', false,
    'status', 'prepared',
    'result_id', v_result.id,
    'analysis_kind', p_analysis_kind,
    'feature_code', v_feature,
    'model_tier', v_model,
    'context', v_context,
    'external_ai_calls', 0,
    'external_ai_cost_eur', 0
  );
end;
$$;

create or replace function public.fmz_phase6d_service_begin_analysis(
  p_user_id uuid,
  p_result_id uuid,
  p_request_id uuid,
  p_analysis_kind text,
  p_payload_hash text,
  p_context_sources jsonb,
  p_unavailable_sources text[] default '{}'
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_result public.ai_analysis_results%rowtype;
  v_existing ai_private.runs%rowtype;
  v_gate jsonb;
  v_entitlement record;
  v_period record;
  v_policy ai_private.budget_policies%rowtype;
  v_account ai_private.budget_accounts%rowtype;
  v_budget jsonb;
  v_rate ai_private.rate_policies%rowtype;
  v_window timestamptz;
  v_bucket ai_private.rate_buckets%rowtype;
  v_feature text := ai_private.phase6d_feature_code(p_analysis_kind);
  v_model text := ai_private.phase6d_model_tier(p_analysis_kind);
  v_manifest_id uuid := gen_random_uuid();
  v_run_id uuid := gen_random_uuid();
begin
  perform ai_private.assert_member(p_user_id);
  if p_result_id is null or p_request_id is null
     or p_payload_hash !~ '^[0-9a-f]{64}$'
     or jsonb_typeof(p_context_sources) <> 'object'
     or pg_column_size(p_context_sources) > 32768
     or p_context_sources::text ~* '"(raw_prompt|prompt|message_content|email|jwt|token|secret|service_role)"\s*:'
     or cardinality(coalesce(p_unavailable_sources, '{}')) > 24 then
    raise exception 'analysis_run_input_invalid' using errcode = '22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_run:' || p_user_id::text || ':' || p_request_id::text, 0));
  select * into v_result
  from public.ai_analysis_results r
  where r.id = p_result_id and r.user_id = p_user_id
  for update;
  if v_result.id is null or v_result.request_id <> p_request_id or v_result.analysis_kind <> p_analysis_kind then
    raise exception 'analysis_result_forbidden' using errcode = '42501';
  end if;
  select * into v_existing from ai_private.runs r where r.user_id = p_user_id and r.request_id = p_request_id;
  if v_existing.id is not null then
    if v_existing.feature_code <> v_feature
       or v_existing.adapter_code <> 'mock'
       or v_existing.model_tier <> v_model
       or v_existing.payload_hash <> p_payload_hash then
      raise exception 'analysis_run_request_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'run_id', v_existing.id, 'status', v_existing.status);
  end if;
  if v_result.status <> 'pending' then
    raise exception 'analysis_result_not_pending' using errcode = '40001';
  end if;
  v_gate := ai_private.phase6d_analysis_status(p_user_id, p_analysis_kind, now());
  if not coalesce((v_gate ->> 'analysis_allowed')::boolean, false) then
    raise exception '%', v_gate ->> 'deny_reason' using errcode = '42501';
  end if;
  if not exists (
    select 1 from ai_private.phase6d_runtime_config c
    where c.singleton and c.mock_analyses_enabled and not c.external_provider_enabled
  ) then
    raise exception 'mock_disabled' using errcode = '42501';
  end if;
  select * into v_entitlement from ai_private.current_entitlement(p_user_id, now());
  select * into v_period from ai_private.subscription_period(v_entitlement.entitlement_started_at, now());
  select * into v_policy from ai_private.budget_policies where active order by created_at desc limit 1;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_budget:' || p_user_id::text || ':' || v_period.period_start::text, 0));
  insert into ai_private.budget_accounts(user_id, period_start, period_end, policy_version)
  values (p_user_id, v_period.period_start, v_period.period_end, v_policy.policy_version)
  on conflict(user_id, period_start) do nothing;
  select * into v_account from ai_private.budget_accounts a
  where a.user_id = p_user_id and a.period_start = v_period.period_start for update;
  v_budget := ai_private.evaluate_budget(v_account.consumed_micros, v_account.reserved_micros, 0, v_model);
  if not (v_budget ->> 'allowed')::boolean then
    raise exception '%', v_budget ->> 'reason' using errcode = '42501';
  end if;
  select * into v_rate from ai_private.rate_policies where feature_code = v_feature and active;
  v_window := to_timestamp(floor(extract(epoch from now()) / v_rate.window_seconds) * v_rate.window_seconds);
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_rate:' || p_user_id::text || ':' || v_feature || ':' || v_window::text, 0));
  insert into ai_private.rate_buckets(user_id, feature_code, window_started_at, window_seconds, request_count)
  values (p_user_id, v_feature, v_window, v_rate.window_seconds, 1)
  on conflict (user_id, feature_code, window_started_at) do update
    set request_count = ai_private.rate_buckets.request_count + 1,
        updated_at = now()
  returning * into v_bucket;
  if v_bucket.request_count > v_rate.max_requests then
    raise exception 'ai_rate_limit' using errcode = '42501';
  end if;
  insert into public.ai_context_manifests(
    id, user_id, feature_code, manifest_version, context_hash, sources, unavailable_sources, source_cutoff_at
  ) values (
    v_manifest_id, p_user_id, v_feature, 'phase6d.context.v1',
    encode(extensions.digest(convert_to(p_context_sources::text, 'UTF8'), 'sha256'), 'hex'),
    p_context_sources, coalesce(p_unavailable_sources, '{}'), now()
  );
  insert into ai_private.runs(
    id, user_id, request_id, thread_id, context_manifest_id, feature_code,
    adapter_code, model_tier, policy_version, schema_version, payload_hash,
    reserved_cost_micros
  ) values (
    v_run_id, p_user_id, p_request_id, null, v_manifest_id, v_feature,
    'mock', v_model, v_policy.policy_version, 'phase6d.analysis.v1', p_payload_hash, 0
  );
  insert into ai_private.usage_ledger(id, user_id, run_id, request_id, feature_code, model_tier, ledger_type, amount_micros)
  values (gen_random_uuid(), p_user_id, v_run_id, p_request_id, v_feature, v_model, 'reserve', 0);
  update public.ai_analysis_results
  set run_id = v_run_id,
      context_manifest_id = v_manifest_id,
      adapter_code = 'mock',
      model_tier = v_model,
      policy_version = v_policy.policy_version,
      unavailable_sources = coalesce(p_unavailable_sources, '{}'),
      revision = revision + 1
  where id = p_result_id and user_id = p_user_id;
  insert into ai_private.audit_events(id, user_id, run_id, event_code, safe_metadata)
  values (gen_random_uuid(), p_user_id, v_run_id, 'analysis_run_reserved', jsonb_build_object('feature_code', v_feature, 'adapter_code', 'mock', 'package', '6d'));
  return jsonb_build_object('replay', false, 'run_id', v_run_id, 'status', 'reserved', 'fair_use_status', v_budget ->> 'fair_use_status');
end;
$$;

create or replace function public.fmz_phase6d_service_complete_analysis(
  p_run_id uuid,
  p_result_id uuid,
  p_structured_output jsonb,
  p_actual_cost_micros bigint,
  p_input_tokens integer,
  p_output_tokens integer
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_run ai_private.runs%rowtype;
  v_result public.ai_analysis_results%rowtype;
  v_entitlement record;
  v_period record;
  v_account ai_private.budget_accounts%rowtype;
  v_budget jsonb;
  v_response_hash text;
begin
  if p_run_id is null or p_result_id is null
     or p_actual_cost_micros not between 0 and 4000000
     or p_input_tokens not between 0 and 1000000
     or p_output_tokens not between 0 and 1000000
     or not ai_private.phase6d_validate_analysis_output(p_structured_output) then
    raise exception 'analysis_structured_output_invalid' using errcode = '22023';
  end if;
  v_response_hash := encode(extensions.digest(convert_to(p_structured_output::text, 'UTF8'), 'sha256'), 'hex');
  select * into v_run from ai_private.runs r where r.id = p_run_id for update;
  if v_run.id is null then raise exception 'ai_run_not_found' using errcode = '22023'; end if;
  if v_run.schema_version <> 'phase6d.analysis.v1'
     or v_run.feature_code <> p_structured_output ->> 'feature_code'
     or (p_structured_output ->> 'analysis_kind') <> (case v_run.feature_code when 'daily_analysis' then 'daily' when 'post_workout' then 'post_workout' else 'weekly' end) then
    raise exception 'analysis_structured_output_conflict' using errcode = '23505';
  end if;
  select * into v_result from public.ai_analysis_results r where r.id = p_result_id and r.user_id = v_run.user_id for update;
  if v_result.id is null or v_result.run_id is distinct from p_run_id or v_result.request_id <> v_run.request_id then
    raise exception 'analysis_result_forbidden' using errcode = '42501';
  end if;
  if v_run.status = 'completed' then
    if v_run.response_hash <> v_response_hash then raise exception 'analysis_completion_conflict' using errcode = '23505'; end if;
    return jsonb_build_object('replay', true, 'run_id', v_run.id, 'result_id', v_result.id, 'status', v_result.status);
  elsif v_run.status <> 'reserved' then
    raise exception 'ai_run_not_completable' using errcode = '40001';
  end if;
  if v_run.adapter_code = 'mock' and p_actual_cost_micros <> 0 then
    raise exception 'ai_mock_cost_forbidden' using errcode = '22023';
  end if;
  select * into v_entitlement from ai_private.current_entitlement(v_run.user_id, v_run.started_at);
  select * into v_period from ai_private.subscription_period(v_entitlement.entitlement_started_at, v_run.started_at);
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_budget:' || v_run.user_id::text || ':' || v_period.period_start::text, 0));
  select * into v_account from ai_private.budget_accounts a
  where a.user_id = v_run.user_id and a.period_start = v_period.period_start for update;
  v_budget := ai_private.evaluate_budget(v_account.consumed_micros, greatest(0, v_account.reserved_micros - v_run.reserved_cost_micros), p_actual_cost_micros, v_run.model_tier);
  if not (v_budget ->> 'allowed')::boolean then
    raise exception '%', v_budget ->> 'reason' using errcode = '42501';
  end if;
  update ai_private.budget_accounts
  set reserved_micros = greatest(0, reserved_micros - v_run.reserved_cost_micros),
      consumed_micros = consumed_micros + p_actual_cost_micros,
      hard_stopped_at = case when consumed_micros + p_actual_cost_micros >= 4000000 then coalesce(hard_stopped_at, now()) else hard_stopped_at end,
      updated_at = now()
  where user_id = v_run.user_id and period_start = v_period.period_start;
  insert into ai_private.usage_ledger(id, user_id, run_id, request_id, feature_code, model_tier, ledger_type, amount_micros)
  values (gen_random_uuid(), v_run.user_id, v_run.id, v_run.request_id, v_run.feature_code, v_run.model_tier, 'actual', p_actual_cost_micros);
  update ai_private.runs
  set status = 'completed',
      actual_cost_micros = p_actual_cost_micros,
      input_tokens = p_input_tokens,
      output_tokens = p_output_tokens,
      response_hash = v_response_hash,
      completed_at = now()
  where id = v_run.id;
  update public.ai_analysis_results
  set status = p_structured_output ->> 'status',
      result_payload = p_structured_output,
      summary_text = p_structured_output ->> 'summary',
      quality = coalesce(p_structured_output -> 'data_quality', quality),
      completed_at = now(),
      result_expires_at = now() + interval '90 days',
      metadata_expires_at = now() + interval '180 days',
      revision = revision + 1
  where id = v_result.id;
  if p_structured_output -> 'safety' ->> 'status' in ('hard_stop','review_required') then
    perform public.fmz_phase6a_service_record_safety_event(
      v_run.user_id,
      v_run.id,
      coalesce(p_structured_output -> 'safety' ->> 'category', 'serious_health'),
      p_structured_output -> 'safety' ->> 'status',
      v_run.policy_version
    );
  end if;
  insert into ai_private.audit_events(id, user_id, run_id, event_code, safe_metadata)
  values (gen_random_uuid(), v_run.user_id, v_run.id, 'analysis_run_completed', jsonb_build_object('feature_code', v_run.feature_code, 'safety_status', p_structured_output -> 'safety' ->> 'status'));
  return jsonb_build_object('replay', false, 'run_id', v_run.id, 'result_id', v_result.id, 'status', p_structured_output ->> 'status', 'fair_use_status', v_budget ->> 'fair_use_status');
end;
$$;

create or replace function public.fmz_phase6d_service_fail_analysis(
  p_run_id uuid,
  p_result_id uuid,
  p_safe_error_code text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_run ai_private.runs%rowtype;
begin
  if p_run_id is null or p_result_id is null
     or p_safe_error_code !~ '^[a-z0-9_]{1,80}$'
     or p_safe_error_code ~ '(prompt|content|message|email|jwt|token|secret)' then
    raise exception 'analysis_safe_error_invalid' using errcode = '22023';
  end if;
  select * into v_run from ai_private.runs r where r.id = p_run_id;
  if v_run.id is null or v_run.schema_version <> 'phase6d.analysis.v1' then
    raise exception 'ai_run_not_found' using errcode = '22023';
  end if;
  perform public.fmz_phase6a_service_fail_run(p_run_id, p_safe_error_code);
  update public.ai_analysis_results
  set status = 'failed',
      safe_error_code = p_safe_error_code,
      completed_at = now(),
      revision = revision + 1
  where id = p_result_id and user_id = v_run.user_id and run_id = p_run_id;
  return jsonb_build_object('replay', false, 'run_id', p_run_id, 'result_id', p_result_id, 'status', 'failed');
end;
$$;

create or replace function public.fmz_phase6d_list_analyses(
  p_limit integer default 20,
  p_before_created_at timestamptz default null,
  p_before_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_limit integer := least(greatest(coalesce(p_limit, 20), 1), 50);
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  perform ai_private.phase6d_apply_retention(v_user_id, now());
  return jsonb_build_object(
    'schema_version', 'phase6d.analysis-list.v1',
    'results', coalesce((
      select jsonb_agg(jsonb_build_object(
        'id', r.id,
        'analysis_kind', r.analysis_kind,
        'status', r.status,
        'locale', r.locale,
        'summary', r.summary_text,
        'result_payload', r.result_payload,
        'quality', r.quality,
        'period_start_local', r.period_start_local,
        'period_end_local', r.period_end_local,
        'timezone_name', r.timezone_name,
        'model_tier', r.model_tier,
        'adapter_code', r.adapter_code,
        'created_at', r.created_at,
        'completed_at', r.completed_at,
        'result_expires_at', r.result_expires_at,
        'revision', r.revision
      ) order by r.created_at desc, r.id desc)
      from (
        select *
        from public.ai_analysis_results r
        where r.user_id = v_user_id
          and (p_before_created_at is null or (r.created_at, r.id) < (p_before_created_at, p_before_id))
        order by r.created_at desc, r.id desc
        limit v_limit
      ) r
    ), '[]'::jsonb)
  );
end;
$$;

create or replace function public.fmz_phase6d_delete_analysis(
  p_result_id uuid,
  p_expected_revision bigint,
  p_request_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_result public.ai_analysis_results%rowtype;
  v_audit public.ai_analysis_lifecycle_requests%rowtype;
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  if p_result_id is null or p_request_id is null or p_expected_revision is null or p_expected_revision < 1 then
    raise exception 'analysis_delete_input_invalid' using errcode = '22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_lifecycle:' || v_user_id::text || ':' || p_request_id::text, 0));
  select * into v_audit from public.ai_analysis_lifecycle_requests r where r.user_id = v_user_id and r.request_id = p_request_id;
  if v_audit.id is not null then
    if v_audit.request_type <> 'delete' or v_audit.result_id is distinct from p_result_id then
      raise exception 'analysis_lifecycle_request_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'result_id', p_result_id, 'deleted', true);
  end if;
  select * into v_result from public.ai_analysis_results r where r.id = p_result_id for update;
  if v_result.id is null or v_result.user_id <> v_user_id then
    raise exception 'analysis_result_forbidden' using errcode = '42501';
  end if;
  if v_result.status <> 'deleted' and v_result.revision <> p_expected_revision then
    raise exception 'analysis_result_stale_conflict' using errcode = '40001';
  end if;
  update public.ai_analysis_results
  set status = 'deleted',
      result_payload = null,
      summary_text = null,
      content_deleted_at = now(),
      completed_at = coalesce(completed_at, now()),
      revision = revision + 1
  where id = p_result_id and user_id = v_user_id;
  insert into public.ai_analysis_lifecycle_requests(
    id, user_id, result_id, request_type, status, request_id, completed_at, safe_result_code
  ) values (
    gen_random_uuid(), v_user_id, p_result_id, 'delete', 'completed', p_request_id, now(), 'analysis_content_deleted'
  );
  return jsonb_build_object('replay', false, 'result_id', p_result_id, 'deleted', true);
end;
$$;

create or replace function public.fmz_phase6d_export_analyses(p_request_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_audit public.ai_analysis_lifecycle_requests%rowtype;
  v_replay boolean := false;
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  if p_request_id is null then raise exception 'analysis_export_input_invalid' using errcode = '22023'; end if;
  perform ai_private.phase6d_apply_retention(v_user_id, now());
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_lifecycle:' || v_user_id::text || ':' || p_request_id::text, 0));
  select * into v_audit from public.ai_analysis_lifecycle_requests r where r.user_id = v_user_id and r.request_id = p_request_id;
  if v_audit.id is not null then
    if v_audit.request_type <> 'export' then raise exception 'analysis_lifecycle_request_conflict' using errcode = '23505'; end if;
    v_replay := true;
  else
    insert into public.ai_analysis_lifecycle_requests(
      id, user_id, request_type, status, request_id, completed_at, safe_result_code
    ) values (
      gen_random_uuid(), v_user_id, 'export', 'completed', p_request_id, now(), 'analysis_json_returned'
    );
  end if;
  return jsonb_build_object(
    'schema_version', 'phase6d.analysis-export.v1',
    'generated_at', now(),
    'replay', v_replay,
    'preferences', ai_private.phase6d_current_preferences(v_user_id),
    'consent', (public.fmz_phase6d_read_analysis_contract('nl') -> 'current' -> 'ai_analysis'),
    'retention', jsonb_build_object('result_days', 90, 'audit_metadata_days', 180),
    'analyses', coalesce((
      select jsonb_agg(jsonb_build_object(
        'id', r.id,
        'analysis_kind', r.analysis_kind,
        'status', r.status,
        'locale', r.locale,
        'summary', r.summary_text,
        'result_payload', r.result_payload,
        'quality', r.quality,
        'period_start_local', r.period_start_local,
        'period_end_local', r.period_end_local,
        'timezone_name', r.timezone_name,
        'created_at', r.created_at,
        'completed_at', r.completed_at,
        'result_expires_at', r.result_expires_at,
        'content_deleted_at', r.content_deleted_at
      ) order by r.created_at, r.id)
      from public.ai_analysis_results r
      where r.user_id = v_user_id
    ), '[]'::jsonb)
  );
end;
$$;

create or replace function ai_private.phase6d_apply_retention(
  p_user_id uuid,
  p_at timestamptz default now()
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_scrubbed integer := 0;
  v_deleted integer := 0;
begin
  perform ai_private.assert_member(p_user_id);
  update public.ai_analysis_results
  set status = 'deleted',
      result_payload = null,
      summary_text = null,
      content_deleted_at = coalesce(content_deleted_at, p_at),
      revision = revision + 1
  where user_id = p_user_id
    and status <> 'deleted'
    and result_expires_at <= p_at;
  get diagnostics v_scrubbed = row_count;

  delete from public.ai_analysis_results
  where user_id = p_user_id
    and status = 'deleted'
    and metadata_expires_at <= p_at;
  get diagnostics v_deleted = row_count;

  delete from public.ai_analysis_lifecycle_requests
  where user_id = p_user_id
    and metadata_expires_at <= p_at;

  return jsonb_build_object('scrubbed_results', v_scrubbed, 'deleted_metadata', v_deleted);
end;
$$;

create or replace function ai_private.phase6d_retention_sweep(p_at timestamptz default now())
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user record;
  v_result jsonb;
  v_scrubbed integer := 0;
  v_deleted integer := 0;
begin
  if not exists (select 1 from ai_private.phase6d_runtime_config c where c.singleton and c.retention_sweep_enabled) then
    return jsonb_build_object('skipped', true, 'reason', 'retention_disabled');
  end if;
  for v_user in
    select distinct user_id
    from public.ai_analysis_results
    where result_expires_at <= p_at or metadata_expires_at <= p_at
  loop
    v_result := ai_private.phase6d_apply_retention(v_user.user_id, p_at);
    v_scrubbed := v_scrubbed + coalesce((v_result ->> 'scrubbed_results')::integer, 0);
    v_deleted := v_deleted + coalesce((v_result ->> 'deleted_metadata')::integer, 0);
  end loop;
  return jsonb_build_object('scrubbed_results', v_scrubbed, 'deleted_metadata', v_deleted);
end;
$$;

create or replace function ai_private.phase6d_select_due_analyses(
  p_at timestamptz default now(),
  p_limit integer default 50
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_candidates jsonb := '[]'::jsonb;
  v_pref record;
  v_local_date date;
  v_local_time time;
  v_weekday integer;
  v_status jsonb;
  v_event_key text;
  v_latest public.workout_sessions%rowtype;
  v_limit integer := least(greatest(coalesce(p_limit, 50), 1), 200);
begin
  if not exists (
    select 1 from ai_private.phase6d_runtime_config c
    where c.singleton and c.scheduled_generation_enabled and c.mock_analyses_enabled and not c.external_provider_enabled
  ) then
    return jsonb_build_object('schema_version','phase6d.due-selection.v1','candidates','[]'::jsonb,'disabled',true);
  end if;
  for v_pref in
    select
      p.id as user_id,
      coalesce(ap.timezone_name, 'Europe/Amsterdam') as timezone_name,
      coalesce(ap.daily_enabled, true) as daily_enabled,
      coalesce(ap.daily_time, time '07:30') as daily_time,
      coalesce(ap.post_workout_enabled, true) as post_workout_enabled,
      coalesce(ap.weekly_enabled, true) as weekly_enabled,
      coalesce(ap.weekly_day, 1) as weekly_day,
      coalesce(ap.weekly_time, time '08:00') as weekly_time
    from public.profiles p
    left join public.ai_analysis_preferences ap on ap.user_id = p.id
    where p.role = 'client'
    order by p.id
  loop
    exit when jsonb_array_length(v_candidates) >= v_limit;
    if not exists (select 1 from pg_timezone_names where name = v_pref.timezone_name) then
      v_pref.timezone_name := 'Europe/Amsterdam';
    end if;
    v_local_date := (p_at at time zone v_pref.timezone_name)::date;
    v_local_time := (p_at at time zone v_pref.timezone_name)::time;
    v_weekday := extract(isodow from v_local_date)::integer;

    if v_pref.daily_enabled and v_local_time >= v_pref.daily_time then
      v_status := ai_private.phase6d_analysis_status(v_pref.user_id, 'daily', p_at);
      v_event_key := 'daily:' || v_local_date::text;
      if coalesce((v_status ->> 'analysis_allowed')::boolean, false)
         and not exists (
           select 1 from public.ai_analysis_results r
           where r.user_id = v_pref.user_id and r.analysis_kind = 'daily' and r.event_key = v_event_key
         ) then
        v_candidates := v_candidates || jsonb_build_array(jsonb_build_object('user_id', v_pref.user_id, 'analysis_kind', 'daily', 'event_key', v_event_key, 'model_tier', 'luna'));
      end if;
    end if;

    if jsonb_array_length(v_candidates) < v_limit and v_pref.weekly_enabled and v_weekday = v_pref.weekly_day and v_local_time >= v_pref.weekly_time then
      v_status := ai_private.phase6d_analysis_status(v_pref.user_id, 'weekly', p_at);
      v_event_key := 'weekly:' || (v_local_date - 6)::text || ':' || v_local_date::text;
      if coalesce((v_status ->> 'analysis_allowed')::boolean, false)
         and not exists (
           select 1 from public.ai_analysis_results r
           where r.user_id = v_pref.user_id and r.analysis_kind = 'weekly' and r.event_key = v_event_key
         ) then
        v_candidates := v_candidates || jsonb_build_array(jsonb_build_object('user_id', v_pref.user_id, 'analysis_kind', 'weekly', 'event_key', v_event_key, 'model_tier', 'terra'));
      end if;
    end if;

    if jsonb_array_length(v_candidates) < v_limit and v_pref.post_workout_enabled then
      select * into v_latest
      from public.workout_sessions w
      where w.user_id = v_pref.user_id and w.status = 'completed' and w.completed_at is not null
      order by w.completed_at desc, w.created_at desc
      limit 1;
      if v_latest.id is not null then
        v_status := ai_private.phase6d_analysis_status(v_pref.user_id, 'post_workout', p_at);
        v_event_key := 'post_workout:' || v_latest.id::text;
        if coalesce((v_status ->> 'analysis_allowed')::boolean, false)
           and not exists (
             select 1 from public.ai_analysis_results r
             where r.user_id = v_pref.user_id and r.analysis_kind = 'post_workout' and r.event_key = v_event_key
           ) then
          v_candidates := v_candidates || jsonb_build_array(jsonb_build_object('user_id', v_pref.user_id, 'analysis_kind', 'post_workout', 'event_key', v_event_key, 'event_id', v_latest.id, 'model_tier', 'luna'));
        end if;
      end if;
    end if;
  end loop;
  return jsonb_build_object('schema_version','phase6d.due-selection.v1','generated_at',p_at,'candidates',v_candidates,'disabled',false);
end;
$$;

create or replace function public.fmz_phase6d_service_select_due_analyses(p_limit integer default 50)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
begin
  return ai_private.phase6d_select_due_analyses(now(), p_limit);
end;
$$;

revoke all on all functions in schema ai_private from public, anon, authenticated;
revoke all on function public.fmz_phase6d_read_analysis_contract(text) from public, anon, authenticated;
revoke all on function public.fmz_phase6d_record_analysis_consent(text,text,text,boolean,uuid) from public, anon, authenticated;
revoke all on function public.fmz_phase6d_get_status() from public, anon, authenticated;
revoke all on function public.fmz_phase6d_update_preferences(text,boolean,text,boolean,boolean,smallint,text,bigint,uuid) from public, anon, authenticated;
revoke all on function public.fmz_phase6d_prepare_analysis(uuid,text,text,uuid) from public, anon, authenticated;
revoke all on function public.fmz_phase6d_service_begin_analysis(uuid,uuid,uuid,text,text,jsonb,text[]) from public, anon, authenticated;
revoke all on function public.fmz_phase6d_service_complete_analysis(uuid,uuid,jsonb,bigint,integer,integer) from public, anon, authenticated;
revoke all on function public.fmz_phase6d_service_fail_analysis(uuid,uuid,text) from public, anon, authenticated;
revoke all on function public.fmz_phase6d_list_analyses(integer,timestamptz,uuid) from public, anon, authenticated;
revoke all on function public.fmz_phase6d_delete_analysis(uuid,bigint,uuid) from public, anon, authenticated;
revoke all on function public.fmz_phase6d_export_analyses(uuid) from public, anon, authenticated;
revoke all on function public.fmz_phase6d_service_select_due_analyses(integer) from public, anon, authenticated;

grant execute on function public.fmz_phase6d_read_analysis_contract(text) to authenticated;
grant execute on function public.fmz_phase6d_record_analysis_consent(text,text,text,boolean,uuid) to authenticated;
grant execute on function public.fmz_phase6d_get_status() to authenticated;
grant execute on function public.fmz_phase6d_update_preferences(text,boolean,text,boolean,boolean,smallint,text,bigint,uuid) to authenticated;
grant execute on function public.fmz_phase6d_list_analyses(integer,timestamptz,uuid) to authenticated;
grant execute on function public.fmz_phase6d_delete_analysis(uuid,bigint,uuid) to authenticated;
grant execute on function public.fmz_phase6d_export_analyses(uuid) to authenticated;
grant execute on function public.fmz_phase6d_prepare_analysis(uuid,text,text,uuid) to authenticated;

grant execute on function public.fmz_phase6d_service_begin_analysis(uuid,uuid,uuid,text,text,jsonb,text[]) to service_role;
grant execute on function public.fmz_phase6d_service_complete_analysis(uuid,uuid,jsonb,bigint,integer,integer) to service_role;
grant execute on function public.fmz_phase6d_service_fail_analysis(uuid,uuid,text) to service_role;
grant execute on function public.fmz_phase6d_service_select_due_analyses(integer) to service_role;

select cron.schedule(
  'fmz-phase6d-analysis-retention-sweep',
  '*/15 * * * *',
  $cron$select ai_private.phase6d_retention_sweep(now());$cron$
);

commit;
