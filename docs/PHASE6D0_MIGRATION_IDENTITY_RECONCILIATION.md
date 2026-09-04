# Package 6D-0 Migration Identity Reconciliation

Date: 2026-09-04. Staging only: mokxyyullfhkfalopbzd.
Repository: Yourizorge/fitmetzorge-staging, main.
Starting HEAD: 65e0ae11d45b7cf3dbddb357e1cbaff493bdf97b.

Status: 6D-0 IDENTITY PASS. Broader legacy migration-history synchronization BLOCKED.
No Package 6D implementation, database change, history repair, SQL reapplication,
frontend/Edge deployment, external AI call or production access occurred.

## Cause And Exact Identity

The prior execution used Supabase apply_migration, which accepts name and SQL rather
than a caller-selected migration version. It recorded execution version 20260904105918.
Git retained the earlier local creation version 20260904093300. The previous receipt
reported both accurately but failed to reconcile the Git filename after deployment.
This was real migration-identity drift, not SQL-content drift or only a report typo.

Live schema_migrations has exactly one record named phase6d0_legacy_authorization_gate,
at version 20260904105918. There is no live 20260904093300 record.
Its statements array contains one complete 17,917-byte SQL string, including the
original comment, BEGIN and COMMIT. Its database-calculated UTF-8 SHA-256 equals both
the reviewed Git blob and the local file:

5B91B22F823A30F86E329B381FE797FD28655D237AD977D6B80D2C99AF5485B3

All eight CREATE OR REPLACE function bodies match pg_proc.prosrc byte-for-byte.
All thirteen involved functions retain SECURITY DEFINER and
search_path=pg_catalog, pg_temp. The invitation table has the expected ten columns,
validated PK/unique/FK/check constraints and indexes. RLS, grants, policies, trigger
bindings and the profile unique-link index pass the unchanged 40-check live verifier.

## Non-Destructive Correction

Canonical version in both Git and staging: **20260904105918**.

Canonical Git path:
supabase/migrations/20260904105918_phase6d0_legacy_authorization_gate.sql

Only the filename changed; no SQL byte changed. There is no second copy under the
old version. The live migration-history row and its original SQL evidence remain
untouched. No migration repair is needed for this identity because Git now adopts
the existing applied identity. Marking an applied migration reverted or executing
it again would be inappropriate.

A narrowly scoped .gitattributes rule keeps this reviewed SQL LF-encoded even in a
Windows core.autocrlf=true checkout. Verifier and rollback-test filenames retain their
original audit timestamp; neither is a migration or a pending deployment artifact.

The official CLI now reports:

Local 20260904105918 | Remote 20260904105918 | 2026-09-04 10:59:18

Thus the CLI no longer treats 6D-0 as missing locally or pending remotely.
The read-only identity checker independently requires a single canonical filename,
single history record, locked checksum, eight exact function bodies and thirteen
safe function contexts. It rejects old/duplicate/missing IDs and altered bytes.

## Important Broader Deployment Limitation

A general clean-checkout db push is NOT yet proven safe or synchronized for the
whole historical project. This predates 6D-0:

- 19 older migrations have matching names but different Git/live timestamps.
- Three Git artifacts have no same-name live history entry:
  20260813_trainer_signup_bootstrap.sql;
  20260818_phase4_nutrition_schema_slice1.sql;
  20260826143000_phase4_nutrition_slice4fc_off_authoritative_logging.sql.
- Four old files share the local version 20260819.
- The existing Git history is not a complete empty-database baseline.

The official db push --dry-run --skip-vault still fails closed with
LegacyDbPushMissingLocalError for the 19 older remote versions. The corrected
6D-0 version is absent from that error list. No SQL was applied by the dry run.

Do not follow its generic suggestion to mass-mark old versions reverted. That would
discard applied-history evidence and could schedule dangerous legacy SQL again.
Do not use --include-all, reset, reapply the bootstrap, or mark the three unrecorded
artifacts applied merely because some current objects exist.

The new checker defaults to nonzero exit on broader history drift. --package-only
permits the narrow 6D-0 identity result while still explicitly reporting
full_history_synchronized=false and broad_db_push_allowed=false. This is an inspection
gate, not a replacement migration executor or a guarantee against bypassing it.

Full-project migration reproducibility remains a separate legacy-history/baseline
remediation gate: compare each older applied artifact and its evolution, reconcile
identity without reapplying security/data SQL, and prove an approved clean baseline.
No older frozen artifact or history row was silently changed in this task.

## Verification Receipt

- Exact 6D-0 identity checks: 8/8 PASS; exact live function bodies: 8/8 PASS.
- New checker negative/regression tests: 12/12 PASS.
- Unchanged read-only 6D-0 security verifier: 40/40 PASS, overall_pass=true.
- Mocked invite Edge tests: 10/10 PASS; security browser contract: 41/41 PASS.
- Frozen Phase 1: 75 PASS; Member UX: 56 PASS; Package 6C: 117 PASS.
- Official CLI migration list: 6D-0 synchronized.
- Clean indexed checkout with core.autocrlf=true: reviewed migration SHA-256 unchanged;
  Git reports a 100% identical rename. This proves file-byte reproducibility, not a
  complete from-empty database rebuild.
- General CLI deployment dry-run: BLOCKED solely by older history differences.
- Before/after complete compared object metadata SHA-256:
  ca33d0335ac0919cc2b7a3e82b51777ddd1aa464ef85820a49b486b506e10c82.
  Includes involved functions/ACLs, three tables, columns/defaults/column ACLs,
  constraints, indexes, policies, trigger definitions and private schema ACL.
- Existing profiles, workspaces, entitlements and normalized-function fingerprints
  unchanged; private chat aggregate counts unchanged. No member rows read into reports.
- No synthetic accounts, invitation acceptance or workspace mutation was needed.
- Security advisors unchanged: 78 notices (25 RLS/no-policy INFO, 51 authenticated
  definer WARN, one historical search-path WARN, one leaked-password-protection WARN).
  No anonymous-definer warning returned. These residual notices are not claimed fixed;
  see [Supabase security guidance](https://supabase.com/docs/guides/database/postgres/row-level-security).

## Reproduction

With FMZ_PYTHON pointing to the local Python runtime and the existing official CLI
credential available in Windows Credential Manager:

    node supabase/tests/phase6d0-migration-identity-check.cjs --live
    node --test supabase/tests/phase6d0-migration-identity-check.test.cjs
    supabase migration list --project-ref mokxyyullfhkfalopbzd
    supabase db push --dry-run --skip-vault --project-ref mokxyyullfhkfalopbzd

The first command uses only a fixed SELECT through the fixed-staging transport.
No secrets enter arguments, files, test output or reports.

Supabase compares migration timestamps, not filenames' descriptive names or SQL
checksums. See [official migration list/repair documentation](https://supabase.com/docs/reference/cli/supabase-migration-repair)
and [database migration workflow](https://supabase.com/docs/guides/deployment/database-migrations).

Ready for the focused 6D-0 owner security retest: YES.
Ready to approve full-project clean migration reproducibility: NO.
6D-0 owner acceptance is not assumed. Real-member AI remains disabled.
