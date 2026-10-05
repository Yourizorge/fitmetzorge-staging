# 6E-20 Offline Verification
Run from staging repository root. No hosted Supabase operation.
- node _offline/phase6e20/run.cjs <new-evidence-dir>
- node _offline/phase6e20/browser.cjs <new-evidence-dir> [--published]
- node _offline/phase6e20/ops.cjs preserve <baseline-dir>
- node _offline/phase6e20/publication.cjs <evidence-dir> before|after

Tests use12/no_network.cjs. Browser serves allowlisted static dependencies only and
blocks all other requests/storage. Published mode visits only staging Pages.
Existing0-19 regression tools are used read-only. Evidence uses unique append-only
paths. Never use this toolset to resume11 while SU-487979 is on hold.
