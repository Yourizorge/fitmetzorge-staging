-- Additive staging-only API. Existing functions, rows, policies and snapshots are untouched.
begin;
create function public.fmz_training_save_workout_v2(
 p_plan_id uuid,p_day_id uuid,p_title text,p_day_label text,p_day_order integer,
 p_exercises jsonb,p_expected_updated_at timestamptz,p_save_id uuid,p_effort_tracking jsonb)
returns jsonb language plpgsql security invoker
set search_path=pg_catalog,pg_temp as $$
declare u uuid:=auth.uid(); existing public.training_plans%rowtype; result jsonb; revision timestamptz;
begin
 if u is null then raise exception 'training_auth_required' using errcode='42501'; end if;
 if jsonb_typeof(p_effort_tracking) is distinct from 'object'
  or jsonb_typeof(p_effort_tracking->'rir') is distinct from 'boolean'
  or jsonb_typeof(p_effort_tracking->'rpe') is distinct from 'boolean'
  or exists(select 1 from jsonb_object_keys(p_effort_tracking) k where k not in ('rir','rpe')) then
  raise exception 'training_effort_invalid' using errcode='22023';
 end if;
 -- Share the original free-day/atomic-save lock, without bypassing RLS or limits.
 perform pg_advisory_xact_lock(hashtextextended('fmz_phase3_training_day_limit:'||u::text,0));
 select * into existing from public.training_plans where id=p_plan_id and user_id=u for update;
 if found and existing.metadata->>'training_save_id'=p_save_id::text
   and existing.metadata->'effort_tracking' is distinct from p_effort_tracking then
  raise exception 'training_retry_payload_conflict' using errcode='22023';
 end if;
 result:=public.fmz_training_save_workout(p_plan_id,p_day_id,p_title,p_day_label,p_day_order,
  p_exercises,p_expected_updated_at,p_save_id);
 if (result->>'replayed')::boolean then return result; end if;
 update public.training_plans
 set metadata=metadata||jsonb_build_object('effort_tracking',p_effort_tracking)
 where id=p_plan_id and user_id=u returning updated_at into revision;
 if not found then raise exception 'training_plan_forbidden' using errcode='42501'; end if;
 return jsonb_build_object('id',p_plan_id,'updated_at',revision,'replayed',false);
end;
$$;
revoke all on function public.fmz_training_save_workout_v2(uuid,uuid,text,text,integer,jsonb,timestamptz,uuid,jsonb) from public,anon;
grant execute on function public.fmz_training_save_workout_v2(uuid,uuid,text,text,integer,jsonb,timestamptz,uuid,jsonb) to authenticated;
comment on function public.fmz_training_save_workout_v2(uuid,uuid,text,text,integer,jsonb,timestamptz,uuid,jsonb) is
 'Own-user atomic plan save plus independent RIR/RPE flags in existing plan metadata. No score conversion, deletion or snapshot update.';
commit;

