# Portable Pure Repository Checks

This is an installed, reviewed repository test runner, not an artifact-Python executor or admission gate. Invoke it from the repository root. It derives root/runtime paths from its own location and requires an explicit expected manifest SHA256 before importing project code. `sources.json` excludes itself and `sources.sha256`; the caller must obtain that expected digest from the trusted delivery/commit, not from an untrusted archive.

## Current Composition And Historical Manifests

The original `sources.json`/`sources.sha256`, the first
`sources-current.json`/`sources-current.sha256`, and the r2 pair are retained historical inputs.
They do not automatically describe later edited source files. Use an explicitly
reviewed composition and its exact digest; do not regenerate pins just to obtain
a green run. The reviewed endchain follow-up uses `sources-current-r4.json` and
`sources-current-r4.sha256` with `--manifest` explicitly supplied. Its receipt
must be read independently of the retained r2 PASS. Neither grants admission.
The r3 attempt stopped before test selection: its excluded-path list had one
joined string instead of two entries. That original manifest remains unchanged.

The v2 manifest permits only the sixteen independently pinned raw LF/CRLF pairs.
It verifies raw size and hash before canonical equality and returns the actual
raw hash. Historical fixture copies remain exact. No other file gets automatic
line-ending normalization. Stage and extract this byte-bound test composition
with command-scoped `git -c core.autocrlf=false`; no global Git setting change is
required. Always compare stored Git blobs against the manifest before calling a
fresh checkout reproducible. Ordinary Windows conversion is not equivalent proof.

The runner reports PASS only when every selected test ran, none was skipped,
and unittest reports no failures or errors. A selected but skipped class is not
a completed check. The full 452 selection is separate from manifest/import,
child-process and platform-specific symlink tests.

```powershell
$checks = '_offline/phase6e11/endchain_v1/assembly_checks'
$pin = (Get-Content "$checks/sources-current-r4.sha256" -Raw).Trim()
python -B "$checks/run.py" --manifest "$checks/sources-current-r4.json" --manifest-sha256 $pin --scope full --report <new-report-path.json>
```

The commands below describe the preserved original composition, not a fallback
when the current source hash check fails.

PowerShell (no workstation paths):

```powershell
$checks = '_offline/phase6e11/endchain_v1/assembly_checks'
$pin = (Get-Content "$checks/sources.sha256" -Raw).Trim()
python -B "$checks/run.py" --manifest-sha256 $pin --scope portable
python -B "$checks/run.py" --manifest-sha256 $pin --scope full --list-only
```

POSIX shell:

```sh
checks=_offline/phase6e11/endchain_v1/assembly_checks
python -B "$checks/run.py" --manifest-sha256 "$(cat "$checks/sources.sha256")" --scope portable
```

Only after Main selects the final composition: use `--scope full` without `--list-only`. The full selection in `selection.json` is exactly the A05 452-test selection; no portable-runner tests are silently added to it. `--scope portable` runs runner negatives, historical/policy checks and one bounded recovery unit, not full-root enumeration. `--report <new-relative-path.json>` is create-only. No report is silently overwritten.

Dependencies default to existing `supabase/.temp/phase6e-server-deps` and `supabase/.temp/phase6e11-pg17-parser`. Explicit `--deps` and `--parser-deps` accept other local installed dependency directories. There is no installation or network fallback. Required: psycopg 3.2.10 binary, reviewed libpq 160009 or 170006, pglast 7.20. The original native driver proof still checks package source/binary identities without connecting.

## Sources And Fixtures

- `sources.json` binds every declared source byte, including the runner, selection, fixture pins, dependencies and current policy inputs. Missing sources stop before test imports. No metadata-only substitute is accepted for required source files.
- `historical/` contains exactly four original source files with their original internal relative paths. They are read-only source fixtures; execution from that subtree is forbidden.
- The 48 policy inputs are read directly from the current repository source root with unchanged fixed hashes. There is no second policy fixture tree.
- The existing test overrides remain usable by direct unittest invocation. This runner requires A_RECOVERY_SOURCE_ROOT, A_RECOVERY_RUNTIME_DIR, A_BOOTSTRAP_HISTORICAL_ROOT, A_BOOTSTRAP_POLICY_ROOT and AUTH_CONTEXT_SOURCE_ROOT to equal its verified layout if already set; conflicting external roots are rejected, not silently replaced.
- `dependency_needed.json` enumerates the 19 exact A05 untracked dependencies outside the earlier 96 integration targets. They are required by this source-bound composition. Their presence here is not evidence that they were committed or that a fresh clone contains them. Main owns any logical commit/staging decision; this runner does not inspect or modify the index.

## Boundaries

The pure runner denies child-process and network operations. Real Python worker process tests and synthetic loopback HTTP tests remain separate suites listed in `selection.json`; they are not dispatched here. Existing process wait/reap limits are unchanged. No host, Docker, database, GoTrue, CI or hosted authority is granted. Source scan covers the entire declared inventory, including the 19 dependency files; no credential-pattern exception is added.

Unittest counts include inherited methods and are not unique live fault scenarios. Green pure tests do not establish a closed budget, measured WAL zero, actual full-chain execution, clean47 authority or READY. All such admission flags remain false.
