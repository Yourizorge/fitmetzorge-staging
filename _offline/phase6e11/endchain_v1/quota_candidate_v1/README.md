# Disposable Quota Candidate V1

Offline compiler and validators only. No connection, SQL execution, migration,
Auth, CLI, hosted or CI-dispatch API. This appended candidate is NOT the clean47
baseline and is NOT hosted authority. Runtime/Node integration and the real full
command register remain missing: `execution_admitted=False` throughout.

## Interface

Import with the source-bound `endchain_v1` directory on Python's module path:

```python
from quota_candidate_v1 import compiler as quota

manifest = quota.prepare(
    root, source_commit=source_commit, candidate_sha256=candidate_sha,
    github_run=ci_run, created_at=starts_at, expires_at=expiry,
    cases=[{'id': fresh_case_uuid, 'label': 'before_call', 'cap': 2349}],
)
case = quota.binding_for_case(root, manifest, fresh_case_uuid, now=now)
quota.validate_case_binding(root, manifest, case, now=now)
quota.validate_target(root, manifest, environment=observed_ci_environment,
    connection=sanitized_driver_parameters, ca_path=official_local_ci_ca, now=now)
```

These calls precede **any DB connection**. `root` is explicit; there is no global
checkout/environment fallback. `source_files(root)` hashes required compiler,
template, test and baseline dependency files, plus pinned M41/M44/M45 and the old
authorization. An optional larger `sources` map must contain all required inputs.
The loaded Python/template bytes are checked against that map. Main must bind the
supplied source commit and archive SHA to its already verified candidate archive.

`case` provides the requested `run_id`, `purpose`, `cap`, `parent_id`,
`source_commit`, `candidate_sha`, `ci_run`, `expiry`. Additional fields are
`binding_sha` (canonical manifest SHA256), `environment='disposable_ci'`,
`execution_admitted=False`, `hosted_permission=False`.
The future Controller grant must use `case.binding_sha` as `manifest_sha`;
the legacy Auth-contract-only hash is not this new binding.

The sanitized connection is an exact map: `host`, `hostaddr`, `port`, `dbname`,
`user`, `sslmode`, `sslrootcert`, `connect_timeout`. Require both hosts 127.0.0.1,
database/user postgres, verify-full with Main's existing local CI CA path, timeout
5, and the actual CI source/run/repository/main identity. Never pass passwords or
connection URLs. Target preflight does not pretend to attest live TLS.

After Main's existing readonly baseline queries (no new executor here):

```python
artifact = quota.compile_candidate(root, manifest, quota_samples, now=now)
quota.validate_candidate(root, artifact, quota_samples, now=now)
```

`quota_samples` is the complete four-query sample mapping from
`admission_quota_readonly.QUERIES`, not its summary PASS receipt. The existing
validator checks the precise M45 constraint AST, function body/ACL, trigger and
empty registry. The generated SQL rechecks the baseline under an exclusive lock
before mutation and requires live pg_stat_ssl SSL, PG17, postgres and expiry.
Main must save source-bound samples/artifact/intent before any eventual apply,
use only NativeRuntime.disposable, and collect real post-catalog/SQL evidence.
Calling only `validate_target` is not execution admission.

## Narrow SQL Delta

- The template is outside `supabase/migrations`. No canonical migration bytes,
  migration history, old authorization or old function/trigger is modified.
- One new private admin-only case table records the nine binding fields, start
  and manifest hash. RLS is enabled with no policies and public/API roles receive
  no privileges. A statement trigger freezes the catalog after exact initial
  insertion. No case cap renewal or extension exists.
- The named runs CHECK retains both historical branches (2237 and 2349) and
  default 128; only exact new UUID branches are appended, each cap 1..2349.
  Catalog lookup enforces the claim/lease in an invoker trigger. This is not a
  mutable table-dependent CHECK function; see PostgreSQL's
  [CHECK limitations](https://www.postgresql.org/docs/17/ddl-constraints.html).
- New receipt identities cannot change, counters/steps cannot decrease, failed
  rows cannot become complete/running, and deletion/truncation cannot erase a
  new receipt. Expiry blocks progression/PASS while allowing capped stop/close.
- Cases are canonical UUIDv4, distinct from parent NEW_RUN and all UUIDs in the
  pinned legacy contracts. Offline checks cannot prove global UUID absence.
  Application requires an empty, locked local registry; no globalzero claim.
- Existing `github_run UNIQUE`, running-slot uniqueness and ten-minute expiry
  constraints stay intact. A manifest may enumerate up to 14 cases, but this
  does NOT allow 14 retained claims under one GitHub run in the same registry.
  Main must resolve real fullchain orchestration without fake run IDs, deletion,
  hidden reset or implying that this candidate solves that separate gap.

The plan reports 17 top-level SQL statements, not a proven protocol/internal-SQL
cost. Bootstrap is separately labelled local diagnostic setup, with actual
accounting pending. No additional allowance, timeout increase or WAL exemption
is introduced. Existing strict WAL/temp0 and full-register gates remain Main's.

## Local Verification

From `endchain_v1` with its pinned pglast v7.20 / PostgreSQL 17 parser available:

```text
python -B quota_candidate_v1/test_quota_candidate.py --source-root <checkout-root> -v
```

Tests use explicit checkout bytes and an isolated copied source tree. Catalog
samples are synthetic. SQL and PL/pgSQL parsing, artifact/binding tampering,
frozen pins, caps, source/expiry, private-target rejection and retention emission
are tested offline. No real DDL, trigger behavior, Auth, fullchain or CI PASS is
claimed. Main owns review, integration, execution and evidence collection.
