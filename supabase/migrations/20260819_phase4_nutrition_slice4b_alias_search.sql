-- FitMetZorge Phase 4 Nutrition - Slice 4B Alias/Search Foundation
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Additive catalog-search schema only. No food seed, provider request, backfill,
-- legacy mutation, trainer access, frontend change or production change.

begin;

create extension if not exists pg_trgm with schema extensions;

do $$
begin
  if not exists (
    select 1
    from pg_catalog.pg_extension e
    join pg_catalog.pg_namespace n on n.oid = e.extnamespace
    where e.extname = 'pg_trgm'
      and n.nspname = 'extensions'
  ) then
    raise exception 'pg_trgm must be installed in the Supabase extensions schema';
  end if;
end $$;

create table if not exists public.food_aliases (
  id uuid primary key,
  food_id uuid not null references public.foods(id) on delete cascade,
  language_code text not null,
  alias text not null,
  normalized_alias text not null,
  alias_type text not null,
  review_status text not null default 'pending',
  source_provider text,
  source_version text,
  license_code text,
  market_code text,
  priority smallint not null default 0,
  provenance jsonb not null default '{}'::jsonb,
  source_updated_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  constraint food_aliases_language_code_check
    check (language_code in ('nl', 'en', 'de')),
  constraint food_aliases_alias_check
    check (char_length(btrim(alias)) between 1 and 240),
  constraint food_aliases_normalized_alias_check
    check (
      char_length(normalized_alias) between 1 and 240
      and normalized_alias = lower(btrim(normalized_alias))
      and normalized_alias ~ '[[:alnum:]]'
      and normalized_alias !~ '[[:space:]]{2,}'
    ),
  constraint food_aliases_alias_type_check
    check (alias_type in ('primary', 'synonym', 'provider', 'search', 'brand_variant')),
  constraint food_aliases_review_status_check
    check (review_status in ('pending', 'reviewed', 'verified')),
  constraint food_aliases_source_provider_check
    check (source_provider is null or char_length(btrim(source_provider)) between 1 and 80),
  constraint food_aliases_source_version_check
    check (source_version is null or char_length(btrim(source_version)) between 1 and 120),
  constraint food_aliases_license_code_check
    check (license_code is null or char_length(btrim(license_code)) between 1 and 120),
  constraint food_aliases_source_contract_check
    check (
      (
        source_provider is null
        and source_version is null
        and license_code is null
        and source_updated_at is null
      )
      or
      (
        source_provider is not null
        and license_code is not null
        and provenance <> '{}'::jsonb
      )
    ),
  constraint food_aliases_market_code_check
    check (market_code is null or market_code ~ '^[A-Z]{2}$'),
  constraint food_aliases_priority_check
    check (priority between -100 and 100),
  constraint food_aliases_json_objects_check
    check (jsonb_typeof(provenance) = 'object' and jsonb_typeof(metadata) = 'object'),
  constraint food_aliases_status_check
    check (status in ('active', 'archived')),
  constraint food_aliases_archive_state_check
    check ((status = 'archived') = (archived_at is not null))
);

create unique index if not exists food_aliases_active_identity_uidx
  on public.food_aliases(
    food_id,
    language_code,
    normalized_alias,
    (coalesce(market_code, ''))
  )
  where status = 'active';

create index if not exists food_aliases_food_status_idx
  on public.food_aliases(food_id, status, priority desc, id);

create index if not exists food_aliases_active_prefix_idx
  on public.food_aliases(
    language_code,
    market_code,
    normalized_alias text_pattern_ops,
    priority desc,
    id
  )
  where status = 'active' and review_status in ('reviewed', 'verified');

create index if not exists food_aliases_active_trgm_idx
  on public.food_aliases using gin (normalized_alias extensions.gin_trgm_ops)
  where status = 'active' and review_status in ('reviewed', 'verified');

create index if not exists food_aliases_market_priority_idx
  on public.food_aliases(market_code, language_code, priority desc, food_id)
  where status = 'active' and review_status in ('reviewed', 'verified');

create index if not exists foods_active_name_trgm_idx
  on public.foods using gin ((lower(name)) extensions.gin_trgm_ops)
  where status = 'active';

create index if not exists foods_active_brand_trgm_idx
  on public.foods using gin ((lower(coalesce(brand, ''))) extensions.gin_trgm_ops)
  where status = 'active' and brand is not null;

do $$
begin
  if not exists (
    select 1
    from pg_catalog.pg_trigger
    where tgname = 'food_aliases_10_sync_archive_state'
      and tgrelid = 'public.food_aliases'::regclass
      and not tgisinternal
  ) then
    create trigger food_aliases_10_sync_archive_state
    before insert or update of status on public.food_aliases
    for each row execute function public.fmz_phase4_sync_archive_state();
  end if;

  if not exists (
    select 1
    from pg_catalog.pg_trigger
    where tgname = 'food_aliases_90_touch_updated_at'
      and tgrelid = 'public.food_aliases'::regclass
      and not tgisinternal
  ) then
    create trigger food_aliases_90_touch_updated_at
    before update on public.food_aliases
    for each row execute function public.fmz_phase4_touch_updated_at();
  end if;
end $$;

alter table public.food_aliases enable row level security;

do $$
begin
  if not exists (
    select 1
    from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'food_aliases'
      and policyname = 'food_aliases_select_visible'
  ) then
    create policy "food_aliases_select_visible"
    on public.food_aliases
    for select
    to authenticated
    using (
      status = 'active'
      and review_status in ('reviewed', 'verified')
      and exists (
        select 1
        from public.foods f
        where f.id = food_aliases.food_id
          and f.status = 'active'
          and (
            f.catalog_scope = 'canonical'
            or (
              f.catalog_scope = 'custom'
              and f.owner_user_id = (select auth.uid())
            )
          )
      )
    );
  end if;
end $$;

revoke all on table public.food_aliases from public;
revoke all on table public.food_aliases from anon;
revoke all on table public.food_aliases from authenticated;
grant select on table public.food_aliases to authenticated;

commit;
