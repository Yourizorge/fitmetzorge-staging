# Training Staging Publication Receipt

Verified 2026-09-08. Technical staging delivery, not owner acceptance/freeze.

- Repository: Yourizorge/fitmetzorge-staging, main.
- Final runtime source: ed1f485af87d68ad7ec6cbee55ba9fda074af9ce.
- Runtime cache: 20260908-training-workout2.
- Pages run: [34255755013](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/34255755013),
  completed/success for exactly that runtime commit.
- Earlier initial publication: 38fe9b425dc4fce37c517954460600f580980de0,
  run [34254304377](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/34254304377), success.
- [Staging application](https://yourizorge.github.io/fitmetzorge-staging/).
- All 59 published runtime assets match committed Git blobs byte-for-byte.
- Seven owner-authorized Training files differ from the historical baseline;
  the remaining 52 runtime assets match bc6308f byte-for-byte.
- All 53 tracked _offline/_tests source paths return HTTP 404 on the Pages site.
  No offline AI code is imported or embedded in runtime. Git repository access
  settings are unchanged; this is website isolation, not a claim of Git secrecy.
- All 23 frozen 6E-0 sources and D1-D12 remain unchanged.
- Published-asset browser matrix: 248/248 PASS on four sizes, synthetic backend only.
  No real member browser mutation, external AI call or provider activation.
- Local matrix: 248/248 PASS; 280 current offline 6E-1, 90 frozen selected,
  22 model/preservation/theme and 6 completion regressions PASS.
  Two historical blanket app-freeze tests are explicitly excluded, never counted PASS.
- Staging migration 20260908100106 applied once; local/live history 32/32;
  final dry-run empty. Five live function bodies match the canonical source.
- 34/34 SQL tests locally and 34/34 in staging with rollback.
- All 67 compared table fingerprints and counts retained (100276 rows).
  Zero synthetic accounts remain. No production or Edge deployment.

## Commit Lineage

| Commit | Scope |
| --- | --- |
| 0e8e77a420c97f97f47d631b68b5cfd29f4897f4 | 36-case offline preregistration |
| cf6c212600b6798a2a2d0a057b9deacc233112bc | Narrow offline recognition fix |
| a27b61a761503ba0a3350bbabe45352ef2f0d7ec | Additive Training SQL and transaction tests |
| 931138bf783fb3f0cb4ac1ff0ed932ff2d8395ca | Initial Training UI/model, adapters and tests |
| 38fe9b425dc4fce37c517954460600f580980de0 | Initial technical documentation |
| ed1f485af87d68ad7ec6cbee55ba9fda074af9ce | First-session retry fix and cache workout2 |

This receipt/evidence is committed afterwards as a documentation/test-only commit.
Its final remote HEAD and Pages result are checked after push and reported in chat;
no self-referential future commit hash is invented here.
That final commit must not alter any runtime, migration or offline AI source.

## Verification Detail

[Machine-readable evidence](TRAINING_WORKOUT_EVIDENCE.json) contains the source
hashes, exact commands, browser checks, schema proof and before/after fingerprints.
[Technical report](TRAINING_WORKOUT_FOLLOWUP_REPORT.md) includes causes, scope,
limitations, security-advisor delta and eight phone-retest steps.

The first live browser run exposed a test-only timing assumption: after an actual
network reload, remaining time was no longer guaranteed above 130 seconds after +15.
The final assertion pauses first and requires an exact +15000 ms delta; it does
not weaken the timer contract or change runtime. Live verification then passed.
Asset bytes are fetched and checked against Git once per path and reused unchanged
inside that browser test. The separate publication check fetches every asset again.

Open: owner phone/product review; expert content/recovery/retention decisions for
offline 6E-1. No medical validation, new owner freeze or automatic next package.
Production touched: NO.

