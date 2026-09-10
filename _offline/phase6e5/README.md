# 6E-5 Offline Progression And Plan Review

New synthetic-only deterministic Node contract. Not loaded by the app.
No provider, live data, database, storage or real plan modification.

Run from the repository root:
- node _offline/phase6e5/test/verify.cjs
- node _offline/phase6e5/test/examples.cjs

Public offline API:
- engine.prepare: frozen 6E-4 context preparation, read-only.
- engine.propose(request, context, authority): exact source/test-rule calculation.
- review.workspace(issuedOption): isolated in-memory plan-version domain.
- review.create(issuedOption, workspace): exact proposal/review deduplication.
  Omitting workspace deliberately creates an independent synthetic scenario.
- review.act(state, event, freshRequest, currentContext, authority): view, accept,
  reject or explicit trainer-only apply. Use its returned state for further actions.

Use the SAME workspace for proposals competing for the SAME simulated plan.
Approvals are member AND trainer for the exact proposal/source/context version;
separate explicit apply, not automatic execution. A shared active-plan comparison
prevents two competing proposals from both modifying the same simulated version.
The simulator is not a durable service or evidence of real transaction concurrency.
Its returned simulated plan is not an authoritative next readset. Reassessment
after external version changes needs a new coherent declared source snapshot,
a new independent scenario and new approvals; no old approval is transferred.

Test rules, including minimum sessions, recency window, rep steps/ceiling/reset,
available weights, effort requirements and forbidden pairs, are explicit sources.
They are NOT validated medical or coaching policy. Without a trainer, a separate
FMZ coaching policy is missing; it is not fabricated here.
All output keeps physical_advice_authorized=false and automatic_actions_allowed=false.

Frozen 6E-0..6E-4 and current Training runtime remain unchanged. O5 is read-only;
no new safety-copy, retention deadline or medical release. Known language misses
and incomplete resumption criteria remain open, not hidden behind a review service.
The user approves THIS implementation GO, not the unbuilt result or live use.
