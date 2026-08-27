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
| Phase 4 | Architecture/readiness | Legacy inventory, normalized model, entitlement/RLS boundaries, food sources, retry, performance, slices, decisions, and test design | BLOCKING GATE | PASS - OWNER CONTRACT LOCKED; PHASE 4 IN PROGRESS |
| Phase 4 | Schema Slice 1 live security | Exact six-table scope, constraints/FKs/indexes, own-user RLS, exact ACLs, RPC authority, Free 10-custom limit, seven-day history, snapshots, retry identity | BLOCKING GATE | PASS - COMPLETE / LIVE / VERIFIED ON STAGING; CORRECTED CHECKER `overall_pass: true` |
| Phase 4 | Functional Slice 2 | Manual daily targets, bounded cursor search, empty catalog, private custom create/edit/archive, NL/EN/DE, mobile-first and legacy isolation | BLOCKING GATE | PASS - DEPLOYED / REAL-PHONE OWNER-TESTED / FROZEN |
| Phase 4 | Atomic log-item replacement | Own-user one-transaction immutable replacement, stale guard, replay identity, archive trail, authoritative day return | BLOCKING GATE | PASS - LIVE / READ-ONLY VERIFIED ON STAGING |
| Phase 4 | Functional Slice 3 | Day totals, targets, four meal moments, logging, atomic edit, archive, retries, date/history behavior, NL/EN/DE | OWNER ACCEPTANCE GATE | PASS - OWNER-TESTED / COMPLETE / FROZEN |
| Phase 4 | Member bottom navigation safe area | Every final member action scrolls above fixed navigation; safe-area, dialogs, keyboard, phone/tablet/desktop | UX FREEZE GATE | PASS - LIVE / OWNER-TESTED / FROZEN |
| Phase 4 | Slice 4A provider contract | OFF/USDA roles, legal gates, local-first ingestion, identity, quality, provenance, privacy, rate limits, 10k-1m scale | ARCHITECTURE GATE | PASS - OWNER LOCKED; OFF LEGAL GATE REMAINS BEFORE USE |
| Phase 4 | Slice 4B alias/search schema | Exact alias columns/constraints/FK/indexes, `pg_trgm`, RLS, SELECT-only ACL, no write/trainer policy, empty catalog, frozen guards | MIGRATION REVIEW GATE | PASS - LIVE / READ-ONLY VERIFIED ON STAGING |
| Phase 4 | Slice 4C provider operational state | Private cache/rate/circuit tables, zero client ACL/policy, service-role least privilege, atomic rate consumption, read-only verification | SECURITY GATE | PASS - LIVE / READ-ONLY VERIFIED ON STAGING |
| Phase 4 | USDA Provider Edge Function | Dedicated UUIDv5 identity, auth, CORS, cache, signed lookup, rate/circuit, normalization, no canonical write or secret | PROVIDER GATE | PASS - SEARCH/LOOKUP LIVE + AUTHENTICATED STAGING SMOKE |
| Phase 4 | Slice 4D transient provider logging | Gram-only signed-candidate log, nullable food identity, immutable snapshots, service-role-only RPC, atomic replacement, no canonical promotion | OWNER ACCEPTANCE GATE | PASS - LIVE / VERIFIED / OWNER-ACCEPTED / FROZEN |
| Phase 4 | Slice 4E Dutch generic catalog | 64 reviewed USDA foods, 197 Dutch/provider aliases, deterministic identity, local quality-gated search | CATALOG FREEZE GATE | PASS - ACCEPTED / FROZEN |
| Phase 4 | Package 4F-A OFF catalog/performance | Separate ODbL release/product/name domain, 24,458 products, 74,184 names, typed bounded search, local barcode, p95 gate | OWNER ACCEPTANCE GATE | PASS - COMPLETE / FROZEN |
| Phase 4 | Package 4F-B Dutch branded search UX | Dutch display labels, OFF-branded unified search, explicit selection and source attribution | OWNER ACCEPTANCE GATE | PASS - OWNER-ACCEPTED / FROZEN |
| Phase 4 | Package 4F-C OFF authoritative logging | Server-resolved ODbL snapshot, g/ml basis isolation, authoritative totals, retry/edit/archive | STAGING MIGRATION + E2E GATE | PASS - COMPLETE / FROZEN |
| Phase 4 | Package 4F-D transient unknown barcode | Local-first GTIN, exact OFF validation, signed transient snapshot, scanner/manual input, custom fallback | CONSOLIDATED STAGING MIGRATION + EDGE + FRONTEND E2E GATE | PASS - COMPLETE / LIVE / VERIFIED / FROZEN |
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
| Phase 4 | Nutrition data changes reversible or forward-fixable; invoices remain outside consumer nutrition | PASS - MIGRATION EXECUTED ON EMPTY STAGING FOUNDATION; CORRECTED LIVE VERIFICATION `overall_pass: true` |
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
| Nutrition | Free contract | Free | Targets, canonical search, unlimited normal daily logging, totals, max 10 active custom foods, seven-day server-enforced history | SLICE 2 OWNER-TESTED; SLICE 3 LOGGING/TOTALS/HISTORY UI LOCAL PASS |
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
| `node assets/phase4-static-check.js` | PASS, 90 checks |
| Frozen Phase 1 suite | PASS, 75 checks |
| Frozen Phase 2 suite | PASS, 46 checks |
| Frozen Phase 3 suite | PASS, 222 checks |
| Frozen Member UX suite | PASS, 56 checks |
| Phase 4 migration execution | SUCCESS WITH COMMIT on staging `mokxyyullfhkfalopbzd` |
| Initial post-migration JSON verification | `overall_pass: false`; every check passed except index metadata reconstruction |
| Live index investigation | PASS: migration definitions correct; verifier omitted `indoption` direction/null ordering and `indclass` operator-class semantics |
| Corrected post-migration JSON verification | PASS ON STAGING - `overall_pass: true`; prior index result confirmed checker-only false negative |

## Phase 4 Functional Slice 2 Local Checks Executed

| Check | Result |
| --- | --- |
| Slice 1 live prerequisite | PASS - corrected staging verifier `overall_pass: true` |
| Client-only normalized Nutrition view; trainer legacy renderer delegated | PASS |
| Empty/current target read, create/supersede RPC, bounds, stable request identity | PASS |
| Changed target retry rotates target/request IDs; unchanged retry reuses them | PASS |
| Empty catalog, query, 25-row server page, cursor append, error/retry | PASS |
| Custom food create/edit/archive through reviewed RPCs | PASS |
| Custom read bounded to 25 rows through SELECT-only RLS catalog access | PASS |
| Free 10-active limit message; server remains authority | PASS |
| Optimistic stale-edit/archive timestamp contract | PASS |
| `g`/`ml` explicit basis and serving/piece explicit conversion | PASS |
| No `1 ml = 1 g` assumption; no primary portion editor | PASS |
| NL/EN/DE runtime copy | PASS |
| Accessibility: semantic dialog, labels, 44px targets, Escape, focus restore, aria-live | PASS |
| Phone `390x844` | PASS - no horizontal overflow; touch targets preserved |
| Narrow phone `320x700` | PASS - no horizontal overflow; touch targets preserved |
| Tablet `820x1180` | PASS - no horizontal overflow; touch targets preserved |
| Desktop `1440x900` | PASS - compatibility maintained |
| `node --check assets/phase4-nutrition-slice2.js` | PASS |
| `node --check assets/phase4-nutrition-slice2-static-check.js` | PASS |
| `node --check assets/phase4-nutrition-slice2-browser-check.js` | PASS |
| `node assets/phase4-nutrition-slice2-browser-check.js` | PASS, 46 checks |
| `node assets/phase4-nutrition-slice2-static-check.js` | PASS after documentation synchronization |
| Full daily logging, recipes, saved meals, favorites, copy, barcode, provider, AI, trainer access | NOT IMPLEMENTED BY DESIGN |
| Database/migration/deployment/production during Slice 2 implementation | NO CHANGE / NO EXECUTION / STAGING DEPLOYMENT LATER OWNER-TESTED / PRODUCTION UNTOUCHED |

## Phase 4 Functional Slice 3 Local Checks Executed

| Check | Result |
| --- | --- |
| Atomic replacement prerequisite | PASS - RPC live and read-only verified on staging `mokxyyullfhkfalopbzd` |
| Authoritative selected-day read, four meals, empty day, totals and target progress | PASS |
| New item logging through `fmz_phase4_log_food_item` | PASS |
| Item edit through one `fmz_phase4_replace_food_log_item` call | PASS |
| Original archived, replacement active, same/changed meal, food, amount and notes | PASS |
| Stale `expected_updated_at`, `40001`, `23505`, network retry and changed-payload identity | PASS |
| Archive/remove and authoritative returned-day refresh | PASS |
| Local IANA timezone, local calendar date and previous-day navigation | PASS |
| Free seven-day behavior remains server-authoritative; Pro/AI/PT authority remains server-side | PASS |
| NL/EN/DE, accessibility and phone-first responsive behavior | PASS |
| Phase 1 frozen suite | PASS, 75 checks |
| Phase 2 frozen suite | PASS, 46 checks |
| Phase 3 frozen suite | PASS, 222 checks |
| Member UX frozen suite | PASS, 56 checks |
| Phase 4 schema suite | PASS, 90 checks |
| Slice 2 static/browser suites | PASS, 98 / 46 checks |
| Atomic replacement static suite | PASS, 79 checks |
| Slice 3 static/browser suites | PASS, 105 / 46 checks |
| JavaScript syntax and combined browser bundle parse | PASS |
| Staging deployment | PASS - runtime commit `14884e410c25cf3df651e08064e5120b59238149`, cache `20260819-phase4-nutrition-slice3-1` |
| Live read-only assets/runtime shell | PASS - four runtime files HTTP 200 and byte-identical; assembled auth navigation initialized; no horizontal overflow at required viewports |
| Database/migration/production during deployment | NO CHANGE / NO EXECUTION / UNTOUCHED |

## Phase 4 Member Bottom Navigation Safe-Area Hotfix Checks

| Check | Result |
| --- | --- |
| Root cause: six member items in a five-column fixed nav create two rows while old reserve was only `98px` | CONFIRMED |
| Global nav height, offset, device inset and interaction-spacing tokens | PASS |
| Member content and scroll padding consume the global safe-area token | PASS |
| Maximum-scroll final action clears nav: Vandaag, Training, Voeding, Trackers, Agenda, Instellingen | PASS |
| Phone `390x844` and `320x700`, no horizontal overflow | PASS; 35px final-action clearance |
| Tablet `820x1180` and desktop `1440x900` | PASS; 34px final-action clearance |
| iPhone-style 34px inset and Android-style zero inset | PASS |
| Slice 2/Slice 3 Nutrition dialogs hide and restore fixed navigation | PASS |
| Phase 3 Exercise Picker, Focus Mode and History hide and restore fixed navigation | PASS |
| Reduced keyboard viewport keeps focused input and save action reachable | PASS |
| Tap targets, focus restoration, dialog semantics and Escape contracts | PASS |
| `node assets/member-bottom-nav-safe-area-static-check.js` | PASS, 41 checks |
| `node assets/member-bottom-nav-safe-area-browser-check.js` | PASS, 45 checks |
| Full frozen regression suites, syntax and combined browser bundle parse | PASS |
| Database/migration/deployment/production | NO CHANGE / NO EXECUTION / NO DEPLOYMENT / UNTOUCHED |

## Phase 4 Slice 4B Alias/Search Schema Local Checks

| Check | Result |
| --- | --- |
| Slice 4A provider/local-first contract | PASS - OWNER LOCKED; OFF legal gate remains |
| One new table only: `public.food_aliases` | PASS |
| Exact 19-column alias/provenance/market/archive contract | PASS |
| FK, 14 CHECK constraints and active alias uniqueness | PASS |
| `pg_trgm`, prefix, trigram, parent and market-priority indexes | PASS |
| RLS and visible-parent policy | PASS |
| `authenticated` SELECT only; `anon`/`PUBLIC` none | PASS |
| No write/delete/trainer policy or new RPC | PASS |
| No seed, backfill, provider table, provider data or legacy mutation | PASS |
| SELECT/CTE-only live verifier and ACL metadata handling | PASS |
| `node assets/phase4-nutrition-slice4b-static-check.js` | PASS, 83 checks |
| Phase 1 / Phase 2 / Phase 3 / Member UX | PASS, 75 / 46 / 222 / 56 checks |
| Phase 4 schema / Slice 2 / atomic / Slice 3 | PASS, 90 / 98+46 / 79 / 105+46 checks |
| Member safe-area frozen suites | PASS, 41 static / 45 browser checks |
| Migration/verifier execution | PASS - LIVE / READ-ONLY VERIFIED ON STAGING |

## Phase 4 USDA Provider Edge Function Checks

| Check | Result |
| --- | --- |
| Dedicated permanent namespace `23440733-7e58-4c21-ad15-591eae6ab8ac` | PASS |
| Exact `provider_code:provider_food_id` UUIDv5 identity | PASS |
| `usda_fdc:171077` deterministic result `a30e5e7f-9711-5823-b668-a25ff4a729fe` | PASS |
| Phase 3 exercise namespace separate and unused | PASS |
| Supabase bearer verification and no client authority input | PASS |
| Strict staging CORS and fixed USDA host | PASS |
| Search/lookup input, body, result and response bounds | PASS |
| HMAC-signed candidate token, canonical encoding, expiry and tamper rejection | PASS |
| Query/user HMAC privacy; request replay bound to operation identity | PASS |
| Cache-first; checksum, mapping-version and TTL validation | PASS |
| Atomic shared rate limit and circuit state integration | PASS |
| USDA type and nutrient mapping, 100 g basis, no density assumption | PASS |
| Quality reject/quarantine and safe provider errors | PASS |
| No canonical food/alias/portion write or ingestion route | PASS |
| No secret value, production ref, AI, OFF, barcode or frontend change | PASS |
| `deno check --frozen supabase/functions/nutrition-provider/index.ts` | PASS; complete pinned dependency graph and Edge entrypoint typecheck |
| `node --experimental-strip-types --test supabase/functions/nutrition-provider/nutrition-provider.test.ts` | PASS, 28 tests; dependency-injected local harness, no live calls |
| `node assets/phase4-nutrition-provider-static-check.js` | PASS, 103 checks |
| Edge Function search/lookup deployment and authenticated USDA smoke | PASS - STAGING ONLY; query/food cache, signed token, tamper rejection, rate/circuit state verified |
| Canonical foods/portions/aliases unchanged by provider smoke | PASS |

## Phase 4 Slice 4D Transient Provider Snapshot Logging Local Checks

| Check | Result |
| --- | --- |
| Owner decisions: transient snapshot, grams-only, no auto-promotion | PASS - LOCKED |
| Existing `food_log_items.food_id` / `food_portion_id` nullable compatibility | PASS - NO TABLE CHANGE REQUIRED |
| Provider log/replace RPCs exact service-role-only ACL | PASS |
| `PUBLIC`, `anon`, `authenticated` cannot execute provider RPCs | PASS |
| Fixed search path and `SECURITY DEFINER` boundary | PASS |
| Browser cannot submit nutrients, food ID, provider payload, user, role or entitlement | PASS |
| Signed candidate token is revalidated through trusted lookup/cache | PASS |
| USDA accepted types, identity, mapping, nutrition bounds and provenance validation | PASS |
| 100 g reference and consumed grams only | PASS |
| Stable item/request UUID and exact-payload idempotent replay | PASS |
| Changed-payload request reuse rejected | PASS |
| Request/item/day advisory-lock ordering | PASS |
| Free current day plus six prior local days | PASS |
| Current Pro/AI/Personal Coaching full-history helper reused | PASS |
| Atomic provider replace: lock, expected timestamp, active replacement, archived original | PASS |
| Existing archive RPC remains nullable-food compatible and unchanged | PASS |
| No canonical `foods`, `food_portions`, or `food_aliases` write | PASS |
| No trainer policy, DELETE policy, seed, import, frontend, AI or production path | PASS |
| Read-only verifier returns individual checks plus `overall_pass` | PASS - LOCAL ARTIFACT |
| Provider unit tests | PASS, 28 tests |
| Provider security/static checks | PASS, 103 checks |
| Slice 4D migration/verifier/static checks | PASS, 93 checks |
| Phase 1 / Phase 2 / Phase 3 / Member UX frozen suites | PASS, 75 / 46 / 222 / 56 checks |
| Phase 4 schema / Slice 2 / Slice 3 / atomic / Slice 4B / Slice 4C | PASS, 90 / 98 / 105 / 79 / 83 / 116 checks |
| Migration execution / Edge deployment / frontend integration | NOT PERFORMED |

## Phase 4 Slice 4C Operational State Schema Local Checks

| Check | Result |
| --- | --- |
| Slice 4A provider contract and USDA-first boundary | PASS - OWNER LOCKED |
| Slice 4B staging foundation | PASS - LIVE / COMPLETE |
| Exactly four operational tables; ingestion ledger deferred | PASS |
| Query cache excludes raw query/user identity and bounds payloads | PASS |
| Food candidate cache preserves provider/mapping/checksum/quality identity | PASS |
| USDA user budgets 3/30s, 12/10m, 100/day and global 800/hour | PASS |
| Global plus per-user check/consume is transactionally atomic | PASS |
| Same-window request replay cannot double-consume | PASS |
| Circuit closed/open/half-open transitions are serialized | PASS |
| RLS enabled with zero member/trainer policies | PASS |
| `authenticated`/`anon`/`PUBLIC` table privileges none | PASS |
| Internal function EXECUTE limited to `service_role` | PASS |
| Cache ACL limited to backend SELECT/INSERT/UPDATE; no removal privilege | PASS |
| SELECT/CTE-only verifier; no application function execution | PASS |
| No provider call, food import, canonical write, Edge deployment or frontend | PASS |
| `node assets/phase4-nutrition-slice4c-static-check.js` | PASS, 116 checks |
| Frozen Phase 1/2/3/Member UX suites | PASS, 75 / 46 / 222 / 56 checks |
| Phase 4 schema / Slice 2 / atomic / Slice 3 | PASS, 90 / 98+46 / 79 / 105+46 checks |
| Member safe-area / Slice 4B suites | PASS, 41+45 / 83 checks |
| Migration/verifier execution | PASS - LIVE / READ-ONLY VERIFIED ON STAGING |

## Phase 4 Slice 4E Ingestion Ledger + Alias Search Local Checks

| Check | Result |
| --- | --- |
| Slice 4D backend/frontend baseline | PASS - FROZEN |
| One private additive ingestion-ledger table | PASS |
| Artifact SHA/provider-version uniqueness and bounded provenance | PASS |
| Forward-only lifecycle, immutable identity, no removal workflow | PASS |
| RLS enabled; zero member/trainer/anon/PUBLIC/service-role ACL | PASS |
| Nullable restrictive foods/aliases ingestion links | PASS |
| Reviewed/verified canonical quality gate | PASS |
| Owned custom foods preserved; other-user custom hidden | PASS |
| Reviewed/verified alias and visible-parent gate | PASS |
| One preferred active NL alias per normalized term and market | PASS |
| Existing search signature/response contract preserved | PASS |
| Exact custom, NL alias, canonical, prefix, relevance, trigram ranking | PASS |
| Dedupe by food UUID; raw/cooked identities remain separate | PASS |
| Rank-aware stable keyset; no OFFSET; bounded candidates/pages | PASS |
| Existing Slice 4B pg_trgm/prefix indexes reused | PASS |
| No browser canonical write, trainer route, seed, provider call or import | PASS |
| SELECT/CTE-only foundation verifier with `overall_pass` | PASS - LIVE STAGING, 27 PASS / 0 FAIL |
| Eight separate whitespace-insensitive alias search source checks | PASS |
| `node assets/phase4-nutrition-slice4e-static-check.js` | PASS, 153 checks |
| Reviewed USDA manifest | PASS, 64 canonical foods / 197 aliases / 0 portions |
| Category distribution | PASS, carbohydrates 17 / dairy 7 / fats-basics 7 / fruit 8 / legumes 4 / protein 11 / vegetables 10 |
| Raw/dry and cooked identity separation | PASS, 10 reviewed pairs |
| Preferred ambiguous NL alias uniqueness | PASS, 9 documented decisions |
| Required Dutch local-search coverage | PASS, 12/12 including `volkoren brood` and reviewed 2%-milk `halfvolle melk` alias |
| Deterministic one-transaction seed | PASS, fail-on-drift replay / exact counts / no DELETE or TRUNCATE |
| SELECT/CTE-only post-import verifier | PASS local parse/static review; NOT EXECUTED |
| `node assets/phase4-nutrition-slice4e-catalog-static-check.js` | PASS, 1908 checks |
| PostgreSQL + PL/pgSQL offline parse | PASS |
| Phase 1 / Phase 2 / Phase 3 / Member UX frozen static suites | PASS, 75 / 46 / 222 / 56 checks |
| Phase 4 schema / Slice 2 / atomic / Slice 3 | PASS, 90 / 98 / 79 / 111 checks |
| Slice 4B / Slice 4C / provider / provider logging / resolver / Slice 4D | PASS, 83 / 116 / 103 / 106 / 80 / 108 checks |
| Slice 2 / Slice 3 / member safe-area browser suites | PASS, 46 / 107 / 45 checks |
| Migration execution | PASS - LIVE ON STAGING |
| Corrected foundation verifier rerun | PASS - LIVE STAGING, `overall_pass = true` |
| Catalog import / post-import verifier | PASS - OWNER-ACCEPTED / FROZEN |

## Phase 4 Slice 4F OFF Catalog + Local Search Local Checks

| Check | Result |
| --- | --- |
| Slice 4E 64-food/197-alias catalog | PASS - ACCEPTED / FROZEN |
| Separate release, product and localized-name ODbL tables | PASS |
| Permanent `open_food_facts:<normalized_gtin14>` UUIDv5 identity | PASS |
| EAN-8, UPC-A, EAN-13 and GTIN-14 check-digit normalization | PASS |
| Original barcode retained; normalized GTIN-14 unique | PASS |
| Duplicate/conflicting GTIN quarantine contract | PASS |
| `per_100_g` and `per_100_ml` distinct; no density assumption | PASS |
| Required nutrition fields and finite bounds | PASS |
| Active complete/reviewed quality gate | PASS |
| Release lifecycle, one current release and exact import-count guard | PASS |
| Product-name revision/licence relational guard | PASS |
| RLS enabled; authenticated SELECT-only; anon/PUBLIC/service-role no direct table grant | PASS |
| No trainer policy, mutating member policy, DELETE policy or browser service role | PASS |
| Frozen `fmz_phase4_search_foods` unchanged | PASS |
| Typed custom/OFF/generic unified-search source separation | PASS |
| Exact/prefix/trigram deterministic ranking | PASS |
| Trigram branches use indexable `%` predicates with fixed threshold | PASS |
| Cross-language OFF prefix index matches search predicate | PASS |
| 15 individually bounded branches, global 1,000 cap, page max 25 | PASS |
| Rank-aware keyset pagination with symmetric trimmed-name cursor; no OFFSET | PASS |
| Authenticated OFF reads limited to explicit safe catalog columns | PASS |
| Exact local barcode lookup; no provider/network call | PASS |
| Original live verifier execution | STOPPED - verifier-only PostgreSQL `22023` on zero-dimensional empty column ACL array |
| Corrected read-only verifier with individual checks and `overall_pass` | PASS - LIVE STAGING, 26 PASS / 0 FAIL |
| Corrected row-wise ACL metadata probe | PASS - 34 intended authenticated column SELECT grants; no unexpected client/service-role grants |
| NL Dutch display label with canonical fallback | PASS - LOCAL ONLY / NOT DEPLOYED |
| Visible-day label hydration bounded to 200 IDs with duplicate suppression | PASS |
| Future immutable OFF snapshot and unknown-barcode path | PASS - ARCHITECTURE ONLY |
| ODbL attribution/export and separate image-licence policy | PASS - DOCUMENTED; PRODUCTION LEGAL REVIEW STILL REQUIRED |
| Pinned source/revision and exact Netherlands extract | PASS - SHA/size/revision locked; 106,650 rows |
| Exact eligible catalog and basis split | PASS - 24,458 products; 20,355 per 100 g; 4,103 per 100 ml |
| GS1 GTIN-14 and UUIDv5 identities | PASS - 24,458 unique of each |
| Source-derived localized/search names | PASS - 74,184 rows; 18,970 Dutch product names; no fabricated translations |
| Product/name/release/import/verifier hashes | PASS - byte-locked in artifact manifest |
| PostgreSQL normalization authority | PASS - existing `fmz_phase4_normalize_catalog_text` mirrored without Unicode compatibility normalization or transliteration |
| Independent normalization fixtures | PASS - 13 PostgreSQL cases covering symbols, accents, Thai, Korean, punctuation, whitespace, brands and names |
| Normalization correction scope | PASS - 1 product / 1 brand / 23 names and name UUIDs; 24,458 product UUIDs unchanged |
| Row-level artifact verifier | PASS - 779,905 checks |
| Bulk artifact static/security suite | PASS - 93 checks |
| Schema-equivalent PostgreSQL dry run | PASS - rollback, import, post-verifier and idempotent replay |
| One-transaction file importer | PASS - two `\copy` loads, advisory lock, fail-on-drift, replay-safe, finalization last |
| 24,458-product import | READY FOR OWNER ARTIFACT REVIEW / NOT EXECUTED |
| Migration execution | PASS - LIVE ON STAGING `mokxyyullfhkfalopbzd` |
| Frontend deployment / Edge deployment | 4F-B FRONTEND OWNER-ACCEPTED / FROZEN; 4F-C FRONTEND LIVE / VERIFIED / FROZEN; EDGE UNCHANGED |

## Phase 4 Package 4F-C OFF Authoritative Logging Checks

| Check | Result |
| --- | --- |
| 4F-B owner acceptance | PASS - COMPLETE / FROZEN |
| Existing log/day/history/archive architecture reused | PASS |
| Server resolves current imported active OFF product | PASS |
| Browser supplies no nutrient authority | PASS |
| `per_100_g` and `per_100_ml` remain isolated | PASS - NO DENSITY OR ML=G |
| Immutable ODbL identity, release, licence, attribution and derivation snapshot | PASS |
| Stable request/item identities and equality replay | PASS |
| Same-product and changed-OFF-product atomic replacement | PASS |
| Optimistic timestamp conflict and authoritative reload | PASS |
| Existing generic/custom/USDA logging and archive preserved | PASS |
| Additive migration/static/security suite | PASS - 98 CHECKS |
| Nutrition browser vertical-slice suite | PASS - 121 CHECKS |
| Phase 1 / Phase 2 / Phase 3 / Member UX frozen suites | PASS - 75 / 46 / 222 / 56 |
| Slice 2 / member navigation browser suites | PASS - 46 / 45 |
| Corrected migration execution | PASS - STAGING ONLY; SHA-256 `15C3ABAFDB7D77E85397006BA1D62C9221DA0820C1052AF284911B9EDF2DFF45` |
| Corrected read-only live verifier | PASS - 18/18; `overall_pass = true`; SHA-256 `E48E4FDFCA17928BB85DE4D478002E3DCE92996210BF8E7CC916870FE1747375` |
| Controlled authenticated staging E2E | PASS - g/ml log, replay, edit, replace, stale conflict, totals, history, archive |
| Controlled E2E cleanup | PASS - transaction `ROLLBACK`; postcheck controlled rows `0` |
| Live frontend | PASS - commit `ebd0fc61652ed624f82cfda35fb96e16141b8a9e`; cache `20260826-phase4f-c1`; runtime SHA-256 `AF1CCCCEDF762E1E36D1813441363CA6B1E502E94B4C8B8D9C065DD1B1BB0801` |

## Phase 4 Package 4F-D Transient OFF Barcode Local Checks

| Check | Result |
| --- | --- |
| Persistent OFF catalog runtime mutation | PASS - ABSENT |
| Exact local-first barcode resolver | PASS |
| Exact OFF product endpoint and server normalization | PASS |
| GTIN Mod-10 and source-bound UUID/token | PASS |
| Explicit 100 g / 100 ml, no density conversion | PASS |
| Immutable transient ODbL snapshot log/replace/archive | PASS |
| Historical same-product edit without expired token | PASS |
| Fresh-candidate changed-product atomic replacement | PASS |
| Custom fallback with normalized barcode | PASS |
| Camera privacy, explicit start, stop and duplicate suppression | PASS |
| Manual barcode uses identical lookup path | PASS |
| Native BarcodeDetector + vendored MIT ZXing fallback | PASS - ZXING SHA-256 `066BC34EDFCDD4A33F0964AEEC967752A0DEA1CCAF36E58E319AC9FCB5070F6A` |
| Edge unit/contract tests | PASS - 49 |
| 4F-D static/security checks | PASS - 93 |
| Nutrition browser vertical-slice checks | PASS - 135 |
| Phase 1 / Phase 2 / Phase 3 / Member UX frozen suites | PASS - 75 / 46 / 222 / 56 |
| Migration/verifier | PASS - main migration/verifier live; parent-context correction `80EB696450ADC81A38BE12EBEC1631F660C85425CC8453E836047815BE3EA0BF` and verifier `96A7FCCF598463E4098AEF56A6D59F238FAA9212C9599597D58607D46E5C9913`; correction verifier PASS 12/12 |
| Controlled authenticated staging E2E | PASS - local hit, transient OFF, 100 g/ml, log/replay, same/changing-product edit, archive, immutable history and cleanup |
| Catalog/member preservation | PASS - 24,458 products, 74,184 names, 64 canonical foods, 197 aliases; zero transient promotion; zero active controlled rows |
| Live frontend | PASS - commit `bb1f7e4`; cache `20260827-phase4fd-barcode1`; runtime and vendored ZXing byte-identical |
| Database / Edge staging / frontend staging / production | APPROVED ADDITIVE MIGRATIONS LIVE / EDGE V8 LIVE / DEPLOYED / UNTOUCHED |
