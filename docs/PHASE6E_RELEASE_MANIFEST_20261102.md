# Phase6E Migration Identity and Preservation Manifest

2026-11-02. Role A. SOURCE INVENTORY COMPLETE; NOT HOSTED ADMISSION.

Sole repository: `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy`.
Coordinator-confirmed main/remote: `9715ac8600bad89ff813ad399e745360028ce48a`. This role did not query remote or change Git history.
Machine-readable companion: [PHASE6E_RELEASE_MANIFEST_20261102.json](PHASE6E_RELEASE_MANIFEST_20261102.json).

## Findings

- Canonical migrations:45. Last-proven hosted history:44, not freshly measured.
- Private app candidates add cumulative counts46 and47. Older code calls themM45/M46; use exact versions and hashes below.
- All44 preserved source hashes match history_pin.json. All44 retained hosted identities and stored SQL hashes match its staging history. Whole-file and stored-history SQL hashes are separate representations.
- All47 migration bytes match retained app CI40354972820 candidate hashes. All45 canonical files match Git at the confirmed commit after CRLF-to-LF comparison;36 match raw bytes and9 differ only by line endings. No file was normalized.
- Preservation:1376 baseline entries,1372 exact matches,4 permitted changes validated against the original Git bytes and existing preservation rules.158 frozen source entries across12-20 match their receipts.
- Dirty snapshot: 364 entries at 2026-11-02T14:01:03.524Z;6 tracked modifications and358 untracked files. JSON records every path/status/size/mtime/hash, never file contents. Ignored files are not part of Git status. Concurrent work may add later differences.

## Release and Rollback Register

| Count | Exact version / raw SHA256 | Scope and dependency | Rollback boundary |
|---|---|---|---|
|45|20261018070231 / `64498fa910966497e92705dcf66b76f40c40f01c006aed98c191ce109dd88635`|Canonical6E-11 quota and retained run receipts; depends on43/44 controller objects. New6f8c exception2349, historical1c3b exception2237, others128.|BEGIN/COMMIT makes uncommitted failure transactional. No proven post-commit down migration. Retain closed receipts and history; coordinator closes run/access using reserved cleanup.|
|46|20261014105919 / `51953e164c2431299bf8825d08e30fe776434a99c8766a9e1faeb3c956d05b0d`|Private server foundation: subjects/workspaces/revisions/requests/audit, restricted role, RLS and actor/request binding. Uses auth.users; applied after canonical45 in local_app CI.|Disable entry; retain history. Disposable-stack removal is test cleanup, not hosted rollback.47 depends on46.|
|47|20261014160019 / `fc0edf31bff828256d3719713bc269646c908673f121ccbce0b26099d7c8b650`|Private outbox, append-only event history, RLS and replacement of46 observe(). Requires46.|Disable processing; retain history. Any reviewed reversal must address outbox objects AND shared observe() restoration. No reviewed hosted inverse supplied.|

Exact candidate paths and dependency details are in JSON release_candidates. Canonical45 is `supabase/migrations/20261018070231_phase6e11_recovery_run_quota.sql`; private46/47 remain under `_offline/phase6e_server_v1/supabase/migrations/`.

46/47 are cumulative counts, not timestamp order: their20261014 versions precede quota20261018. The existing disposable local_app profile builds canonical1-45 first, then46, then47, with local-only --include-all. This is not a hosted command recommendation. Never renumber candidates, rewrite historical migration files or repair history to mask the ordering.

45 alone does not close6E-11. Relative to retained hosted44, only45 is canonically pending.46 is shared private persistence for accepted12-20;47 adds in-app outbox. Package-specific functional mapping belongs to Role D. Offline freeze is not hosted release acceptance.21 remains unaccepted/default-off/excluded.

Post-commit reversal and full cleanup are NOT newly proven here. No deletion, down migration, stack cleanup or forward correction was performed. Main must bind the final selected migration set, rollback boundaries and cleanup reserve to complete CI/WAL/reviewer gates before any hosted execution.

## Canonical Raw Hashes

Exact on-disk SHA256, including line endings. JSON also records Git blob and LF-comparison hashes, plus separate retained hosted/disposable stored-SQL hashes for1-44.

| Ordinal | File under supabase/migrations | SHA256 |
|---|---|---|
| 1 | `20260812000000_legacy_phase1_3_source_baseline.sql` | `ae06ca53771d90baa12c12af8d8b43e3bd0464d926d8795197859c4a8b8ae26b` |
| 2 | `20260813_trainer_signup_bootstrap.sql` | `055567b0a3e66671d45c75600f5ca3bf9191d08ccf1b95dbd6904bb106da4c52` |
| 3 | `20260818_phase4_nutrition_schema_slice1.sql` | `da73c53023c8c513707d52381dccfcde3dca94875f631ded802888c0c23e9ddd` |
| 4 | `20260819134024_phase4_nutrition_slice3_atomic_log_item_replacement.sql` | `fddc1760a71da056010bcb3e1909e52cac6c71a07c21f488dd3462159b572d1d` |
| 5 | `20260819163738_phase4_nutrition_slice4b_alias_search.sql` | `7b7b00673d8f58514ffe46695577f27f1de726bcadc4d0eed430a22ed9b88dbf` |
| 6 | `20260819175756_phase4_nutrition_slice4c_operational_state.sql` | `1c68de71a3c4ff3b4859eb08eb20053637dc4030d836315d250db546a7d1ea3a` |
| 7 | `20260820082018_phase4_nutrition_slice4d_provider_snapshot_logging.sql` | `0784183f88ec383b123d714fd57a0e0e06bfbaec67ee138830b8eb33c6446b9e` |
| 8 | `20260820150513_phase4_nutrition_slice4d_historical_provider_resolver.sql` | `e1c3a0429dffe86059e964b7983d56849c387ecf34f57b3de5d67cdb4b16f8be` |
| 9 | `20260822172635_phase4_nutrition_slice4e_ingestion_alias_search.sql` | `f5240d56e4e573af1d01089503c518f31c7bc67c3817948bdbbeff0c979a43e1` |
| 10 | `20260824113551_phase4_nutrition_slice4f_off_catalog_search.sql` | `109deb61aacc9deadd38452d00473e0c75007cf302237c5e5db3a57bf1a1805e` |
| 11 | `20260826143000_phase4_nutrition_slice4fc_off_authoritative_logging.sql` | `15c3abafdb7d77e85397006ba1d62c9221da0820c1052af284911b9edf2dff45` |
| 12 | `20260827125343_phase4_nutrition_slice4fd_transient_off_barcode.sql` | `476f829a2c669c029b87bec9f24459f7e1f5430d02fb32559c50cd9c418c2a2b` |
| 13 | `20260827152727_phase4_nutrition_slice4fd_transient_off_parent_context_fix.sql` | `80eb696450adc81a38be12ebec1631f660c85425cc8453e836047815be3ea0bf` |
| 14 | `20260831145357_phase5_progress_foundation.sql` | `deb29504de883b6cb1f0573e7e60744a81be878952c22f85e28d066baf6661d6` |
| 15 | `20260831150434_phase5_progress_unit_preference.sql` | `b0b83cfe565cb8d7a1a7e88c0097052b657e6a2c6cd9849450bb32de5b07e8fb` |
| 16 | `20260831153512_phase5_progress_revision_indexes.sql` | `d7434837e2d37b5f6ef54c3535a1d0d264d439eda0b79a481553858c997744b7` |
| 17 | `20260901161314_phase5_unit_system_constraint_fix.sql` | `77ef7c490a9430ecacb3c8be2f9a3e021fda391fd45bc7ee698891003b0c1177` |
| 18 | `20260901183914_phase6a_ai_trust_foundation.sql` | `5b48b142fbdc2298bf268cf5804f99053c9346e554faa12b558409e3aa98ee6f` |
| 19 | `20260901184418_phase6a_ai_consent_event_ordering.sql` | `7f653bf3be688d294d68af80689ccb4804eaf65cde1d7c77559a8fdd2134c82c` |
| 20 | `20260901190328_phase6a_pgcrypto_search_path.sql` | `b93b711519796958a2569a363cc1d3131a444eace34ec04395e08aba82ee4325` |
| 21 | `20260901191328_phase6a_foreign_key_indexes.sql` | `5997fe0bacd706503c8bf7397685eb14720c58e946b9bcf70db58c70e6d52c9d` |
| 22 | `20260902045834_phase6b_provider_privacy_cost_gate.sql` | `6b432da3aa389920d5a8eea4f15f74d35e2a9e2d6f7bf44c7b0fbf62473cc526` |
| 23 | `20260903085454_phase6c_private_ai_chat.sql` | `131e63ff165069a4d2861eadec838ad47906cf74a382c0f7ce8ab99f91d8d26f` |
| 24 | `20260903125150_phase6c_request_scoped_safety.sql` | `35ef14f978ad6500abd086b5db80dbec2d875a2a8ddeb39825e8b0ac2b57a831` |
| 25 | `20260904105918_phase6d0_legacy_authorization_gate.sql` | `5b91b22f823a30f86e329b381fe797fd28655d237ad977d6b80d2c99af5485b3` |
| 26 | `20260904230850_phase6d_read_only_ai_analyses.sql` | `a4339bcc4714cdaf4dc7e6b4ad1b448703fb35da6189a9a1fa73842517666953` |
| 27 | `20260904235253_phase6d_analysis_lifecycle_safe_code_fix.sql` | `ecc48734b187c48af699c9639ef369ccb4a5a911e92e743f49082105d73371f0` |
| 28 | `20260906080455_phase6d_owner_safety_settings.sql` | `708d6f547bb0662d4804739fb3c635178305bda2af88c3fd2b62d718c843cdf3` |
| 29 | `20260906092905_phase6d_automatic_inbox.sql` | `546de1b06ff8c84c48ac39dd714afe585777adf7a9b7daad16ffb984c059df6a` |
| 30 | `20260906134827_phase6d_recent_dashboard_analyses.sql` | `6647ea555c175060b139dba6011f67f6397895338c8b9b9a1eedccdf9de3ffbd` |
| 31 | `20260907095307_phase6d_theme_preference.sql` | `865ddc92795cc7f76471343d3d84225a29a2b2ce62cc7e3050ad8407b4953f9b` |
| 32 | `20260908100106_training_workout_editor.sql` | `6f36470394b91b96247df1b3f68f3c0841702326bd456c5f1df9eab360806576` |
| 33 | `20260909215122_training_plan_effort_tracking.sql` | `c062e03da21165d5191b90bfd284815628610bd2e093dda7265e42a4e0343eb1` |
| 34 | `20260915072202_phase6e9_synthetic_authorization.sql` | `2d470e0da00c9fe9e96b5d942c941cbf6dad2c8964e36799909b9dbe601c46c3` |
| 35 | `20260915104711_phase6e10_sources_managed_windows.sql` | `b03336057596dd0591798e1a13d6ae4ac0a7aeaef00ced8148d66c64e3c4a1fb` |
| 36 | `20260916071416_phase6e10_source_reference_indexes.sql` | `f44dcc8e665b926b5f52ceae57a3d4c4148c719217eb34c738a3ed00bc5a5de4` |
| 37 | `20260916072203_phase6e10_strict_command_versions.sql` | `998ecbc9d596f8fba64a2a03decc4ca4c6802dd113ff1e6008169169b85260cc` |
| 38 | `20260916073923_phase6e10_api_conflict_sqlstate.sql` | `a1a2a181617afdbb7eb23a0de0932acdc08ce0c6b3330ea2008152233b92dd99` |
| 39 | `20260916162120_phase6e11_final_app_integration.sql` | `e07c22a6116c970e7cc14830bbb47fb085aa0740696d7311090ead2da5eba0ae` |
| 40 | `20260924130052_phase6e11_private_transaction_audit.sql` | `10db658a56ee0e32fef891fca4fe6522526d059f4ee056baf32ab9acda2a2146` |
| 41 | `20260924155822_phase6e11_rpc_bridge.sql` | `4d474becdc5c3a7343562602115f9333b5cffc6bed0c323fca3abc560843af7d` |
| 42 | `20260928120846_phase6e11_request_binding.sql` | `5eebec968d2dae27d4e1462dbcc9de8d9e5599552ff145ad099e57fffd5f5f7c` |
| 43 | `20261012104331_phase6e11_controller_evidence.sql` | `bab79b7ca5876c2dcef055d0e95997595772aebc051283e69bbeb2ca1dc4bd57` |
| 44 | `20261012185121_phase6e11_single_endchain_budget.sql` | `b21650fa40e2143fb11faff8aeb486ce07bdbead15c7e33b9695b2845e6e4d3e` |
| 45 | `20261018070231_phase6e11_recovery_run_quota.sql` | `64498fa910966497e92705dcf66b76f40c40f01c006aed98c191ce109dd88635` |

## Preservation and Evidence

Baseline: `supabase/.temp/phase6e11-controller-590796353d7344778ee8efb69454065c/before.json`, SHA256 `213673e2a04f04b715f247efe3f27263c0dc998859d5d7e54685a356412f8fef`, historical head `9772d9f0d58f21386515b716de00e3880f7c6438`.
Four differences are .gitattributes (four exact appended LF rules) and docs/ARCHITECTURE.md, docs/MASTER_BUILD_PLAN.md, docs/TEST_MATRIX.md (documented status prefixes/historical headings). Original bodies and baseline are retained. Each transformation was checked against the original hash, not merely accepted by filename.

All44 discovered freeze documents are bound by path/size/hash. For12-20 the JSON includes every frozen source's expected/current hash, receipt, evidence and explicitly mapped report checks. Older freeze documents are hash-bound; this does not independently re-run every earlier phase contract.

Retained receipt roots, newly measured locally without rewriting history:

| Root | Files | Inventory SHA256 |
|---|---:|---|
| `_offline/phase6e11/endchain_v1/receipts` | 1191 | `3af1d59678483514f50548f268eb3b927eb558148a254bc324508897c98addd0` |
| `_offline/phase6e11/recovery_v1/receipts` | 79 | `f3a1dd422e1a5d009abfaff9117f4a7bff46e3b763ab353029d1a2afd54d58da` |
| `_offline/phase6e11/utility_diagnosis_v1/receipts` | 34 | `804354011a011f361b05d04b18a887d7cc755cbea69c1c7bf457b058d8189419` |
| `_offline/phase6e_server_v1/receipts` | 1547 | `84c43f099f3c0280f975f14ecb89b1ab6d3ac9bd04e0fd5a8412dd6fe4be1700` |

Root inventory hash: SHA256 over UTF8 rows sorted by relative path; each row is path + NUL + decimal byte length + NUL + raw SHA256 + LF. This binds current local receipt bytes, not fresh hosted results.24 selected retained artifact members also match their original artifact-manifest hashes across five CI bundles. Complete archive verification was not repeated.

Hosted44 evidence is the retained4b0b preflight, SHA256 `f3f9c3f4e0f3cd2816a05a7f684ac9454bcd8f63c342113b4a2a38cfdbdde4a1`, with exact44-row equality to history_pin.json. The26October report is retained and bound. Earlier18October quota hash d0f7b100... belongs to earlier run-specific bytes; current64498fa9... is the separately bound6f8c candidate. No old result is relabelled as a new PASS.

The JSON binds the owner attachment, AGENTS.md, prior report, quota boundary, history pin, freeze records, app CI40354972820 and the numeric-stop/incomplete WAL receipts. Incomplete diagnostic outcomes remain incomplete. Nine CRLF/LF differences and distinct stored-SQL history representations do not authorize rewriting or repairing anything.

## Validation and Limits

Source metadata/hash verification passed:45 canonical +2 private files;44 historical source pins;44 hosted history rows;47 retained CI migration bindings;158 frozen source entries;24 selected artifact members;1376 preservation entries with4 validated permitted transformations. This is source/evidence verification only, not new PostgreSQL/Auth, WAL, RLS, rollback or integral CI execution.

The dirty list is a timestamped metadata snapshot in JSON. It includes preserved older work and coordinator work already present at capture; no claim is made about authorship of each path. This role writes only this file and its JSON companion. No cleanup or existing-file edit.

Unchanged admission limits: maximum2349 SQL commands; own temporary writes0; strict existing zero-read-WAL gate; one coordinator-owned hosted attempt only after complete admission. No retry, timeout increase, benign-WAL inference, or package21 activation.

External AI calls/cost:0 / EUR0.00. Real-member AI enabled:NO. Production, APPFMZ active and business website touched:NO. Hosted staging touched:NO. Local staging documentation touched:YES. Hosted migrations begin/end:last-proven44 / not remeasured. JIT mappings and synthetic fixtures remaining:not remeasured; this role created none. Owner phone test:NO-GO pending coordinator proof. Remote HEAD:9715ac8600bad89ff813ad399e745360028ce48a, supplied by main; not queried by Role A.
