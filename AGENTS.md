# FitMetZorge Staging Agent Policy

## Permanent Staging Autonomy

The owner grants autonomous execution authority inside all of these exact boundaries:

- Repository: `Yourizorge/fitmetzorge-staging`
- Branch: `main`
- Supabase project: `mokxyyullfhkfalopbzd`
- Frontend: `https://yourizorge.github.io/fitmetzorge-staging/`

Inside those boundaries, work may continue through audit, design, implementation, migrations, RLS/ACL, staging data operations, tests, commits, pushes, staging deployments, verification, documentation, and reversible fixes without repeated owner approval when the approved product contract remains unchanged.

Stop for owner input only before a new cost, missing credential, irreversible external action, unresolved product/privacy/pricing/licence/legal decision, material frozen-contract change, owner acceptance/freeze, or any action outside the exact staging boundaries.

## Production Lock

Production is never implied or authorized by staging autonomy, technical readiness, owner acceptance on staging, or phase completion.

- Production repository: `Yourizorge/fitmetzorge`
- Production Supabase project: `hgoygcviutmynaihcvpd`
- Production requires a separate explicit owner GO.

Do not prepare, push, deploy, migrate, configure, or otherwise touch production without that separate GO.

## Frozen Baselines

Preserve owner-accepted frozen functionality. A frozen phase may only receive a minimal compatible correction when a proven regression or a new approved integration requires it. Never remove or rewrite legacy data without a reviewed migration and explicit contract.
