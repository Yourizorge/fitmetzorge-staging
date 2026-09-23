# PG17, Write Coverage And Canary Preregistration

22 September 2026. Baseline 7883c2a90c7bed9e6bb27dbabf11ddedce0d08de.
No hosted fingerprints, mutations, cleanup or owner window admitted by this file.

Before new implementation/tests:
- Run the existing 36 collector tests and 143-table benchmark on isolated PG17.6,
  never substitute PG18. Verify major/minor, immutable source hashes and provenance.
- Add explicit tests for staging's observed extra_float_digits=0 versus pinned=3,
  locale/DateStyle differences and multiplicity, without rewriting old expectations.
- Register all source-bound A/B, denial/replay, Auth, management and cleanup actions.
  Distinguish known direct writes from unproven service/trigger/cascade closures.
- Fail on unknown routes, missing pair contracts, missing after_saved, premature
  cleanup, stale source manifests, added mutation sources and budget overruns.
- Bind evidence to run, step, actor, request and scope, with immutable receipts.
- Count SQL commands separately from tables. A UNION ALL visits 143 tables in one
  content query, but targeted transactions and action calls also consume budget.
- Persist a fail-closed canary decision: PG17 + complete coverage + stable IO +
  valid historical expectation + bounded streaming transport are all mandatory.
- At most two lightweight resource scrapes and three SQL metadata samples, no
  stats reset and no member row payload. A failed gate means zero hosted cycles.

Retain all historical evidence, dirty runtime and frozen AI sources. Any local
test clusters are newly created outside OneDrive and stopped without deleting files.
