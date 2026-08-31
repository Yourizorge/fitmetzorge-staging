# Phase 5 Progressie - Architecture And Packages

Status: TECHNICAL PASS / READY FOR OWNER TESTING ON STAGING

Target repository: `Yourizorge/fitmetzorge-staging` / `main`  
Target Supabase: `mokxyyullfhkfalopbzd`  
Production: FORBIDDEN

## Readiness Audit

The live staging database has no normalized Progress tables. Member Progress currently uses legacy weekly values in `coach_workspaces.state`; the old member detail also accepts local image files as data URLs. That path is not suitable as the Phase 5 source of truth and is not a safe photo-storage architecture.

Reusable frozen sources:

- `user_settings.unit_system` for metric/imperial display.
- `user_onboarding` for height, current onboarding weight, primary goal and target weight bootstrap context.
- `entitlements` for current Free versus Pro/AI/PT access.
- `workout_sessions` and `workout_set_logs` for authoritative strength and adherence summaries.
- `recovery_logs` for descriptive recovery/activity context.
- `food_logs` and `food_log_items` for descriptive Nutrition context.
- Existing auth/session, NL/EN/DE, mobile-safe navigation and runtime patch architecture.

Trainer legacy Progress remains intact. No normalized trainer policy is introduced in Phase 5.

## Package 5A - Normalized Progress Foundation

Add own-user, RPC-only normalized storage for:

- Progress preferences and IANA timezone.
- Primary goal configuration.
- Weight revisions in canonical kilograms.
- Body-measurement revisions in canonical centimetres.

Writes derive ownership exclusively from `auth.uid()`. Stable request UUIDs, per-user transaction locks, immutable superseded revisions, optimistic timestamps and archive-only correction protect retries and history. Tables have RLS, own-user defense-in-depth policies, no DELETE policy, no trainer policy and no browser table privileges. Authenticated members receive only the minimum reviewed RPC EXECUTE grants.

Free receives a useful but bounded 30-day Progress window. Current active Pro, AI and personal-coaching entitlements receive full retained Progress history. Missing, future, expired or inactive entitlements resolve to Free. The boundary is server-enforced and isolated for later commercial configuration.

## Package 5B - Mobile-First Progress Experience

Replace the member-facing legacy Progress detail with one normalized Progress surface:

1. Goal progress and current trend.
2. Quick weight entry.
3. Body measurements and history.
4. Strength progress from completed set logs.
5. Training consistency.
6. Descriptive Recovery/Activity and Nutrition context.
7. Truthful running/conditioning insufficient-data state until an authoritative activity contract exists.

Charts remain compact, mobile first and accompanied by accessible tables/text. Raw values remain visible; the smoothed trend is explicitly labelled as a seven-entry moving average. Metric and imperial are display choices only; storage remains kg/cm. NL/EN/DE labels, locale-aware numbers/dates and 390x844, 320x700, tablet and desktop compatibility are required.

The old visible member photo inputs are removed. The internal legacy values remain untouched for trainer compatibility and are never merged into normalized records.

## Package 5C - Staging Verification And Deployment

Required gates:

- Exact migration and read-only verifier.
- RLS, ACL, function security and cross-member isolation.
- Entitlement-window tests.
- Idempotent retry, stale conflict, archive and revision-history tests.
- Frozen Phase 1-4 and Member UX regression suites.
- Dedicated Phase 5 static and browser/responsive suites.
- Live asset HTTP and byte-identity verification.
- Clean staging repository and synchronized documentation.

## Progress Photo Privacy Gate

Photos are not part of the first normalized Phase 5 runtime package. No public bucket is allowed and no data-URL value becomes a normalized photo record. A later reviewed slice must define a private bucket, own-user object paths, signed access, explicit optional upload consent, deletion and consent-withdrawal behavior, trainer-access rules, retention, and a separate AI-analysis opt-in. Staging currently has no Storage bucket, so deferring the photo runtime avoids introducing an incomplete privacy contract.

## Rollback And Preservation

Package 5A is additive. If frontend activation must be reverted, remove the Phase 5 loader reference and retain normalized rows. No legacy workspace data is deleted or rewritten. Database objects are forward-fixed through append-only migrations; owner records are never bulk removed. Production remains untouched.

## Technical Completion Record

- Foundation migration SHA-256: `DEB29504DE883B6CB1F0573E7E60744A81BE878952C22F85E28D066BAF6661D6`.
- Unit-preference migration SHA-256: `B0B83CFE565CB8D7A1A7E88C0097052B657E6A2C6CD9849450BB32DE5B07E8FB`.
- Revision-index migration SHA-256: `D7434837E2D37B5F6EF54C3535A1D0D264D439EDA0B79A481553858C997744B7`.
- Read-only verifier SHA-256: `B1724EB814DF1F81AC9DF9FE09A4343FD6FC48E3D476BD293A6C9F91506DD4BE`; live `overall_pass=true`, 30/30.
- Transactional E2E SHA-256: `D83AC9FF74D1BAD17C4C2D68F8D04009E4C5A59967E9C266ECCF6FD0D5804DF5`; PASS with rollback and no persisted fixtures.
- Runtime SHA-256: `84C2F8709ACFE11C8F768B21979030B3B5A68C61F6B6266E1AF2C65A119DADFF`; live GitHub Pages identity verified at runtime commit `cb1e926` and cache `20260831-phase5-progress1`.
- Static suite: PASS, 85/85 including the assembled seven-patch bundle parse. Responsive browser suite: PASS, 19/19.

Owner acceptance and freeze are intentionally not recorded. The next gate is real-phone owner testing; Phase 6 remains not started.
