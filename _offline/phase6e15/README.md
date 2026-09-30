# 6E-15 Offline Route B
Only fictional intake and existing frozen 6E-8 catalogs; frozen 6E-13 safety read-only.
No Supabase/provider/Auth/database connection and no real member data.

Run from repository root:
- node _offline/phase6e15/build.cjs
- node _offline/phase6e15/run_tests.cjs NEW_EVIDENCE_DIRECTORY
- node _offline/phase6e15/test/browser.cjs NEW_SCREENSHOT_DIRECTORY
- Append --published for the same browser tests against static Pages.
- node _offline/phase6e15/publication.cjs EVIDENCE_DIRECTORY before|after

The browser test uses installed Playwright and Edge; no new packages. Its loopback
server serves only ten public static assets. CSP/no-network guard enforce isolation.
Frozen test runners are used unchanged. Historical evidence is never overwritten.
See docs/PHASE6E15_REPORT.md for constraints, coverage and limitations.
