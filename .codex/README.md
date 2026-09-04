# FitMetZorge Staging Autonomy

Owner-authorized on 2026-09-04. Applies only to this trusted repository.

## Configuration

- approval_policy = on-request
- approvals_reviewer = auto_review
- sandbox_mode = workspace-write
- sandbox_workspace_write.network_access = true
- No additional writable roots; no never or danger-full-access setting.
- App approvals inherit project auto_review. The five existing local GitHub tool
  overrides are explicitly set to auto in this project, not unconditional approve.
- The project reviewer policy checks the exact staging repository/branch and Supabase
  project. It does not grant permission for other projects, production, member-data
  destruction, secrets exposure, new costs or unapproved product decisions.

AGENTS.md records permanent approved-package autonomy and the staging-only boundaries.
Automatic review is risk-based, not automatic approval of every request. Managed rules,
OAuth/backend permissions and tool-specific policies still apply. Network access is not
a project-ref firewall; target validation remains mandatory for every remote write.

## One-Time Activation

The actual Git checkout is:

C:/Users/Fitme/OneDrive/Documenten/Fit Met Zorge/Zip github fitmetzorge staging/fitmetzorge-staging-main/supabase/.temp/phase4fb-staging-deploy

Open that folder as the Codex project and mark that exact folder trusted once. Then use
a new task/session in that project. The older task rooted at the separate assets folder
does not load this sibling checkout's project configuration. Restarting the whole app
is not intrinsically required; a running task's managed permission snapshot is not
retroactively relaxed by editing this file.

No global user config or account-wide connector permission was changed. The read-only
user-config audit found the assets folder trusted but not this actual Git checkout.
An app-server config/read check confirmed the project layer was skipped for that reason.

## Validation

Codex CLI 0.153.0-alpha.5 validated the configuration with app-server --strict-config
and config/read. A process-only trusted-project override was used to test loading; it
was not persisted. The resulting settings came from this project's config:
on-request, auto_review, workspace-write, network_access=true, writable_roots=[],
project reviewer policy loaded, app default and GitHub reviewer auto_review,
all five GitHub tool overrides auto.

Existing ChatGPT connector settings were inspected, not changed:
Supabase inherits Allow low-risk actions; GitHub has an account-wide Allow all actions
override. That external permission is not a repository-scoped ACL. This project config
does not widen it, and restores reviewable modes for the five Codex tool overrides.
No project-scoped external connector-permission mutation API was available, so no
account-wide permission update was attempted.

Official references:
- [Configuration and project trust](https://learn.chatgpt.com/docs/config-file/config-basic)
- [Reviewer, sandbox and app settings](https://learn.chatgpt.com/docs/config-file/config-reference)

## Resumed Migration Reconciliation

6D-0 remains canonical at 20260904105918 with its exact reviewed checksum and single
live history entry. No SQL was replayed.

The next read-only inventory compared committed Git blobs (not autocrlf working copies)
with all 21 history records. Of 24 Git migrations:
- 6D-0 is byte-exact.
- Thirteen older artifacts match after CRLF/outer-whitespace normalization only.
- Seven other recorded artifacts still require a statement-level comparison. One
  history record contains 95 parsed statements, so its joined-string hash cannot
  establish original file-byte equality.
- Three artifacts have no same-name live history record.

These are evidence categories, not proof that the seven differ semantically.
No older version was mass-renamed, marked reverted/applied or executed based on a
name/whitespace match. The broader deployment gate stays fail-closed until its remaining
artifact and baseline checks are resolved. See the migration reconciliation receipt.
