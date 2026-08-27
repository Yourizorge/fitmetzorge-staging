# Phase 4 Nutrition Package 4F-D - Transient OFF Barcode

Status: LOCAL IMPLEMENTATION AND FINAL REVIEW PASS / CONSOLIDATED STAGING GO REQUIRED

## Contract

Barcode discovery is local-first. The backend resolves active persistent OFF, reviewed generic and own custom identities before any network request. A true miss uses one exact authenticated Open Food Facts product lookup. The server validates GS1 Mod-10 identity, Netherlands relevance, product name and brand, explicit `per_100_g` or `per_100_ml`, bounded required macros, source revision/checksum and ODbL identity. It returns a 15-minute signed candidate derived from `open_food_facts:<normalized_gtin14>` under the permanent Phase 4 provider namespace.

Runtime OFF candidates never mutate the persistent release catalog or `public.foods`. Logging and replacement run through service-only backend adapters and write immutable source, nutrition and licence snapshots with null canonical food identities. Browser input is limited to the signed token plus normal member log controls. Existing day totals, history boundaries, stale guards, request identity, archive behavior and atomic replacement remain authoritative.

## Mobile Scanner

The member starts the camera explicitly. Native `BarcodeDetector` is preferred; vendored ZXing Browser 0.2.1 is the reviewed MIT fallback. Video frames never leave the device and every media track stops on close or route change. One decoded code triggers one lookup and never logs automatically. Manual EAN/UPC/GTIN entry uses the same server path. A provider miss offers private custom-food creation with the normalized barcode prefilled.

## Reviewed Artifacts

- Migration: `supabase/migrations/20260827_phase4_nutrition_slice4fd_transient_off_barcode.sql`
- Migration SHA-256: `476F829A2C669C029B87BEC9F24459F7E1F5430D02FB32559C50CD9C418C2A2B`
- Read-only verifier: `supabase/verification/20260827_phase4_nutrition_slice4fd_transient_off_barcode_verification.sql`
- Verifier SHA-256: `5D1DED2671AF128FF3C2024B41321162211C5FCCE4D72EA0047BB45D41115C59`
- Edge routes: `off-barcode`, `off-log`, `off-replace`
- Runtime cache: `20260827-phase4fd-barcode1`
- ZXing bundle SHA-256: `066BC34EDFCDD4A33F0964AEEC967752A0DEA1CCAF36E58E319AC9FCB5070F6A`

## Execution Gate

One owner GO must authorize the additive migration on staging `mokxyyullfhkfalopbzd`, its exact read-only verifier, Edge deployment, controlled authenticated barcode/log/edit/archive E2E, and only then the scanner frontend deployment. The migration explicitly stops if pre-existing active duplicate custom-food GTINs need owner review. No automatic cleanup occurs. Production remains blocked.
