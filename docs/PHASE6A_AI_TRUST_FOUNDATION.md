# Phase 6A Youri AI Trust Foundation

Status: TECHNICAL PASS / READY FOR OWNER REVIEW

Date: 2026-09-01
Repository: `Yourizorge/fitmetzorge-staging` / `main`
Supabase: `mokxyyullfhkfalopbzd`
Production repository/ref: `Yourizorge/fitmetzorge` / `hgoygcviutmynaihcvpd` - FORBIDDEN

## Purpose

Package 6A establishes the provider-neutral trust boundary for Youri AI without activating OpenAI, configuring a provider credential, making an external AI call, charging a member, or exposing an operational member AI feature. It is a storage, authorization, consent, budget, safety, retention, audit and structured-contract foundation only.

## Owner Decisions Locked

- Primary future provider: OpenAI.
- Product model routes: `GPT-5.6 Luna` for normal/cost-sensitive work and `GPT-5.6 Terra` only for approved complex work. These are policy route labels, not active provider model IDs in 6A.
- No automatic cross-provider fallback.
- Separate explicit AI-processing consent with affirmative action, version, purpose, categories, timestamp and locale.
- Separate trainer-summary consent. Private chat is never trainer-readable.
- Consent withdrawal immediately blocks new AI processing while non-AI functionality remains usable.
- Active subscription chat remains available until member deletion. After AI entitlement ends, raw chat has a maximum 90-day grace period; reactivation within that window restores access, and expiry deletes raw content.
- Per active AI user/subscription month: EUR 3 included internal operating-cost ceiling, warning at 80 percent, at most EUR 1 Luna grace, EUR 4 absolute ceiling, Terra stopped before grace, no automatic member charge.
- Automatic action proposals are allowlisted, explained and reversible. Training load increases are limited to 20 percent. Larger reductions require fatigue/deload context. Calorie changes are limited to the smaller of 10 percent and 300 kcal and require sufficient new authoritative data.
- Serious or unclear health signals create a deterministic hard stop. Youri does not diagnose, prescribe treatment, modify medication or recommend training through the warning.

## Database Contract

Migration: `supabase/migrations/20260901193000_phase6a_ai_trust_foundation.sql`

Public own-user foundation tables:

1. `ai_consent_events` - append-only, versioned AI and trainer-summary consent/withdrawal events.
2. `ai_threads` - private member thread and 90-day retention state.
3. `ai_messages` - private immutable message foundation with deletion-ready raw-content nulling.
4. `ai_context_manifests` - immutable context hashes, source manifests and explicit unavailable sources.
5. `ai_action_proposals` - typed, bounded, explainable proposal records; no domain executor.
6. `ai_action_decisions` - append-only future member/trainer/system decision audit.
7. `ai_member_safety_state` - minimized current hard-stop/review state without raw prompts.
8. `ai_data_lifecycle_requests` - idempotent export/delete lifecycle request foundation.

Private operational/configuration tables in non-exposed `ai_private`:

1. `consent_documents`
2. `feature_flags`
3. `budget_policies`
4. `rate_policies`
5. `action_policies`
6. `structured_schemas`
7. `runs`
8. `budget_accounts`
9. `usage_ledger`
10. `rate_buckets`
11. `safety_events`
12. `audit_events`

All 20 tables use RLS. The eight public tables have own-user SELECT policies as defense in depth, but `authenticated`, `anon` and `PUBLIC` receive no base-table privileges. `ai_private` grants no schema/table/function access to browser roles. There is no INSERT, UPDATE, DELETE or trainer policy.

Composite ownership foreign keys prevent a message, run, context, proposal or decision from linking objects belonging to another member. Public member writes and reads are narrow RPCs deriving ownership from `auth.uid()`. Operational writes are service-role-only RPCs with fixed `search_path`; no service credential exists in browser/runtime code.

## RPC Boundary

Authenticated member RPCs:

- `fmz_phase6a_read_consent_contract(text)`
- `fmz_phase6a_record_consent(text,text,text,text,boolean,uuid)`
- `fmz_phase6a_get_trust_status(text)`
- `fmz_phase6a_get_context_manifest(text)`
- `fmz_phase6a_submit_user_message(uuid,uuid,text,text,text)`
- `fmz_phase6a_read_thread_history(uuid,integer,timestamptz)`
- `fmz_phase6a_request_data_lifecycle(text,uuid)`
- `fmz_phase6a_read_export_manifest()`

Service-role-only RPCs:

- `fmz_phase6a_service_begin_run(...)`
- `fmz_phase6a_service_complete_run(...)`
- `fmz_phase6a_service_fail_run(uuid,text)`
- `fmz_phase6a_service_record_safety_event(uuid,uuid,text,text,text)`
- `fmz_phase6a_service_reconcile_retention(uuid,timestamptz)`

Internal helpers are not executable by `PUBLIC`, `anon` or `authenticated`. No function performs an HTTP request or mutates Training, Nutrition, Recovery or Progress.

## Consent And Withdrawal

`ai_processing` and `trainer_summary_sharing` have separate NL/EN/DE versioned documents, purposes and category sets. Recording either grant or withdrawal requires `explicit_confirmation=true`; no preselection is represented. The current event wins. A database-generated monotone `event_sequence` makes that ordering deterministic even when multiple events share one transaction timestamp. A provider/mock run requires a current active AI document grant. Withdrawal therefore blocks the next trust-gate evaluation immediately.

The three digest-consuming RPCs use the fixed `pg_catalog, extensions, public, ai_private, pg_temp` search path required by Supabase's `pgcrypto` installation. Other Phase 6A functions retain the narrower fixed path.

All Phase 6A foreign keys have covering indexes. The performance advisor may still report new indexes as unused while the default-off tables are empty; that is expected until a later enabled package produces controlled traffic.

Trainer-summary permission is checked separately and creates no trainer read policy. Ending or withdrawing summary consent stops future sharing. Full private messages are not part of the summary contract.

## Entitlement And Feature Gates

Only current time-valid `ai` or `personal_coaching` rows grant structural eligibility:

- `status='active'`
- `starts_at <= now()`
- `ends_at is null or ends_at > now()`

Free, Pro, missing, inactive, expired and future entitlements deny generation. The browser cannot supply an entitlement, package, role, provider or model. Phase 7 still owns the 30-day trial lifecycle.

Live defaults after migration are locked to:

- `ai_coach_enabled=false`
- `provider_calls_enabled=false`
- `staging_mock_enabled=false`

OpenAI activated: NO. A provider call is impossible while the provider flag is false. The deterministic mock also requires the separate database flag and a local/Edge environment test flag, both false by default.

## Budget And Rate Contract

The current entitlement `starts_at` anchors the subscription-month period. Atomic advisory locks protect run identity, per-user monthly budget and per-feature rate windows.

- included: 3,000,000 EUR micros (EUR 3)
- warning: 2,400,000 EUR micros (80 percent)
- grace: 1,000,000 EUR micros (EUR 1)
- hard cap: 4,000,000 EUR micros (EUR 4)
- Terra stop: 3,000,000 EUR micros
- Luna may use the bounded grace
- automatic billing: false

Members receive only `normal`, `warning`, `grace` or `blocked` fair-use state, not a token-sale or raw-provider-euro presentation. Reservations, actual usage and releases are append-only and exact replay cannot reserve twice.

## Action And Safety Contract

Allowed proposal types:

- `training_volume_adjustment`
- `add_rest_day`
- `reschedule_training`
- `replace_exercise`
- `calorie_target_adjustment`

There is no execution RPC in 6A. Medication, diagnosis and treatment are absent from the allowlist. Every proposal must have an explanation and be reversible. Compatible exercise replacement is mandatory. Existing domain constraints and trainer authority remain authoritative.

Safety events store only category, outcome, policy version, run reference and timestamp. Raw prompts, chat, email, JWT, secrets and private health text are forbidden from operational audit metadata. A current `hard_stop` or `review_required` state blocks all new automatic processing/action paths until a service-reviewed resolution event exists.

## Context And Structured Output

The context RPC uses `auth.uid()` and reads minimized own-user aggregates/references from frozen sources. It does not copy domain authority into AI tables. It explicitly reports unavailable Health sync, running activity and progress photos. Notes and raw private text are excluded from the 6A context envelope.

`phase6a.response.v1` uses exact top-level keys, bounded arrays, a safety object and only allowlisted typed actions. Unknown keys, malformed fixtures and out-of-bounds actions fail validation before persistence.

## Deterministic Mock And Edge Scaffold

Edge folder: `supabase/functions/youri-ai`

The adapter interface is provider-neutral. `DeterministicMockAdapter` has fixtures for success, failure, timeout, malformed output, safety hard stop and out-of-bounds action. It declares and proves zero external calls. The Edge scaffold uses the member JWT and publishable key only; it contains no service-role key or AI-provider secret.

Ordinary staging members cannot receive mock coaching because database feature flags are false and `FMZ_PHASE6A_MOCK_TEST_ENABLED` is absent/false. Mock content is always labelled `deterministic_mock` and never presented as real coaching.

External AI calls: 0.
External AI cost: EUR 0.

## Retention, Export And Deletion Readiness

An active AI entitlement keeps thread retention `active`. Entitlement loss moves active threads to `grace` with an exact 90-day deadline. Reactivation before the deadline restores `active`. After the deadline, message raw text/structured content is nulled and the thread becomes `content_deleted`. Aggregate operational records may remain only under the minimized non-content contract.

Members can create idempotent export/delete lifecycle requests and read an own-user export manifest. Final archive packaging and account-wide deletion orchestration remain later chat/account lifecycle work, but the request identity, privacy boundary and retention enforcement hooks are live in 6A.

## Verification Artifacts

- Foundation migration: `supabase/migrations/20260901193000_phase6a_ai_trust_foundation.sql`, SHA-256 `5B48B142FBDC2298BF268CF5804F99053C9346E554FAA12B558409E3AA98EE6F`.
- Consent ordering correction: `supabase/migrations/20260901203000_phase6a_ai_consent_event_ordering.sql`, SHA-256 `7F653BF3BE688D294D68AF80689CCB4804EAF65CDE1D7C77559A8FDD2134C82C`.
- Pgcrypto search-path correction: `supabase/migrations/20260901204500_phase6a_pgcrypto_search_path.sql`, SHA-256 `B93B711519796958A2569A363CC1D3131A444EACE34EC04395E08ABA82EE4325`.
- Foreign-key index correction: `supabase/migrations/20260901211500_phase6a_foreign_key_indexes.sql`, SHA-256 `5997FE0BACD706503C8BF7397685EB14720C58E946B9BCF70DB58C70E6D52C9D`.
- Read-only verifier: `supabase/verification/20260901193000_phase6a_ai_trust_foundation_verification.sql`, SHA-256 `5A721B370718DD37FB5E534462B7848AEE98EA17CC0CB3838AD9E86D3547D818`.
- Transactional E2E: `supabase/tests/20260901193000_phase6a_ai_trust_transactional_e2e.sql`, SHA-256 `E2F9BDB2A111E8BCB6123C2021E005A9D9C59741E6824FBE8BB3D95DFA5558F1`.
- Static/security suite: `assets/phase6a-static-check.js`
- Mock/contract tests: `supabase/functions/youri-ai/youri-ai.test.ts`

All four migrations are live only on staging `mokxyyullfhkfalopbzd`, recorded as `20260901183914`, `20260901184418`, `20260901190328` and `20260901191328`. The exact read-only verifier returned `overall_pass=true`, 47 PASS and 0 FAIL. The transactional E2E returned `overall_pass=true`, `external_ai_calls=0`, `external_ai_cost_eur=0` and `fixtures_persisted=false`.

The deterministic mock/contract suite passes 11/11. Package 6A static/security checks pass 93/93 after this evidence update. Frozen suites pass Phase 1 75/75, Phase 2 46/46, Phase 3 222/222, Member UX 56/56, Phase 4 schema 90/90, Phase 4F-E 45/45, Nutrition browser 138/138, Phase 5 static 116/116 and Phase 5 browser 53/53.

The staging `youri-ai` Edge Function is deployed as version 1, status `ACTIVE`, with JWT verification enabled. Its deployed source is the reviewed provider-neutral disabled scaffold. An unauthenticated smoke request returned HTTP 401. No frontend runtime was changed or deployed for Package 6A.

Security advisors report only the intentional closed-schema `rls_enabled_no_policy` informational findings for `ai_private` and the intentional authenticated `SECURITY DEFINER` member-RPC warnings. Those RPCs derive ownership from `auth.uid()`, use fixed search paths, expose no base tables and have minimal ACL. Performance advisors report only expected unused-index informational findings while all 6A flags are OFF and tables are empty; no unindexed 6A foreign keys remain.

Implementation commits before this final evidence commit: `16ca8cd`, `828c8cf`, `4064689`, `a21b901`, `1fd5e96` and `5f7326b`. The final documentation commit is recorded in the completion report.

## Rollback And Next Package

The migration is additive. The immediate runtime rollback is to keep all three feature flags false and leave the member frontend unchanged. No existing domain row is rewritten. Pending AI proposals have no executor. If later forward correction is required, use a new reviewed migration; do not rewrite applied history.

Package 6B is NOT STARTED. It may not activate OpenAI until privacy/legal/DPA/international-transfer/DPIA and reviewed medical-safety gates are complete, real model IDs and spend controls are approved, and a separate controlled staging provider GO exists.

Package 6A result: TECHNICAL PASS / READY FOR OWNER REVIEW. It is not owner-accepted or frozen.

Production touched: NO.
