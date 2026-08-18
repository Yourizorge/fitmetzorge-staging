# FitMetZorge Test Matrix

Status: MASTER PLAN COVERAGE MATRIX
Last updated: 2026-08-18

This matrix records the required functional, security, entitlement, AI, migration, and release checks for the Master Build. No implementation tests are executed by this document.

## Test Status Values

- `PLANNED`: Required by the Master Build plan, not implemented yet.
- `READY TO DESIGN`: Can be specified in detail when the phase starts.
- `BLOCKING GATE`: Must pass before the phase/release can be accepted.
- `REGRESSION`: Existing staging functionality that must keep working until an accepted replacement exists.
- `MANUAL VERIFICATION REQUIRED`: Local implementation or migration preparation exists, but live staging/browser/Supabase verification has not been completed.
- `PASS`: Required live staging/manual/static verification has passed.

## Phase Gate Matrix

| Phase | Area | Required Coverage | Gate Type | Status |
| --- | --- | --- | --- | --- |
| Phase 0 | Governance | Baseline audit, Phase 0A docs, Phase 0B staging infra verification | BLOCKING GATE | COMPLETE |
| Phase 1 | Accounts | Signup, login, logout, session persistence, password reset, invite acceptance regression | BLOCKING GATE | PASS |
| Phase 1 | Onboarding | Required Free profile fields, BMI calculation, goal inputs, realistic goal constraints | BLOCKING GATE | PASS |
| Phase 1 | Language foundation | NL/EN/DE translation-key structure, no hardcoded mixed UI on primary client/Lid surfaces | BLOCKING GATE | PASS |
| Phase 1 | Legacy bridge | Existing trainer/client Auth and profile/workspace relationships preserved | BLOCKING GATE | PASS |
| Phase 1 | Entitlement foundation | Minimal single source of truth for Free/Pro/AI/PT access decisions; no payments yet | BLOCKING GATE | PASS |
| Phase 2 | Vandaag | Daily hub shows relevant actions without clutter | BLOCKING GATE | PASS |
| Phase 2 | Recovery | Manual sleep, steps, wellbeing, recovery feeling, training-load placeholders | BLOCKING GATE | PASS |
| Phase 2 | Health entitlement | Free has no auto Health sync; Pro/AI Health-sync entry points are controlled | BLOCKING GATE | PASS |
| Phase 3 | Training | Plan/template creation, workout start, pause/resume, set logging, timer, completion | BLOCKING GATE | PASS - OWNER REAL-PHONE ACCEPTED; FUNCTIONALLY FROZEN |
| Phase 3 | Training history | Previous performance, history, PRs, progressive overload signals | BLOCKING GATE | PASS - OWNER ACCEPTED |
| Phase 3 | UUID persistence | Plan/day/exercise/session/set-log DB IDs are valid UUIDs; no prefixed IDs enter uuid columns | BLOCKING GATE | PASS - UUID BLOCKER RESOLVED AND OWNER ACCEPTED |
| Phase 3 | Exercise Engine | UUIDv5 canonical ids/slugs, 898 real pinned Kinetic records now and quality-only growth toward circa 1,500, no synthetic padding, final NL-name policy, honest instruction/DE coverage, taxonomy, provenance/license, legacy mapping | BLOCKING GATE | FUNCTIONAL PASS; DUTCH/GERMAN EDITORIAL CONTENT REMAINS A SEPARATE GATE |
| Phase 3 | Exercise picker | Desktop modal/mobile bottom-sheet, search, muscle/equipment filters, batched results, no 1,500 permanent DOM cards | BLOCKING GATE | PASS - OWNER ACCEPTED |
| Phase 3 | Animation architecture | Active workout preview slot and placeholder/legacy/Youri-avatar-ready media model without changing exercise identity | BLOCKING GATE | FUNCTIONAL PLACEHOLDER PASS; YOURI-AVATAR MEDIA REMAINS A SEPARATE GATE |
| Phase 3 | Offline safety | Active workout survives poor connection where technically responsible | BLOCKING GATE | PASS FOR ACCEPTED PHASE 3 FUNCTIONAL SCOPE |
| Phase 3 | Training sharing | Personal training schemas cannot be publicly shared | BLOCKING GATE | PASS - OWN-USER RLS AND NO BROAD TRAINER/PUBLIC ACCESS |
| Pre-Phase 4 | Member Vandaag consistency | One combined hero, exactly one Daily Check-in CTA, Training active-session/fallback entry, conditional onboarding; no standalone Tracker cards or Analyse implementation | BLOCKING GATE | PASS - OWNER/RUNTIME VERIFIED; FROZEN |
| Pre-Phase 4 | Member Tracker consistency | Compact overview, focused body-level details, shared Water/day values, mobile Recovery history, no wide default table | BLOCKING GATE | PASS - OWNER/RUNTIME VERIFIED; FROZEN |
| Pre-Phase 4 | Rendering and regression | Active-view boundaries, no Nutrition render on Tracker day change, no polling/observer/reload, Phase 1-3 preserved | BLOCKING GATE | PASS - OWNER/RUNTIME VERIFIED; FROZEN |
| Phase 4 | Architecture/readiness | Legacy inventory, normalized model, entitlement/RLS boundaries, food sources, retry, performance, slices, decisions, and test design | BLOCKING GATE | PASS - OWNER CONTRACT LOCKED; SLICE 1 MIGRATION CREATED / LOCAL REVIEW PASS / NOT EXECUTED |
| Phase 4 | Schema Slice 1 local security | Exact six-table scope, constraints/FKs/indexes, own-user RLS, exact ACLs, RPC authority, Free 10-custom limit, seven-day history, snapshots, retry identity | BLOCKING GATE | PASS LOCALLY - MIGRATION AND READ-ONLY CHECKER REVIEW-READY; LIVE VERIFICATION PENDING |
| Phase 4 | Nutrition | Day totals, meal moments, manual logging, macros, custom foods | BLOCKING GATE | PLANNED |
| Phase 4 | Nutrition Pro | Full kcal/protein/carbs/fat goals, saved meals, recipes, copy meal/day | BLOCKING GATE | PLANNED |
| Phase 4 | Barcode | Barcode behind entitlement and feature flag | BLOCKING GATE | PLANNED |
| Phase 4 | Consumer boundaries | Invoices do not appear in consumer nutrition | BLOCKING GATE | PLANNED |
| Phase 5 | Progress | Weight, BMI, trend, week averages, target percentage | BLOCKING GATE | PLANNED |
| Phase 5 | Measurements | Logical body measurements without forced neck/calf default | BLOCKING GATE | PLANNED |
| Phase 5 | Photos | Private progress photos, signed access, no public default, AI photo consent gate | BLOCKING GATE | PLANNED |
| Phase 5 | Milestones | Strength progress, PRs, milestones, achievements | BLOCKING GATE | PLANNED |
| Phase 6 | Youri AI | Backend-mediated AI, no browser-to-AI provider call, entitlement check before call | BLOCKING GATE | PLANNED |
| Phase 6 | AI context | Goals, training, nutrition, progress, recovery context only when authorized | BLOCKING GATE | PLANNED |
| Phase 6 | AI quality | Missing data handled honestly; no hallucinated facts; structured responses validated | BLOCKING GATE | PLANNED |
| Phase 6 | AI cost | Usage/cost/rate-limit logging; no paid AI call without valid entitlement | BLOCKING GATE | PLANNED |
| Phase 6 | Avatar | Youri avatar support exists, final avatar remains ASSET REQUIRED until supplied | BLOCKING GATE | PLANNED |
| Phase 7 | Entitlements | Free/Pro/AI/trial/referral/goal/PT entitlements enforced server-side | BLOCKING GATE | PLANNED |
| Phase 7 | AI trial | 7-day no-payment-details trial starts, ends, locks AI, preserves data | BLOCKING GATE | PLANNED |
| Phase 7 | Referrals | Server-validated referral, max 2/month/user, abuse prevention | BLOCKING GATE | PLANNED |
| Phase 7 | Goal rewards | Qualified serious goal reward, max 2/12 months, paid users keep bonus value | BLOCKING GATE | PLANNED |
| Phase 7 | Payments | Provider test-mode integration only after NEEDS DECISION is resolved | BLOCKING GATE | PLANNED |
| Phase 8 | Gamification | Streaks, PR achievements, workout milestones, 25/50/75/100 goal milestones | BLOCKING GATE | PLANNED |
| Phase 8 | Streak logic | Planned vacation/rest/pause does not unfairly break streaks | BLOCKING GATE | PLANNED |
| Phase 8 | Notifications | Preferences, useful categories, frequency caps, no spam behavior | BLOCKING GATE | PLANNED |
| Phase 9 | Traineromgeving 3.0 | Dashboard, clients, dossier, training, nutrition, progress, recovery, agenda, notes | BLOCKING GATE | PLANNED |
| Phase 9 | Trainer business | Administration, invoices, rates, finances, settings preserved or replaced | BLOCKING GATE | REGRESSION |
| Phase 9 | Trainer isolation | Trainer A cannot access Trainer B clients/data | BLOCKING GATE | PLANNED |
| Phase 10 | Private Copilot | Copilot internal only, client cannot see analyses/concepts/inbox | BLOCKING GATE | PLANNED |
| Phase 10 | Copilot workflow | Analyze -> concept -> trainer review -> adjust -> approve -> client-facing execution | BLOCKING GATE | PLANNED |
| Phase 10 | AI Coach Inbox | Priorities normal/aandacht/belangrijk; signals backed by data; no alert fatigue | BLOCKING GATE | PLANNED |
| Phase 11 | Owner dashboard | Users, packages, trials, PT, upgrades, downgrades, cancellations, engagement | BLOCKING GATE | PLANNED |
| Phase 11 | Revenue metrics | MRR, ARR, ARPU, ARPPU, LTV only when data is reliable enough | BLOCKING GATE | PLANNED |
| Phase 11 | Retention | D1/D7/D30/later D90, cohorts, funnels, cancellation reasons not blocking cancellation | BLOCKING GATE | PLANNED |
| Phase 11 | Business AI | Observation/correlation/hypothesis/recommendation separated; no unsupported causal claims | BLOCKING GATE | PLANNED |
| Phase 12 | PWA polish | Responsive mobile UX, installability, performance, poor-connection behavior | BLOCKING GATE | PLANNED |
| Phase 12 | Language QA | NL/EN/DE end-to-end check | BLOCKING GATE | PLANNED |
| Phase 12 | Release hardening | No open P0, no release-blocking P1, owner test flows complete | BLOCKING GATE | PLANNED |
| Post Phase 12 | Full staging QA | All critical flows tested in staging before beta | BLOCKING GATE | PLANNED |
| Post Phase 12 | Beta | Controlled tester cohorts, onboarding/workout/D7/D30/trial/conversion/bug metrics | BLOCKING GATE | PLANNED |
| Post Phase 12 | Mobile staging | iOS TestFlight staging, Android internal/closed staging, mobile QA | BLOCKING GATE | PLANNED |
| Production | Readiness | Functionality, security, migrations, RLS, payments, languages, PWA/mobile, backup, rollback | BLOCKING GATE | PLANNED |

## Phase Safety And Rollback Matrix

| Phase | Required Safety / Rollback Condition | Status |
| --- | --- | --- |
| Phase 1 | Rollback/restoration notes for auth/profile/onboarding/entitlement foundation changes | PASS |
| Phase 2 | Recovery data changes documented; Health-sync remains placeholder unless separately approved | PASS |
| Phase 3 | Legacy training preserved until replacement accepted; workout data restoration path documented | PASS FOR FUNCTIONAL FREEZE; LEGACY DATA PRESERVED |
| Phase 4 | Nutrition data changes reversible or forward-fixable; invoices remain outside consumer nutrition | PASS FOR EMPTY LOCAL MIGRATION DESIGN; EXECUTION/LIVE VERIFICATION PENDING |
| Phase 5 | Private storage/RLS rollback notes required before progress photos go live | PLANNED |
| Phase 6 | AI calls gated by entitlement; no secret exposure; AI proposal/action rollback rules documented | PLANNED |
| Phase 7 | Payment/growth lifecycle changes staging test mode only; entitlement rollback/credit correction path documented | PLANNED |
| Phase 8 | Notification and reward triggers can be disabled or corrected; frequency caps tested | PLANNED |
| Phase 9 | Trainer/client data migration has rollback or compatibility bridge; cross-trainer isolation tested | PLANNED |
| Phase 10 | Copilot proposals/actions require approval and can be withdrawn/corrected before client-facing execution | PLANNED |
| Phase 11 | Analytics are privacy-aware and can be disabled/corrected without exposing raw private data | PLANNED |
| Phase 12 | Release hardening includes restoration notes for changed state and no open P0/release-blocking P1 | PLANNED |
## Functional Flow Matrix

| Area | Flow | Plans/Roles | Expected Result | Status |
| --- | --- | --- | --- | --- |
| Auth | Trainer signup | Trainer | Trainer profile and workspace remain valid | REGRESSION |
| Auth | Email confirmation | All | Confirmed account can continue onboarding/login | PASS |
| Auth | Login/logout | All | Correct session state and role-specific routing | PASS |
| Auth | Password reset | All | Reset link returns to staging and does not expose production URL | PASS |
| Auth | Client invitation | Trainer/PT client | Invite creates or relinks Auth user safely | PASS |
| Auth | Invite acceptance | PT client | Client profile links to trainer/client id | PASS |
| Onboarding | Free onboarding | Free | Required fields captured, BMI calculated | PASS |
| Onboarding | Goal engine | Free/Pro/AI | End goal captured; unsafe pace not freely chosen | PASS |
| Onboarding | AI goal discussion | AI | Youri proposes realistic pace/timeline/nutrition/training | PLANNED |
| Account | Account & language foundation | All | Account settings and NL/EN/DE primary client/Lid i18n persist in staging | PASS |
| Entitlements | Source of truth foundation | All | Free entitlement foundation exists and active Free state is verified | PASS |
| Entitlements | Locked premium feature | Free | Feature visible, locked, clear upgrade explanation | PLANNED |
| Entitlements | Pro access | Pro | Full Pro functionality available, AI only if separate entitlement exists | PLANNED |
| Entitlements | PT included access | PT client | Pro + Youri AI active while relationship active | PLANNED |
| Trial | AI trial start | New user | 7 days Youri AI without payment details | PLANNED |
| Trial | AI trial expiry | Trial user | AI locks, data preserved, fallback package applies | PLANNED |
| Referral | Bring a Friend reward | Referrer/new user | Server-validated reward, max 2/month/user | PLANNED |
| Training | Start workout | Free/Pro/PT/AI | User consciously starts active workout | PASS - OWNER REAL-PHONE ACCEPTED |
| Training | Log set | Free/Pro/PT/AI | Sets/reps/weight/RIR/RPE/rest/notes saved according to entitlement | PASS - OWNER REAL-PHONE ACCEPTED |
| Training | Free limit | Free | Max 4 active training_plan_days/workouts enforced server-side; exercise count inside workout is not limited | PASS - OWNER LIVE VERIFIED |
| Training | Exercise library | All | Canonical exercise metadata, picker, translations, and placeholder/legacy animation slots render correctly | PASS - 898 CATALOG/PICKER OWNER ACCEPTED; CONTENT/MEDIA GATES SEPARATE |
| Training | UUID save | All | Workout save works for one and multiple exercises without invalid uuid syntax | PASS - OWNER ACCEPTED |
| Nutrition | Free contract | Free | Targets, canonical search, unlimited normal daily logging, totals, max 10 active custom foods, seven-day server-enforced history | PLANNED - CONTRACT LOCKED |
| Nutrition | Full macros | Pro/AI/PT | kcal/protein/carbs/fat tracked correctly; AI receives Pro Nutrition without Phase 4 AI execution | PLANNED - CONTRACT LOCKED |
| Nutrition | Barcode | Pro/AI/PT | Barcode feature requires entitlement and enabled flag | PLANNED |
| Nutrition | Recipes/meals | Pro/AI/PT | Saved meals, recipes, favorites, copy meal/day work | PLANNED |
| Progress | Weight and BMI | All | Logs update trend/week average/target percentage | PLANNED |
| Progress | Progress photos | Pro/AI/PT or allowed plan | Private storage and signed access only | PLANNED |
| Recovery | Manual recovery | All | Sleep/steps/wellbeing/recovery feeling can be entered manually and persists per user/day | PASS |
| Health | Apple Health | Pro/AI iOS | Sync only when entitled and consented | PLANNED |
| Health | Health Connect | Pro/AI Android | Sync only when entitled and consented | PLANNED |
| Gamification | Goal milestones | All | 25/50/75/100 milestones trigger correctly | PLANNED |
| Notifications | Preferences | All | User can control notification categories | PLANNED |
| Trainer | Dossier tabs | Trainer | Overview/Training/Nutrition/Progress/Recovery/Agenda/Notes/AI available | PLANNED |
| Trainer | Existing finance/admin | Trainer | Existing invoices/rates/finance remain available until replacement accepted | REGRESSION |
| Copilot | Internal visibility | Trainer/PT client | Client never sees private Copilot artifacts | PLANNED |
| Owner | Admin access | Owner/admin | Only authorized owner/admin can open management dashboard | PLANNED |
| Analytics | Funnels | Owner/admin | Registration-to-paid and retention funnels calculated privacy-aware | PLANNED |
| Business AI | Insight wording | Owner/admin | No unsupported causal claims | PLANNED |

## Security Matrix

| Area | Risk | Required Test | Status |
| --- | --- | --- | --- |
| RLS | Cross-user data access | User A cannot read/write User B private data | PASS FOR PHASE 1, PHASE 2 RECOVERY_LOGS, AND PHASE 3 TRAINING DB FOUNDATION |
| RLS | Cross-trainer data access | Trainer A cannot access Trainer B client data | PLANNED |
| Roles | Owner/admin escalation | Non-owner cannot access owner dashboard/API | PLANNED |
| Entitlements | Premium bypass | Direct API/database attempts cannot unlock Pro/AI/barcode/Health | PLANNED |
| AI | Secret exposure | AI provider keys are not present in frontend bundles or logs | PLANNED |
| AI | Unauthorized AI context | AI context contains only data the user/trainer may access | PLANNED |
| AI | Cost abuse | Rate limits and usage logs prevent unexpected cost spikes | PLANNED |
| Payments | Client-side premium boolean | Client cannot grant paid state by changing frontend data | PLANNED |
| Storage | Private photos | Progress photos cannot be accessed without valid authorization/signed URL | PLANNED |
| Logs | Sensitive logging | Personal/health/fitness data not logged unnecessarily | PLANNED |
| Invite | Existing Edge Function risks | Broad CORS, pagination scan, metadata replacement reviewed before refactor | PLANNED |
| Production | Environment boundary | Staging changes never touch production resources | BLOCKING GATE - PASS TO DATE |
| Phase 3 | Exercise catalog grants | `public.exercises` authenticated SELECT-only; no anon/PUBLIC; no trainer or DELETE policy | BLOCKING GATE | PASS - LIVE STAGING VERIFIED |
| Phase 3 | Catalog import | Exactly 898 reviewed rows, stable UUID/slug, one transaction, idempotent upsert, no truncate/delete/legacy mutation | BLOCKING GATE | PASS - 898 LIVE STAGING ROWS VERIFIED |
| Phase 3 | Exercise language policy | NL canonical English names + Dutch instructions/UI; EN English; DE reviewed German + English alias search | BLOCKING GATE | POLICY/ARCHITECTURE PASS; NL INSTRUCTIONS AND DE EDITORIAL CONTENT OPEN |
| Phase 3 | Scale target | Catalog browsing, workout start/logging/history paths avoid unbounded DOM/media/query patterns for circa 1,000-user architecture target | BLOCKING GATE | PLANNED LOAD/PERFORMANCE TEST BEFORE PRODUCTION |

## Migration And Regression Matrix

| Area | Legacy Dependency | Required Check | Status |
| --- | --- | --- | --- |
| Profiles | `profiles.id` | Auth user relationship preserved | PASS |
| Trainer profile | `profiles.trainer_id` | Trainer id remains stable through migration | PASS |
| Client profile | `profiles.client_id` | Client id remains stable through migration | PASS |
| Workspace | `coach_workspaces.trainer_id` | Workspace relationship preserved | PASS |
| Legacy clients | `coach_workspaces.state.clients[].id` | Legacy client ids mapped to target tables | PLANNED |
| Legacy state | `coach_workspaces.state` | No destructive removal before migration rehearsal and rollback plan | BLOCKING GATE |
| Existing app | Current trainer/client flows | Working functionality preserved until accepted replacement exists | BLOCKING GATE |

## Release Blocking Rules

- P0: data loss, security leak, production touched, payment error, app unusable.
- P1: important feature broken, wrong entitlement, important AI error, trainer/client flow broken.
- P2: polish, spacing, small translation, visual detail.

No release with open P0. No release with release-blocking P1.

## Phase 3 Local Checks Prepared

| Check | Result |
| --- | --- |
| `node --check app.js` | PASS |
| `node --check assets/phase3-training-engine.js` | PASS |
| `node --check assets/phase3-static-check.js` | PASS |
| `node --check assets/phase3-exercise-import-pipeline.js` | PASS |
| `node assets/phase1-static-check.js` | PASS |
| `node assets/phase2-static-check.js` | PASS |
| `node assets/phase3-static-check.js` | PASS, 222 catalog/UUID/schema/seed/security/Focus Mode/accordion/edit/archive/restore/disclosure/regression checks |
| Canonical UUIDv5 guard | PASS, 12,000 unique deterministic UUIDs; browser/import mappings equal |
| Pinned Kinetic artifact | PASS, 899 source records; SHA-256/license verified; no media fields |
| Normalized real catalog | PASS, 898 records after one exact semantic duplicate removal; zero target padding; zero unmapped taxonomy values |
| Catalog localization | NL names 898/898 intentional canonical English; EN names/instructions 898/898 source; NL instructions 0/898 reviewed; DE names/instructions 0/898 reviewed with explicit English staging fallback |
| Catalog seed | PASS locally: 898 DB rows, artifact-equal payload, explicit transaction/count guard, idempotent difference-only upsert, no destructive/privileged SQL |
| Combined `app.bundle.js` plus Phase 1/2/3 patches parse | PASS |
| Phase 3 migration execution | SUCCESS, owner-reported Supabase SQL Editor result: `Success. No rows returned` |
| Phase 3 live schema/RLS/grants/functions/triggers verification | PASS, owner-reported read-only verification v3 with `overall_pass: true` |
| Phase 3 Free-day corrective migration execution | SUCCESS, owner-reported Supabase SQL Editor result: `Success. No rows returned` |
| Phase 3 Free-day corrective live verification | PASS, owner-reported read-only verification with `overall_pass: true` |
| Phase 3 final UUID/catalog/picker hardening deployment | PASS, staging only |
| Phase 3 mobile catalog + Focus Mode deployment | PASS, staging only; real-phone owner acceptance positive |
| Owner Free max-4 active workout-day test | PASS: four active workout days allowed; fifth server-blocked |
| Training accordion local responsive verification | PASS at 390x844, 820x1180, and 1440x900; one open section, no horizontal overflow, accessible expansion state |
| Saved workout edit local verification | PASS: populated builder, reorder, remove/archive, field update, stable row identity, completed History unchanged |
| Archive/restore local verification | PASS: archive reduces active count, restored plan consumes slot, restore at four active days shows localized limit message |
| Phase 3 final owner manual tests | PASS on real phone; complete functional Training acceptance recorded 2026-08-18 |

Known non-functional Phase 3 gates: reviewed Dutch exercise instructions, reviewed German exercise localization, and Youri-avatar exercise animations remain open as content/media work. They do not reopen the functionally frozen Training Engine.

## Phase 3 Live Database Verification

| Check | Result |
| --- | --- |
| All 5 expected Phase 3 tables present | PASS |
| Expected columns, datatypes, constraints, and indexes | PASS |
| RLS enabled on all 5 Phase 3 tables | PASS |
| Own-user policies present | PASS |
| No DELETE policies | PASS |
| No trainer-like broad policies | PASS |
| `authenticated` privileges limited to `SELECT`, `INSERT`, and `UPDATE` | PASS |
| `anon` and `PUBLIC` privileges absent | PASS |
| Function security and trigger checks | PASS |
| Free max-4 source logic, current entitlement logic, and advisory lock | PASS |
| Relational ownership guards for session/plan/day/exercise chains | PASS |
| Phase 1/2 guard tables still present with RLS enabled | PASS |
| Forbidden production/secrets reference scan | PASS |


## Phase 1 Local Checks Executed

| Check | Result |
| --- | --- |
| `node --check assets/phase1-foundation.js` | PASS |
| `node --check app.js` | PASS |
| Combined `app.bundle.js` plus Phase 1 patch syntax check | PASS |
| Local HTTP fetch for `index.html`, `app.js`, `assets/phase1-foundation.js` | PASS |
| `node assets/phase1-static-check.js` | PASS |
| Staging/production leakage search over changed files | PASS |
| Phase 1 staging migration execution | SUCCESS, owner-reported Supabase SQL Editor result: `Success. No rows returned` |
| Browser automation smoke test | NOT EXECUTED - bundled Playwright browser executable missing |
| Live Supabase schema/RLS/RPC permission verification | PASS, owner-reported 39-row read-only staging result |
| Live Supabase/Auth/email/browser verification | PASS, owner final Phase 1 exit-gate verification |
| Phase 1 owner tests 1-12 | PASS |
| Phase 1 performance retest on phone and laptop | PASS |

## Phase 2 Local Checks Executed

| Check | Result |
| --- | --- |
| `node --check app.js` | PASS |
| `node --check assets/phase2-home-recovery.js` | PASS |
| `node --check assets/phase2-static-check.js` | PASS |
| `node assets/phase1-static-check.js` | PASS |
| `node assets/phase2-static-check.js` | PASS |
| Combined bundle parse | PASS |
| Production/secret/service-role scan for Phase 2 scope | PASS |
| No MutationObserver/polling/native Health sync/Phase 3 Training Engine in Phase 2 scope | PASS |
| Phase 2 migration execution | SUCCESS, owner-reported Supabase SQL Editor result: `Success. No rows returned` |
| Live Supabase schema/RLS/policy/FK/index/trigger verification | PASS |
| Live grants hardening verification | PASS |
| Staging deployment | SUCCESS |
| Live staging cache/version verification | PASS |
| Owner Phase 2 tests 1-12 | PASS |
| Phase 2 performance retest on phone and laptop | PASS |

## Phase 2 Owner Exit-Gate Tests

| Test | Area | Result |
| --- | --- | --- |
| 1 | Vandaag/Home hub | PASS |
| 2 | Recovery save, refresh, logout/login persistence | PASS |
| 3 | Free Health entitlement gate | PASS |
| 4 | Training-load placeholder | PASS |
| 5 | Trackers -> Vandaag compatibility | PASS |
| 6 | Vandaag -> Trackers compatibility | PASS |
| 7 | Recovery date isolation | PASS |
| 8 | NL/EN/DE Phase 2 surfaces | PASS |
| 9 | Existing linked client compatibility | PASS |
| 10 | Logout and performance | PASS |
| 11 | Recovery input validation | PASS |
| 12 | Final Phase 1/Phase 2 regression | PASS |

## Phase 4 Schema Slice 1 Local Checks Executed

| Check | Result |
| --- | --- |
| Exact six-table migration scope and exact approved column order | PASS |
| One transaction; no seed/backfill/legacy mutation/destructive data operation | PASS |
| Constraints, FKs, partial uniqueness, indexes, RLS, own-user policies, and exact table ACL contract | PASS STATIC REVIEW |
| Function signatures, safe search path, Auth authority, internal/public execute ACL split | PASS STATIC REVIEW |
| Current Pro/AI/PT entitlement logic; missing/inactive/expired/future remains Free | PASS STATIC REVIEW |
| Free 10-active-custom-food concurrency lock and restore enforcement | PASS STATIC REVIEW |
| Free seven-local-day read/write/retry/archive boundary | PASS STATIC REVIEW |
| Server-calculated immutable food/provenance snapshots and request idempotency | PASS STATIC REVIEW |
| `node --check assets/phase4-static-check.js` | PASS |
| `node assets/phase4-static-check.js` | PASS, 87 checks |
| Frozen Phase 1 suite | PASS, 75 checks |
| Frozen Phase 2 suite | PASS, 46 checks |
| Frozen Phase 3 suite | PASS, 222 checks |
| Frozen Member UX suite | PASS, 56 checks |
| Post-migration JSON verification query | CREATED / SELECT-ONLY / NOT EXECUTED |
| Phase 4 migration execution | NOT EXECUTED |
