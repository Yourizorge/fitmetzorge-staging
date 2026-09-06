# Project-Wide Migration History Reconciliation Gate

Date: 2026-09-04. Target: staging `mokxyyullfhkfalopbzd` only.
Result: RESOLVED / VERIFIED. Later Package 6D work appended forward-only migrations
without reopening the historical repair.

## Owner Retest Hotfix 2 Addendum - 2026-09-06

Forward-only 20260906092905_phase6d_automatic_inbox.sql is applied to staging only.
Current chain is 29 local / 29 live, including a clean fresh-clone migration list and
db push --dry-run --skip-vault (upToDate=true, empty migrations/seeds/roles). No historical
repair, SQL replay, remote reset or source baseline rewrite was performed in this task.
The worker was enabled only after transactional tests and frontend asset verification;
actual cron processing and complete synthetic cleanup are recorded in
PACKAGE6D_OWNER_RETEST_HOTFIX2_REPORT.md. All 21 checked member-table hashes/counts match
before/after migration and after the committed cron fixture was removed.

Fresh committed checkout: runtime 2e1fd983385ad360632667c954d7f63725555b3c,
supabase/.temp/hf2-fresh-checkout. Windows core.longpaths=true is clone-local; without
it Git emits Filename too long/misleading modified-file status. With it the checkout
is clean and the assembled browser passes 323/323. No canonical SQL was rewritten.

Local PostgreSQL 18.6 rebuild with --keep-temp applied 22 migrations through
20260902045834; seven 6C/6D migrations were explicitly skipped for missing pg_cron.
Docker is unavailable. This is not full 29-migration replay or zero schema-diff proof.
The database was stopped and the generated cluster was retained outside OneDrive at
C:\Users\Fitme\AppData\Local\Temp\fmz-local-rebuild-YsUaP4.
No PostgreSQL filesystem deletion occurred; the full 971-item OneDrive deletion
manifest remains unavailable, so no pending item is certified disposable. Exact known
paths and next verification boundary are in the new report. The historical 25-row
reconciliation manifest below is preserved, not retrospectively treated as 29-row evidence.

## Combined Owner Hotfix Addendum - Historical Hotfix 1

The reviewed additive 20260906080455_phase6d_owner_safety_settings.sql follows the
original 25 and two initial 6D migrations: current list is 28 local / 28 remote.
Post-apply db push --dry-run --skip-vault reports upToDate=true, migrations=[], seeds=[],
roles=[]. No history repair/replay/reset occurred in this hotfix. All 21 allowlisted
member/safety/domain table fingerprints/counts match before/after; rollback Auth/profile
fixtures and new recovery/UI preference rows are zero. See
PACKAGE6D_COMBINED_OWNER_HOTFIX_REPORT.md and its machine-readable evidence.

Fresh source verification uses clone-local core.longpaths=true on Windows. Full local
database replay/diff still needs Docker/pg_cron. No PostgreSQL cleanup was performed.
The original 25-row manifest and historical observations below remain unchanged.

## Root Cause

The repository migration chain and the live staging migration history had drifted:

- 19 Git migration files used older local timestamps while staging had the same
  logical migration names under canonical live timestamps.
- Three Git migrations had no same-name live-history row:
  `20260813_trainer_signup_bootstrap.sql`,
  `20260818_phase4_nutrition_schema_slice1.sql`, and
  `20260826143000_phase4_nutrition_slice4fc_off_authoritative_logging.sql`.
- Four older Phase 4 files reused local version `20260819`.
- The canonical Git chain was missing the Phase 1-3/source baseline needed for a
  clean empty-database rebuild. Later migrations assumed tables and functions such as
  `profiles`, `coach_workspaces`, `user_settings`, `entitlements`, Recovery and
  Training objects already existed.

Git history and the available archived artifacts did not contain a complete,
byte-exact historical Phase 1-3 migration series. Current live object presence alone
was not treated as proof of historical execution identity.

## Resolution

No historical SQL was replayed on staging. No remote reset, destructive reconstruction,
or member-data rewrite was performed.

The 19 timestamp drifts were resolved by renaming the Git files to the canonical live
history versions:

| Previous Git version | Canonical live version | Migration |
| --- | --- | --- |
| `20260819` | `20260819134024` | `phase4_nutrition_slice3_atomic_log_item_replacement` |
| `20260819` | `20260819163738` | `phase4_nutrition_slice4b_alias_search` |
| `20260819` | `20260819175756` | `phase4_nutrition_slice4c_operational_state` |
| `20260819` | `20260820082018` | `phase4_nutrition_slice4d_provider_snapshot_logging` |
| `20260820134211` | `20260820150513` | `phase4_nutrition_slice4d_historical_provider_resolver` |
| `20260821214541` | `20260822172635` | `phase4_nutrition_slice4e_ingestion_alias_search` |
| `20260827` | `20260827125343` | `phase4_nutrition_slice4fd_transient_off_barcode` |
| `20260827165426` | `20260827152727` | `phase4_nutrition_slice4fd_transient_off_parent_context_fix` |
| `20260831153000` | `20260831145357` | `phase5_progress_foundation` |
| `20260831161000` | `20260831150434` | `phase5_progress_unit_preference` |
| `20260831163000` | `20260831153512` | `phase5_progress_revision_indexes` |
| `20260901170000` | `20260901161314` | `phase5_unit_system_constraint_fix` |
| `20260901193000` | `20260901183914` | `phase6a_ai_trust_foundation` |
| `20260901203000` | `20260901184418` | `phase6a_ai_consent_event_ordering` |
| `20260901204500` | `20260901190328` | `phase6a_pgcrypto_search_path` |
| `20260901211500` | `20260901191328` | `phase6a_foreign_key_indexes` |
| `20260901230000` | `20260902045834` | `phase6b_provider_privacy_cost_gate` |
| `20260902203000` | `20260903085454` | `phase6c_private_ai_chat` |
| `20260903145000` | `20260903125150` | `phase6c_request_scoped_safety` |

The duplicate old `20260819` version conflict is gone because all four files now have
their live canonical versions.

A forward-only source baseline was added:
`supabase/migrations/20260812000000_legacy_phase1_3_source_baseline.sql`.
It reconstructs the Phase 1-3/source schema contract from live read-only metadata,
frozen verifier contracts and existing function definitions. It is intentionally a
fresh-rebuild baseline, not a claim that the original historical SQL was recovered.
It contains no data inserts, no backfill, no role/link grants and no owner/member data
mutation.

After the file chain was corrected, four versions were marked as applied in staging
history only:

- `20260812000000`
- `20260813`
- `20260818`
- `20260826143000`

This repaired only `supabase_migrations.schema_migrations` metadata. The repaired
versions describe migrations already represented in the live staging schema; they were
not replayed.

## Evidence

The refreshed manifest at
`docs/PROJECT_MIGRATION_RECONCILIATION_MANIFEST.json` records the original repaired
25 local migrations and 25 live history rows with:

- zero local-only versions;
- zero remote-only versions;
- zero name mismatches;
- zero duplicate versions;
- the four history-only repair versions;
- the 19 resolved timestamp mappings;
- the reconstructed baseline scope and live object presence.

Official Supabase CLI checks:

- `supabase migration list --project-ref mokxyyullfhkfalopbzd`: synchronized 25/25
  at the reconciliation close, and 27/27 after the later Package 6D migrations
  `20260904230850` and `20260904235253`.
- `supabase db push --dry-run --skip-vault --project-ref mokxyyullfhkfalopbzd`:
  `Remote database is up to date`, with no migrations, seeds or roles pending.
- `supabase db diff --linked --schema public,ai_private,legacy_auth_private`:
  not executable in this local environment because Docker Desktop is unavailable
  (`LegacyImagePrepullError`). No staging change was attempted by this failed diff.

Live migration history from the Supabase management API also returns all 25 expected
versions and names, including `20260812000000_legacy_phase1_3_source_baseline`,
the three previously missing Git migrations and the existing `20260904105918`
6D-0 gate.

The live 6D-0 migration identity checker now returns `package_identity_pass=true`,
`full_history_synchronized=true`, `broad_db_push_allowed=true`, and no local-only,
remote-only or duplicate local versions.

Local rebuild verification:

- `node supabase/tests/project-migration-local-rebuild.cjs`: PASS through
  `20260902045834_phase6b_provider_privacy_cost_gate.sql` on local PostgreSQL 18.
- The rebuild produced the expected Phase 1-6B public objects and RLS flags,
  including `profiles`, `coach_workspaces`, `user_settings`, `entitlements`,
  `recovery_logs`, Training, Nutrition, Progress and AI trust objects.
- Full local replay of the final three migrations is blocked only by the local machine
  missing the `pg_cron` extension. The migration chain itself is synchronized and
  staging dry-run clean.

Data preservation:

- Before repair, all 39 live public tables were counted and fingerprinted.
- After repair, all 39 live public table counts matched the pre-repair counts exactly.
- The only intended live write was migration-history metadata. No application table,
  Auth role/link, Edge Function, frontend runtime, AI provider state, catalog or member
  row was changed by this reconciliation.

OneDrive/temp safety:

- The only local rebuild delete candidates from the original reconciliation were:
  `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\local-rebuild-tc26YR`
  and
  `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\local-rebuild-YIC31o`.
- On 2026-09-06 they were rechecked as directory reparse points at those exact paths,
  with no resolved target exposed by PowerShell. The same directory also held old
  proof artifacts such as `auth-hotfix-*.png`, `live_public_schema_20260904.sql`,
  `public-auth-live-result.json` and `registration-confirmation-resend-20260904.json`.
- A full recursive file scan under the current workrepo for `pg_control`,
  `config_exec_params` and `postmaster.pid` returned zero results. `git ls-files
  supabase/.temp` also returned zero tracked files.
- No files were deleted. Future local rebuilds should continue to use the system temp
  directory outside OneDrive unless the exact target path is proven to be only a
  rebuildable local Supabase/PostgreSQL cluster.

## Outcome

The broad migration deployment gate is reopened for staging: the live history now
matches the Git chain, `db push --dry-run` is clean, and the repository contains a
rebuildable source baseline for the missing Phase 1-3/source objects.

The baseline is deliberately conservative. If future work needs legal/audit-grade
byte identity of the original Phase 1-3 SQL, that exact historical source still was
not found and must be treated as unavailable unless the owner supplies an external
archive. This is not a blocker for forward-only staging development under the repaired
chain.

Public Auth hotfix status remains successful. The owner has received the confirmation
email for the new test account, so no new resend, Brevo investigation, manual account
confirmation, trainer role or trainer linkage was performed.

Production remains untouched and forbidden.

## Package 6D Addendum - 2026-09-06

After this reconciliation closed, Package 6D added two ordinary forward-only staging
migrations:

- `20260904230850_phase6d_read_only_ai_analyses.sql`
- `20260904235253_phase6d_analysis_lifecycle_safe_code_fix.sql`

Both are present in Git and live staging history. The official Supabase CLI result is
now 27 synchronized local/remote migration rows, and `db push --dry-run --skip-vault`
returns `Remote database is up to date` with no pending migrations, seeds or roles.
This addendum did not alter the historical reconstruction strategy: no blind replay,
history reset, remote reset, production access or existing member-data mutation was
performed.
