# 6E-19 Recovery and Check-in Planning
2026-10-04. Local technical verification complete; publication evidence is recorded
separately in PHASE6E19_PUBLICATION_RECEIPT.md. Delivery is for owner review only.
No 6E-19 owner acceptance or freeze. Phase 6E as a whole remains incomplete.

## Current authoritative status
6E-18: COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE/SYNTHETIC ONLY.
The owner's physical sixteen-scenario PASS and18-R1/R2/R3 acceptance are bound in
PHASE6E18_FREEZE_RECEIPT.md and PHASE6E18_FREEZE_EVIDENCE.json. Training/nutrition
values are NOT expert-validated. Earlier pending-owner wording is historical.
Accepted13-18 contracts supersede older audits. D1-D12,O1-O5 remain unchanged.
6E-11 hosted: SUPPORT HOLD - SU-487979. No Supabase operation in this package.

## Implemented increment
An isolated memory-only agenda links an existing training/nutrition snapshot to
twelve daily sleep/recovery records. Missing data are visible. Receiving the last
record triggers exact comparisons and one source-bound review notice without a
chat question. Changes are facts, not readiness, causation or clinical inference.
Completing the check-in references its exact record version; it does not complete
a set, workout or proposed schedule change.

The next scheduled check-in is distinct from the uncompleted historical occurrence.
After-workout uses the explicitly supplied next training appointment; daily uses
the active time and fixed synthetic UTC clock. A pending proposal does not change
the appointment. No real clock scheduler, timezone/DST integration or reminder
service is implemented. Refresh resets the entire memory simulation.

## Sources and calculations
- Frozen13 metric definitions and3+3-day exact mean comparison; six complete days
  per metric. Integer sleep minutes allow0, null remains missing. Recovery1-10 is
  separate self-report, not a calibrated clinical instrument.
- Frozen8/15 supplies existing after_workout/daily catalog options. The reported
  category low is separately and explicitly supplied. Numeric scores never imply it.
- Frozen18 supplies B's training16/nutrition17 snapshot; A's workout comes from
  accepted14 and its nutrition snapshot is separately read-only. Declared synthetic
  identity aliases are in data.provenance/origin; no live identity is inferred.
- New fixture rule explicitly binds route, plan version, option version, source
  fingerprint, validity, allowed restoration options and A's trainer relationship.
  08:00/20:00 are explicit fictional member choices, not recovery advice.
- Fixture dates are explicitly rebased copies of13 values to the fixed18 clock.
  Historical source files are not rewritten.
- Examples:450 ->360 minutes, difference-90; recovery8 ->6, difference-2.
  Correcting the last recovery6 to8 yields20/3, not a fabricated rounded integer.
- Missing/disputed/incomplete, duplicated, mismatched identity/day/plan, different
  units/methods, expired/future sources and unavailable/conflicting/revoked rules
  block conclusions/options as appropriate. Reliable facts remain when only the
  option rule is missing. No partial comparison is presented as complete.
- New source/plan changes retire old cards and approvals. Replays or identical
  values produce no second card. An actual correction preserves older record
  versions and creates a new review revision.

## Workflow and preservation
A: member confirms -> explicit synthetic trainer approves -> member applies.
B: member confirms -> member applies; no trainer step or A-to-B fallback.
Only cadence/time changes. Training and nutrition bytes are invariant.
Check-in time editing invalidates approvals. Existing plan editing remains in
the accepted separate demos; no cross-demo synchronization is claimed.
A simulated upstream plan change invalidates the old bound option.

Application is atomic and idempotent IN MEMORY, preserving the complete prior
state on injected failure. Each applied version stores plan/rule/record/agenda
bindings. Restoration creates a new proposal and version with fresh approvals,
within the rule's explicit allowedRestore list. No physical advice or automatic
action is authorized.

Restoration also checks the catalog's CURRENT recovery category and allowed time.
The original after_workout cadence remains in history but cannot be restored
while the current declared low category selects daily. Scenario16 first changes
the permitted daily time08:00 ->20:00, then restores08:00 as version4. It also
proves the forbidden old cadence was rejected. No rule exception is invented.

Current/uncertain/unresolved health context blocks planning; recording and reliable
facts remain available. Self-reported resolution does not clear the safety latch.
This is an explicit fixture context, NOT new NLP recognition or a medical service.
Consent withdrawal stops new processing and replay. Existing history remains.
No new persistent health registry or retention policy is introduced. O5 remains
binding for future server design; this demo is not a live O5 storage implementation.

## Isolation and architecture
Public: recovery-checkin-demo/{data,fixtures,model,review,copy,app}.js,index.html,demo.css.
Private: _offline/phase6e19 build/tests/ops/browser/publication/evidence.
Only the existing brand bitmap is loaded besides the eight new files.
No network API, storage, cookies, Auth, database, Edge, provider or external AI.
CSP connect-src none. Browser roles/source authority are mock-only, not security
proof. No secrets or member data. Private paths must remain404 on Pages.
Original1260 worktree files,58 historical proof hashes, migrations41/42,112 valid
pairs and incomplete113 are preserved. Dirty6E11 files are not staged.

## Remaining scope
Real server integration needs verified identity/consent, authorized versioned
sources and trainer rules, immutable history, durable transactions/idempotency,
protected notification deduplication, correction invalidation, retention/delete
and timezone semantics, request/audit/write-set proof and RLS/access controls.
Those are not bypassed by this demo;6E11 remains held for SU-487979.

There is no validated rule linking these observations to physical load changes,
food/calorie changes, medical recovery or automatic training resumption. Such
rules require distinct product/source authority and relevant expert review.
Privacy/legal/language and live-data provider conditions remain open. No photos
or video, no provider calls or new cost. No next package is started.
