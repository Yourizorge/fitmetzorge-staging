-- Package 6D theme restoration. Staging mokxyyullfhkfalopbzd only.
-- Nullable, no default/backfill: existing row values and revisions are preserved.
begin;
alter table public.member_app_preferences add column theme_mode text
  constraint member_app_preferences_theme_mode_check check (theme_mode in ('system','light','dark'));
comment on column public.member_app_preferences.theme_mode is
  'Own-user appearance preference; NULL means system until an explicit choice. No authorization meaning.';

create or replace function public.fmz_phase6d_get_member_settings()
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
    'hour_cycle',coalesce(v_app.hour_cycle,'24'),'theme_mode',coalesce(v_app.theme_mode,'system')),
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

create or replace function public.fmz_phase6d_update_member_settings(p_patch jsonb, p_expected_revision bigint)
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
      ('language','name','country','date_format','hour_cycle','avatar_visible','avatar_side','avatar_y','theme_mode')) then
   raise exception 'settings_input_invalid' using errcode='22023'; end if;
 if exists(select 1 from jsonb_each(p_patch) e where e.value='null'::jsonb)
    or (p_patch ? 'language' and (jsonb_typeof(p_patch->'language')<>'string' or p_patch->>'language' not in ('nl','en','de')))
    or (p_patch ? 'theme_mode' and (jsonb_typeof(p_patch->'theme_mode')<>'string' or p_patch->>'theme_mode' not in ('system','light','dark')))
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
 insert into public.member_app_preferences(user_id,date_format,hour_cycle,avatar_visible,avatar_side,avatar_y,theme_mode)
 values(v_user,coalesce(p_patch->>'date_format',v_current.date_format,'locale'),
 coalesce(p_patch->>'hour_cycle',v_current.hour_cycle,'24'),
 coalesce((p_patch->>'avatar_visible')::boolean,v_current.avatar_visible,true),
 coalesce(p_patch->>'avatar_side',v_current.avatar_side,'right'),
 coalesce((p_patch->>'avatar_y')::numeric,v_current.avatar_y,0.72),
 coalesce(p_patch->>'theme_mode',v_current.theme_mode))
 on conflict(user_id) do update set date_format=excluded.date_format,hour_cycle=excluded.hour_cycle,
 avatar_visible=excluded.avatar_visible,avatar_side=excluded.avatar_side,avatar_y=excluded.avatar_y,theme_mode=excluded.theme_mode,
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
commit;
