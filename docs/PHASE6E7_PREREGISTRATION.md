# 6E-7 Preregistration

2026-09-13. Baseline ef42876164f82330de016cb38c5213034cd2f072, main, clean.
Owner GO K1-K4 accepted; no result acceptance or freeze.
The cases in _offline/phase6e7/preregistered-cases.json were written before new
implementation. Existing 6E-6 is read-only, including all 30 executable examples.
Public mock controller is new standalone code, never an export/import of frozen
private modules. A private adapter executes the frozen engine and exports ONLY
allowlisted synthetic readmodels. No actual auth/RLS/server durability claim.

Commands require member acceptance BEFORE trainer approval and explicit trainer
apply. Restore is a new proposal and monotone revision. No automatic action.
Expected negative outcomes are refusals, not partial writes. No medical labels
or new physical criteria introduced. Limitation observations counted separately.

Test matrix covers actions, ownership/bindings, idempotency, in-memory atomicity,
restore, O5 and missing context, W1/W2, deterministic copy, responsive UI, storage,
network, all frozen/runtime hashes and public-path isolation. Browser measurements
are emulation, not a physical phone owner retest.
