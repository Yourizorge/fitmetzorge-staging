# Synthetic 6E-9 Backend Boundary

TECHNICAL PASS / READY FOR OWNER REVIEW - SYNTHETIC BACKEND ONLY.
Actual hosted Auth/Edge/REST, SQL atomicity and published browser evidence are in
docs/PHASE6E9_TECHNICAL_REPORT.md. Test accounts/fixtures are removed; flag is off.
The new public entry is separate; accepted 6E-8 and normal app bytes are not edited.
Frozen deterministic A/B models are bundled verbatim and replay only allowlisted
synthetic commands. No free text, uploaded images, custom goals or provider inputs.

The Edge handler verifies the access token with Auth, forwards that user's JWT to
PostgREST and adds an isolated server-only proof secret. Public RPC wrappers are
SECURITY INVOKER. The private SECURITY DEFINER helpers revoke default grants and
require auth.uid(), a live auth.sessions binding, the server proof, standard-off
feature flag, dedicated expiring synthetic workspace and current trusted profiles.
No user_metadata, browser actor/route fields or service-role client writes.
Private helper privilege is necessary for append-only version transactions while
authenticated callers have NO direct table write grants. RLS additionally protects
minimal audit/notices; trainers receive only Route A training data, never B intake.

SQL locks each subject, binds source/consent/profile/eligibility versions, exact
candidate hash, member approval and required trainer approval. Apply is separate;
version + audit + notice + idempotency result commit together. Frozen Edge planner
is a trusted computation boundary, not a browser-supplied result. Direct RPC without
server proof fails even with a valid JWT. No assertion of real trainer provenance:
only explicitly provisioned synthetic profiles use the existing 6D-0 authority.

All test subjects expire within 24 hours, with exact cleanup after tests. O5 records
have independent first-registration expiry and earlier unnecessary deletion; no
retry extension or health-copy audit. No permanent clinical recovery service.
