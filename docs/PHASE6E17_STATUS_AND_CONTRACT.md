# 6E-17 Nutrition Contract and Status
2026-10-01. New isolated Route B offline/synthetic nutrition contract.

This additive current-status/architecture/test document accompanies BUILD_STATUS,
MASTER_BUILD_PLAN, ARCHITECTURE and TEST_MATRIX. Their existing dirty files and
historical text are preserved. Roadmap search found no conflicting package17.
The explicit owner GO authorizes17, not18 or live AI.

6E-16 is COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE/SYNTHETIC ONLY. See its new
freeze receipt and16-source working/Git hash manifest. Owner physically accepted
all16 scenarios and16-R1 through16-R3. Training numbers remain unvalidated concepts.
6E-17 is delivered for ownerreview after the publication receipt passes. No
automatic acceptance/freeze. Whole Phase6E remains incomplete. 6E-11 hosted remains
SUPPORT HOLD SU-487979. No Supabase/JIT/Auth/migration/Edge/cleanup operations.

## Contract

Public namespace: nutrition-rules-demo, eight isolated files. Private tests/tools:
_offline/phase6e17. Only shared public dependency is the frozen brand image. No
change/import into Route A or Phase4 nutrition, products, goals or real runtime.
Memory only; refresh resets. CSP connect-src none. No storage, external calls,
new dependency installation, live identity or server-authority claim.

Every one of22 intake fields is a cell with status known/not_applicable/missing,
plus an explicit value or null. Goal, age, audience confirmation, original height
and weight, activity, training frequency, existing target reference, meals, moments,
favorites, exclusions, allergies, diet, cultural/practical restrictions, recipe
count, preparation time, budget, language, units, health and consent are distinct.

Missing required data blocks; zero is not missing. Only budget may be missing
without blocking and is then not used to infer an allowance. Not-applicable is
permitted for favorites/exclusions/diet/restrictions/budget. A not-applicable
target is preserved but cannot build a plan because no approved calculation rule
exists. Allergies require known[] to explicitly assert no reported allergy;
not-applicable/missing is not silently interpreted as allergy-free. Required age
and positive audience assertion enforce the fictional adult-only fixture; they
are not a legal or medical assessment of eligibility.

The catalog has IDs/versions and validity; eight fictional products with aliases,
per100g source values, exact ingredients, allergen/may-contain lists, category,
diet/budget tags; four flat recipes bound to exact product versions; one existing-
target rule; and a synthetic existing target with person/goal/version/date binding.
Each rule carries required fields, source/method, conceptual validation status,
portion limits/steps, categories, exclusions, substitutions, meal distribution,
reason and unit/rounding policy. The target supplies explicit nutrient bounds.

Method is existing_target_only. CalculationRules is empty and cannot be filled
with a made-up approved formula. No BMR/TDEE, deficit, surplus or macro target is
derived from body measurements, activity or training. Those fields are retained
with source states, not fed into an unreviewed formula. Only the existing fictional
target is used. All content remains synthetic_unreviewed, not expert-approved.

## Executable Example

The fictitious existing goal is1800 kcal,60g protein,280g carbohydrates,45g fat.
Default recipe has200g rice,150g beans,200g vegetables and10g oil, all test products.
Per meal:575 kcal,18.5g protein,93g carbohydrates,13.5g fat. Three meals total1725
kcal,55.5g protein,279g carbohydrates,40.5g fat. Differences from goal are displayed:
-75 kcal,-4.5g protein,-1g carbohydrates,-4.5g fat. No automatic target adjustment.

The three planned shares are34/33/33 percent, with calculated meal totals shown
separately. Layouts for2 and4 meals have separately declared gram quantities and
shares. Daily bounds and portion ranges are explicit fictional source limits,
not assertions of safe intake or scientific norms. A within-portion edit can still
be refused if its resulting day total violates those source limits.

Arithmetic uses integer millikcal and nutrient milligrams. Source amounts remain
grams: per100 value * grams /100. Nonintegral or overflowing internal arithmetic
is refused rather than rounded. Display uses up to three exact decimals. Meal
sums equal the day sum; planned shares sum to the existing goal; differences are
never hidden. Source energy is not recalculated with an invented macro formula.

## Safety and Editing

Canonical identity and closed aliases resolve exclusions such as groundnut,
arachide and pinda to peanut. Recipe ingredients are flattened, version-bound
leaf foods. Composite products/nested recipes are NOT supported; extra hidden
ingredients fail validation. Alias collisions and unknown identities block.
Allergen/may-contain, product exclusions and rule exclusions filter every actual
item, product alternative and recipe alternative. A known allergy conflicting
with a favorite blocks rather than silently overriding a preference.

Substitution lists are allowed source options, not a guarantee that any portion
combination meets the whole-plan goal bounds. Whole-plan checks run after every
item/recipe/portion/time edit. Selected favorites must remain represented; maximum
recipe count, available moments, preparation metadata and declared budget/diet
tags must fit. No price estimates or real dietary certification is implied.

UI supports moving to a declared moment, replacing a meal or product, changing
grams within bounds, preferences, rejection and reassessment. The preference form
is a bounded subset of the full22-field input contract; all fields are visible
with status in the active-input disclosure. Missing/source-failure scenarios are
explicit fixtures, not guessed form values.

Every new intake/source invalidates the draft and prior confirmation. Confirm
and activate are separate; exact retry is idempotent; conflicting replay, wrong
person/route/version and stale source fail without partial changes. Restore must
match current intake/source and becomes a newly confirmed/activated version.
Old versions remain immutable. A simulated precommit failure rolls all state back.
Body sources165lb/69in stay exactly so when a unit preference changes; food grams
are never implicitly converted. No new body or food values are inferred.

Complaint/medical restriction/unclear recovery contexts block personal nutrition
adjustment and retain an open expert-review boundary. Removing a reported context
does not provide clearance. Consent withdrawal blocks new processing/drafts;
existing history remains readable. No clinical diagnosis, diet treatment,
application-service review queue or automated action. Context is manually assigned
synthetic state; this package does not expand health-language recognition.

## Evidence and Limits

Preregistered cases: PHASE6E17_PREREGISTRATION.md. New289 tests and3749 frozen
regressions total4038, zero failed/skipped in the final suites. Existing limitation
observations are retained, not counted as successful medical recognition.
The final local and published browser counts, source hashes,60 executable localized
examples and byte-identity receipts are in the evidence/publication documents.
Browser matrix includes NL/EN/DE, light/dark,320/390/768/1280 and390x480 keyboard-space
emulation. Physical ownerreview of17 remains open. Tampered visible totals,
missing proof and unsafe injected option must produce AFWIJKING.

All1210 original worktree files and58 historical evidence files are preserved,
including112 valid historical pairs/incomplete113 and migrations41/42. All117 prior
public files must remain byte-identical; private tests remain404. Existing dirty
work is excluded from commits. No true server/data test performed or implied.

Before real use: independently reviewed nutrition catalog, calculation authority
if desired, allergy completeness/cross-contact and ingredient-quality policy,
medical diet and recovery boundaries, audience eligibility, original source
freshness, consent/privacy/legal retention and translations remain open. This
finite fixture catalog cannot certify absence of allergens in real food or provide
clinical nutrition. Support-ticket hold is not bypassed by the browser simulation.
