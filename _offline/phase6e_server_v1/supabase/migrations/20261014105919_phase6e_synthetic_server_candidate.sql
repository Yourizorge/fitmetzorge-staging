-- LOCAL/CI candidate only. Not part of the canonical hosted migration directory.
begin;
set local lock_timeout='1s';
set local statement_timeout='5s';
create schema fmz6e_integration_private;
revoke all on schema fmz6e_integration_private from public,anon,authenticated,service_role;
create role fmz6e_integration_server nologin nosuperuser nocreatedb nocreaterole noinherit nobypassrls;
grant usage on schema fmz6e_integration_private to fmz6e_integration_server;

create table fmz6e_integration_private.subjects(
 user_id uuid primary key references auth.users(id),
 synthetic boolean not null check(synthetic),
 enabled boolean not null default false,
 expires_at timestamptz not null
);
create table fmz6e_integration_private.workspaces(
 id uuid primary key,
 fixture_run uuid not null,
 member_id uuid not null references fmz6e_integration_private.subjects(user_id),
 trainer_id uuid references fmz6e_integration_private.subjects(user_id),
 owner_id uuid not null references fmz6e_integration_private.subjects(user_id),
 route text not null check(route in ('A','B')),
 version integer not null default 0 check(version between 0 and 250),
 consent boolean not null default true,
 expires_at timestamptz not null,
 state_text text not null check(octet_length(state_text)<=8388608 and jsonb_typeof(state_text::jsonb)='object'),
 state_sha text not null check(state_sha ~ '^[0-9a-f]{64}$'),
 check((route='A' and trainer_id is not null and trainer_id<>member_id) or (route='B' and trainer_id is null))
);
create table fmz6e_integration_private.revisions(
 workspace_id uuid not null references fmz6e_integration_private.workspaces(id),
 version integer not null check(version between 0 and 250),
 request_id uuid,
 state_text text not null,
 state_sha text not null check(state_sha ~ '^[0-9a-f]{64}$'),
 primary key(workspace_id,version)
);
create table fmz6e_integration_private.requests(
 workspace_id uuid not null references fmz6e_integration_private.workspaces(id),
 request_id uuid not null,
 actor_id uuid not null,
 payload_sha text not null check(payload_sha ~ '^[0-9a-f]{64}$'),
 version integer not null,
 primary key(workspace_id,request_id),
 foreign key(workspace_id,version) references fmz6e_integration_private.revisions(workspace_id,version)
);
create table fmz6e_integration_private.audit(
 id bigint generated always as identity primary key,
 fixture_run uuid not null,
 workspace_id uuid not null,
 request_id uuid not null,
 actor_sha text not null,
 xid text not null,
 table_name text not null,
 operation text not null check(operation in ('INSERT','UPDATE','DELETE')),
 key_sha text not null,
 at timestamptz not null default clock_timestamp()
);
create index integration_audit_workspace on fmz6e_integration_private.audit(workspace_id,id);

create function fmz6e_integration_private.actor() returns uuid
language sql stable security invoker set search_path=pg_catalog,pg_temp as $f$
 select p.user_id from fmz6e_integration_private.subjects p
 where p.user_id=(nullif(current_setting('request.jwt.claims',true),'')::jsonb->>'sub')::uuid
 and nullif(current_setting('fmz6e.verified_session',true),'')::uuid=
     (nullif(current_setting('request.jwt.claims',true),'')::jsonb->>'session_id')::uuid
 and p.synthetic and p.enabled and p.expires_at>now()
$f$;
create function fmz6e_integration_private.observe() returns trigger
language plpgsql security invoker set search_path=pg_catalog,pg_temp as $f$
declare row_value jsonb; w uuid; f uuid; actor uuid; request uuid; row_key jsonb;
begin
 row_value:=case when TG_OP='DELETE' then to_jsonb(OLD) else to_jsonb(NEW) end;
 w:=coalesce(row_value->>'workspace_id',row_value->>'id')::uuid;
 actor:=fmz6e_integration_private.actor();
 request:=nullif(current_setting('fmz6e.request_id',true),'')::uuid;
 if actor is null or request is null then raise exception using errcode='42501',message='integration_audit_binding'; end if;
 if TG_TABLE_NAME='workspaces' then f:=(row_value->>'fixture_run')::uuid;
 else select fixture_run into strict f from fmz6e_integration_private.workspaces where id=w; end if;
 row_key:=case when TG_TABLE_NAME='workspaces' then jsonb_build_array(w)
  when TG_TABLE_NAME='revisions' then jsonb_build_array(w,row_value->'version')
  else jsonb_build_array(w,row_value->'request_id') end;
 insert into fmz6e_integration_private.audit(fixture_run,workspace_id,request_id,actor_sha,xid,table_name,operation,key_sha)
 values(f,w,request,encode(sha256(convert_to(actor::text,'UTF8')),'hex'),pg_current_xact_id()::text,
 TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,TG_OP,encode(sha256(convert_to(row_key::text,'UTF8')),'hex'));
 return null;
end $f$;

alter table fmz6e_integration_private.subjects enable row level security;
alter table fmz6e_integration_private.workspaces enable row level security;
alter table fmz6e_integration_private.revisions enable row level security;
alter table fmz6e_integration_private.requests enable row level security;
alter table fmz6e_integration_private.audit enable row level security;
create policy subject_self on fmz6e_integration_private.subjects for select to fmz6e_integration_server
 using(user_id=(nullif(current_setting('request.jwt.claims',true),'')::jsonb->>'sub')::uuid);
create policy workspace_read on fmz6e_integration_private.workspaces for select to fmz6e_integration_server
 using(fmz6e_integration_private.actor() in (member_id,trainer_id,owner_id) and expires_at>now());
create policy workspace_write on fmz6e_integration_private.workspaces for update to fmz6e_integration_server
 using(fmz6e_integration_private.actor() in (member_id,trainer_id) and consent and expires_at>now())
 with check(fmz6e_integration_private.actor() in (member_id,trainer_id));
create policy revision_read on fmz6e_integration_private.revisions for select to fmz6e_integration_server
 using(exists(select 1 from fmz6e_integration_private.workspaces w where w.id=workspace_id));
create policy revision_insert on fmz6e_integration_private.revisions for insert to fmz6e_integration_server
 with check(exists(select 1 from fmz6e_integration_private.workspaces w where w.id=workspace_id
 and fmz6e_integration_private.actor() in (w.member_id,w.trainer_id) and w.expires_at>now()));
create policy request_read on fmz6e_integration_private.requests for select to fmz6e_integration_server
 using(exists(select 1 from fmz6e_integration_private.workspaces w where w.id=workspace_id));
create policy request_insert on fmz6e_integration_private.requests for insert to fmz6e_integration_server
 with check(actor_id=fmz6e_integration_private.actor() and exists(
 select 1 from fmz6e_integration_private.workspaces w where w.id=workspace_id
 and fmz6e_integration_private.actor() in (w.member_id,w.trainer_id) and w.expires_at>now()));
create policy audit_read on fmz6e_integration_private.audit for select to fmz6e_integration_server
 using(exists(select 1 from fmz6e_integration_private.workspaces w where w.id=workspace_id));
create policy audit_insert on fmz6e_integration_private.audit for insert to fmz6e_integration_server
 with check(request_id=nullif(current_setting('fmz6e.request_id',true),'')::uuid and
 actor_sha=encode(sha256(convert_to(fmz6e_integration_private.actor()::text,'UTF8')),'hex'));

grant select on all tables in schema fmz6e_integration_private to fmz6e_integration_server;
grant update(version,consent,state_text,state_sha) on fmz6e_integration_private.workspaces to fmz6e_integration_server;
grant insert on fmz6e_integration_private.revisions,fmz6e_integration_private.requests,fmz6e_integration_private.audit to fmz6e_integration_server;
grant usage on all sequences in schema fmz6e_integration_private to fmz6e_integration_server;
revoke all on all functions in schema fmz6e_integration_private from public,anon,authenticated,service_role;
grant execute on all functions in schema fmz6e_integration_private to fmz6e_integration_server;
create trigger integration_observe after insert or update or delete on fmz6e_integration_private.workspaces
 for each row execute function fmz6e_integration_private.observe();
create trigger integration_observe after insert or update or delete on fmz6e_integration_private.revisions
 for each row execute function fmz6e_integration_private.observe();
create trigger integration_observe after insert or update or delete on fmz6e_integration_private.requests
 for each row execute function fmz6e_integration_private.observe();
commit;
