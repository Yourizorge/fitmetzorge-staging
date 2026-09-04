# Public Auth Registration Hotfix

Date: 2026-09-04. Scope: staging only, mokxyyullfhkfalopbzd.
Status: DEPLOYED / LIVE TECHNICAL PASS. Owner inbox/confirmation acceptance pending.

## Root Cause

The legacy renderAll dispatches every dashboard renderer, including Progress, without
an authentication boundary. Phase 5 replaces the Progress host's legacy markup for
members. Its non-member branch delegates to the captured legacy renderer, which assumes
progressGoalStrip still exists. A subsequent logged-out render can therefore reach a
detached legacy DOM contract. A persisted loggedIn UI boolean also did not prove that a
real session/profile had finished hydrating. Auth startup and password-link handling
could run the member render chain before that lifecycle was ready.

The no-session signup branch itself already returned without profile hydration; signup
success does not prove that all other render entry points are safe. The reported Auth
signup HTTP 200 and the frontend failure are independent. The new assembled-browser
fixture removes the legacy element, exercises public routes and transitions from member
Progress back to Auth to guard the complete failure path.

## Fix

- Phase 1 defines app-ready login as an authenticated, hydrated profile; persisted UI
  state, password setup and public confirmation/error screens do not qualify.
- The Phase 1 renderAll boundary performs only Auth styling/copy/visibility while
  public; no member/dashboard dispatch or state-save occurs. Public nav remains empty.
- A final loader binding wraps the complete renderer/navigation chain after all modules
  load. Cold Auth routes do not invoke frozen module teardown (including Training's
  vibration cancellation); an existing app session is torn down once on logout.
  This additional path was found by the actual live browser console check, not hidden
  by suppressing console errors. Training runtime bytes remain unchanged.
- User hydration requires a session and a current Auth epoch. Late onboarding results
  are discarded after logout/recovery. Invite/recovery callbacks no longer prehydrate
  member workspaces before password setup.
- Confirmation/error callbacks stay in the public shell, clear URL auth parameters and
  require explicit successful login. A status-only session flag preserves this on refresh.
  Confirmation success text requires a confirmed Auth session, not merely a query flag.
- Phase 5 adds a public no-op, a defensive legacy mount check and async session guards.
- Public login/register/reset/password errors use localized safe text, not raw errors.
- Resend uses auth.resend({type:"signup",email,options:{emailRedirectTo}}), a shared
  in-flight gate and 60-second cooldown. Only the deadline is session-persisted.
  NL/EN/DE feedback is enumeration-safe; known account-state responses share generic copy.
  Server/network failures are not displayed as a successful send. Auth remains authoritative.

Runtime files: index.html, app.js, app.bundle.js, assets/phase1-foundation.js,
assets/phase5-progress.js. Cache: 20260904-auth-lifecycle2.
The legacy bundle change is required for callback ordering and safe public error handling;
it is not an unrelated refactor. No Edge, migration, RLS, trainer or AI change.

## Exact Account And Mail Evidence

Only the owner-designated trainercheck account was inspected, without publishing its
email, UUID, credentials, confirmation link or tokens.

- Exactly one Auth account, created 2026-09-04 12:15:18.628951 UTC.
- Email identity exists; account is not deleted and remains unconfirmed.
- Signup log: HTTP 200 at 12:15:19 UTC; confirmation_sent_at initially
  12:15:18.704475 UTC. This is a real new account, not merely an obfuscated existing-user
  response. No corresponding rate-limit/mailer rejection is visible in returned Auth logs.
- Email confirmation required. Custom Brevo SMTP configured; required field presence
  checked as booleans only. Send-email hook disabled. Rate limit 30/hour, cooldown 60s.
- Site URL and exact allowed redirect match staging. The app emailRedirectTo matches.
  Confirmation template uses ConfirmationURL, without a custom token route.
  URL-path override is empty, so Supabase's default verification path applies; OTP TTL 3600s.
- No misconfiguration was established, so no speculative SMTP/Auth configuration edit
  was made. Brevo mailbox delivery/bounce/spam status is not available through Supabase
  Auth logs or the SMTP credentials alone. Provider event access is an owner-only follow-up
  if delivery is still missing; do not request another resend automatically.
- Exactly ONE /auth/v1/resend request: HTTP 200. confirmation_sent_at advanced to
  2026-09-04 12:41:49.407945 UTC. Supabase dispatch accepted; inbox delivery NOT proven.
- A local preflight initially received a transport rejection before the resend request;
  adding the same explicit non-secret User-Agent as the existing approved transport
  resolved it. That preflight did not send a mail. A local exclusive receipt prevents
  accidental repeat execution; it contains no email/token and is not committed.
- No account recreation/deletion, manual confirmation, trainer role or linkage created.
  The intended Auth mutation is only the supported confirmation-resend lifecycle.

## Tests

- Actual assembled browser runtime: 88 PASS, including public signup, failed login,
  reset, password setup, confirmed/error callbacks, delayed session response, refresh,
  cooldown, duplicate taps, NL/EN/DE, successful member login, Progress and logout.
- 320x700, 390x844, 820x1180, 1440x900: no console errors/horizontal overflow.
  Screenshots reviewed locally; no personal data or tokens in fixtures/screenshots.
- New static/security/syntax/combined parse: 26 PASS.
- Frozen static: Phase 1 75; Phase 2 46; Phase 3 222; Member UX 56;
  Nutrition schema 90/final 45; Phase 5 116; 6A 93; 6B 98; 6C 117.
- Frozen browsers: Nutrition 138; Progress 53; private chat 85; 6D-0 41.
- Mock invite Edge, mock private-chat Edge and migration identity unit suites PASS.
- Live read-only verifiers: Nutrition 22, Progress 30, 6A freeze 47, 6B 36,
  private chat 37, request safety 16, 6D-0 authorization 40. Total 228 PASS / 0 FAIL.
- Historical test cache expectations were updated only for changed runtime URLs.
  Missing legacy SQL/catalog fixtures are read from the original archive; actual runtime
  under test comes from this checkout. No catalog import or generation is deployed.

## Live Deployment Receipt

- Repository/branch: Yourizorge/fitmetzorge-staging / main.
- Implementation commit: e63e05b325bf9302a74e7c03c995171ee9d81675.
- Final runtime commit: 333954a68a1429634e49bafbcc08720ea688131a.
- Cache: 20260904-auth-lifecycle2.
- Live index.html, app.js, app.bundle.js, Phase 1 and Phase 5 assets: HTTP 200 and
  SHA-256 identical to the committed blobs. Frozen Phase 6C and 6D-0 assets also
  HTTP 200 / commit-identical. No runtime change is included in the final evidence commit.
- Actual staging public login/register/forgot navigation and refresh: PASS at
  320x700, 390x844, 820x1180 and 1440x900; zero console/page errors and zero mutating
  requests. Real confirmation/password flows were covered with synthetic Auth responses
  in the 88-check assembled-browser suite, not by consuming the owner's email link.
- Live verification did not authenticate as the owner or create another account.
- Before/after read-only fingerprints of profiles, workspaces, entitlements and
  normalized functions match; private chat row counts match. No member/trainer data
  or schema change. The single supported Auth resend is the only intended account action.
- Full project migration history is NOT synchronized. The separate reconciliation
  gate is BLOCKED, as documented in PROJECT_MIGRATION_RECONCILIATION.md. Its dry-run
  applied no SQL and the live migration history is unchanged.

The remaining mail question is delivery, not dispatch: Supabase accepted the one resend,
but the reason the first email was not received cannot be established from the available
Auth logs. If the new email is absent, inspect Brevo delivery/bounce events with owner
provider access. Do not resend again automatically, reset credentials or confirm manually.

Package 6D functionality NOT STARTED. External member AI stays disabled. No external
AI calls or cost. Production UNTOUCHED.
