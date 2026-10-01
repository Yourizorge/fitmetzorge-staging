# 6E-16 Status, Architecture and Test Addendum
2026-10-01. Offline Route B training-rule contract; ownerreview pending.

This additive current-status document accompanies BUILD_STATUS.md,
MASTER_BUILD_PLAN.md, ARCHITECTURE.md and TEST_MATRIX.md without rewriting
their preserved work-in-progress or historical claims. Roadmap review found
no conflicting16 package. The explicit owner GO now authorizes this package.

- 6E-15: COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE/SYNTHETIC ONLY.
  Owner physically accepted all nine guided scenarios and Q1-Q3; see
  PHASE6E15_FREEZE_RECEIPT.md and its21-source hash manifest.
- 6E-16: local technical checks PASS; final Pages proof in
  PHASE6E16_PUBLICATION_RECEIPT.md. READY FOR OWNER REVIEW after that PASS.
  No automatic owneracceptance, freeze or17 start.
- 6E-11 hosted: SUPPORT HOLD SU-487979. No connection, Auth, JIT, migration,
  Edge, database test or fixturecleanup performed. Whole Phase6E incomplete.

## Architecture

New public isolated training-rules-demo/{catalog,model,fixtures,copy,review,app}.js,
index.html and demo.css; private harness in _offline/phase6e16. Read-only imports
are frozen8 exercise identities, frozen15 safety data, frozen14 styling and
frozen12 brand image. No change to Route A, trainer rules, runtime or0-15 sources.
Memory-only simulation, refresh resets; CSP connect-src none; no local/session
storage, cookies, IndexedDB, network provider, live authority or automatic action.

The catalog carries source/rule IDs and versions, effective/expiry dates, exact
exercise identities and equipment, goal, experience, role/type, sets/reps/rest
ranges and steps, optional independent effort targets, layout, timing budget,
reps-step metadata, alternatives and a reason code. Twelve rules cover three
goals x two experience levels x two roles. Missing or multiple applicable rules
block; precedence is not invented. Full catalog snapshot binds every plan.

Synthetic example values, NOT training advice or expert-approved norms:

| Goal / experience | Main exercise | Supporting exercise |
|---|---|---|
| Fitness / beginner | 2 sets,10 reps,60s rest; sets2-3 | 1 set,12 reps,45s rest; sets1-2 |
| Muscle / experienced | 4 sets,10 reps,90s rest; sets3-5 | 3 sets,12 reps,60s rest; sets2-4 |
| Strength / experienced | 4 sets,5 reps,120s rest; sets3-5 | 3 sets,8 reps,75s rest; sets2-4 |

Two or four sessions; declared available days remain distinct from chosen days.
Supported budgets:10/15/30/45/60 minutes. Day edits require an available unused
day. Exercise edits require matching role/type/equipment and respect exclusions.
Favorites prioritize only eligible choices; deterministic selection is not a
claim to produce an optimal program. Intake, goal, experience, equipment or
source changes invalidate the pending assessment/confirmation, not old versions.

Time estimate in seconds:180 + sum(45 + sets*reps*3 + (sets-1)*rest).
Example totals per session:426,888 and912 above. An edit to3x11 with75s rest
gives555s in the beginner first session. This is transparent planning arithmetic,
not measured duration, exertion, fitness, recovery or medical safety evidence.
Overbudget/out-of-range/off-step edits reject atomically; no silent clamping.

RIR0 remains valid; RIR and RPE are independent optional self-report targets.
Historical effort can remain missing, separately from zero. No inference of
capacity, health or start load. New load stays null even with a history record.
kg and lb are accepted as original units; switching requested planunit NEVER
converts, rounds or relabels old20kg to20lb. The source20kg remains visible.
Progression step1 rep is explicit catalog metadata, NOT an executed or
performance-derived progression recommendation. Weight progression not added.

Optional history: null means unavailable,[] means explicitly no records.
Declared records require same synthetic person, exact exercise/session/version,
supported unit, value ranges and consistent dates. Wrong identities, expired,
ambiguous or conflicting records block. Synthetic validity is at most24h;
this is a test fixture boundary, not a real-world retention/freshness decision.
Reliable history is shown as evidence, not used to invent a new physical load.

Confirm and activate are separate. Exact retries are idempotent; changed replay,
stale source/intake/version or wrong actor/route rejects. Restore proposes an old
snapshot under current valid rules, then requires confirmation and activation
as a new version. Fault injection preserves all prior state/audit/history.
Health reports and withdrawn consent latch; removing a displayed complaint does
not grant clearance. These are manually assigned synthetic contexts, not new
NLP recognition. Existing sources and decisions remain read-only.

## Verification

Preregistered cases: PHASE6E16_PREREGISTRATION.md. Evidence:
PHASE6E16_EVIDENCE.json;48 exact executable localized examples:
PHASE6E16_EXAMPLES.json.207 new tests +3542 frozen regressions =3749 PASS,
zero failed/skipped.536 combined new/frozen15,2591 earlier/frozen12,233 frozen13,
389 frozen14. Historical limitation observations remain observations, not
recognition success. No technical test constitutes medical reliability.

Local browser1812 checks,385 layout inspections,24 settings across320/390/768/1280,
NL/EN/DE, light/dark. Additional390x480 keyboard-space emulation and actual
input/button/restore/reload tests. All16 guided cases; tampered visible99 and
missing proof deliberately produce AFWIJKING. Published checks are recorded
separately after deployment. No physical16 phone check claimed.

All1185 pre-existing working files and58 historical evidence files retained.
112 historical valid pairs and incomplete113 remain unchanged. M41/M42 unchanged.
109 prior public asset bytes and private paths checked before/after publication.
Old unrelated dirty/untracked work must remain unstaged and unmodified.

## Open Boundaries

Ownerreview of16 remains required. Independent exercise-programming/content,
medical safety/recovery, privacy/legal/consent/retention and language reviews remain
open where relevant before real use. Finite fictional catalog, hand-labeled safety,
synthetic time/freshness constants and simulated authorization are not live proof.
No nutrition change, photo/video analysis, real training prescription or automatic
application. Server authority, durable storage and real-member processing remain
outside this release and are not bypassed while SU-487979 is open.
