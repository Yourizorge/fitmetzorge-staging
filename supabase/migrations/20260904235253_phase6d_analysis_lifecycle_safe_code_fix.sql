begin;

create or replace function public.fmz_phase6d_delete_analysis(
  p_result_id uuid,
  p_expected_revision bigint,
  p_request_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_result public.ai_analysis_results%rowtype;
  v_audit public.ai_analysis_lifecycle_requests%rowtype;
begin
  if v_user_id is null then raise exception 'ai_auth_required' using errcode = '42501'; end if;
  perform ai_private.assert_member(v_user_id);
  if p_result_id is null or p_request_id is null or p_expected_revision is null or p_expected_revision < 1 then
    raise exception 'analysis_delete_input_invalid' using errcode = '22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6d_lifecycle:' || v_user_id::text || ':' || p_request_id::text, 0));
  select * into v_audit from public.ai_analysis_lifecycle_requests r where r.user_id = v_user_id and r.request_id = p_request_id;
  if v_audit.id is not null then
    if v_audit.request_type <> 'delete' or v_audit.result_id is distinct from p_result_id then
      raise exception 'analysis_lifecycle_request_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'result_id', p_result_id, 'deleted', true);
  end if;
  select * into v_result from public.ai_analysis_results r where r.id = p_result_id for update;
  if v_result.id is null or v_result.user_id <> v_user_id then
    raise exception 'analysis_result_forbidden' using errcode = '42501';
  end if;
  if v_result.status <> 'deleted' and v_result.revision <> p_expected_revision then
    raise exception 'analysis_result_stale_conflict' using errcode = '40001';
  end if;
  update public.ai_analysis_results
  set status = 'deleted',
      result_payload = null,
      summary_text = null,
      content_deleted_at = now(),
      completed_at = coalesce(completed_at, now()),
      revision = revision + 1
  where id = p_result_id and user_id = v_user_id;
  insert into public.ai_analysis_lifecycle_requests(
    id, user_id, result_id, request_type, status, request_id, completed_at, safe_result_code
  ) values (
    gen_random_uuid(), v_user_id, p_result_id, 'delete', 'completed', p_request_id, now(), 'analysis_result_deleted'
  );
  return jsonb_build_object('replay', false, 'result_id', p_result_id, 'deleted', true);
end;
$$;

revoke all on function public.fmz_phase6d_delete_analysis(uuid,bigint,uuid) from public, anon, authenticated;
grant execute on function public.fmz_phase6d_delete_analysis(uuid,bigint,uuid) to authenticated;

commit;
