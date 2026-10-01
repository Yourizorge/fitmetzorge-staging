# 6E-16 Offline Verification

Route B training-rule catalog. Synthetic memory only. No Supabase operation.
User-facing source: training-rules-demo; private harness: this directory.

Use a fresh ignored evidence directory; output files are append-only.
Run ops.cjs before before any edits, run.cjs for new/frozen15 tests,
phase6e12/run_tests.cjs, phase6e13/run_tests.cjs and phase6e14/run_tests.cjs
for frozen regressions. Existing network blocker is required by these runners.
Run browser.cjs locally and with --published after Pages. Browser tests create
and close their own allowlisted local server when not published.
Run ops.cjs preserve before/after publication. publication.cjs before/after
checks109 prior asset bytes and private404 routes. evidence.cjs binds the local
reports and generates48 executable NL/EN/DE review examples.

Windows tools use the existing bundled Node/Git and installed Edge/Playwright.
FMZ_GIT points to Git; no credentials are required by this synthetic harness.
No packages installed, providers invoked, storage written or database tested.
Synthetic browser role validation is NOT production authentication or RLS proof.
