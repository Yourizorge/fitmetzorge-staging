# 6E-11 Offline Endchain Work Package

Status: IN PROGRESS / READY=false. No hosted admission or owner acceptance.

## Scope And Starting Point

Local and remote main were both verified as
`235b74e1e2a2acef5b3b88cb2d3eea288df0a93c` before this package. The five older
tracked modifications (AGENTS.md, app.js, BUILD_STATUS.md, PHASE6E11_PROPOSAL.md
and index.html) remain outside these commits. Two existing agents work in
separate delivery directories; only Main integrates, commits and dispatches CI.

No hosted Supabase connection, JIT, migration, Auth operation, fixture cleanup,
run activation or owner window is permitted in this package. The unused hosted
attempt and 2349-command cap are unchanged. Package21 remains unaccepted/off;
no production, APPFMZ, website or JARVIS changes are included.

## Preservation

A new local preservation receipt checks 1376 retained files: 1372 byte-identical,
four previously authorized differences unchanged, zero unexpected differences.
The original baseline SHA-256 remains
`213673e2a04f04b715f247efe3f27263c0dc998859d5d7e54685a356412f8fef`.
This is source preservation, not a new hosted-data measurement.

## Actual Linux Import Checks

The isolated component has no database, no installed third-party dependencies,
no inherited credentials and no external network interface. It runs as non-root
in a separate network namespace with dropped capabilities/no-new-privileges.
All selected loader tests must execute without skips or expected failures.
The component never reports full-chain admission, even on a successful run.

1. Commit `de70c0aad5ed9c5a464ef0bd9056a21210bf6ea1`,
   [run 43079305858](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/43079305858):
   FAIL before tests, `external_interface`. The guard read the mounted sysfs
   interface view instead of the active network namespace. The correction uses
   `socket.if_nameindex`, as the existing native component does. Three targeted
   runner tests passed, including rejection of any additional interface.
2. Commit `c4e9599c87ecb84b3303c0794ff9a408a4ed0697`,
   [run 43079755636](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/43079755636):
   FAIL, 29 executed, zero assertion failures, 27 errors, zero skips. The namespace
   check succeeded. Python 3.12 pathlib imports ntpath while constructing a path;
   the import guard constructs paths while classifying imports, causing recursive
   guard entry. Windows validation had not exposed this Linux interpreter path.
   This is a real reader compatibility defect, not evidence of a database failure.

3. Commit `8b35821cd19db8346a386e1ded9179b78d54ee4f`,
   [run 43081420433](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/43081420433):
   FAIL, 34 executed, 33 passed, one error, zero skips. The actual Linux symlink
   boundary and five reentrant-import regressions passed. The remaining error is
   the standard-library platform module's optional Windows `_wmi` import on Linux.
   The guard correctly refuses an unbound import; its rules are not loosened to
   hide this error. A fresh isolated standard-library bootstrap is under review.
4. Commit `52d71369176e893f4fcd4e524e676567344b36ab`,
   [run 43084939998](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/43084939998):
   PASS, 41 executed, zero failures/errors/skips, 0.493 seconds, Python 3.12.3.
   The fresh isolated bootstrap verifies standard-library origins and compiles
   platform/uuid from the recorded raw source bytes before installing project
   guards. Seven negative bootstrap cases and the actual symlink case execute.
   This closes the narrow Linux import component, not database/endchain admission.
   One local dispatch-client TypeError occurred before any HTTP request was sent;
   it is retained separately. The corrected API call produced one CI run.

All original runs and their logs are preserved; none becomes PASS after a
later fix. The second original artifact has SHA-256
`c9132002e3f1e8cf619b63f6b2bb4bf581d340428175b6b521547c6f52996065`.
Its unabridged result is retained locally. New component output is bounded while
retaining the original technical-log hash, length and an explicit truncation flag.
The third original artifact ZIP has SHA-256
`60d67e8463ca794e4fb4cb73ccaa0580269aa40d1ac5a9213c987717ce73ff7c`;
its result has SHA-256
`700c5025db9e1e0148a4b9479e75b66188c95a695a0ad2dd2da9e242010dfd45`.
Four targeted harness tests pass. The original 452-test receipt has not been
rerun yet; it is not evidence for later changed sources.

## Remaining Gates

| Gate | Current claim |
| --- | --- |
| Original canonical/worker/recovery/closure replay | Work in progress; incomplete domains remain UNVERIFIED |
| Full normal and every-stop command bound | Not closed; unknown dispatch/startup/platform/Auth costs are not zero |
| Actual PG17/GoTrue fault matrix and producer barriers | Not yet executed on this new composition |
| Linux import/symlink boundary | 41/41 component PASS on commit 52d7136; broader replay remains separately gated |
| WAL interval coverage | Prior incomplete intervals retained; no fourth same-method run |
| Combined same-source CI | Not dispatched; hard prechecks still open |
| Hosted attempt and owner phone test | Not used / NO-GO |

## Documentation Check

The [official Supabase changelog](https://supabase.com/changelog.md) was checked.
The CLI v3 breaking change says to adapt CI before upgrading or keep v2 pinned.
This package does not change the existing CLI 2.117.0 pin. The
[local testing documentation](https://supabase.com/docs/guides/local-development/cli/testing-and-linting)
does not turn local database/Auth tests into hosted evidence. No new remote
capability is inferred from newer documentation.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.
