-- FitMetZorge Phase 6B provider/privacy/cost gate.
-- STAGING ONLY: mokxyyullfhkfalopbzd.
-- Provider tests are synthetic-only; real member processing remains fail-closed.

begin;

create table if not exists ai_private.provider_configurations (
  provider_code text primary key,
  environment text not null default 'staging',
  execution_mode text not null default 'synthetic_only',
  provider_enabled boolean not null default true,
  synthetic_calls_enabled boolean not null default true,
  real_member_processing_enabled boolean not null default false,
  zdr_status text not null default 'unverified',
  dpa_status text not null default 'incomplete',
  dpia_status text not null default 'incomplete',
  eu_route_status text not null default 'unverified',
  privacy_notice_status text not null default 'draft',
  consent_copy_status text not null default 'draft',
  transfer_assessment_status text not null default 'incomplete',
  lifecycle_verification_status text not null default 'incomplete',
  owner_real_member_activation boolean not null default false,
  synthetic_endpoint text not null default 'https://api.openai.com/v1/responses',
  real_member_endpoint text,
  checked_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint ai_provider_config_provider_check check (provider_code = 'openai'),
  constraint ai_provider_config_environment_check check (environment = 'staging'),
  constraint ai_provider_config_mode_check check (execution_mode in ('disabled','synthetic_only','real_member_blocked','zdr_verified')),
  constraint ai_provider_config_zdr_check check (zdr_status in ('unverified','requested','verified')),
  constraint ai_provider_config_completion_checks check (
    dpa_status in ('incomplete','pending_owner','complete')
    and dpia_status in ('incomplete','pending_owner','complete')
    and eu_route_status in ('unverified','requested','verified')
    and privacy_notice_status in ('draft','pending_owner','approved')
    and consent_copy_status in ('draft','pending_owner','approved')
    and transfer_assessment_status in ('incomplete','pending_owner','complete')
    and lifecycle_verification_status in ('incomplete','pending_owner','complete')
  ),
  constraint ai_provider_config_synthetic_endpoint_check
    check (synthetic_endpoint = 'https://api.openai.com/v1/responses'),
  constraint ai_provider_config_real_endpoint_check
    check (real_member_endpoint is null or real_member_endpoint = 'https://eu.api.openai.com/v1/responses'),
  constraint ai_provider_config_real_member_gate_check check (
    not real_member_processing_enabled
    or (
      provider_enabled
      and execution_mode = 'zdr_verified'
      and zdr_status = 'verified'
      and dpa_status = 'complete'
      and dpia_status = 'complete'
      and eu_route_status = 'verified'
      and privacy_notice_status = 'approved'
      and consent_copy_status = 'approved'
      and transfer_assessment_status = 'complete'
      and lifecycle_verification_status = 'complete'
      and owner_real_member_activation
      and real_member_endpoint = 'https://eu.api.openai.com/v1/responses'
    )
  )
);

create table if not exists ai_private.provider_models (
  provider_code text not null references ai_private.provider_configurations(provider_code) on delete restrict,
  model_route text not null,
  model_id text not null,
  availability_status text not null default 'officially_documented',
  responses_supported boolean not null,
  structured_outputs_supported boolean not null,
  input_usd_micros_per_million bigint not null,
  cached_input_usd_micros_per_million bigint not null,
  output_usd_micros_per_million bigint not null,
  max_test_input_tokens integer not null default 4096,
  max_test_output_tokens integer not null default 512,
  max_test_attempts integer not null default 2,
  enabled_for_synthetic boolean not null default true,
  enabled_for_real_member boolean not null default false,
  official_checked_on date not null,
  primary key (provider_code, model_route),
  unique (provider_code, model_id),
  constraint ai_provider_models_route_check check (model_route in ('luna','terra')),
  constraint ai_provider_models_id_check check (
    (model_route = 'luna' and model_id = 'gpt-5.6-luna')
    or (model_route = 'terra' and model_id = 'gpt-5.6-terra')
  ),
  constraint ai_provider_models_support_check check (responses_supported and structured_outputs_supported),
  constraint ai_provider_models_price_check check (
    (model_route = 'luna'
      and input_usd_micros_per_million = 200000
      and cached_input_usd_micros_per_million = 20000
      and output_usd_micros_per_million = 1200000)
    or
    (model_route = 'terra'
      and input_usd_micros_per_million = 2000000
      and cached_input_usd_micros_per_million = 200000
      and output_usd_micros_per_million = 12000000)
  ),
  constraint ai_provider_models_test_bounds_check check (
    max_test_input_tokens between 1 and 4096
    and max_test_output_tokens between 1 and 512
    and max_test_attempts between 1 and 2
  ),
  constraint ai_provider_models_real_member_disabled_check check (not enabled_for_real_member)
);

create table if not exists ai_private.provider_payload_fields (
  contract_version text not null,
  field_path text not null,
  purpose text not null,
  classification text not null,
  required boolean not null default false,
  primary key (contract_version, field_path),
  constraint ai_provider_payload_contract_check check (contract_version = 'phase6b.synthetic-payload.v1'),
  constraint ai_provider_payload_field_check check (field_path in (
    'schema_version','feature_code','locale','synthetic_subject_token',
    'snapshot.goal_code','snapshot.training.completed_sessions_7d',
    'snapshot.nutrition.average_energy_kcal_7d','snapshot.recovery.average_sleep_hours_7d',
    'request_purpose'
  )),
  constraint ai_provider_payload_classification_check check (classification in ('contract','synthetic_non_personal','aggregate_synthetic')),
  constraint ai_provider_payload_text_check check (
    char_length(btrim(purpose)) between 3 and 240
    and purpose !~* '(email|full name|address|phone|raw row|private chat|trainer note)'
  )
);

create table if not exists ai_private.provider_test_budget (
  policy_code text primary key,
  currency_code text not null default 'EUR',
  max_total_eur_micros bigint not null default 5000000,
  conservative_eur_per_usd_ppm bigint not null default 1250000,
  max_external_calls integer not null default 6,
  reserved_eur_micros bigint not null default 0,
  consumed_eur_micros bigint not null default 0,
  reserved_calls integer not null default 0,
  completed_calls integer not null default 0,
  updated_at timestamptz not null default now(),
  constraint ai_provider_test_budget_policy_check check (policy_code = 'phase6b-staging-v1'),
  constraint ai_provider_test_budget_currency_check check (currency_code = 'EUR'),
  constraint ai_provider_test_budget_fixed_check check (
    max_total_eur_micros = 5000000
    and conservative_eur_per_usd_ppm = 1250000
    and max_external_calls = 6
  ),
  constraint ai_provider_test_budget_amount_check check (
    reserved_eur_micros >= 0
    and consumed_eur_micros >= 0
    and reserved_eur_micros + consumed_eur_micros <= max_total_eur_micros
  ),
  constraint ai_provider_test_budget_call_check check (
    reserved_calls >= 0
    and completed_calls >= 0
    and reserved_calls + completed_calls <= max_external_calls
  )
);

create table if not exists ai_private.provider_test_runs (
  id uuid primary key,
  request_id uuid not null unique,
  fixture_code text not null,
  request_purpose text not null,
  provider_code text not null,
  model_route text not null,
  model_id text not null,
  payload_hash text not null,
  status text not null default 'reserved',
  reserved_eur_micros bigint not null,
  max_attempts integer not null,
  attempt_count integer,
  input_tokens integer,
  cached_input_tokens integer,
  output_tokens integer,
  actual_usd_micros bigint,
  actual_eur_micros bigint,
  response_hash text,
  provider_request_hash text,
  safe_error_code text,
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  foreign key (provider_code, model_route)
    references ai_private.provider_models(provider_code, model_route) on delete restrict,
  foreign key (provider_code, model_id)
    references ai_private.provider_models(provider_code, model_id) on delete restrict,
  constraint ai_provider_test_runs_fixture_check check (fixture_code in ('luna_connectivity_v1','terra_structured_v1')),
  constraint ai_provider_test_runs_purpose_check check (request_purpose in ('connectivity_and_contract','complex_route_contract')),
  constraint ai_provider_test_runs_model_fixture_check check (
    (fixture_code = 'luna_connectivity_v1' and request_purpose = 'connectivity_and_contract' and model_route = 'luna' and model_id = 'gpt-5.6-luna')
    or (fixture_code = 'terra_structured_v1' and request_purpose = 'complex_route_contract' and model_route = 'terra' and model_id = 'gpt-5.6-terra')
  ),
  constraint ai_provider_test_runs_hash_check check (
    payload_hash ~ '^[0-9a-f]{64}$'
    and (response_hash is null or response_hash ~ '^[0-9a-f]{64}$')
    and (provider_request_hash is null or provider_request_hash ~ '^[0-9a-f]{64}$')
  ),
  constraint ai_provider_test_runs_status_check check (status in ('reserved','completed','failed')),
  constraint ai_provider_test_runs_bounds_check check (
    reserved_eur_micros between 1 and 5000000
    and max_attempts between 1 and 2
    and (attempt_count is null or attempt_count between 0 and max_attempts)
    and (input_tokens is null or input_tokens between 0 and 4096 * max_attempts)
    and (cached_input_tokens is null or cached_input_tokens between 0 and coalesce(input_tokens, 0))
    and (output_tokens is null or output_tokens between 0 and 512 * max_attempts)
    and (actual_usd_micros is null or actual_usd_micros >= 0)
    and (actual_eur_micros is null or actual_eur_micros between 0 and reserved_eur_micros)
  ),
  constraint ai_provider_test_runs_safe_error_check check (
    safe_error_code is null
    or (safe_error_code ~ '^[a-z0-9_]{1,80}$' and safe_error_code !~ '(prompt|content|message|email|jwt|token|secret)')
  ),
  constraint ai_provider_test_runs_completion_check check (
    (status = 'reserved' and completed_at is null and actual_eur_micros is null)
    or (status = 'completed' and completed_at is not null and response_hash is not null and safe_error_code is null)
    or (status = 'failed' and completed_at is not null and safe_error_code is not null)
  )
);

create index if not exists ai_provider_test_runs_status_created_idx
  on ai_private.provider_test_runs(status, created_at desc);
create index if not exists ai_provider_test_runs_model_created_idx
  on ai_private.provider_test_runs(model_id, created_at desc);

alter table ai_private.provider_configurations enable row level security;
alter table ai_private.provider_models enable row level security;
alter table ai_private.provider_payload_fields enable row level security;
alter table ai_private.provider_test_budget enable row level security;
alter table ai_private.provider_test_runs enable row level security;

revoke all on table ai_private.provider_configurations from public, anon, authenticated;
revoke all on table ai_private.provider_models from public, anon, authenticated;
revoke all on table ai_private.provider_payload_fields from public, anon, authenticated;
revoke all on table ai_private.provider_test_budget from public, anon, authenticated;
revoke all on table ai_private.provider_test_runs from public, anon, authenticated;

insert into ai_private.provider_configurations(
  provider_code, environment, execution_mode, provider_enabled,
  synthetic_calls_enabled, real_member_processing_enabled,
  zdr_status, dpa_status, dpia_status, eu_route_status,
  privacy_notice_status, consent_copy_status, transfer_assessment_status,
  lifecycle_verification_status, owner_real_member_activation,
  synthetic_endpoint, real_member_endpoint, checked_at
) values (
  'openai', 'staging', 'synthetic_only', true,
  true, false,
  'unverified', 'incomplete', 'incomplete', 'unverified',
  'draft', 'draft', 'incomplete',
  'incomplete', false,
  'https://api.openai.com/v1/responses', null, now()
)
on conflict (provider_code) do nothing;

insert into ai_private.provider_models(
  provider_code, model_route, model_id, availability_status,
  responses_supported, structured_outputs_supported,
  input_usd_micros_per_million, cached_input_usd_micros_per_million,
  output_usd_micros_per_million, official_checked_on
) values
  ('openai','luna','gpt-5.6-luna','officially_documented',true,true,200000,20000,1200000,date '2026-09-01'),
  ('openai','terra','gpt-5.6-terra','officially_documented',true,true,2000000,200000,12000000,date '2026-09-01')
on conflict (provider_code, model_route) do update set
  model_id = excluded.model_id,
  availability_status = excluded.availability_status,
  responses_supported = excluded.responses_supported,
  structured_outputs_supported = excluded.structured_outputs_supported,
  input_usd_micros_per_million = excluded.input_usd_micros_per_million,
  cached_input_usd_micros_per_million = excluded.cached_input_usd_micros_per_million,
  output_usd_micros_per_million = excluded.output_usd_micros_per_million,
  official_checked_on = excluded.official_checked_on,
  enabled_for_real_member = false;

insert into ai_private.provider_payload_fields(contract_version, field_path, purpose, classification, required)
values
  ('phase6b.synthetic-payload.v1','schema_version','Validate the immutable synthetic request contract.','contract',true),
  ('phase6b.synthetic-payload.v1','feature_code','Select the reviewed AI response schema branch.','contract',true),
  ('phase6b.synthetic-payload.v1','locale','Test multilingual structured output without member identity.','contract',true),
  ('phase6b.synthetic-payload.v1','synthetic_subject_token','Pseudonymous unmistakably synthetic subject identifier.','synthetic_non_personal',true),
  ('phase6b.synthetic-payload.v1','snapshot.goal_code','Synthetic goal context required by the fixture.','synthetic_non_personal',true),
  ('phase6b.synthetic-payload.v1','snapshot.training.completed_sessions_7d','Synthetic aggregate for bounded coaching output.','aggregate_synthetic',true),
  ('phase6b.synthetic-payload.v1','snapshot.nutrition.average_energy_kcal_7d','Synthetic aggregate for bounded coaching output.','aggregate_synthetic',true),
  ('phase6b.synthetic-payload.v1','snapshot.recovery.average_sleep_hours_7d','Synthetic aggregate for bounded coaching output.','aggregate_synthetic',true),
  ('phase6b.synthetic-payload.v1','request_purpose','Auditable synthetic test purpose.','contract',true)
on conflict (contract_version, field_path) do update set
  purpose = excluded.purpose,
  classification = excluded.classification,
  required = excluded.required;

insert into ai_private.provider_test_budget(policy_code)
values ('phase6b-staging-v1')
on conflict (policy_code) do nothing;

create or replace function ai_private.phase6b_estimate_test_cost(
  p_model_id text,
  p_input_tokens integer,
  p_cached_input_tokens integer,
  p_output_tokens integer,
  p_attempt_count integer
)
returns table(usd_micros bigint, eur_micros bigint)
language plpgsql
stable
security invoker
set search_path = pg_catalog, ai_private, pg_temp
as $$
declare
  v_model ai_private.provider_models%rowtype;
  v_budget ai_private.provider_test_budget%rowtype;
begin
  select * into v_model from ai_private.provider_models m
  where m.provider_code = 'openai' and m.model_id = p_model_id;
  select * into v_budget from ai_private.provider_test_budget b
  where b.policy_code = 'phase6b-staging-v1';
  if v_model.model_id is null
     or p_attempt_count is null
     or p_input_tokens is null
     or p_cached_input_tokens is null
     or p_output_tokens is null
     or p_attempt_count not between 1 and v_model.max_test_attempts
     or p_input_tokens not between 0 and v_model.max_test_input_tokens * p_attempt_count
     or p_cached_input_tokens not between 0 and p_input_tokens
     or p_output_tokens not between 0 and v_model.max_test_output_tokens * p_attempt_count then
    raise exception 'ai_provider_usage_invalid' using errcode = '22023';
  end if;
  usd_micros := ceil((
    ((p_input_tokens - p_cached_input_tokens)::numeric * v_model.input_usd_micros_per_million)
    + (p_cached_input_tokens::numeric * v_model.cached_input_usd_micros_per_million)
    + (p_output_tokens::numeric * v_model.output_usd_micros_per_million)
  ) / 1000000)::bigint;
  eur_micros := ceil((usd_micros::numeric * v_budget.conservative_eur_per_usd_ppm) / 1000000)::bigint;
  return next;
end;
$$;

create or replace function ai_private.phase6b_real_member_gate()
returns jsonb
language sql
stable
security invoker
set search_path = pg_catalog, ai_private, pg_temp
as $$
  select jsonb_build_object(
    'allowed', false,
    'provider_code', c.provider_code,
    'execution_mode', c.execution_mode,
    'zdr_status', c.zdr_status,
    'dpa_status', c.dpa_status,
    'dpia_status', c.dpia_status,
    'eu_route_status', c.eu_route_status,
    'privacy_notice_status', c.privacy_notice_status,
    'consent_copy_status', c.consent_copy_status,
    'transfer_assessment_status', c.transfer_assessment_status,
    'lifecycle_verification_status', c.lifecycle_verification_status,
    'owner_real_member_activation', c.owner_real_member_activation,
    'deny_reason', 'real_member_provider_processing_blocked_phase6b'
  )
  from ai_private.provider_configurations c
  where c.provider_code = 'openai';
$$;

create or replace function public.fmz_phase6b_service_begin_synthetic_test(
  p_request_id uuid,
  p_fixture_code text,
  p_request_purpose text,
  p_model_route text,
  p_payload_hash text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, extensions, public, ai_private, pg_temp
as $$
declare
  v_config ai_private.provider_configurations%rowtype;
  v_model ai_private.provider_models%rowtype;
  v_budget ai_private.provider_test_budget%rowtype;
  v_existing ai_private.provider_test_runs%rowtype;
  v_run_id uuid := gen_random_uuid();
  v_reserve record;
begin
  if p_request_id is null
     or p_fixture_code is null
     or p_request_purpose is null
     or p_model_route is null
     or p_payload_hash is null
     or p_payload_hash !~ '^[0-9a-f]{64}$'
     or p_fixture_code not in ('luna_connectivity_v1','terra_structured_v1')
     or p_request_purpose not in ('connectivity_and_contract','complex_route_contract')
     or (p_fixture_code = 'luna_connectivity_v1' and (p_model_route <> 'luna' or p_request_purpose <> 'connectivity_and_contract'))
     or (p_fixture_code = 'terra_structured_v1' and (p_model_route <> 'terra' or p_request_purpose <> 'complex_route_contract')) then
    raise exception 'ai_provider_test_input_invalid' using errcode = '22023';
  end if;

  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6b_test_request:' || p_request_id::text, 0));
  select * into v_existing from ai_private.provider_test_runs r where r.request_id = p_request_id;
  if v_existing.id is not null then
    if v_existing.fixture_code <> p_fixture_code
       or v_existing.request_purpose <> p_request_purpose
       or v_existing.model_route <> p_model_route
       or v_existing.payload_hash <> p_payload_hash then
      raise exception 'ai_provider_test_request_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object(
      'replay', true, 'run_id', v_existing.id, 'status', v_existing.status,
      'model_id', v_existing.model_id, 'max_attempts', v_existing.max_attempts
    );
  end if;

  select * into v_config from ai_private.provider_configurations c where c.provider_code = 'openai';
  if not coalesce(v_config.provider_enabled, false)
     or not coalesce(v_config.synthetic_calls_enabled, false)
     or v_config.execution_mode <> 'synthetic_only'
     or v_config.real_member_processing_enabled then
    raise exception 'ai_provider_synthetic_disabled' using errcode = '42501';
  end if;
  select * into v_model from ai_private.provider_models m
  where m.provider_code = 'openai' and m.model_route = p_model_route and m.enabled_for_synthetic;
  if v_model.model_id is null then
    raise exception 'ai_provider_model_disabled' using errcode = '42501';
  end if;
  select * into v_reserve from ai_private.phase6b_estimate_test_cost(
    v_model.model_id,
    v_model.max_test_input_tokens * v_model.max_test_attempts,
    0,
    v_model.max_test_output_tokens * v_model.max_test_attempts,
    v_model.max_test_attempts
  );

  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6b_test_budget:phase6b-staging-v1', 0));
  select * into v_budget from ai_private.provider_test_budget b
  where b.policy_code = 'phase6b-staging-v1' for update;
  if v_budget.consumed_eur_micros + v_budget.reserved_eur_micros + v_reserve.eur_micros > v_budget.max_total_eur_micros then
    raise exception 'ai_provider_test_budget_exceeded' using errcode = '42501';
  end if;
  if v_budget.completed_calls + v_budget.reserved_calls + v_model.max_test_attempts > v_budget.max_external_calls then
    raise exception 'ai_provider_test_call_cap_exceeded' using errcode = '42501';
  end if;

  insert into ai_private.provider_test_runs(
    id, request_id, fixture_code, request_purpose, provider_code,
    model_route, model_id, payload_hash, reserved_eur_micros, max_attempts
  ) values (
    v_run_id, p_request_id, p_fixture_code, p_request_purpose, 'openai',
    v_model.model_route, v_model.model_id, p_payload_hash, v_reserve.eur_micros, v_model.max_test_attempts
  );
  update ai_private.provider_test_budget
  set reserved_eur_micros = reserved_eur_micros + v_reserve.eur_micros,
      reserved_calls = reserved_calls + v_model.max_test_attempts,
      updated_at = now()
  where policy_code = 'phase6b-staging-v1';

  return jsonb_build_object(
    'replay', false, 'run_id', v_run_id, 'status', 'reserved',
    'model_id', v_model.model_id, 'max_attempts', v_model.max_test_attempts,
    'max_input_tokens', v_model.max_test_input_tokens,
    'max_output_tokens', v_model.max_test_output_tokens,
    'store', false, 'tools_allowed', false
  );
end;
$$;

create or replace function public.fmz_phase6b_service_complete_synthetic_test(
  p_run_id uuid,
  p_attempt_count integer,
  p_input_tokens integer,
  p_cached_input_tokens integer,
  p_output_tokens integer,
  p_response_hash text,
  p_provider_request_hash text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, extensions, public, ai_private, pg_temp
as $$
declare
  v_run ai_private.provider_test_runs%rowtype;
  v_cost record;
begin
  if p_run_id is null
     or p_attempt_count is null
     or p_input_tokens is null
     or p_cached_input_tokens is null
     or p_output_tokens is null
     or p_response_hash is null
     or p_provider_request_hash is null
     or p_response_hash !~ '^[0-9a-f]{64}$'
     or p_provider_request_hash !~ '^[0-9a-f]{64}$' then
    raise exception 'ai_provider_test_completion_invalid' using errcode = '22023';
  end if;
  select * into v_run from ai_private.provider_test_runs r where r.id = p_run_id for update;
  if v_run.id is null then raise exception 'ai_provider_test_run_not_found' using errcode = '22023'; end if;
  if v_run.status = 'completed' then
    if v_run.attempt_count <> p_attempt_count
       or v_run.input_tokens <> p_input_tokens
       or v_run.cached_input_tokens <> p_cached_input_tokens
       or v_run.output_tokens <> p_output_tokens
       or v_run.response_hash <> p_response_hash
       or v_run.provider_request_hash <> p_provider_request_hash then
      raise exception 'ai_provider_test_completion_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'run_id', v_run.id, 'status', v_run.status, 'actual_eur_micros', v_run.actual_eur_micros);
  elsif v_run.status <> 'reserved' then
    raise exception 'ai_provider_test_not_completable' using errcode = '40001';
  end if;
  select * into v_cost from ai_private.phase6b_estimate_test_cost(
    v_run.model_id, p_input_tokens, p_cached_input_tokens, p_output_tokens, p_attempt_count
  );
  if v_cost.eur_micros > v_run.reserved_eur_micros then
    raise exception 'ai_provider_test_reservation_exceeded' using errcode = '42501';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6b_test_budget:phase6b-staging-v1', 0));
  update ai_private.provider_test_budget
  set reserved_eur_micros = reserved_eur_micros - v_run.reserved_eur_micros,
      consumed_eur_micros = consumed_eur_micros + v_cost.eur_micros,
      reserved_calls = reserved_calls - v_run.max_attempts,
      completed_calls = completed_calls + p_attempt_count,
      updated_at = now()
  where policy_code = 'phase6b-staging-v1';
  update ai_private.provider_test_runs
  set status = 'completed', attempt_count = p_attempt_count,
      input_tokens = p_input_tokens, cached_input_tokens = p_cached_input_tokens,
      output_tokens = p_output_tokens, actual_usd_micros = v_cost.usd_micros,
      actual_eur_micros = v_cost.eur_micros, response_hash = p_response_hash,
      provider_request_hash = p_provider_request_hash, completed_at = now()
  where id = v_run.id;
  return jsonb_build_object(
    'replay', false, 'run_id', v_run.id, 'status', 'completed',
    'actual_usd_micros', v_cost.usd_micros, 'actual_eur_micros', v_cost.eur_micros
  );
end;
$$;

create or replace function public.fmz_phase6b_service_fail_synthetic_test(
  p_run_id uuid,
  p_attempt_count integer,
  p_safe_error_code text,
  p_cost_unknown boolean default true
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, extensions, public, ai_private, pg_temp
as $$
declare
  v_run ai_private.provider_test_runs%rowtype;
  v_charge bigint;
begin
  if p_run_id is null
     or p_attempt_count is null
     or p_cost_unknown is null
     or p_safe_error_code is null
     or p_attempt_count not between 0 and 2
     or p_safe_error_code !~ '^[a-z0-9_]{1,80}$'
     or p_safe_error_code ~ '(prompt|content|message|email|jwt|token|secret)' then
    raise exception 'ai_provider_test_failure_invalid' using errcode = '22023';
  end if;
  select * into v_run from ai_private.provider_test_runs r where r.id = p_run_id for update;
  if v_run.id is null then raise exception 'ai_provider_test_run_not_found' using errcode = '22023'; end if;
  v_charge := case when p_cost_unknown and p_attempt_count > 0 then v_run.reserved_eur_micros else 0 end;
  if p_attempt_count > v_run.max_attempts then raise exception 'ai_provider_test_attempts_invalid' using errcode = '22023'; end if;
  if v_run.status = 'failed' then
    if v_run.attempt_count <> p_attempt_count
       or v_run.safe_error_code <> p_safe_error_code
       or v_run.actual_eur_micros <> v_charge then
      raise exception 'ai_provider_test_failure_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'run_id', v_run.id, 'status', v_run.status, 'charged_eur_micros', v_run.actual_eur_micros);
  elsif v_run.status <> 'reserved' then
    raise exception 'ai_provider_test_not_failable' using errcode = '40001';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6b_test_budget:phase6b-staging-v1', 0));
  update ai_private.provider_test_budget
  set reserved_eur_micros = reserved_eur_micros - v_run.reserved_eur_micros,
      consumed_eur_micros = consumed_eur_micros + v_charge,
      reserved_calls = reserved_calls - v_run.max_attempts,
      completed_calls = completed_calls + p_attempt_count,
      updated_at = now()
  where policy_code = 'phase6b-staging-v1';
  update ai_private.provider_test_runs
  set status = 'failed', attempt_count = p_attempt_count,
      actual_eur_micros = v_charge, safe_error_code = p_safe_error_code,
      completed_at = now()
  where id = v_run.id;
  return jsonb_build_object('replay', false, 'run_id', v_run.id, 'status', 'failed', 'charged_eur_micros', v_charge);
end;
$$;

create or replace function public.fmz_phase6b_service_read_provider_status()
returns jsonb
language sql
stable
security definer
set search_path = pg_catalog, extensions, public, ai_private, pg_temp
as $$
  select jsonb_build_object(
    'schema_version', 'phase6b.provider-status.v1',
    'provider_code', c.provider_code,
    'execution_mode', c.execution_mode,
    'synthetic_calls_enabled', c.synthetic_calls_enabled,
    'real_member_gate', ai_private.phase6b_real_member_gate(),
    'models', (
      select jsonb_agg(jsonb_build_object(
        'route', m.model_route, 'model_id', m.model_id,
        'availability_status', m.availability_status,
        'synthetic_enabled', m.enabled_for_synthetic,
        'real_member_enabled', m.enabled_for_real_member
      ) order by m.model_route)
      from ai_private.provider_models m where m.provider_code = c.provider_code
    ),
    'test_budget', (
      select jsonb_build_object(
        'max_eur_micros', b.max_total_eur_micros,
        'consumed_eur_micros', b.consumed_eur_micros,
        'reserved_eur_micros', b.reserved_eur_micros,
        'max_external_calls', b.max_external_calls,
        'completed_calls', b.completed_calls,
        'reserved_calls', b.reserved_calls
      ) from ai_private.provider_test_budget b where b.policy_code = 'phase6b-staging-v1'
    )
  )
  from ai_private.provider_configurations c where c.provider_code = 'openai';
$$;

revoke all on function ai_private.phase6b_estimate_test_cost(text,integer,integer,integer,integer) from public, anon, authenticated;
revoke all on function ai_private.phase6b_real_member_gate() from public, anon, authenticated;
revoke all on function public.fmz_phase6b_service_begin_synthetic_test(uuid,text,text,text,text) from public, anon, authenticated;
revoke all on function public.fmz_phase6b_service_complete_synthetic_test(uuid,integer,integer,integer,integer,text,text) from public, anon, authenticated;
revoke all on function public.fmz_phase6b_service_fail_synthetic_test(uuid,integer,text,boolean) from public, anon, authenticated;
revoke all on function public.fmz_phase6b_service_read_provider_status() from public, anon, authenticated;

grant execute on function public.fmz_phase6b_service_begin_synthetic_test(uuid,text,text,text,text) to service_role;
grant execute on function public.fmz_phase6b_service_complete_synthetic_test(uuid,integer,integer,integer,integer,text,text) to service_role;
grant execute on function public.fmz_phase6b_service_fail_synthetic_test(uuid,integer,text,boolean) to service_role;
grant execute on function public.fmz_phase6b_service_read_provider_status() to service_role;

drop trigger if exists ai_provider_config_touch_updated_at on ai_private.provider_configurations;
create trigger ai_provider_config_touch_updated_at
before update on ai_private.provider_configurations
for each row execute function ai_private.touch_updated_at();

drop trigger if exists ai_provider_test_budget_touch_updated_at on ai_private.provider_test_budget;
create trigger ai_provider_test_budget_touch_updated_at
before update on ai_private.provider_test_budget
for each row execute function ai_private.touch_updated_at();

commit;
