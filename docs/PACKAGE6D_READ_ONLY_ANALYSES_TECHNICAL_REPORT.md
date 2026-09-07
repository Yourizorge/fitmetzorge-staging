# Package 6D Read-Only Analyses Technical Report

Current status: COMPLETE / OWNER-ACCEPTED / FROZEN, explicitly accepted on a real
phone on 2026-09-07. See PHASE6D_FREEZE_RECEIPT.md and PHASE6D_FREEZE_EVIDENCE.json.
All pending-owner statuses in historical implementation/hotfix sections below are
superseded. Frozen runtime 7fec9da; Edge v43; cache 20260907-dashboard-placement1;
current migration parity 30/30. Only a read-only 6E readiness audit is authorized.

Accepted final follow-up: PACKAGE 6D FINAL DASHBOARD PLACEMENT HOTFIX.
See [current presentation report](PACKAGE6D_DASHBOARD_PLACEMENT_HOTFIX_REPORT.md) for
the exact order below greeting/Check-in/training, matching card styles and stable
hydration. Runtime 7fec9da7cb00cb7dff4a601810ddd2c977db0f5f; local/live426 checks,
42 live assets Git-identical. No migration, databasewrite or Edge change.
Owner confirms the lifecycle, mobile detail and final dashboard placement work.

See [preceding mobile report](PACKAGE6D_FINAL_OWNER_MOBILE_HOTFIX_REPORT.md) for
opened/missing-notification dashboard persistence, the newest-three read model and
fully bounded mobile comparison/detail. New live-assets browser 180/180, 25 layouts,
41 assets commit-identical, 23 member-table hashes unchanged. Current chain 30/30.
The automatic mock worker, renewed chat, vertical settings, device timezone/flags,
recovery, private-chat consent, approved floating avatar and Edge v43 are preserved.
The initial implementation receipt below remains historical evidence, not the latest
runtime/cache. Package 6D is now owner-accepted/frozen; prior evidence is preserved.

Date: 2026-09-06. Scope: staging only, `Yourizorge/fitmetzorge-staging` branch `main`,
Supabase project `mokxyyullfhkfalopbzd`. Production remains forbidden and untouched.

Status: MOCK-ONLY TECHNICAL PASS / OWNER TESTING PENDING. Package 6D is not
owner-accepted or frozen yet.

## Preflight

- Workrepo: `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy`.
- Git branch: `main`.
- Starting local HEAD and `origin/main`: `cbc6c5c9f23ea709314e33efa0f93f02d8b52fd1`.
- The user-provided expected HEAD `977e2311e969cb17dc753c007c3b3187675e4530` was already superseded by the public-auth/reconciliation work in this repo.
- `AGENTS.md` and `.codex/config.toml` confirm auto review, `workspace-write`, network-enabled staging work and permanent staging autonomy.
- Required status, architecture, test, reconciliation and public-auth hotfix documents were read before implementation.

## OneDrive Temp Safety

The exact checked temp directory was:

`C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp`

The only `local-rebuild-*` entries present on 2026-09-06 were directory reparse points:

- `...\supabase\.temp\local-rebuild-tc26YR`
- `...\supabase\.temp\local-rebuild-YIC31o`

A recursive scan under the current workrepo for `pg_control`, `config_exec_params` and
`postmaster.pid` returned zero files. `git ls-files supabase/.temp` returned zero tracked
files. No canonical migration, source, documentation, staging data or Git object was a
delete target. No files were deleted.

## Owner-Locked 6D Scope

- Initial analysis kinds: daily, post-workout and weekly.
- Placement: Youri AI member surface, under a separate Analyses tab.
- Consent: separate `ai_analysis` purpose; no reuse of private chat consent.
- Privacy: bounded aggregates only; no private 6C chat context, trainer notes/messages,
  photos, GPS, legacy water/bedtime workspace fields or free-text harvesting.
- Authority: read-only analyses only; no proposals, actions, domain writes, trainer
  sharing, trainer access or automatic changes.
- Retention: result content max 90 days; minimized audit metadata/tombstones max 180 days.
- Provider: no real provider calls. Daily/post-workout use Luna policy, weekly uses Terra
  policy for future accounting only; external provider activation remains false.
- Budget: shared 6A member cap model, EUR3 included, EUR2.40 warning, Luna-only grace to
  EUR4 hard cap, no Terra grace and no automatic billing.

## Database Changes

Migration `20260904230850_phase6d_read_only_ai_analyses.sql` adds the 6D boundary:

- Widened consent constraints for `ai_analysis`.
- `ai_private.phase6d_runtime_config` with `external_provider_enabled=false`.
- `public.ai_analysis_preferences`, `public.ai_analysis_results` and
  `public.ai_analysis_lifecycle_requests`.
- Active NL/EN/DE consent documents for `phase6d-analysis-v1`.
- Strict `phase6d.analysis.v1` structured schema registration.
- Bounded context, model-tier, budget, status, validation, retention and due-selection
  helper functions.
- Member RPCs for contract, consent, status, preferences, prepare, list, export and delete.
- Service-only RPCs for begin, complete, fail and due-selection.
- Retention cron `fmz-phase6d-analysis-retention-sweep`.

Migration `20260904235253_phase6d_analysis_lifecycle_safe_code_fix.sql` safely replaces
only `fmz_phase6d_delete_analysis` so lifecycle metadata uses
`analysis_result_deleted`, satisfying the existing no-content safe-code constraint.

No existing member rows were updated. No Training, Nutrition, Recovery, Progress, chat,
profile, entitlement, trainer-link or catalog table is written by Package 6D.

## Edge And Frontend Changes

- `supabase/functions/youri-ai/phase6d-handler.ts` implements
  `POST /functions/v1/youri-ai/phase6d/analyze`.
- The route accepts only `request_id`, `analysis_kind`, `locale` and optional `event_id`.
- The route authenticates the bearer token, uses database gates, generates deterministic
  mock output, validates strict no-action output and records zero-cost service completion.
- It imports no OpenAI adapter and exposes no provider/model/entitlement/user authority.
- `assets/phase6c-private-ai-chat.js` adds the Analyses tab, consent panel, preferences,
  generation buttons, result history, export and delete inside the existing Youri AI UI.
- Cache version: `20260904-phase6d-analyses1`.

## Live Verification

- `supabase migration list --project-ref mokxyyullfhkfalopbzd`: 27 local / 27 remote rows.
- `supabase db push --dry-run --skip-vault --project-ref mokxyyullfhkfalopbzd`:
  `Remote database is up to date`.
- Read-only live 6D verifier: 13/13 named checks PASS.
- Rollback E2E SQL: PASS; all synthetic rows rolled back.
- Post-E2E cleanup snapshot: 0 analysis results, 0 analysis lifecycle rows, 0 6D private
  run rows, 0 6D usage-ledger rows, 0 synthetic auth users, 0 synthetic profiles and
  0 synthetic workout rows.
- Staging Edge Function `youri-ai` deployed successfully as v42 with JWT verification
  enabled and the 6D route present.
- Unauthenticated live smoke on `/functions/v1/youri-ai/phase6d/analyze`: HTTP 401
  `UNAUTHORIZED_NO_AUTH_HEADER`.

## Test Results

- `node assets/phase6d-static-check.js`: 17/17 PASS.
- `node assets/phase6c-static-check.js`: 117/117 PASS.
- `node --test supabase/functions/youri-ai/phase6c-handler.test.ts supabase/functions/youri-ai/phase6d-handler.test.ts`: 25/25 PASS.
- `assets/phase6d-browser-check.js`: 48/48 PASS at 320x700, 390x844, 820x1180 and 1440x900.
- `assets/phase6c-browser-check.js`: 85/85 PASS.
- `assets/phase6d0-browser-check.js`: 41/41 PASS.

`deno test` was not available in PATH on this host. Node tests cover the TypeScript
handlers, and Supabase CLI deployment successfully bundled and uploaded the Edge assets.

## Data And Provider Impact

Existing member data is unchanged. The only persistent staging data added is schema,
configuration, consent-document, function, cron and migration-history metadata required
for 6D. Synthetic test data was transaction-scoped and rolled back. External provider
calls: 0. External AI cost: EUR0.00. No Brevo investigation, new confirmation email,
manual account confirmation, trainer role or trainer link was performed.

## Remaining Gate

Owner real-phone acceptance remains required before Package 6D can be frozen. Real-member
external provider activation remains a separate blocked gate requiring ZDR, DPA, DPIA,
exact EU route, privacy/medical/transfer/lifecycle evidence and explicit owner GO.
