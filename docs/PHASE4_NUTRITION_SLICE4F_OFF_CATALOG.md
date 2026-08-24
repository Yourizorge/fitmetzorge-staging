# Phase 4 Nutrition Slice 4F - Open Food Facts Catalog Foundation

Status: LOCAL FOUNDATION READY FOR MIGRATION REVIEW. No SQL execution, OFF import, frontend deployment, Edge change, scanner runtime, or production change has occurred.

## Frozen Baseline

Slice 4E is accepted and frozen. Its 64 reviewed USDA generic foods remain canonical `public.foods` rows with their original `usda_fdc:<fdcId>` identities and English canonical names. Slice 4F does not mutate those rows, the 197 aliases, existing custom foods, member logs, provider caches, legacy Nutrition, or trainer Nutrition.

## ODbL Boundary

Open Food Facts data lives in a separate, extractable ODbL catalog domain:

- `public.nutrition_off_catalog_releases` stores pinned-source and normalized-artifact audit identity.
- `public.nutrition_off_products` stores current OFF product records keyed by normalized GTIN-14.
- `public.nutrition_off_product_names` stores localized and search names without mixing them into USDA aliases.

OFF rows are never inserted into `public.foods`. Unified search combines typed result sets at query time and retains `off_branded_food`, `generic_food`, and `custom_food` source identity. Member logs and other proprietary FitMetZorge data remain outside the OFF catalog domain.

The member UI can show a concise `Open Food Facts` source label on branded product details and a persistent About/data-sources attribution linking to Open Food Facts and the ODbL 1.0 terms. An export or substantial extraction of the OFF database domain must preserve attribution, notice, and applicable share-alike obligations. This engineering contract does not replace final legal review before production.

## Release And Identity

Each release records the source revision and timestamp, source and normalized SHA-256 values, Netherlands source count, eligible/imported counts, mapping version, predecessor, reviewer, ODbL metadata, provenance, and timestamps. Releases enter as `reviewed`, may transition to `imported` or `rejected`, and an imported release may become `superseded`. There is no removal workflow. Exactly one release per provider may be current with status `imported`.

The permanent namespace is `23440733-7e58-4c21-ad15-591eae6ab8ac`. Product identity is:

`UUIDv5(namespace, "open_food_facts:<normalized_gtin14>")`

The database validates EAN-8, UPC-A, EAN-13, and GTIN-14 check digits, left-pads valid inputs to GTIN-14 without discarding the original barcode, enforces the identity prefix and UUIDv5 result, and makes normalized GTIN and provider identity unique. A duplicate source conflict produces one quarantined normalized product with reviewed conflict provenance; it is never silently selected as nutrition authority.

## Product Quality

Nutrition bases are exactly `per_100_g` and `per_100_ml`; no density or `1 ml = 1 g` assumption exists. Energy, protein, carbohydrates, and fat are finite and bounded. Fiber may be absent. Only active `complete` or `reviewed` products with all required nutrition fields are searchable and loggable. `complete` means the automated acceptance contract passed; it does not mean FitMetZorge independently verified the community record. Incomplete, quarantined, and archived rows are excluded.

Image references are optional. No images are downloaded in this slice. A retained image reference requires separate CC BY-SA 4.0 attribution metadata; product search and logging cannot depend on images.

## Search And Barcode

The frozen `fmz_phase4_search_foods` RPC is unchanged. The new `fmz_phase4_search_nutrition_catalog` RPC is authenticated, `SECURITY INVOKER`, stable, page-capped at 25, keyset-paginated, and source-typed. It ranks exact barcode, exact own custom name, exact Dutch OFF name, other exact OFF name, brand relevance, reviewed Dutch generic aliases, prefixes, and controlled trigram candidates. Every candidate branch is bounded before a global cap and final page ordering. Prefix, indexable trigram, quality-partial, release, and exact GTIN indexes cover the expected 24,458 products and 50,000-90,000 name rows. The keyset comparison and returned cursor apply the same trimmed/lowercased display-name normalization.

`fmz_phase4_lookup_off_product_by_barcode` performs authenticated local exact lookup only. It makes no network request, creates no member row, and returns only active complete/reviewed OFF nutrition. Camera scanning and feature-entitlement UI remain later work.

## Future Logging

OFF logging is not implemented here. The future trusted flow is member selection -> authenticated backend resolution of the current active OFF row -> quality and basis validation -> server-authored immutable snapshot -> member log. The snapshot must retain product name, brand, original and normalized barcode, basis, nutrients, provider, licence, attribution, OFF revision, source checksum, and derivation. Historical truth must never depend on later OFF refreshes.

An unknown barcode will later follow local miss -> backend exact OFF lookup -> validation -> optional reviewed ODbL ingestion/cache -> typed result. A provider miss routes to private custom-product creation. It does not promote a community record into `public.foods`.

## Refresh And Import Gate

The future deterministic flow is pinned OFF snapshot -> Netherlands filter -> food/drink filter -> valid GTIN -> name and brand -> explicit basis -> complete macros -> quality-error exclusion -> deterministic manifest -> artifact SHA-256 -> reviewed one-transaction import -> read-only verification.

The accepted source audit found 106,650 Netherlands-associated rows and exactly 24,458 currently eligible branded products. No import artifact or rows are included in this slice. A later artifact must lock the pinned source, exact counts, deterministic record/name IDs, checksums, conflict quarantine report, zero synthetic padding, and expected post-import counts. A count change requires a documented source or transformation change and a new review.

Refreshes compare deterministic GTIN identity and checksums. New rows are inserted, changed current records are refreshed under a successor release, regressions are quarantined, and missing records are marked stale before any separately reviewed archive decision. Existing member snapshots remain unchanged.

## Access Contract

RLS is enabled on all three OFF tables. Authenticated members get column-scoped SELECT only on safe active complete/reviewed product and name fields; release IDs, source revisions, checksums, provenance, completeness metadata, import metadata, and ingestion timestamps remain outside the browser ACL. The release ledger has no client policy or grant. `anon`, `PUBLIC`, `service_role`, and trainer-specific routes receive no direct OFF table authority. Import uses only a separately reviewed owner SQL artifact. Browser code contains no service-role credential.

## Dutch Display Labels

The local presentation-only fix uses `foods.metadata.dutch_display_label` in the NL member UI and otherwise falls back to the immutable canonical name. Search results, selected food, logging dialog, logged day item, and item details share one display helper. Visible day items hydrate at most 200 own-visible food metadata rows with a read-only query and duplicate-request suppression. EN and DE continue showing canonical names. No canonical identity, snapshot, logging RPC, Nutrition calculation, or database row is changed.

## Artifacts

- Migration: `supabase/migrations/20260824113551_phase4_nutrition_slice4f_off_catalog_search.sql`
- Migration SHA-256: `606658F53EA29083E315F43546B507B40C9D0CF7D02FB074591B542E71D89AF4`
- Verification: `supabase/verification/20260824113551_phase4_nutrition_slice4f_off_catalog_search_verification.sql`
- Verification SHA-256: `4772BF4550978572BE6DD0D595A42E145FB2DF7D29D7008FF3F87934A12F967D`
- Static/security suite: `assets/phase4-nutrition-slice4f-static-check.js`
- Static/security result: PASS, 125 checks. Final review replaced the old artifact hashes after adding indexable trigram predicates, aligning the cross-language prefix index, removing an unused product GIN index, making keyset name normalization symmetric, restricting authenticated catalog access to explicit safe columns, and strengthening release-identity and exact-ACL verification. Full PostgreSQL, PL/pgSQL, JavaScript, combined-browser parse, frozen regression, responsive browser, and security scans also pass. The Dutch label runtime and its focused regression changes remain local because pushing loaded runtime assets to the Pages-backed `main` branch would be a frontend deployment.

Migration executed: NO

OFF products imported: NO

Frontend deployed: NO

Edge Function changed: NO

Production touched: NO
