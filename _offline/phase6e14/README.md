# 6E-14 Isolated Offline Contract
Synthetic, deterministic, memory only. Do not connect this folder to Supabase.
Source flow and limitations: docs/PHASE6E14_REPORT.md.

From repository root:
- node _offline/phase6e14/build.cjs
- node _offline/phase6e14/run_tests.cjs EXISTING_NEW_EVIDENCE_DIRECTORY
- node _offline/phase6e14/test/browser.cjs EXISTING_NEW_SCREENSHOT_DIRECTORY
- Optional published static browser test: append --published.
- node _offline/phase6e14/publication.cjs EVIDENCE_DIRECTORY before|after

Browser tests use the installed bundled Playwright/Edge runtime. No new dependencies.
The static server is loopback, GET-only and allowlisted; it is closed by the test.
No AI/Auth/database calls. UI packets are not a trusted server boundary. The private
engine validates sources; generated public data contains only reviewed synthetic
fixtures. Frozen 6E-6/8/13 are imported read-only, never edited.
