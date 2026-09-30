# 6E-15 Visible Owner Test Mode
2026-09-30. **TECHNICAL PASS / READY FOR OWNER RETEST** after local checks.
Owner acceptance is NOT complete. 6E-15 is NOT frozen.
Published verification is recorded separately in OWNER_TESTMODE_PUBLICATION.

## Requested Correction
The prior situations were reachable through the scenario selector, but that was
not an adequate nontechnical owner test. The isolated demo now has nine large
named buttons, plain Dutch expected behavior, changed inputs, permission/reason,
and a guided previous/next route. The original manual workflow remains available.

Only app.js, index.html and demo.css in independent-intake-demo changed.
One new public review.js calls the unchanged model and existing fixtures/catalogs.
The private static test server allowlist gained that one file. New local tests,
measurement helpers and documentation are separate from all historical proof.

## Real Test Results, Not Preset Green Labels
Each selection creates a fresh memory-only synthetic model, executes the existing
commands and records before/after states and expected return reasons.
PASS requires all recorded checks and all expected actions. The display is checked
against the actual model: exercise IDs/labels, food IDs/labels/grams, version
history, blocked controls and blocked-old-concept notice.
Errors, missing action/check evidence, changed state or wrong visible content
give red AFWIJKING. Manual intake/plan editing or a manual command clears the
previous PASS. Selecting a new test does not assert owner acceptance.

1. Complete: concept only, no activation.
2. Missing: goal absent, build refused, no mutation.
3. Allergy: nuts/dairy plus tofu exclusion; squat also excluded. A supported
   alternative is built. Attempts to add nuts or yogurt are refused atomically.
   Actual absence counts are visible, including the excluded exercise.
4. Complaint: current synthetic health context prevents physical plan formation.
5. Rule: unsupported cable machine prevents invented catalog selection.
6. Source: changed days clear old confirmation/concept; stale activation refuses;
   conflicting source version then prevents a new build.
7. Withdrawal: new intake, build and activation all refuse. Old concept is clearly
   labeled unusable; existing evidence is not erased to claim success.
8. Duplicates: exact replay and fresh duplicate tested; one plan version only.
9. Restore: versions1/2 retained, no activation before a fresh confirmation,
   restored plan becomes version3. No trainer step is introduced into Route B.

The automatic command sequence is explicitly a TEST simulation, never application
approval or background application of a real plan. The normal confirm/activate
commands still enforce the same state machine. Refresh resets all demo state.

## Local Verification
- 329 deterministic, network-disabled tests PASS: existing245 unchanged +84 new.
- Existing browser suite:463 PASS,49 layout checks.
- New owner browser suite:1346 PASS,217 layout checks.
- Each matrix has24 settings:320/390/768/1280 widths,NL/EN/DE,light/dark.
- Guided forward/back, keyboard Enter, reduced390x480 keyboard-space,
  no persisted state, refresh reset, withheld processing and stale PASS invalidation.
- Browser negative controls inject wrong food text and missing evidence:
  the visible badge becomes red AFWIJKING.
- No unexpected network requests or browser errors. Only static allowlisted assets.
- Mobile/keyboard testing is emulated, not physical Safari/Android acceptance.
- Owner test guidance intentionally stays Dutch (lang=nl); existing plan UI remains
  NL/EN/DE. Test counts are technical evidence, not expert validation.

PHASE6E15_OWNER_TESTMODE_EVIDENCE.json binds source and evidence hashes.
Ignored raw evidence: supabase/.temp/phase6e15-owner-review-1790786498720.
Verified final-text runs are in its verified subdirectory. Earlier test results
and screenshots remain intact. Historical original15 evidence is not rewritten.

## Preservation And Boundaries
Starting local/remote main:e942b06e30ae47b3128a800147100c0e22eaa4b3.
Of1175 baseline entries,1171 remain byte-identical; only four pre-registered
existing files may change. This baseline includes the newly added measurement
helper itself. All prior nonignored files outside those four are unchanged.
Old dirty/untracked6E-11 work is retained and excluded from the commit.

Existing model.js/data.js/copy.js and245-test file are checked against original15
hashes. Frozen14 source hashes remain checked by the old suite. Route A, all
frozen sources and existing app runtime are unchanged. Migrations41/42,112
historical pairs and incomplete113 remain preserved. No hosted measurement.
Prepublication:102 existing public asset hashes match,57 private paths return404.
Only isolated demo/test/docs changes are eligible for the staging push.

No new product rules, expert approval or owner acceptance. Fixed set rules and
manual synthetic health context remain existing limitations. No package16.
6E-11 hosted: **SUPPORT HOLD - SU-487979**.
Supabase/JIT/Auth/migration/Edge/cleanup operations:0.
External AI calls/cost:0 / EUR0.00. Real-member AI enabled:NO.
Production touched:NO.
