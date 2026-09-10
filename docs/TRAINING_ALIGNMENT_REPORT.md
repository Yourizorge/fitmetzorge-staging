# Training Alignment And Owner Acceptance

Status: COMPLETE / OWNER-ACCEPTED.
On 2026-09-10 the owner confirms a successful physical phone test of the large
round timer, independent/simultaneous RIR/RPE, RIR under KG and RPE under REPS.
Alignment is accepted too; no further owner retest is outstanding for this correction.
This acceptance update changes documentation only, not runtime, storage or database.
The implementation and emulator evidence below remain the original release record.
Latest freeze/publication checks: [acceptance receipt](PHASE6E3_FREEZE_RECEIPT.md).

## Exact Scope And Cause

Baseline main, local/direct origin: 9406ab5a0869564a6a5498ec2d7a679589a38bc0, clean.
Only repository Yourizorge/fitmetzorge-staging at the owner-specified
supabase/.temp/phase4fb-staging-deploy root. No newer change overwritten.

Previous extra inputs used a separate flex row starting in column 2 with fixed
64px controls. Visibility and being below a set did not align their edges to KG/REPS.
The pre-edit 390px matrix measured 72 failed input/label edge assertions across
the four combinations and reload/theme states. This is the reproduced cause.

The main row and effort row now share --tw-set-columns. RIR occupies column 3 (KG);
RPE occupies column 4 (REPS), independent of the other field. Labels sit above
their own input, with the same left/right edges. Both off still produces no extra DOM row.
No plan, session, set record, preference or timer logic changes.

Runtime commit: 89dde6a4e535b38631e6223134f4943252136cfc.
Exactly three paths: assets/training-workout.css, app.js, index.html.
The latter two ONLY update the stylesheet/loader cache references to
20260910-effort-align1. The approved Training engine, model and editor remain unchanged.
A scoped CSS comparison protects every non-effort/grid rule, including the entire timer.
All 57 other runtime assets keep their baseline identities.

## Targeted Verification

| Check | Result | Scope |
| --- | --- | --- |
| Local browser matrix | 930/930 PASS, 26 screenshots | 320, 390, 1440px; all four combinations; light/dark; save/reload |
| Published-asset browser matrix | 930/930 PASS, 26 screenshots | Same matrix using fetched bytes checked against committed Git |
| Column geometry | PASS | Every displayed effort input AND label shares both edges with KG/REPS, tolerance <0.6 CSS px |
| Controls/overflow | PASS | Inputs >=44px high/wide; compact main row; no horizontal overflow; no empty extra row |
| Optional scores | PASS | RIR 0, independent RPE 9.5 and null retain their distinct values across save/reload; snapshot unchanged |
| Accepted timer | PASS | 390x844: 300x300 circle at x45/y272 in both themes, real visible countdown, minimize/reopen same deadline; no set/completion |
| Offline/preservation/model/theme suite | 676/676 PASS | See PHASE6E3_TECHNICAL_REPORT.md; includes one limitation observation, not medical recognition success |
| Existing completion regression | 6/6 PASS | Original event-order/assertions unchanged |
| Syntax/diff | PASS | App/CJS parsed, scoped diff and whitespace checked |

The initial theme assertion expected a dark class, while this app uses dark as
the default without light; the test was corrected before the authoritative baseline.
A fixed 1.2-second wait could precede the rounded display's next visible change;
the test now waits, bounded to five seconds, for an actual changed value.
No timer behavior was changed to satisfy the test.

These are real app controls with test-only inspection hooks and SYNTHETIC backend
and auth. This task did not perform a new real-account login/member test.
The previously accepted behavior is additionally protected by unchanged engine/model/UI bytes.
Browser sizes are emulated, not physical iOS/Android, Safari, OS keyboard/browser
chrome or OS suspension tests. The subsequent owner phone test now accepts timer,
choice behavior AND alignment. This is owner-reported physical acceptance, not a
new agent-run device matrix or proof of every OS/browser combination.

Screenshots (local ignored evidence):
supabase/.temp/training-alignment-live-390-11-light.png
supabase/.temp/training-alignment-live-390-11-dark.png
supabase/.temp/training-alignment-live-390-10-light.png
supabase/.temp/training-alignment-live-390-01-dark.png
The complete coordinates and SHA-256 are in [alignment evidence](TRAINING_ALIGNMENT_EVIDENCE.json).

## Publication And Isolation

Source push to staging main succeeded, ending at
bcfed5d245b1c4d82f5a9caa2d207e7cbf3e4cdd (the separate offline AI commit).
[Pages run 34481071064](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/34481071064)
completed SUCCESS. Published assets: 60/60 match raw committed bytes.
57 non-alignment assets unchanged; all 94 offline/test source paths HTTP404.
The pre-push check matched all 60 old baseline bytes and the 93 source paths then
present; the subsequently added README is included in the final 94-path probe.
No offline code imported or embedded; workflow/site settings unchanged.
The original documentation push ended at 6a584641eecb7b6987a21e9985ea1d9a5dc12cbf.
[Pages run 34482455221](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/34482455221)
completed SUCCESS. That is the unchanged-runtime baseline for this acceptance update.
Its docs-only publication must retain ALL 60 runtime assets and ALL 69 offline files.
The definitive acceptance commit/Pages result is checked after publication and reported in chat.

All frozen 6E-0/6E-1/6E-2 sources preserved. The new AI implementation is only
_offline/phase6e3; [accepted offline design](PHASE6E3_OWNER_OVERVIEW.md), not live integration.
6E-2 accepted/frozen offline per [receipt](PHASE6E2_FREEZE_RECEIPT.md).
D1-D12/O1-O5/N1-N3 retained; Phase 6E remains incomplete.

No database, migration, Edge, real member processing, entitlement/provider change,
AI call/cost, production/appfmz/other website or cleanup operation.
Earlier migration counts/member fingerprints remain historical; no new DB measurement claimed.

## Historical Retest Checklist - Now Accepted

The owner has completed and accepted the correction; the original checklist is
retained for provenance, not as a new required acceptance round.

1. Refresh staging and open a workout with both choices enabled.
2. Verify RIR directly under KG, RPE directly under REPS, both left AND right edges.
3. Check RIR-only, RPE-only and both-off; no shifted columns or empty extra row.

Reproduce from repository root with bundled Playwright on NODE_PATH:
node _tests/training/alignment-browser.cjs local
node _tests/training/alignment-browser.cjs live
node _tests/training/alignment-publication.cjs final
node _offline/phase6e3/test/verify.cjs

No automatic next package. No medical, privacy/legal or language approval inferred.
