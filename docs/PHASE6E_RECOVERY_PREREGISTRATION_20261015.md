# Recovery and integration preregistration - 15 October 2026

Owner source: attachment `8373cb38-f185-4662-924d-2d4ea2b0cc0b`.
Starting local and remote main: `f07f4ee1ab7400952174fc8a8666cb4fa6ff1aa8`.
Scope remains Yourizorge/fitmetzorge-staging and mokxyyullfhkfalopbzd only.
All pre-existing worktree changes and historical receipts remain untouched.

## Separate read-only diagnosis

Run `08292976-0e47-4a4a-a425-8ae6c48e37e6` is new and single-use.
Maximum 128 SQL commands, ten minutes, one collector, no retry. Reserve 32 native,
64 CLI/unknown and 32 closure commands. Expected native protocol: 16 commands in
two distinct explicit read-only transactions, each ending in rollback and close.
The proven session-pooler binding, official CA, verify-full, jit=true,
five-second query/connect timeout and one-second lock timeout remain unchanged.
JIT is limited to the verified owner, postgres, 300 seconds and revoked in finally.

No application/Auth/fixture writes, migration application or fixture cleanup.
Queries read migration history, exact M44 object metadata, numeric statistics
without SQL text, own transaction identity and lightweight active-query counts.
No app rows, row-hash transport, chat or health contents are read.

CLI 2.117.0 remains pinned. `db push --dry-run --skip-vault` uses the existing
read-only startup option; no seeds or roles are included. The canonical migration
folder has 44 files. Candidate 45/46 remain in their existing private source paths;
no files are moved or removed. A 43-history result must report exactly M44 pending;
an exact 44-history result must report an empty dry-run. Neither applies SQL.

Stored M44 SQL is compared using the existing PG17 AST canonicalizer. Its function
body, invoker/owner, fixed search_path, execute ACL, trigger and validated constraint
must match. Absence, mismatch, missing after evidence, unexpected IO or incomplete
closure is NO-GO. A failed CLI still gets a distinct mandatory after measurement.

Database-wide postgres statement counters are not CLI session attribution.
Known native commands are subtracted; remaining activity stays UNKNOWN and the
entire CLI reservation is charged conservatively. Missing/reset/duplicate counters,
more than 64 unknown calls or temp writes stop admission. No old count is changed.
The historical 16-versus-14 cause remains UNKNOWN, not retroactively PASS.

Local tests cover both migration branches, changed SQL/ACL/trigger/constraint,
concurrent unknown activity, missing counters, query failures, rollback/close,
immutable evidence and the CLI dry-run/skip-vault flags. These are local adapter
tests, not a full workflow admission.

## New endrun remains conditional

Reserved identity: `4b0bb35f-02b5-4a9d-92d7-c29995691460`. It is NOT started.
Maximum 2,237 SQL commands, 106,496 protected row places, three full cycles,
one collector; existing time/IO limits remain. Full source-bound CI is mandatory.
M44's higher database counter is bound only to the consumed old run UUID. It is
not silently reused or changed. This separate boundary must be resolved before
the new endrun can be admitted. Local releases 45/46 are not authorized for bulk
hosted deployment by this task.

## Independent local work

Extend actual local HTTP/Auth/PG selection coverage from preferences to all eight
release slices, preserving default-off boundaries and existing combined tests.
Measure actual commands separately from planned capacity. Improve the existing
integrated UI, not a new demo. 6E-21 stays unaccepted and disabled.

Official sources checked: Supabase changelog and pinned CLI help/reference.
CBC deprecation concerns HTTP endpoints, not direct database/pooler/Management API;
scoped PAT support does not require replacing the existing credential. No secret
reset, rotation or security downgrade is performed.

External AI calls/cost: 0 / EUR 0.00. Real-member AI enabled: NO.
Production touched: NO.
