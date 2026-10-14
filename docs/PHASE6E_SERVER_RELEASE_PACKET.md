# Synthetic Server Integration Release Packet

This is the next local/CI candidate, not a hosted release or a request to enable
all packages together. Package 6E-21 is still pending owner review. No medical,
nutrition, privacy or language validation is inferred from technical tests.

## Delivered Local Chain

One default-off entry in `_offline/phase6e_server_v1/` connects the accepted
source contracts to PostgreSQL and real local GoTrue:

| Area | Implemented candidate | Boundary |
| --- | --- | --- |
| Intake and editable B plan | Versioned intake, exercise/day/set and catalog portion changes | Missing/conflicting rules deny proposals; no new physical rules |
| Registration | Workout/set and meal records, immutable correction revisions, original snapshots | Explicit completion; partial food records are not a complete intake |
| Reflection | Reliable planned/actual facts and exact product-version subtotals | No invented targets, progression or missing registrations |
| Signals and check-ins | Shared Today state, existing source-bound signals, stale-review invalidation and deduplication | No background scheduler or external notification delivery |
| Review and application | Separate member/trainer decisions for A, no trainer step for B, atomic application | A physical changes require explicit trainer authority; only the existing check-in option is admitted here |
| History and restore | Old registration/plan versions remain; restore creates a new approved version | No destructive rollback or history replacement |
| Safety | Consent, source expiry/conflicts, separate RIR/RPE and null/zero, health restrictions | Self-reported recovery is not medical clearance; incomplete comparable windows block conclusions |

## Exact Source And Migration Boundary

The candidate is
`_offline/phase6e_server_v1/supabase/migrations/20261014105919_phase6e_synthetic_server_candidate.sql`.
Its identity was created by the pinned CLI. It is not in the canonical hosted
migration directory and is not applied to staging.

The executable composition is `domain.cjs`, `worker.cjs`, `store.py`,
`protocol.py`, `server.py`, `ui.html`, `ui.js` and `ui.css` in that directory.
Frozen imports are included by exact hash in the CI candidate manifest.
`ci.py`, `ci_auth.py`, `database_tests.py`, `domain.test.cjs`,
`browser_checks.cjs`, protocol tests and release-packet tests bind the proof.
Every verified artifact contains the source commit, candidate digest, archive
digest and per-file hashes. Older green receipts do not admit changed files.

Current local proof: CI `38586129123`, source
`f2fda85fed087b7a0aa36a2cc3d0f8876b4d5a6d`, candidate
`e8eee895191db485b8549dd8dd5fb951f4984f90adf55fdbaeb771f15f350b13`,
archive `f6c68a569466ddfb605acb6f9c599a20b9c74f445e53480cdd264795cfa6a938`.
Clean 45/45, local dry-run empty; 22 domain, 49 database, 4 real Auth and
204 browser checks, plus 5 protocol and 4 release-budget unit tests.
The 12 existing SQL regressions and 30 M44 database checks also pass.

## Rights And Configuration

- Entry is disabled unless the local operator explicitly enables
  `FMZ_LOCAL_INTEGRATION_ENABLED`. Private configuration supplies only the local
  database, local Auth endpoint and exact synthetic workspace allowlist.
- The server binds to loopback. Database connections require verified TLS and a
  local CA. A hosted endpoint is deliberately rejected by this candidate.
- Auth tokens stay in server memory. An opaque HttpOnly/SameSite cookie and
  same-origin CSRF check protect the local browser entry. Each operation verifies
  the current Auth identity and live session before using the restricted DB role.
- `fmz6e_integration_server` is NOLOGIN, NOSUPERUSER and NOBYPASSRLS. Private
  tables have workspace/participant RLS. There is no browser-controlled role,
  public Data API grant or public SECURITY DEFINER endpoint.
- Writes use transaction-local identity/request binding, expected version,
  payload hash, immutable revisions and a durable idempotency receipt.
- The candidate uses the explicit historical synthetic source clock. A real
  server clock/expiry binding is a separate admission requirement, not silently
  inferred from these examples.

## Command Register

`release_packet.py` builds a machine-readable dossier from verified CI
receipts. It includes application, fixture-admin, managed Auth, migration CLI,
dry-run and all eight before/after observer commands per CLI operation.
An older receipt without those observer commands is rejected.

This CI observed 3,420 commands: 1,841 application protocol, 81 fixture-admin
(including three expected permission denials), 1,433 managed Auth, 47 migration
CLI, 2 dry-run CLI and 16 observer protocol commands. This local test allowance
is separate from the 2,226-command one-off hosted 6E-11 limit.

The bounded proposed capacity is 4,015 ordinary commands plus 120 safety
commands, maximum 4,135. This is NOT the 6E-11 allowance and is not authorized
hosted expenditure. Actual local usage must be taken from the current receipt.
It cannot be replaced by the capacity or by a simulated zero measurement.

| Next-release phase | Proposed cap |
| --- | ---: |
| Three bounded protected streams | 93 |
| Identity, rights, sources and expiry metadata | 12 |
| Candidate migration and dry-run, including observers | 65 |
| Fixture setup, negative controls and cleanup | 90 |
| Application transaction protocols | 2,055 |
| Managed Auth protocols | 1,700 |
| Separate failure/closure reserve | 120 |

The twelve metadata slots, new-schema protected-stream exclusions, hosted Auth
audit and transport must still be bound to executable hosted admission. They
are explicit open gates, not a claim of a complete hosted proof or a reason to
start deployment. Before a later GO, replace estimates with the selected slice's
source-bound register, exact synthetic identities and complete failure paths.

## Release Order And Rollback

1. Complete 6E-11 hosted proof and its separate physical owner test.
2. Select only durable synthetic registration-12 as the first hosted slice.
   Do not turn on the broader 12-21 candidate as a bundle.
3. Bind a server transport, live session/expiry checks, exact synthetic actors,
   source hashes, rights, write sets, protected baselines and command register.
   No database or service-role secret may reach the browser or Pages.
4. Obtain one bundled release decision for that exact migration, scope and
   budget. Preserve default-off flags until admission and migration checks pass.
5. Prove reload/relogin, cross-user denial, stale sources, duplicates, atomic
   faults, old versions, delete audit and protected data on the selected slice.
6. Open a bounded synthetic window only after complete before/after evidence.

Rollback first disables the new entry and synthetic participants. Keep audit,
registrations and prior versions. An eligible plan restore is a new proposal
with the required fresh approvals. Do not drop histories, rewrite migration
history or reset real accounts. Fixture deletion requires exact ownership and
complete scoped delete evidence.

## Review Gates

6E-21 physical acceptance, content/trainer rules absent from the sources,
expert training/nutrition/medical and NL/EN/DE review, and purpose-specific
privacy/retention remain separate gates. Future real-member providers also
require the accepted consent, DPA/DPIA, ZDR/EU-route and cost conditions.

No hosted deployment, real-member processing, AI calls or costs are enabled
by this packet. Production and JARVIS remain outside scope.
