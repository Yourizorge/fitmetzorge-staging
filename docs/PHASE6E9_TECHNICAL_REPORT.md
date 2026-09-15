# Package 6E-9 Technical Report

TECHNICAL PASS / READY FOR OWNER REVIEW - SYNTHETIC BACKEND ONLY.
Final evidence is recorded in PHASE6E9_EVIDENCE.json.
6E-9 is not owner-accepted/frozen. Phase 6E remains incomplete; 6E-10 is not started.

## Baseline And Acceptance

Repository Yourizorge/fitmetzorge-staging, branch main; initial local, cached and
direct remote HEAD 8b7eb0c9c9488902451fe20e7385b4093237cc24, clean worktree.
Actual repository is the nested supabase/.temp/phase4fb-staging-deploy checkout,
not the outer assets directory. No reset, unrelated edit or file cleanup occurred.
AGENTS.md and project config retain on-request/auto_review/workspace-write.
Managed permissions were honored through scoped reviewed commands; no settings changed.

Commit 1666915 records explicit physical owner acceptance of 6E-8/J1-J3:
COMPLETE / OWNER-ACCEPTED / FROZEN - SYNTHETIC STAGING DEMO ONLY.
The receipt records source 936dd3a, delivery 8b7eb0c and 219 protected source/runtime
hashes. Existing historical reports are preserved with correction references.
D1-D12, O1-O5 and all accepted 6E-0 through 6E-8 decisions remain unchanged.

## Cause And Architecture

6E-8 deliberately stored a fictional workflow in browser memory. Its persona
selector could demonstrate UX but could not prove real identity, authorization,
durability or database atomicity. 6E-9 adds a SEPARATE public entry,
coach-backend-demo/index.html; it does not replace the accepted memory demo or
normal application bootstrap.

The new fmz6e9-synthetic Edge endpoint verifies the caller with Auth, uses that
user's JWT for PostgREST, and adds an isolated server-only proof. No service role
in the frontend or workflow Edge. Provisioning alone uses the EXISTING admin key
in a private test broker's memory; passwords, access tokens and proof values are
not written to evidence, command arguments or repository files.

Server eligibility is a dedicated expiring synthetic allowlist. The existing
6D-0 profiles.role / profiles.trainer_id authority is read only for these NEW
synthetic identities. No editable user_metadata, client role/user/trainer/route
or automatic fallback can grant authority. A linked trainer is required for A;
an explicitly independent fixture plus absence of a trainer is required for B.

Frozen 6E-7/6E-8 deterministic models are bundled verbatim and replay only closed
catalog commands on the server. Their model hash is version-bound. This is NOT
AI inference or proof that fictional trainer sources are authentic live rules.
The trusted Edge planner computes the result; a browser cannot submit a trusted
next state directly because transaction RPCs also require the server proof.

## Objects And Atomicity

One additive migration, officially named by CLI 2.115.0:
20260915072202_phase6e9_synthetic_authorization.sql.
SHA256: 2d470e0da00c9fe9e96b5d942c941cbf6dad2c8964e36799909b9dbe601c46c3.

Five private tables: config, subjects, safety, versions, requests.
Two public read surfaces: fmz6e9_audit, fmz6e9_notices.
Six private functions: can_read, context, read_state, commit_state, home,
replay_request. Four public SECURITY INVOKER wrappers: fmz6e9_home/read/replay/commit.
No views. All seven tables have RLS. No client table write grants or write policies.
Private SECURITY DEFINER helpers have pinned search_path and revoked PUBLIC/anon/
service_role defaults. context is owner-only; authenticated EXECUTE on the other
private helpers is necessary for the invoker wrapper/RLS chain. The private
schema is not exposed through Data API. Direct RPC without server proof fails.

Reads bind auth.uid(), a non-revoked/non-expired auth.sessions entry, feature flag,
workspace expiry and ownership. Audit RLS allows only own/actually linked A data.
Notice RLS additionally requires recipient=auth.uid(). No UPDATE policy is needed:
all direct INSERT/UPDATE/DELETE is denied, so there is no missing WITH CHECK path.

The transaction locks configuration, subject and ordered relevant profile rows.
It binds expected revision, model/source revision, profile timestamps, eligibility,
consent and exact candidate hash. A member acceptance, trainer approval and separate
application are distinct. B needs member confirmation but has no trainer approval.
Editing invalidates approvals. Restore creates a new candidate and monotone version.
Whole version, audit, notices and idempotency receipt commit together or roll back.
Prior immutable versions are never overwritten. Same-key retries return the receipt;
changed payload under that key and stale writes fail. A different-key second apply
cannot repeat a completed proposal.

Audit contains actor/role/action, proposal hash, source/target version, server time,
status and request ID. Notices contain only recipient, code and request ID.
No free chat, health narrative, uploaded photo or custom arbitrary source fields.
J3 remains a fixed fictional catalog with no Storage or provider connection.

## Tests

- 1,725/1,725 offline/frozen tests PASS; final counts in evidence.
  The 219 file hash checks are preservation checks, NOT recognition successes.
- 48 local PostgreSQL authorization/concurrency groups PASS, also from a fresh
  checkout of 0fcffc3. Minimal Auth stubs are not represented as hosted Auth.
- 23 real staging Auth/Edge/REST security/workflow groups PASS.
- Hosted and initial published browser runs: 199 checks / 72 layouts PASS.
  Final published run including explicit loading lock: 200/200 checks, 72 layouts,
  zero page errors, followed by full synthetic cleanup.
- Widths 320/390/768/1280, NL/EN/DE, light/dark/system; both routes and B's three tabs.
  Account switch, logout/relogin, refresh, lost apply response + same-request retry,
  offline/online recovery, keyboard focus and zero horizontal overflow.
  These are desktop Edge emulations, NOT a physical iOS/Android test.

Negative coverage includes anonymous, unrelated member/trainer, synthetic ordinary
non-fixture principal, forged metadata/payload, direct REST/RPC, absent proof,
missing A approval, forbidden B trainer action/link, duplicates, stale approvals,
changed source/consent/profile authority, rejection, cross-recipient notices,
logged-out tokens and non-allowlisted health/photo/private fields. No real account
was used to test denial: a new non-fixture principal exercises the same predicate.

Actual concurrent Edge apply/apply commits once. Local additional same-key race,
apply/edit and lock-winning consent revocation pass. A forced fault AFTER version/
audit/notices but BEFORE request receipt rolls the entire transaction back, locally
and on staging. The temporary fault trigger/function were removed immediately.

Safety fixture tests keep distinct message references; clarification removes only
communication markers, never another health report. Self-report and 30-day O5 expiry
do not release physical proposals. Expired/needless references are removed and an
eligibility/context-required marker prevents reconstruction or clearance by expiry.
No medical text or old report is copied into that marker. This is a synthetic
fixture contract, not a new live classifier or completed clinical recovery flow.

## Migration And Reconstruction

All previous 33 identities matched exactly before application. Official dry-run
listed ONLY this new migration, with no seeds or roles. CLI applied it once to
mokxyyullfhkfalopbzd. Post-application dry-run is up to date; final inventory in evidence.
No history repair, historical remote replay, remote reset or production target.

The official migration-new command encountered an existing-directory OneDrive CLI
error. It was run in an empty ignored tool-authoring directory; only that newly
CLI-named file was copied to canonical migrations and authored. No version invented.

Fresh checkout outside OneDrive: fmz6e9-checkout-40b920f40e924cde995b253d3231220c.
Exact new migration plus its 48 tests rebuild successfully. Historical reconstruction
applies 22 migrations and explicitly skips the remaining 12 because local pg_cron
is absent. Docker is unavailable. This is NOT a claim of a complete hosted Supabase
rebuild/schema diff. PostgreSQL temporary clusters were stopped and retained;
zero PostgreSQL/OneDrive files were deleted.

## Preservation, Advisors And Cleanup

Before/after evidence compares all 66 pre-existing public/ai_private/legacy_auth_private
tables using row counts and order-independent server-side SHA256 aggregates.
Only aggregates leave the database. Exact new Auth IDs are captured and removed;
sessions are revoked BEFORE deletion. New synthetic profile rows and fixtures are
removed, including versions, audit, notices and request receipts. The feature flag
returns to false and the temporary FMZ6E9_PROOF secret is removed.

Security advisors: no new WARN/ERROR. Five additional INFO rls_enabled_no_policy
items are deliberate private deny-all tables. Existing warnings remain unchanged:
function_search_path_mutable 1, authenticated_security_definer_function_executable
68, auth_leaked_password_protection 1. Performance counts unchanged: unindexed FK
16 INFO, auth_rls_initplan 47 WARN, unused_index 32 INFO.

Only the new Edge source was deployed. Supabase secret add/remove operations also
increment existing function deployment counters; their bundle hashes and source
timestamps remain unchanged. Do not confuse the counters with code changes.
Final Edge counters: invite-client 16 -> 24, nutrition-provider 20 -> 28,
youri-ai 43 -> 51; all three prior bundle hashes are identical.
New fmz6e9-synthetic final counter 10, verify_jwt=true, bundle SHA256
e74a071c3cf6b01a1561dd33910a9893029bcc959f212e43452f9095950965f4.
Both new Edge source deployments are isolated; remaining counter increments are
the platform's secret-environment reloads. No explicit deploy command targeted
any previous function; their code bundles remained byte-identical.

Published proof before final docs: 80/80 assets match Git, including 76 unchanged
existing assets and four new demo assets; 185 private offline/test paths return 404.
All 60 application runtime assets and accepted timer/RIR/RPE remain unchanged.
No external AI, email/push or photo calls; external AI cost EUR 0. Production untouched.

## Corrections Found During Verification

Historical failed attempts are not counted as passes. Initial local SQL syntax,
immutable view projection and local psql-null transport issues were corrected.
The browser mock required an explicit offline check and lost-response simulation.
First hosted probe correctly returned disabled 503; the test expectation was fixed.
A subsequent probe exposed a missing explicit version-list projection; the endpoint
now returns database version identities. Cleanup completed after failed attempts.
Uncertain-network wording was corrected from a false failure claim to no confirmation.
No bypass of an authorization check, frozen source or historical migration occurred.

## Limits And Next Step

No owner acceptance of 6E-9 yet. After cleanup the public URL intentionally cannot
log in or operate until a new explicitly provisioned synthetic test window exists.
The receipt is NOT a promise of permanent test accounts or immediate phone access.
Auth infrastructure may retain its normal operational logs; no existing Auth log
retention/configuration was changed. No clinical data entered this dataset.

Source rules, goals, safety and independent eligibility remain controlled fixtures.
No real trainer onboarding, independent paid membership, durable clinical recovery,
automated retention scheduler, provider, real photo analysis or real plan application.
O5 deletion is exercised on access plus unconditional test cleanup; unattended
long-lived retention is not claimed. Synthetic subjects expire within 24 hours,
but expiry is not itself a scheduled physical deletion job.

Medical, nutrition/recovery content, native-language review and privacy/legal
purpose/retention decisions remain open for real use. External member processing
requires the separately scoped DPA/ZDR/DPIA/EU-route/consent and cost decisions.
Existing non-medical synthetic workflow testing does not require medical clearance.
Recommended next scope: PHASE6E10_PROPOSAL.md, not started.

## Exact Delivery Sources

- 16669159458e9f0ba8d0ea112c9866c29470b877: 6E-8 acceptance/freeze and preregistration.
- 0fcffc3fc223ee60cd9c6d99788a764a253a710a: new backend, UI, migration and tests.
- 0623b51cbd7b65867fb9d6444392d949ea8b317e: explicit version response and hosted tests.
- 383e25d4b893e549a062a5a357b1c8d797b6c924: final demo feedback and loading tests.
- The final documentation/evidence commit is the Git revision containing this
  report; its full remote HEAD and post-docs Pages result are reported at delivery.

Runtime publication runs 34947028289 (0623b51) and 34948042583 (383e25d) succeeded.
The final docs-only publication is separately checked against these same 80 assets.
Evidence includes per-file hashes; local full TAP, SQL/browser JSON and screenshots
remain in supabase/.temp/phase6e9-* and are not published as private source files.
Version-conflict feedback is transient in-app notification, not a partial committed
version/audit. Committed transitions are audited; rejected unauthorized requests
do not insert another user's notice or partial transaction history.

Official guidance checked before implementation: Supabase changelog (2026-09-15),
[RLS](https://supabase.com/docs/guides/database/postgres/row-level-security),
[functions](https://supabase.com/docs/guides/database/functions),
[Auth server checks](https://supabase.com/docs/guides/auth/server-side/advanced-guide)
and installed CLI help. No settings or extension/provider upgrade was needed.
