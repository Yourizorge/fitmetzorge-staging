# Auth Failure Component Contract

Role 2, 2026-11-02. Only new `auth_failure*` files are owned here. No shared
Auth, lifecycle, migrations, historical receipts, CI dispatcher or run binding
has been edited. This component is local diagnostic preparation, never hosted
admission. No fourth WAL diagnostic is started.

## Parent API

Import `auth_failure` from this directory and call `run(gate)`. Required Gate
properties are `.out`, `.save(name, value)`, and private `.auth_failure_context`.
Parent CI retains responsibility for loaded-source/candidate binding, complete
artifact binding and the isolated PG17/GoTrue environment. No bootstrap, Docker
pull, schema migration, quota activation, fixture setup or CI dispatch is hidden
inside this component.

```python
with ci_auth.environment(prefixed_gate, include_test_admin=True) as ctx:
    prefixed_gate.auth_failure_context = auth_failure.context_from_ci(
        ctx,
        run_id=admission_binding.NEW_RUN,
        managed_costs=dict.fromkeys(('create', 'login', 'logout', 'delete'), 128),
        exclusive_local_auth=True,
    )
    result = auth_failure.run(prefixed_gate)
```

The separately authorized optional suffix is
`auth_failure.run(prefixed_gate, safety_reconciliation=True)` (CLI:
`--safety-reconciliation`). Default execution does not silently invoke it.

`test_admin_token` stays memory-only; do not serialize the context. The helper
copies `ctx['dsn']`, `ctx['auth'].url` and `ctx['test_admin_token']`. Only exact
loopback origins 59999 or 54321/auth/v1 are accepted. SQL requires PG17,
verify-full TLS and an existing CA, host and hostaddr exactly 127.0.0.1;
conflicting PGHOSTADDR is refused. Hostaddr is explicitly pinned at connection.
HTTP uses no proxies, redirects or automatic retries. Native SQL uses autocommit,
no prepares, connect_timeout=5, statement_timeout=5000 and lock_timeout=1000.

Missing/invalid context returns `BLOCKED` before connection/mutation; unavailable
or invalid PG/TLS returns `BLOCKED` before mutation. These are not skipped PASS
cases. Credentials must refer to an exclusive disposable service: statistics
measure the whole local supabase_auth_admin role between each HTTP action.
Concurrent external Auth traffic invalidates that attribution.

The preparation ID supplied by main is
`11a909f4-7113-424a-aa4b-ce9964720a3e`. Every case gets a fresh UUID4; the
preparation ID does not activate database quota or reuse an October workflow.
The historical October UUID appears only in a refusal check and refusal test.
No existing migration bytes are modified or executed by this component.

## CLI

Private environment: `FMZ_AUTH_FAILURE_DSN`, `FMZ_AUTH_FAILURE_URL`,
`FMZ_AUTH_FAILURE_ADMIN`, and optional `FMZ_AUTH_FAILURE_API_KEY` (local gateway).
Use an existing private output directory:

```text
python -B auth_failure.py --out PRIVATE_DIRECTORY --run-id NEW_PREPARATION_UUID --exclusive-disposable --managed-costs '{"create":128,"login":128,"logout":128,"delete":128}'
```

Exit 0 means only `LOCAL_AUTH_FAILURE_COMPONENT_PASS`; exit 2 means blocked or
component failure. Every deliberately failed execution remains `NO_GO`, even
when its negative-test expectations pass. `full_chain_admission` is always false.

## Cost Contract

Main explicitly proposed 128 per HTTP operation as a conservative preregistered
LOCAL DIAGNOSTIC ceiling. It is not an observed count, proven upper bound,
hosted authorization, or a change to the 2338/2349 planned run. No defaults are
silently substituted: the caller must supply all four positive costs.

The old managed register's `issue=11` and `verify=21` do not establish the costs
of admin-create or password-login. The old logout=10 is also not substituted
for this separate local contract. Actual per-action counters use the existing
auth_protocol.STATS/difference numeric collector, including its reset,
deallocation, utility-tracking and temp-write checks. No query text is exported.

Before any Auth operation, the complete case allocation is durable:

- Four distinct HTTP actions, each with its caller-supplied managed SQL charge.
- Twelve native SQL slots: four scoped snapshots and before/after statistics
  for each of four possible HTTP actions.
- Total reserved per case: `12 + create + login + logout + delete`.
- With 128 each this is **524**, not 528. Eleven independent cases reserve 5764
  local diagnostic units; they are NOT one run under the hosted 2349 allowance.
- Each allowed HTTP action and native SQL statement is fsynced before dispatch.
  An unknown result remains charged; unused reserve is not reported as a refund.
- An observed managed overrun blocks every later HTTP mutation, including delete;
  claims stay retained. Read-only final observations still have prepaid slots.

Expected model paths, assuming all non-injected operations complete:

| Case | HTTP dispatches | Native SQL | Cleanup disposition |
| --- | ---: | ---: | --- |
| before_dispatch | 0 | 4 | Proven empty/no Auth dispatch; no delete claim |
| create_lost_reply | 2 | 8 | Recover exact owned user, confirmed delete + zero |
| partial_user | 2 | 8 | User exists, login not dispatched; delete + zero |
| partial_session | 3 | 10 | Login committed but reply lost; delete + zero |
| login_timeout | 3 | 10 | Real client timeout; terminal relay required; delete + zero |
| logout_timeout | 4 | 12 | Real client timeout after global logout; delete + zero |
| admin_unknown | 3 | 10 | Delete reply lost; zero observed but claim retained |
| duplicate_request | 3 | 10 | Second login rejected before dispatch, original charged |
| cleanup_interrupted | 2 | 7 | Stop before delete; owned user/session remain, claim retained |
| missing_mint_barrier | 2 | 6 | No delete without terminal proof; claim retained |
| duplicate_cleanup | 3 | 10 | Second cleanup rejected with no additional dispatch |

These are control-flow counts, NOT real GoTrue measurements. Expected totals
are 27 HTTP / 95 native SQL, with prepaid consumption
`95 + 10*create + 8*login + logout + 8*delete` (3551 at 128 each).
Runtime receipts report actual dispatched counts and observed managed SQL
separately. Parent environment setup, initial ci_auth accounts, startup protocol,
baseline statistics and environment teardown are outside these totals and must
be counted separately by parent CI. Do not double-add its overlapping role-level
statistics and this per-action collector.

## Ownership And Cleanup Proof

Each case creates an exclusive retained directory and claim before SQL/HTTP.
Reopening the same claim or reusing the same matrix directory is refused.
The synthetic email uses a case UUID and example.invalid. Creation records an
admin-controlled app_metadata marker; no user_metadata authorization is used.
The baseline must be empty. Discovery is limited to the exact email, exact marker
and previously bound UUID; conflicting or multiple matches stop cleanup.
Only an exactly owned user is deleted, through the admin API. No broad SQL delete
or fixture sweep exists here. Real member/owner/support records are not used.

The journal records hashed actor/session identities, original failure, dispatch
status, numeric load, deletion acknowledgement and final counts. It never records
passwords, bearer tokens, emails, raw user UUIDs, DSNs or SQL result bodies.
Absence checks cover users, identities, sessions, refresh_tokens, mfa_amr_claims,
mfa_factors, one_time_tokens and flow_state for this exact scope. Append-only
Auth audit history is not deleted; zero temporary objects does not mean zero
audit history or zero global Auth objects. Public profile/fixture cleanup is not
claimed here and belongs to the fixture component.

The snapshot validator requires exactly all eight nonnegative integer counters.
User/session counters must match their returned lists; session keys must be
unique canonical UUIDs within the existing bound. Missing counters or a zero
counter paired with remaining session keys cannot prove absence. The same
validator is applied before ordinary cleanup and separate reconciliation. It
adds no SQL, HTTP dispatch or budget allocation.

Mint-barrier scope is deliberately narrow: client dispatch is permanently closed
and each dispatched upstream HTTP request has completely responded. A lost
client reply can still have separate relay terminal evidence. An upstream timeout
without that evidence blocks deletion and claim release; an advisory lock or
a zero snapshot cannot replace it. No request is repeated to discover its outcome.

Independent F follow-up: a bounded read alone does not prove Content-Length
completeness. The relay now requires exact advertised length, or successful
chunk decoding including the final trailer CRLF, before marking terminal. The
body limit is 65536 bytes. Duplicate/conflicting length/encoding headers,
unsupported transfer encodings, unframed non-empty-status responses, truncated
bodies and oversized responses remain unknown. A bodyless 204 is accepted.
The strict trailer check closes stdlib's otherwise tolerated EOF-at-trailer case.

If an HTTP failure is followed by a stats-after/difference failure, the original
HTTP exception remains primary. Sanitized phase/class details are separately
retained in `primary_failure_detail`, `http_failures`, `observer_failures` and
journal events. Both dispatch reservations stay spent, no refund is issued, and
the missing managed observation prevents claim release or component PASS.

Further F follow-up: failure to persist the HTTP `unknown` event also cannot
replace the original HTTP exception. Its phase/class is captured before that
write; the save error is retained separately in `journal_failures` without raw
error text. `journal_complete=False` prevents claim release and component PASS.
The pre-dispatch charge stays spent. If later receipt writes remain possible,
the result retains both failures; persistent storage failure still cannot yield
a successful durable receipt. No create retry or refund is performed.

This is NOT proof that the entire GoTrue process has no background writers.
`gotrue_process_quiescence_proven` and `hosted_mint_barrier_proven` remain false.
Parent must retain service lifecycle evidence; this local relay does not solve the
hosted incomplete-request barrier. `claim_released` is the scoped local cleanup
decision only. It never asserts future global absence or invalidation of every
unexpired JWT. Deleting sessions/users is not immediate cryptographic JWT expiry.

On expected fault paths admin_unknown, cleanup_interrupted and
missing_mint_barrier the claims remain retained. The last two intentionally leave
one local synthetic user/session each. Do not feed that disposable database into
unrelated clean-state claims or silently repair those outcomes. The parent owns
eventual teardown of the disposable environment, separately evidenced, without
rewriting the original unresolved receipts. Component PASS can contain these
expected NO-GO states; it does not mean all claims or sessions are zero.

## Separate Safety Reconciliation

Inspection of the current `ci_auth.environment` confirms its final action is
`docker rm -f` for the GoTrue container only. It does not delete users/sessions
from PostgreSQL. Main's `admission_ci.py` runs fixture tests inside that same
environment after the Auth matrix. Removing the Auth service is not a database
zero proof, and fixture cleanup is not evidence of Auth-user deletion. The
environment's own three baseline users are outside this component's scope too.

Each original case now exports `owned_scope_audit`: hashed actor/session keys,
hashed claim marker, the last scoped count observation and its sequence. The
aggregate has `retained_object_audit`. These observations are explicitly not
global zero and not current-after-teardown evidence.

The opt-in suffix gets a NEW exclusive `safety-reconciliation` journal under
each retained case, with the SHA256 of the immutable original result. Every
original result/claim/NO-GO and prepaid consumption remains unchanged; no refund
is issued. Repeating the suffix is refused. The suffix is separately included,
with sanitized journal contents and byte hashes, in `safety_reconciliations`.

- `cleanup_interrupted`: permitted only for an originally expected fault with
  complete observations, valid ownership, a sealed dispatcher and complete
  original upstream terminal proof. The exact owned user, session keys and counts
  must still match the original prefix. Only the previously UNSENT admin delete
  may execute. Confirmed HTTP delete, measured managed cost within allocation,
  and a fresh eight-table scoped zero observation are all required. This proves
  local scoped reconciliation, not process-wide or hosted quiescence.
- `admin_unknown`: one scoped observation only. Even if zero, there is no replay
  and no retroactive acknowledgement of the original unknown delete. Original
  claim and NO-GO remain, `reconciliation_confirmed=False`.
- `missing_mint_barrier`: one scoped audit observation, no mutation. The exact
  blocker is `missing_mint_barrier_no_new_independent_terminal_evidence`. The
  suffix cannot substitute a zero snapshot or service-container removal for the
  missing independent proof. It does not toggle the old false barrier to true.

The complete suffix is reserved before its first SQL dispatch from the ORIGINAL
unused local allocation. For cleanup_interrupted it needs four native SQL slots
plus its existing delete tariff (132 at tariff128). The other two cases reserve
one native observation each. No new hosted allowance or 2349 change is made.
On the expected model path, original 263 plus suffix132 is 395, within original
524. Across all three suffixes the additional local accounting is six native
SQL and one HTTP dispatch, with 134 prepaid units at tariff128. It is reported
in `reconciliation_diagnostic_totals`, separate from original fault-path totals.
Unavailable capacity, changed ownership, changed rows, uncertain deletion,
failed observation or overrun leaves reconciliation unconfirmed without refund.

Reconciliation acknowledgement and measurement flags become true only AFTER
their corresponding durable journal events succeed. A failed delete-confirmation
or managed-observation receipt cannot leave a stale true flag that confirms
cleanup. Original case results remain byte-identical; attempted operations stay
charged even when their receipt fails. This does not turn physical deletion into
a claim of complete proof when evidence is missing.

Expected local outcome WITH suffix: cleanup_interrupted's one user/session is
removed; missing_mint_barrier's one user/session remains unresolved. The original
admin_unknown case remains an unknown-delete claim with observed zero. Without
the suffix, both originally retained users/sessions remain. These are expected
control-flow outcomes, not current actual PostgreSQL observations.

Consequently the component explicitly exports `full_auth_cleanup_proven=False`,
`full_auth_cleanup_status=NOT_PROVEN` and `global_auth_zero_claim=False` even if
all negative-test checks pass. Complete Auth cleanup for every partial path is
still NOT proven with the available evidence. It needs new independent terminal
evidence for the missing barrier and separately accountable owned cleanup; this
agent has not generated that evidence or claimed a full Auth PASS.

Parent coordination checkpoint, 2026-11-03: C owns the separate disposable
parent-closure helper and its fixture/bootstrap ownership, costs and receipts.
This component does not sweep those objects, invoke that helper implicitly, or
change shared files. Per owner's update, the fixture phase leaves four intentional
rows plus three bootstrap identities/operator context; that is parent-reported,
not a new database observation by this reviewer. GoTrue stopping may be lifecycle
evidence but is NEVER evidence that PostgreSQL accounts or sessions were deleted.
Parent closure must report its own barrier, exact owned cleanup and final scoped
observations separately; incomplete original claims remain NO_GO. Neither this
component's observations nor container removal establish global Auth zero.

## Artifacts And Evidence

`auth-failure-component.json` contains every case result and its
`retained_journal.files` dictionary: exact sanitized claim/event/result JSON,
SHA256 of the original fsynced bytes, and byte length. Thus a parent's existing
flat artifact glob retains all nested journal evidence through this aggregate.
Original exclusive journal files remain in the nested private directory.
Prefixing `gate.save` is supported; no fixed existing integration receipt is
overwritten. Source hashes cover the two new runtime modules; parent same-source
binding must also cover the imported existing auth_protocol module and test file.

Earlier checkpoint: 22 tests PASS in 14.601s. After independent F's P1/P2 fixes:
31 tests PASS in 23.570s. After explicit safety-reconciliation support:
38 tests PASS in 23.937s. After the failed-unknown-event persistence correction:
39 tests PASS in 19.351s. Latest cleanup-proof checkpoint, 2026-11-03:
**42 tests PASS in 33.027s**, run with the supplied Python runtime and
`-B auth_failure_test.py`. These exercise the state machine with a
fake Auth backend and actual loopback relay HTTP. They are not real GoTrue/SQL evidence.
The three newly added regression tests first reproduced five failing subcases:
failed delete receipt, failed managed receipt, missing final counter in ordinary
cleanup, missing reconciliation counter and inconsistent zero/session keys.
All now fail closed. The existing eleven-path matrix and unknown-outcome,
ownership, no-replay, no-refund and incomplete-mint tests remain passing.
An initial sandbox attempt failed due temporary-directory and loopback restrictions;
the authorized outside-sandbox rerun passed. No local Docker command is available
in this agent session. Actual PG17/GoTrue component execution and parent combined
CI remain pending. Previous appCI41474475311 does not prove these new files.
The parent coordinator reports CI3 confirmed 47 protocolcommands within one
migration apply and numeric zero temp before stopping;
it did NOT reach Auth. CI4 was announced as pending, not verified here. These
reports do not upgrade mock/loopback test results to actual GoTrue evidence,
full Auth cleanup PASS, or end-to-end admission. The 524-per-case local contract,
separate suffix accounting and hosted 2349 boundary remain unchanged.

Official documentation consulted: [self-hosted Auth API](https://supabase.com/docs/reference/self-hosting-auth/introduction),
[sessions](https://supabase.com/docs/guides/auth/sessions),
[signout](https://supabase.com/docs/guides/auth/signout), and
[changelog](https://supabase.com/changelog). No hosted project calls were made.
