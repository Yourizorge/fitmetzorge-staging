-- Owner-authorized Training upgrade. Staging mokxyyullfhkfalopbzd only.
-- Nullable additions: no backfill and no modification of existing member rows.
begin;
create function public.fmz_training_valid_set_targets(p_targets jsonb)
returns boolean language plpgsql immutable security invoker
set search_path=pg_catalog,pg_temp as $$
declare s jsonb;
begin
 if p_targets is null then return true; end if;
 if jsonb_typeof(p_targets)<>'array' or jsonb_array_length(p_targets) not between 1 and 20 then return false; end if;
 for s in select value from jsonb_array_elements(p_targets) loop
  if jsonb_typeof(s)<>'object' or not (s ?& array['reps','weight','rir','rpe'])
    or exists(select 1 from jsonb_object_keys(s) k where k not in ('reps','weight','rir','rpe'))
    or jsonb_typeof(s->'reps')<>'string' or length(s->>'reps') not between 1 and 32
    or (s->>'reps') !~ '^[1-9][0-9]{0,2}(-[1-9][0-9]{0,2})?$'
    or (position('-' in s->>'reps')>0 and split_part(s->>'reps','-',2)::integer<split_part(s->>'reps','-',1)::integer)
    or (s->'weight'<>'null'::jsonb and (jsonb_typeof(s->'weight')<>'number' or (s->>'weight')::numeric not between 0 and 10000))
    or (s->'rir'<>'null'::jsonb and (jsonb_typeof(s->'rir')<>'number' or (s->>'rir')::numeric not between 0 and 10 or (s->>'rir')::numeric<>trunc((s->>'rir')::numeric)))
    or (s->'rpe'<>'null'::jsonb and (jsonb_typeof(s->'rpe')<>'number' or (s->>'rpe')::numeric not between 1 and 10))
  then return false; end if;
 end loop;
 return true;
exception when others then return false;
end;
$$;
revoke all on function public.fmz_training_valid_set_targets(jsonb) from public,anon;
grant execute on function public.fmz_training_valid_set_targets(jsonb) to authenticated,service_role;

alter table public.training_plan_exercises
 add column set_targets jsonb constraint training_set_targets_valid check (public.fmz_training_valid_set_targets(set_targets)),
 add column superset_id uuid,
 add column superset_rest_seconds integer,
 add constraint training_superset_rest_valid check (
  (superset_id is null and superset_rest_seconds is null) or
  (superset_id is not null and superset_rest_seconds is not null and superset_rest_seconds between 0 and 3600));
alter table public.member_app_preferences
 add column training_effort_mode text constraint training_effort_mode_valid check(training_effort_mode in ('rir','rpe','none')),
 add column training_timer_enabled boolean;
comment on column public.training_plan_exercises.set_targets is
 'Optional per-set plan targets; NULL retains legacy exercise-level targets. Session snapshots remain independent.';
comment on column public.training_plan_exercises.superset_id is
 'Ordered group inside one plan day. New editor validates contiguity and consistent group rest atomically.';
comment on column public.member_app_preferences.training_effort_mode is
 'Display preference only. NULL displays RIR; does not translate or erase recorded effort scores.';

create function public.fmz_training_save_workout(
 p_plan_id uuid,p_day_id uuid,p_title text,p_day_label text,p_day_order integer,
 p_exercises jsonb,p_expected_updated_at timestamptz,p_save_id uuid)
returns jsonb language plpgsql security invoker
set search_path=pg_catalog,pg_temp as $$
declare
 u uuid:=auth.uid(); existing public.training_plans%rowtype; e jsonb; first_set jsonb;
 exercise_row public.training_plan_exercises%rowtype; catalog public.exercises%rowtype;
 ids uuid[]:=array[]::uuid[]; eid uuid; cid uuid; ord integer:=0; revision timestamptz;
 fingerprint text:=md5(jsonb_build_array(p_plan_id,p_day_id,p_title,p_day_label,p_day_order,p_exercises)::text);
begin
 if u is null or not exists(select 1 from public.profiles where id=u and role='client') then
  raise exception 'training_auth_required' using errcode='42501'; end if;
 if p_plan_id is null or p_day_id is null or p_save_id is null
  or p_title is null or length(btrim(p_title)) not between 1 and 120
  or p_day_label is null or length(btrim(p_day_label)) not between 1 and 60
  or p_day_order is null or p_day_order not between 0 and 6
  or jsonb_typeof(p_exercises) is distinct from 'array'
  or jsonb_array_length(p_exercises) not between 1 and 100 then
  raise exception 'training_input_invalid' using errcode='22023'; end if;
 -- Same lock as the existing Free active-day limit; RLS stays effective.
 perform pg_advisory_xact_lock(hashtextextended('fmz_phase3_training_day_limit:'||u::text,0));
 select * into existing from public.training_plans where id=p_plan_id and user_id=u for update;
 if found then
  if existing.metadata->>'training_save_id'=p_save_id::text then
   if existing.metadata->>'training_save_hash' is distinct from fingerprint then
    raise exception 'training_retry_payload_conflict' using errcode='22023'; end if;
   return jsonb_build_object('id',p_plan_id,'updated_at',existing.updated_at,'replayed',true);
  end if;
  if existing.updated_at is distinct from p_expected_updated_at then
   raise exception 'training_stale_conflict' using errcode='40001'; end if;
  if existing.source='legacy_bridge' or not exists(select 1 from public.training_plan_days where id=p_day_id and training_plan_id=p_plan_id) then
   raise exception 'training_day_forbidden' using errcode='42501'; end if;
 else
  if p_expected_updated_at is not null then raise exception 'training_plan_forbidden' using errcode='42501'; end if;
  insert into public.training_plans(id,user_id,title,status,source) values(p_plan_id,u,btrim(p_title),'active','phase3_client');
  insert into public.training_plan_days(id,training_plan_id,day_label,day_order) values(p_day_id,p_plan_id,btrim(p_day_label),p_day_order);
 end if;
 -- Reject duplicate IDs and broken groups before any exercise write.
 if exists(select 1 from jsonb_array_elements(p_exercises) x group by x->>'id' having count(*)>1)
  or exists(select 1 from jsonb_array_elements(p_exercises) with ordinality x(value,n)
    where value->>'superset_id' is not null
    group by value->>'superset_id'
    having count(*)<2 or max(n)-min(n)+1<>count(*)
      or count(distinct value->>'superset_rest_seconds')<>1) then
  raise exception 'training_group_invalid' using errcode='22023'; end if;
 for e in select value from jsonb_array_elements(p_exercises) loop
  if jsonb_typeof(e)<>'object' or e->>'id' is null
   or not(e ? 'set_targets') or e->'set_targets'='null'::jsonb
   or not public.fmz_training_valid_set_targets(e->'set_targets')
   or jsonb_typeof(e->'rest_seconds') is distinct from 'number'
   or (e->>'rest_seconds')::numeric not between 0 and 3600
   or (e->>'rest_seconds')::numeric<>trunc((e->>'rest_seconds')::numeric)
   or length(coalesce(e->>'notes',''))>2000 or length(coalesce(e->>'tempo',''))>80 then
   raise exception 'training_exercise_invalid' using errcode='22023'; end if;
  eid:=(e->>'id')::uuid; cid:=(e->>'exercise_id')::uuid;
  select * into exercise_row from public.training_plan_exercises where id=eid;
  if found and exercise_row.training_plan_day_id<>p_day_id then
   raise exception 'training_exercise_forbidden' using errcode='42501'; end if;
  if cid is not null then
   select * into catalog from public.exercises where id=cid and is_active;
   if not found or catalog.canonical_slug is distinct from e->>'exercise_slug' then
    raise exception 'training_catalog_invalid' using errcode='22023'; end if;
  elsif exercise_row.id is null or exercise_row.exercise_slug is distinct from e->>'exercise_slug' then
   raise exception 'training_catalog_required' using errcode='22023';
  end if;
  if exercise_row.id is not null and exercise_row.exercise_id is distinct from cid then
   raise exception 'training_replacement_requires_new_id' using errcode='22023'; end if;
  first_set:=e->'set_targets'->0;
  insert into public.training_plan_exercises(id,training_plan_day_id,exercise_id,exercise_slug,exercise_name_snapshot,
   exercise_order,status,archived_at,target_sets,target_reps,target_weight,target_rir,target_rpe,rest_seconds,notes,tempo,
   set_targets,superset_id,superset_rest_seconds)
  values(eid,p_day_id,cid,e->>'exercise_slug',case when cid is null then exercise_row.exercise_name_snapshot else catalog.name_en end,
   ord,'active',null,jsonb_array_length(e->'set_targets'),first_set->>'reps',(first_set->>'weight')::numeric,
   (first_set->>'rir')::integer,(first_set->>'rpe')::numeric,(e->>'rest_seconds')::integer,
   nullif(e->>'notes',''),nullif(e->>'tempo',''),e->'set_targets',(e->>'superset_id')::uuid,(e->>'superset_rest_seconds')::integer)
  on conflict(id) do update set exercise_order=excluded.exercise_order,status='active',archived_at=null,
   target_sets=excluded.target_sets,target_reps=excluded.target_reps,target_weight=excluded.target_weight,
   target_rir=excluded.target_rir,target_rpe=excluded.target_rpe,rest_seconds=excluded.rest_seconds,
   notes=excluded.notes,tempo=excluded.tempo,set_targets=excluded.set_targets,
   superset_id=excluded.superset_id,superset_rest_seconds=excluded.superset_rest_seconds;
  ids:=array_append(ids,eid); ord:=ord+1;
 end loop;
 update public.training_plan_exercises set status='archived'
  where training_plan_day_id=p_day_id and status='active' and not(id=any(ids));
 update public.training_plan_days set day_label=btrim(p_day_label),day_order=p_day_order
  where id=p_day_id and training_plan_id=p_plan_id;
 update public.training_plans set title=btrim(p_title),
  metadata=metadata||jsonb_build_object('training_save_id',p_save_id,'training_save_hash',fingerprint)
  where id=p_plan_id and user_id=u returning updated_at into revision;
 return jsonb_build_object('id',p_plan_id,'updated_at',revision,'replayed',false);
end;
$$;
revoke all on function public.fmz_training_save_workout(uuid,uuid,text,text,integer,jsonb,timestamptz,uuid) from public,anon;
grant execute on function public.fmz_training_save_workout(uuid,uuid,text,text,integer,jsonb,timestamptz,uuid) to authenticated;

-- Preferences use the existing private-write member preference table. Definer is
-- intentional: no direct table write grant is added. Exact auth.uid + shared lock.
create function public.fmz_training_get_preferences()
returns jsonb language plpgsql stable security definer set search_path=pg_catalog,pg_temp as $$
declare u uuid:=auth.uid(); p public.member_app_preferences%rowtype;
begin
 if u is null or not exists(select 1 from public.profiles where id=u and role='client') then
  raise exception 'training_auth_required' using errcode='42501'; end if;
 select * into p from public.member_app_preferences where user_id=u;
 return jsonb_build_object('effort_mode',coalesce(p.training_effort_mode,'rir'),
  'timer_enabled',coalesce(p.training_timer_enabled,true),'revision',coalesce(p.revision,0));
end;
$$;
create function public.fmz_training_set_preferences(p_effort_mode text,p_timer_enabled boolean,p_expected_revision bigint)
returns jsonb language plpgsql security definer set search_path=pg_catalog,pg_temp as $$
declare u uuid:=auth.uid(); r bigint;
begin
 if u is null or not exists(select 1 from public.profiles where id=u and role='client') then
  raise exception 'training_auth_required' using errcode='42501'; end if;
 if p_effort_mode is null or p_effort_mode not in ('rir','rpe','none') or p_timer_enabled is null or p_expected_revision is null then
  raise exception 'training_preferences_invalid' using errcode='22023'; end if;
 perform pg_advisory_xact_lock(hashtextextended('fmz_member_settings:'||u::text,0));
 select revision into r from public.member_app_preferences where user_id=u for update;
 if coalesce(r,0)<>p_expected_revision then raise exception 'training_preferences_stale' using errcode='40001'; end if;
 insert into public.member_app_preferences(user_id,training_effort_mode,training_timer_enabled)
  values(u,p_effort_mode,p_timer_enabled)
 on conflict(user_id) do update set training_effort_mode=excluded.training_effort_mode,
  training_timer_enabled=excluded.training_timer_enabled,revision=member_app_preferences.revision+1,updated_at=now();
 return public.fmz_training_get_preferences();
end;
$$;
revoke all on function public.fmz_training_get_preferences() from public,anon;
revoke all on function public.fmz_training_set_preferences(text,boolean,bigint) from public,anon;
grant execute on function public.fmz_training_get_preferences() to authenticated;
grant execute on function public.fmz_training_set_preferences(text,boolean,bigint) to authenticated;
create function public.fmz_training_complete_workout(p_session_id uuid,p_completed_at timestamptz,p_focus jsonb)
returns jsonb language plpgsql security invoker set search_path=pg_catalog,pg_temp as $$
declare s public.workout_sessions%rowtype;
begin
 if auth.uid() is null then raise exception 'training_auth_required' using errcode='42501'; end if;
 if p_completed_at is null or jsonb_typeof(p_focus) is distinct from 'object' or pg_column_size(p_focus)>32000 then
  raise exception 'training_completion_invalid' using errcode='22023'; end if;
 select * into s from public.workout_sessions where id=p_session_id and user_id=auth.uid() for update;
 if not found then raise exception 'training_session_forbidden' using errcode='42501'; end if;
 if s.status='completed' then return jsonb_build_object('completed_at',s.completed_at,'replayed',true); end if;
 if s.status not in ('active','paused') or p_completed_at<s.started_at then
  raise exception 'training_completion_invalid' using errcode='22023'; end if;
 update public.workout_sessions set status='completed',completed_at=p_completed_at,
  metadata=jsonb_set(metadata,'{focus}',p_focus) where id=s.id and user_id=auth.uid();
 return jsonb_build_object('completed_at',p_completed_at,'replayed',false);
end;
$$;
revoke all on function public.fmz_training_complete_workout(uuid,timestamptz,jsonb) from public,anon;
grant execute on function public.fmz_training_complete_workout(uuid,timestamptz,jsonb) to authenticated;
commit;
