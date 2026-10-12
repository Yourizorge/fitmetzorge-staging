# Temporary Auth Metadata Audit

Owner approval: 12 October 2026, explicitly limited to the three registered
synthetic identities, at most ten minutes, metadata only, after local/CI PASS.
This supersedes the pending decision in the guard report, not its historic proof.

## Scope And Authority

Separate private, run-unique schema; no alteration of the proven identity guard.
Seven observed Auth tables: users, identities, sessions, refresh_tokens,
audit_log_entries, one_time_tokens, mfa_amr_claims. Existing postgres TRIGGER and
SELECT privileges were confirmed read-only on staging; no extra managed-schema
privilege is needed. No managed function, RLS policy, password or ordinary account
is changed. No public RPC or Data API access is added.

Only the exact three UUID/address pairs may be registered. The guard must remain
active during token issuance. Audit expiry cannot exceed the guard expiry or ten
minutes. Every action is separately armed by the server, with one actor and one
unique action ID. No automatic extension or reuse is permitted.

Rows contain table/operation, transaction/backend, timestamp, run/action IDs and
SHA-256 row/actor/session keys. No tokens, passwords, email contents, payload
contents or personal/chat/health contents are copied. Trigger code accesses only
the specific identity columns and audit actor_id, never serializes a whole row.
Session-key mappings survive cascaded deletes until this temporary audit is
removed. A deleted row remains a DELETE event in the same committed transaction.
Rolled-back writes have no committed event; the failed request is separately kept.

The trigger is SECURITY INVOKER. Only the managed Auth database role receives
minimal usage/read/append rights on the new metadata objects. It cannot arm an
action, extend expiry, modify existing events, or access the control endpoint.
The existing trusted database/Auth server remains the evidence trust boundary;
this is not tamper-proof evidence against a malicious database administrator.

## Measurement And Attribution

Native controller serializes actions. Before/after exports use only scoped
metadata. Each observed write must match the predeclared table/operation and
actor, session and exact counts. Extra or missing records stop dependent work.
No full database scan is introduced. Auditing only three identities does NOT
prove absence of writes by all other actors; the existing workflow audit and
protected-data controls remain mandatory.

Auth does not expose a supported custom run/action transaction setting. The
server action lease associates the request interval with observed transactions;
the controller must also verify returned request/session metadata and exact
effects. A lease alone is not claimed as proof of an unforgeable Auth request ID.
Concurrent unexpected writes by the same synthetic actor cause NO-GO, not PASS.

## Admission And Removal

Local PG17 checks precede fresh source-bound clean CI with the real pinned GoTrue
image. Tests cover all operations, cascade deletes, rollback, concurrency,
unrelated identities, ACLs, expiry, unknown dependencies and exact removal.
Old CI admission does not cover the new audit.

On every exit, independently of the general NO-GO gate: close issuance, export
technical evidence if possible, validate owned objects, remove only the exact
audit triggers/function/tables/schema, remove the separate identity guard, close
JIT. No fixture cleanup is implied. Unknown objects prevent broad CASCADE removal.
Failure to store evidence remains NO-GO even when safety removal succeeds.

## Official References

[Supabase trigger documentation](https://supabase.com/docs/guides/database/postgres/triggers)
documents OLD/NEW delete evidence and removal through the owned trigger function
when managed-table ownership prevents DROP TRIGGER. Dependency validation is
mandatory before that narrow CASCADE.
[Auth sessions](https://supabase.com/docs/guides/auth/sessions) distinguishes
session revocation from JWT expiry; local helper denial is not a hosted denial.
[Pinned AMR source](https://github.com/supabase/auth/blob/v2.196.0/internal/models/amr.go)
binds AMR claims to session_id, not user_id.

## Canary Admission

The first audit canary stopped during read-only project admission on the
adapter's query allowlist (`unregistered_readonly_query`), not TLS or Auth.
Run `19239cccf8c244fe9c8845ca1a92c722`: eight commands, zero row/DDL writes,
confirmed rollback, JIT disabled and zero mappings. Evidence is immutable.

A single corrected source-bound admission adds the existing required query
signature, without changing query contents or weakening the read-only gate.
Local tests exercise the real adapter: old query denied, corrected query
admitted, payload unchanged (3/3). The corrected marker is separate; neither
attempt marker is overwritten. It inherits the eight commands already used:
both attempts combined must remain within 128. No automatic loop or lease
extension. The first attempt never installed a guard/audit or opened an active
protection window. The corrected active window is limited to 180 seconds.

The tiny canary uses one new synthetic session key and exactly INSERT, UPDATE,
DELETE in one transaction. It produces no tokens or Auth HTTP calls. EXPLAIN
ANALYZE is executed once per statement, with only numerical load evidence
retained. The before/after comparison and retained DELETE events must match.
This proves the observer, NOT hosted HTTP Auth or the Route A/B workflow.

## Native Adapter Follow-up

The corrected attempt `15d85ca72ce2405b93c5918c1801b028` remained NO-GO.
It installed and exactly removed the audit and guard; JIT was disabled with
zero mappings. It stopped on the first EXPLAIN statement before a committed
action or complete action pair. The historical error retained only `Stop`,
not the precise protocol code. That evidence is not rewritten.

Local PG17/libpq reproduces `terminal_row_count` when EXPLAIN is sent through
the ordinary command-tag decoder. The immutable existing Native EXPLAIN reader
handles the empty command count correctly, provided the exact `explain (`
prefix is used. The new runner uses that reader and saves each statement phase
and only allowlisted protocol/SQLSTATE failure codes. No security or SQL change.

The owner separately approved ONE new native-adapter audit probe on 12 October:
at most 180 seconds and 128 commands, including 40 reserved safety commands;
one collector; one new session INSERT/UPDATE/DELETE; no token issuance or
workflow writes. Prior 103 commands remain a separate consumed historical
budget. A new write-once marker prevents reuse. Admission checks both old
cleanup receipts and fresh source-bound CI, including the native decoder tests.
Safety removal is mandatory even on NO-GO or expired action time; no automatic
retry, extension, or dependent hosted Auth/workflow run is authorized by this
small additional budget. The existing broader workflow scope still requires
its own complete source-bound admission and execution plan.

Status: new owner-approved CI admission pending; no hosted Auth PASS claimed.
