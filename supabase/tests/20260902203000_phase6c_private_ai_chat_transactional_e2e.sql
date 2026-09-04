begin;

select set_config('phase6c.user1',gen_random_uuid()::text,true);
select set_config('phase6c.user2',gen_random_uuid()::text,true);
select set_config('phase6c.trainer',gen_random_uuid()::text,true);
select set_config('phase6c.thread',gen_random_uuid()::text,true);
select set_config('phase6c.thread.req',gen_random_uuid()::text,true);
select set_config('phase6c.message.req',gen_random_uuid()::text,true);
select set_config('phase6c.attempt',gen_random_uuid()::text,true);

insert into auth.users(id,aud,role,email,raw_user_meta_data,created_at,updated_at) values
(current_setting('phase6c.user1')::uuid,'authenticated','authenticated','phase6c-a@example.invalid','{"role":"client","name":"6C A"}',now(),now()),
(current_setting('phase6c.user2')::uuid,'authenticated','authenticated','phase6c-b@example.invalid','{"role":"client","name":"6C B"}',now(),now()),
(current_setting('phase6c.trainer')::uuid,'authenticated','authenticated','phase6c-trainer@example.invalid','{"role":"trainer","name":"6C trainer"}',now(),now());
insert into public.profiles(id,role,name,email) values
(current_setting('phase6c.user1')::uuid,'client','6C A','phase6c-a@example.invalid'),
(current_setting('phase6c.user2')::uuid,'client','6C B','phase6c-b@example.invalid');
update public.profiles set role='client' where id in (current_setting('phase6c.user1')::uuid,current_setting('phase6c.user2')::uuid);
-- Trusted fixture setup must not rely on user-metadata trainer provisioning.
insert into public.profiles(id,role,name,email) values(current_setting('phase6c.trainer')::uuid,'trainer','6C trainer','phase6c-trainer@example.invalid');
insert into public.user_onboarding(user_id,age,goal_safety_status) values
(current_setting('phase6c.user1')::uuid,25,'realistic_foundation');
insert into public.entitlements(user_id,entitlement_code,status,source,starts_at,ends_at) values
(current_setting('phase6c.user1')::uuid,'ai','active','phase6c_fixture',now()-interval '1 day',now()+interval '1 day'),
(current_setting('phase6c.user2')::uuid,'pro','active','phase6c_fixture',now()-interval '1 day',null);

select set_config('request.jwt.claim.sub',current_setting('phase6c.user1'),true);
set local role authenticated;
do $member$
declare v jsonb;
begin
  v:=public.fmz_phase6c_get_chat_status();
  if v->>'deny_reason'<>'ai_consent_required' then raise exception 'consent gate failed'; end if;
  perform public.fmz_phase6a_record_consent('ai_processing','granted','phase6a-ai-processing-v1','nl',true,gen_random_uuid());
  v:=public.fmz_phase6c_get_chat_status();
  if not (v->>'chat_write_allowed')::boolean or (v->>'external_ai_enabled')::boolean then raise exception 'chat gate failed'; end if;
  v:=public.fmz_phase6c_create_thread(current_setting('phase6c.thread')::uuid,'nl',current_setting('phase6c.thread.req')::uuid);
  if (v->>'revision')::bigint<>1 then raise exception 'thread revision failed'; end if;
  v:=public.fmz_phase6c_submit_message(current_setting('phase6c.thread')::uuid,current_setting('phase6c.message.req')::uuid,1,'nl','Synthetic private message.');
  if (v->>'sequence_number')::bigint<>1 or (v->>'revision')::bigint<>2 then raise exception 'message sequencing failed'; end if;
  v:=public.fmz_phase6c_submit_message(current_setting('phase6c.thread')::uuid,current_setting('phase6c.message.req')::uuid,1,'nl','Synthetic private message.');
  if not (v->>'replay')::boolean then raise exception 'message replay failed'; end if;
  begin
    perform public.fmz_phase6c_submit_message(current_setting('phase6c.thread')::uuid,current_setting('phase6c.message.req')::uuid,2,'nl','Changed content.');
    raise exception 'changed replay accepted';
  exception when unique_violation then null; end;
  begin
    update public.ai_messages set content_text='Changed' where request_id=current_setting('phase6c.message.req')::uuid;
    raise exception 'direct message update allowed';
  exception when insufficient_privilege then null; end;
end $member$;
reset role;

do $service$
declare v jsonb; v_run uuid; v_output jsonb;
begin
  v:=public.fmz_phase6c_service_begin_mock_run(current_setting('phase6c.user1')::uuid,(select id from public.ai_messages where request_id=current_setting('phase6c.message.req')::uuid),current_setting('phase6c.attempt')::uuid,repeat('a',64));
  v_run:=(v->>'run_id')::uuid;
  v_output:='{"schema_version":"phase6a.response.v1","feature_code":"private_chat","summary":"Deterministic mock reply.","observations":[],"uncertainties":[],"recommendations":["fixture"],"actions":[],"safety":{"status":"clear","category":"none","message_key":"safety.clear","automatic_execution_blocked":false}}';
  perform public.fmz_phase6a_service_complete_run(v_run,v_output,0,0,0);
  v:=public.fmz_phase6c_service_begin_mock_run(current_setting('phase6c.user1')::uuid,(select id from public.ai_messages where request_id=current_setting('phase6c.message.req')::uuid),current_setting('phase6c.attempt')::uuid,repeat('a',64));
  if not (v->>'replay')::boolean or v->>'status'<>'completed' then raise exception 'run replay failed'; end if;
  if (select count(*) from public.ai_messages where thread_id=current_setting('phase6c.thread')::uuid)<>2 then raise exception 'assistant duplicate or missing'; end if;
end $service$;

select set_config('request.jwt.claim.sub',current_setting('phase6c.user1'),true);
set local role authenticated;
do $history_export_delete$
declare v jsonb; v_rev bigint;
begin
  v:=public.fmz_phase6c_read_thread(current_setting('phase6c.thread')::uuid,50,null);
  if jsonb_array_length(v->'messages')<>2 or v#>>'{messages,0,content_text}' is null then raise exception 'history failed'; end if;
  v_rev:=(v#>>'{thread,revision}')::bigint;
  v:=public.fmz_phase6c_export_chat(gen_random_uuid());
  if v->>'schema_version'<>'phase6c.chat-export.v1' or jsonb_array_length(v->'conversations')<>1 then raise exception 'export failed'; end if;
  v:=public.fmz_phase6c_delete_thread(current_setting('phase6c.thread')::uuid,v_rev,gen_random_uuid());
  if not (v->>'deleted')::boolean then raise exception 'delete failed'; end if;
end $history_export_delete$;
reset role;
do $delete_proof$
begin
  if exists(select 1 from public.ai_messages where thread_id=current_setting('phase6c.thread')::uuid and (content_text is not null or structured_output is not null or status<>'deleted')) then raise exception 'raw content remained'; end if;
end $delete_proof$;

select set_config('request.jwt.claim.sub',current_setting('phase6c.user2'),true);
set local role authenticated;
do $deny_matrix$
declare v jsonb;
begin
  perform public.fmz_phase6a_record_consent('ai_processing','granted','phase6a-ai-processing-v1','nl',true,gen_random_uuid());
  v:=public.fmz_phase6c_get_chat_status();
  if v->>'deny_reason'<>'ai_entitlement_required' then raise exception 'Free Pro deny failed'; end if;
end $deny_matrix$;
reset role;

insert into public.entitlements(user_id,entitlement_code,status,source,starts_at,ends_at)
values(current_setting('phase6c.user2')::uuid,'ai','active','phase6c_age_fixture',now()-interval '1 day',now()+interval '1 day');
select set_config('request.jwt.claim.sub',current_setting('phase6c.user2'),true);
set local role authenticated;
do $age_gate$
declare v jsonb;
begin
  v:=public.fmz_phase6c_get_chat_status();
  if v->>'deny_reason'<>'ai_age_required' then raise exception 'age gate failed'; end if;
end $age_gate$;
reset role;

select set_config('request.jwt.claim.sub',current_setting('phase6c.trainer'),true);
set local role authenticated;
do $trainer$
begin
  begin perform public.fmz_phase6c_get_chat_status(); raise exception 'trainer chat access'; exception when insufficient_privilege then null; end;
  begin execute 'select content_text from public.ai_messages'; raise exception 'trainer table access'; exception when insufficient_privilege then null; end;
end $trainer$;
reset role;

do $retention$
declare v_user uuid:=current_setting('phase6c.user1')::uuid; v_thread uuid:=gen_random_uuid(); v_started timestamptz:=now()-interval '91 days';
begin
  insert into public.ai_threads(id,user_id,feature_code,locale,retention_state,retention_started_at,retention_due_at)
  values(v_thread,v_user,'private_chat','nl','grace',v_started,v_started+interval '90 days');
  insert into public.ai_messages(id,user_id,thread_id,message_role,feature_code,content_text,status,request_id)
  values(gen_random_uuid(),v_user,v_thread,'user','private_chat','Retention fixture','active',gen_random_uuid());
  perform ai_private.phase6c_apply_retention(v_user,now());
  if exists(select 1 from public.ai_messages where thread_id=v_thread and content_text is not null) or not exists(select 1 from public.ai_threads where id=v_thread and retention_state='deleted') then raise exception 'retention scrub failed'; end if;
end $retention$;

rollback;

select jsonb_build_object(
  'overall_pass',
    not exists(select 1 from auth.users where email like 'phase6c-%@example.invalid')
    and not exists(select 1 from public.profiles where email like 'phase6c-%@example.invalid'),
  'fixtures_remaining',
    (select count(*) from auth.users where email like 'phase6c-%@example.invalid')
) as phase6c_transactional_result;
