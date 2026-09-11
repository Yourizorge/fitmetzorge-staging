# Package 6E-6 Offline

TECHNICAL IMPLEMENTATION / OWNER REVIEW REQUIRED. No live integration.
Run: node _offline/phase6e6/test/verify.cjs (repository root).
Pure core: rules.cjs, facts.cjs, engine.cjs, review.cjs, copy.json.
Frozen 6E-0..6E-5 read-only. Synthetic fixtures only, no provider or storage.
Rulebook resolves explicit exercise/type rules into the frozen 6E-5 rule contract.
No implicit precedence, default thresholds, conversion or rounding.
Member/trainer/application are separate; transaction simulator retains old plan,
source identities and hash-chained audit in one in-memory aggregate publication.
No durable database transaction, live trainer attestation or medical validation.
See docs/PHASE6E6_CONTRACTS.md and docs/PHASE6E6_OWNER_OVERVIEW.md.
