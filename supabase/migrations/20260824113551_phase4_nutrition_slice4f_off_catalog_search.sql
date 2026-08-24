-- FitMetZorge Phase 4 Nutrition - Slice 4F OFF Catalog + Local Search Foundation
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Additive ODbL-isolated schema and read-only search/barcode RPC foundation.
-- No OFF rows, member-log writes, provider calls, scanner runtime, legacy changes,
-- trainer access, Edge deployment, frontend deployment, AI, or production change.

begin;

create extension if not exists pg_trgm with schema extensions;
create extension if not exists pgcrypto with schema extensions;

do $$
begin
  if exists (
    select 1
    from (values ('pg_trgm'::text), ('pgcrypto'::text)) required(extension_name)
    where not exists (
      select 1
      from pg_catalog.pg_extension e
      join pg_catalog.pg_namespace n on n.oid = e.extnamespace
      where e.extname = required.extension_name
        and n.nspname = 'extensions'
    )
  ) then
    raise exception 'pg_trgm and pgcrypto must be installed in the Supabase extensions schema';
  end if;
end $$;

create or replace function public.fmz_phase4_normalize_gtin14(p_barcode text)
returns text
language plpgsql
immutable
strict
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_barcode text := btrim(p_barcode);
  v_gtin14 text;
  v_sum integer := 0;
  v_position integer;
  v_expected_check integer;
begin
  if v_barcode !~ '^[0-9]+$'
     or char_length(v_barcode) not in (8, 12, 13, 14) then
    return null;
  end if;

  v_gtin14 := lpad(v_barcode, 14, '0');

  for v_position in 1..13 loop
    v_sum := v_sum
      + substring(v_gtin14 from v_position for 1)::integer
        * case when mod(v_position, 2) = 1 then 3 else 1 end;
  end loop;

  v_expected_check := mod(10 - mod(v_sum, 10), 10);
  if substring(v_gtin14 from 14 for 1)::integer <> v_expected_check then
    return null;
  end if;

  return v_gtin14;
end;
$$;

create or replace function public.fmz_phase4_provider_candidate_uuid_v5(p_identity_name text)
returns uuid
language plpgsql
immutable
strict
security invoker
set search_path = pg_catalog, extensions, pg_temp
as $$
declare
  v_hash bytea;
  v_hex text;
begin
  v_hash := extensions.digest(
    pg_catalog.decode(pg_catalog.replace('23440733-7e58-4c21-ad15-591eae6ab8ac', '-', ''), 'hex')
      || pg_catalog.convert_to(p_identity_name, 'UTF8'),
    'sha1'
  );
  v_hash := pg_catalog.set_byte(v_hash, 6, (pg_catalog.get_byte(v_hash, 6) & 15) | 80);
  v_hash := pg_catalog.set_byte(v_hash, 8, (pg_catalog.get_byte(v_hash, 8) & 63) | 128);
  v_hex := pg_catalog.encode(pg_catalog.substr(v_hash, 1, 16), 'hex');

  return (
    pg_catalog.substr(v_hex, 1, 8) || '-' ||
    pg_catalog.substr(v_hex, 9, 4) || '-' ||
    pg_catalog.substr(v_hex, 13, 4) || '-' ||
    pg_catalog.substr(v_hex, 17, 4) || '-' ||
    pg_catalog.substr(v_hex, 21, 12)
  )::uuid;
end;
$$;

create or replace function public.fmz_phase4_normalize_catalog_text(p_value text)
returns text
language sql
immutable
strict
security invoker
set search_path = pg_catalog, pg_temp
as $$
  select btrim(
    pg_catalog.regexp_replace(
      pg_catalog.regexp_replace(lower(btrim(p_value)), '[^[:alnum:]]+', ' ', 'g'),
      '[[:space:]]+',
      ' ',
      'g'
    )
  );
$$;

create table if not exists public.nutrition_off_catalog_releases (
  id uuid primary key,
  source_provider text not null default 'open_food_facts',
  source_revision text not null,
  source_snapshot_at timestamptz not null,
  source_file_sha256 text not null,
  normalized_artifact_sha256 text not null,
  license_code text not null default 'ODbL-1.0',
  license_url text not null default 'https://opendatacommons.org/licenses/odbl/1-0/',
  attribution_text text not null default 'Open Food Facts contributors',
  netherlands_source_count integer not null,
  eligible_product_count integer not null,
  imported_product_count integer not null default 0,
  mapping_version text not null,
  predecessor_release_id uuid references public.nutrition_off_catalog_releases(id) on delete restrict,
  status text not null default 'reviewed',
  reviewed_by text not null,
  reviewed_at timestamptz not null,
  imported_at timestamptz,
  provenance jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint nutrition_off_releases_artifact_sha_key unique (normalized_artifact_sha256),
  constraint nutrition_off_releases_provider_check
    check (source_provider = 'open_food_facts'),
  constraint nutrition_off_releases_revision_check
    check (char_length(btrim(source_revision)) between 7 and 160),
  constraint nutrition_off_releases_source_sha_check
    check (source_file_sha256 ~ '^[A-F0-9]{64}$'),
  constraint nutrition_off_releases_artifact_sha_check
    check (normalized_artifact_sha256 ~ '^[A-F0-9]{64}$'),
  constraint nutrition_off_releases_license_check
    check (
      license_code = 'ODbL-1.0'
      and license_url = 'https://opendatacommons.org/licenses/odbl/1-0/'
      and char_length(btrim(attribution_text)) between 3 and 240
    ),
  constraint nutrition_off_releases_count_check
    check (
      netherlands_source_count between 0 and 5000000
      and eligible_product_count between 0 and netherlands_source_count
      and imported_product_count between 0 and eligible_product_count
    ),
  constraint nutrition_off_releases_mapping_check
    check (char_length(btrim(mapping_version)) between 1 and 120),
  constraint nutrition_off_releases_predecessor_check
    check (predecessor_release_id is null or predecessor_release_id <> id),
  constraint nutrition_off_releases_status_check
    check (status in ('reviewed', 'imported', 'superseded', 'rejected')),
  constraint nutrition_off_releases_review_check
    check (char_length(btrim(reviewed_by)) between 1 and 120),
  constraint nutrition_off_releases_timestamps_check
    check (
      updated_at >= created_at
      and reviewed_at >= source_snapshot_at
      and (
        (
          status in ('reviewed', 'rejected')
          and imported_at is null
          and imported_product_count = 0
        )
        or
        (
          status in ('imported', 'superseded')
          and imported_at is not null
          and imported_at >= reviewed_at
          and imported_product_count = eligible_product_count
        )
      )
    ),
  constraint nutrition_off_releases_json_check
    check (jsonb_typeof(provenance) = 'object' and jsonb_typeof(metadata) = 'object')
);

create table if not exists public.nutrition_off_products (
  id uuid primary key,
  release_id uuid not null references public.nutrition_off_catalog_releases(id) on delete restrict,
  source_provider text not null default 'open_food_facts',
  off_code text not null,
  barcode_original text not null,
  normalized_gtin14 text not null,
  provider_identity_name text not null,
  product_name text not null,
  product_name_nl text,
  generic_name text,
  brand text,
  normalized_brand text,
  quantity_text text,
  serving_size_text text,
  nutrition_basis text,
  energy_kcal_100 numeric(10,3),
  protein_grams_100 numeric(10,3),
  carbohydrate_grams_100 numeric(10,3),
  fat_grams_100 numeric(10,3),
  fiber_grams_100 numeric(10,3),
  countries_tags text[] not null default '{}'::text[],
  is_netherlands_associated boolean not null default true,
  off_revision text not null,
  source_updated_at timestamptz,
  source_checksum text not null,
  provenance jsonb not null default '{}'::jsonb,
  license_code text not null default 'ODbL-1.0',
  license_url text not null default 'https://opendatacommons.org/licenses/odbl/1-0/',
  attribution_text text not null default 'Open Food Facts contributors',
  image_reference_url text,
  image_license_code text,
  image_attribution text,
  completeness jsonb not null default '{}'::jsonb,
  quality_status text not null default 'incomplete',
  lifecycle_status text not null default 'active',
  imported_at timestamptz not null,
  refreshed_at timestamptz not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint nutrition_off_products_gtin_key unique (normalized_gtin14),
  constraint nutrition_off_products_identity_name_key unique (provider_identity_name),
  constraint nutrition_off_products_provider_check
    check (source_provider = 'open_food_facts'),
  constraint nutrition_off_products_off_code_check
    check (off_code = barcode_original),
  constraint nutrition_off_products_barcode_check
    check (
      barcode_original ~ '^[0-9]+$'
      and char_length(barcode_original) in (8, 12, 13, 14)
      and public.fmz_phase4_normalize_gtin14(barcode_original) = normalized_gtin14
      and normalized_gtin14 ~ '^[0-9]{14}$'
    ),
  constraint nutrition_off_products_identity_check
    check (
      provider_identity_name = 'open_food_facts:' || normalized_gtin14
      and id = public.fmz_phase4_provider_candidate_uuid_v5(provider_identity_name)
    ),
  constraint nutrition_off_products_name_check
    check (char_length(btrim(product_name)) between 1 and 240),
  constraint nutrition_off_products_nl_name_check
    check (product_name_nl is null or char_length(btrim(product_name_nl)) between 1 and 240),
  constraint nutrition_off_products_generic_name_check
    check (generic_name is null or char_length(btrim(generic_name)) between 1 and 240),
  constraint nutrition_off_products_brand_check
    check (
      (
        brand is null
        and normalized_brand is null
      )
      or
      (
        char_length(btrim(brand)) between 1 and 160
        and char_length(normalized_brand) between 1 and 160
        and normalized_brand = public.fmz_phase4_normalize_catalog_text(brand)
        and normalized_brand ~ '[[:alnum:]]'
        and normalized_brand !~ '[[:space:]]{2,}'
      )
    ),
  constraint nutrition_off_products_quantity_check
    check (quantity_text is null or char_length(btrim(quantity_text)) between 1 and 120),
  constraint nutrition_off_products_serving_check
    check (serving_size_text is null or char_length(btrim(serving_size_text)) between 1 and 120),
  constraint nutrition_off_products_basis_check
    check (nutrition_basis is null or nutrition_basis in ('per_100_g', 'per_100_ml')),
  constraint nutrition_off_products_energy_check
    check (
      energy_kcal_100 is null
      or (
        energy_kcal_100::text not in ('NaN', 'Infinity', '-Infinity')
        and energy_kcal_100 between 0 and 900
      )
    ),
  constraint nutrition_off_products_protein_check
    check (
      protein_grams_100 is null
      or (
        protein_grams_100::text not in ('NaN', 'Infinity', '-Infinity')
        and protein_grams_100 between 0 and 100
      )
    ),
  constraint nutrition_off_products_carbohydrate_check
    check (
      carbohydrate_grams_100 is null
      or (
        carbohydrate_grams_100::text not in ('NaN', 'Infinity', '-Infinity')
        and carbohydrate_grams_100 between 0 and 100
      )
    ),
  constraint nutrition_off_products_fat_check
    check (
      fat_grams_100 is null
      or (
        fat_grams_100::text not in ('NaN', 'Infinity', '-Infinity')
        and fat_grams_100 between 0 and 100
      )
    ),
  constraint nutrition_off_products_fiber_check
    check (
      fiber_grams_100 is null
      or (
        fiber_grams_100::text not in ('NaN', 'Infinity', '-Infinity')
        and fiber_grams_100 between 0 and 100
      )
    ),
  constraint nutrition_off_products_market_check
    check (
      is_netherlands_associated
      and countries_tags @> array['en:netherlands']::text[]
    ),
  constraint nutrition_off_products_revision_check
    check (char_length(btrim(off_revision)) between 7 and 160),
  constraint nutrition_off_products_source_checksum_check
    check (source_checksum ~ '^[A-F0-9]{64}$'),
  constraint nutrition_off_products_license_check
    check (
      license_code = 'ODbL-1.0'
      and license_url = 'https://opendatacommons.org/licenses/odbl/1-0/'
      and char_length(btrim(attribution_text)) between 3 and 240
    ),
  constraint nutrition_off_products_image_check
    check (
      (
        image_reference_url is null
        and image_license_code is null
        and image_attribution is null
      )
      or
      (
        image_reference_url ~ '^https://'
        and image_license_code = 'CC-BY-SA-4.0'
        and char_length(btrim(image_attribution)) between 3 and 240
      )
    ),
  constraint nutrition_off_products_quality_check
    check (quality_status in ('incomplete', 'complete', 'reviewed', 'quarantined')),
  constraint nutrition_off_products_lifecycle_check
    check (lifecycle_status in ('active', 'archived')),
  constraint nutrition_off_products_loggable_check
    check (
      quality_status not in ('complete', 'reviewed')
      or (
        brand is not null
        and nutrition_basis in ('per_100_g', 'per_100_ml')
        and energy_kcal_100 is not null
        and protein_grams_100 is not null
        and carbohydrate_grams_100 is not null
        and fat_grams_100 is not null
        and is_netherlands_associated
      )
    ),
  constraint nutrition_off_products_quarantine_check
    check (
      quality_status <> 'quarantined'
      or (
        metadata ? 'quarantine_reason'
        and char_length(btrim(metadata ->> 'quarantine_reason')) between 3 and 500
      )
    ),
  constraint nutrition_off_products_json_check
    check (
      jsonb_typeof(provenance) = 'object'
      and jsonb_typeof(completeness) = 'object'
      and jsonb_typeof(metadata) = 'object'
    ),
  constraint nutrition_off_products_archive_check
    check ((lifecycle_status = 'archived') = (archived_at is not null)),
  constraint nutrition_off_products_timestamps_check
    check (
      updated_at >= created_at
      and refreshed_at >= imported_at
      and (source_updated_at is null or imported_at >= source_updated_at)
    )
);

create table if not exists public.nutrition_off_product_names (
  id uuid primary key,
  product_id uuid not null references public.nutrition_off_products(id) on delete restrict,
  language_code text not null,
  name_type text not null,
  name text not null,
  normalized_name text not null,
  is_preferred boolean not null default false,
  source_provider text not null default 'open_food_facts',
  source_revision text not null,
  license_code text not null default 'ODbL-1.0',
  provenance jsonb not null default '{}'::jsonb,
  quality_status text not null default 'complete',
  lifecycle_status text not null default 'active',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint nutrition_off_product_names_language_check
    check (language_code ~ '^[a-z]{2,8}$'),
  constraint nutrition_off_product_names_type_check
    check (name_type in ('primary', 'localized', 'generic', 'brand', 'search_variant')),
  constraint nutrition_off_product_names_name_check
    check (char_length(btrim(name)) between 1 and 240),
  constraint nutrition_off_product_names_normalized_check
    check (
      char_length(normalized_name) between 1 and 240
      and normalized_name = public.fmz_phase4_normalize_catalog_text(name)
      and normalized_name ~ '[[:alnum:]]'
      and normalized_name !~ '[[:space:]]{2,}'
    ),
  constraint nutrition_off_product_names_provider_check
    check (source_provider = 'open_food_facts'),
  constraint nutrition_off_product_names_revision_check
    check (char_length(btrim(source_revision)) between 7 and 160),
  constraint nutrition_off_product_names_license_check
    check (license_code = 'ODbL-1.0'),
  constraint nutrition_off_product_names_quality_check
    check (quality_status in ('complete', 'reviewed', 'quarantined')),
  constraint nutrition_off_product_names_lifecycle_check
    check (lifecycle_status in ('active', 'archived')),
  constraint nutrition_off_product_names_json_check
    check (jsonb_typeof(provenance) = 'object' and jsonb_typeof(metadata) = 'object'),
  constraint nutrition_off_product_names_archive_check
    check ((lifecycle_status = 'archived') = (archived_at is not null))
);

create index if not exists nutrition_off_releases_status_snapshot_idx
  on public.nutrition_off_catalog_releases(status, source_snapshot_at desc, id);

create unique index if not exists nutrition_off_releases_predecessor_uidx
  on public.nutrition_off_catalog_releases(predecessor_release_id)
  where predecessor_release_id is not null;

create unique index if not exists nutrition_off_releases_current_uidx
  on public.nutrition_off_catalog_releases(source_provider)
  where status = 'imported';

create index if not exists nutrition_off_products_release_idx
  on public.nutrition_off_products(release_id, lifecycle_status, quality_status, id);

create index if not exists nutrition_off_products_active_name_prefix_idx
  on public.nutrition_off_products((lower(product_name)) text_pattern_ops, id)
  where lifecycle_status = 'active' and quality_status in ('complete', 'reviewed');

create index if not exists nutrition_off_products_active_nl_name_prefix_idx
  on public.nutrition_off_products((lower(product_name_nl)) text_pattern_ops, id)
  where lifecycle_status = 'active'
    and quality_status in ('complete', 'reviewed')
    and product_name_nl is not null;

create index if not exists nutrition_off_products_active_brand_prefix_idx
  on public.nutrition_off_products(normalized_brand text_pattern_ops, id)
  where lifecycle_status = 'active'
    and quality_status in ('complete', 'reviewed')
    and normalized_brand is not null;

create index if not exists nutrition_off_products_source_updated_idx
  on public.nutrition_off_products(source_updated_at desc, normalized_gtin14)
  where lifecycle_status = 'active';

create unique index if not exists nutrition_off_product_names_active_identity_uidx
  on public.nutrition_off_product_names(
    product_id,
    language_code,
    name_type,
    normalized_name
  )
  where lifecycle_status = 'active';

create unique index if not exists nutrition_off_product_names_preferred_uidx
  on public.nutrition_off_product_names(product_id, language_code)
  where lifecycle_status = 'active'
    and quality_status in ('complete', 'reviewed')
    and is_preferred;

create index if not exists nutrition_off_product_names_product_idx
  on public.nutrition_off_product_names(product_id, lifecycle_status, quality_status, id);

create index if not exists nutrition_off_product_names_active_exact_idx
  on public.nutrition_off_product_names(normalized_name, language_code, is_preferred desc, product_id, id)
  where lifecycle_status = 'active' and quality_status in ('complete', 'reviewed');

create index if not exists nutrition_off_product_names_active_prefix_idx
  on public.nutrition_off_product_names(
    normalized_name text_pattern_ops,
    language_code,
    is_preferred desc,
    product_id,
    id
  )
  where lifecycle_status = 'active' and quality_status in ('complete', 'reviewed');

create index if not exists nutrition_off_product_names_active_trgm_idx
  on public.nutrition_off_product_names using gin (normalized_name extensions.gin_trgm_ops)
  where lifecycle_status = 'active' and quality_status in ('complete', 'reviewed');

create or replace function public.fmz_phase4_enforce_off_release_state()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_predecessor_provider text;
  v_predecessor_status text;
  v_loggable_product_count bigint;
begin
  if tg_op = 'INSERT' then
    perform pg_catalog.pg_advisory_xact_lock(
      pg_catalog.hashtextextended('fmz_phase4_off_release_chain:' || new.source_provider, 0)
    );

    if new.status <> 'reviewed' then
      raise exception 'OFF release must enter the forward lifecycle as reviewed'
        using errcode = '22023';
    end if;

    if new.predecessor_release_id is null then
      if exists (
        select 1
        from public.nutrition_off_catalog_releases r
        where r.source_provider = new.source_provider
      ) then
        raise exception 'subsequent OFF release requires a predecessor'
          using errcode = '23514';
      end if;
    else
      select r.source_provider, r.status
      into v_predecessor_provider, v_predecessor_status
      from public.nutrition_off_catalog_releases r
      where r.id = new.predecessor_release_id
      for key share;

      if not found
         or v_predecessor_provider is distinct from new.source_provider
         or v_predecessor_status not in ('imported', 'superseded') then
        raise exception 'OFF release predecessor must be an imported release from the same provider'
          using errcode = '23514';
      end if;
    end if;

    return new;
  end if;

  if new.id is distinct from old.id
     or new.source_provider is distinct from old.source_provider
     or new.source_revision is distinct from old.source_revision
     or new.source_snapshot_at is distinct from old.source_snapshot_at
     or new.source_file_sha256 is distinct from old.source_file_sha256
     or new.normalized_artifact_sha256 is distinct from old.normalized_artifact_sha256
     or new.license_code is distinct from old.license_code
     or new.license_url is distinct from old.license_url
     or new.attribution_text is distinct from old.attribution_text
     or new.netherlands_source_count is distinct from old.netherlands_source_count
     or new.eligible_product_count is distinct from old.eligible_product_count
     or new.mapping_version is distinct from old.mapping_version
     or new.predecessor_release_id is distinct from old.predecessor_release_id
     or new.reviewed_by is distinct from old.reviewed_by
     or new.reviewed_at is distinct from old.reviewed_at
     or new.provenance is distinct from old.provenance
     or new.created_at is distinct from old.created_at then
    raise exception 'OFF release audit identity is immutable; use a successor release'
      using errcode = '55000';
  end if;

  if new.status is distinct from old.status
     and not (
       (old.status = 'reviewed' and new.status in ('imported', 'rejected'))
       or (old.status = 'imported' and new.status = 'superseded')
     ) then
    raise exception 'invalid OFF release status transition'
      using errcode = '22023';
  end if;

  if old.imported_at is not null
     and new.imported_at is distinct from old.imported_at then
    raise exception 'OFF release import timestamp is immutable'
      using errcode = '55000';
  end if;

  if old.imported_product_count > 0
     and new.imported_product_count is distinct from old.imported_product_count then
    raise exception 'OFF release imported count is immutable'
      using errcode = '55000';
  end if;

  if old.status = 'reviewed' and new.status = 'imported' then
    select count(*)
    into v_loggable_product_count
    from public.nutrition_off_products p
    where p.release_id = new.id
      and p.lifecycle_status = 'active'
      and p.quality_status in ('complete', 'reviewed');

    if v_loggable_product_count <> new.imported_product_count then
      raise exception 'OFF release imported count must equal active loggable products'
        using errcode = '23514';
    end if;
  end if;

  return new;
end;
$$;

create or replace function public.fmz_phase4_prevent_off_catalog_removal()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
begin
  raise exception 'OFF catalog objects use archive/successor workflows'
    using errcode = '55000';
end;
$$;

create or replace function public.fmz_phase4_sync_off_archive_state()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
begin
  if new.lifecycle_status = 'archived' then
    new.archived_at := coalesce(new.archived_at, now());
  else
    new.archived_at := null;
  end if;
  return new;
end;
$$;

create or replace function public.fmz_phase4_enforce_off_product_identity()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_release public.nutrition_off_catalog_releases%rowtype;
begin
  select r.*
  into v_release
  from public.nutrition_off_catalog_releases r
  where r.id = new.release_id
  for key share;

  if not found
     or v_release.source_provider <> 'open_food_facts'
     or v_release.source_revision is distinct from new.off_revision
     or v_release.status not in ('reviewed', 'imported') then
    raise exception 'OFF product must reference the matching reviewed/imported release'
      using errcode = '23514';
  end if;

  if public.fmz_phase4_normalize_gtin14(new.barcode_original) is distinct from new.normalized_gtin14 then
    raise exception 'OFF product barcode is not a valid EAN/UPC/GTIN identity'
      using errcode = '22023';
  end if;

  if tg_op = 'UPDATE'
     and (
       new.id is distinct from old.id
       or new.source_provider is distinct from old.source_provider
       or new.off_code is distinct from old.off_code
       or new.barcode_original is distinct from old.barcode_original
       or new.normalized_gtin14 is distinct from old.normalized_gtin14
       or new.provider_identity_name is distinct from old.provider_identity_name
       or new.created_at is distinct from old.created_at
     ) then
    raise exception 'OFF product identity is immutable; archive and use a new identity'
      using errcode = '55000';
  end if;

  return new;
end;
$$;

create or replace function public.fmz_phase4_enforce_off_product_name_identity()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_product public.nutrition_off_products%rowtype;
begin
  select p.*
  into v_product
  from public.nutrition_off_products p
  where p.id = new.product_id
  for key share;

  if not found
     or v_product.source_provider <> 'open_food_facts'
     or new.source_provider <> v_product.source_provider
     or new.source_revision is distinct from v_product.off_revision
     or new.license_code is distinct from v_product.license_code then
    raise exception 'OFF product name must match its product source revision and licence'
      using errcode = '23514';
  end if;

  if tg_op = 'UPDATE'
     and (
       new.id is distinct from old.id
       or new.product_id is distinct from old.product_id
       or new.language_code is distinct from old.language_code
       or new.name_type is distinct from old.name_type
       or new.normalized_name is distinct from old.normalized_name
       or new.source_provider is distinct from old.source_provider
       or new.created_at is distinct from old.created_at
     ) then
    raise exception 'OFF product-name identity is immutable; archive and add a successor name'
      using errcode = '55000';
  end if;

  return new;
end;
$$;

do $$
begin
  if not exists (
    select 1 from pg_catalog.pg_trigger
    where tgname = 'nutrition_off_releases_10_enforce_state'
      and tgrelid = 'public.nutrition_off_catalog_releases'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_off_releases_10_enforce_state
    before insert or update on public.nutrition_off_catalog_releases
    for each row execute function public.fmz_phase4_enforce_off_release_state();
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
    where tgname = 'nutrition_off_releases_20_prevent_removal'
      and tgrelid = 'public.nutrition_off_catalog_releases'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_off_releases_20_prevent_removal
    before delete on public.nutrition_off_catalog_releases
    for each row execute function public.fmz_phase4_prevent_off_catalog_removal();
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
    where tgname = 'nutrition_off_releases_90_touch_updated_at'
      and tgrelid = 'public.nutrition_off_catalog_releases'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_off_releases_90_touch_updated_at
    before update on public.nutrition_off_catalog_releases
    for each row execute function public.fmz_phase4_touch_updated_at();
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
    where tgname = 'nutrition_off_products_10_enforce_identity'
      and tgrelid = 'public.nutrition_off_products'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_off_products_10_enforce_identity
    before insert or update on public.nutrition_off_products
    for each row execute function public.fmz_phase4_enforce_off_product_identity();
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
    where tgname = 'nutrition_off_products_20_sync_archive_state'
      and tgrelid = 'public.nutrition_off_products'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_off_products_20_sync_archive_state
    before insert or update of lifecycle_status on public.nutrition_off_products
    for each row execute function public.fmz_phase4_sync_off_archive_state();
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
    where tgname = 'nutrition_off_products_30_prevent_removal'
      and tgrelid = 'public.nutrition_off_products'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_off_products_30_prevent_removal
    before delete on public.nutrition_off_products
    for each row execute function public.fmz_phase4_prevent_off_catalog_removal();
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
    where tgname = 'nutrition_off_products_90_touch_updated_at'
      and tgrelid = 'public.nutrition_off_products'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_off_products_90_touch_updated_at
    before update on public.nutrition_off_products
    for each row execute function public.fmz_phase4_touch_updated_at();
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
    where tgname = 'nutrition_off_names_10_enforce_identity'
      and tgrelid = 'public.nutrition_off_product_names'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_off_names_10_enforce_identity
    before insert or update on public.nutrition_off_product_names
    for each row execute function public.fmz_phase4_enforce_off_product_name_identity();
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
    where tgname = 'nutrition_off_names_20_sync_archive_state'
      and tgrelid = 'public.nutrition_off_product_names'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_off_names_20_sync_archive_state
    before insert or update of lifecycle_status on public.nutrition_off_product_names
    for each row execute function public.fmz_phase4_sync_off_archive_state();
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
    where tgname = 'nutrition_off_names_30_prevent_removal'
      and tgrelid = 'public.nutrition_off_product_names'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_off_names_30_prevent_removal
    before delete on public.nutrition_off_product_names
    for each row execute function public.fmz_phase4_prevent_off_catalog_removal();
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
    where tgname = 'nutrition_off_names_90_touch_updated_at'
      and tgrelid = 'public.nutrition_off_product_names'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_off_names_90_touch_updated_at
    before update on public.nutrition_off_product_names
    for each row execute function public.fmz_phase4_touch_updated_at();
  end if;
end $$;

alter table public.nutrition_off_catalog_releases enable row level security;
alter table public.nutrition_off_products enable row level security;
alter table public.nutrition_off_product_names enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'nutrition_off_products'
      and policyname = 'nutrition_off_products_select_loggable'
  ) then
    create policy "nutrition_off_products_select_loggable"
    on public.nutrition_off_products
    for select
    to authenticated
    using (
      lifecycle_status = 'active'
      and quality_status in ('complete', 'reviewed')
    );
  end if;

  if not exists (
    select 1 from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'nutrition_off_product_names'
      and policyname = 'nutrition_off_product_names_select_loggable'
  ) then
    create policy "nutrition_off_product_names_select_loggable"
    on public.nutrition_off_product_names
    for select
    to authenticated
    using (
      lifecycle_status = 'active'
      and quality_status in ('complete', 'reviewed')
      and exists (
        select 1
        from public.nutrition_off_products p
        where p.id = nutrition_off_product_names.product_id
          and p.lifecycle_status = 'active'
          and p.quality_status in ('complete', 'reviewed')
      )
    );
  end if;
end $$;

create or replace function public.fmz_phase4_search_nutrition_catalog(
  p_query text default null,
  p_locale text default 'nl',
  p_page_size integer default 25,
  p_after_rank integer default null,
  p_after_score numeric default null,
  p_after_name text default null,
  p_after_source text default null,
  p_after_id uuid default null
)
returns table (
  result_type text,
  source_provider text,
  source_id uuid,
  barcode text,
  display_name text,
  brand text,
  nutrition_basis text,
  reference_amount numeric,
  reference_unit text,
  energy_kcal_reference numeric,
  protein_grams_reference numeric,
  carbohydrate_grams_reference numeric,
  fat_grams_reference numeric,
  fiber_grams_reference numeric,
  quality_status text,
  loggable boolean,
  rank_tier integer,
  rank_score numeric,
  cursor_name text,
  cursor_source text,
  cursor_id uuid
)
language plpgsql
stable
security invoker
set search_path = pg_catalog, public, extensions, pg_temp
set pg_trgm.similarity_threshold = 0.3
as $$
declare
  v_user_id uuid := auth.uid();
  v_locale text := lower(btrim(coalesce(p_locale, 'nl')));
  v_query text := public.fmz_phase4_normalize_catalog_text(coalesce(p_query, ''));
  v_gtin14 text := public.fmz_phase4_normalize_gtin14(btrim(coalesce(p_query, '')));
  v_page_size integer := greatest(1, least(coalesce(p_page_size, 25), 25));
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if v_locale not in ('nl', 'en', 'de') then
    raise exception 'unsupported catalog locale'
      using errcode = '22023';
  end if;

  if char_length(v_query) > 120 then
    raise exception 'catalog query is too long'
      using errcode = '22023';
  end if;

  if (p_after_rank is null) <> (p_after_score is null)
     or (p_after_rank is null) <> (p_after_name is null)
     or (p_after_rank is null) <> (p_after_source is null)
     or (p_after_rank is null) <> (p_after_id is null) then
    raise exception 'complete catalog cursor required'
      using errcode = '22023';
  end if;

  return query
  with empty_food_candidates as (
    select
      case when f.catalog_scope = 'custom' then 'custom_food' else 'generic_food' end as source_type,
      f.id as candidate_id,
      100::integer as match_tier,
      case when f.catalog_scope = 'custom' then 2::numeric else 1::numeric end as match_score
    from public.foods f
    where v_query = ''
      and f.status = 'active'
      and (
        (f.catalog_scope = 'custom' and f.owner_user_id = v_user_id)
        or (
          f.catalog_scope = 'canonical'
          and f.quality_status in ('reviewed', 'verified')
          and f.ingestion_id is not null
        )
      )
    order by match_score desc, f.name, f.id
    limit 100
  ),
  empty_off_candidates as (
    select 'off_branded_food', p.id, 100, case when p.quality_status = 'reviewed' then 2::numeric else 1::numeric end
    from public.nutrition_off_products p
    where v_query = ''
      and p.lifecycle_status = 'active'
      and p.quality_status in ('complete', 'reviewed')
    order by p.quality_status desc, coalesce(p.product_name_nl, p.product_name), p.id
    limit 100
  ),
  exact_off_barcode_candidates as (
    select 'off_branded_food', p.id, 0, case when p.quality_status = 'reviewed' then 2::numeric else 1::numeric end
    from public.nutrition_off_products p
    where v_gtin14 is not null
      and p.normalized_gtin14 = v_gtin14
      and p.lifecycle_status = 'active'
      and p.quality_status in ('complete', 'reviewed')
    limit 1
  ),
  exact_food_barcode_candidates as (
    select case when f.catalog_scope = 'custom' then 'custom_food' else 'generic_food' end,
      f.id, 0, case when f.quality_status in ('verified', 'reviewed') then 2::numeric else 1::numeric end
    from public.foods f
    where v_gtin14 is not null
      and public.fmz_phase4_normalize_gtin14(f.barcode) = v_gtin14
      and f.status = 'active'
      and (
        (f.catalog_scope = 'custom' and f.owner_user_id = v_user_id)
        or (
          f.catalog_scope = 'canonical'
          and f.quality_status in ('reviewed', 'verified')
          and f.ingestion_id is not null
        )
      )
    order by case when f.catalog_scope = 'custom' then 0 else 1 end, f.id
    limit 25
  ),
  exact_custom_name_candidates as (
    select 'custom_food', f.id, 10, 2::numeric
    from public.foods f
    where v_query <> ''
      and f.catalog_scope = 'custom'
      and f.owner_user_id = v_user_id
      and f.status = 'active'
      and lower(btrim(f.name)) = v_query
    order by f.id
    limit 25
  ),
  exact_off_nl_name_candidates as (
    select 'off_branded_food', n.product_id, 20,
      (case when p.quality_status = 'reviewed' then 2 else 1 end
       + case when n.is_preferred then 0.20 else 0 end)::numeric
    from public.nutrition_off_product_names n
    join public.nutrition_off_products p on p.id = n.product_id
    where v_query <> ''
      and n.language_code = 'nl'
      and n.normalized_name = v_query
      and n.lifecycle_status = 'active'
      and n.quality_status in ('complete', 'reviewed')
      and p.lifecycle_status = 'active'
      and p.quality_status in ('complete', 'reviewed')
    order by n.is_preferred desc, p.quality_status desc, n.product_id
    limit 100
  ),
  exact_off_other_name_candidates as (
    select 'off_branded_food', n.product_id, 30,
      (case when p.quality_status = 'reviewed' then 2 else 1 end
       + case when n.is_preferred then 0.20 else 0 end)::numeric
    from public.nutrition_off_product_names n
    join public.nutrition_off_products p on p.id = n.product_id
    where v_query <> ''
      and n.language_code <> 'nl'
      and n.name_type in ('primary', 'localized')
      and n.normalized_name = v_query
      and n.lifecycle_status = 'active'
      and n.quality_status in ('complete', 'reviewed')
      and p.lifecycle_status = 'active'
      and p.quality_status in ('complete', 'reviewed')
    order by n.is_preferred desc, p.quality_status desc, n.product_id
    limit 100
  ),
  exact_off_brand_candidates as (
    select 'off_branded_food', p.id, 40,
      (case when p.quality_status = 'reviewed' then 2 else 1 end)::numeric
    from public.nutrition_off_products p
    where v_query <> ''
      and p.lifecycle_status = 'active'
      and p.quality_status in ('complete', 'reviewed')
      and (
        p.normalized_brand = v_query
        or public.fmz_phase4_normalize_catalog_text(
          coalesce(p.brand, '') || ' ' || coalesce(p.product_name_nl, p.product_name)
        ) = v_query
      )
    order by p.quality_status desc, coalesce(p.product_name_nl, p.product_name), p.id
    limit 100
  ),
  exact_generic_alias_candidates as (
    select 'generic_food', a.food_id, 50,
      (2 + case when a.is_preferred then 0.20 else 0 end + greatest(a.priority, 0)::numeric / 1000)::numeric
    from public.food_aliases a
    join public.foods f on f.id = a.food_id
    where v_query <> ''
      and a.normalized_alias = v_query
      and a.status = 'active'
      and a.review_status in ('reviewed', 'verified')
      and f.status = 'active'
      and f.catalog_scope = 'canonical'
      and f.quality_status in ('reviewed', 'verified')
      and f.ingestion_id is not null
    order by a.is_preferred desc, a.priority desc, a.food_id
    limit 100
  ),
  prefix_off_name_candidates as (
    select 'off_branded_food', n.product_id, 60,
      (case when p.quality_status = 'reviewed' then 2 else 1 end
       + case when n.language_code = 'nl' then 0.20 else 0 end
       + case when n.is_preferred then 0.10 else 0 end)::numeric
    from public.nutrition_off_product_names n
    join public.nutrition_off_products p on p.id = n.product_id
    where char_length(v_query) >= 2
      and n.normalized_name like v_query || '%'
      and n.lifecycle_status = 'active'
      and n.quality_status in ('complete', 'reviewed')
      and p.lifecycle_status = 'active'
      and p.quality_status in ('complete', 'reviewed')
    order by (n.language_code = 'nl') desc, n.is_preferred desc, n.normalized_name, n.product_id
    limit 150
  ),
  prefix_custom_name_candidates as (
    select 'custom_food', f.id, 65, 2::numeric
    from public.foods f
    where char_length(v_query) >= 2
      and f.catalog_scope = 'custom'
      and f.owner_user_id = v_user_id
      and f.status = 'active'
      and lower(f.name) like v_query || '%'
    order by lower(f.name), f.id
    limit 100
  ),
  prefix_generic_alias_candidates as (
    select 'generic_food', a.food_id, 70,
      (2 + case when a.is_preferred then 0.20 else 0 end + greatest(a.priority, 0)::numeric / 1000)::numeric
    from public.food_aliases a
    join public.foods f on f.id = a.food_id
    where char_length(v_query) >= 2
      and a.normalized_alias like v_query || '%'
      and a.status = 'active'
      and a.review_status in ('reviewed', 'verified')
      and f.status = 'active'
      and f.catalog_scope = 'canonical'
      and f.quality_status in ('reviewed', 'verified')
      and f.ingestion_id is not null
    order by a.is_preferred desc, a.priority desc, a.normalized_alias, a.food_id
    limit 150
  ),
  prefix_generic_name_candidates as (
    select 'generic_food', f.id, 71, 2::numeric
    from public.foods f
    where char_length(v_query) >= 2
      and f.status = 'active'
      and f.catalog_scope = 'canonical'
      and f.quality_status in ('reviewed', 'verified')
      and f.ingestion_id is not null
      and lower(f.name) like v_query || '%'
    order by lower(f.name), f.id
    limit 150
  ),
  trigram_off_name_candidates as (
    select 'off_branded_food', n.product_id, 80,
      (case when p.quality_status = 'reviewed' then 2 else 1 end
       + extensions.similarity(n.normalized_name, v_query))::numeric
    from public.nutrition_off_product_names n
    join public.nutrition_off_products p on p.id = n.product_id
    where char_length(v_query) >= 3
      and n.normalized_name operator(extensions.%) v_query
      and extensions.similarity(n.normalized_name, v_query) >= 0.30
      and n.lifecycle_status = 'active'
      and n.quality_status in ('complete', 'reviewed')
      and p.lifecycle_status = 'active'
      and p.quality_status in ('complete', 'reviewed')
    order by extensions.similarity(n.normalized_name, v_query) desc, n.normalized_name, n.product_id
    limit 200
  ),
  trigram_generic_alias_candidates as (
    select 'generic_food', a.food_id, 90,
      (2 + extensions.similarity(a.normalized_alias, v_query))::numeric
    from public.food_aliases a
    join public.foods f on f.id = a.food_id
    where char_length(v_query) >= 3
      and a.normalized_alias operator(extensions.%) v_query
      and extensions.similarity(a.normalized_alias, v_query) >= 0.30
      and a.status = 'active'
      and a.review_status in ('reviewed', 'verified')
      and f.status = 'active'
      and f.catalog_scope = 'canonical'
      and f.quality_status in ('reviewed', 'verified')
      and f.ingestion_id is not null
    order by extensions.similarity(a.normalized_alias, v_query) desc, a.normalized_alias, a.food_id
    limit 200
  ),
  raw_candidates as (
    select * from empty_food_candidates
    union all select * from empty_off_candidates
    union all select * from exact_off_barcode_candidates
    union all select * from exact_food_barcode_candidates
    union all select * from exact_custom_name_candidates
    union all select * from exact_off_nl_name_candidates
    union all select * from exact_off_other_name_candidates
    union all select * from exact_off_brand_candidates
    union all select * from exact_generic_alias_candidates
    union all select * from prefix_off_name_candidates
    union all select * from prefix_custom_name_candidates
    union all select * from prefix_generic_alias_candidates
    union all select * from prefix_generic_name_candidates
    union all select * from trigram_off_name_candidates
    union all select * from trigram_generic_alias_candidates
  ),
  bounded_candidates as (
    select rc.*
    from raw_candidates rc
    order by rc.match_tier, rc.match_score desc, rc.source_type, rc.candidate_id
    limit 1000
  ),
  deduplicated as (
    select source_type, candidate_id, match_tier, match_score
    from (
      select
        bc.*,
        row_number() over (
          partition by bc.source_type, bc.candidate_id
          order by bc.match_tier, bc.match_score desc
        ) as candidate_order
      from bounded_candidates bc
    ) ranked
    where candidate_order = 1
  ),
  hydrated as (
    select
      d.source_type as result_type,
      f.source_provider,
      f.id as source_id,
      f.barcode,
      case
        when v_locale = 'nl'
          then coalesce(nullif(btrim(f.metadata ->> 'dutch_display_label'), ''), f.name)
        else f.name
      end as display_name,
      f.brand,
      case
        when f.reference_amount = 100 and f.reference_unit = 'g' then 'per_100_g'
        when f.reference_amount = 100 and f.reference_unit = 'ml' then 'per_100_ml'
        else 'per_reference'
      end as nutrition_basis,
      f.reference_amount,
      f.reference_unit,
      f.energy_kcal as energy_kcal_reference,
      f.protein_grams as protein_grams_reference,
      f.carbohydrate_grams as carbohydrate_grams_reference,
      f.fat_grams as fat_grams_reference,
      f.fiber_grams as fiber_grams_reference,
      f.quality_status,
      true as loggable,
      d.match_tier as rank_tier,
      d.match_score as rank_score
    from deduplicated d
    join public.foods f on f.id = d.candidate_id
    where d.source_type in ('custom_food', 'generic_food')
      and f.status = 'active'
      and (
        (d.source_type = 'custom_food' and f.catalog_scope = 'custom' and f.owner_user_id = v_user_id)
        or (
          d.source_type = 'generic_food'
          and f.catalog_scope = 'canonical'
          and f.quality_status in ('reviewed', 'verified')
          and f.ingestion_id is not null
        )
      )
    union all
    select
      d.source_type,
      p.source_provider,
      p.id,
      p.barcode_original,
      case when v_locale = 'nl' then coalesce(p.product_name_nl, p.product_name) else p.product_name end,
      p.brand,
      p.nutrition_basis,
      100::numeric,
      case when p.nutrition_basis = 'per_100_ml' then 'ml' else 'g' end,
      p.energy_kcal_100,
      p.protein_grams_100,
      p.carbohydrate_grams_100,
      p.fat_grams_100,
      p.fiber_grams_100,
      p.quality_status,
      p.lifecycle_status = 'active' and p.quality_status in ('complete', 'reviewed'),
      d.match_tier,
      d.match_score
    from deduplicated d
    join public.nutrition_off_products p on p.id = d.candidate_id
    where d.source_type = 'off_branded_food'
      and p.lifecycle_status = 'active'
      and p.quality_status in ('complete', 'reviewed')
  ),
  paged as (
    select
      h.*,
      lower(btrim(h.display_name)) as page_name,
      h.result_type as page_source,
      h.source_id as page_id
    from hydrated h
    where p_after_rank is null
       or h.rank_tier > p_after_rank
       or (
         h.rank_tier = p_after_rank
         and h.rank_score < p_after_score
       )
       or (
         h.rank_tier = p_after_rank
         and h.rank_score = p_after_score
         and (lower(btrim(h.display_name)), h.result_type, h.source_id)
           > (lower(btrim(p_after_name)), p_after_source, p_after_id)
       )
  )
  select
    p.result_type,
    p.source_provider,
    p.source_id,
    p.barcode,
    p.display_name,
    p.brand,
    p.nutrition_basis,
    p.reference_amount,
    p.reference_unit,
    p.energy_kcal_reference,
    p.protein_grams_reference,
    p.carbohydrate_grams_reference,
    p.fat_grams_reference,
    p.fiber_grams_reference,
    p.quality_status,
    p.loggable,
    p.rank_tier,
    p.rank_score,
    p.page_name,
    p.page_source,
    p.page_id
  from paged p
  order by p.rank_tier, p.rank_score desc, p.page_name, p.page_source, p.page_id
  limit v_page_size;
end;
$$;

create or replace function public.fmz_phase4_lookup_off_product_by_barcode(p_barcode text)
returns table (
  result_type text,
  source_provider text,
  source_id uuid,
  barcode text,
  display_name text,
  brand text,
  nutrition_basis text,
  reference_amount numeric,
  reference_unit text,
  energy_kcal_reference numeric,
  protein_grams_reference numeric,
  carbohydrate_grams_reference numeric,
  fat_grams_reference numeric,
  fiber_grams_reference numeric,
  quality_status text,
  loggable boolean
)
language plpgsql
stable
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_gtin14 text := public.fmz_phase4_normalize_gtin14(p_barcode);
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if v_gtin14 is null then
    raise exception 'valid EAN-8, UPC-A, EAN-13, or GTIN-14 required'
      using errcode = '22023';
  end if;

  return query
  select
    'off_branded_food'::text,
    p.source_provider,
    p.id,
    p.barcode_original,
    coalesce(p.product_name_nl, p.product_name),
    p.brand,
    p.nutrition_basis,
    100::numeric,
    case when p.nutrition_basis = 'per_100_ml' then 'ml' else 'g' end,
    p.energy_kcal_100,
    p.protein_grams_100,
    p.carbohydrate_grams_100,
    p.fat_grams_100,
    p.fiber_grams_100,
    p.quality_status,
    true
  from public.nutrition_off_products p
  where p.normalized_gtin14 = v_gtin14
    and p.lifecycle_status = 'active'
    and p.quality_status in ('complete', 'reviewed')
  limit 1;
end;
$$;

revoke all on table public.nutrition_off_catalog_releases from public;
revoke all on table public.nutrition_off_catalog_releases from anon;
revoke all on table public.nutrition_off_catalog_releases from authenticated;
revoke all on table public.nutrition_off_catalog_releases from service_role;

revoke all on table public.nutrition_off_products from public;
revoke all on table public.nutrition_off_products from anon;
revoke all on table public.nutrition_off_products from authenticated;
revoke all on table public.nutrition_off_products from service_role;
grant select (
  id,
  source_provider,
  barcode_original,
  normalized_gtin14,
  product_name,
  product_name_nl,
  generic_name,
  brand,
  normalized_brand,
  quantity_text,
  serving_size_text,
  nutrition_basis,
  energy_kcal_100,
  protein_grams_100,
  carbohydrate_grams_100,
  fat_grams_100,
  fiber_grams_100,
  license_code,
  license_url,
  attribution_text,
  image_reference_url,
  image_license_code,
  image_attribution,
  quality_status,
  lifecycle_status
) on table public.nutrition_off_products to authenticated;

revoke all on table public.nutrition_off_product_names from public;
revoke all on table public.nutrition_off_product_names from anon;
revoke all on table public.nutrition_off_product_names from authenticated;
revoke all on table public.nutrition_off_product_names from service_role;
grant select (
  id,
  product_id,
  language_code,
  name_type,
  name,
  normalized_name,
  is_preferred,
  quality_status,
  lifecycle_status
) on table public.nutrition_off_product_names to authenticated;

revoke all on function public.fmz_phase4_normalize_gtin14(text) from public;
revoke all on function public.fmz_phase4_normalize_gtin14(text) from anon;
revoke all on function public.fmz_phase4_normalize_gtin14(text) from authenticated;
revoke all on function public.fmz_phase4_normalize_gtin14(text) from service_role;
grant execute on function public.fmz_phase4_normalize_gtin14(text) to authenticated;

revoke all on function public.fmz_phase4_normalize_catalog_text(text) from public;
revoke all on function public.fmz_phase4_normalize_catalog_text(text) from anon;
revoke all on function public.fmz_phase4_normalize_catalog_text(text) from authenticated;
revoke all on function public.fmz_phase4_normalize_catalog_text(text) from service_role;
grant execute on function public.fmz_phase4_normalize_catalog_text(text) to authenticated;

revoke all on function public.fmz_phase4_provider_candidate_uuid_v5(text) from public;
revoke all on function public.fmz_phase4_provider_candidate_uuid_v5(text) from anon;
revoke all on function public.fmz_phase4_provider_candidate_uuid_v5(text) from authenticated;
revoke all on function public.fmz_phase4_provider_candidate_uuid_v5(text) from service_role;

revoke all on function public.fmz_phase4_enforce_off_release_state() from public;
revoke all on function public.fmz_phase4_enforce_off_release_state() from anon;
revoke all on function public.fmz_phase4_enforce_off_release_state() from authenticated;
revoke all on function public.fmz_phase4_enforce_off_release_state() from service_role;

revoke all on function public.fmz_phase4_prevent_off_catalog_removal() from public;
revoke all on function public.fmz_phase4_prevent_off_catalog_removal() from anon;
revoke all on function public.fmz_phase4_prevent_off_catalog_removal() from authenticated;
revoke all on function public.fmz_phase4_prevent_off_catalog_removal() from service_role;

revoke all on function public.fmz_phase4_sync_off_archive_state() from public;
revoke all on function public.fmz_phase4_sync_off_archive_state() from anon;
revoke all on function public.fmz_phase4_sync_off_archive_state() from authenticated;
revoke all on function public.fmz_phase4_sync_off_archive_state() from service_role;

revoke all on function public.fmz_phase4_enforce_off_product_identity() from public;
revoke all on function public.fmz_phase4_enforce_off_product_identity() from anon;
revoke all on function public.fmz_phase4_enforce_off_product_identity() from authenticated;
revoke all on function public.fmz_phase4_enforce_off_product_identity() from service_role;

revoke all on function public.fmz_phase4_enforce_off_product_name_identity() from public;
revoke all on function public.fmz_phase4_enforce_off_product_name_identity() from anon;
revoke all on function public.fmz_phase4_enforce_off_product_name_identity() from authenticated;
revoke all on function public.fmz_phase4_enforce_off_product_name_identity() from service_role;

revoke all on function public.fmz_phase4_search_nutrition_catalog(text,text,integer,integer,numeric,text,text,uuid) from public;
revoke all on function public.fmz_phase4_search_nutrition_catalog(text,text,integer,integer,numeric,text,text,uuid) from anon;
revoke all on function public.fmz_phase4_search_nutrition_catalog(text,text,integer,integer,numeric,text,text,uuid) from authenticated;
revoke all on function public.fmz_phase4_search_nutrition_catalog(text,text,integer,integer,numeric,text,text,uuid) from service_role;
grant execute on function public.fmz_phase4_search_nutrition_catalog(text,text,integer,integer,numeric,text,text,uuid) to authenticated;

revoke all on function public.fmz_phase4_lookup_off_product_by_barcode(text) from public;
revoke all on function public.fmz_phase4_lookup_off_product_by_barcode(text) from anon;
revoke all on function public.fmz_phase4_lookup_off_product_by_barcode(text) from authenticated;
revoke all on function public.fmz_phase4_lookup_off_product_by_barcode(text) from service_role;
grant execute on function public.fmz_phase4_lookup_off_product_by_barcode(text) to authenticated;

commit;
