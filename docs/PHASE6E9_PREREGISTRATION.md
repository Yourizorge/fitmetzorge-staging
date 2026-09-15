# Package 6E-9 Preregistration

Recorded before implementation, 2026-09-15. Baseline main
8b7eb0c9c9488902451fe20e7385b4093237cc24. Local/direct remote equal, worktree clean.
33/33 migration versions match; official CLI 2.115.0 dry-run is empty.
Edge baseline: invite-client 16, nutrition-provider 20, youri-ai 43.

## Positive Workflows

A: synthetic member creates proposal, accepts exact revision; only its database-
linked trainer approves; separate apply creates version; restore is a new proposal
requiring both fresh approvals. B: server-owned independent eligibility with no
trainer, synthetic intake, editable complete training/nutrition/recovery bundle,
member confirmation then separate activation; restore preserves history.
Exercise/meal/food/recovery edits invalidate previous confirmation. J3 signals and
fictitious photo concept remain predefined, candidate-only and source-bound.

## Required Negative Cases

Anonymous access; other member/workspace; unrelated trainer; forged browser role,
subject/trainer/route; real non-test subject; expired/revoked session/consent/route;
A apply without either approval; B with any trainer or ambiguous authority;
old approvals/new candidate; changed relationship; rejected/blocked apply;
stale sources; duplicate action/key with same and different payload; concurrent
apply/apply, apply/edit and apply/revoke; forced fault rolls back whole mutation;
restore without new approvals; direct REST/RPC bypass; audit/notice disclosure;
extra keys and private chat/health/photo/free-text input; disabled feature flag.
O5 exact first-registration +30 days, early expiry, no retry/status extension;
expiry/deletion/self-report never gives medical clearance.

## Browser And Preservation

NL/EN/DE, light/dark/system, mobile/tablet/desktop, keyboard, reload/relogin/account
switch, loading/offline/retry/error, no overflow, distinct authority/version states.
Synthetic screenshots only; no claim of physical phone testing by the agent.
Preserve frozen sources and normal application assets; isolate new entrypoint.
Before/after server-side aggregate hashes only for existing data, no member content
in reports. Cleanup only exact newly created synthetic identities/fixtures.
No PostgreSQL/OneDrive deletion. No providers/email/push/storage/production/costs.

## Gates

No migration until local authorization/transaction tests and exact live identity
pass. Official CLI creates filenames; forward-only additive changes only.
Existing local PostgreSQL 18 is available; Docker is absent, pg_cron limitation
must be reported, not concealed with a claimed complete Supabase rebuild.
No TECHNICAL PASS until required live direct-API, concurrency, cleanup and
post-publication checks actually pass. No automatic owner acceptance or 6E-10.
