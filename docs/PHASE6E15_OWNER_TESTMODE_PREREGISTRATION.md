# 6E-15 Owner Test Mode Preregistration
2026-09-30, before the visible test-mode implementation.
Baseline e942b06e30ae47b3128a800147100c0e22eaa4b3.
Owner acceptance is pending; no freeze. Hosted 6E-11 SUPPORT HOLD SU-487979.

Only an isolated UI/test adapter calls the existing unchanged 6E-15 model.
No catalog, model, fixtures, Route A, frozen source or runtime changes.
Preserve previous receipts, results, working changes and historical evidence.

Nine visible cases, also accessible through previous/next:
1. Complete intake: pending proposal, no activation.
2. Missing goal: incomplete refusal, no proposal, no state change.
3. Nuts/dairy allergy and tofu exclusion; exclude squat as an exercise:
   supported clean plan; attempted nuts/yogurt substitution rejected atomically;
   show actual product/exercise absence, not merely a preset green label.
4. Current health complaint: safety refusal, no physical plan.
5. Cable machine without catalog rule: explicit missing-rule refusal.
6. Changed days invalidate old confirmation; stale activation refused.
   Subsequent source conflict prevents a new proposal.
7. Withdrawal: no new build, intake processing or activation; old concept marked
   unusable, without pretending that old evidence/history was deleted.
8. Repeated confirm/activate: exact replay, fresh duplicate; only one version.
9. Restore version1 after version2: new confirmation and separate activation;
   version3, versions1/2 unchanged.

PASS is a calculated local result, not owner acceptance or medical validation.
An unexpected model result, absent check or visible/model mismatch must show
AFWIJKING. Manual editing invalidates the previous test badge.
Each scenario resets only its fictional in-memory state; simulated approvals in
cases8/9 are explicitly disclosed. Refresh has no persistence.
Tests: unchanged245 contract tests; new unit negative-control/corruption tests;
all9 buttons + guided navigation + labels, errors, DOM-derived results,
keyboard/mobile/tablet/desktop and light/dark; old463 browser checks.
Pre/post Pages:102 existing assets unchanged; all new demo files match Git;
private paths remain404. No Supabase, accounts, JIT, Auth, migrations or cleanup.
