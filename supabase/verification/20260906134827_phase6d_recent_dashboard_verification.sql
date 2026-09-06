begin;
create temporary table mobile_verify(name text,pass boolean);
insert into mobile_verify values
('migration recorded',exists(select 1 from supabase_migrations.schema_migrations where version='20260906134827')),
('recent read model declared',pg_get_functiondef('public.fmz_phase6d_get_inbox()'::regprocedure) like '%''recent''%limit 3%'),
('results are availability source',pg_get_functiondef('public.fmz_phase6d_get_inbox()'::regprocedure) like '%from public.ai_analysis_results r%left join public.member_notifications%'),
('member-bound read',pg_get_functiondef('public.fmz_phase6d_get_inbox()'::regprocedure) like '%auth.uid()%assert_member%r.user_id=v_user%'),
('member-bound mark',pg_get_functiondef('public.fmz_phase6d_mark_notification(uuid,text)'::regprocedure) like '%auth.uid()%assert_member%user_id=v_user for update%'),
('read does not backfill',pg_get_functiondef('public.fmz_phase6d_get_inbox()'::regprocedure) not ilike '%insert into%'),
('explicit action missing-state upsert',pg_get_functiondef('public.fmz_phase6d_mark_notification(uuid,text)'::regprocedure) like '%on conflict(user_id,analysis_id) do update%'),
('anonymous read denied',not has_function_privilege('anon','public.fmz_phase6d_get_inbox()','execute')),
('anonymous mark denied',not has_function_privilege('anon','public.fmz_phase6d_mark_notification(uuid,text)','execute')),
('browser notifications read write denied',not has_table_privilege('authenticated','public.member_notifications','select,insert,update,delete')),
('browser results write denied',not has_table_privilege('authenticated','public.ai_analysis_results','insert,update,delete')),
('two tables RLS',(select bool_and(relrowsecurity) from pg_class where oid in ('public.member_notifications'::regclass,'public.ai_analysis_results'::regclass))),
('no mismatched notification owner',not exists(select 1 from public.member_notifications n join public.ai_analysis_results r on r.id=n.analysis_id where r.user_id<>n.user_id)),
('no duplicate notifications',not exists(select 1 from public.member_notifications group by user_id,analysis_id having count(*)>1)),
('mock worker preserved',(select inbox_worker_enabled and mock_analyses_enabled and scheduled_generation_enabled and not external_provider_enabled from ai_private.phase6d_runtime_config where singleton)),
('no mobile fixtures',not exists(select 1 from auth.users where email in ('mobile-final-member@example.invalid','mobile-final-other@example.invalid','mobile-final-trainer@example.invalid'))),
('zero analysis provider cost',not exists(select 1 from ai_private.runs where schema_version='phase6d.analysis.v1' and (adapter_code<>'mock' or coalesce(actual_cost_micros,0)<>0))),
('cron active',exists(select 1 from cron.job where jobname='fmz-phase6d-inbox-mock-worker' and active));
select jsonb_build_object('pass_count',count(*) filter(where pass),'overall_pass',bool_and(pass),'failed',coalesce(jsonb_agg(name)filter(where not pass),'[]'),
 'existing_availability',(select jsonb_agg(x) from (
  select r.analysis_kind,coalesce(n.state,'new') as state,count(*) as available,
   count(*) filter(where n.state in ('new','later')) as old_dashboard_eligible
  from public.ai_analysis_results r left join public.member_notifications n on n.analysis_id=r.id and n.user_id=r.user_id
  where r.status in ('ready','partial','insufficient_data') and r.content_deleted_at is null and r.result_expires_at>now() and coalesce(n.state,'new')<>'archived'
  group by 1,2 order by 1,2
 )x)) as mobile_verification from mobile_verify;
rollback;

