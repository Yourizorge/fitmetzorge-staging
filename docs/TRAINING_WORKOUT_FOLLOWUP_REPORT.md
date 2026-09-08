# Training Upgrade And Offline 6E-1 Follow-Up

## Status And Scope

2026-09-08. Explicit owner GO for a narrow offline AI correction and an actual
Training staging upgrade. Technical delivery; NO owner acceptance or new freeze.
6E-0 remains COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE PREPARATION ONLY.
6E-1 remains not owner-accepted/frozen; Phase 6E remains INCOMPLETE.

Only repository: Yourizorge/fitmetzorge-staging, main, in the specified
supabase/.temp/phase4fb-staging-deploy Git root. Initial local/direct remote HEAD:
1af2e04fc4418876e5591dd45cf522fb23667daf, initially clean.
AGENTS/config read; on-request + auto_review + workspace-write, scoped staging
autonomy. Managed boundaries observed through reviewed elevated commands.
No approval, workflow, provider, entitlement or production configuration change.

Initial Training implementation: 931138bf783fb3f0cb4ac1ff0ed932ff2d8395ca.
Final Training runtime source commit: ed1f485af87d68ad7ec6cbee55ba9fda074af9ce.
Cache: 20260908-training-workout2.
Historical application baseline bc6308fbf0f914b04c7faa711219d9ae46e9cbe3 remains
the preservation reference OUTSIDE the exact seven authorized Training files.
Pages deployed successfully; [publication receipt](TRAINING_WORKOUT_PUBLICATION.md)
and [machine-readable evidence](TRAINING_WORKOUT_EVIDENCE.json).
Live matrix 248/248 PASS; 59/59 published assets match Git, 52 unchanged from
bc6308f, 53 offline/test paths HTTP404 on Pages. Git access settings unchanged.
Staging: https://yourizorge.github.io/fitmetzorge-staging/

## A. Narrow Offline Correction

Preregistration: 0e8e77a420c97f97f47d631b68b5cfd29f4897f4.
Correction: cf6c212600b6798a2a2d0a057b9deacc233112bc.
36 expectations committed before changing context.cjs; original logic 7 PASS,
29 FAIL. Cases cover exact originals, paraphrases, negation, historical,
educational/quoted context, reassuring/denied other clauses, normal training,
nonsense and simulated technical failure. These are synthetic, not clinical cases.

| Original / fixture reference | Cause / previous result | New result |
| --- | --- | --- |
| Mijn borst brandt van binnen | Missing inner-chest-burning phrasing; unclear/clarification | health_report / current_unclassified / level null |
| My left arm has gone numb | Missing arm-numbness wording; unclear/clarification | health_report / current_unclassified / level null |
| Mir schnurt es die Kehle zu (original retains umlaut in fixture) | Missing German throat-tightness idiom; unclear/clarification | health_report / current_unclassified / level null |

The exact Unicode German original is preserved in the preregistered JSON.
Three narrowly scoped context patterns reuse existing clause context/negation
handling. Their trace IDs are context.followup.inner_chest_burning.v1,
context.followup.arm_numbness.v1 and context.followup.throat_tightness.v1.
Unmapped sensation context stays uncertain; explicit normal chest-muscle training
counterexamples are not alarms. No medical level or frozen warning text changed.
Tests exercise text -> context -> feedback, without expected context as input.

The current-unclassified path selects the existing stop/help concept wording.
Historical, quoted, educational and denied signals stay separately scoped.
All 36 new tests now PASS. Historical three limitation observations in the
original PHASE6E1_EVIDENCE.json are retained, not counted as current successes.
This correction supersedes only those three old observations, not all limitations.

D1-D12, access/facts/advice/actions separation, no human approval service,
no automatic trainer disclosure, self-report without medical clearance and
bounded clarification/retry remain unchanged. Content, serious/recurrent/
unclassified recovery, retention and expert reviews remain OPEN.
No live AI import, AI call, new AI authority, reviewer contact or medical validation.

## B. Implemented Training

Seven authorized runtime paths:
- app.js: ordered model/UI loading before existing phase3 engine; scoped cache updates.
- index.html: Training stylesheet and loader cache only.
- assets/phase3-training-engine.js: existing normalized plans/sessions/setlogs adapted.
- assets/phase6d-owner-settings.js: member Training preference section only.
- assets/training-workout-model.js: pure target/group/sequence/identity/unit helpers.
- assets/training-workout-ui.js: fullscreen maker using existing catalog and save adapter.
- assets/training-workout.css: scoped real-app theme/responsive styles.

No second training domain in legacy workspace-state. Existing IDs, ownership,
Free limit, immutable session snapshots, history and Progress calculations retained.

Maker: 898 existing canonical catalog identities, search, muscle/material filters,
multi-selection, details with retained search/scroll, set targets and notes,
exercise replacement with new planned ID, removal, accessible reorder plus real
desktop mouse dragging, contiguous supersets and group rest, existing-plan editing.
Atomic save uses optimistic updated_at and payload-bound request identity.
Failed save keeps a visible draft/error; explicit cancellation never partially saves.
Own fallback is the FitMetZorge logo, not an unlicensed or guessed exercise photo.

Execution: one exercise, complete visible/correctable set list, unsaved input cache,
exact exercise-ID previous results, group round sequence, notes/instructions,
overview and manual navigation that does not register sets.
Failed set save does not start rest. Correction reuses the same set identity.
A final additional fixture forced initial session creation to fail and enforced
the set-log foreign key. The earlier route could not recover on set retry.
Commit ed1f485 makes set retry save/retry the parent session before flushing sets,
and shows the unsaved session status. The full matrix now passes 248 checks.
Completion flushes sets first and retries idempotently; refresh after lost completion
response cannot lock the UI, duplicate history or silently permit a new session.
A pending completion is retried before new set edits. No duplicate completion event
in the synthetic lost-response path; existing downstream analysis code is unchanged.

Timer: persistent on/off, per-exercise/group seconds, pause/resume/+15/skip.
Deadline survives refresh/background return. No closed-app notification promise.
Settings -> Training: RIR default, RPE or None; one optional field visible.
Blank remains missing, explicit RIR 0 remains 0; historical RIR/RPE are never
converted or erased when the display preference changes.
phase3OverloadSignal no longer treats blank/null RPE/RIR as load-increase room.
Metric/imperial input converts to existing kg storage; historical summaries use
the display unit. No new AI training authority.

## Migration And Data Proof

Migration/commit: 20260908100106_training_workout_editor.sql /
a27b61a761503ba0a3350bbabe45352ef2f0d7ec.
Version was generated by Supabase CLI; canonical identity is identical in Git/live.
Only target mokxyyullfhkfalopbzd. CLI dry-run showed exactly one new migration;
application succeeded without seeds, roles, vault changes, replay or history repair.
Afterwards: migration list 32/32 aligned; dry-run upToDate=true, no pending migration.
All five live function bodies and fixed search paths match the source exactly.

Nullable additions only, no backfill:
training_plan_exercises.set_targets, superset_id, superset_rest_seconds;
member_app_preferences.training_effort_mode, training_timer_enabled.
Existing session/set columns and existing functions/RLS/ACL are not rewritten.
Atomic save and completion are SECURITY INVOKER using existing own-user RLS.
The two own-preference functions intentionally use SECURITY DEFINER because the
existing preference table is private-write; fixed auth.uid/client check, safe
search_path, shared preference revision lock, no anonymous execute/table-write grant.

Security advisor delta: only two expected authenticated-definer notices for those
preference RPCs (66 -> 68). Reviewed intent and authorization are tested.
Existing 28 RLS-no-policy INFO notices, touch_updated_at search-path WARN and
disabled leaked-password protection WARN remain unchanged, outside this package.
Reference: https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable

Before/after hashes: 67 tables selected from public, ai_private,
legacy_auth_private and auth.users; 100276 rows in total.
Counts and content hashes unchanged after excluding ONLY the five new nullable
columns from row comparisons. No existing member/config/provider rows changed.
Two synthetic accounts and all associated fixtures were inside BEGIN/ROLLBACK;
zero synthetic accounts remain. Browser fixtures never call live Supabase.

Local rebuild retained all files: 22 canonical migrations before the existing
pg_cron platform boundary, followed by exact accepted member-preference DDL and
this Training migration. 34/34 tests passed locally and 34/34 on actual staging
with rollback. This is not claimed as a complete local Supabase platform rebuild.
Retained local cluster: C:\Users\Fitme\AppData\Local\Temp\fmz-local-rebuild-hZGlcc.
Cluster stopped. No OneDrive/PostgreSQL/source/Git cleanup or file removal.

## Tests And Limits

| Check | Result | Boundary |
| --- | --- | --- |
| Narrow follow-up | 36/36 PASS | Technical synthetic recognition, not medical reliability |
| Current 6E-1 suite | 280/280 executed PASS | Two historical blanket runtime-freeze tests explicitly excluded; not counted PASS |
| Frozen 6E-0 selected regressions | 90/90 PASS | Original files unchanged |
| Training model + preservation + theme authority | 22/22 PASS | 6 model, 6 current preservation, 10 unchanged theme assertions |
| Historical completion regression | 6/6 PASS | Original assertions unchanged; adapter adds only new mutex fixture values |
| Browser matrix | 248/248 PASS | 320x700, 390x844, 820x1180, 1440x900; 28 geometry probes; 24 screenshots |
| Published-asset browser matrix | 248/248 PASS | Same real published JS/CSS, synthetic backend; exact paused-timer +15-second delta |
| SQL local / staging | 34/34 each PASS | Synthetic transaction rollback, own/cross-user, validation, Free, snapshots, retries |
| Existing data | 67/67 table hashes equal | 100276 rows; no raw member fields exported |
| Source identity | 5/5 functions identical | Exact canonical migration version/name |

Historical _offline/phase6e1/test/isolation.test.cjs is untouched. The two excluded
I01 tests require the ENTIRE app/schema to equal bc6308f, contrary to this new
explicit Training GO. Current preservation checks restrict the complete diff to
exact Training paths, new migration, test support, docs and the narrow AI patch;
remaining security, D1-D12, 23-source freeze and offline-import assertions still run.
Git text identity accounts for pre-existing CRLF checkout conversion; publication
must compare raw served bytes against committed Git blobs, without normalization.

Browser tests use actual app CSS and JS, existing mock integration hooks and the
read-only 898-row catalog snapshot. No protective CSS or real member mutation.
Desktop uses actual mouse dragging; mobile/tablet cover buttons and drag-event
wiring. Device/browser emulation is not a physical iPhone/Android test.
Theme modes, NL/EN/DE, metric/imperial, retries, refresh/relogin, supersets,
timer, history and dashboard navigation are exercised.
Screenshots checked visually on mobile. No broad provider/application suite claimed.

## Owner Retest (Maximum Eight Steps)

1. Open staging on your phone and refresh; choose Training -> Workout maken.
2. Search/filter, select multiple exercises, open details and return; verify selection.
3. Add sets/notes, replace/reorder, link a superset, set group rest and save.
4. Reopen the same workout, change a target, save and refresh/relogin.
5. Start it; enter weight/reps, leave effort blank or enter RIR 0; register a set.
6. Follow superset rounds; pause/resume/+15/skip rest, then turn timer off and refresh.
7. Settings -> Training: RIR/RPE/None; test light/dark/system and your units/language.
8. Finish once, inspect history/Progress/dashboard; verify previous exact-exercise sets.

No automatic owner acceptance/freeze. Next step is owner phone/product review of
the deployed Training UX and offline 6E-1 concepts, not an automatic new package.
Exact open boundaries: clinical content/recovery/retention reviews; recognizer
coverage beyond this preregistered set; actual-device acceptance; no closed-app
timer notification; neutral fallback where licensed exercise media is absent.
Previous performance retains the existing 25-session hydration window; repeated
same-exercise occurrences use one deterministic occurrence, not combined records.
Production touched: NO. No external AI calls, emails, costs or Edge deployment.
