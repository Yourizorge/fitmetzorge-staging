# One-run quota recovery: preregistration

Scope: Yourizorge/fitmetzorge-staging/main, project mokxyyullfhkfalopbzd.
The owner's conditional approval is recorded in
PHASE6E11_RECOVERY_RUN_AUTHORIZATION_20261018.md. No owner acceptance is implied.

## Exact boundary

New, unused run: `4b0bb35f-02b5-4a9d-92d7-c29995691460`.
Maximum charged capacity: 2349. Normal full capacity: 2338; worst safe suffix:
2349. This is reserved capacity, not a claim of observed hosted SQL commands.
One collector, at most three protected streams of 106496 rows each, no retry.
The existing 600-second ceiling, ordinary stop at540, 5-second query/connect
deadline, 1-second lock limit and zero own temporary writes remain unchanged.
The guard/observer worker remains limited to180 seconds. No timeout is enlarged.

| Phase | Capacity |
| --- | ---: |
| Preflight | 4 |
| Migration boundary | 92 |
| Baseline | 61 |
| Fixture setup | 33 |
| Guard | 13 |
| Auth | 318 |
| Controller | 286 |
| Route A | 191 |
| Route B | 286 |
| Restore | 54 |
| Scoped measurements | 136 |
| IO | 97 |
| Cleanup | 633 |
| Final checks | 133 |
| Closure | 1 |

Each CLI operation reserves64 potentially unobservable CLI/background commands
plus8 directly observed native observer commands. CI retains actual disposable
CLI protocol counts separately. Hosted global counters are not session
attribution: they remain UNKNOWN and cannot be filled with CI templates.
Counter resets, excess capacity, temp writes or incomplete observers stop the
chain. A CLI exception still requires its direct after-observation, without retry.

## Minimal forward migration

CLI2.117.0 generated
`20261018070231_phase6e11_recovery_run_quota.sql` (canonical ordinal45).
SHA256: `00c3757bcb8b3da367285835e2b3013063838d133a9d77f2c10c718e72be2a5b`.
It adds only the exact new UUID's quota exception and a private invoker trigger
protecting its immutable identity, counter and retained terminal receipt.
No public execution, new role, app table, RLS change or existing row rewrite.
M44 bytes, function, trigger, old quota exception and all closed receipts remain.
The separately named private local application candidates45/46 are NOT this
canonical quota migration and are NOT authorized for hosted deployment here.

The source-bound gate must validate both supported starting states: pending
44-to45 migration, or already-present45 followed by dry-run only. Both use the
same real disposable GoTrue/controller/workflow/audit/cleanup execution. The
second case has its own receipts and may not reuse the first case's closure.
Three failure-injection stacks retain their separate incomplete evidence.

## Admission, not a hosted result

Initial local regression checks:199 Python tests and132 Node tests passed.
These do not prove a database build, hosted writes or preservation. New complete
CI must independently reproduce the command register and every cleanup prefix,
clean45 build, both entry states and real fault paths against the exact sources.
Only then may the one registered hosted attempt start. Prior successful CI is
historical evidence, not admission for these changed sources.

Original 112 valid pairs, incomplete113, historical utility UNKNOWN and all
earlier stops remain unchanged. The hosted attempt is still unused at this
preregistration. No owner window, freeze or 6E-12 server release is authorized
by this document. 6E-21 remains unaccepted.

External AI calls/cost:0 / EUR0.00. Real-member AI enabled:NO.
Production touched:NO.
