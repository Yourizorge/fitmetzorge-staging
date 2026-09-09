# Training Mobile Publication Receipt

Verified 2026-09-09. Technical staging delivery; owner phone acceptance remains open.

- Repository: Yourizorge/fitmetzorge-staging, branch main.
- Starting local/direct remote: 633e9f9ab50bd298a66088e6cc0cb824215e98f5, clean.
- Runtime/test commit: 58515aa99792e99c8b733e0c3c7b54ecb0d2a634.
- Cache: 20260908-training-mobile1.
- Pages workflow: pages build and deployment, completed / success.
- Exact source run: [34342609222](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/34342609222).
- [Staging application](https://yourizorge.github.io/fitmetzorge-staging/).

## Verified Outcome

| Verification | Result |
| --- | --- |
| Focused mobile + model + preservation + theme tests | 29/29 PASS |
| Existing completion regressions | 6/6 PASS |
| Syntax + Git whitespace checks | PASS |
| Local actual-app browser matrix | 940/940 PASS |
| Published actual-app browser matrix | 940/940 PASS |
| Sizes | 320x700, 360x780, 390x844, 1440x900 |
| Geometry probes per matrix | 90, no horizontal overflow violations |
| Unique screenshots per matrix | 71, including mobile basic list, set rows, timer and keyboard-space emulation |
| Published assets vs committed raw Git blobs | 60/60 byte-identical |
| Unchanged assets vs phone baseline 633e9f9 | 54/54 byte-identical |
| Unrelated assets vs historical bc6308f | 52/52 byte-identical |
| Offline/test source URLs on Pages | 56/56 HTTP 404 |
| Frozen 6E-0 raw sources | 23/23 unchanged |
| All offline AI, SQL, Edge, workflow/config sources | Unchanged |
| Live member calls / mutations in this task | 0 / 0 |
| Database migrations / Edge deployments | 0 / 0 |
| Production touched / file cleanup | NO / NO |

The six mobile-authorized runtime paths are the five modified Training files plus
one new Lucide clock asset. Model and owner-settings source bytes remain unchanged.
No broader runtime exemption was introduced: the new scope gate compares the
entire diff against 633e9f9, separately from historical bc6308f preservation.

All browser backend operations are synthetic. The published run fetches actual
staging JS/CSS and compares their raw bytes with Git before using them in the
isolated harness. It never logs in as or mutates a real member.
Git checkout CRLF conversion is not used to normalize published-byte comparisons.
Pages isolation is not a claim of Git repository secrecy or changed access settings.

The receipt, report, evidence and four status documents form a subsequent
documentation-only commit. Its final remote HEAD, successful Pages result, clean
worktree and byte identity to this runtime commit are checked after push and
reported in chat; no future/self-referential commit hash is invented here.

## Evidence And Retest

[Technical report, causes, exact 35-ID map and phone retest](TRAINING_MOBILE_FOLLOWUP.md).
[Machine-readable source, test and publication evidence](TRAINING_MOBILE_EVIDENCE.json).
Historical TRAINING_WORKOUT_EVIDENCE.json and earlier reports remain intact.

Keyboard coverage: focused typing and a reduced viewport representing keyboard
space, not a physical iOS/Android OS keyboard. Physical-device acceptance stays open.
No new live member fingerprint comparison is claimed; prior fingerprints remain
historical. No closed-app rest notification or cross-device real-time guarantee.

Only next step: owner's phone retest of basics, compact rows and optional rest.
6E-0 remains accepted/frozen offline only; 6E-1 remains offline and not newly
accepted/frozen. Phase 6E is incomplete. D1-D12 retained; no next package.
