-- FitMetZorge Phase 4 Nutrition Engine - Slice 4D historical provider resolver
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Additive service-role-only read RPC. No data writes, canonical promotion,
-- table changes, browser grants, trainer access or production changes.

begin;

create or replace function public.fmz_phase4_resolve_provider_food_log_item(
  p_user_id uuid,
  p_original_item_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_item public.food_log_items%rowtype;
  v_candidate_id uuid;
  v_provider_food_id text;
  v_provider_data_type text;
  v_metadata jsonb;
  v_provenance jsonb;
  v_retrieved_at timestamptz;
  v_source_updated_at timestamptz;
  v_metadata_retrieved_at timestamptz;
  v_metadata_source_updated_at timestamptz;
begin
  if p_user_id is null or p_original_item_id is null then
    raise exception 'trusted user and original provider item are required'
      using errcode = '22023';
  end if;

  select i.*
  into v_item
  from public.food_log_items i
  join public.food_logs l
    on l.id = i.food_log_id
   and l.user_id = p_user_id
  where i.id = p_original_item_id
    and i.user_id = p_user_id
    and i.status = 'active'
    and l.status = 'active';

  if not found then
    raise exception 'active provider food log item is unavailable for this user'
      using errcode = '42501';
  end if;

  v_metadata := v_item.metadata;
  v_provenance := v_item.provenance_snapshot;
  v_provider_food_id := nullif(btrim(v_item.provider_food_id_snapshot), '');
  v_provider_data_type := v_metadata ->> 'provider_data_type';

  if v_item.food_id is not null
     or v_item.food_portion_id is not null
     or v_item.source_provider_snapshot is distinct from 'usda_fdc'
     or v_provider_food_id is null
     or v_provider_food_id !~ '^[1-9][0-9]{0,15}$'
     or v_item.reference_amount_snapshot is distinct from 100::numeric
     or v_item.reference_unit_snapshot is distinct from 'g'
     or v_item.consumed_unit is distinct from 'g'
     or v_item.calculation_basis is distinct from 'direct_reference'
     or v_item.portion_label_snapshot is not null
     or v_item.portion_equivalent_amount_snapshot is not null
     or v_item.portion_equivalent_unit_snapshot is not null
     or v_item.density_g_per_ml_snapshot is not null
     or jsonb_typeof(v_metadata) is distinct from 'object'
     or jsonb_typeof(v_provenance) is distinct from 'object'
     or v_metadata ->> 'calculation_version' is distinct from 'phase4_provider_snapshot_v1'
     or v_metadata ->> 'source_type' is distinct from 'transient_provider_snapshot'
     or v_metadata ->> 'operation' is null
     or v_metadata ->> 'operation' not in ('provider_log', 'provider_replace')
     or v_metadata ->> 'mapping_version' is distinct from 'phase4_usda_v1'
     or v_metadata ->> 'reference_basis' is distinct from 'per_100_g'
     or v_provider_data_type is null
     or v_provider_data_type not in ('Foundation', 'Survey (FNDDS)', 'SR Legacy')
     or v_provenance ->> 'provider' is distinct from 'usda_fdc'
     or v_provenance ->> 'provider_food_id' is distinct from v_provider_food_id
     or v_provenance ->> 'candidate_id' is distinct from v_metadata ->> 'candidate_id'
     or v_provenance ->> 'mapping_version' is distinct from 'phase4_usda_v1'
     or v_provenance ->> 'provider_data_type' is distinct from v_provider_data_type
     or v_provenance ->> 'reference_basis' is distinct from 'per_100_g'
     or jsonb_typeof(v_provenance -> 'derivation') is distinct from 'object'
     or jsonb_typeof(v_provenance -> 'attribution') is distinct from 'object'
     or v_provenance #>> '{derivation,reference_basis}' is distinct from 'per_100_g'
     or v_provenance #>> '{derivation,energy}' is null
     or v_provenance #>> '{derivation,energy}' not in (
       '2048_kcal', '2047_kcal', '1008_kcal', '1062_kj_converted'
     )
     or v_provenance #>> '{attribution,label}' is distinct from 'USDA FoodData Central'
     or v_provenance #>> '{attribution,license}' is distinct from 'CC0 1.0'
     or v_provenance #>> '{attribution,url}' is distinct from 'https://fdc.nal.usda.gov/'
     or nullif(btrim(v_item.food_name_snapshot), '') is null
     or v_item.energy_kcal_snapshot::text in ('NaN', 'Infinity', '-Infinity')
     or v_item.protein_grams_snapshot::text in ('NaN', 'Infinity', '-Infinity')
     or v_item.carbohydrate_grams_snapshot::text in ('NaN', 'Infinity', '-Infinity')
     or v_item.fat_grams_snapshot::text in ('NaN', 'Infinity', '-Infinity')
     or v_item.energy_kcal_snapshot < 0
     or v_item.protein_grams_snapshot < 0
     or v_item.carbohydrate_grams_snapshot < 0
     or v_item.fat_grams_snapshot < 0
     or (
       v_item.fiber_grams_snapshot is not null
       and (
         v_item.fiber_grams_snapshot::text in ('NaN', 'Infinity', '-Infinity')
         or v_item.fiber_grams_snapshot < 0
       )
     ) then
    raise exception 'historical provider snapshot failed trusted identity validation'
      using errcode = '22023';
  end if;

  begin
    v_candidate_id := (v_metadata ->> 'candidate_id')::uuid;
    v_retrieved_at := (v_provenance ->> 'retrieved_at')::timestamptz;
    v_metadata_retrieved_at := (v_metadata ->> 'retrieved_at')::timestamptz;
    if nullif(v_provenance ->> 'source_updated_at', '') is not null then
      v_source_updated_at := (v_provenance ->> 'source_updated_at')::timestamptz;
    end if;
    if nullif(v_metadata ->> 'source_updated_at', '') is not null then
      v_metadata_source_updated_at := (v_metadata ->> 'source_updated_at')::timestamptz;
    end if;
  exception
    when invalid_text_representation or datetime_field_overflow then
      raise exception 'historical provider snapshot contains invalid typed identity data'
        using errcode = '22023';
  end;

  if v_candidate_id is null
     or substring(v_candidate_id::text, 15, 1) <> '5'
     or v_retrieved_at is null
     or v_metadata_retrieved_at is distinct from v_retrieved_at
     or v_metadata_source_updated_at is distinct from v_source_updated_at
     or coalesce(v_item.source_version_snapshot, '')
        is distinct from coalesce(v_provenance ->> 'source_version', '')
     or v_retrieved_at > now() + interval '5 minutes'
     or (v_source_updated_at is not null and v_source_updated_at > now() + interval '5 minutes') then
    raise exception 'historical provider snapshot contains invalid trusted identity data'
      using errcode = '22023';
  end if;

  return jsonb_build_object(
    'provider', 'usda_fdc',
    'provider_food_id', v_provider_food_id,
    'candidate_id', v_candidate_id,
    'mapping_version', 'phase4_usda_v1',
    'provider_data_type', v_provider_data_type
  );
end;
$$;

revoke all on function public.fmz_phase4_resolve_provider_food_log_item(uuid, uuid)
  from public;
revoke all on function public.fmz_phase4_resolve_provider_food_log_item(uuid, uuid)
  from anon;
revoke all on function public.fmz_phase4_resolve_provider_food_log_item(uuid, uuid)
  from authenticated;
revoke all on function public.fmz_phase4_resolve_provider_food_log_item(uuid, uuid)
  from service_role;
grant execute on function public.fmz_phase4_resolve_provider_food_log_item(uuid, uuid)
  to service_role;

commit;
