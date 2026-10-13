# 6E-11 complete budget and integral CI receipt

## Decision

INTEGRAL LOCAL/CI CAPACITY PASS; HOSTED NO-GO (approved budget insufficient).
The single authorized hosted attempt is unused. The approved maximum remains
1,280 SQL commands. No Supabase, JIT, hosted Auth, migration, fixture cleanup or
owner-window operation was performed for this work.

The complete registered normal capacity is **2,208 commands**. The maximum
across every execution prefix plus its reserved safety suffix is **2,226**.
The requested one-run adjustment is therefore **946 additional commands**, not
an unbounded allowance. This is the smallest calculated cap for this exact
bounded composition, not a universal lower bound on every possible design.

The former 1,297 subtotal and the interim 338-command cleanup calculation were
partial. Their historical receipts remain unchanged. They are not admission.

## Complete register

The executable compiler is `_offline/phase6e11/endchain_v1/complete_register.py`.
The durable register is under
`_offline/phase6e11/endchain_v1/receipts/ci-38380711049/`:

- `complete-command-register.json`: totals, scope, infrastructure writesets,
  source hashes, bounded stream capacity and required non-SQL operations.
- `register-phase-*.json`: all 2,208 ordered command slots, action/source binding,
  SQL cost, allowed writes, evidence requirements and stop rule.
- `register-prefix-reserves.json`: every prefix, remaining normal cleanup,
  emergency suffix, reserved capacity and whether it fits 1,280.
- `MANIFEST.json`: hashes of the 77 retained CI evidence files.

| Phase | Commands |
| --- | ---: |
| Project/TLS/migration preflight | 4 |
| Migration-aware application of candidate 44 | 14 |
| Protected baseline and object/rights checks | 67 |
| Controls, fixtures and fixture identity | 33 |
| Temporary identity guard and observer installation | 13 |
| Auth issuance, verification and refresh | 318 |
| Controller evidence and admission | 286 |
| Route A | 191 |
| Route B | 286 |
| Restore workflow | 54 |
| Scoped pairs and pre-cleanup preservation | 142 |
| Numeric IO attribution | 97 |
| Synthetic cleanup, its Auth/evidence/IO and access removal | 633 |
| Final preservation, absence, rights and empty dry-run | 69 |
| Durable final controller receipt | 1 |
| **Normal capacity** | **2,208** |
| **Maximum including failure/closure reserve** | **2,226** |

The normal capacity comprises 1,614 native/CLI protocol commands and 594
independently observed managed GoTrue SQL commands. Auth HTTP requests are not
misrepresented as free work: 234 commands accompany the 18 Auth actions; 360
accompany 72 identity validations (71 workflow steps plus fixture authorization).
BEGIN, COMMIT, ROLLBACK, cursor operations, evidence writes, IO sampling and
security closeout are counted. SQL inside a single server function is not
mistaken for additional client protocol commands.

The normal CI trace contains 1,519 native composition commands. Sixteen are
explicitly enumerated disposable-CI bootstrap commands: observer setup and
creation of CI-only identities/profiles. Hosted uses the already registered
three identities; the run cannot create replacements for missing accounts.
The remaining calculation is:

`1,519 - 16 + 90 stream slots + 4 preflight + 14 migration + 2 dry-run + 1 final receipt + 594 managed Auth = 2,208`.

Each of the three streams used 17 commands in the small CI database and reserves
47 at its maximum 131,072 rows, with 8,192-row pages and an explicit empty terminal
frame. These are bounded cursor streams, not repeated sort/aggregation scans.
No optional capacity has to be spent merely because it was reserved.

JIT/OIDC, TLS setup, source checks, local durable evidence and Pages checks are
mandatory non-SQL operations. Their zero in this SQL register means no client
SQL command, not zero wall time or a claim about unobservable management-plane
internal implementation. Hosted Auth-version/query-family mismatch is a stop,
not permission to borrow unregistered work.

## Failure and cleanup reserve

Before every command/mutation, the executable escrow requires at least the
larger of remaining normal cleanup/final/closure and the identity-bound emergency
suffix. At the start, cleanup plus final/closure reserves 703 commands. The
emergency suffix reaches 29 commands while all temporary facilities are active.
The worst prefix requires 2,226 overall; this is not normal cost plus a blanket
percentage. The current 1,280 admission correctly refuses this register.

The suffix includes one rollback per open channel, durable stop/closure,
one scoped after-attempt, numeric IO, compare-and-restore of this run's controls,
and exact inspection/removal/absence checks for this run's guard and observer.
No second full run, blind mutation retry, fabricated after-pair or deletion of
fixtures with incomplete proof is allowed. On unreachable SQL, close the
connection, preserve the error and rely on server expiry; do not claim SQL
cleanup or zero remaining objects without confirmation.

Three complete failure rehearsals used separate empty CI databases and actual
GoTrue, controller and workflow adapters:

| Injection | Native composition commands | Committed request receipts | Sealed receipts | Result |
| --- | ---: | ---: | ---: | --- |
| Before first workflow call | 358 | 0 | 0 | stopped; no retry |
| Lost response after committed call | 360 | 1 | 0 | stopped; no replay |
| Missing direct after-snapshot | 362 | 1 | 1 | stopped; missing pair retained |

Each case additionally used one explicitly recorded CI-only final assertion.
Each retained 12 completed Auth pairs, the incomplete fixture evidence and a
stopped controller at step 12. Both access controls were disabled; temporary
guard/observer schemas were zero. The test fixture window was deliberately
retained as incomplete evidence, not passed off as successful fixture cleanup.
These are the three tested failure timings, not proof of every conceivable
network failure at every statement. Prefix reserves cover the registered safe
stop costs; uncertain cleanup remains a hard NO-GO.

## Source-bound CI

- Run: https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/38380711049
- CI HEAD: `10ba2ada6cc59739c0c586a447bc281b4a18ee7d`.
- Candidate SHA256: `2709a7f78b8d09a510d14b007c04408ad209d1909d6465a735c66e0907d20d20`.
- Bound endchain source-map SHA256: `53ef7db9723b88183c97b759c66247cc106494ad25194e307e86fdfba192845c`.
- GitHub archive SHA256: `8cc6ab28be9ef29dc863f9e3f662d88c1c34470bda7d486697c46aa50904f042`.
- Retained receipt manifest SHA256: `675401f96d9e1601e8c60c021ff46a6b87b0a9498693ee86fdfba192845c`.

Admission binds HEAD **and** the candidate bundle, which includes preserved
uncommitted dependencies. HEAD alone is not an assertion that every dependency
was already committed. All bound source files matched the worktree when archived.
The 1,018 payload-file hashes plus the artifact manifest were verified. The old
collector rejected 1,019 archive entries against its 1,000-entry bound after
verifying the GitHub archive digest. The original ZIP and refusal remain. A
separately tested local-only exporter verified the same official digest, all
paths and hashes under a finite 1,100-entry/30-MB/2-MB-per-file bound, and created
a new receipt without overwriting the original collection.

Clean rebuild: **44/44 PASS**, real PostgreSQL 17.6, Supabase CLI 2.117.0,
`public.ecr.aws/supabase/postgres:17.6.1.167`, actual GoTrue v2.196.0. No extension
mocks. Empty **local** migration dry-run; controller/request access checks PASS.
The CI contains 319 distinct Node tests (198 + 121), 98 Python endchain tests,
12 SQL regression files, 34 guard, 34 observer and 30 candidate-budget database
checks. Subset reruns are not additional distinct tests. The receipt exporter
has six additional local tests, separate from the source-bound integral CI.

Integral normal-path evidence: 18 real Auth action contracts, 71 workflow pairs,
89 controller steps, 295 observed workflow writes including 123 deletes. Fixture
seed, activation and final window deletion have three additional scoped audited
pairs; control enable/restore have separate exact compare-and-swap pairs.
The component workflow file retains its earlier component-scope `missing` labels;
the outer lifecycle/register receipts supply those proofs without rewriting it.
The final approved-budget closure is intentionally denied under 1,280; no closed
hosted run or enlarged-budget database receipt is claimed.

## Load and preservation

- One sequential collector; three full streams only, plus scoped action pairs.
- 169 table fingerprints in each empty-CI preservation inventory; equality PASS
  before, before cleanup and after cleanup, with explicit synthetic exclusions.
- Own temporary writes: zero for monitored stream, metadata, workflow and Auth
  query families. Background counters are separate, never automatically blamed
  on the collector. No statistics query reads stored query text.
- Observed WAL is recorded separately, not confused with temporary spill:
  three stream windows 190/384/118 bytes; workflow windows 1,485,439 bytes.
  Read-only WAL is not falsely treated as a logical member-data write.
- Workflow worker CPU 516.496 ms; wall 5,142.782 ms, below its 2,000-ms CPU and
  120,000-ms wall gates. CI timings are not a hosted latency guarantee.
- Query and lock deadlines remain unchanged; one collector, no full retry,
  180-second temporary guard/control scope, hard per-phase and cleanup escrow.
  Candidate 44 retains its existing separate 15-second migration DDL timeout.
- Normal CI closeout proves zero own windows/workspaces/participants/sessions/
  refresh tokens/temporary schemas and original object/rights catalogue equality.
- 1,376 protected local source/runtime files retained. No change to production
  or historical hosted evidence. No new hosted data-preservation claim is made.

## Migration and next decision

Hosted migration status remains **last proven 43**, not freshly queried here.
Candidate 44 remains unapplied and byte-identical:
`20261012185121_phase6e11_single_endchain_budget.sql`, SHA256
`01719a133e732b33fa435be25552f92824acd29ae0f4be2af669a29c3e168d3f`.
It still permits only 1,280 for the single reserved run and 128 for ordinary runs.

One decision is needed: authorize at most **2,226 SQL commands for that one
previously unused hosted run**, under all existing project, identity, IO,
deadline, retry, evidence and cleanup boundaries. This is not a permanent cap
increase. After that decision, adjust the still-unapplied candidate and exact
controller budget together, obtain fresh bound CI including successful final
closure at the new limit, then recheck current hosted source/project/history
and dry-run before any migration or run. No second general staging approval is
needed for those routine steps, but current evidence cannot admit changed SQL.

Until then: no hosted run, no owner phone window, no owner acceptance/freeze,
no JARVIS handoff, no 6E-12 server integration; 6E-21 remains unaccepted.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.
