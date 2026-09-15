# Package 6E-9 Proposal

Historical proposal; owner GO is recorded in Decision 0050 (2026-09-15).
Implemented scope and current evidence: PHASE6E9_TECHNICAL_REPORT.md.
The proposed object names and not-started language below describe the pre-GO plan.

## One Concrete Result

Build a server-authoritative, synthetic-only workflow sandbox for the accepted
dual-route contract. Test durable proposals, member confirmation, required human
coach approval, separate atomic activation and restore under real authorization
checks. No providers, real members, real plans, photos or production.
The 6E-8 browser selector is NOT an identity/entitlement mechanism.

## Proposed Data Flow

1. A dedicated test identity authenticates; the server derives its subject and
   eligible route from a versioned, server-owned synthetic eligibility record.
   A missing/revoked required coach blocks route A, never silently selects B.
2. The server reads only fixture catalog, intake, consent, source versions and
   mock safety disposition scoped to the test subject. Existing member tables
   are not inputs or write targets. A deterministic planner creates a candidate.
3. An edit makes a new candidate revision/hash and invalidates prior approval.
   Member confirmation binds exact bundle hash, subject, source versions and
   current consent. Route A independently binds valid coach authority/limits.
   Route B has no coach approval field or endpoint requirement.
4. A separate activation command rechecks everything transactionally, locks the
   current version, compares expected revision and a unique idempotency key,
   then appends a complete immutable version + audit + minimal outbox.
   Training/nutrition/recovery activate together or not at all.
5. Restore copies earlier content into a new candidate under CURRENT exclusions,
   consent and eligibility; history is not overwritten. New approvals required
   according to route. Notifications remain simulated in-app only.

## Proposed Components

- Frontend: separate synthetic test route with authenticated test personas, clear
  pending/rejected/conflict states and server-returned history; no client route
  assertion or local-authority fallback. Keep 6E-8 memory demo available separately.
- Edge: one scoped orchestration endpoint for synthetic commands, request allowlist,
  authenticated subject, bounded payload/time/rate, zero provider calls. No service
  secret in browser; no use of caller-supplied owner/trainer as authority.
- Database: NEW dedicated synthetic tables, concept names only:
  mock_coach_eligibility, mock_coach_sources, mock_plan_candidates,
  mock_plan_approvals, mock_plan_versions, mock_plan_events, mock_plan_outbox.
  Idempotency result belongs to the transaction; no partial success on retry.
- RLS/ACL: deny anon; separate own-member, authorized linked-coach and test-admin
  policies. Restrict coach access to the exact permitted proposal, not private
  chat, nutrition, photos or unrelated intake. No broad service-role client path.
  Revoke default grants and grant only required operations, including RPC execute.

These are future design names, not claims that these tables/endpoints exist.
The database enforcement approach follows official
[RLS and grants guidance](https://supabase.com/docs/guides/database/postgres/row-level-security)
and [database function guidance](https://supabase.com/docs/guides/database/functions)
(consulted 2026-09-14). Detailed policy/migration SQL is not created in 6E-8.

## Tests And Acceptance Criteria

- At least two distinct test members, their coach, an unrelated coach, anonymous
  caller and administrative fixture role. Prove permitted and denied reads/writes.
- A cannot apply before both approvals; B cannot inherit A's required-coach gate
  or bypass its own eligibility, member confirmation or source checks.
- Simultaneous apply/apply, apply/edit, apply/revoke, restore/apply, expired source,
  duplicate id with changed payload, stale version and cross-member commands.
  Exactly one whole version/audit/outbox transaction or zero, including fault injection.
- Restore creates a new monotone version. Old content and approval evidence stay
  intact. Changed allergies/exclusions or missing context may refuse restore.
- Purpose-specific test retention: O5 expires at first registration + 30 days,
  never renewed or hidden in another status. Plan/audit retention must have its own
  approved purpose/period; do not copy medical context into immutable audit.
- Network proof: zero provider, email, push, photo and production calls.
- UI re-login/reload verifies server persistence only for synthetic test rows.
  Dedicated fixture identifiers and pre/post evidence prove no memberdata change.

## Owner Choices Before GO

| Choice | Concrete recommendation | Why |
| --- | --- | --- |
| B1 Test scope | Dedicated synthetic identity/namespace only; additive staging migration after local SQL/RLS/concurrency proof | Tests actual authorization without touching member plans |
| B2 Independent eligibility | Versioned server-owned eligibility fixture now; do not equate client route selection, lost trainer or generic AI chat access with independent coaching eligibility | Prevents silent route escalation |
| B3 Activation unit | One confirmed training/nutrition/recovery bundle; unchanged components keep content/version lineage | Prevents partially active or unreviewed nutrition/recovery changes |
| B4 Human-coach review surface | Only training proposal + minimum goal/rule evidence; no implied access to private nutrition, intake or chat | Keeps existing consent and privacy boundaries separate |

Final mapping of real independent AI membership rights, validated coaching sources
and health gates remains a later explicit product/security decision, not a reopening
of D1-D12, O1-O5 or accepted earlier frozen choices.

## Migration, Rollback And External Gates

Potential later migrations: dedicated synthetic tables, constraints/indexes, RLS,
grants, narrow transaction RPCs and purpose-specific deletion jobs. None executed
or numbered now. Review staging-only target and migration history before that GO.
Rollback: disable only the new test endpoint/entry, revoke its scoped grants and
preserve synthetic evidence/version history; no drop/reset of member tables.
Schema removal only after explicit reviewed cleanup scope, never a blind down migration.

External AI calls: 0. Maximum external AI cost: EUR 0. No paid services.
Medical/nutrition/recovery criteria and source validation, native-language warning
review, privacy/legal retention and consent assessment remain open for real use.
Before external processing of real members: approved DPA, ZDR suitability/evidence,
DPIA/EU routing where required, scoped explicit consent, data minimization/deletion,
provider/cost kill switches and a separate owner GO. No such readiness is claimed.
