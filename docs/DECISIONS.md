# FitMetZorge Architecture Decision Log

Approved architecture and product decisions must be recorded here chronologically.

## Decision 0001: Staging-first release model

Status: APPROVED

Date: 2026-08-14

Decision:

New functionality follows this release path:

1. Build in staging.
2. Test in staging.
3. Owner approval.
4. Only then consider production.

Production may never be modified without explicit user permission.

Rationale:

This protects the existing production environment while the Master Build is developed and verified incrementally.

## Decision 0002: Master Build product specification is source of truth

Status: APPROVED

Date: 2026-08-15

Decision:

The definitive Master Build product specification is captured in `docs/MASTER_BUILD_PLAN.md` and governs Phase 1 onward.

Rationale:

The build needs one stable product direction so later phases do not silently remove or simplify required functionality.

## Decision 0003: FitMetZorge is a full fitness and lifestyle platform

Status: APPROVED

Date: 2026-08-15

Decision:

The product combines training, nutrition, progress, recovery, health integrations, goals, gamification, AI coaching, and human Personal Training for Free, Pro, Youri AI, PT clients, trainers, and owner/admin.

Rationale:

The product goal is outcome-oriented coaching, not just logging.

## Decision 0004: Free, Pro, Youri AI, and Personal Coaching are entitlement-driven

Status: APPROVED

Date: 2026-08-15

Decision:

Free, Pro, Youri AI, trials, referrals, goal rewards, and Personal Coaching access must be represented as real server-enforced entitlements. UI locks are not sufficient.

Rationale:

Entitlement logic protects revenue, prevents bypasses, and supports trials/rewards cleanly.

## Decision 0005: Pro and Youri AI target prices are configurable

Status: APPROVED

Date: 2026-08-15

Decision:

Pro has an initial target price around EUR 9.99/month and Youri AI around EUR 19.99/month, but implementation must keep pricing configurable.

Rationale:

Pricing may change without requiring a core refactor.

## Decision 0006: Youri AI is not a generic chatbot

Status: APPROVED

Date: 2026-08-15

Decision:

The AI coach is named `YOURI`, must use FitMetZorge data context when authorized, and must become more personal as history grows. The final avatar based on owner Youri Zorge is `ASSET REQUIRED`.

Rationale:

The AI experience should be product-native, recognizable, and useful, not a detached chat widget.

## Decision 0007: AI calls must be backend-mediated and cost-controlled

Status: APPROVED

Date: 2026-08-15

Decision:

No browser-to-AI provider calls. AI runs through a secure backend/Edge Function with auth, authorization, entitlement check, context retrieval, structured response validation, rate limiting, and usage/cost logging.

Rationale:

This protects secrets, user data, entitlements, and operating cost.

## Decision 0008: Personal Coaching clients use the same consumer app

Status: APPROVED

Date: 2026-08-15

Decision:

Active PT clients use the same consumer app and receive Pro plus Youri AI plus linked human coach access while the coaching relationship is active.

Rationale:

PT clients should not get an inferior app experience, and the trainer remains strategically in control.

## Decision 0009: Trainer Copilot is private and approval-based

Status: APPROVED

Date: 2026-08-15

Decision:

Private Trainer Copilot and AI Coach Inbox are internal trainer tools. Strategic AI changes require trainer review and approval before becoming client-facing.

Rationale:

The AI supports the trainer but does not replace trainer responsibility or expose internal reasoning to clients.

## Decision 0010: Normalize away from permanent coach_workspaces.state dependency

Status: APPROVED

Date: 2026-08-15

Decision:

The target Supabase architecture must not permanently depend on one large `coach_workspaces.state` JSONB object. Legacy remains until a safe staged migration exists.

Rationale:

Normalized domains are needed for RLS, entitlements, analytics, AI context, migrations, and maintainability.

## Decision 0011: RLS and server authorization are mandatory security boundaries

Status: APPROVED

Date: 2026-08-15

Decision:

RLS is primary database security. Sensitive actions require server-side authorization. Service-role keys, AI keys, and payment secrets never go to frontend.

Rationale:

Hidden UI controls do not prevent data access or entitlement bypasses.

## Decision 0012: Web/PWA comes before native iOS and Android

Status: APPROVED

Date: 2026-08-15

Decision:

Build the full new functionality as web/PWA in staging first. Native iOS/Android builds come after PWA maturity, using shared code where possible and staging backend for TestFlight/internal testing.

Rationale:

This reduces complexity and lets the product mature before native-specific work.

## Decision 0013: Training schemas are not publicly shareable

Status: APPROVED

Date: 2026-08-15

Decision:

Personal training schemas must not be publicly shared between users. Achievement cards may be shareable.

Rationale:

Training schemas are personal and public sharing can reduce subscription value.

## Decision 0014: Phase order and review gates are mandatory

Status: APPROVED

Date: 2026-08-15

Decision:

Build order is Phase 1 through Phase 12 as documented in `docs/MASTER_BUILD_PLAN.md`. Codex must stop for review between major phases and stop immediately for production, destructive migration, data loss, security, credentials, provider setup, missing product decision, requirements conflict, or impossible acceptance criteria.

Rationale:

The Master Build is broad and needs controlled increments with owner review.

## Decision 0015: Production release requires explicit owner approval

Status: APPROVED

Date: 2026-08-15

Decision:

Codex may never independently release production. Production requires a Production Readiness Report and explicit owner approval.

Rationale:

Production contains real user risk and must be protected from accidental release or migration.

## Decision 0016: Minimal entitlement foundation precedes entitlement consumers

Status: APPROVED

Date: 2026-08-15

Decision:

Phase 1 must establish the minimal entitlement source-of-truth contract needed by later phases. Phase 7 expands that foundation into subscriptions, trials, referrals, goal rewards, bonus entitlements, and payment-provider lifecycle logic.

Rationale:

Training limits, nutrition locks, Health access, AI access, and PT included access appear before or during Phase 6, so those phases need a consistent entitlement foundation without depending on later payment work.

## Decision 0017: Phase 4 Nutrition tier contract

Status: APPROVED

Date: 2026-08-18

Decision:

Free Nutrition includes calorie and macro targets, canonical search, unlimited normal daily logging, daily totals, up to 10 active private custom foods, and seven-day history. Pro adds full retained history, favorites, recents, saved meals, own recipes, meal/day copy, richer presentation, unlimited product-level custom foods subject to abuse controls, and later barcode. AI and active Personal Coaching receive the complete Pro Nutrition feature set, while actual AI functionality remains later.

Rationale:

Free must be genuinely usable while paid tiers receive meaningful reusable content, history, and workflow value. Server authority protects the history and custom-food boundaries.

## Decision 0018: Nutrition logs, targets, and plans remain separate

Status: APPROVED

Date: 2026-08-18

Decision:

Actual consumed food logs, nutrition targets, and meal plans are separate normalized concepts. Log items keep immutable nutrient, calculation-basis, food, and provider snapshots. Catalog, recipe, plan, or target changes may not silently rewrite completed intake history.

Rationale:

This preserves auditability, correct history, future trainer assignment, provider updates, and safe AI context.

## Decision 0019: Provider-neutral private Nutrition data model

Status: APPROVED

Date: 2026-08-18

Decision:

Canonical food identity is provider-neutral with first-class provenance, version, license, and quality metadata. Custom foods, saved meals, and recipes are private. Open Food Facts and USDA have preferred future roles; NEVO is excluded until legal/license approval. Barcode and all credentialed provider calls remain backend-mediated later slices.

Rationale:

This avoids vendor lock-in, protects private member content, and makes source quality and licensing reviewable.

## Decision 0020: Phase 4 starts with own-user Schema Slice 1

Status: APPROVED / LIVE / VERIFIED ON STAGING

Date: 2026-08-18

Decision:

The first additive Phase 4 schema slice is limited to Nutrition preferences/timezone, foods, food portions, targets, day logs, log items, and their minimum RLS/grants/RPC foundation. It has no catalog data, legacy backfill, trainer policy, saved meals, recipes, copy, barcode, calculator logic, AI, or frontend. Free seven-day history and the 10-active-custom-food limit are server-authoritative.

Rationale:

A small security-first slice can be reviewed, migrated, and live-verified before frontend work while preserving all frozen baselines and legacy Nutrition.

## Decision 0021: Slice 4 uses a local-first hybrid food-provider architecture

Status: APPROVED / SLICE 4A LOCKED; OFF LEGAL GATE REQUIRED BEFORE PROVIDER USE

Date: 2026-08-19

Decision:

Use USDA Foundation/FNDDS as the primary source for a reviewed generic starter catalog with Dutch aliases. Reserve Open Food Facts for Dutch/EU branded foods and future barcode identity after explicit ODbL/DCL legal and attribution approval. Search the local normalized catalog first; provider calls are backend-only, cached, rate-limited, quality-gated, and never triggered on every keystroke. Private custom foods remain separate. NEVO remains excluded.

The live `foods` and `food_portions` tables remain the normalized catalog source of truth. Slice 4B adds only a reviewed `food_aliases` contract and local prefix/trigram candidate indexes. It does not change the frozen search RPC, import provider data, or create provider cache/import/rate-limit tables. Those operational tables remain deferred until Slice 4C proves the exact backend requirements. No provider record may be imported before separate migration, legal, provenance, quality, and owner execution gates pass.

Rationale:

USDA offers CC0 generic nutrient data but limited Dutch naming. Open Food Facts has stronger Dutch/EU branded coverage, but community quality, ODbL obligations, and strict public search rate limits make direct browser or search-as-you-type integration unsafe. Local-first search gives predictable mobile performance, privacy, resilience, and scale while preserving provider provenance.

## Decision 0022: Slice 4C provider operational state is private and server-controlled

Status: APPROVED / LIVE / READ-ONLY VERIFIED ON STAGING

Date: 2026-08-19

Decision:

Slice 4C uses exactly four additive backend-only tables: `nutrition_provider_query_cache`, `nutrition_provider_food_cache`, `nutrition_provider_rate_buckets`, and `nutrition_provider_runtime_state`. All four have RLS enabled and no member, trainer, `anon`, or `PUBLIC` policy or table privilege. Service-role access is limited to cache read/upsert, runtime-state read, and two narrowly scoped internal functions for atomic rate consumption and circuit transitions. The service credential remains backend-only and is never stored in the database.

The database hard-enforces the current USDA ceilings of 3 requests per 30 seconds, 12 per 10 minutes, 100 per day per HMAC subject, and 800 per hour globally. A later backend may enforce stricter configuration but cannot widen these ceilings. Query caches store an HMAC identity rather than raw queries or user IDs. Provider candidates remain non-canonical. The ingestion ledger, canonical import, USDA calls, Open Food Facts, barcode, Edge deployment, and frontend integration remain deferred.

Rationale:

Durable shared counters and circuit state are required for concurrency-safe abuse protection across Edge instances. Private RLS-protected state, explicit payload bounds, checksums, mapping-version keys, short expiry contracts, and transactionally consumed buckets prevent member access, partial counter updates, incompatible cache reuse, and unbounded provider payload retention.

## Decision 0023: Phase 4 provider candidates use a dedicated permanent UUIDv5 namespace

Status: APPROVED / LOCKED

Date: 2026-08-19

Decision:

`PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE = 23440733-7e58-4c21-ad15-591eae6ab8ac` is the permanent, non-secret UUIDv5 namespace for deterministic external-provider candidate identity. It was generated once on 2026-08-19 with the operating system cryptographic random UUID generator. All environments use the same namespace. The exact name format is `provider_code:provider_food_id`; the initial USDA identity is therefore `usda_fdc:<fdcId>`, for example `usda_fdc:171077`.

Provider codes are part of identity, so a later separately approved provider can use the same namespace without collision, for example `open_food_facts:<providerFoodId>`. This decision does not authorize Open Food Facts. The Phase 3 exercise namespace `9439f2af-0e84-5e41-9482-d4b6765154ed` remains separate and frozen and must never derive Nutrition provider candidates.

Rationale:

Stable candidate IDs make cache, signed lookup, review, and future promotion flows deterministic across staging and production without exposing a secret or conflating Exercise and Nutrition identity domains.

## Decision 0024: USDA candidates use transient immutable log snapshots

Status: APPROVED / LIVE / VERIFIED / OWNER-ACCEPTED / FROZEN

Date: 2026-08-19

Decision:

A member may log a revalidated USDA candidate without promoting it to the canonical `foods` catalog. The resulting `food_log_items` row keeps `food_id = NULL` and `food_portion_id = NULL`, uses an explicit 100 g reference, accepts consumed grams only, and stores immutable server-generated nutrition, provider identity, candidate UUID, mapping version, source timestamps, derivation, attribution, and provenance snapshots.

The browser submits only a signed candidate token and normal log inputs to `nutrition-provider`. The Edge Function verifies the bearer user, verifies and resolves the candidate through trusted cache/lookup logic, and calls service-role-only `fmz_phase4_log_provider_food_item`. Editing uses a separate atomic `fmz_phase4_replace_provider_food_log_item`; browser archive-plus-readd emulation is forbidden. Existing `fmz_phase4_archive_food_log_item` remains the archive route. Provider RPC execution is revoked from `PUBLIC`, `anon`, and `authenticated` and granted only to `service_role`.

USDA serving portions, automatic canonical promotion, canonical `foods`/`food_portions`/`food_aliases` writes, frontend integration, and Open Food Facts remain outside this decision. Retry identity uses stable item/request UUIDs and exact payload comparison; changed-payload request reuse is rejected.

Rationale:

Transient snapshots let members log trusted provider nutrition without polluting the reviewed canonical catalog. A server-authoritative gram-only path keeps calculations auditable, prevents browser nutrient spoofing, preserves immutable history, and isolates canonical ingestion for a separate owner-reviewed pipeline.

## Decision 0025: Slice 4E canonical ingestion is ledgered and local search is alias-aware

Status: APPROVED / FOUNDATION AND 64-FOOD IMPORT LIVE / ACCEPTED / FROZEN

Date: 2026-08-21

Decision:

The first reviewed Dutch local canonical catalog import must be represented by a private `nutrition_food_ingestions` audit row. Reviewed/verified canonical foods and imported provider aliases link to that artifact. The ledger is RLS-enabled, has no browser or trainer policy/ACL, uses forward-only status transitions, and cannot be removed through a data workflow. Current import authority is a separately reviewed SQL artifact; no public ingestion RPC exists.

Canonical member visibility requires active reviewed/verified quality plus an ingestion link. Owned custom-food visibility remains unchanged. Active reviewed/verified aliases participate in the existing `fmz_phase4_search_foods(text,integer,text,uuid)` contract. The RPC ranks exact custom names, Dutch aliases, canonical names, prefixes, reviewed market relevance, and controlled trigram matches, deduplicates by food UUID, and preserves stable keyset pagination by recomputing the cursor food's rank from its UUID.

One active preferred Dutch alias per normalized alias and market is enforced explicitly. Raw/cooked foods and provider identities remain separate. The accepted first manifest locks 64 generic USDA foods, 197 aliases, 10 raw/cooked pairs, 9 preferred ambiguous Dutch aliases, and 0 portions. It uses pinned Foundation, Survey (FNDDS), and SR Legacy detail datasets, deterministic `usda_fdc:<fdcId>` UUIDv5 identities, and a one-transaction fail-on-drift seed. `Magere kwark`, `halfvolle kwark`, `skyr`, and Dutch product-specific breads remain explicit coverage gaps. The imported catalog is frozen. Open Food Facts, NEVO, further catalog mutation, and production remain outside this decision.

Rationale:

Artifact-level auditability and quality-gated visibility prevent unreviewed provider data from silently becoming canonical member content. Alias-aware local search makes the future Dutch catalog discoverable without introducing a second frontend flow or weakening custom-food ownership.

## Decision 0026: Open Food Facts remains a separate ODbL catalog domain

Status: APPROVED / SLICE 4F ARCHITECTURE LOCKED; MIGRATION NOT EXECUTED

Date: 2026-08-24

Decision:

Store Open Food Facts branded products in separate `nutrition_off_catalog_releases`, `nutrition_off_products`, and `nutrition_off_product_names` tables. Do not merge OFF rows into `public.foods` or `food_aliases`. Unified member search may combine typed result sets, but must preserve `off_branded_food`, `generic_food`, and `custom_food` identity.

Use permanent provider namespace `23440733-7e58-4c21-ad15-591eae6ab8ac` and exact identity name `open_food_facts:<normalized_gtin14>`. Validate EAN-8, UPC-A, EAN-13, and GTIN-14 check digits; retain the original barcode; keep `per_100_g` and `per_100_ml` separate. Only active complete/reviewed products are nutrition authority. Complete community data is not labelled FitMetZorge verified. Conflicts are quarantined rather than silently selected.

The OFF domain keeps ODbL 1.0 provenance, attribution, release hashes, and exportability. Product images remain optional separately licensed references and are not bulk downloaded. Authenticated clients receive read-only active catalog access; no trainer-special write route, browser service-role, automatic canonical promotion, barcode scanner, import, or production action is authorized by this decision.

## Decision 0027: Unknown barcodes use transient trusted OFF snapshots

Status: ACCEPTED / LOCAL IMPLEMENTATION REVIEWED / STAGING EXECUTION PENDING

An unknown local barcode does not mutate the pinned Open Food Facts release catalog and does not automatically become a private custom food. The server performs an exact OFF barcode lookup, validates exact GTIN identity, Dutch relevance, product/brand identity, an explicit `per_100_g` or `per_100_ml` basis, required bounded macros, revision, checksum and ODbL provenance, then signs a short-lived candidate under the permanent Phase 4 provider namespace using `open_food_facts:<normalized_gtin14>`.

The browser supplies barcode, normal meal controls and quantity only. It never supplies nutrition or licence authority. Trusted log and replace paths create immutable transient OFF snapshots with `food_id` and `food_portion_id` null, preserve g/ml separation, use existing request/object locks, stale guards, archive history and authoritative day totals, and never promote the scanned product into `nutrition_off_products`, `nutrition_off_product_names`, `nutrition_off_catalog_releases`, or `public.foods`. Historical same-product edits resolve the saved immutable snapshot server-side; a fresh signed candidate is required when changing to another transient OFF product. Camera frames remain local.

The accepted audit baseline is 106,650 Netherlands-associated source rows and 24,458 eligible products. A later pinned, deterministic, hash-reviewed import artifact and post-import verifier are mandatory before those rows may be loaded.

Rationale:

The separate domain keeps ODbL content technically and operationally distinguishable from CC0 USDA foods, private custom foods, immutable member logs, and proprietary FitMetZorge data. Typed local search still gives members one fast discovery surface without weakening provenance, licensing, quality, or future refresh controls.

## Decision 0028: App-wide visual redesign is one deferred design-system phase

Status: APPROVED / LOCKED / DEFERRED

Date: 2026-08-27

Decision:

Do not redesign individual tabs piecemeal during functional Phase 4 packages. The owner-approved future direction is a smoother, less static, premium, futuristic and more color-neutral application with layered surfaces and fluid interactions. That direction will be implemented later as one app-wide design-system and visual-polish phase across all member and trainer surfaces.

The future phase must define and apply shared design tokens, colors, surfaces, elevation, floating-card language, navigation, buttons, inputs, typography, spacing, animation, transitions, loading states, charts, modals and bottom sheets. Until that phase is explicitly started, focused functional packages may make only the minimum usability polish required by their acceptance criteria and must preserve the current frozen baselines.

Rationale:

A single shared visual system prevents inconsistent tab-by-tab styling, avoids repeated rework, and lets functionality, accessibility, mobile performance and regression safety remain the priority during current packages.

## Decision 0029: Phase 5 Progress uses normalized own-user revision history

Status: APPROVED / LIVE / TECHNICALLY VERIFIED ON STAGING

Date: 2026-08-31

Decision:

Use four additive own-user tables for Progress preferences, goals, weight and body measurements. Store kilograms and centimetres canonically, treat `user_settings.unit_system` as display preference only, validate local calendar dates against IANA timezone context, archive instead of deleting, and represent corrections as immutable superseding revisions. Browser writes use authenticated RPCs that derive ownership from `auth.uid()`; direct personal-table grants, broad trainer policies and client-supplied entitlement authority are forbidden.

Free receives the current local day plus 29 prior days. Only current active Pro, AI and personal-coaching entitlements receive full retained history. Missing, future, inactive or expired entitlement rows resolve to Free. Strength and consistency reuse frozen normalized Training sources; Recovery and Nutrition are descriptive context only. Running shows an explicit unavailable state until an authoritative source is reviewed.

Rationale:

One normalized revision model gives transparent history, safe retries, stale-write protection and later growth without rewriting legacy trainer workspaces or allowing presentation units to become competing data authority.

## Decision 0030: Progress photos require a separate private-media gate

Status: APPROVED / LOCKED / DEFERRED

Date: 2026-08-31

Decision:

The first normalized Phase 5 runtime contains no photo table, Storage bucket, file input or data-URL migration. A later photo package must separately review a private bucket, own-user object paths, RLS, signed access, optional consent, deletion and withdrawal, retention, trainer-access rules and independent AI-analysis opt-in. Legacy values are not destructively removed, but they are not promoted into the normalized member runtime.

Rationale:

Deferring media prevents an incomplete privacy architecture from becoming a production-shaped contract while allowing weight, measurements and derived progress to ship safely.

## Decision 0031: Phase 5 Progress is owner-accepted and frozen

Status: APPROVED / COMPLETE / OWNER-ACCEPTED / FROZEN

Date: 2026-09-01

Decision:

Freeze the normalized Phase 5 Progress member experience after owner real-phone acceptance of goals, weight, body measurements, graphs/trends, mobile layout, Dutch `Voortgang` naming, metric/imperial switching, immediate conversion, refresh persistence and restoration of correct metric values. Canonical storage remains kilograms and centimetres. Free Progress history remains 30 local days; current Pro, AI and personal-coaching entitlements receive full retained history. Nutrition keeps its separate frozen seven-day Free history.

Accepted runtime baselines are `cb1e926f7ecc567992f31f5107e785d293608932`, `eaac528030c44e7d0383121e3a7fc551ace4dee2` and `f96f9346174a636d71adb6fd1cd151d28c6c449b`; cache baseline is `20260901-phase5-unit-switch1`. Reopen Phase 5 only for a proven regression or a minimal compatible fix.

Rationale:

The technical, security, responsive and owner acceptance gates now pass, so the Progress domain can serve as a stable source for later authorized AI context without continued feature churn.

## Decision 0032: The Youri AI trial duration is 30 days

Status: APPROVED / PRODUCT CONTRACT LOCKED; LIFECYCLE IMPLEMENTATION REMAINS PHASE 7

Date: 2026-09-01

Decision:

The owner-locked AI trial is 30 days without payment details and does not auto-renew. Reminders occur seven days before expiry, one day before expiry and on the final day. On expiry, paid AI generation locks, the account falls back to its otherwise valid package or Free, and user data is retained. This decision supersedes older 7-day references.

Phase 6 may consume a current time-valid `ai` entitlement regardless of source. Phase 7 remains responsible for creating the trial entitlement, one-trial abuse prevention, reminders, expiry and subscription lifecycle behavior.

Rationale:

One explicit trial duration prevents contradictory entitlement, UX, test and cost assumptions while preserving the Phase 1 entitlement foundation and Phase 7 ownership of growth lifecycle logic.

## Decision 0033: Phase 6A AI trust, consent, budget, retention and safety contract

Status: APPROVED / PACKAGE 6A IMPLEMENTATION AUTHORIZED

Date: 2026-09-01

Decision:

Build Package 6A on staging as a provider-neutral trust foundation with no paid provider call. OpenAI is the future primary provider and `GPT-5.6 Luna` / `GPT-5.6 Terra` are product routing labels, but no real provider model identifier, key or call is activated in 6A. Private AI chat is never trainer-readable. AI processing and minimized trainer-summary sharing use separate versioned, affirmative, withdrawable consent.

Active-entitlement chat remains until member deletion. On entitlement loss, raw chat receives at most a 90-day grace period; reactivation inside the window restores access and expiry removes raw content. Internal per-user subscription-month operating cost is bounded at EUR 3 included, warning at 80 percent, at most EUR 1 Luna grace and an absolute EUR 4 stop; Terra stops before grace and there is no automatic member billing.

Automatic changes remain proposals under strict reversible allowlists. Normal training increases are capped at 20 percent, larger fatigue/deload reductions require an explicit safe reason, calorie changes are capped at the smaller of 10 percent and 300 kcal with sufficient new authoritative data, and compatible exercise replacement is mandatory. Serious or unclear health signals hard-stop automation without diagnosis, medication change or treatment advice.

Rationale:

An enforceable database/Edge trust boundary before provider activation prevents consent, entitlement, cost, safety, trainer privacy and stale/idempotency guarantees from being reduced to prompt text or browser state.
