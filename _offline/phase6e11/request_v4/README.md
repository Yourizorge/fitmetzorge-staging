# Request Binding V4

Owner instruction 28 September 2026 supersedes the former shared GoTrue/workflow
transaction requirement. GoTrue events remain independently evidenced. The Edge
verifies the user token with Auth and binds only trusted minimum claims to a
single application transaction. No managed Auth/Storage/Realtime schema writes
or observers are added. Local Auth stubs never constitute hosted Auth evidence.

The immutable M40 audit core is reused. M41 is not edited. New request support
is private, default-off, SECURITY INVOKER, and callable only by the existing
server-side database connection. This privilege is necessary to use the private
audit core, which intentionally denies client execution. The original principal
and workspace guards still run with the verified user claims; the server's
database privilege is not used as the user's authorization.

Tests in cases.json were recorded before the V4 implementation. Historical
receipts and failed attempts are retained; none becomes a pass retroactively.

Official documentation reviewed: Auth sessions (session_id/live session check),
Edge Auth (server verification), database functions (invoker/revoked execution),
and the 25 September changelog. PG17.11 rollout has extension-specific breaking
changes; no upgrade, reindex or encryption rewrite is part of this package.
The required reproducibility target remains PG17.6. Logs pricing is changing;
no paid logging, add-on or infrastructure is enabled.

Current evidence: docs/PHASE6E11_REQUEST_BINDING_REPORT.md. M42 has passed clean
CI and is installed 42/42 with an empty dry-run, but the complete hosted workflow
is not admitted. The temporary read-only OIDC probe was removed after its strict
Edge database configuration guard failed. Its local follow-up diagnostics are
not permission to redeploy or widen access. The normal application Edge adapter
is a tested candidate, not a deployed replacement. No owner window is open.

The retained local evidence tooling depends on earlier isolated 6E-11 directories
and ignored proof manifests in this workspace. Publishing this candidate alone
does not claim a complete fresh-checkout hosted test package. Clean database
reproduction uses the pinned ci42 workflow and immutable recorded candidate blob.
