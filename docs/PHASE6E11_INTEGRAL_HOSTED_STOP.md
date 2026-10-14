# 6E-11 Integral Hosted Stop

## Outcome

**NO-GO. No owner window. The single permitted hosted attempt has been used.**
No second attempt, migration, Auth issuance, workflow mutation or fixture cleanup
was started after this stop. Older 112 valid pairs and incomplete step 113 retain
their original status.

Admitted source: `92153c45ab214a94789b8cd345389f04229a74c3`.
CI: `38584249412`, complete clean 44/44 and real local Auth/controller/Route A/B
with three injected failure paths. Archive SHA-256:
`16d51cb1e177b7c28ac2cbcdac1372c4cee872e94532def994df5f01f7b6bbf0`.
Candidate digest:
`3f0cc6fad55ca89b91e2d32bf2c34c1ab26214822c350c4f65a0a5a168377fe1`.

Reserved run: `32321f17-07f1-4f3d-aa4b-3218bc7368a4`.
The local run-directory lock remains intact. Historical error receipts are not
modified by the later offline diagnostic correction.

## What Was Actually Proven Hosted

- Project/owner binding and applied SSL enforcement passed.
- The existing official Connect session-pooler route used temporary owner JIT,
  port 5432, verified CA/hostname and `jit=true`.
- Explicit read-only preflight completed four recorded commands: BEGIN, bound
  identity/read-only/TLS metadata, migration history and ROLLBACK.
- The live history contained 43 migrations, ending at `20261012104331`.
- The initial hash stream reached its cursor DECLARE and the following numeric
  statistics sample. It stopped before its first FETCH and before M44 application.
- JIT was revoked, disabled and read back with **zero mappings**. SSL enforcement
  remained applied. The lifecycle confirms no temporary guard/audit installation
  had been reached.

## Exact Failure And Evidence Limit

`integral_stream.utility` rejected `stream_utility_attribution`: after excluding
the reader, the changed numeric query counters did not match exactly one utility
call. The retained stack locates this at the first cursor DECLARE.

The old implementation saved numeric pairs only after successful attribution.
It did not retain the rejected before/after samples. Therefore this attempt
does **not** prove whether another postgres-role query ran concurrently, utility
tracking differed, or the observer binding itself was wrong. Do not claim
background interference, collector temp writes or zero own temp writes as fact.

The outer error receipt was recorded after ROLLBACK, masking the original phase
in one field; the nested stack preserves the location. The complete failed-run
command ledger was also not persisted. Four preflight commands are directly
recorded; thirteen total protocol commands follow from the executed control path,
but that derivation is **not** a complete measured ledger.

There is no complete protected before/after fingerprint pair. Read-only
transaction control and the stop before migration/Auth/workflow writes show that
this code did not perform application or member mutations. They are not a new
global databehoud-PASS or proof that no unrelated activity occurred.

No M44 CLI apply or dry-run was reached. Local 44/44 CI must not be reported as
hosted 44/44. No full hosted Route A/B, audit/delete or cleanup PASS is claimed.

## Offline Correction And Next Gate

The subsequent offline correction saves both numeric samples, fixed SQL hash,
reader query ID, observed call deltas and attribution status before deciding.
It retains the failing phase before rollback and preserves the incomplete
protocol/budget ledger even on NO-GO. No extra SQL, automatic retry or relaxed
attribution condition was added.

Local regression explicitly injects two competing utility counters: both samples
survive, the operation is rejected, ROLLBACK remains last, and no hash page is
read. The earlier stop is not retroactively promoted to PASS.

Corrected offline composition CI `38586145759` passed at
`f2fda85fed087b7a0aa36a2cc3d0f8876b4d5a6d`: clean44, 161 Python and 131 Node
endchain tests, 18 real local Auth contracts, the complete 71-pair workflow and
three real injected failure paths. Candidate digest:
`b8173d59b979cfcb311949f2faad3ed26001347cfbbafd01cc388fbf9d98643a`.
Archive digest:
`4108e0bc42fdef1702d415150b9eaddf4d208f6b4b6f7c828a7621247a690c9e`.
Its additional numeric evidence produces a bounded 43,155,377-byte expanded
archive with 1,341 files, largest file 1,339,691 bytes. A local collector
correction accepts at most 48 MB expanded while retaining the original 30 MB
compressed, 1,400 paths and 2 MB/file limits. The original downloaded archive
was preserved; recovery used a new directory and verified every manifest hash.
Those later collection-helper changes have eleven passing local tests and are
not falsely included in the earlier CI source admission.

## Complete CI Phase Capacity

| Phase | Commands |
| --- | ---: |
| Preflight | 4 |
| Migration plus direct metadata and observers | 42 |
| Protected baseline | 51 |
| Fixture setup | 33 |
| Guard and metadata observer | 13 |
| Auth | 318 |
| Controller | 286 |
| Route A | 191 |
| Route B | 286 |
| Restore | 54 |
| Scoped measurements | 126 |
| IO monitoring | 97 |
| Cleanup | 633 |
| Final checks and dry-run | 61 |
| Durable closure | 1 |
| Normal capacity | 2,196 |

Every prefix has a reserved safe suffix. The worst registered combined path is
2,207; the successful local execution actually used 2,154. These are CI values,
not the missing full hosted command ledger.

The smallest next hosted decision is one separately bounded read-only
utility-attribution diagnosis with the corrected evidence storage, no M44,
Auth or workflow writes. It must obtain its own attempt authorization; the
used full-run allowance is not silently reused. If attribution is unresolved,
all dependent hosted mutations remain blocked.

Independent local server-integration work continues. Its future hosted release
is described separately in `PHASE6E_SERVER_RELEASE_PACKET.md`.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.
