# 6E-11 Request Binding and Migration 42

Date: 28 September 2026.
**M42 installation PASS; complete hosted workflow and owner retest NO-GO.**

## Owner boundary

Only Yourizorge/fitmetzorge-staging, main, and mokxyyullfhkfalopbzd.
The latest owner instruction explicitly separates normal Supabase Auth events
from the application transaction. Earlier reports requiring a shared GoTrue
and workflow transaction are historical, not the current admission condition.

The new contract binds server-verified sub/session_id/issuer/audience/expiry to
a strictly validated request ID, actor, route, role, workspace, action, source,
payload hash and idempotency key. The workflow mutation, request intent and
audit confirmation share one application transaction. A separate post-commit
seal proves the saved after-state and blocks the next mutation if incomplete.
Auth login, refresh, logout and live session revocation still require real
hosted proof; local Auth surrogates are never counted as that proof.

## Implemented scope

- New CLI-created migration: `20260928120846_phase6e11_request_binding.sql`.
- M41 remains byte-identical. M38 workflow and M40 audit core are reused.
- New private schema, two RLS-protected tables and five SECURITY INVOKER functions.
- Fixed `search_path=pg_catalog,pg_temp`; no schema/table/function access for
  anon, authenticated, service_role or PUBLIC. Existing Edge database context
  is necessary because the private audit core intentionally denies client calls.
  The original verified-user principal/workspace guards still decide authority.
- Default-off control with bounded expiry. No managed Auth, Storage or Realtime
  observer, DDL or direct managed-table writes.
- 62 application-table observers use the unchanged private audit implementation.
  Logical row keys, transaction identity and duplicate write multiplicity remain
  visible, including deleted rows.
- Exact predeclared successful/denied/replayed write branches, missing/extra-write
  rejection, idempotency conflict checks, active-session validation and fail-closed
  pending-pair gate.
- Private bounded cleanup admits at most eight rows per batch in the exact revoked
  synthetic window, retaining the independent audit. No hosted cleanup executed.
- New isolated code is under `_offline/phase6e11/request_v4/`. Existing frozen
  sources and uncommitted application candidate changes are preserved.

## Clean database and local evidence

Clean CI: [run 36423073344](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/36423073344).
All 42 canonical migrations applied in order to an empty database.

| Evidence | Result and limitation |
| --- | --- |
| Supabase CLI | 2.117.0 |
| PostgreSQL | 17.6 / 170006 |
| Image | ghcr.io/supabase/postgres:17.6.1.167 |
| Image digest | sha256:6942962433a569e87f228b4d4ab7e11db5deca64e43babb3a038443ad6c4f1bb |
| Real extensions | pgcrypto 1.3; pg_trgm 1.6; pg_cron 1.6.4 |
| Clean build | 42/42 PASS; no migration skipped or mocked |
| SQL regressions | 12/12 PASS |
| Existing audit suite | 22 tests, plus identity checks |
| Driver A/B | 45 complete local PG17/TLS/postgres.js pairs; 110 INSERT, 58 UPDATE |
| Request security | 33/33, including rollback, conflicts, missing observer/seal and retained DELETE proof |
| Existing Edge/scope | 39/39 |
| New request adapter | 6/6 |
| Read-only OIDC gate | 19/19 |
| Installation/load checks | 12/12 |
| Historical Auth receipt unit tests | 17/17; not real Auth proof |
| Buffer mechanics | 18/18 local surrogate tests; not hosted managed-table coverage |
| Deno | Pinned dependency typechecks PASS |
| CI dry-run | EMPTY |

The first CI run 36422416801 built all 42 migrations but failed a historical
workout-only test on Monday, when its default weekly schedule ran early.
The added CI-only fixture adapter disables daily/weekly schedules during that
workout-only setup. The original test later explicitly enables weekly delivery.
Original assertions, original migration and original test files are unchanged.
The initial failure and corrected complete run are both retained.

Local driver receipt:
`supabase/.temp/phase6e11-workflow-local-a51734e39df247a29694bd453b8056b1/request-v4-result.json`.
Security receipt:
`supabase/.temp/phase6e11-request-security-4fb275b9fa374f60a705dfd1c43547f3/request-security.json`.

## Hosted migration and preservation

Migration applied once through the migration-aware CLI. Before: 41; after: 42.
Local/hosted 42/42 match. Registered SQL matches the exact CLI statement partition.

- Local M42 raw SHA256:
  `5eebec968d2dae27d4e1462dbcc9de8d9e5599552ff145ad099e57fffd5f5f7c`.
- Registered statement-join SHA256:
  `21c2db7d134e0c1f1cbaefd56c2836fbf6cfe7a0b816abe20e90226d2832c095`.
  This representation omits CLI statement-separator formatting; it is not claimed
  byte-identical to the original file. Exact statement-partition comparison PASS.
- Unchanged M41 raw SHA256:
  `4d474becdc5c3a7343562602115f9333b5cffc6bed0c323fca3abc560843af7d`.
- 153 protected-table measurements, 100771 streamed row hashes before and after,
  identical protected counts/hashes. No personal content was returned.
- Exclusions: existing cron execution-log exclusion; exact new M42 history row;
  new observer-registry rows validated individually. They are not silently ignored.
- Existing catalog entries unchanged; only the expected new private objects and
  observers added. No managed observers.
- Private control disabled, no request receipts or workflow calls.
- Explicit read-only measurement transactions and confirmed ROLLBACKs.
- Two full streams only, 65 and 72 measured query commands; CLI migration/dry-run
  reservations reported separately. No repeat full scan after the load-stop.
- Follow-up metadata-only closure: 27 commands including eight reserved CLI
  commands; fresh dry-run EMPTY; JIT disabled, zero mappings.

Hosted pair:
`supabase/.temp/phase6e11-m42-be9a04735a66446b82d7503cd0d03831/pair.json`.
Dry closure:
`supabase/.temp/phase6e11-m42-dry-closeout-166cbec729e44984a18e570b280ac621/result.json`.

### Preserved stop and corrected load interpretation

The earlier label attempt stopped before the first content query because the
new qv4 label did not match the proven read-only qv1 protocol. Five transaction
control commands, no hash scan, no migration, ROLLBACK and JIT revocation.

The actual installation saved a complete pair, then the old aggregate timing
guard stopped. Query ID -4197738871146833420 totaled 7852.205846 ms across 14 FETCH
calls. Every saved individual profile is bound to the exact FETCH SQL hash,
has one call, zero temporary reads/writes, and is below 2500 ms; maximum 1098.823567 ms.
Every numeric counter sum equals the aggregate interval. Remaining query IDs
are below the conservative 5000 ms aggregate cap with zero spill.

The old NO_GO receipt is unchanged. A new offline correction verifies all
profiles, detects missing/duplicate/wrong/slow/spilling profiles, and explains
why an aggregate of many calls was not one slow CLI statement. No threshold
was raised and migration 42 was not reapplied.

Own reader/hash temp writes: zero. Database-wide background temp delta was
21429943 bytes in the before interval, zero in the after interval. Its exact
background producer remains unproven; it is not attributed to the zero-spill
collector. This is not a claim of zero database-wide IO or long-term recovery.

## Server-only connection admission and exact blocker

Service-role/proof/database secrets were not exported from Edge. A temporary
read-only diagnostic used signature-verified GitHub OIDC bound to one exact
repository, main commit, CI run and expiry; no application actor was inferred
from CI identity. This is a control-plane probe, NOT real Supabase Auth proof.

Auto-review initially rejected the new JWT-gateway-disabled OIDC boundary.
The owner then explicitly approved only this bounded read-only diagnostic.
Run 36426447746 was cancelled without invocation.
Run 36426724594 failed before the database on the old OIDC subject format.
The verified repository was created after GitHub's immutable-subject rollout;
the corrected subject pins owner ID 292557331 and repository ID 1330119916.
Run 36427380641 passed OIDC verification, then returned
`database_configuration_invalid` before opening a database connection.

This proves that the Edge-injected database URL fails at least one strict
protocol/host/5432/database/postgres-role/password/options/verify-full condition.
It does NOT yet identify which field differs. No URL, password or token was logged.
No authentication attempt, fixture mutation or managed-table access occurred.

A further diagnostic deployment with field-specific fixed error codes was
rejected by auto-review as beyond the bounded attempts. Run 36427882283 was
cancelled. No workaround, weaker host/TLS rule or new credential route was used.
The additional diagnostic remains local only.

The temporary function `fmz-phase6e11-proof` (exact ID
144aba78-4fc4-46ad-8213-2141ffac82d1, version 2) was deleted and management GET
returned 404 at 2026-09-28T13:21:58Z. Its access deadline was already
2026-09-28T13:20:50Z. JIT remained disabled with zero mappings.
The actual `fmz-phase6e11` application Edge function was not redeployed.

Receipts:
`supabase/.temp/phase6e11-request-ci-receipts-442c38dad2df438ebea001488f865eb1/result.json`;
`supabase/.temp/phase6e11-request-probe-close-206b6443675d44fb9c13419567a3ec84/result.json`.

## Advisors and retained scope

M42 has no public execute rights, unsafe search_path or new definer. Advisors
report intended no-policy RLS on its two inaccessible private tables, and unused
indexes because the bridge is disabled. Existing project findings remain:
public.touch_updated_at mutable path, 68 authenticated definer RPCs,
47 RLS initplan warnings, 21 unindexed FKs and disabled leaked-password protection.
These are not silently marked globally clean or altered outside this task.

189 frozen files, 88 local candidate runtime assets, 5372 historical artifacts,
888 reference artifacts, 58 prior CI sources, all 112 valid historical pairs and
incomplete historical step 113 pass preservation checks. Original status bytes
are archived before the new current entry. Historical fixtures/accounts/sessions
remain untouched. No new Auth/app fixtures need cleanup.

84 published runtime assets still match the accepted baseline byte-for-byte.
The existing dirty app.js/index.html candidate was not published.
New commits contain only the scoped migration, offline/CI material and documentation.
Pages and private-path verification are recorded separately in the new evidence.

## Remaining gate

6E-11 is NOT Technical Pass as a whole. Real hosted Auth login/refresh/logout,
full request-bound A/B transactions, hosted cleanup DELETE and the final complete
chain preservation proof remain unexecuted. No owner window, freeze or 6E-12.

The immediate blocked operation is a new strictly read-only server-side diagnosis
of which Edge database-configuration guard fails, without revealing its value.
Auto-review requires a new explicitly bounded authorization for that diagnostic;
the prior short read-only authorization is closed. This does not authorize a
mutating OIDC controller, role widening, secret export or password reset.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.

References: [Auth sessions](https://supabase.com/docs/guides/auth/sessions),
[Edge secrets](https://supabase.com/docs/guides/functions/secrets),
[GitHub immutable OIDC subjects](https://docs.github.com/en/actions/reference/security/oidc#immutable-subject-claims),
[Database advisors](https://supabase.com/docs/guides/database/database-linter).

