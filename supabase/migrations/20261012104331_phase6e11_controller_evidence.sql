-- Controller evidence only. Empty/default closed; no application or Auth writes.
begin;
set local lock_timeout='1s';
set local statement_timeout='15s';
create schema fmz6e11_controller_private authorization postgres;
revoke all on schema fmz6e11_controller_private from public,anon,authenticated,service_role;
alter default privileges in schema fmz6e11_controller_private revoke execute on functions from public;

create table fmz6e11_controller_private.runs (
 id uuid primary key,
 github_run bigint not null unique check(github_run>0),
 head_sha text not null check(head_sha ~ '^[0-9a-f]{40}$'),
 manifest_sha text not null check(manifest_sha ~ '^[0-9a-f]{64}$'),
 created_at timestamptz not null default clock_timestamp(),
 expires_at timestamptz not null,
 state text not null default 'running' check(state in ('running','stopped','complete','closed')),
 next_step integer not null default 0 check(next_step>=0),
 command_count integer not null default 0 check(command_count between 0 and 128),
 closed_at timestamptz,
 check(expires_at>created_at and expires_at<=created_at+interval '10 minutes')
);
-- Claim this unique slot, then check expiry while holding the row lock.
create unique index one_running_controller on fmz6e11_controller_private.runs ((true)) where state='running';

create table fmz6e11_controller_private.steps (
 run_id uuid not null references fmz6e11_controller_private.runs,
 step integer not null check(step>=0),
 action_id uuid not null unique,
 request_id uuid not null unique,
 actor uuid not null,
 workspace uuid,
 kind text not null check(kind in ('auth','workflow','lifecycle','access','cleanup')),
 operation text not null check(operation ~ '^[a-z][a-z0-9_]{0,63}$'),
 contract_sha text not null check(contract_sha ~ '^[0-9a-f]{64}$'),
 state text not null default 'before_saved' check(state in ('before_saved','action_started','action_confirmed','after_saved','pair_validated','stopped')),
 primary key(run_id,step)
);
create table fmz6e11_controller_private.evidence (
 run_id uuid not null,
 step integer not null,
 phase text not null check(phase in ('before_saved','action_started','action_confirmed','after_saved','pair_validated','stopped')),
 recorded_at timestamptz not null default clock_timestamp(),
 metadata jsonb not null check(jsonb_typeof(metadata)='object' and octet_length(metadata::text)<=65536),
 sha256 text not null check(sha256 ~ '^[0-9a-f]{64}$'),
 primary key(run_id,step,phase),
 foreign key(run_id,step) references fmz6e11_controller_private.steps
);
alter table fmz6e11_controller_private.runs enable row level security;
alter table fmz6e11_controller_private.steps enable row level security;
alter table fmz6e11_controller_private.evidence enable row level security;
revoke all on all tables in schema fmz6e11_controller_private from public,anon,authenticated,service_role;
-- No SQL function, exposed RPC, managed-schema observer or default grant.
commit;
