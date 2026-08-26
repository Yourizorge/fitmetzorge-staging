# Phase 4 Nutrition Slice 4F - Open Food Facts Catalog Foundation

Status: 4F-A COMPLETE / FROZEN; 4F-B OWNER-ACCEPTED / FROZEN; 4F-C LOCALLY READY / STAGING GATE REQUIRED. The isolated catalog contains exactly 24,458 products and 74,184 source-derived names. Unified search performance and the Dutch branded selection UX are accepted. Authoritative OFF logging/edit/archive is implemented locally without deploying its additive function migration or frontend runtime. Production remains untouched.

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

## Package 4F-C Authoritative Logging

The reviewed 4F-C flow is member selection -> authenticated database RPC -> server-side resolution from the current imported, active, complete/reviewed OFF product -> exact `per_100_g` or `per_100_ml` validation -> immutable nutrition and ODbL snapshot -> authoritative day payload. The browser sends only OFF identity, quantity/unit and normal log controls; it never supplies nutrients, density or licence authority. Historical truth therefore does not depend on a future OFF refresh.

4F-C reuses `food_logs`, `food_log_items`, `fmz_phase4_day_payload`, the existing archive RPC, Free seven-day history, Pro/AI/PT entitlement behavior and the established request/object advisory-lock namespaces. It adds no table, no policy, no trainer route and no parallel logging model. Same-product and changed-OFF-product edits insert a new immutable row and archive the original in one transaction with optimistic `updated_at` conflict protection and equality replay.

An unknown barcode will later follow local miss -> backend exact OFF lookup -> validation -> optional reviewed ODbL ingestion/cache -> typed result. A provider miss routes to private custom-product creation. It does not promote a community record into `public.foods`.

## Refresh And Import Gate

The future deterministic flow is pinned OFF snapshot -> Netherlands filter -> food/drink filter -> valid GTIN -> name and brand -> explicit basis -> complete macros -> quality-error exclusion -> deterministic manifest -> artifact SHA-256 -> reviewed one-transaction import -> read-only verification.

The accepted source audit found 106,650 Netherlands-associated rows and exactly 24,458 eligible branded products. The reviewed local artifact contains 24,458 unique GS1-valid GTIN-14 identities, 24,458 deterministic UUIDv5 product identities, 20,355 `per_100_g` products, 4,103 `per_100_ml` products, 18,970 Dutch product names, and 74,184 truthful source-derived name/search rows. No synthetic padding, fabricated translation, image download, duplicate identity, or post-filter macro rejection is present. A count change requires a documented source or transformation change and a new review.

Catalog text normalization is owned by the already-live PostgreSQL function `public.fmz_phase4_normalize_catalog_text(text)`: lowercase, boundary trim, replacement of non-POSIX-alphanumeric runs by a space, whitespace collapse, and final trim. Generation performs no NFC/NFD/NFKC/NFKD normalization and no transliteration. Independent fixtures cover trademark and ordinal symbols, subscripts, composed/decomposed accents, Thai, Korean, punctuation, whitespace, mixed strings, brands, and names. Correcting the former Python compatibility-normalization mismatch changed one product row, one normalized brand and 23 name rows/name UUIDs. All 24,458 product UUIDs and GTIN identities remain byte-for-byte stable; total name count remains 74,184.

The approved bulk-import transport is file-based and hash-gated. It uses one deterministic product CSV, one deterministic source-derived names CSV, and one reviewed `psql` importer. `psql` loads both files into temporary staging tables inside one transaction, validates the exact source/release/count/GTIN/UUID/macro/name contracts, blocks identity drift, inserts only exact missing identities, and changes the release from `reviewed` to `imported` only after the complete product and name sets validate. A failure rolls back the release, products, and names together. An exact replay is safe; an unequal replay fails. No manual SQL chunks, remote calls, removal statements, custom-food writes, USDA writes, member-log writes, image downloads, or production references are permitted.

The pinned input is `food.parquet` at immutable revision `e544a38353692b2df59df78f47393990a578eb8e`, published `2026-08-23T18:34:47Z`, byte size `7,797,955,269`, and SHA-256 `38D7A48D32F574812490024AA77FB064E84B041CB2687E46DF87AFCE441100C2`. The immutable Hugging Face commit-tree LFS object metadata is the source identity gate. The reproducible local extractor additionally requires the complete local source file to match the exact byte size and SHA-256 before transformation, pins DuckDB 1.4.1, and produces the locked 106,650-row Netherlands extract. Transformation uses only `countries_tags` association and the accepted Slice 4F eligibility contract; barcode prefix 87 is never inclusion authority.

Refreshes compare deterministic GTIN identity and checksums. New rows are inserted, changed current records are refreshed under a successor release, regressions are quarantined, and missing records are marked stale before any separately reviewed archive decision. Existing member snapshots remain unchanged.

## Access Contract

RLS is enabled on all three OFF tables. Authenticated members get column-scoped SELECT only on safe active complete/reviewed product and name fields; release IDs, source revisions, checksums, provenance, completeness metadata, import metadata, and ingestion timestamps remain outside the browser ACL. The release ledger has no client policy or grant. `anon`, `PUBLIC`, `service_role`, and trainer-specific routes receive no direct OFF table authority. Import uses only a separately reviewed owner SQL artifact. Browser code contains no service-role credential.

## Post-import Performance Gate

Artifact file size is not a production-performance claim. After a separately approved staging import, representative `EXPLAIN (ANALYZE, BUFFERS)` and repeated warm-cache measurements must cover exact normalized GTIN, exact Dutch name, exact normalized brand, two-character and longer name prefix, and controlled trigram search through the public search contract. Tests must include first and last keyset pages and mixed generic/custom/OFF result sets. The target is p95 below 150 ms under representative catalog usage; it remains unproven until measured on staging. Table, TOAST, and index sizes must be captured with read-only PostgreSQL size functions after import.

## Dutch Display Labels

The local presentation-only fix uses `foods.metadata.dutch_display_label` in the NL member UI and otherwise falls back to the immutable canonical name. Search results, selected food, logging dialog, logged day item, and item details share one display helper. Visible day items hydrate at most 200 own-visible food metadata rows with a read-only query and duplicate-request suppression. EN and DE continue showing canonical names. No canonical identity, snapshot, logging RPC, Nutrition calculation, or database row is changed.

## Artifacts

- Migration: `supabase/migrations/20260824113551_phase4_nutrition_slice4f_off_catalog_search.sql`
- Migration SHA-256: `606658F53EA29083E315F43546B507B40C9D0CF7D02FB074591B542E71D89AF4`
- Verification: `supabase/verification/20260824113551_phase4_nutrition_slice4f_off_catalog_search_verification.sql`
- Verification SHA-256: `7E5D6CB7859A5BEE733E379ABAD5661FE08FBF680AC984F4D80C5F109B4DECD2`
- Static/security suite: `assets/phase4-nutrition-slice4f-static-check.js`
- Static/security result: PASS, 127 checks. The original live verifier hash `4772BF4550978572BE6DD0D595A42E145FB2DF7D29D7008FF3F87934A12F967D` is invalidated because its column-ACL CTE converted `NULL` ACLs into a zero-dimensional empty `aclitem[]`, causing PostgreSQL `22023`. The corrected verifier explodes nullable `pg_attribute.attacl` values row-wise and preserves the exact least-privilege checks. Read-only live ACL diagnostics confirm RLS, policies, 34 intended authenticated column grants, four intended function grants, and no unexpected anon, PUBLIC, service-role, or trainer authority. Full frozen regression and security checks pass; the corrected full verifier still requires the separately authorized live rerun. The Dutch label runtime remains local because pushing loaded runtime assets to the Pages-backed `main` branch would be a frontend deployment.

### 24,458-product bulk-import bundle

- Source extractor: `supabase/catalog/extract_phase4_off_netherlands.py`
- Deterministic generator: `supabase/catalog/generate_phase4_off_catalog.py`
- Product CSV: `supabase/catalog/20260825_phase4_off_catalog/20260825_phase4_off_products.csv`; SHA-256 `BFB88DFC6C57E2EC4EDA05E29C5F19515E678B7509C0EC4D62BD9686C57F6A9D`
- Name CSV: `supabase/catalog/20260825_phase4_off_catalog/20260825_phase4_off_product_names.csv`; SHA-256 `04E56D0D237CABB77DE2A574D8CEC4A440C15D6824645820920CCB4B220FFAC6`
- Release artifact: `supabase/catalog/20260825_phase4_off_catalog/20260825_phase4_off_release.json`; release UUID `4b487f4f-ac8e-5579-a2a2-d4164c4b368a`; SHA-256 `06A53E9266160767828E1576F982C07CA90D8E74DEA3B20A9096B56507F21F88`
- Artifact manifest: `supabase/catalog/20260825_phase4_off_catalog/20260825_phase4_off_artifact_manifest.json`; SHA-256 `473BDAA8E8611F39C3D20E366FEEF6FD5B165456F50DCFFBEDBFA5EA7B272BAC`
- Normalized artifact SHA-256: `3E826B252B484081CB6D271C73AFFEE70A4B177CAB10E228E46963C5BF63D07D`
- File importer: `supabase/imports/20260825_phase4_off_catalog_import.psql`; SHA-256 `9EEDC73E03FEDCA5ACF8FDFF2A3F77459C1589C710B903C12DFFB7E33EBAE506`
- Post-import verifier: `supabase/verification/20260825_phase4_nutrition_slice4f_off_catalog_import_verification.sql`; SHA-256 `AC0BB83EB1140DCA69468C65832F57C694A833AA3A8E82536A6F4419FC2F902D`
- PostgreSQL normalization verifier: `supabase/verification/20260825_phase4_off_normalization_contract_verification.sql`; SHA-256 `44F18C290E1C5E76DF270F500B814E0A55CE218860F784337256791780F4F0AF`
- Import model: one `psql` transaction, two `\copy` operations into temporary tables, exact-count and identity validation, advisory transaction lock, fail-on-drift, exact replay, and release finalization last. There are no manual chunks.
- Local verification and staging execution: PASS. The corrected artifact passed 779,905 artifact checks, 93 artifact static/security checks, 13 PostgreSQL normalization checks, hash-gated staging import, post-import/normalization verification and the corrected unified-search performance gate. Package 4F-A is complete and frozen.

Migration executed on STAGING: YES

OFF products imported: YES - 24,458

Frontend deployed: YES FOR 4F-B / NO FOR 4F-C

Edge Function changed: NO

Production touched: NO
