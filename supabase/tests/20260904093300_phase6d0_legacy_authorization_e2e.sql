-- Synthetic fixtures only. Always run the entire file; no external calls.
begin;
create temporary table gate_checks(name text primary key, pass boolean not null);
grant select,insert on gate_checks to authenticated,anon;
create function pg_temp.assert_gate(p_ok boolean,p_name text) returns void language plpgsql as $$
begin
 if not coalesce(p_ok,false) then raise exception '6D0 assertion failed: %',p_name; end if;
 insert into gate_checks values(p_name,true);
end $$;
create function pg_temp.denied(p_sql text,p_name text) returns void language plpgsql as $$
begin
 begin
  execute p_sql;
 exception when insufficient_privilege or serialization_failure or unique_violation then
  perform pg_temp.assert_gate(true,p_name); return;
 end;
 raise exception '6D0 expected denial: %',p_name;
end $$;
select set_config('gate.member',gen_random_uuid()::text,true);
select set_config('gate.other',gen_random_uuid()::text,true);
select set_config('gate.trainer',gen_random_uuid()::text,true);
select set_config('gate.trainer2',gen_random_uuid()::text,true);
insert into auth.users(id,aud,role,email,email_confirmed_at,raw_user_meta_data,created_at,updated_at) values
(current_setting('gate.member')::uuid,'authenticated','authenticated','6d0-member@example.invalid',now(),'{"role":"trainer","trainer_id":"00000000-0000-0000-0000-000000000001","client_id":"fake"}',now(),now()),
(current_setting('gate.other')::uuid,'authenticated','authenticated','6d0-other@example.invalid',now(),'{"role":"trainer"}',now(),now()),
(current_setting('gate.trainer')::uuid,'authenticated','authenticated','6d0-trainer@example.invalid',now(),'{"role":"trainer"}',now(),now()),
(current_setting('gate.trainer2')::uuid,'authenticated','authenticated','6d0-trainer2@example.invalid',now(),'{}',now(),now());
select pg_temp.assert_gate(not exists(select 1 from public.profiles where id in
(current_setting('gate.member')::uuid,current_setting('gate.other')::uuid,current_setting('gate.trainer')::uuid)),'signup_metadata_cannot_provision_trainer');
insert into public.profiles(id,role,name,email) values
(current_setting('gate.trainer')::uuid,'trainer','Synthetic trainer','6d0-trainer@example.invalid'),
(current_setting('gate.trainer2')::uuid,'trainer','Synthetic trainer2','6d0-trainer2@example.invalid');
insert into public.coach_workspaces(trainer_id,state) values
(current_setting('gate.trainer')::uuid,'{"trainerAccount":{"secret":"private"},"trainerFinance":{"invoices":["private"]},"clients":[{"id":"slot-a","email":"6d0-member@example.invalid","name":"A","water":1,"password":"legacy-never-return"},{"id":"slot-b","email":"6d0-other@example.invalid","name":"B","water":2}]}'),
(current_setting('gate.trainer2')::uuid,'{"clients":[{"id":"slot-c","email":"6d0-member@example.invalid","name":"A"}]}');

select set_config('request.jwt.claim.sub','',true);
set local role anon;
select pg_temp.denied('select public.fmz_bootstrap_trainer_profile(gen_random_uuid())','anon_bootstrap_denied');
select pg_temp.denied('select public.accept_client_invite()','anon_invite_denied');
select pg_temp.denied('select * from public.profiles','anon_profiles_denied');
select pg_temp.denied('select * from public.coach_workspaces','anon_workspace_denied');
select pg_temp.denied('select public.fmz_phase6d0_issue_client_invite(''slot-a'')','anon_issue_denied');
reset role;
select set_config('request.jwt.claim.sub',current_setting('gate.member'),true);
select set_config('request.jwt.claims',jsonb_build_object('sub',current_setting('gate.member'),'role','authenticated','user_metadata',
jsonb_build_object('role','trainer','trainer_id',current_setting('gate.trainer'),'client_id','slot-a'))::text,true);
set local role authenticated;
select pg_temp.assert_gate((public.fmz_bootstrap_trainer_profile(auth.uid(),'spoof@example.invalid','Synthetic')).role='client','self_bootstrap_always_client');
select pg_temp.assert_gate((public.fmz_bootstrap_trainer_profile(auth.uid())).id=auth.uid(),'self_bootstrap_idempotent');
select pg_temp.denied('select public.fmz_bootstrap_trainer_profile('''||current_setting('gate.other')||'''::uuid)','cross_user_bootstrap_denied');
select pg_temp.denied('update public.profiles set role=''trainer'' where id=auth.uid()','direct_role_escalation_denied');
select pg_temp.denied('update public.profiles set trainer_id='''||current_setting('gate.trainer')||'''::uuid where id=auth.uid()','direct_self_link_denied');
select pg_temp.denied('update public.profiles set email=''spoof@example.invalid'' where id=auth.uid()','direct_email_spoof_denied');
select pg_temp.denied('insert into public.profiles(id,role) values(gen_random_uuid(),''trainer'')','direct_profile_insert_denied');
select pg_temp.denied('truncate public.profiles','profile_truncate_denied');
select pg_temp.denied('truncate public.coach_workspaces','workspace_truncate_denied');
select pg_temp.denied('select public.accept_client_invite()','metadata_link_denied');
select pg_temp.denied('select public.fmz_phase6d0_issue_client_invite(''slot-a'')','member_cannot_issue');
select pg_temp.denied('select * from legacy_auth_private.client_invitations','private_ledger_denied');
update public.profiles set name='Synthetic renamed' where id=auth.uid();
select pg_temp.assert_gate((select name='Synthetic renamed' from public.profiles where id=auth.uid()),'own_display_name_update_preserved');
reset role;
select pg_temp.assert_gate((select email='6d0-member@example.invalid' from public.profiles where id=current_setting('gate.member')::uuid),'authoritative_auth_email');
select set_config('request.jwt.claim.sub',current_setting('gate.trainer'),true);
set local role authenticated;
select pg_temp.assert_gate((public.fmz_bootstrap_trainer_profile(auth.uid())).role='trainer','existing_trainer_preserved');
select pg_temp.denied('select public.fmz_phase6d0_issue_client_invite(''slot-c'')','other_workspace_slot_denied');
select set_config('gate.invite',public.fmz_phase6d0_issue_client_invite('slot-a')::text,true);
reset role;
select pg_temp.assert_gate((select count(*)=1 from legacy_auth_private.client_invitations
where id=(current_setting('gate.invite')::jsonb->>'invitation_id')::uuid and expires_at<=created_at+interval '24 hours'),'invitation_expiry_bounded');
select pg_temp.assert_gate((select token_hash<>(current_setting('gate.invite')::jsonb->>'token') from legacy_auth_private.client_invitations
where id=(current_setting('gate.invite')::jsonb->>'invitation_id')::uuid),'token_only_stored_as_digest');
select set_config('request.jwt.claim.sub',current_setting('gate.other'),true);
set local role authenticated;
select pg_temp.denied(format('select public.fmz_phase6d0_accept_client_invite(%L)',current_setting('gate.invite')::jsonb->>'token'),'other_email_cannot_accept');
reset role;
select set_config('request.jwt.claim.sub',current_setting('gate.member'),true);
set local role authenticated;
select pg_temp.denied('select public.fmz_phase6d0_accept_client_invite(repeat(''0'',64))','modified_token_denied');
select pg_temp.assert_gate((public.fmz_phase6d0_accept_client_invite(current_setting('gate.invite')::jsonb->>'token')).trainer_id=current_setting('gate.trainer')::uuid,'valid_invite_links_exact_member');
select pg_temp.denied(format('select public.fmz_phase6d0_accept_client_invite(%L)',current_setting('gate.invite')::jsonb->>'token'),'replayed_token_denied');
select pg_temp.assert_gate((public.accept_client_invite()).client_id='slot-a','legacy_accept_existing_link_preserved');
select pg_temp.assert_gate((select count(*)=0 from public.coach_workspaces),'member_direct_workspace_read_denied');
select pg_temp.assert_gate((select count(*)=0 from public.profiles where id=current_setting('gate.other')::uuid),'cross_member_profile_read_denied');
select set_config('gate.workspace',public.fmz_phase6d0_read_own_workspace()::text,true);
select pg_temp.assert_gate(jsonb_array_length(current_setting('gate.workspace')::jsonb#>'{state,clients}')=1,'only_one_own_client_returned');
select pg_temp.assert_gate(not ((current_setting('gate.workspace')::jsonb->'state') ? 'trainerFinance') and
not ((current_setting('gate.workspace')::jsonb#>'{state,clients,0}') ? 'password'),'workspace_private_fields_not_returned');
select pg_temp.denied('select public.fmz_phase6d0_save_own_workspace(''{"id":"slot-b"}'',''bad'')','cross_member_workspace_write_denied');
select pg_temp.denied('select public.fmz_phase6d0_save_own_workspace(''{"id":"slot-a","water":9}'',''bad'')','stale_workspace_write_denied');
select set_config('gate.updated',public.fmz_phase6d0_save_own_workspace(
(current_setting('gate.workspace')::jsonb#>'{state,clients,0}')||'{"water":3}',current_setting('gate.workspace')::jsonb->>'revision')::text,true);
select pg_temp.assert_gate((public.fmz_phase6d0_save_own_workspace(
(current_setting('gate.workspace')::jsonb#>'{state,clients,0}')||'{"water":3}',current_setting('gate.workspace')::jsonb->>'revision')->>'replay')::boolean,'workspace_exact_retry_idempotent');
select pg_temp.denied('select public.fmz_phase6d0_save_own_workspace(''{"id":"slot-a","water":9}'','||
quote_literal(current_setting('gate.workspace')::jsonb->>'revision')||')','workspace_changed_retry_denied');
reset role;
select pg_temp.assert_gate((select state#>>'{clients,1,water}'='2' and state#>>'{trainerFinance,invoices,0}'='private'
and state#>>'{clients,0,password}'='legacy-never-return' from public.coach_workspaces where trainer_id=current_setting('gate.trainer')::uuid),'other_member_and_legacy_secrets_unchanged');
select set_config('request.jwt.claim.sub',current_setting('gate.trainer2'),true);
set local role authenticated;
select pg_temp.denied('select public.fmz_phase6d0_issue_client_invite(''slot-c'')','conflicting_trainer_relink_denied');
reset role;
select set_config('request.jwt.claim.sub',current_setting('gate.trainer'),true);
set local role authenticated;
select set_config('gate.expired',public.fmz_phase6d0_issue_client_invite('slot-b')::text,true);
select set_config('gate.superseded',public.fmz_phase6d0_issue_client_invite('slot-b')::text,true);
reset role;
select set_config('request.jwt.claim.sub',current_setting('gate.other'),true);
set local role authenticated;
select pg_temp.denied(format('select public.fmz_phase6d0_accept_client_invite(%L)',current_setting('gate.expired')::jsonb->>'token'),'superseded_invitation_denied');
reset role;
update legacy_auth_private.client_invitations set created_at=now()-interval '2 days',expires_at=now()-interval '1 day'
where id=(current_setting('gate.superseded')::jsonb->>'invitation_id')::uuid;
set local role authenticated;
select pg_temp.denied(format('select public.fmz_phase6d0_accept_client_invite(%L)',current_setting('gate.superseded')::jsonb->>'token'),'expired_invitation_denied');
reset role;
select set_config('request.jwt.claim.sub',current_setting('gate.trainer'),true);
set local role authenticated;
select set_config('gate.revoked',public.fmz_phase6d0_issue_client_invite('slot-b')::text,true);
select public.fmz_phase6d0_revoke_client_invite((current_setting('gate.revoked')::jsonb->>'invitation_id')::uuid);
reset role;
select set_config('request.jwt.claim.sub',current_setting('gate.other'),true);
set local role authenticated;
select pg_temp.denied(format('select public.fmz_phase6d0_accept_client_invite(%L)',current_setting('gate.revoked')::jsonb->>'token'),'revoked_invitation_denied');
reset role;
select set_config('request.jwt.claim.sub',current_setting('gate.trainer'),true);
set local role authenticated;
select set_config('gate.changed',public.fmz_phase6d0_issue_client_invite('slot-b')::text,true);
reset role;
update public.coach_workspaces set state=jsonb_set(state,'{clients,1,email}','"changed@example.invalid"') where trainer_id=current_setting('gate.trainer')::uuid;
select set_config('request.jwt.claim.sub',current_setting('gate.other'),true);
set local role authenticated;
select pg_temp.denied(format('select public.fmz_phase6d0_accept_client_invite(%L)',current_setting('gate.changed')::jsonb->>'token'),'changed_slot_denied');
reset role;
-- Separate AI consent and private chat remain governed by the frozen own-user RPCs.
insert into public.user_onboarding(user_id,age,goal_safety_status) values(current_setting('gate.member')::uuid,25,'realistic_foundation');
insert into public.entitlements(user_id,entitlement_code,status,source,starts_at,ends_at)
values(current_setting('gate.member')::uuid,'ai','active','6d0_fixture',now()-interval '1 day',now()+interval '1 day');
select set_config('request.jwt.claim.sub',current_setting('gate.member'),true);
set local role authenticated;
select pg_temp.assert_gate(not (public.fmz_phase6c_get_chat_status()->>'chat_write_allowed')::boolean,'trainer_link_does_not_grant_ai_consent');
select public.fmz_phase6a_record_consent('ai_processing','granted','phase6a-ai-processing-v1','nl',true,gen_random_uuid());
select set_config('gate.thread',gen_random_uuid()::text,true);
select public.fmz_phase6c_create_thread(current_setting('gate.thread')::uuid,'nl',gen_random_uuid());
select pg_temp.assert_gate((public.fmz_phase6c_get_chat_status()->>'chat_write_allowed')::boolean,'existing_chat_consent_gate_preserved');
reset role;
select set_config('request.jwt.claim.sub',current_setting('gate.trainer'),true);
set local role authenticated;
select pg_temp.denied('select * from public.ai_threads','trainer_cannot_read_private_threads');
select pg_temp.denied('select public.fmz_phase6c_read_thread('||quote_literal(current_setting('gate.thread'))||'::uuid)','trainer_cannot_read_private_chat_rpc');
reset role;
select set_config('request.jwt.claim.sub',current_setting('gate.member'),true);
set local role authenticated;
select public.fmz_phase6a_record_consent('ai_processing','withdrawn','phase6a-ai-processing-v1','nl',true,gen_random_uuid());
select pg_temp.assert_gate(not (public.fmz_phase6c_get_chat_status()->>'chat_write_allowed')::boolean,'withdrawal_still_blocks_processing');
reset role;
select jsonb_build_object('overall_pass',bool_and(pass),'pass_count',count(*),'fail_count',0,'fixture_mode','transaction_rollback') as result from gate_checks;
rollback;
