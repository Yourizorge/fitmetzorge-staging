# Local Synthetic Server Integration

One isolated integration candidate for accepted 6E-12 through 6E-20 and the
still-unaccepted technical 6E-21 extension. Disabled by default. No hosted
deployment or migration application is authorized by this candidate.

Execution: frozen source validators -> server-owned identity and consent ->
locked workspace/version -> pure transition -> atomic durable revision,
request receipt and audit. Browser-supplied roles are never authority.

This directory and its migration candidates must not be included in Pages.
The existing app, training timer and RIR/RPE controls remain unchanged.

## Preregistered Integration Cases

1. Route B intake, source-bound joint plan, separate confirm/apply.
2. Route A member confirm, linked trainer approval, separate apply.
3. Whole/partial set/meal registration, explicit completion and exact totals.
4. Missing versus zero, RIR/RPE independence, kg/lb without conversion.
5. Corrections create durable versions and invalidate prior approvals.
6. New registrations create deduplicated in-app facts/signals without chat.
7. Missing/allergy-conflicting/expired source rules block proposals.
8. Health and self-reported recovery never authorize physical resumption.
9. Consent expiry/withdrawal blocks processing, not authorized old history.
10. Duplicate requests, changed payload, concurrency and wrong actors.
11. Failure after each write rolls back the whole transaction.
12. Restore creates a new proposal/version after fresh required approvals.
13. Refresh, server restart and real local Auth relogin retain history.
14. RLS denies other members, unlinked trainers, anonymous/unauthorized roles.
15. Exact synthetic cleanup records deletes with independent evidence.

Report local/unit, real database, CI Auth, browser and hosted results separately.
No technical PASS is clinical validation or owner acceptance.

## Separate Release12

`RegistrationStore` uses only the five-table M45 candidate, before M46. It calls
the frozen 6E-12 registration validator, preserves the original snapshot and
each correction, and returns historical facts only. It cannot activate a plan,
an outbox or package21. The operator provides an exact workspace/member UUID map;
trainer and control-account attempts are rejected. Live database-clock expiry
is checked again on the final conditional UPDATE. Private schema, RLS, explicit
transaction, exact audit writes and receipt idempotency are shared with the
proven local server infrastructure.

Entry flags are mutually exclusive and default off:
`FMZ_LOCAL_REGISTRATION12_ENABLED=1` selects only registration12;
`FMZ_LOCAL_INTEGRATION_ENABLED=1` selects the broader local integration.
`FMZ_LOCAL_FULL_DAY21_ENABLED=1` is an additional, independent experimental flag
for the latter, not owner acceptance. The private config for registration12 has
exactly `dsn`, `auth_url`, `bindings`; for the combined entry it has `dsn`,
`auth_url`, `workspaces`. Never place credentials in Pages or this directory.
Both entries reject non-loopback database/Auth endpoints. A hosted transport,
full hosted lifecycle/budget and release decision remain separate gates.

Historical source-bound evidence: CI38710983711, completion receipt in
`receipts/ci-38710983711-completion/`; the older receipt remains unchanged.
The selected12 register has970 observed
local commands, including meter setup/closure. It is not a hosted allowance.
See `docs/PHASE6E_CURRENT_COMPLETION.md` and the dated completion report for
current status; older release packets retain their historical meaning.

`registration_transport.py` and `registration_scope.py` are private offline
candidates without a listener or activation flag. Their15 synthetic unit tests
are distinct from real local Auth/storage integration. They require completed11,
physical review, a selected12 decision and exact source/register admission.
They do not enable hosted operation of either existing local entry.

Current CI38725094585 adds actual private transport execution against disposable
GoTrue and verified local TLS for both member routes:46 DB checks,4 Auth checks,
22 complete scoped pairs,1433 observed local commands. `registration_proof.py`
checks exact request/actor/transaction/key and zero writes on denied/replayed
operations. `registration_accounting.py` exports the executed protocol register;
it does not grant a hosted budget. Seventeen scope/transport plus seven pair/
accounting tests supplement the real database proof. See
`receipts/ci-38725094585-completion/` and the current selected-release boundary.
The separate original25 DB/15 browser/4 Auth proof and combined62 DB/209 browser/
4 Auth proof also pass. Hosted11 and selected12 gates remain closed.

M46 adds a transactional in-app outbox to the broader local candidate only.
No push/mail/background delivery is implemented. Expired pending entries are
visibly expired and cannot be processed; a later authorized action may persist
that status. No claim is made of a running background expiry worker.

Comparison windows reuse frozen13 metric definitions and the explicit 3+3-day
policy. All 24 rows must be version-bound, complete and comparable. The UI's
six-day example is explicitly synthetic and is never substituted for missing
actual day records. Its correction creates a new comparison revision.

Planning resolves explicitly approved local times and DST folds/gaps; ambiguous
or nonexistent times fail closed. The accepted fixture still uses UTC and its
historical explicit appointment date. No new cadence, medical policy or durable
background scheduler is implied.
