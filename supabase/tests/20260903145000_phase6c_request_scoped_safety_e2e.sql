begin;

select set_config('phase6c.continue.user1', gen_random_uuid()::text, true);
select set_config('phase6c.continue.user2', gen_random_uuid()::text, true);
select set_config('phase6c.continue.trainer', gen_random_uuid()::text, true);

insert into auth.users(id,aud,role,email,raw_user_meta_data,created_at,updated_at) values
(current_setting('phase6c.continue.user1')::uuid,'authenticated','authenticated','phase6c-continue-a@example.invalid','{"role":"client","name":"6C Continue A"}',now(),now()),
(current_setting('phase6c.continue.user2')::uuid,'authenticated','authenticated','phase6c-continue-b@example.invalid','{"role":"client","name":"6C Continue B"}',now(),now()),
(current_setting('phase6c.continue.trainer')::uuid,'authenticated','authenticated','phase6c-continue-trainer@example.invalid','{"role":"trainer","name":"6C Continue trainer"}',now(),now());

insert into public.profiles(id,role,name,email) values
(current_setting('phase6c.continue.user1')::uuid,'client','6C Continue A','phase6c-continue-a@example.invalid'),
(current_setting('phase6c.continue.user2')::uuid,'client','6C Continue B','phase6c-continue-b@example.invalid');
update public.profiles set role='client' where id in (current_setting('phase6c.continue.user1')::uuid,current_setting('phase6c.continue.user2')::uuid);
-- Trusted fixture setup must not rely on user-metadata trainer provisioning.
insert into public.profiles(id,role,name,email) values(current_setting('phase6c.continue.trainer')::uuid,'trainer','6C Continue trainer','phase6c-continue-trainer@example.invalid');

insert into public.user_onboarding(user_id,age,goal_safety_status) values
(current_setting('phase6c.continue.user1')::uuid,25,'realistic_foundation'),
(current_setting('phase6c.continue.user2')::uuid,26,'realistic_foundation');
insert into public.entitlements(user_id,entitlement_code,status,source,starts_at,ends_at) values
(current_setting('phase6c.continue.user1')::uuid,'ai','active','phase6c_continue_fixture',now()-interval '1 day',now()+interval '1 day'),
(current_setting('phase6c.continue.user2')::uuid,'ai','active','phase6c_continue_fixture',now()-interval '1 day',now()+interval '1 day');
insert into public.ai_member_safety_state(user_id,safety_status,risk_category,blocked_at)
values(current_setting('phase6c.continue.user1')::uuid,'hard_stop','serious_health',now());

select set_config('request.jwt.claim.sub',current_setting('phase6c.continue.user1'),true);
set local role authenticated;
select public.fmz_phase6a_record_consent('ai_processing','granted','phase6a-ai-processing-v1','nl',true,gen_random_uuid());

do $continued_chat$
declare
  v_status jsonb;
  v_risk_thread uuid:=gen_random_uuid();
  v_new_thread uuid:=gen_random_uuid();
  v_after_delete uuid:=gen_random_uuid();
  v_message jsonb;
  v_thread jsonb;
begin
  v_status:=public.fmz_phase6c_get_chat_status();
  if not (v_status->>'chat_write_allowed')::boolean
     or not (v_status->>'communication_allowed')::boolean
     or v_status->>'deny_reason'<>'allowed'
     or v_status->>'safety_status'<>'hard_stop'
     or not (v_status->>'automatic_execution_blocked')::boolean then
    raise exception 'request-scoped communication gate failed';
  end if;

  v_thread:=public.fmz_phase6c_create_thread(v_risk_thread,'nl',gen_random_uuid());
  v_message:=public.fmz_phase6c_submit_message(v_risk_thread,gen_random_uuid(),(v_thread->>'revision')::bigint,'nl','Normale veilige vervolgvraag.');
  if (v_message->>'sequence_number')::bigint<>1 then raise exception 'normal follow-up blocked'; end if;

  v_thread:=public.fmz_phase6c_create_thread(v_new_thread,'nl',gen_random_uuid());
  if (v_thread->>'revision')::bigint<>1 then raise exception 'new conversation after hard stop blocked'; end if;

  perform public.fmz_phase6c_delete_thread(v_risk_thread,(v_message->>'revision')::bigint,gen_random_uuid());
  v_thread:=public.fmz_phase6c_create_thread(v_after_delete,'nl',gen_random_uuid());
  if (v_thread->>'revision')::bigint<>1 then raise exception 'new conversation after delete blocked'; end if;

  v_status:=public.fmz_phase6c_get_chat_status();
  if v_status->>'safety_status'<>'hard_stop' or not (v_status->>'chat_write_allowed')::boolean then
    raise exception 'safety metadata was lost';
  end if;
end $continued_chat$;
reset role;

select set_config('request.jwt.claim.sub',current_setting('phase6c.continue.user2'),true);
set local role authenticated;
select public.fmz_phase6a_record_consent('ai_processing','granted','phase6a-ai-processing-v1','nl',true,gen_random_uuid());
do $member_isolation$
declare v_status jsonb;
begin
  v_status:=public.fmz_phase6c_get_chat_status();
  if not (v_status->>'chat_write_allowed')::boolean or v_status->>'safety_status'<>'clear' then
    raise exception 'member safety isolation failed';
  end if;
end $member_isolation$;
reset role;

select set_config('request.jwt.claim.sub',current_setting('phase6c.continue.user1'),true);
set local role authenticated;
select public.fmz_phase6a_record_consent('ai_processing','withdrawn','phase6a-ai-processing-v1','nl',true,gen_random_uuid());
do $consent_block$
declare v_status jsonb;
begin
  v_status:=public.fmz_phase6c_get_chat_status();
  if (v_status->>'chat_write_allowed')::boolean or v_status->>'deny_reason'<>'ai_consent_required' then
    raise exception 'consent withdrawal no longer blocks processing';
  end if;
end $consent_block$;
reset role;

update public.entitlements set status='inactive'
where user_id=current_setting('phase6c.continue.user2')::uuid and entitlement_code='ai';
select set_config('request.jwt.claim.sub',current_setting('phase6c.continue.user2'),true);
set local role authenticated;
do $entitlement_block$
declare v_status jsonb;
begin
  v_status:=public.fmz_phase6c_get_chat_status();
  if (v_status->>'chat_write_allowed')::boolean or v_status->>'deny_reason'<>'ai_entitlement_required' then
    raise exception 'entitlement loss no longer blocks processing';
  end if;
end $entitlement_block$;
reset role;

select set_config('request.jwt.claim.sub',current_setting('phase6c.continue.trainer'),true);
set local role authenticated;
do $trainer_isolation$
begin
  begin perform public.fmz_phase6c_get_chat_status(); raise exception 'trainer chat access'; exception when insufficient_privilege then null; end;
  begin execute 'select content_text from public.ai_messages'; raise exception 'trainer message access'; exception when insufficient_privilege then null; end;
  begin execute 'select safety_status from public.ai_member_safety_state'; raise exception 'trainer safety access'; exception when insufficient_privilege then null; end;
end $trainer_isolation$;
reset role;

rollback;

select jsonb_build_object(
  'overall_pass',
    not exists(select 1 from auth.users where email like 'phase6c-continue-%@example.invalid')
    and not exists(select 1 from public.profiles where email like 'phase6c-continue-%@example.invalid'),
  'fixtures_remaining',
    (select count(*) from auth.users where email like 'phase6c-continue-%@example.invalid')
) as phase6c_request_scoped_safety_result;
