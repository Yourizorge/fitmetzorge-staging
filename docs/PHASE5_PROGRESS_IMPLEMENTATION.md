# Phase 5 Progressie - Technical Implementation

Status: OWNER MOBILE FORM PASS / UNIT-SWITCH HOTFIX LIVE / READY FOR OWNER RETEST

Updated: 2026-09-01

## Delivered Runtime

- Mobile-first member Progressie route and navigation.
- Primary goal, raw weight history and transparent seven-entry trend.
- Optional body measurements with immutable corrections and archive.
- Strength and training consistency from frozen normalized Training data.
- Descriptive Recovery and Nutrition context without cross-domain writes.
- Explicit insufficient-data state for running/conditioning.
- Contextual BMI with limitation copy; never a body-composition authority.
- NL/EN/DE and metric/imperial display using canonical kg/cm storage.
- Goal, weight and measurement dialogs with stable retry IDs and stale-write handling.

Trainer legacy Progress and `coach_workspaces.state` remain untouched. The member runtime has no progress-photo file input or competing 72-item/legacy data source.

## Database Artifacts

| Artifact | SHA-256 | Status |
| --- | --- | --- |
| `20260831153000_phase5_progress_foundation.sql` | `DEB29504DE883B6CB1F0573E7E60744A81BE878952C22F85E28D066BAF6661D6` | LIVE |
| `20260831161000_phase5_progress_unit_preference.sql` | `B0B83CFE565CB8D7A1A7E88C0097052B657E6A2C6CD9849450BB32DE5B07E8FB` | LIVE |
| `20260831163000_phase5_progress_revision_indexes.sql` | `D7434837E2D37B5F6EF54C3535A1D0D264D439EDA0B79A481553858C997744B7` | LIVE |
| `20260901170000_phase5_unit_system_constraint_fix.sql` | `77EF7C490A9430ECACB3C8BE2F9A3E021FDA391FD45BC7EE698891003B0C1177` | LIVE / CONSTRAINT ONLY |
| `20260831153000_phase5_progress_foundation_verification.sql` | `B1724EB814DF1F81AC9DF9FE09A4343FD6FC48E3D476BD293A6C9F91506DD4BE` | PASS 30/30 |
| `20260901170000_phase5_unit_system_constraint_fix_verification.sql` | `9424A357E08B4DAEB472BF8C171A6734136D10E3B302AD92BC45E48A3CFA4F69` | PASS 9/9 |
| `20260831_phase5_progress_transactional_e2e.sql` | `D83AC9FF74D1BAD17C4C2D68F8D04009E4C5A59967E9C266ECCF6FD0D5804DF5` | PASS / ROLLED BACK |
| `20260901_phase5_unit_system_transactional_e2e.sql` | `BE165BCEFCD0C33B8B3757FFA749AB9DA2C1C67869569E30E34F21BE4C1A51DB` | PASS / ROLLED BACK |

The four tables use own-user RLS. Browser writes are RPC-only. Authenticated table grants, DELETE policies, trainer policies and client-supplied ownership/entitlement authority are absent. Free history is 30 local calendar days; current Pro/AI/personal-coaching entitlements receive full history.

## Verification

- Read-only live verifier: PASS, 30/30.
- Transactional database E2E: PASS; zero retained fixtures.
- Phase 5 static suite: PASS, 116/116 including the assembled seven-patch bundle parse and live constraint guards.
- Responsive browser suite: PASS, 53/53 using the real app stylesheet rather than protective harness field CSS.
- Mobile 320x700 and 390x844: PASS for goal, weight and measurement dialogs, label/control separation, focus, feedback and horizontal overflow.
- Reduced-height keyboard-class viewport: PASS with active control reachable and no horizontal overflow.
- Tablet 820x1180 and desktop 1440x900 compatibility: PASS.
- Frozen Phase 1/2/3/Member UX and current Phase 4 gates: PASS.
- No polling, `MutationObserver`, reload workaround, browser service role, secret, production reference or AI call.

## Owner Gate

The owner real-phone functional test passed for opening the page, entering progress data and rendering the graph, and the follow-up mobile form/Dutch naming retest passed. Technical implementation and those functional passes do not equal final owner acceptance. A final owner phone retest remains required for persisted metric/imperial switching. Phase 6 remains outside scope.

## Staging Deployment

- Runtime/schema hotfix commit: `f96f9346174a636d71adb6fd1cd151d28c6c449b`.
- Cache version: `20260901-phase5-unit-switch1`.
- Live URL: `https://yourizorge.github.io/fitmetzorge-staging/`.
- `index.html`, `app.js`, `assets/phase1-foundation.js`, and `assets/phase5-progress.js`: HTTP 200 and byte-identical to the runtime commit.
- Live cache chain exposes the unit-switch hotfix version and no longer references `20260901-phase5-mobile-form1`.
- Production: untouched.

## Owner Mobile UX Hotfix

The original Phase 5 dialog grid kept two columns active at 390px and depended on generic `.field` styling. Long Dutch labels could therefore wrap into cramped cells and visually run into controls. The former browser harness supplied its own safe field and input widths, masking this real-phone failure.

The focused hotfix makes forms mobile-first with one column below 560px and progressive two-column enhancement above it. Phase 5 now owns label wrapping and line height, field/control min-width and max-width, 46px touch controls, visible focus, feedback containment, modal scroll reserve and heading wrapping. The measurements date occupies a full row and the unused spacer cell was removed. The Dutch user-facing navigation, title, loading and section error copy now consistently use `Voortgang`; English `Progress` and German `Fortschritt` are unchanged.

## Owner Unit-Switch Hotfix

Live PostgreSQL logs and metadata proved that `fmz_phase5_set_unit_system('imperial')` reached the database but failed because `user_settings_unit_system_check` still required `unit_system = 'metric'`. The Settings surface independently exposed only metric and hard-coded metric on submit. After another Progress write, a missing terminal rerender could also leave the visible unit buttons disabled.

The focused migration replaces only that named CHECK constraint with an exact `metric|imperial` allowlist. The column, default, existing rows, RPC body, grants, policies and RLS remain unchanged. Voortgang now exposes a labelled segmented choice with localized feedback; Settings exposes the same two choices and delegates to the shared Phase 5 setter. Both rehydrate authoritative state immediately. Canonical weight and length remain kg/cm, while all member-facing target, form, chart, history, measurement and strength values convert at render/input boundaries only.

Verification passed live metadata 9/9 and a two-member transactional E2E covering imperial save, dashboard hydration, metric round trip and cross-member isolation. The transaction rolled back every fixture; aggregate member settings counts were unchanged. Browser tests cover refresh persistence, repeated unit round trips without canonical drift, NL/EN/DE and phone/tablet/desktop layouts.

Database/schema changed: YES, named CHECK constraint only. Catalog/member data changed: NO. Edge Functions changed: NO. Production touched: NO. Phase 5 owner acceptance/freeze: PENDING final owner unit-switch retest.
