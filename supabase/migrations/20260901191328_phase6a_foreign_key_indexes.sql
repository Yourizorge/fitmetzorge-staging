-- FitMetZorge Phase 6A foreign-key index hardening (STAGING first)
-- Additive performance indexes only; no data or access-contract changes.

begin;

create index if not exists ai_messages_thread_owner_idx
  on public.ai_messages(thread_id, user_id);

create index if not exists ai_action_proposals_context_owner_idx
  on public.ai_action_proposals(context_manifest_id, user_id);

create index if not exists ai_action_decisions_proposal_owner_idx
  on public.ai_action_decisions(proposal_id, user_id);

create index if not exists ai_runs_thread_owner_idx
  on ai_private.runs(thread_id, user_id)
  where thread_id is not null;

create index if not exists ai_runs_context_owner_idx
  on ai_private.runs(context_manifest_id, user_id)
  where context_manifest_id is not null;

create index if not exists ai_budget_accounts_policy_idx
  on ai_private.budget_accounts(policy_version);

create index if not exists ai_safety_events_run_idx
  on ai_private.safety_events(run_id)
  where run_id is not null;

create index if not exists ai_audit_events_run_idx
  on ai_private.audit_events(run_id)
  where run_id is not null;

commit;
