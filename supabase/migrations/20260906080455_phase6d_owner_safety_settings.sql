-- Package 6D combined owner hotfix. Staging: mokxyyullfhkfalopbzd.
-- No member backfill; recovery does not modify historical/action safety state.
begin;

create table public.member_app_preferences (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  date_format text not null default 'locale' check (date_format in ('locale','iso','day_first')),
  hour_cycle text not null default '24' check (hour_cycle in ('12','24')),
  avatar_visible boolean not null default true,
  avatar_side text not null default 'right' check (avatar_side in ('left','right')),
  avatar_y numeric not null default 0.72 check (avatar_y between 0 and 1),
  revision bigint not null default 1,
  updated_at timestamptz not null default now()
);
alter table public.member_app_preferences enable row level security;
create policy member_app_preferences_select_own on public.member_app_preferences
  for select to authenticated using ((select auth.uid()) = user_id);
revoke all on public.member_app_preferences from public, anon, authenticated;

create table ai_private.analysis_safety_recoveries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  safety_revision bigint not null,
  reason_code text not null check (reason_code in ('symptoms_resolved','misunderstood','reassessment')),
  request_id uuid not null,
  policy_version text not null default 'phase6d-recovery-v1',
  created_at timestamptz not null default now(),
  unique(user_id, safety_revision),
  unique(user_id, request_id)
);
alter table ai_private.analysis_safety_recoveries enable row level security;
revoke all on ai_private.analysis_safety_recoveries from public, anon, authenticated;

create function ai_private.phase6d_recovery_status(p_user_id uuid)
returns jsonb language sql stable security definer
set search_path = pg_catalog, public, ai_private, pg_temp as $$
  select jsonb_build_object(
    'safety_revision', coalesce(s.revision,0),
    'historical_status', coalesce(s.safety_status,'clear'),
    'analysis_blocked', coalesce(s.safety_status in ('hard_stop','review_required'),false) and r.id is null,
    'analysis_status', case when r.id is not null then 'recovered' else coalesce(s.safety_status,'clear') end,
    'automatic_execution_blocked', coalesce(s.safety_status in ('hard_stop','review_required'),false),
    'recovered_at', r.created_at, 'reason_code', r.reason_code,
    'policy_version','phase6d-recovery-v1')
  from (select p_user_id as user_id) u
  left join public.ai_member_safety_state s on s.user_id=u.user_id
  left join ai_private.analysis_safety_recoveries r on r.user_id=u.user_id and r.safety_revision=s.revision;
$$;
revoke all on function ai_private.phase6d_recovery_status(uuid) from public,anon,authenticated;

create function public.fmz_phase6d_recover_analysis_safety(
  p_expected_safety_revision bigint, p_reason_code text,
  p_no_previous_symptoms boolean, p_no_current_serious_symptoms boolean,
  p_understands_support boolean, p_request_id uuid
) returns jsonb language plpgsql security definer
set search_path = pg_catalog, public, ai_private, pg_temp as $$
declare
  v_user uuid := auth.uid();
  v_state public.ai_member_safety_state%rowtype;
  v_recovery ai_private.analysis_safety_recoveries%rowtype;
begin
  perform ai_private.assert_member(v_user);
  if p_request_id is null or p_expected_safety_revision is null
     or p_reason_code is null or p_reason_code not in ('symptoms_resolved','misunderstood','reassessment')
     or p_no_previous_symptoms is distinct from true
     or p_no_current_serious_symptoms is distinct from true
     or p_understands_support is distinct from true then
    raise exception 'recovery_explicit_confirmation_required' using errcode='22023';
  end if;
  -- Same lock as a new serious signal; a stale confirmation cannot clear it.
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_safety:' || v_user::text,0));
  select * into v_state from public.ai_member_safety_state where user_id=v_user for update;
  if v_state.revision is distinct from p_expected_safety_revision then
    raise exception 'recovery_stale_conflict' using errcode='40001';
  end if;
  select * into v_recovery from ai_private.analysis_safety_recoveries
    where user_id=v_user and request_id=p_request_id;
  if found then
    if v_recovery.safety_revision<>p_expected_safety_revision or v_recovery.reason_code<>p_reason_code then
      raise exception 'recovery_request_conflict' using errcode='23505';
    end if;
    return ai_private.phase6d_recovery_status(v_user) || '{"replay":true}'::jsonb;
  end if;
  if v_state.safety_status not in ('hard_stop','review_required') then
    raise exception 'recovery_not_required' using errcode='22023';
  end if;
  insert into ai_private.analysis_safety_recoveries(user_id,safety_revision,reason_code,request_id)
    values(v_user,p_expected_safety_revision,p_reason_code,p_request_id)
    on conflict(user_id,safety_revision) do nothing;
  return ai_private.phase6d_recovery_status(v_user);
end;
$$;
revoke all on function public.fmz_phase6d_recover_analysis_safety(bigint,text,boolean,boolean,boolean,uuid) from public,anon,authenticated;
grant execute on function public.fmz_phase6d_recover_analysis_safety(bigint,text,boolean,boolean,boolean,uuid) to authenticated;

alter table public.ai_consent_events drop constraint ai_consent_events_kind_check;
alter table public.ai_consent_events add constraint ai_consent_events_kind_check
 check(consent_kind in ('ai_processing','trainer_summary_sharing','ai_analysis','private_chat'));
alter table ai_private.consent_documents drop constraint ai_consent_documents_kind_check;
alter table ai_private.consent_documents add constraint ai_consent_documents_kind_check
 check(consent_kind in ('ai_processing','trainer_summary_sharing','ai_analysis','private_chat'));

-- Separate, purpose-limited staging consent. No existing grant is copied.
with copy(locale,content_text) as (values
 ('nl','Ik geef afzonderlijk toestemming voor het verwerken en bewaren van mijn berichten en de antwoorden in mijn privegesprekken met Youri AI. Deze stagingversie gebruikt een vaste simulatie; er gaat geen inhoud naar een externe AI-provider. Mijn trainer krijgt geen toegang tot deze gesprekken. Ik kan deze toestemming intrekken en mijn gesprekken exporteren of verwijderen via Instellingen. Intrekken wijzigt mijn andere toestemmingen niet.'),
 ('en','I separately consent to processing and storing my messages and replies in private conversations with Youri AI. This staging version uses a fixed simulation; no content is sent to an external AI provider. My trainer cannot access these conversations. I can withdraw this consent and export or delete my conversations in Settings. Withdrawal does not change my other consents.'),
 ('de','Ich willige gesondert in die Verarbeitung und Speicherung meiner Nachrichten und Antworten in privaten Gespraechen mit Youri AI ein. Diese Stagingversion verwendet eine feste Simulation; keine Inhalte gehen an einen externen KI-Anbieter. Mein Trainer hat keinen Zugriff auf diese Gespraeche. Ich kann diese Einwilligung widerrufen und meine Gespraeche in den Einstellungen exportieren oder loeschen. Andere Einwilligungen bleiben unveraendert.')
)
insert into ai_private.consent_documents(consent_kind,document_version,locale,purpose_code,categories,content_text,content_sha256,status,effective_at)
select 'private_chat','phase6d-private-chat-v1',locale,'private_chat_staging_v1',array['private_messages','assistant_replies'],
 content_text,encode(extensions.digest(convert_to(content_text,'UTF8'),'sha256'),'hex'),'active',now() from copy;

create function public.fmz_phase6d_get_member_settings()
returns jsonb language plpgsql stable security definer
set search_path=pg_catalog,public,ai_private,pg_temp as $$
declare
 v_user uuid:=auth.uid();
 v_profile public.profiles%rowtype;
 v_settings public.user_settings%rowtype;
 v_app public.member_app_preferences%rowtype;
 v_plan public.entitlements%rowtype;
begin
 if v_user is null then raise exception 'auth_required' using errcode='42501'; end if;
 select * into v_profile from public.profiles where id=v_user;
 if not found then raise exception 'profile_required' using errcode='42501'; end if;
 select * into v_settings from public.user_settings where user_id=v_user;
 select * into v_app from public.member_app_preferences where user_id=v_user;
 select * into v_plan from public.entitlements where user_id=v_user
 order by (status='active' and starts_at<=now() and (ends_at is null or ends_at>now())) desc,
 case entitlement_code when 'personal_coaching' then 4 when 'ai' then 3 when 'pro' then 2 else 1 end desc,
 starts_at desc limit 1;
 return jsonb_build_object(
  'profile',jsonb_build_object('name',v_profile.name,'email',(select email from auth.users where id=v_user),
    'role',v_profile.role,'trainer_linked',v_profile.trainer_id is not null),
  'language',coalesce(v_settings.language,'nl'),
  'country',coalesce(v_settings.country,'Nederland'),
  'unit_system',coalesce(v_settings.unit_system,'metric'),
  'display',jsonb_build_object('date_format',coalesce(v_app.date_format,'locale'),
    'hour_cycle',coalesce(v_app.hour_cycle,'24')),
  'avatar',jsonb_build_object('visible',coalesce(v_app.avatar_visible,true),
    'side',coalesce(v_app.avatar_side,'right'),'y',coalesce(v_app.avatar_y,0.72)),
  'revision',coalesce(v_app.revision,0),
  'analysis_preferences',case when v_profile.role='client' then ai_private.phase6d_current_preferences(v_user) else null end,
  'subscription',jsonb_build_object('plan',coalesce(v_plan.entitlement_code,'free'),
    'status',coalesce(v_plan.status,'unavailable'),'starts_at',v_plan.starts_at,'ends_at',v_plan.ends_at,
    'trial_status',case when v_plan.source ilike '%trial%' then 'trial' else 'not_recorded' end,
    'billing_available',false,'future_destination','subscription_management'),
  'account_deletion_available',false);
end;
$$;

create function public.fmz_phase6d_update_member_settings(p_patch jsonb, p_expected_revision bigint)
returns jsonb language plpgsql security definer
set search_path=pg_catalog,public,ai_private,pg_temp as $$
declare
 v_user uuid:=auth.uid();
 v_current public.member_app_preferences%rowtype;
begin
 if v_user is null or not exists(select 1 from public.profiles where id=v_user) then
   raise exception 'auth_required' using errcode='42501'; end if;
 if jsonb_typeof(p_patch) is distinct from 'object' or p_expected_revision is null
    or exists(select 1 from jsonb_object_keys(p_patch) k where k not in
      ('language','name','country','date_format','hour_cycle','avatar_visible','avatar_side','avatar_y')) then
   raise exception 'settings_input_invalid' using errcode='22023'; end if;
 if exists(select 1 from jsonb_each(p_patch) e where e.value='null'::jsonb)
    or (p_patch ? 'language' and (jsonb_typeof(p_patch->'language')<>'string' or p_patch->>'language' not in ('nl','en','de')))
    or (p_patch ? 'date_format' and p_patch->>'date_format' not in ('locale','iso','day_first'))
    or (p_patch ? 'hour_cycle' and p_patch->>'hour_cycle' not in ('12','24'))
    or (p_patch ? 'avatar_visible' and jsonb_typeof(p_patch->'avatar_visible')<>'boolean')
    or (p_patch ? 'avatar_side' and p_patch->>'avatar_side' not in ('left','right'))
    or (p_patch ? 'avatar_y' and (jsonb_typeof(p_patch->'avatar_y')<>'number' or (p_patch->>'avatar_y')::numeric not between 0 and 1))
    or (p_patch ? 'name' and (jsonb_typeof(p_patch->'name')<>'string' or length(btrim(p_patch->>'name')) not between 1 and 120))
    or (p_patch ? 'country' and (jsonb_typeof(p_patch->'country')<>'string' or length(btrim(p_patch->>'country')) not between 1 and 80)) then
   raise exception 'settings_input_invalid' using errcode='22023'; end if;
 perform pg_advisory_xact_lock(hashtextextended('fmz_member_settings:' || v_user::text,0));
 select * into v_current from public.member_app_preferences where user_id=v_user for update;
 if coalesce(v_current.revision,0)<>p_expected_revision then
   raise exception 'settings_stale_conflict' using errcode='40001'; end if;
 insert into public.member_app_preferences(user_id,date_format,hour_cycle,avatar_visible,avatar_side,avatar_y)
 values(v_user,coalesce(p_patch->>'date_format',v_current.date_format,'locale'),
 coalesce(p_patch->>'hour_cycle',v_current.hour_cycle,'24'),
 coalesce((p_patch->>'avatar_visible')::boolean,v_current.avatar_visible,true),
 coalesce(p_patch->>'avatar_side',v_current.avatar_side,'right'),
 coalesce((p_patch->>'avatar_y')::numeric,v_current.avatar_y,0.72))
 on conflict(user_id) do update set date_format=excluded.date_format,hour_cycle=excluded.hour_cycle,
 avatar_visible=excluded.avatar_visible,avatar_side=excluded.avatar_side,avatar_y=excluded.avatar_y,
 revision=member_app_preferences.revision+1,updated_at=now();
 if p_patch ? 'language' or p_patch ? 'country' then
   insert into public.user_settings(user_id,language,country) values(v_user,coalesce(p_patch->>'language','nl'),coalesce(p_patch->>'country','Nederland'))
   on conflict(user_id) do update set language=coalesce(p_patch->>'language',user_settings.language),
     country=coalesce(p_patch->>'country',user_settings.country),updated_at=now();
 end if;
 if p_patch ? 'name' then update public.profiles set name=btrim(p_patch->>'name'),updated_at=now() where id=v_user; end if;
 return public.fmz_phase6d_get_member_settings();
end;
$$;
revoke all on function public.fmz_phase6d_get_member_settings() from public,anon,authenticated;
revoke all on function public.fmz_phase6d_update_member_settings(jsonb,bigint) from public,anon,authenticated;
grant execute on function public.fmz_phase6d_get_member_settings() to authenticated;
grant execute on function public.fmz_phase6d_update_member_settings(jsonb,bigint) to authenticated;

create or replace function ai_private.phase6d_analysis_status(
  p_user_id uuid,
  p_analysis_kind text default 'daily',
  p_at timestamptz default now()
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_feature text;
  v_model text;
  v_entitlement record;
  v_consent record;
  v_safety public.ai_member_safety_state%rowtype;
  v_config ai_private.phase6d_runtime_config%rowtype;
  v_budget jsonb;
  v_age boolean;
  v_allowed boolean;
  v_reason text := 'allowed';
begin
  perform ai_private.assert_member(p_user_id);
  v_feature := ai_private.phase6d_feature_code(p_analysis_kind);
  v_model := ai_private.phase6d_model_tier(p_analysis_kind);
  select * into v_entitlement from ai_private.current_entitlement(p_user_id, p_at);
  select * into v_consent from ai_private.current_consent(p_user_id, 'ai_analysis');
  select * into v_safety from public.ai_member_safety_state where user_id = p_user_id;
  select * into v_config from ai_private.phase6d_runtime_config where singleton;
  v_age := ai_private.phase6d_age_eligible(p_user_id);
  v_budget := ai_private.phase6d_budget_snapshot(p_user_id, v_model, p_at);

  if v_config.singleton is null or not v_config.mock_analyses_enabled then
    v_reason := 'mock_disabled';
  elsif v_config.external_provider_enabled then
    v_reason := 'external_provider_forbidden';
  elsif p_analysis_kind = 'daily' and not v_config.daily_enabled then
    v_reason := 'analysis_kind_disabled';
  elsif p_analysis_kind = 'post_workout' and not v_config.post_workout_enabled then
    v_reason := 'analysis_kind_disabled';
  elsif p_analysis_kind = 'weekly' and not v_config.weekly_enabled then
    v_reason := 'analysis_kind_disabled';
  elsif v_entitlement.entitlement_code is null then
    v_reason := 'ai_entitlement_required';
  elsif coalesce(v_consent.consent_state, 'missing') <> 'granted' or not coalesce(v_consent.document_active, false) then
    v_reason := 'ai_analysis_consent_required';
  elsif not v_age then
    v_reason := 'ai_age_required';
  elsif (ai_private.phase6d_recovery_status(p_user_id)->>'analysis_blocked')::boolean then
    v_reason := 'safety_hard_stop';
  elsif not coalesce((v_budget ->> 'allowed')::boolean, false) then
    v_reason := coalesce(v_budget ->> 'reason', 'budget_hard_stop');
  end if;
  v_allowed := v_reason = 'allowed';

  return jsonb_build_object(
    'analysis_allowed', v_allowed,
    'deny_reason', v_reason,
    'analysis_kind', p_analysis_kind,
    'feature_code', v_feature,
    'model_tier', v_model,
    'adapter_code', 'mock',
    'entitlement_code', v_entitlement.entitlement_code,
    'consent_state', coalesce(v_consent.consent_state, 'missing'),
    'document_active', coalesce(v_consent.document_active, false),
    'age_eligible', v_age,
    'safety_status', ai_private.phase6d_recovery_status(p_user_id)->>'analysis_status',
    'recovery', ai_private.phase6d_recovery_status(p_user_id),
    'automatic_execution_blocked', coalesce(v_safety.safety_status, 'clear') in ('hard_stop', 'review_required'),
    'mock_mode', coalesce(v_config.mock_analyses_enabled, false),
    'external_ai_enabled', false,
    'external_ai_calls', 0,
    'external_ai_cost_eur', 0,
    'budget', v_budget,
    'provider_status', jsonb_build_object(
      'real_provider_enabled', false,
      'dpa_dpia_eu_route_zdr_approved', false,
      'store', false,
      'background', false,
      'tools', '[]'::jsonb,
      'tool_choice', 'none'
    )
  );
end;
$$;

create or replace function public.fmz_phase6d_get_status()
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_latest public.workout_sessions%rowtype;
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  select * into v_latest
  from public.workout_sessions w
  where w.user_id = v_user_id and w.status = 'completed' and w.completed_at is not null
  order by w.completed_at desc, w.created_at desc
  limit 1;
  return jsonb_build_object(
    'schema_version', 'phase6d.status.v1',
    'recovery', ai_private.phase6d_recovery_status(v_user_id),
    'preferences', ai_private.phase6d_current_preferences(v_user_id),
    'contract', public.fmz_phase6d_read_analysis_contract('nl'),
    'kinds', jsonb_build_object(
      'daily', ai_private.phase6d_analysis_status(v_user_id, 'daily', now()),
      'post_workout', ai_private.phase6d_analysis_status(v_user_id, 'post_workout', now()),
      'weekly', ai_private.phase6d_analysis_status(v_user_id, 'weekly', now())
    ),
    'latest_completed_workout', case when v_latest.id is null then null else jsonb_build_object(
      'id', v_latest.id,
      'title', v_latest.title_snapshot,
      'completed_at', v_latest.completed_at
    ) end,
    'result_counts', jsonb_build_object(
      'active', (select count(*) from public.ai_analysis_results r where r.user_id = v_user_id and r.status <> 'deleted'),
      'deleted', (select count(*) from public.ai_analysis_results r where r.user_id = v_user_id and r.status = 'deleted')
    ),
    'privacy', jsonb_build_object(
      'private_chat_used_as_context', false,
      'trainer_access', false,
      'raw_prompt_logging', false,
      'domain_writes_allowed', false,
      'retention_days', 90,
      'audit_metadata_days', 180
    )
  );
end;
$$;

create or replace function public.fmz_phase6a_record_consent(
  p_consent_kind text,
  p_action text,
  p_document_version text,
  p_locale text,
  p_explicit_confirmation boolean,
  p_request_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_document record;
  v_existing public.ai_consent_events%rowtype;
  v_row public.ai_consent_events%rowtype;
begin
  perform ai_private.assert_member(v_user_id);
  if p_consent_kind not in ('ai_processing', 'trainer_summary_sharing', 'private_chat')
     or p_action not in ('granted', 'withdrawn')
     or p_locale not in ('nl', 'en', 'de')
     or p_request_id is null
     or p_explicit_confirmation is distinct from true then
    raise exception 'ai_consent_input_invalid' using errcode = '22023';
  end if;
  select * into v_document
  from ai_private.consent_documents d
  where d.consent_kind = p_consent_kind
    and d.document_version = p_document_version
    and d.locale = p_locale
    and d.status = 'active'
    and d.effective_at <= now();
  if v_document is null then
    raise exception 'ai_consent_document_invalid' using errcode = '22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_consent:' || v_user_id::text || ':' || p_consent_kind, 0));
  select * into v_existing
  from public.ai_consent_events e
  where e.user_id = v_user_id and e.request_id = p_request_id;
  if v_existing.id is not null then
    if v_existing.consent_kind <> p_consent_kind
       or v_existing.consent_state <> p_action
       or v_existing.document_version <> p_document_version
       or v_existing.locale <> p_locale then
      raise exception 'ai_consent_request_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'consent', to_jsonb(v_existing));
  end if;
  insert into public.ai_consent_events(
    id, user_id, consent_kind, consent_state, document_version,
    purpose_code, categories, locale, explicit_confirmation, request_id
  ) values (
    gen_random_uuid(), v_user_id, p_consent_kind, p_action, p_document_version,
    v_document.purpose_code, v_document.categories, p_locale, true, p_request_id
  ) returning * into v_row;
  insert into ai_private.audit_events(id, user_id, event_code, safe_metadata)
  values (
    gen_random_uuid(), v_user_id, 'consent_' || p_action,
    jsonb_build_object('consent_kind', p_consent_kind, 'document_version', p_document_version, 'locale', p_locale)
  );
  return jsonb_build_object('replay', false, 'consent', to_jsonb(v_row));
end;
$$;

create or replace function public.fmz_phase6a_read_consent_contract(p_locale text default 'nl')
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
begin
  perform ai_private.assert_member(v_user_id);
  if p_locale not in ('nl', 'en', 'de') then
    raise exception 'ai_locale_invalid' using errcode = '22023';
  end if;
  return jsonb_build_object(
    'locale', p_locale,
    'contracts', coalesce((
      select jsonb_agg(jsonb_build_object(
        'consent_kind', d.consent_kind,
        'document_version', d.document_version,
        'purpose_code', d.purpose_code,
        'categories', to_jsonb(d.categories),
        'content_text', d.content_text,
        'content_sha256', d.content_sha256,
        'effective_at', d.effective_at,
        'explicit_confirmation_required', true,
        'preselected', false
      ) order by d.consent_kind)
      from ai_private.consent_documents d
      where d.locale = p_locale and d.status = 'active' and d.effective_at <= now()
    ), '[]'::jsonb),
    'current', jsonb_build_object(
      'private_chat', coalesce((select to_jsonb(c) from ai_private.current_consent(v_user_id, 'private_chat') c), '{"consent_state":"missing"}'::jsonb),
      'ai_processing', coalesce((select to_jsonb(c) from ai_private.current_consent(v_user_id, 'ai_processing') c), '{"consent_state":"missing"}'::jsonb),
      'trainer_summary_sharing', coalesce((select to_jsonb(c) from ai_private.current_consent(v_user_id, 'trainer_summary_sharing') c), '{"consent_state":"missing"}'::jsonb)
    )
  );
end;
$$;

create or replace function ai_private.phase6c_chat_status(p_user_id uuid, p_at timestamptz default now())
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_entitlement record;
  v_consent record;
  v_age boolean;
  v_safety text;
  v_config ai_private.phase6c_runtime_config%rowtype;
  v_allowed boolean;
  v_reason text;
begin
  perform ai_private.assert_member(p_user_id);
  select * into v_entitlement from ai_private.current_entitlement(p_user_id, p_at);
  select * into v_consent from ai_private.current_consent(p_user_id, 'private_chat');
  v_age := ai_private.phase6c_age_eligible(p_user_id);
  select coalesce(s.safety_status, 'clear') into v_safety
  from public.ai_member_safety_state s where s.user_id = p_user_id;
  v_safety := coalesce(v_safety, 'clear');
  select * into v_config from ai_private.phase6c_runtime_config where singleton;

  -- Safety remains authoritative for automatic execution, but communication stays open.
  v_allowed := v_entitlement.entitlement_code is not null
    and v_consent.consent_state = 'granted'
    and coalesce(v_consent.document_active, false)
    and v_age
    and coalesce(v_config.mock_chat_enabled, false)
    and not coalesce(v_config.external_provider_enabled, true);
  v_reason := case
    when v_entitlement.entitlement_code is null then 'ai_entitlement_required'
    when v_consent.consent_state is distinct from 'granted' or not coalesce(v_consent.document_active, false) then 'ai_consent_required'
    when not v_age then 'ai_age_required'
    when not coalesce(v_config.mock_chat_enabled, false) then 'mock_disabled'
    when coalesce(v_config.external_provider_enabled, true) then 'external_provider_forbidden'
    else 'allowed'
  end;

  return jsonb_build_object(
    'chat_write_allowed', v_allowed,
    'communication_allowed', v_allowed,
    'deny_reason', v_reason,
    'entitlement_code', v_entitlement.entitlement_code,
    'consent_state', coalesce(v_consent.consent_state, 'missing'),
    'consent_document_version', v_consent.document_version,
    'age_eligible', v_age,
    'safety_status', v_safety,
    'automatic_execution_blocked', v_safety in ('hard_stop', 'review_required'),
    'mock_mode', coalesce(v_config.mock_chat_enabled, false),
    'external_ai_enabled', false,
    'external_ai_calls', 0,
    'external_ai_cost_eur', 0
  );
end;
$$;

create or replace function public.fmz_phase6d_update_preferences(
  p_timezone_name text,
  p_daily_enabled boolean,
  p_daily_time text,
  p_post_workout_enabled boolean,
  p_weekly_enabled boolean,
  p_weekly_day smallint,
  p_weekly_time text,
  p_expected_revision bigint default null,
  p_request_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_existing public.ai_analysis_preferences%rowtype;
  v_daily_time time;
  v_weekly_time time;
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  if p_request_id is null or p_expected_revision is null or p_weekly_day is null or p_weekly_day not between 1 and 7
     or p_daily_time is null or p_daily_time !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
     or p_weekly_time is null or p_weekly_time !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
     or p_daily_enabled is null or p_weekly_enabled is null or p_post_workout_enabled is null
     or not exists (select 1 from pg_timezone_names where name = p_timezone_name) then
    raise exception 'analysis_preferences_input_invalid' using errcode = '22023';
  end if;
  v_daily_time := p_daily_time::time;
  v_weekly_time := p_weekly_time::time;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_preferences:' || v_user_id::text, 0));
  select * into v_existing from public.ai_analysis_preferences where user_id = v_user_id for update;
  if v_existing.user_id is not null and v_existing.last_request_id = p_request_id then
    if v_existing.timezone_name<>p_timezone_name or v_existing.daily_time<>v_daily_time
       or v_existing.weekly_time<>v_weekly_time or v_existing.weekly_day<>p_weekly_day
       or v_existing.daily_enabled<>p_daily_enabled or v_existing.weekly_enabled<>p_weekly_enabled
       or v_existing.post_workout_enabled<>p_post_workout_enabled then
      raise exception 'analysis_preferences_request_conflict' using errcode='23505';
    end if;
    return ai_private.phase6d_current_preferences(v_user_id) || jsonb_build_object('replay', true);
  end if;
  if coalesce(v_existing.revision,0) <> p_expected_revision then
    raise exception 'analysis_preferences_stale_conflict' using errcode = '40001';
  end if;
  insert into public.ai_analysis_preferences(
    user_id, timezone_name, daily_enabled, daily_time, post_workout_enabled,
    weekly_enabled, weekly_day, weekly_time, last_request_id, revision
  ) values (
    v_user_id, p_timezone_name, coalesce(p_daily_enabled, true), v_daily_time,
    coalesce(p_post_workout_enabled, true), coalesce(p_weekly_enabled, true),
    p_weekly_day, v_weekly_time, p_request_id, 1
  )
  on conflict (user_id) do update
  set timezone_name = excluded.timezone_name,
      daily_enabled = excluded.daily_enabled,
      daily_time = excluded.daily_time,
      post_workout_enabled = excluded.post_workout_enabled,
      weekly_enabled = excluded.weekly_enabled,
      weekly_day = excluded.weekly_day,
      weekly_time = excluded.weekly_time,
      last_request_id = excluded.last_request_id,
      revision = public.ai_analysis_preferences.revision + 1,
      updated_at = now();
  return ai_private.phase6d_current_preferences(v_user_id) || jsonb_build_object('replay', false);
end;
$$;


-- Stable period lookup also recognizes results from the previous event-key format.
create function ai_private.phase6d_period_result(
 p_user_id uuid,p_kind text,p_event_key text,p_local_date date,p_timezone text
) returns uuid language sql stable security definer
set search_path=pg_catalog,public,ai_private,pg_temp as $$
 select r.id from public.ai_analysis_results r
 where r.user_id=p_user_id and r.analysis_kind=p_kind and (
  r.event_key=p_event_key or
  (p_kind='daily' and (r.period_end_local=p_local_date or (r.created_at at time zone p_timezone)::date=p_local_date)) or
  (p_kind='weekly' and date_trunc('week',coalesce(r.period_end_local,(r.created_at at time zone p_timezone)::date)::timestamp)=date_trunc('week',p_local_date::timestamp))
 ) order by r.created_at,r.id limit 1;
$$;
revoke all on function ai_private.phase6d_period_result(uuid,text,text,date,text) from public,anon,authenticated;
create index ai_analysis_results_period_lookup_idx on public.ai_analysis_results(user_id,analysis_kind,period_end_local);

create or replace function ai_private.phase6d_build_context(
  p_user_id uuid,
  p_analysis_kind text,
  p_event_id uuid default null,
  p_at timestamptz default now()
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_feature text := ai_private.phase6d_feature_code(p_analysis_kind);
  v_pref jsonb := ai_private.phase6d_current_preferences(p_user_id);
  v_tz text := coalesce(v_pref ->> 'timezone_name', 'Europe/Amsterdam');
  v_today date;
  v_period_start date;
  v_period_end date;
  v_window_start date;
  v_event_key text;
  v_workout public.workout_sessions%rowtype;
  v_recovery jsonb := '{}'::jsonb;
  v_nutrition jsonb := '{}'::jsonb;
  v_training jsonb := '{}'::jsonb;
  v_progress jsonb := '{}'::jsonb;
  v_recovery_count integer := 0;
  v_food_days integer := 0;
  v_food_items integer := 0;
  v_workout_count integer := 0;
  v_set_count integer := 0;
  v_weight_count integer := 0;
  v_measure_count integer := 0;
  v_domain_count integer := 0;
  v_observation_count integer := 0;
  v_missing text[] := '{}';
  v_reliable boolean;
  v_quality_level text;
begin
  perform ai_private.assert_member(p_user_id);
  if not exists (select 1 from pg_timezone_names where name = v_tz) then
    v_tz := 'Europe/Amsterdam';
  end if;
  v_today := (p_at at time zone v_tz)::date;

  if p_analysis_kind = 'daily' then
    v_period_start := v_today;
    v_period_end := v_today;
    v_window_start := v_today - 6;
    v_event_key := 'daily:' || v_today::text;
  elsif p_analysis_kind = 'weekly' then
    v_period_end := v_today;
    v_period_start := v_today - 6;
    v_window_start := v_period_start;
    v_event_key := 'weekly:' || to_char(v_today, 'IYYY-IW');
  elsif p_analysis_kind = 'post_workout' then
    select * into v_workout
    from public.workout_sessions w
    where w.user_id = p_user_id
      and w.status = 'completed'
      and w.completed_at is not null
      and (p_event_id is null or w.id = p_event_id)
    order by case when p_event_id is null then w.completed_at end desc nulls last, w.created_at desc
    limit 1;
    if v_workout.id is null then
      v_period_start := v_today;
      v_period_end := v_today;
      v_window_start := v_today - 29;
      v_event_key := 'post_workout:none:' || v_today::text;
    else
      v_period_start := (v_workout.completed_at at time zone v_tz)::date;
      v_period_end := v_period_start;
      v_window_start := v_period_start - 29;
      v_event_key := 'post_workout:' || v_workout.id::text;
    end if;
  else
    raise exception 'analysis_kind_invalid' using errcode = '22023';
  end if;

  select
    count(*)::integer,
    jsonb_strip_nulls(jsonb_build_object(
      'days_logged', count(*),
      'avg_sleep_hours', round(avg(sleep_hours), 1),
      'avg_sleep_quality', round(avg(sleep_quality)::numeric, 1),
      'avg_steps', round(avg(steps)::numeric, 0),
      'avg_energy', round(avg(wellbeing_energy)::numeric, 1),
      'avg_stress', round(avg(wellbeing_stress)::numeric, 1),
      'avg_motivation', round(avg(wellbeing_motivation)::numeric, 1),
      'avg_recovery_feeling', round(avg(recovery_feeling)::numeric, 1),
      'load_statuses', coalesce(jsonb_agg(distinct training_load_status) filter (where training_load_status is not null), '[]'::jsonb)
    ))
  into v_recovery_count, v_recovery
  from public.recovery_logs r
  where r.user_id = p_user_id
    and r.log_date between v_window_start and v_period_end;

  with daily as (
    select
      fl.log_date,
      sum(i.energy_kcal_snapshot) as energy_kcal,
      sum(i.protein_grams_snapshot) as protein_grams,
      sum(i.carbohydrate_grams_snapshot) as carbohydrate_grams,
      sum(i.fat_grams_snapshot) as fat_grams,
      sum(coalesce(i.fiber_grams_snapshot, 0)) as fiber_grams,
      count(i.id) as items
    from public.food_logs fl
    join public.food_log_items i on i.food_log_id = fl.id and i.user_id = fl.user_id and i.status = 'active'
    where fl.user_id = p_user_id
      and fl.status = 'active'
      and fl.archived_at is null
      and i.archived_at is null
      and fl.log_date between v_window_start and v_period_end
    group by fl.log_date
  )
  select
    coalesce(count(*), 0)::integer,
    coalesce(sum(items), 0)::integer,
    jsonb_strip_nulls(jsonb_build_object(
      'days_logged', count(*),
      'items_logged', coalesce(sum(items), 0),
      'avg_energy_kcal', round(avg(energy_kcal), 0),
      'avg_protein_grams', round(avg(protein_grams), 1),
      'avg_carbohydrate_grams', round(avg(carbohydrate_grams), 1),
      'avg_fat_grams', round(avg(fat_grams), 1),
      'avg_fiber_grams', round(avg(fiber_grams), 1)
    ))
  into v_food_days, v_food_items, v_nutrition
  from daily;

  if p_analysis_kind = 'post_workout' and v_workout.id is not null then
    select
      1,
      coalesce(count(*), 0)::integer,
      jsonb_strip_nulls(jsonb_build_object(
        'completed_workouts', 1,
        'selected_workout_title', left(v_workout.title_snapshot, 120),
        'completed_at', v_workout.completed_at,
        'exercise_count', count(distinct s.exercise_slug),
        'set_count', count(s.id),
        'total_volume_kg', round(sum(coalesce(s.actual_reps, 0) * coalesce(s.actual_weight, 0)), 1),
        'avg_rpe', round(avg(s.rpe), 1),
        'avg_rir', round(avg(s.rir)::numeric, 1),
        'sets_with_reps', count(*) filter (where s.actual_reps is not null),
        'sets_with_weight', count(*) filter (where s.actual_weight is not null)
      ))
    into v_workout_count, v_set_count, v_training
    from public.workout_set_logs s
    where s.user_id = p_user_id and s.workout_session_id = v_workout.id;
  else
    select
      count(*)::integer,
      coalesce(sum(set_count), 0)::integer,
      jsonb_strip_nulls(jsonb_build_object(
        'completed_workouts', count(*),
        'set_count', coalesce(sum(set_count), 0),
        'avg_sets_per_workout', round(avg(set_count)::numeric, 1)
      ))
    into v_workout_count, v_set_count, v_training
    from (
      select w.id, count(s.id) as set_count
      from public.workout_sessions w
      left join public.workout_set_logs s on s.workout_session_id = w.id and s.user_id = w.user_id
      where w.user_id = p_user_id
        and w.status = 'completed'
        and w.completed_at is not null
        and (w.completed_at at time zone v_tz)::date between v_window_start and v_period_end
      group by w.id
    ) workouts;
  end if;

  select
    count(*)::integer,
    jsonb_strip_nulls(jsonb_build_object(
      'weight_logs', count(*),
      'latest_weight_kg', (array_agg(weight_kg order by measured_at desc))[1],
      'first_weight_kg', (array_agg(weight_kg order by measured_at asc))[1],
      'latest_log_date', max(log_date),
      'first_log_date', min(log_date)
    ))
  into v_weight_count, v_progress
  from public.weight_logs wl
  where wl.user_id = p_user_id
    and wl.status = 'active'
    and wl.archived_at is null
    and wl.log_date between v_window_start and v_period_end;

  select count(*)::integer into v_measure_count
  from public.body_measurements bm
  where bm.user_id = p_user_id
    and bm.status = 'active'
    and bm.archived_at is null
    and bm.log_date between v_window_start and v_period_end;

  v_progress := v_progress || jsonb_build_object('body_measurement_logs', v_measure_count);

  if v_recovery_count = 0 then v_missing := array_append(v_missing, 'recovery'); end if;
  if v_food_days = 0 then v_missing := array_append(v_missing, 'nutrition'); end if;
  if v_workout_count = 0 then v_missing := array_append(v_missing, 'training'); end if;
  if v_weight_count + v_measure_count = 0 then v_missing := array_append(v_missing, 'progress'); end if;

  v_domain_count :=
    (case when v_recovery_count > 0 then 1 else 0 end)
    + (case when v_food_days > 0 then 1 else 0 end)
    + (case when v_workout_count > 0 then 1 else 0 end)
    + (case when v_weight_count + v_measure_count > 0 then 1 else 0 end);
  v_observation_count := v_recovery_count + v_food_days + v_workout_count + v_weight_count + v_measure_count;

  if p_analysis_kind = 'daily' then
    v_reliable := v_domain_count >= 1 and v_observation_count >= 1;
  elsif p_analysis_kind = 'weekly' then
    v_reliable := v_domain_count >= 2 and v_observation_count >= 3;
  else
    v_reliable := v_workout.id is not null;
  end if;
  v_quality_level := case
    when not v_reliable then 'insufficient'
    when p_analysis_kind = 'post_workout' and v_set_count = 0 then 'partial'
    when v_domain_count >= 3 then 'sufficient'
    else 'partial'
  end;

  return jsonb_build_object(
    'schema_version', 'phase6d.context.v1',
    'analysis_kind', p_analysis_kind,
    'feature_code', v_feature,
    'event_key', v_event_key,
    'source_cutoff_at', p_at,
    'period', jsonb_build_object(
      'start_local', v_period_start,
      'end_local', v_period_end,
      'timezone_name', v_tz,
      'max_lookback_days', 30
    ),
    'quality', jsonb_build_object(
      'level', v_quality_level,
      'reliable', v_reliable,
      'domain_count', v_domain_count,
      'observation_count', v_observation_count,
      'missing_sources', to_jsonb(v_missing),
      'stop_before_provider', not v_reliable
    ),
    'sources', jsonb_build_object(
      'training', v_training,
      'nutrition', v_nutrition,
      'recovery', v_recovery,
      'progress', v_progress
    ),
    'unavailable_sources', to_jsonb(v_missing),
    'privacy', jsonb_build_object(
      'private_chat_included', false,
      'raw_prompts_included', false,
      'raw_notes_included', false,
      'trainer_visible', false,
      'domain_writes_allowed', false
    )
  );
end;
$$;

create or replace function public.fmz_phase6d_prepare_analysis(
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
  v_user_id uuid := auth.uid();
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
      'summary', 'Er is nog niet genoeg betrouwbare data voor deze read-only analyse. Vul eerst recente training, voeding, herstel of voortgang aan.',
      'observations', '[]'::jsonb,
      'uncertainties', jsonb_build_array('insufficient_reliable_data'),
      'suggestions', jsonb_build_array(jsonb_build_object('kind','data_quality','text','Voeg recente meetpunten toe en probeer de analyse daarna opnieuw.')),
      'actions', '[]'::jsonb,
      'safety', jsonb_build_object('status','clear','category','none','message_key','safety.clear','automatic_execution_blocked',false),
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

create or replace function public.fmz_phase6d_service_select_due_analyses(p_limit integer default 50)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
begin
  return ai_private.phase6d_select_due_analyses(now(), p_limit);
end;
$$;

create or replace function public.fmz_phase6a_service_complete_run(
  p_run_id uuid,
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
  v_entitlement record;
  v_period record;
  v_account ai_private.budget_accounts%rowtype;
  v_budget jsonb;
  v_release bigint;
  v_response_hash text;
begin
  if p_run_id is null or p_actual_cost_micros not between 0 and 4000000
     or p_input_tokens not between 0 and 1000000
     or p_output_tokens not between 0 and 1000000
     or not ai_private.validate_structured_response(p_structured_output) then
    raise exception 'ai_structured_output_invalid' using errcode = '22023';
  end if;
  v_response_hash := encode(extensions.digest(convert_to(p_structured_output::text, 'UTF8'), 'sha256'), 'hex');
  select * into v_run from ai_private.runs r where r.id = p_run_id for update;
  if v_run.id is null then raise exception 'ai_run_not_found' using errcode = '22023'; end if;
  if v_run.status = 'completed' then
    if v_run.actual_cost_micros <> p_actual_cost_micros
       or v_run.input_tokens <> p_input_tokens
       or v_run.output_tokens <> p_output_tokens
       or v_run.response_hash <> v_response_hash then
      raise exception 'ai_run_completion_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'run_id', v_run.id, 'status', v_run.status);
  elsif v_run.status <> 'reserved' then
    raise exception 'ai_run_not_completable' using errcode = '40001';
  end if;
  if p_structured_output ->> 'feature_code' <> v_run.feature_code
     or p_structured_output ->> 'schema_version' <> v_run.schema_version then
    raise exception 'ai_structured_output_conflict' using errcode = '23505';
  end if;
  if v_run.adapter_code = 'mock' and p_actual_cost_micros <> 0 then
    raise exception 'ai_mock_cost_forbidden' using errcode = '22023';
  end if;
  if v_run.feature_code='private_chat' and v_run.adapter_code='mock'
     and not coalesce((ai_private.phase6c_chat_status(v_run.user_id,now())->>'chat_write_allowed')::boolean,false) then
    raise exception 'ai_consent_or_access_changed' using errcode='42501';
  end if;
  select * into v_entitlement from ai_private.current_entitlement(v_run.user_id, v_run.started_at);
  select * into v_period from ai_private.subscription_period(v_entitlement.entitlement_started_at, v_run.started_at);
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_budget:' || v_run.user_id::text || ':' || v_period.period_start::text, 0));
  select * into v_account from ai_private.budget_accounts a
  where a.user_id = v_run.user_id and a.period_start = v_period.period_start for update;
  v_budget := ai_private.evaluate_budget(
    v_account.consumed_micros,
    greatest(0, v_account.reserved_micros - v_run.reserved_cost_micros),
    p_actual_cost_micros,
    v_run.model_tier
  );
  if not (v_budget ->> 'allowed')::boolean then
    raise exception '%', v_budget ->> 'reason' using errcode = '42501';
  end if;
  v_release := greatest(0, v_run.reserved_cost_micros - p_actual_cost_micros);
  update ai_private.budget_accounts
  set reserved_micros = greatest(0, reserved_micros - v_run.reserved_cost_micros),
      consumed_micros = consumed_micros + p_actual_cost_micros,
      hard_stopped_at = case when consumed_micros + p_actual_cost_micros >= 4000000 then coalesce(hard_stopped_at, now()) else hard_stopped_at end,
      updated_at = now()
  where user_id = v_run.user_id and period_start = v_period.period_start;
  insert into ai_private.usage_ledger(
    id, user_id, run_id, request_id, feature_code, model_tier, ledger_type, amount_micros
  ) values (
    gen_random_uuid(), v_run.user_id, v_run.id, v_run.request_id, v_run.feature_code, v_run.model_tier, 'actual', p_actual_cost_micros
  );
  if v_release > 0 then
    insert into ai_private.usage_ledger(
      id, user_id, run_id, request_id, feature_code, model_tier, ledger_type, amount_micros
    ) values (
      gen_random_uuid(), v_run.user_id, v_run.id, v_run.request_id, v_run.feature_code, v_run.model_tier, 'release', v_release
    );
  end if;
  update ai_private.runs
  set status = 'completed', actual_cost_micros = p_actual_cost_micros,
      input_tokens = p_input_tokens, output_tokens = p_output_tokens,
      response_hash = v_response_hash, completed_at = now()
  where id = v_run.id;
  if p_structured_output -> 'safety' ->> 'status' in ('hard_stop','review_required') then
    perform public.fmz_phase6a_service_record_safety_event(
      v_run.user_id,
      v_run.id,
      p_structured_output -> 'safety' ->> 'category',
      p_structured_output -> 'safety' ->> 'status',
      v_run.policy_version
    );
  end if;
  if v_run.thread_id is not null then
    insert into public.ai_messages(
      id, user_id, thread_id, message_role, feature_code, content_text,
      structured_output, schema_version, status, request_id, run_id
    ) values (
      gen_random_uuid(), v_run.user_id, v_run.thread_id, 'assistant', v_run.feature_code,
      p_structured_output ->> 'summary', p_structured_output, v_run.schema_version,
      'active', v_run.request_id, v_run.id
    );
    update public.ai_threads set updated_at = now() where id = v_run.thread_id;
  end if;
  insert into ai_private.audit_events(id, user_id, run_id, event_code, safe_metadata)
  values (gen_random_uuid(), v_run.user_id, v_run.id, 'run_completed', jsonb_build_object('feature_code', v_run.feature_code, 'safety_status', p_structured_output -> 'safety' ->> 'status'));
  return jsonb_build_object('replay', false, 'run_id', v_run.id, 'status', 'completed', 'fair_use_status', v_budget ->> 'fair_use_status');
end;
$$;
create or replace function ai_private.phase6d_select_due_analyses(
  p_at timestamptz default now(),
  p_limit integer default 50
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_candidates jsonb := '[]'::jsonb;
  v_pref record;
  v_local_date date;
  v_local_time time;
  v_weekday integer;
  v_status jsonb;
  v_event_key text;
  v_latest public.workout_sessions%rowtype;
  v_limit integer := least(greatest(coalesce(p_limit, 50), 1), 200);
begin
  if not exists (
    select 1 from ai_private.phase6d_runtime_config c
    where c.singleton and c.scheduled_generation_enabled and c.mock_analyses_enabled and not c.external_provider_enabled
  ) then
    return jsonb_build_object('schema_version','phase6d.due-selection.v1','candidates','[]'::jsonb,'disabled',true);
  end if;
  for v_pref in
    select
      p.id as user_id,
      coalesce(ap.timezone_name, 'Europe/Amsterdam') as timezone_name,
      coalesce(ap.daily_enabled, true) as daily_enabled,
      coalesce(ap.daily_time, time '07:30') as daily_time,
      coalesce(ap.post_workout_enabled, true) as post_workout_enabled,
      coalesce(ap.weekly_enabled, true) as weekly_enabled,
      coalesce(ap.weekly_day, 1) as weekly_day,
      coalesce(ap.weekly_time, time '08:00') as weekly_time
    from public.profiles p
    left join public.ai_analysis_preferences ap on ap.user_id = p.id
    where p.role = 'client'
    order by p.id
  loop
    exit when jsonb_array_length(v_candidates) >= v_limit;
    if not exists (select 1 from pg_timezone_names where name = v_pref.timezone_name) then
      v_pref.timezone_name := 'Europe/Amsterdam';
    end if;
    v_local_date := (p_at at time zone v_pref.timezone_name)::date;
    v_local_time := (p_at at time zone v_pref.timezone_name)::time;
    v_weekday := extract(isodow from v_local_date)::integer;

    if v_pref.daily_enabled and v_local_time >= v_pref.daily_time then
      v_status := ai_private.phase6d_analysis_status(v_pref.user_id, 'daily', p_at);
      v_event_key := 'daily:' || v_local_date::text;
      if coalesce((v_status ->> 'analysis_allowed')::boolean, false)
         and ai_private.phase6d_period_result(v_pref.user_id,'daily',v_event_key,v_local_date,v_pref.timezone_name) is null then
        v_candidates := v_candidates || jsonb_build_array(jsonb_build_object('user_id', v_pref.user_id, 'analysis_kind', 'daily', 'event_key', v_event_key, 'model_tier', 'luna'));
      end if;
    end if;

    if jsonb_array_length(v_candidates) < v_limit and v_pref.weekly_enabled and v_weekday = v_pref.weekly_day and v_local_time >= v_pref.weekly_time then
      v_status := ai_private.phase6d_analysis_status(v_pref.user_id, 'weekly', p_at);
      v_event_key := 'weekly:' || to_char(v_local_date,'IYYY-IW');
      if coalesce((v_status ->> 'analysis_allowed')::boolean, false)
         and ai_private.phase6d_period_result(v_pref.user_id,'weekly',v_event_key,v_local_date,v_pref.timezone_name) is null then
        v_candidates := v_candidates || jsonb_build_array(jsonb_build_object('user_id', v_pref.user_id, 'analysis_kind', 'weekly', 'event_key', v_event_key, 'model_tier', 'terra'));
      end if;
    end if;

    if jsonb_array_length(v_candidates) < v_limit and v_pref.post_workout_enabled then
      select * into v_latest
      from public.workout_sessions w
      where w.user_id = v_pref.user_id and w.status = 'completed' and w.completed_at is not null
      order by w.completed_at desc, w.created_at desc
      limit 1;
      if v_latest.id is not null then
        v_status := ai_private.phase6d_analysis_status(v_pref.user_id, 'post_workout', p_at);
        v_event_key := 'post_workout:' || v_latest.id::text;
        if coalesce((v_status ->> 'analysis_allowed')::boolean, false)
           and not exists (
             select 1 from public.ai_analysis_results r
             where r.user_id = v_pref.user_id and r.analysis_kind = 'post_workout' and r.event_key = v_event_key
           ) then
          v_candidates := v_candidates || jsonb_build_array(jsonb_build_object('user_id', v_pref.user_id, 'analysis_kind', 'post_workout', 'event_key', v_event_key, 'event_id', v_latest.id, 'model_tier', 'luna'));
        end if;
      end if;
    end if;
  end loop;
  return jsonb_build_object('schema_version','phase6d.due-selection.v1','generated_at',p_at,'candidates',v_candidates,'disabled',false);
end;
$$;
notify pgrst, 'reload schema';
commit;
