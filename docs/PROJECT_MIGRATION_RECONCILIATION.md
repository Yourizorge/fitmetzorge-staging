# Project-Wide Migration History Reconciliation Gate

Date: 2026-09-04. Target: staging mokxyyullfhkfalopbzd only.
Result: READ-ONLY INVENTORY COMPLETE / RECONCILIATION BLOCKED.
Runtime/audit checkout: 333954a68a1429634e49bafbcc08720ea688131a, staging main.

## Evidence And Classification

The committed chain contains 24 SQL files; live history contains 21 rows.
There are 19 same-name timestamp differences, three files without a same-name history
row and four files reusing local version 20260819. No local or remote ID was changed.

The [manifest](PROJECT_MIGRATION_RECONCILIATION_MANIFEST.json) records every exact Git
path, byte count, SHA-256, local/remote identity, history checksum, table/function name
candidates, current presence, candidate canonical ID and required action. It also
records before/after history, live table RLS and function identity/definition hashes.
The inventory is metadata-only; no member values, Auth tokens or secrets are included.

Class 1 means recorded SQL identity is proven: 6D-0 matches byte-for-byte; 13 other
single-statement history entries match after CRLF and outer-whitespace normalization
only. No internal SQL tokens are rewritten. This does not prove that a historical
function has never subsequently been replaced. Class 5 means insufficient execution
identity evidence. Class 4 flags the duplicate local version in addition to class 5.
Classes 2/3 are deliberately not inferred merely from current object presence/absence.

| Git ID | Same-name live ID | Migration suffix | Class |
| --- | --- | --- | --- |
| 20260813 | absent | trainer_signup_bootstrap | 5 |
| 20260818 | absent | phase4_nutrition_schema_slice1 | 5 |
| 20260819 | 20260819134024 | phase4_nutrition_slice3_atomic_log_item_replacement | 5 + 4 |
| 20260819 | 20260819163738 | phase4_nutrition_slice4b_alias_search | 5 + 4 |
| 20260819 | 20260819175756 | phase4_nutrition_slice4c_operational_state | 5 + 4 |
| 20260819 | 20260820082018 | phase4_nutrition_slice4d_provider_snapshot_logging | 5 + 4 |
| 20260820134211 | 20260820150513 | phase4_nutrition_slice4d_historical_provider_resolver | 5 |
| 20260821214541 | 20260822172635 | phase4_nutrition_slice4e_ingestion_alias_search | 5 |
| 20260824113551 | 20260824113551 | phase4_nutrition_slice4f_off_catalog_search | 5 |
| 20260826143000 | absent | phase4_nutrition_slice4fc_off_authoritative_logging | 5 |
| 20260827165426 | 20260827152727 | phase4_nutrition_slice4fd_transient_off_parent_context_fix | 1 |
| 20260827 | 20260827125343 | phase4_nutrition_slice4fd_transient_off_barcode | 1 |
| 20260831153000 | 20260831145357 | phase5_progress_foundation | 1 |
| 20260831161000 | 20260831150434 | phase5_progress_unit_preference | 1 |
| 20260831163000 | 20260831153512 | phase5_progress_revision_indexes | 1 |
| 20260901170000 | 20260901161314 | phase5_unit_system_constraint_fix | 1 |
| 20260901193000 | 20260901183914 | phase6a_ai_trust_foundation | 1 |
| 20260901203000 | 20260901184418 | phase6a_ai_consent_event_ordering | 1 |
| 20260901204500 | 20260901190328 | phase6a_pgcrypto_search_path | 1 |
| 20260901211500 | 20260901191328 | phase6a_foreign_key_indexes | 1 |
| 20260901230000 | 20260902045834 | phase6b_provider_privacy_cost_gate | 1 |
| 20260902203000 | 20260903085454 | phase6c_private_ai_chat | 1 |
| 20260903145000 | 20260903125150 | phase6c_request_scoped_safety | 1 |
| 20260904105918 | 20260904105918 | phase6d0_legacy_authorization_gate | 1, exact |

The remote IDs of the 14 class-1 files are canonical identity candidates in the
manifest, not permission to rename an incomplete dependency chain. The other ten
canonical IDs remain unresolved. In particular, the OFF foundation history contains
95 separate statements: concatenated transport bytes do not establish full-file identity.
Seven recorded artifacts lack whole-artifact equivalence proof; three have no matching
history name. Their current function hashes cannot establish historical execution alone.

## Material Baseline Blocker

Git contains no creation baseline for public.profiles, public.coach_workspaces,
public.user_settings or public.entitlements. The first committed bootstrap already
returns public.profiles, so it depends on a pre-existing relation type. Therefore this
chain cannot reconstruct a new empty public schema from Git as currently committed.

The old trainer bootstrap is also historical authorization logic. Replaying it while
repairing history could reintroduce authority intentionally closed by Package 6D-0.
No historical SQL was executed, no uncertain migration was marked applied and no
automatic repair suggestion was accepted. Archive files are not silently promoted into
the canonical migration chain. Missing baseline/evolution evidence needs separate review.

## Official CLI And Reproducibility

- Installed official Supabase CLI: 2.115.0; relevant --help inspected.
- migration list --project-ref mokxyyullfhkfalopbzd: completes, showing the differences
  above. Before/after history snapshots are equal, 21 rows. NOT synchronized.
- db push --dry-run --skip-vault --project-ref mokxyyullfhkfalopbzd: exit 1,
  LegacyDbPushMissingLocalError, 19 remote versions missing locally. No SQL applied;
  Vault synchronization explicitly skipped. The CLI's proposed repair was NOT run.
- Exact artifact hashes are read from committed Git blobs, not a working-tree SQL copy.
- New full checkout, empty-database replay and rebuilt-schema comparison: NOT EXECUTED
  after the explicit uncertain-migration/baseline stop. They are not reported as PASS.
- The manifest's two reads are a metadata before/after comparison, not a full recoverable
  history export. A complete history export is still required before any future repair.
- Renamed files: NONE. History repairs: NONE. SQL replay: NONE. Open transactions and
  inserted test fixtures: NONE. This audit uses SELECT metadata inspection only.

## Frozen Security And Preservation

Package 6D-0 remains Git/live 20260904105918. Migration SHA-256 remains
5B91B22F823A30F86E329B381FE797FD28655D237AD977D6B80D2C99AF5485B3.
Its authorization verifier passes 40/40; all seven current read-only database verifiers
pass 228/228. Phase 1 through 6C frozen static/browser/Edge regression suites PASS;
exact counts are in PUBLIC_AUTH_REGISTRATION_HOTFIX.md. These prove current checked
contracts, not an exhaustive historic migration equivalence proof.

Before/after profiles, workspace and entitlement fingerprints match. Private chat
counts and normalized-function fingerprints match. No schema/member/trainer data
change occurred. The separately authorized Auth hotfix performed one supported
confirmation resend; that action did not repair migration history or confer a role.
No Edge deployment, external AI call, new Package 6D functionality or production access.

## Required Next Action

Recover and review the missing core baseline and exact evolution evidence for the ten
uncertain artifacts. Then establish dependency order and a canonical migration identity
for every file before performing a reviewed history-only reconciliation. Re-run the
official list/dry-run and a new empty local rebuild/schema comparison before reopening
general migration deployment. Broad future migrations are NOT cleared by this audit.

The urgent frontend Auth hotfix is independently deployed and verified; its runtime
commit does not contain migration SQL changes. The final documentation/audit commit
records this blocked gate, not a claim of a clean or repaired migration chain.
