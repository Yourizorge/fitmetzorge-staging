-- FitMetZorge Phase 4 Nutrition - Slice 4F-D transient OFF parent context fix
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Corrects the trusted parent food-log ownership context for transient OFF logs.
-- No table/data/RLS/catalog/frontend/Edge/legacy/production changes.

begin;

do $$
begin
  if to_regprocedure('public.fmz_phase4_enforce_food_log_owner()') is null
     or to_regprocedure(
       'public.fmz_phase4_transient_off_food_item_mutation(text,uuid,uuid,uuid,uuid,timestamp with time zone,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb)'
     ) is null
     or to_regprocedure(
       'public.fmz_phase4_log_transient_off_food_item(uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb)'
     ) is null then
    raise exception 'Phase 4F-D transient OFF parent-context prerequisites are unavailable';
  end if;
end $$;

-- Browser/member writes continue to use auth.uid(). The service-role-only
-- transient OFF wrapper sets a transaction-local user context before the day
-- parent can be created. Every populated context must identify the same owner.
create or replace function public.fmz_phase4_enforce_food_log_owner()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_authenticated_user_id uuid := auth.uid();
  v_internal_user_id uuid;
  v_transient_off_user_id uuid;
  v_user_id uuid;
begin
  begin
    v_internal_user_id := nullif(
      current_setting('fmz.phase4_provider_snapshot_user_id', true),
      ''
    )::uuid;
    v_transient_off_user_id := nullif(
      current_setting('fmz.phase4_transient_off_snapshot_user_id', true),
      ''
    )::uuid;
  exception
    when invalid_text_representation then
      raise exception 'invalid internal provider write context'
        using errcode = '42501';
  end;

  v_user_id := coalesce(
    v_authenticated_user_id,
    v_internal_user_id,
    v_transient_off_user_id
  );

  if v_user_id is null
     or new.user_id is distinct from v_user_id
     or (v_authenticated_user_id is not null
         and v_authenticated_user_id is distinct from v_user_id)
     or (v_internal_user_id is not null
         and v_internal_user_id is distinct from v_user_id)
     or (v_transient_off_user_id is not null
         and v_transient_off_user_id is distinct from v_user_id) then
    raise exception 'food log owner must match authorized user'
      using errcode = '42501';
  end if;

  if tg_op = 'UPDATE' then
    if new.user_id is distinct from old.user_id
       or new.log_date is distinct from old.log_date
       or new.timezone_name is distinct from old.timezone_name
       or new.timezone_offset_minutes is distinct from old.timezone_offset_minutes
       or new.target_id is distinct from old.target_id
       or new.target_energy_kcal_snapshot is distinct from old.target_energy_kcal_snapshot
       or new.target_protein_grams_snapshot is distinct from old.target_protein_grams_snapshot
       or new.target_carbohydrate_grams_snapshot is distinct from old.target_carbohydrate_grams_snapshot
       or new.target_fat_grams_snapshot is distinct from old.target_fat_grams_snapshot
       or new.target_fiber_grams_snapshot is distinct from old.target_fiber_grams_snapshot
       or new.source is distinct from old.source then
      raise exception 'food log identity and target snapshots are immutable'
        using errcode = '42501';
    end if;
  end if;

  if new.source <> 'phase4_member' then
    raise exception 'member food log source is fixed server-side'
      using errcode = '42501';
  end if;

  if not exists (
    select 1
    from pg_catalog.pg_timezone_names tz
    where tz.name = new.timezone_name
  ) then
    raise exception 'invalid IANA timezone'
      using errcode = '22023';
  end if;

  if new.target_id is not null and not exists (
    select 1
    from public.nutrition_targets t
    where t.id = new.target_id
      and t.user_id = v_user_id
  ) then
    raise exception 'food log target must belong to authorized user'
      using errcode = '42501';
  end if;

  return new;
end;
$$;

-- Establish the transient context before the internal mutation can create the
-- parent food_logs row. The mutation retains authority over all validation,
-- immutable snapshot construction, idempotency, quantity and history rules.
create or replace function public.fmz_phase4_log_transient_off_food_item(
  p_user_id uuid,
  p_item_id uuid,
  p_request_id uuid,
  p_log_date date,
  p_timezone_name text,
  p_timezone_offset_minutes smallint,
  p_meal_moment text,
  p_consumed_quantity numeric,
  p_consumed_unit text,
  p_notes text,
  p_consumed_at timestamptz,
  p_candidate jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
begin
  if p_user_id is null then
    raise exception 'trusted OFF user is required'
      using errcode = '22023';
  end if;

  perform pg_catalog.set_config(
    'fmz.phase4_transient_off_snapshot_user_id',
    p_user_id::text,
    true
  );

  return public.fmz_phase4_transient_off_food_item_mutation(
    'log', p_user_id, null, p_item_id, p_request_id, null,
    p_log_date, p_timezone_name, p_timezone_offset_minutes,
    p_meal_moment, p_consumed_quantity, p_consumed_unit,
    p_notes, p_consumed_at, p_candidate
  );
end;
$$;

-- Trigger functions remain trigger-only. The public wrapper remains callable
-- exclusively by the trusted backend service role.
revoke all on function public.fmz_phase4_enforce_food_log_owner()
  from public, anon, authenticated, service_role;

revoke all on function public.fmz_phase4_log_transient_off_food_item(
  uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb
) from public, anon, authenticated, service_role;
grant execute on function public.fmz_phase4_log_transient_off_food_item(
  uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb
) to service_role;

commit;
