# Phase 4 Nutrition - Slice 4 Canonical Food Catalog Architecture

Status: SLICE 4A LOCKED / SLICE 4B LIVE AND COMPLETE / SLICE 4C LIVE AND VERIFIED / USDA SEARCH+LOOKUP EDGE LIVE AND SMOKE-VERIFIED / SLICE 4D FINAL REVIEW PASS AND GITHUB-SYNCED, NOT EXECUTED OR DEPLOYED

Date: 2026-08-19

Environment: Slice 4B and Slice 4C are live and read-only verified on staging `mokxyyullfhkfalopbzd`. USDA search/lookup is deployed and its authenticated smoke path passed without canonical mutation. Slice 4D provider logging exists locally only. No food import, provider-log frontend integration, Slice 4D migration execution/deployment, or production change has occurred.

## Frozen Baseline

Phase 4 Functional Slice 3 and the global member bottom-navigation safe-area contract are owner-tested, complete, and frozen. Daily logging, macro totals, targets, four meal moments, persistence, atomic replacement, meal movement, archive/remove, date navigation, custom foods, dialogs, and real-phone reachability must remain regression baselines.

Phase 1, Phase 2, Phase 3 Training, Member UX, Phase 4 Schema Slice 1, Functional Slice 2, and Functional Slice 3 remain frozen.

## Slice 4A Locked Contract

The owner locked the local-first hybrid provider contract on 2026-08-19:

- USDA Foundation/FNDDS is the intended reviewed generic-food source; API credentials remain backend-only.
- Open Food Facts is reserved for Dutch/EU branded products and later barcode use after explicit ODbL/DCL legal and attribution approval.
- NEVO stays excluded until separate legal/licensing approval.
- Search is local first. Provider fallback is controlled and cached later, never browser typeahead or one provider request per keystroke.
- Private custom foods remain private, visually distinct, and are never promoted automatically.
- Provider identity, provenance, source version, license, quality, and source update time remain auditable.
- Barcode, provider calls, imports, and operational provider state are later slices and are not part of Slice 4B.

## Product Objective

Normal members should find trustworthy everyday generic and branded foods without manually creating them. The first market is the Netherlands, while provider identity, provenance, locale, and search contracts stay internationally extensible. Private custom foods remain the fallback for genuinely missing or special foods and never become public automatically.

## Provider Assessment

### Open Food Facts

Recommended role: Dutch and European branded products, brand and product names, barcode identity, package/serving metadata, and nutrition per explicit 100 g or 100 ml basis when complete.

Current official constraints relevant to the design:

- The database uses ODbL; individual contents use the Database Contents License; product images use CC BY-SA and may contain additional rights.
- Community data has no accuracy, completeness, or reliability guarantee.
- Product reads are limited to 15 requests/minute/IP and search to 10 requests/minute/IP. Search-as-you-type is explicitly discouraged.
- A custom identifying User-Agent is required/recommended.
- For more than a few hundred products or material traffic, Open Food Facts recommends downloads/local infrastructure rather than repeated public API calls.
- API v3 is the current product-read API. Full-text search remains a moving surface; the current documentation points to Search-a-licious and warns that v2/v3 do not provide ordinary full-text search in the same way.

Architecture consequence: Open Food Facts cannot be the live per-keystroke search backend for FitMetZorge. It belongs behind a backend proxy, cache, ingestion pipeline, quality gate, and legal approval. Images are excluded from the initial catalog slice.

### USDA FoodData Central

Recommended role: generic foods, foundational foods, raw ingredients, standardized nutrient records, and reviewed gram-based portions. Foundation Foods is preferred for current analytical generic data, FNDDS can support common consumption forms/portions, and SR Legacy is a lower-priority fallback because it is no longer updated. USDA Branded is not the primary Dutch branded source.

Current official constraints relevant to the design:

- FoodData Central data is public domain and published under CC0; attribution is requested.
- Every API request requires a data.gov API key. The key holder must keep it private.
- The default rate limit is 1,000 requests/hour/IP; excess use can block the key for one hour. Rate headers are available.
- Search and detail endpoints are available, as are periodic downloadable datasets.
- Data types have different provenance, update cadence, and portion semantics.

Architecture consequence: USDA is the safest source for a curated generic starter catalog, but English names need reviewed Dutch aliases. API access remains backend-only and cached.

### NEVO

NEVO remains excluded from implementation, import, API use, and derived catalog work until explicit legal/licensing approval is recorded.

## Recommended Provider Mix

Use a hybrid local-first model:

1. A reviewed generic starter catalog sourced primarily from USDA Foundation/FNDDS data, normalized to FitMetZorge units and supplemented by reviewed Dutch search aliases.
2. Open Food Facts for Dutch/EU branded products and future barcode lookup only after ODbL/DCL reuse, attribution, database-sharing implications, and operations are legally approved.
3. Cached normalized provider records in `public.foods`; source-specific identity and provenance always remain visible internally.
4. Private member custom foods for missing or specialist entries.
5. No silent merge of USDA, Open Food Facts, custom, or legacy rows.

The exact launch-catalog count is determined by a measured Dutch coverage test, not by padding to an arbitrary number.

## Canonical Identity

- Provider identity is `(source_provider, provider_food_id)` and remains unique.
- Provider candidate UUIDs are deterministic UUIDv5 values over permanent namespace `23440733-7e58-4c21-ad15-591eae6ab8ac` and exact name `provider_code:provider_food_id`. The namespace constant is `PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE`, is non-secret, and is shared by staging and future production. The initial name is `usda_fdc:<fdcId>`.
- The Phase 3 exercise namespace `9439f2af-0e84-5e41-9482-d4b6765154ed` remains separate/frozen and is never used for provider candidates.
- Generic curated foods use a stable reviewed `canonical_slug` representing food, preparation state, and relevant form.
- Branded products remain separate from generic foods and include normalized brand plus barcode when valid.
- Barcode is a strong same-product candidate, not an unconditional cross-provider merge rule.
- Provider updates revise the same provider row, preserve `source_version` and `source_updated_at`, and never rewrite historical `food_log_items` snapshots.
- Discontinued or invalid records are archived; they are not deleted.
- Cross-provider duplicates are review candidates. Automated normalization may flag them but may not collapse them.

## Language And Aliases

- `foods.name` is the best reviewed display name available for the target market record.
- Original provider names remain in `provenance`/metadata and are never misrepresented as reviewed translations.
- NL uses reviewed Dutch generic names/aliases where available; branded provider names remain authentic product names.
- EN and DE use reviewed aliases where available, otherwise the canonical/provider display name with an explicit fallback contract.
- Search aliases support spelling variants, singular/plural forms, common Dutch terms, preparation terms, and safe synonyms.
- Runtime AI translation is forbidden.

The current schema has no normalized first-class alias table. Slice 4 therefore likely needs a small additive `food_aliases` table before high-quality NL/EN/DE search is implemented.

## Nutrition Normalization

- Canonical values are kcal, protein g, carbohydrate g, fat g, and optional fiber g.
- Preferred reference bases are exactly 100 g for solids and 100 ml for liquids.
- Provider per-serving data is accepted only when an explicit gram or milliliter equivalent exists.
- Never assume 1 ml equals 1 g. Density is stored only when the provider supplies trustworthy density or a reviewed source establishes it.
- If kcal is absent and kJ is trustworthy, derive kcal as `kJ / 4.184`, record the derivation, and round stored nutrients to three decimals.
- If both kcal and kJ exist but materially disagree, quarantine the row rather than choosing silently.
- Missing protein, carbohydrate, or fat prevents normal active search unless a reviewed source contract explicitly supports the omission.
- Negative, impossible, non-finite, or physically implausible values are rejected/quarantined.
- Provider nutrients are mapped by stable nutrient identifiers where available, not display-name string matching alone.

## Portion Strategy

`food_portions` contains only explicit provider/reviewed conversions. A portion label must point to an exact equivalent in g, ml, serving, or piece under the existing database constraints. Package size is not automatically a serving. Provider-specific portion semantics and source references remain in metadata. Missing conversion data means users log by the canonical g/ml basis.

## Data Quality

Use the existing quality contract without widening it initially:

- `pending`: quarantined or awaiting normalization/review; never activated for normal search.
- `community`: sufficiently complete Open Food Facts/community record that passed automated safety checks, shown with lower ranking/confidence.
- `reviewed`: trusted provider record plus successful deterministic mapping and review rules.
- `verified`: manually verified FitMetZorge record or explicitly verified source mapping.
- `user_entered`: private custom food only.

Only `active` rows that pass minimum completeness may enter member search. Rejected/incomplete records stay outside the active catalog or are archived with a reason in metadata. Search ranking must never imply that community data is clinically verified.

## Provenance And Licensing

Every provider record must retain provider ID, provider version, source updated timestamp, license code, retrieval/import timestamp, mapping version, source URL/reference, field-level derivation notes where needed, and normalization checksum. USDA attribution should be displayed in a catalog attribution surface. Open Food Facts attribution and any database-sharing obligations require legal approval before import.

Open Food Facts data must stay extractable by provider/license. Whether mixed storage in `public.foods` creates ODbL derivative-database obligations is an external legal decision, not an engineering assumption.

## Backend Proxy

Future external lookups use a dedicated Supabase Edge Function or equivalent trusted backend:

1. Verify the Supabase user token.
2. Apply per-user and global abuse limits. Canonical search remains a Free feature; entitlement is not accepted from the browser.
3. Normalize locale/country/query and reject unsafe or overly broad input.
4. Search FitMetZorge local data first.
5. Consult a short-lived provider-query cache only when local coverage is insufficient or the member explicitly requests more results.
6. Call the provider with backend-only credentials/User-Agent.
7. Validate, normalize, quality-score, and persist only accepted fields.
8. Return bounded results with provenance and attribution metadata.

The frontend never receives USDA keys, service-role keys, provider credentials, or unrestricted import rights.

## Local-First Search

- Minimum normalized query length: 2 characters, except exact barcode lookup in the later barcode slice.
- UI debounce: approximately 300 ms for local search.
- Provider fallback: explicit or delayed after insufficient local results; never on every keystroke.
- Local page size remains bounded; use stable keyset pagination.
- Stale requests are cancelled/ignored with request tokens or `AbortController`.
- Ranking order: exact canonical/alias match, exact brand/product match, prefix, Dutch alias relevance, generic-quality boost, Dutch/EU market relevance, reviewed/verified quality, then controlled fuzzy relevance.
- Private `my food` results are visually distinguished from catalog results without being globally promoted.
- Barcode exact match later reuses the same identity/cache path.

## Caching And Rate Limits

- Normalized accepted products persist in `foods` and are refreshed by `source_updated_at`/provider version rather than refetched per user.
- Provider query-result cache keys contain provider, normalized query, locale, country, page, and mapping version.
- Cache TTLs are provider/configuration-specific and adjustable without frontend release.
- Open Food Facts public limits are treated as shared outbound limits when called from Edge Functions; queueing, backoff, circuit breaking, and daily exports are required before scale.
- USDA responses honor `X-RateLimit-*`; 429 triggers backoff and local-only behavior.
- No provider outage may block custom foods or already cached/local catalog search.

## Privacy And Logging

Food searches can reveal diet, religion, allergy, condition, or health-related interests and are treated as potentially sensitive behavioral data. The provider receives no Supabase user ID, email, trainer ID, health profile, targets, or food log. Raw search terms are not written to normal application logs. Operational metrics use coarse counts or keyed hashes with short retention; error messages are sanitized. A retention/DPIA/legal review remains required before production.

## Database Sufficiency

The live Slice 1 schema is sufficient for normalized accepted provider rows, portions, provider identity, barcode, provenance, quality, archive state, and immutable log snapshots.

It is not sufficient for high-quality multilingual candidate search at 100k-1m scale. Slice 4B therefore creates the smallest additive layer:

- `public.food_aliases` with stable UUID, parent food FK, `nl`/`en`/`de`, display and normalized alias, constrained alias type, reviewed/verified visibility, optional provider/version/license/source timestamp, compact `market_code`, bounded priority, provenance/metadata, and soft archive state.
- `pg_trgm` in the Supabase `extensions` schema, plus partial GIN trigram indexes for reviewed active aliases and active food name/brand candidates.
- B-tree indexes for active prefix lookup, parent/FK access, active alias uniqueness, and market/language priority.
- Authenticated SELECT-only RLS/ACL. No member write route, trainer policy, delete policy, service-role frontend, or new public function is added.

Dutch and EU relevance stay alias-level through uppercase two-character `market_code` plus bounded `priority`; this avoids changing `foods` or introducing an unproven market table. `normalized_alias` is explicit trusted-ingestion data rather than an opaque generated search document, so future normalization versions remain reviewable.

The frozen `fmz_phase4_search_foods` RPC and its pagination contract remain unchanged. A ranked alias-aware v2 RPC is designed and reviewed only with Slice 4F frontend integration. Slice 4C now defines the proven minimum operational state: HMAC-keyed query cache, normalized provider-food cache, transactionally atomic rate buckets, and shared circuit state. The canonical ingestion ledger remains deferred to the first reviewed import slice.

Local artifacts:

- Migration: `supabase/migrations/20260819_phase4_nutrition_slice4b_alias_search.sql`, SHA-256 `4C0E63DC09A8CC1DE7F93DBA278CD36F714C52BEDAB32FFC98147A5DA0D5C88F`.
- Read-only verifier: `supabase/verification/20260819_phase4_nutrition_slice4b_alias_search_verification.sql`, SHA-256 `598D70447917FA7903472D9B2C4977FDC4BEA5AA08B1B9739C69703067B2F414`.
- Static/security suite: `assets/phase4-nutrition-slice4b-static-check.js`.

The Slice 4B migration is live and verified on staging. It remains one transaction, additive, seed-free, backfill-free, and does not alter `foods`, `food_portions`, legacy Nutrition, logging history, or frozen RPCs.

Live result: Slice 4B executed and direct read-only verification passed on staging. `pg_trgm` is in `extensions`; `food_aliases` has 19 columns, RLS, one SELECT policy, zero rows, authenticated SELECT only, and seven expected indexes. No catalog or aliases were imported.

### Slice 4C Operational State Live Foundation

Slice 4C adds exactly four backend-only tables: `nutrition_provider_query_cache`, `nutrition_provider_food_cache`, `nutrition_provider_rate_buckets`, and `nutrition_provider_runtime_state`. All have RLS and zero client policies. Query identities are HMACs, payloads and metadata are shape/size bounded, mapping versions and checksums prevent incompatible or poisoned reuse, and explicit expiry timestamps support 24-hour positive, 15-minute empty, and 30-day food-detail runtime configuration.

The database hard-enforces USDA ceilings of 3/30 seconds, 12/10 minutes, 100/day per HMAC subject, and 800/hour globally. `fmz_phase4_provider_consume_rate_limits` serializes the provider-global and user namespaces, prepares all four aligned buckets, detects all-or-none replay, checks every limit, and only then increments all counters in one transaction. `fmz_phase4_provider_transition_runtime_state` serializes closed/open/half-open transitions and one half-open probe. Both functions have a fixed `pg_catalog` search path and service-role-only execution. Cache upserts are service-role-only; rate tables have no direct backend table grant and runtime state is read-only outside its transition function.

Reviewed artifacts:

- Migration: `supabase/migrations/20260819_phase4_nutrition_slice4c_operational_state.sql`, SHA-256 `0A2D2CA5B4CAAD30A17B73F66C018A742DC1D9326335AA7C9307D0021CF0AE2F`.
- Read-only verifier: `supabase/verification/20260819_phase4_nutrition_slice4c_operational_state_verification.sql`, SHA-256 `B444C84CA42347E2D637A025CD76141F8C12821262CBD0E110B770BBBA2CA200`.
- Static/security suite: `assets/phase4-nutrition-slice4c-static-check.js`, PASS 116 checks.

The migration and SELECT-only verifier completed successfully on staging. The exact four tables retain RLS and zero client policies/ACL; the service-role ACL and two internal functions match the reviewed contract; all operational rows remained zero. No provider credential, USDA/OFF request, food row, ingestion ledger, frontend change, Edge deployment, or production change was included.

### Local USDA Edge Function

`supabase/functions/nutrition-provider/` implements deployed staging routes `POST /search` and `POST /lookup` using mapping version `phase4_usda_v1`. Search accepts only Foundation, Survey (FNDDS), and SR Legacy. Lookup requires a short-lived HMAC-signed candidate token from search. The proxy authenticates the Supabase bearer user, uses no client role/package/user authority, sends no member identity to USDA, uses only a fixed USDA host, applies strict staging CORS, and returns bounded normalized candidates rather than raw provider payloads. Cache hits are accepted only after checksum, exact payload shape, deterministic UUID, nutrition bounds, attribution and provenance revalidation. Replay identities use canonical structured operation serialization. The exact `@supabase/supabase-js@2.95.0` runtime dependency and its transitive graph are integrity-locked in frozen Deno mode.

Cache lookup precedes provider budget consumption. Cache identity and rate subject are HMAC-derived; rate replay identity is additionally bound server-side to client request ID plus route and operation. The live atomic rate RPC and circuit RPC remain authoritative across Edge instances. Positive query cache is 24 hours, empty search 15 minutes, and food detail 30 days. Nutrients are per 100 g, USDA nutrient IDs and energy precedence are explicit, kJ conversion uses 4.184, missing macros are never zero-filled, and volume is never assumed equal to mass. Invalid details are quarantined. No canonical `foods`, `food_portions`, or `food_aliases` write exists.

Required secret names are `USDA_FDC_API_KEY` and `FMZ_PROVIDER_HMAC_KEY`; values are absent from source and reports. Both names are configured on staging. Controlled authenticated search/lookup, cache, token-tamper, rate and circuit smoke checks passed without canonical writes.

### Slice 4D Transient Provider Snapshot Logging

Owner-approved initial behavior is gram-only transient USDA logging with no canonical promotion. The browser sends `candidate_token`, stable item/request UUIDs, local day/timezone context, meal, grams, notes, and optional consumed timestamp to `POST /log`. It cannot send food ID, nutrients, provider URL/payload, user ID, role, package, or entitlement. The Edge Function verifies the bearer user, verifies and resolves the signed candidate through the existing trusted cache/lookup path, constructs the authoritative snapshot, and calls service-role-only `fmz_phase4_log_provider_food_item`.

Provider rows keep `food_id = NULL` and `food_portion_id = NULL`; the existing nullable FK contract already permits this. Reference amount/unit remain 100 g, calculation is direct-reference grams, and the row snapshots provider ID, candidate UUID, mapping/data type, source version, retrieval/source timestamps, derivation, attribution, provenance, notes, and calculated kcal/macros. No future cache or canonical row is required to interpret history.

Provider edits use service-role-only `fmz_phase4_replace_provider_food_log_item`. It serializes request and object identities, locks the original, requires `expected_updated_at`, creates one active replacement in the same log/day, and archives the original in the same transaction. Same exact requests replay; changed payload reuse rejects. Existing `fmz_phase4_archive_food_log_item` already supports nullable `food_id` and remains the only archive route. Free retains the current local day plus six prior days; current Pro, AI, and Personal Coaching entitlements retain full history. USDA portions, browser archive-plus-readd editing, automatic writes to `foods`/`food_portions`/`food_aliases`, frontend wiring, and deployment remain blocked pending separate review.

Final reviewed artifacts are `supabase/migrations/20260819_phase4_nutrition_slice4d_provider_snapshot_logging.sql` (SHA-256 `10228D7CDEC07341C85BFF80D2464ED4F46995FB732976F3045DFB2CB72F9DD0`) and `supabase/verification/20260819_phase4_nutrition_slice4d_provider_snapshot_logging_verification.sql` (SHA-256 `035B61D9175B49F163A400E3932A5E42D0F41D4ABE258B57CE0524F215025450`). The earlier verifier hash `1DABC7E3AF0941DDBACB3BB4A72A01338AE05BB277C98EDCB6A877A8AF83D27F` is obsolete because final review corrected its exact `proconfig` comparison and strengthened trigger, canonical-member-path, numeric-bound, and day-total assertions. The migration remains byte-identical: one additive transaction changing only the two ownership trigger functions required for internal nullable-food writes, the two provider RPCs, and their ACL. The verifier remains one SELECT/CTE statement and invokes no application function.

## Scale

### 10,000 foods

PostgreSQL local search is straightforward. B-tree prefix indexes plus reviewed alias/name/brand trigram candidates are sufficient. Keyset pagination and bounded RPC results remain mandatory.

### 100,000 foods

Use normalized aliases, partial GIN/trigram candidate selection, B-tree locale/market/prefix paths, and candidate-first ranking. The future RPC should union bounded food-name, brand, and alias candidates, rank exact and prefix matches before similarity, deduplicate by food ID, then keyset-page a stable score/name/ID order. Verify plans with representative Dutch terms and avoid JSON or unindexed full-table scans.

### 1,000,000 foods

PostgreSQL remains viable with disciplined partial GIN indexes, selective candidate caps, autovacuum/analyze monitoring, batch ingestion, soft archive, and operational observability. GIN write amplification, index size, broad two-character queries, and ranking work become the main bottlenecks. Provider/country partitioning or a rebuildable external search index is considered only after measured plans breach the service objective; PostgreSQL remains source of truth.

## Provider Failure Behavior

Provider timeout, 429, 5xx, schema drift, license uncertainty, or failed normalization returns local results plus a localized retryable status. It never returns fabricated nutrition, never blocks custom-food creation, and never persists an incomplete row as verified. Circuit breakers prevent repeated provider pressure.

## Future Barcode Compatibility

Barcode input later calls the same backend provider lookup, validates the code, searches local indexed barcode first, fetches provider data only on a miss/staleness rule, normalizes to `foods`/`food_portions`, and logs through the existing Slice 3 RPCs. Camera/barcode UI is outside this slice.

## Implementation Breakdown

1. **4A Provider/legal contract:** LOCKED. Provider roles and local-first behavior are approved; the OFF legal gate remains mandatory before use.
2. **4B Additive search schema:** LIVE / COMPLETE ON STAGING. Alias/search indexes only; no catalog rows imported.
3. **4C Backend provider proxy:** OPERATIONAL STATE LIVE / VERIFIED; SEARCH+LOOKUP EDGE LIVE / AUTHENTICATED SMOKE PASS. Private caches, atomic abuse limits, shared circuit state, and the reviewed USDA adapter are active on staging without canonical mutation.
4. **4D Transient provider logging:** FINAL SQL/EDGE REVIEW PASS / GITHUB SYNCED / NOT EXECUTED OR DEPLOYED. Gram-only immutable USDA snapshots, service-role-only log/replace RPCs, existing member archive route, no canonical promotion; staging migration execution, live verification, Edge deployment, and frontend wiring remain separate gates.
5. **4E Curated generic catalog:** deterministic USDA-based generic artifact, Dutch aliases, provenance, quality report, hash review, staged import, and read-only verification.
6. **4F Branded ingestion/cache:** OFF only after legal approval; controlled Dutch/EU subset or export/on-demand pipeline, never blind bulk ingestion.
7. **4G Member search integration:** ranked local-first results, `catalog` versus `my food`, bounded provider fallback, NL/EN/DE, and mobile-first UX.
8. **4H Quality/attribution operations:** refresh, archive/discontinued behavior, provider drift monitoring, attribution UI, and audit/export process.
9. **4I Owner acceptance:** real-phone Dutch search coverage, nutrition correctness, provider failure, security, performance, frozen regressions, and explicit freeze.

## External Gates

- OWNER/LEGAL DECISION REQUIRED: Open Food Facts ODbL/DCL reuse, attribution, share-alike/database-extract obligations, and commercial product presentation.
- OWNER DECISION REQUIRED: initial curated generic coverage target and acceptance benchmark.
- OWNER/PRIVACY DECISION REQUIRED: raw-query retention policy and DPIA/AVG posture.
- OWNER/OPERATIONS DECISION REQUIRED: provider budget, refresh cadence, monitoring, and incident ownership.
- NEVO LEGAL APPROVAL REQUIRED before any implementation consideration.

## Exact Next Step

Owner may separately authorize execution of the final reviewed Slice 4D migration on staging `mokxyyullfhkfalopbzd`. Execution must be followed by the final read-only verifier before any separately approved Edge deployment. Provider-log frontend wiring, canonical imports, barcode, production, Open Food Facts, and legacy mutation remain blocked.
