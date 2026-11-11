# 6E-11 Linux Native Client Component

Status: SYNTHETIC COMPONENT OBSERVED / FULL ADMISSION REMAINS NO-GO.
This is not full-chain, hosted or owner admission. The 2349-command hosted
limit and the existing WAL stop remain unchanged. No Supabase request is
authorized or performed by this component.

## Sources And Scope

- Reviewed source manifest SHA-256:
  `6e515f0f5394634db4221f558ca874f4548d52b4af2cdb4e4518d58dcc50d871`.
- Existing native adapter SHA-256:
  `9d086efe38a5b42b83684754cdc644ed461fbb9ee0311d5ca53fff5445b5ac3a`.
- Preserved synthetic peer SHA-256:
  `715a5ca9335a68e346f010d122b13652703926cd03b2d67604af3bfb34176daf`.
- Manual workflow: `phase6e-native-connect-component.yml`, staging main only,
  first attempt only. No automatic retry or hosted workflow dispatch.

The pinned peer is reused unchanged. Fifteen synthetic cases distinguish
ordinary connection/close, target-session probes, explicit queries and
transactions, failed authentication, EOF and a five-second startup timeout.
The peer is not PostgreSQL and its AuthenticationOk is not SCRAM or GoTrue.
The existing incomplete EOF-capture limitation is preserved.

All driver traffic runs in a new loopback-only Linux network namespace. The
runner drops groups and capabilities and sets no-new-privileges before Python
runs. Missing isolation fails closed. TLS certificate verification remains
enabled; the temporary synthetic CA/key stay outside the artifact directory.
No application or database writes occur. No CI or database secret is passed
to the driver process. Public dependency retrieval precedes network isolation.

The six binary-only CPython 3.12/x86_64 dependency wheels have exact public
PyPI URLs and SHA-256 pins. Installation uses no dependency discovery,
source build, inherited pip configuration or retry. The component records
actual Python, psycopg/libpq and support-library binary identity and effective
nonsecret connection parameters. A Windows binary/version is not Linux proof.

## Limits And Evidence

- Package installation: 150 seconds, plus five-second forced-stop allowance.
- Unit child: 60 seconds; component child: 240 seconds.
- Namespace supervisor: 340 seconds; workflow: 12 minutes.
- One outer driver dispatch per case, 15-second case deadline and the existing
  five-second connect timeout. No assumed bound on unobserved internal retries.
- At most 24 original technical JSON members plus their export manifest.
- Exclusive evidence writes, SHA-256, fsync/readback and waited process exits.
- No private PEM, environment dump, raw child output or connection string in
  exported artifacts. Incomplete outcomes remain incomplete.

Main independently repeated 32 offline adapter/supervisor tests: PASS in
0.806 seconds. All nine required source hashes matched the installed files.
These are unit/source checks, not an actual Linux execution. The Linux job
also selects nine original peer negative tests before the 15 wire cases.

Even a successful component reports `driver_implicit_sql_bound=null`,
`actual_postgres_test=false`, `wal_observed=false`, `full_admission=false` and
`hosted_admitted=false`. Interpretation against the actual Linux client and
the remaining full-case/platform/managed-Auth evidence is separate work.

External AI calls/cost: 0 / EUR 0.00. Real-member AI enabled: NO.
Production touched: NO.

## Actual Linux CI Observation

Source commit `644775f890224c56808e4faf4b4570d857955887`; one manual run,
[43047774041](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/43047774041),
attempt 1: success. Artifact `13866944261`, ZIP SHA-256
`37aee24c83cebf7a85c55b13d4abcdb75b56732ce17663ef3aa612de7764b8d6`.
Main independently checked all 25 JSON members, the 24 export-member hashes,
the component reference hashes and all nine source hashes. Original ZIP and
the create-only verification receipt are retained in the ignored evidence
directory `supabase/.temp/phase6e-native-component-c71123e3a632452d9fd485f2eff51ac2/`.
The 25 original JSON members and the independent verification receipt are also
retained under `_offline/phase6e11/endchain_v1/native_connect_component/receipts/run-43047774041/`.
All 26 files passed the unchanged source/secret scanner; no private work files
or PEM were copied. This private source directory is excluded from Pages.

- 41 unit/negative tests: no failures, errors or skips.
- 15 synthetic wire cases observed, one outer driver dispatch each.
- Both child processes returned zero and were waited; no timeout or kill.
- Fresh loopback-only namespace, zero capabilities, non-root execution and
  no-new-privileges were recorded. No database was contacted.
- Python 3.12.3, psycopg binary 3.2.10, actual libpq build/runtime 170005.
  This is not the previously reviewed Windows libpq 160009, nor an assumed
  Linux 170006. Before/after binary inventories are byte-identical.
- Normal controlled connections emit no observed SQL. Explicit transactions
  show their expected BEGIN/COMMIT/ROLLBACK messages. Ambient target-session
  probes demonstrate one extra SHOW or SELECT; the controlled `any` option
  suppresses those probes in its observed case. These finite observations
  are not a universal upper bound on driver-internal commands or retries.
- Startup timeout: ConnectionTimeout after 5.107201 seconds. Authentication
  rejection and startup EOF: OperationalError. The startup-EOF case retains
  `capture_to_client_termination=false`; it is not complete negative proof.

The peer uses synthetic AuthenticationOk, not real PostgreSQL authentication,
SCRAM, GoTrue or a Supabase pooler. No WAL measurement was performed. Source
and binary observations do not attest the complete library build provenance.
`driver_implicit_sql_bound` remains null. Full command closure, platform and
managed-Auth accounting, full-chain CI and the existing WAL blocker remain
open. This run does not consume or reopen a hosted attempt.

Pages verification at this exact source commit also passed: run `43047313002`,
artifact `13867956440`, SHA-256
`7a54c4c73b704a8a5f107ec79270cb5a1106e55593078e286bf241894f081317`.
All 152 protected runtime assets are byte-identical, all private roots are
absent from the 819-entry artifact, and all seven private HTTP probes return
404. This checks publication isolation, not a live database workflow.
