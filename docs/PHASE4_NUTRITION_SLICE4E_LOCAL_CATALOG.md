# Phase 4 Nutrition Slice 4E - Dutch Local Catalog Foundation

Status: FOUNDATION LIVE + VERIFIED / REVIEWED 64-FOOD MANIFEST + SEED READY / IMPORT NOT EXECUTED

Environment guard: staging project `mokxyyullfhkfalopbzd` only. Production is forbidden.

## Locked Scope

Slice 4D remains complete and frozen. Slice 4E prepares a reviewed Dutch local canonical catalog without importing catalog rows. USDA FoodData Central Foundation, Survey (FNDDS), and SR Legacy generic foods are the only sources in the first manifest. Open Food Facts branded foods, NEVO, barcode, media, AI, trainer catalog access, and legacy Nutrition mutation remain outside this slice.

Catalog imported: NO

Migration executed: YES - STAGING ONLY

Frontend changed: NO

Edge Function changed: NO

## Ingestion Authority

`public.nutrition_food_ingestions` is the private audit source of truth for every reviewed catalog artifact. It records stable artifact identity, uppercase SHA-256, source and mapping versions, predecessor, manifest counts, reviewer marker, review/import timestamps, and bounded provenance/metadata objects.

The allowed lifecycle is forward-only:

1. `reviewed` can become `imported` or `rejected`.
2. `imported` can become `superseded`.
3. `superseded` and `rejected` are terminal.
4. Audit identity and an existing `imported_at` value are immutable.
5. The first provider artifact may omit a predecessor; every later artifact for that provider must reference the same-provider predecessor.
6. A per-provider advisory lock and unique successor index serialize the chain and prevent branching.
7. Row removal is rejected by a database trigger. Corrections use a new artifact and explicit predecessor.

RLS is enabled. The ledger has no member, trainer, `anon`, `authenticated`, `PUBLIC`, or `service_role` table access and no policy. The currently approved import authority is therefore a separately reviewed SQL artifact executed by a database owner. A later trusted ingestion service would require its own reviewed least-privilege migration.

## Catalog Links And Quality

`foods.ingestion_id` and `food_aliases.ingestion_id` are nullable restrictive foreign keys. Existing private custom foods and existing compatibility rows are not backfilled. Custom foods cannot acquire ingestion authority. A canonical row in `reviewed` or `verified` quality must reference a ledger artifact.

Member canonical visibility requires all of:

- `catalog_scope = 'canonical'`
- `status = 'active'`
- `quality_status in ('reviewed', 'verified')`
- a non-null ingestion reference

Owned custom-food visibility is unchanged. Other-user custom foods remain hidden.

Alias visibility requires an active `reviewed` or `verified` alias and a visible parent food. Pending aliases remain hidden.

## Ambiguous Alias Rule

`food_aliases.is_preferred` is an explicit reviewer decision. Preferred aliases must be reviewed/verified Dutch aliases with a market code. A partial unique index permits only one active preferred row for a normalized alias plus market. This prevents a term such as `rijst` from silently giving raw/dry and cooked foods equal preferred authority. Other variants use explicit labels such as `rijst droog` and `rijst gekookt`.

Raw and cooked foods remain separate canonical UUIDs. Search deduplicates only duplicate matches for the same food UUID; it never merges distinct foods or provider identities.

## Alias-Aware Search

`fmz_phase4_search_foods(text, integer, text, uuid)` keeps its exact frontend signature and returns `setof public.foods`. No ledger fields are added to the response.

The deterministic order is:

1. Exact barcode for a visible canonical row.
2. Exact owned custom-food name.
3. Exact reviewed Dutch alias, with NL market and explicit preferred status first.
4. Exact canonical name, then brand.
5. Owned custom prefix.
6. Reviewed Dutch alias prefix, then other reviewed alias languages.
7. Canonical name prefix, then brand prefix.
8. Controlled alias trigram match with market, preferred status, review priority, and similarity.
9. Controlled custom/canonical trigram match.
10. Lowercase canonical name and food UUID as final stable tie-break.

Every source branch is capped at 250 candidates. Final pages remain between 1 and 50 rows. The current frontend continues sending the last canonical `name` and `id`; the RPC recomputes that food's complete rank for the same query and performs keyset comparison on rank, name, and UUID. No `OFFSET` scan is introduced.

The current signature has no locale parameter. Search therefore preserves NL/EN/DE compatibility by searching reviewed aliases in all supported languages while applying the locked Dutch local-catalog relevance to NL aliases and the NL market. It does not infer or fabricate translated labels.

Existing Slice 4B prefix and `pg_trgm` indexes are reused. Slice 4E adds only ingestion-reference indexes and the narrow preferred-NL-alias uniqueness index.

## Reviewed Dutch Catalog Artifact

The first manifest contains 64 reviewed generic canonical foods and 197 reviewed aliases. Category coverage is carbohydrates 17, dairy 7, fats/basics 7, fruit 8, legumes 4, protein 11, and vegetables 10. Ten explicit raw/dry-versus-cooked pairs cover Atlantic salmon, brown rice, chicken breast, ground turkey, lean beef, pasta, potato, sweet potato, white rice, and whole-wheat pasta.

Nine ambiguous Dutch aliases have one intentional preferred NL interpretation: `aardappel`, `pasta`, `rijst`, `zoete aardappel`, `melk`, `kalkoengehakt`, `kipfilet`, `mager rundvlees`, and `zalm`. The manifest documents each decision. Known local gaps are `magere kwark`, `halfvolle kwark`, `skyr`, and Dutch product-specific bread types. They are not approximated or padded. Generic whole-wheat bread is included; USDA 2% reduced-fat milk is retained with an explicit 2% label and reviewed `halfvolle melk` search alias as the closest approved generic record.

The records come from pinned official USDA detail datasets: Foundation 2026-04-30, FNDDS 2021-2023 release 2024-10-31, and SR Legacy 2018-04. Archive and extracted-JSON hashes are stored in the manifest. Nutrients use the existing `phase4_usda_v1` detail-record mapping per 100 g. Missing fiber remains `null`; no missing value is converted to zero and no volume/mass assumption is made.

Canonical food UUIDs use UUIDv5 namespace `23440733-7e58-4c21-ad15-591eae6ab8ac` and exact name `usda_fdc:<fdcId>`. Alias UUIDs are deterministic under their canonical food UUID. The single ingestion identity is `92fbeedd-63a8-5d22-9000-24e2a16189f1`.

## Import Idempotency

The reviewed seed uses one transaction and embeds the exact manifest. It validates the current ledger state, replays or inserts the ingestion artifact, foods, and aliases, compares every deterministic identity to the expected payload, verifies exact counts and zero portions, and only then transitions the ledger to `imported`. A replay creates no duplicate and performs no silent overwrite; any identity collision or payload drift raises an exception and rolls back the transaction. It contains no `DELETE`, `TRUNCATE`, custom-food mutation, remote call, or legacy mutation.

## Artifacts

- Migration: `supabase/migrations/20260821214541_phase4_nutrition_slice4e_ingestion_alias_search.sql`
- Migration SHA-256: `A19FF1AA8DAEC57CD61A8DB5FEB19F1A98FD049838EA1F1B7B6C7E3B3C32B54C`
- Read-only verifier: `supabase/verification/20260821214541_phase4_nutrition_slice4e_ingestion_alias_search_verification.sql`
- Verifier SHA-256: `98B22C8CEC13B6E688B1CA363A18EF9D69C6805A826B77F531FF4D7F591AEB49`
- Invalidated verifier SHA-256: `81393E24CF04E853FEF6DCB131503A56ABD154B9DABFFB9AF53A2522752C219C`
- Static/security suite: `assets/phase4-nutrition-slice4e-static-check.js`
- Static/security result: PASS, 153 checks.
- Catalog generator: `supabase/catalog/generate_phase4_dutch_catalog.py`
- Reviewed manifest: `supabase/catalog/20260822_phase4_dutch_catalog_manifest.json`
- Manifest SHA-256: `5E9D8ED2C70125794F869827FC835A62BED56749CB23792E4225310E8F6864D5`
- Deterministic seed: `supabase/seeds/20260822_phase4_dutch_catalog_seed.sql`
- Seed SHA-256: `567B6E6A63E93329B5B696B4631331716DE53E05AC08CD32DDD37ACE7A38886B`
- Post-import verifier: `supabase/verification/20260822_phase4_dutch_catalog_import_verification.sql`
- Post-import verifier SHA-256: `E27C09762C2C853AC1C2DE1AB75498297155DD9B698C5B006A74124CCEEAED51`
- Catalog static/security suite: `assets/phase4-nutrition-slice4e-catalog-static-check.js`
- Catalog static/security result: PASS, 1908 checks.

The foundation verifier is one SELECT/CTE statement, invokes no application RPC, returns `overall_pass`, and checks ledger schema/security, restrictive links, quality policies, alias ranking, keyset pagination, frozen Slice 4B/4C/4D contracts, and all expected RLS guard tables. Its corrected live staging rerun passed all 27 checks. The separate post-import verifier is also one SELECT/CTE statement; it verifies the exact imported artifact, row counts, UUID/link integrity, generic USDA provenance, nutrients, aliases, raw/cooked separation, required Dutch terms, and zero portions.

## Review Gate

The Slice 4E foundation migration and corrected verifier are live and accepted on staging. The manifest, seed, and post-import verifier are review artifacts only. Catalog import remains blocked until the owner separately reviews the immutable hashes and gives an explicit staging-only execution instruction. This preparation performed no database, frontend, Edge, production, or legacy-data change.
