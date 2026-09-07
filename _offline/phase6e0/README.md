# Package 6E-0 Offline Preparation

Status: TECHNICAL PASS / READY FOR OWNER REVIEW. Not a runtime component.
Owner authority: attachment 2c282c20-0e1e-48fe-8879-2acd41891ade.
Frozen runtime: bc6308fbf0f914b04c7faa711219d9ae46e9cbe3.

## Run

From the staging repository root, with Node 24 or newer and Git available:

```powershell
node --test _offline/phase6e0/test/*.test.cjs
node --test assets/phase6d-theme-authority.test.cjs
```

No npm install, dependencies, Docker, database, secrets, browser, network or temp files
are required. Core calculations and invented fixtures run in memory. Isolation tests
read the repository and invoke read-only Git commands. Run from a checkout containing
the frozen commit, not a shallow export without that history.

## Scope

- contract.json: versioned strict envelopes, five provisional levels, uncertainty,
  access/content/action separation, review gates and provisional retention bounds.
- rules.json / engine.cjs: deliberately limited deterministic lexical/context proposal;
  fixed help copy and allowlisted synthetic facts. No personalized advice implementation.
- state.cjs: revision-bound, subject-bound, in-memory self-report/recurrence simulation.
- retention.cjs: synthetic-clock plans only, never a storage or cleanup job.
- copy.json: NL/EN/DE concept text, NOT EXPERT APPROVED; FR/IT deferred.
- fixture-seeds.json / corpus.cjs: 30 invented seeds, 10 categories, 3 languages,
  expanded to 360 lexical/context probes. Not 360 independent clinical observations.
  Some variants intentionally use sentence fragments and are not localization approval.
- context-hints.json: unclassified health-context hints, never new medical ranks.
- recognition-followup-cases.json: 79 hand-authored, pre-registered NL/EN/DE cases.
- known-limitations.json: four original R0 gaps are now resolved to explicit uncertainty;
  historical results remain recorded, while current tests require improved behavior.
  This is not a claim of complete recognition or clinical accuracy.

The leading underscore directory is excluded from the current Pages publication.
No frontend, Edge, bundler or scheduler imports this code. Node-only guard, source
checks and restricted-dependency execution support that boundary; they are not a
security sandbox for arbitrary untrusted JavaScript. Synthetic flags/IDs are labels,
not a mechanism to anonymize real data. Do not feed real messages into this package.

See ../../docs/PHASE6E0_TECHNICAL_REPORT.md, PHASE6E0_OWNER_DECISIONS.md,
PHASE6E0_OFFLINE_CONTRACT.md, PHASE6E0_COMPATIBILITY_MATRIX.md and PHASE6E1_PROPOSAL.md.
Technical success gives no authorization to integrate, deploy or process real users.
