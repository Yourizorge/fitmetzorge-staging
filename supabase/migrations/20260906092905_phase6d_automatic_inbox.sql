-- Owner hotfix 2. Staging only: mokxyyullfhkfalopbzd. No historical workout backfill.
begin;
alter table ai_private.phase6d_runtime_config add column inbox_worker_enabled boolean not null default false;

create table ai_private.analysis_jobs (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references public.profiles(id) on delete cascade,
 analysis_kind text not null check(analysis_kind in ('daily','weekly','post_workout')),
 event_key text not null,
 workout_id uuid references public.workout_sessions(id) on delete set null,
 status text not null default 'queued' check(status in ('queued','completed','cancelled')),
 result_id uuid references public.ai_analysis_results(id) on delete set null,
 attempts integer not null default 0,
 last_error_code text,
 available_at timestamptz not null default now(),
 created_at timestamptz not null default now(),
 finished_at timestamptz,
 unique(user_id,analysis_kind,event_key),
 check(last_error_code is null or last_error_code ~ '^[a-z0-9_]{1,80}$')
);
create index analysis_jobs_queue_idx on ai_private.analysis_jobs(available_at,created_at) where status='queued';
create index analysis_jobs_result_idx on ai_private.analysis_jobs(result_id) where result_id is not null;
create index analysis_jobs_workout_idx on ai_private.analysis_jobs(workout_id) where workout_id is not null;
alter table ai_private.analysis_jobs enable row level security;
revoke all on ai_private.analysis_jobs from public,anon,authenticated;

create table public.member_notifications (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references public.profiles(id) on delete cascade,
 analysis_id uuid not null references public.ai_analysis_results(id) on delete cascade,
 kind text not null default 'analysis_ready' check(kind='analysis_ready'),
 state text not null default 'new' check(state in ('new','later','opened','archived')),
 created_at timestamptz not null default now(),
 opened_at timestamptz,
 updated_at timestamptz not null default now(),
 unique(user_id,analysis_id)
);
create index member_notifications_inbox_idx on public.member_notifications(user_id,created_at desc,id desc) where state in ('new','later');
create index member_notifications_analysis_idx on public.member_notifications(analysis_id);
alter table public.member_notifications enable row level security;
create policy member_notifications_select_own on public.member_notifications for select to authenticated using((select auth.uid())=user_id);
revoke all on public.member_notifications from public,anon,authenticated;

create function ai_private.phase6d_enqueue_workout() returns trigger
language plpgsql security definer set search_path=pg_catalog,public,ai_private,pg_temp as $$
begin
 if new.status='completed' and new.completed_at is not null and
    (tg_op='INSERT' or old.status is distinct from 'completed') then
   insert into ai_private.analysis_jobs(user_id,analysis_kind,event_key,workout_id)
   values(new.user_id,'post_workout','post_workout:'||new.id::text,new.id)
   on conflict(user_id,analysis_kind,event_key) do nothing;
 end if;
 return new;
end;
$$;
revoke all on function ai_private.phase6d_enqueue_workout() from public,anon,authenticated;
create trigger phase6d_workout_analysis_job after insert or update of status on public.workout_sessions
 for each row execute function ai_private.phase6d_enqueue_workout();

create function ai_private.phase6d_notify_result() returns trigger
language plpgsql security definer set search_path=pg_catalog,public,ai_private,pg_temp as $$
begin
 if new.status in ('ready','partial','insufficient_data') and new.content_deleted_at is null then
   insert into public.member_notifications(user_id,analysis_id) values(new.user_id,new.id)
   on conflict(user_id,analysis_id) do nothing;
 elsif new.status='deleted' then
   update public.member_notifications set state='archived',updated_at=now() where analysis_id=new.id;
 end if;
 return new;
end;
$$;
revoke all on function ai_private.phase6d_notify_result() from public,anon,authenticated;
create trigger phase6d_result_notification after insert or update of status on public.ai_analysis_results
 for each row execute function ai_private.phase6d_notify_result();

create function public.fmz_phase6d_read_analysis(p_result_id uuid) returns jsonb
language plpgsql security definer set search_path=pg_catalog,public,ai_private,pg_temp as $$
declare v_user uuid:=auth.uid(); v_result public.ai_analysis_results%rowtype;
begin
 perform ai_private.assert_member(v_user);
 select * into v_result from public.ai_analysis_results where id=p_result_id and user_id=v_user;
 if not found then raise exception 'analysis_result_forbidden' using errcode='42501'; end if;
 if v_result.status='deleted' or v_result.content_deleted_at is not null or v_result.result_expires_at<=now() then
   raise exception 'analysis_result_unavailable' using errcode='22023';
 end if;
 return jsonb_build_object('schema_version','phase6d.detail.v1','result',
   to_jsonb(v_result)-array['user_id','request_id','context_manifest_id','run_id','event_key']);
end;
$$;
revoke all on function public.fmz_phase6d_read_analysis(uuid) from public,anon,authenticated;
grant execute on function public.fmz_phase6d_read_analysis(uuid) to authenticated;

create function public.fmz_phase6d_get_inbox() returns jsonb
language plpgsql security definer set search_path=pg_catalog,public,ai_private,pg_temp as $$
declare v_user uuid:=auth.uid();
begin
 perform ai_private.assert_member(v_user);
 return jsonb_build_object('items',coalesce((
  select jsonb_agg(to_jsonb(i) order by created_at desc,id desc) from (
   select n.id,n.analysis_id,n.state,n.created_at,r.analysis_kind,r.status,r.model_tier,r.completed_at
   from public.member_notifications n join public.ai_analysis_results r on r.id=n.analysis_id and r.user_id=n.user_id
   where n.user_id=v_user and n.state in ('new','later') and r.status in ('ready','partial','insufficient_data')
     and r.content_deleted_at is null and r.result_expires_at>now()
   order by n.created_at desc,n.id desc limit 5
  ) i),'[]'::jsonb),
  'unread_count',(select count(*) from public.member_notifications n join public.ai_analysis_results r
    on r.id=n.analysis_id and r.user_id=n.user_id where n.user_id=v_user and n.state in ('new','later')
    and r.content_deleted_at is null and r.result_expires_at>now()),
  'server_time',now());
end;
$$;
revoke all on function public.fmz_phase6d_get_inbox() from public,anon,authenticated;
grant execute on function public.fmz_phase6d_get_inbox() to authenticated;

create function public.fmz_phase6d_mark_notification(p_analysis_id uuid,p_action text) returns jsonb
language plpgsql security definer set search_path=pg_catalog,public,ai_private,pg_temp as $$
declare v_user uuid:=auth.uid(); v_note public.member_notifications%rowtype;
begin
 perform ai_private.assert_member(v_user);
 if p_action is null or p_action not in ('later','opened','archived') then
  raise exception 'notification_action_invalid' using errcode='22023';
 end if;
 perform public.fmz_phase6d_read_analysis(p_analysis_id);
 select * into v_note from public.member_notifications where user_id=v_user and analysis_id=p_analysis_id for update;
 if found then
  update public.member_notifications set
   state=case when state='archived' then state when p_action='later' and state='opened' then state else p_action end,
   opened_at=case when p_action='opened' then coalesce(opened_at,now()) else opened_at end,updated_at=now()
  where id=v_note.id returning * into v_note;
 end if;
 return jsonb_build_object('analysis_id',p_analysis_id,'state',v_note.state);
end;
$$;
revoke all on function public.fmz_phase6d_mark_notification(uuid,text) from public,anon,authenticated;
grant execute on function public.fmz_phase6d_mark_notification(uuid,text) to authenticated;

create function public.fmz_phase6d_sync_device_timezone(p_timezone_name text) returns jsonb
language plpgsql security definer set search_path=pg_catalog,public,ai_private,pg_temp as $$
declare v_user uuid:=auth.uid();
begin
 perform ai_private.assert_member(v_user);
 if p_timezone_name is null or not exists(select 1 from pg_timezone_names where name=p_timezone_name) then
  raise exception 'analysis_timezone_invalid' using errcode='22023';
 end if;
 perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_preferences:'||v_user::text,0));
 insert into public.ai_analysis_preferences(user_id,timezone_name) values(v_user,p_timezone_name)
 on conflict(user_id) do update set timezone_name=excluded.timezone_name,
  revision=ai_analysis_preferences.revision+1,last_request_id=null
 where ai_analysis_preferences.timezone_name is distinct from excluded.timezone_name;
 return ai_private.phase6d_current_preferences(v_user);
end;
$$;
revoke all on function public.fmz_phase6d_sync_device_timezone(text) from public,anon,authenticated;
grant execute on function public.fmz_phase6d_sync_device_timezone(text) to authenticated;

create function ai_private.phase6d_workout_comparison(p_user uuid,p_workout uuid) returns jsonb
language plpgsql stable security definer set search_path=pg_catalog,public,ai_private,pg_temp as $$
declare
 c public.workout_sessions%rowtype; p public.workout_sessions%rowtype;
 keys text[]; rows jsonb; match_code text;
begin
 select * into c from public.workout_sessions where id=p_workout and user_id=p_user and status='completed' and completed_at is not null;
 if not found then return jsonb_build_object('available',false,'reason','completed_workout_unavailable'); end if;
 select array_agg(distinct coalesce('id:'||exercise_id::text,'slug:'||exercise_slug) order by coalesce('id:'||exercise_id::text,'slug:'||exercise_slug))
 into keys from public.workout_set_logs where user_id=p_user and workout_session_id=c.id;
 select w.* into p from public.workout_sessions w
 where w.user_id=p_user and w.status='completed' and w.completed_at<c.completed_at
 and ((c.training_plan_day_id is not null and w.training_plan_day_id=c.training_plan_day_id)
  or (c.training_plan_day_id is null and cardinality(keys)>0 and
   (select array_agg(distinct coalesce('id:'||s.exercise_id::text,'slug:'||s.exercise_slug) order by coalesce('id:'||s.exercise_id::text,'slug:'||s.exercise_slug))
    from public.workout_set_logs s where s.user_id=p_user and s.workout_session_id=w.id)=keys))
 order by w.completed_at desc,w.id desc limit 1;
 match_code:=case when p.id is null then 'first_suitable_workout' when c.training_plan_day_id is not null then 'same_program_day' else 'same_exercise_set' end;
 with metrics as (
  select workout_session_id,coalesce('id:'||exercise_id::text,'slug:'||exercise_slug) as key,min(exercise_slug) as label,
   count(*) as sets,case when count(actual_reps)=count(*) then sum(actual_reps) else null end as reps,max(actual_weight) as max_weight_kg,
   case when count(actual_weight*actual_reps)=count(*) then sum(actual_weight*actual_reps) else null end as volume_kg,
   round(avg(rpe),1) as rpe,round(avg(rir),1) as rir,
   count(actual_reps) as reps_observations,count(actual_weight) as weight_observations
  from public.workout_set_logs where user_id=p_user and workout_session_id in (c.id,p.id)
  group by workout_session_id,coalesce('id:'||exercise_id::text,'slug:'||exercise_slug)
 ), paired as (
  select coalesce(a.key,b.key) as key,coalesce(a.label,b.label) as label,
   to_jsonb(a)-array['key','label','workout_session_id'] as current,
   to_jsonb(b)-array['key','label','workout_session_id'] as previous,
   case when a.volume_kg is null or b.volume_kg is null then null
    when a.volume_kg>b.volume_kg then 'higher' when a.volume_kg<b.volume_kg then 'lower' else 'equal' end as volume_change
  from (select * from metrics where workout_session_id=c.id) a
  full join (select * from metrics where workout_session_id=p.id) b on b.key=a.key
  order by coalesce(a.key,b.key) limit 20
 )
 select coalesce(jsonb_agg(to_jsonb(paired)),'[]'::jsonb) into rows from paired;
 return jsonb_build_object('available',p.id is not null,'reason',match_code,
  'current',jsonb_build_object('id',c.id,'completed_at',c.completed_at,'elapsed_seconds',greatest(0,extract(epoch from c.completed_at-c.started_at))::bigint),
  'previous',case when p.id is not null then jsonb_build_object('id',p.id,'completed_at',p.completed_at,'elapsed_seconds',greatest(0,extract(epoch from p.completed_at-p.started_at))::bigint) else null end,
  'exercises',rows,'duration_kind','elapsed_including_pauses','active_duration_available',false,
  'interpretation','observed_performance_not_fatigue_diagnosis','exercise_limit',20);
end;
$$;
revoke all on function ai_private.phase6d_workout_comparison(uuid,uuid) from public,anon,authenticated;

create function ai_private.phase6d_mock_result(p_context jsonb,p_locale text,p_comparison jsonb default null) returns jsonb
language plpgsql immutable set search_path=pg_catalog,ai_private,pg_temp as $$
declare lang text:=case when p_locale in ('nl','en','de') then p_locale else 'nl' end;
 summary text; reflection text; observations jsonb:='[]'; kind text:=p_context->>'analysis_kind';
begin
 summary:=case lang when 'en' then 'Your analysis is ready from the saved observations. This is a deterministic staging test.'
  when 'de' then 'Deine Analyse der gespeicherten Beobachtungen ist bereit. Dies ist ein deterministischer Staging-Test.'
  else 'Je analyse van de opgeslagen meetpunten staat klaar. Dit is een deterministische stagingtest.' end;
 reflection:=case lang when 'en' then 'Compare only like-for-like observations. Lower performance alone does not establish fatigue. No plan has been changed.'
  when 'de' then 'Vergleiche nur gleichartige Beobachtungen. Geringere Leistung allein belegt keine Ermuedung. Kein Plan wurde geaendert.'
  else 'Vergelijk alleen gelijksoortige meetpunten. Lagere prestaties bewijzen op zichzelf geen vermoeidheid. Er is geen schema gewijzigd.' end;
 if kind='post_workout' then
  observations:=jsonb_build_array(jsonb_build_object('source','training','evidence',jsonb_build_array('completed_workout_pair'),
   'text',case when (p_comparison->>'available')::boolean then
    case lang when 'en' then 'The previous relevant completed workout is shown below with the measured differences.'
     when 'de' then 'Das vorige passende abgeschlossene Training und die gemessenen Unterschiede stehen unten.'
     else 'Hieronder staat de vorige relevante voltooide training met de gemeten verschillen.' end
    else case lang when 'en' then 'This is the first suitable comparison. No previous performance has been invented.'
     when 'de' then 'Dies ist der erste passende Vergleich. Es wurden keine frueheren Leistungen erfunden.'
     else 'Dit is de eerste geschikte vergelijking. Er zijn geen eerdere prestaties ingevuld.' end end));
 else
  select coalesce(jsonb_agg(jsonb_build_object('source',key,'evidence',jsonb_build_array('aggregate_'||key),
    'metrics',value)),'[]') into observations from jsonb_each(p_context->'sources');
 end if;
 return jsonb_build_object('schema_version','phase6d.analysis.v1','analysis_kind',kind,
  'feature_code',ai_private.phase6d_feature_code(kind),
  'status',case when p_context->'quality'->>'level'='partial' then 'partial' else 'ready' end,
  'summary',summary,'observations',observations,'uncertainties',coalesce(p_context->'quality'->'missing_sources','[]'),
  'suggestions',jsonb_build_array(jsonb_build_object('kind','read_only_reflection','text',reflection)),
  'actions','[]'::jsonb,'safety',jsonb_build_object('status','clear','category','none','message_key','safety.clear','automatic_execution_blocked',true),
  'data_quality',p_context->'quality','period',p_context->'period','privacy',p_context->'privacy',
  'comparison',p_comparison,'mock',true);
end;
$$;
revoke all on function ai_private.phase6d_mock_result(jsonb,text,jsonb) from public,anon,authenticated;


create or replace function ai_private.phase6d_prepare_member_analysis(
  p_user_id uuid,
  p_request_id uuid,
  p_analysis_kind text,
  p_locale text default 'nl',
  p_event_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := p_user_id;
  v_locale text := case when p_locale in ('nl','en','de') then p_locale else 'nl' end;
  v_status jsonb;
  v_context jsonb;
  v_existing public.ai_analysis_results%rowtype;
  v_result public.ai_analysis_results%rowtype;
  v_feature text;
  v_model text;
  v_event_key text;
  v_quality jsonb;
  v_missing text[];
  v_local_payload jsonb;
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  if p_request_id is null or p_analysis_kind not in ('daily','post_workout','weekly') then
    raise exception 'analysis_request_invalid' using errcode = '22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_preferences:' || v_user_id::text,0));
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_period:' || v_user_id::text || ':' || p_analysis_kind,0));
  if p_analysis_kind='post_workout' and not exists(select 1 from public.workout_sessions where user_id=v_user_id and status='completed' and completed_at is not null and (p_event_id is null or id=p_event_id)) then
    raise exception 'analysis_completed_workout_required' using errcode='22023';
  end if;
  v_feature := ai_private.phase6d_feature_code(p_analysis_kind);
  v_model := ai_private.phase6d_model_tier(p_analysis_kind);
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_request:' || v_user_id::text || ':' || p_request_id::text, 0));
  select * into v_existing from public.ai_analysis_results r where r.user_id = v_user_id and r.request_id = p_request_id;
  if v_existing.id is not null then
    return jsonb_build_object('replay', true, 'status', v_existing.status, 'result', jsonb_build_object(
      'id', v_existing.id,
      'analysis_kind', v_existing.analysis_kind,
      'status', v_existing.status,
      'summary', v_existing.summary_text,
      'result_payload', v_existing.result_payload,
      'revision', v_existing.revision
    ));
  end if;
  v_status := ai_private.phase6d_analysis_status(v_user_id, p_analysis_kind, now());
  if not coalesce((v_status ->> 'analysis_allowed')::boolean, false) then
    raise exception '%', v_status ->> 'deny_reason' using errcode = '42501';
  end if;
  v_context := ai_private.phase6d_build_context(v_user_id, p_analysis_kind, p_event_id, now());
  v_event_key := v_context ->> 'event_key';
  v_quality := v_context -> 'quality';
  v_missing := coalesce(array(select jsonb_array_elements_text(v_context -> 'unavailable_sources')), '{}');
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_event:' || v_user_id::text || ':' || p_analysis_kind || ':' || v_event_key, 0));
  select * into v_existing
  from public.ai_analysis_results r
  where r.id = ai_private.phase6d_period_result(v_user_id,p_analysis_kind,v_event_key,
    (now() at time zone (ai_private.phase6d_current_preferences(v_user_id)->>'timezone_name'))::date,
    ai_private.phase6d_current_preferences(v_user_id)->>'timezone_name');
  if v_existing.id is not null then
    return jsonb_build_object('replay', true, 'status', v_existing.status, 'result', jsonb_build_object(
      'id', v_existing.id,
      'analysis_kind', v_existing.analysis_kind,
      'status', v_existing.status,
      'summary', v_existing.summary_text,
      'result_payload', v_existing.result_payload,
      'revision', v_existing.revision
    ));
  end if;
  if not coalesce((v_quality ->> 'reliable')::boolean, false) then
    v_local_payload := jsonb_build_object(
      'schema_version', 'phase6d.analysis.v1',
      'analysis_kind', p_analysis_kind,
      'feature_code', v_feature,
      'status', 'partial',
      'summary', case v_locale when 'en' then 'There is not enough reliable data for an analysis yet.' when 'de' then 'Es gibt noch nicht genug verlaessliche Daten fuer eine Analyse.' else 'Er is nog niet genoeg betrouwbare data voor een analyse.' end,
      'observations', '[]'::jsonb,
      'uncertainties', jsonb_build_array('insufficient_reliable_data'),
      'suggestions', jsonb_build_array(jsonb_build_object('kind','data_quality','text',case v_locale when 'en' then 'New observations will be included in a future analysis.' when 'de' then 'Neue Beobachtungen werden in einer spaeteren Analyse beruecksichtigt.' else 'Nieuwe meetpunten worden meegenomen in een volgende analyse.' end)),
      'actions', '[]'::jsonb,
      'safety', jsonb_build_object('status','clear','category','none','message_key','safety.clear','automatic_execution_blocked',true),
      'data_quality', v_quality,
      'period', v_context -> 'period',
      'privacy', v_context -> 'privacy'
    );
    insert into public.ai_analysis_results(
      id, user_id, analysis_kind, feature_code, event_key, request_id, status, locale,
      schema_version, source_cutoff_at, period_start_local, period_end_local, timezone_name,
      quality, unavailable_sources, result_payload, summary_text, completed_at
    ) values (
      gen_random_uuid(), v_user_id, p_analysis_kind, v_feature, v_event_key, p_request_id,
      'insufficient_data', v_locale, 'phase6d.analysis.v1', (v_context ->> 'source_cutoff_at')::timestamptz,
      (v_context -> 'period' ->> 'start_local')::date, (v_context -> 'period' ->> 'end_local')::date,
      v_context -> 'period' ->> 'timezone_name', v_quality, v_missing, v_local_payload,
      v_local_payload ->> 'summary', now()
    ) returning * into v_result;
    return jsonb_build_object('replay', false, 'status', 'insufficient_data', 'result', jsonb_build_object(
      'id', v_result.id,
      'analysis_kind', v_result.analysis_kind,
      'status', v_result.status,
      'summary', v_result.summary_text,
      'result_payload', v_result.result_payload,
      'revision', v_result.revision
    ));
  end if;
  insert into public.ai_analysis_results(
    id, user_id, analysis_kind, feature_code, event_key, request_id, status, locale,
    schema_version, source_cutoff_at, period_start_local, period_end_local, timezone_name,
    quality, unavailable_sources
  ) values (
    gen_random_uuid(), v_user_id, p_analysis_kind, v_feature, v_event_key, p_request_id, 'pending',
    v_locale, 'phase6d.analysis.v1', (v_context ->> 'source_cutoff_at')::timestamptz,
    (v_context -> 'period' ->> 'start_local')::date, (v_context -> 'period' ->> 'end_local')::date,
    v_context -> 'period' ->> 'timezone_name', v_quality, v_missing
  ) returning * into v_result;
  return jsonb_build_object(
    'replay', false,
    'status', 'prepared',
    'result_id', v_result.id,
    'analysis_kind', p_analysis_kind,
    'feature_code', v_feature,
    'model_tier', v_model,
    'context', v_context,
    'external_ai_calls', 0,
    'external_ai_cost_eur', 0
  );
end;
$$;

create or replace function public.fmz_phase6d_service_complete_analysis(
  p_run_id uuid,
  p_result_id uuid,
  p_structured_output jsonb,
  p_actual_cost_micros bigint,
  p_input_tokens integer,
  p_output_tokens integer
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_run ai_private.runs%rowtype;
  v_result public.ai_analysis_results%rowtype;
  v_entitlement record;
  v_period record;
  v_account ai_private.budget_accounts%rowtype;
  v_budget jsonb;
  v_response_hash text;
begin
  if p_run_id is null or p_result_id is null
     or p_actual_cost_micros not between 0 and 4000000
     or p_input_tokens not between 0 and 1000000
     or p_output_tokens not between 0 and 1000000
     or not ai_private.phase6d_validate_analysis_output(p_structured_output) then
    raise exception 'analysis_structured_output_invalid' using errcode = '22023';
  end if;
  v_response_hash := encode(extensions.digest(convert_to(p_structured_output::text, 'UTF8'), 'sha256'), 'hex');
  select * into v_run from ai_private.runs r where r.id = p_run_id for update;
  if v_run.id is null then raise exception 'ai_run_not_found' using errcode = '22023'; end if;
  if v_run.schema_version <> 'phase6d.analysis.v1'
     or v_run.feature_code <> p_structured_output ->> 'feature_code'
     or (p_structured_output ->> 'analysis_kind') <> (case v_run.feature_code when 'daily_analysis' then 'daily' when 'post_workout' then 'post_workout' else 'weekly' end) then
    raise exception 'analysis_structured_output_conflict' using errcode = '23505';
  end if;
  select * into v_result from public.ai_analysis_results r where r.id = p_result_id and r.user_id = v_run.user_id for update;
  if v_result.id is null or v_result.run_id is distinct from p_run_id or v_result.request_id <> v_run.request_id then
    raise exception 'analysis_result_forbidden' using errcode = '42501';
  end if;
  if v_run.status = 'completed' then
    if v_run.response_hash <> v_response_hash then raise exception 'analysis_completion_conflict' using errcode = '23505'; end if;
    return jsonb_build_object('replay', true, 'run_id', v_run.id, 'result_id', v_result.id, 'status', v_result.status);
  elsif v_run.status <> 'reserved' then
    raise exception 'ai_run_not_completable' using errcode = '40001';
  end if;
  if v_run.adapter_code = 'mock' and p_actual_cost_micros <> 0 then
    raise exception 'ai_mock_cost_forbidden' using errcode = '22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_safety:'||v_run.user_id::text,0));
  if not coalesce((ai_private.phase6d_analysis_status(v_run.user_id,v_result.analysis_kind,now())->>'analysis_allowed')::boolean,false) then
    raise exception 'analysis_delivery_gate_blocked' using errcode='42501';
  end if;
  select * into v_entitlement from ai_private.current_entitlement(v_run.user_id, v_run.started_at);
  select * into v_period from ai_private.subscription_period(v_entitlement.entitlement_started_at, v_run.started_at);
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_budget:' || v_run.user_id::text || ':' || v_period.period_start::text, 0));
  select * into v_account from ai_private.budget_accounts a
  where a.user_id = v_run.user_id and a.period_start = v_period.period_start for update;
  v_budget := ai_private.evaluate_budget(v_account.consumed_micros, greatest(0, v_account.reserved_micros - v_run.reserved_cost_micros), p_actual_cost_micros, v_run.model_tier);
  if not (v_budget ->> 'allowed')::boolean then
    raise exception '%', v_budget ->> 'reason' using errcode = '42501';
  end if;
  update ai_private.budget_accounts
  set reserved_micros = greatest(0, reserved_micros - v_run.reserved_cost_micros),
      consumed_micros = consumed_micros + p_actual_cost_micros,
      hard_stopped_at = case when consumed_micros + p_actual_cost_micros >= 4000000 then coalesce(hard_stopped_at, now()) else hard_stopped_at end,
      updated_at = now()
  where user_id = v_run.user_id and period_start = v_period.period_start;
  insert into ai_private.usage_ledger(id, user_id, run_id, request_id, feature_code, model_tier, ledger_type, amount_micros)
  values (gen_random_uuid(), v_run.user_id, v_run.id, v_run.request_id, v_run.feature_code, v_run.model_tier, 'actual', p_actual_cost_micros);
  update ai_private.runs
  set status = 'completed',
      actual_cost_micros = p_actual_cost_micros,
      input_tokens = p_input_tokens,
      output_tokens = p_output_tokens,
      response_hash = v_response_hash,
      completed_at = now()
  where id = v_run.id;
  update public.ai_analysis_results
  set status = p_structured_output ->> 'status',
      result_payload = p_structured_output,
      summary_text = p_structured_output ->> 'summary',
      quality = coalesce(p_structured_output -> 'data_quality', quality),
      completed_at = now(),
      result_expires_at = now() + interval '90 days',
      metadata_expires_at = now() + interval '180 days',
      revision = revision + 1
  where id = v_result.id;
  if p_structured_output -> 'safety' ->> 'status' in ('hard_stop','review_required') then
    perform public.fmz_phase6a_service_record_safety_event(
      v_run.user_id,
      v_run.id,
      coalesce(p_structured_output -> 'safety' ->> 'category', 'serious_health'),
      p_structured_output -> 'safety' ->> 'status',
      v_run.policy_version
    );
  end if;
  insert into ai_private.audit_events(id, user_id, run_id, event_code, safe_metadata)
  values (gen_random_uuid(), v_run.user_id, v_run.id, 'analysis_run_completed', jsonb_build_object('feature_code', v_run.feature_code, 'safety_status', p_structured_output -> 'safety' ->> 'status'));
  return jsonb_build_object('replay', false, 'run_id', v_run.id, 'result_id', v_result.id, 'status', p_structured_output ->> 'status', 'fair_use_status', v_budget ->> 'fair_use_status');
end;
$$;

revoke all on function ai_private.phase6d_prepare_member_analysis(uuid,uuid,text,text,uuid) from public,anon,authenticated;

create or replace function public.fmz_phase6d_prepare_analysis(p_request_id uuid,p_analysis_kind text,p_locale text default 'nl',p_event_id uuid default null)
returns jsonb language sql security definer set search_path=pg_catalog,public,ai_private,pg_temp as $$
 select ai_private.phase6d_prepare_member_analysis(auth.uid(),p_request_id,p_analysis_kind,p_locale,p_event_id);
$$;
revoke all on function public.fmz_phase6d_prepare_analysis(uuid,text,text,uuid) from public,anon,authenticated;
grant execute on function public.fmz_phase6d_prepare_analysis(uuid,text,text,uuid) to authenticated;

create function ai_private.phase6d_run_inbox_worker(p_limit integer default 10)
returns jsonb language plpgsql security definer set search_path=pg_catalog,extensions,public,ai_private,pg_temp as $$
declare
 j ai_private.analysis_jobs%rowtype; candidate jsonb; prepared jsonb; context jsonb; output jsonb; comparison jsonb;
 result public.ai_analysis_results%rowtype; gate jsonb; pref jsonb; started jsonb; lang text; current_key text;
 total integer:=0; failures integer:=0; existing_id uuid;
begin
 if not exists(select 1 from ai_private.phase6d_runtime_config where singleton and inbox_worker_enabled
  and scheduled_generation_enabled and mock_analyses_enabled and not external_provider_enabled) then
  return jsonb_build_object('disabled',true,'processed',0);
 end if;
 if not pg_try_advisory_xact_lock(hashtextextended('fmz_phase6d_inbox_worker',0)) then
  return jsonb_build_object('busy',true,'processed',0);
 end if;
 for candidate in select value from jsonb_array_elements(ai_private.phase6d_select_due_analyses(now(),200)->'candidates') loop
  if candidate->>'analysis_kind' in ('daily','weekly') then
   insert into ai_private.analysis_jobs(user_id,analysis_kind,event_key)
   values((candidate->>'user_id')::uuid,candidate->>'analysis_kind',candidate->>'event_key')
   on conflict(user_id,analysis_kind,event_key) do nothing;
  end if;
 end loop;
 for j in select * from ai_private.analysis_jobs where status='queued' and available_at<=now()
  order by available_at,created_at limit least(greatest(coalesce(p_limit,10),1),50) for update skip locked loop
  begin
   perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_preferences:'||j.user_id::text,0));
   perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_safety:'||j.user_id::text,0));
   pref:=ai_private.phase6d_current_preferences(j.user_id);
   current_key:=case j.analysis_kind when 'daily' then 'daily:'||(now() at time zone (pref->>'timezone_name'))::date::text
    when 'weekly' then 'weekly:'||to_char(now() at time zone (pref->>'timezone_name'),'IYYY-IW') else 'post_workout:'||j.workout_id::text end;
   if current_key is null or current_key<>j.event_key then
    update ai_private.analysis_jobs set status='cancelled',last_error_code='period_elapsed',finished_at=now() where id=j.id;
    continue;
   end if;
   gate:=ai_private.phase6d_analysis_status(j.user_id,j.analysis_kind,now());
   if not coalesce((gate->>'analysis_allowed')::boolean,false) then
    update ai_private.analysis_jobs set available_at=now()+interval '5 minutes',last_error_code=gate->>'deny_reason' where id=j.id;
    continue;
   end if;
   -- Recheck saved clock time too: changing the schedule cannot run an old queued time.
   if j.analysis_kind in ('daily','weekly') and (
     (j.analysis_kind='daily' and (now() at time zone (pref->>'timezone_name'))::time<(pref->>'daily_time')::time)
     or (j.analysis_kind='weekly' and (extract(isodow from now() at time zone (pref->>'timezone_name'))::int<>(pref->>'weekly_day')::int
       or (now() at time zone (pref->>'timezone_name'))::time<(pref->>'weekly_time')::time))) then
    update ai_private.analysis_jobs set available_at=now()+interval '1 minute' where id=j.id;
    continue;
   end if;
   select coalesce(s.language,'nl') into lang from public.profiles p left join public.user_settings s on s.user_id=p.id where p.id=j.user_id;
   prepared:=ai_private.phase6d_prepare_member_analysis(j.user_id,j.id,j.analysis_kind,lang,j.workout_id);
   existing_id:=coalesce((prepared->>'result_id')::uuid,(prepared->'result'->>'id')::uuid);
   select * into result from public.ai_analysis_results where id=existing_id and user_id=j.user_id for update;
   if result.id is null then raise exception 'analysis_result_missing'; end if;
   if result.status='pending' then
    context:=prepared->'context';
    if context is null and result.context_manifest_id is not null then
      select sources into context from public.ai_context_manifests where id=result.context_manifest_id and user_id=j.user_id;
    end if;
    context:=coalesce(context,ai_private.phase6d_build_context(j.user_id,j.analysis_kind,j.workout_id,now()));
    if result.run_id is null then
     started:=public.fmz_phase6d_service_begin_analysis(j.user_id,result.id,result.request_id,j.analysis_kind,
      encode(extensions.digest(convert_to(context::text,'UTF8'),'sha256'),'hex'),context,
      coalesce(array(select jsonb_array_elements_text(context->'unavailable_sources')),'{}'));
    else started:=jsonb_build_object('run_id',result.run_id); end if;
    comparison:=case when j.analysis_kind='post_workout' then ai_private.phase6d_workout_comparison(j.user_id,j.workout_id) else null end;
    output:=ai_private.phase6d_mock_result(context,lang,comparison);
    perform public.fmz_phase6d_service_complete_analysis((started->>'run_id')::uuid,result.id,output,0,0,0);
   elsif result.status='insufficient_data' then
    update public.ai_analysis_results set model_tier=ai_private.phase6d_model_tier(j.analysis_kind),adapter_code='mock',result_payload=result_payload||jsonb_build_object('mock',true) where id=result.id;
   end if;
   update ai_private.analysis_jobs set status='completed',result_id=result.id,finished_at=now(),last_error_code=null,attempts=attempts+1 where id=j.id;
   total:=total+1;
  exception when others then
   -- Per-job savepoint rolls back all partial result/budget writes; never log context.
   update ai_private.analysis_jobs set attempts=attempts+1,available_at=now()+interval '5 minutes',
    last_error_code='worker_'||lower(sqlstate) where id=j.id;
   failures:=failures+1;
  end;
 end loop;
 delete from ai_private.analysis_jobs where created_at<now()-interval '180 days';
 return jsonb_build_object('disabled',false,'processed',total,'retry_count',failures,'external_calls',0,'cost_eur',0);
end;
$$;
revoke all on function ai_private.phase6d_run_inbox_worker(integer) from public,anon,authenticated;

select cron.schedule('fmz-phase6d-inbox-mock-worker','* * * * *','select ai_private.phase6d_run_inbox_worker(10)');
create or replace function public.fmz_phase6c_list_threads(
  p_limit integer default 20,
  p_before_updated_at timestamptz default null,
  p_before_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
begin
  perform ai_private.phase6c_reconcile_member(v_user_id, now());
  if p_limit not between 1 and 25 or ((p_before_updated_at is null) <> (p_before_id is null)) then
    raise exception 'ai_thread_page_invalid' using errcode = '22023';
  end if;
  return jsonb_build_object('threads', coalesce((
    select jsonb_agg(to_jsonb(x) order by x.updated_at desc, x.id desc)
    from (
      select t.id, t.locale, t.status, t.retention_state, t.retention_due_at,
        t.revision, t.last_message_sequence, t.created_at, t.updated_at,
        (select left(m.content_text,80) from public.ai_messages m where m.thread_id=t.id and m.user_id=v_user_id and m.status='active' and m.message_role='user' order by m.sequence_number limit 1) as title,
        (select left(m.content_text,160) from public.ai_messages m where m.thread_id=t.id and m.status='active' order by m.sequence_number desc limit 1) as last_message,
        (select r.status from ai_private.runs r where r.thread_id=t.id order by r.started_at desc, r.id desc limit 1) as processing_status
      from public.ai_threads t
      where t.user_id = v_user_id and t.feature_code = 'private_chat'
        and t.retention_state <> 'deleted'
        and (p_before_updated_at is null or (t.updated_at, t.id) < (p_before_updated_at, p_before_id))
      order by t.updated_at desc, t.id desc
      limit p_limit
    ) x
  ), '[]'::jsonb));
end;
$$;
notify pgrst,'reload schema';
commit;
