# Package 6E-10 Preregistration

IMPLEMENTATION GO / NOT OWNER-ACCEPTED. Baseline 53b7d36a9dd45ba2c6f0326f5f563304f2e5583f.
Only staging mokxyyullfhkfalopbzd / Yourizorge/fitmetzorge-staging main.
6E-9 accepted/frozen; source hashes preserved. No existing runtime changes.

Before implementing source/window logic, required test expectations:
- Anonymous, real/ordinary non-enrolled principal and missing/revoked session: deny.
- Member source creation, unrelated trainer, other workspace, forged actor/route/source
  revision, direct REST/write and missing proof: deny.
- Sources: immutable ID/version/hash, explicit valid-from/until, matching workspace/trainer,
  kg/kg and lb/lb only, no conversion, explicit complete rules/sets, separate effort values.
- Missing rules/step, ambiguous W1, W2 non-fitting full step: factual blocked result.
- RIR zero valid versus null; RPE zero invalid, never treated as missing.
- Source withdrawn/expired before review: block; source change after either approval: stale.
- New proposal has new source binding and empty approvals; old proposal not mutated.
- No A application without exact member and trainer approvals plus a separate apply.
- Concurrent writes and same-key changed payload: conflict; exact retry: one receipt.
- Restore creates a new plan version and retains its original source provenance.
- B never consumes A sources and an unexpected trainer relation denies B access.
- Windows: prepared cannot read fixtures; start inclusive/end exclusive; <=24h hard bound;
  revoke immediately denies old JWT; no expired reactivation; new test = new window UUID.
- Only registry-bound synthetic IDs/roles; concurrent windows cannot mix active fixtures.
- Duplicate activate/cleanup idempotent, cleanup removes only this window's synthetic data.
- Fault before receipt must roll back source/plan/approval/audit changes together.
- Published NL/EN/DE, light/dark and mobile/tablet/desktop workflow; fixed source v1->v2
  stale path plus fresh proposal/approvals/application/revoke/history.
- All old runtime/frozen hashes preserved; additive CLI migration identity and empty final
  dry-run; before/after real-row aggregate hashes unchanged; advisors and fresh local test.

Operator decision: existing synthetic A-trainer only, capability limited to the three
manifest-proven identities. Control-plane window metadata/activate/revoke/cleanup requires
this explicit server grant and auth.uid/session, never a client role switch. Participant
source/plan data requires an active window. A normal trainer is not an operator.

No medical criteria, autonomous Route B platform source or external provider is introduced.
Synthetic trainer explanations are bounded and are not consent to store real health data.
