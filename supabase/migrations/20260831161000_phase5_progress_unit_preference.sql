-- FitMetZorge Phase 5 persisted metric/imperial display preference.

begin;

create or replace function public.fmz_phase5_set_unit_system(p_unit_system text)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_unit_system text := lower(btrim(p_unit_system));
  v_row public.user_settings%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required' using errcode = '42501';
  end if;
  if v_unit_system not in ('metric', 'imperial') then
    raise exception 'unit_system must be metric or imperial' using errcode = '22023';
  end if;

  insert into public.user_settings(user_id, language, country, unit_system)
  values (v_user_id, 'nl', 'Nederland', v_unit_system)
  on conflict (user_id) do update
    set unit_system = excluded.unit_system
  returning * into v_row;

  return jsonb_build_object(
    'unit_system', v_row.unit_system,
    'updated_at', v_row.updated_at
  );
end;
$$;

revoke all on function public.fmz_phase5_set_unit_system(text) from public, anon, authenticated;
grant execute on function public.fmz_phase5_set_unit_system(text) to authenticated;

commit;
