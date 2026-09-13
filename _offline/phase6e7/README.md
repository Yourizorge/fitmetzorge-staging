# 6E-7 Synthetic Workflow

New offline adapter/test harness. Frozen 6E-0..6E-6 are read-only.
Run from repository root:

    node _offline/phase6e7/build.cjs
    node _offline/phase6e7/examples.cjs
    node _offline/phase6e7/test/verify.cjs
    node _offline/phase6e7/test/browser.cjs

The adapter executes the issued frozen 6E-6 engine and validates person/plan/set
bindings. The newly authored public model.js is a synthetic in-memory controller,
shared by offline tests and the standalone UI. Import direction is private -> public;
no public file imports/contains a private executable module. data.js is generated
from an explicit synthetic allowlist, without chat, safety records or credentials.
Public model validation is NOT live trainer authentication or trusted server attestation.

Private workspace commands re-evaluate the frozen source/context. Browser source
events are selected simulations, not a real health classifier or live source monitor.
Time is a labelled synthetic clock; proposal expiry is a fixture event. The O5 tests
use frozen retention logic; no real records are retained or deleted. Each reset
starts another entirely fictional fixture, not a medical clearance decision.

Accepted actions are logged with immutable snapshots and source refs. Invalid
commands return an error without partial aggregate changes; successful command
retries do not duplicate audit/outbox. No server durability or concurrent database
isolation is claimed. Member acceptance must precede trainer approval. Apply and
restore apply are separate trainer actions; both require a fresh pair of approvals.

Only tests, generated synthetic data and standalone public demo are new.
No changes to the existing runtime, database, Edge, Auth, RLS or member records.
