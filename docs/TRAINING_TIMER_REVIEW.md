# Training Timer And Effort Follow-Up

## Scope

Owner GO: round rest timer, visible RIR/RPE/None and the existing offline 6E-1
product review. The owner accepts the basic exercise selection, compact set rows
and other previously delivered Training operation. This is not AI acceptance.
Initial Git root: supabase/.temp/phase4fb-staging-deploy, staging main.
Initial clean local/cached/direct remote HEAD: dd3b4e8af6974e6f6bbf8e9ba8c1e2e53720aac8.
AGENTS and project config read; on-request, auto_review, workspace-write,
project network setting and exact staging autonomy retained. Managed permissions
remain authoritative. No settings/permissions/workflow changes or cleanup.

## Changes

Only four runtime files: app.js and index.html (scoped cache references),
assets/phase3-training-engine.js and assets/training-workout.css.
Cache: 20260909-training-timer1. Model, basic catalog UI and Settings source intact.
Runtime/test commit: 802c3b141ec9293820c69fe229c618b73965abb7.

Manual Start opens a full-screen circular minutes:seconds display, with a shrinking
ring and pause/resume, +15 and Stop controls. The header back arrow minimizes;
Rusttimer reopens the same countdown. Escape minimizes; keyboard focus stays in
the large timer. Light/dark reuse the application's existing theme variables.

This is one stored rest object and the existing single interval, not a second timer.
Absolute endsAt is authoritative while running; remainingMs is authoritative while
paused. Adding 15 seconds also extends the ring denominator by 15 seconds, so it
shows remaining fraction of the total allotted rest. View preference lives on the
same rest object. Refresh and background-return reconciliation use existing logic.
Manual stop/expiry never register sets, advance an exercise or finish a workout.
Stop ends this countdown but leaves that workout's timer opt-in intact; Uitschakelen
in the compact panel disables rest for that workout. New workouts still start off.
Existing successful-set automatic rest remains compact to avoid interrupting set
entry. Its established superset/next-step behavior remains unchanged.
No closed-app notification, OS background execution or cross-device timer guarantee.

The three-way radio selector immediately above the set table shares the existing
Training preference setter and revision-controlled RPC with Settings -> Training.
One optional column is visible. Blank is missing; explicit zero remains zero.
Switching never converts/swaps/deletes RIR/RPE, including hidden unsaved drafts.
NL/EN/DE descriptions distinguish reps remaining from perceived effort 1-10.
An in-flight change disables the selector without replacing the clicked element.
Failure keeps the old choice and shows the save error before stale workout feedback.
The established single-row mobile grid and 44px set controls are unchanged.

## Verification

See TRAINING_TIMER_REVIEW_EVIDENCE.json and TRAINING_TIMER_REVIEW_PUBLICATION.md
for final results, exact source/publication commits and raw-byte identities.
Initial new state tests: 1 PASS / 3 FAIL (new presentation API absent).
After implementation: 33 focused unit/preservation/theme assertions and six
historical completion regressions PASS. Existing 36 offline recognition regressions
and five executable AI scenarios rerun; no medical validation inferred.
Definitive local browser matrix: 1084/1084 PASS, 110 geometry probes and
95 unique screenshots. Includes an additional 844x390 landscape timer check.
Published-assets matrix: the same 1084/1084 checks PASS, with the same 110
geometry probes and 95 screenshots. Raw publication identities are verified.

Browser tests use real app JS/CSS and actual controls with an intercepted synthetic
backend. No live member call is permitted. Matrix: 320x700, 360x780, 390x844,
1440x900; NL/EN/DE, light/dark/system, metric/imperial, failed writes/retries,
single completion, preserved basics, compact rows, values and timer persistence.
New timer tests observe real elapsed countdown/ring decrease, pause, +15, stop,
expiry, minimize/reopen, keyboard focus and refresh of the large paused display.
New effort tests click the visible segments, retain RIR 0 / RPE 9.5, simulate
save failure and cross-check the real Settings controls.

Physical iPhone/Android, native keyboard, mobile browser chrome and OS suspension
are NOT tested. Phone dimensions/touch and keyboard space are emulated in Edge.
Prior test artifacts and limitation records are retained unmodified.
A test fixture initially compared a deadline recorded before its own pause/+15;
the expectation was moved after those intentional operations. A radio check helper
retried a reverted failed save; the test now uses a single actual label click.

## AI Review Boundary

Read current BUILD_STATUS, MASTER_BUILD_PLAN, ARCHITECTURE, TEST_MATRIX,
PHASE6E1_OWNER_OVERVIEW, PHASE6E1_CONTRACTS and the recognition follow-up report.
The three old misses were fixed by cf6c212, with 36 preregistered regression cases;
they are not current misses. No AI classifier or other offline source is changed.

The current owner-review supplement is in PHASE6E1_OWNER_OVERVIEW.md.
6E-0 remains accepted/frozen OFFLINE ONLY. 6E-1 is technically ready, not
owner-accepted or live. Phase 6E remains incomplete. D1-D12 unchanged.
No live integration, paid AI call, external member processing or reviewer contact.
No database, migration, Edge, member, entitlement, provider or production operation.
Member preservation evidence is source isolation and zero live member calls here,
not a newly claimed live database fingerprint. No file deletion.

## Short Phone Retest

1. Refresh staging; start a workout. Without Rusttimer opt-in, no timer appears.
2. Rusttimer -> duration -> Start. Check the large ring, pause/resume and +15.
3. Minimize, type a set value and reopen; refresh once while paused.
4. Stop or let it expire: no set should register and the workout remains active.
5. Above sets: RIR 0 -> RPE 9.5 -> Geen -> back; check both values and Settings.
6. Check the same row with your actual keyboard, light/dark, then train normally.
