# 6E-11 recovery run, 18 October 2026

Status: **HOSTED NO-GO / OWNER PHONE TEST CLOSED**.

Scope: Yourizorge/fitmetzorge-staging/main and mokxyyullfhkfalopbzd only.
The owner approved a single run with at most 2349 SQL commands. That attempt
has now been consumed. No retry, new owner window, freeze or 6E-12 server
integration has been performed. 6E-21 remains unaccepted.

## Budget and admission

The complete executable register, including CLI uncertainty and every required
cleanup prefix, fits: **2338 normal / 2349 worst permitted path**. The phase
capacities are:

| Phase | Commands |
| --- | ---: |
| Preflight | 4 |
| Migration boundary | 92 |
| Baseline | 61 |
| Fixtures | 33 |
| Guard | 13 |
| Auth | 318 |
| Controller | 286 |
| Route A | 191 |
| Route B | 286 |
| Restore | 54 |
| Scoped measurements | 136 |
| IO | 97 |
| Cleanup | 633 |
| Final checks | 133 |
| Closure | 1 |

These are reserved maxima, not observed commands. Each CLI operation reserves
64 potentially unobservable commands plus 8 direct observer commands. No work
is moved outside the SQL counter. Management-API requests are recorded separately.

Full source-bound CI [39108116233](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/39108116233)
passed at `306a7559fd25ac4de770ea63059616e2f34ad1dc`, payload
`ecedcf651ab445e7cab2e3a5034671e0149432a48285cbfc4590f3ae2b8acaa7`.
The archive SHA256 is
`c385dc5f0970e4464ba72f908e2c2477be0461da922e5feb7a03f4c15777e76b`.
All 1926 archive files and 237 admission-source hashes were verified locally
before the hosted attempt.

That CI proves a clean 45-migration disposable build, both pending and
already-present quota entry states, real local GoTrue/controller/workflow
integration, cleanup, IO and three fault paths. Evidence includes 194 Python
tests, 132 Node tests, 42 quota database checks, 18 Auth contracts, 71 workflow
pairs and 123 deletes. Test groups overlap with supporting suites and must not
be added into a fictitious unique grand total. This is CI, not hosted evidence.

CLI: 2.117.0. PostgreSQL image: ghcr.io/supabase/postgres:17.6.1.167,
digest `sha256:6942962433a569e87f228b4d4ab7e11db5deca64e43babb3a038443ad6c4f1bb`.
Local GoTrue: 2.197.0. No query/connect deadline was increased.

## Actual hosted result

Run: `4b0bb35f-02b5-4a9d-92d7-c29995691460`.
Exact admitted source: `306a7559fd25ac4de770ea63059616e2f34ad1dc`.
Management window: 18 October 2026, 09:41:38-09:42:08 Europe/Amsterdam (CEST).
**21 SQL commands**, consisting of 4 read-only preflight and 17 baseline
protocol commands, including confirmed ROLLBACK. The registered worker lasted
7765 ms; the command meter records rollback at 8782 ms from its start.

The project-bound native session used owner JIT, session pooling, jit=true,
official CA and verify-full. Preflight returned the expected 44 migration
identities; only the canonical new quota migration was pending. The protected
capacity sentinel returned **100844 rows**, within the 106496-row limit.

The stop is `utility_attribution / stream_utility_attribution` after global
SQL command **20** (stream command 16), following the third FETCH at global
command 19. SQL command 21 confirmed ROLLBACK. The broader wrapper records
registered_chain/registered_install_failure; the retained nested receipt gives
the exact phase and ValueError. No migration, fixture, guard, observer, Auth
token issuance or workflow mutation had started.

The same FETCH source hash appeared in two earlier isolated measurements with
query family `-6151475249528387694`. During the third FETCH, that family again
increased by one call, but family `-2832392023678874621` also increased by one.
The admitted meter required exactly one non-reader changed family on every
page, so it stopped. The origin/actor of the second family is **UNKNOWN**;
it is not proven to be the exporter or harmless owner activity. No query text
was fetched to identify it.

| Numeric delta in the stop window | Calls | Execution ms | Temp read/write blocks | WAL bytes |
| --- | ---: | ---: | --- | ---: |
| Previously observed FETCH family | 1 | 425.537 | 0 / 0 | 0 |
| Numeric reader | 1 | 45.090 | 0 / 0 | 0 |
| Other, unattributed family | 1 | 28.935 | 0 / 0 | 0 |

Database-wide temp_bytes delta was 0; IO-wait and long-active counts were 0.
All four preceding completed utility profiles also recorded zero own temp
writes and zero WAL. This does not prove every unexecuted query or future
window has zero IO. The closing reader witness was not reached.

Two pages (16384 hashes) were validated. A third page returned 8192 hashes but
was stopped before acceptance: total transported 24576, accepted 16384.
The initial protected fingerprint is incomplete. There is **no full before/after
data-preservation PASS**, and no inference of drift from the incomplete stream.
Read-only execution plus rollback proves this attempt did not perform member
or application DML; it does not certify unrelated concurrent activity.

## Closure and migration state

JIT was explicitly revoked and disabled. `closed.json` confirms **0 mappings**,
SSL enforcement still on and no closure request failures. The run never installed
guards/observers or created fixtures/sessions; historical fixtures and evidence
remain untouched. No fixture cleanup was required or attempted for this run.
The final runtime meter is complete; the workflow/evidence chain is not.

Hosted remains **44**, local canonical migrations **45**. Quota candidate
`20261018070231_phase6e11_recovery_run_quota.sql` was **not applied**.
Raw SHA256: `d0f7b100480651da44fea23324a34445ab8a0d04f44e35ce5ed1c1a1f65d4745`.
M44 raw SHA256 remains
`b21650fa40e2143fb11faff8aeb486ce07bdbead15c7e33b9695b2845e6e4d3e`.
The private app candidates45/46 remain excluded. The hosted dry-run phase was
not reached, so no new empty hosted dry-run is claimed. CI dry-runs were empty.

Immutable selected receipts:

- `_offline/phase6e11/endchain_v1/receipts/reserved-ci-39108116233`:
  52 files, manifest SHA256
  `e2b016b5acead0ec60decdd44df4aa514625f2b53446225bbcdf5cf60f860c8a`.
- `_offline/phase6e11/endchain_v1/receipts/reserved-4b0bb35f-02b5-4a9d-92d7-c29995691460`:
  67 files, manifest SHA256
  `3603962da41a27890199bcb29ffa5115dae486ed7b0145d49dddc1d44b4888cd`.

The originals, 112 historical pairs and incomplete historical step113 are not
rewritten or promoted to PASS.

## Independent local correction

The candidate meter now retains an isolated source-hash/query-family binding
within one stream. Later observations of the same source require exactly one
call of that family. Other numeric families are reported separately with actor
UNKNOWN. A first ambiguous observation, changed/missing/duplicate own count,
duplicate metadata key, counter reset/replacement, spill, excessive load or
unhealthy project still blocks. No extra SQL, excluded rows or larger limit is
introduced. Complete protected comparison remains mandatory.

This is not perfect session-level attribution: an overlapping execution of
the same query family still blocks. A first observation under concurrent load
can still block. No binding is reused across streams or from historical logs.
The correction does not retroactively admit the stopped run. Local tests:212
Python PASS. A new disposable PG17 interleaving check and complete CI validation
are prepared; their outcome will be recorded separately. No new hosted attempt
is authorized by that validation. The final local suite contains 213 passing
Python tests; unchanged Node regressions remain 132/132.

Final local safety review also requires `track_utility=on` and `track=top/all`
in both existing numeric snapshots. Disabled or missing utility tracking must
not allow another query's counter to stand in for an untracked FETCH. This adds
no command. It changes the numeric reader's source hash and therefore requires
fresh full CI for the final source, not reuse of a previous source's PASS.
[PostgreSQL17 documents](https://www.postgresql.org/docs/17/pgstatstatements.html)
that these counters aggregate by database, database user, query family and
top-level status; they are not per-session audit identities. The collector
retains those limits and never treats a numeric family as an Auth identity.

Intermediate complete CI39109175578 at
`6956444bf7d27882a82a026e31fc0b1e0738d942` passed the real PG17 interleaving
check: one source-bound FETCH remains separate from an independently identified
second connection's query; an ambiguous first observation and double FETCH are
denied. The full 45-migration/Auth/workflow/cleanup/fault composition also passed.
Its 1963-file archive hash is
`7f79fb2189088b2d055e08e0655c44fd8c56bc4f57b8481bf855eb6048eb849b`.
This does not cover the later explicit tracking-configuration gate; final-source
CI39109482869 is separate. Neither CI permits reuse of the consumed hosted run.

### Final corrected source

[CI39109482869](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/39109482869)
is **CLEAN_CI_PASS** at
`ab9d4c0e12e78cfd4cda072b569691364e6851c3`.
Payload SHA256:
`10c7199e15a2f7fc097150931f57193e6f8c8ed4272d389f984d7e334a2dbf2f`.
Archive SHA256:
`d41e9a12af9cf4f2e911ef869e5d2a62802e94eec9d6d12bf91015953c865c8b`.
1963 artifact-file hashes verified; 240 exact source files bound.

It passes clean45/45, 205 CI Python tests (the local suite additionally includes
8 archive-export checks), 132 Node tests, 42 quota checks, 18 real local Auth
contracts, both full workflow entry states, three real fault paths and six
PG17 interleaving checks. No mock replaces the native database or GoTrue.
The complete register is still 2338/2349 with the unchanged phase capacities.
The final stack pulled the official public.ecr.aws/supabase/postgres:17.6.1.167
mirror, with the same repository digest and image ID as the earlier GHCR image.

53 selected immutable receipts are committed under
`_offline/phase6e11/endchain_v1/receipts/reserved-ci-39109482869`.
Manifest SHA256:
`cbc78199ff654b78355fbd825cdea981519de111f20d7f97215db42ccad13896`.
All original archives remain local. **No hosted call followed this PASS.**

## Preservation and next boundary

Only offline code/tests, evidence, quota candidate, CI label and documentation
are committed. No live runtime, frozen AI contract, owner/member account,
production, APPFMZ, website or JARVIS file is changed by this work. Existing
older dirty files are deliberately retained. The strict historical preservation
receipt flags .gitattributes because exactly two authorized LF rules were
appended; a separate scoped check confirms the original prefix and all other
protected files. This is not described as universal byte-identity.

The post-run strict local check retained its NO_GO at
`supabase/.temp/phase6e-server-ci-d96cbfd340e64ea2b493ee98f33b8f32/workday-preservation-02f606600d744eb1883a1ab7a35d2f8d.json`:
1372/1376 files byte-identical, three previously authorized documentation
prefixes preserved, and only .gitattributes outside that old check's allowlist.
A separate exact-prefix comparison confirms only the two authorized LF rules.
M44 remains byte-identical. All 119 archived CI/hosted receipt files also match
both their original local files and their immutable manifest hashes.

The smallest next boundary is **one separately authorized, new run**, after the
now-completed local query-binding correction, with fresh source admission and a fresh
run-specific quota binding. Neither the consumed run nor its migration exception
may be silently reused. No budget increase is currently indicated; 2349 still
covers the register. Owner phone review remains closed until a complete hosted
Auth/Route A/B/audit/delete/cleanup and preservation PASS.

## Commits and publication scope

- b04c939: one-run quota and complete reserved register.
- a8a9f9e: exact migration boundary and retained comparison evidence.
- 306a755: five-second DDL and complete pre-hosted CI evidence.
- 6956444: preserved consumed hosted attempt and utility-binding correction.
- ab9d4c0: mandatory utility-tracking metadata and negative tests.

Only offline sources, tests, immutable receipts and documentation are published
to Git, plus the already described unexecuted quota candidate and CI label.
GitHub Pages excludes all `_offline`, `supabase` and `.github` roots. The final
publication check verifies the artifact for the actual remote main and 152
protected runtime assets, plus bounded HTTP probes. That separate publication
receipt records its exact head rather than inventing a self-referential report
commit hash. A clean worktree is not claimed: older unrelated changes remain.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.
