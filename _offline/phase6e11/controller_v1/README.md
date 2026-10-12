# Synthetic controller candidate

Status: LOCAL/CI COMPONENT PASS; HOSTED WORKFLOW NO-GO.
This directory is excluded from GitHub Pages. It is not an application Edge
entry point, and must not be deployed by pointing an Edge Function at it.

## Implemented

- Separate exact-run GitHub OIDC verifier; no reuse of the read-only audience.
- Fixed-manifest identity, role, workspace and operation checks.
- Durable one-shot admission and ordered before/action/after/validated states.
- Empty, incomplete and stopped runs cannot be closed as complete.
- Metadata-only Auth helper for the three existing synthetic accounts. Tests
  use stub Auth responses, not live logins. No email is sent by the helper.
- Independent workflow receipt/write-multiset validation, including DELETE
  tombstones, request/session/transaction binding and negative write evidence.
- Additive M43 private proof storage; no new RPC or grants to client roles.
- Local PG17 and clean 43-migration Docker CI controls.
- A separate 155-table adapter using the frozen hash reducer and identical
  row, page, memory, statement-time and zero-spill limits.

## Deliberately not claimed complete

There is no deployed mutating controller. The final server-compiled hosted
action manifest, fixture prepare/activate adapter and Auth scoped-measurement
composition have not been executed end-to-end. The 45 workflow assertions run
the existing product functions locally with Auth stubs; they do not prove
hosted session authorization or fixture lifecycle writes.

Hosted Auth, Route A/B, activation, restore, rejection, conflict, duplicate,
cleanup/DELETE and final preservation proof remain pending. They require real
synthetic service requests and complete durable pairs, not mocked receipts.

The first M43 precheck stopped at the frozen 153-table cap before row streaming.
The explicitly corrected attempt stopped at JIT lease admission, HTTP 406,
before opening a database connection. Both are immutable incomplete attempts.
No migration, Auth or application write was made. JIT is disabled with zero
mappings. The old helper did not preserve which JIT subrequest received 406;
`lease_trace.py` and its tests prevent that diagnostic loss in a future
separately admitted attempt. Do not invoke it as a workaround or automatic retry.

## Execution guards

`install.py` verifies an exact CI source receipt and immutable attempt markers.
Its two admitted attempts are consumed. A bare rerun cannot create a third
lease. Do not delete or edit the markers to resume. Diagnose the platform
refusal and preregister a new bounded attempt first.

The workflow canary remains at one collector / 128 commands / three cycles /
zero automatic retries. The separately documented migration installation cap
does not change that canary cap. Never load credentials, real users or data
into tests. Never change migrations 1-42 or historical evidence to pass a test.

The owner window remains closed. No owner acceptance, freeze or 6E-12 server
integration follows from these component tests. 6E-21 remains unaccepted.
