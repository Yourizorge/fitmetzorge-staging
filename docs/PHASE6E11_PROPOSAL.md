# Package 6E-11 Proposal

PROPOSED / NOT STARTED. Separate owner GO required.
No change to D1-D12, O1-O5, W1/W2 or accepted dual-route decisions.

## One Concrete Result

Version-bound, explicitly published SYNTHETIC platform sources for Route B,
using the tested managed-window lifecycle. This is not a trainer fallback and
not an autonomous training, nutrition or recovery policy. Route A stays frozen.

A controlled fictional catalog supports one deterministic workout example with
complete source provenance. A dedicated platform publisher appends a source;
B reviews, confirms and separately activates a new synthetic version. The
platform publisher does not approve the member's individual proposal as a trainer.
A changed or withdrawn source invalidates a pending confirmation.

## Data Flow And Components

1. Fixed registry grants a separate synthetic platform-publisher capability.
   No user_metadata authority, role switch or inherited ordinary trainer rights.
2. Publisher supplies immutable source ID/version/hash, purpose, validity,
   controlled exercise identities, kg OR lb, explicit sets/reps/weights and
   limits. No derived medical standards or implicit unit conversion.
3. Server binds the B participant, no-trainer relationship, window, consent fixture,
   exact source and base version. It rejects trainer-source IDs even if structurally
   similar. Missing/ambiguous/incomplete sources produce facts, never a partial plan.
4. Member confirmation and separate activation commit version/audit/receipt together;
   stale/conflicting/double requests fail or replay their exact prior receipt.
5. Restore is a new proposal/version with fresh member confirmation and separate
   activation; original provenance is preserved. No trainer step is introduced.
6. Expiry/revoke denies access; scoped cleanup proves removal, not just timestamp denial.

Frontend: a separate synthetic B source/proposal view, not normal-app integration.
Edge: a narrow, proof-protected staging-only command entry forwarding the actual JWT.
Database: later additive CLI migration for private platform source heads/versions,
publisher registry, exact B proposal bindings and immutable audit/receipts.
RLS/ACL: deny direct table access; SECURITY INVOKER wrapper and pinned private
transaction functions; source publisher cannot read unrelated A/B personal content.
Exact objects/migration timestamp are determined only after GO. No SQL is delivered
or applied by this proposal.

## New Owner Choices

| Choice | Concrete recommendation | Reason |
| --- | --- | --- |
| M1 Publisher authority | A separate, demonstrably synthetic platform-publisher identity with a narrow server grant; owner supplies its test alias before provisioning | Makes platform authority visibly different from trainer authority |
| M2 Catalog scope | One fictional workout catalog, three controlled exercises, kg/kg and lb/lb; no new nutrition/recovery progression | Tests provenance and activation before inventing broader coaching rules |
| M3 Version lifecycle | Publication creates an immutable source; change/withdrawal requires a fresh B proposal and member confirmation, then separate activation | Preserves the already accepted independent route without stale consent |

No previously accepted choice is reopened. These are implementation-scope proposals,
not accepted results or medical/legal validation.

## Targeted Acceptance Criteria

- Positive NL/EN/DE example cites actual source, plan and exact changed values.
- A source cannot enter B; ordinary trainer cannot publish platform sources.
- Unlinked/foreign/anonymous/expired actors, unexpected trainer link, withdrawn consent,
  safety fixtures, stale sources/versions and incomplete sets all fail closed.
- Exact same-key retry, changed-body replay, concurrent activation and mid-transaction
  failure prove atomicity; restore appends rather than overwrites.
- Refresh and fresh login preserve server status. Mobile/tablet/desktop, light/dark
  and all three languages show explicit confirmation versus separate activation.
- New fixed participants cannot gain ordinary-app privileges or real member access.
- Existing runtime and frozen sources remain byte-identical unless a separately
  approved integration exception is necessary. Private tests stay unavailable on Pages.
- CLI history matches and dry-run is empty; existing-cohort hashes remain unchanged.

## Rollback, Cost And External Gates

Revoke only the new B window/capability, disable its isolated entry, then perform
audited exact-fixture cleanup. Retain additive migrations and immutable evidence;
no down-migration, database reset or change to existing member schemas.

External AI calls: 0. Maximum external AI cost: EUR 0.
No paid service, email, provider or real member processing is implied.
Before eventual real coaching: authentic source authority, approved recommendation
content, appropriate medical recovery criteria, privacy/legal retention and rights,
language review, explicit consent/entitlements, applicable DPA/ZDR/DPIA/EU-route,
provider/cost controls and a separate integration GO. Synthetic success replaces none
of these. Medical blockers do not prevent this non-medical synthetic workflow test.
