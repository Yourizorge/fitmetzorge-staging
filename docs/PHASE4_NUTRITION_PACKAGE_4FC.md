# Phase 4 Nutrition Package 4F-C - OFF Authoritative Logging

Status: LOCALLY IMPLEMENTED / FINAL REVIEW PASS / STAGING EXECUTION GO REQUIRED

Package 4F-B is owner-accepted and frozen. Package 4F-C connects its selected `off_branded_food` result to the existing normalized Nutrition day architecture without making the browser a nutrient authority.

## Authority Boundary

The member submits an OFF product UUID, quantity, exact source unit, meal, notes and stable retry identifiers. `fmz_phase4_resolve_off_food_snapshot` reads the current imported OFF release and an active complete/reviewed product on the server. It rejects missing required macros, non-ODbL rows, stale releases, mismatched provider identity and revisions that cannot fit the immutable log snapshot.

Mass and volume stay separate. `per_100_g` accepts only `g`; `per_100_ml` accepts only `ml`. No density, portion or `1 ml = 1 g` conversion is performed.

## Persistence And History

`fmz_phase4_log_off_food_item` stores immutable name, brand, normalized GTIN, nutrition, release, mapping, revision, checksum, attribution, ODbL licence and derivation snapshots in `food_log_items` with `food_id = NULL`. The existing authoritative day payload calculates the visible totals.

`fmz_phase4_replace_off_food_log_item` can replace any own active Nutrition item with a selected OFF product. It shares the existing request/object lock namespaces, validates `updated_at`, inserts the replacement and archives the original in one transaction, and returns the authoritative day. The existing archive RPC removes an active item without deleting its history. Generic/custom and USDA paths remain unchanged.

## Security

Both write RPCs derive ownership from `auth.uid()` and expose no user/role/entitlement or nutrient parameters. The resolver and trigger function are not executable by browser roles. Only the two OFF write RPCs grant `EXECUTE` to `authenticated`; `anon`, `PUBLIC` and `service_role` receive no execute grant. Existing table RLS, policies, grants and trainer boundaries are unchanged.

## Artifacts

- Migration: `supabase/migrations/20260826143000_phase4_nutrition_slice4fc_off_authoritative_logging.sql`
- Migration SHA-256: `15C3ABAFDB7D77E85397006BA1D62C9221DA0820C1052AF284911B9EDF2DFF45`
- Supersedes the pre-execution `E5203453E40CF429A5EB0839E8748F1853D3E4099B1ADE6F43FBED8FC01C58EA` artifact after a parser-only parenthesization correction. The failed first execution was transactionally rolled back before this corrected artifact was reviewed.
- Read-only verifier: `supabase/verification/20260826143000_phase4_nutrition_slice4fc_off_authoritative_logging_verification.sql`
- Verifier SHA-256: `271EF1A161829574D7C420C1209A896CD56B5110696395D31046268F364D4E40`
- Prepared runtime SHA-256: `AF1CCCCEDF762E1E36D1813441363CA6B1E502E94B4C8B8D9C065DD1B1BB0801`
- Static/security: PASS, 96 checks
- Browser vertical slice: PASS, 121 checks

Migration executed: NO

Frontend deployed: NO

Production touched: NO
