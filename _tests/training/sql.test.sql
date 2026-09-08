-- Controlled synthetic fixtures only; all changes rolled back.
begin;
set local statement_timeout='30s';
create temporary table training_test_results(label text primary key,pass boolean);
grant select,insert on training_test_results to authenticated,anon;
create function pg_temp.training_assert(p_label text,p_pass boolean) returns void language plpgsql as $$
begin
 if p_pass is distinct from true then raise exception 'training_test_failed:%',p_label; end if;
 insert into training_test_results values(p_label,true);
end; $$;
insert into auth.users(id,email,raw_user_meta_data) values
 ('660e1000-0000-4000-8000-000000000001','training-a@example.invalid','{"role":"client","name":"Training Synthetic A"}'),
 ('660e1000-0000-4000-8000-000000000002','training-b@example.invalid','{"role":"client","name":"Training Synthetic B"}');
insert into public.profiles(id,role,name,email) values
 ('660e1000-0000-4000-8000-000000000001','client','Training Synthetic A','training-a@example.invalid'),
 ('660e1000-0000-4000-8000-000000000002','client','Training Synthetic B','training-b@example.invalid')
 on conflict(id) do nothing;
select set_config('request.jwt.claim.sub','660e1000-0000-4000-8000-000000000001',true);
set local role authenticated;
do $test$
declare
 rows jsonb; single_row jsonb; result jsonb; revision timestamptz; before_count bigint; e record; n integer;
 pid uuid:='660e1000-0000-4000-8000-000000000100'; did uuid:='660e1000-0000-4000-8000-000000000110';
 sid uuid:='660e1000-0000-4000-8000-000000000120';
 saveid uuid:='660e1000-0000-4000-8000-000000000130';
begin
 select * into e from public.exercises where is_active order by canonical_slug limit 1;
 perform pg_temp.training_assert('canonical catalog available',e.id is not null);
 single_row:=jsonb_build_object('id','660e1000-0000-4000-8000-000000000201','exercise_id',e.id,
  'exercise_slug',e.canonical_slug,'rest_seconds',60,'notes','Synthetic only','tempo',null,
  'set_targets',jsonb_build_array(jsonb_build_object('reps','8-10','weight',null,'rir',0,'rpe',null)),
  'superset_id',null,'superset_rest_seconds',null);
 rows:=jsonb_build_array(single_row);
 result:=public.fmz_training_save_workout(pid,did,'Synthetic workout','Maandag',0,rows,null,saveid);
 revision:=(result->>'updated_at')::timestamptz;
 perform pg_temp.training_assert('own atomic create',exists(select 1 from public.training_plan_exercises where training_plan_day_id=did and set_targets->0->>'rir'='0'));
 result:=public.fmz_training_save_workout(pid,did,'Synthetic workout','Maandag',0,rows,null,saveid);
 perform pg_temp.training_assert('same save id is idempotent',(result->>'replayed')::boolean and (select count(*) from public.training_plans where id=pid)=1);
 begin
  perform public.fmz_training_save_workout(pid,did,'Changed retry','Maandag',0,rows,null,saveid);
  raise exception 'expected retry conflict';
 exception when invalid_parameter_value then perform pg_temp.training_assert('changed retry payload rejected',true); end;
 begin
  perform public.fmz_training_save_workout(pid,did,'Stale','Maandag',0,rows,revision-interval '1 second',gen_random_uuid());
  raise exception 'expected stale';
 exception when serialization_failure then perform pg_temp.training_assert('optimistic conflict rejected',true); end;
 perform pg_temp.training_assert('blank effort remains null',exists(select 1 from public.training_plan_exercises where training_plan_day_id=did and target_rpe is null and target_rir=0));
 for n in 1..9 loop
  begin
   perform public.fmz_training_save_workout(gen_random_uuid(),gen_random_uuid(),'Invalid','Maandag',0,
    jsonb_build_array(jsonb_set(single_row,'{id}',to_jsonb(gen_random_uuid()::text)) ||
      jsonb_build_object('set_targets',case n
       when 1 then '[{"reps":"8","weight":null,"rir":null,"rpe":0}]'::jsonb
       when 2 then '[{"reps":"8","weight":null,"rir":1.5,"rpe":null}]'::jsonb
       when 3 then '[{"reps":"8","weight":-1,"rir":null,"rpe":null}]'::jsonb
       when 4 then '[{"reps":"0","weight":null,"rir":null,"rpe":null}]'::jsonb
       when 5 then '[]'::jsonb
       when 7 then '[{"reps":"10-8","weight":null,"rir":null,"rpe":null}]'::jsonb
       when 8 then '[{"reps":"8-0","weight":null,"rir":null,"rpe":null}]'::jsonb
       when 9 then '[{"reps":"00","weight":null,"rir":null,"rpe":null}]'::jsonb
       else '[{"reps":"8","weight":null,"rir":null,"rpe":null,"advice":"forbidden"}]'::jsonb end)),null,gen_random_uuid());
   raise exception 'expected target validation';
  exception when invalid_parameter_value then perform pg_temp.training_assert('server target validation '||n,true); end;
 end loop;
 perform pg_temp.training_assert('failed saves leave no partial plans',(select count(*) from public.training_plans where user_id=auth.uid())=1);
 rows:=jsonb_build_array(single_row||jsonb_build_object('superset_id','660e1000-0000-4000-8000-000000000300','superset_rest_seconds',120),
   single_row||jsonb_build_object('id','660e1000-0000-4000-8000-000000000202','superset_id','660e1000-0000-4000-8000-000000000300','superset_rest_seconds',120));
 result:=public.fmz_training_save_workout(pid,did,'Superset','Maandag',0,rows,revision,gen_random_uuid());
 revision:=(result->>'updated_at')::timestamptz;
 perform pg_temp.training_assert('superset order and group rest persisted',(select count(*) from public.training_plan_exercises where training_plan_day_id=did and status='active' and superset_rest_seconds=120)=2);
 begin
  perform public.fmz_training_save_workout(pid,did,'Broken','Maandag',0,jsonb_set(rows,'{1,superset_rest_seconds}','90'),revision,gen_random_uuid());
  raise exception 'expected group validation';
 exception when invalid_parameter_value then perform pg_temp.training_assert('mixed group rest rejected',true); end;
 insert into public.workout_sessions(id,user_id,training_plan_id,training_plan_day_id,local_session_key,title_snapshot,started_at,metadata)
 values(sid,auth.uid(),pid,did,'synthetic-training-session','Superset',now()-interval '30 minutes',jsonb_build_object('plannedExercises',rows));
 result:=public.fmz_training_save_workout(pid,did,'Edited later','Maandag',0,jsonb_build_array(single_row),revision,gen_random_uuid());
 perform pg_temp.training_assert('removed exercise archived not deleted',exists(select 1 from public.training_plan_exercises where id='660e1000-0000-4000-8000-000000000202' and status='archived'));
 perform pg_temp.training_assert('started session snapshot unchanged',(select metadata->'plannedExercises'=rows and title_snapshot='Superset' from public.workout_sessions where id=sid));
 insert into public.workout_set_logs(id,user_id,workout_session_id,training_plan_exercise_id,exercise_id,planned_exercise_key,exercise_slug,exercise_name_snapshot,set_index,actual_reps,actual_weight,rir,rpe)
 values(gen_random_uuid(),auth.uid(),sid,'660e1000-0000-4000-8000-000000000201',e.id,'660e1000-0000-4000-8000-000000000201',e.canonical_slug,e.name_en,1,10,null,0,null);
 perform pg_temp.training_assert('set missing weight/RPE never zero',exists(select 1 from public.workout_set_logs where workout_session_id=sid and actual_weight is null and rir=0 and rpe is null));
 result:=public.fmz_training_complete_workout(sid,now(),'{}');
 result:=public.fmz_training_complete_workout(sid,now()+interval '1 minute','{}');
 perform pg_temp.training_assert('completion idempotent without timestamp change',(result->>'replayed')::boolean and (select completed_at=now() from public.workout_sessions where id=sid));
 perform pg_temp.training_assert('completed snapshot retained',(select metadata->'plannedExercises'=rows from public.workout_sessions where id=sid));
 result:=public.fmz_training_get_preferences();
 perform pg_temp.training_assert('default effort RIR timer enabled',result->>'effort_mode'='rir' and (result->>'timer_enabled')::boolean);
 result:=public.fmz_training_set_preferences('none',false,(result->>'revision')::bigint);
 perform pg_temp.training_assert('own preferences persisted',result->>'effort_mode'='none' and not (result->>'timer_enabled')::boolean);
 perform pg_temp.training_assert('effort preference does not rewrite history',exists(select 1 from public.workout_set_logs where workout_session_id=sid and rir=0 and rpe is null));
 begin
  perform public.fmz_training_set_preferences('invalid',true,(result->>'revision')::bigint);
  raise exception 'expected preference validation';
 exception when invalid_parameter_value then perform pg_temp.training_assert('invalid preference rejected',true); end;
 for n in 2..4 loop
  perform public.fmz_training_save_workout(gen_random_uuid(),gen_random_uuid(),'Synthetic '||n,'Maandag',0,
   jsonb_build_array(jsonb_set(single_row,'{id}',to_jsonb(gen_random_uuid()::text))),null,gen_random_uuid());
 end loop;
 begin
  perform public.fmz_training_save_workout(gen_random_uuid(),gen_random_uuid(),'Fifth','Maandag',0,
   jsonb_build_array(jsonb_set(single_row,'{id}',to_jsonb(gen_random_uuid()::text))),null,gen_random_uuid());
  raise exception 'expected Free limit';
 exception when check_violation then perform pg_temp.training_assert('Free maximum four preserved',true); end;
end;
$test$;
select set_config('request.jwt.claim.sub','660e1000-0000-4000-8000-000000000002',true);
do $test$
begin
 perform pg_temp.training_assert('cross-user plans hidden',not exists(select 1 from public.training_plans));
 perform pg_temp.training_assert('cross-user sets hidden',not exists(select 1 from public.workout_set_logs));
 begin
  perform public.fmz_training_complete_workout('660e1000-0000-4000-8000-000000000120',now(),'{}');
  raise exception 'expected cross-user denial';
 exception when insufficient_privilege then perform pg_temp.training_assert('cross-user completion denied',true); end;
 perform pg_temp.training_assert('preferences isolated',public.fmz_training_get_preferences()->>'effort_mode'='rir');
end; $test$;
reset role;
select pg_temp.training_assert('anon RPC execute denied',not has_function_privilege('anon','public.fmz_training_save_workout(uuid,uuid,text,text,integer,jsonb,timestamptz,uuid)','execute'));
select pg_temp.training_assert('RLS retained',(select bool_and(relrowsecurity) from pg_class where oid in ('public.training_plans'::regclass,'public.training_plan_exercises'::regclass,'public.workout_sessions'::regclass,'public.workout_set_logs'::regclass,'public.member_app_preferences'::regclass)));
select jsonb_build_object('synthetic_only',true,'rolled_back',true,'checks',jsonb_agg(to_jsonb(r) order by label),'pass_count',count(*)) from training_test_results r;
rollback;
