# Training Corrections And Next Offline AI Review

Status: TECHNICAL PASS / PENDING OWNER RETEST. Staging only.
This replaces the earlier large-timer and mutually exclusive effort-display specification.
The basic exercise catalog and other accepted Training behavior remain in place.
AI 6E-2 stays TECHNICAL PASS / READY FOR OWNER REVIEW, NOT accepted/frozen/live.

## Preflight And Exact Scope

Repository root: supabase/.temp/phase4fb-staging-deploy under the owner-provided
fitmetzorge-staging-main directory. Initial main was clean; local and direct
origin/main both 037a338a84a6144a149d44238cd936630cfbe503.
AGENTS.md and .codex/config.toml read. Existing on-request/auto_review,
workspace-write and exact staging autonomy retained; managed permissions take
precedence. No permission, provider, entitlement or workflow edits.

Runtime/test/migration commit: 4edc8054202b15c7bd1e884982a94a7346991ed1.
Only six Training-authorized runtime paths change:
app.js, index.html, assets/phase3-training-engine.js,
assets/training-workout-model.js, assets/training-workout-ui.js,
assets/training-workout.css. Cache version: 20260909-training-correction2.
All 54 other runtime assets retain the immediate baseline's byte identities.
All 57 offline AI files, including 23 frozen 6E-0 and 22 frozen 6E-1 sources,
are unchanged. Earlier migrations, Edge and access-control source files remain intact.

## Timer Diagnosis And Correction

The prior published 390x844 rendering was measured, not merely checked for visibility:
circle 340x340, x=25, y=248; center offset x=0, y=-4.
The owner's small top-left phone rendering was NOT reproduced with matching assets.
Its exact device/cache cause cannot honestly be declared proven without that phone.

Disabling the Training stylesheet in the same historical app produces no round dial:
the dial container becomes 360x19.59375 and its time is small/left aligned.
This demonstrates sensitivity to missing/stale Training styling, not proof of the
owner's exact cache state. The old loader did not enforce the stylesheet version.
No service-worker controller was observed in the isolated browser fixture.

The loader now awaits the matching versioned Training stylesheet even with stale HTML;
a stylesheet failure is explicit instead of silently opening unstyled Training.
The dialog and its center use explicit viewport geometry, with vh/dvh fallbacks.
At 390x844 the measured published result is x=45, y=272, width=height=300, zero center offset.
Landscape 844x390 uses a 200px circle; 390x650 remains 300px and centered.
Header/footer controls remain separate from the centered circle.

Every opted-in new rest interval opens large. Only explicit minimize/Escape makes
that interval compact; reopening retains the same deadline. No second interval is
created. Pause, +15, serialized refresh and wall-clock continuation are preserved.
No opt-in means no timer. Start/stop/expiry create no sets or workout completion.

## Independent Effort Choices And Snapshots

New workout plans explicitly start with rir=false and rpe=false. Two independent
maker/editor checkboxes allow all four combinations. The global execution selector
is removed; Settings displays the per-plan scope, with no conflicting global editor.
The old preference API remains backward compatible but cannot override plan/session flags.

The main set row contains number, previous performance, weight, reps and save/check.
Only selected effort fields appear below that SAME set; both sit side by side.
Inputs are individually labelled, at least 44px high, and do not scroll horizontally.
Zero RIR stays zero; blank stays missing. Hiding inputs never converts, swaps or
deletes saved targets/scores. Existing targets and actual scores are distinct.

Existing unconfigured plans/sessions derive initial visibility only from actual
stored target/score presence, including zero. No general preference is imported.
Explicit false remains false even with retained old scores. The choice is copied
into the active session and both server/local completed-history metadata.
Editing a plan changes future sessions, never the choices of an existing session.

## Additive Staging Migration And Data

20260909215122_training_plan_effort_tracking.sql adds ONE SECURITY INVOKER RPC:
fmz_training_save_workout_v2. It wraps the existing atomic save under the same
own-user RLS, transaction lock, optimistic version, idempotency and Free-day limits.
It stores effort_tracking in existing training_plans.metadata, preserving other keys.
Different flags with the same save ID are rejected. No table changes/backfill,
old-function replacement, score rewrite or history repair/replay/reset.

CLI 2.115.0 generated the filename. Its existing-directory creation error required
a new ignored authoring directory inside this repo, not renaming/deleting migrations.
The pinned CLI and all local artifacts were retained; no filesystem cleanup occurred.
Migration list: 33/33 aligned. Post-apply db push --dry-run --skip-vault:
upToDate=true, migrations=[], seeds=[], roles=[].
The live wrapper body matches Git after newline normalization; invoker/search_path
and anonymous denial are checked. REST returns 401/42501 for unauthenticated execution.

43 new rollback SQL assertions PASS before AND after apply; 34 original rollback
Training assertions PASS after apply. Synthetic accounts/rows are rolled back.
67 table fingerprints and 100332 rows unchanged before/after: public, ai_private,
legacy_auth_private and auth.users. No real member field was printed or used in tests.
No Edge deployment, live AI activation, provider call, external member processing,
production/appfmz/other website action, cost or deletion.

Security advisors have identical pre/post entity sets: 28 informational deny-by-default
tables, 68 existing signed-in definer-function warnings, one existing mutable-search-path
warning and one existing leaked-password-protection warning. No new finding for this
invoker wrapper. This is NOT a globally clean-security claim and does not authorize
unrelated hardening. Existing references:
[function search path](https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable),
[definer functions](https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable),
[password protection](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection).

## Test Evidence And Limits

- 720 local browser assertions, 40 screenshots: 320, 390 and 1440px; all four choices
  through create/edit/execute/save/reload/actual logout and login form controls.
  The backend AND authentication are synthetic. No claim of real-account E2E login.
- New browser contexts with empty storage rehydrate server snapshots and both scores.
  Later plan edits preserve active/history choices; future sessions use new choices.
  Failed set writes, retry, null/zero, themes, tap targets and main/subrow geometry checked.
- Timer checks include real countdown/ring movement, pause/+15, minimize/reopen,
  refresh, elapsed wall-clock time, short real expiry, landscape and shortened viewport.
  visibilitychange is simulated; this is NOT proof of OS background suspension.
- 570 focused unit/frozen-AI regressions PASS, zero skipped/failed; six original
  completion assertions PASS using an updated fixture with the actual snapshot helper.
- The old blanket task-scope tests predate these authorized Training/AI changes.
  They remain historical, not counted as passing; new exact six-file/migration scope
  and frozen-source byte gates replace them for this task.
- The prior SQL assembler initially collapsed dollar quotes; corrected by literal
  replacement. A fixture initially violated one-open-session uniqueness; it now
  completes each synthetic session. No production logic was weakened to fix tests.
- No full local Supabase rebuild/global schema-diff claim. Existing Docker/pg_cron
  and retained OneDrive-file limitations remain outside this small additive change.
- Published matrix: another 720/720 PASS, 40 screenshots. All 60 runtime assets match
  committed bytes, 54 retain the previous baseline; all 80 offline/test paths HTTP404.
  These records accompany the successful Pages run; physical iOS/Android, OS keyboard, browser
  bars/cache and OS background behavior still require owner phone retest.

See [machine-readable evidence](TRAINING_CORRECTIONS_EVIDENCE.json).
Current repeatable commands: node _tests/training/correction-verify.cjs;
node _tests/training/completion-regression.cjs; with bundled Playwright on NODE_PATH,
node _tests/training/correction-browser.cjs local or live;
node _tests/training/correction-publication.cjs final.
The current scoped matrix supersedes earlier mutually exclusive effort/compact-rest
browser expectations without rewriting their historical result records.
Runtime Pages run: [34446358436](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/34446358436).
Docs-only follow-up publication must retain these exact runtime blobs.

## Phone Retest And AI Boundary

1. Refresh staging. Open Rusttimer, select a duration and Start: large centered ring.
2. Pause, +15, resume, minimize and reopen; refresh and background/return on the phone.
3. Create/edit plans with neither, RIR only, RPE only and both; inspect fields BELOW sets.
4. Save RIR 0 and a separate RPE value; log out/in and verify both.
5. Edit the plan during an existing session: existing snapshot stays; new session changes.

Training remains PENDING OWNER RETEST. These emulator checks are not physical acceptance.
N1-N3 remain open in [the unchanged 6E-2 concepts](PHASE6E2_OWNER_OVERVIEW.md).
The single next proposal is [6E-3 goal/plan-bound workout reflection](PHASE6E3_PROPOSAL.md):
explicit source identities, existing goals and exact session/set comparisons first.
Nutrition targets/recovery records exist but their approved coaching adapters and
expert content/resumption criteria do not. Trainer links are not invented trainer limits.
6E-0/6E-1 accepted/frozen, D1-D12/O1-O5 preserved, Phase 6E incomplete. No next AI start.
