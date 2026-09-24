-- Additive, private packaging of the reviewed workflow_bridge_v1 adapter.
-- No existing workflow/audit definition, ACL, row or trigger is replaced.
begin;
set local lock_timeout = '1s';
set local statement_timeout = '15s';

do $preflight$
begin
 if current_user <> 'postgres' then raise exception 'bridge_server_role_required'; end if;
 if current_setting('server_version_num')::integer not between 170000 and 179999
 then raise exception 'bridge_pg17_required'; end if;
 if (select encode(sha256(convert_to(prosrc,'UTF8')),'hex') from pg_proc
     where oid='fmz6e11_private.api_call(jsonb)'::regprocedure) is distinct from
 '4cb3383993916475f1da1562c0fbb557c850d95505869361a9336220bf7aed92'
 then raise exception 'bridge_original_source_unreviewed'; end if;
 if to_regprocedure('fmz6e11_audit_private.confirm_action(uuid)') is null
 then raise exception 'bridge_audit_core_required'; end if;
end $preflight$;

create schema fmz6e11_workflow_audit authorization postgres;
revoke all on schema fmz6e11_workflow_audit from public,anon,authenticated,service_role;

create table fmz6e11_workflow_audit.control (
 id boolean primary key default true check(id),
 enabled boolean not null default false,
 original_body_sha text not null check(original_body_sha~'^[0-9a-f]{64}$')
);
create table fmz6e11_workflow_audit.intents (
 -- Resolve against the existing action in call(); no FK triggers on old tables.
 action_id uuid primary key,
 session_id uuid not null,
 request_sha text not null check(request_sha~'^[0-9a-f]{64}$'),
 expected_status integer not null check(expected_status between 200 and 599),
 expected_versions jsonb not null check(jsonb_typeof(expected_versions)='object'),
 request_id uuid not null
);
create index intents_request_binding_idx
 on fmz6e11_workflow_audit.intents(session_id,request_sha,request_id);
alter table fmz6e11_workflow_audit.control enable row level security;
alter table fmz6e11_workflow_audit.intents enable row level security;
revoke all on all tables in schema fmz6e11_workflow_audit from public,anon,authenticated,service_role;
insert into fmz6e11_workflow_audit.control(original_body_sha)
 values('4cb3383993916475f1da1562c0fbb557c850d95505869361a9336220bf7aed92');

create function fmz6e11_workflow_audit.versions(p_window_id uuid) returns jsonb
language sql security invoker set search_path=pg_catalog,pg_temp as $v$
 select jsonb_build_object('revision',w.revision,'a_version',a.active_version,'b_version',b.active_version)
 from fmz6e11_private.windows w
 join fmz6e11_private.workspaces a on a.window_id=w.id and a.route='A'
 join fmz6e11_private.workspaces x on x.window_id=w.id and x.route='B'
 join fmz6e11_private.b_states b on b.workspace_id=x.id
 where w.id=p_window_id
$v$;

-- This is a server entry, NOT a PostgREST/public RPC. JWT verification belongs to
-- the trusted transport; the unchanged principal also verifies the live session.
create function fmz6e11_workflow_audit.call(input jsonb) returns jsonb
language plpgsql security invoker set search_path=pg_catalog,pg_temp as $bridge$
declare c fmz6e11_workflow_audit.control;i fmz6e11_workflow_audit.intents;
 q jsonb;principal jsonb;claims jsonb;headers jsonb;
 v_session_id uuid;v_request_sha text;v_request_id uuid;result jsonb;actual_sha text;
begin
 if current_user <> 'postgres' then
 raise exception using errcode='42501',message='bridge_server_role_required';end if;
 select * into c from fmz6e11_workflow_audit.control where id;
 if not found then raise exception using errcode='P0001',message='bridge_control_missing';end if;
 if not c.enabled then raise exception using errcode='P0001',message='bridge_disabled';end if;
 select encode(sha256(convert_to(prosrc,'UTF8')),'hex') into actual_sha
 from pg_proc where oid='fmz6e11_private.api_call(jsonb)'::regprocedure;
 if actual_sha is distinct from c.original_body_sha then
 raise exception using errcode='P0001',message='bridge_original_changed';end if;
 q:=case when input->>'op'='internal_b' then input->'request' else input end;
 if q->>'op' is distinct from 'command' or q->>'action' is null or q->>'action' not in
 ('source_append','source_withdraw','propose','restore','member_accept','trainer_approve','apply',
 'member_reject','trainer_reject','trainer_block','b_build','b_edit','b_confirm','b_apply',
 'b_reject','b_restore','b_reopen','viewed','later') then
 raise exception using errcode='P0001',message='bridge_route_not_admitted';end if;
 if not pg_try_advisory_xact_lock(611,20260924) then
 raise exception using errcode='P0001',message='bridge_collector_busy';end if;
 principal:=fmz6e11_private.principal();
 -- An empty registry must never turn absent observations into a false PASS.
 if exists(select 1 from pg_class t join pg_namespace n on n.oid=t.relnamespace
 where t.relkind='r' and (n.nspname='fmz6e11_private' or
 t.oid in ('public.profiles'::regclass,'auth.users'::regclass,'auth.sessions'::regclass))
 and not exists(select 1 from fmz6e11_audit_private.relations r where r.rel=t.oid)) then
 raise exception using errcode='P0001',message='bridge_observer_registry_incomplete';end if;
 claims:=coalesce(nullif(current_setting('request.jwt.claims',true),''),'{}')::jsonb;
 headers:=coalesce(nullif(current_setting('request.headers',true),''),'{}')::jsonb;
 if coalesce(headers->>'x-fmz6e11-request-id','') !~
 '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
 then raise exception using errcode='P0001',message='bridge_request_id_required';end if;
 v_request_id:=(headers->>'x-fmz6e11-request-id')::uuid;
 v_session_id:=(claims->>'session_id')::uuid;
 v_request_sha:=encode(sha256(convert_to(input::text,'UTF8')),'hex');
 begin
 select intent.* into strict i
 from fmz6e11_workflow_audit.intents intent
 join fmz6e11_audit_private.actions act on act.id=intent.action_id
 join fmz6e11_audit_private.runs r on r.id=act.run_id
 where act.actor=(principal->>'uid')::uuid and act.workspace=(q->>'workspace')::uuid
 and intent.session_id=v_session_id and intent.request_sha=v_request_sha
 and intent.request_id=v_request_id
 and act.state='before_saved' and r.enabled and r.expires_at>clock_timestamp()
 for update of intent;
 exception
 when no_data_found then raise exception using errcode='P0001',message='bridge_intent_missing';
 when too_many_rows then raise exception using errcode='P0001',message='bridge_intent_ambiguous';
 end;
 perform fmz6e11_audit_private.start_action(i.action_id);
 result:=fmz6e11_private.api_call(input);
 if coalesce((result->>'http_status')::integer,200)<>i.expected_status then
 raise exception using errcode='P0001',message='bridge_response_contract';end if;
 if fmz6e11_workflow_audit.versions((q->>'window')::uuid) is distinct from i.expected_versions then
 raise exception using errcode='P0001',message='bridge_version_contract';end if;
 perform fmz6e11_audit_private.confirm_action(i.action_id);
 return result;
end $bridge$;
revoke all on all functions in schema fmz6e11_workflow_audit from public,anon,authenticated,service_role;
commit;
