# 6E Integration Completion Report

## Verdict

**6E-11 hosted: NO-GO. Independent local integration: LOCAL/CI PASS.
No hosted integration release, owner window, acceptance or freeze.**

Scope: Yourizorge/fitmetzorge-staging main, Supabase mokxyyullfhkfalopbzd only.
The current matrix is `PHASE6E_CURRENT_COMPLETION.md`; historical reports and
older uncommitted work were not overwritten. The new complete hosted attempt
remains unused. The old attempt remains used and NO-GO.

## One Authorized Hosted Diagnosis

- Run `e91ae17a-357c-4af3-a10a-dc2de7c471f7`:22/128 SQL commands, one collector,
  no retries, five complete numeric before/after pairs;14.688s through rollback.
- Explicit repeatable-read READ ONLY transaction, same backend/snapshot/project
  instance, session pooler with JIT, verified CA/hostname and SSL enforcement.
- The observer's EXPLAIN ID equals its numeric counter. Synthetic NULL/duplicate
  rows transfer correctly. The exact original stream is DECLARE/CLOSE only:
  zero real hash rows fetched, no personal/chat/health contents exported.
- The tested utilities each produced exactly one other changed query counter.
  All observed collector deltas had zero temporary blocks and zero WAL;
  original DECLARE332.725ms, observer about40-46ms.
- Database-wide temp_bytes stayed898319773249 across the sampled interval;
  sampled IO-wait and long-active counts were0. This is a short observation,
  not a new general project-performance certification.
- Rollback confirmed, connection closed, JIT disabled,0 remaining mappings,
  SSL enforcement retained. No migration/Auth issuance/application writes.

**Cause remains unresolved:** the old rejected samples were never saved. The
new probe did not reproduce the attribution failure. It cannot prove old
background interference, reconstruct the missing samples or change the old
verdict. The conditional cause/admission gate for another full run is not met.

New error handling preserves the primary error when stop-receipt storage or
rollback also fails. Local failure injection covers evidence-storage phases,
read-only denial, counter resets, temporary writes and reserved closure budget.
The numeric receipt is archived under
`_offline/phase6e11/utility_diagnosis_v1/receipts/e91ae17a-357c-4af3-a10a-dc2de7c471f7/`.
Its manifest SHA256 is
`58383ec0060f1d9052590285e7e483cbc314787d77e0c19c5776b0608359adab`.

## Independent Integration

The existing single local server candidate now includes a transactional private
outbox. Source correction, viewed/declined/superseded/applied/withdrawn/expired
states are distinct; event identity deduplicates repeat processing. Outbox,
revision, request receipt and audit write in the same transaction. A fault
after any write rolls back all of them. There is no push/mail delivery or
background worker. Expiry is enforced on access and projected in the view;
later authorized processing can persist an expiry event.

Complete comparison windows use frozen13's explicit three-plus-three-day
policy for sleep, recovery, nutrition and training.24 version-bound, complete,
comparable synthetic source rows are required. Missing/conflicting/expired
rows stop conclusions. The six-day example is explicitly a synthetic source
series, never an invented completion of missing daily records. Subsequent
source corrections advance comparison revisions without deleting history.

Planning resolves an explicit approved time and timezone. DST gaps are rejected;
ambiguous times require an explicit fold. The accepted UTC fixture/date remains
unchanged. No medical cadence, sleep norm or nutritional rule is invented.

The combined Today view retains planned-versus-recorded distinction, exact
portions, snapshots, source-bound proposals, separate Route A/B approvals,
versioned restore and guided expectations. Package21's full-day writes require
an additional flag that is absent by default.21 remains unaccepted.

## Selected Release12

The separate registration12 adapter uses the unchanged frozen12 validator and
the minimal M45 private schema, without the optional M46 outbox or package21.
It supports historical workout registration/corrections and facts only, not
new physical prescriptions or plan application. Exact operator-controlled
workspace/member bindings, actual database-clock expiry, RLS, receipt payload
binding, concurrency, unchanged snapshots and permanent delete metadata are
tested before optional M46 is applied.

The two local entry flags are mutually exclusive and default off. Browser roles
are not authority. GoTrue tokens remain server-side; local HTTP uses HttpOnly
sessions and CSRF. Database TLS uses verify-full and explicit CA validation.
The local adapter deliberately rejects hosted endpoints. Its future hosted
transport/lifecycle admission, exact release identities, full safety budget
and concrete release decision remain gated by complete6E-11 and ownerreview.
The old4135 proposal is not an authorized budget.

The source-bound release dossier records all observed native transaction,
fixture, Auth, migration, observer and dry-run command costs, including
BEGIN/COMMIT/ROLLBACK. It is local evidence, not permission for a hosted run.
Rollback is feature/subject disablement while retaining revisions/audit; never
history deletion or rewinding a migration.

## Proof and Preservation

Final CI38603611445 is PASS, bound to source
`1f005f7313e8a3b434bdbe6bdc23eb903273733c`, candidate SHA256
`977007b04bbffebafbd5e3881f31048343870b69e214583594ed6aa53476969f`,
and verified artifact SHA256
`dba34dbc640fc8c88d8f01da1106d02bd48b5390502a50cfd494c7bab1bfeea6`.
437 artifact files were independently hash-verified;77 selected receipts,
screenshots and source hashes are retained in the completion archive.
Earlier runs38597382064 and38598753663 remain separate evidence, not replacement
tests or admission of changed sources.

| Evidence | Passed checks |
| --- | ---: |
| Frozen-domain reuse, complete windows and registration12 | 29 |
| Combined real PostgreSQL/Auth database behavior | 62 |
| Minimal registration12 database behavior before M46 | 25 |
| Combined real-Auth browser assertions | 209 |
| Separate registration12 real-Auth browser assertions | 15 |
| Real GoTrue relogin/revocation checks, four per entry | 8 |
| Existing SQL regressions | 12 |
| Existing M44 database/security checks | 30 |
| Local helper unit checks in CI | 25 |
| Independent receipt-accounting tests | 2 |
| Diagnosis failure-injection tests / stream tests | 7 / 5 |

CLI2.117.0; PostgreSQL17.6; container
`public.ecr.aws/supabase/postgres:17.6.1.167`, image SHA256
`66089200353d90686fe9b252a47d17d078364bf47c50190852c33dc850a0191f`;
real GoTrue2.197.0. All44 original migrations build first, then minimal45;
the first slice passes with an empty dry-run before optional46. Final46 dry-run
is empty. pgcrypto, pg_trgm and pg_cron are real installed extensions, not mocks.
The platform receipt's availability snapshot precedes migrations; the final
extension checks establish actual installation.

M45 SHA256: `51953e164c2431299bf8825d08e30fe776434a99c8766a9e1faeb3c956d05b0d`.
Local-only M46 SHA256: `fc0edf31bff828256d3719713bc269646c908673f121ccbce0b26099d7c8b650`.

The minimal selected12 test register totals970 commands:

| Measured phase | SQL commands |
| --- | ---: |
| M45 apply / empty dry-run | 47 / 2 |
| Numeric migration observers | 16 |
| Disposable cron isolation and restoration | 16 |
| Meter configuration, metadata and restoration | 10 |
| Fixture/clock/denial/cleanup/Auth observers | 26 |
| Actual local Auth, relogin and revocation | 488 |
| Registration read/write/rollback/terminal protocol | 365 |

These are actual selected-slice local costs, not a hosted maximum or the cost
of every bootstrap/advisor statement in the full CI job. The subsequent wider
integration has2447 application,86 fixture/admin and1653 Auth commands, plus
66 M46/dry-run/meter/isolation commands. Its measured subtotal is4252, distinct
from selected12 and from the2226 hosted6E-11 ceiling. No count authorizes hosting.

| Local measured role | Temp blocks written | WAL bytes |
| --- | ---: | ---: |
| Registration12 restricted application role | 0 | 89401 |
| Registration12 postgres fixture/observer role | 0 | 21402 |
| Registration12 Auth role | 0 | 40730 |
| Combined restricted application role | 0 | 8691450 |
| Combined postgres fixture/observer role | 0 | 715906 |
| Combined Auth role | 0 | 51539 |

Numeric-role observations overlap protocol accounting and are not extra commands.
They are isolated local-CI evidence, not historical hosted attribution. All four
CLI protocol/independent numeric comparisons pass with zero temp writes. Raw
numeric samples remain available; no query text or credentials were exported.

The local registration cleanup proves10 exact deletes (4 receipts,5 revisions,
1 workspace); the combined cleanup proves117 (20 outbox,46 receipts,47 revisions,
4 workspaces). Hashed deleted keys and transaction IDs survive cleanup, and the
independent control record is unchanged. Disposable local Auth/container teardown
is not a claim that old hosted identities or fixtures have been deleted.
The focused visual regression has96 checks across NL/EN/DE, mobile/desktop,
light/dark; its synthetic read-only API fixture is not database evidence.

Two extra local evidence issues were found and retained rather than hidden:

- CI38600298004 stopped because the Auth-specific1024-counter validation cap
  was also applied to the postgres role's unchanged migration history. The
  corrected local reader retains the full bounded raw samples (maximum5000),
  excludes only exactly unchanged entries from the delta validator, and still
  rejects resets, missing/replaced/duplicate counters, negative deltas and temp
  writes. No hosted measurement rule was relaxed.
- CI38601417852 passed function/security/browser checks, but its later release
  dossier correctly refused the incomplete M45 CLI receipt:47 CLI commands
  versus49 numeric calls, with pg_cron and an unnamed application in the log
  window. This is not a complete release PASS. Its partial archive is explicitly
  INCOMPLETE and the original artifact remains immutable. The corrected local
  wrapper stops CI immediately on incomplete CLI attribution. It suspends job
  launching only in the disposable Docker CI database around each measurement,
  requires zero active cron queries, restores the original setting even on
  error, and includes all isolation/restore commands in the register. No staging
  cron configuration was touched. The extension remains installed, not mocked.
  This local isolation uses the documented reloadable
  [pg_cron launch control](https://github.com/citusdata/pg_cron#extension-settings).
- CI38602926486 then stopped before M45 when the local postgres role could not
  set that configuration parameter. The wrapper was corrected to use the
  existing supabase_admin Docker-only control path, pinned to the exact disposable
  container. No new privilege or hosted configuration was introduced.

This local cron observation does NOT establish the cause of the historical
hosted DECLARE failure. The two contexts and conclusions remain separate.

Hosted migrations remain43 (last20261012104331); canonical44 is still pending.
M45/M46 are local candidates only. No new hosted dry-run or full protected
fingerprint was run after the diagnosis. A read-only probe is not a fresh
full-table databehoud measurement. No new hosted fixtures were created and no
historical fixtures or the incomplete step113 were cleaned up.

The retained1376 files pass byte-preservation. Pre-final Pages inspection:
152 protected assets identical,19 older private paths404. Final publication
and all added private paths are checked separately below.

## Remaining Release Boundary

Do not give the owner a phone test against this backend yet. The smallest
remaining decision is whether the irrecoverable old attribution cause may
remain explicitly UNKNOWN while a newly admitted, fully evidenced endchain
is assessed on its own results. Existing conditional permission does not
silently waive that cause requirement. Alternatively keep NO-GO and await
independent evidence that actually explains the historical stop.

Before any release12 hosting: complete6E-11, its required physical review and
the concrete selected-slice release decision. No bulk activation12-21.
Medical/nutrition/language/privacy/legal reviews remain open where applicable.

External AI calls/cost:0 / EUR0.00. Real-member AI enabled:NO.
Production touched:NO. JARVIS, APPFMZ and the separate website untouched.
