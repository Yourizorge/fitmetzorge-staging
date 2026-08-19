-- FitMetZorge Phase 4 Nutrition Engine - Slice 4D transient provider snapshot logging
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Additive RPC/trigger compatibility/ACL only. No seed, provider import,
-- canonical food mutation, legacy mutation, trainer access or production change.

begin;

-- Existing member writes continue to use auth.uid(). The provider RPCs set a
-- transaction-local user context after service-role-only authorization so the
-- existing ownership triggers can validate their backend-created rows.
create or replace function public.fmz_phase4_enforce_food_log_owner()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_authenticated_user_id uuid := auth.uid();
  v_internal_user_id uuid;
  v_user_id uuid;
begin
  begin
    v_internal_user_id := nullif(
      current_setting('fmz.phase4_provider_snapshot_user_id', true),
      ''
    )::uuid;
  exception
    when invalid_text_representation then
      raise exception 'invalid internal provider write context'
        using errcode = '42501';
  end;

  v_user_id := coalesce(v_authenticated_user_id, v_internal_user_id);

  if v_user_id is null or new.user_id is distinct from v_user_id then
    raise exception 'food log owner must match authorized user'
      using errcode = '42501';
  end if;

  if v_authenticated_user_id is null
     and v_internal_user_id is distinct from new.user_id then
    raise exception 'internal provider write context does not match food log owner'
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
    select 1 from pg_catalog.pg_timezone_names tz
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

create or replace function public.fmz_phase4_enforce_food_log_item_owner()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_authenticated_user_id uuid := auth.uid();
  v_internal_user_id uuid;
  v_user_id uuid;
begin
  begin
    v_internal_user_id := nullif(
      current_setting('fmz.phase4_provider_snapshot_user_id', true),
      ''
    )::uuid;
  exception
    when invalid_text_representation then
      raise exception 'invalid internal provider write context'
        using errcode = '42501';
  end;

  v_user_id := coalesce(v_authenticated_user_id, v_internal_user_id);

  if v_user_id is null or new.user_id is distinct from v_user_id then
    raise exception 'food log item owner must match authorized user'
      using errcode = '42501';
  end if;

  if tg_op = 'UPDATE' then
    if (to_jsonb(new) - array['status', 'archived_at', 'updated_at']::text[])
       is distinct from
       (to_jsonb(old) - array['status', 'archived_at', 'updated_at']::text[]) then
      raise exception 'historical food log item snapshots are immutable'
        using errcode = '42501';
    end if;
    return new;
  end if;

  if not exists (
    select 1
    from public.food_logs l
    where l.id = new.food_log_id
      and l.user_id = v_user_id
      and l.status = 'active'
  ) then
    raise exception 'food log item day must belong to authorized user'
      using errcode = '42501';
  end if;

  if new.food_id is null then
    if v_authenticated_user_id is not null
       or v_internal_user_id is distinct from new.user_id
       or new.food_portion_id is not null
       or new.source_provider_snapshot is distinct from 'usda_fdc'
       or new.provider_food_id_snapshot is null
       or new.provider_food_id_snapshot !~ '^[1-9][0-9]{0,15}$'
       or new.reference_amount_snapshot is distinct from 100::numeric
       or new.reference_unit_snapshot is distinct from 'g'
       or new.consumed_unit is distinct from 'g'
       or new.calculation_basis is distinct from 'direct_reference'
       or new.portion_label_snapshot is not null
       or new.portion_equivalent_amount_snapshot is not null
       or new.portion_equivalent_unit_snapshot is not null
       or new.density_g_per_ml_snapshot is not null
       or new.metadata ->> 'operation' is null
       or new.metadata ->> 'operation' not in ('provider_log', 'provider_replace')
       or new.metadata ->> 'candidate_id' is null
       or new.metadata ->> 'mapping_version' is distinct from 'phase4_usda_v1'
       or new.provenance_snapshot ->> 'provider' is distinct from 'usda_fdc'
       or new.provenance_snapshot ->> 'provider_food_id'
          is distinct from new.provider_food_id_snapshot
       or new.provenance_snapshot ->> 'candidate_id'
          is distinct from new.metadata ->> 'candidate_id'
       or new.provenance_snapshot ->> 'mapping_version'
          is distinct from 'phase4_usda_v1'
       or new.provenance_snapshot ->> 'reference_basis'
          is distinct from 'per_100_g' then
      raise exception 'provider snapshot item requires trusted USDA backend context'
        using errcode = '42501';
    end if;
    return new;
  end if;

  if not exists (
    select 1
    from public.foods f
    where f.id = new.food_id
      and f.status = 'active'
      and (
        f.catalog_scope = 'canonical'
        or (f.catalog_scope = 'custom' and f.owner_user_id = v_user_id)
      )
  ) then
    raise exception 'food must be active and visible to authorized user'
      using errcode = '42501';
  end if;

  if new.food_portion_id is not null and not exists (
    select 1
    from public.food_portions p
    where p.id = new.food_portion_id
      and p.food_id = new.food_id
      and p.status = 'active'
  ) then
    raise exception 'food portion must be active and belong to selected food'
      using errcode = '42501';
  end if;

  return new;
end;
$$;

create or replace function public.fmz_phase4_log_provider_food_item(
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
declare
  v_user_id uuid := p_user_id;
  v_timezone text := btrim(p_timezone_name);
  v_saved_timezone text;
  v_today date;
  v_anchor timestamptz;
  v_expected_offset integer;
  v_has_full_access boolean;
  v_target public.nutrition_targets%rowtype;
  v_log public.food_logs%rowtype;
  v_existing_item public.food_log_items%rowtype;
  v_item_id_conflict public.food_log_items%rowtype;
  v_item public.food_log_items%rowtype;
  v_sort_order integer;
  v_normalized_notes text := nullif(btrim(p_notes), '');
  v_candidate_id uuid;
  v_provider_food_id text;
  v_food_name text;
  v_brand text;
  v_provider_data_type text;
  v_source_version text;
  v_retrieved_at timestamptz;
  v_source_updated_at timestamptz;
  v_kcal numeric;
  v_protein numeric;
  v_carbohydrates numeric;
  v_fat numeric;
  v_fiber numeric;
  v_factor numeric;
  v_provenance jsonb;
  v_request_payload jsonb;
  v_metadata jsonb;
begin
  if v_user_id is null
     or p_item_id is null
     or p_request_id is null
     or p_log_date is null then
    raise exception 'trusted user, stable item UUID, request UUID, and log date required'
      using errcode = '22023';
  end if;

  if not exists (select 1 from public.profiles p where p.id = v_user_id) then
    raise exception 'authorized user profile not found'
      using errcode = '42501';
  end if;

  if p_consumed_unit is distinct from 'g' then
    raise exception 'provider food logging supports grams only'
      using errcode = '22023';
  end if;

  if p_consumed_quantity is null
     or p_consumed_quantity::text in ('NaN', 'Infinity', '-Infinity')
     or p_consumed_quantity <= 0
     or p_consumed_quantity > 100000 then
    raise exception 'consumed grams must be positive and within supported bounds'
      using errcode = '22023';
  end if;

  if p_meal_moment not in ('breakfast', 'lunch', 'dinner', 'snacks') then
    raise exception 'unsupported meal moment'
      using errcode = '22023';
  end if;

  if v_normalized_notes is not null and char_length(v_normalized_notes) > 1000 then
    raise exception 'notes exceed supported length'
      using errcode = '22023';
  end if;

  if jsonb_typeof(p_candidate) is distinct from 'object' then
    raise exception 'trusted provider candidate payload must be an object'
      using errcode = '22023';
  end if;

  if (select count(*) from pg_catalog.jsonb_object_keys(p_candidate)) <> 18
     or p_candidate - array[
       'provider', 'provider_food_id', 'candidate_id', 'mapping_version',
       'provider_data_type', 'food_name', 'brand', 'reference_amount',
       'reference_unit', 'energy_kcal_per_100g', 'protein_grams_per_100g',
       'carbohydrate_grams_per_100g', 'fat_grams_per_100g',
       'fiber_grams_per_100g', 'source_version', 'retrieved_at',
       'source_updated_at', 'provenance'
     ]::text[] <> '{}'::jsonb then
    raise exception 'trusted provider candidate payload has unsupported fields'
      using errcode = '22023';
  end if;

  if jsonb_typeof(p_candidate -> 'provider') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'candidate_id') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'provider_food_id') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'mapping_version') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'provider_data_type') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'food_name') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'brand') not in ('string', 'null')
     or jsonb_typeof(p_candidate -> 'reference_amount') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'reference_unit') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'energy_kcal_per_100g') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'protein_grams_per_100g') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'carbohydrate_grams_per_100g') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'fat_grams_per_100g') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'fiber_grams_per_100g') not in ('number', 'null')
     or jsonb_typeof(p_candidate -> 'source_version') not in ('string', 'null')
     or jsonb_typeof(p_candidate -> 'retrieved_at') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'source_updated_at') not in ('string', 'null')
     or jsonb_typeof(p_candidate -> 'provenance') is distinct from 'object' then
    raise exception 'trusted provider candidate payload is malformed'
      using errcode = '22023';
  end if;

  begin
    v_candidate_id := (p_candidate ->> 'candidate_id')::uuid;
    v_kcal := (p_candidate ->> 'energy_kcal_per_100g')::numeric;
    v_protein := (p_candidate ->> 'protein_grams_per_100g')::numeric;
    v_carbohydrates := (p_candidate ->> 'carbohydrate_grams_per_100g')::numeric;
    v_fat := (p_candidate ->> 'fat_grams_per_100g')::numeric;
    v_fiber := case
      when p_candidate -> 'fiber_grams_per_100g' is null
        or p_candidate -> 'fiber_grams_per_100g' = 'null'::jsonb then null
      else (p_candidate ->> 'fiber_grams_per_100g')::numeric
    end;
    v_retrieved_at := (p_candidate ->> 'retrieved_at')::timestamptz;
    v_source_updated_at := case
      when p_candidate -> 'source_updated_at' is null
        or p_candidate -> 'source_updated_at' = 'null'::jsonb then null
      else (p_candidate ->> 'source_updated_at')::timestamptz
    end;
  exception
    when invalid_text_representation or datetime_field_overflow then
      raise exception 'trusted provider candidate payload has invalid typed values'
        using errcode = '22023';
  end;

  v_provider_food_id := btrim(p_candidate ->> 'provider_food_id');
  v_food_name := btrim(p_candidate ->> 'food_name');
  v_brand := nullif(btrim(p_candidate ->> 'brand'), '');
  v_provider_data_type := p_candidate ->> 'provider_data_type';
  v_source_version := nullif(btrim(p_candidate ->> 'source_version'), '');
  v_provenance := p_candidate -> 'provenance';

  if p_candidate ->> 'provider' is distinct from 'usda_fdc'
     or v_provider_food_id !~ '^[1-9][0-9]{0,15}$'
     or p_candidate ->> 'mapping_version' is distinct from 'phase4_usda_v1'
     or v_provider_data_type is null
     or v_provider_data_type not in ('Foundation', 'Survey (FNDDS)', 'SR Legacy')
     or p_candidate ->> 'reference_amount' is distinct from '100'
     or p_candidate ->> 'reference_unit' is distinct from 'g'
     or char_length(v_food_name) not between 1 and 180
     or (v_brand is not null and char_length(v_brand) > 120)
     or (v_source_version is not null and char_length(v_source_version) > 120)
     or v_retrieved_at is null
     or v_retrieved_at > now() + interval '5 minutes'
     or (v_source_updated_at is not null and v_source_updated_at > now() + interval '5 minutes')
     or v_kcal::text in ('NaN', 'Infinity', '-Infinity')
     or v_kcal < 0 or v_kcal > 1500
     or v_protein::text in ('NaN', 'Infinity', '-Infinity')
     or v_protein < 0 or v_protein > 100
     or v_carbohydrates::text in ('NaN', 'Infinity', '-Infinity')
     or v_carbohydrates < 0 or v_carbohydrates > 100
     or v_fat::text in ('NaN', 'Infinity', '-Infinity')
     or v_fat < 0 or v_fat > 100
     or (v_fiber is not null and (
       v_fiber::text in ('NaN', 'Infinity', '-Infinity')
       or v_fiber < 0 or v_fiber > 100
     ))
     or v_provenance ->> 'provider' is distinct from 'usda_fdc'
     or v_provenance ->> 'provider_food_id' is distinct from v_provider_food_id
     or v_provenance ->> 'candidate_id' is distinct from v_candidate_id::text
     or v_provenance ->> 'mapping_version' is distinct from 'phase4_usda_v1'
     or v_provenance ->> 'provider_data_type' is distinct from v_provider_data_type
     or v_provenance ->> 'reference_basis' is distinct from 'per_100_g'
     or v_provenance ->> 'retrieved_at' is distinct from p_candidate ->> 'retrieved_at'
     or v_provenance ->> 'source_version' is distinct from p_candidate ->> 'source_version'
     or v_provenance ->> 'source_updated_at'
        is distinct from p_candidate ->> 'source_updated_at'
     or v_provenance -> 'derivation' is null
     or v_provenance -> 'attribution' is null then
    raise exception 'trusted USDA candidate failed provider snapshot validation'
      using errcode = '22023';
  end if;

  if v_timezone is null
     or not exists (
       select 1 from pg_catalog.pg_timezone_names tz
       where tz.name = v_timezone
     ) then
    raise exception 'valid IANA timezone required'
      using errcode = '22023';
  end if;

  select p.timezone_name into v_saved_timezone
  from public.nutrition_preferences p
  where p.user_id = v_user_id;

  if found and v_saved_timezone is distinct from v_timezone then
    raise exception 'timezone differs from Nutrition preference; update preference first'
      using errcode = '22023';
  end if;

  v_today := (now() at time zone v_timezone)::date;
  v_has_full_access := public.fmz_phase4_has_full_nutrition_access(v_user_id);

  if p_log_date > v_today then
    raise exception 'future Nutrition logging is not supported'
      using errcode = '22023';
  end if;

  if not v_has_full_access and p_log_date < v_today - 6 then
    raise exception 'Free Nutrition history is limited to seven local calendar days'
      using errcode = '42501';
  end if;

  if p_consumed_at is not null
     and (p_consumed_at at time zone v_timezone)::date is distinct from p_log_date then
    raise exception 'consumed timestamp must belong to selected local log date'
      using errcode = '22023';
  end if;

  v_anchor := coalesce(
    p_consumed_at,
    (p_log_date::timestamp + interval '12 hours') at time zone v_timezone
  );
  v_expected_offset := round(
    extract(epoch from (
      (v_anchor at time zone v_timezone) - (v_anchor at time zone 'UTC')
    )) / 60
  );

  if p_timezone_offset_minutes is null
     or p_timezone_offset_minutes::integer <> v_expected_offset then
    raise exception 'timezone offset does not match selected timezone and date'
      using errcode = '22023';
  end if;

  v_request_payload := jsonb_build_object(
    'item_id', p_item_id,
    'log_date', p_log_date,
    'timezone_name', v_timezone,
    'timezone_offset_minutes', p_timezone_offset_minutes,
    'meal_moment', p_meal_moment,
    'consumed_quantity', p_consumed_quantity,
    'consumed_unit', 'g',
    'notes', v_normalized_notes,
    'consumed_at', p_consumed_at,
    'candidate', p_candidate
  );

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_request:' || v_user_id::text || ':' || p_request_id::text,
      0
    )
  );

  select i.* into v_existing_item
  from public.food_log_items i
  where i.user_id = v_user_id
    and i.request_id = p_request_id;

  if found then
    if v_existing_item.id is distinct from p_item_id
       or v_existing_item.food_id is not null
       or v_existing_item.metadata ->> 'operation' is distinct from 'provider_log'
       or v_existing_item.metadata -> 'provider_request' is distinct from v_request_payload then
      raise exception 'provider request UUID was already used with a different payload'
        using errcode = '23505';
    end if;

    select l.* into v_log
    from public.food_logs l
    where l.id = v_existing_item.food_log_id
      and l.user_id = v_user_id;

    return jsonb_build_object(
      'item', to_jsonb(v_existing_item),
      'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date),
      'idempotent_replay', true
    );
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log:' || v_user_id::text || ':' || p_log_date::text,
      0
    )
  );

  select i.* into v_existing_item
  from public.food_log_items i
  where i.user_id = v_user_id
    and i.request_id = p_request_id;

  if found then
    if v_existing_item.id is distinct from p_item_id
       or v_existing_item.food_id is not null
       or v_existing_item.metadata ->> 'operation' is distinct from 'provider_log'
       or v_existing_item.metadata -> 'provider_request' is distinct from v_request_payload then
      raise exception 'provider request UUID was already used with a different payload'
        using errcode = '23505';
    end if;

    select l.* into v_log
    from public.food_logs l
    where l.id = v_existing_item.food_log_id
      and l.user_id = v_user_id;

    return jsonb_build_object(
      'item', to_jsonb(v_existing_item),
      'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date),
      'idempotent_replay', true
    );
  end if;

  -- The day lock serializes normal create ordering. A global UUID collision on
  -- another day/user remains protected by the table primary key without taking
  -- an item lock that could invert the replace path's lock order.
  select i.* into v_item_id_conflict
  from public.food_log_items i
  where i.id = p_item_id;

  if found then
    raise exception 'provider item UUID is unavailable'
      using errcode = '23505';
  end if;

  select * into v_target
  from public.nutrition_targets t
  where t.user_id = v_user_id
    and t.target_context = 'daily'
    and t.status in ('active', 'superseded')
    and t.effective_from <= p_log_date
    and (t.effective_to is null or t.effective_to >= p_log_date)
  order by (t.status = 'active') desc, t.effective_from desc, t.created_at desc
  limit 1;

  perform pg_catalog.set_config(
    'fmz.phase4_provider_snapshot_user_id',
    v_user_id::text,
    true
  );

  if v_saved_timezone is null then
    insert into public.nutrition_preferences(user_id, timezone_name)
    values (v_user_id, v_timezone)
    on conflict (user_id) do nothing;
  end if;

  insert into public.food_logs(
    id, user_id, log_date, timezone_name, timezone_offset_minutes,
    target_id, target_energy_kcal_snapshot, target_protein_grams_snapshot,
    target_carbohydrate_grams_snapshot, target_fat_grams_snapshot,
    target_fiber_grams_snapshot, status, source, metadata
  )
  values (
    pg_catalog.gen_random_uuid(), v_user_id, p_log_date, v_timezone,
    p_timezone_offset_minutes, v_target.id, v_target.energy_kcal,
    v_target.protein_grams, v_target.carbohydrate_grams, v_target.fat_grams,
    v_target.fiber_grams, 'active', 'phase4_member',
    jsonb_build_object('created_by', 'fmz_phase4_log_provider_food_item')
  )
  on conflict (user_id, log_date) do nothing;

  select * into v_log
  from public.food_logs l
  where l.user_id = v_user_id
    and l.log_date = p_log_date
    and l.status = 'active'
  for update;

  if not found then
    raise exception 'active Nutrition day log unavailable'
      using errcode = '23514';
  end if;

  select coalesce(max(i.sort_order), -1) + 1
  into v_sort_order
  from public.food_log_items i
  where i.user_id = v_user_id
    and i.food_log_id = v_log.id
    and i.meal_moment = p_meal_moment;

  if v_sort_order > 10000 then
    raise exception 'destination meal order is full'
      using errcode = '22023';
  end if;

  v_factor := p_consumed_quantity / 100;
  v_metadata := jsonb_build_object(
    'calculation_version', 'phase4_provider_snapshot_v1',
    'operation', 'provider_log',
    'source_type', 'transient_provider_snapshot',
    'candidate_id', v_candidate_id,
    'mapping_version', 'phase4_usda_v1',
    'provider_data_type', v_provider_data_type,
    'reference_basis', 'per_100_g',
    'retrieved_at', v_retrieved_at,
    'source_updated_at', v_source_updated_at,
    'provider_request', v_request_payload
  );

  insert into public.food_log_items(
    id, user_id, food_log_id, food_id, food_portion_id, meal_moment,
    sort_order, consumed_quantity, consumed_unit, food_name_snapshot,
    brand_snapshot, reference_amount_snapshot, reference_unit_snapshot,
    portion_label_snapshot, portion_equivalent_amount_snapshot,
    portion_equivalent_unit_snapshot, density_g_per_ml_snapshot,
    calculation_basis, energy_kcal_snapshot, protein_grams_snapshot,
    carbohydrate_grams_snapshot, fat_grams_snapshot, fiber_grams_snapshot,
    source_provider_snapshot, provider_food_id_snapshot,
    source_version_snapshot, provenance_snapshot, notes, status, request_id,
    consumed_at, metadata
  )
  values (
    p_item_id, v_user_id, v_log.id, null, null, p_meal_moment,
    v_sort_order, p_consumed_quantity, 'g', v_food_name, v_brand,
    100, 'g', null, null, null, null, 'direct_reference',
    round(v_kcal * v_factor, 3), round(v_protein * v_factor, 3),
    round(v_carbohydrates * v_factor, 3), round(v_fat * v_factor, 3),
    case when v_fiber is null then null else round(v_fiber * v_factor, 3) end,
    'usda_fdc', v_provider_food_id, v_source_version, v_provenance,
    v_normalized_notes, 'active', p_request_id, p_consumed_at, v_metadata
  )
  returning * into v_item;

  return jsonb_build_object(
    'item', to_jsonb(v_item),
    'day', public.fmz_phase4_day_payload(v_user_id, p_log_date),
    'idempotent_replay', false
  );
end;
$$;

create or replace function public.fmz_phase4_replace_provider_food_log_item(
  p_user_id uuid,
  p_original_item_id uuid,
  p_replacement_item_id uuid,
  p_replacement_request_id uuid,
  p_expected_original_updated_at timestamptz,
  p_meal_moment text,
  p_consumed_quantity numeric,
  p_consumed_unit text,
  p_notes text,
  p_candidate jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := p_user_id;
  v_original public.food_log_items%rowtype;
  v_replacement public.food_log_items%rowtype;
  v_item_id_conflict public.food_log_items%rowtype;
  v_log public.food_logs%rowtype;
  v_timezone text;
  v_today date;
  v_has_full_access boolean;
  v_sort_order integer;
  v_normalized_notes text := nullif(btrim(p_notes), '');
  v_candidate_id uuid;
  v_provider_food_id text;
  v_food_name text;
  v_brand text;
  v_provider_data_type text;
  v_source_version text;
  v_retrieved_at timestamptz;
  v_source_updated_at timestamptz;
  v_kcal numeric;
  v_protein numeric;
  v_carbohydrates numeric;
  v_fat numeric;
  v_fiber numeric;
  v_factor numeric;
  v_provenance jsonb;
  v_request_payload jsonb;
  v_metadata jsonb;
begin
  if v_user_id is null
     or p_original_item_id is null
     or p_replacement_item_id is null
     or p_replacement_request_id is null
     or p_expected_original_updated_at is null then
    raise exception 'trusted user, original item, replacement item, request, and expected timestamp required'
      using errcode = '22023';
  end if;

  if p_original_item_id = p_replacement_item_id then
    raise exception 'replacement item UUID must differ from original item UUID'
      using errcode = '22023';
  end if;

  if p_consumed_unit is distinct from 'g' then
    raise exception 'provider food logging supports grams only'
      using errcode = '22023';
  end if;

  if p_consumed_quantity is null
     or p_consumed_quantity::text in ('NaN', 'Infinity', '-Infinity')
     or p_consumed_quantity <= 0
     or p_consumed_quantity > 100000 then
    raise exception 'consumed grams must be positive and within supported bounds'
      using errcode = '22023';
  end if;

  if p_meal_moment not in ('breakfast', 'lunch', 'dinner', 'snacks') then
    raise exception 'unsupported meal moment'
      using errcode = '22023';
  end if;

  if v_normalized_notes is not null and char_length(v_normalized_notes) > 1000 then
    raise exception 'notes exceed supported length'
      using errcode = '22023';
  end if;

  if jsonb_typeof(p_candidate) is distinct from 'object' then
    raise exception 'trusted provider candidate payload must be an object'
      using errcode = '22023';
  end if;

  if (select count(*) from pg_catalog.jsonb_object_keys(p_candidate)) <> 18
     or p_candidate - array[
       'provider', 'provider_food_id', 'candidate_id', 'mapping_version',
       'provider_data_type', 'food_name', 'brand', 'reference_amount',
       'reference_unit', 'energy_kcal_per_100g', 'protein_grams_per_100g',
       'carbohydrate_grams_per_100g', 'fat_grams_per_100g',
       'fiber_grams_per_100g', 'source_version', 'retrieved_at',
       'source_updated_at', 'provenance'
     ]::text[] <> '{}'::jsonb then
    raise exception 'trusted provider candidate payload has unsupported fields'
      using errcode = '22023';
  end if;

  if jsonb_typeof(p_candidate -> 'provider') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'candidate_id') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'provider_food_id') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'mapping_version') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'provider_data_type') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'food_name') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'brand') not in ('string', 'null')
     or jsonb_typeof(p_candidate -> 'reference_amount') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'reference_unit') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'energy_kcal_per_100g') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'protein_grams_per_100g') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'carbohydrate_grams_per_100g') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'fat_grams_per_100g') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'fiber_grams_per_100g') not in ('number', 'null')
     or jsonb_typeof(p_candidate -> 'source_version') not in ('string', 'null')
     or jsonb_typeof(p_candidate -> 'retrieved_at') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'source_updated_at') not in ('string', 'null')
     or jsonb_typeof(p_candidate -> 'provenance') is distinct from 'object' then
    raise exception 'trusted provider candidate payload is malformed'
      using errcode = '22023';
  end if;

  begin
    v_candidate_id := (p_candidate ->> 'candidate_id')::uuid;
    v_kcal := (p_candidate ->> 'energy_kcal_per_100g')::numeric;
    v_protein := (p_candidate ->> 'protein_grams_per_100g')::numeric;
    v_carbohydrates := (p_candidate ->> 'carbohydrate_grams_per_100g')::numeric;
    v_fat := (p_candidate ->> 'fat_grams_per_100g')::numeric;
    v_fiber := case
      when p_candidate -> 'fiber_grams_per_100g' is null
        or p_candidate -> 'fiber_grams_per_100g' = 'null'::jsonb then null
      else (p_candidate ->> 'fiber_grams_per_100g')::numeric
    end;
    v_retrieved_at := (p_candidate ->> 'retrieved_at')::timestamptz;
    v_source_updated_at := case
      when p_candidate -> 'source_updated_at' is null
        or p_candidate -> 'source_updated_at' = 'null'::jsonb then null
      else (p_candidate ->> 'source_updated_at')::timestamptz
    end;
  exception
    when invalid_text_representation or datetime_field_overflow then
      raise exception 'trusted provider candidate payload has invalid typed values'
        using errcode = '22023';
  end;

  v_provider_food_id := btrim(p_candidate ->> 'provider_food_id');
  v_food_name := btrim(p_candidate ->> 'food_name');
  v_brand := nullif(btrim(p_candidate ->> 'brand'), '');
  v_provider_data_type := p_candidate ->> 'provider_data_type';
  v_source_version := nullif(btrim(p_candidate ->> 'source_version'), '');
  v_provenance := p_candidate -> 'provenance';

  if p_candidate ->> 'provider' is distinct from 'usda_fdc'
     or v_provider_food_id !~ '^[1-9][0-9]{0,15}$'
     or p_candidate ->> 'mapping_version' is distinct from 'phase4_usda_v1'
     or v_provider_data_type is null
     or v_provider_data_type not in ('Foundation', 'Survey (FNDDS)', 'SR Legacy')
     or p_candidate ->> 'reference_amount' is distinct from '100'
     or p_candidate ->> 'reference_unit' is distinct from 'g'
     or char_length(v_food_name) not between 1 and 180
     or (v_brand is not null and char_length(v_brand) > 120)
     or (v_source_version is not null and char_length(v_source_version) > 120)
     or v_retrieved_at is null
     or v_retrieved_at > now() + interval '5 minutes'
     or (v_source_updated_at is not null and v_source_updated_at > now() + interval '5 minutes')
     or v_kcal::text in ('NaN', 'Infinity', '-Infinity')
     or v_kcal < 0 or v_kcal > 1500
     or v_protein::text in ('NaN', 'Infinity', '-Infinity')
     or v_protein < 0 or v_protein > 100
     or v_carbohydrates::text in ('NaN', 'Infinity', '-Infinity')
     or v_carbohydrates < 0 or v_carbohydrates > 100
     or v_fat::text in ('NaN', 'Infinity', '-Infinity')
     or v_fat < 0 or v_fat > 100
     or (v_fiber is not null and (
       v_fiber::text in ('NaN', 'Infinity', '-Infinity')
       or v_fiber < 0 or v_fiber > 100
     ))
     or v_provenance ->> 'provider' is distinct from 'usda_fdc'
     or v_provenance ->> 'provider_food_id' is distinct from v_provider_food_id
     or v_provenance ->> 'candidate_id' is distinct from v_candidate_id::text
     or v_provenance ->> 'mapping_version' is distinct from 'phase4_usda_v1'
     or v_provenance ->> 'provider_data_type' is distinct from v_provider_data_type
     or v_provenance ->> 'reference_basis' is distinct from 'per_100_g'
     or v_provenance ->> 'retrieved_at' is distinct from p_candidate ->> 'retrieved_at'
     or v_provenance ->> 'source_version' is distinct from p_candidate ->> 'source_version'
     or v_provenance ->> 'source_updated_at'
        is distinct from p_candidate ->> 'source_updated_at'
     or v_provenance -> 'derivation' is null
     or v_provenance -> 'attribution' is null then
    raise exception 'trusted USDA candidate failed provider snapshot validation'
      using errcode = '22023';
  end if;

  v_request_payload := jsonb_build_object(
    'original_item_id', p_original_item_id,
    'replacement_item_id', p_replacement_item_id,
    'expected_original_updated_at', p_expected_original_updated_at,
    'meal_moment', p_meal_moment,
    'consumed_quantity', p_consumed_quantity,
    'consumed_unit', 'g',
    'notes', v_normalized_notes,
    'candidate', p_candidate
  );

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_request:' || v_user_id::text || ':' ||
      p_replacement_request_id::text,
      0
    )
  );

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_item_request:' || v_user_id::text || ':' ||
      p_original_item_id::text,
      0
    )
  );

  select i.* into v_original
  from public.food_log_items i
  where i.id = p_original_item_id
    and i.user_id = v_user_id
  for update;

  if not found then
    raise exception 'provider food log item not found'
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
       or v_replacement.food_id is not null
       or v_replacement.food_log_id is distinct from v_original.food_log_id
       or v_replacement.metadata ->> 'operation' is distinct from 'provider_replace'
       or v_replacement.metadata ->> 'replaces_item_id'
          is distinct from p_original_item_id::text
       or v_replacement.metadata -> 'provider_replacement_request'
          is distinct from v_request_payload then
      raise exception 'provider replacement request UUID was already used with a different payload'
        using errcode = '23505';
    end if;

    if v_original.status is distinct from 'archived' then
      raise exception 'provider replacement replay found incomplete archive state'
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

  if v_original.food_id is not null
     or v_original.food_portion_id is not null
     or v_original.source_provider_snapshot is distinct from 'usda_fdc'
     or v_original.metadata ->> 'operation' is null
     or v_original.metadata ->> 'operation' not in ('provider_log', 'provider_replace') then
    raise exception 'provider replacement accepts provider snapshot items only'
      using errcode = '42501';
  end if;

  if v_original.status is distinct from 'active'
     or v_original.updated_at is distinct from p_expected_original_updated_at then
    raise exception 'provider food log item changed; refresh before replacing'
      using errcode = '40001';
  end if;

  select i.* into v_item_id_conflict
  from public.food_log_items i
  where i.id = p_replacement_item_id;

  if found then
    raise exception 'replacement item UUID is unavailable'
      using errcode = '23505';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_item_request:' || v_user_id::text || ':' ||
      p_replacement_item_id::text,
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

  perform pg_catalog.set_config(
    'fmz.phase4_provider_snapshot_user_id',
    v_user_id::text,
    true
  );

  v_factor := p_consumed_quantity / 100;
  v_metadata := jsonb_build_object(
    'calculation_version', 'phase4_provider_snapshot_v1',
    'operation', 'provider_replace',
    'source_type', 'transient_provider_snapshot',
    'replaces_item_id', p_original_item_id,
    'candidate_id', v_candidate_id,
    'mapping_version', 'phase4_usda_v1',
    'provider_data_type', v_provider_data_type,
    'reference_basis', 'per_100_g',
    'retrieved_at', v_retrieved_at,
    'source_updated_at', v_source_updated_at,
    'provider_replacement_request', v_request_payload
  );

  insert into public.food_log_items(
    id, user_id, food_log_id, food_id, food_portion_id, meal_moment,
    sort_order, consumed_quantity, consumed_unit, food_name_snapshot,
    brand_snapshot, reference_amount_snapshot, reference_unit_snapshot,
    portion_label_snapshot, portion_equivalent_amount_snapshot,
    portion_equivalent_unit_snapshot, density_g_per_ml_snapshot,
    calculation_basis, energy_kcal_snapshot, protein_grams_snapshot,
    carbohydrate_grams_snapshot, fat_grams_snapshot, fiber_grams_snapshot,
    source_provider_snapshot, provider_food_id_snapshot,
    source_version_snapshot, provenance_snapshot, notes, status, request_id,
    consumed_at, metadata
  )
  values (
    p_replacement_item_id, v_user_id, v_original.food_log_id, null, null,
    p_meal_moment, v_sort_order, p_consumed_quantity, 'g', v_food_name,
    v_brand, 100, 'g', null, null, null, null, 'direct_reference',
    round(v_kcal * v_factor, 3), round(v_protein * v_factor, 3),
    round(v_carbohydrates * v_factor, 3), round(v_fat * v_factor, 3),
    case when v_fiber is null then null else round(v_fiber * v_factor, 3) end,
    'usda_fdc', v_provider_food_id, v_source_version, v_provenance,
    v_normalized_notes, 'active', p_replacement_request_id,
    v_original.consumed_at, v_metadata
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
    raise exception 'provider food log item changed; atomic replacement rolled back'
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

revoke all on function public.fmz_phase4_enforce_food_log_owner() from public;
revoke all on function public.fmz_phase4_enforce_food_log_owner() from anon;
revoke all on function public.fmz_phase4_enforce_food_log_owner() from authenticated;
revoke all on function public.fmz_phase4_enforce_food_log_owner() from service_role;

revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from public;
revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from anon;
revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from authenticated;
revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from service_role;

revoke all on function public.fmz_phase4_log_provider_food_item(
  uuid, uuid, uuid, date, text, smallint, text, numeric, text, text,
  timestamptz, jsonb
) from public;
revoke all on function public.fmz_phase4_log_provider_food_item(
  uuid, uuid, uuid, date, text, smallint, text, numeric, text, text,
  timestamptz, jsonb
) from anon;
revoke all on function public.fmz_phase4_log_provider_food_item(
  uuid, uuid, uuid, date, text, smallint, text, numeric, text, text,
  timestamptz, jsonb
) from authenticated;
revoke all on function public.fmz_phase4_log_provider_food_item(
  uuid, uuid, uuid, date, text, smallint, text, numeric, text, text,
  timestamptz, jsonb
) from service_role;
grant execute on function public.fmz_phase4_log_provider_food_item(
  uuid, uuid, uuid, date, text, smallint, text, numeric, text, text,
  timestamptz, jsonb
) to service_role;

revoke all on function public.fmz_phase4_replace_provider_food_log_item(
  uuid, uuid, uuid, uuid, timestamptz, text, numeric, text, text, jsonb
) from public;
revoke all on function public.fmz_phase4_replace_provider_food_log_item(
  uuid, uuid, uuid, uuid, timestamptz, text, numeric, text, text, jsonb
) from anon;
revoke all on function public.fmz_phase4_replace_provider_food_log_item(
  uuid, uuid, uuid, uuid, timestamptz, text, numeric, text, text, jsonb
) from authenticated;
revoke all on function public.fmz_phase4_replace_provider_food_log_item(
  uuid, uuid, uuid, uuid, timestamptz, text, numeric, text, text, jsonb
) from service_role;
grant execute on function public.fmz_phase4_replace_provider_food_log_item(
  uuid, uuid, uuid, uuid, timestamptz, text, numeric, text, text, jsonb
) to service_role;

commit;
