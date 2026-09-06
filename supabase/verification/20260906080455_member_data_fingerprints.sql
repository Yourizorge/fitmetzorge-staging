begin;
create temporary table hotfix_member_fingerprints(table_name text,row_count bigint,content_md5 text);
do $$
declare t record; n bigint; h text;
begin
 for t in select table_schema,table_name from information_schema.tables
 where table_schema in ('public','ai_private') and table_type='BASE TABLE' and table_name in
 ('profiles','user_settings','user_onboarding','entitlements','coach_workspaces','recovery_logs','training_plans','training_days','training_exercises',
 'workout_sessions','workout_set_logs','food_logs','food_log_items','nutrition_targets','weight_logs','body_measurements',
 'ai_threads','ai_messages','ai_member_safety_state','ai_consent_events','ai_analysis_results','ai_analysis_preferences','safety_events')
 order by table_schema,table_name loop
  execute format('select count(*),md5(coalesce(string_agg(to_jsonb(t)::text,%L order by to_jsonb(t)::text),%L)) from %I.%I t','','',t.table_schema,t.table_name) into n,h;
  insert into hotfix_member_fingerprints values(t.table_schema||'.'||t.table_name,n,h);
 end loop;
end; $$;
select * from hotfix_member_fingerprints order by table_name;
rollback;
