-- Package 6D-0: staging legacy identity boundary, no existing member data rewrite.
begin;

create schema if not exists legacy_auth_private;
revoke all on schema legacy_auth_private from public, anon, authenticated;
create table legacy_auth_private.client_invitations (
  id uuid primary key default gen_random_uuid(),
  token_hash text not null unique check (token_hash ~ '^[0-9a-f]{64}$'),
  trainer_id uuid not null references public.profiles(id),
  client_id text not null check (length(client_id) between 1 and 160),
  target_email text not null check (target_email = lower(btrim(target_email))),
  created_at timestamptz not null default clock_timestamp(),
  expires_at timestamptz not null,
  accepted_at timestamptz,
  accepted_by uuid references auth.users(id),
  revoked_at timestamptz,
  check (expires_at > created_at and expires_at <= created_at + interval '24 hours'),
  check ((accepted_at is null) = (accepted_by is null))
);
alter table legacy_auth_private.client_invitations enable row level security;
revoke all on table legacy_auth_private.client_invitations from public, anon, authenticated, service_role;
create index client_invitations_target_idx on legacy_auth_private.client_invitations(target_email);
create index client_invitations_trainer_slot_idx on legacy_auth_private.client_invitations(trainer_id,client_id);
create index client_invitations_accepted_by_idx on legacy_auth_private.client_invitations(accepted_by);
-- Existing valid links stay byte-identical; duplicates fail migration rather than being repaired.
create unique index profiles_unique_trainer_client_slot on public.profiles(trainer_id,client_id)
where trainer_id is not null and client_id is not null;

create or replace function public.fmz_bootstrap_trainer_profile(
 p_user_id uuid, p_email text default null, p_name text default null
) returns public.profiles language plpgsql security definer
set search_path = pg_catalog, pg_temp as $fn$
declare v_uid uuid := auth.uid(); v_email text; v_profile public.profiles;
begin
 if v_uid is null or p_user_id is distinct from v_uid then
   raise exception using errcode='42501', message='profile_owner_required';
 end if;
 select lower(btrim(email)) into v_email from auth.users where id=v_uid;
 if not found then raise exception using errcode='42501', message='profile_owner_required'; end if;
 -- Compatibility signature only: no requested role/email/ID becomes authority.
 insert into public.profiles(id,role,name,email)
 values(v_uid,'client',coalesce(nullif(btrim(p_name),''),'Gebruiker'),coalesce(v_email,''))
 on conflict(id) do nothing;
 select * into v_profile from public.profiles where id=v_uid;
 if v_profile.role='trainer' then
   insert into public.coach_workspaces(trainer_id,state) values(v_uid,'{}') on conflict(trainer_id) do nothing;
 end if;
 return v_profile;
end $fn$;

create or replace function public.fmz_handle_new_auth_user()
returns trigger language plpgsql security definer set search_path = pg_catalog, pg_temp as $fn$
begin
 -- Signup metadata is presentation-only; Phase 1 creates a client account after authentication.
 return new;
end $fn$;

create or replace function public.accept_client_invite(display_name text default null)
returns public.profiles language plpgsql security definer set search_path = pg_catalog, pg_temp as $fn$
declare v_profile public.profiles;
begin
 if auth.uid() is null then raise exception using errcode='42501', message='authentication_required'; end if;
 select * into v_profile from public.profiles where id=auth.uid();
 if not found or v_profile.role<>'client' or v_profile.trainer_id is null or v_profile.client_id is null then
  raise exception using errcode='42501', message='verified_invitation_required';
 end if;
 -- Old route can read an already established own link, never create/repair one from metadata.
 return v_profile;
end $fn$;

create or replace function public.fmz_phase6d0_issue_client_invite(p_client_id text)
returns jsonb language plpgsql security definer set search_path = pg_catalog, pg_temp as $fn$
declare v_uid uuid:=auth.uid(); v_client jsonb; v_email text; v_token text; v_now timestamptz:=clock_timestamp(); v_id uuid; v_other public.profiles;
begin
 if v_uid is null or not exists(select 1 from public.profiles where id=v_uid and role='trainer') then
  raise exception using errcode='42501', message='trainer_required';
 end if;
 select c into v_client from public.coach_workspaces w cross join lateral jsonb_array_elements(w.state->'clients') c
 where w.trainer_id=v_uid and c->>'id'=p_client_id;
 if v_client is null or (select count(*) from public.coach_workspaces w cross join lateral jsonb_array_elements(w.state->'clients') c
 where w.trainer_id=v_uid and c->>'id'=p_client_id)<>1 then
  raise exception using errcode='42501', message='owned_client_slot_required';
 end if;
 v_email:=lower(btrim(v_client->>'email'));
 if v_email is null or position('@' in v_email)<2 then raise exception using errcode='22023', message='invite_email_invalid'; end if;
 -- All issue/accept/revoke routes use email -> slot -> invitation/profile lock order.
 perform pg_advisory_xact_lock(hashtextextended('fmz6d0:invite-email:'||v_email,0));
 perform pg_advisory_xact_lock(hashtextextended('fmz6d0:invite-slot:'||v_uid::text||':'||p_client_id,0));
 select p.* into v_other from auth.users u join public.profiles p on p.id=u.id where lower(btrim(u.email))=v_email;
 if found and (v_other.role<>'client' or (v_other.trainer_id is not null and
   (v_other.trainer_id is distinct from v_uid or v_other.client_id is distinct from p_client_id))) then
  raise exception using errcode='42501', message='existing_link_conflict';
 end if;
 if exists(select 1 from public.profiles where trainer_id=v_uid and client_id=p_client_id and id is distinct from v_other.id) then
  raise exception using errcode='42501', message='client_slot_conflict';
 end if;
 if exists(select 1 from legacy_auth_private.client_invitations where target_email=v_email and accepted_at is null
 and revoked_at is null and expires_at>v_now and (trainer_id<>v_uid or client_id<>p_client_id)) then
  raise exception using errcode='42501', message='pending_link_conflict';
 end if;
 update legacy_auth_private.client_invitations set revoked_at=v_now where target_email=v_email
 and accepted_at is null and revoked_at is null;
 v_token:=replace(gen_random_uuid()::text,'-','')||replace(gen_random_uuid()::text,'-','');
 insert into legacy_auth_private.client_invitations(token_hash,trainer_id,client_id,target_email,created_at,expires_at)
 values(encode(sha256(convert_to(v_token,'UTF8')),'hex'),v_uid,p_client_id,v_email,v_now,v_now+interval '24 hours')
 returning id into v_id;
 return jsonb_build_object('invitation_id',v_id,'token',v_token,'email',v_email,
 'name',coalesce(v_client->>'name','Client'),'expires_at',v_now+interval '24 hours');
end $fn$;

create or replace function public.fmz_phase6d0_accept_client_invite(p_token text)
returns public.profiles language plpgsql security definer set search_path = pg_catalog, pg_temp as $fn$
declare v_uid uuid:=auth.uid(); v_email text; v_inv legacy_auth_private.client_invitations; v_profile public.profiles; v_slot_count integer;
begin
 if v_uid is null then raise exception using errcode='42501', message='authentication_required'; end if;
 if p_token is null or p_token !~ '^[0-9a-f]{64}$' then raise exception using errcode='42501', message='invitation_invalid'; end if;
 select lower(btrim(email)) into v_email from auth.users where id=v_uid and email_confirmed_at is not null;
 if not found then raise exception using errcode='42501', message='verified_email_required'; end if;
 select * into v_inv from legacy_auth_private.client_invitations where token_hash=encode(sha256(convert_to(p_token,'UTF8')),'hex');
 if not found or v_inv.target_email is distinct from v_email then raise exception using errcode='42501', message='invitation_invalid'; end if;
 perform pg_advisory_xact_lock(hashtextextended('fmz6d0:invite-email:'||v_email,0));
 perform pg_advisory_xact_lock(hashtextextended('fmz6d0:invite-slot:'||v_inv.trainer_id::text||':'||v_inv.client_id,0));
 select * into v_inv from legacy_auth_private.client_invitations where id=v_inv.id for update;
 if v_inv.accepted_at is not null or v_inv.revoked_at is not null or v_inv.expires_at<=clock_timestamp() then
  raise exception using errcode='42501', message='invitation_used_expired_or_revoked';
 end if;
 if not exists(select 1 from public.profiles where id=v_inv.trainer_id and role='trainer') then
  raise exception using errcode='42501', message='trainer_required';
 end if;
 insert into public.profiles(id,role,name,email) values(v_uid,'client','Client',v_email) on conflict(id) do nothing;
 select * into v_profile from public.profiles where id=v_uid for update;
 -- Profile -> workspace matches the own-workspace save lock order.
 -- Verify the slot still exists and still names this email at the moment of acceptance.
 perform 1 from public.coach_workspaces where trainer_id=v_inv.trainer_id for share;
 select count(*) into v_slot_count from public.coach_workspaces w cross join lateral jsonb_array_elements(w.state->'clients') c
 where w.trainer_id=v_inv.trainer_id and c->>'id'=v_inv.client_id and lower(btrim(c->>'email'))=v_email;
 if v_slot_count<>1 then raise exception using errcode='42501', message='invitation_slot_changed'; end if;
 if v_profile.role<>'client' or (v_profile.trainer_id is not null and
  (v_profile.trainer_id is distinct from v_inv.trainer_id or v_profile.client_id is distinct from v_inv.client_id)) then
  raise exception using errcode='42501', message='existing_link_conflict';
 end if;
 if exists(select 1 from public.profiles where trainer_id=v_inv.trainer_id and client_id=v_inv.client_id and id<>v_uid) then
  raise exception using errcode='42501', message='client_slot_conflict';
 end if;
 update public.profiles set trainer_id=v_inv.trainer_id,client_id=v_inv.client_id where id=v_uid returning * into v_profile;
 update legacy_auth_private.client_invitations set accepted_at=clock_timestamp(),accepted_by=v_uid where id=v_inv.id;
 return v_profile;
end $fn$;

create or replace function public.fmz_phase6d0_revoke_client_invite(p_invitation_id uuid)
returns void language plpgsql security definer set search_path = pg_catalog, pg_temp as $fn$
declare v_inv legacy_auth_private.client_invitations;
begin
 select * into v_inv from legacy_auth_private.client_invitations where id=p_invitation_id and trainer_id=auth.uid();
 if auth.uid() is null or not found or not exists(select 1 from public.profiles where id=auth.uid() and role='trainer') then
  raise exception using errcode='42501', message='owned_invitation_required';
 end if;
 perform pg_advisory_xact_lock(hashtextextended('fmz6d0:invite-email:'||v_inv.target_email,0));
 perform pg_advisory_xact_lock(hashtextextended('fmz6d0:invite-slot:'||v_inv.trainer_id::text||':'||v_inv.client_id,0));
 update legacy_auth_private.client_invitations set revoked_at=coalesce(revoked_at,clock_timestamp())
 where id=p_invitation_id and accepted_at is null;
end $fn$;

create or replace function public.fmz_phase6d0_read_own_workspace()
returns jsonb language plpgsql stable security definer set search_path = pg_catalog, pg_temp as $fn$
declare v_profile public.profiles; v_client jsonb; v_library jsonb;
begin
 select * into v_profile from public.profiles where id=auth.uid() and role='client';
 if not found or v_profile.trainer_id is null or v_profile.client_id is null then
  raise exception using errcode='42501', message='own_client_link_required';
 end if;
 select c into v_client from public.coach_workspaces w cross join lateral jsonb_array_elements(w.state->'clients') c
 where w.trainer_id=v_profile.trainer_id and c->>'id'=v_profile.client_id;
 if v_client is null or (select count(*) from public.coach_workspaces w cross join lateral jsonb_array_elements(w.state->'clients') c
 where w.trainer_id=v_profile.trainer_id and c->>'id'=v_profile.client_id)<>1 then
  raise exception using errcode='42501', message='own_client_slot_required';
 end if;
 -- Shared legacy exercise names/media only; never trainer finance, account or other clients.
 select coalesce(jsonb_agg(jsonb_build_object('id',e->'id','name',e->'name','image',e->'image','muscle',e->'muscle','equipment',e->'equipment')),'[]')
 into v_library from public.coach_workspaces w cross join lateral jsonb_array_elements(coalesce(w.state->'exerciseLibrary','[]')) e
 where w.trainer_id=v_profile.trainer_id;
 v_client:=v_client-'password';
 return jsonb_build_object('state',jsonb_build_object('clients',jsonb_build_array(v_client),'exerciseLibrary',v_library,'trainerAccount',null),
 'revision',encode(sha256(convert_to(v_client::text,'UTF8')),'hex'));
end $fn$;

create or replace function public.fmz_phase6d0_save_own_workspace(p_client jsonb,p_expected_revision text)
returns jsonb language plpgsql security definer set search_path = pg_catalog, pg_temp as $fn$
declare v_profile public.profiles; v_state jsonb; v_client jsonb; v_index integer; v_revision text; v_next jsonb;
begin
 select * into v_profile from public.profiles where id=auth.uid() and role='client' for share;
 if not found or v_profile.trainer_id is null or v_profile.client_id is null then
  raise exception using errcode='42501', message='own_client_link_required';
 end if;
 if jsonb_typeof(p_client) is distinct from 'object' or octet_length(p_client::text)>2097152
 or p_client->>'id' is distinct from v_profile.client_id then
  raise exception using errcode='42501', message='own_client_payload_required';
 end if;
 select state into v_state from public.coach_workspaces where trainer_id=v_profile.trainer_id for update;
 if (select count(*) from jsonb_array_elements(v_state->'clients') c where c->>'id'=v_profile.client_id)<>1 then
  raise exception using errcode='42501', message='own_client_slot_required';
 end if;
 select c,(ord-1)::integer into v_client,v_index from jsonb_array_elements(v_state->'clients') with ordinality as entries(c,ord)
 where c->>'id'=v_profile.client_id;
 v_revision:=encode(sha256(convert_to((v_client-'password')::text,'UTF8')),'hex');
 -- Preserve server identity and any legacy password bytes, without returning them to a client.
 v_next:=(p_client-'password')||jsonb_build_object('id',v_client->'id','email',v_client->'email');
 if v_client ? 'password' then v_next:=v_next||jsonb_build_object('password',v_client->'password'); end if;
 if (v_next-'password')=(v_client-'password') then return jsonb_build_object('revision',v_revision,'replay',true); end if;
 if p_expected_revision is distinct from v_revision then raise exception using errcode='40001', message='workspace_conflict_reload_required'; end if;
 update public.coach_workspaces set state=jsonb_set(v_state,array['clients',v_index::text],v_next),updated_at=clock_timestamp()
 where trainer_id=v_profile.trainer_id;
 return jsonb_build_object('revision',encode(sha256(convert_to((v_next-'password')::text,'UTF8')),'hex'),'replay',false);
end $fn$;

-- No browser INSERT or role/link/email UPDATE, and no TRUNCATE (RLS cannot protect TRUNCATE).
revoke all on public.profiles from public, anon, authenticated;
grant select on public.profiles to authenticated;
grant update(name) on public.profiles to authenticated;
drop policy if exists "profiles insert own trainer" on public.profiles;
alter policy "profiles select own or linked" on public.profiles to authenticated;
alter policy "profiles update own" on public.profiles to authenticated;
revoke all on public.coach_workspaces from public, anon, authenticated;
grant select,insert,update on public.coach_workspaces to authenticated;
drop policy if exists "workspace read trainer or linked client" on public.coach_workspaces;
drop policy if exists "workspace update trainer or linked client" on public.coach_workspaces;
alter policy "workspace insert trainer" on public.coach_workspaces to authenticated;
create policy "workspace read own trainer" on public.coach_workspaces for select to authenticated
 using (trainer_id=(select auth.uid()) and public.fmz_is_trainer());
create policy "workspace update own trainer" on public.coach_workspaces for update to authenticated
 using (trainer_id=(select auth.uid()) and public.fmz_is_trainer())
 with check (trainer_id=(select auth.uid()) and public.fmz_is_trainer());

alter function public.fmz_current_profile_role() set search_path = pg_catalog, pg_temp;
alter function public.fmz_current_profile_trainer_id() set search_path = pg_catalog, pg_temp;
alter function public.fmz_is_trainer() set search_path = pg_catalog, pg_temp;
alter function public.fmz_can_select_profile(uuid,text,uuid) set search_path = pg_catalog, pg_temp;
alter function public.fmz_can_access_workspace(uuid) set search_path = pg_catalog, pg_temp;

revoke all on function public.fmz_bootstrap_trainer_profile(uuid,text,text),
 public.accept_client_invite(text),public.fmz_handle_new_auth_user(),
 public.fmz_current_profile_role(),public.fmz_current_profile_trainer_id(),public.fmz_is_trainer(),
 public.fmz_can_select_profile(uuid,text,uuid),public.fmz_can_access_workspace(uuid),
 public.fmz_phase6d0_issue_client_invite(text),public.fmz_phase6d0_accept_client_invite(text),
 public.fmz_phase6d0_revoke_client_invite(uuid),public.fmz_phase6d0_read_own_workspace(),
 public.fmz_phase6d0_save_own_workspace(jsonb,text) from public,anon,authenticated;
grant execute on function public.fmz_bootstrap_trainer_profile(uuid,text,text), public.accept_client_invite(text),
 public.fmz_current_profile_role(),public.fmz_current_profile_trainer_id(),public.fmz_is_trainer(),
 public.fmz_can_select_profile(uuid,text,uuid),public.fmz_can_access_workspace(uuid),
 public.fmz_phase6d0_issue_client_invite(text),public.fmz_phase6d0_accept_client_invite(text),
 public.fmz_phase6d0_revoke_client_invite(uuid),public.fmz_phase6d0_read_own_workspace(),
 public.fmz_phase6d0_save_own_workspace(jsonb,text) to authenticated;
commit;
