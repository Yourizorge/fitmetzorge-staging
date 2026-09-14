# Package 6E-8 Technical Report

6E-8 TECHNICAL PASS / READY FOR OWNER REVIEW - SYNTHETIC STAGING DEMO.
Result acceptance/freeze and Package 6E-9 are NOT started.

## Baseline And Scope

Repository Yourizorge/fitmetzorge-staging, branch main.
Initial local and remote HEAD: 5b65755f349379378b84b67a9f6ad3da0bab10db; clean worktree.
Owner acceptance and preregistration: b58a6b3d0ff2f50e63d3ecf15a7e4be2e4d22289.
Implementation commit: eee1c8cce04894d771cdc1a4ad0fcc2f7d5c68d4.
Final implementation/verification source: 936dd3a954557cdb3f590fcd0775a2b8ce595809.
Bootstrap compatibility: a4687afec152670edb13629acabb4c0adfa42e35.
Exact file hashes are in PHASE6E8_EVIDENCE.json.
6E-7 source c38d9d89797cd1f794463b645579f65fe4851930 is now owner-accepted/frozen;
all 141 frozen files remain byte-identical. Historical results/receipts preserved.

Project auto_review, workspace-write and staging autonomy were read; managed
restrictions were honored using reviewed scoped commands. No approval settings changed.
No file cleanup, OneDrive deletion, reset or unrelated project operation.

## Implemented Contract

- index.html is the ONLY existing-runtime exception: an early opt-in loader.
  Without fmzDemo all original static script tags and DOM remain intact, with no
  demo script dependency. Only demo mode inserts an inert template before loading
  its asynchronous mount; original theme/app/config scripts cannot execute.
  It removes inert legacy DOM and opens one sandbox=allow-scripts iframe.
  Only allowlisted language/theme parameters cross the boundary. Unknown/duplicate
  parameters fail closed. No postMessage, storage or application-state bridge.
- coach-review-demo contains a nine-file public synthetic UI/model/catalog.
  Route A imports frozen 6E-7 model/data/copy read-only; missing trainer still blocks.
  Route B is another fictitious member, with no trainer action/approval field.
- Intake validates every required field and enum, rejects conflicting preferences,
  filters all exercises/meals/alternatives, and applies time/day/experience/unit,
  diet/allergy/kitchen/budget/routine/sleep/recovery and separate RIR/RPE choices.
  The catalog is deliberately finite; insufficient compatible alternatives refuse.
- Training has exact exercise identities/order/sets/reps/rest and explicit missing
  start-load explanation; no invented kg/lb value/conversion. Existing goals and
  secondary check-in purpose are carried in the immutable intake snapshot.
- Nutrition totals are sums of fictional portions, not estimated personal energy
  requirements. Ingredient replacement recalculates totals/cost, preserves exclusions,
  changes only the draft, and invalidates member confirmation.
- Recovery has concept sleep goal, rest-day spread, check-ins and an optional lighter
  week marker. This is not an executable periodized program or medical recovery rule.
- Explicit member confirm + separate activation creates a whole immutable bundle.
  Component lineage, previous bundles, source refs, events and minimal notices remain
  in memory. Restore is a new candidate under current exclusions, never a rewind.
  Errors/fault injection cannot partially apply; idempotent retry cannot apply twice.
- Signals cover all eight requested patterns and a one-night counterexample.
  Exact fixture window/values, reason, unchanged components and confirmation are shown.
  Improvement is constrained by the explicit synthetic rep rule. Reusing its old
  source after the bound plan version changes is refused; no iterative invented data.
- Photo concept uses two code-drawn fictitious illustrations, no photo processing.
  Fixed corroborating measurement/history can yield an eligible same-muscle temporary
  swap for two weeks. Missing source/alternative refuses. No body composition,
  diagnosis, guaranteed growth, upload or image API.
- Accepted complaint, unclear-language, technical-error and self-report copy is
  byte-exact in NL/EN/DE. Manual context selection is NOT a classifier.
  Clarification removes only communication/technical fixture flags. Other complaints
  remain, self-report/expiry is not clearance, and no review service is invented.

## Technical Evidence

1673/1673 offline tests PASS: 352 new contract/hash/isolation tests + 1321 frozen
functional regressions. No skips. Existing 30 6E-6 and 15 6E-7 executable concept
examples remain exact; 33 new NL/EN/DE outputs reproduce from the new code.
Old package-specific isolation runners have obsolete pre-6E-8 allowlists; they were
not edited or treated as current scope gates. The new 141-source/59-runtime/exact-index
and full-change-allowlist checks replace those gates; selected tests have no skips.
Frozen observation tests remain limitation records, NOT successful recognition.
O5 first-registration/expiry behavior is exercised by frozen tests, not reimplemented
as a new persistent safety store. No safety/member storage exists in this demo.

Local Edge browser: 936/936 checks PASS after the final corrections.
The full matrix contains 120 layout inspections across 24 combinations:
320/390/768/1280 px x NL/EN/DE x light/dark. Both approval/version/restore flows,
actual edits, refusal states, W2 numbers, image rendering, refresh/close reset,
no parent access, no storage attempts and no unexpected requests/errors.
Normal bootstrap probe uses inert original scripts to prove execution order and DOM;
it does NOT log into the real app or claim live Auth/member regression evidence.
All phone/tablet tests are emulated; a physical 6E-8 owner retest remains open.
The previously accepted physical Training timer/RIR/RPE test remains valid.

Before publication: 59/59 other legacy runtime files and 141/141 frozen sources
byte-identical. The index test requires the exact small authorized bootstrap diff.
Private sources/tests must return HTTP404 after Pages. Public fixtures are intentional:
sandbox isolation is NOT authentication or proof of live trainer authority.

## Corrections During Verification

Initial contract run had three failures: a new adapter displayed internal workflow
revision instead of active schema revision; a plateau test chose an alternative
already present in its fixture; an exact-bootstrap expectation omitted indentation.
Corrected only new adapter/test code and the authorized index formatting.
Browser harness initially measured request arrival instead of script execution;
its injected serviceWorker blocker also threw in an opaque sandbox. Corrected the
harness, then proved actual execution order and zero app access without suppressing
application errors. One long-interrupted rerun timed out and is not counted as PASS.
Review added signal-evidence replay prevention before final verification.
Unsubmitted intake choices now remain intact across language/theme changes and
route navigation; the browser test explicitly preserves exercise exclusions.

Final compatibility review replaced document-written normal scripts with their
original static tags. Chrome can intervene against cross-site document-written
scripts on slow connections ([official explanation](https://developer.chrome.com/blog/removing-document-write)).
Only demo mode now creates an inert template, without injecting executable script
tags through document.write. The normal app does not load the demo entry at all.
Browsers may speculatively fetch existing PUBLIC libraries from the original HTML
(including the existing static CDN URL); these are not Auth/member/provider API
calls. Browser tests fulfill such preloads with execution markers and prove they
never execute in demo mode. Storage/parent access and actual API-egress checks remain
strict; preloads are reported separately, not concealed as zero network traffic.

## Publication And Commits

See PHASE6E8_EVIDENCE.json for exact source hashes, local/published proof and commits.
Final source publication: 936dd3a954557cdb3f590fcd0775a2b8ce595809.
[Pages run 34826303976](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/34826303976)
completed successfully. Published Edge browser: 936/936 checks PASS, 120 layout
inspections across all 24 variants, no unexpected execution/egress/storage errors.
All 76 public files are byte-identical to Git (60 legacy + 7 frozen 6E-7 + 9 new
synthetic files); all 168 private offline/test paths return HTTP404.
The 59 protected legacy files and 141 frozen sources remain unchanged. The only
baseline index diff is the small opt-in inert-template bootstrap, not normal app logic.
Immutable source publication artifact:
supabase/.temp/phase6e8-publication-936dd3a954557cdb3f590fcd0775a2b8ce595809.json.
The closing docs-only publication is verified separately against the same runtime.

Commits:
- b58a6b3d0ff2f50e63d3ecf15a7e4be2e4d22289: 6E-7 freeze / 6E-8 preregistration.
- eee1c8cce04894d771cdc1a4ad0fcc2f7d5c68d4: initial executable 6E-8 implementation.
- e28fed0191e88e2d59a7c3bdcbb7a15b5e7fc431: local evidence and scoped ownerreview.
- a4687afec152670edb13629acabb4c0adfa42e35: native bootstrap / inert demo isolation.
- 936dd3a954557cdb3f590fcd0775a2b8ce595809: intake choice retention and final source.
- The containing final documentation commit records this verified result; its exact
  remote HEAD is reported with the final push/Pages check, avoiding self-hash recursion.
Only staging main/Pages is authorized. No production, APPFMZ or separate website.

## Remaining Limits And Next Step

No claim of reliable language recognition, clinical triage, authentic trainer
authority, real member eligibility, database atomicity, durable deletion/retention,
validated nutrition database or personalized calorie/load prescription.
Sleep and lighter-week values are concepts; coaching/content/safety reviews remain
open. The photo panel cannot infer anything from real images.
No real chat is implemented here; existing access/consent axes are retained, not
replaced by a new general health-related subscription block.

Ownerreview: J1 route separation, J2 complete fixture plan/editing workflow,
J3 source-bound proactive/photo concept. 6E-8 is not automatically accepted/frozen.
One next proposal: PHASE6E9_PROPOSAL.md, synthetic durable backend/authorization,
with separate owner GO, server-owned eligibility, scoped RLS and concurrency tests.
No implementation of that package has begun.

Database/migrations/Edge/Auth/RLS/memberdata changes: NONE.
External AI/provider calls: 0. External AI cost: EUR 0. Production touched: NO.
Phase 6E as a whole remains INCOMPLETE.
