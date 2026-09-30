# 6E-15 Preregistration
2026-09-30. Owner confirms full offline GO. Roadmap search: 6E-15 unassigned.
Freeze 6E-14 P1-P3 separately. No live server release, no hosted work under SU-487979.

## Slice Fixed Before Implementation
Route B intake and week-plan basis using frozen 6E-8 versioned catalog/model,
plus read-only frozen 6E-13 safety results. No Route A changes.
New explicit intake adds location/machines, less-liked versus excluded exercises,
known dietary restrictions, activity/source records, locale and consent. No
personal free text, accounts, photos or external providers. Presets are fictional.
Complete intake required; an empty list explicitly means none, null means missing.

Training/food/recovery values come from existing catalog. Dislikes rank behind
otherwise eligible exercises; hard exclusions never return. Unknown machine or
diet-rule requests block rather than invent a catalog. Allergy exclusions enforced
at initial build, edits, confirmation, activation and restore.
Existing set count is FIXED: beginner2, regular3. Unsupported direct set edits
are rejected; changing explicit experience then rebuilding can select the other
existing rule. No new free-set range is invented. Reps use the existing1..12
validator. No load recommendation/conversion; kg/lb loads remain null. Food portions
remain source grams, even with lb training units. No calorie-needs/macro-goal claim.

## Required Cases
Complete/missing/null versus explicit none; favorite/dislike/excluded conflicts;
home/mat-only and too-small equipment catalog; days/duration; plant/omnivore;
allergy/food exclusion, unsupported diet/machines; sleep/recovery/activity missing
or conflicting or expired; current/recurring/unclassified/self-report/O5/technical
safety, no clearance from absence; consent withdrawn and trainer-route input denied.
Wrong subject/source/catalog/version; exact source fingerprint; tampered request,
duplicate confirm/activate, atomic fault, stale proposal; failed edits preserve
whole valid prior draft (explicit rejected edit), not a partially modified draft.
Allergen/avoidance enforcement on alternative lists and restore; no silent reintro.
Editing clears confirmation. Intake revision invalidates pending plan; active/
historical versions remain. Restore uses current constraints and creates new version.
NL/EN/DE, mobile/tablet/desktop light/dark, reduced keyboard space, keyboard navigation,
reset on refresh, zero storage/backend calls. Frozen tests/hash preservation.

Known language-limit observations remain limitations, not recognition successes.
Physical phone owner review and medical/privacy/legal/language review stay separate.
