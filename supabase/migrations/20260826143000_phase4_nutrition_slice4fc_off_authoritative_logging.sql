-- FitMetZorge Phase 4 Nutrition Engine - Package 4F-C OFF authoritative logging
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Additive RPC/trigger compatibility/ACL only. No catalog mutation, provider call,
-- trainer access, legacy mutation, entitlement change or production reference.

begin;

do $$
begin
  if to_regclass('public.nutrition_off_catalog_releases') is null
     or to_regclass('public.nutrition_off_products') is null
     or to_regclass('public.food_logs') is null
     or to_regclass('public.food_log_items') is null then
    raise exception 'Phase 4 OFF and Nutrition foundations must exist before 4F-C';
  end if;

  if to_regprocedure('public.fmz_phase4_day_payload(uuid,date)') is null
     or to_regprocedure('public.fmz_phase4_has_full_nutrition_access(uuid)') is null
     or to_regprocedure('public.fmz_phase4_archive_food_log_item(uuid,timestamp with time zone)') is null
     or to_regprocedure('public.fmz_phase4_log_provider_food_item(uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb)') is null
     or to_regprocedure('public.fmz_phase4_replace_provider_food_log_item(uuid,uuid,uuid,uuid,timestamp with time zone,text,numeric,text,text,jsonb)') is null
     or to_regprocedure('public.fmz_phase4_replace_food_log_item(uuid,uuid,uuid,timestamp with time zone,text,uuid,uuid,numeric,text,text)') is null then
    raise exception 'Frozen Phase 4 logging contracts must exist before 4F-C';
  end if;
end $$;

-- This resolver is deliberately internal. Browser input is only an OFF product
-- UUID; all nutrition, identity, quality and ODbL provenance come from the live
-- server-side catalog row and its imported release.
create or replace function public.fmz_phase4_resolve_off_food_snapshot(
  p_off_product_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_snapshot jsonb;
begin
  if p_off_product_id is null then
    raise exception 'OFF product UUID required'
      using errcode = '22023';
  end if;

  select jsonb_build_object(
    'off_product_id', p.id,
    'release_id', p.release_id,
    'provider', p.source_provider,
    'provider_food_id', p.normalized_gtin14,
    'food_name', p.product_name,
    'display_name_nl', p.product_name_nl,
    'brand', p.brand,
    'reference_amount', 100,
    'reference_unit', case when p.nutrition_basis = 'per_100_ml' then 'ml' else 'g' end,
    'reference_basis', p.nutrition_basis,
    'energy_kcal_reference', p.energy_kcal_100,
    'protein_grams_reference', p.protein_grams_100,
    'carbohydrate_grams_reference', p.carbohydrate_grams_100,
    'fat_grams_reference', p.fat_grams_100,
    'fiber_grams_reference', p.fiber_grams_100,
    'source_version', p.off_revision,
    'mapping_version', r.mapping_version,
    'provenance', jsonb_build_object(
      'provider', p.source_provider,
      'provider_food_id', p.normalized_gtin14,
      'off_code', p.off_code,
      'barcode_original', p.barcode_original,
      'candidate_id', p.id,
      'release_id', p.release_id,
      'mapping_version', r.mapping_version,
      'reference_basis', p.nutrition_basis,
      'source_revision', p.off_revision,
      'source_checksum', p.source_checksum,
      'source_updated_at', p.source_updated_at,
      'license_code', p.license_code,
      'license_url', p.license_url,
      'attribution_text', p.attribution_text,
      'derivation', jsonb_build_object(
        'calculation', 'consumed_quantity / 100 * catalog_reference',
        'catalog_reference_amount', 100,
        'catalog_reference_unit', case when p.nutrition_basis = 'per_100_ml' then 'ml' else 'g' end
      ),
      'attribution', jsonb_build_object(
        'source', 'Open Food Facts',
        'text', p.attribution_text,
        'license_code', p.license_code,
        'license_url', p.license_url
      ),
      'catalog_provenance', p.provenance
    )
  )
  into v_snapshot
  from public.nutrition_off_products p
  join public.nutrition_off_catalog_releases r on r.id = p.release_id
  where p.id = p_off_product_id
    and p.source_provider = 'open_food_facts'
    and p.provider_identity_name = 'open_food_facts:' || p.normalized_gtin14
    and p.lifecycle_status = 'active'
    and p.quality_status in ('complete', 'reviewed')
    and p.nutrition_basis in ('per_100_g', 'per_100_ml')
    and p.energy_kcal_100 is not null
    and p.protein_grams_100 is not null
    and p.carbohydrate_grams_100 is not null
    and p.fat_grams_100 is not null
    and char_length(p.off_revision) between 1 and 120
    and p.license_code = 'ODbL-1.0'
    and r.source_provider = 'open_food_facts'
    and r.status = 'imported'
    and r.imported_at is not null
    and r.license_code = 'ODbL-1.0';

  if v_snapshot is null then
    raise exception 'active loggable OFF product not found'
      using errcode = '42501';
  end if;

  return v_snapshot;
end;
$$;

-- Preserve the frozen USDA branch byte-for-byte in behavior and add one
-- separately gated OFF branch. Historical snapshots remain immutable.
create or replace function public.fmz_phase4_enforce_food_log_item_owner()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_authenticated_user_id uuid := auth.uid();
  v_internal_user_id uuid;
  v_off_internal_user_id uuid;
  v_user_id uuid;
begin
  begin
    v_internal_user_id := nullif(
      current_setting('fmz.phase4_provider_snapshot_user_id', true),
      ''
    )::uuid;
    v_off_internal_user_id := nullif(
      current_setting('fmz.phase4_off_snapshot_user_id', true),
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
    if new.source_provider_snapshot = 'usda_fdc' then
      if v_authenticated_user_id is not null
         or v_internal_user_id is distinct from new.user_id
         or new.food_portion_id is not null
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

    if new.source_provider_snapshot = 'open_food_facts' then
      if v_authenticated_user_id is distinct from new.user_id
         or v_off_internal_user_id is distinct from new.user_id
         or new.food_portion_id is not null
         or new.provider_food_id_snapshot is null
         or new.provider_food_id_snapshot !~ '^[0-9]{14}$'
         or new.reference_amount_snapshot is distinct from 100::numeric
         or new.reference_unit_snapshot not in ('g', 'ml')
         or new.consumed_unit is distinct from new.reference_unit_snapshot
         or new.calculation_basis is distinct from 'direct_reference'
         or new.portion_label_snapshot is not null
         or new.portion_equivalent_amount_snapshot is not null
         or new.portion_equivalent_unit_snapshot is not null
         or new.density_g_per_ml_snapshot is not null
         or new.metadata ->> 'operation' not in ('off_log', 'off_replace')
         or new.metadata ->> 'off_product_id' is null
         or new.metadata ->> 'candidate_id'
            is distinct from new.metadata ->> 'off_product_id'
         or new.metadata ->> 'mapping_version' is null
         or new.metadata ->> 'reference_basis'
            is distinct from case when new.reference_unit_snapshot = 'ml' then 'per_100_ml' else 'per_100_g' end
         or new.provenance_snapshot ->> 'provider' is distinct from 'open_food_facts'
         or new.provenance_snapshot ->> 'provider_food_id'
            is distinct from new.provider_food_id_snapshot
         or new.provenance_snapshot ->> 'candidate_id'
            is distinct from new.metadata ->> 'off_product_id'
         or new.provenance_snapshot ->> 'mapping_version'
            is distinct from new.metadata ->> 'mapping_version'
         or new.provenance_snapshot ->> 'reference_basis'
            is distinct from new.metadata ->> 'reference_basis'
         or new.provenance_snapshot ->> 'source_revision'
            is distinct from new.source_version_snapshot
         or new.provenance_snapshot ->> 'license_code' is distinct from 'ODbL-1.0'
         or new.provenance_snapshot ->> 'license_url'
            is distinct from 'https://opendatacommons.org/licenses/odbl/1-0/'
         or new.provenance_snapshot -> 'derivation' is null
         or new.provenance_snapshot -> 'attribution' is null then
        raise exception 'OFF snapshot item requires trusted authenticated catalog context'
          using errcode = '42501';
      end if;
      return new;
    end if;

    raise exception 'unsupported provider snapshot source'
      using errcode = '42501';
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

create or replace function public.fmz_phase4_log_off_food_item(
  p_item_id uuid,
  p_request_id uuid,
  p_log_date date,
  p_timezone_name text,
  p_timezone_offset_minutes smallint,
  p_meal_moment text,
  p_off_product_id uuid,
  p_consumed_quantity numeric,
  p_consumed_unit text,
  p_notes text,
  p_consumed_at timestamptz
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
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
  v_snapshot jsonb;
  v_reference_unit text;
  v_factor numeric;
  v_request_payload jsonb;
  v_metadata jsonb;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if p_item_id is null or p_request_id is null or p_log_date is null
     or p_off_product_id is null then
    raise exception 'stable item, request, log date, and OFF product UUID required'
      using errcode = '22023';
  end if;

  if p_meal_moment not in ('breakfast', 'lunch', 'dinner', 'snacks') then
    raise exception 'unsupported meal moment'
      using errcode = '22023';
  end if;

  if p_consumed_unit not in ('g', 'ml')
     or p_consumed_quantity is null
     or p_consumed_quantity::text in ('NaN', 'Infinity', '-Infinity')
     or p_consumed_quantity <= 0
     or p_consumed_quantity > 100000 then
    raise exception 'OFF quantity and unit are outside supported bounds'
      using errcode = '22023';
  end if;

  if v_normalized_notes is not null and char_length(v_normalized_notes) > 1000 then
    raise exception 'notes exceed supported length'
      using errcode = '22023';
  end if;

  if v_timezone is null
     or not exists (select 1 from pg_catalog.pg_timezone_names tz where tz.name = v_timezone) then
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
    extract(epoch from ((v_anchor at time zone v_timezone) - (v_anchor at time zone 'UTC'))) / 60
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
    'off_product_id', p_off_product_id,
    'consumed_quantity', p_consumed_quantity,
    'consumed_unit', p_consumed_unit,
    'notes', v_normalized_notes,
    'consumed_at', p_consumed_at
  );

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_request:' || v_user_id::text || ':' || p_request_id::text,
      0
    )
  );

  select i.* into v_existing_item
  from public.food_log_items i
  where i.user_id = v_user_id and i.request_id = p_request_id;

  if found then
    if v_existing_item.id is distinct from p_item_id
       or v_existing_item.food_id is not null
       or v_existing_item.metadata ->> 'operation' is distinct from 'off_log'
       or v_existing_item.metadata -> 'off_request' is distinct from v_request_payload then
      raise exception 'OFF request UUID was already used with a different payload'
        using errcode = '23505';
    end if;

    select l.* into v_log from public.food_logs l
    where l.id = v_existing_item.food_log_id and l.user_id = v_user_id;

    return jsonb_build_object(
      'item', to_jsonb(v_existing_item),
      'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date),
      'idempotent_replay', true
    );
  end if;

  v_snapshot := public.fmz_phase4_resolve_off_food_snapshot(p_off_product_id);
  v_reference_unit := v_snapshot ->> 'reference_unit';
  if p_consumed_unit is distinct from v_reference_unit then
    raise exception 'OFF quantity unit must match the catalog nutrition basis'
      using errcode = '22023';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log:' || v_user_id::text || ':' || p_log_date::text,
      0
    )
  );

  select i.* into v_existing_item
  from public.food_log_items i
  where i.user_id = v_user_id and i.request_id = p_request_id;

  if found then
    if v_existing_item.id is distinct from p_item_id
       or v_existing_item.food_id is not null
       or v_existing_item.metadata ->> 'operation' is distinct from 'off_log'
       or v_existing_item.metadata -> 'off_request' is distinct from v_request_payload then
      raise exception 'OFF request UUID was already used with a different payload'
        using errcode = '23505';
    end if;

    select l.* into v_log from public.food_logs l
    where l.id = v_existing_item.food_log_id and l.user_id = v_user_id;

    return jsonb_build_object(
      'item', to_jsonb(v_existing_item),
      'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date),
      'idempotent_replay', true
    );
  end if;

  select i.* into v_item_id_conflict
  from public.food_log_items i where i.id = p_item_id;
  if found then
    raise exception 'OFF item UUID is unavailable'
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
  ) values (
    pg_catalog.gen_random_uuid(), v_user_id, p_log_date, v_timezone,
    p_timezone_offset_minutes, v_target.id, v_target.energy_kcal,
    v_target.protein_grams, v_target.carbohydrate_grams, v_target.fat_grams,
    v_target.fiber_grams, 'active', 'phase4_member',
    jsonb_build_object('created_by', 'fmz_phase4_log_off_food_item')
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

  select coalesce(max(i.sort_order), -1) + 1 into v_sort_order
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
    'calculation_version', 'phase4_off_snapshot_v1',
    'operation', 'off_log',
    'source_type', 'off_catalog_snapshot',
    'off_product_id', v_snapshot ->> 'off_product_id',
    'candidate_id', v_snapshot ->> 'off_product_id',
    'release_id', v_snapshot ->> 'release_id',
    'mapping_version', v_snapshot ->> 'mapping_version',
    'reference_basis', v_snapshot ->> 'reference_basis',
    'display_name_nl', v_snapshot ->> 'display_name_nl',
    'off_request', v_request_payload
  );

  perform pg_catalog.set_config(
    'fmz.phase4_off_snapshot_user_id',
    v_user_id::text,
    true
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
  ) values (
    p_item_id, v_user_id, v_log.id, null, null, p_meal_moment,
    v_sort_order, p_consumed_quantity, v_reference_unit,
    v_snapshot ->> 'food_name', nullif(v_snapshot ->> 'brand', ''),
    100, v_reference_unit, null, null, null, null, 'direct_reference',
    round((v_snapshot ->> 'energy_kcal_reference')::numeric * v_factor, 3),
    round((v_snapshot ->> 'protein_grams_reference')::numeric * v_factor, 3),
    round((v_snapshot ->> 'carbohydrate_grams_reference')::numeric * v_factor, 3),
    round((v_snapshot ->> 'fat_grams_reference')::numeric * v_factor, 3),
    case when v_snapshot -> 'fiber_grams_reference' = 'null'::jsonb then null
      else round((v_snapshot ->> 'fiber_grams_reference')::numeric * v_factor, 3) end,
    'open_food_facts', v_snapshot ->> 'provider_food_id',
    v_snapshot ->> 'source_version', v_snapshot -> 'provenance',
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

create or replace function public.fmz_phase4_replace_off_food_log_item(
  p_original_item_id uuid,
  p_replacement_item_id uuid,
  p_replacement_request_id uuid,
  p_expected_original_updated_at timestamptz,
  p_meal_moment text,
  p_off_product_id uuid,
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
  v_timezone text;
  v_today date;
  v_has_full_access boolean;
  v_sort_order integer;
  v_normalized_notes text := nullif(btrim(p_notes), '');
  v_snapshot jsonb;
  v_reference_unit text;
  v_factor numeric;
  v_request_payload jsonb;
  v_metadata jsonb;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if p_original_item_id is null or p_replacement_item_id is null
     or p_replacement_request_id is null or p_expected_original_updated_at is null
     or p_off_product_id is null then
    raise exception 'original, replacement, request, expected timestamp, and OFF product UUID required'
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

  if p_consumed_unit not in ('g', 'ml')
     or p_consumed_quantity is null
     or p_consumed_quantity::text in ('NaN', 'Infinity', '-Infinity')
     or p_consumed_quantity <= 0
     or p_consumed_quantity > 100000 then
    raise exception 'OFF quantity and unit are outside supported bounds'
      using errcode = '22023';
  end if;

  if v_normalized_notes is not null and char_length(v_normalized_notes) > 1000 then
    raise exception 'notes exceed supported length'
      using errcode = '22023';
  end if;

  v_request_payload := jsonb_build_object(
    'original_item_id', p_original_item_id,
    'replacement_item_id', p_replacement_item_id,
    'expected_original_updated_at', p_expected_original_updated_at,
    'meal_moment', p_meal_moment,
    'off_product_id', p_off_product_id,
    'consumed_quantity', p_consumed_quantity,
    'consumed_unit', p_consumed_unit,
    'notes', v_normalized_notes
  );

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_request:' || v_user_id::text || ':' || p_replacement_request_id::text,
      0
    )
  );
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_item_request:' || v_user_id::text || ':' || p_original_item_id::text,
      0
    )
  );

  select i.* into v_original
  from public.food_log_items i
  where i.id = p_original_item_id and i.user_id = v_user_id
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
  where i.user_id = v_user_id and i.request_id = p_replacement_request_id;

  if found then
    if v_replacement.id is distinct from p_replacement_item_id
       or v_replacement.food_id is not null
       or v_replacement.food_log_id is distinct from v_original.food_log_id
       or v_replacement.metadata ->> 'operation' is distinct from 'off_replace'
       or v_replacement.metadata ->> 'replaces_item_id' is distinct from p_original_item_id::text
       or v_replacement.metadata -> 'off_replacement_request' is distinct from v_request_payload then
      raise exception 'OFF replacement request UUID was already used with a different payload'
        using errcode = '23505';
    end if;

    if v_original.status is distinct from 'archived' then
      raise exception 'OFF replacement replay found incomplete archive state'
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

  if v_original.status is distinct from 'active'
     or v_original.updated_at is distinct from p_expected_original_updated_at then
    raise exception 'food log item changed; refresh before replacing'
      using errcode = '40001';
  end if;

  select i.* into v_item_id_conflict
  from public.food_log_items i where i.id = p_replacement_item_id;
  if found then
    raise exception 'replacement item UUID is unavailable'
      using errcode = '23505';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_item_request:' || v_user_id::text || ':' || p_replacement_item_id::text,
      0
    )
  );

  select i.* into v_item_id_conflict
  from public.food_log_items i where i.id = p_replacement_item_id;
  if found then
    raise exception 'replacement item UUID is unavailable'
      using errcode = '23505';
  end if;

  select coalesce(p.timezone_name, v_log.timezone_name, 'UTC') into v_timezone
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

  v_snapshot := public.fmz_phase4_resolve_off_food_snapshot(p_off_product_id);
  v_reference_unit := v_snapshot ->> 'reference_unit';
  if p_consumed_unit is distinct from v_reference_unit then
    raise exception 'OFF quantity unit must match the catalog nutrition basis'
      using errcode = '22023';
  end if;

  if p_meal_moment = v_original.meal_moment then
    v_sort_order := v_original.sort_order;
  else
    select coalesce(max(i.sort_order), -1) + 1 into v_sort_order
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

  v_factor := p_consumed_quantity / 100;
  v_metadata := jsonb_build_object(
    'calculation_version', 'phase4_off_snapshot_v1',
    'operation', 'off_replace',
    'source_type', 'off_catalog_snapshot',
    'replaces_item_id', p_original_item_id,
    'off_product_id', v_snapshot ->> 'off_product_id',
    'candidate_id', v_snapshot ->> 'off_product_id',
    'release_id', v_snapshot ->> 'release_id',
    'mapping_version', v_snapshot ->> 'mapping_version',
    'reference_basis', v_snapshot ->> 'reference_basis',
    'display_name_nl', v_snapshot ->> 'display_name_nl',
    'off_replacement_request', v_request_payload
  );

  perform pg_catalog.set_config(
    'fmz.phase4_off_snapshot_user_id',
    v_user_id::text,
    true
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
  ) values (
    p_replacement_item_id, v_user_id, v_original.food_log_id, null, null,
    p_meal_moment, v_sort_order, p_consumed_quantity, v_reference_unit,
    v_snapshot ->> 'food_name', nullif(v_snapshot ->> 'brand', ''),
    100, v_reference_unit, null, null, null, null, 'direct_reference',
    round((v_snapshot ->> 'energy_kcal_reference')::numeric * v_factor, 3),
    round((v_snapshot ->> 'protein_grams_reference')::numeric * v_factor, 3),
    round((v_snapshot ->> 'carbohydrate_grams_reference')::numeric * v_factor, 3),
    round((v_snapshot ->> 'fat_grams_reference')::numeric * v_factor, 3),
    case when v_snapshot -> 'fiber_grams_reference' = 'null'::jsonb then null
      else round((v_snapshot ->> 'fiber_grams_reference')::numeric * v_factor, 3) end,
    'open_food_facts', v_snapshot ->> 'provider_food_id',
    v_snapshot ->> 'source_version', v_snapshot -> 'provenance',
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

revoke all on function public.fmz_phase4_resolve_off_food_snapshot(uuid) from public;
revoke all on function public.fmz_phase4_resolve_off_food_snapshot(uuid) from anon;
revoke all on function public.fmz_phase4_resolve_off_food_snapshot(uuid) from authenticated;
revoke all on function public.fmz_phase4_resolve_off_food_snapshot(uuid) from service_role;

revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from public;
revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from anon;
revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from authenticated;
revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from service_role;

revoke all on function public.fmz_phase4_log_off_food_item(
  uuid, uuid, date, text, smallint, text, uuid, numeric, text, text, timestamptz
) from public;
revoke all on function public.fmz_phase4_log_off_food_item(
  uuid, uuid, date, text, smallint, text, uuid, numeric, text, text, timestamptz
) from anon;
revoke all on function public.fmz_phase4_log_off_food_item(
  uuid, uuid, date, text, smallint, text, uuid, numeric, text, text, timestamptz
) from authenticated;
revoke all on function public.fmz_phase4_log_off_food_item(
  uuid, uuid, date, text, smallint, text, uuid, numeric, text, text, timestamptz
) from service_role;
grant execute on function public.fmz_phase4_log_off_food_item(
  uuid, uuid, date, text, smallint, text, uuid, numeric, text, text, timestamptz
) to authenticated;

revoke all on function public.fmz_phase4_replace_off_food_log_item(
  uuid, uuid, uuid, timestamptz, text, uuid, numeric, text, text
) from public;
revoke all on function public.fmz_phase4_replace_off_food_log_item(
  uuid, uuid, uuid, timestamptz, text, uuid, numeric, text, text
) from anon;
revoke all on function public.fmz_phase4_replace_off_food_log_item(
  uuid, uuid, uuid, timestamptz, text, uuid, numeric, text, text
) from authenticated;
revoke all on function public.fmz_phase4_replace_off_food_log_item(
  uuid, uuid, uuid, timestamptz, text, uuid, numeric, text, text
) from service_role;
grant execute on function public.fmz_phase4_replace_off_food_log_item(
  uuid, uuid, uuid, timestamptz, text, uuid, numeric, text, text
) to authenticated;

commit;
