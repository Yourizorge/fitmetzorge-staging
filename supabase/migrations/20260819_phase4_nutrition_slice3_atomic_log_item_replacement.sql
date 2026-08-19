-- FitMetZorge Phase 4 Nutrition Engine - Slice 3 atomic log item replacement
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Additive RPC/ACL only. No table, policy, seed, backfill, legacy mutation,
-- trainer access, provider integration, AI execution or production change.

begin;

create or replace function public.fmz_phase4_replace_food_log_item(
  p_original_item_id uuid,
  p_replacement_item_id uuid,
  p_replacement_request_id uuid,
  p_expected_original_updated_at timestamptz,
  p_meal_moment text,
  p_food_id uuid,
  p_food_portion_id uuid,
  p_consumed_quantity numeric,
  p_consumed_unit text,
  p_notes text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_original public.food_log_items%rowtype;
  v_replacement public.food_log_items%rowtype;
  v_item_id_conflict public.food_log_items%rowtype;
  v_log public.food_logs%rowtype;
  v_food public.foods%rowtype;
  v_portion public.food_portions%rowtype;
  v_timezone text;
  v_today date;
  v_has_full_access boolean;
  v_base_quantity numeric;
  v_base_unit text;
  v_factor numeric;
  v_calculation_basis text;
  v_density_snapshot numeric;
  v_sort_order integer;
  v_normalized_notes text := nullif(btrim(p_notes), '');
  v_request_payload jsonb;
  v_replacement_metadata jsonb;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if p_original_item_id is null
     or p_replacement_item_id is null
     or p_replacement_request_id is null
     or p_expected_original_updated_at is null
     or p_food_id is null then
    raise exception 'original item, stable replacement item, replacement request, expected timestamp, and food UUID required'
      using errcode = '22023';
  end if;

  if p_original_item_id = p_replacement_item_id then
    raise exception 'replacement item UUID must differ from original item UUID'
      using errcode = '22023';
  end if;

  if p_meal_moment not in ('breakfast', 'lunch', 'dinner', 'snacks') then
    raise exception 'unsupported meal moment'
      using errcode = '22023';
  end if;

  if p_consumed_unit not in ('g', 'ml', 'serving', 'piece') then
    raise exception 'unsupported consumption unit'
      using errcode = '22023';
  end if;

  if p_consumed_quantity is null
     or p_consumed_quantity <= 0
     or p_consumed_quantity > 100000 then
    raise exception 'consumed quantity must be positive and within supported bounds'
      using errcode = '22023';
  end if;

  if v_normalized_notes is not null and char_length(v_normalized_notes) > 1000 then
    raise exception 'notes exceed supported length'
      using errcode = '22023';
  end if;

  v_request_payload := jsonb_build_object(
    'original_item_id', p_original_item_id,
    'replacement_item_id', p_replacement_item_id,
    'meal_moment', p_meal_moment,
    'food_id', p_food_id,
    'food_portion_id', p_food_portion_id,
    'consumed_quantity', p_consumed_quantity,
    'consumed_unit', p_consumed_unit,
    'notes', v_normalized_notes
  );

  -- Share the normal logging request namespace so a request UUID cannot race
  -- between create and replace operations.
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_request:' || v_user_id::text || ':' || p_replacement_request_id::text,
      0
    )
  );

  -- Share the archive object namespace so archive and replacement serialize.
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_item_request:' || v_user_id::text || ':' || p_original_item_id::text,
      0
    )
  );

  select i.* into v_original
  from public.food_log_items i
  where i.id = p_original_item_id
    and i.user_id = v_user_id
  for update;

  if not found then
    raise exception 'food log item not found'
      using errcode = '42501';
  end if;

  select l.* into v_log
  from public.food_logs l
  where l.id = v_original.food_log_id
    and l.user_id = v_user_id
    and l.status = 'active'
  for update;

  if not found then
    raise exception 'active Nutrition day log unavailable'
      using errcode = '42501';
  end if;

  select i.* into v_replacement
  from public.food_log_items i
  where i.user_id = v_user_id
    and i.request_id = p_replacement_request_id;

  if found then
    if v_replacement.id is distinct from p_replacement_item_id
       or v_replacement.food_log_id is distinct from v_original.food_log_id
       or v_replacement.metadata ->> 'operation' is distinct from 'replace'
       or v_replacement.metadata ->> 'replaces_item_id' is distinct from p_original_item_id::text
       or v_replacement.metadata -> 'replacement_request' is distinct from v_request_payload then
      raise exception 'replacement request UUID was already used with a different payload'
        using errcode = '23505';
    end if;

    if v_original.status is distinct from 'archived' then
      raise exception 'replacement replay found an incomplete original archive state'
        using errcode = '40001';
    end if;

    return jsonb_build_object(
      'replacement_item', to_jsonb(v_replacement),
      'archived_original', jsonb_build_object(
        'id', v_original.id,
        'status', v_original.status,
        'archived_at', v_original.archived_at,
        'updated_at', v_original.updated_at
      ),
      'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date),
      'idempotent_replay', true
    );
  end if;

  if v_original.status is distinct from 'active' then
    raise exception 'food log item is no longer active; refresh before replacing'
      using errcode = '40001';
  end if;

  if v_original.updated_at is distinct from p_expected_original_updated_at then
    raise exception 'food log item changed; refresh before replacing'
      using errcode = '40001';
  end if;

  -- Reject an already existing replacement identity before taking its object
  -- lock. This avoids crossed original/replacement lock waits between devices.
  select i.* into v_item_id_conflict
  from public.food_log_items i
  where i.id = p_replacement_item_id;

  if found then
    raise exception 'replacement item UUID is unavailable'
      using errcode = '23505';
  end if;

  -- A separate object lock makes same replacement UUID conflicts deterministic.
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_item_request:' || v_user_id::text || ':' || p_replacement_item_id::text,
      0
    )
  );

  select i.* into v_item_id_conflict
  from public.food_log_items i
  where i.id = p_replacement_item_id;

  if found then
    raise exception 'replacement item UUID is unavailable'
      using errcode = '23505';
  end if;

  select coalesce(p.timezone_name, v_log.timezone_name, 'UTC')
  into v_timezone
  from (select 1) seed
  left join public.nutrition_preferences p on p.user_id = v_user_id;
  v_timezone := coalesce(v_timezone, v_log.timezone_name, 'UTC');
  v_today := (now() at time zone v_timezone)::date;
  v_has_full_access := public.fmz_phase4_has_full_nutrition_access(v_user_id);

  if v_log.log_date > v_today then
    raise exception 'future Nutrition day is unavailable'
      using errcode = '22023';
  end if;

  if not v_has_full_access and v_log.log_date < v_today - 6 then
    raise exception 'Free Nutrition history is limited to seven local calendar days'
      using errcode = '42501';
  end if;

  select * into v_food
  from public.foods f
  where f.id = p_food_id
    and f.status = 'active'
    and (
      f.catalog_scope = 'canonical'
      or (f.catalog_scope = 'custom' and f.owner_user_id = v_user_id)
    );

  if not found then
    raise exception 'active visible food not found'
      using errcode = '42501';
  end if;

  if p_food_portion_id is not null then
    select * into v_portion
    from public.food_portions p
    where p.id = p_food_portion_id
      and p.food_id = v_food.id
      and p.status = 'active';

    if not found then
      raise exception 'active portion does not belong to selected food'
        using errcode = '42501';
    end if;

    if p_consumed_unit is distinct from v_portion.unit then
      raise exception 'consumption unit must match selected portion unit'
        using errcode = '22023';
    end if;

    v_base_quantity := p_consumed_quantity / v_portion.amount * v_portion.equivalent_amount;
    v_base_unit := v_portion.equivalent_unit;
    v_calculation_basis := 'portion_conversion';
  else
    v_base_quantity := p_consumed_quantity;
    v_base_unit := p_consumed_unit;
    v_calculation_basis := 'direct_reference';
  end if;

  if v_base_unit = v_food.reference_unit then
    v_factor := v_base_quantity / v_food.reference_amount;
  elsif v_base_unit = 'g' and v_food.reference_unit = 'ml' and v_food.density_g_per_ml is not null then
    v_factor := (v_base_quantity / v_food.density_g_per_ml) / v_food.reference_amount;
    v_density_snapshot := v_food.density_g_per_ml;
    if p_food_portion_id is null then
      v_calculation_basis := 'density_conversion';
    end if;
  elsif v_base_unit = 'ml' and v_food.reference_unit = 'g' and v_food.density_g_per_ml is not null then
    v_factor := (v_base_quantity * v_food.density_g_per_ml) / v_food.reference_amount;
    v_density_snapshot := v_food.density_g_per_ml;
    if p_food_portion_id is null then
      v_calculation_basis := 'density_conversion';
    end if;
  else
    raise exception 'explicit portion or density conversion required for these units'
      using errcode = '22023';
  end if;

  if v_factor is null or v_factor <= 0 then
    raise exception 'calculated food factor must be positive'
      using errcode = '22023';
  end if;

  if p_meal_moment = v_original.meal_moment then
    v_sort_order := v_original.sort_order;
  else
    select coalesce(max(i.sort_order), -1) + 1
    into v_sort_order
    from public.food_log_items i
    where i.user_id = v_user_id
      and i.food_log_id = v_original.food_log_id
      and i.meal_moment = p_meal_moment
      and i.status = 'active';

    if v_sort_order > 10000 then
      raise exception 'destination meal order is full'
        using errcode = '22023';
    end if;
  end if;

  v_replacement_metadata := jsonb_build_object(
    'calculation_version', 'phase4_slice1_v1',
    'operation', 'replace',
    'replaces_item_id', p_original_item_id,
    'replacement_request', v_request_payload
  );

  insert into public.food_log_items(
    id,
    user_id,
    food_log_id,
    food_id,
    food_portion_id,
    meal_moment,
    sort_order,
    consumed_quantity,
    consumed_unit,
    food_name_snapshot,
    brand_snapshot,
    reference_amount_snapshot,
    reference_unit_snapshot,
    portion_label_snapshot,
    portion_equivalent_amount_snapshot,
    portion_equivalent_unit_snapshot,
    density_g_per_ml_snapshot,
    calculation_basis,
    energy_kcal_snapshot,
    protein_grams_snapshot,
    carbohydrate_grams_snapshot,
    fat_grams_snapshot,
    fiber_grams_snapshot,
    source_provider_snapshot,
    provider_food_id_snapshot,
    source_version_snapshot,
    provenance_snapshot,
    notes,
    status,
    request_id,
    consumed_at,
    metadata
  )
  values (
    p_replacement_item_id,
    v_user_id,
    v_original.food_log_id,
    v_food.id,
    v_portion.id,
    p_meal_moment,
    v_sort_order,
    p_consumed_quantity,
    p_consumed_unit,
    v_food.name,
    v_food.brand,
    v_food.reference_amount,
    v_food.reference_unit,
    v_portion.label,
    v_portion.equivalent_amount,
    v_portion.equivalent_unit,
    v_density_snapshot,
    v_calculation_basis,
    round(v_food.energy_kcal * v_factor, 3),
    round(v_food.protein_grams * v_factor, 3),
    round(v_food.carbohydrate_grams * v_factor, 3),
    round(v_food.fat_grams * v_factor, 3),
    case when v_food.fiber_grams is null then null else round(v_food.fiber_grams * v_factor, 3) end,
    v_food.source_provider,
    v_food.provider_food_id,
    v_food.source_version,
    v_food.provenance,
    v_normalized_notes,
    'active',
    p_replacement_request_id,
    v_original.consumed_at,
    v_replacement_metadata
  )
  returning * into v_replacement;

  update public.food_log_items
  set status = 'archived'
  where id = p_original_item_id
    and user_id = v_user_id
    and status = 'active'
    and updated_at = p_expected_original_updated_at
  returning * into v_original;

  if not found then
    raise exception 'food log item changed; atomic replacement rolled back'
      using errcode = '40001';
  end if;

  return jsonb_build_object(
    'replacement_item', to_jsonb(v_replacement),
    'archived_original', jsonb_build_object(
      'id', v_original.id,
      'status', v_original.status,
      'archived_at', v_original.archived_at,
      'updated_at', v_original.updated_at
    ),
    'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date),
    'idempotent_replay', false
  );
end;
$$;

revoke all on function public.fmz_phase4_replace_food_log_item(
  uuid, uuid, uuid, timestamptz, text, uuid, uuid, numeric, text, text
) from public;
revoke all on function public.fmz_phase4_replace_food_log_item(
  uuid, uuid, uuid, timestamptz, text, uuid, uuid, numeric, text, text
) from anon;
revoke all on function public.fmz_phase4_replace_food_log_item(
  uuid, uuid, uuid, timestamptz, text, uuid, uuid, numeric, text, text
) from authenticated;
grant execute on function public.fmz_phase4_replace_food_log_item(
  uuid, uuid, uuid, timestamptz, text, uuid, uuid, numeric, text, text
) to authenticated;

commit;
