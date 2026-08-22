# Phase 4 Nutrition Slice 4E - Dutch Local Catalog Foundation

Status: LOCAL IMPLEMENTATION COMPLETE / MIGRATION REVIEW REQUIRED / NOT EXECUTED

Environment guard: staging project `mokxyyullfhkfalopbzd` only. Production is forbidden.

## Locked Scope

Slice 4D remains complete and frozen. Slice 4E prepares a reviewed Dutch local canonical catalog without importing catalog rows. USDA generic foods are the approved future source. Open Food Facts branded foods, NEVO, barcode, media, AI, trainer catalog access, and legacy Nutrition mutation remain outside this slice.

Catalog imported: NO

Migration executed: NO

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

## Future Import Idempotency

A future separately reviewed manifest must use:

- one unique artifact SHA and one provider/version identity;
- deterministic canonical food UUIDs;
- deterministic alias UUIDs;
- explicit ingestion links on reviewed/verified canonical foods and provider aliases;
- a new artifact row and predecessor for changed content;
- one transaction, no `TRUNCATE`, no delete-all, and no silent replacement.

The same artifact cannot create a second ledger row. Existing provider identity and alias identity indexes continue preventing duplicate canonical foods and aliases. No 64-food manifest or seed exists in this slice.

## Artifacts

- Migration: `supabase/migrations/20260821214541_phase4_nutrition_slice4e_ingestion_alias_search.sql`
- Migration SHA-256: `A19FF1AA8DAEC57CD61A8DB5FEB19F1A98FD049838EA1F1B7B6C7E3B3C32B54C`
- Read-only verifier: `supabase/verification/20260821214541_phase4_nutrition_slice4e_ingestion_alias_search_verification.sql`
- Verifier SHA-256: `81393E24CF04E853FEF6DCB131503A56ABD154B9DABFFB9AF53A2522752C219C`
- Static/security suite: `assets/phase4-nutrition-slice4e-static-check.js`
- Static/security result: PASS, 139 checks.

The verifier is one SELECT/CTE statement, invokes no application RPC, returns `overall_pass`, and checks ledger schema/security, restrictive links, quality policies, alias ranking, keyset pagination, frozen Slice 4B/4C/4D contracts, and all expected RLS guard tables.

## Review Gate

The exact migration and verifier require owner/external SQL review. No migration may be executed before a separate staging-only GO. After execution, the exact read-only verifier must return `overall_pass = true` before any catalog manifest is created or imported.
