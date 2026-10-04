# 6E-19 Offline Verification
Only new recovery-checkin-demo files and phase6e19 tests/docs are writable scope.
Never run Supabase commands.6E11 is SUPPORT HOLD SU-487979.
Run from the repository root with the existing Node runtime:
- node _offline/phase6e19/run.cjs <ignored-output-directory>
- node _offline/phase6e19/browser.cjs <ignored-output-directory> [--published]
- node _offline/phase6e19/ops.cjs preserve <original-output-directory>
- node _offline/phase6e19/publication.cjs <ignored-output-directory> before|after
- node _offline/phase6e19/evidence.cjs <ignored-output-directory>

Browser uses installed Edge/Playwright and a strict read-only loopback allowlist;
the published mode allows only the staging Pages origin. Both deny storage and
unexpected egress. There are no Supabase/provider calls.
Reports use exclusive writes. Do not overwrite the baseline or earlier failures.
build.cjs creates the public fictional data from read-only frozen sources and
refuses overwrite. data.js is committed so verification does not need rebuilding.
ops before/freeze were run once; preserve is repeatable with unique outputs.
evidence runs only after the final local tests match current source hashes.
Publication requires132 original files unchanged and private sources404.
Memory simulation does not prove server authority or medical reliability.
