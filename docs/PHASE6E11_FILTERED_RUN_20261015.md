# Filtered Endchain: Separately Authorized Attempt

Owner instruction cead148d-244b-4676-b6a3-907098ac55df. Starting main:
c8ce051ed6774fdabbe697e705db8a2371b81da9. Preparation only until fresh integral CI.
New run: debe3298-9772-40b1-a9f4-8e3d99c8fd20, purpose
6e11_filtered_endchain_20261015. Exactly one attempt; maximum2226 SQL,
600s total/540s ordinary,5s connect/query,1s lock,one collector,no automatic retry.
The two earlier used runs remain NO-GO; original receipts and UNKNOWN historical
utility cause are not rewritten. Fresh-checkout consumed-run checks remain active.

## Capacity And Equivalence

65536 is the unchanged maximum number of transported row hashes in one cycle,
not a per-table or unique-hash allowance. Duplicates each consume a row. Previously
excluded rows unnecessarily consumed this transport capacity. The corrected WHERE
uses exactly the previous predicates before hashing, so only protected rows are
transported. No additional exclusions or larger transport allowance are introduced.

Before opening the hash cursor, a numeric SELECT counts a UNION ALL of constant1
rows with exactly those predicates and LIMIT65537. It returns one scalar, no row
contents or hashes.65537 means only 'at least65537': stop before hash transport,
without any dependent mutation. This sentinel is not a larger hash-row budget.
It is bounded, not assumed free: its own duration/temp/WAL/statistic attribution
are measured in the same utility before/after chain and charged to the register.
Existing query and own-load limits apply unchanged.

The count and cursor use one verified repeatable-read/read-only snapshot. Fetches
request min(page8192,remaining count,remaining65536). There is no extra hash FETCH
after capacity is reached. The same-snapshot numeric count proves completeness;
short or extra frames stop. NULL predicates remain excluded; NULL column values
remain hashed; duplicates and legacy PG17 JSONB canonicalization are preserved.
Query/filter/capacity-query/source hashes are saved before count/cursor execution.

One count+IO pair replaces the old empty-terminal FETCH+IO pair: capacity remains
31 commands per full cycle, normal2196/worst2207 pending fresh CI verification.
The maximum remains2226. No command is outside accounting; the count also fits
the original per-phase limits. Real hosted size remains unproven until execution.

Local tests include empty/exact/partial pages,65535/65536/65537, truncation,
interruption and rollback. Disposable PG17 independently compares legacy/filter
multisets including duplicate NULL rows, checks numeric plans for sort/spill and
exercises actual cursor pagination. These synthetic tests do not prove hosted size.

## Minimal Pending Migration

M44 remains unapplied last observed hosted43. Candidate changes only the exact
exceptional run UUID and adds that UUID to retained-receipt protection; both old
UUIDs retain protection without exceptional allowance. Source SHA256:
2973c826dd2c177cdade43422013204bbbb2b354ef7bba67cd7b35af6ef823fd.
No old migration history or controller row is repaired or reset.

Official changelog reviewed15 October: October12 HTTP TLS-cipher deprecation
does not authorize a TLS downgrade; October14 .NET telemetry is irrelevant to
this pinned Python/JS stack. Official temporary-access rules remain SSL enforcement,
owner-role mapping, expiry, shared-session5432 with jit=true and CA/verify-full.
No secret reset, new privilege or hosted attempt has occurred during preparation.

Sources: https://supabase.com/changelog.md,
https://supabase.com/docs/guides/platform/temporary-access,
https://www.postgresql.org/docs/17/sql-fetch.html.

## Release12 Boundary

Continue independent local integration. Registration12 still requires complete11,
physical review and a concrete selected-release decision.970 measured local SQL
and the old4135 proposal are not hosted authorizations. No bulk12-21 activation,
ownerfreeze or real-member AI. All1376 protected files and older dirty files stay.

CI38721412989 at36c000737170e0ac0a6ff6b895a4cd04b582d561 is retained NO-GO.
Clean44,36 migration checks,175 Python/131 JS and18 local Auth checks passed.
The new disposable boundary test then failed before execution because psycopg
interpreted the modulo percent sign in parameterized SQL as a placeholder.
Use mod(g,2) in that synthetic generator; no hosted access or attempt was used.
Verified artifact SHA25609e245ae1ccd7e268388796fdf1ceb4d34d3a1b09666431eb3531571e954a7d9.

CI38722021646 atc12d92e45a113faaa1d32ca635ae2fda77b916af passed the complete
chain,36 PG17 filter/capacity assertions and all three failure paths. Capacity
remains2196/worst2207. Its1416-file archive exceeds the old1410 collector count,
not the byte limits:43318393 uncompressed,largest1339728,no unsafe/duplicate paths.
Collector allowance becomes1420 files;30MB compressed/48MB total/2MB per file,
hash/path checks and all hosted limits remain unchanged. Fresh joint CI includes
this postprocessing correction. The original partial archive is retained.
