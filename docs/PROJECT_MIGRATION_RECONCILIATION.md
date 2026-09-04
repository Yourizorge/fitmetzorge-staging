# Project-Wide Migration History Reconciliation Gate

Date: 2026-09-04. Target: staging `mokxyyullfhkfalopbzd` only.
Result: RESOLVED / VERIFIED. Package 6D functionality was not started.

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
`docs/PROJECT_MIGRATION_RECONCILIATION_MANIFEST.json` records 25 local migrations and
25 live history rows with:

- zero local-only versions;
- zero remote-only versions;
- zero name mismatches;
- zero duplicate versions;
- the four history-only repair versions;
- the 19 resolved timestamp mappings;
- the reconstructed baseline scope and live object presence.

Official Supabase CLI checks:

- `supabase migration list --project-ref mokxyyullfhkfalopbzd`: synchronized 25/25.
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

- The only deletion candidates found after the OneDrive prompt were:
  `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\local-rebuild-tc26YR`
  and
  `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\local-rebuild-YIC31o`.
- They contain only temporary PostgreSQL 18 rebuild-cluster files, including
  `PG_VERSION`, `base`, `global`/WAL/config data, and no `.git`, canonical migrations,
  docs, assets, functions or source paths.
- No `postmaster.pid` was present. They are ignored by `.gitignore`. Because OneDrive
  restored them after the owner chose to keep items, the verifier was changed to use
  the system temp directory instead of a repo/OneDrive temp path.

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
