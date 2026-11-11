# 6E-11 Linux Native Client Component

Status before dispatch: OFFLINE UNIT PASS / LINUX OBSERVATION PENDING.
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
