-- 6E-9: additive, standard-off synthetic namespace. No existing rows are inputs.
begin;
create schema fmz6e9_private;
revoke all on schema fmz6e9_private from public, anon, authenticated, service_role;
create table fmz6e9_private.config (
 id boolean primary key default true check(id), enabled boolean not null default false,
 proof_hash text check(proof_hash ~ '^[0-9a-f]{64}$'),
 source_revision integer not null default 1 check(source_revision>0),
 model_sha256 text not null default '1993a8073f40c583f108cc6baa2ef78c1d522d52b81b0f6071f10f109ca4753b'
);
insert into fmz6e9_private.config(id) values(true);
create table fmz6e9_private.subjects (
 workspace uuid primary key, member_id uuid not null unique references auth.users(id),
 route text not null check(route in ('A','B')), trainer_id uuid references auth.users(id),
 seed text not null default 'normal', eligibility_revision integer not null default 1,
 consent boolean not null default true, consent_revision integer not null default 1,
 expires_at timestamptz not null check(expires_at<=created_at+interval '24 hours'),
 created_at timestamptz not null default clock_timestamp(),
 context_required boolean not null default false,
 revision bigint not null default 0, active_version integer not null default 0,
 status text not null default 'intake', candidate_hash text, candidate_basis jsonb,
 member_approval jsonb, trainer_approval jsonb, events jsonb not null default '[]',
 check((route='A' and trainer_id is not null) or (route='B' and trainer_id is null)),
 check(jsonb_typeof(events)='array' and jsonb_array_length(events)<=500)
);
create index subjects_trainer on fmz6e9_private.subjects(trainer_id);
create table fmz6e9_private.safety (
 workspace uuid not null references fmz6e9_private.subjects(workspace) on delete cascade,
 first_registered_at timestamptz not null, message_ref uuid not null,
 status text not null check(status in ('current','serious','recurring','unclassified','self_reported','missing','misunderstanding','technical')),
 necessary boolean not null default true,
 primary key(workspace,message_ref)
);
create table fmz6e9_private.versions (
 workspace uuid not null references fmz6e9_private.subjects(workspace) on delete cascade,
 version integer not null, content jsonb not null, content_hash text not null,
 source_basis jsonb not null, created_at timestamptz not null default clock_timestamp(),
 primary key(workspace,version)
);
create table fmz6e9_private.requests (
 workspace uuid not null references fmz6e9_private.subjects(workspace) on delete cascade,
 actor uuid not null references auth.users(id), request_id uuid not null,
 payload_hash text not null, result jsonb not null, created_at timestamptz not null default clock_timestamp(),
 primary key(workspace,actor,request_id)
);
create index requests_actor on fmz6e9_private.requests(actor);
create table public.fmz6e9_audit (
 id bigint generated always as identity primary key,
 workspace uuid not null references fmz6e9_private.subjects(workspace) on delete cascade,
 actor uuid not null, actor_role text not null check(actor_role in ('member','trainer')),
 action text not null, proposal_hash text, source_version integer not null, target_version integer not null,
 status text not null, request_id uuid not null, at timestamptz not null default clock_timestamp()
);
create index fmz6e9_audit_workspace on public.fmz6e9_audit(workspace,id);
create table public.fmz6e9_notices (
 id bigint generated always as identity primary key,
 workspace uuid not null references fmz6e9_private.subjects(workspace) on delete cascade,
 recipient uuid not null, code text not null check(code in ('new','member_pending','trainer_pending','approved','rejected','ready','applied','restore','conflict','blocked')),
 request_id uuid not null, at timestamptz not null default clock_timestamp()
);
create index fmz6e9_notices_recipient on public.fmz6e9_notices(recipient,workspace,id);
create index fmz6e9_notices_workspace on public.fmz6e9_notices(workspace);
alter table fmz6e9_private.config enable row level security;
alter table fmz6e9_private.subjects enable row level security;
alter table fmz6e9_private.safety enable row level security;
alter table fmz6e9_private.versions enable row level security;
alter table fmz6e9_private.requests enable row level security;
alter table public.fmz6e9_audit enable row level security;
alter table public.fmz6e9_notices enable row level security;
revoke all on all tables in schema fmz6e9_private from public,anon,authenticated,service_role;
revoke all on public.fmz6e9_audit,public.fmz6e9_notices from public,anon,authenticated,service_role;
revoke all on sequence public.fmz6e9_audit_id_seq,public.fmz6e9_notices_id_seq from public,anon,authenticated,service_role;

-- Deliberate private boolean helper: RLS needs server fixture/profile authority.
create function fmz6e9_private.can_read(p_workspace uuid) returns boolean
language sql stable security definer set search_path=pg_catalog,pg_temp as $f$
 select auth.uid() is not null and exists(select 1 from auth.sessions
 where id=(coalesce(current_setting('request.jwt.claims',true),'{}')::jsonb->>'session_id')::uuid
 and user_id=auth.uid() and (not_after is null or not_after>now())) and exists(
 select 1 from fmz6e9_private.subjects s
 join fmz6e9_private.config c on c.id and c.enabled
 join public.profiles m on m.id=s.member_id and m.role='client'
 where s.workspace=p_workspace and s.expires_at>now()
 and (s.member_id=auth.uid() or (s.route='A' and s.trainer_id=auth.uid()
 and m.trainer_id=s.trainer_id and exists(select 1 from public.profiles t where t.id=s.trainer_id and t.role='trainer'))))
$f$;
revoke all on function fmz6e9_private.can_read(uuid) from public,anon,authenticated,service_role;
grant usage on schema fmz6e9_private to authenticated;
grant execute on function fmz6e9_private.can_read(uuid) to authenticated;
grant select on public.fmz6e9_audit,public.fmz6e9_notices to authenticated;
create policy fmz6e9_audit_read on public.fmz6e9_audit for select to authenticated
 using(fmz6e9_private.can_read(workspace));
create policy fmz6e9_notices_read on public.fmz6e9_notices for select to authenticated
 using(recipient=(select auth.uid()) and fmz6e9_private.can_read(workspace));
-- No client INSERT/UPDATE/DELETE grant or policy. No views or role-metadata authority.

create function fmz6e9_private.context(p_workspace uuid) returns jsonb
language plpgsql security definer set search_path=pg_catalog,pg_temp as $f$
declare c fmz6e9_private.config; s fmz6e9_private.subjects; m public.profiles;
 t public.profiles; v_uid uuid:=auth.uid(); v_role text; v_proof text;
begin
 select * into c from fmz6e9_private.config where id for share;
 v_proof:=coalesce(current_setting('request.headers',true),'{}')::jsonb->>'x-fmz6e9-proof';
 if v_uid is null or not c.enabled or c.proof_hash is null or v_proof is null
 or encode(sha256(convert_to(v_proof,'UTF8')),'hex')<>c.proof_hash then
 raise exception using errcode='42501',message='synthetic_access_denied'; end if;
 if not exists(select 1 from auth.sessions
 where id=(coalesce(current_setting('request.jwt.claims',true),'{}')::jsonb->>'session_id')::uuid
 and user_id=v_uid and (not_after is null or not_after>clock_timestamp())) then raise exception using errcode='42501',message='synthetic_session_required'; end if;
 select * into s from fmz6e9_private.subjects where workspace=p_workspace for update;
 if not found or s.expires_at<=clock_timestamp() then
 raise exception using errcode='42501',message='synthetic_access_denied'; end if;
 -- Same server-owned legacy profile authority as 6D-0; never metadata.
 perform 1 from public.profiles where id in (s.member_id,s.trainer_id) order by id for share;
 select * into m from public.profiles where id=s.member_id;
 select * into t from public.profiles where id=s.trainer_id;
 if m.id is null or m.role<>'client' or
 (s.route='A' and (m.trainer_id is distinct from s.trainer_id or t.role is distinct from 'trainer')) or
 (s.route='B' and (m.trainer_id is not null or s.trainer_id is not null)) then
 raise exception using errcode='42501',message='synthetic_authority_conflict'; end if;
 v_role:=case when v_uid=s.member_id then 'member'
 when s.route='A' and v_uid=s.trainer_id then 'trainer' else null end;
 if v_role is null then raise exception using errcode='42501',message='synthetic_access_denied'; end if;
 return jsonb_build_object('role',v_role,'route',s.route,'member',s.member_id,'trainer',s.trainer_id,
 'basis',jsonb_build_object('source',c.source_revision,'model',c.model_sha256,'eligibility',s.eligibility_revision,
 'consent',s.consent_revision,'trainer',s.trainer_id,'member_profile',m.updated_at,'trainer_profile',t.updated_at),
 'consent',s.consent);
end $f$;

create function fmz6e9_private.read_state(p_workspace uuid) returns jsonb
language plpgsql security definer set search_path=pg_catalog,pg_temp as $f$
declare ctx jsonb; s fmz6e9_private.subjects; guard text:='clear';
begin
 ctx:=fmz6e9_private.context(p_workspace);
 select * into s from fmz6e9_private.subjects where workspace=p_workspace;
 if s.context_required then guard:='missing'; end if;
 -- Expired/needless O5 rows are physically removed; an eligibility revision
 -- change makes previous context unusable without retaining old health contents.
 if exists(select 1 from fmz6e9_private.safety where workspace=p_workspace
 and (not necessary or first_registered_at+interval '30 days'<=clock_timestamp())) then
 delete from fmz6e9_private.safety where workspace=p_workspace
 and (not necessary or first_registered_at+interval '30 days'<=clock_timestamp());
 update fmz6e9_private.subjects set eligibility_revision=eligibility_revision+1,
 context_required=true where workspace=p_workspace;
 guard:='missing';
 ctx:=fmz6e9_private.context(p_workspace);
 end if;
 select coalesce((select status from fmz6e9_private.safety where workspace=p_workspace
 order by case status when 'serious' then 0 when 'current' then 1 when 'recurring' then 2
 when 'unclassified' then 3 when 'self_reported' then 4 when 'missing' then 5 else 6 end,
 first_registered_at,message_ref limit 1),guard) into guard;
 return jsonb_build_object('workspace',s.workspace,'revision',s.revision,'route',ctx->>'route',
 'actor_role',ctx->>'role','basis',ctx->'basis','consent',ctx->'consent','seed',s.seed,
 'events',s.events,'guard',guard,'status',s.status,'candidate_hash',s.candidate_hash,
 'versions',(select coalesce(jsonb_agg(jsonb_build_object('version',version,'content_hash',content_hash)
 order by version),'[]') from fmz6e9_private.versions where workspace=p_workspace));
end $f$;

create function fmz6e9_private.commit_state(
 p_workspace uuid,p_key uuid,p_expected bigint,p_action text,p_payload jsonb,p_basis jsonb,p_next jsonb
) returns jsonb language plpgsql security definer set search_path=pg_catalog,pg_temp as $f$
declare ctx jsonb; s fmz6e9_private.subjects; replay fmz6e9_private.requests;
 v_hash text; v_result jsonb; v_status text; v_version integer; v_code text; v_bound jsonb;
begin
 ctx:=fmz6e9_private.context(p_workspace);
 select * into s from fmz6e9_private.subjects where workspace=p_workspace;
 if not s.consent then raise exception using errcode='42501',message='synthetic_consent_required'; end if;
 if p_key is null or p_expected is null or p_action is null or p_action not in
 ('open','build','edit','member_accept','member_reject','trainer_approve','trainer_reject','trainer_block',
 'confirm','apply','reject','reopen','restore','signal','photo','clarify') then
 raise exception using errcode='22023',message='synthetic_command_invalid'; end if;
 if (p_action like 'trainer_%' or (p_action='apply' and s.route='A')) and ctx->>'role'<>'trainer'
 or (p_action not like 'trainer_%' and not(p_action='apply' and s.route='A') and ctx->>'role'<>'member')
 or (s.route='B' and p_action in ('member_accept','member_reject','trainer_approve','trainer_reject','trainer_block'))
 then raise exception using errcode='42501',message='synthetic_actor_denied'; end if;
 v_hash:=encode(sha256(convert_to(jsonb_build_object('expected',p_expected,'action',p_action,'payload',p_payload)::text,'UTF8')),'hex');
 select * into replay from fmz6e9_private.requests where workspace=p_workspace and actor=auth.uid() and request_id=p_key;
 if found then
 if replay.payload_hash<>v_hash then raise exception using errcode='40001',message='synthetic_idempotency_conflict'; end if;
 return replay.result||jsonb_build_object('replay',true);
 end if;
 if s.revision<>p_expected or p_basis is distinct from ctx->'basis' then
 raise exception using errcode='40001',message='synthetic_version_conflict'; end if;
 if jsonb_array_length(s.events)>=500 or (select count(*) from fmz6e9_private.requests
 where actor=auth.uid() and created_at>clock_timestamp()-interval '1 minute')>=60
 then raise exception using errcode='54000',message='synthetic_session_limit'; end if;
 if p_action='open' and (s.route<>'A' or s.revision<>0) then raise exception 'synthetic_open_order'; end if;
 if (s.context_required or exists(select 1 from fmz6e9_private.safety where workspace=p_workspace))
 and p_action not in ('reject','member_reject','trainer_reject','trainer_block','clarify') then
 raise exception using errcode='42501',message='synthetic_safety_block'; end if;
 if p_action in ('member_accept','confirm','trainer_approve','apply')
 and s.candidate_basis is distinct from ctx->'basis' then
 raise exception using errcode='40001',message='synthetic_source_conflict'; end if;
 v_status:=p_next->>'status';
 v_version:=(p_next->>'version')::integer;
 if v_status not in ('member_pending','trainer_pending','approved','confirmed','applied','rejected','blocked','facts','intake')
 or v_version is null or jsonb_typeof(p_next->'event')<>'object' then
 raise exception using errcode='22023',message='synthetic_result_invalid'; end if;
 v_bound:=jsonb_build_object('hash',s.candidate_hash,'basis',s.candidate_basis);
 if p_action in ('member_accept','confirm') then
 if s.status<>'member_pending' or s.candidate_hash is null then raise exception 'synthetic_acceptance_order'; end if;
 update fmz6e9_private.subjects set member_approval=v_bound where workspace=p_workspace;
 elsif p_action='trainer_approve' then
 if s.status<>'trainer_pending' or s.member_approval is distinct from v_bound then raise exception 'synthetic_approval_order'; end if;
 update fmz6e9_private.subjects set trainer_approval=v_bound where workspace=p_workspace;
 elsif p_action='apply' then
 if s.status<>(case when s.route='A' then 'approved' else 'confirmed' end)
 or s.member_approval is distinct from v_bound
 or (s.route='A' and s.trainer_approval is distinct from v_bound)
 or (s.route='B' and s.trainer_approval is not null)
 or v_version<>s.active_version+1 or p_next->'content' is null then raise exception 'synthetic_application_order'; end if;
 insert into fmz6e9_private.versions(workspace,version,content,content_hash,source_basis)
 values(p_workspace,v_version,p_next->'content',encode(sha256(convert_to((p_next->'content')::text,'UTF8')),'hex'),ctx->'basis');
 elsif p_action in ('open','build','edit','reopen','restore','signal','photo') then
 update fmz6e9_private.subjects set member_approval=null,trainer_approval=null,
 candidate_basis=ctx->'basis',candidate_hash=p_next->>'candidate_hash' where workspace=p_workspace;
 elsif p_action='clarify' then
 delete from fmz6e9_private.safety where workspace=p_workspace and status in ('technical','misunderstanding');
 update fmz6e9_private.subjects set member_approval=null,trainer_approval=null where workspace=p_workspace;
 elsif p_action in ('reject','member_reject','trainer_reject','trainer_block') then
 update fmz6e9_private.subjects set member_approval=null,trainer_approval=null where workspace=p_workspace;
 end if;
 if p_action='open' then
 insert into fmz6e9_private.versions(workspace,version,content,content_hash,source_basis)
 values(p_workspace,s.active_version,p_next->'content',
 encode(sha256(convert_to((p_next->'content')::text,'UTF8')),'hex'),ctx->'basis');
 end if;
 if p_action<>'apply' and v_version<>s.active_version then raise exception 'synthetic_unexpected_version'; end if;
 update fmz6e9_private.subjects set revision=revision+1,status=v_status,
 active_version=v_version,events=events||jsonb_build_array(p_next->'event') where workspace=p_workspace;
 insert into public.fmz6e9_audit(workspace,actor,actor_role,action,proposal_hash,source_version,target_version,status,request_id)
 values(p_workspace,auth.uid(),ctx->>'role',p_action,
 coalesce(p_next->>'candidate_hash',s.candidate_hash),s.active_version,v_version,v_status,p_key);
 v_code:=case when p_action='restore' then 'restore' when p_action='apply' then 'applied'
 when v_status='confirmed' then 'ready' when v_status in ('trainer_pending','member_pending','approved','rejected','blocked') then v_status else 'new' end;
 insert into public.fmz6e9_notices(workspace,recipient,code,request_id) values(p_workspace,s.member_id,v_code,p_key);
 if s.route='A' and v_code in ('trainer_pending','approved','applied','restore','rejected','blocked') then
 insert into public.fmz6e9_notices(workspace,recipient,code,request_id) values(p_workspace,s.trainer_id,v_code,p_key);
 end if;
 v_result:=jsonb_build_object('revision',s.revision+1,'status',v_status,'version',v_version,'replay',false);
 insert into fmz6e9_private.requests(workspace,actor,request_id,payload_hash,result)
 values(p_workspace,auth.uid(),p_key,v_hash,v_result);
 return v_result;
end $f$;
revoke all on function fmz6e9_private.context(uuid),fmz6e9_private.read_state(uuid),
 fmz6e9_private.commit_state(uuid,uuid,bigint,text,jsonb,jsonb,jsonb) from public,anon,authenticated,service_role;
grant execute on function fmz6e9_private.read_state(uuid),
 fmz6e9_private.commit_state(uuid,uuid,bigint,text,jsonb,jsonb,jsonb) to authenticated;
-- Exposed wrappers have NO elevated privileges. Private helpers require both
-- auth.uid()/session/profile authorization AND the non-client Edge proof secret.
create function public.fmz6e9_read(p_workspace uuid) returns jsonb
language sql security invoker set search_path=pg_catalog,pg_temp as $f$
 select fmz6e9_private.read_state(p_workspace)
$f$;
create function public.fmz6e9_commit(p_workspace uuid,p_key uuid,p_expected bigint,p_action text,p_payload jsonb,p_basis jsonb,p_next jsonb)
returns jsonb language sql security invoker set search_path=pg_catalog,pg_temp as $f$
 select fmz6e9_private.commit_state(p_workspace,p_key,p_expected,p_action,p_payload,p_basis,p_next)
$f$;
revoke all on function public.fmz6e9_read(uuid),
 public.fmz6e9_commit(uuid,uuid,bigint,text,jsonb,jsonb,jsonb) from public,anon,authenticated,service_role;
grant execute on function public.fmz6e9_read(uuid),
 public.fmz6e9_commit(uuid,uuid,bigint,text,jsonb,jsonb,jsonb) to authenticated;
create function fmz6e9_private.home() returns jsonb
language plpgsql security definer set search_path=pg_catalog,pg_temp as $f$
declare s record; ctx jsonb; result jsonb:='[]';
begin
 if auth.uid() is null then raise exception using errcode='42501',message='synthetic_access_denied'; end if;
 for s in select workspace from fmz6e9_private.subjects
 where member_id=auth.uid() or trainer_id=auth.uid() order by workspace loop
 ctx:=fmz6e9_private.context(s.workspace);
 result:=result||jsonb_build_array(jsonb_build_object('workspace',s.workspace,'route',ctx->>'route','actor_role',ctx->>'role'));
 end loop;
 if result='[]'::jsonb then raise exception using errcode='42501',message='synthetic_access_denied'; end if;
 return result;
end $f$;
create function fmz6e9_private.replay_request(p_workspace uuid,p_key uuid,p_expected bigint,p_action text,p_payload jsonb)
returns jsonb language plpgsql security definer set search_path=pg_catalog,pg_temp as $f$
declare r fmz6e9_private.requests; h text;
begin
 perform fmz6e9_private.context(p_workspace);
 h:=encode(sha256(convert_to(jsonb_build_object('expected',p_expected,'action',p_action,'payload',p_payload)::text,'UTF8')),'hex');
 select * into r from fmz6e9_private.requests where workspace=p_workspace and actor=auth.uid() and request_id=p_key;
 if not found then return null; end if;
 if r.payload_hash<>h then raise exception using errcode='40001',message='synthetic_idempotency_conflict'; end if;
 return r.result||jsonb_build_object('replay',true);
end $f$;
revoke all on function fmz6e9_private.home(),
 fmz6e9_private.replay_request(uuid,uuid,bigint,text,jsonb) from public,anon,authenticated,service_role;
grant execute on function fmz6e9_private.home(),
 fmz6e9_private.replay_request(uuid,uuid,bigint,text,jsonb) to authenticated;
create function public.fmz6e9_home() returns jsonb language sql security invoker
set search_path=pg_catalog,pg_temp as $f$ select fmz6e9_private.home() $f$;
create function public.fmz6e9_replay(p_workspace uuid,p_key uuid,p_expected bigint,p_action text,p_payload jsonb)
returns jsonb language sql security invoker set search_path=pg_catalog,pg_temp as $f$
 select fmz6e9_private.replay_request(p_workspace,p_key,p_expected,p_action,p_payload)
$f$;
revoke all on function public.fmz6e9_home(),public.fmz6e9_replay(uuid,uuid,bigint,text,jsonb) from public,anon,authenticated,service_role;
grant execute on function public.fmz6e9_home(),public.fmz6e9_replay(uuid,uuid,bigint,text,jsonb) to authenticated;
commit;
