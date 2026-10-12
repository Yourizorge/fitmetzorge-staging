# 6E-11 temporary Auth identity guard

Owner GO: 12 October 2026. Baseline `fea115915286d22eae81b1a7cc4637860599ed78`.
Only staging `mokxyyullfhkfalopbzd`; migrations remain 43/43.
Status: LOCAL/CI CANDIDATE, not hosted admission or owner acceptance.

The owner's temporary-guard GO is the narrow exception to the earlier controller
design's managed-schema-trigger prohibition. It does not permit any other Auth
schema change or managed function replacement.

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

## Hosted Lifecycle Admission

Before token issuance, the native adapter must prove the guard's install/remove
lifecycle on the actual staging ownership model. This canary does not call Auth
or execute workflows, create fixtures, or scan member rows. It uses the exact
registered UUIDs, a unique guard schema, a 180-second immutable guard deadline,
one verified session-pooler connection, owner JIT capped at 300 seconds, and no
retry. The existing metadata reader measures its own query load; no full table
fingerprints are added. Project/migration binding must confirm exactly 43/43.

Maximum 128 SQL commands, including 40 commands reserved before installation
for independent safety inspection/removal. The main path cannot consume this
reservation. Before/after catalog measurements bind existing Auth/private
functions, triggers, RLS policies and ACLs. Only one schema, one function and
three triggers may appear; the original catalog must be restored. No row-write
or full protected-data PASS is inferred solely from a catalog comparison.

Lost installation acknowledgment is handled by source-bound inspection, not
repeating installation. Safety removal remains active after a controller stop
or evidence-storage failure. Minimal read-only safety inspection does not reuse
the stopped load-admission gate. Missing durable safety evidence remains NO-GO
even when the guard is demonstrably removed; it never prevents that removal.
The lifecycle was tested with the native PG17
single-statement transport as well as disposable Supabase CI. A lifecycle PASS
is not admission for unimplemented or untested Auth/workflow composition.

CI run 38262806969 was green, but its downloaded log export failed the declared
SHA-256 for advisors.json in both copies. The originals are retained; this run
is not used as complete admission. No hosted mutation followed. Subsequent CI
uses the pinned official upload-artifact action, a one-day artifact, GitHub's
archive digest and a per-file manifest. Local negative tests reject wrong run,
attempt, HEAD, expired artifact, archive/file hashes and unsafe/extra paths.
