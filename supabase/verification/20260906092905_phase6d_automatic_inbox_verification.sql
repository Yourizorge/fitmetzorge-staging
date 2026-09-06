begin;
create temporary table hf2_verify(name text,pass boolean);
insert into hf2_verify values
('migration recorded',exists(select 1 from supabase_migrations.schema_migrations where version='20260906092905')),
('job RLS',(select relrowsecurity from pg_class where oid='ai_private.analysis_jobs'::regclass)),
('inbox RLS',(select relrowsecurity from pg_class where oid='public.member_notifications'::regclass)),
('workout trigger installed',exists(select 1 from pg_trigger where tgname='phase6d_workout_analysis_job' and tgenabled='O')),
('result trigger installed',exists(select 1 from pg_trigger where tgname='phase6d_result_notification' and tgenabled='O')),
('one active DB mock cron',1=(select count(*) from cron.job where jobname='fmz-phase6d-inbox-mock-worker' and active and schedule='* * * * *' and command='select ai_private.phase6d_run_inbox_worker(10)')),
('browser cannot write inbox',not has_table_privilege('authenticated','public.member_notifications','insert,update,delete')),
('browser cannot read jobs',not has_table_privilege('authenticated','ai_private.analysis_jobs','select')),
('anonymous cannot read detail',not has_function_privilege('anon','public.fmz_phase6d_read_analysis(uuid)','execute')),
('anonymous cannot read inbox',not has_function_privilege('anon','public.fmz_phase6d_get_inbox()','execute')),
('anonymous cannot mark inbox',not has_function_privilege('anon','public.fmz_phase6d_mark_notification(uuid,text)','execute')),
('anonymous cannot sync timezone',not has_function_privilege('anon','public.fmz_phase6d_sync_device_timezone(text)','execute')),
('member cannot call private prepare',not has_function_privilege('authenticated','ai_private.phase6d_prepare_member_analysis(uuid,uuid,text,text,uuid)','execute')),
('member cannot execute worker',not has_function_privilege('authenticated','ai_private.phase6d_run_inbox_worker(integer)','execute')),
('member cannot complete results',not has_function_privilege('authenticated','public.fmz_phase6d_service_complete_analysis(uuid,uuid,jsonb,bigint,integer,integer)','execute')),
('inbox own-user predicate',exists(select 1 from pg_policies where schemaname='public' and tablename='member_notifications' and qual like '%auth.uid()%user_id%')),
('zero orphan inbox owners',not exists(select 1 from public.member_notifications n join public.ai_analysis_results r on r.id=n.analysis_id where n.user_id<>r.user_id)),
('zero duplicate notification results',not exists(select 1 from public.member_notifications group by user_id,analysis_id having count(*)>1)),
('zero duplicate jobs',not exists(select 1 from ai_private.analysis_jobs group by user_id,analysis_kind,event_key having count(*)>1)),
('zero mock provider cost',not exists(select 1 from ai_private.runs where schema_version='phase6d.analysis.v1' and (adapter_code<>'mock' or coalesce(actual_cost_micros,0)<>0))),
('all analyses have no executable actions',not exists(select 1 from public.ai_analysis_results where status in ('ready','partial','insufficient_data') and result_payload->'actions'<>'[]'::jsonb)),
('external provider disabled',(select not external_provider_enabled and mock_analyses_enabled and scheduled_generation_enabled from ai_private.phase6d_runtime_config where singleton)),
('no transactional fixture users',not exists(select 1 from auth.users where email in ('hf2-member@example.invalid','hf2-other@example.invalid','hf2-trainer@example.invalid','phase6d-owner-member@example.invalid','phase6d-owner-other@example.invalid','phase6d-owner-trainer@example.invalid')));
select jsonb_build_object(
 'overall_pass',bool_and(pass),'pass_count',count(*) filter(where pass),'failed',coalesce(jsonb_agg(name)filter(where not pass),'[]'),
 'worker_enabled',(select inbox_worker_enabled from ai_private.phase6d_runtime_config where singleton),
 'queued_jobs',(select count(*) from ai_private.analysis_jobs where status='queued'),
 'notifications',(select count(*) from public.member_notifications),
 'cron_runs',(select coalesce(jsonb_agg(to_jsonb(x)),'[]') from (
   select d.status,d.return_message,d.start_time,d.end_time from cron.job_run_details d join cron.job j using(jobid)
   where j.jobname='fmz-phase6d-inbox-mock-worker' order by d.start_time desc limit 3
 ) x)
) as hotfix2_verification from hf2_verify;
rollback;
