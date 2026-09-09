# Package 6E-1 Offline Contracts

COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE CONTRACTS ONLY.
Owner accepted O1-O5 on 2026-09-09. Phase 6E remains incomplete; no live GO.
Only synthetic, deterministic in-memory Node experiments. No dependencies, providers,
database, browser adapter, bundler, timers, storage, worker or scheduler.

Run from repository root:
```text
node --test _offline/phase6e1/test/*.test.cjs
node _offline/phase6e1/test/examples.cjs
```

The 23 frozen phase6e0 files remain byte-identical. Only four frozen JSON sources
are reused read-only; the old request/review flow is not used. D1-D12 remain intact.
No clinical validation or live authorization follows from tests.

- contract.json: versions, boundaries and open decisions.
- context.cjs: text to context, exact original spans, provisional copy and uncertainty.
- flow.cjs: immutable branded synthetic state, scoped attempts and self-report.
- content-contract.json / analysis.cjs: allowlisted aggregate facts and comparisons.
- retention.cjs: O5 minimal-record projection capped at 30 days from first registration;
  separate existing D5 30/90/180 what-if diagnostics. All storage stays off.
- preregistered-cases.json: 42 new cases + 79 frozen language cases, 25 contract scenarios.
- test/examples.cjs: five complete message/feedback/analysis/recovery examples.

Warning copy remains a product concept. Recovery is a self-report, never clearance.
Descriptive content is owner-accepted offline, not expert-validated; recommendations
are not implemented, actions are off. Older `bounded_descriptive_proposal` protocol
tokens are retained for compatibility, not an outstanding O3 owner decision.
A missing global recommendation policy is not a permanent member health block.
Branded objects and injected authority are only simulator guards, not server proof.
Historical in-memory events are not a proposal for indefinite retained health data.

O5 usage: `projectSafety(state, nowMs, options, previousProjection)` returns only
date/status/message-reference records. Always pass the previous result in the same
simulation sequence, including after earlier unnecessary removal. Null initializes
a new synthetic experiment, NOT a reset/new-chat/production rehydration path.
Retry keeps the first source anchor. Every status expires at that same 30-day cap;
no expired IDs/text/sentinel records are returned. Missing sources can be simulated
without reconstruction; genuine new reports get a new first registration.
`plan()` is a diagnostic comparison for distinct D5 purposes, never an O5 storage
payload or a way to relabel an expired record into a longer-lived class.
The injected clock/source state and revision watermark are not durable storage,
restart, concurrency, trusted server lineage or real deletion proofs. Privacy,
legal, medical and native-language review remain open for any future live scope.

Read docs/PHASE6E1_CONTRACTS.md, docs/PHASE6E1_OWNER_OVERVIEW.md and
docs/PHASE6E1_FREEZE_RECEIPT.md for accepted scope, expert gates and source evidence.
Files under this directory must remain excluded from the public Pages site.
