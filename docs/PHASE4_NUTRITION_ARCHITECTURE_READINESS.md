# Phase 4 Nutrition Engine - Architecture And Readiness Audit

Status: ARCHITECTURE AUDIT COMPLETE - OWNER PRODUCT CONTRACT LOCKED - SLICE 1 MIGRATION EXECUTED ON STAGING / CORRECTED VERIFICATION PENDING RERUN

Last updated: 2026-08-18

Environment guard: staging project ref `mokxyyullfhkfalopbzd` only. Production project ref `hgoygcviutmynaihcvpd` was not connected to or changed.

## 1. Audit Mandate

This document records the documentation-only Phase 4 architecture and readiness audit. It defines what exists, what must remain compatible, the proposed normalized target, security and entitlement boundaries, implementation slices, tests, and the owner decisions required before implementation.

The audit itself did not change runtime or a database. After separate explicit owner GO and review, the additive Slice 1 migration executed successfully on staging `mokxyyullfhkfalopbzd`. The first read-only verification run passed all checks except an index metadata reconstruction check; that checker false negative has been corrected locally and awaits owner rerun. No food data was imported, no food API was connected, no frontend was changed, and no deployment or production change occurred.

The owner resolved the Phase 4 product decisions on 2026-08-18. The final contract and exact first additive schema-slice design are recorded in `docs/PHASE4_NUTRITION_PRODUCT_CONTRACT_SCHEMA_SLICE1.md`.

Authoritative product rules:

- Member Nutrition is mobile first: phone primary, tablet secondary, desktop compatible.
- Member surfaces follow `Overview First, Details On Demand`.
- The Phase 1 entitlement foundation is the only approved entitlement source for Phase 4.
- Phase 1, Phase 2, frozen Phase 3 Training, and frozen Member UX remain regression baselines.
- Consumer Nutrition excludes invoices.
- Phase 4 does not implement Youri AI. It only leaves an authorized future integration boundary.
- Current trainer/client and legacy Nutrition data must remain available until an accepted migration or compatibility route exists.

## 2. Current Nutrition Inventory

### 2.1 Current Runtime And UI

The current Nutrition experience is implemented in the legacy application bundle and page markup. It combines member and trainer behavior in one surface.

Existing behavior includes:

- A hardcoded `PRODUCTS` list of 41 foods with kcal, protein, carbohydrates, and fat per 100 grams.
- A local deterministic collection of 44 recipe templates.
- Five fixed meal moments: breakfast, snack, lunch, dinner, and late snack.
- Trainer-created nutrition-plan rows with free-text ingredients and macro snapshots.
- Plan publishing to a linked client through a `published` boolean.
- Client plan-adherence states such as eaten as planned, different, or not eaten.
- A free-text note and macro snapshot in the legacy food log.
- A trainer macro scratch calculator stored as workspace-level `trainerCalc` state.
- Copying nutrition plans between legacy clients by cloning JSON and generating new local IDs.

The visible recipe generator is labelled as trainer AI, but it performs deterministic local template calculations. It makes no AI request and must not be represented as actual AI in the normalized product.

### 2.2 Current Legacy Data Source

Nutrition has no normalized Phase 4 database tables. Its durable source is the JSONB document in `coach_workspaces.state`:

- Per client: `goals.kcalTraining`, `goals.kcalRest`, `goals.protein`, `goals.carbsTraining`, `goals.carbsRest`, and `goals.fat`.
- Per client: `nutritionPlan[]` with local/random IDs, meal type, free-text items, kcal/macros, schema name, publication state, and weekly adherence/alternative state.
- Per client: `foodLog[]` with local/random IDs, date, meal type, plan-meal link, adherence status, note, and macro snapshots.
- Per workspace: `trainerCalc[]`.

The current client is linked through the existing Auth/profile/workspace chain. Current workspace policies permit a linked client to update the workspace document. Phase 4 must not extend this whole-workspace write pattern into the normalized Nutrition domain.

### 2.3 Current Calculation Behavior

- Food macros are calculated proportionally from the hardcoded per-100-gram values.
- Liter input is currently treated as 1 liter = 1,000 grams for every product. That is not a safe general density rule.
- Totals use JavaScript floating-point addition without a documented storage/rounding contract.
- The current daily kcal target assumes Saturday and Sunday are rest days. There is no accepted schedule rule supporting that assumption.
- A planned meal contributes its macro snapshot only when marked eaten as planned.
- Historical rows do not carry an auditable food-source version or nutrient provenance.

### 2.4 What Must Be Preserved

Until a reviewed cutover is accepted, preserve:

- Legacy trainer-created nutrition plans and client visibility.
- Legacy food-log/adherence history.
- Existing goals and macro values.
- Existing trainer/client relationships and workspace access.
- Existing Auth, invite, reset, and session flows.
- Legacy recipe/macro behavior needed to render stored data.

No legacy Nutrition cleanup, destructive rewrite, or blind backfill belongs in the first Phase 4 slice.

## 3. Gap And Risk Assessment

The current model is not suitable as the long-term commercial source of truth because:

- A whole trainer workspace is rewritten for small client Nutrition changes.
- Nutrition rows lack stable database UUID ownership and relational constraints.
- Current workspace access has a broader write surface than a dedicated own-user table design.
- The 41-food list has no recorded source, license, version, barcode, brand, serving, or data-quality status.
- There is no scalable food search, barcode lookup, favorite, recent-food, custom-food, saved-meal, persistent-recipe, or copy-day contract.
- Targets have no effective date or version history.
- History can change meaning when mutable food data changes because item snapshots and provenance are incomplete.
- Random local IDs and multi-step JSON writes do not provide idempotent retry guarantees.
- Entitlements are not server-enforced for Nutrition writes or premium read models.
- Trainer, member, and future AI responsibilities are mixed.
- The weekend/rest-day and liter/gram assumptions can produce incorrect guidance.
- The current UI is not a complete NL/EN/DE Phase 4 experience.

These are architecture gaps, not permission to discard working legacy data.

## 4. Required Product Entitlement Model

| Capability | Free | Pro | AI entitlement | Personal Coaching/PT |
| --- | --- | --- | --- | --- |
| Useful Nutrition engine | Targets, canonical search, unlimited normal daily logging, totals | Included | Full Pro Nutrition | Full member Nutrition |
| kcal/protein/carbs/fat tracking | Included | Included | Included | Included |
| History | Seven local calendar days | Full retained history | Full retained history | Full retained history |
| Custom foods | Maximum 10 active, private | No Free product cap; abuse controls apply | Same as Pro | Same as Pro |
| Favorites and recents | Not included | Included | Included | Included |
| Saved meals, recipes, copy meal/day | Not included | Included | Included | Included |
| Barcode | Not entitled | Later, only when feature flag is enabled | Later, only when feature flag is enabled | Later, only when feature flag is enabled |
| Youri-generated Nutrition support | Not Phase 4 | Not included without AI entitlement | Deferred to Phase 6 | Deferred to Phase 6 with trainer-priority rules |
| Trainer-assigned normalized plans | Not Phase 4 initial own-user slice | Not Phase 4 initial own-user slice | Not an AI right | Future reviewed linked-client slice |

Server entitlement evaluation must use `public.entitlements` and accept only current rows:

- `status = 'active'`.
- `starts_at` is null or not in the future.
- `ends_at` is null or in the future.
- Missing, inactive, expired, or future-only entitlement rows produce safe Free behavior.
- A browser-supplied plan, role, owner ID, premium boolean, or feature name is never trusted.

The existing frontend package-derived entitlement helper is a compatibility display model, not sufficient authorization for Phase 4.

## 5. Proposed Normalized Data Architecture

Table names below are design targets, not created objects.

### 5.1 Core Logging And Targets

`nutrition_targets`

- Versioned target records owned by `user_id`.
- Effective date range and explicit target mode, such as default, training, or rest.
- kcal, protein, carbohydrates, and fat stored as constrained PostgreSQL `numeric` values.
- Source such as member, system, legacy, or future trainer assignment; creator recorded separately.
- Archived/superseded state rather than destructive deletion.
- No automatic weekend-to-rest mapping.

`food_logs`

- One day container per `(user_id, log_date)`.
- Local calendar date plus timezone snapshot; no UTC conversion may silently select another day around midnight.
- Optional target/version snapshot and day-mode choice.
- Status and timestamps.

`food_log_items`

- Stable client-generated UUID plus database ownership.
- Parent day log, meal moment, ordering, quantity, unit, notes, and archive status.
- Nullable canonical/custom food reference plus immutable name, serving, nutrient, source, and provenance snapshots.
- kcal/protein/carbohydrates/fat snapshots are the historical source of truth.
- Unique request/idempotency key where a retry could otherwise duplicate a row.

Day totals are derived from non-archived item snapshots. A second mutable totals table is not proposed as a source of truth. A bounded SQL aggregate or trusted summary read model may be introduced only after measurement proves it necessary.

### 5.2 Food Catalog And Personal Food Data

`foods`

- One canonical interface for curated global and member-custom foods.
- `catalog_scope` distinguishes global from custom; custom rows require `owner_user_id = auth.uid()`.
- Provider/source ID, barcode, name, brand, reference amount/unit, nutrient values, optional serving/density data, source version, license/attribution, quality status, metadata, and active/archive timestamps.
- Global rows are read-only to normal authenticated users.
- Member custom rows are visible and mutable only by their owner.
- No unsafe ml-to-gram conversion when density is unknown.

`food_favorites`

- Own-user relation to a visible food.
- Unique `(user_id, food_id)`.

Recent foods should initially be derived from indexed `food_log_items`, not duplicated in a separate mutable table.

### 5.3 Reusable Meals And Recipes

`saved_meals` and `saved_meal_items`

- Reusable personal meal composition with ordered item snapshots and optional food references.
- Archive instead of delete.
- Copying a saved meal to a day is transactional and idempotent.

`recipes` and `recipe_items`

- Personal recipe, serving count, localized/member-entered instructions, ordered ingredients, nutrient snapshots, source/provenance, and archive state.
- Recipes are not public by default.
- The legacy deterministic templates may remain a compatibility/reference input only after their food values and ownership are reviewed; they are not AI.

### 5.4 Nutrition Plans And Multiple Options

`nutrition_plans`, `nutrition_plan_meals`, and `nutrition_plan_items`

- Separate a reusable plan from meal moments and their food/item options.
- Support multiple options without embedding unbounded JSON.
- Record owner/assignee/creator distinctly for future trainer assignment.
- Initial Phase 4 policies remain own-user only unless a separate trainer relationship design is approved.
- No public sharing policy.

### 5.5 Idempotent Multi-Row Commands

Multi-row operations such as copy meal, copy day, save recipe to log, and create plan use reviewed transactional RPCs. A small `nutrition_mutation_requests` ledger may record `(user_id, request_id, operation, status, result_reference)` if destination uniqueness alone cannot prove exactly-once behavior.

Each write contract must:

- Derive owner from `auth.uid()`.
- Accept a stable `request_id`/UUID, not generate time/random IDs in the browser.
- Perform validation and all row writes in one transaction.
- Return the authoritative result on retry.
- Use unique constraints to prevent duplicate items.
- Reject stale updates using `updated_at` or an explicit version when conflict matters.
- Archive rather than silently remove history.

## 6. Macro And Target Correctness Contract

- Store nutrient amounts as `numeric`, with database checks for finite non-negative values and documented upper bounds.
- Store source energy as supplied; do not blindly recalculate kcal as 4/4/9 because provider energy may include fiber, polyols, alcohol, or provider-specific rules.
- Define canonical reference amount and unit for every food.
- Convert volume only when reviewed density or source serving conversion exists.
- Preserve nutrient snapshots on logs, saved meals, recipes, and assigned plans so catalog updates do not rewrite history.
- Keep storage precision separate from display rounding.
- Apply the selected local calendar date directly and retain timezone context.
- Make training/rest/default target selection explicit until a reviewed schedule mapping exists.
- Any target calculator requires a separately reviewed evidence, safety, validation, and disclaimer contract. The current scratch macro calculator is not a complete calorie-target engine.

## 7. Security And RLS Architecture

Required baseline for every Phase 4 table:

- RLS enabled and forced where appropriate after Supabase compatibility review.
- `PUBLIC` and `anon` have no table privileges.
- `authenticated` receives only the exact operations needed.
- Own-user policies compare database ownership to `auth.uid()`.
- Parent/child policies verify relational ownership, not only a client-supplied parent ID.
- No DELETE policy; use explicit archive state.
- No broad trainer policy in the initial member slice.
- No service-role or provider secret in frontend code.

Premium protection cannot rely on hidden controls or RLS alone. RLS controls rows, not conditional visibility of premium columns. If Free users must not read full macros, the design must expose an entitlement-aware read RPC/view and revoke direct reads that would bypass it.

Trusted write functions must use safe `search_path`, reject cross-user IDs, evaluate current entitlements server-side, validate every parent relation, and expose `EXECUTE` only to the intended role. Trigger-only functions must not be directly executable by `PUBLIC`, `anon`, or `authenticated` unless technically required and reviewed.

Barcode/provider lookups must run through a trusted backend or Edge Function with authentication, entitlement, feature-flag, rate-limit, caching, and response validation. Provider keys must never enter the browser.

## 8. Legacy And Trainer Compatibility Strategy

The first normalized member slice must not mutate `coach_workspaces.state`. Legacy data remains a read-only compatibility source until a separately reviewed transition.

Safe sequence:

1. Inventory and count legacy Nutrition rows in staging without personal-data export.
2. Add normalized own-user schema and policies only after migration review.
3. Keep legacy render paths available for existing linked clients.
4. Introduce normalized member logging without rewriting legacy plans/history.
5. Decide how linked/PT clients transition before enabling normalized trainer assignment.
6. Rehearse any mapping with stable legacy-to-normalized IDs and reconciliation reports.
7. Keep a rollback/read fallback until owner acceptance.
8. Never delete legacy data as part of Phase 4 rollout.

The current policy allowing a linked client to update the workspace JSON must not become the authorization basis for new normalized tables. Trainer access should eventually depend on a reviewed normalized relationship model and strict linked-client RLS, aligned with Phase 9. The transition choice is an owner decision because it affects when PT clients receive the normalized Nutrition engine.

## 9. Food Data Source Assessment

### Open Food Facts

Useful for European branded products and barcodes. Its official API guidance describes community-contributed data, license/attribution obligations, rate limits, and a recommendation not to implement search-as-you-type against the search API. A commercial implementation therefore needs a provider adapter, validation, attribution, caching, pagination, and honest data-quality status. It should not be queried directly from every browser keystroke.

Official references:

- [Open Food Facts API documentation](https://openfoodfacts.github.io/openfoodfacts-server/api/)

### USDA FoodData Central

Useful as a public-domain generic-food and nutrient source. The official API requires a key and documents request limits; the key belongs in a trusted backend. Official downloadable datasets can support a curated import, but a full branded-food import is too large and operationally unnecessary for the first Phase 4 release.

Official references:

- [FoodData Central API guide](https://fdc.nal.usda.gov/api-guide/)
- [FoodData Central downloads](https://fdc.nal.usda.gov/download-datasets/)

### NEVO/RIVM

Relevant for Dutch foods, but the official download and copyright terms require attribution and usage-condition review. The published conditions create a potential commercial-product conflict that must receive legal/owner approval before NEVO data is imported or exposed as part of a paid Nutrition product.

Official references:

- [NEVO download](https://www.rivm.nl/nederlands-voedingsstoffenbestand/gebruik-nevo-online/download-bestand)
- [NEVO conditions for use 2025](https://www.rivm.nl/documenten/voorwaarden-voor-gebruik-nevo-online-2025)
- [NEVO copyright and disclaimer](https://www.rivm.nl/nederlands-voedingsstoffenbestand/gebruik-nevo-online/copyright-en-disclaimer)

### Locked Technical Direction And Later Import Gate

- Provider-neutral `foods` schema with explicit provenance and source version.
- Curated generic foundation rather than an unreviewed bulk import.
- Server-side, cached Open Food Facts barcode/product enrichment if approved.
- USDA generic-food fallback/curation if approved.
- NEVO only after legal review.
- Member custom food as an always-available fallback when a product is absent.
- No remote API dependency for reading an already-logged historical item.

The provider-neutral architecture and future Open Food Facts/USDA roles are locked. The exact imported launch catalog, provider terms, attribution UX, operational budget, and license review remain mandatory gates before any external data import. NEVO remains excluded until separate legal approval.

## 10. Performance And 1,000+ User Readiness

The target is feasible for 1,000+ users without premature partitioning when bounded queries and indexes are designed first.

Required indexes include:

- `food_logs (user_id, log_date desc)` with unique day ownership.
- `food_log_items (user_id, food_log_id, meal_moment, sort_order)` and recent-food lookup by user/date.
- `nutrition_targets (user_id, effective_from desc, status)`.
- `foods` unique provider/source ID and barcode rules, normalized-name search index, and scope/status filtering.
- Favorites, saved-meal, recipe, and plan parent/ordering indexes.

Runtime rules:

- Fetch one day and its bounded items in one composed request/read model.
- Paginate food search and history; never render or hydrate an entire catalog/history.
- Debounce search locally, but do not use polling or DOM-wide observers.
- Cache provider responses server-side and apply per-user/provider rate limits.
- Avoid N+1 food lookups by returning the required snapshots with each item.
- Load details on demand on phone; do not block the Nutrition overview on recipes/history.
- Measure slow queries, provider failures, cache hit rate, duplicate/retry conflicts, and save latency.
- Define backup, restoration, retention, export, and deletion procedures before production.

## 11. Future Youri AI And Trainer Boundaries

Phase 4 stores structured Nutrition data that later phases can use, but performs no AI calls.

Future Youri AI integration in Phase 6 must:

- Run backend-mediated only.
- Check active AI entitlement before each paid call.
- Retrieve the minimum authorized target/log context.
- Distinguish observation, proposal, and applied change.
- Never silently change calories or macros.
- Respect trainer priority for active PT clients.
- Log cost/rate-limit metadata without unnecessary health data.

Future trainer integration must:

- Require a verified active trainer-client relationship.
- Give a trainer access only to explicitly linked clients.
- Keep private trainer/Copilot material invisible to clients.
- Record creator, assignee, publication, and approval state.
- Avoid broad trainer policies and cross-trainer access.
- Preserve member history if a coaching relationship ends.

## 12. Reviewable Implementation Slices

This audit did not itself authorize a slice. A later explicit owner GO authorized only local creation and review of Slice 1; execution and feature implementation remain unauthorized.

### Slice 0 - Locked Contract And Preconditions

The Free/Pro/AI/PT, privacy, source, target, logging, copy, and linked-client boundaries are locked. The exact Schema Slice 1 design is approved; the created full migration SQL still requires owner/external review before any staging execution.

### Slice 1 - Normalized Schema And Security Foundation

Prepare one reviewed additive staging migration containing only Nutrition preferences, provider-neutral foods, food portions, member daily targets, day logs, log items, constraints, indexes, grants, RLS, and the minimum trusted RPC contracts. Saved meals, recipes, nutrition plans, copy, barcode, trainer access, AI, and catalog rows remain later slices. Execute manually only after SQL review, then run read-only live verification. No frontend deployment in the migration step.

### Slice 2 - Curated Foods, Search, And Custom Foods

Implement the approved provider-neutral catalog, paginated search, provenance display contract, and own-user custom foods. No barcode yet unless separately approved.

### Slice 3 - Mobile Day Logging, Targets, And Totals

Build the phone-first overview, meal moments, detail entry, correct macro snapshots/totals, date isolation, target selection, and the approved Free/Pro gate.

### Slice 4 - Favorites, Recents, Saved Meals, And Recipes

Add reusable content and transactional application to a day while preserving history and entitlement rules.

### Slice 5 - History, Copy Meal/Day, Offline Retry

Add bounded history, approved copy semantics, conflict handling, idempotent retries, and poor-connection behavior.

### Slice 6 - Barcode Behind Feature Flag

Add `nutrition_barcode_enabled`, backend provider adapter, entitlement enforcement, cache/rate limits, camera/manual-code UX, and unavailable-product fallback.

### Slice 7 - Linked/PT Compatibility And Trainer Transition

Execute only the owner-approved transition strategy. Do not add broad trainer access. Any legacy data mapping requires its own read-only precheck, reviewed migration/backfill, reconciliation, and rollback plan.

### Slice 8 - Phase 4 Exit Gate

Complete security, correctness, mobile, i18n, performance, regression, restoration, live staging, and owner tests. Phase 4 remains incomplete until the full gate passes.

## 13. Test And Exit-Gate Design

### Database And Security

- Exact tables, columns, types, checks, PK/FK/unique constraints, indexes, triggers, and functions.
- RLS enabled; exact policies and least-privilege grants.
- `anon`/`PUBLIC` blocked; no DELETE policy; no broad trainer policy.
- Cross-user parent/child IDOR attempts rejected.
- Direct table/RPC attempts cannot spoof owner, role, entitlement, target, or premium capability.
- SECURITY DEFINER attack surface, `auth.uid()`, `search_path`, ACL, and malformed JSON/numeric input reviewed.

### Entitlements

- Free, Pro, AI-only, PT, missing, inactive, expired, and future entitlement cases.
- UI and direct API behavior match the same server decision.
- Barcode requires both entitlement and feature flag.
- No AI call occurs in Phase 4.

### Nutrition Correctness

- Gram, serving, and approved volume conversions.
- Decimal quantity and rounding boundaries.
- Provider kcal and all four macro snapshots/totals.
- Catalog updates do not rewrite historical logs.
- Explicit training/rest/default target behavior; no weekend assumption.
- Local date isolation around DST/midnight and timezone change.
- Custom food validation and provenance.
- Copy meal/day merge/replace behavior and undo, after owner decision.
- Retry after interrupted multi-item writes creates no duplicates or partial copies.

### Member UX And Accessibility

- Real phone first at representative 390x844 and narrow-phone 320x700 sizes.
- Tablet secondary; desktop compatibility.
- `Overview First, Details On Demand`, stable controls, no horizontal overflow.
- Search pagination, loading, empty, offline, provider-error, validation, and retry states.
- NL/EN/DE labels, errors, units, meal moments, and date/decimal behavior.
- Free locked states are clear without exposing premium data.
- Invoices are absent from consumer Nutrition.

### Regression And Performance

- Phase 1 Auth/onboarding/settings/entitlements and invite/reset flows.
- Phase 2 Vandaag/Recovery/Trackers/date isolation/logout.
- Frozen Phase 3 Training, UUID/history/PR, Free max-4, Exercise Picker, 898 catalog.
- Frozen Member UX composition and onboarding hydration.
- Legacy trainer/client Nutrition remains readable until accepted replacement.
- No polling, MutationObserver, repeated full hydration, N+1 food loads, or listener accumulation.
- Load tests cover catalog search, day hydration, transactional writes, history pagination, and provider rate/error behavior at the 1,000+ user target.

### Required Exit Gate

Phase 4 can be marked complete only when:

- The approved Free/Pro/AI/PT contract is server-enforced.
- Macro and target calculations pass reviewed correctness tests.
- Own-user isolation, grants, RLS, and direct-API abuse tests pass live staging verification.
- Food-source provenance/license rules are satisfied.
- Retry/copy operations are idempotent and date-safe.
- Phone-first NL/EN/DE owner tests pass.
- Legacy linked-client Nutrition remains preserved or an accepted migration has passed reconciliation.
- Phase 1/2/3 and Member UX regression suites pass.
- Rollback/restoration or forward-fix instructions exist for every persistent change.
- No production resource has been touched.

## 14. Owner Product Contract Lock

Resolved on 2026-08-18:

- Free: targets, canonical search, unlimited normal daily logging, totals, 10 active custom foods, and seven-day history.
- Pro: complete self-service Nutrition, full retained history, favorites, recents, saved meals, recipes, meal/day copy, and later barcode.
- AI: all Pro Nutrition; no AI implementation in Phase 4.
- PT: full member Nutrition plus future reviewed trainer assignment/adherence access; no trainer policy in Slice 1 and no historical-log rewriting.
- Provider-neutral foods; future Open Food Facts packaged/barcode role, USDA generic fallback, and no NEVO commercial integration before legal approval.
- One initial explicit daily target; no weekend/rest inference.
- Four initial meal moments: breakfast, lunch, dinner, snacks.
- Actual log, target, and meal plan remain separate.
- Historical nutrient/provenance snapshots are immutable.
- Meal copy adds/merges and is idempotent. Non-empty day copy requires add/replace/cancel; never silent replacement.
- Custom foods, saved meals, and recipes are private; no community sharing.
- Barcode remains a later feature-flagged slice.
- Privacy/retention/export/deletion and provider-license review are mandatory before production.

Remaining gates do not block the empty Slice 1 schema design. They block only calculator code, provider import/API work, trainer access, day-copy implementation, operational abuse ceilings, or production launch as documented in the final product contract.

## 15. Readiness Conclusion

Architecture readiness: PASS - OWNER PRODUCT CONTRACT LOCKED.

The existing system and legacy constraints are sufficiently understood. Schema Slice 1 is designed, the local migration/security artifacts have been created after explicit owner permission, and local review is complete. Migration execution still requires separate owner approval and must be followed by live read-only staging verification.

No migration has been executed and no feature code has been created. The local SQL/checker artifacts are review material only.
