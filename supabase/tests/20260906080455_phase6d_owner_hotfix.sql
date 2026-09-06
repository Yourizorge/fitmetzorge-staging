-- All fixtures and mutations are enclosed in one rollback-only transaction.
begin;
create temporary table hotfix_checks(name text primary key,pass boolean not null);
create function pg_temp.check_hotfix(p_name text,p_pass boolean)
returns void language plpgsql as $$
begin
 if p_pass is distinct from true then raise exception 'HOTFIX CHECK FAILED: %',p_name; end if;
 insert into hotfix_checks values(p_name,true);
end;
$$;
create temporary table hotfix_ids(key text primary key,id uuid not null default gen_random_uuid());
insert into hotfix_ids(key) values('member'),('other'),('trainer'),('workout'),('recovery_request');
insert into auth.users(id,aud,role,email,created_at,updated_at)
 select id,'authenticated','authenticated','phase6d-owner-'||key||'@example.invalid',now(),now()
 from hotfix_ids where key in ('member','other','trainer');
insert into public.profiles(id,role,name,email)
 select id,case when key='trainer' then 'trainer' else 'client' end,'Owner hotfix fixture '||key,'phase6d-owner-'||key||'@example.invalid'
 from hotfix_ids where key in ('member','other','trainer');
insert into public.user_onboarding(user_id,age,completed_at) select id,34,now() from hotfix_ids where key in ('member','other');
insert into public.entitlements(user_id,entitlement_code,status,source,starts_at,ends_at)
 select id,'ai','active','owner_hotfix_fixture',now()-interval '1 day',now()+interval '29 days' from hotfix_ids where key in ('member','other');
select set_config('request.jwt.claim.sub',(select id::text from hotfix_ids where key='member'),true);

do $test$
declare
 v_user uuid:=(select id from hotfix_ids where key='member');
 v_other uuid:=(select id from hotfix_ids where key='other');
 v_trainer uuid:=(select id from hotfix_ids where key='trainer');
 v_settings jsonb;
 v_status jsonb;
 v_recovery jsonb;
 v_before jsonb;
 v_weekly jsonb;
 v_daily jsonb;
 v_post jsonb;
 v_chat uuid:=gen_random_uuid();
 v_revision bigint;
 v_event_count bigint;
 v_result uuid;
 v_req uuid:=gen_random_uuid();
 v_failure boolean;
 v_pref_req uuid:=gen_random_uuid();
begin
 perform pg_temp.check_hotfix('settings initial own name',(public.fmz_phase6d_get_member_settings()->'profile'->>'name')='Owner hotfix fixture member');
 v_settings:=public.fmz_phase6d_update_member_settings('{"language":"en","date_format":"iso","hour_cycle":"12","avatar_side":"left","avatar_y":0.31,"avatar_visible":false,"name":"Updated fixture"}',0);
 perform pg_temp.check_hotfix('language saved to own authoritative settings',v_settings->>'language'='en' and exists(select 1 from public.user_settings where user_id=v_user and language='en'));
 perform pg_temp.check_hotfix('display and avatar preferences persistent',v_settings->'display'->>'hour_cycle'='12' and v_settings->'avatar'->>'side'='left' and not (v_settings->'avatar'->>'visible')::boolean);
 perform pg_temp.check_hotfix('name own RPC',(select name from public.profiles where id=v_user)='Updated fixture');
 perform pg_temp.check_hotfix('other member untouched',not exists(select 1 from public.user_settings where user_id=v_other));
 v_failure:=false;
 begin perform public.fmz_phase6d_update_member_settings(jsonb_build_object('user_id',v_other),1); exception when invalid_parameter_value then v_failure:=true; end;
 perform pg_temp.check_hotfix('supplied user ID rejected',v_failure);
 v_failure:=false;
 begin perform public.fmz_phase6d_update_member_settings('{"language":"de"}',0); exception when serialization_failure then v_failure:=true; end;
 perform pg_temp.check_hotfix('stale settings write rejected',v_failure);
 v_failure:=false;
 begin perform public.fmz_phase6d_update_member_settings('{"avatar_y":2}',1); exception when invalid_parameter_value then v_failure:=true; end;
 perform pg_temp.check_hotfix('offscreen position rejected',v_failure);
 perform public.fmz_phase6a_record_consent('ai_processing','granted','phase6a-ai-processing-v1','nl',true,gen_random_uuid());
 perform public.fmz_phase6a_record_consent('private_chat','granted','phase6d-private-chat-v1','nl',true,gen_random_uuid());
 perform public.fmz_phase6d_record_analysis_consent('granted','phase6d-analysis-v1','nl',true,gen_random_uuid());
 perform public.fmz_phase6a_record_consent('trainer_summary_sharing','granted','phase6a-trainer-summary-v1','nl',true,gen_random_uuid());
 perform pg_temp.check_hotfix('private chat enabled',(public.fmz_phase6c_get_chat_status()->>'chat_write_allowed')::boolean);
 perform public.fmz_phase6a_record_consent('private_chat','withdrawn','phase6d-private-chat-v1','nl',true,gen_random_uuid());
 perform pg_temp.check_hotfix('private chat withdrawal enforced',not (public.fmz_phase6c_get_chat_status()->>'chat_write_allowed')::boolean);
 perform pg_temp.check_hotfix('other consents remain granted',(select consent_state='granted' from ai_private.current_consent(v_user,'ai_processing')) and (select consent_state='granted' from ai_private.current_consent(v_user,'ai_analysis')) and (select consent_state='granted' from ai_private.current_consent(v_user,'trainer_summary_sharing')));
 perform public.fmz_phase6a_record_consent('private_chat','granted','phase6d-private-chat-v1','nl',true,gen_random_uuid());
 perform public.fmz_phase6a_record_consent('ai_processing','withdrawn','phase6a-ai-processing-v1','nl',true,gen_random_uuid());
 perform pg_temp.check_hotfix('coach withdrawal does not revoke private chat',(public.fmz_phase6c_get_chat_status()->>'chat_write_allowed')::boolean);
 perform public.fmz_phase6a_service_record_safety_event(v_user,null,'unclear_health','hard_stop','owner-hotfix-test');
 select to_jsonb(s),s.revision into v_before,v_revision from public.ai_member_safety_state s where user_id=v_user;
 select count(*) into v_event_count from ai_private.safety_events where user_id=v_user;
 v_status:=public.fmz_phase6d_get_status();
 perform pg_temp.check_hotfix('old safety blocks analyses',not (v_status->'kinds'->'daily'->>'analysis_allowed')::boolean);
 perform pg_temp.check_hotfix('old safety does not block communication',(public.fmz_phase6c_get_chat_status()->>'chat_write_allowed')::boolean);
 v_failure:=false;
 begin perform public.fmz_phase6d_recover_analysis_safety(v_revision,'symptoms_resolved',true,false,true,gen_random_uuid()); exception when invalid_parameter_value then v_failure:=true; end;
 perform pg_temp.check_hotfix('incomplete confirmations cannot recover',v_failure);
 v_recovery:=public.fmz_phase6d_recover_analysis_safety(v_revision,'symptoms_resolved',true,true,true,v_req);
 perform pg_temp.check_hotfix('valid own recovery releases temporary block',not (v_recovery->>'analysis_blocked')::boolean);
 perform pg_temp.check_hotfix('recovery keeps action safety blocked',(v_recovery->>'automatic_execution_blocked')::boolean);
 perform pg_temp.check_hotfix('historical state byte-identical',v_before=(select to_jsonb(s) from public.ai_member_safety_state s where user_id=v_user));
 perform pg_temp.check_hotfix('historical audit remains',v_event_count=(select count(*) from ai_private.safety_events where user_id=v_user));
 perform pg_temp.check_hotfix('separate minimized recovery event',(select count(*)=1 from ai_private.analysis_safety_recoveries where user_id=v_user and reason_code='symptoms_resolved'));
 perform pg_temp.check_hotfix('same recovery request idempotent',(public.fmz_phase6d_recover_analysis_safety(v_revision,'symptoms_resolved',true,true,true,v_req)->>'replay')::boolean);
 perform pg_temp.check_hotfix('new read-only analyses allowed',(public.fmz_phase6d_get_status()->'kinds'->'daily'->>'analysis_allowed')::boolean);
 perform set_config('request.jwt.claim.sub',v_other::text,true);
 perform pg_temp.check_hotfix('new session different member gets own settings',public.fmz_phase6d_get_member_settings()->>'language'='nl');
 v_failure:=false;
 begin perform public.fmz_phase6d_recover_analysis_safety(v_revision,'symptoms_resolved',true,true,true,gen_random_uuid()); exception when serialization_failure then v_failure:=true; end;
 perform pg_temp.check_hotfix('cross member recovery cannot affect owner',v_failure);
 perform set_config('request.jwt.claim.sub',v_user::text,true);
 perform pg_temp.check_hotfix('refresh and new session retain language',public.fmz_phase6d_get_member_settings()->>'language'='en');
 perform pg_temp.check_hotfix('refresh and new session retain recovered status',not (public.fmz_phase6d_get_status()->'recovery'->>'analysis_blocked')::boolean);
 v_settings:=public.fmz_phase6d_update_preferences('Europe/London',true,'11:45',true,true,5::smallint,'19:15',0,v_pref_req);
 perform pg_temp.check_hotfix('all schedule fields persisted',v_settings->>'timezone_name'='Europe/London' and v_settings->>'daily_time'='11:45' and v_settings->>'weekly_day'='5' and v_settings->>'weekly_time'='19:15');
 perform pg_temp.check_hotfix('schedule RPC replay',(public.fmz_phase6d_update_preferences('Europe/London',true,'11:45',true,true,5::smallint,'19:15',0,v_pref_req)->>'replay')::boolean);
 perform pg_temp.check_hotfix('central and analysis schedule same source',public.fmz_phase6d_get_member_settings()->'analysis_preferences'=public.fmz_phase6d_get_status()->'preferences');
 v_failure:=false;
 begin perform public.fmz_phase6d_update_preferences('Mars/Test',true,'11:45',true,true,5::smallint,'19:15',1,gen_random_uuid()); exception when invalid_parameter_value then v_failure:=true; end;
 perform pg_temp.check_hotfix('invalid timezone rejected',v_failure);
 v_failure:=false;
 begin perform public.fmz_phase6d_update_preferences('UTC',true,'25:00',true,true,5::smallint,'19:15',1,gen_random_uuid()); exception when invalid_parameter_value then v_failure:=true; end;
 perform pg_temp.check_hotfix('invalid time rejected',v_failure);
 v_daily:=public.fmz_phase6d_prepare_analysis(gen_random_uuid(),'daily','nl',null);
 v_weekly:=public.fmz_phase6d_prepare_analysis(gen_random_uuid(),'weekly','nl',null);
 perform public.fmz_phase6d_update_preferences('Europe/Berlin',true,'21:30',true,true,2::smallint,'22:15',1,gen_random_uuid());
 perform pg_temp.check_hotfix('changed daily time does not duplicate',(public.fmz_phase6d_prepare_analysis(gen_random_uuid(),'daily','nl',null)->>'replay')::boolean);
 perform pg_temp.check_hotfix('changed weekly day does not duplicate',(public.fmz_phase6d_prepare_analysis(gen_random_uuid(),'weekly','nl',null)->>'replay')::boolean);
 perform pg_temp.check_hotfix('due selector excludes existing daily and weekly',not exists(select 1 from jsonb_array_elements(ai_private.phase6d_select_due_analyses(now(),200)->'candidates') c where c->>'user_id'=v_user::text and c->>'analysis_kind' in ('daily','weekly')));
 v_failure:=false;
 begin perform public.fmz_phase6d_prepare_analysis(gen_random_uuid(),'post_workout','nl',null); exception when invalid_parameter_value then v_failure:=true; end;
 perform pg_temp.check_hotfix('post workout requires completed authoritative workout',v_failure);
 insert into public.workout_sessions(id,user_id,local_session_key,status,title_snapshot,started_at,completed_at,source,metadata)
 values((select id from hotfix_ids where key='workout'),v_user,'owner-hotfix-workout','completed','Synthetic',now()-interval '2 hours',now()-interval '1 hour','phase3_client','{}');
 v_post:=public.fmz_phase6d_prepare_analysis(gen_random_uuid(),'post_workout','nl',(select id from hotfix_ids where key='workout'));
 perform pg_temp.check_hotfix('post workout exactly once',(public.fmz_phase6d_prepare_analysis(gen_random_uuid(),'post_workout','nl',(select id from hotfix_ids where key='workout'))->>'replay')::boolean);
 perform public.fmz_phase6c_create_thread(v_chat,'nl',gen_random_uuid());
 perform public.fmz_phase6a_service_record_safety_event(v_user,null,'serious_health','hard_stop','owner-hotfix-new-signal');
 perform pg_temp.check_hotfix('new serious signal hard stops again',(public.fmz_phase6d_get_status()->'recovery'->>'analysis_blocked')::boolean);
 v_failure:=false;
 begin perform public.fmz_phase6d_recover_analysis_safety(v_revision,'symptoms_resolved',true,true,true,gen_random_uuid()); exception when serialization_failure then v_failure:=true; end;
 perform pg_temp.check_hotfix('stale confirmation cannot clear new event',v_failure);
 perform public.fmz_phase6c_delete_thread(v_chat,(select revision from public.ai_threads where id=v_chat),gen_random_uuid());
 perform pg_temp.check_hotfix('chat deletion cannot bypass safety',(public.fmz_phase6d_get_status()->'recovery'->>'analysis_blocked')::boolean);
 select id into v_result from public.ai_analysis_results where user_id=v_user and analysis_kind='daily' limit 1;
 perform public.fmz_phase6d_delete_analysis(v_result,(select revision from public.ai_analysis_results where id=v_result),gen_random_uuid());
 perform pg_temp.check_hotfix('analysis deletion cannot bypass safety',(public.fmz_phase6d_get_status()->'recovery'->>'analysis_blocked')::boolean);
 perform pg_temp.check_hotfix('ordinary private chat remains usable',(public.fmz_phase6c_get_chat_status()->>'chat_write_allowed')::boolean);
 perform set_config('request.jwt.claim.sub',v_trainer::text,true);
 v_failure:=false;
 begin perform public.fmz_phase6d_recover_analysis_safety(v_revision,'misunderstood',true,true,true,gen_random_uuid()); exception when insufficient_privilege then v_failure:=true; end;
 perform pg_temp.check_hotfix('trainer cannot recover member',v_failure);
 v_failure:=false;
 begin perform public.fmz_phase6c_read_thread(v_chat,50,null); exception when insufficient_privilege then v_failure:=true; end;
 perform pg_temp.check_hotfix('trainer cannot read private chat',v_failure);
 perform pg_temp.check_hotfix('direct app preferences writes denied',not has_table_privilege('authenticated','public.member_app_preferences','INSERT,UPDATE,DELETE'));
 perform pg_temp.check_hotfix('direct recovery table access denied',not has_table_privilege('authenticated','ai_private.analysis_safety_recoveries','SELECT,INSERT,UPDATE,DELETE'));
 perform pg_temp.check_hotfix('anon settings RPC denied',not has_function_privilege('anon','public.fmz_phase6d_get_member_settings()','EXECUTE'));
 perform pg_temp.check_hotfix('anon recovery RPC denied',not has_function_privilege('anon','public.fmz_phase6d_recover_analysis_safety(bigint,text,boolean,boolean,boolean,uuid)','EXECUTE'));
 perform pg_temp.check_hotfix('no provider run cost',not exists(select 1 from ai_private.runs where user_id in (v_user,v_other) and (adapter_code<>'mock' or coalesce(actual_cost_micros,0)<>0)));
 perform pg_temp.check_hotfix('billing explicitly unavailable',not (public.fmz_phase6d_get_member_settings()->'subscription'->>'billing_available')::boolean);
 perform pg_temp.check_hotfix('account deletion explicitly unavailable',not (public.fmz_phase6d_get_member_settings()->>'account_deletion_available')::boolean);
end;
$test$;
select jsonb_build_object('overall_pass',bool_and(pass),'pass_count',count(*),'checks',jsonb_agg(name order by name)) as hotfix_result from hotfix_checks;
rollback;
