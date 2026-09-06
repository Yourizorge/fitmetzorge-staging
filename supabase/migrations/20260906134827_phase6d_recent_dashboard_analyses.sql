-- Final owner mobile hotfix. Staging only: mokxyyullfhkfalopbzd.
-- Read-model correction only: no backfill, existing result update or history repair.
begin;

create or replace function public.fmz_phase6d_get_inbox() returns jsonb
language plpgsql security definer set search_path=pg_catalog,public,ai_private,pg_temp as $$
declare v_user uuid:=auth.uid(); v_response jsonb;
begin
 perform ai_private.assert_member(v_user);
 with available as (
  select coalesce(n.id,r.id) as id,r.id as analysis_id,coalesce(n.state,'new') as state,
    r.created_at,r.completed_at,coalesce(r.completed_at,r.created_at) as available_at,
    r.analysis_kind,r.status,r.model_tier,left(coalesce(nullif(r.summary_text,''),r.analysis_kind),120) as title
  from public.ai_analysis_results r
  left join public.member_notifications n on n.analysis_id=r.id and n.user_id=r.user_id
  where r.user_id=v_user and r.status in ('ready','partial','insufficient_data')
    and r.content_deleted_at is null and r.result_expires_at>now()
    and coalesce(n.state,'new')<>'archived'
 )
 select jsonb_build_object(
  'items',coalesce((select jsonb_agg(to_jsonb(i) order by available_at desc,analysis_id desc)
    from (select * from available where state in ('new','later') order by available_at desc,analysis_id desc limit 5) i),'[]'::jsonb),
  'recent',coalesce((select jsonb_agg(to_jsonb(i) order by available_at desc,analysis_id desc)
    from (select * from available order by available_at desc,analysis_id desc limit 3) i),'[]'::jsonb),
  'unread_count',(select count(*) from available where state in ('new','later')),
  'server_time',now()
 ) into v_response;
 return v_response;
end;
$$;
revoke all on function public.fmz_phase6d_get_inbox() from public,anon,authenticated;
grant execute on function public.fmz_phase6d_get_inbox() to authenticated;

create or replace function public.fmz_phase6d_mark_notification(p_analysis_id uuid,p_action text) returns jsonb
language plpgsql security definer set search_path=pg_catalog,public,ai_private,pg_temp as $$
declare v_user uuid:=auth.uid(); v_note public.member_notifications%rowtype; v_result jsonb;
begin
 perform ai_private.assert_member(v_user);
 if p_action is null or p_action not in ('later','opened','archived') then
  raise exception 'notification_action_invalid' using errcode='22023';
 end if;
 -- Serialize with result deletion and create missing delivery state only on an explicit member action.
 perform 1 from public.ai_analysis_results where id=p_analysis_id and user_id=v_user for update;
 if not found then raise exception 'analysis_result_forbidden' using errcode='42501'; end if;
 v_result:=public.fmz_phase6d_read_analysis(p_analysis_id)->'result';
 if v_result->>'status' not in ('ready','partial','insufficient_data') then
  return jsonb_build_object('analysis_id',p_analysis_id,'state',null);
 end if;
 insert into public.member_notifications(user_id,analysis_id,state,opened_at)
 values(v_user,p_analysis_id,p_action,case when p_action='opened' then now() end)
 on conflict(user_id,analysis_id) do update set
  state=case when member_notifications.state='archived' then 'archived'
    when p_action='later' and member_notifications.state='opened' then 'opened' else p_action end,
  opened_at=case when p_action='opened' then coalesce(member_notifications.opened_at,now()) else member_notifications.opened_at end,
  updated_at=now()
 returning * into v_note;
 return jsonb_build_object('analysis_id',p_analysis_id,'state',v_note.state);
end;
$$;
revoke all on function public.fmz_phase6d_mark_notification(uuid,text) from public,anon,authenticated;
grant execute on function public.fmz_phase6d_mark_notification(uuid,text) to authenticated;

commit;

