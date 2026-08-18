# Phase 4 Nutrition Engine - Final Product Contract And Schema Slice 1 Design

Status: OWNER PRODUCT CONTRACT LOCKED - SCHEMA SLICE 1 MIGRATION CREATED / LOCAL REVIEW PASS - NOT EXECUTED

Last updated: 2026-08-18

Environment guard: staging project ref `mokxyyullfhkfalopbzd` only. Production project ref `hgoygcviutmynaihcvpd` remains forbidden.

This document remains the product/data contract. After separate explicit owner GO, the local migration, read-only post-migration checker, and static/security suite were created from it. No SQL was executed, no database changed, no frontend functionality or provider was implemented, nothing was deployed, and production was not touched.

## 1. Locked Free Contract

Free receives a useful self-service Nutrition foundation:

- One clear active daily calorie target.
- Active protein, carbohydrate, and fat targets.
- Canonical food search.
- Manual logging with no daily food-log item count limit.
- Daily kcal, protein, carbohydrate, and fat totals.
- Private custom foods, limited to 10 active rows per user.
- Seven local-calendar-day Nutrition history.

Free does not receive saved meals, saved recipes, favorites, meal/day copy, unlimited history, barcode, advanced analysis, or AI Nutrition functionality.

The seven-day history boundary and 10-active-custom-food boundary are server-authoritative. A hidden frontend control is not enforcement.

## 2. Locked Pro Contract

Pro receives the complete self-service Nutrition Engine:

- Unlimited normal food logging.
- Full retained Nutrition history, subject to the later retention policy.
- Full target management.
- Favorites and derived recent foods.
- Saved meals and own recipes.
- Meal copy and day copy.
- Richer adherence/progress presentation.
- Private custom foods without the Free product limit, subject to separately defined platform abuse limits.
- Barcode only when its later Phase 4 feature-flagged slice is approved.

## 3. Locked AI Contract

An active `ai` entitlement grants the full Pro Nutrition capability set. Capability order is `Free < Pro <= AI`.

This does not implement AI in Phase 4. Youri analysis, recommendations, coaching, and meal suggestions remain later-phase backend functionality. AI output can propose but never becomes the authoritative food log or silently changes active targets.

## 4. Locked PT Contract

An active `personal_coaching` entitlement grants full Pro/AI-level member Nutrition capability while the relationship/entitlement remains current.

The normalized model must later support trainer-assigned targets and meal plans plus reviewed adherence/log access. Slice 1 remains own-user-only and adds no trainer policy. A trainer must never rewrite completed historical intake. Relationship validation, trainer permissions, assignment workflow, and relationship-end behavior require a separate reviewed trainer slice.

## 5. Food-Source Contract

- Canonical identity is FitMetZorge/provider-neutral, not derived from one provider's identifier.
- Provider, provider row ID, source version, license/provenance metadata, quality status, and source update time are first-class data.
- Open Food Facts is the preferred future source for European packaged/barcoded products.
- USDA FoodData Central is the preferred future generic/reference fallback.
- NEVO is excluded until separate legal/license approval.
- No external API, provider key, import, or catalog seed belongs in Schema Slice 1.
- Credentialed/rate-controlled provider traffic must later use a secure backend/Edge Function, never the frontend.
- The 41 hardcoded foods and 44 local recipe templates are compatibility material, not automatically the commercial canonical catalog.

## 6. Custom-Food Contract

- Custom foods are private to `owner_user_id`.
- No community/public sharing.
- Minimum fields: name, reference amount/unit, kcal, protein, carbohydrates, and fat.
- Optional fiber and deterministic mass/volume/portion conversion fields are supported by the schema.
- Free may own at most 10 active custom foods.
- Pro, AI, and Personal Coaching are exempt from that product limit while their entitlement is active and time-valid.
- Archive rather than delete.
- Archived custom foods remain referenceable by historical snapshot rows.
- Limit enforcement covers insert, archived-to-active restore, and ownership/scope mutation attempts.
- A per-user advisory transaction lock prevents concurrent requests from exceeding 10.

## 7. Portion And Unit Contract

Supported consumption units are `g`, `ml`, `serving`, and `piece`.

- A food has one deterministic nutrient reference amount and unit.
- Direct mass/volume scaling is permitted only when the logged and reference units match.
- Mass-to-volume or volume-to-mass conversion requires explicit `density_g_per_ml` or an explicit portion conversion.
- `serving`/`piece` logging requires a matching reviewed portion conversion unless the food's own nutrient reference uses that same unit.
- Generic `1 liter = 1 kilogram` logic is forbidden.
- Each log item snapshots quantity, unit, reference basis, optional density/portion conversion, and calculated nutrients.

The logging RPC calculates snapshots from trusted food/portion rows. The browser does not supply authoritative macro results for a referenced food.

## 8. Target Authority Contract

Targets remain separate from food logs and meal plans.

Each target records:

- Target values.
- Source type: `member`, `calculator`, `trainer`, `future_ai_suggestion`, or `legacy_bridge`.
- Creator identity where applicable.
- Accepted-by and accepted-at state.
- Effective dates and superseded target.
- Visible source/authority metadata.

Initial Slice 1 exposes only a member-controlled active `daily` target. `training` and `rest` contexts exist as future-compatible schema values but are not automatically selected or exposed by initial UI.

There is no numeric hidden source priority. One row is explicitly active per user/context. Calculator or future AI output starts as a recommendation and cannot become active without accepted workflow. Future trainer assignment uses a separate reviewed workflow; it does not silently overwrite a member target.

## 9. Calculator Contract

- One deterministic calculation engine should later serve member and trainer contexts.
- Its output is a recommended target, not diagnosis or medical nutrition therapy.
- It never assumes weekend equals rest day.
- The user/trainer can review, accept, or edit according to entitlement and later trainer rules.
- Deterministic safety bounds, caution/escalation behavior, allowed inputs, calculation formula, validation, and disclaimer must be approved before calculator implementation.
- No medical-condition inference from unrelated data.

The unresolved calculator formula/safety policy does not block the structural target table, but it blocks calculator code and activation workflows.

## 10. Meal-Moment Contract

Initial accepted codes:

- `breakfast`
- `lunch`
- `dinner`
- `snacks`

The database stores a validated extensible code rather than a PostgreSQL enum. Initial RPCs accept only the four locked codes. Future pre-workout, post-workout, or custom moments can be added by a reviewed RPC policy change without replacing historical rows or changing the column type.

## 11. Food-Log And History Contract

`food_logs` is a daily container. `food_log_items` records actual consumed foods. Targets and plans are separate.

- One log per `(user_id, log_date)`.
- The log stores IANA timezone and offset snapshots.
- Items keep immutable food-name, brand, reference, calculation, nutrient, provider, and version snapshots.
- Catalog changes never rewrite past intake.
- Day totals are derived from active item snapshots, not a second mutable totals source.
- Item archive is supported; no DELETE policy.
- Stable item UUID and request UUID prevent duplicate-tap/retry duplication.
- Free history RPCs expose only today plus the previous six days in the user's stored valid timezone.
- Pro/AI/PT history RPCs allow cursor-paginated retained history with a bounded page size.
- Base logs/items are not directly selectable by `authenticated`; entitlement-aware read RPCs prevent trivial Free-history bypass.

## 12. Meal-Plan Contract

Meal plans are planned/advised intake, never actual intake. They are not part of Slice 1.

A later reviewed slice uses separate `nutrition_plans`, `nutrition_plan_meals`, and `nutrition_plan_items` objects with creator, assignee, publication/acceptance, option ordering, snapshots, status, and future trainer relationship validation. Logging a planned item creates actual immutable food-log snapshots. Editing a plan never rewrites completed logs.

## 13. Copy Contract

Meal copy for Pro/AI/PT defaults to add/merge. A stable operation UUID makes retry exactly-once.

Day copy behavior:

- Empty destination: confirm and copy transactionally.
- Non-empty destination: explicitly choose add, replace, or cancel.
- Never silently replace.
- Replacement is one transaction.
- The later copy slice must define an undo/recovery record or equivalent safe restoration before implementation.

Copy objects/RPCs are not part of Slice 1.

## 14. Barcode Contract

Barcode is a later Phase 4 slice behind `nutrition_barcode_enabled`.

It requires approved provider/license, backend/Edge Function mediation where required, entitlement checks, authentication, caching, rate limiting, provider-failure UX, manual fallback, and no browser secret. Barcode does not block search-first manual logging or Slice 1.

## 15. Legacy Compatibility

- Do not migrate, rewrite, remove, or clean `coach_workspaces.state` Nutrition in Slice 1.
- Keep legacy `nutritionPlan`, `foodLog`, goals, `trainerCalc`, and render compatibility.
- Do not seed the 41 foods or 44 recipes into normalized tables automatically.
- Do not dual-write legacy and normalized state without a separate consistency design.
- Do not add trainer RLS.
- Preserve profiles, trainer/client links, Auth, invite, reset, Phase 1, Phase 2, frozen Phase 3, and frozen Member UX.

## 16. Privacy And Pre-Production Gates

The schema carries ownership, source/provenance, timestamps, status, and archive fields so future export, deletion, and retention workflows remain possible.

Before production Phase 4 launch, require:

- Privacy/AVG and legal-basis review.
- Retention schedule.
- User export format and completeness test.
- Account deletion/anonymization workflow and FK review.
- Provider license and required attribution review.
- Processor/Edge Function/provider data-flow review.
- Nutrition/medical-safety wording review.

These are pre-production gates and do not block an empty additive staging schema review.

## 17. Schema Slice 1 Boundary

Slice 1 is one additive staging schema/security migration containing exactly these six tables:

1. `nutrition_preferences`
2. `foods`
3. `food_portions`
4. `nutrition_targets`
5. `food_logs`
6. `food_log_items`

It also contains the minimum indexes, constraints, RLS policies, ACLs, internal helpers/triggers, and typed member RPCs required for custom-food limits, targets, logging, snapshots, history entitlement, and idempotency.

It does not contain catalog rows, legacy backfill, saved meals, recipes, favorites, copy, nutrition plans, barcode, provider calls, calculator logic, trainer access, AI, frontend, or data cleanup.

## 18. Exact Proposed Columns And Types

### 18.1 `public.nutrition_preferences`

| Column | Type | Null/default | Contract |
| --- | --- | --- | --- |
| `user_id` | `uuid` | PK, not null | FK `profiles(id) on delete cascade` |
| `timezone_name` | `text` | not null, default `UTC` | 1-64 chars; RPC validates against `pg_timezone_names` |
| `created_at` | `timestamptz` | not null, default `now()` | Audit/export |
| `updated_at` | `timestamptz` | not null, default `now()` | Optimistic refresh |

### 18.2 `public.foods`

| Column | Type | Null/default | Contract |
| --- | --- | --- | --- |
| `id` | `uuid` | PK, not null | Stable client/canonical identity; no random text IDs |
| `owner_user_id` | `uuid` | nullable | FK `profiles(id) on delete cascade`; null only for canonical |
| `catalog_scope` | `text` | not null | `canonical` or `custom` |
| `canonical_slug` | `text` | nullable | Required for canonical; null for custom; max 180 |
| `name` | `text` | not null | 1-240 chars |
| `brand` | `text` | nullable | Max 160 chars |
| `barcode` | `text` | nullable | 4-32 digits; no numeric type |
| `source_provider` | `text` | not null | Provider-neutral code; custom uses `custom_user` |
| `provider_food_id` | `text` | nullable | Provider identity, max 240 |
| `source_version` | `text` | nullable | Max 120 |
| `license_code` | `text` | nullable | Max 120 |
| `provenance` | `jsonb` | not null, default `{}` | Attribution/source metadata only |
| `quality_status` | `text` | not null, default `pending` | `pending`, `community`, `user_entered`, `reviewed`, `verified` |
| `reference_amount` | `numeric(12,3)` | not null | Positive deterministic nutrient basis |
| `reference_unit` | `text` | not null | `g`, `ml`, `serving`, `piece` |
| `reference_mass_grams` | `numeric(12,3)` | nullable | Explicit conversion only |
| `reference_volume_ml` | `numeric(12,3)` | nullable | Explicit conversion only |
| `density_g_per_ml` | `numeric(12,6)` | nullable | Explicit density only |
| `energy_kcal` | `numeric(12,3)` | not null | Per reference amount, non-negative |
| `protein_grams` | `numeric(12,3)` | not null | Per reference amount, non-negative |
| `carbohydrate_grams` | `numeric(12,3)` | not null | Per reference amount, non-negative |
| `fat_grams` | `numeric(12,3)` | not null | Per reference amount, non-negative |
| `fiber_grams` | `numeric(12,3)` | nullable | Future-compatible, non-negative |
| `status` | `text` | not null, default `active` | `active` or `archived` |
| `source_updated_at` | `timestamptz` | nullable | Provider source time |
| `metadata` | `jsonb` | not null, default `{}` | Non-authoritative extension data |
| `created_at` | `timestamptz` | not null, default `now()` | Audit |
| `updated_at` | `timestamptz` | not null, default `now()` | Audit/conflict |
| `archived_at` | `timestamptz` | nullable | Must match archived status |

Structural numeric upper bounds prevent corrupt/extreme storage but are not medical recommendations. Calculator safety limits remain separate.

### 18.3 `public.food_portions`

| Column | Type | Null/default | Contract |
| --- | --- | --- | --- |
| `id` | `uuid` | PK, not null | Stable portion identity |
| `food_id` | `uuid` | not null | FK `foods(id) on delete cascade` |
| `label` | `text` | not null | 1-120 chars, e.g. one slice |
| `amount` | `numeric(12,3)` | not null, default `1` | Positive amount of `unit` |
| `unit` | `text` | not null | `serving` or `piece` |
| `equivalent_amount` | `numeric(12,3)` | not null | Positive conversion amount |
| `equivalent_unit` | `text` | not null | `g`, `ml`, `serving`, or `piece` |
| `is_default` | `boolean` | not null, default `false` | Max one active default per food |
| `sort_order` | `integer` | not null, default `0` | 0-1000 |
| `status` | `text` | not null, default `active` | `active` or `archived` |
| `metadata` | `jsonb` | not null, default `{}` | Provider/reference details |
| `created_at` | `timestamptz` | not null, default `now()` | Audit |
| `updated_at` | `timestamptz` | not null, default `now()` | Audit |
| `archived_at` | `timestamptz` | nullable | Must match archived status |

### 18.4 `public.nutrition_targets`

| Column | Type | Null/default | Contract |
| --- | --- | --- | --- |
| `id` | `uuid` | PK, not null | Stable target/version identity |
| `user_id` | `uuid` | not null | FK `profiles(id) on delete cascade` |
| `target_context` | `text` | not null, default `daily` | `daily`, `training`, `rest`; initial RPC only `daily` |
| `energy_kcal` | `numeric(8,2)` | not null | Structural safe-storage range |
| `protein_grams` | `numeric(8,2)` | not null | Non-negative |
| `carbohydrate_grams` | `numeric(8,2)` | not null | Non-negative |
| `fat_grams` | `numeric(8,2)` | not null | Non-negative |
| `fiber_grams` | `numeric(8,2)` | nullable | Future-compatible |
| `source_type` | `text` | not null | `member`, `calculator`, `trainer`, `future_ai_suggestion`, `legacy_bridge` |
| `created_by_user_id` | `uuid` | nullable | FK `profiles(id) on delete set null` |
| `status` | `text` | not null | `recommended`, `active`, `superseded`, `archived` |
| `effective_from` | `date` | not null | Local effective date |
| `effective_to` | `date` | nullable | Must not precede start |
| `accepted_by_user_id` | `uuid` | nullable | FK `profiles(id) on delete set null` |
| `accepted_at` | `timestamptz` | nullable | Explicit acceptance |
| `supersedes_target_id` | `uuid` | nullable | Self-FK `on delete set null` |
| `request_id` | `uuid` | not null | Unique per user for retry |
| `notes` | `text` | nullable | Max 500 chars |
| `metadata` | `jsonb` | not null, default `{}` | Non-authoritative extension data |
| `created_at` | `timestamptz` | not null, default `now()` | Audit |
| `updated_at` | `timestamptz` | not null, default `now()` | Audit/conflict |
| `archived_at` | `timestamptz` | nullable | Archive consistency |

### 18.5 `public.food_logs`

| Column | Type | Null/default | Contract |
| --- | --- | --- | --- |
| `id` | `uuid` | PK, not null | Stable day-log identity |
| `user_id` | `uuid` | not null | FK `profiles(id) on delete cascade` |
| `log_date` | `date` | not null | Local calendar date |
| `timezone_name` | `text` | not null | IANA snapshot, 1-64 chars |
| `timezone_offset_minutes` | `smallint` | not null | Between -840 and 840 |
| `target_id` | `uuid` | nullable | FK `nutrition_targets(id) on delete set null` |
| `target_energy_kcal_snapshot` | `numeric(8,2)` | nullable | Target shown for that day |
| `target_protein_grams_snapshot` | `numeric(8,2)` | nullable | Historical target snapshot |
| `target_carbohydrate_grams_snapshot` | `numeric(8,2)` | nullable | Historical target snapshot |
| `target_fat_grams_snapshot` | `numeric(8,2)` | nullable | Historical target snapshot |
| `target_fiber_grams_snapshot` | `numeric(8,2)` | nullable | Future-compatible snapshot |
| `status` | `text` | not null, default `active` | `active` or `archived` |
| `source` | `text` | not null, default `phase4_member` | Initial RPC fixes `phase4_member`; future `legacy_bridge` allowed only by reviewed migration |
| `metadata` | `jsonb` | not null, default `{}` | Non-authoritative extension data |
| `created_at` | `timestamptz` | not null, default `now()` | Audit |
| `updated_at` | `timestamptz` | not null, default `now()` | Audit |
| `archived_at` | `timestamptz` | nullable | Archive consistency |

### 18.6 `public.food_log_items`

| Column | Type | Null/default | Contract |
| --- | --- | --- | --- |
| `id` | `uuid` | PK, not null | Stable client item UUID |
| `user_id` | `uuid` | not null | FK `profiles(id) on delete cascade`; denormalized ownership guard |
| `food_log_id` | `uuid` | not null | FK `food_logs(id) on delete cascade` |
| `food_id` | `uuid` | nullable | FK `foods(id) on delete set null` |
| `food_portion_id` | `uuid` | nullable | FK `food_portions(id) on delete set null` |
| `meal_moment` | `text` | not null | Extensible code, max 40; initial RPC allows four locked values |
| `sort_order` | `integer` | not null | 0-10000, server assigned/validated |
| `consumed_quantity` | `numeric(12,3)` | not null | Positive |
| `consumed_unit` | `text` | not null | `g`, `ml`, `serving`, `piece` |
| `food_name_snapshot` | `text` | not null | 1-240 chars |
| `brand_snapshot` | `text` | nullable | Max 160 chars |
| `reference_amount_snapshot` | `numeric(12,3)` | not null | Calculation source |
| `reference_unit_snapshot` | `text` | not null | Calculation source unit |
| `portion_label_snapshot` | `text` | nullable | Selected serving/piece label |
| `portion_equivalent_amount_snapshot` | `numeric(12,3)` | nullable | Exact conversion |
| `portion_equivalent_unit_snapshot` | `text` | nullable | Exact conversion unit |
| `density_g_per_ml_snapshot` | `numeric(12,6)` | nullable | Used only when explicit |
| `calculation_basis` | `text` | not null | `direct_reference`, `portion_conversion`, `density_conversion` |
| `energy_kcal_snapshot` | `numeric(12,3)` | not null | Authoritative historical result |
| `protein_grams_snapshot` | `numeric(12,3)` | not null | Authoritative historical result |
| `carbohydrate_grams_snapshot` | `numeric(12,3)` | not null | Authoritative historical result |
| `fat_grams_snapshot` | `numeric(12,3)` | not null | Authoritative historical result |
| `fiber_grams_snapshot` | `numeric(12,3)` | nullable | Future-compatible result |
| `source_provider_snapshot` | `text` | not null | Historical provenance |
| `provider_food_id_snapshot` | `text` | nullable | Historical provenance |
| `source_version_snapshot` | `text` | nullable | Historical provenance |
| `provenance_snapshot` | `jsonb` | not null, default `{}` | Historical attribution metadata |
| `notes` | `text` | nullable | Max 1000 chars |
| `status` | `text` | not null, default `active` | `active` or `archived` |
| `request_id` | `uuid` | not null | Unique per user; duplicate retry returns original result |
| `consumed_at` | `timestamptz` | nullable | Optional actual time; date source remains `food_logs.log_date` |
| `metadata` | `jsonb` | not null, default `{}` | Non-authoritative extension data |
| `created_at` | `timestamptz` | not null, default `now()` | Audit |
| `updated_at` | `timestamptz` | not null, default `now()` | Audit/conflict |
| `archived_at` | `timestamptz` | nullable | Archive consistency |

## 19. Exact Constraints And Indexes

Required constraints/indexes in the later reviewed migration:

- Scope/owner consistency: canonical requires null owner and slug; custom requires owner, null canonical slug, and `source_provider = 'custom_user'`.
- Active/archive timestamp consistency on foods, portions, targets, logs, and items.
- Food reference/mass/volume amounts are `> 0 and <= 100000`; density is `> 0 and <= 100` g/ml.
- Food/item energy is `>= 0 and <= 1000000`; protein/carbohydrate/fat are `>= 0 and <= 100000`; nullable fiber uses the same non-negative macro bound.
- Target energy is `> 0 and <= 20000`; protein/carbohydrate/fat are `>= 0 and <= 2000`; nullable target fiber is `>= 0 and <= 500`. RPC-level product/calculator validation may be stricter.
- Portion and consumed quantities are `> 0 and <= 100000`.
- Barcode is null or 4-32 ASCII digits. Meal-moment codes match `^[a-z][a-z0-9_]{0,39}$`; initial write RPC allows only the four locked codes.
- `nutrition_targets_effective_range_check` and acceptance/source/status consistency.
- Unique `foods` canonical slug for canonical scope.
- Unique `(source_provider, provider_food_id)` when provider ID is present.
- Barcode lookup index without assuming provider-global uniqueness.
- Name/search indexes for active canonical and own custom foods; final text-search extension choice is reviewed with migration SQL.
- Unique active portion label per food and max one active default portion per food.
- Unique `(user_id, request_id)` on targets and food-log items.
- Unique one active target per `(user_id, target_context)`.
- Unique `(user_id, log_date)` on food logs.
- Item lookup/order index `(user_id, food_log_id, meal_moment, sort_order)` for active rows.
- Recent-food lookup `(user_id, created_at desc, food_id)` for active referenced rows.
- History index `(user_id, log_date desc)`.

No unique constraint may make archived reusable labels/orders impossible unless implemented as an active-row partial index.

## 20. Functions, Triggers, And Server Authority

Exact proposed internal helpers/triggers:

- `fmz_phase4_has_full_nutrition_access(uuid)`: internal `SECURITY DEFINER`; true only for current active `pro`, `ai`, or `personal_coaching` entitlement within starts/ends window.
- `fmz_phase4_enforce_custom_food_limit()`: trigger `SECURITY DEFINER`; `auth.uid()` ownership, immutable scope/owner, shared per-user advisory lock, 10-active Free count.
- `fmz_phase4_enforce_food_portion_owner()`: trigger relational guard; portion parent must be own custom food for member writes.
- `fmz_phase4_enforce_target_owner()`: trigger guard; no ownership/source escalation.
- `fmz_phase4_enforce_food_log_owner()`: trigger guard; ownership immutable.
- `fmz_phase4_enforce_food_log_item_owner()`: trigger relational guard; item user, day log, food visibility, and portion-food relation must agree.
- The migration uses the scoped internal `fmz_phase4_touch_updated_at()` helper so Slice 1 does not depend on or modify the legacy shared timestamp helper.
- `fmz_phase4_sync_archive_state()` keeps status and archive timestamp consistent.
- `fmz_phase4_day_payload(uuid, date)` is an internal read assembler used only behind entitlement-aware public RPCs.

All trigger-only/internal functions use `search_path = pg_catalog, public, pg_temp` and revoke direct execute from `PUBLIC`, `anon`, and `authenticated`.

Typed member RPC contract:

- `fmz_phase4_set_nutrition_timezone(p_timezone_name text)`.
- `fmz_phase4_search_foods(p_query text, p_page_size integer, p_after_name text, p_after_id uuid)` with bounded keyset pagination; `SECURITY INVOKER` over RLS-visible foods.
- `fmz_phase4_upsert_custom_food(p_food_id uuid, p_name text, p_brand text, p_reference_amount numeric, p_reference_unit text, p_reference_mass_grams numeric, p_reference_volume_ml numeric, p_density_g_per_ml numeric, p_energy_kcal numeric, p_protein_grams numeric, p_carbohydrate_grams numeric, p_fat_grams numeric, p_fiber_grams numeric, p_expected_updated_at timestamptz)`.
- `fmz_phase4_archive_custom_food(p_food_id uuid, p_expected_updated_at timestamptz)`.
- `fmz_phase4_upsert_food_portion(p_portion_id uuid, p_food_id uuid, p_label text, p_amount numeric, p_unit text, p_equivalent_amount numeric, p_equivalent_unit text, p_is_default boolean, p_expected_updated_at timestamptz)`.
- `fmz_phase4_save_member_target(p_target_id uuid, p_request_id uuid, p_energy_kcal numeric, p_protein_grams numeric, p_carbohydrate_grams numeric, p_fat_grams numeric, p_fiber_grams numeric, p_effective_from date)`; source and context are fixed server-side to `member`/`daily`.
- `fmz_phase4_get_current_nutrition_target()`.
- `fmz_phase4_log_food_item(p_item_id uuid, p_request_id uuid, p_log_date date, p_timezone_name text, p_timezone_offset_minutes smallint, p_meal_moment text, p_food_id uuid, p_food_portion_id uuid, p_consumed_quantity numeric, p_consumed_unit text, p_notes text, p_consumed_at timestamptz)`; server calculates snapshots.
- `fmz_phase4_archive_food_log_item(p_item_id uuid, p_expected_updated_at timestamptz)`; repeating archive is inherently idempotent and returns the archived row.
- `fmz_phase4_get_nutrition_day(p_log_date date)`.
- `fmz_phase4_get_nutrition_history(p_before_date date, p_page_size integer)` with server-clamped Free window and bounded Pro keyset pagination.

All member RPCs except the RLS-only search are `SECURITY DEFINER` because authenticated receives no direct privileges on the protected base tables. Their implementations must perform explicit Auth, ownership, entitlement, relationship, and input checks; RLS is defense-in-depth rather than being silently assumed inside owner-bypassing functions.

Every write/read RPC:

- Requires non-null `auth.uid()`.
- Derives `user_id` from Auth.
- Does not accept role, entitlement, trainer ID, or owner ID as authority.
- Uses typed scalar inputs and validates lengths/ranges before mutation.
- Uses one transaction and stable request identity.
- Returns authoritative database rows/totals.
- Gives truthful errors; no partial multi-row success.

## 21. RLS And Grants Design

RLS is enabled on all six tables. No DELETE policy and no trainer policy exists.

Policies:

- `nutrition_preferences_*_own`: own select/insert/update defense-in-depth.
- `foods_select_visible`: active canonical rows plus all own custom rows.
- `foods_insert_own_custom` and `foods_update_own_custom`: own custom only; retained as defense, while direct table write grant remains absent.
- `food_portions_select_visible`: active portions of an active canonical parent, plus all portions belonging to an own custom parent.
- `food_portions_insert_own_custom` and `food_portions_update_own_custom`: parent is own custom food.
- `nutrition_targets_*_own`, `food_logs_*_own`, and `food_log_items_*_own`: own select/insert/update defense-in-depth.

ACL contract:

| Object | `PUBLIC` | `anon` | `authenticated` |
| --- | --- | --- | --- |
| `foods` | none | none | `SELECT` only |
| `food_portions` | none | none | `SELECT` only |
| Preferences, targets, logs, items | none | none | no direct table privileges; RPC only |
| Public member RPCs | no execute | no execute | execute only |
| Internal/trigger functions | no execute | no execute | no execute |

Every table is explicitly `REVOKE ALL` from `PUBLIC`, `anon`, and `authenticated` before the minimum grants. This prevents inherited/default broad privileges such as DELETE, TRUNCATE, REFERENCES, TRIGGER, or MAINTAIN.

Entitlement-aware history cannot be bypassed through direct base-table SELECT because `authenticated` has no direct SELECT grant on targets/logs/items. Security-definer read RPCs must manually apply `auth.uid()` and entitlement/date checks.

## 22. Concurrency And Idempotency

- Custom-food insert/restore uses `pg_advisory_xact_lock(hashtextextended('fmz_phase4_custom_food_limit:' || auth.uid(), 0))` before entitlement/count checks.
- All routes that can activate a custom food use that exact namespace.
- Custom-food create/update/archive retries additionally serialize on stable `(user_id, food_id)` request identity; a creation retry without an optimistic timestamp succeeds only when its normalized payload exactly matches the existing active row.
- Custom portion upserts serialize per own custom food and use the stable portion UUID plus exact-payload replay to prevent duplicate-tap rows.
- Free counts only own rows with `catalog_scope = 'custom'` and `status = 'active'`.
- Pro/AI/PT is unlimited only with a current entitlement.
- Active-target replacement uses `pg_advisory_xact_lock(hashtextextended('fmz_phase4_nutrition_target:' || auth.uid() || ':daily', 0))`; duplicate request is checked first, then the prior active row is superseded and the new row is inserted in one transaction.
- Item `(user_id, request_id)` uniqueness makes duplicate logging retry return the same item.
- Target `(user_id, request_id)` uniqueness makes target-save retry return the same target version.
- Food/day creation and item creation happen in one logging RPC transaction.
- Logging serializes duplicate requests on `(user_id, request_id)` before the per-user/day lock; archive retries serialize on `(user_id, item_id)`.
- Client IDs are UUIDs produced once and retained across retries.
- No frontend-only debounce is treated as integrity or entitlement enforcement.

## 23. Rollback And Restoration Strategy

Before any future migration execution:

- Record read-only baseline metadata for profiles, workspaces, entitlements, Phase 2, and Phase 3.
- Confirm no conflicting Phase 4 objects exist.
- Review complete SQL and transaction wrapper.

Migration behavior:

- One transaction; failure rolls back all Slice 1 DDL.
- Additive objects only.
- No data seed/backfill.
- No change to legacy or Phase 1-3 rows/policies/functions.
- Frontend remains disabled/not deployed until live verification passes.

If empty schema verification fails before frontend use, a separately reviewed staging rollback may remove only the new empty Phase 4 objects in dependency order. Once any Nutrition rows exist, do not use blind rollback/drop: disable the Phase 4 frontend flag, export/reconcile affected rows, preserve snapshots, and apply a reviewed forward fix or restoration migration.

Applied migration files are append-only and are never silently rewritten after execution.

## 24. Read-Only Migration Verification SQL Design

The created post-migration checker is one SELECT/CTE-only query returning JSON with `overall_pass` and individual checks. It does not call app RPCs.

Required CTE/check groups:

1. Six exact tables present; no unexpected Phase 4 tables.
2. Exact columns, `data_type`/`udt_name`, nullability, defaults, precision, and scale. Integer precision metadata is normalized to avoid prior false negatives.
3. PK/FK/unique/check constraints and FK delete actions.
4. Exact indexes, keys, predicates, validity, and readiness. `name[]` is explicitly cast to `text[]` before comparison.
5. RLS enabled on all six tables.
6. Exact policies/commands/expressions; no DELETE or trainer-like policy.
7. Table ACLs via `information_schema.role_table_grants`; exact authenticated grants and no `anon`/`PUBLIC` grants.
8. Function existence, identity arguments, `prosecdef`, volatility, and safe `proconfig` search path.
9. Function ACLs through `pg_proc.proacl` plus `aclexplode`, treating grantee OID 0 as `PUBLIC`; no `has_function_privilege('PUBLIC', ...)` pseudo-role error.
10. Trigger existence/enabled/function links.
11. Function-source metadata checks for active/time-valid `pro`/`ai`/`personal_coaching`, 10 active custom foods, shared advisory-lock namespace, Free seven-day clamp, Auth ownership, and absence of weekend inference.
12. No barcode/provider network/AI/service-role/production/secret reference in Phase 4 object definitions.
13. All six new tables have row count zero immediately after schema-only execution.
14. Phase 1/2/3 and legacy guard objects still exist with RLS/expected relationship columns.

The checker avoids literal standalone mutating statements. Metadata function-definition text may contain SQL keywords and can still trigger a Supabase scanner warning; a warning-minimized version should inspect normalized `prosrc` patterns and clearly document that the outer query remains SELECT-only.

## 25. Static And Security Check Design

The current `assets/phase4-static-check.js` suite fails unless:

- Migration contains staging ref `mokxyyullfhkfalopbzd` and no production ref.
- Transaction starts/commits once.
- Exactly six approved tables are created.
- No seed rows, provider calls, backfill, legacy mutation, DROP, DELETE, or TRUNCATE.
- No Phase 1/2/3 table alteration.
- All six tables have RLS.
- No DELETE/trainer/public-sharing policy.
- ACL hardening revokes all three roles before minimum grants.
- Direct log/history/target SELECT is unavailable to authenticated.
- Public RPC execute is authenticated-only; internal functions are not executable.
- Security-definer functions use safe search path and `auth.uid()`.
- Current entitlement checks include Pro, AI, PT and exclude inactive/expired/future rows.
- Free custom-food limit is 10 active custom foods and uses the same advisory lock on insert/restore.
- Free history is seven local calendar days and cannot be widened by a client limit/cursor.
- No daily food-log item count limit exists.
- No generic liter-to-kilogram conversion exists.
- Snapshot columns and relation guards exist.
- Stable UUID/request uniqueness exists.
- No service role, secret, AI call, barcode integration, polling, MutationObserver, or reload workaround.
- Phase 1, Phase 2, frozen Phase 3, and Member UX suites remain unchanged and pass before any deployment.

## 26. Implementation Plan And Gates

1. Owner approves this final contract and Slice 1 design. COMPLETE.
2. Create one additive migration from this design only after explicit implementation GO. COMPLETE LOCALLY / NOT EXECUTED.
3. Run local SQL/static/security self-review; show full SQL to owner. LOCAL REVIEW COMPLETE / OWNER SQL REVIEW NEXT.
4. Perform external/final migration review.
5. Owner executes migration manually on staging only.
6. Owner runs the SELECT-only post-migration checker and returns full JSON.
7. Correct only verified schema/security blockers through a separately reviewed hardening migration if needed.
8. Prepare the first mobile frontend logging slice only after live database verification PASS and separate GO.
9. Seed/import canonical foods only after provider/catalog/license review; never as an implicit part of schema deployment.
10. Deploy frontend only after Phase 1/2/3/Member UX regression, mobile, i18n, security, and performance checks.
11. Run owner tests for Free/Pro/AI/PT boundaries, 10-custom limit, seven-day history, date isolation, snapshots, duplicate retry, and existing flows.

## 27. Remaining True Blockers

No unresolved product decision blocks creation of the reviewed empty Slice 1 migration after explicit owner GO.

Remaining blockers apply to later work:

- Calculator formula, safety bounds, caution/escalation, and disclaimer block calculator implementation.
- Provider/catalog/license approval blocks food import and external search/barcode integration.
- Normalized trainer-client authorization blocks trainer assignment/adherence access.
- Day-replacement undo/recovery design blocks day-copy implementation.
- Exact platform abuse ceilings block the final unlimited-tier operational policy, but not the Free product limit.
- Privacy/retention/export/deletion/legal review blocks production Phase 4 launch, not staging schema review.

## 28. Design Readiness

Final product contract: LOCKED.

Schema Slice 1 design: LOCKED.

Migration: `supabase/migrations/20260818_phase4_nutrition_schema_slice1.sql` - CREATED / LOCAL REVIEW PASS / NOT EXECUTED. SHA-256: `D70A589FEF997C14FCC9805E746536C86556E22622C8952B33DE9CA222B36188`.

Post-migration checker: `supabase/verification/20260818_phase4_nutrition_schema_slice1_verification.sql` - HARDENED / SELECT-ONLY / NOT EXECUTED. SHA-256: `D77AD4EBE0FE194F1AC73F297C1855A5B34FDEEEABAC44FCDF28B5C5E244D485`.

Static/security suite: `assets/phase4-static-check.js` - CREATED / PASS.

Next gate: owner/external migration review before any manual staging execution.
