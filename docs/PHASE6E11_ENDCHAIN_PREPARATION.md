# 6E-11 Hosted End-Chain Preparation

Date: 2026-10-12. Status: **NO-GO for the full hosted chain and owner phone test**.

This follow-up starts at `298f62bb8cc02b13a0a58425ce835225ddd68132` on
`Yourizorge/fitmetzorge-staging/main`. It does not change a frozen package,
application runtime, migration, Edge deployment, ordinary account or member row.
There is no JARVIS handoff and no 6E-12 server integration.

## Evidence Reused, Not Expanded

The accepted, bounded audit probe and clean 43/43 CI evidence remain valid in
their original scope. See `PHASE6E11_AUTH_METADATA_FOLLOWUP_REPORT.md`.
The audit probe did not issue real Auth tokens or execute the full workflow.
Historical failed attempts, the 112 valid pairs and incomplete step 113 remain
unchanged. New offline assertions do not fill missing historical measurements.

## Light Hosted Preflight

One read-only metadata query returned:

| Scope | Observed count/state |
| --- | --- |
| Registered migrations | 43 |
| Enabled registered synthetic identities | 3 |
| Sessions for those registered identities | 0 |
| Live 6E-11 test windows | 0 |
| `fmz6e11_private.workspaces` | 0 |
| Incomplete request receipts | 0 |
| Running private controllers | 0 |
| Temporary guard/audit schemas | 0 |
| Request control | disabled; not unexpired |
| Registered observed relations | 64 |

These are narrowly scoped counts, not a full database preservation measurement,
new Auth proof, JIT recheck, dry-run or cleanup of older package fixtures. No
hosted mutation, token issuance, pooler probe or fingerprint scan was started.

## New Offline Preparation

`_offline/phase6e11/endchain_v1/` compiles a source-bound preparation plan from
the unchanged 45-action product scenario and the existing exact Auth contract.
It is not an executable hosted controller or a hosted admission receipt.

The workflow source SHA-256 is
`3343f906077c766e95e4d06b7cf9b9b7752ada8b0a9805a77a8203644cb27da9`.

- Three actors each run issue, verify, get-user and refresh before the workflow.
- All 45 Route A/B actions retain their original requests and expected writes.
- Fixture revocation and measured deletion must precede logout.
- Each actor then runs logout and a real server request with the revoked token.
- Guard/audit safety removal and JIT revocation remain unconditional safety work;
  uncertain fixture deletion never bypasses a missing pair.
- Every action still requires the existing row-key/transaction validator. Table
  counts alone are never sufficient evidence of allowed writes.

Expected effects from the existing scenario are 168 workflow writes plus 66
Auth writes. These are preregistered expectations, **not observed hosted writes**.
Auth effects are bound to the previously tested GoTrue v2.196.0 contract. A
hosted mismatch must stop, not silently broaden that contract.

The 27 new unit checks cover ordering, source identity, all original cases,
Auth effects and delete requirements, denial/replay effects, lifecycle gaps,
budget rejection and rejection of false hosted-admission claims. They do not
replace real local/CI database execution or hosted Auth verification.

## New Local Verification

| Check | Result | Boundary |
| --- | --- | --- |
| New preparation/ordering tests | 27/27 PASS | No network or database |
| Existing controller/manifest/guard/write-validator regressions | 131/131 PASS | Unit tests, not hosted authorization |
| Original Route A/B through the actual local PG driver | 45/45 complete pairs PASS | Disposable PostgreSQL 17.6; local Auth stubs |
| ACL, request/session/hash conflicts, rollback, seal and delete tests | 33/33 PASS | Disposable local PG17; not real hosted Auth |
| Protected source/history preservation | 1,376/1,376 unchanged | SHA-256 file comparison; not member-data fingerprinting |

New immutable local preparation receipt:

`supabase/.temp/phase6e11-endchain-54c480a0130e464da2cd7d76f6598976/manifest.json`

SHA-256:
`681fa365fca5e53d5b237dd2cc62df26a01b7d66b9c10ee23d19e3ceb076315f`.

Database evidence directories:

- `supabase/.temp/phase6e11-workflow-local-da02bc0b345940d0bd3fb8396e0c086d`
- `supabase/.temp/phase6e11-request-security-29f6d32d0e124005bbd2e38f177014e1`

The first local launch stopped before its first workflow action because
`FMZ_DENO` was unset. Its failure record remains in
`phase6e11-workflow-local-55c396586baf4141bd37094c85e350b1`.
Setting the already present Deno 2.9.7/cache paths fixed the local environment;
no dependency download, runtime-code edit or hosted retry was used.

The tests are reported separately, not as a combined hosted-PASS total.
The six earlier modified tracked files remain intact. New preparation files
and this report are local additions; no commit, push or publication is claimed
by these receipts.

## Execution Limit Requiring a Separate Decision

The existing M43 storage constraint, controller and manifest limit remain 128
SQL commands. No file or hosted constraint implementing that limit was changed.

With the current evidence store, each action requires five separate commands:
`before_saved`, `action_started`, `action_confirmed`, `after_saved`,
`pair_validated`. The 45 workflow plus 18 Auth actions therefore require **at
least 315 evidence commands**, excluding actions, measurements, setup and cleanup.

A single bundled owner question requests a separate maximum of 1,280 commands
for this full end-run, ten minutes, one collector and zero retries. The original
128-command canary limit, row limits and IO limits would remain intact. At this
report's preparation stage that question is pending. It is not permission to
alter the limit. Splitting artificial run IDs or resetting counters is forbidden.

Even approval of that ceiling would not be admission by itself. The final
composition must first provide a complete command ledger within the approved
ceiling, source-bound clean CI and exact lifecycle contracts. Any necessary
private-storage change must be additive and migration-aware; M43 stays immutable.

## Still Required Before Hosted Admission

1. Compile exact fixture preparation/activation, access-negative and bounded
   cleanup contracts, including row keys and retained delete evidence.
2. Assemble the actual controller endpoint, real Auth adapter, workflow bridge
   and lifecycle adapters. Preserve server-side secrets and existing authority.
3. Bind fresh CI admission to every byte of that composition and its plan;
   earlier CI does not automatically cover these new preparation files.
4. Count every transport, measurement, evidence, lifecycle and safety command;
   preserve independent safety-removal capacity and deadline enforcement.
5. Perform one admitted hosted chain with complete pairs, exact writesets,
   protected-data and own-IO proof; then exact owned cleanup and closure checks.
6. Only after the complete chain and final checks pass, prepare a new bounded
   synthetic owner phone window. No window is opened by this preparation.

Current official Supabase Auth session guidance still requires server-side
session checks for strict revocation: an access token alone is insufficient.
TLS/CA/hostname validation and SSL enforcement remain mandatory. No password,
privilege, RLS or secret changes were made while checking documentation.

References: [Auth sessions](https://supabase.com/docs/guides/auth/sessions),
[function authentication](https://supabase.com/docs/guides/functions/auth),
[changelog](https://supabase.com/changelog).

External AI calls/cost: 0 / EUR 0.00

Real-member AI enabled: NO

Production touched: NO
