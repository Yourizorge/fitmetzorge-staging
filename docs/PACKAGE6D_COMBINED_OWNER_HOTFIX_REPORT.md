# Package 6D Combined Owner Hotfix Technical Report

Date: 2026-09-06. Staging only: Yourizorge/fitmetzorge-staging, main,
Supabase mokxyyullfhkfalopbzd.

**PACKAGE 6D COMBINED OWNER UX/SAFETY HOTFIX - READY FOR OWNER RETEST**

This is technical readiness, not owner acceptance or a new freeze. The combined
owner instruction supersedes the earlier 6D additions. Package 6D remains mock-only
and read-only with respect to Training, Nutrition, Recovery and Progress.

## Preflight And OneDrive

- Initial clean main, local HEAD and origin/main:
  79f9c587f31cc766f0d24f5597fbcaecfe35ff20.
- Earlier expected 977e2311e969cb17dc753c007c3b3187675e4530 was superseded by
  already committed public-auth, reconciliation and initial Package 6D work.
- Sole workrepo:
  C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy
- AGENTS.md, .codex/config.toml, status, Master Plan, architecture, test matrix,
  reconciliation, public-auth and Package 6D documents were read.
- Config retains auto_review, workspace-write, network_access=true and permanent
  staging autonomy. Managed runtime restrictions still apply; no permissions,
  global settings or production boundary was relaxed.
- No confirmation mail was sent, no Brevo investigation performed, no account
  manually confirmed, and no real trainer role or link added.

The checked PostgreSQL cleanup candidates remain these exact old paths:
C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\local-rebuild-tc26YR
C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\local-rebuild-YIC31o

They were reparse points without a resolved target exposed by PowerShell. The earlier
workrepo scan found no pg_control, config_exec_params or postmaster.pid files.
This does NOT prove all 971 OneDrive pending deletion targets are disposable:
their full OneDrive deletion manifest was unavailable. Therefore nothing was deleted,
and no PostgreSQL cleanup command was run. Canonical SQL, sources, docs and Git are
untouched by cleanup. The two disposable source checkouts made for this verification
also remain under the workrepo's ignored supabase/.temp; they contain no database cluster.

## Causes And Safety Recovery

The old analysis gate read retained hard_stop/review_required as an enduring
operational denial and had no separate member recovery record. Clearing that original
state would also weaken future action safety. The corrected design separates:

1. Current request classification in the existing deterministic Edge classifier.
2. Temporary analysis denial, derived from the current safety revision.
3. Original historical state and minimized safety_events, unchanged.
4. Own-member recovery for exactly that revision, in analysis_safety_recoveries.
5. Future automatic-execution safety, still blocked independently.

The UI explains the temporary stop, absence of diagnosis and need for professional
or urgent assistance with current/recurring serious symptoms. Three unselected,
explicit confirmations are required. Recovery stores only user/revision, reason
enum, request identity, policy version and timestamp, not symptom prose.
The own-member RPC serializes with the same lock as a new serious signal, rejects
stale revisions and replays an identical request. It never rewrites old safety events.

All five owner recovery phrases may offer the confirmation dialog; none silently
clears safety. The six contradictory/current/bypass examples do not request
recovery. Serious symptoms retain the existing warning and immediately establish a
new blocking revision. Deleting chat/results cannot clear that state.
Ordinary private chat has an independent request-scoped gate. Recovery is a member
self-report, not a medical diagnosis, clinical clearance or permission for AI actions.

## Analysis Scheduling

The previous form/initial-revision flow did not provide a reliable central save and
rehydrate path. Defaults used revision zero in reads but the frontend sent null;
the old RPC also accepted insufficiently constrained revision/replay inputs.
The own-user preferences RPC now validates HH:MM, real PostgreSQL timezone names,
ISO weekday 1-7, explicit booleans and expected revision, including initial zero.
Reusing a request ID with different settings is rejected. A stale form reloads the
authoritative values instead of silently overwriting them.

Instellingen > AI, Tijd en datum and the analysis summary use the same RPC snapshot.
Both successful saves and refresh/login load server values. Locale display is
separate from the analysis timezone.

Daily identity is a member-local date; weekly identity is a member-local ISO week.
Existing rolling-week results remain recognized without rewriting them. The period
lookup also recognizes previous results in the newly selected timezone and retains
deleted tombstones as dedupe evidence. Preferences/period locks and result uniqueness
preserve idempotence. Post-workout identity is a completed, owned workout UUID and
never a browser timer or unfinished workout.

The service due-selector recalculates eligibility from current saved settings.
This hotfix does not activate an unattended generation dispatcher or a paid provider.
Automatic background delivery remains a separate operational gate; the existing
retention cron is not an analysis-generation scheduler. Current mock requests and
due-selection are tested, not a claim of continuously running background delivery.

## Central Settings And Consent

A shared module adds seven sections: Account, Privacy/data, Time/date, Language,
AI, Subscription and Legal. Own-member settings RPCs bind to auth.uid(), allow only
a bounded field list, and use revision conflict detection. New member_app_preferences
contains only presentation/avatar preferences; no backfill runs.

- Account reads server email and allows name/country changes. Password change
  validates the current password in an isolated nonpersistent Auth client, revokes
  that verification session, calls Auth updateUser and globally signs out on success.
  Reauthentication nonce is supported when required by Supabase. No real password
  or email-security flow was exercised during this task.
- Privacy/AI reuse own-user exports and revision-checked content deletion.
  Historical minimized safety metadata is not removed as a safety bypass.
- ai_processing, private_chat, ai_analysis and relevant trainer_summary_sharing are
  independent purposes. Separate private_chat documents exist for NL/EN/DE
  (phase6d-private-chat-v1), without copying or granting prior member consent.
  Existing members must explicitly give private-chat consent before writing again.
  General AI withdrawal does not revoke private-chat/analysis consent.
- Status/version/date and consent text live centrally; the chat footer is no longer
  a settings form. A compact settings destination remains at relevant gates.
- Account deletion is intentionally unavailable, not a fake successful action.
  Required separate gate: reauthentication, session revocation, retention/legal hold,
  audit minimization, storage/domain deletion, retries and verifiable completion.
- Subscription reads the server entitlement plan/status/dates. Unrecorded trial or
  renewal data is shown honestly. There is no payment, local premium flag or fake
  cancellation. Phase 7 owns plan changes, cancellation, monthly/annual choices,
  invoices, billing details and verified provider/webhook state.
- General terms/privacy destinations are explicitly dated staging drafts, not
  invented legal approvals. Controlled purpose documents remain distinguishable.

The quick globe and central language selector share user_settings.language.
NL/EN/DE updates rerender immediately after server success, persist through login,
and never authorize another user's settings.

## Floating Avatar And Chat

The existing approved 256px WebP is byte-unchanged; no face generation, new avatar,
3D runtime or continuous animation was added. Its SHA-256 remains
257f31e6fe4faa7fecf5fb9874eed06d4018dc8c60958aa714e7d4b79a7517dc.
Pinned Lucide 0.468.0 gear/globe/close assets and licence are vendored.

Youri AI is removed from the bottom navigation, but #ai-coach and ?view=ai-coach
remain entry routes, including delayed session restoration after refresh.
A 60px button opens the existing private chat in a mobile sheet/desktop dialog;
it moves the same DOM surface, preserving conversation state and returning to the
previous app screen. Nested settings and chat close restore focus correctly.

Mouse, touch/pointer and arrow keys move the avatar. A short tap opens it; a drag
does not. Coordinates clamp to visual viewport, safe-area, top controls and bottom
navigation, snap left/right and persist a normalized vertical position by own RPC.
Rapid position saves are serialized and pending visual position is kept separate
from older server responses. Hide/show/reset are central settings.

The avatar hides for public auth, scanner/fullscreen and critical modal flows.
Native dialogs contain focus; controls have accessible names and 44px touch targets.
Reduced-motion is respected, and dialogs use opaque backgrounds for legibility.
No-entitlement/consent states remain server gates and cannot make a provider call.

## Migration And Security Evidence

Forward-only migration: 20260906080455_phase6d_owner_safety_settings.sql.
It was first exercised together with all 50 hotfix assertions in a rollback-only
transaction, then applied once using the official staging CLI. No already-applied
migration was edited. Two tables, bounded own-user RPCs, consent documents, safer
preference/dedupe helpers and the independent recovery gate are the changed scope.

Migration list: 28 local / 28 remote, no mismatch. Post-apply db push --dry-run
--skip-vault: upToDate=true, migrations=[], seeds=[], roles=[].
No history repair/replay/reset occurred in this hotfix. The original reconciliation
of 19 timestamp differences, three absent live registrations, duplicate old version
and missing source baseline remains resolved, with its original evidence preserved.

RLS is enabled on both new tables. Direct anon/authenticated table access is revoked.
Only bounded own-user RPCs are exposed; private recovery helpers and service
completion/due-selection are not browser APIs. Trainer and cross-member negatives
pass, and raw private chat/analysis context is not shared with trainers.

Security advisor: 0 ERROR, 27 INFO private RLS-without-policy notices, 62 WARN
authenticated SECURITY DEFINER RPC notices, 1 WARN legacy mutable search path,
1 WARN leaked-password protection disabled. These are not a claim of a warning-free
database. The new private recovery table intentionally has no public policy. The
three new public settings/recovery RPCs intentionally expose checked own-user
SECURITY DEFINER entry points with fixed search paths and no anon execution.

The existing public.touch_updated_at search_path warning was not introduced here;
it requires a separate scoped hardening review. Leaked-password protection remains
an Auth release gate, not silently enabled with possible plan/cost implications.
References: [RPC exposure](https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable),
[private RLS](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy),
[search path](https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable),
[password protection](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection).

## Tests

| Evidence | Result |
| --- | --- |
| New owner SQL, before/after migration | 50/50; rollback-only synthetic members/trainer/workout |
| Live 6D schema/RLS/ACL/provider verifier | 13/13 |
| Live 6C transactional and request-safety regressions | overall_pass=true; fixtures_remaining=0 |
| Live 6D0 authorization E2E | 48/48 |
| Existing 6D transactional E2E | exit 0, rollback; CLI only displays first result set |
| New full assembled owner browser | 196/196, 320x700, 390x844, 820x1180, 1440x900 |
| Existing 6D / 6D0 / 6C browsers | 48/48, 41/41, 85/85 |
| Public-auth assembled browser | 88/88, no real email |
| Phase 5 / 6A / 6B / 6C / 6D static | 116/116, 93/93, 98/98, 117/117, 17/17 |
| Public-auth static / assembled syntax | 26/26 |
| Combined 6C + 6D Node handler tests | 27/27 |
| Live public UI | Four viewports; zero console/page errors or mutating requests |
| Live Edge unauthenticated routes | Chat and analysis both HTTP 401 |
| Live assets | 13/13 HTTP 200 and byte-identical to runtime commit |

Browser integration uses the real assembled application with synthetic RPC/Auth/Edge
responses, not a real authenticated member session. SQL tests exercise real staging
functions and permissions using rollback fixtures. Password tests verify the frontend
sequence with a mock Auth service; actual password changes remain an optional owner
retest. Live public-page tests never submit registration/reset/resend forms.
Screenshots were visually inspected at mobile/desktop; authenticated devices still
require owner acceptance.

Owner checklist coverage:
- 1-10: SQL recovery/audit/new-risk/deletion checks, phrase handler cases and browser recovery flow.
- 11-17: SQL timezone/revision/dedupe/new-session checks and browser shared-source persistence.
- 18-28: seven settings views, independent grants, logout, server plan, drafts and NL/EN/DE tests.
- 29-42: browser navigation, pointer/touch/keyboard, bounds, reset/hide, focus, history,
  composer, scanner and deep-link checks; database/handler entitlement/consent negatives.
- 43-48: SQL ACL/isolation/trainer/no-domain-write/zero-cost and rollback fixture checks.
- 49-50: the listed selected frozen regressions, four viewports, console and overflow checks.
This maps automated evidence, not a declaration that all historic manual frozen tests
or a real-phone owner test were rerun.

Old test fixtures were updated only to use the new explicit private_chat consent
document and expected initial preference revision. No negative security assertions
were removed. Phase 5/6A/6B static paths now use reconciled canonical migration names.
A fresh Windows checkout exposed a CRLF-sensitive Phase 6B text assertion; its text
reader now normalizes CRLF, without changing schema/runtime or byte-hash assertions.

Fresh checkout: isolated clone under supabase/.temp/fresh6d, main at the runtime
commit, initially clean. Git core.longpaths=true is local to that disposable clone;
a first longer-path clone failed Windows MAX_PATH and was retained, not deleted.
Fresh syntax/static verification passes 116/93/98/117/17/26 checks, and the full
assembled owner browser passes 196/196 from that clone. The CRLF correction is
verified after a fast-forward to f6e5b0ba3202742b72c7a72c09b64564a7d25945.

Full local database replay and CLI schema diff remain environment-limited:
Docker Desktop is unavailable and the earlier local PostgreSQL rebuild lacks
pg_cron after Phase 6B. No destructive cleanup, stub extension, replay on staging
or false full-schema-equivalence claim was used to hide this limitation.
Live schema/ACL checks and rollback integration tests pass, but an extension-complete
local rebuild/diff is still a separate verification step.

## Deployment, Commits And Data Impact

Runtime commit: a9f14d9306eee17bd44033132a3d95e20e447428.
Verification commit: f6e5b0ba3202742b72c7a72c09b64564a7d25945 (expanded live assets
and CRLF-portable Windows static check). Documentation is committed separately;
the final repository HEAD identifies that receipt without changing runtime bytes.
See PACKAGE6D_COMBINED_OWNER_HOTFIX_EVIDENCE.json for hashes and named browser checks.
Frontend: https://yourizorge.github.io/fitmetzorge-staging/
Cache: 20260906-owner-hotfix1. Live asset hashes are in the JSON evidence receipt.

Staging youri-ai: version 43, ACTIVE, verify_jwt=true.
Bundle SHA-256: 627c883a9b001e6215d101c827f96fbb94825c7f1437077088ec09fbba7460c6.
Only this Edge Function was deployed. Docker was not running; the CLI successfully
used remote bundling. No provider request was made by deployment or tests.

Before/after content fingerprints AND row counts match for all 21 allowlisted
member/safety/domain tables. This is a precise checked scope, not a fingerprint of
every managed/Auth/catalog table. Auth/profile fixture counts are zero afterward;
new member_app_preferences and analysis_safety_recoveries contain zero rows before
owner use. Existing consents and blocked safety state were not silently changed.
Only schema, controlled consent documents, migration metadata and deployed code changed.

No real memberdata went to OpenAI; external calls/cost for this hotfix: 0 / EUR 0.00.
No payment, provider activation, trainer link, manual Auth confirmation or production
operation occurred. The original public-auth hotfix remains successful.

## Remaining Gates And Exact Owner Retest

No additional owner approval is needed to publish this mock-only hotfix. Remaining
acceptance gates are the real-phone UX/recovery test, optional real password/nonce
flow test, extension-complete local rebuild/diff, separate account-deletion contract,
Phase 7 billing and legal/member-provider activation. No production GO is implied.

1. Open staging, refresh and sign in with an existing confirmed test account.
   No new confirmation email is needed. Use an account with a valid AI/trial/PT
   entitlement for chat; a Free account must show an honest access explanation.
2. Open the gear, then AI. Check and explicitly grant the new private-chat consent
   and analysis consent only if desired. Existing general consent is not copied.
3. Open the floating avatar, then Analyses. With the existing old safety block,
   choose Controleer mijn status. Confirm only statements that are actually true;
   do not clear a real current symptom to complete a software test.
4. On an appropriate synthetic scenario, verify all three confirmations are required.
   After confirmation, refresh: recovery persists, ordinary chat works and mock
   analyses are available when entitlement/consent/data requirements are met.
5. In a test conversation, a new serious-symptom example must immediately stop
   analyses again. Contradictory/bypass text must not clear it. An explicit recovery
   phrase may open the checklist but must never clear it automatically.
6. Set a distinctive daily time, weekday, weekly time and timezone in AI. Save,
   compare Tijd en datum and the analysis summary, refresh, sign out/in and compare.
7. Switch NL, EN and DE with the globe and central menu. Check the same selected
   language after refresh/login.
8. Drag by finger/mouse to both edges, navigate, refresh and check position. A drag
   must not open chat. Test hide/show/reset in AI and arrow-key movement on desktop.
9. Open chat from Training or another normal page, switch conversations, type a
   draft, open/close nested settings, then close chat: the previous page and draft
   must be retained. Test a #ai-coach refresh.
10. Inspect Account, Privacy/data, Subscription and Legal. Export/delete only
    intentionally created test content. Withdrawing one purpose must not revoke
    the others or disable the ordinary app.
11. Verify login/reset/confirmation and scanner controls are not obstructed.
    Optional: test password change on an expendable account; verify old-password
    rejection and sign-in requirement afterward.
12. Report device/browser, expected/actual behavior and screenshot for any failure.
    Explicit owner approval is still required before Package 6D can be frozen.
