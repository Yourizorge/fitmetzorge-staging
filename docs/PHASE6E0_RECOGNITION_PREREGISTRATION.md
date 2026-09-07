# 6E-0 Recognition Follow-Up: Pre-Registered Cases

Baseline: e5dc0ef948d22225f8b2907a2be41f74f4b15d3d.
The recognition-followup-cases.json inputs/expectations and their tests were written
BEFORE changing engine.cjs or adding hints. Cases are hand-authored natural-language
contrasts, not substitutions generated from matching regexes. This is still a
developer-authored synthetic set, not independent clinical validation.

79 cases: four EXACT original inputs, NL/EN/DE paraphrases and word order,
localized negation, historical/educational/quoted/hypothetical contexts, ordinary
training controls, compound messages and preservation of existing provisional levels.
New health formulations require explicit uncertainty/null instead of known/R0.
No new medical rank is prescribed. Existing R3 labels in three mixed cases remain
provisional, while their newly unclassified context must stay explicitly uncertain.
Four additional state/access tests require unchanged entitlements/facts/no-actions
and self-report without clearance.

The first run is expected to FAIL against the baseline. Record that run separately,
then repair code without rewriting these expectations merely to pass.
Historical limitation observations are not counted as recognition success.
No runtime, copy, medical ranks, D1-D12, provider or data processing is authorized.
