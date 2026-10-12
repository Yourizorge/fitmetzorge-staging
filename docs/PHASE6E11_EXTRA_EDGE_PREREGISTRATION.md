# 6E-11 additional Edge probe preregistration

Owner grant: 12 October 2026, one additional read-only Edge attempt, separately
accounted for from the three exhausted resumption attempts. Baseline main:
`ea77e48cb16e50178cf43508fd14e2f2f9a6be40`. Package 6E-11 and owner test remain NO-GO.

## Fixed experiment

- Reuse the byte-identical, locally proven `resume_v1/read_only.mjs` helper and
  native Postgres.js 3.4.7 driver with `fetch_types:false`, no `reserve()`, max:1,
  max_pipeline:1 and prepare:false. Do not change the historical candidate.
- Same official session endpoint, IPv4/5432, CA and hostname-validated TLS;
  explicitly observe the handshake of this exact attempt.
- Exact current main commit / GitHub run / attempt-one OIDC binding; at most
  ten minutes. Default checked-in binding continues to deny access.
- One socket, no retry; DNS 2 seconds, connection/BEGIN 5 seconds, each subsequent
  metadata command 2 seconds. Close deadline 1 second.
- Exactly BEGIN TRANSACTION READ ONLY, transaction/backend guard, project-instance
  identity and ROLLBACK. No catalog discovery, row scans or application writes.
- Confirm same backend, explicit read-only, exact instance, rollback and connection
  closure. Preserve both transport phase and SQL phase with sanitized timings.
- Remove only the exact newly deployed diagnostic identity. JIT must remain
  disabled with zero mappings; no lease is needed for the existing Edge secret.

## Local gates and outcomes

Run the proven helper tests, new trace failure tests and existing connection/OIDC
tests before deployment. Bind the deployment bundle and receipts to SHA-256.
Preserve original evidence and dirty files. No historical report is overwritten.

PASS admits prepared synthetic hosted workflow checks, not a workflow/data PASS.
Any incomplete result blocks dependent writes, cleanup and the owner test window.
No retry under this grant. Independently testable documentation/code may continue.

No additional migration, privilege, password change, real-member AI, provider call
or production activity. 6E-21 remains unaccepted. Durable synthetic 6E-12 starts
only after the complete 6E-11 chain passes, not after connection success alone.
