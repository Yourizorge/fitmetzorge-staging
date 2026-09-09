# Package 6E-2 Offline Recommendations

TECHNICAL PASS / READY FOR OWNER REVIEW. Not owner-accepted, frozen or live.
Synthetic, deterministic Node-only recommendation contracts; no provider/dependencies.
Existing 6E-0 and 6E-1 sources remain read-only. D1-D12 and O1-O5 are preserved.

From repository root:
```text
node _offline/phase6e2/test/verify.cjs
node _offline/phase6e2/test/examples.cjs
```

- engine.cjs: issued context snapshots, exact message/revision binding, read-only O5
  projection, bounded data/context eligibility and template rendering.
- contract.json / copy.json: three implemented NONPHYSICAL content types, four
  explicitly unreviewed physical/goal content boundaries, exact NL/EN/DE concepts.
- preregistered-cases.json: 122 committed expectations preceding implementation.
- test/: fixtures, negative/boundary tests, examples, frozen isolation and explicit
  operator-run verification/publication helpers. The core imports none of these.

Call prepare(state, nowMs, options, previousContext) with an issued 6E-1 state.
Always thread previousContext in the same simulation sequence, including early
O5 removal. A superseded snapshot cannot issue another recommendation. Same-state
reprocessing preserves the original O5 cap; divergent event lineage is rejected.
Then call recommend({synthetic_only:true,type,binding:context.binding,analysis},
context,authority). analysis and authority use the exact frozen 6E-1 contracts;
no goals, trainer restrictions or medical authority are invented or accepted.

Daily record checks may accompany health feedback. Workout/week reflection is
withheld for available current health reports; self-report can restore only these
nonphysical proposals under their specific source conditions. Missing/expired
context is not reconstructed. A new ordinary message may support only nonphysical
reflection, without settling other issues, creating clearance or overriding current
health reports. These are OWNER REVIEW PROPOSALS, not clinical resumption criteria.

No live persistence: returned records are the existing minimal O5 projection.
Raw synthetic state, context bindings and test outputs are not retention payloads.
Initial null creates a synthetic experiment, never a safety reset/new-chat shortcut.
WeakMap branding/lineage is not server authority, durable storage or multi-process proof.
Within a sequence, a missing source stays missing when retry options are omitted.
Only still-retained O5 references carry that status; expiry leaves no extra
per-message marker. Restoring deleted originals is not an implemented route.
All context-based content remains subject to existing chat consent; facts/access
retain independent authority checks. Missing expert criteria remain open.

No workload/exercise/nutrition/goal changes, recovery claims, domain writes or sharing.
These limited personal proposals add optional record checks/reflection to facts,
not training/food/recovery coaching yet. That broader ambition remains unimplemented.
See docs/PHASE6E2_OWNER_OVERVIEW.md and docs/PHASE6E2_CONTRACTS.md.
