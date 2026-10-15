# Numeric-only size diagnosis, separate from the spent hosted attempt

Owner authorization: the 15 October autonomous workday request, section 8. Run `91ba398d-8888-4026-9f0b-3aafd988e5b3`. This is NOT a new 6E-11 mutation run and does not reopen `debe3298-9772-40b1-a9f4-8e3d99c8fd20`.

- One collector, one attempt, no retries; maximum 128 protocol commands, 600 seconds total, ordinary stop at 540 seconds. Existing 5-second connection/query and 1-second lock limits remain. Expected normal path: 14 SQL commands including BEGIN/ROLLBACK; hard stop for own measured query time above 2.5 seconds, temp blocks, missing statistics, unhealthy project or incomplete result.
- A fresh explicit repeatable-read read-only transaction, immediate role/database/TLS/project-instance verification; same verification before rollback. No session-wide read-only state.
- Exact frozen historical filter plan SHA256 `b94f4eea413204787b134198bcaae488bf6c98082687e44bf466f735920ef85a`. No new exclusions. Changed inventory stops the measurement. Fixed predicates are applied before COUNT; only table index and numeric cardinality leave the database. No row values or row hashes are computed or transported.
- Exact query identifier from EXPLAIN, text-free pg_stat_statements before/after, own load separate from background load. No query-text statistics. Counts preserve duplicate rows and SQL NULL filter semantics.
- Numerical output supports an estimate of hash transport size and page-command costs. It is not a protected-data equality proof and does not itself approve larger capacities.
- Real disposable PG17 tests and source-bound clean CI required before any hosted execution. No Auth/fixture/cleanup/application writes, migration or CLI push.
- Existing official Connect endpoint, session5432, `jit=true`, official CA, verify-full. Existing owner-only JIT lease <=300 seconds, exact revocation/disable/readback afterward. No secret export/reset. All historical receipts stay untouched.

Current official checks: [temporary access](https://supabase.com/docs/guides/platform/temporary-access), [session pooling](https://supabase.com/docs/guides/database/connecting-to-postgres), [Auth sessions](https://supabase.com/docs/guides/auth/sessions). The current changelog announces [HTTP TLS cipher deprecation](https://supabase.com/changelog/cbc-tls-ciphers-deprecated); this is not a reason to weaken TLS. The [PG17.11 minor-upgrade advisory](https://supabase.com/changelog/postgres-15-19-17-11-breaking-changes) does not authorize an upgrade/reindex/re-encryption in this task. The pinned isolated CI image remains recorded separately from actual hosted version. Current docs' JIT request example differs from the already-proven Management API payload; retain the tested adapter, do not change fields speculatively.

## Local composition correction

CI `38734722189` rebuilt 46/46 and passed 209 existing browser checks. The new composed browser stopped at the intake checkbox selector after 96 checks: translated caption shadowed the technical checkbox name. Fixed in `panels.js`; a three-language regression now asserts exact field names. This failed run is retained as NO-GO, not promoted retroactively. No hosted action occurred.

The optional integrated historical-workout lifecycle is a separate local capability. It does not expand the selected minimal registration12 hosted slice. The minimum slice still accepts only register/revoke and has no lifecycle/proposal/application activation.
