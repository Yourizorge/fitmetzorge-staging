-- Synthetic fixture transaction is always rolled back.
begin;
create temporary table hf2_checks(name text primary key,pass boolean);
create function pg_temp.hf2_check(n text,b boolean) returns void language plpgsql as $$
begin if b is distinct from true then raise exception 'HOTFIX2 FAILED: %',n; end if; insert into hf2_checks values(n,b); end;
$$;
create temporary table hf2_ids(k text primary key,id uuid default gen_random_uuid());
insert into hf2_ids(k) values('member'),('other'),('trainer'),('previous'),('current'),('first'),('offplan');
insert into auth.users(id,aud,role,email,created_at,updated_at)
 select id,'authenticated','authenticated','hf2-'||k||'@example.invalid',now(),now() from hf2_ids where k in ('member','other','trainer');
insert into public.profiles(id,role,name,email)
 select id,case when k='trainer' then 'trainer' else 'client' end,'HF2 fixture','hf2-'||k||'@example.invalid' from hf2_ids where k in ('member','other','trainer');
insert into public.user_onboarding(user_id,age,completed_at) select id,32,now() from hf2_ids where k in ('member','other');
insert into public.entitlements(user_id,entitlement_code,status,source,starts_at,ends_at)
 select id,'ai','active','hf2_fixture',now()-interval '1 day',now()+interval '29 days' from hf2_ids where k in ('member','other');
select set_config('request.jwt.claim.sub',(select id::text from hf2_ids where k='member'),true);
do $test$
declare
 u uuid:=(select id from hf2_ids where k='member');
 other_u uuid:=(select id from hf2_ids where k='other');
 previous_id uuid:=(select id from hf2_ids where k='previous');
 current_id uuid:=(select id from hf2_ids where k='current');
 first_id uuid:=(select id from hf2_ids where k='first');
 r jsonb; cmp jsonb; inbox jsonb; result_id uuid; day_result uuid; week_result uuid; fail boolean; count_before integer; original_safety jsonb;
begin
 perform public.fmz_phase6d_record_analysis_consent('granted','phase6d-analysis-v1','nl',true,gen_random_uuid());
 perform public.fmz_phase6d_sync_device_timezone('UTC');
 r:=public.fmz_phase6d_update_preferences('UTC',true,'00:00',true,true,extract(isodow from now())::smallint,'00:00',1,gen_random_uuid());
 perform pg_temp.hf2_check('timezone sync creates own prefs',r->>'timezone_name'='UTC');
 perform public.fmz_phase6d_sync_device_timezone('Europe/London');
 perform pg_temp.hf2_check('travel preserves chosen clock',(ai_private.phase6d_current_preferences(u)->>'daily_time')='00:00');
 fail:=false;begin perform public.fmz_phase6d_sync_device_timezone('Invalid/Fake');exception when invalid_parameter_value then fail:=true;end;
 perform pg_temp.hf2_check('invalid device timezone rejected',fail);
 perform public.fmz_phase6d_sync_device_timezone('UTC');
 insert into public.workout_sessions(id,user_id,local_session_key,status,title_snapshot,started_at,completed_at)
 values(previous_id,u,'hf2-previous','completed','Synthetic previous',now()-interval '7 days 1 hour',now()-interval '7 days');
 insert into public.workout_set_logs(id,user_id,workout_session_id,planned_exercise_key,exercise_slug,exercise_name_snapshot,set_index,actual_reps,actual_weight,rir,rpe)
 select gen_random_uuid(),u,previous_id,'squat','squat','Synthetic squat',i,10,30,2,7 from generate_series(1,2)i;
 update ai_private.analysis_jobs set status='cancelled' where user_id=u and workout_id=previous_id;
 insert into public.workout_sessions(id,user_id,local_session_key,status,title_snapshot,started_at)
 values(current_id,u,'hf2-current','active','Synthetic current',now()-interval '1 hour');
 insert into public.workout_set_logs(id,user_id,workout_session_id,planned_exercise_key,exercise_slug,exercise_name_snapshot,set_index,actual_reps,actual_weight,rir,rpe)
 select gen_random_uuid(),u,current_id,'squat','squat','Synthetic squat',i,10,35,1,8 from generate_series(1,2)i;
 perform pg_temp.hf2_check('active workout has no job',not exists(select 1 from ai_private.analysis_jobs where workout_id=current_id));
 update public.workout_sessions set status='completed',completed_at=now() where id=current_id;
 update public.workout_sessions set status='completed' where id=current_id;
 perform pg_temp.hf2_check('completed workout creates exactly one job',(select count(*) from ai_private.analysis_jobs where workout_id=current_id)=1);
 cmp:=ai_private.phase6d_workout_comparison(u,current_id);
 perform pg_temp.hf2_check('previous relevant workout exact ID',cmp->'previous'->>'id'=previous_id::text);
 perform pg_temp.hf2_check('same exercise match criterion',cmp->>'reason'='same_exercise_set');
 perform pg_temp.hf2_check('current volume is authoritative',cmp->'exercises'->0->'current'->>'volume_kg'='700.00');
 perform pg_temp.hf2_check('previous volume is authoritative',(cmp->'exercises'->0->'previous'->>'volume_kg')::numeric=600);
 perform pg_temp.hf2_check('RPE and RIR not invented',(cmp->'exercises'->0->'current'->>'rpe')::numeric=8 and (cmp->'exercises'->0->'current'->>'rir')::numeric=1);
 perform pg_temp.hf2_check('observed increase labelled',cmp->'exercises'->0->>'volume_change'='higher');
 perform pg_temp.hf2_check('duration labelled elapsed not active',cmp->>'duration_kind'='elapsed_including_pauses' and not (cmp->>'active_duration_available')::boolean);
 perform pg_temp.hf2_check('first suitable workout no invented previous',not (ai_private.phase6d_workout_comparison(u,previous_id)->>'available')::boolean);
 perform pg_temp.hf2_check('comparison rejects other owner',ai_private.phase6d_workout_comparison(other_u,current_id)->>'reason'='completed_workout_unavailable');

 update ai_private.phase6d_runtime_config set inbox_worker_enabled=true where singleton;
 r:=ai_private.phase6d_run_inbox_worker(50);
 perform pg_temp.hf2_check('worker completes automatically',exists(select 1 from ai_private.analysis_jobs where workout_id=current_id and status='completed'));
 select j.result_id into result_id from ai_private.analysis_jobs j where workout_id=current_id;
 perform pg_temp.hf2_check('result ID bound to completed workout',result_id is not null);
 perform pg_temp.hf2_check('post workout model Luna',(select model_tier='luna' and adapter_code='mock' from public.ai_analysis_results where id=result_id));
 perform pg_temp.hf2_check('result contains exact comparison',(public.fmz_phase6d_read_analysis(result_id)->'result'->'result_payload'->'comparison'->'previous'->>'id')=previous_id::text);
 perform pg_temp.hf2_check('notification once per exact result',(select count(*) from public.member_notifications where analysis_id=result_id)=1);
 select count(*) into count_before from public.ai_analysis_results where user_id=u;
 perform ai_private.phase6d_run_inbox_worker(50);
 perform pg_temp.hf2_check('worker retry no duplicate',(select count(*) from public.ai_analysis_results where user_id=u)=count_before);
 select id into day_result from public.ai_analysis_results where user_id=u and analysis_kind='daily';
 select id into week_result from public.ai_analysis_results where user_id=u and analysis_kind='weekly';
 perform pg_temp.hf2_check('daily generated automatically',day_result is not null);
 perform pg_temp.hf2_check('weekly generated automatically',week_result is not null);
 perform pg_temp.hf2_check('weekly model Terra',(select model_tier='terra' from public.ai_analysis_results where id=week_result));
 perform pg_temp.hf2_check('weekly stable ISO event',(select event_key='weekly:'||to_char(now(),'IYYY-IW') from public.ai_analysis_results where id=week_result));
 perform pg_temp.hf2_check('no executable actions',(select bool_and(result_payload->'actions'='[]'::jsonb) from public.ai_analysis_results where user_id=u));
 perform pg_temp.hf2_check('zero provider calls and budget cost',(select coalesce(sum(actual_cost_micros),0)=0 and bool_and(adapter_code='mock') from ai_private.runs where user_id=u));

 inbox:=public.fmz_phase6d_get_inbox();
 perform pg_temp.hf2_check('bounded inbox has generated result',exists(select 1 from jsonb_array_elements(inbox->'items') i where i->>'analysis_id'=result_id::text));
 perform public.fmz_phase6d_mark_notification(result_id,'later');
 perform pg_temp.hf2_check('later remains in persisted inbox',exists(select 1 from jsonb_array_elements(public.fmz_phase6d_get_inbox()->'items')i where i->>'analysis_id'=result_id::text and i->>'state'='later'));
 perform set_config('request.jwt.claim.sub',other_u::text,true);
 fail:=false;begin perform public.fmz_phase6d_read_analysis(result_id);exception when insufficient_privilege then fail:=true;end;
 perform pg_temp.hf2_check('detail cross-member denied',fail);
 fail:=false;begin perform public.fmz_phase6d_mark_notification(result_id,'opened');exception when insufficient_privilege then fail:=true;end;
 perform pg_temp.hf2_check('notification cross-member denied',fail);
 perform pg_temp.hf2_check('other inbox isolated',jsonb_array_length(public.fmz_phase6d_get_inbox()->'items')=0);
 perform set_config('request.jwt.claim.sub',u::text,true);
 perform pg_temp.hf2_check('new session retains deferred notification',exists(select 1 from jsonb_array_elements(public.fmz_phase6d_get_inbox()->'items')i where i->>'analysis_id'=result_id::text and i->>'state'='later'));
 perform public.fmz_phase6d_mark_notification(result_id,'opened');
 perform public.fmz_phase6d_mark_notification(result_id,'later');
 perform pg_temp.hf2_check('late later action cannot regress opened',(select state='opened' from public.member_notifications where analysis_id=result_id));
 perform pg_temp.hf2_check('opened leaves dashboard inbox',not exists(select 1 from jsonb_array_elements(public.fmz_phase6d_get_inbox()->'items')i where i->>'analysis_id'=result_id::text));
 perform pg_temp.hf2_check('opened result still readable',(public.fmz_phase6d_read_analysis(result_id)->'result'->>'id')=result_id::text);
 perform pg_temp.hf2_check('existing export includes results',public.fmz_phase6d_export_analyses(gen_random_uuid()) is not null);
 r:=public.fmz_phase6d_read_analysis(result_id);
 perform public.fmz_phase6d_delete_analysis(result_id,(r->'result'->>'revision')::bigint,gen_random_uuid());
 perform pg_temp.hf2_check('deleted result notification archived',(select state='archived' from public.member_notifications where analysis_id=result_id));
 fail:=false;begin perform public.fmz_phase6d_read_analysis(result_id);exception when invalid_parameter_value then fail:=true;end;
 perform pg_temp.hf2_check('deleted detail unavailable',fail);
 perform public.fmz_phase6d_sync_device_timezone('Pacific/Honolulu');
 perform ai_private.phase6d_run_inbox_worker(50);
 perform pg_temp.hf2_check('travel no daily duplicate',(select count(*) from public.ai_analysis_results where user_id=u and analysis_kind='daily')=1);
 perform pg_temp.hf2_check('travel no weekly duplicate',(select count(*) from public.ai_analysis_results where user_id=u and analysis_kind='weekly')=1);
 perform pg_temp.hf2_check('deleting result does not recreate workout',(select count(*) from ai_private.analysis_jobs where workout_id=current_id)=1);

 perform set_config('request.jwt.claim.sub',(select id::text from hf2_ids where k='trainer'),true);
 fail:=false;begin perform public.fmz_phase6d_read_analysis(day_result);exception when insufficient_privilege then fail:=true;end;
 perform pg_temp.hf2_check('trainer private detail denied',fail);
 perform set_config('request.jwt.claim.sub','',true);
 fail:=false;begin perform public.fmz_phase6d_get_inbox();exception when insufficient_privilege then fail:=true;end;
 perform pg_temp.hf2_check('anonymous inbox denied',fail);
 perform pg_temp.hf2_check('anonymous cannot execute detail',not has_function_privilege('anon','public.fmz_phase6d_read_analysis(uuid)','execute'));
 perform pg_temp.hf2_check('member cannot execute worker',not has_function_privilege('authenticated','ai_private.phase6d_run_inbox_worker(integer)','execute'));
 perform pg_temp.hf2_check('no direct browser notifications',not has_table_privilege('authenticated','public.member_notifications','select,insert,update,delete'));
 perform pg_temp.hf2_check('no direct browser jobs',not has_table_privilege('authenticated','ai_private.analysis_jobs','select,insert,update,delete'));
 perform pg_temp.hf2_check('both new tables RLS',(select bool_and(relrowsecurity) from pg_class where oid in ('public.member_notifications'::regclass,'ai_private.analysis_jobs'::regclass)));

 -- An existing queued job must honor consent, entitlement and current safety at execution.
 perform set_config('request.jwt.claim.sub',other_u::text,true);
 perform public.fmz_phase6d_sync_device_timezone('UTC');
 insert into public.workout_sessions(id,user_id,local_session_key,status,title_snapshot,started_at,completed_at)
 values(first_id,other_u,'hf2-first','completed','Synthetic first',now()-interval '1 hour',now());
 perform ai_private.phase6d_run_inbox_worker(50);
 perform pg_temp.hf2_check('no consent defers queued workout',exists(select 1 from ai_private.analysis_jobs where workout_id=first_id and status='queued' and last_error_code='ai_analysis_consent_required'));
 perform public.fmz_phase6d_record_analysis_consent('granted','phase6d-analysis-v1','de',true,gen_random_uuid());
 perform public.fmz_phase6d_record_analysis_consent('withdrawn','phase6d-analysis-v1','de',true,gen_random_uuid());
 update ai_private.analysis_jobs set available_at=now() where user_id=other_u;
 perform ai_private.phase6d_run_inbox_worker(50);
 perform pg_temp.hf2_check('withdrawn consent makes no result',not exists(select 1 from public.ai_analysis_results where user_id=other_u));
 perform public.fmz_phase6d_record_analysis_consent('granted','phase6d-analysis-v1','de',true,gen_random_uuid());
 update public.entitlements set ends_at=now()-interval '1 hour' where user_id=other_u;
 update ai_private.analysis_jobs set available_at=now() where user_id=other_u;
 perform ai_private.phase6d_run_inbox_worker(50);
 perform pg_temp.hf2_check('expired entitlement defers without result',not exists(select 1 from public.ai_analysis_results where user_id=other_u));
 update public.entitlements set ends_at=now()+interval '29 days' where user_id=other_u;
 perform public.fmz_phase6a_service_record_safety_event(other_u,null,'serious_health','hard_stop','hf2-safety');
 select to_jsonb(s) into original_safety from public.ai_member_safety_state s where user_id=other_u;
 update ai_private.analysis_jobs set available_at=now() where user_id=other_u;
 perform ai_private.phase6d_run_inbox_worker(50);
 perform pg_temp.hf2_check('new safety blocks queued execution',not exists(select 1 from public.ai_analysis_results where user_id=other_u));
 perform public.fmz_phase6d_recover_analysis_safety((original_safety->>'revision')::bigint,'symptoms_resolved',true,true,true,gen_random_uuid());
 update ai_private.analysis_jobs set available_at=now() where user_id=other_u;
 perform ai_private.phase6d_run_inbox_worker(50);
 perform pg_temp.hf2_check('explicit recovery permits queued workout',exists(select 1 from ai_private.analysis_jobs where workout_id=first_id and status='completed'));
 perform pg_temp.hf2_check('worker preserves historical safety',original_safety=(select to_jsonb(s) from public.ai_member_safety_state s where user_id=other_u));
 perform public.fmz_phase6a_service_record_safety_event(other_u,null,'serious_health','hard_stop','hf2-safety-new');
 perform pg_temp.hf2_check('new risk blocks again after recovery',not (ai_private.phase6d_analysis_status(other_u,'post_workout',now())->>'analysis_allowed')::boolean);
 select to_jsonb(s) into original_safety from public.ai_member_safety_state s where user_id=other_u;
 perform public.fmz_phase6d_recover_analysis_safety((original_safety->>'revision')::bigint,'symptoms_resolved',true,true,true,gen_random_uuid());

 -- A queued weekly time is rechecked; one sparse training cannot produce a weekly conclusion.
 r:=ai_private.phase6d_current_preferences(other_u);
 perform public.fmz_phase6d_update_preferences('UTC',false,'23:59',true,true,((extract(isodow from now())::integer%7)+1)::smallint,'00:00',(r->>'revision')::bigint,gen_random_uuid());
 insert into ai_private.analysis_jobs(user_id,analysis_kind,event_key)
 values(other_u,'weekly','weekly:'||to_char(now(),'IYYY-IW')) on conflict do nothing;
 update ai_private.analysis_jobs set available_at=now() where user_id=other_u and analysis_kind='weekly';
 perform ai_private.phase6d_run_inbox_worker(50);
 perform pg_temp.hf2_check('changed weekly day honored for queued job',not exists(select 1 from public.ai_analysis_results where user_id=other_u and analysis_kind='weekly'));
 r:=ai_private.phase6d_current_preferences(other_u);
 perform public.fmz_phase6d_update_preferences('UTC',false,'23:59',true,true,extract(isodow from now())::smallint,'23:59',(r->>'revision')::bigint,gen_random_uuid());
 update ai_private.analysis_jobs set available_at=now() where user_id=other_u and analysis_kind='weekly';
 perform ai_private.phase6d_run_inbox_worker(50);
 perform pg_temp.hf2_check('changed weekly clock honored for queued job',not exists(select 1 from public.ai_analysis_results where user_id=other_u and analysis_kind='weekly'));
 r:=ai_private.phase6d_current_preferences(other_u);
 perform public.fmz_phase6d_update_preferences('UTC',false,'23:59',true,true,extract(isodow from now())::smallint,'00:00',(r->>'revision')::bigint,gen_random_uuid());
 update ai_private.analysis_jobs set available_at=now() where user_id=other_u and analysis_kind='weekly';
 perform ai_private.phase6d_run_inbox_worker(50);
 perform pg_temp.hf2_check('insufficient weekly data has no invented observations',exists(select 1 from public.ai_analysis_results where user_id=other_u and analysis_kind='weekly' and status='insufficient_data' and result_payload->'observations'='[]'));
 perform pg_temp.hf2_check('insufficient result also delivered to inbox',exists(select 1 from public.member_notifications n join public.ai_analysis_results a on a.id=n.analysis_id where a.user_id=other_u and a.analysis_kind='weekly' and a.status='insufficient_data'));
end;
$test$;
select count(*) as pass_count,bool_and(pass) as overall_pass from hf2_checks;
rollback;
