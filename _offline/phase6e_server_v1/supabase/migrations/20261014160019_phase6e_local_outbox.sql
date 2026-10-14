-- LOCAL/CI ONLY. No canonical hosted application is authorized.
begin;
set local lock_timeout='1s';
set local statement_timeout='5s';
create table fmz6e_integration_private.outbox(
 workspace_id uuid not null references fmz6e_integration_private.workspaces(id),
 event_key text not null check(event_key ~ '^[0-9a-f]{64}$'),
 source_sha text not null check(source_sha ~ '^[0-9a-f]{64}$'),
 kind text not null check(kind in ('records_changed','proposal_pending')),
 status text not null check(status in ('pending','seen','declined','superseded','expired','applied','withdrawn')),
 created_at timestamptz not null default clock_timestamp(),
 expires_at timestamptz not null,
 history jsonb not null check(jsonb_typeof(history)='array' and jsonb_array_length(history) between 1 and 251),
 primary key(workspace_id,event_key)
);
alter table fmz6e_integration_private.outbox enable row level security;
create policy outbox_read on fmz6e_integration_private.outbox for select to fmz6e_integration_server
 using(exists(select 1 from fmz6e_integration_private.workspaces w where w.id=workspace_id and fmz6e_integration_private.actor() in(w.member_id,w.trainer_id)));
create policy outbox_insert on fmz6e_integration_private.outbox for insert to fmz6e_integration_server
 with check(exists(select 1 from fmz6e_integration_private.workspaces w where w.id=workspace_id and fmz6e_integration_private.actor() in(w.member_id,w.trainer_id) and w.consent and outbox.expires_at<=w.expires_at));
create policy outbox_update on fmz6e_integration_private.outbox for update to fmz6e_integration_server
 using(exists(select 1 from fmz6e_integration_private.workspaces w where w.id=workspace_id and fmz6e_integration_private.actor() in(w.member_id,w.trainer_id)))
 with check(exists(select 1 from fmz6e_integration_private.workspaces w where w.id=workspace_id and fmz6e_integration_private.actor() in(w.member_id,w.trainer_id) and (w.consent or status='withdrawn')));
grant select,insert on fmz6e_integration_private.outbox to fmz6e_integration_server;
grant update(status,history) on fmz6e_integration_private.outbox to fmz6e_integration_server;

create function fmz6e_integration_private.outbox_append() returns trigger
language plpgsql security invoker set search_path=pg_catalog,pg_temp as $f$
begin
 if NEW.workspace_id<>OLD.workspace_id or NEW.event_key<>OLD.event_key or NEW.source_sha<>OLD.source_sha
 or NEW.kind<>OLD.kind or NEW.created_at<>OLD.created_at or NEW.expires_at<>OLD.expires_at
 or jsonb_array_length(NEW.history)<>jsonb_array_length(OLD.history)+1
 or NEW.history-(jsonb_array_length(NEW.history)-1)<>OLD.history
 or NEW.history->-1->>'status'<>NEW.status then
 raise exception using errcode='42501',message='outbox_history_immutable'; end if;
 return NEW;
end $f$;
revoke all on function fmz6e_integration_private.outbox_append() from public,anon,authenticated,service_role;
grant execute on function fmz6e_integration_private.outbox_append() to fmz6e_integration_server;
create trigger outbox_append before update on fmz6e_integration_private.outbox for each row execute function fmz6e_integration_private.outbox_append();

create or replace function fmz6e_integration_private.observe() returns trigger
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
  when TG_TABLE_NAME='outbox' then jsonb_build_array(w,row_value->'event_key')
  else jsonb_build_array(w,row_value->'request_id') end;
 insert into fmz6e_integration_private.audit(fixture_run,workspace_id,request_id,actor_sha,xid,table_name,operation,key_sha)
 values(f,w,request,encode(sha256(convert_to(actor::text,'UTF8')),'hex'),pg_current_xact_id()::text,
 TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,TG_OP,encode(sha256(convert_to(row_key::text,'UTF8')),'hex'));
 return null;
end $f$;
create trigger integration_observe after insert or update or delete on fmz6e_integration_private.outbox
 for each row execute function fmz6e_integration_private.observe();
commit;
