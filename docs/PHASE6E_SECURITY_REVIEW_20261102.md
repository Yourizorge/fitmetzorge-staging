# Phase 6E security review checkpoint, 2 November 2026

Status: app CI41474475311 CLEAN_CI_PASS verified from retained artifacts;
security18 executed PASS on the corrected dependency target. E1-E3 are closed
for this source-bound disposable app CI. Advisors: 211 INFO, 117 WARN, 0 ERROR,
not zero findings. No fullchain/hosted GO. Replacement Role E; no DB calls or
implementation changes made by E.

## Scope and source identity

Read the latest owner attachment, repository AGENTS.md and
`docs/PHASE6E_PARALLEL_RESULT_20261026.md`. Sole repository:
`Yourizorge/fitmetzorge-staging`, local checkout
`supabase/.temp/phase4fb-staging-deploy`.
At the original checkpoint, local HEAD and cached origin/main both resolved to
`9715ac8600bad89ff813ad399e745360028ce48a`. Live remote identity is supplied by
main/the owner; this reviewer made no remote Git request.

Role E inspected source and retained evidence only. No SQL was executed, no
database/Auth connection was opened, and no migration, JIT, cleanup, Git write,
CI dispatch or publication was performed. Network access was limited to official
Supabase documentation. Existing dirty/frozen/history files were preserved.
Registered runner, lifecycle and safety_auth remain Role C's files.

Only this report is newly written by replacement E. The predecessor's useful
`_offline/phase6e_server_v1/test_release_security.py` is retained unchanged.
Main implemented the store.py fixes and CI inclusion described below; E did not
edit store.py, ci.py or any test. Main then explicitly requested this read-only
re-review and report update. Historical failure evidence and pre-fix hashes are
retained below; the new local verification has its own source hashes. No further
edits beyond this report are authorized by that request.

## Findings and closure criteria

### E1 / original P1: Auth redirect boundary fixed and verified locally

The pre-fix `_offline/phase6e_server_v1/store.py:44-54` used the default urllib opener.
Allowlisting the initial Auth URL does not constrain redirects or environment
proxy selection. An in-memory HTTP-handler test returned a synthetic 302 from
the allowlisted loopback endpoint to `http://outside.invalid/user`. The real
urllib redirect handling issued the second request with Authorization present.
Both socket creation entry points were blocked: no request reached a network.
This is a demonstrated offline transport-boundary failure, not evidence of an
actual credential leak or a remote attack against the running app. It requires
an untrusted response/transport configuration on the local Auth path.

The existing regression
`LocalBoundary.test_local_auth_cannot_redirect_bearer_off_loopback` originally
failed with `Denied not raised`. Main added NoRedirect and an explicit empty
ProxyHandler to LocalAuth.call. Re-review ran the unchanged regression
successfully: only the initial loopback request is observed, then Denied.
A supplemental in-memory check supplied hostile proxy environment values and
made ambient proxy discovery fail if called; the request remained direct to
loopback and succeeded through the mock handler. No sockets were opened.
E1 was first closed at source/offline-test level. App CI41474475311 now supplies
the executed security regression and separate real local GoTrue evidence bound
to the corrected bytes; see the final CI section below.

### E2 / original P1: effective database address fixed and verified locally

The pre-fix `store.py:68-76` checked host and verify-full but neither rejected
non-loopback hostaddr nor pinned the connection's effective hostaddr. An explicit hostaddr or
ambient PGHOSTADDR can therefore select a different destination while the
accepted host string remains local. TLS verification is an additional control;
this finding does not claim arbitrary remote TLS authentication succeeds.
The local-only policy must reject the attempt before connecting.

The original review could not load psycopg. Using main's supplied local
dependency paths, re-review now passes the unchanged explicit hostaddr and
PGHOSTADDR rejection tests with the real psycopg connection-string parser;
connect itself is mocked and no database connection is made. Main rejects
explicit/environment hostaddr values other than exactly 127.0.0.1 and passes
hostaddr='127.0.0.1' explicitly to psycopg.connect. A supplemental mocked-connect
check confirms that pin survives a PGHOSTADDR change after Store construction.
E2 was first closed at source/offline-test level. App CI41474475311 now supplies
successful actual local adapter/database execution with these same corrected
bytes. The offline mocked-connect result alone did not establish that. No hosted
probe was made.

### E3 / original P1 evidence gap: dependency fix now executed in app CI

At the original checkpoint `_offline/phase6e_server_v1/ci.py:12-33` omitted
`test_release_security.py` and did not invoke it. That historical CI coverage
gap did not mean old CI had run or passed these new tests.

Re-review confirms ci.py NEW includes test_release_security.py at line 24 and
line 211 invokes it from the candidate folder through self.command with label
release-security. E3's source inclusion issue is closed. E independently ran
all 18 tests locally with pglast/psycopg. Main reports combined 42 PASS (security
18 plus release 24); E did not repeat the unrelated release suite or count its
results as independently executed. Fresh CI must retain the release-security
result and verify candidate source binding before/after. No E edit to the CI
assembler was made. Diagnostics are not app Auth/RLS or fullchain evidence.

Subsequent actual run [app CI41471744180](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/41471744180)
reached clean47/47 and SQL/Auth/database tests, then stopped at release-security
with missing pglast before test execution, as reported by main. No retained
receipt for this run was present in the app receipts directory at this inspection;
these run facts are main-supplied, not independently downloaded or hash-verified
by E. Do not infer exact suite counts, completed final source binding, advisors,
final dry-run or whole-app PASS from that partial progress.

The source explains the failure: Gate.install installs pglast==7.20 and
psycopg[binary]==3.2.10 into self.sources/supabase/.temp/phase6e11-pg17-parser and
adds that directory to the parent sys.path. A new Python child does not inherit
sys.path. The reviewed release-security command lacked an explicit PYTHONPATH
for that directory, unlike adjacent dependency-bearing test commands. E's prior
local run supplied PYTHONPATH explicitly; the inclusion review missed this child
environment gap. E3 is reopened for executable CI evidence, not for omission of
the test file. The original 18/18 local result remains valid within its stated
environment and cannot turn this CI import failure into PASS.

Role D's subsequent fix is now independently inspected. ci.py:211-212 invokes
release-security via env with PYTHONPATH set to exactly the pinned install
target, followed by sys.executable, -B and the candidate-folder test file. The
existing command wrapper still raises on a nonzero exit and retains sanitized
stdout/stderr. No package version, network operation, timeout, test skip or
acceptance threshold was added by this invocation change.

E independently ran D's new
test_release_train.ReleaseTrainTests.test_ci_release_security_uses_the_actual_pinned_install_target:
1 test PASS (4.428 seconds). It AST-checks that the installer includes both pinned
dependencies and that the child uses that exact target, candidate test file and
default failure propagation. It is a source regression, not an executed Linux
CI subprocess or import/integration proof.

A fresh local subprocess with only the proposed target on PYTHONPATH imported
pglast but stopped on missing psycopg, before test execution. The existing local
layout has psycopg in the separate phase6e-server-deps directory; CI's reviewed
installer puts both dependencies in phase6e11-pg17-parser. E did not install or
copy packages to disguise this local layout difference. The earlier 18/18 PASS
used both local directories. The new source fix is consistent with CI's actual
pinned installation and has no remaining source blocker identified by E for
main's appCI dispatch. A successful new source-bound CI security step is still
required; this review does not retroactively pass run41471744180 or grant any
fullchain/hosted admission. No E edits to D's files.

The pending-CI statements above describe the earlier review checkpoint. The
subsequent app CI41474475311 executed security18 successfully and closes this
dependency-execution gap for its exact source. CI41471744180 remains failed;
the successful later run does not rewrite that history.

Reviewed D-patch raw SHA256, also matched in app3 source-binding receipts:

- ci.py: 2938d2ff55b3bb4b55d3a01a7d5a824e4ae92a94ad9fc318f5bad41d8e978b0a.
- test_release_train.py: 93856e6ef796ab84f4e27425a61e30137000566214fea988b8d27dab670433e5.

### E4 / existing scope observation: inherited public SECURITY DEFINER endpoints

The private app's three effective functions are SECURITY INVOKER. However,
`supabase/migrations/20260904105918_phase6d0_legacy_authorization_gate.sql`
defines legacy SECURITY DEFINER functions in public and grants authenticated
EXECUTE at lines 247-252. Examples are fmz_bootstrap_trainer_profile,
fmz_phase6d0_issue_client_invite, fmz_phase6d0_accept_client_invite,
fmz_phase6d0_read_own_workspace and fmz_phase6d0_save_own_workspace.

These have explicit actor/profile/owned-workspace checks and fixed search paths;
PUBLIC/anon grants are revoked for the listed functions. Public schema presence
does not by itself prove anonymous access. Per main's clarified scope, these are
existing legacy endpoints, not newly introduced functions or an instruction to
change frozen SQL. No concrete authorization bug was established in this scoped
review, so E4 is not an additional remediation or product-expansion gate.
Preserve existing ACL/regression coverage in app CI. Do not claim all functions
in the legacy public schema are SECURITY INVOKER. No migration or privilege
change is requested without a concrete bug.

## Exact roles and RLS

The private candidate is synthetic-only. It does not create a support role or
derive authorization from user_metadata/app_metadata. The actor is a verified
Auth subject with a live session, an enabled/unexpired synthetic subject row and
an explicit relationship to the workspace. The six agent roles A-F are work
assignments, not six application database roles.

| Role / identity | Source-level boundary |
|---|---|
| Member | Exact workspace member_id; member actions still pass domain, consent, version and request checks. |
| Trainer | Exact trainer_id on Route A; approval/block actions; restricted review projection. Route B has no trainer_id. |
| Private app owner | Exact owner_id, not a global owner or metadata claim. Read-only restricted review projection; execute rejects owner_read_only before mutation. No entitlement, notice or planning detail returned. |
| Support / outsider | No special support authority exists. Without an explicit workspace relationship, no workspace read/write. Support must not be aliased to owner. No new support role, product capability or additional support release gate is requested. |
| anon / authenticated / service_role | No direct private-schema access granted; schema/function ACLs revoked. Possessing an authenticated JWT alone is insufficient. |
| fmz6e_integration_server | NOLOGIN, NOSUPERUSER, NOINHERIT, NOBYPASSRLS; SET role is a private server operation. PostgreSQL administrator remains trusted and outside RLS protection. |

All six candidate tables enable RLS. Their 12 policies target only the restricted
server role. Effective policy review of candidates 46 and 47:

| Table | SELECT | Mutation |
|---|---|---|
| subjects | Own subject only. | No app-role write grant/policy. |
| workspaces | actor in member_id/trainer_id/owner_id; workspace unexpired. | UPDATE USING member/trainer, consent and expiry; WITH CHECK member/trainer. Only version, consent, state_text and state_sha are writable. Identity/expiry columns are not granted. |
| revisions | Exists a workspace visible through workspace RLS. | INSERT requires member/trainer and unexpired workspace; no update/delete grant. |
| requests | Exists a visible workspace. | INSERT actor_id equals actor plus member/trainer workspace and expiry; no update/delete grant. |
| audit | Exists a visible workspace. | INSERT requires current request id and actor hash. It does not independently check workspace membership; trusted triggers/server generate the write set. No claim that this role is safe for untrusted direct SQL. |
| outbox | Member/trainer on visible workspace, excluding owner. | INSERT needs consent and bounded expiry; UPDATE has USING/WITH CHECK plus immutable append-history trigger. Only status/history may change; withdrawal remains possible. |

Both UPDATE policies have corresponding SELECT policies, USING and WITH CHECK.
Consent withdrawal intentionally permits the new consent=false workspace value;
the next operation is denied before idempotent replay. Omitting consent from
that WITH CHECK is not reported as an ownership bypass: identity columns cannot
be updated by the app role. Revisions/requests similarly permit finishing the
same atomic withdrawal transaction; the trusted adapter is part of this design.

The 6E-11 private workflow tables (config, identities, operators, windows,
participants, workspaces, source_versions, source_heads, plans, proposals, audit,
requests, b_states, b_versions, inbox_state, events) enable RLS and revoke direct
browser/service-role access. Access runs through the guarded API, not direct
authenticated table policies. Request-private control and receipts also enable
RLS with browser ACLs revoked. This is source inspection, not a new live catalog
attestation or a complete table-by-table audit of every legacy product table.

## Auth, workflow and privacy observations

- The effective legacy signup trigger no longer uses raw_user_meta_data to
  grant trainer status. Compatibility bootstrap binds auth.uid() and creates a
  client profile. Profile browser UPDATE is limited to name; role/link/email
  are not browser-writable in the reviewed authorization gate.
- LocalAuth asks GoTrue /user to validate the same token before adopting sub and
  session_id. Store.bind checks auth.sessions for that exact actor/session and
  not_after before SET ROLE/claims. A JWT decode alone is not the authorization.
- The 6E-11 principal additionally requires a server proof, enabled exact
  synthetic identity, matching server-side profile and live session. Its roles
  are a_member, a_trainer and b_member. Operator requires a_trainer plus the
  enabled operators row; it is not the private app's owner role or support.
- Controller Auth uses a fixed issuer/audience, guarded token issuance, a
  restricted endpoint set and redirect:error. Identity guards hold/check the
  registered identity and relation before issuance. This remains source review;
  changes to Role C's composition still need its new real-chain evidence.
- Request-private call/seal bind actor, session, payload, key and complete
  measurement pair; a later transaction seals unchanged state. The private app
  instead binds replay to workspace/request/actor/payload with a fresh live
  session check, allowing intended retry after re-login. Do not claim its
  requests table stores or enforces original-session identity.
- Private app requests lock the workspace, reject version conflicts and require
  separate member confirmation/Route A trainer approval. Domain logic is a
  trusted server dependency: RLS alone does not validate semantic plan changes.
- Source inspection found no CREATE VIEW or storage.objects/storage.buckets
  references in the 45 canonical plus two app migration files. Thus there is
  no new view/security_invoker or Storage policy to approve in this candidate.
  This does not attest all existing hosted views, buckets or Storage ACLs.
- The local HTTP server binds 127.0.0.1, checks exact Host/Origin, uses HttpOnly
  SameSite=Strict cookies and CSRF tokens, and keeps GoTrue tokens in memory.
  Its HTTP cookie configuration is local-only, not a reviewed hosted deployment.
- Drafts are actor/workspace/source-bound synthetic payloads in IndexedDB;
  cross-actor replay is checked. They are not encrypted secret storage. The
  service worker allowlists three generic offline-shell assets and does not
  cache API responses or login. Real member data remains prohibited.
- Reviewed transport/protocol error paths avoid logging tokens, SQL parameters
  and row contents. This was a targeted source/evidence review, not a complete
  repository secret scan. No credentials or member records were read/exported.
- Prior Pages exclusion/probe evidence remains historical. No live Pages probe
  was made and no fresh publication/privacy PASS is asserted.

## Evidence ledger

| Evidence | What it proves / does not prove |
|---|---|
| Actual app CI40354972820 at 06b9ac0ad961705a3f7fc8de2fb80d3cf82637a4 | Retained result says CLEAN_CI_PASS, 47 migrations, EMPTY local dry-run, 74 integration DB tests, 4 integration Auth tests, 209 integration browser checks. Real disposable GoTrue/RLS evidence, not hosted or current-source fullchain PASS. |
| Retained collection | Records original archive SHA256 d2c4719cac92a74d9005d01fa606e840ea8df1258bdc8f554607a982128171f5 and 616 files. This reviewer did not redownload/reverify the full archive. |
| Six locally retained payloads | app-cli-profile, candidate, composed-browser, loaded-source-final, loaded-source-preflight and result each match the retained artifact-manifest hash. Manifest/collection are provenance records, not a new independent CI execution. |
| Original targeted candidate comparison | Before main's fixes, 178 existing candidate-listed source files across app, canonical migrations, controller, guard and request areas were checked using raw bytes or CRLF-to-LF matching; 176 matched. ci.py and work_register.json differed. This historical comparison does not cover the corrected store.py or new candidate additions. |
| Original E-suite attempt | Originally stopped at import because pglast/psycopg were not on the runtime path. This historical attempt remains unsuccessful; no dependency install/download was made. |
| Original isolated Auth regression | Pre-fix LocalAuth/Denied and the existing test method were AST-extracted unchanged. One test FAILED (Denied not raised); a separate mock trace confirmed Authorization on the redirected request. This failure remains historical evidence. |
| Current E-suite rerun | Independently executed all 18 unchanged tests: PASS, exit 0, 1.751 seconds reported by unittest. Real pglast parsing and psycopg conninfo parsing; mocked HTTP/database I/O. No SQL, real GoTrue or network execution. |
| Actual app CI41471744180 | Main reports clean47/47 plus SQL/Auth/database progress, then missing pglast at release-security before any of its test methods ran. Overall run failed; no 18-test security CI PASS. Local receipt/source/archive verification pending. |
| D dependency fix review, historical checkpoint | Correct target/candidate invocation inspected; focused AST regression 1/1 PASS. One-target local import probe stopped on psycopg because local dependencies are split. That probe remains unsuccessful; later CI execution is separate evidence. |
| Actual app CI41474475311 | Independently checked 619/619 manifest-listed file hashes. CLEAN_CI_PASS at 5c6ca4aa57621a15c71afde006c90b0063eac138; clean47/47, EMPTY dry-run, security18 actually ran and passed. Both source-binding receipts PASS. See final CI/advisor section for precise limits. |
| Current supplemental checks | Hostile ambient proxies ignored; connect address remains pinned after environment change. Both PASS with sockets blocked and connect mocked. These two checks are separate from the 18-test suite and main's reported combined 42, not extra CI tests. |
| RLS/function review | Source inspection plus the now-passing SQL AST/static assertions. SQL parsing does not execute policies or establish fresh live RLS results. |
| Actual CI advisors | app3 advisors.json records hash-pinned Splinter execution on disposable PostgreSQL: 211 INFO, 117 WARN, 0 ERROR. E read/hash-verified the receipt and did not execute SQL or advisors. Separate db lint exited 0 with warnings. Neither result is zero findings or hosted Auth configuration evidence. |
| Endchain/WAL | Prior CI40354914899 stopped before Auth/workflow. Earlier incomplete diagnostic intervals remain INCOMPLETE. No new causal/WAL-zero claim. |

### What the security tests actually assert

`test_release_security.py` has 12 SqlSecurity tests and 6 LocalBoundary tests.
SqlSecurity uses pglast to parse migration files and inspects AST nodes/rendered
SQL or function-body substrings. Its six-table RLS check proves ENABLE RLS
statements exist in source; it does not query pg_class or execute an RLS policy.
Policy targets, USING/WITH CHECK presence, grants, invoker declarations, fixed
search paths and principal/replay fragments are similarly source assertions.
The suite does not prove every predicate is semantically correct or all migration
effects compose into the expected effective database catalog.

LocalBoundary blocks sockets and mocks psycopg.connect. Its live-session case
uses a fake execute/fetchone result, and its redirect case uses an in-memory
HTTP handler. Real conninfo parsing is not a real database connection. None of
these 18 tests supplies actual Auth issuance, live RLS, SQL execution or hosted
admission evidence. Do not label their PASS as an RLS integration PASS.

Separate `_offline/phase6e_server_v1/database_tests.py:163-173` does execute
database checks when run by its real integration caller: after Store.bind it
queries another member's workspace under the restricted server role and asserts
zero rows (`RLS_cross_member_zero`). It also SET ROLEs anon/authenticated/
service_role and requires SQLSTATE 42501 for private-workspace access. Those
three denials demonstrate ACL/schema exclusion, not independently each table's
RLS behavior. Other adapter denials can originate from domain/application checks;
their success must not all be attributed to PostgreSQL RLS. The suite is not an
exhaustive live six-table by all-role/mutation matrix. Its caller in ci.py uses
real_local_GoTrue, while the shared test module can also receive mock-local Auth.
Attribute any executed result to its actual caller, source hash and receipt.
Historical app CI40354972820 and the new failed run remain separate evidence.

## Final app3 CI and advisor disposition

Inspected the user-designated app3 evidence, physically present at
`supabase/.temp/phase6e-server-ci-3e7589b8931c46698ff10d5040c979a0/verified-41474475311`
under the sole repository (no intervening app3 subdirectory on disk).
[App CI41474475311](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/41474475311)
result.json records CLEAN_CI_PASS at commit
`5c6ca4aa57621a15c71afde006c90b0063eac138`, candidate SHA256
`ca8b724de035bcce8fbd34cc218414827afb8c72db8208570dc3b1f4853b7e71`.
E independently recomputed all 619 manifest-listed hashes: 619 match, none
missing/mismatched. The collection records archive SHA256
`3620e0b1716b625f5bec8dbc158fdacb862a8dabef127e542514e71df7c16842`;
E did not redownload or rehash the original archive or query GitHub live.

`365-release-security.json` has exitcode 0 and explicitly reports 18 tests run,
OK (0.251 seconds unittest time, 0.481 seconds process time). This resolves the
actual missing-pglast execution failure from CI41471744180. The test file remains
unchanged. Both loaded-source-preflight.json and loaded-source-final.json say
ALL_PYTHON_SOURCE_BINDING_PASS; the final receipt lists 210 sources and matches
the reviewed ci.py, store.py, test_release_security.py and test_release_train.py
hashes. This is evidence for that commit/candidate, not arbitrary later changes.

Result.json also records clean47/47, all 12 planned SQL regressions, 74 integrated
database tests, 4 integrated Auth tests, 209 integration browser checks and an
EMPTY local final dry-run. Groups are distinct and are not summed. The inspected
integration-database.json explicitly names real_local_GoTrue and successful
RLS_cross_member_zero plus private_denied_anon/authenticated/service_role cases.
integration-auth.json records actual password re-login, session deletion on
global logout and both revoked-token denials. Therefore actual local Auth and
the named live RLS/ACL checks have evidence separate from security18's AST/mocks;
this still is not an exhaustive live six-table/all-role policy matrix.

### Actual advisor totals

E parsed every row of the retained advisors.json output, rather than inferring
an empty report from CLEAN_CI_PASS:

| Severity | Check | Count |
|---|---|---:|
| WARN | auth_rls_initplan | 49 |
| WARN | authenticated_security_definer_function_executable | 67 |
| WARN | function_search_path_mutable | 1 |
| INFO | rls_enabled_no_policy | 76 |
| INFO | unindexed_foreign_keys | 25 |
| INFO | unused_index | 110 |
| ERROR | All checks | 0 |

Totals: 328 findings = 211 INFO + 117 WARN + 0 ERROR. All 67 authenticated-definer
warnings name functions in public; none names the app candidate's private schema.
Do not describe these as 328 vulnerabilities, universally harmless findings, or
a zero-advisor result. They remain review/maintenance findings under existing
scope. The pinned advisor source is Supabase Splinter commit
`e74a9e36cb12258cb67d1464bc1cb196e9cd8446`, source SHA256
`d8d558baad3e03832e521c527907fa50a9a172fabd899dd0f5c2504a5a0e9349`, executed SQL SHA256
`8ed8cd1eb6ece2c5582fc89a1b1a52eb130170570f8d587993ec2a244e700ffc`.
Scope is local database security/performance, not hosted Auth configuration.

The bound runner rejects advisor ERRORs and specifically WARNs involving
fmz6e11_workflow_audit; it does not require zero WARNs globally. That explains
why this actual CI PASS coexists with warnings and does not waive them. The
separate `374-cli-db.json` is db lint, exit 0 with issues on 28 functions, none
named fmz6e_integration_private.*. Do not confuse lint output with advisor totals.

### Mutable path and candidate findings

The single mutable-path warning is `public.touch_updated_at()`. Its definition
is in the original `20260812000000_legacy_phase1_3_source_baseline.sql:346`.
It returns trigger, has no SECURITY DEFINER declaration (default invoker), and
its body only assigns `new.updated_at = now()` and returns NEW. It has no fixed
search_path, so the advisor finding is real; it is not introduced by candidates
45/46/47 or the dependency fix. No later definition/ALTER for this exact function
was found in the reviewed migrations. No concrete new privilege-escalation path
was established here; mutable path remains legacy hardening debt, not a request
to rewrite frozen SQL or a newly demonstrated candidate security blocker.

The baseline file's local hash matches the app3 candidate hash
`ae06ca53771d90baa12c12af8d8b43e3bd0464d926d8795197859c4a8b8ae26b`.
All 47 migration hashes in app3's candidate manifest equal their entries in
historical app CI40354972820's candidate manifest. This proves unchanged source,
not equality of all historical advisor outputs or current hosted catalog state.

Exactly six advisor findings name fmz6e_integration_private:

- WARN auth_rls_initplan on subjects.subject_self and audit.audit_insert: repeated
  current_setting/auth evaluation is a performance concern; it is not itself
  evidence of an ownership bypass. These policies belong to the existing private
  candidate source, unchanged from the previous app CI.
- INFO unindexed_foreign_keys on requests_workspace_id_version_fkey and the
  workspaces member_id, owner_id and trainer_id foreign keys. These are index/
  performance findings, not missing authorization checks. No index change made.

No mutable-path or authenticated-definer advisor warning names this private
candidate. integration-security.json independently records its actor, observe
and outbox_append functions as invoker with search_path=pg_catalog, pg_temp and
the server role as non-login/non-superuser/non-bypassrls. E found no new concrete
candidate security blocker in these six findings. This scoped disposition does
not certify performance at arbitrary scale, dismiss all legacy warnings, or
override the fullchain WAL/IO/budget gates. Official
[advisor guidance](https://supabase.com/docs/guides/observability/advisors)
also calls for evaluating findings against the intended schema/access model.

Pre-fix reviewed file SHA256 values (raw on-disk bytes; retained as history):

| File under _offline/phase6e_server_v1 | SHA256 |
|---|---|
| store.py | a1e11929faef77e1388bbb5b4103fc6e712198ec37cd59f2f4fb9d450c40a866 |
| server.py | 7cd23d0d3b6103fc7700728f8708a3e9e56c13d40d64e49a65e02665c42cc5c4 |
| test_release_security.py | c24f1b6e2ffd96eadbfe0c70cccb6e4d14d8e9fa93f45a7f2a25f2ec190e44ba |
| registration_transport.py | 40f85353fc445a0857e57f64ac61dfc6a5841ed82b2b22e62520066652ea46e6 |
| supabase/migrations/20261014105919_phase6e_synthetic_server_candidate.sql | 51953e164c2431299bf8825d08e30fe776434a99c8766a9e1faeb3c956d05b0d |
| supabase/migrations/20261014160019_phase6e_local_outbox.sql | fc0edf31bff828256d3719713bc269646c908673f121ccbce0b26099d7c8b650 |

Current re-reviewed SHA256 values (raw on-disk bytes):

| File under _offline/phase6e_server_v1 | SHA256 |
|---|---|
| store.py | 85195ac378122df946fe159b15364829f961b396711a596e67d56c9f248e7808 |
| ci.py | 261d88bacfdb266bc437177912da70d6ab6866336c8f95a0269c048a5eb4b7e6 |
| test_release_security.py, unchanged | c24f1b6e2ffd96eadbfe0c70cccb6e4d14d8e9fa93f45a7f2a25f2ec190e44ba |

Reproduction from the sole repository root in PowerShell, using existing local
dependencies supplied by main:

```powershell
$env:PYTHONPATH='_offline/phase6e_server_v1;supabase/.temp/phase6e11-pg17-parser;supabase/.temp/phase6e-server-deps'
& 'C:\Users\Fitme\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m unittest -v test_release_security
```

## Official documentation checked

Checked 2026-11-02; no new Supabase feature introduced. The changelog Markdown
endpoint was unsupported by the web reader, so the official HTML index was used.

- [RLS](https://supabase.com/docs/guides/database/postgres/row-level-security):
  user metadata is not authorization; ownership predicates matter; UPDATE needs
  SELECT. The current docs explicitly say omitted WITH CHECK reuses USING, so
  omission alone must not be described as an automatic ownership bypass.
  Exposed views should use security_invoker on supported PostgreSQL.
- [Functions](https://supabase.com/docs/guides/database/functions): fixed search
  paths and explicit EXECUTE ACLs matter. Schema-scoped default revocation does
  not remove the global PUBLIC default. The request migration's final explicit
  revoke on all functions is material; its earlier default-privilege statement
  alone is not a complete control.
- [Sessions](https://supabase.com/docs/guides/auth/sessions): correlate JWT
  session_id with auth.sessions for strict sign-out checks.
- [Storage access](https://supabase.com/docs/guides/storage/security/access-control):
  upsert needs SELECT/UPDATE as well as INSERT; no new Storage use reviewed here.
- [API security](https://supabase.com/docs/guides/api/securing-your-api) and
  [Data API exposure change](https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically):
  verify explicit grants and RLS separately; changed defaults are not proof of
  current hosted ACLs. The private direct-connection design does not rely on
  automatic Data API exposure.
- [Changelog](https://supabase.com/changelog): inspected relevant breaking-change
  entries. The self-hosted gateway detail page timed out; no compatibility claim
  is made from it. No image, SDK or runtime upgrade was attempted.
- [CLI reference](https://supabase.com/docs/reference/cli/supabase-db-advisors):
  advisors capability exists in current docs, but the actual installed CLI must
  be discovered with --help by main before any separately authorized execution.

## Handoff and limits

E1-E3 now have source-bound app CI41474475311 execution evidence, including the
18 security tests and separate real local Auth/database checks. CI41471744180
remains a historical failed attempt. Advisors are explicitly 211 INFO/117 WARN/
0 ERROR; no new concrete security blocker was established in the single legacy
mutable-path function or the six private-candidate findings. The remaining
fullchain/hosted gates are not replaced by this disposable app CI PASS.
Reviewer F retains the complete evidence review; the documented audit-insert
trust boundary is not a new untrusted direct-SQL capability. E4 remains existing
scope, and no support-role expansion, frozen SQL or public runtime edit is requested.

The diagnostic-only runs plus app CI do not establish the complete endchain.
Fullchain GO still requires the real complete gates, independently classified
durable WAL interval, exact migration/source binding, complete command accounting
and cleanup reserve. Maximum 2349 SQL commands, strict existing read-WAL limit
and measured own temporary writes zero remain unchanged. No hosted attempt was
consumed by Role E. Package21 and real-member AI remain off.

- External AI calls/cost: 0 / EUR 0.00 for application/provider operations.
- Real-member AI enabled: NO.
- Production touched: NO.
- APPFMZ active touched: NO.
- Business website touched: NO.
- Staging touched: local review document only; hosted NO.
- Hosted migrations begin/end: last proven 44 / not remeasured.
- JIT mappings after review: not remeasured; none opened or changed by E.
- Synthetic fixtures remaining: not remeasured; none created by E.
- Owner phone test: NO-GO at this checkpoint.
- Initial remote HEAD: owner/main-confirmed 9715ac8600bad89ff813ad399e745360028ce48a; not queried live by E. Current app CI source is 5c6ca4aa57621a15c71afde006c90b0063eac138; Main reports the definitive delivery HEAD separately.
