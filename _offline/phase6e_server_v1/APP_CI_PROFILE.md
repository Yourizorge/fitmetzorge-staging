# Canonical45 App CI

Source base: `c64f0bc4637bd9153b5339d015b14d768eaf965b`.
This patch is local CI preparation, not a hosted admission or a migration receipt.

## Required Integration

- Merge the coordinator's `_offline/phase6e11/endchain_v1/ci_source_binding.py`
  (`verify_all(checkout, candidate, files)`)
  and bootstrap allowlist corrections. Both prebuild and final advisor checks are required.
  The inherited endchain `fetch()` alone writes `loaded-source-preflight.json`;
  app `fetch()` must not repeat that exclusive write. App advisors retain the
  separate `verify_all()` and `loaded-source-final.json` after later imports.
- Merge Agent A's shared meter support for `gate.cli_profile == "local_app"`.
  Keep `cli_meter.run(gate, args, timeout)`. Each receipt must expose
  `profile: "local_app"`, actual arguments, dry-run status, exit code, complete
  protocol commands, confirmed observer commands and numeric protocol coverage.
  Do not apply an endchain quota/pre_auth/final slot, capacity_reserved or
  charged_commands to this profile. No SQL logging or numeric checks are removed.
- Include app-local `ci_profile.py`, `test_ci_profile.py` and updated
  CI/dossier/test sources in the source-bound candidate. Source binding belongs
  to the coordinator's endchain source list, never the app-local `NEW` list.
  Retain all 45 canonical
  SQL files unchanged and both existing isolated app SQL files unchanged.
- Coordinator commits all checked execution sources before building/dispatching;
  mixed checkout/candidate Python imports must fail before DB setup and at final
  verification. Candidate-only historical helper exceptions remain coordinator-owned.

## Actual Execution

The platform runner really applies canonical migrations 1 through 45. No canonical
migration is skipped, mocked, renamed or rewritten. Its existing identity/history,
PG17.6, workflow/request/controller ACL and quota-M45 database checks remain.
App install/rebuild/regression/advisor dispatch calls the platform base directly,
not registered endchain runtime or endchain allowance hooks.

Four measured app invocations, in order:

1. `db push --local --skip-vault --yes --include-all`: the existing app schema.
2. `db push --local --dry-run --skip-vault`: no pending migration, before minimal tests.
3. `db push --local --skip-vault --yes --include-all`: the existing app outbox.
4. `db push --local --dry-run --skip-vault`: final empty check after regressions.

`--include-all` is restricted to the two app installation slots in disposable CI.
The older app timestamps are intentional. Minimal history is exactly 46 and full
history exactly 47; both sorted histories end at canonical quota version
`20261018070231`, not at the app timestamp. Every version is checked against the
source manifest, not only the count or final row.

Evidence: `app-canonical-history.json`, `registration12-minimal-history.json`,
`candidate-47-history.json`, four original protocol/numeric/isolation sets,
`app-cli-profile.json`, `loaded-source-preflight.json`, `loaded-source-final.json`.
Historical 44+1/2 dossiers remain explicitly legacy; they are not upgraded to this
profile. Current dossiers report actual observations, not the old proposed 4135
allowance or any endchain allowance. Accepted product rules and default-off21 do
not change.

## Verification And Rollback

Unit tests exercise the real canonical source inventory and pure history/profile
contracts; they do not substitute for actual PostgreSQL/Auth/browser CI. No CI,
hosted call, commit or push was performed by this patch's author. Coordinator must
obtain fresh source-bound 47-migration CI before admitting the candidate.

Fetch regression tests execute the real app/endchain/guard inheritance and the
platform's exclusive `save()` implementation. Only the network-fetch boundary and
source-verifier result are mocked; source-verifier failures must still propagate.
The isolated c64 base lacks the coordinator's updated parent. For local testing,
load that real parent from the read-only coordinator root; do not replace its
`fetch()` or weaken the one-write assertion. Integrated CI uses its own parent.

Before integration, omit this patch to return to the earlier (incompatible) app-CI
profile. For an executed disposable stack, discard that stack through the existing
CI lifecycle; never rewind canonical migration history or delete durable audit.
