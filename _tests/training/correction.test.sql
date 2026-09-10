-- Controlled synthetic fixtures only; all changes rolled back.
begin;
set local statement_timeout='30s';
create temporary table training_test_results(label text primary key,pass boolean);
create temporary table training_test_fixture(pid uuid,did uuid,rows jsonb,revision timestamptz);
grant select,insert on training_test_fixture to authenticated;
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
declare e record; rowdata jsonb; flags jsonb; result jsonb; rev timestamptz; pid uuid; did uuid; saveid uuid; sid uuid; n integer;
begin
 select * into e from public.exercises where is_active order by canonical_slug limit 1;
 for n in 0..3 loop
  pid:=gen_random_uuid();did:=gen_random_uuid();saveid:=gen_random_uuid();sid:=gen_random_uuid();
  flags:=jsonb_build_object('rir',n in(1,3),'rpe',n in(2,3));
  rowdata:=jsonb_build_array(jsonb_build_object('id',gen_random_uuid(),'exercise_id',e.id,'exercise_slug',e.canonical_slug,
   'rest_seconds',60,'notes','Synthetic only','tempo',null,'superset_id',null,'superset_rest_seconds',null,
   'set_targets',jsonb_build_array(jsonb_build_object('reps','8','weight',55.5,'rir',0,'rpe',9.5))));
  result:=public.fmz_training_save_workout_v2(pid,did,'Synthetic choices','Maandag',0,rowdata,null,saveid,flags);
  rev:=(result->>'updated_at')::timestamptz;
  insert into training_test_fixture values(pid,did,rowdata,rev);
  perform pg_temp.training_assert('create flags '||n,(select metadata->'effort_tracking'=flags from public.training_plans where id=pid));
  result:=public.fmz_training_save_workout_v2(pid,did,'Synthetic choices','Maandag',0,rowdata,null,saveid,flags);
  perform pg_temp.training_assert('idempotent '||n,(result->>'replayed')::boolean);
  begin
   perform public.fmz_training_save_workout_v2(pid,did,'Synthetic choices','Maandag',0,rowdata,null,saveid,jsonb_build_object('rir',not(n in(1,3)),'rpe',false));
   raise exception 'expected mismatch';
  exception when invalid_parameter_value then perform pg_temp.training_assert('changed flag retry rejected '||n,true); end;
  insert into public.workout_sessions(id,user_id,training_plan_id,training_plan_day_id,local_session_key,status,title_snapshot,started_at,source,metadata)
   values(sid,auth.uid(),pid,did,sid::text,'active','Synthetic',now(),'phase3_client',jsonb_build_object('effortTracking',flags,'plannedExercises',rowdata));
  insert into public.workout_set_logs(id,user_id,workout_session_id,planned_exercise_key,exercise_slug,exercise_name_snapshot,set_index,actual_reps,actual_weight,rir,rpe,completed_at,source)
   values(gen_random_uuid(),auth.uid(),sid,'synthetic',e.canonical_slug,e.name_en,1,8,55.5,0,9.5,now(),'phase3_client');
  result:=public.fmz_training_save_workout_v2(pid,did,'Synthetic edit','Maandag',0,rowdata,rev,gen_random_uuid(),'{"rir":false,"rpe":false}');
  perform pg_temp.training_assert('disable retains both targets '||n,(select set_targets->0->>'rir'='0' and set_targets->0->>'rpe'='9.5' from public.training_plan_exercises where training_plan_day_id=did));
  perform pg_temp.training_assert('disable retains both scores '||n,(select rir=0 and rpe=9.5 from public.workout_set_logs where workout_session_id=sid));
  perform pg_temp.training_assert('snapshot unchanged '||n,(select metadata->'effortTracking'=flags from public.workout_sessions where id=sid));
  perform pg_temp.training_assert('other metadata preserved '||n,(select metadata ?& array['training_save_id','training_save_hash','effort_tracking'] from public.training_plans where id=pid));
  begin
   perform public.fmz_training_save_workout_v2(pid,did,'Stale','Maandag',0,rowdata,rev-interval '1 second',gen_random_uuid(),flags);
   raise exception 'expected stale';
  exception when serialization_failure then perform pg_temp.training_assert('stale edit rejected '||n,true); end;
  perform public.fmz_training_complete_workout(sid,now(),'{}');
 end loop;
 for flags in select value from jsonb_array_elements('[null,{},{"rir":false},{"rir":0,"rpe":false},{"rir":false,"rpe":false,"extra":true}]'::jsonb) loop
  begin
   perform public.fmz_training_save_workout_v2(gen_random_uuid(),gen_random_uuid(),'Invalid','Maandag',0,rowdata,null,gen_random_uuid(),flags);
   raise exception 'expected validation';
  exception when invalid_parameter_value then perform pg_temp.training_assert('invalid flags rejected '||flags::text,true); end;
 end loop;
 begin
  perform public.fmz_training_save_workout_v2(gen_random_uuid(),gen_random_uuid(),'Fifth','Maandag',0,
   jsonb_set(rowdata,'{0,id}',to_jsonb(gen_random_uuid())),null,gen_random_uuid(),'{"rir":false,"rpe":false}');
  raise exception 'expected limit';
 exception when check_violation then perform pg_temp.training_assert('Free four-day limit preserved',true); end;
end; $test$;
select set_config('request.jwt.claim.sub','660e1000-0000-4000-8000-000000000002',true);
do $test$
declare f record;
begin
 perform pg_temp.training_assert('cross-user plans hidden',not exists(select 1 from public.training_plans));
 perform pg_temp.training_assert('cross-user sessions hidden',not exists(select 1 from public.workout_sessions));
 select * into f from training_test_fixture limit 1;
 begin
  perform public.fmz_training_save_workout_v2(f.pid,f.did,'Other','Maandag',0,f.rows,f.revision,gen_random_uuid(),'{"rir":true,"rpe":true}');
  raise exception 'expected cross-user denial';
 exception when insufficient_privilege then perform pg_temp.training_assert('valid cross-user edit denied',true); end;
end; $test$;
reset role;
select pg_temp.training_assert('anon denied',not has_function_privilege('anon','public.fmz_training_save_workout_v2(uuid,uuid,text,text,integer,jsonb,timestamptz,uuid,jsonb)','execute'));
select pg_temp.training_assert('invoker RLS preserved',(select not prosecdef and proconfig=array['search_path=pg_catalog, pg_temp'] from pg_proc where oid='public.fmz_training_save_workout_v2(uuid,uuid,text,text,integer,jsonb,timestamptz,uuid,jsonb)'::regprocedure));
select jsonb_build_object('synthetic_only',true,'rolled_back',true,'checks',jsonb_agg(to_jsonb(r) order by label),'pass_count',count(*)) from training_test_results r;
rollback;
