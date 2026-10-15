# Local offline shell integration

Scope: existing `_offline/phase6e_server_v1` only. No hosted operation, CI
dispatch, commit, push, frozen source change, or owner acceptance by this worker.
The shell and queue source changes are not covered by an earlier CI revision.

## Owned files

Modified: `draft_queue.js`, `draft_queue.test.cjs`, `queue_ui.js`, `server.py`,
`ui.html`.

Added: `offline_shell.html`, `offline_shell.css`, `offline_shell.js`,
`offline_sw.js`, `offline_queue_ui.test.cjs`, `offline_shell_browser.cjs`,
`offline_shell_local.cjs`, `offline_shell_INTEGRATION.md`.

The two shared entry files contain additive shell hooks plus James's requested
`/account_center.js` static mapping and script before `ui.js`. Account source,
`ui.js`, `panels.js`, `ui.css`, `composed_browser.cjs`, and `ci.py` were not
edited by this worker. Existing dirty files and other workers' changes remain.

## Parent CI hooks

Add all eight new names above to `ci.py`'s `NEW` source list so the candidate
archive and hash cover them. Keep James's account files in his source list.
The five modified files already belong to `NEW`.

Continue the existing draft-queue unit command and add:

```python
self.command('offline-queue-ui-regression', [
    'node', '--test', str(folder / 'offline_queue_ui.test.cjs')])
```

James's coordinated lifecycle fix also adds `ui_session.test.cjs`. Include it
in the parent's candidate source list and Node test execution. It loads the
real `ui.js` and `queue_ui.js` with controlled HTTP completion timing.

Run the new browser module immediately after a PASS from `composed_browser.cjs`,
inside the same `joined_app` server lifetime, before its `finally` shutdown:

```python
p = subprocess.run(
    ['node', str(folder / 'offline_shell_browser.cjs')],
    input=json.dumps(data), text=True, capture_output=True, timeout=180)
result = json.loads(p.stdout)
self.save('offline-shell-browser.json', result)
if p.returncode or result['status'] != 'PASS':
    raise RuntimeError('offline_shell_browser')
self.result['offline_shell_browser_checks'] = result['checks']
```

Input is exactly the existing composed-browser object:
`url`, `accounts`, `playwright`, `screenshots`. The screenshot directory must
exist. The suite creates fresh isolated browser contexts and closes them.

Fixture preconditions:

- Use **joinedB + historical**, not mappedA/B. Member `accounts.b` must log in.
- `composed_browser.cjs` must already have revoked joinedB consent. The test
  locates the non-registration12 view with `consent === false` and fails if
  absent. No requirement on historical consent, session phase, or version.
- `accounts.trainer` must remain unmapped to these composed workspaces.
- No new PostgreSQL workspace, account, entitlement, or grant is needed.
- Auth login/logout/read calls are real; the suite makes zero `/api/action`
  requests and verifies that workspace versions stay identical.
- A local IndexedDB draft is deliberately seeded as a pre-revocation fixture.
  The real server state stays revoked throughout. It is never submitted.
- This suite does not need a consenting fresh workspace, so James's suite can
  independently run before the existing mappedA/B browser checks.

The queue now performs a fresh `/api/today` Auth read before every explicit
queued action attempt, including the general lost-response retry. Its recovery
button also refreshes the displayed state first. Initial page refreshes that
started before the queue wrapper loaded receive one additional verification
read before reading IndexedDB. Include these reads in local Auth accounting;
no hosted command register or hosted budget was modified.

## Behavior and privacy boundary

`offline_sw.js` registers only on `127.0.0.1`. Its versioned Cache API allowlist
contains exactly `offline_shell.html`, `offline_shell.css`, `offline_shell.js`.
Installation fetches omit credentials, reject redirects and incorrect MIME
types, and validate all assets before storing them. Only exact root navigation
gets a network-first generic fallback; query URLs, API, POST, account scripts,
app HTML, and runtime scripts are never added to this cache. Bump the cache
version for a subsequent shell release. Existing controlled tabs are not
force-reloaded during worker installation.

Cold offline startup has no login form, account view, queue code, or IndexedDB
access. Online events update a generic message only. Reconnect is explicit;
server Auth verification is required to restore account views. The only
localStorage key added is `fmz-shell-display-v1`, containing a validated device
language/theme pair. It contains no actor, account, token, or server preference
object. A first-ever visit requires a working local server to install the shell;
browser cache eviction/private mode can remove offline availability.

Existing IndexedDB drafts remain separate from the shell cache. They contain
only allowlisted registration/recovery fields and their exact actor/workspace/
source/request bindings. This is local draft storage, not encrypted storage or
an authorization mechanism. API responses and credentials are never persisted.
Verified-view checks, storage-key checks, compare-before-delete, and immutable
payload hashing protect recovery. No approval/apply or automatic synchronization
is introduced. Explicit revoke/health actions can proceed while the queue is
loading without deleting the stored draft or clearing an unrelated uncertain
approval/apply request. Local discard also preserves unrelated uncertain actions.

## Local evidence

Run unit tests from the repository root:

```text
node --test _offline/phase6e_server_v1/draft_queue.test.cjs _offline/phase6e_server_v1/offline_queue_ui.test.cjs
```

The separate `offline_shell_local.cjs <absolute-playwright-module> <output-dir>`
runner serves only static local files and denies every API call. It uses the
same generic browser/cache/IndexedDB checks as the integrated suite, without
synthetic Auth or independent database setup. Output must remain inside this
repository. It closes the server and browser when finished.

Local results: 44 draft/queue unit tests PASS; 62 real-browser shell/storage
checks PASS. Combined with James's 26 lifecycle tests, account and presentation
tests, all 91 unit tests PASS. His simulated-HTTP account browser suite also
passes 80 checks with the final queue/UI sources. That fixture suite proves UI
behavior only, not PostgreSQL or real Auth.
Twelve screenshots cover NL/EN/DE, light/dark, 390px/1280px. Mobile German dark
and desktop English light screenshots were visually inspected. Server Python
syntax also PASS. Evidence is under
`supabase/.temp/phase6e-offline-shell-checks/`, including
`offline-shell-local.json`.

The standalone Auth-backed browser module is prepared but was not executed by
this worker: the existing disposable PostgreSQL/GoTrue environment belongs to
the parent's CI. Local browser/storage results are not PG/Auth, hosted, or
physical owner-test evidence. No persistent app server was left running.

## Follow-up lifecycle review

Eight additional regressions reproduced missing/blank CSRF acceptance,
wrong-actor recovery leaving old DOM visible, obsolete success/failure clearing
a newer login, and restored-page requests rebinding after invalidation. The
queue fixes pass all eight. They affect only `queue_ui.js` and its test module.

For the coordinated UI fix, `globalThis.FMZQueueSession.epoch()` exposes the
current generation. An obsolete completion carries `err.staleSession === true`
and never invalidates a newer login; it is not marked server-confirmed. A current
request that deliberately clears authentication carries `invalidatedSession`
and `invalidatedEpoch`, and displays the generic binding message.

James's completed `ui.js` fix defers initial refresh until all wrappers are
loaded and guards asynchronous refresh/login/logout/submit continuations,
including pending-request, status, and busy writes. Auth form operations are
serialized separately. This worker reviewed that code and ran his new
`ui_session.test.cjs` against the completed queue changes; this worker has not
modified `ui.js`.

The queue's send/discard handlers and registration action now also capture
their generation. Deferred get/create/put/remove, inspect, and refresh
completions cannot change a new session's panel, message, pending request, or
busy state. Invalidation releases the old busy operation synchronously; old
catch/finally handlers do nothing in a later generation. Tests include relogin
as the same actor with a new pending request. Already initiated durable writes
remain bound to their original actor/workspace and existing compare-delete
hash; no stale completion sends a new action.

No remaining issue was found in the reviewed cross-session completion paths.
Parent CI must still verify the complete source with PostgreSQL/GoTrue; these
local lifecycle/fixture results are not a replacement for that run.
