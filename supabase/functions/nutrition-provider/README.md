# Phase 4 Nutrition Provider Edge Function

Status: search, lookup, transient provider logging, atomic replacement and historical same-food
replacement resolver support are live on staging. The Edge replay orchestration resolves an active
replacement snapshot only when the active-only original resolver reports the exact unavailable
condition; the existing database RPC remains authoritative for idempotent replay validity.

## Identity

`PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE` is permanently fixed to
`23440733-7e58-4c21-ad15-591eae6ab8ac`. Candidate UUIDs use UUIDv5 with exact name
`provider_code:provider_food_id`. USDA therefore uses `usda_fdc:<fdcId>`. The namespace is
non-secret and shared across environments. The Phase 3 exercise namespace remains separate and
frozen.

## Routes

- `POST /nutrition-provider/search`: authenticated, bounded USDA Foundation, Survey (FNDDS), and SR
  Legacy search.
- `POST /nutrition-provider/lookup`: authenticated detail lookup using only a current HMAC-signed
  candidate token returned by search.
- `POST /nutrition-provider/log`: authenticated, gram-only transient provider-snapshot logging.
  The browser supplies only the signed candidate token and ordinary log inputs. The function
  revalidates the candidate and calls the service-role-only logging RPC.
- `POST /nutrition-provider/replace`: authenticated atomic replacement of an existing provider
  snapshot item. A supplied candidate token keeps the existing new/different-food path. Without a
  token, the Edge Function uses the service-role-only historical resolver, validates the returned
  immutable provider identity, and revalidates it through the same cache-first/controlled USDA
  lookup path. The original item is archived in the database transaction that creates its
  replacement. On an exact retry after that archive, the Edge Function may resolve the supplied
  active replacement item only to re-establish trusted candidate authority. It then delegates all
  original/replacement linkage, request identity and payload equality checks to the same atomic
  database RPC.

There is no ingest route. Logging and replacing candidates never creates canonical `foods`,
`food_portions`, or `food_aliases` rows.

The historical resolver never returns a candidate token or nutrient authority to the browser. It
accepts only the authenticated member identity established by the Edge Function and the original
item UUID, and it rejects archived, canonical, custom, cross-user, or malformed provider rows.

## Runtime boundary

- Validates the Supabase bearer user with `auth.getUser()`.
- Accepts only staging origins `https://yourizorge.github.io` and `https://test.appfmz.nl`; the
  GitHub Pages path is not part of the browser `Origin` header.
- Uses only the fixed USDA FoodData Central host.
- Reads/upserts the private Slice 4C cache tables through the server-only service role.
- Uses the reviewed internal RPCs for atomic shared rate limiting and circuit transitions.
- HMACs user/query identity. Raw queries and user IDs are not stored or logged.
- Binds rate-limit replay identity to request ID plus route and operation so a request UUID cannot
  be reused for a different provider call. Operation identity uses canonical structured
  serialization rather than delimiter-based concatenation.
- Revalidates checksums, exact payload shape, deterministic candidate identity, nutrition bounds,
  attribution, provenance, and portions before serving any query or food cache hit.
- Returns bounded normalized candidate data and attribution; never raw USDA payloads or secrets.
- Search and lookup write only provider operational state. Slice 4D log/replace writes immutable
  member `food_log_items` snapshots through two reviewed service-role-only RPCs. It never writes a
  canonical food, alias, or portion.

## Transient provider snapshot contract

- USDA provider items use `food_id = NULL` and `food_portion_id = NULL`.
- The calculation reference is fixed at 100 g and consumption is grams only. No serving, piece,
  millilitre, density, or inferred conversion is accepted.
- Candidate UUID, provider food ID, mapping version, accepted USDA data type, source version,
  retrieval/source timestamps, derivation, attribution, and provenance are stored with immutable
  nutrition snapshots.
- The browser cannot send user identity, provider identity, nutrition authority, canonical food ID,
  role, package, or entitlement data.
- Stable item/request UUIDs, request-payload equality checks, transaction advisory locks, and the
  existing unique request index provide retry idempotency. Changed payload reuse is rejected.
- Free history remains the current local day plus six prior local dates. Current Pro, AI, and
  personal-coaching entitlements retain the existing full-history contract.
- Existing `fmz_phase4_archive_food_log_item` remains the only member archive route and supports
  provider rows because it does not require `food_id`.

## Required secret names

- `USDA_FDC_API_KEY`
- `FMZ_PROVIDER_HMAC_KEY`

The runtime also consumes Supabase's default URL, publishable/anon key, and secret/service-role key
environment variables. No value is stored in source.

## Dependencies

The sole external runtime import is exactly pinned to `npm:@supabase/supabase-js@2.95.0`.
`deno.lock` records the complete transitive dependency graph and integrity hashes; `deno.json`
enforces the lock in frozen mode. There are no dynamic, JSR, or arbitrary remote imports.

## Mapping

Mapping version is `phase4_usda_v1`. Nutrients are normalized per 100 g. The explicit USDA IDs are
protein 1003, fat 1004, carbohydrate 1005, fiber 1079, energy 2048/2047/1008, and kJ fallback 1062
divided by 4.184. Missing required macros, negative/excessive nutrients, invalid identity/type, and
materially conflicting energy are rejected. Portions require an explicit positive USDA `gramWeight`;
no volume/mass density is inferred.

## Local checks

Run with the workspace Node runtime:

```powershell
node --experimental-strip-types --test supabase/functions/nutrition-provider/nutrition-provider.test.ts
node assets/phase4-nutrition-provider-static-check.js
```

The final dependency gate additionally runs `deno check --frozen index.ts` and
`deno test --frozen nutrition-provider.test.ts`.

Tests use dependency-injected in-memory adapters. They do not contact Supabase or USDA and do not
require secrets.
