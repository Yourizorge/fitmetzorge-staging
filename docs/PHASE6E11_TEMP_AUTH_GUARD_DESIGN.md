# 6E-11 temporary Auth identity guard

Owner GO: 12 October 2026. Baseline `fea115915286d22eae81b1a7cc4637860599ed78`.
Only staging `mokxyyullfhkfalopbzd`; migrations remain 43/43.
Status: LOCAL/CI CANDIDATE, not hosted admission or owner acceptance.

## Authority And Lifetime

Exactly the three pre-registered UUIDs AND the three exact existing test aliases
are required. No prefix authorization, new account, password write, Auth setting,
managed function, RLS change, ordinary account or production operation.

A unique private schema owns one SECURITY INVOKER trigger function. Three
temporary triggers attach to auth.users: INSERT, DELETE and identity-column
UPDATE. The function uses only OLD/NEW and immutable arguments, not private
table access. All direct execution privileges are revoked from PUBLIC, anon,
authenticated and service_role. No Data API exposure or new role is required.
The authoritative identity remains auth.users.id plus its exact email and
non-SSO status. Existing profile/registry locks preserve application relations.

Installation validates all three accounts and address uniqueness under a short
NOWAIT DDL lock, in one transaction. Missing accounts, conflicts, another guard,
or inability to acquire the lock abort installation without residual objects.
INSERT of a protected UUID/address, DELETE of a protected account, or changing
its UUID/email/SSO binding are denied. Necessary token/last-sign-in updates are
allowed; unrelated rows are not changed by this guard.

The database sets an immutable expiry no more than 600 seconds after creation.
No renewal. Expired triggers become inert; the controller must refuse issuance
unless the exact live schema/function/triggers and UUID/address mapping are
attested in its dedicated session. No issuance in the final 60 seconds. An
aborted/unconfirmed Auth request is NO-GO, never retried or promoted to PASS.
No token from a failed/expired request is returned or used. No claim that client
cancellation rolls back Auth: its scoped after-state must still be measured.

## Unconditional Safety Removal

Safety removal is separate from fixture cleanup and run success. A finally path
closes token issuance, verifies the recorded guard identity/definitions and its
exact three dependent triggers, then drops only its own function (CASCADE to
those verified triggers) and its now-empty schema (RESTRICT). Unknown dependencies
or changed objects are not deleted. Original schema/object/ACL fingerprints must
match afterwards. No other Auth trigger/function is replaced, disabled or removed.

The existing role has TRIGGER on auth.users but is not its owner and cannot
CREATE in auth. This is why direct DROP TRIGGER is not assumed available. Removal
must be proven locally and in real Supabase CI with equivalent ownership first.
The guard carries no secrets and creates no accounts. Temporary JIT is revoked
independently. Fixture cleanup still requires its normal complete proof pairs.

## Preregistered Tests

1. Exact valid three-account binding; missing account and swapped UUID rejected.
2. Duplicate/case-conflicting address and SSO identity rejected.
3. Concurrent email, UUID and SSO changes rejected; DELETE and replacement INSERT rejected.
4. Recovery-token and last-sign-in updates remain possible from Auth role.
5. Unrelated synthetic account INSERT/UPDATE/DELETE behaves unchanged.
6. No direct client function access; fixed search_path; invoker, not definer.
7. Expiry cannot extend; controller denies missing/expired/tampered guard.
8. Aborted issuance always releases locks, stops the run and invokes safety removal.
9. Removal restores original catalog/ACL without member or fixture deletion.
10. Unexpected function/trigger dependency blocks broad deletion.
11. Full new source-bound controller CI; old admission cannot authorize new code.

## Documentation Review

Reviewed official [Auth architecture](https://supabase.com/docs/guides/auth/architecture),
[user management](https://supabase.com/docs/guides/auth/managing-user-data),
[trigger troubleshooting](https://supabase.com/docs/guides/troubleshooting/dashboard-errors-when-managing-users-N1ls4A),
[PG17 locking](https://www.postgresql.org/docs/17/explicit-locking.html) and
[Supabase changelog](https://supabase.com/changelog).
Managed Auth columns/indexes can change; validate the actual shape and do not
change existing objects. Trigger failures can block Auth, hence mandatory
concurrency, outside-scope and removal tests. The 12 October TLS cipher notice
does not change direct/pooler connections or justify weakening HTTPS/TLS here.

No hosted Auth/workflow proof is implied by a local/CI pass. Historical missing
pairs remain missing. 6E-21 remains unaccepted; no JARVIS changes or handoff.
