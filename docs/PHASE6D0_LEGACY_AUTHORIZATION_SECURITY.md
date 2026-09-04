# Package 6D-0 Legacy Authorization Security Gate

Owner authority: 2026-09-04, staging only, FAST BUILD v2.
Base: 80ad593853f029183ecedd73d25ac92ecd23ed46.
Status: reviewed locally; transactional staging rehearsal PASS; permanent deployment pending.
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

- Migration: 20260904093300_phase6d0_legacy_authorization_gate.sql.
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
- Security browser contract suite: 37/37, 320x700, 390x844, tablet and desktop.
- Real assembled nine-patch source parses; no new polling, observer or external AI route.
- Frozen static: Phase 1 75; Phase 2 46; Phase 3 222; Member UX 56; navigation 41;
  Nutrition schema 90; Nutrition final 45; Phase 5 116; 6A 93; 6B 98; 6C 117.
- Frozen browser: Nutrition 138; Phase 5 53; 6C 85.
- Frozen mocked Youri AI tests: 53. External AI calls/cost: 0 / EUR 0.00.
- One 6C static cache assertion updated solely to accept the new shell cache while
  requiring the exact unchanged 6C avatar/runtime cache reference.
- Concurrency and post-deployment live evidence will be recorded below.

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
