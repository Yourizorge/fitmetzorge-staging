-- FitMetZorge Phase 4 Nutrition Engine - Schema Slice 1
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Additive empty schema/security foundation. No seed, backfill, provider call,
-- legacy mutation, trainer access, AI execution, barcode integration or cleanup.
-- Production is forbidden.

begin;

create table if not exists public.nutrition_preferences (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  timezone_name text not null default 'UTC',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint nutrition_preferences_timezone_name_check
    check (char_length(btrim(timezone_name)) between 1 and 64)
);

create table if not exists public.foods (
  id uuid primary key,
  owner_user_id uuid references public.profiles(id) on delete cascade,
  catalog_scope text not null,
  canonical_slug text,
  name text not null,
  brand text,
  barcode text,
  source_provider text not null,
  provider_food_id text,
  source_version text,
  license_code text,
  provenance jsonb not null default '{}'::jsonb,
  quality_status text not null default 'pending',
  reference_amount numeric(12,3) not null,
  reference_unit text not null,
  reference_mass_grams numeric(12,3),
  reference_volume_ml numeric(12,3),
  density_g_per_ml numeric(12,6),
  energy_kcal numeric(12,3) not null,
  protein_grams numeric(12,3) not null,
  carbohydrate_grams numeric(12,3) not null,
  fat_grams numeric(12,3) not null,
  fiber_grams numeric(12,3),
  status text not null default 'active',
  source_updated_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint foods_catalog_scope_check
    check (catalog_scope in ('canonical', 'custom')),
  constraint foods_scope_owner_check
    check (
      (
        catalog_scope = 'canonical'
        and owner_user_id is null
        and canonical_slug is not null
        and source_provider <> 'custom_user'
      )
      or
      (
        catalog_scope = 'custom'
        and owner_user_id is not null
        and canonical_slug is null
        and source_provider = 'custom_user'
      )
    ),
  constraint foods_canonical_slug_check
    check (canonical_slug is null or char_length(btrim(canonical_slug)) between 1 and 180),
  constraint foods_name_check
    check (char_length(btrim(name)) between 1 and 240),
  constraint foods_brand_check
    check (brand is null or char_length(btrim(brand)) between 1 and 160),
  constraint foods_barcode_check
    check (barcode is null or barcode ~ '^[0-9]{4,32}$'),
  constraint foods_provider_food_id_check
    check (provider_food_id is null or char_length(provider_food_id) between 1 and 240),
  constraint foods_source_version_check
    check (source_version is null or char_length(source_version) between 1 and 120),
  constraint foods_license_code_check
    check (license_code is null or char_length(license_code) between 1 and 120),
  constraint foods_json_objects_check
    check (jsonb_typeof(provenance) = 'object' and jsonb_typeof(metadata) = 'object'),
  constraint foods_quality_status_check
    check (quality_status in ('pending', 'community', 'user_entered', 'reviewed', 'verified')),
  constraint foods_reference_unit_check
    check (reference_unit in ('g', 'ml', 'serving', 'piece')),
  constraint foods_reference_amount_check
    check (reference_amount > 0 and reference_amount <= 100000),
  constraint foods_reference_mass_check
    check (reference_mass_grams is null or (reference_mass_grams > 0 and reference_mass_grams <= 100000)),
  constraint foods_reference_volume_check
    check (reference_volume_ml is null or (reference_volume_ml > 0 and reference_volume_ml <= 100000)),
  constraint foods_density_check
    check (density_g_per_ml is null or (density_g_per_ml > 0 and density_g_per_ml <= 100)),
  constraint foods_energy_check
    check (energy_kcal >= 0 and energy_kcal <= 1000000),
  constraint foods_protein_check
    check (protein_grams >= 0 and protein_grams <= 100000),
  constraint foods_carbohydrate_check
    check (carbohydrate_grams >= 0 and carbohydrate_grams <= 100000),
  constraint foods_fat_check
    check (fat_grams >= 0 and fat_grams <= 100000),
  constraint foods_fiber_check
    check (fiber_grams is null or (fiber_grams >= 0 and fiber_grams <= 100000)),
  constraint foods_status_check
    check (status in ('active', 'archived')),
  constraint foods_archive_state_check
    check ((status = 'archived') = (archived_at is not null))
);

create table if not exists public.food_portions (
  id uuid primary key,
  food_id uuid not null references public.foods(id) on delete cascade,
  label text not null,
  amount numeric(12,3) not null default 1,
  unit text not null,
  equivalent_amount numeric(12,3) not null,
  equivalent_unit text not null,
  is_default boolean not null default false,
  sort_order integer not null default 0,
  status text not null default 'active',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint food_portions_label_check
    check (char_length(btrim(label)) between 1 and 120),
  constraint food_portions_amount_check
    check (amount > 0 and amount <= 100000),
  constraint food_portions_unit_check
    check (unit in ('serving', 'piece')),
  constraint food_portions_equivalent_amount_check
    check (equivalent_amount > 0 and equivalent_amount <= 100000),
  constraint food_portions_equivalent_unit_check
    check (equivalent_unit in ('g', 'ml', 'serving', 'piece')),
  constraint food_portions_sort_order_check
    check (sort_order between 0 and 1000),
  constraint food_portions_status_check
    check (status in ('active', 'archived')),
  constraint food_portions_metadata_check
    check (jsonb_typeof(metadata) = 'object'),
  constraint food_portions_archive_state_check
    check ((status = 'archived') = (archived_at is not null))
);

create table if not exists public.nutrition_targets (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  target_context text not null default 'daily',
  energy_kcal numeric(8,2) not null,
  protein_grams numeric(8,2) not null,
  carbohydrate_grams numeric(8,2) not null,
  fat_grams numeric(8,2) not null,
  fiber_grams numeric(8,2),
  source_type text not null,
  created_by_user_id uuid references public.profiles(id) on delete set null,
  status text not null,
  effective_from date not null,
  effective_to date,
  accepted_by_user_id uuid references public.profiles(id) on delete set null,
  accepted_at timestamptz,
  supersedes_target_id uuid references public.nutrition_targets(id) on delete set null,
  request_id uuid not null,
  notes text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint nutrition_targets_context_check
    check (target_context in ('daily', 'training', 'rest')),
  constraint nutrition_targets_energy_check
    check (energy_kcal > 0 and energy_kcal <= 20000),
  constraint nutrition_targets_protein_check
    check (protein_grams >= 0 and protein_grams <= 2000),
  constraint nutrition_targets_carbohydrate_check
    check (carbohydrate_grams >= 0 and carbohydrate_grams <= 2000),
  constraint nutrition_targets_fat_check
    check (fat_grams >= 0 and fat_grams <= 2000),
  constraint nutrition_targets_fiber_check
    check (fiber_grams is null or (fiber_grams >= 0 and fiber_grams <= 500)),
  constraint nutrition_targets_source_type_check
    check (source_type in ('member', 'calculator', 'trainer', 'future_ai_suggestion', 'legacy_bridge')),
  constraint nutrition_targets_status_check
    check (status in ('recommended', 'active', 'superseded', 'archived')),
  constraint nutrition_targets_effective_range_check
    check (effective_to is null or effective_to >= effective_from),
  constraint nutrition_targets_notes_check
    check (notes is null or char_length(notes) <= 500),
  constraint nutrition_targets_metadata_check
    check (jsonb_typeof(metadata) = 'object'),
  constraint nutrition_targets_acceptance_check
    check (
      (status = 'recommended' and accepted_by_user_id is null and accepted_at is null)
      or
      (status in ('active', 'superseded', 'archived') and accepted_by_user_id is not null and accepted_at is not null)
    ),
  constraint nutrition_targets_member_authority_check
    check (
      source_type <> 'member'
      or (
        created_by_user_id = user_id
        and accepted_by_user_id = user_id
        and status in ('active', 'superseded', 'archived')
      )
    ),
  constraint nutrition_targets_archive_state_check
    check ((status = 'archived') = (archived_at is not null))
);

create table if not exists public.food_logs (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  log_date date not null,
  timezone_name text not null,
  timezone_offset_minutes smallint not null,
  target_id uuid references public.nutrition_targets(id) on delete set null,
  target_energy_kcal_snapshot numeric(8,2),
  target_protein_grams_snapshot numeric(8,2),
  target_carbohydrate_grams_snapshot numeric(8,2),
  target_fat_grams_snapshot numeric(8,2),
  target_fiber_grams_snapshot numeric(8,2),
  status text not null default 'active',
  source text not null default 'phase4_member',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint food_logs_timezone_name_check
    check (char_length(btrim(timezone_name)) between 1 and 64),
  constraint food_logs_timezone_offset_check
    check (timezone_offset_minutes between -840 and 840),
  constraint food_logs_target_energy_check
    check (target_energy_kcal_snapshot is null or (target_energy_kcal_snapshot > 0 and target_energy_kcal_snapshot <= 20000)),
  constraint food_logs_target_protein_check
    check (target_protein_grams_snapshot is null or (target_protein_grams_snapshot >= 0 and target_protein_grams_snapshot <= 2000)),
  constraint food_logs_target_carbohydrate_check
    check (target_carbohydrate_grams_snapshot is null or (target_carbohydrate_grams_snapshot >= 0 and target_carbohydrate_grams_snapshot <= 2000)),
  constraint food_logs_target_fat_check
    check (target_fat_grams_snapshot is null or (target_fat_grams_snapshot >= 0 and target_fat_grams_snapshot <= 2000)),
  constraint food_logs_target_fiber_check
    check (target_fiber_grams_snapshot is null or (target_fiber_grams_snapshot >= 0 and target_fiber_grams_snapshot <= 500)),
  constraint food_logs_status_check
    check (status in ('active', 'archived')),
  constraint food_logs_source_check
    check (source in ('phase4_member', 'legacy_bridge')),
  constraint food_logs_metadata_check
    check (jsonb_typeof(metadata) = 'object'),
  constraint food_logs_archive_state_check
    check ((status = 'archived') = (archived_at is not null)),
  constraint food_logs_user_date_unique unique (user_id, log_date)
);

create table if not exists public.food_log_items (
  id uuid primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  food_log_id uuid not null references public.food_logs(id) on delete cascade,
  food_id uuid references public.foods(id) on delete set null,
  food_portion_id uuid references public.food_portions(id) on delete set null,
  meal_moment text not null,
  sort_order integer not null,
  consumed_quantity numeric(12,3) not null,
  consumed_unit text not null,
  food_name_snapshot text not null,
  brand_snapshot text,
  reference_amount_snapshot numeric(12,3) not null,
  reference_unit_snapshot text not null,
  portion_label_snapshot text,
  portion_equivalent_amount_snapshot numeric(12,3),
  portion_equivalent_unit_snapshot text,
  density_g_per_ml_snapshot numeric(12,6),
  calculation_basis text not null,
  energy_kcal_snapshot numeric(12,3) not null,
  protein_grams_snapshot numeric(12,3) not null,
  carbohydrate_grams_snapshot numeric(12,3) not null,
  fat_grams_snapshot numeric(12,3) not null,
  fiber_grams_snapshot numeric(12,3),
  source_provider_snapshot text not null,
  provider_food_id_snapshot text,
  source_version_snapshot text,
  provenance_snapshot jsonb not null default '{}'::jsonb,
  notes text,
  status text not null default 'active',
  request_id uuid not null,
  consumed_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint food_log_items_meal_moment_check
    check (meal_moment ~ '^[a-z][a-z0-9_]{0,39}$'),
  constraint food_log_items_sort_order_check
    check (sort_order between 0 and 10000),
  constraint food_log_items_consumed_quantity_check
    check (consumed_quantity > 0 and consumed_quantity <= 100000),
  constraint food_log_items_consumed_unit_check
    check (consumed_unit in ('g', 'ml', 'serving', 'piece')),
  constraint food_log_items_food_name_check
    check (char_length(btrim(food_name_snapshot)) between 1 and 240),
  constraint food_log_items_brand_check
    check (brand_snapshot is null or char_length(btrim(brand_snapshot)) between 1 and 160),
  constraint food_log_items_reference_amount_check
    check (reference_amount_snapshot > 0 and reference_amount_snapshot <= 100000),
  constraint food_log_items_reference_unit_check
    check (reference_unit_snapshot in ('g', 'ml', 'serving', 'piece')),
  constraint food_log_items_portion_snapshot_check
    check (
      (
        portion_label_snapshot is null
        and portion_equivalent_amount_snapshot is null
        and portion_equivalent_unit_snapshot is null
        and calculation_basis <> 'portion_conversion'
      )
      or
      (
        portion_label_snapshot is not null
        and char_length(btrim(portion_label_snapshot)) between 1 and 120
        and portion_equivalent_amount_snapshot > 0
        and portion_equivalent_amount_snapshot <= 100000
        and portion_equivalent_unit_snapshot in ('g', 'ml', 'serving', 'piece')
        and calculation_basis = 'portion_conversion'
      )
    ),
  constraint food_log_items_density_check
    check (density_g_per_ml_snapshot is null or (density_g_per_ml_snapshot > 0 and density_g_per_ml_snapshot <= 100)),
  constraint food_log_items_calculation_basis_check
    check (calculation_basis in ('direct_reference', 'portion_conversion', 'density_conversion')),
  constraint food_log_items_calculation_snapshot_check
    check (
      (calculation_basis = 'direct_reference' and density_g_per_ml_snapshot is null)
      or calculation_basis = 'portion_conversion'
      or (calculation_basis = 'density_conversion' and density_g_per_ml_snapshot is not null)
    ),
  constraint food_log_items_energy_check
    check (energy_kcal_snapshot >= 0 and energy_kcal_snapshot <= 1000000),
  constraint food_log_items_protein_check
    check (protein_grams_snapshot >= 0 and protein_grams_snapshot <= 100000),
  constraint food_log_items_carbohydrate_check
    check (carbohydrate_grams_snapshot >= 0 and carbohydrate_grams_snapshot <= 100000),
  constraint food_log_items_fat_check
    check (fat_grams_snapshot >= 0 and fat_grams_snapshot <= 100000),
  constraint food_log_items_fiber_check
    check (fiber_grams_snapshot is null or (fiber_grams_snapshot >= 0 and fiber_grams_snapshot <= 100000)),
  constraint food_log_items_provider_id_check
    check (provider_food_id_snapshot is null or char_length(provider_food_id_snapshot) between 1 and 240),
  constraint food_log_items_source_version_check
    check (source_version_snapshot is null or char_length(source_version_snapshot) between 1 and 120),
  constraint food_log_items_json_objects_check
    check (jsonb_typeof(provenance_snapshot) = 'object' and jsonb_typeof(metadata) = 'object'),
  constraint food_log_items_notes_check
    check (notes is null or char_length(notes) <= 1000),
  constraint food_log_items_status_check
    check (status in ('active', 'archived')),
  constraint food_log_items_archive_state_check
    check ((status = 'archived') = (archived_at is not null))
);

create unique index if not exists foods_canonical_slug_uidx
  on public.foods(canonical_slug)
  where catalog_scope = 'canonical';

create unique index if not exists foods_provider_identity_uidx
  on public.foods(source_provider, provider_food_id)
  where provider_food_id is not null;

create index if not exists foods_barcode_idx
  on public.foods(barcode)
  where barcode is not null and status = 'active';

create index if not exists foods_active_name_idx
  on public.foods(lower(name) text_pattern_ops, id)
  where status = 'active';

create index if not exists foods_owner_status_idx
  on public.foods(owner_user_id, status)
  where catalog_scope = 'custom';

create index if not exists foods_source_provenance_idx
  on public.foods(source_provider, source_updated_at desc)
  where catalog_scope = 'canonical';

create unique index if not exists food_portions_active_label_uidx
  on public.food_portions(food_id, lower(label))
  where status = 'active';

create unique index if not exists food_portions_one_active_default_uidx
  on public.food_portions(food_id)
  where status = 'active' and is_default;

create index if not exists food_portions_food_status_order_idx
  on public.food_portions(food_id, status, sort_order, id);

create unique index if not exists nutrition_targets_user_request_uidx
  on public.nutrition_targets(user_id, request_id);

create unique index if not exists nutrition_targets_one_active_context_uidx
  on public.nutrition_targets(user_id, target_context)
  where status = 'active';

create index if not exists nutrition_targets_user_history_idx
  on public.nutrition_targets(user_id, target_context, effective_from desc, created_at desc);

create index if not exists food_logs_user_history_idx
  on public.food_logs(user_id, log_date desc)
  where status = 'active';

create unique index if not exists food_log_items_user_request_uidx
  on public.food_log_items(user_id, request_id);

create index if not exists food_log_items_log_meal_order_idx
  on public.food_log_items(user_id, food_log_id, meal_moment, sort_order, id)
  where status = 'active';

create index if not exists food_log_items_recent_food_idx
  on public.food_log_items(user_id, created_at desc, food_id)
  where status = 'active' and food_id is not null;

create index if not exists food_log_items_food_idx
  on public.food_log_items(food_id, created_at desc)
  where food_id is not null;

create or replace function public.fmz_phase4_touch_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create or replace function public.fmz_phase4_sync_archive_state()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
begin
  if new.status = 'archived' then
    new.archived_at := coalesce(new.archived_at, now());
  else
    new.archived_at := null;
  end if;
  return new;
end;
$$;

create or replace function public.fmz_phase4_has_full_nutrition_access(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path = pg_catalog, public, pg_temp
as $$
  select exists (
    select 1
    from public.entitlements e
    where e.user_id = p_user_id
      and e.status = 'active'
      and e.entitlement_code in ('pro', 'ai', 'personal_coaching')
      and e.starts_at <= now()
      and (e.ends_at is null or e.ends_at > now())
  );
$$;

create or replace function public.fmz_phase4_enforce_custom_food_limit()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_active_count integer;
begin
  if tg_op = 'UPDATE' and (
    new.owner_user_id is distinct from old.owner_user_id
    or new.catalog_scope is distinct from old.catalog_scope
  ) then
    raise exception 'food ownership and catalog scope are immutable'
      using errcode = '42501';
  end if;

  if new.catalog_scope = 'canonical' then
    if v_user_id is not null then
      raise exception 'canonical foods are database-managed'
        using errcode = '42501';
    end if;
    return new;
  end if;

  if v_user_id is null then
    raise exception 'authenticated user required for custom foods'
      using errcode = '42501';
  end if;

  if new.owner_user_id is distinct from v_user_id
     or new.source_provider is distinct from 'custom_user'
     or new.canonical_slug is not null then
    raise exception 'custom food owner and scope must be server-authorized'
      using errcode = '42501';
  end if;

  if new.status = 'active'
     and (tg_op = 'INSERT' or old.status is distinct from 'active') then
    perform pg_catalog.pg_advisory_xact_lock(
      pg_catalog.hashtextextended('fmz_phase4_custom_food_limit:' || v_user_id::text, 0)
    );

    if not public.fmz_phase4_has_full_nutrition_access(v_user_id) then
      select count(*)
      into v_active_count
      from public.foods f
      where f.owner_user_id = v_user_id
        and f.catalog_scope = 'custom'
        and f.status = 'active'
        and f.id <> new.id;

      if v_active_count >= 10 then
        raise exception 'Free Nutrition limit reached: maximum 10 active custom foods'
          using errcode = '23514';
      end if;
    end if;
  end if;

  return new;
end;
$$;

create or replace function public.fmz_phase4_enforce_food_portion_owner()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_food public.foods%rowtype;
begin
  if tg_op = 'UPDATE' and new.food_id is distinct from old.food_id then
    raise exception 'food portion parent is immutable'
      using errcode = '42501';
  end if;

  select * into v_food
  from public.foods f
  where f.id = new.food_id;

  if not found then
    raise exception 'food portion parent does not exist'
      using errcode = '23503';
  end if;

  if v_food.catalog_scope = 'canonical' then
    if v_user_id is not null then
      raise exception 'canonical food portions are database-managed'
        using errcode = '42501';
    end if;
    return new;
  end if;

  if v_user_id is null or v_food.owner_user_id is distinct from v_user_id then
    raise exception 'custom food portion must belong to authenticated user'
      using errcode = '42501';
  end if;

  return new;
end;
$$;

create or replace function public.fmz_phase4_enforce_target_owner()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
begin
  if v_user_id is null then
    raise exception 'authenticated user required for nutrition target'
      using errcode = '42501';
  end if;

  if new.user_id is distinct from v_user_id then
    raise exception 'nutrition target owner must match authenticated user'
      using errcode = '42501';
  end if;

  if tg_op = 'UPDATE' and new.user_id is distinct from old.user_id then
    raise exception 'nutrition target ownership is immutable'
      using errcode = '42501';
  end if;

  if new.target_context <> 'daily'
     or new.source_type <> 'member'
     or new.created_by_user_id is distinct from v_user_id
     or new.accepted_by_user_id is distinct from v_user_id
     or new.accepted_at is null
     or new.status not in ('active', 'superseded', 'archived') then
    raise exception 'initial target route is member-controlled daily only'
      using errcode = '42501';
  end if;

  if new.supersedes_target_id is not null and not exists (
    select 1
    from public.nutrition_targets t
    where t.id = new.supersedes_target_id
      and t.user_id = v_user_id
  ) then
    raise exception 'superseded target must belong to authenticated user'
      using errcode = '42501';
  end if;

  return new;
end;
$$;

create or replace function public.fmz_phase4_enforce_food_log_owner()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
begin
  if v_user_id is null or new.user_id is distinct from v_user_id then
    raise exception 'food log owner must match authenticated user'
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
    raise exception 'food log target must belong to authenticated user'
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
  v_user_id uuid := auth.uid();
begin
  if v_user_id is null or new.user_id is distinct from v_user_id then
    raise exception 'food log item owner must match authenticated user'
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

  if new.food_id is null then
    raise exception 'new food log item requires a food identity'
      using errcode = '23514';
  end if;

  if not exists (
    select 1
    from public.food_logs l
    where l.id = new.food_log_id
      and l.user_id = v_user_id
      and l.status = 'active'
  ) then
    raise exception 'food log item day must belong to authenticated user'
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
    raise exception 'food must be active and visible to authenticated user'
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

create or replace function public.fmz_phase4_day_payload(
  p_user_id uuid,
  p_log_date date
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_log public.food_logs%rowtype;
  v_target jsonb;
  v_items jsonb;
  v_totals jsonb;
begin
  select * into v_log
  from public.food_logs l
  where l.user_id = p_user_id
    and l.log_date = p_log_date
    and l.status = 'active';

  if found then
    v_target := jsonb_build_object(
      'target_id', v_log.target_id,
      'energy_kcal', v_log.target_energy_kcal_snapshot,
      'protein_grams', v_log.target_protein_grams_snapshot,
      'carbohydrate_grams', v_log.target_carbohydrate_grams_snapshot,
      'fat_grams', v_log.target_fat_grams_snapshot,
      'fiber_grams', v_log.target_fiber_grams_snapshot
    );

    select coalesce(
      jsonb_agg(to_jsonb(i) order by i.meal_moment, i.sort_order, i.id),
      '[]'::jsonb
    )
    into v_items
    from public.food_log_items i
    where i.user_id = p_user_id
      and i.food_log_id = v_log.id
      and i.status = 'active';

    select jsonb_build_object(
      'energy_kcal', coalesce(sum(i.energy_kcal_snapshot), 0),
      'protein_grams', coalesce(sum(i.protein_grams_snapshot), 0),
      'carbohydrate_grams', coalesce(sum(i.carbohydrate_grams_snapshot), 0),
      'fat_grams', coalesce(sum(i.fat_grams_snapshot), 0),
      'fiber_grams', coalesce(sum(i.fiber_grams_snapshot), 0)
    )
    into v_totals
    from public.food_log_items i
    where i.user_id = p_user_id
      and i.food_log_id = v_log.id
      and i.status = 'active';
  else
    select to_jsonb(t)
    into v_target
    from public.nutrition_targets t
    where t.user_id = p_user_id
      and t.target_context = 'daily'
      and t.status in ('active', 'superseded')
      and t.effective_from <= p_log_date
      and (t.effective_to is null or t.effective_to >= p_log_date)
    order by (t.status = 'active') desc, t.effective_from desc, t.created_at desc
    limit 1;

    v_items := '[]'::jsonb;
    v_totals := jsonb_build_object(
      'energy_kcal', 0,
      'protein_grams', 0,
      'carbohydrate_grams', 0,
      'fat_grams', 0,
      'fiber_grams', 0
    );
  end if;

  return jsonb_build_object(
    'log_date', p_log_date,
    'log', case when v_log.id is null then null else to_jsonb(v_log) end,
    'target', v_target,
    'items', v_items,
    'totals', v_totals
  );
end;
$$;

create or replace function public.fmz_phase4_set_nutrition_timezone(
  p_timezone_name text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_timezone text := btrim(p_timezone_name);
  v_preference public.nutrition_preferences%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if v_timezone is null
     or not exists (
       select 1 from pg_catalog.pg_timezone_names tz
       where tz.name = v_timezone
     ) then
    raise exception 'valid IANA timezone required'
      using errcode = '22023';
  end if;

  insert into public.nutrition_preferences(user_id, timezone_name)
  values (v_user_id, v_timezone)
  on conflict (user_id) do update
  set timezone_name = excluded.timezone_name
  returning * into v_preference;

  return to_jsonb(v_preference);
end;
$$;

create or replace function public.fmz_phase4_search_foods(
  p_query text default null,
  p_page_size integer default 25,
  p_after_name text default null,
  p_after_id uuid default null
)
returns setof public.foods
language plpgsql
stable
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_query text := lower(btrim(coalesce(p_query, '')));
  v_page_size integer := greatest(1, least(coalesce(p_page_size, 25), 50));
begin
  if auth.uid() is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  return query
  select f.*
  from public.foods f
  where f.status = 'active'
    and (
      v_query = ''
      or lower(f.name) like v_query || '%'
      or lower(coalesce(f.brand, '')) like v_query || '%'
      or f.barcode = btrim(coalesce(p_query, ''))
    )
    and (
      p_after_name is null
      or p_after_id is null
      or (lower(f.name), f.id) > (lower(p_after_name), p_after_id)
    )
  order by lower(f.name), f.id
  limit v_page_size;
end;
$$;

create or replace function public.fmz_phase4_upsert_custom_food(
  p_food_id uuid,
  p_name text,
  p_brand text,
  p_reference_amount numeric,
  p_reference_unit text,
  p_reference_mass_grams numeric,
  p_reference_volume_ml numeric,
  p_density_g_per_ml numeric,
  p_energy_kcal numeric,
  p_protein_grams numeric,
  p_carbohydrate_grams numeric,
  p_fat_grams numeric,
  p_fiber_grams numeric,
  p_expected_updated_at timestamptz default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_existing public.foods%rowtype;
  v_food public.foods%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if p_food_id is null then
    raise exception 'stable food UUID required'
      using errcode = '22023';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_custom_food_request:' || v_user_id::text || ':' || p_food_id::text,
      0
    )
  );

  select * into v_existing
  from public.foods f
  where f.id = p_food_id;

  if found then
    if v_existing.catalog_scope <> 'custom'
       or v_existing.owner_user_id is distinct from v_user_id then
      raise exception 'custom food does not belong to authenticated user'
        using errcode = '42501';
    end if;

    if p_expected_updated_at is null then
      if v_existing.status = 'active'
         and v_existing.name is not distinct from btrim(p_name)
         and v_existing.brand is not distinct from nullif(btrim(p_brand), '')
         and v_existing.reference_amount is not distinct from p_reference_amount::numeric(12,3)
         and v_existing.reference_unit is not distinct from p_reference_unit
         and v_existing.reference_mass_grams is not distinct from p_reference_mass_grams::numeric(12,3)
         and v_existing.reference_volume_ml is not distinct from p_reference_volume_ml::numeric(12,3)
         and v_existing.density_g_per_ml is not distinct from p_density_g_per_ml::numeric(12,6)
         and v_existing.energy_kcal is not distinct from p_energy_kcal::numeric(12,3)
         and v_existing.protein_grams is not distinct from p_protein_grams::numeric(12,3)
         and v_existing.carbohydrate_grams is not distinct from p_carbohydrate_grams::numeric(12,3)
         and v_existing.fat_grams is not distinct from p_fat_grams::numeric(12,3)
         and v_existing.fiber_grams is not distinct from p_fiber_grams::numeric(12,3) then
        return to_jsonb(v_existing);
      end if;

      raise exception 'custom food UUID already exists; refresh before saving'
        using errcode = '23505';
    end if;

    if v_existing.updated_at is distinct from p_expected_updated_at then
      raise exception 'custom food changed; refresh before saving'
        using errcode = '40001';
    end if;

    update public.foods
    set
      name = btrim(p_name),
      brand = nullif(btrim(p_brand), ''),
      reference_amount = p_reference_amount,
      reference_unit = p_reference_unit,
      reference_mass_grams = p_reference_mass_grams,
      reference_volume_ml = p_reference_volume_ml,
      density_g_per_ml = p_density_g_per_ml,
      energy_kcal = p_energy_kcal,
      protein_grams = p_protein_grams,
      carbohydrate_grams = p_carbohydrate_grams,
      fat_grams = p_fat_grams,
      fiber_grams = p_fiber_grams,
      quality_status = 'user_entered',
      status = 'active'
    where id = p_food_id
      and owner_user_id = v_user_id
      and updated_at = p_expected_updated_at
    returning * into v_food;

    if not found then
      raise exception 'custom food changed; refresh before saving'
        using errcode = '40001';
    end if;
  else
    insert into public.foods(
      id,
      owner_user_id,
      catalog_scope,
      canonical_slug,
      name,
      brand,
      source_provider,
      provenance,
      quality_status,
      reference_amount,
      reference_unit,
      reference_mass_grams,
      reference_volume_ml,
      density_g_per_ml,
      energy_kcal,
      protein_grams,
      carbohydrate_grams,
      fat_grams,
      fiber_grams,
      status,
      metadata
    )
    values (
      p_food_id,
      v_user_id,
      'custom',
      null,
      btrim(p_name),
      nullif(btrim(p_brand), ''),
      'custom_user',
      jsonb_build_object('source', 'member_entry'),
      'user_entered',
      p_reference_amount,
      p_reference_unit,
      p_reference_mass_grams,
      p_reference_volume_ml,
      p_density_g_per_ml,
      p_energy_kcal,
      p_protein_grams,
      p_carbohydrate_grams,
      p_fat_grams,
      p_fiber_grams,
      'active',
      jsonb_build_object('created_by', 'fmz_phase4_upsert_custom_food')
    )
    returning * into v_food;
  end if;

  return to_jsonb(v_food);
end;
$$;

create or replace function public.fmz_phase4_archive_custom_food(
  p_food_id uuid,
  p_expected_updated_at timestamptz
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_food public.foods%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if p_food_id is null then
    raise exception 'stable food UUID required'
      using errcode = '22023';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_custom_food_request:' || v_user_id::text || ':' || p_food_id::text,
      0
    )
  );

  select * into v_food
  from public.foods f
  where f.id = p_food_id
    and f.catalog_scope = 'custom'
    and f.owner_user_id = v_user_id;

  if not found then
    raise exception 'custom food not found'
      using errcode = '42501';
  end if;

  if v_food.status = 'archived' then
    return to_jsonb(v_food);
  end if;

  if p_expected_updated_at is null
     or v_food.updated_at is distinct from p_expected_updated_at then
    raise exception 'custom food changed; refresh before archiving'
      using errcode = '40001';
  end if;

  update public.foods
  set status = 'archived'
  where id = p_food_id
    and owner_user_id = v_user_id
    and updated_at = p_expected_updated_at
  returning * into v_food;

  if not found then
    raise exception 'custom food changed; refresh before archiving'
      using errcode = '40001';
  end if;

  return to_jsonb(v_food);
end;
$$;

create or replace function public.fmz_phase4_upsert_food_portion(
  p_portion_id uuid,
  p_food_id uuid,
  p_label text,
  p_amount numeric,
  p_unit text,
  p_equivalent_amount numeric,
  p_equivalent_unit text,
  p_is_default boolean,
  p_expected_updated_at timestamptz default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_existing public.food_portions%rowtype;
  v_portion public.food_portions%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if p_portion_id is null or p_food_id is null then
    raise exception 'stable portion and food UUIDs required'
      using errcode = '22023';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_portion_request:' || v_user_id::text || ':' || p_food_id::text,
      0
    )
  );

  if not exists (
    select 1 from public.foods f
    where f.id = p_food_id
      and f.catalog_scope = 'custom'
      and f.owner_user_id = v_user_id
      and f.status = 'active'
  ) then
    raise exception 'active custom food must belong to authenticated user'
      using errcode = '42501';
  end if;

  select * into v_existing
  from public.food_portions p
  where p.id = p_portion_id;

  if found then
    if v_existing.food_id is distinct from p_food_id then
      raise exception 'food portion parent is immutable'
        using errcode = '42501';
    end if;

    if p_expected_updated_at is null then
      if v_existing.status = 'active'
         and v_existing.label is not distinct from btrim(p_label)
         and v_existing.amount is not distinct from p_amount::numeric(12,3)
         and v_existing.unit is not distinct from p_unit
         and v_existing.equivalent_amount is not distinct from p_equivalent_amount::numeric(12,3)
         and v_existing.equivalent_unit is not distinct from p_equivalent_unit
         and v_existing.is_default is not distinct from coalesce(p_is_default, false) then
        return to_jsonb(v_existing);
      end if;

      raise exception 'food portion UUID already exists; refresh before saving'
        using errcode = '23505';
    end if;

    if v_existing.updated_at is distinct from p_expected_updated_at then
      raise exception 'food portion changed; refresh before saving'
        using errcode = '40001';
    end if;
  end if;

  if coalesce(p_is_default, false) then
    update public.food_portions p
    set is_default = false
    where p.food_id = p_food_id
      and p.status = 'active'
      and p.is_default
      and p.id <> p_portion_id;
  end if;

  if v_existing.id is null then
    insert into public.food_portions(
      id, food_id, label, amount, unit, equivalent_amount,
      equivalent_unit, is_default, status
    )
    values (
      p_portion_id, p_food_id, btrim(p_label), p_amount, p_unit,
      p_equivalent_amount, p_equivalent_unit, coalesce(p_is_default, false), 'active'
    )
    returning * into v_portion;
  else
    update public.food_portions
    set
      label = btrim(p_label),
      amount = p_amount,
      unit = p_unit,
      equivalent_amount = p_equivalent_amount,
      equivalent_unit = p_equivalent_unit,
      is_default = coalesce(p_is_default, false),
      status = 'active'
    where id = p_portion_id
      and updated_at = p_expected_updated_at
    returning * into v_portion;

    if not found then
      raise exception 'food portion changed; refresh before saving'
        using errcode = '40001';
    end if;
  end if;

  return to_jsonb(v_portion);
end;
$$;

create or replace function public.fmz_phase4_save_member_target(
  p_target_id uuid,
  p_request_id uuid,
  p_energy_kcal numeric,
  p_protein_grams numeric,
  p_carbohydrate_grams numeric,
  p_fat_grams numeric,
  p_fiber_grams numeric,
  p_effective_from date
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_existing public.nutrition_targets%rowtype;
  v_previous public.nutrition_targets%rowtype;
  v_target public.nutrition_targets%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if p_target_id is null or p_request_id is null or p_effective_from is null then
    raise exception 'stable target UUID, request UUID, and effective date required'
      using errcode = '22023';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_nutrition_target:' || v_user_id::text || ':daily',
      0
    )
  );

  select * into v_existing
  from public.nutrition_targets t
  where t.user_id = v_user_id
    and t.request_id = p_request_id;

  if found then
    return to_jsonb(v_existing);
  end if;

  if exists (
    select 1 from public.nutrition_targets t
    where t.id = p_target_id
  ) then
    raise exception 'target UUID already exists with a different request'
      using errcode = '23505';
  end if;

  select * into v_previous
  from public.nutrition_targets t
  where t.user_id = v_user_id
    and t.target_context = 'daily'
    and t.status = 'active'
  for update;

  if found and p_effective_from < v_previous.effective_from then
    raise exception 'new active target cannot begin before current active target'
      using errcode = '22023';
  end if;

  if v_previous.id is not null then
    update public.nutrition_targets
    set
      status = 'superseded',
      effective_to = case
        when p_effective_from > v_previous.effective_from then p_effective_from - 1
        else v_previous.effective_from
      end
    where id = v_previous.id;
  end if;

  insert into public.nutrition_targets(
    id,
    user_id,
    target_context,
    energy_kcal,
    protein_grams,
    carbohydrate_grams,
    fat_grams,
    fiber_grams,
    source_type,
    created_by_user_id,
    status,
    effective_from,
    effective_to,
    accepted_by_user_id,
    accepted_at,
    supersedes_target_id,
    request_id,
    metadata
  )
  values (
    p_target_id,
    v_user_id,
    'daily',
    p_energy_kcal,
    p_protein_grams,
    p_carbohydrate_grams,
    p_fat_grams,
    p_fiber_grams,
    'member',
    v_user_id,
    'active',
    p_effective_from,
    null,
    v_user_id,
    now(),
    v_previous.id,
    p_request_id,
    jsonb_build_object('created_by', 'fmz_phase4_save_member_target')
  )
  returning * into v_target;

  return to_jsonb(v_target);
end;
$$;

create or replace function public.fmz_phase4_get_current_nutrition_target()
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_target jsonb;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  select to_jsonb(t) into v_target
  from public.nutrition_targets t
  where t.user_id = v_user_id
    and t.target_context = 'daily'
    and t.status = 'active'
  limit 1;

  return v_target;
end;
$$;

create or replace function public.fmz_phase4_log_food_item(
  p_item_id uuid,
  p_request_id uuid,
  p_log_date date,
  p_timezone_name text,
  p_timezone_offset_minutes smallint,
  p_meal_moment text,
  p_food_id uuid,
  p_food_portion_id uuid,
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
  v_food public.foods%rowtype;
  v_portion public.food_portions%rowtype;
  v_target public.nutrition_targets%rowtype;
  v_log public.food_logs%rowtype;
  v_existing_item public.food_log_items%rowtype;
  v_item public.food_log_items%rowtype;
  v_base_quantity numeric;
  v_base_unit text;
  v_factor numeric;
  v_calculation_basis text;
  v_density_snapshot numeric;
  v_sort_order integer;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if p_item_id is null or p_request_id is null or p_log_date is null or p_food_id is null then
    raise exception 'stable item UUID, request UUID, log date, and food UUID required'
      using errcode = '22023';
  end if;

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
    select * into v_log
    from public.food_logs l
    where l.id = v_existing_item.food_log_id
      and l.user_id = v_user_id;

    select coalesce(p.timezone_name, v_log.timezone_name, 'UTC')
    into v_saved_timezone
    from (select 1) seed
    left join public.nutrition_preferences p on p.user_id = v_user_id;
    v_saved_timezone := coalesce(v_saved_timezone, v_log.timezone_name, 'UTC');
    v_today := (now() at time zone v_saved_timezone)::date;
    v_has_full_access := public.fmz_phase4_has_full_nutrition_access(v_user_id);

    if not v_has_full_access and v_log.log_date < v_today - 6 then
      raise exception 'Free Nutrition history is limited to seven local calendar days'
        using errcode = '42501';
    end if;

    return jsonb_build_object(
      'item', to_jsonb(v_existing_item),
      'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date),
      'idempotent_replay', true
    );
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

  if not found then
    insert into public.nutrition_preferences(user_id, timezone_name)
    values (v_user_id, v_timezone);
  elsif v_saved_timezone is distinct from v_timezone then
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

  if p_meal_moment not in ('breakfast', 'lunch', 'dinner', 'snacks') then
    raise exception 'unsupported meal moment'
      using errcode = '22023';
  end if;

  if p_consumed_unit not in ('g', 'ml', 'serving', 'piece') then
    raise exception 'unsupported consumption unit'
      using errcode = '22023';
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
    select * into v_log
    from public.food_logs l
    where l.id = v_existing_item.food_log_id
      and l.user_id = v_user_id;

    return jsonb_build_object(
      'item', to_jsonb(v_existing_item),
      'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date),
      'idempotent_replay', true
    );
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

  insert into public.food_logs(
    id,
    user_id,
    log_date,
    timezone_name,
    timezone_offset_minutes,
    target_id,
    target_energy_kcal_snapshot,
    target_protein_grams_snapshot,
    target_carbohydrate_grams_snapshot,
    target_fat_grams_snapshot,
    target_fiber_grams_snapshot,
    status,
    source,
    metadata
  )
  values (
    pg_catalog.gen_random_uuid(),
    v_user_id,
    p_log_date,
    v_timezone,
    p_timezone_offset_minutes,
    v_target.id,
    v_target.energy_kcal,
    v_target.protein_grams,
    v_target.carbohydrate_grams,
    v_target.fat_grams,
    v_target.fiber_grams,
    'active',
    'phase4_member',
    jsonb_build_object('created_by', 'fmz_phase4_log_food_item')
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
    p_item_id,
    v_user_id,
    v_log.id,
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
    nullif(btrim(p_notes), ''),
    'active',
    p_request_id,
    p_consumed_at,
    jsonb_build_object('calculation_version', 'phase4_slice1_v1')
  )
  returning * into v_item;

  return jsonb_build_object(
    'item', to_jsonb(v_item),
    'day', public.fmz_phase4_day_payload(v_user_id, p_log_date),
    'idempotent_replay', false
  );
end;
$$;

create or replace function public.fmz_phase4_archive_food_log_item(
  p_item_id uuid,
  p_expected_updated_at timestamptz
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_item public.food_log_items%rowtype;
  v_log_date date;
  v_timezone text;
  v_today date;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if p_item_id is null then
    raise exception 'stable item UUID required'
      using errcode = '22023';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      'fmz_phase4_food_log_item_request:' || v_user_id::text || ':' || p_item_id::text,
      0
    )
  );

  select i.* into v_item
  from public.food_log_items i
  join public.food_logs l on l.id = i.food_log_id
  where i.id = p_item_id
    and i.user_id = v_user_id
    and l.user_id = v_user_id;

  if not found then
    raise exception 'food log item not found'
      using errcode = '42501';
  end if;

  select l.log_date into v_log_date
  from public.food_logs l
  where l.id = v_item.food_log_id
    and l.user_id = v_user_id;

  select coalesce(p.timezone_name, 'UTC') into v_timezone
  from public.nutrition_preferences p
  where p.user_id = v_user_id;
  v_timezone := coalesce(v_timezone, 'UTC');
  v_today := (now() at time zone v_timezone)::date;

  if not public.fmz_phase4_has_full_nutrition_access(v_user_id)
     and v_log_date < v_today - 6 then
    raise exception 'Free Nutrition history is limited to seven local calendar days'
      using errcode = '42501';
  end if;

  if v_item.status = 'archived' then
    return jsonb_build_object(
      'item', to_jsonb(v_item),
      'day', public.fmz_phase4_day_payload(v_user_id, v_log_date),
      'idempotent_replay', true
    );
  end if;

  if p_expected_updated_at is null
     or v_item.updated_at is distinct from p_expected_updated_at then
    raise exception 'food log item changed; refresh before archiving'
      using errcode = '40001';
  end if;

  update public.food_log_items
  set status = 'archived'
  where id = p_item_id
    and user_id = v_user_id
    and updated_at = p_expected_updated_at
  returning * into v_item;

  if not found then
    raise exception 'food log item changed; refresh before archiving'
      using errcode = '40001';
  end if;

  return jsonb_build_object(
    'item', to_jsonb(v_item),
    'day', public.fmz_phase4_day_payload(v_user_id, v_log_date),
    'idempotent_replay', false
  );
end;
$$;

create or replace function public.fmz_phase4_get_nutrition_day(
  p_log_date date
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_timezone text;
  v_today date;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if p_log_date is null then
    raise exception 'log date required'
      using errcode = '22023';
  end if;

  select coalesce(p.timezone_name, 'UTC') into v_timezone
  from public.nutrition_preferences p
  where p.user_id = v_user_id;
  v_timezone := coalesce(v_timezone, 'UTC');
  v_today := (now() at time zone v_timezone)::date;

  if p_log_date > v_today then
    raise exception 'future Nutrition day is unavailable'
      using errcode = '22023';
  end if;

  if not public.fmz_phase4_has_full_nutrition_access(v_user_id)
     and p_log_date < v_today - 6 then
    raise exception 'Free Nutrition history is limited to seven local calendar days'
      using errcode = '42501';
  end if;

  return public.fmz_phase4_day_payload(v_user_id, p_log_date);
end;
$$;

create or replace function public.fmz_phase4_get_nutrition_history(
  p_before_date date default null,
  p_page_size integer default 14
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_timezone text;
  v_today date;
  v_has_full_access boolean;
  v_page_size integer := greatest(1, least(coalesce(p_page_size, 14), 31));
  v_before_date date;
  v_days jsonb;
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  select coalesce(p.timezone_name, 'UTC') into v_timezone
  from public.nutrition_preferences p
  where p.user_id = v_user_id;
  v_timezone := coalesce(v_timezone, 'UTC');
  v_today := (now() at time zone v_timezone)::date;
  v_has_full_access := public.fmz_phase4_has_full_nutrition_access(v_user_id);

  if not v_has_full_access then
    select coalesce(
      jsonb_agg(
        public.fmz_phase4_day_payload(v_user_id, v_today - d.day_offset)
        order by d.day_offset
      ),
      '[]'::jsonb
    )
    into v_days
    from pg_catalog.generate_series(0, 6) as d(day_offset);

    return jsonb_build_object(
      'access', 'free',
      'window_days', 7,
      'timezone_name', v_timezone,
      'days', v_days
    );
  end if;

  v_before_date := least(coalesce(p_before_date, v_today), v_today);

  select coalesce(jsonb_agg(day_payload order by log_date desc), '[]'::jsonb)
  into v_days
  from (
    select
      l.log_date,
      public.fmz_phase4_day_payload(v_user_id, l.log_date) as day_payload
    from public.food_logs l
    where l.user_id = v_user_id
      and l.status = 'active'
      and l.log_date <= v_before_date
    order by l.log_date desc
    limit v_page_size
  ) history_rows;

  return jsonb_build_object(
    'access', 'full',
    'window_days', null,
    'timezone_name', v_timezone,
    'days', v_days
  );
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_trigger
    where tgname = 'foods_10_sync_archive_state'
      and tgrelid = 'public.foods'::regclass
  ) then
    create trigger foods_10_sync_archive_state
    before insert or update of status on public.foods
    for each row execute function public.fmz_phase4_sync_archive_state();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'foods_20_enforce_custom_limit'
      and tgrelid = 'public.foods'::regclass
  ) then
    create trigger foods_20_enforce_custom_limit
    before insert or update of owner_user_id, catalog_scope, status on public.foods
    for each row execute function public.fmz_phase4_enforce_custom_food_limit();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'foods_90_touch_updated_at'
      and tgrelid = 'public.foods'::regclass
  ) then
    create trigger foods_90_touch_updated_at
    before update on public.foods
    for each row execute function public.fmz_phase4_touch_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'food_portions_10_sync_archive_state'
      and tgrelid = 'public.food_portions'::regclass
  ) then
    create trigger food_portions_10_sync_archive_state
    before insert or update of status on public.food_portions
    for each row execute function public.fmz_phase4_sync_archive_state();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'food_portions_20_enforce_owner'
      and tgrelid = 'public.food_portions'::regclass
  ) then
    create trigger food_portions_20_enforce_owner
    before insert or update on public.food_portions
    for each row execute function public.fmz_phase4_enforce_food_portion_owner();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'food_portions_90_touch_updated_at'
      and tgrelid = 'public.food_portions'::regclass
  ) then
    create trigger food_portions_90_touch_updated_at
    before update on public.food_portions
    for each row execute function public.fmz_phase4_touch_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'nutrition_preferences_90_touch_updated_at'
      and tgrelid = 'public.nutrition_preferences'::regclass
  ) then
    create trigger nutrition_preferences_90_touch_updated_at
    before update on public.nutrition_preferences
    for each row execute function public.fmz_phase4_touch_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'nutrition_targets_10_sync_archive_state'
      and tgrelid = 'public.nutrition_targets'::regclass
  ) then
    create trigger nutrition_targets_10_sync_archive_state
    before insert or update of status on public.nutrition_targets
    for each row execute function public.fmz_phase4_sync_archive_state();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'nutrition_targets_20_enforce_owner'
      and tgrelid = 'public.nutrition_targets'::regclass
  ) then
    create trigger nutrition_targets_20_enforce_owner
    before insert or update on public.nutrition_targets
    for each row execute function public.fmz_phase4_enforce_target_owner();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'nutrition_targets_90_touch_updated_at'
      and tgrelid = 'public.nutrition_targets'::regclass
  ) then
    create trigger nutrition_targets_90_touch_updated_at
    before update on public.nutrition_targets
    for each row execute function public.fmz_phase4_touch_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'food_logs_10_sync_archive_state'
      and tgrelid = 'public.food_logs'::regclass
  ) then
    create trigger food_logs_10_sync_archive_state
    before insert or update of status on public.food_logs
    for each row execute function public.fmz_phase4_sync_archive_state();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'food_logs_20_enforce_owner'
      and tgrelid = 'public.food_logs'::regclass
  ) then
    create trigger food_logs_20_enforce_owner
    before insert or update on public.food_logs
    for each row execute function public.fmz_phase4_enforce_food_log_owner();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'food_logs_90_touch_updated_at'
      and tgrelid = 'public.food_logs'::regclass
  ) then
    create trigger food_logs_90_touch_updated_at
    before update on public.food_logs
    for each row execute function public.fmz_phase4_touch_updated_at();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'food_log_items_10_sync_archive_state'
      and tgrelid = 'public.food_log_items'::regclass
  ) then
    create trigger food_log_items_10_sync_archive_state
    before insert or update of status on public.food_log_items
    for each row execute function public.fmz_phase4_sync_archive_state();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'food_log_items_20_enforce_owner'
      and tgrelid = 'public.food_log_items'::regclass
  ) then
    create trigger food_log_items_20_enforce_owner
    before insert or update on public.food_log_items
    for each row execute function public.fmz_phase4_enforce_food_log_item_owner();
  end if;

  if not exists (
    select 1 from pg_trigger
    where tgname = 'food_log_items_90_touch_updated_at'
      and tgrelid = 'public.food_log_items'::regclass
  ) then
    create trigger food_log_items_90_touch_updated_at
    before update on public.food_log_items
    for each row execute function public.fmz_phase4_touch_updated_at();
  end if;
end $$;

alter table public.nutrition_preferences enable row level security;
alter table public.foods enable row level security;
alter table public.food_portions enable row level security;
alter table public.nutrition_targets enable row level security;
alter table public.food_logs enable row level security;
alter table public.food_log_items enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'nutrition_preferences'
      and policyname = 'nutrition_preferences_select_own'
  ) then
    create policy "nutrition_preferences_select_own"
    on public.nutrition_preferences
    for select
    using (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'nutrition_preferences'
      and policyname = 'nutrition_preferences_insert_own'
  ) then
    create policy "nutrition_preferences_insert_own"
    on public.nutrition_preferences
    for insert
    with check (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'nutrition_preferences'
      and policyname = 'nutrition_preferences_update_own'
  ) then
    create policy "nutrition_preferences_update_own"
    on public.nutrition_preferences
    for update
    using (user_id = auth.uid())
    with check (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'foods'
      and policyname = 'foods_select_visible'
  ) then
    create policy "foods_select_visible"
    on public.foods
    for select
    using (
      (catalog_scope = 'canonical' and status = 'active')
      or (catalog_scope = 'custom' and owner_user_id = auth.uid())
    );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'foods'
      and policyname = 'foods_insert_own_custom'
  ) then
    create policy "foods_insert_own_custom"
    on public.foods
    for insert
    with check (
      catalog_scope = 'custom'
      and owner_user_id = auth.uid()
      and source_provider = 'custom_user'
    );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'foods'
      and policyname = 'foods_update_own_custom'
  ) then
    create policy "foods_update_own_custom"
    on public.foods
    for update
    using (catalog_scope = 'custom' and owner_user_id = auth.uid())
    with check (
      catalog_scope = 'custom'
      and owner_user_id = auth.uid()
      and source_provider = 'custom_user'
    );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'food_portions'
      and policyname = 'food_portions_select_visible'
  ) then
    create policy "food_portions_select_visible"
    on public.food_portions
    for select
    using (
      exists (
        select 1 from public.foods f
        where f.id = food_id
          and (
            (f.catalog_scope = 'canonical' and f.status = 'active' and food_portions.status = 'active')
            or (f.catalog_scope = 'custom' and f.owner_user_id = auth.uid())
          )
      )
    );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'food_portions'
      and policyname = 'food_portions_insert_own_custom'
  ) then
    create policy "food_portions_insert_own_custom"
    on public.food_portions
    for insert
    with check (
      exists (
        select 1 from public.foods f
        where f.id = food_id
          and f.catalog_scope = 'custom'
          and f.owner_user_id = auth.uid()
      )
    );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'food_portions'
      and policyname = 'food_portions_update_own_custom'
  ) then
    create policy "food_portions_update_own_custom"
    on public.food_portions
    for update
    using (
      exists (
        select 1 from public.foods f
        where f.id = food_id
          and f.catalog_scope = 'custom'
          and f.owner_user_id = auth.uid()
      )
    )
    with check (
      exists (
        select 1 from public.foods f
        where f.id = food_id
          and f.catalog_scope = 'custom'
          and f.owner_user_id = auth.uid()
      )
    );
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'nutrition_targets'
      and policyname = 'nutrition_targets_select_own'
  ) then
    create policy "nutrition_targets_select_own"
    on public.nutrition_targets
    for select
    using (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'nutrition_targets'
      and policyname = 'nutrition_targets_insert_own'
  ) then
    create policy "nutrition_targets_insert_own"
    on public.nutrition_targets
    for insert
    with check (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'nutrition_targets'
      and policyname = 'nutrition_targets_update_own'
  ) then
    create policy "nutrition_targets_update_own"
    on public.nutrition_targets
    for update
    using (user_id = auth.uid())
    with check (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'food_logs'
      and policyname = 'food_logs_select_own'
  ) then
    create policy "food_logs_select_own"
    on public.food_logs
    for select
    using (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'food_logs'
      and policyname = 'food_logs_insert_own'
  ) then
    create policy "food_logs_insert_own"
    on public.food_logs
    for insert
    with check (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'food_logs'
      and policyname = 'food_logs_update_own'
  ) then
    create policy "food_logs_update_own"
    on public.food_logs
    for update
    using (user_id = auth.uid())
    with check (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'food_log_items'
      and policyname = 'food_log_items_select_own'
  ) then
    create policy "food_log_items_select_own"
    on public.food_log_items
    for select
    using (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'food_log_items'
      and policyname = 'food_log_items_insert_own'
  ) then
    create policy "food_log_items_insert_own"
    on public.food_log_items
    for insert
    with check (user_id = auth.uid());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'food_log_items'
      and policyname = 'food_log_items_update_own'
  ) then
    create policy "food_log_items_update_own"
    on public.food_log_items
    for update
    using (user_id = auth.uid())
    with check (user_id = auth.uid());
  end if;
end $$;

revoke all on table public.nutrition_preferences from public;
revoke all on table public.nutrition_preferences from anon;
revoke all on table public.nutrition_preferences from authenticated;

revoke all on table public.foods from public;
revoke all on table public.foods from anon;
revoke all on table public.foods from authenticated;
grant select on table public.foods to authenticated;

revoke all on table public.food_portions from public;
revoke all on table public.food_portions from anon;
revoke all on table public.food_portions from authenticated;
grant select on table public.food_portions to authenticated;

revoke all on table public.nutrition_targets from public;
revoke all on table public.nutrition_targets from anon;
revoke all on table public.nutrition_targets from authenticated;

revoke all on table public.food_logs from public;
revoke all on table public.food_logs from anon;
revoke all on table public.food_logs from authenticated;

revoke all on table public.food_log_items from public;
revoke all on table public.food_log_items from anon;
revoke all on table public.food_log_items from authenticated;

revoke all on function public.fmz_phase4_touch_updated_at() from public;
revoke all on function public.fmz_phase4_touch_updated_at() from anon;
revoke all on function public.fmz_phase4_touch_updated_at() from authenticated;

revoke all on function public.fmz_phase4_sync_archive_state() from public;
revoke all on function public.fmz_phase4_sync_archive_state() from anon;
revoke all on function public.fmz_phase4_sync_archive_state() from authenticated;

revoke all on function public.fmz_phase4_has_full_nutrition_access(uuid) from public;
revoke all on function public.fmz_phase4_has_full_nutrition_access(uuid) from anon;
revoke all on function public.fmz_phase4_has_full_nutrition_access(uuid) from authenticated;

revoke all on function public.fmz_phase4_enforce_custom_food_limit() from public;
revoke all on function public.fmz_phase4_enforce_custom_food_limit() from anon;
revoke all on function public.fmz_phase4_enforce_custom_food_limit() from authenticated;

revoke all on function public.fmz_phase4_enforce_food_portion_owner() from public;
revoke all on function public.fmz_phase4_enforce_food_portion_owner() from anon;
revoke all on function public.fmz_phase4_enforce_food_portion_owner() from authenticated;

revoke all on function public.fmz_phase4_enforce_target_owner() from public;
revoke all on function public.fmz_phase4_enforce_target_owner() from anon;
revoke all on function public.fmz_phase4_enforce_target_owner() from authenticated;

revoke all on function public.fmz_phase4_enforce_food_log_owner() from public;
revoke all on function public.fmz_phase4_enforce_food_log_owner() from anon;
revoke all on function public.fmz_phase4_enforce_food_log_owner() from authenticated;

revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from public;
revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from anon;
revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from authenticated;

revoke all on function public.fmz_phase4_day_payload(uuid, date) from public;
revoke all on function public.fmz_phase4_day_payload(uuid, date) from anon;
revoke all on function public.fmz_phase4_day_payload(uuid, date) from authenticated;

revoke all on function public.fmz_phase4_set_nutrition_timezone(text) from public;
revoke all on function public.fmz_phase4_set_nutrition_timezone(text) from anon;
revoke all on function public.fmz_phase4_set_nutrition_timezone(text) from authenticated;
grant execute on function public.fmz_phase4_set_nutrition_timezone(text) to authenticated;

revoke all on function public.fmz_phase4_search_foods(text, integer, text, uuid) from public;
revoke all on function public.fmz_phase4_search_foods(text, integer, text, uuid) from anon;
revoke all on function public.fmz_phase4_search_foods(text, integer, text, uuid) from authenticated;
grant execute on function public.fmz_phase4_search_foods(text, integer, text, uuid) to authenticated;

revoke all on function public.fmz_phase4_upsert_custom_food(
  uuid, text, text, numeric, text, numeric, numeric, numeric,
  numeric, numeric, numeric, numeric, numeric, timestamptz
) from public;
revoke all on function public.fmz_phase4_upsert_custom_food(
  uuid, text, text, numeric, text, numeric, numeric, numeric,
  numeric, numeric, numeric, numeric, numeric, timestamptz
) from anon;
revoke all on function public.fmz_phase4_upsert_custom_food(
  uuid, text, text, numeric, text, numeric, numeric, numeric,
  numeric, numeric, numeric, numeric, numeric, timestamptz
) from authenticated;
grant execute on function public.fmz_phase4_upsert_custom_food(
  uuid, text, text, numeric, text, numeric, numeric, numeric,
  numeric, numeric, numeric, numeric, numeric, timestamptz
) to authenticated;

revoke all on function public.fmz_phase4_archive_custom_food(uuid, timestamptz) from public;
revoke all on function public.fmz_phase4_archive_custom_food(uuid, timestamptz) from anon;
revoke all on function public.fmz_phase4_archive_custom_food(uuid, timestamptz) from authenticated;
grant execute on function public.fmz_phase4_archive_custom_food(uuid, timestamptz) to authenticated;

revoke all on function public.fmz_phase4_upsert_food_portion(
  uuid, uuid, text, numeric, text, numeric, text, boolean, timestamptz
) from public;
revoke all on function public.fmz_phase4_upsert_food_portion(
  uuid, uuid, text, numeric, text, numeric, text, boolean, timestamptz
) from anon;
revoke all on function public.fmz_phase4_upsert_food_portion(
  uuid, uuid, text, numeric, text, numeric, text, boolean, timestamptz
) from authenticated;
grant execute on function public.fmz_phase4_upsert_food_portion(
  uuid, uuid, text, numeric, text, numeric, text, boolean, timestamptz
) to authenticated;

revoke all on function public.fmz_phase4_save_member_target(
  uuid, uuid, numeric, numeric, numeric, numeric, numeric, date
) from public;
revoke all on function public.fmz_phase4_save_member_target(
  uuid, uuid, numeric, numeric, numeric, numeric, numeric, date
) from anon;
revoke all on function public.fmz_phase4_save_member_target(
  uuid, uuid, numeric, numeric, numeric, numeric, numeric, date
) from authenticated;
grant execute on function public.fmz_phase4_save_member_target(
  uuid, uuid, numeric, numeric, numeric, numeric, numeric, date
) to authenticated;

revoke all on function public.fmz_phase4_get_current_nutrition_target() from public;
revoke all on function public.fmz_phase4_get_current_nutrition_target() from anon;
revoke all on function public.fmz_phase4_get_current_nutrition_target() from authenticated;
grant execute on function public.fmz_phase4_get_current_nutrition_target() to authenticated;

revoke all on function public.fmz_phase4_log_food_item(
  uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamptz
) from public;
revoke all on function public.fmz_phase4_log_food_item(
  uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamptz
) from anon;
revoke all on function public.fmz_phase4_log_food_item(
  uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamptz
) from authenticated;
grant execute on function public.fmz_phase4_log_food_item(
  uuid, uuid, date, text, smallint, text, uuid, uuid, numeric, text, text, timestamptz
) to authenticated;

revoke all on function public.fmz_phase4_archive_food_log_item(uuid, timestamptz) from public;
revoke all on function public.fmz_phase4_archive_food_log_item(uuid, timestamptz) from anon;
revoke all on function public.fmz_phase4_archive_food_log_item(uuid, timestamptz) from authenticated;
grant execute on function public.fmz_phase4_archive_food_log_item(uuid, timestamptz) to authenticated;

revoke all on function public.fmz_phase4_get_nutrition_day(date) from public;
revoke all on function public.fmz_phase4_get_nutrition_day(date) from anon;
revoke all on function public.fmz_phase4_get_nutrition_day(date) from authenticated;
grant execute on function public.fmz_phase4_get_nutrition_day(date) to authenticated;

revoke all on function public.fmz_phase4_get_nutrition_history(date, integer) from public;
revoke all on function public.fmz_phase4_get_nutrition_history(date, integer) from anon;
revoke all on function public.fmz_phase4_get_nutrition_history(date, integer) from authenticated;
grant execute on function public.fmz_phase4_get_nutrition_history(date, integer) to authenticated;

commit;
