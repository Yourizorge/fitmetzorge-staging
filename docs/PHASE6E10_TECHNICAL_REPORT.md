# Package 6E-10 Technical Report

TECHNICAL PASS / READY FOR OWNER REVIEW / NOT OWNER-ACCEPTED.
The owner-confirmed login now matches the exact historical account/session/nine rows.
New 127-table before/after evidence, published UI verification and a fresh owner
window are complete. See [current full report](PHASE6E10_FOLLOWUP_REPORT.md)
and [follow-up evidence](PHASE6E10_FOLLOWUP_EVIDENCE.json).
The older blocked-state findings below are preserved history, superseded only by
the explicit owner match and separately recorded new measurements, not a rebaseline.
Read-only follow-up: [investigation](PHASE6E10_READONLY_INVESTIGATION.md),
[metadata](PHASE6E10_READONLY_INVESTIGATION.json),
[partial test receipts](PHASE6E10_VERIFICATION_PENDING.json).
Implementation was pushed as 03eb55af7ab1897a3c6a12b82fcb5d182e88c4de.
The original comparison remains 59/68 equal plus nine explained owner changes.
The new owner window expires 2026-09-17 16:22:20.720 Europe/Amsterdam.
Scope: Yourizorge/fitmetzorge-staging main; mokxyyullfhkfalopbzd only.
Phase 6E remains INCOMPLETE. No 6E-11 implementation, provider or production action.

## Baseline And Acceptance

Actual initial local/remote HEAD: 53b7d36a9dd45ba2c6f0326f5f563304f2e5583f.
6E-9 physical owner acceptance K1 and 6E-10 GO K2 recorded in local commit
f3a1fc8ea5274938ad1eff77a115b438421b6ede. Exact prior sources/80 public assets
are in PHASE6E9_FREEZE_EVIDENCE.json. All 243 protected checkout files match.
Existing Training timer/RIR/RPE, normal app, 6E-0 through 6E-9 remain unchanged.

Old 6E-9 window closed: exact two synthetic workspaces removed, all three sessions
revoked, still-signed JWTs denied, flag OFF and proof removed. The exact three
synthetic Auth/profile identities and owner passwords are retained; zero mail sent.
The owner explicitly selected only the synthetic A-trainer as 6E-10 operator.
An ordinary trainer has no operator capability. See PHASE6E9_FREEZE_RECEIPT.md.

## Implemented Flow

New isolated coach-source-demo entry, four static assets, NL/EN/DE and light/dark/system.
Authenticated trainer appends immutable source ID/version/hash, validity, workspace,
goal, exercise/type, kg or lb, exact steps/available weights/set limits and separate
RIR/RPE constraints. Deterministic server calculation shows planned, recorded and
proposed values. W1 ambiguity blocks; W2 shows full step and why it cannot fit.

Exact source/base/proposal versions bind member acceptance, trainer approval and
separate application. New source makes an old proposal stale, never rewrites it.
Restore makes a newer plan with original and current authorizing source references.
Rejection/blocking is separate from transport failure. Unknown transaction outcome
offers an explicit same-key retry; no automatic physical action.

B is isolation-only here: no A source, editor, proposal or operator control.
An unexpected trainer link denies B. Frozen 6E-9 independent-route behavior is not
rewritten, but its old test window is closed. No new autonomous platform rules.

Managed windows: fixed three server-enrolled identities, source scenario kg/lb,
new UUID, prepared/active/expired/revoked/cleaned, start inclusive/end exclusive,
hard maximum 24 hours. Operator control metadata is available outside a live window
to allow cleanup/new preparation; participant content requires active membership.
Revocation/expiry rejects an already signed JWT. No expired reactivation or overlap.
Exact-window cleanup is idempotent and does not delete retained accounts or real rows.
Expiry denial is not automatic physical deletion. Minimal cleanup receipts remain.

## Database And Edge

New private schema fmz6e10_private, 12 tables:
config, identities, operators, windows, participants, workspaces, source_versions,
source_heads, plans, proposals, audit, requests.
RLS enabled; no client table grants/policies, private schema not exposed by Data API.
Public SECURITY INVOKER fmz6e10_call delegates to guarded private transaction entry.
Pinned search_path, revoked PUBLIC defaults, server proof plus auth.uid/session,
exact identity/profile/link/window/participant checks; no user_metadata authority.
Helpers are not client-callable. Source/plan UPDATE is guarded as immutable.

New Edge fmz6e10-synthetic verifies the user with Auth and forwards the same JWT to
the fixed RPC with a server-only proof. No browser/Edge service-role authority.
Bounded payload, CORS allowlist, no secrets/detail logs, separate input/auth/database
errors. Ordinary app Edge functions and runtime code are not modified.

Four forward-only CLI migrations:
- 20260915104711_phase6e10_sources_managed_windows.sql: isolated implementation.
- 20260916071416_phase6e10_source_reference_indexes.sql: three FK indexes.
- 20260916072203_phase6e10_strict_command_versions.sql: exact numeric command versions.
- 20260916073923_phase6e10_api_conflict_sqlstate.sql: business conflicts use PT409.

The NULL-version regression was reproduced before fixing: SQL NULL comparison had
allowed omission of a redundant supplied version. Stored source/base/approval
bindings still applied, but this did not meet the explicit request contract.
Both NULL and string versions now fail. Original failed evidence is retained.

A strict hosted test rejected a 503 on a stale operation rather than counting it
as authorization success. Supabase documents retry loops for intentional 40001
business exceptions in affected PostgREST versions. Only new 6E-10 exceptions were
changed to PT409; frozen functions were untouched. See
[Supabase troubleshooting](https://supabase.com/docs/guides/troubleshooting/high-cpu-and-infinite-transaction-retries-when-using-custom-error-codes-in-rpc-functions-77326b).
Auth/database outages stay 503. No claim is made that a transport timeout proves denial.

## Verification

- Local PostgreSQL 18, fresh temporary cluster, all four migrations: 65 groups PASS.
  Minimal Auth stubs, not a complete Supabase stack or hosted JWT proof.
- Contract/frozen regressions: 1,734 PASS, 0 fail, 0 skipped.
  One obsolete frozen scope gate is superseded by the new explicit 6E-10 allowlist;
  no frozen behavior test or source is rewritten. Older isolation matrices are
  replaced for this additive scope, not treated as medical reliability tests.
- Preservation: all 243 frozen source/runtime files byte-identical.
- Hosted strict suite: 65 groups PASS. Local UI with hosted backend: 27 checks,
  18 emulated layouts PASS. Fresh checkout: 10 targeted tests + 65 SQL groups PASS.
- Initial Pages assets: 84 identical; all 209 tracked offline/test paths 404.
  ACL/RLS verified; no new security WARN. New FK-index INFO addressed.
- Published UI workflow, final fingerprints and owner window remain pending.
  Read-only follow-up found 59/68 original table hashes equal, nine different.
  Current metadata matches a non-synthetic password session; its human legitimacy
  is not confirmed. The conditional GO has not been claimed as satisfied.

Historical loose/failed/interrupted hosted attempts are not final authorization proof.
Tests use newly created unregistered synthetic ordinary/foreign-trainer controls,
not real member credentials. Negative controls are removed by exact ID/email proof.
Member data is compared via aggregate hashes, not exported into test fixtures.
Browser sessions are genuine synthetic Auth sessions; unknown owner passwords are
neither displayed nor changed. Physical phone behavior remains owner retest.

## Data, Retention And Rollback

Before: 68 pre-existing-cohort table fingerprints and exact 34 migration records.
After target: same 68 hashes, same old 34 entries plus four new entries, empty dry-run.
That data target was NOT achieved: nine differences are preserved, not rebased.
The old 34 migration content hashes are verified identical; 38 entries now exist.
No real chat, photos, health inputs or member plans used as test data. The subsequent
read-only investigation used minimal ownership/time/session metadata and aggregates.
Test-only profile-link changes affect the exact proven synthetic identities and are
restored in finally blocks. Accounts/passwords remain unchanged after tests.

Rollback: revoke the active 6E-10 window through the operator, scoped cleanup when
the owner is finished, then disable only this synthetic entry/proof if required.
Retain additive migrations and evidence; no down-migration, history repair or reset.
No local PostgreSQL or OneDrive files deleted. Temporary clusters are stopped and retained.
No provider/AI calls, email or new external service cost. Production untouched.

## Limitations And Reviews

- Synthetic source provenance is not proof of authentic live trainer authority.
- Three controlled exercises, complete homogeneous sets, explicit comparable
  historical fixture versions; not arbitrary real program/rep-range interpretation.
- Restore conservatively rejects multiple matching rules even where normal progression
  could use explicit priority. No silent fallback.
- Safety/consent are manual controlled fixtures, not health recognition or medical release.
  Self-report, expiry, deletion and lack of detected symptoms never clear physical advice.
- Technical limits on numeric input/volumes are not medical norms.
- Source notes are bounded synthetic text; no genuine health or personal data belongs here.
- D1-D12, O1-O5, W1/W2 remain unchanged. No human medical approval service.
- Medical/resumption, privacy/purpose/retention, legal and language reviews remain open
  for relevant real use, alongside explicit consent/entitlements and applicable
  provider DPA/ZDR/DPIA/EU-route/cost controls. No live integration authorization.
- Cleanup is an explicit operator action; no unattended cleanup scheduler is claimed.

[Owner review](PHASE6E10_OWNER_OVERVIEW.md).
[Single proposed next package](PHASE6E11_PROPOSAL.md), NOT STARTED.
