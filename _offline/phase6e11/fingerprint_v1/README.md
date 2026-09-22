# Offline Fingerprint v1

This directory is not an application component. It has no Supabase credentials,
remote database transport, mutation implementation or hosted runner integration.
Only a locally created PostgreSQL cluster on 127.0.0.1 ports 55000-59999 is supported.

From the staging repository, using Python 3.11+ and installed PostgreSQL 18 on Windows:

```powershell
python -m unittest discover -s _offline/phase6e11/fingerprint_v1 -p test_offline.py -v
python _offline/phase6e11/fingerprint_v1/benchmark.py
node _offline/phase6e11/fingerprint_v1/publication.cjs
```

The first two commands create only synthetic local data, stop their local clusters
and retain all evidence/files. The third only reads staging GitHub Pages and local
Git; it never queries Supabase. FMZ_LOCAL_PG_BIN can locate the already installed
local PostgreSQL binaries. Do not point this code at staging or add a remote DSN.

The immutable budget ledger permits at most 3 full cycles and 128 query commands
per explicitly selected budget directory. Restarting with a new run ID does not
reset that budget. A repository-wide process lock also excludes a different budget
directory. A crash leaves the lock in place: there is no automatic stale takeover.
Unit crash tests use an isolated lock_scope; production callers must not override it.
There is no code that creates a replacement budget after failure or retries a query.

Rows are converted to SHA256 on PostgreSQL, streamed in single-row mode and sorted
locally in bounded digest-only chunks. Completion requires the PostgreSQL terminal
row count, all chunks' verified digests, transaction completion and saved identity.
No row payload is stored. Digest files remain pseudonymous sensitive material if
ever applied to real data; these tests contain synthetic data only.

The identity manifest excludes clocks/run IDs and is byte-reproducible. Operational
journals deliberately keep unique run IDs and timestamps. Pinned settings are a
versioned contract, not proof of undocumented historical settings. Compare the
transition manifest before any future baseline handoff.

targeted() always fails: complete write-coverage is not proven. The legacy hosted
runner remains paused and unmodified. See docs/PHASE6E11_EFFICIENT_FINGERPRINT_REPORT.md.
