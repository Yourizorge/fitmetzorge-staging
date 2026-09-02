# FitMetZorge Architecture

Status: CURRENT AND TARGET ARCHITECTURE DOCUMENTED
Last updated: 2026-08-15

## Environment Boundary

Staging and production are permanently separate.

- Staging Supabase project ref: `mokxyyullfhkfalopbzd`.
- Production Supabase project ref: `hgoygcviutmynaihcvpd`.
- Production is strictly forbidden without explicit owner approval.
- This architecture document does not authorize code, database, Supabase, Auth, Edge Function, SMTP, deployment, or production changes.

## CURRENT ARCHITECTURE

The current staging application is a static frontend application built with plain HTML, CSS, and JavaScript.

The current root files include:

- `index.html` as the main static entrypoint.
- `styles.css` for application styling.
- `config.js` for public Supabase configuration.
- `app.js` as a staging launcher that loads and rewrites `app.bundle.js` at runtime.
- `app.bundle.js` as the main monolithic application bundle.
- `Fit_Met_Zorge_Coach_App_standalone.html` as a standalone historical artifact.
- `supabase/migrations/20260813_trainer_signup_bootstrap.sql` as the only visible local migration from the baseline audit.

Supabase is used for Auth and cloud synchronization. The frontend initializes Supabase through the hosted Supabase JS v2 library.

The visible database model currently depends on:

- `profiles`.
- `coach_workspaces`.
- Supabase `auth.users`.

The current application stores most trainer and client domain data inside `coach_workspaces.state` as JSONB. The frontend reads and writes this workspace state directly through Supabase queries.

The current state structure includes trainer account data, UI state, finance/admin settings, exercise library data, and `clients[]`. Client entries include profile fields, goals, training plans, nutrition plans, trackers, appointments, logs, and progress data.

## CURRENT STAGING INFRASTRUCTURE VERIFIED IN PHASE 0B

Phase 0B verified live staging metadata and dashboard state for project ref `mokxyyullfhkfalopbzd`.

Verified areas:

- Full structure of `profiles` from read-only metadata output.
- Full structure of `coach_workspaces` from read-only metadata output.
- Primary keys, foreign keys, unique constraints, indexes, RLS status, and policies from metadata output.
- Function/RPC `accept_client_invite` existence and definition metadata.
- Trigger/functions around new Auth users, including `fmz_bootstrap_trainer_profile` and `fmz_handle_new_auth_user` metadata.
- Edge Function `invite-client` exists, is deployed, and source was reviewed read-only.
- Edge Function secret names were verified without secret values.
- Auth URL configuration was verified.
- SMTP/email configuration and templates were verified.
- Storage was verified: staging currently has no Storage buckets.

See `docs/STAGING_INFRA_VERIFICATION.md` for the detailed Phase 0B record.

## CURRENT AUTH AND INVITE ARCHITECTURE

Phase 0B live staging verification confirmed the Edge Function `invite-client` exists and is deployed in staging project ref `mokxyyullfhkfalopbzd`.

The current client invite architecture is:

- Browser frontend calls `/functions/v1/invite-client` with the trainer's Supabase bearer token.
- Edge Function verifies the bearer token through a user-scoped Supabase client and `auth.getUser()`.
- Edge Function authorizes the caller by checking the caller's `profiles` row and requiring `role = trainer`.
- Edge Function uses a service-role Supabase client only in the trusted server-side function context.
- Service-role is required for Auth admin actions such as inviting users, listing existing Auth users, updating user metadata, sending reset links for existing users, and upserting `profiles` links.
- New client users receive `auth.admin.inviteUserByEmail(...)` with metadata containing `role`, `trainer_id`, `client_id`, and `name`.
- Existing Auth users are found through paginated Auth admin user listing, relinked through Auth metadata and `profiles`, then sent a password reset email as the invite/re-entry flow.
- The persistent trainer/client relationship is stored in `profiles.trainer_id` and `profiles.client_id`.
- Invite metadata mirrors that relationship in Auth `user_metadata` so `accept_client_invite` can complete or repair the client profile on login.

Verified staging redirect behavior in `invite-client`:

- Default redirect: `https://yourizorge.github.io/fitmetzorge-staging/`.
- Allowed redirect origins in the function: `https://yourizorge.github.io` and `https://test.appfmz.nl`.
- `yourizorge.github.io` redirects must stay under `/fitmetzorge-staging/`.
- `WEBAPP_URL` may be used only if it passes the same whitelist.

Auth URL Configuration verified in Dashboard:

- Site URL: `https://yourizorge.github.io/fitmetzorge-staging/`.
- Allowed Redirect URLs: `https://yourizorge.github.io/fitmetzorge-staging/` and `https://yourizorge.github.io/fitmetzorge-staging/**`.
- No production URLs were present in this configuration.

Known technical risks to preserve for later design:

- The Edge Function currently uses broad CORS with `Access-Control-Allow-Origin: *`.
- Existing Auth-user relinking currently scans Auth users with pagination up to 20 pages of 1000 users.
- `updateUserById` writes a complete `user_metadata` object for the client invite metadata, which may replace unrelated existing metadata.
- These risks are documented only; they must not be changed until a controlled implementation phase.

## CURRENT LEGACY CAPABILITIES TO PRESERVE

The rebuild must preserve existing working staging functionality until tested replacements are accepted:

- Trainer dashboard.
- Member/client management.
- Client invite and invite acceptance.
- Goals.
- Training builder and exercise library.
- Nutrition, recipes, macros.
- Trackers.
- Agenda and appointment types.
- Administration, invoices, rates, finance.
- Settings.
- Client dashboard.
- Client training, nutrition, trackers, agenda.
- Supabase Auth, session persistence, password reset, cloud workspace sync.

## PHASE 1 IMPLEMENTED FOUNDATION

Status: LOCAL IMPLEMENTATION COMPLETE, DATABASE MIGRATION NOT EXECUTED

Phase 1 adds an additive account foundation while preserving the current legacy app bundle and `coach_workspaces.state` compatibility.

Local app changes:

- `app.js` loads `assets/phase1-foundation.js` before `init()` inside the evaluated app bundle.
- `app.bundle.js` is not modified.
- Existing trainer/client login, reset, invite and invite acceptance paths remain in place.
- Client onboarding, BMI, Goal Engine foundation, account language settings and local entitlement read model are added as a Phase 1 layer.

Prepared database target:

- `user_settings` for language/country/unit foundation.
- `user_onboarding` for Phase 1 onboarding and safe goal metadata.
- `entitlements` for default Free entitlement source of truth.
- `fmz_phase1_upsert_account_foundation(...)` RPC for authenticated account foundation upsert.

The prepared migration is `supabase/migrations/20260815_phase1_account_foundation.sql` and must be run manually only in staging project ref `mokxyyullfhkfalopbzd` before full online verification.
## TARGET ARCHITECTURE

The target architecture is a staged, normalized Supabase-backed web/PWA platform with server-enforced authorization and entitlements, AI behind trusted backend functions, and a permanent staging-to-production release path.

### Frontend Target

- Web/PWA first.
- Mobile-first responsive consumer UX.
- Trainer and owner/admin surfaces in the same product ecosystem with role-based access.
- Translation-key based NL/EN/DE UI.
- Feature flags for incomplete or high-risk capabilities.
- Native iOS/Android later, using as much shared code as possible.

### Data Model Target

The new architecture must not permanently depend on one giant `coach_workspaces.state` JSONB model. Legacy remains temporarily as a compatibility source until migration is safe.

Conceptual normalized domains:

- IDENTITY: `profiles`, `user_settings`, `subscriptions`, `entitlements`.
- COACHING: `coach_client_relationships`, `coach_notes`, trainer/copilot data.
- TRAINING: `exercises`, `exercise_translations`, `training_plans`, `workouts`, `workout_exercises`, `workout_logs`, `workout_set_logs`, `personal_records`.
- NUTRITION: `nutrition_targets`, `food_logs`, `food_log_items`, `foods`, `recipes`, `saved_meals`.
- PROGRESS: `weight_logs`, `body_measurements`, `progress_photos`, `goals`, `goal_milestones`, `achievements`.
- RECOVERY: `recovery_logs`, `health_sync_connections`, health samples where needed.
- AI: `ai_threads`, `ai_messages`, `ai_recommendations`, `ai_action_proposals`, `ai_action_decisions`.
- GROWTH: `referrals`, `referral_rewards`, `goal_rewards`, `bonus_entitlements`.
- NOTIFICATIONS: `notifications`, `notification_preferences`, `push_tokens`.
- ANALYTICS: privacy-aware event and aggregate data.

These table names are directional. Later design may refine normalization, but the functional domains must remain covered.

### Legacy Bridge And Migration Target

Preserve these relationships during migration:

- Auth user <-> `profiles.id`.
- Trainer <-> `profiles.trainer_id`.
- Client <-> `profiles.client_id`.
- Trainer workspace <-> `coach_workspaces.trainer_id`.
- Legacy client id <-> `coach_workspaces.state.clients[].id`.

Target migration strategy:

1. Inventory legacy JSON state shape.
2. Design normalized tables and RLS in staging.
3. Build compatibility bridge/read model where needed.
4. Rehearse migration with staging data only.
5. Validate counts, relationships, permissions, and user flows.
6. Keep rollback path.
7. Only consider production after backup, rehearsal, validation, rollback plan, and owner approval.

### Security And RLS Target

- RLS is primary database security.
- UI hiding is never a security boundary.
- Sensitive actions require server-side authorization.
- Trainer can access only linked clients.
- Client can access only own/allowed data.
- Owner/admin access must be explicit through role/claims and safe backend rules.
- Service-role, AI, and payment secrets never reach the frontend.
- Use least privilege and audit logging for important actions.
- Avoid personal, health, and fitness data in logs unless necessary and safe.

### Entitlements And Payments Target

The entitlement layer is the single source of truth for plan and feature access.

Free/Pro/AI access must be enforced server-side.

Entitlements must cover barcode, Health sync, AI Coach, workout limits, premium analytics, bonus AI, and Personal Coaching included access.

A minimal entitlement foundation is required before consumer domains or AI consume entitlement decisions. Subscription, trial, referral, goal reward, bonus-day, and payment-webhook lifecycle logic expands later in Phase 7.

Trials, referrals, goal rewards, and Personal Coaching access must be real temporary entitlements/credits.

Payment provider is `NEEDS DECISION`. Provider webhooks must become source of truth for paid subscriptions. Client-side premium booleans are not trusted. Payment integration starts in staging test mode only.

### Phase 4 Nutrition Target

The Phase 4 architecture/readiness audit is recorded in `docs/PHASE4_NUTRITION_ARCHITECTURE_READINESS.md`. The locked owner product contract and exact first additive schema-slice design are recorded in `docs/PHASE4_NUTRITION_PRODUCT_CONTRACT_SCHEMA_SLICE1.md`. Schema Slice 1, Functional Slice 2, the atomic replacement RPC, and Functional Slice 3 are live and verified on staging; Slice 3 and the global member safe-area contract are owner-tested and frozen. Slice 4A is locked, Slice 4B alias/search and Slice 4C operational state are live and verified, Slice 4D provider logging/editing is owner-accepted and frozen, and the 64-food Slice 4E USDA catalog is accepted and frozen. The USDA `nutrition-provider` Edge Function is deployed on staging; authenticated search, lookup, signed candidate tokens, query/food cache behavior, tamper rejection, rate buckets, circuit state, and the absence of automatic canonical mutation passed controlled owner testing. Production remains untouched.

### Phase 4 Slice 4F OFF Domain

The reviewed local Slice 4F design keeps Open Food Facts in an independently extractable ODbL domain: `nutrition_off_catalog_releases`, `nutrition_off_products`, and `nutrition_off_product_names`. OFF records never become `public.foods` rows. The permanent UUIDv5 identity is `open_food_facts:<normalized_gtin14>` under namespace `23440733-7e58-4c21-ad15-591eae6ab8ac`; original barcode text remains alongside validated GTIN-14. `per_100_g` and `per_100_ml` are different authorities, and incomplete, quarantined, or archived products cannot be returned as loggable.

The new `fmz_phase4_search_nutrition_catalog` contract unions bounded, source-typed custom, OFF branded, and reviewed USDA generic candidates without changing frozen `fmz_phase4_search_foods`. Exact local barcode lookup is read-only and makes no provider request. The migration is additive and import-free; the accepted 24,458-row OFF subset requires a later pinned manifest, hash review, one-transaction import, and post-import verification. `public.fmz_phase4_normalize_catalog_text(text)` is the sole catalog-text normalization authority; artifact generation mirrors its PostgreSQL lower/trim/POSIX-alnum/whitespace behavior without Unicode compatibility normalization or transliteration. Future logging resolves an active trusted OFF row server-side and writes an immutable source/nutrition/licence snapshot, never historical truth through a mutable OFF FK. Full details are in `docs/PHASE4_NUTRITION_SLICE4F_OFF_CATALOG.md`.

Package 4F-D separates runtime barcode discovery from the deterministic OFF release lifecycle. The Edge route checks active local custom/generic/OFF identities first. A true miss performs one exact authenticated OFF barcode lookup, validates GTIN, Dutch relevance, explicit 100 g or 100 ml authority, required macros and ODbL provenance, then signs a 15-minute `open_food_facts:<gtin14>` candidate. Logging and replacement accept only the trusted server snapshot; historical same-product edits resolve the immutable saved snapshot and never depend on an expired token. Runtime scans never insert or update the persistent OFF catalog. Camera frames remain local and only the decoded barcode is sent to the backend.

The target Nutrition architecture replaces new whole-workspace JSON writes with normalized own-user data while preserving legacy `coach_workspaces.state` Nutrition until a reviewed transition is accepted. Directional objects include versioned `nutrition_targets`, calendar-day `food_logs`, immutable-snapshot `food_log_items`, provenance-aware `foods`, favorites, saved meals/items, recipes/items, and normalized nutrition plans/meals/items.

Key architecture rules:

- Historical log items keep nutrient/source snapshots; mutable catalog rows cannot rewrite history.
- Day totals derive from non-archived item snapshots; no second mutable totals source is introduced by default.
- Dates use the member's local `log_date` plus timezone context; weekend is not assumed to mean rest day.
- Macro values use constrained PostgreSQL `numeric`; volume conversion requires known density/serving data.
- Phase 1 `entitlements` is evaluated server-side for current active/time-valid rights; missing rights produce Free behavior.
- RLS is own-user only in the initial member slice. No broad trainer policy or whole-workspace authorization is added.
- Multi-row writes and copy operations are transactional and idempotent through stable UUID/request IDs and unique constraints.
- Barcode/provider access is backend-mediated, feature-flagged, entitlement-checked, cached, rate-limited, and secret-free in the browser.
- Youri AI execution remains Phase 6; trainer normalized access requires a separately reviewed linked-client architecture.

The owner contract fixes Free at targets, unlimited normal daily logging, totals, 10 active custom foods, and seven-day history. Pro adds the complete self-service engine; AI receives Pro Nutrition without Phase 4 AI execution; PT receives full member capability while trainer access remains a separate reviewed policy. History and custom-food limits are server-authoritative. Slice 1 uses six additive own-user tables and entitlement-aware RPC reads; direct authenticated base-table reads do not expose premium history.

The live reviewed SQL implements RPC-only direct access for preferences, targets, logs, and items; authenticated receives SELECT only on `foods` and `food_portions`. Internal helpers and trigger functions have no app-role execute right. Public RPCs derive authority from `auth.uid()`, use a fixed safe search path, and expose no trainer shortcut. Slice 4B preserves this contract by adding `food_aliases` as authenticated SELECT-only with active reviewed/verified aliases, parent-food visibility, no member writes, and no trainer policy. Prefix and `pg_trgm` candidate indexes cover alias, food-name, and brand search; Dutch/EU relevance uses constrained alias `market_code` plus priority.

Slice 4E's `nutrition_food_ingestions` foundation is live and verified. It keeps private audit state with no app or service-role ACL, nullable restrictive ingestion links on `foods` and `food_aliases`, canonical reviewed/verified visibility that requires a ledger link, and explicit preferred-NL-alias uniqueness per normalized term and market. The existing `fmz_phase4_search_foods(text,integer,text,uuid)` signature is alias-aware without a frontend contract change. It remains `SECURITY INVOKER`, uses bounded indexed candidate branches, deduplicates by food UUID, and reconstructs the last row's rank from `p_after_id` for stable rank-aware keyset pagination.

The first reviewed local catalog artifact contains 64 generic USDA foods and 197 reviewed aliases from pinned Foundation, Survey (FNDDS), and SR Legacy detail datasets. Canonical identities use UUIDv5 namespace `23440733-7e58-4c21-ad15-591eae6ab8ac` with exact `usda_fdc:<fdcId>` names. A one-transaction seed binds every row to ingestion UUID `92fbeedd-63a8-5d22-9000-24e2a16189f1`, rejects identity drift, inserts zero portions, and never mutates custom foods. A separate SELECT/CTE-only verifier is the post-import gate. The artifact is prepared, not imported.

Slice 4C provides four private RLS-enabled operational tables: `nutrition_provider_query_cache`, `nutrition_provider_food_cache`, `nutrition_provider_rate_buckets`, and `nutrition_provider_runtime_state`. They have no member/trainer/anonymous policies or privileges. Cache tables allow only backend service-role read/upsert; rate writes occur only through `fmz_phase4_provider_consume_rate_limits`, and circuit writes only through `fmz_phase4_provider_transition_runtime_state`. Both internal functions are `SECURITY DEFINER`, fixed to `search_path=pg_catalog`, and executable only by `service_role`. Query and user identity use backend HMACs without raw terms or user IDs. The Edge Function binds each rate replay UUID to request ID plus canonically serialized route/operation identity, uses signed short-lived lookup candidates, fixed USDA endpoints, strict staging CORS, bounded payloads, exact cache-payload revalidation, deterministic quality mapping `phase4_usda_v1`, and no canonical catalog writes. Its only external runtime package is exactly pinned and protected by a frozen Deno integrity lock.

Provider candidates use UUIDv5 namespace `PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE = 23440733-7e58-4c21-ad15-591eae6ab8ac` with exact name `provider_code:provider_food_id`. Thus USDA FDC `171077` derives from `usda_fdc:171077`. This namespace is permanent and non-secret across environments. It is separate from the frozen Phase 3 exercise namespace `9439f2af-0e84-5e41-9482-d4b6765154ed`.

Slice 4D locks transient provider-snapshot logging. `food_log_items.food_id` and `food_portion_id` remain nullable for this narrow server path; canonical and custom member logging keep their existing non-null food identity contract. Browser requests to `POST /nutrition-provider/log` or `/replace` contain only a signed candidate token and normal log/edit fields. The Edge Function revalidates the candidate through trusted cache/lookup logic, derives the authenticated user from the verified bearer JWT, constructs the authoritative provider snapshot, and calls service-role-only `fmz_phase4_log_provider_food_item` or `fmz_phase4_replace_provider_food_log_item`. Both database functions have fixed `pg_catalog, public, pg_temp` search paths, exact-payload idempotency, transaction advisory locks, local-date/history enforcement, and no canonical catalog writes. Provider rows use `food_id = NULL`, explicit 100 g reference, gram-only consumption, immutable nutrition/provenance snapshots, and the existing archive RPC. Automatic candidate promotion and browser nutrient authority are forbidden.

### AI Backend Target

No browser-to-AI provider calls.

Required flow:

1. App calls secure backend/Edge Function.
2. Backend authenticates user.
3. Backend authorizes action.
4. Backend checks entitlement.
5. Backend retrieves minimal relevant context.
6. Backend calls AI provider.
7. Backend validates structured response.
8. Backend stores recommendation/proposal/action only where allowed.

Strategic AI actions require proposal -> approval -> execution. Trainer priority applies for PT clients. AI usage, cost, rate limit, and abuse-control logging are mandatory.

### Storage Target

Phase 0B verified no current staging Storage buckets.

Target storage:

- Private progress-photo bucket.
- Private sensitive upload buckets as needed.
- Signed URLs or equivalent secure access.
- Exercise media separately as read-only/public or CDN-like assets where appropriate.
- No sensitive files public.

### Analytics Target

Owner analytics and Business Insights must be privacy-aware. Product AI insights must distinguish observation, correlation, hypothesis, and recommendation. Unsupported causal claims are forbidden.

### Mobile Target

After mature PWA staging:

1. iOS TestFlight staging build.
2. Android internal/closed staging build.
3. Mobile QA using staging backend.
4. Production app store builds only after Production Readiness Review and owner approval.

### Phase 5 Progressie Architecture

Status: COMPLETE / OWNER-ACCEPTED / FROZEN

The live normalized domain uses `progress_preferences`, `progress_goals`, `weight_logs`, and `body_measurements`. Canonical values are kilograms and centimetres; local dates are validated against an IANA timezone and client offset. Corrections create immutable superseding rows, removals archive, stable request UUIDs make retries idempotent, expected timestamps protect against stale writes, and per-user/date advisory locks serialize competing writes.

Member writes are RPC-only and derive ownership from `auth.uid()`. Base-table browser privileges are absent; own-user RLS remains defense in depth. Free history is server-bounded to the current local day plus 29 prior days. Only current active Pro, AI, or personal-coaching entitlements grant full history. The dashboard reads frozen Training, Recovery, and Nutrition sources descriptively without changing their ownership or data models. Running remains explicitly unavailable until a reviewed authoritative source exists.

The existing `user_settings.unit_system` stores the presentation choice. No imperial value becomes database authority. Progress photos remain deferred: there is no Phase 5 photo table or bucket, and the member runtime exposes no file input. Legacy trainer Progress and historical `coach_workspaces.state` data remain untouched.

### Phase 6 Youri AI Core Readiness

Status: ARCHITECTURE AUDIT COMPLETE; PACKAGES 6A AND 6B COMPLETE / OWNER-ACCEPTED / FROZEN

Live staging now contains the additive Package 6A AI trust schema. Normalized own-user Identity, Recovery, Training, Nutrition and Progress inputs remain the frozen authorities. No provider credential, external provider call or member-facing AI runtime is active.

Phase 6 uses a dedicated provider-neutral `youri-ai` Edge boundary. It authenticates the member, resolves current time-valid `ai` or `personal_coaching` entitlement, verifies AI consent, reads minimized context through member-JWT-scoped RPCs, applies rate/budget/safety/idempotency gates, invokes one approved provider, validates a strict structured response and persists only allowed private member and operational records. The browser never supplies data authority, model choice, entitlement, provider credentials or executable domain changes.

Private `ai_threads` and `ai_messages` have no trainer read path. Future trainer summaries/signals are separate minimized records with explicit consent and active-link authorization. Strategic linked-client changes remain proposal-only until a reviewed trainer approval path exists. Every meaningful recommendation/action keeps feature, policy/model/schema versions, context manifest/hash, evidence references, safety result, usage/cost metadata and append-only decisions.

Package 6A implements a provider-free trust boundary with eight own-user public foundations, twelve private operational/configuration tables, RPC-only browser access, strict JSON schemas, deterministic mock adapter, context manifests, exact replay, subscription-month budget reservation and safety/retention state. `ai_coach_enabled`, `provider_calls_enabled` and `staging_mock_enabled` are live and false. The verifier passed 47/47; the transactional E2E retained no fixtures and recorded zero external calls/cost. Package 6A is owner-accepted and frozen. The contracts are in `docs/PHASE6_AI_CORE_ARCHITECTURE_READINESS.md` and `docs/PHASE6A_AI_TRUST_FOUNDATION.md`.

Package 6B adds a service-only synthetic path around an `OpenAiResponsesAdapter`; browsers never receive OpenAI credentials or choose prompts, models, tools or endpoints. The adapter accepts only deterministic synthetic fixtures, sends `store:false`, disables all hosted tools, validates the exact returned model and strict `phase6a.response.v1` output, and reports bounded input/cached/output/reasoning usage metadata before returning it.

Five RLS-enabled tables in non-exposed `ai_private` hold provider configuration, exact model policy, payload purpose inventory, a global staging test budget and minimized test-run accounting. No browser role has table access or service-RPC execution. Per-request/global advisory locks reserve maximum cost and calls before a provider attempt and reconcile returned usage. Real-member processing has no route and remains blocked by technical ZDR/DPA/DPIA/EU-route/copy/transfer/lifecycle/owner gates.

This 6B boundary is live only on staging as migration history `20260902045834` and final `youri-ai` v38 with JWT verification. The verifier passes 36/36 and the isolated rollback E2E persists no fixtures or cost. One Luna and one Terra locked synthetic fixture passed exact-model, schema, token and cost reconciliation; successful-call estimates total EUR 0.004518. The synthetic flag is off and the real-member block remains unchanged. Package 6B was owner-accepted and frozen on 2026-09-02; Package 6C has not started and requires a separate owner GO.


