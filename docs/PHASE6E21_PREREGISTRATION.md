# 6E-21 Preregistered Verification
2026-10-08. Written before21 domain implementation. Baseline main:
2fdb7b6cf4529b7b6143ffe846ac0bf151981baf. No existing21 namespace found.
1315 worktree files and58 historical evidence hashes protected.

Positive cases: both B workouts/all exercises/all6 sets and all3 meals/all12 items;
A all6 sets; explicit workout completion; partial completion honestly labelled;
independent kg/reps/RIR/RPE with null,0 and RPE7.5; exact original source snapshot;
explicit uneaten item versus missing; original exact product/recipe calculation;
goal difference from registered subtotal; no claim of full day intake; history.

Negative cases: unknown/cross-workout set, wrong person/role/route/plan/row/source,
wrong unit and implicit conversion, negative/non-finite/out-of-range numbers,
wrong recipe/product version, portion outside existing bound or off step, unknown
food, stale completion, stale application, changed duplicate request, source expiry
and conflict, complaint and self-reported resolution, revoked consent.

Coupling cases: record correction after approval retires ALL approvals/notices;
correction after workout completion reopens that workout for explicit recompletion;
unchanged and duplicate registration do not add histories or notices; training
completion does not complete check-in or other workout; meal input does not complete
workout; cadence-only apply retains original recording snapshot; physical plan
change starts empty new records while retaining old histories; restore is reviewed
and creates a new version; faults at prepare/commit do not partially change state.

Use frozen16/17 validators and nutrient arithmetic,18 linked sources,19 check-in
rules,20 source/approval architecture read-only. No invented load progression,
calorie/macro adjustment, medical criterion or new physical proposal.
A/B workflows remain distinct. Full-plan registration is not a new live authority.

Browser: guided test scenarios plus real input on allworkouts/meals; NL/EN/DE,
light/dark,320/390/768/1280; source labels, planned/actual,0/missing/uneaten, history,
explicit finish, approval invalidation, blocked controls and reset. No network
except allowlisted static assets; no browser storage. Published bytes and hidden
paths checked before/after; frozen0-20 regressions. Known limitations remain separate
from recognition success. No hosted Supabase activity, no owner21 acceptance.
