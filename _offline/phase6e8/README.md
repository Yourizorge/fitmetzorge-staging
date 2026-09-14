# Package 6E-8 Synthetic Dual Route

Owner GO recorded before implementation in Decision 0049 and commit b58a6b3.
Preregistered cases: preregistered-cases.json. Frozen 6E-7 receipt protects 141
sources and 59 legacy runtime files; only index.html has an approved bootstrap edit.

Public, intentionally fictional demo: coach-review-demo. Private tests and builders
stay here and must return HTTP404 via Pages. The sandbox is a data-isolation
boundary, not authentication: everyone with the public URL can see the fixtures.
No actual member identity, app storage, provider, database or external notification.

Commands from repository root:

    node _offline/phase6e8/test/verify.cjs
    node _offline/phase6e8/test/browser.cjs
    node _offline/phase6e8/test/browser.cjs --published
    node _offline/phase6e8/test/publication.cjs
    node _offline/phase6e8/examples.cjs

Browser checks host the real index locally and use installed Edge, then close all
test browsers/servers. Published tests use staging only. Generated raw proof and
screenshots go to ignored supabase/.temp/phase6e8-*; nothing is deleted.

Route A imports frozen public 6E-7 model/data read-only. Route B is a separate
in-memory model for another fictional subject. No trainer action exists in B.
Context selection is a manually defined fixture, not language recognition.
O5 is regression-tested in its frozen implementation; this package adds no durable
safety store. Test-context flags are fixture selectors, not real health records.

Final delivery and limitations: docs/PHASE6E8_TECHNICAL_REPORT.md and
docs/PHASE6E8_OWNER_OVERVIEW.md. No automatic owner acceptance or next-package GO.
