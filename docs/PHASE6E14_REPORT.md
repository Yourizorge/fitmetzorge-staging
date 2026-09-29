# 6E-14 Technical Report
2026-09-29. **TECHNICAL PASS / READY FOR OWNER REVIEW - OFFLINE/SYNTHETIC ONLY.**
Static publication verification is recorded separately in PHASE6E14_PUBLICATION_RECEIPT.

## Implementation
New private implementation: `_offline/phase6e14`.
New public, standalone memory-only demo: `bounded-adjustments-demo`.
No existing application assets, Auth, Edge, database, migration, workflow or
frozen executable source was edited. Existing dirty/untracked 6E-11 work is not
part of these commits. No hosted Supabase operation took place.

Architecture: immutable frozen 6E-6 trainer fixture / frozen 6E-8 catalog ->
explicit newly authored synthetic source envelope -> frozen 6E-13 source/safety
evaluation -> 6E-14 exact option/rule binding -> generated synthetic result packet ->
separate memory-only member/trainer/apply state machine. The browser does not
import private adapters. Its role switch is visibly a simulation, never server
authorization. Browser packets are not authenticated live trainer evidence.

Sources bind subject, goal, plan, rule/catalog revision and SHA256, sessions,
six-day manifest, issued/expiry times and the opaque frozen safety receipt.
Existing legacy template IDs and clocks are retained in provenance; fixtures are
explicitly copied into a new syn-owner envelope, with synthetic date rebasing.
This is not Auth/identity remapping or fresh real historical evidence.
Training totals must exactly match the explicit session records. No missing
session is silently inferred to be zero. RIR/RPE remain distinct and null is not zero.

## Existing Options Only
Route A: accepted 6E-6 trainer progression/maintain/lb templates. Complete historical
set evidence and exact rulebook determine reps/weight/maintain, not a sleep or food
correlation. Concrete values, source versions, rule IDs and per-set observations
remain inspectable. Missing/ambiguous/revoked/conflicting rules give no candidate.

Route B: accepted 6E-8 `missed` scheduling catalog only. Three explicitly recorded
planned sessions, one explicitly not completed, plus existing early rhythm yield
the existing 18:00 scheduling option. No new intensity, sleep or food rule.
Member exercise/day/preference edits use existing catalog validators. Food plan
and sleep target stay identical; changed training days also change the existing
catalog's complementary rest-day schedule. No inferred health suitability.

Food: incomplete registration prompts optional checking, with no invented quantity,
completion flag, calorie or macro change. Recovery: nonphysical planning reflection.
No approved calorie/macro CHANGE rule exists in this slice, so that request blocks.
This is an intentional content boundary, not a hidden TODO marked as success.

## State And Safety
A: member -> trainer -> separate apply. Trainer reject/block and restore proposal
are supported. Member may also request restoration; both approvals are repeated.
B: edit -> member confirm -> separate activate, no trainer actions. Both routes
retain original and new snapshots; restore makes a new monotone version.
Restoration never overrides current exclusions; incompatible historical B plans
remain blocked. The demo does not manufacture a substitute plan to force success.

Each command carries synthetic subject/route/actor, request ID, proposal/source/
plan basis. Identical replays are idempotent; changed replay or stale basis rejects.
Commit-fault injection restores the whole prior state, including audit and approvals.
No partially applied plan. Consent, health, expiry and version conflict are independent
latches. Source correction cannot clear them, fill missing measurements or free an
old safety report. Actual/new/recurring/unclassified complaints, self-reported recovery
and O5 missing-context states block physical options under frozen safety contracts.
Chat/history/facts retain their separate access conditions.

Correction before application removes approvals and requires a fresh review.
After application the active version/history remain; re-review demands a new source
recording the now-current plan. The demo explicitly stops there rather than silently
reapplying an old progression. This limitation is visible, not an implemented live
source acquisition flow. A confirmation of checking a food log does not fill its gaps.

## Verification
Fixed preregistration preceded implementation. Exact counts, source hashes and raw
evidence hashes are in PHASE6E14_EVIDENCE.json. Tests cover 24 scenarios, NL/EN/DE,
two source revisions, both routes, all state gates, bad source bindings, invalid options,
expired/revoked sources, O5, null/zero, units, atomic fault, stale/replayed commands,
edits, trainer rejection/block/restoration and applied-version preservation.
Frozen 6E-0 through 6E-10/12: 2591 checks; frozen 6E-13: 233 checks.
Known limitation-observation tests are not medical recognition successes.

Browser: 320/390/768/1280 widths, three languages, light/dark; A/B checks and a
390x480 reduced-height/keyboard-navigation check. No overflow, storage, unexpected
network call or browser error. These are Edge/Playwright emulations, not a physical
iOS/Android keyboard or phone test. Refresh resets memory and audit as declared.

Initial failing attempts are retained: three locale tests caught a correction
filling a null value; corrected in the new fixture adapter. The first browser test
looked for an English catalog label in Dutch; assertion now uses exact locale labels.
Final passes never replace original evidence. No frozen classifier was modified.

## Preservation And Publication
1122 pre-existing working files checked byte-for-byte; 58 retained 6E-11 evidence
hashes independently checked. M41/M42 exact hashes in evidence. 112 valid historical
pairs and step113 still incomplete; no new hosted claim or migration/dry-run result.
Pages checks compare 96 existing public assets with frozen Git byte hashes and
all six new files against the committed version, plus private-source 404 checks.
No cleanup is performed during support hold.

## Open Boundaries
Owner physical product review remains required for 6E-14. Existing trainer/catalog
rules are fictional accepted product examples, not clinically validated rules.
Medical/resumption, privacy/retention, legal/DPIA/DPA/ZDR/EU/consent and language
reviews remain open for their eventual real-data/live scope. Scheduling time and
source validity are synthetic inputs, not universal advice. No new clinical norm.
6E-11 hosting/Auth/request/audit/cleanup proof remains blocked by SU-487979; no
workaround, live-member processing or provider call. No 6E-15 implementation.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO. Production touched: NO.
