-- FitMetZorge Phase 6A AI trust foundation (STAGING first)
-- Provider-neutral contracts only: no paid provider, no provider key, no domain mutation.

begin;

do $$
begin
  if not exists (select 1 from pg_extension where extname = 'pgcrypto') then
    raise exception 'phase6a_requires_pgcrypto';
  end if;
end;
$$;

create schema if not exists ai_private;
revoke all on schema ai_private from public, anon, authenticated;

create table if not exists public.ai_consent_events (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  consent_kind text not null,
  consent_state text not null,
  document_version text not null,
  purpose_code text not null,
  categories text[] not null,
  locale text not null,
  explicit_confirmation boolean not null,
  request_id uuid not null,
  created_at timestamptz not null default now(),
  constraint ai_consent_events_kind_check
    check (consent_kind in ('ai_processing', 'trainer_summary_sharing')),
  constraint ai_consent_events_state_check
    check (consent_state in ('granted', 'withdrawn')),
  constraint ai_consent_events_version_check
    check (char_length(btrim(document_version)) between 1 and 80),
  constraint ai_consent_events_purpose_check
    check (char_length(btrim(purpose_code)) between 1 and 80),
  constraint ai_consent_events_categories_check
    check (cardinality(categories) between 1 and 24),
  constraint ai_consent_events_locale_check
    check (locale in ('nl', 'en', 'de')),
  constraint ai_consent_events_explicit_check
    check (explicit_confirmation is true),
  constraint ai_consent_events_user_request_unique unique (user_id, request_id)
);

create table if not exists public.ai_threads (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  feature_code text not null,
  locale text not null,
  status text not null default 'active',
  retention_state text not null default 'active',
  retention_started_at timestamptz,
  retention_due_at timestamptz,
  content_deleted_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint ai_threads_feature_check
    check (feature_code in ('private_chat', 'daily_analysis', 'weekly_checkin', 'post_workout')),
  constraint ai_threads_locale_check check (locale in ('nl', 'en', 'de')),
  constraint ai_threads_status_check check (status in ('active', 'archived', 'content_deleted')),
  constraint ai_threads_retention_state_check check (retention_state in ('active', 'grace', 'deleted')),
  constraint ai_threads_archive_state_check check (
    (status = 'active' and archived_at is null)
    or (status <> 'active' and archived_at is not null)
  ),
  constraint ai_threads_retention_window_check check (
    (retention_state = 'active' and retention_started_at is null and retention_due_at is null and content_deleted_at is null)
    or (retention_state = 'grace' and retention_started_at is not null and retention_due_at = retention_started_at + interval '90 days' and content_deleted_at is null)
    or (retention_state = 'deleted' and retention_started_at is not null and retention_due_at is not null and content_deleted_at is not null)
  ),
  constraint ai_threads_id_user_unique unique (id, user_id)
);

create table if not exists public.ai_messages (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  thread_id uuid not null references public.ai_threads(id) on delete cascade,
  message_role text not null,
  feature_code text not null,
  content_text text,
  structured_output jsonb,
  schema_version text,
  status text not null default 'active',
  request_id uuid not null,
  run_id uuid,
  created_at timestamptz not null default now(),
  constraint ai_messages_role_check check (message_role in ('user', 'assistant', 'system_notice')),
  constraint ai_messages_feature_check
    check (feature_code in ('private_chat', 'daily_analysis', 'weekly_checkin', 'post_workout')),
  constraint ai_messages_content_check check (
    (status = 'active' and content_text is not null and char_length(content_text) between 1 and 8000)
    or (status = 'deleted' and content_text is null and structured_output is null)
  ),
  constraint ai_messages_status_check check (status in ('active', 'deleted')),
  constraint ai_messages_structured_role_check check (
    (message_role = 'assistant' and schema_version is not null and structured_output is not null)
    or (message_role <> 'assistant' and schema_version is null and structured_output is null)
    or status = 'deleted'
  ),
  constraint ai_messages_thread_owner_fk foreign key (thread_id, user_id)
    references public.ai_threads(id, user_id) on delete cascade,
  constraint ai_messages_request_role_unique unique (user_id, request_id, message_role)
);

create table if not exists public.ai_context_manifests (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  feature_code text not null,
  manifest_version text not null,
  context_hash text not null,
  sources jsonb not null,
  unavailable_sources text[] not null default '{}',
  source_cutoff_at timestamptz not null,
  created_at timestamptz not null default now(),
  constraint ai_context_manifests_feature_check
    check (feature_code in ('private_chat', 'daily_analysis', 'weekly_checkin', 'post_workout')),
  constraint ai_context_manifests_version_check
    check (char_length(btrim(manifest_version)) between 1 and 80),
  constraint ai_context_manifests_hash_check check (context_hash ~ '^[0-9a-f]{64}$'),
  constraint ai_context_manifests_sources_check
    check (jsonb_typeof(sources) = 'object' and pg_column_size(sources) <= 32768),
  constraint ai_context_manifests_id_user_unique unique (id, user_id)
);

create table if not exists public.ai_action_proposals (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  context_manifest_id uuid not null references public.ai_context_manifests(id) on delete restrict,
  action_code text not null,
  proposed_change jsonb not null,
  expected_source_versions jsonb not null,
  explanation text not null,
  safety_class text not null,
  status text not null default 'pending',
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint ai_action_proposals_action_check check (action_code in (
    'training_volume_adjustment', 'add_rest_day', 'reschedule_training',
    'replace_exercise', 'calorie_target_adjustment'
  )),
  constraint ai_action_proposals_change_check
    check (jsonb_typeof(proposed_change) = 'object' and pg_column_size(proposed_change) <= 16384),
  constraint ai_action_proposals_versions_check
    check (jsonb_typeof(expected_source_versions) = 'object' and pg_column_size(expected_source_versions) <= 16384),
  constraint ai_action_proposals_explanation_check check (char_length(explanation) between 1 and 2000),
  constraint ai_action_proposals_safety_check check (safety_class in ('normal', 'deload', 'fatigue_reduction')),
  constraint ai_action_proposals_status_check check (status in ('pending', 'approved', 'rejected', 'expired', 'superseded', 'blocked')),
  constraint ai_action_proposals_expiry_check check (expires_at > created_at),
  constraint ai_action_proposals_context_owner_fk foreign key (context_manifest_id, user_id)
    references public.ai_context_manifests(id, user_id) on delete restrict,
  constraint ai_action_proposals_id_user_unique unique (id, user_id)
);

create table if not exists public.ai_action_decisions (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  proposal_id uuid not null references public.ai_action_proposals(id) on delete restrict,
  decision_type text not null,
  decision_source text not null,
  reason_code text not null,
  request_id uuid not null,
  created_at timestamptz not null default now(),
  constraint ai_action_decisions_type_check check (decision_type in ('approve', 'reject', 'expire', 'supersede', 'block', 'execution_result')),
  constraint ai_action_decisions_source_check check (decision_source in ('member', 'trainer', 'system')),
  constraint ai_action_decisions_reason_check check (char_length(btrim(reason_code)) between 1 and 80),
  constraint ai_action_decisions_proposal_owner_fk foreign key (proposal_id, user_id)
    references public.ai_action_proposals(id, user_id) on delete restrict,
  constraint ai_action_decisions_user_request_unique unique (user_id, request_id)
);

create table if not exists public.ai_member_safety_state (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  safety_status text not null default 'clear',
  risk_category text,
  blocked_at timestamptz,
  resolved_at timestamptz,
  resolution_code text,
  revision bigint not null default 1,
  updated_at timestamptz not null default now(),
  constraint ai_member_safety_state_status_check check (safety_status in ('clear', 'hard_stop', 'review_required', 'resolved')),
  constraint ai_member_safety_state_risk_check check (risk_category is null or risk_category in ('serious_health', 'unclear_health', 'injury', 'eating_disorder', 'other')),
  constraint ai_member_safety_state_consistency_check check (
    (safety_status = 'clear' and risk_category is null and blocked_at is null and resolved_at is null and resolution_code is null)
    or (safety_status in ('hard_stop', 'review_required') and risk_category is not null and blocked_at is not null and resolved_at is null and resolution_code is null)
    or (safety_status = 'resolved' and risk_category is not null and blocked_at is not null and resolved_at is not null and resolution_code is not null)
  )
);

create table if not exists public.ai_data_lifecycle_requests (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  request_type text not null,
  status text not null default 'requested',
  request_id uuid not null,
  requested_at timestamptz not null default now(),
  completed_at timestamptz,
  safe_result_code text,
  constraint ai_data_lifecycle_requests_type_check check (request_type in ('export', 'delete')),
  constraint ai_data_lifecycle_requests_status_check check (status in ('requested', 'processing', 'completed', 'failed')),
  constraint ai_data_lifecycle_requests_result_check check (
    (status in ('requested', 'processing') and completed_at is null and safe_result_code is null)
    or (status in ('completed', 'failed') and completed_at is not null and safe_result_code is not null)
  ),
  constraint ai_data_lifecycle_requests_user_request_unique unique (user_id, request_id)
);

create table if not exists ai_private.consent_documents (
  consent_kind text not null,
  document_version text not null,
  locale text not null,
  purpose_code text not null,
  categories text[] not null,
  content_text text not null,
  content_sha256 text not null,
  status text not null default 'active',
  effective_at timestamptz not null,
  created_at timestamptz not null default now(),
  primary key (consent_kind, document_version, locale),
  constraint ai_consent_documents_kind_check check (consent_kind in ('ai_processing', 'trainer_summary_sharing')),
  constraint ai_consent_documents_locale_check check (locale in ('nl', 'en', 'de')),
  constraint ai_consent_documents_status_check check (status in ('draft', 'active', 'retired')),
  constraint ai_consent_documents_hash_check check (content_sha256 ~ '^[0-9a-f]{64}$'),
  constraint ai_consent_documents_content_check check (char_length(content_text) between 40 and 4000)
);

create table if not exists ai_private.feature_flags (
  flag_code text primary key,
  enabled boolean not null default false,
  environment text not null default 'staging',
  reason_code text not null,
  updated_at timestamptz not null default now(),
  constraint ai_feature_flags_code_check check (flag_code in ('ai_coach_enabled', 'provider_calls_enabled', 'staging_mock_enabled')),
  constraint ai_feature_flags_environment_check check (environment = 'staging')
);

create table if not exists ai_private.budget_policies (
  policy_version text primary key,
  currency_code text not null,
  included_micros bigint not null,
  warning_micros bigint not null,
  grace_micros bigint not null,
  hard_cap_micros bigint not null,
  terra_stop_micros bigint not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  constraint ai_budget_policy_currency_check check (currency_code = 'EUR'),
  constraint ai_budget_policy_values_check check (
    included_micros = 3000000
    and warning_micros = 2400000
    and grace_micros = 1000000
    and hard_cap_micros = 4000000
    and terra_stop_micros = 3000000
  )
);

create table if not exists ai_private.rate_policies (
  feature_code text primary key,
  window_seconds integer not null,
  max_requests integer not null,
  active boolean not null default true,
  constraint ai_rate_policies_feature_check
    check (feature_code in ('private_chat', 'daily_analysis', 'weekly_checkin', 'post_workout')),
  constraint ai_rate_policies_bounds_check check (window_seconds between 60 and 604800 and max_requests between 1 and 100)
);

create table if not exists ai_private.action_policies (
  action_code text primary key,
  enabled boolean not null default true,
  max_increase_percent numeric(6,2),
  max_decrease_percent numeric(6,2),
  max_absolute_delta numeric(10,2),
  requires_explanation boolean not null default true,
  requires_reversible boolean not null default true,
  policy_metadata jsonb not null default '{}',
  constraint ai_action_policies_code_check check (action_code in (
    'training_volume_adjustment', 'add_rest_day', 'reschedule_training',
    'replace_exercise', 'calorie_target_adjustment'
  )),
  constraint ai_action_policies_bounds_check check (
    (max_increase_percent is null or max_increase_percent between 0 and 100)
    and (max_decrease_percent is null or max_decrease_percent between 0 and 100)
    and (max_absolute_delta is null or max_absolute_delta >= 0)
  )
);

create table if not exists ai_private.structured_schemas (
  schema_code text not null,
  schema_version text not null,
  schema_body jsonb not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  primary key (schema_code, schema_version),
  constraint ai_structured_schemas_body_check
    check (jsonb_typeof(schema_body) = 'object' and pg_column_size(schema_body) <= 32768)
);

create table if not exists ai_private.runs (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  request_id uuid not null,
  thread_id uuid references public.ai_threads(id) on delete set null,
  context_manifest_id uuid references public.ai_context_manifests(id) on delete restrict,
  feature_code text not null,
  adapter_code text not null,
  model_tier text not null,
  policy_version text not null,
  schema_version text not null,
  payload_hash text not null,
  status text not null default 'reserved',
  reserved_cost_micros bigint not null default 0,
  actual_cost_micros bigint,
  input_tokens integer,
  output_tokens integer,
  response_hash text,
  safe_error_code text,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  constraint ai_runs_feature_check
    check (feature_code in ('private_chat', 'daily_analysis', 'weekly_checkin', 'post_workout')),
  constraint ai_runs_adapter_check check (adapter_code in ('mock', 'provider')),
  constraint ai_runs_model_tier_check check (model_tier in ('luna', 'terra')),
  constraint ai_runs_hash_check check (payload_hash ~ '^[0-9a-f]{64}$'),
  constraint ai_runs_response_hash_check check (response_hash is null or response_hash ~ '^[0-9a-f]{64}$'),
  constraint ai_runs_status_check check (status in ('reserved', 'completed', 'failed', 'blocked')),
  constraint ai_runs_cost_check check (
    reserved_cost_micros between 0 and 4000000
    and (actual_cost_micros is null or actual_cost_micros between 0 and 4000000)
  ),
  constraint ai_runs_tokens_check check (
    (input_tokens is null or input_tokens between 0 and 1000000)
    and (output_tokens is null or output_tokens between 0 and 1000000)
  ),
  constraint ai_runs_completion_check check (
    (status = 'reserved' and completed_at is null and actual_cost_micros is null and response_hash is null and safe_error_code is null)
    or (status = 'completed' and completed_at is not null and actual_cost_micros is not null and response_hash is not null and safe_error_code is null)
    or (status in ('failed', 'blocked') and completed_at is not null and response_hash is null and safe_error_code is not null)
  ),
  constraint ai_runs_thread_owner_fk foreign key (thread_id, user_id)
    references public.ai_threads(id, user_id) on delete restrict,
  constraint ai_runs_context_owner_fk foreign key (context_manifest_id, user_id)
    references public.ai_context_manifests(id, user_id) on delete restrict,
  constraint ai_runs_user_request_unique unique (user_id, request_id)
);

create table if not exists ai_private.budget_accounts (
  user_id uuid not null references public.profiles(id) on delete cascade,
  period_start timestamptz not null,
  period_end timestamptz not null,
  policy_version text not null references ai_private.budget_policies(policy_version) on delete restrict,
  consumed_micros bigint not null default 0,
  reserved_micros bigint not null default 0,
  warning_issued_at timestamptz,
  hard_stopped_at timestamptz,
  updated_at timestamptz not null default now(),
  primary key (user_id, period_start),
  constraint ai_budget_accounts_period_check check (period_end > period_start),
  constraint ai_budget_accounts_amount_check check (consumed_micros >= 0 and reserved_micros >= 0 and consumed_micros + reserved_micros <= 4000000)
);

create table if not exists ai_private.usage_ledger (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  run_id uuid not null references ai_private.runs(id) on delete restrict,
  request_id uuid not null,
  feature_code text not null,
  model_tier text not null,
  ledger_type text not null,
  amount_micros bigint not null,
  created_at timestamptz not null default now(),
  constraint ai_usage_ledger_feature_check
    check (feature_code in ('private_chat', 'daily_analysis', 'weekly_checkin', 'post_workout')),
  constraint ai_usage_ledger_model_check check (model_tier in ('luna', 'terra')),
  constraint ai_usage_ledger_type_check check (ledger_type in ('reserve', 'actual', 'release')),
  constraint ai_usage_ledger_amount_check check (amount_micros >= 0),
  constraint ai_usage_ledger_run_type_unique unique (run_id, ledger_type)
);

create table if not exists ai_private.rate_buckets (
  user_id uuid not null references public.profiles(id) on delete cascade,
  feature_code text not null,
  window_started_at timestamptz not null,
  window_seconds integer not null,
  request_count integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key (user_id, feature_code, window_started_at),
  constraint ai_rate_buckets_feature_check
    check (feature_code in ('private_chat', 'daily_analysis', 'weekly_checkin', 'post_workout')),
  constraint ai_rate_buckets_values_check check (window_seconds between 60 and 604800 and request_count between 0 and 10000)
);

create table if not exists ai_private.safety_events (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  run_id uuid references ai_private.runs(id) on delete set null,
  risk_category text not null,
  safety_outcome text not null,
  policy_version text not null,
  created_at timestamptz not null default now(),
  constraint ai_safety_events_category_check check (risk_category in ('serious_health', 'unclear_health', 'injury', 'eating_disorder', 'other')),
  constraint ai_safety_events_outcome_check check (safety_outcome in ('hard_stop', 'review_required', 'resolved')),
  constraint ai_safety_events_no_raw_content_check check (char_length(policy_version) between 1 and 80)
);

create table if not exists ai_private.audit_events (
  id uuid primary key,
  user_id uuid references public.profiles(id) on delete cascade,
  run_id uuid references ai_private.runs(id) on delete set null,
  event_code text not null,
  safe_metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  constraint ai_audit_events_code_check check (char_length(event_code) between 1 and 80),
  constraint ai_audit_events_metadata_check check (
    jsonb_typeof(safe_metadata) = 'object'
    and pg_column_size(safe_metadata) <= 8192
    and not (safe_metadata ?| array['prompt', 'content', 'message', 'email', 'jwt', 'token', 'secret'])
  )
);

create index if not exists ai_consent_events_current_idx
  on public.ai_consent_events(user_id, consent_kind, created_at desc, id desc);
create index if not exists ai_threads_user_history_idx
  on public.ai_threads(user_id, updated_at desc, id desc);
create index if not exists ai_threads_retention_due_idx
  on public.ai_threads(retention_due_at)
  where retention_state = 'grace';
create index if not exists ai_messages_thread_history_idx
  on public.ai_messages(thread_id, created_at desc, id desc);
create index if not exists ai_context_manifests_user_feature_idx
  on public.ai_context_manifests(user_id, feature_code, created_at desc);
create index if not exists ai_action_proposals_user_status_idx
  on public.ai_action_proposals(user_id, status, created_at desc);
create index if not exists ai_action_decisions_proposal_idx
  on public.ai_action_decisions(proposal_id, created_at);
create index if not exists ai_lifecycle_requests_user_idx
  on public.ai_data_lifecycle_requests(user_id, requested_at desc);
create index if not exists ai_runs_user_status_idx
  on ai_private.runs(user_id, status, started_at desc);
create index if not exists ai_budget_accounts_period_end_idx
  on ai_private.budget_accounts(period_end);
create index if not exists ai_usage_ledger_user_created_idx
  on ai_private.usage_ledger(user_id, created_at desc);
create index if not exists ai_rate_buckets_updated_idx
  on ai_private.rate_buckets(updated_at);
create index if not exists ai_safety_events_user_created_idx
  on ai_private.safety_events(user_id, created_at desc);
create index if not exists ai_audit_events_user_created_idx
  on ai_private.audit_events(user_id, created_at desc);

alter table public.ai_consent_events enable row level security;
alter table public.ai_threads enable row level security;
alter table public.ai_messages enable row level security;
alter table public.ai_context_manifests enable row level security;
alter table public.ai_action_proposals enable row level security;
alter table public.ai_action_decisions enable row level security;
alter table public.ai_member_safety_state enable row level security;
alter table public.ai_data_lifecycle_requests enable row level security;

alter table ai_private.consent_documents enable row level security;
alter table ai_private.feature_flags enable row level security;
alter table ai_private.budget_policies enable row level security;
alter table ai_private.rate_policies enable row level security;
alter table ai_private.action_policies enable row level security;
alter table ai_private.structured_schemas enable row level security;
alter table ai_private.runs enable row level security;
alter table ai_private.budget_accounts enable row level security;
alter table ai_private.usage_ledger enable row level security;
alter table ai_private.rate_buckets enable row level security;
alter table ai_private.safety_events enable row level security;
alter table ai_private.audit_events enable row level security;

drop policy if exists ai_consent_events_select_own on public.ai_consent_events;
create policy ai_consent_events_select_own on public.ai_consent_events
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists ai_threads_select_own on public.ai_threads;
create policy ai_threads_select_own on public.ai_threads
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists ai_messages_select_own on public.ai_messages;
create policy ai_messages_select_own on public.ai_messages
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists ai_context_manifests_select_own on public.ai_context_manifests;
create policy ai_context_manifests_select_own on public.ai_context_manifests
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists ai_action_proposals_select_own on public.ai_action_proposals;
create policy ai_action_proposals_select_own on public.ai_action_proposals
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists ai_action_decisions_select_own on public.ai_action_decisions;
create policy ai_action_decisions_select_own on public.ai_action_decisions
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists ai_member_safety_state_select_own on public.ai_member_safety_state;
create policy ai_member_safety_state_select_own on public.ai_member_safety_state
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));
drop policy if exists ai_data_lifecycle_requests_select_own on public.ai_data_lifecycle_requests;
create policy ai_data_lifecycle_requests_select_own on public.ai_data_lifecycle_requests
  for select to authenticated
  using ((select auth.uid()) is not null and user_id = (select auth.uid()));

revoke all on table public.ai_consent_events from public, anon, authenticated;
revoke all on table public.ai_threads from public, anon, authenticated;
revoke all on table public.ai_messages from public, anon, authenticated;
revoke all on table public.ai_context_manifests from public, anon, authenticated;
revoke all on table public.ai_action_proposals from public, anon, authenticated;
revoke all on table public.ai_action_decisions from public, anon, authenticated;
revoke all on table public.ai_member_safety_state from public, anon, authenticated;
revoke all on table public.ai_data_lifecycle_requests from public, anon, authenticated;

revoke all on all tables in schema ai_private from public, anon, authenticated;
revoke all on all sequences in schema ai_private from public, anon, authenticated;

insert into ai_private.feature_flags(flag_code, enabled, environment, reason_code)
values
  ('ai_coach_enabled', false, 'staging', 'phase6a_owner_review_required'),
  ('provider_calls_enabled', false, 'staging', 'phase6b_not_started'),
  ('staging_mock_enabled', false, 'staging', 'explicit_safe_test_flag_required')
on conflict (flag_code) do update
set enabled = false,
    environment = excluded.environment,
    reason_code = excluded.reason_code,
    updated_at = now();

insert into ai_private.budget_policies(
  policy_version, currency_code, included_micros, warning_micros,
  grace_micros, hard_cap_micros, terra_stop_micros, active
)
values ('phase6a-budget-v1', 'EUR', 3000000, 2400000, 1000000, 4000000, 3000000, true)
on conflict (policy_version) do nothing;

insert into ai_private.rate_policies(feature_code, window_seconds, max_requests, active)
values
  ('private_chat', 300, 12, true),
  ('daily_analysis', 86400, 2, true),
  ('weekly_checkin', 604800, 2, true),
  ('post_workout', 86400, 10, true)
on conflict (feature_code) do nothing;

insert into ai_private.action_policies(
  action_code, max_increase_percent, max_decrease_percent, max_absolute_delta, policy_metadata
)
values
  ('training_volume_adjustment', 20, 100, null, '{"large_reduction_requires":["fatigue","deload"]}'::jsonb),
  ('add_rest_day', null, null, null, '{"domain":"training"}'::jsonb),
  ('reschedule_training', null, null, null, '{"domain":"training"}'::jsonb),
  ('replace_exercise', null, null, null, '{"compatible_alternative_required":true}'::jsonb),
  ('calorie_target_adjustment', 10, 10, 300, '{"new_authoritative_data_required":true,"safe_minima_remain_domain_authority":true}'::jsonb)
on conflict (action_code) do nothing;

with consent_copy(consent_kind, document_version, locale, purpose_code, categories, content_text) as (
  values
    ('ai_processing'::text, 'phase6a-ai-processing-v1'::text, 'nl'::text, 'youri_ai_coaching_v1'::text,
      array['activity','goals','health_limitations','nutrition','onboarding','profile','progress','recovery','sleep','training','workout_performance']::text[],
      'Ik geef apart en uitdrukkelijk toestemming dat FitMetZorge de genoemde profiel-, doel-, training-, voedings-, herstel-, slaap-, activiteits-, voortgangs-, prestatie- en relevante gezondheids- of beperkingsgegevens gebruikt voor Youri AI coaching. Ik kan deze toestemming altijd intrekken zonder de gewone app te verliezen.'::text),
    ('ai_processing', 'phase6a-ai-processing-v1', 'en', 'youri_ai_coaching_v1',
      array['activity','goals','health_limitations','nutrition','onboarding','profile','progress','recovery','sleep','training','workout_performance']::text[],
      'I separately and explicitly consent to FitMetZorge using the listed profile, goal, training, nutrition, recovery, sleep, activity, progress, performance and relevant health or limitation data for Youri AI coaching. I can withdraw this consent at any time without losing the non-AI app.'),
    ('ai_processing', 'phase6a-ai-processing-v1', 'de', 'youri_ai_coaching_v1',
      array['activity','goals','health_limitations','nutrition','onboarding','profile','progress','recovery','sleep','training','workout_performance']::text[],
      'Ich willige separat und ausdrucklich ein, dass FitMetZorge die aufgefuhrten Profil-, Ziel-, Trainings-, Ernahrungs-, Erholungs-, Schlaf-, Aktivitats-, Fortschritts-, Leistungs- und relevanten Gesundheits- oder Einschrankungsdaten fur Youri AI Coaching nutzt. Ich kann diese Einwilligung jederzeit widerrufen, ohne die normale App zu verlieren.'),
    ('trainer_summary_sharing', 'phase6a-trainer-summary-v1', 'nl', 'trainer_summary_sharing_v1',
      array['minimized_trainer_summary']::text[],
      'Ik geef apart en uitdrukkelijk toestemming om uitsluitend geminimaliseerde relevante samenvattingen, signalen, veranderingen en uitleg met mijn gekoppelde trainer te delen. Mijn privechat wordt nooit gedeeld. Ik kan deze toestemming altijd intrekken.'),
    ('trainer_summary_sharing', 'phase6a-trainer-summary-v1', 'en', 'trainer_summary_sharing_v1',
      array['minimized_trainer_summary']::text[],
      'I separately and explicitly consent to sharing only minimized relevant summaries, signals, changes and explanations with my linked trainer. My private chat is never shared. I can withdraw this consent at any time.'),
    ('trainer_summary_sharing', 'phase6a-trainer-summary-v1', 'de', 'trainer_summary_sharing_v1',
      array['minimized_trainer_summary']::text[],
      'Ich willige separat und ausdrucklich ein, dass nur minimierte relevante Zusammenfassungen, Signale, Anderungen und Erklarungen mit meinem verbundenen Trainer geteilt werden. Mein privater Chat wird niemals geteilt. Ich kann diese Einwilligung jederzeit widerrufen.')
)
insert into ai_private.consent_documents(
  consent_kind, document_version, locale, purpose_code, categories,
  content_text, content_sha256, status, effective_at
)
select consent_kind, document_version, locale, purpose_code, categories,
  content_text, encode(digest(convert_to(content_text, 'UTF8'), 'sha256'), 'hex'),
  'active', timestamptz '2026-09-01 00:00:00+00'
from consent_copy
on conflict (consent_kind, document_version, locale) do nothing;

insert into ai_private.structured_schemas(schema_code, schema_version, schema_body, active)
values (
  'coach_response',
  'phase6a.response.v1',
  '{
    "type":"object",
    "additionalProperties":false,
    "required":["schema_version","feature_code","summary","observations","uncertainties","recommendations","actions","safety"],
    "properties":{
      "schema_version":{"const":"phase6a.response.v1"},
      "feature_code":{"enum":["private_chat","daily_analysis","weekly_checkin","post_workout"]},
      "summary":{"type":"string","maxLength":2000},
      "observations":{"type":"array","maxItems":12},
      "uncertainties":{"type":"array","maxItems":12},
      "recommendations":{"type":"array","maxItems":12},
      "actions":{"type":"array","maxItems":8},
      "safety":{"type":"object"}
    }
  }'::jsonb,
  true
)
on conflict (schema_code, schema_version) do nothing;

create or replace function ai_private.touch_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create or replace function ai_private.assert_member(p_user_id uuid)
returns void
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
begin
  if p_user_id is null or not exists (
    select 1 from public.profiles p where p.id = p_user_id and p.role = 'client'
  ) then
    raise exception 'ai_member_required' using errcode = '42501';
  end if;
end;
$$;

create or replace function ai_private.current_entitlement(
  p_user_id uuid,
  p_at timestamptz default now()
)
returns table (
  entitlement_code text,
  entitlement_source text,
  entitlement_started_at timestamptz,
  entitlement_ends_at timestamptz
)
language sql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
  select e.entitlement_code, e.source, e.starts_at, e.ends_at
  from public.entitlements e
  where e.user_id = p_user_id
    and e.entitlement_code in ('ai', 'personal_coaching')
    and e.status = 'active'
    and e.starts_at <= p_at
    and (e.ends_at is null or e.ends_at > p_at)
  order by
    case e.entitlement_code when 'personal_coaching' then 0 else 1 end,
    e.starts_at desc,
    e.source
  limit 1;
$$;

create or replace function ai_private.current_consent(
  p_user_id uuid,
  p_consent_kind text
)
returns table (
  consent_state text,
  document_version text,
  purpose_code text,
  categories text[],
  locale text,
  consented_at timestamptz,
  document_active boolean
)
language sql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
  select e.consent_state, e.document_version, e.purpose_code, e.categories,
    e.locale, e.created_at,
    exists (
      select 1
      from ai_private.consent_documents d
      where d.consent_kind = e.consent_kind
        and d.document_version = e.document_version
        and d.locale = e.locale
        and d.status = 'active'
        and d.effective_at <= now()
    )
  from public.ai_consent_events e
  where e.user_id = p_user_id
    and e.consent_kind = p_consent_kind
  order by e.created_at desc, e.id desc
  limit 1;
$$;

create or replace function ai_private.subscription_period(
  p_anchor timestamptz,
  p_at timestamptz default now()
)
returns table (period_start timestamptz, period_end timestamptz)
language plpgsql
stable
security invoker
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_months integer;
begin
  if p_anchor is null or p_at < p_anchor then
    return;
  end if;
  v_months := greatest(
    0,
    extract(year from age(p_at, p_anchor))::integer * 12
      + extract(month from age(p_at, p_anchor))::integer
  );
  period_start := p_anchor + make_interval(months => v_months);
  if period_start > p_at then
    v_months := greatest(0, v_months - 1);
    period_start := p_anchor + make_interval(months => v_months);
  end if;
  period_end := p_anchor + make_interval(months => v_months + 1);
  return next;
end;
$$;

create or replace function ai_private.evaluate_budget(
  p_consumed_micros bigint,
  p_reserved_micros bigint,
  p_requested_micros bigint,
  p_model_tier text
)
returns jsonb
language plpgsql
immutable
security invoker
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_total bigint;
  v_allowed boolean;
  v_reason text;
  v_band text;
begin
  if p_consumed_micros < 0 or p_reserved_micros < 0
     or p_requested_micros < 0 or p_requested_micros > 4000000
     or p_model_tier not in ('luna', 'terra') then
    raise exception 'ai_budget_input_invalid' using errcode = '22023';
  end if;
  v_total := p_consumed_micros + p_reserved_micros + p_requested_micros;
  v_allowed := v_total <= 4000000
    and not (p_model_tier = 'terra' and v_total > 3000000);
  v_reason := case
    when v_total > 4000000 then 'budget_hard_stop'
    when p_model_tier = 'terra' and v_total > 3000000 then 'terra_grace_forbidden'
    else 'allowed'
  end;
  v_band := case
    when v_total >= 4000000 then 'blocked'
    when v_total > 3000000 then 'grace'
    when v_total >= 2400000 then 'warning'
    else 'normal'
  end;
  return jsonb_build_object(
    'allowed', v_allowed,
    'reason', v_reason,
    'fair_use_status', v_band,
    'automatic_billing', false
  );
end;
$$;

create or replace function ai_private.validate_action_contract(
  p_action_code text,
  p_payload jsonb
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_enabled boolean;
  v_valid boolean := false;
  v_reason text := 'action_not_allowed';
  v_delta_percent numeric;
  v_delta_kcal numeric;
begin
  select enabled into v_enabled
  from ai_private.action_policies
  where action_code = p_action_code;
  if coalesce(v_enabled, false) is false or jsonb_typeof(p_payload) <> 'object' then
    return jsonb_build_object('allowed', false, 'reason', v_reason);
  end if;
  if coalesce(char_length(btrim(p_payload ->> 'explanation')), 0) = 0
     or coalesce((p_payload ->> 'reversible')::boolean, false) is false then
    return jsonb_build_object('allowed', false, 'reason', 'explanation_or_reversibility_missing');
  end if;

  if p_action_code = 'training_volume_adjustment' then
    begin v_delta_percent := (p_payload ->> 'delta_percent')::numeric;
    exception when others then return jsonb_build_object('allowed', false, 'reason', 'delta_invalid'); end;
    v_valid := v_delta_percent <= 20 and v_delta_percent >= -100;
    if v_valid and v_delta_percent < -20 then
      v_valid := p_payload ->> 'reason_code' in ('fatigue', 'deload');
    end if;
    v_reason := case when v_valid then 'allowed' else 'training_volume_limit' end;
  elsif p_action_code = 'calorie_target_adjustment' then
    begin
      v_delta_percent := abs((p_payload ->> 'delta_percent')::numeric);
      v_delta_kcal := abs((p_payload ->> 'delta_kcal')::numeric);
    exception when others then return jsonb_build_object('allowed', false, 'reason', 'delta_invalid'); end;
    v_valid := v_delta_percent <= 10
      and v_delta_kcal <= 300
      and coalesce((p_payload ->> 'has_sufficient_new_authoritative_data')::boolean, false);
    v_reason := case when v_valid then 'allowed' else 'calorie_adjustment_limit' end;
  elsif p_action_code = 'replace_exercise' then
    v_valid := coalesce((p_payload ->> 'compatible_alternative')::boolean, false);
    v_reason := case when v_valid then 'allowed' else 'compatible_alternative_required' end;
  elsif p_action_code in ('add_rest_day', 'reschedule_training') then
    v_valid := true;
    v_reason := 'allowed';
  end if;

  return jsonb_build_object('allowed', v_valid, 'reason', v_reason);
end;
$$;

create or replace function ai_private.validate_structured_response(p_payload jsonb)
returns boolean
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_action jsonb;
begin
  if jsonb_typeof(p_payload) <> 'object'
    or not (p_payload ?& array[
      'schema_version','feature_code','summary','observations',
      'uncertainties','recommendations','actions','safety'
    ])
    or exists (
      select 1 from jsonb_object_keys(p_payload) k
      where k not in (
        'schema_version','feature_code','summary','observations',
        'uncertainties','recommendations','actions','safety'
      )
    )
    or coalesce(p_payload ->> 'schema_version', '') <> 'phase6a.response.v1'
    or coalesce(p_payload ->> 'feature_code', '') not in ('private_chat','daily_analysis','weekly_checkin','post_workout')
    or coalesce(char_length(p_payload ->> 'summary'), 0) not between 1 and 2000
    or jsonb_typeof(p_payload -> 'observations') <> 'array'
    or jsonb_array_length(p_payload -> 'observations') > 12
    or jsonb_typeof(p_payload -> 'uncertainties') <> 'array'
    or jsonb_array_length(p_payload -> 'uncertainties') > 12
    or jsonb_typeof(p_payload -> 'recommendations') <> 'array'
    or jsonb_array_length(p_payload -> 'recommendations') > 12
    or jsonb_typeof(p_payload -> 'actions') <> 'array'
    or jsonb_array_length(p_payload -> 'actions') > 8
    or jsonb_typeof(p_payload -> 'safety') <> 'object'
    or not (p_payload -> 'safety' ?& array['status','category','message_key','automatic_execution_blocked'])
    or exists (
      select 1 from jsonb_object_keys(p_payload -> 'safety') k
      where k not in ('status','category','message_key','automatic_execution_blocked')
    )
    or coalesce(p_payload -> 'safety' ->> 'status', '') not in ('clear','hard_stop','review_required')
    or coalesce(p_payload -> 'safety' ->> 'category', '') not in ('none','serious_health','unclear_health','injury','eating_disorder','other')
    or coalesce(char_length(p_payload -> 'safety' ->> 'message_key'), 0) not between 1 and 120
    or jsonb_typeof(p_payload -> 'safety' -> 'automatic_execution_blocked') <> 'boolean'
    or (
      p_payload -> 'safety' ->> 'status' in ('hard_stop','review_required')
      and coalesce((p_payload -> 'safety' ->> 'automatic_execution_blocked')::boolean, false) is false
    )
    or (
      p_payload -> 'safety' ->> 'status' in ('hard_stop','review_required')
      and jsonb_array_length(p_payload -> 'actions') <> 0
    ) then
    return false;
  end if;
  for v_action in select value from jsonb_array_elements(p_payload -> 'actions') loop
    if jsonb_typeof(v_action) <> 'object'
       or not coalesce((ai_private.validate_action_contract(v_action ->> 'action_code', v_action -> 'payload') ->> 'allowed')::boolean, false) then
      return false;
    end if;
  end loop;
  return true;
end;
$$;

create or replace function ai_private.trust_status(
  p_user_id uuid,
  p_feature_code text,
  p_adapter_code text default 'provider',
  p_at timestamptz default now()
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_member boolean;
  v_entitlement record;
  v_consent record;
  v_safety text;
  v_ai_enabled boolean := false;
  v_adapter_enabled boolean := false;
  v_structural boolean;
  v_operational boolean;
  v_reason text;
  v_period record;
  v_consumed bigint := 0;
  v_reserved bigint := 0;
  v_fair_use text := 'normal';
begin
  if p_feature_code not in ('private_chat','daily_analysis','weekly_checkin','post_workout')
     or p_adapter_code not in ('provider','mock') then
    raise exception 'ai_request_contract_invalid' using errcode = '22023';
  end if;
  select exists (
    select 1 from public.profiles p where p.id = p_user_id and p.role = 'client'
  ) into v_member;
  select * into v_entitlement from ai_private.current_entitlement(p_user_id, p_at);
  select * into v_consent from ai_private.current_consent(p_user_id, 'ai_processing');
  select s.safety_status into v_safety
  from public.ai_member_safety_state s where s.user_id = p_user_id;
  select enabled into v_ai_enabled
  from ai_private.feature_flags where flag_code = 'ai_coach_enabled';
  select enabled into v_adapter_enabled
  from ai_private.feature_flags
  where flag_code = case p_adapter_code when 'mock' then 'staging_mock_enabled' else 'provider_calls_enabled' end;

  v_structural := v_member
    and v_entitlement.entitlement_code is not null
    and v_consent.consent_state = 'granted'
    and coalesce(v_consent.document_active, false)
    and coalesce(v_safety, 'clear') not in ('hard_stop', 'review_required');
  v_operational := v_structural and coalesce(v_ai_enabled, false) and coalesce(v_adapter_enabled, false);
  v_reason := case
    when not v_member then 'member_required'
    when v_entitlement.entitlement_code is null then 'ai_entitlement_required'
    when v_consent.consent_state is distinct from 'granted' or not coalesce(v_consent.document_active, false) then 'ai_consent_required'
    when coalesce(v_safety, 'clear') in ('hard_stop', 'review_required') then 'safety_hard_stop'
    when not coalesce(v_ai_enabled, false) then 'ai_feature_disabled'
    when not coalesce(v_adapter_enabled, false) then case p_adapter_code when 'mock' then 'mock_disabled' else 'provider_disabled' end
    else 'allowed'
  end;

  if v_entitlement.entitlement_started_at is not null then
    select * into v_period
    from ai_private.subscription_period(v_entitlement.entitlement_started_at, p_at);
    select coalesce(a.consumed_micros, 0), coalesce(a.reserved_micros, 0)
      into v_consumed, v_reserved
    from ai_private.budget_accounts a
    where a.user_id = p_user_id and a.period_start = v_period.period_start;
    v_fair_use := ai_private.evaluate_budget(
      coalesce(v_consumed, 0), coalesce(v_reserved, 0), 0, 'luna'
    ) ->> 'fair_use_status';
  end if;

  return jsonb_build_object(
    'structurally_eligible', v_structural,
    'operationally_allowed', v_operational,
    'deny_reason', v_reason,
    'entitlement_code', v_entitlement.entitlement_code,
    'consent_state', coalesce(v_consent.consent_state, 'missing'),
    'safety_status', coalesce(v_safety, 'clear'),
    'feature_enabled', coalesce(v_ai_enabled, false),
    'adapter_enabled', coalesce(v_adapter_enabled, false),
    'fair_use_status', v_fair_use,
    'automatic_billing', false,
    'provider_cost_visible_to_member', false
  );
end;
$$;

create or replace function ai_private.can_share_trainer_summary(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
  select coalesce((
    select c.consent_state = 'granted' and c.document_active
    from ai_private.current_consent(p_user_id, 'trainer_summary_sharing') c
  ), false);
$$;

create or replace function public.fmz_phase6a_read_consent_contract(p_locale text default 'nl')
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
begin
  perform ai_private.assert_member(v_user_id);
  if p_locale not in ('nl', 'en', 'de') then
    raise exception 'ai_locale_invalid' using errcode = '22023';
  end if;
  return jsonb_build_object(
    'locale', p_locale,
    'contracts', coalesce((
      select jsonb_agg(jsonb_build_object(
        'consent_kind', d.consent_kind,
        'document_version', d.document_version,
        'purpose_code', d.purpose_code,
        'categories', to_jsonb(d.categories),
        'content_text', d.content_text,
        'content_sha256', d.content_sha256,
        'explicit_confirmation_required', true,
        'preselected', false
      ) order by d.consent_kind)
      from ai_private.consent_documents d
      where d.locale = p_locale and d.status = 'active' and d.effective_at <= now()
    ), '[]'::jsonb),
    'current', jsonb_build_object(
      'ai_processing', coalesce((select to_jsonb(c) from ai_private.current_consent(v_user_id, 'ai_processing') c), '{"consent_state":"missing"}'::jsonb),
      'trainer_summary_sharing', coalesce((select to_jsonb(c) from ai_private.current_consent(v_user_id, 'trainer_summary_sharing') c), '{"consent_state":"missing"}'::jsonb)
    )
  );
end;
$$;

create or replace function public.fmz_phase6a_record_consent(
  p_consent_kind text,
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
  v_document record;
  v_existing public.ai_consent_events%rowtype;
  v_row public.ai_consent_events%rowtype;
begin
  perform ai_private.assert_member(v_user_id);
  if p_consent_kind not in ('ai_processing', 'trainer_summary_sharing')
     or p_action not in ('granted', 'withdrawn')
     or p_locale not in ('nl', 'en', 'de')
     or p_request_id is null
     or p_explicit_confirmation is distinct from true then
    raise exception 'ai_consent_input_invalid' using errcode = '22023';
  end if;
  select * into v_document
  from ai_private.consent_documents d
  where d.consent_kind = p_consent_kind
    and d.document_version = p_document_version
    and d.locale = p_locale
    and d.status = 'active'
    and d.effective_at <= now();
  if v_document is null then
    raise exception 'ai_consent_document_invalid' using errcode = '22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_consent:' || v_user_id::text || ':' || p_consent_kind, 0));
  select * into v_existing
  from public.ai_consent_events e
  where e.user_id = v_user_id and e.request_id = p_request_id;
  if v_existing.id is not null then
    if v_existing.consent_kind <> p_consent_kind
       or v_existing.consent_state <> p_action
       or v_existing.document_version <> p_document_version
       or v_existing.locale <> p_locale then
      raise exception 'ai_consent_request_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'consent', to_jsonb(v_existing));
  end if;
  insert into public.ai_consent_events(
    id, user_id, consent_kind, consent_state, document_version,
    purpose_code, categories, locale, explicit_confirmation, request_id
  ) values (
    gen_random_uuid(), v_user_id, p_consent_kind, p_action, p_document_version,
    v_document.purpose_code, v_document.categories, p_locale, true, p_request_id
  ) returning * into v_row;
  insert into ai_private.audit_events(id, user_id, event_code, safe_metadata)
  values (
    gen_random_uuid(), v_user_id, 'consent_' || p_action,
    jsonb_build_object('consent_kind', p_consent_kind, 'document_version', p_document_version, 'locale', p_locale)
  );
  return jsonb_build_object('replay', false, 'consent', to_jsonb(v_row));
end;
$$;

create or replace function public.fmz_phase6a_get_trust_status(p_feature_code text default 'private_chat')
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
begin
  perform ai_private.assert_member(v_user_id);
  return ai_private.trust_status(v_user_id, p_feature_code, 'provider', now());
end;
$$;

create or replace function public.fmz_phase6a_get_context_manifest(p_feature_code text)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_gate jsonb;
  v_context jsonb;
  v_sources jsonb;
begin
  perform ai_private.assert_member(v_user_id);
  v_gate := ai_private.trust_status(v_user_id, p_feature_code, 'provider', now());
  if not coalesce((v_gate ->> 'operationally_allowed')::boolean, false) then
    raise exception '%', v_gate ->> 'deny_reason' using errcode = '42501';
  end if;

  v_context := jsonb_build_object(
    'schema_version', 'phase6a.context.v1',
    'feature_code', p_feature_code,
    'identity', coalesce((
      select jsonb_build_object('language', s.language, 'country', s.country, 'updated_at', s.updated_at)
      from public.user_settings s where s.user_id = v_user_id
    ), '{"available":false}'::jsonb),
    'onboarding', coalesce((
      select jsonb_build_object(
        'fitness_goal', o.fitness_goal,
        'goal_direction', o.goal_direction,
        'training_experience', o.training_experience,
        'available_days', o.available_days,
        'goal_safety_status', o.goal_safety_status,
        'updated_at', o.updated_at
      ) from public.user_onboarding o where o.user_id = v_user_id
    ), '{"available":false}'::jsonb),
    'recovery', jsonb_build_object(
      'entries_last_7_days', (select count(*) from public.recovery_logs r where r.user_id = v_user_id and r.log_date >= current_date - 6),
      'latest_log_date', (select max(r.log_date) from public.recovery_logs r where r.user_id = v_user_id),
      'latest_updated_at', (select max(r.updated_at) from public.recovery_logs r where r.user_id = v_user_id)
    ),
    'training', jsonb_build_object(
      'active_plan_count', (select count(*) from public.training_plans p where p.user_id = v_user_id and p.status = 'active'),
      'completed_sessions_last_28_days', (select count(*) from public.workout_sessions w where w.user_id = v_user_id and w.status = 'completed' and w.completed_at >= now() - interval '28 days'),
      'latest_completed_at', (select max(w.completed_at) from public.workout_sessions w where w.user_id = v_user_id and w.status = 'completed')
    ),
    'nutrition', jsonb_build_object(
      'active_target_available', exists(select 1 from public.nutrition_targets t where t.user_id = v_user_id and t.status = 'active'),
      'logged_days_last_7_days', (select count(*) from public.food_logs f where f.user_id = v_user_id and f.status = 'active' and f.log_date >= current_date - 6),
      'latest_log_date', (select max(f.log_date) from public.food_logs f where f.user_id = v_user_id and f.status = 'active')
    ),
    'progress', jsonb_build_object(
      'active_goal', (select g.goal_code from public.progress_goals g where g.user_id = v_user_id and g.status = 'active' limit 1),
      'latest_weight_date', (select max(w.log_date) from public.weight_logs w where w.user_id = v_user_id and w.status = 'active'),
      'latest_measurement_date', (select max(b.log_date) from public.body_measurements b where b.user_id = v_user_id and b.status = 'active')
    ),
    'unavailable', jsonb_build_array('health_sync', 'running_activity', 'progress_photos')
  );
  v_sources := jsonb_build_object(
    'identity', jsonb_build_object('authority', 'user_settings', 'copied', false),
    'onboarding', jsonb_build_object('authority', 'user_onboarding', 'copied', false),
    'recovery', jsonb_build_object('authority', 'recovery_logs', 'copied', false),
    'training', jsonb_build_object('authority', jsonb_build_array('training_plans','workout_sessions'), 'copied', false),
    'nutrition', jsonb_build_object('authority', jsonb_build_array('nutrition_targets','food_logs'), 'copied', false),
    'progress', jsonb_build_object('authority', jsonb_build_array('progress_goals','weight_logs','body_measurements'), 'copied', false)
  );
  return jsonb_build_object(
    'context', v_context,
    'manifest', jsonb_build_object(
      'manifest_version', 'phase6a.context-manifest.v1',
      'context_hash', encode(digest(convert_to(v_context::text, 'UTF8'), 'sha256'), 'hex'),
      'sources', v_sources,
      'unavailable_sources', jsonb_build_array('health_sync','running_activity','progress_photos'),
      'source_cutoff_at', now()
    )
  );
end;
$$;

create or replace function public.fmz_phase6a_submit_user_message(
  p_request_id uuid,
  p_thread_id uuid,
  p_feature_code text,
  p_locale text,
  p_content text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_gate jsonb;
  v_existing public.ai_messages%rowtype;
  v_thread public.ai_threads%rowtype;
  v_message public.ai_messages%rowtype;
begin
  perform ai_private.assert_member(v_user_id);
  if p_request_id is null or p_thread_id is null
     or p_feature_code not in ('private_chat','daily_analysis','weekly_checkin','post_workout')
     or p_locale not in ('nl','en','de')
     or char_length(btrim(coalesce(p_content, ''))) not between 1 and 4000 then
    raise exception 'ai_message_input_invalid' using errcode = '22023';
  end if;
  v_gate := ai_private.trust_status(v_user_id, p_feature_code, 'provider', now());
  if not coalesce((v_gate ->> 'operationally_allowed')::boolean, false) then
    raise exception '%', v_gate ->> 'deny_reason' using errcode = '42501';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_message:' || v_user_id::text || ':' || p_request_id::text, 0));
  select * into v_existing from public.ai_messages m
  where m.user_id = v_user_id and m.request_id = p_request_id and m.message_role = 'user';
  if v_existing.id is not null then
    if v_existing.thread_id <> p_thread_id or v_existing.feature_code <> p_feature_code or v_existing.content_text <> btrim(p_content) then
      raise exception 'ai_message_request_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'message_id', v_existing.id, 'thread_id', v_existing.thread_id);
  end if;
  select * into v_thread from public.ai_threads t where t.id = p_thread_id for update;
  if v_thread.id is null then
    insert into public.ai_threads(id, user_id, feature_code, locale)
    values (p_thread_id, v_user_id, p_feature_code, p_locale)
    returning * into v_thread;
  elsif v_thread.user_id <> v_user_id or v_thread.status <> 'active' or v_thread.retention_state <> 'active' then
    raise exception 'ai_thread_forbidden' using errcode = '42501';
  elsif v_thread.feature_code <> p_feature_code then
    raise exception 'ai_thread_feature_conflict' using errcode = '23505';
  end if;
  insert into public.ai_messages(
    id, user_id, thread_id, message_role, feature_code,
    content_text, status, request_id
  ) values (
    gen_random_uuid(), v_user_id, p_thread_id, 'user', p_feature_code,
    btrim(p_content), 'active', p_request_id
  ) returning * into v_message;
  update public.ai_threads set updated_at = now() where id = p_thread_id;
  return jsonb_build_object('replay', false, 'message_id', v_message.id, 'thread_id', p_thread_id);
end;
$$;

create or replace function public.fmz_phase6a_read_thread_history(
  p_thread_id uuid,
  p_limit integer default 50,
  p_before timestamptz default null
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_thread public.ai_threads%rowtype;
begin
  perform ai_private.assert_member(v_user_id);
  if p_limit not between 1 and 100 then
    raise exception 'ai_history_limit_invalid' using errcode = '22023';
  end if;
  select * into v_thread from public.ai_threads t
  where t.id = p_thread_id and t.user_id = v_user_id;
  if v_thread.id is null or v_thread.retention_state = 'deleted'
     or (v_thread.retention_state = 'grace' and v_thread.retention_due_at <= now()) then
    raise exception 'ai_thread_unavailable' using errcode = '42501';
  end if;
  return jsonb_build_object(
    'thread', jsonb_build_object(
      'id', v_thread.id, 'feature_code', v_thread.feature_code,
      'locale', v_thread.locale, 'status', v_thread.status,
      'retention_state', v_thread.retention_state,
      'retention_due_at', v_thread.retention_due_at
    ),
    'messages', coalesce((
      select jsonb_agg(to_jsonb(x) order by x.created_at, x.id)
      from (
        select m.id, m.message_role, m.feature_code, m.content_text,
          m.structured_output, m.schema_version, m.status, m.created_at
        from public.ai_messages m
        where m.thread_id = p_thread_id and m.user_id = v_user_id
          and (p_before is null or m.created_at < p_before)
        order by m.created_at desc, m.id desc
        limit p_limit
      ) x
    ), '[]'::jsonb)
  );
end;
$$;

create or replace function public.fmz_phase6a_request_data_lifecycle(
  p_request_type text,
  p_request_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_existing public.ai_data_lifecycle_requests%rowtype;
begin
  perform ai_private.assert_member(v_user_id);
  if p_request_type not in ('export', 'delete') or p_request_id is null then
    raise exception 'ai_lifecycle_request_invalid' using errcode = '22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_lifecycle:' || v_user_id::text || ':' || p_request_id::text, 0));
  select * into v_existing from public.ai_data_lifecycle_requests r
  where r.user_id = v_user_id and r.request_id = p_request_id;
  if v_existing.id is not null then
    if v_existing.request_type <> p_request_type then
      raise exception 'ai_lifecycle_request_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'request', to_jsonb(v_existing));
  end if;
  insert into public.ai_data_lifecycle_requests(id, user_id, request_type, request_id)
  values (gen_random_uuid(), v_user_id, p_request_type, p_request_id)
  returning * into v_existing;
  return jsonb_build_object('replay', false, 'request', to_jsonb(v_existing));
end;
$$;

create or replace function public.fmz_phase6a_read_export_manifest()
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
begin
  perform ai_private.assert_member(v_user_id);
  return jsonb_build_object(
    'schema_version', 'phase6a.export-manifest.v1',
    'user_id_included', false,
    'consent_events', (select count(*) from public.ai_consent_events e where e.user_id = v_user_id),
    'threads', (select count(*) from public.ai_threads t where t.user_id = v_user_id),
    'active_messages', (select count(*) from public.ai_messages m where m.user_id = v_user_id and m.status = 'active'),
    'context_manifests', (select count(*) from public.ai_context_manifests c where c.user_id = v_user_id),
    'action_proposals', (select count(*) from public.ai_action_proposals p where p.user_id = v_user_id),
    'action_decisions', (select count(*) from public.ai_action_decisions d where d.user_id = v_user_id),
    'lifecycle_requests', (select count(*) from public.ai_data_lifecycle_requests r where r.user_id = v_user_id)
  );
end;
$$;

create or replace function public.fmz_phase6a_service_begin_run(
  p_user_id uuid,
  p_request_id uuid,
  p_thread_id uuid,
  p_feature_code text,
  p_adapter_code text,
  p_model_tier text,
  p_policy_version text,
  p_schema_version text,
  p_payload_hash text,
  p_reserved_cost_micros bigint,
  p_context_sources jsonb,
  p_unavailable_sources text[] default '{}'
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_gate jsonb;
  v_existing ai_private.runs%rowtype;
  v_entitlement record;
  v_period record;
  v_policy ai_private.budget_policies%rowtype;
  v_account ai_private.budget_accounts%rowtype;
  v_budget jsonb;
  v_rate ai_private.rate_policies%rowtype;
  v_window timestamptz;
  v_bucket ai_private.rate_buckets%rowtype;
  v_manifest_id uuid := gen_random_uuid();
  v_run_id uuid := gen_random_uuid();
begin
  perform ai_private.assert_member(p_user_id);
  if p_request_id is null
     or p_feature_code not in ('private_chat','daily_analysis','weekly_checkin','post_workout')
     or p_adapter_code not in ('mock','provider')
     or p_model_tier not in ('luna','terra')
     or p_payload_hash !~ '^[0-9a-f]{64}$'
     or char_length(btrim(coalesce(p_policy_version, ''))) not between 1 and 80
     or p_schema_version <> 'phase6a.response.v1'
     or p_reserved_cost_micros not between 0 and 4000000
     or jsonb_typeof(p_context_sources) <> 'object'
     or pg_column_size(p_context_sources) > 32768
     or p_context_sources::text ~* '"(prompt|content|message|email|jwt|token|secret)"\s*:'
     or cardinality(coalesce(p_unavailable_sources, '{}')) > 24 then
    raise exception 'ai_run_input_invalid' using errcode = '22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_run:' || p_user_id::text || ':' || p_request_id::text, 0));
  select * into v_existing from ai_private.runs r
  where r.user_id = p_user_id and r.request_id = p_request_id;
  if v_existing.id is not null then
    if v_existing.feature_code <> p_feature_code
       or v_existing.adapter_code <> p_adapter_code
       or v_existing.model_tier <> p_model_tier
       or v_existing.payload_hash <> p_payload_hash
       or v_existing.thread_id is distinct from p_thread_id
       or v_existing.policy_version <> p_policy_version
       or v_existing.schema_version <> p_schema_version
       or v_existing.reserved_cost_micros <> p_reserved_cost_micros then
      raise exception 'ai_run_request_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'run_id', v_existing.id, 'status', v_existing.status);
  end if;
  v_gate := ai_private.trust_status(p_user_id, p_feature_code, p_adapter_code, now());
  if not coalesce((v_gate ->> 'operationally_allowed')::boolean, false) then
    raise exception '%', v_gate ->> 'deny_reason' using errcode = '42501';
  end if;
  if p_thread_id is not null and not exists (
    select 1 from public.ai_threads t
    where t.id = p_thread_id and t.user_id = p_user_id
      and t.status = 'active' and t.retention_state = 'active'
  ) then
    raise exception 'ai_thread_forbidden' using errcode = '42501';
  end if;
  select * into v_entitlement from ai_private.current_entitlement(p_user_id, now());
  select * into v_period from ai_private.subscription_period(v_entitlement.entitlement_started_at, now());
  select * into v_policy from ai_private.budget_policies where active order by created_at desc limit 1;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_budget:' || p_user_id::text || ':' || v_period.period_start::text, 0));
  insert into ai_private.budget_accounts(user_id, period_start, period_end, policy_version)
  values (p_user_id, v_period.period_start, v_period.period_end, v_policy.policy_version)
  on conflict (user_id, period_start) do nothing;
  select * into v_account from ai_private.budget_accounts a
  where a.user_id = p_user_id and a.period_start = v_period.period_start for update;
  v_budget := ai_private.evaluate_budget(v_account.consumed_micros, v_account.reserved_micros, p_reserved_cost_micros, p_model_tier);
  if not (v_budget ->> 'allowed')::boolean then
    raise exception '%', v_budget ->> 'reason' using errcode = '42501';
  end if;
  select * into v_rate from ai_private.rate_policies where feature_code = p_feature_code and active;
  v_window := to_timestamp(floor(extract(epoch from now()) / v_rate.window_seconds) * v_rate.window_seconds);
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_rate:' || p_user_id::text || ':' || p_feature_code || ':' || v_window::text, 0));
  insert into ai_private.rate_buckets(user_id, feature_code, window_started_at, window_seconds, request_count)
  values (p_user_id, p_feature_code, v_window, v_rate.window_seconds, 1)
  on conflict (user_id, feature_code, window_started_at) do update
    set request_count = ai_private.rate_buckets.request_count + 1,
        updated_at = now()
  returning * into v_bucket;
  if v_bucket.request_count > v_rate.max_requests then
    raise exception 'ai_rate_limit' using errcode = '42501';
  end if;
  insert into public.ai_context_manifests(
    id, user_id, feature_code, manifest_version, context_hash,
    sources, unavailable_sources, source_cutoff_at
  ) values (
    v_manifest_id, p_user_id, p_feature_code, 'phase6a.context-manifest.v1',
    encode(digest(convert_to(p_context_sources::text, 'UTF8'), 'sha256'), 'hex'),
    p_context_sources, coalesce(p_unavailable_sources, '{}'), now()
  );
  insert into ai_private.runs(
    id, user_id, request_id, thread_id, context_manifest_id, feature_code,
    adapter_code, model_tier, policy_version, schema_version, payload_hash,
    reserved_cost_micros
  ) values (
    v_run_id, p_user_id, p_request_id, p_thread_id, v_manifest_id, p_feature_code,
    p_adapter_code, p_model_tier, p_policy_version, p_schema_version, p_payload_hash,
    p_reserved_cost_micros
  );
  update ai_private.budget_accounts
  set reserved_micros = reserved_micros + p_reserved_cost_micros,
      warning_issued_at = case
        when consumed_micros + reserved_micros + p_reserved_cost_micros >= v_policy.warning_micros
          then coalesce(warning_issued_at, now()) else warning_issued_at end,
      updated_at = now()
  where user_id = p_user_id and period_start = v_period.period_start;
  insert into ai_private.usage_ledger(
    id, user_id, run_id, request_id, feature_code, model_tier, ledger_type, amount_micros
  ) values (
    gen_random_uuid(), p_user_id, v_run_id, p_request_id, p_feature_code, p_model_tier, 'reserve', p_reserved_cost_micros
  );
  insert into ai_private.audit_events(id, user_id, run_id, event_code, safe_metadata)
  values (gen_random_uuid(), p_user_id, v_run_id, 'run_reserved', jsonb_build_object('feature_code', p_feature_code, 'adapter_code', p_adapter_code));
  return jsonb_build_object('replay', false, 'run_id', v_run_id, 'fair_use_status', v_budget ->> 'fair_use_status');
end;
$$;

create or replace function public.fmz_phase6a_service_complete_run(
  p_run_id uuid,
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
  v_entitlement record;
  v_period record;
  v_account ai_private.budget_accounts%rowtype;
  v_budget jsonb;
  v_release bigint;
  v_response_hash text;
begin
  if p_run_id is null or p_actual_cost_micros not between 0 and 4000000
     or p_input_tokens not between 0 and 1000000
     or p_output_tokens not between 0 and 1000000
     or not ai_private.validate_structured_response(p_structured_output) then
    raise exception 'ai_structured_output_invalid' using errcode = '22023';
  end if;
  v_response_hash := encode(digest(convert_to(p_structured_output::text, 'UTF8'), 'sha256'), 'hex');
  select * into v_run from ai_private.runs r where r.id = p_run_id for update;
  if v_run.id is null then raise exception 'ai_run_not_found' using errcode = '22023'; end if;
  if v_run.status = 'completed' then
    if v_run.actual_cost_micros <> p_actual_cost_micros
       or v_run.input_tokens <> p_input_tokens
       or v_run.output_tokens <> p_output_tokens
       or v_run.response_hash <> v_response_hash then
      raise exception 'ai_run_completion_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'run_id', v_run.id, 'status', v_run.status);
  elsif v_run.status <> 'reserved' then
    raise exception 'ai_run_not_completable' using errcode = '40001';
  end if;
  if p_structured_output ->> 'feature_code' <> v_run.feature_code
     or p_structured_output ->> 'schema_version' <> v_run.schema_version then
    raise exception 'ai_structured_output_conflict' using errcode = '23505';
  end if;
  if v_run.adapter_code = 'mock' and p_actual_cost_micros <> 0 then
    raise exception 'ai_mock_cost_forbidden' using errcode = '22023';
  end if;
  select * into v_entitlement from ai_private.current_entitlement(v_run.user_id, v_run.started_at);
  select * into v_period from ai_private.subscription_period(v_entitlement.entitlement_started_at, v_run.started_at);
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_budget:' || v_run.user_id::text || ':' || v_period.period_start::text, 0));
  select * into v_account from ai_private.budget_accounts a
  where a.user_id = v_run.user_id and a.period_start = v_period.period_start for update;
  v_budget := ai_private.evaluate_budget(
    v_account.consumed_micros,
    greatest(0, v_account.reserved_micros - v_run.reserved_cost_micros),
    p_actual_cost_micros,
    v_run.model_tier
  );
  if not (v_budget ->> 'allowed')::boolean then
    raise exception '%', v_budget ->> 'reason' using errcode = '42501';
  end if;
  v_release := greatest(0, v_run.reserved_cost_micros - p_actual_cost_micros);
  update ai_private.budget_accounts
  set reserved_micros = greatest(0, reserved_micros - v_run.reserved_cost_micros),
      consumed_micros = consumed_micros + p_actual_cost_micros,
      hard_stopped_at = case when consumed_micros + p_actual_cost_micros >= 4000000 then coalesce(hard_stopped_at, now()) else hard_stopped_at end,
      updated_at = now()
  where user_id = v_run.user_id and period_start = v_period.period_start;
  insert into ai_private.usage_ledger(
    id, user_id, run_id, request_id, feature_code, model_tier, ledger_type, amount_micros
  ) values (
    gen_random_uuid(), v_run.user_id, v_run.id, v_run.request_id, v_run.feature_code, v_run.model_tier, 'actual', p_actual_cost_micros
  );
  if v_release > 0 then
    insert into ai_private.usage_ledger(
      id, user_id, run_id, request_id, feature_code, model_tier, ledger_type, amount_micros
    ) values (
      gen_random_uuid(), v_run.user_id, v_run.id, v_run.request_id, v_run.feature_code, v_run.model_tier, 'release', v_release
    );
  end if;
  update ai_private.runs
  set status = 'completed', actual_cost_micros = p_actual_cost_micros,
      input_tokens = p_input_tokens, output_tokens = p_output_tokens,
      response_hash = v_response_hash, completed_at = now()
  where id = v_run.id;
  if p_structured_output -> 'safety' ->> 'status' in ('hard_stop','review_required') then
    perform public.fmz_phase6a_service_record_safety_event(
      v_run.user_id,
      v_run.id,
      p_structured_output -> 'safety' ->> 'category',
      p_structured_output -> 'safety' ->> 'status',
      v_run.policy_version
    );
  end if;
  if v_run.thread_id is not null then
    insert into public.ai_messages(
      id, user_id, thread_id, message_role, feature_code, content_text,
      structured_output, schema_version, status, request_id, run_id
    ) values (
      gen_random_uuid(), v_run.user_id, v_run.thread_id, 'assistant', v_run.feature_code,
      p_structured_output ->> 'summary', p_structured_output, v_run.schema_version,
      'active', v_run.request_id, v_run.id
    );
    update public.ai_threads set updated_at = now() where id = v_run.thread_id;
  end if;
  insert into ai_private.audit_events(id, user_id, run_id, event_code, safe_metadata)
  values (gen_random_uuid(), v_run.user_id, v_run.id, 'run_completed', jsonb_build_object('feature_code', v_run.feature_code, 'safety_status', p_structured_output -> 'safety' ->> 'status'));
  return jsonb_build_object('replay', false, 'run_id', v_run.id, 'status', 'completed', 'fair_use_status', v_budget ->> 'fair_use_status');
end;
$$;

create or replace function public.fmz_phase6a_service_fail_run(
  p_run_id uuid,
  p_safe_error_code text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_run ai_private.runs%rowtype;
  v_entitlement record;
  v_period record;
begin
  if p_run_id is null or p_safe_error_code !~ '^[a-z0-9_]{1,80}$'
     or p_safe_error_code ~ '(prompt|content|message|email|jwt|token|secret)' then
    raise exception 'ai_safe_error_invalid' using errcode = '22023';
  end if;
  select * into v_run from ai_private.runs r where r.id = p_run_id for update;
  if v_run.id is null then raise exception 'ai_run_not_found' using errcode = '22023'; end if;
  if v_run.status in ('failed', 'blocked') then
    return jsonb_build_object('replay', true, 'run_id', v_run.id, 'status', v_run.status);
  elsif v_run.status <> 'reserved' then
    raise exception 'ai_run_not_failable' using errcode = '40001';
  end if;
  select * into v_entitlement from ai_private.current_entitlement(v_run.user_id, v_run.started_at);
  select * into v_period from ai_private.subscription_period(v_entitlement.entitlement_started_at, v_run.started_at);
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_budget:' || v_run.user_id::text || ':' || v_period.period_start::text, 0));
  update ai_private.budget_accounts
  set reserved_micros = greatest(0, reserved_micros - v_run.reserved_cost_micros), updated_at = now()
  where user_id = v_run.user_id and period_start = v_period.period_start;
  insert into ai_private.usage_ledger(
    id, user_id, run_id, request_id, feature_code, model_tier, ledger_type, amount_micros
  ) values (
    gen_random_uuid(), v_run.user_id, v_run.id, v_run.request_id,
    v_run.feature_code, v_run.model_tier, 'release', v_run.reserved_cost_micros
  );
  update ai_private.runs
  set status = 'failed', safe_error_code = p_safe_error_code, completed_at = now()
  where id = v_run.id;
  insert into ai_private.audit_events(id, user_id, run_id, event_code, safe_metadata)
  values (gen_random_uuid(), v_run.user_id, v_run.id, 'run_failed', jsonb_build_object('safe_error_code', p_safe_error_code));
  return jsonb_build_object('replay', false, 'run_id', v_run.id, 'status', 'failed');
end;
$$;

create or replace function public.fmz_phase6a_service_record_safety_event(
  p_user_id uuid,
  p_run_id uuid,
  p_risk_category text,
  p_safety_outcome text,
  p_policy_version text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_state text;
begin
  perform ai_private.assert_member(p_user_id);
  if p_risk_category not in ('serious_health','unclear_health','injury','eating_disorder','other')
     or p_safety_outcome not in ('hard_stop','review_required','resolved')
     or char_length(btrim(coalesce(p_policy_version, ''))) not between 1 and 80 then
    raise exception 'ai_safety_event_invalid' using errcode = '22023';
  end if;
  if p_run_id is not null and not exists (
    select 1 from ai_private.runs r where r.id = p_run_id and r.user_id = p_user_id
  ) then
    raise exception 'ai_safety_run_forbidden' using errcode = '42501';
  end if;
  v_state := p_safety_outcome;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_safety:' || p_user_id::text, 0));
  insert into ai_private.safety_events(
    id, user_id, run_id, risk_category, safety_outcome, policy_version
  ) values (
    gen_random_uuid(), p_user_id, p_run_id, p_risk_category, p_safety_outcome, p_policy_version
  );
  insert into public.ai_member_safety_state(
    user_id, safety_status, risk_category, blocked_at, resolved_at, resolution_code, revision
  ) values (
    p_user_id, v_state, p_risk_category,
    case when v_state in ('hard_stop','review_required') then now() else now() end,
    case when v_state = 'resolved' then now() else null end,
    case when v_state = 'resolved' then 'reviewed_resolution' else null end,
    1
  )
  on conflict (user_id) do update
  set safety_status = excluded.safety_status,
      risk_category = excluded.risk_category,
      blocked_at = case when excluded.safety_status in ('hard_stop','review_required') then now() else public.ai_member_safety_state.blocked_at end,
      resolved_at = excluded.resolved_at,
      resolution_code = excluded.resolution_code,
      revision = public.ai_member_safety_state.revision + 1,
      updated_at = now();
  return jsonb_build_object('safety_status', v_state, 'automatic_execution_blocked', v_state in ('hard_stop','review_required'));
end;
$$;

create or replace function public.fmz_phase6a_service_reconcile_retention(
  p_user_id uuid,
  p_at timestamptz default now()
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_has_entitlement boolean;
  v_grace_started integer := 0;
  v_restored integer := 0;
  v_deleted integer := 0;
begin
  perform ai_private.assert_member(p_user_id);
  v_has_entitlement := exists(select 1 from ai_private.current_entitlement(p_user_id, p_at));
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_retention:' || p_user_id::text, 0));
  if v_has_entitlement then
    update public.ai_threads
    set retention_state = 'active', retention_started_at = null,
        retention_due_at = null, updated_at = p_at
    where user_id = p_user_id and retention_state = 'grace';
    get diagnostics v_restored = row_count;
  else
    update public.ai_threads
    set retention_state = 'grace', retention_started_at = p_at,
        retention_due_at = p_at + interval '90 days', updated_at = p_at
    where user_id = p_user_id and retention_state = 'active';
    get diagnostics v_grace_started = row_count;
  end if;
  update public.ai_messages m
  set content_text = null, structured_output = null, schema_version = null, status = 'deleted'
  from public.ai_threads t
  where t.id = m.thread_id and t.user_id = p_user_id
    and t.retention_state = 'grace' and t.retention_due_at <= p_at
    and m.status = 'active';
  update public.ai_threads
  set retention_state = 'deleted', status = 'content_deleted',
      content_deleted_at = p_at, archived_at = coalesce(archived_at, p_at), updated_at = p_at
  where user_id = p_user_id and retention_state = 'grace' and retention_due_at <= p_at;
  get diagnostics v_deleted = row_count;
  return jsonb_build_object(
    'active_entitlement', v_has_entitlement,
    'grace_started', v_grace_started,
    'restored', v_restored,
    'threads_content_deleted', v_deleted,
    'retention_days', 90
  );
end;
$$;

drop trigger if exists ai_threads_touch_updated_at on public.ai_threads;
create trigger ai_threads_touch_updated_at
before update on public.ai_threads
for each row execute function ai_private.touch_updated_at();
drop trigger if exists ai_action_proposals_touch_updated_at on public.ai_action_proposals;
create trigger ai_action_proposals_touch_updated_at
before update on public.ai_action_proposals
for each row execute function ai_private.touch_updated_at();
drop trigger if exists ai_member_safety_state_touch_updated_at on public.ai_member_safety_state;
create trigger ai_member_safety_state_touch_updated_at
before update on public.ai_member_safety_state
for each row execute function ai_private.touch_updated_at();
drop trigger if exists ai_feature_flags_touch_updated_at on ai_private.feature_flags;
create trigger ai_feature_flags_touch_updated_at
before update on ai_private.feature_flags
for each row execute function ai_private.touch_updated_at();
drop trigger if exists ai_budget_accounts_touch_updated_at on ai_private.budget_accounts;
create trigger ai_budget_accounts_touch_updated_at
before update on ai_private.budget_accounts
for each row execute function ai_private.touch_updated_at();
drop trigger if exists ai_rate_buckets_touch_updated_at on ai_private.rate_buckets;
create trigger ai_rate_buckets_touch_updated_at
before update on ai_private.rate_buckets
for each row execute function ai_private.touch_updated_at();

revoke all on all functions in schema ai_private from public, anon, authenticated;

revoke all on function public.fmz_phase6a_read_consent_contract(text) from public, anon, authenticated;
revoke all on function public.fmz_phase6a_record_consent(text,text,text,text,boolean,uuid) from public, anon, authenticated;
revoke all on function public.fmz_phase6a_get_trust_status(text) from public, anon, authenticated;
revoke all on function public.fmz_phase6a_get_context_manifest(text) from public, anon, authenticated;
revoke all on function public.fmz_phase6a_submit_user_message(uuid,uuid,text,text,text) from public, anon, authenticated;
revoke all on function public.fmz_phase6a_read_thread_history(uuid,integer,timestamptz) from public, anon, authenticated;
revoke all on function public.fmz_phase6a_request_data_lifecycle(text,uuid) from public, anon, authenticated;
revoke all on function public.fmz_phase6a_read_export_manifest() from public, anon, authenticated;
revoke all on function public.fmz_phase6a_service_begin_run(uuid,uuid,uuid,text,text,text,text,text,text,bigint,jsonb,text[]) from public, anon, authenticated;
revoke all on function public.fmz_phase6a_service_complete_run(uuid,jsonb,bigint,integer,integer) from public, anon, authenticated;
revoke all on function public.fmz_phase6a_service_fail_run(uuid,text) from public, anon, authenticated;
revoke all on function public.fmz_phase6a_service_record_safety_event(uuid,uuid,text,text,text) from public, anon, authenticated;
revoke all on function public.fmz_phase6a_service_reconcile_retention(uuid,timestamptz) from public, anon, authenticated;

grant execute on function public.fmz_phase6a_read_consent_contract(text) to authenticated;
grant execute on function public.fmz_phase6a_record_consent(text,text,text,text,boolean,uuid) to authenticated;
grant execute on function public.fmz_phase6a_get_trust_status(text) to authenticated;
grant execute on function public.fmz_phase6a_get_context_manifest(text) to authenticated;
grant execute on function public.fmz_phase6a_submit_user_message(uuid,uuid,text,text,text) to authenticated;
grant execute on function public.fmz_phase6a_read_thread_history(uuid,integer,timestamptz) to authenticated;
grant execute on function public.fmz_phase6a_request_data_lifecycle(text,uuid) to authenticated;
grant execute on function public.fmz_phase6a_read_export_manifest() to authenticated;

grant execute on function public.fmz_phase6a_service_begin_run(uuid,uuid,uuid,text,text,text,text,text,text,bigint,jsonb,text[]) to service_role;
grant execute on function public.fmz_phase6a_service_complete_run(uuid,jsonb,bigint,integer,integer) to service_role;
grant execute on function public.fmz_phase6a_service_fail_run(uuid,text) to service_role;
grant execute on function public.fmz_phase6a_service_record_safety_event(uuid,uuid,text,text,text) to service_role;
grant execute on function public.fmz_phase6a_service_reconcile_retention(uuid,timestamptz) to service_role;

commit;
