# Package 6E-10 Synthetic Architecture

Status: implementation verification in progress. No owner acceptance or live AI.
Only Yourizorge/fitmetzorge-staging main and mokxyyullfhkfalopbzd.

## Boundaries
- Existing 6E-0 through 6E-9 and all 80 prior public runtime/demo assets are read-only.
- New entry: coach-source-demo/index.html. No normal-app bootstrap modification.
- New Edge: fmz6e10-synthetic. It verifies the JWT through Auth, forwards that same
  user token to one fixed RPC and adds a server-only proof. No service role in Edge/browser.
- public.fmz6e10_call is SECURITY INVOKER; the private entry is SECURITY DEFINER,
  with a fixed search_path, Auth session check, exact registry identity, profile/link,
  participant, active-window, role and revision checks. No editable metadata authority.
- The only operator is the owner-selected existing synthetic A-trainer. Operator
  capability does not grant access to B workspace data or ordinary members.
- Control-plane window metadata remains available to this operator outside active
  windows so expired fixtures can be cleaned and a new window can be prepared.
  Participant plans, sources and proposals require an active window.
- B has no trainer source, A proposal, A plan, source editor or operator controls.
  An unexpected trainer relation denies B. This adds no B coaching engine.

## Additive Objects
Migration: 20260915104711_phase6e10_sources_managed_windows.sql.
Forward-only index follow-up: 20260916071416_phase6e10_source_reference_indexes.sql.
It covers three composite source/plan foreign keys identified by the advisor,
without changing the applied source/window contract or previous migration.
20260916072203_phase6e10_strict_command_versions.sql rejects NULL and string
command versions explicitly. PostgreSQL NULL comparisons previously allowed the
redundant supplied proposal version to be omitted; exact stored source/base/approval
bindings still applied. Reproduced locally before the forward-only correction.
20260916073923_phase6e10_api_conflict_sqlstate.sql changes only explicit 6E-10
business conflicts from retryable SQLSTATE 40001 to HTTP-mapped PT409. Supabase
documents repeated transactions with 40001 on affected PostgREST versions. The
strict hosted test correctly rejected a timeout instead of counting it as a denial.
Technical Auth/database failures stay HTTP 503, not authentication/contract denial.
The browser preserves uncertain request keys for explicit idempotent retry.
Private tables: config, identities, operators, windows, participants, workspaces,
source_versions, source_heads, plans, proposals, audit and requests.
All have RLS and no client table policies/grants: deny by default. Access is only
through the guarded transaction function, not client UPDATE policies or views.
Sources and plans have immutable UPDATE guards. Cleanup is exact-window cascading
deletion inside the new private schema, not Auth/account or real-member deletion.

A source has stable ID, increasing revision, bound workspace/trainer, hash over
content and binding/validity, explicit goal, comparable plan versions, minimum
session count, controlled exercise/type rules, kg OR lb, reps/set limits, explicit
weight step/available weights, independent RIR/RPE constraints and trainer note.
Numeric storage is exact Postgres numeric, at most six decimal places. This is a
technical input bound, not a clinical or recommended training norm.
W1: every matching rule needs explicit numeric priority, and exactly one has the
lowest value. Otherwise no selection. W2: no smaller weight step, conversion,
rounding or automatic repetitions fallback.
The fixture supplies three controlled exercises and one comparable historical
session. Complete homogeneous sets are supported, not arbitrary rep-range plans.
Source-declared comparisons cannot manufacture missing observations.

## Transaction Rules
Each mutation locks the window, uses its expected revision and an actor-scoped UUID
idempotency key, and commits state/audit/minimal receipt together. Same key/body
replays the original receipt; changed body/key reuse fails. A new-key repeat cannot
apply a proposal twice. Read access is checked before returning prior receipts.
Source append does not edit historical proposals. Current head, source validity,
source hash, base version/hash and exact approval bindings gate review/application.
Source changes after either approval make the old proposal stale.
A new proposal starts with empty approvals. Member and trainer actor IDs are server
derived. Application remains a separate trainer action in this synthetic Route A.
Current/serious/recurring/unclassified/self-reported/missing safety context and
withdrawn consent block proposal/review/application. These are controlled fixture
states, not a deployed medical classifier or medical resumption workflow.
Rejected authorization attempts roll back and do not write another participant's
audit. Committed rejections/blocking actions do create audit events.

Restore creates a new proposal and monotonically newer plan, preserving the restored
plan's original source reference as well as the currently authorizing source.
The current restore validator conservatively requires one matching rule per exercise;
multiple prioritized matches are not yet supported for restore, even where normal
progression can select explicit priority. It fails closed.

## Windows And Retention
Window ID, package 6e10@1, kg/lb scenario, exact fixed participants/roles, operator,
server creation timestamp, bounded start/end, revision, state and feature flag.
Start inclusive; end exclusive; maximum 24 hours from creation and scheduled start.
No extension/reactivation of expired windows. A new test receives a new UUID.
Only one active window may overlap the fixed participants, guarded atomically.
Expiry/revoke denies old signed JWT requests, independent of browser clock.
Expired is a computed server state. Expiry is NOT automatic physical deletion.
Cleanup requires an inactive window, removes its private fixtures/participants and
request receipts, and retains minimal count/hash cleanup evidence, never real data.
A new-key duplicate cleanup is a harmless audited no-op; an exact retry replays.
Retained Auth identities keep existing owner passwords. No mail is sent.
O5 and all earlier retention decisions stay frozen; no real safety registration or
member-data lifecycle is implemented here. Long-term production retention requires
its own approved purpose/retention design.

## Client And Test Storage
Only the new demo's standard Auth session uses its own sessionStorage key.
No existing app storage is read or overwritten. Refresh reads authoritative server
state; fresh Auth login reads the same active window. The proof never reaches JS.
Failed/uncertain commands retain the same request key for explicit retry.
The source editor accepts only synthetic trainer context. Do not enter real members,
health notes or private chats. NL/EN/DE copy is an unvalidated product concept.
Browser checks inject genuine synthetic Auth sessions in memory; they do not know or
change the owner's existing passwords and are not physical-device tests.

## Operational Safeguards
CLI migration naming/application only; fixed project; 34 prior migration records
preserved, four new migrations. A fresh temporary CLI working directory is used due
to the existing OneDrive makeDirectory error; canonical copies are hash compared.
Local Postgres clusters are outside OneDrive, stopped after tests and not deleted.
Existing member tables are compared by aggregate hashes, not exported into fixtures.
The ops broker uses Credential Manager in process memory, no credential files/logs.
Temporary negative-control identities are newly created, non-enrolled .invalid
accounts, removed only after exact captured ID/email proof. No real login is borrowed.
