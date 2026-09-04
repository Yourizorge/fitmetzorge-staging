# Package 6D-0 Legacy Authorization Security Gate

Owner authority: 2026-09-04, staging only, FAST BUILD v2.
Base: 80ad593853f029183ecedd73d25ac92ecd23ed46.
Status: COMPLETE / STAGING TECHNICALLY VERIFIED. Awaiting owner acceptance of this security gate.
This is identity remediation, not Package 6D analysis implementation or owner acceptance.

## Proven Causes

- SECURITY DEFINER bootstrap accepted arbitrary user ID without caller ownership.
- Auth signup trigger trusted editable role metadata.
- Legacy accept RPC trusted editable trainer/client metadata.
- Profile INSERT/UPDATE privileges and policies allowed direct role/link changes.
- Linked members could SELECT/UPDATE the whole trainer workspace, including other clients.
- Old invite Edge directly relinked existing accounts using privileged profile writes.

## New Authority

- Bootstrap signature retained, but only auth.uid() may be targeted. New role is always client.
  Existing database trainer roles are retained; public trainer signup was already disabled in Phase 1.
- Signup metadata creates no role. Phase 1 remains the member account foundation.
- Browser profiles are SELECT and own display-name UPDATE only; no role/link/email/ID writes.
- Old accept_client_invite(text) reads an existing own relationship only.
- Server-issued invitation: stored trainer role + exact owned legacy client slot + stored email.
  Browser email, trainer ID, role and redirect never determine authority.
- Random 244-bit token, SHA-256-only database storage, verified Auth email binding,
  24-hour validity, one acceptance, revocation, supersession and conflicting-link rejection.
  Authentication verifies the mailbox; possession of the token alone is insufficient.
- All issue/accept/revoke routes lock email then trainer/client slot. Acceptance locks the
  member profile before the workspace, matching the member-save route.
- A private invitation ledger has RLS and no anon/authenticated/service_role table access.
  No AI consent, trainer-summary consent, entitlements or subscription record is written.
- Direct workspace access is trainer-own only. Linked members use an auth.uid()-bound
  projection/merge RPC: one client, no other clients, trainer account/finance or password.
  Only shared legacy exercise identity/media fields accompany the own-client projection.
  New member writes replace only that array element under row lock and revision comparison.
  Identical retry returns replay; changed stale writes fail instead of overwriting another edit.
- Invitation mail still uses existing Supabase Auth invitation/recovery delivery. Delivery
  failure revokes the pending invitation. Existing valid links are never rewritten by issuance.
- The callback token is captured in per-tab sessionStorage and removed from the URL. It is
  cleared on acceptance/invalidity. It survives the existing recovery signout-to-login step;
  the server still enforces email binding, expiry and one-use. It is never an AI credential.

## Changes

- Canonical migration: 20260904105918_phase6d0_legacy_authorization_gate.sql.
  Original reviewed filename used 20260904093300; identity reconciled without changing SQL.
- New private schema/table: legacy_auth_private.client_invitations.
- New unique partial index: profiles_unique_trainer_client_slot (existing duplicates would fail, not be cleaned up).
- Changed bootstrap, signup trigger function, legacy accept function; hardened helper search paths/ACLs.
- Five RPCs: issue/accept/revoke invitation; read/save own legacy workspace.
- Profiles: old public trainer-insert policy removed; remaining policies authenticated-only.
- Workspaces: linked-member whole-workspace policies replaced by trainer-own policies.
- No existing member/relationship/data rewrite, no deletion or reset migration.
- Edge: invite-client only. Youri AI and nutrition-provider remain frozen.
- Frontend: index.html, app.js, assets/phase6d0-legacy-auth.js; security patch loads before
  Phase 1 captures the legacy helpers. Frozen Phase 1-6C runtime assets are unchanged.
- Cache: 20260904-phase6d0-auth1; frozen 6C asset keeps its approved-avatar version.

## Verification

- Transactional rollback E2E: 48/48 (only synthetic example.invalid accounts).
- Read-only verifier rehearsal: 40/40.
- Invite Edge local mocked tests: 10/10; no real invitation email sent by tests.
- Security browser contract suite: 41/41, 320x700, 390x844, tablet and desktop.
- Real assembled nine-patch source parses; no new polling, observer or external AI route.
- Frozen static: Phase 1 75; Phase 2 46; Phase 3 222; Member UX 56; navigation 41;
  Nutrition schema 90; Nutrition final 45; Phase 5 116; 6A 93; 6B 98; 6C 117.
- The historical Phase 1 and Member UX harnesses also PASS against the actual deployment
  checkout through assets/phase6d0-frozen-regression-check.cjs (75 + 56). Only missing
  historical SQL fixtures are read from the archive. Obsolete cache expectations are
  refreshed; the gold-action assertion renders both Sleep detail and the already-frozen
  Phase 5 Progress navigation branch. No frozen runtime or security assertion is weakened.
- Frozen browser: Nutrition 138; Phase 5 53; 6C 85.
- Frozen mocked Youri AI tests: 53. External AI calls/cost: 0 / EUR 0.00.
- One 6C static cache assertion updated solely to accept the new shell cache while
  requiring the exact unchanged 6C avatar/runtime cache reference.
- Live two-session concurrency: 8/8, exactly one invitation acceptance; replay denied;
  exactly one competing workspace write; stale competitor denied; all fixtures removed.
- Live read-only frozen database verifiers: Nutrition final 22/22, Phase 5 30/30,
  6A freeze 47/47, 6B 36/36, 6C 37/37, request-scoped safety 16/16.
- Frozen transactional 6A and both 6C E2Es PASS, with zero fixtures remaining. The two
  old 6C trainer fixture setups now explicitly insert a trusted test trainer rather than
  depend on the deliberately removed metadata vulnerability; assertions are unchanged.

## Live Deployment Receipt

- Runtime/migration commit: ab9b3f186898522ae91dba230e8df0adf1f9d895.
- Staging: mokxyyullfhkfalopbzd; ACTIVE_HEALTHY.
- Migration history: 20260904105918 / phase6d0_legacy_authorization_gate.
- Git and live 6D-0 versions now match. See [identity reconciliation](PHASE6D0_MIGRATION_IDENTITY_RECONCILIATION.md).
  The broader pre-existing migration-history drift was later resolved by the
  project-wide reconciliation without SQL replay; see
  [project migration reconciliation](PROJECT_MIGRATION_RECONCILIATION.md).
- Migration SHA-256: 5B91B22F823A30F86E329B381FE797FD28655D237AD977D6B80D2C99AF5485B3.
- Verifier SHA-256: 9B5F54B40550F57AD67D678AD5A5889CAB2BA31897B81DD873E5171EF4FCE76D.
- invite-client: version 16, JWT enabled, ACTIVE.
- Edge bundle SHA-256: 06bc95c43054de7630b0a4538d0cbe568f98162717c29be3da84919688a4cc63.
- Live index/app/security asset: HTTP 200 and byte-identical to the runtime commit.
- index.html SHA-256: c9168f8cc08535918de294da628fa462ab1b1d633feac5e64f133bb8d9ff1ee0.
- app.js SHA-256: 3b6156756ddd1553e6b7653a352a67455e25bd6b5c7506a7d694fe7229b23747.
- phase6d0-legacy-auth.js SHA-256: fdaca0d3637ca2dcd36fad7a3698ff6c4edae709c582ef3c6709530e2012d4e3.
- Live unauthenticated invitation: 401; approved staging preflight: 204.
- Assembled live logged-out runtime: 320x700, 390x844, 820x1180, 1440x900 PASS;
  no page errors, horizontal overflow or mutating Supabase requests.
- Frozen chat/avatar bytes unchanged. Youri AI version 41 and bundle SHA unchanged.
- Existing profiles, entire legacy workspaces and entitlements: before/after server-side
  checksums identical. Six profiles / two linked profiles remain; chat counts unchanged.
- No new real invitations, no real account emails sent, no raw owner chat inspected.
  SMTP delivery is locally mocked, not claimed as a new real-mail E2E result.
- All 6D-0 fixture Auth accounts and invitation rows: 0 remaining.
- Advisor anonymous SECURITY DEFINER warnings: 8 -> 0. Security inventory: 81 -> 78:
  25 RLS/no-policy INFO (private operational isolation), 51 authenticated-definer WARN
  (guarded RPCs), one historical mutable-path WARN and one leaked-password-protection WARN.
  No new private-chat trainer policy or widened normalized access.
- No material blocker remains for the targeted authorization gate.

## Reproducible Tests And Transport Notes

- Run assets/phase6d0-browser-check.js with local Playwright.
- Run node assets/phase6d0-frozen-regression-check.cjs with the original archive available
  (or FMZ_ARCHIVE_ROOT pointing to it). Runtime files always come from the Git checkout.
- Run node --test supabase/functions/invite-client/handler.test.ts (network-free).
- Run the complete rollback E2E SQL and SELECT-only verifier against staging.
- Set FMZ_PYTHON to the bundled Python binary, then run
  node supabase/tests/phase6d0-concurrency-check.cjs. The helper uses the existing
  Windows Supabase CLI credential in memory through the fixed staging Management API.
  No key is printed, persisted, passed as an argument or returned to the model.
- Initial concurrent CLI processes stalled during login-role initialization (also reproduced
  by simultaneous SELECT-only probes). All attempted fixture runs were cleaned up. A
  fixed-target Management API transport removes that CLI serialization. An explicit
  non-secret test User-Agent resolves its default-client HTTP 403. No SQL safety rule
  was weakened to obtain PASS.
- Final helper sends generated synthetic SQL through stdin, not credential arguments or
  token-bearing files. Only allowlisted error classes and aggregate test outcomes are logged.
- assets/phase6d0-live-check.cjs verifies immutable runtime bytes and clean browser startup.
- Evidence-only follow-up commit contains the final helper/test/docs results; no second
  runtime or database deployment is needed.

## Deployment And Privacy Boundaries

The old invite Edge must be replaced before the migration, failing closed until its new
RPC exists. The new frontend is published immediately after schema verification. During
this staging-only transition old member tabs may need refresh; no permissive fallback exists.
Do not weaken RLS to accommodate cached legacy JavaScript.

No original personal photographs, secrets, owner messages or unrelated member data are
copied into fixtures/reports. Preservation evidence uses server-side checksums/counts only.
Pending invitation records are private operational authorization records, not chat context.
Expired tokens never authorize access; no real invitation data cleanup is part of this task.
Existing trainer workspace editing remains the legacy trainer-owned workflow, not a new
Trainer Environment or permission to normalized private AI records.

Broader Advisor INFO/WARN inventory is not equivalent to exploitable defects. The old
touch_updated_at search-path advisory and leaked-password-protection setting are outside
this focused gate; they must not be claimed resolved. Current official RLS guidance:
https://supabase.com/docs/guides/database/postgres/row-level-security

Package 6D functional analyses: NOT STARTED.
Real-member external AI: DISABLED. Production: UNTOUCHED.
