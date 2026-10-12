# 6E-11 isolated synthetic controller: preregistration

12 October 2026. Owner GO received after extra Edge PASS. Baseline main:
`9772d9f0d58f21386515b716de00e3880f7c6438`. Migrations 1-42 and all historical
receipts remain immutable. This document is a plan, NOT hosted evidence.

## Authority boundary

The new controller is separate from the former read-only admission function.
No public browser endpoint or client role selector. The caller must present a
cryptographically verified GitHub OIDC token for the exact staging repository,
main SHA, workflow, run and attempt 1. The compiled grant expires within ten
minutes. Reject browser Origin, other methods, arbitrary payloads, redirects,
duplicate runs, concurrent calls and all unknown fields before side effects.

Only the three already registered synthetic identities are eligible. Both the
fixed UUID and exact email, private identity role, profile relationship and
operator registration must match. Never derive authority from user_metadata.
The member A, trainer A and member B roles are not interchangeable. Do not create
accounts, change passwords, send email or alter normal accounts.

Existing server credentials stay inside Edge. The existing postgres connection
is required by the private M42 SECURITY INVOKER entry; no client grants or RLS
changes are needed. The service-role secret is used only for exact synthetic
Auth operations which require it, never as application actor authority. Auth
verifies each application token; M42 independently checks the live session.
Any inability to scope an Auth operation is a blocking result, not a waiver.

## Durable admission and proof

Before a hosted controller may mutate anything, its one-shot run claim and
action evidence must survive isolate restart and lost HTTP responses. Pure
in-memory busy flags or a short expiry do not prove at-most-once execution.
Reuse existing private durable structures only where their documented meaning
fits. Otherwise use a minimal, independently tested additive private proof
store; never overload an old PASS receipt or change an old migration.

Each fixed action has run/action/request IDs, synthetic actor and workspace,
expected writeset and count, versions, source hashes and a scoped before/after
pair. Workflow writes use the existing M42 request binding and M40 transaction
observer, including DELETE tombstones. GoTrue is a separate service transaction:
its metadata and request/session IDs must be reported separately, never forged
into the workflow transaction. No managed-schema triggers may be added.

State order: before_saved -> action_started -> action_confirmed -> after_saved
-> pair_validated -> next_step_allowed. Missing/extra writes, stale sources,
incomplete evidence or unexpected own IO are NO-GO. No automatic mutation
retry or cleanup after an incomplete pair. Evidence is append-only; retain
historical 112 pairs and incomplete step 113 unchanged.

## Test matrix and execution budgets

First prove negative controller admission locally/CI: absent/forged/expired
OIDC, other SHA/run/attempt/workflow, browser Origin, payload injection, duplicate
and parallel execution, restart after claim, missing before/after, malformed
request/payload hashes, secret/error redaction, deadline and query limits.

Then the smallest hosted canary: one collector, at most 128 SQL commands, three
full cycles (prefer zero), no retries, no heavy fingerprints. A separate full
workflow manifest must be preregistered and budgeted before its first mutation;
do not squeeze a 45-action proofrun into the canary's budget.

The separate M43 installation uses the already proven migration protocol:
two efficient hash streams, each at most 128 commands, plus 40 reserved CLI
commands (296 maximum, one collector, no retry). This is not the workflow
canary and does not increase that canary's 128-command cap. The retained M42
run needed 65/72 measurement commands, so a shared 128 total would predictably
halt after DDL. No attempt uses that rejected draft budget. CLI load samples
are now taken after the before-stream and before the after-stream, preventing
14 individually bounded FETCH calls from being misclassified as one slow
migration statement. Original M42 failure and reconciliation are unchanged.

Auth matrix: exact-account issuance, verification, getUser, refresh, local
sign-out and rejection of the revoked session. Unprovable routes remain closed.
Workflow matrix: source/proposal, member accept/reject, trainer approve/reject/
block, separate apply, stale versions, duplicate requests/apply, Route B edit/
confirm/apply/reopen, restore proposal and restore as a new version, revoke,
synthetic-only cleanup with retained DELETE audit. Reuse existing product logic.

Only complete hosted evidence permits publication of the candidate application
Edge and an owner window. Closing the testcontroller never substitutes for
fixture/data-preservation checks. Close its temporary authority on every exit.

## Current official guidance

Reviewed 12 October: [changelog](https://supabase.com/changelog),
[Edge authentication](https://supabase.com/docs/guides/functions/auth),
[Auth sessions](https://supabase.com/docs/guides/auth/sessions),
[generateLink](https://supabase.com/docs/reference/javascript/auth-admin-generatelink),
[Auth audit logs](https://supabase.com/docs/guides/auth/audit-logs).
JWT expiry alone does not prove logout; check the live session. Administrative
link generation must never return link/token values or implicitly create an
unknown identity. No upgrade, paid logging, managed-schema modification or
credential rotation is included.

No owner acceptance/freeze; 6E-21 remains unaccepted. JARVIS is out of scope.
External AI calls/cost: 0 / EUR 0.00. Real-member AI enabled: NO.
Production touched: NO.
