# 6E-9 Owner Retest Window

Status: PREPARING / NOT OWNER-ACCEPTED. Baseline c7b44357a5e56b86a9b0a38b46e4739aeacf7a07.

The owner approved exactly three Gmail plus aliases and the narrow demo-login
compatibility change. No server authority, role model, migration, Edge source or
functional workflow contract changes. All three identities must be NEW. Existing
identities at these addresses cause a stop, never an update or role conversion.

## Provisioning And Bounds

The isolated owner-window runner reuses the existing fixed-project broker,
Auth password login, proof-secret gate, private subjects, server roles and existing
published browser suite. It creates three profiles, two workspaces and synthetic
workflow records only. Route B is first tested as an ordinary newly authenticated
principal WITHOUT a workspace, then enrolled. No real account is used for denial tests.

Expiry is fixed once, at database time plus 23 hours 59 minutes, never extended by
login, refresh, commands or mail delivery. The existing 24-hour constraint is unchanged.
Expired-session denial is exercised by temporarily expiring only these two new
workspaces and restoring their ORIGINAL deadline. No migration or expiry bypass.

Only coach-backend-demo/app.js changes publicly: the login allowlist is exactly the
three approved aliases. Authorization remains server-derived from auth.uid(), sessions,
trusted profile role/link, subject membership, consent, versions, proof and expiry.
The global test switch is enabled only with exactly these two workspace memberships;
it does not enroll other users. No editable metadata grants access.

## Secrets And Mail

Passwords are random and held only in process memory for verification. Only three
standard recovery emails are requested, after the checks, using the existing staging
password-setup route. No passwords, tokens, session data or recovery links are logged
or written. The existing Auth recovery TTL is 3600 seconds; this is separate from the
workspace deadline. No SMTP/provider settings change. Receipt records mail attempts,
not delivery claims. Owner receipt and physical phone use remain unverified until reported.

On success the broker explicitly retains fixtures/proof. On failure it disables access
but does not delete fixtures. The nonsecret receipt is kept in ignored
supabase/.temp/phase6e9-owner-window.json for exact-ID cleanup after the owner test or
expiry. No automatic cleanup on successful process exit. Server expiry does not imply
physical deletion; cleanup remains a separate bounded operation, never a broad delete.

## Verification And Owner Flow

Preexisting row fingerprints are compared excluding ONLY the three newly created profile
IDs and the two new synthetic audit/notice workspaces. All other public/AI/legacy business
tables remain included. Entire migration records are compared, not just their count.
Official migration list and db push --dry-run are also required.

The existing published browser matrix exercises real test Auth/Edge/RLS: Route A
member acceptance, trainer approval, separate apply; Route B independent confirm/apply;
restore as a new version, explicit lost-response retry, refresh and relogin. All inputs
are synthetic. Browser layout checks emulate mobile/tablet/desktop, not a physical phone.

Audit history is NOT reset after internal tests. The owner receives an A restore proposal
awaiting member acceptance and a B candidate awaiting confirmation. This uses the existing
workflow; it does not fabricate a new initial version. An A rejection/block is terminal
in this existing design: test it LAST. Refresh does not undo it or create a fresh proposal.
Stale version testing uses two pages: update one, then attempt a decision from the older
page. No client-side admin/injection controls are added.

1725 existing contract/frozen regression tests passed before opening. The live window
receipt and final delivery section record actual subsequent outcomes. None implies
owner acceptance/freeze, live AI permission or a start of 6E-10.
