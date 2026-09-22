# Offline Fingerprint Preregistration

22 September 2026. NO-GO remains; no hosted database connection is permitted.
Baseline staging main: 96fc380e47420474efde5509eab0a944398b1190.
Existing runtime candidates, frozen sources, old measurements and missing pair 113
are retained. Only new offline code/tests and scoped documentation may be pushed.

Before implementation, required cases:
- 143-table inventory, all columns; raw and protected cohorts and synthetic/retained
  subcohorts; empty tables, NULL ownership and all historical exclusion branches.
- Insert/update/delete, duplicate identical rows, duplicate multiplicity, shuffled
  order, dropped table, schema change and mismatched expected inventory.
- JSON/JSONB, arrays with NULL, timestamps with time zones, interval, numeric scale,
  floats, Unicode including distinct normalization forms, bytea and null/empty.
- Same pinned canonicalization must match old PostgreSQL row/table hashes exactly.
  Show explicitly whether unpinned old timestamps differ across TimeZone settings.
- Fresh identical runs must have byte-identical identity manifests, while operational
  receipts retain distinct run IDs/times. Do not demand identical operational logs.
- Midstream error, omitted row, missing terminal acknowledgement, connection exit,
  corrupt chunk, timeout and process interruption must never create a PASS.
- Single-cycle lock, process lock, persisted budgets, no automatic retry, query and
  byte/row/time limits; 649 repeated full cycles must be rejected well before 649.
- Missing direct after measurement must block next action and cleanup.
- Benchmark old/new on the same synthetic data in a disposable local PostgreSQL
  cluster; measure client/server counters separately and disclose cache limitations.
- No weakened bookend-only preservation: targeted-measurement mode requires a proven
  complete write-coverage certificate and remains disabled in this scope.

Local PostgreSQL 18 is installed; hosted uses 17. Cross-major equivalence and exact
historical session settings remain explicit gates, not assumptions.
No raw personal data, Supabase credentials, provider calls or live fixtures.
