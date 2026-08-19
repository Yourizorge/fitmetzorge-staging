# Phase 4 Nutrition Provider Edge Function

Status: local implementation only. Not deployed. No live USDA request has been made.

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

There is no ingest route. Candidates are not canonical `foods` rows.

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
- Writes no canonical food, alias, portion, target, or member log data.

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
