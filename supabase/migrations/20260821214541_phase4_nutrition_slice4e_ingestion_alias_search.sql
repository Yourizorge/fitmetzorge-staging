-- FitMetZorge Phase 4 Nutrition - Slice 4E Ingestion Ledger + Alias Search
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Additive catalog-ingestion audit, quality visibility, and local alias search.
-- No catalog rows, aliases, portions, provider calls, legacy mutation, trainer
-- access, frontend deployment, Edge deployment, AI, or production change.

begin;

create table if not exists public.nutrition_food_ingestions (
  id uuid primary key,
  artifact_version text not null,
  artifact_sha256 text not null,
  source_provider text not null,
  mapping_version text not null,
  status text not null default 'reviewed',
  predecessor_ingestion_id uuid references public.nutrition_food_ingestions(id) on delete restrict,
  manifest_food_count integer not null,
  manifest_alias_count integer not null,
  reviewed_by text not null,
  reviewed_at timestamptz not null,
  imported_at timestamptz,
  provenance jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint nutrition_food_ingestions_artifact_sha256_key unique (artifact_sha256),
  constraint nutrition_food_ingestions_provider_version_key unique (source_provider, artifact_version),
  constraint nutrition_food_ingestions_artifact_version_check
    check (char_length(btrim(artifact_version)) between 1 and 120),
  constraint nutrition_food_ingestions_artifact_sha256_check
    check (artifact_sha256 ~ '^[A-F0-9]{64}$'),
  constraint nutrition_food_ingestions_source_provider_check
    check (
      char_length(source_provider) between 2 and 40
      and source_provider = lower(btrim(source_provider))
      and source_provider ~ '^[a-z0-9_]+$'
    ),
  constraint nutrition_food_ingestions_mapping_version_check
    check (char_length(btrim(mapping_version)) between 1 and 120),
  constraint nutrition_food_ingestions_status_check
    check (status in ('reviewed', 'imported', 'superseded', 'rejected')),
  constraint nutrition_food_ingestions_predecessor_check
    check (predecessor_ingestion_id is null or predecessor_ingestion_id <> id),
  constraint nutrition_food_ingestions_manifest_counts_check
    check (
      manifest_food_count between 0 and 1000000
      and manifest_alias_count between 0 and 5000000
    ),
  constraint nutrition_food_ingestions_reviewed_by_check
    check (char_length(btrim(reviewed_by)) between 1 and 120),
  constraint nutrition_food_ingestions_json_objects_check
    check (
      jsonb_typeof(provenance) = 'object'
      and jsonb_typeof(metadata) = 'object'
    ),
  constraint nutrition_food_ingestions_status_timestamps_check
    check (
      (
        status in ('reviewed', 'rejected')
        and imported_at is null
      )
      or
      (
        status in ('imported', 'superseded')
        and imported_at is not null
        and imported_at >= reviewed_at
      )
    ),
  constraint nutrition_food_ingestions_updated_at_check
    check (updated_at >= created_at)
);

create index if not exists nutrition_food_ingestions_status_created_idx
  on public.nutrition_food_ingestions(status, created_at desc, id);

create unique index if not exists nutrition_food_ingestions_predecessor_uidx
  on public.nutrition_food_ingestions(predecessor_ingestion_id)
  where predecessor_ingestion_id is not null;

create or replace function public.fmz_phase4_enforce_food_ingestion_state()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_predecessor_provider text;
begin
  if tg_op = 'INSERT' then
    perform pg_catalog.pg_advisory_xact_lock(
      pg_catalog.hashtextextended(
        'fmz_phase4_food_ingestion_chain:' || new.source_provider,
        0
      )
    );

    if new.predecessor_ingestion_id is null then
      if exists (
        select 1
        from public.nutrition_food_ingestions i
        where i.source_provider = new.source_provider
      ) then
        raise exception 'subsequent food ingestion artifact requires predecessor'
          using errcode = '23514';
      end if;
    else
      select i.source_provider
      into v_predecessor_provider
      from public.nutrition_food_ingestions i
      where i.id = new.predecessor_ingestion_id
      for key share;

      if not found or v_predecessor_provider is distinct from new.source_provider then
        raise exception 'food ingestion predecessor must use the same source provider'
          using errcode = '23514';
      end if;
    end if;

    return new;
  end if;

  if new.id is distinct from old.id
     or new.artifact_version is distinct from old.artifact_version
     or new.artifact_sha256 is distinct from old.artifact_sha256
     or new.source_provider is distinct from old.source_provider
     or new.mapping_version is distinct from old.mapping_version
     or new.predecessor_ingestion_id is distinct from old.predecessor_ingestion_id
     or new.manifest_food_count is distinct from old.manifest_food_count
     or new.manifest_alias_count is distinct from old.manifest_alias_count
     or new.reviewed_by is distinct from old.reviewed_by
     or new.reviewed_at is distinct from old.reviewed_at
     or new.provenance is distinct from old.provenance
     or new.created_at is distinct from old.created_at then
    raise exception 'food ingestion audit identity is immutable'
      using errcode = '55000';
  end if;

  if new.status is distinct from old.status
     and not (
       (old.status = 'reviewed' and new.status in ('imported', 'rejected'))
       or (old.status = 'imported' and new.status = 'superseded')
     ) then
    raise exception 'invalid food ingestion status transition'
      using errcode = '22023';
  end if;

  if old.imported_at is not null
     and new.imported_at is distinct from old.imported_at then
    raise exception 'food ingestion import timestamp is immutable'
      using errcode = '55000';
  end if;

  return new;
end;
$$;

create or replace function public.fmz_phase4_prevent_food_ingestion_removal()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, pg_temp
as $$
begin
  raise exception 'food ingestion audit records use forward fixes only'
    using errcode = '55000';
end;
$$;

do $$
begin
  if not exists (
    select 1
    from pg_catalog.pg_trigger
    where tgname = 'nutrition_food_ingestions_10_enforce_state'
      and tgrelid = 'public.nutrition_food_ingestions'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_food_ingestions_10_enforce_state
    before insert or update on public.nutrition_food_ingestions
    for each row execute function public.fmz_phase4_enforce_food_ingestion_state();
  end if;

  if not exists (
    select 1
    from pg_catalog.pg_trigger
    where tgname = 'nutrition_food_ingestions_20_prevent_removal'
      and tgrelid = 'public.nutrition_food_ingestions'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_food_ingestions_20_prevent_removal
    before delete on public.nutrition_food_ingestions
    for each row execute function public.fmz_phase4_prevent_food_ingestion_removal();
  end if;

  if not exists (
    select 1
    from pg_catalog.pg_trigger
    where tgname = 'nutrition_food_ingestions_90_touch_updated_at'
      and tgrelid = 'public.nutrition_food_ingestions'::regclass
      and not tgisinternal
  ) then
    create trigger nutrition_food_ingestions_90_touch_updated_at
    before update on public.nutrition_food_ingestions
    for each row execute function public.fmz_phase4_touch_updated_at();
  end if;
end $$;

alter table public.nutrition_food_ingestions enable row level security;

revoke all on table public.nutrition_food_ingestions from public;
revoke all on table public.nutrition_food_ingestions from anon;
revoke all on table public.nutrition_food_ingestions from authenticated;
revoke all on table public.nutrition_food_ingestions from service_role;

revoke all on function public.fmz_phase4_enforce_food_ingestion_state() from public;
revoke all on function public.fmz_phase4_enforce_food_ingestion_state() from anon;
revoke all on function public.fmz_phase4_enforce_food_ingestion_state() from authenticated;
revoke all on function public.fmz_phase4_enforce_food_ingestion_state() from service_role;

revoke all on function public.fmz_phase4_prevent_food_ingestion_removal() from public;
revoke all on function public.fmz_phase4_prevent_food_ingestion_removal() from anon;
revoke all on function public.fmz_phase4_prevent_food_ingestion_removal() from authenticated;
revoke all on function public.fmz_phase4_prevent_food_ingestion_removal() from service_role;

alter table public.foods
  add column if not exists ingestion_id uuid;

do $$
begin
  if not exists (
    select 1
    from pg_catalog.pg_constraint
    where conname = 'foods_ingestion_id_fkey'
      and conrelid = 'public.foods'::regclass
  ) then
    alter table public.foods
      add constraint foods_ingestion_id_fkey
      foreign key (ingestion_id)
      references public.nutrition_food_ingestions(id)
      on delete restrict;
  end if;

  if not exists (
    select 1
    from pg_catalog.pg_constraint
    where conname = 'foods_ingestion_scope_check'
      and conrelid = 'public.foods'::regclass
  ) then
    alter table public.foods
      add constraint foods_ingestion_scope_check
      check (catalog_scope = 'canonical' or ingestion_id is null);
  end if;

  if not exists (
    select 1
    from pg_catalog.pg_constraint
    where conname = 'foods_canonical_ingestion_quality_check'
      and conrelid = 'public.foods'::regclass
  ) then
    alter table public.foods
      add constraint foods_canonical_ingestion_quality_check
      check (
        catalog_scope <> 'canonical'
        or quality_status not in ('reviewed', 'verified')
        or ingestion_id is not null
      );
  end if;
end $$;

create index if not exists foods_ingestion_id_idx
  on public.foods(ingestion_id, id)
  where ingestion_id is not null;

alter table public.food_aliases
  add column if not exists ingestion_id uuid,
  add column if not exists is_preferred boolean not null default false;

do $$
begin
  if not exists (
    select 1
    from pg_catalog.pg_constraint
    where conname = 'food_aliases_ingestion_id_fkey'
      and conrelid = 'public.food_aliases'::regclass
  ) then
    alter table public.food_aliases
      add constraint food_aliases_ingestion_id_fkey
      foreign key (ingestion_id)
      references public.nutrition_food_ingestions(id)
      on delete restrict;
  end if;

  if not exists (
    select 1
    from pg_catalog.pg_constraint
    where conname = 'food_aliases_reviewed_ingestion_check'
      and conrelid = 'public.food_aliases'::regclass
  ) then
    alter table public.food_aliases
      add constraint food_aliases_reviewed_ingestion_check
      check (
        ingestion_id is not null
        or source_provider is null
        or review_status = 'pending'
      );
  end if;

  if not exists (
    select 1
    from pg_catalog.pg_constraint
    where conname = 'food_aliases_preferred_review_check'
      and conrelid = 'public.food_aliases'::regclass
  ) then
    alter table public.food_aliases
      add constraint food_aliases_preferred_review_check
      check (
        not is_preferred
        or (
          language_code = 'nl'
          and market_code is not null
          and review_status in ('reviewed', 'verified')
        )
      );
  end if;
end $$;

create index if not exists food_aliases_ingestion_id_idx
  on public.food_aliases(ingestion_id, id)
  where ingestion_id is not null;

create unique index if not exists food_aliases_preferred_nl_market_uidx
  on public.food_aliases(normalized_alias, market_code)
  where status = 'active'
    and review_status in ('reviewed', 'verified')
    and language_code = 'nl'
    and is_preferred;

alter policy "foods_select_visible"
on public.foods
to authenticated
using (
  (
    catalog_scope = 'canonical'
    and status = 'active'
    and quality_status in ('reviewed', 'verified')
    and ingestion_id is not null
  )
  or (
    catalog_scope = 'custom'
    and owner_user_id = (select auth.uid())
  )
);

alter policy "food_aliases_select_visible"
on public.food_aliases
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
        (
          f.catalog_scope = 'canonical'
          and f.quality_status in ('reviewed', 'verified')
          and f.ingestion_id is not null
        )
        or (
          f.catalog_scope = 'custom'
          and f.owner_user_id = (select auth.uid())
        )
      )
  )
);

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
  v_user_id uuid := auth.uid();
  v_query text := lower(btrim(coalesce(p_query, '')));
  v_normalized_query text := btrim(
    pg_catalog.regexp_replace(
      pg_catalog.regexp_replace(lower(btrim(coalesce(p_query, ''))), '[^[:alnum:]]+', ' ', 'g'),
      '[[:space:]]+',
      ' ',
      'g'
    )
  );
  v_barcode text := btrim(coalesce(p_query, ''));
  v_page_size integer := greatest(1, least(coalesce(p_page_size, 25), 50));
begin
  if v_user_id is null then
    raise exception 'authenticated user required'
      using errcode = '42501';
  end if;

  if v_query = '' then
    return query
    select f.*
    from public.foods f
    where f.status = 'active'
      and (
        (
          f.catalog_scope = 'canonical'
          and f.quality_status in ('reviewed', 'verified')
          and f.ingestion_id is not null
        )
        or (
          f.catalog_scope = 'custom'
          and f.owner_user_id = v_user_id
        )
      )
      and (
        p_after_name is null
        or p_after_id is null
        or (lower(f.name), f.id) > (lower(btrim(p_after_name)), p_after_id)
      )
    order by lower(f.name), f.id
    limit v_page_size;

    return;
  end if;

  return query
  with raw_candidates as (
    (
      select
        f.id as food_id,
        0::integer as match_tier,
        0::integer as locale_rank,
        0::integer as preferred_rank,
        0::integer as priority_sort,
        0::numeric(8,6) as similarity_sort
      from public.foods f
      where f.status = 'active'
        and f.catalog_scope = 'canonical'
        and f.quality_status in ('reviewed', 'verified')
        and f.ingestion_id is not null
        and f.barcode = v_barcode
      order by f.id
      limit 250
    )
    union all
    (
      select f.id, 10, 0, 0, 0, 0::numeric(8,6)
      from public.foods f
      where f.status = 'active'
        and f.catalog_scope = 'custom'
        and f.owner_user_id = v_user_id
        and lower(f.name) = v_query
      order by f.id
      limit 250
    )
    union all
    (
      select
        a.food_id,
        case when a.language_code = 'nl' then 20 else 22 end,
        case
          when a.language_code = 'nl' and a.market_code = 'NL' then 0
          when a.language_code = 'nl' then 1
          else 2
        end,
        case when a.is_preferred then 0 else 1 end,
        -a.priority::integer,
        0::numeric(8,6)
      from public.food_aliases a
      join public.foods f on f.id = a.food_id
      where a.status = 'active'
        and a.review_status in ('reviewed', 'verified')
        and a.normalized_alias = v_normalized_query
        and f.status = 'active'
        and (
          (
            f.catalog_scope = 'canonical'
            and f.quality_status in ('reviewed', 'verified')
            and f.ingestion_id is not null
          )
          or (
            f.catalog_scope = 'custom'
            and f.owner_user_id = v_user_id
          )
        )
      order by
        case when a.language_code = 'nl' and a.market_code = 'NL' then 0 when a.language_code = 'nl' then 1 else 2 end,
        a.is_preferred desc,
        a.priority desc,
        a.food_id,
        a.id
      limit 250
    )
    union all
    (
      select f.id, 30, 0, 0, 0, 0::numeric(8,6)
      from public.foods f
      where f.status = 'active'
        and f.catalog_scope = 'canonical'
        and f.quality_status in ('reviewed', 'verified')
        and f.ingestion_id is not null
        and lower(f.name) = v_query
      order by f.id
      limit 250
    )
    union all
    (
      select f.id, 31, 0, 0, 0, 0::numeric(8,6)
      from public.foods f
      where f.status = 'active'
        and f.catalog_scope = 'canonical'
        and f.quality_status in ('reviewed', 'verified')
        and f.ingestion_id is not null
        and lower(coalesce(f.brand, '')) = v_query
      order by f.id
      limit 250
    )
    union all
    (
      select f.id, 35, 0, 0, 0, 0::numeric(8,6)
      from public.foods f
      where f.status = 'active'
        and f.catalog_scope = 'custom'
        and f.owner_user_id = v_user_id
        and lower(f.name) like v_query || '%'
      order by lower(f.name), f.id
      limit 250
    )
    union all
    (
      select
        a.food_id,
        case when a.language_code = 'nl' then 40 else 42 end,
        case
          when a.language_code = 'nl' and a.market_code = 'NL' then 0
          when a.language_code = 'nl' then 1
          else 2
        end,
        case when a.is_preferred then 0 else 1 end,
        -a.priority::integer,
        0::numeric(8,6)
      from public.food_aliases a
      join public.foods f on f.id = a.food_id
      where a.status = 'active'
        and a.review_status in ('reviewed', 'verified')
        and a.normalized_alias like v_normalized_query || '%'
        and f.status = 'active'
        and (
          (
            f.catalog_scope = 'canonical'
            and f.quality_status in ('reviewed', 'verified')
            and f.ingestion_id is not null
          )
          or (
            f.catalog_scope = 'custom'
            and f.owner_user_id = v_user_id
          )
        )
      order by
        a.normalized_alias,
        case when a.language_code = 'nl' and a.market_code = 'NL' then 0 when a.language_code = 'nl' then 1 else 2 end,
        a.is_preferred desc,
        a.priority desc,
        a.food_id,
        a.id
      limit 250
    )
    union all
    (
      select f.id, 50, 0, 0, 0, 0::numeric(8,6)
      from public.foods f
      where f.status = 'active'
        and f.catalog_scope = 'canonical'
        and f.quality_status in ('reviewed', 'verified')
        and f.ingestion_id is not null
        and lower(f.name) like v_query || '%'
      order by lower(f.name), f.id
      limit 250
    )
    union all
    (
      select f.id, 51, 0, 0, 0, 0::numeric(8,6)
      from public.foods f
      where f.status = 'active'
        and f.catalog_scope = 'canonical'
        and f.quality_status in ('reviewed', 'verified')
        and f.ingestion_id is not null
        and lower(coalesce(f.brand, '')) like v_query || '%'
      order by lower(coalesce(f.brand, '')), lower(f.name), f.id
      limit 250
    )
    union all
    (
      select
        a.food_id,
        case when a.language_code = 'nl' then 60 else 62 end,
        case
          when a.language_code = 'nl' and a.market_code = 'NL' then 0
          when a.language_code = 'nl' then 1
          else 2
        end,
        case when a.is_preferred then 0 else 1 end,
        -a.priority::integer,
        (-extensions.similarity(a.normalized_alias, v_normalized_query))::numeric(8,6)
      from public.food_aliases a
      join public.foods f on f.id = a.food_id
      where char_length(v_normalized_query) >= 3
        and a.status = 'active'
        and a.review_status in ('reviewed', 'verified')
        and a.normalized_alias operator(extensions.%) v_normalized_query
        and f.status = 'active'
        and (
          (
            f.catalog_scope = 'canonical'
            and f.quality_status in ('reviewed', 'verified')
            and f.ingestion_id is not null
          )
          or (
            f.catalog_scope = 'custom'
            and f.owner_user_id = v_user_id
          )
        )
      order by
        extensions.similarity(a.normalized_alias, v_normalized_query) desc,
        case when a.language_code = 'nl' and a.market_code = 'NL' then 0 when a.language_code = 'nl' then 1 else 2 end,
        a.is_preferred desc,
        a.priority desc,
        a.food_id,
        a.id
      limit 250
    )
    union all
    (
      select
        f.id,
        65,
        0,
        0,
        0,
        (-extensions.similarity(lower(f.name), v_query))::numeric(8,6)
      from public.foods f
      where char_length(v_query) >= 3
        and f.status = 'active'
        and f.catalog_scope = 'custom'
        and f.owner_user_id = v_user_id
        and lower(f.name) operator(extensions.%) v_query
      order by extensions.similarity(lower(f.name), v_query) desc, lower(f.name), f.id
      limit 250
    )
    union all
    (
      select
        f.id,
        70,
        0,
        0,
        0,
        (-extensions.similarity(lower(f.name), v_query))::numeric(8,6)
      from public.foods f
      where char_length(v_query) >= 3
        and f.status = 'active'
        and f.catalog_scope = 'canonical'
        and f.quality_status in ('reviewed', 'verified')
        and f.ingestion_id is not null
        and lower(f.name) operator(extensions.%) v_query
      order by extensions.similarity(lower(f.name), v_query) desc, lower(f.name), f.id
      limit 250
    )
    union all
    (
      select
        f.id,
        71,
        0,
        0,
        0,
        (-extensions.similarity(lower(coalesce(f.brand, '')), v_query))::numeric(8,6)
      from public.foods f
      where char_length(v_query) >= 3
        and f.status = 'active'
        and f.catalog_scope = 'canonical'
        and f.quality_status in ('reviewed', 'verified')
        and f.ingestion_id is not null
        and lower(coalesce(f.brand, '')) operator(extensions.%) v_query
      order by extensions.similarity(lower(coalesce(f.brand, '')), v_query) desc, lower(f.name), f.id
      limit 250
    )
  ),
  best_candidates as (
    select distinct on (c.food_id)
      c.food_id,
      c.match_tier,
      c.locale_rank,
      c.preferred_rank,
      c.priority_sort,
      c.similarity_sort
    from raw_candidates c
    order by
      c.food_id,
      c.match_tier,
      c.locale_rank,
      c.preferred_rank,
      c.priority_sort,
      c.similarity_sort
  ),
  ranked as (
    select
      c.food_id,
      f.name as food_name,
      c.match_tier,
      c.locale_rank,
      c.preferred_rank,
      c.priority_sort,
      c.similarity_sort
    from best_candidates c
    join public.foods f on f.id = c.food_id
  ),
  cursor_key as (
    select
      r.match_tier,
      r.locale_rank,
      r.preferred_rank,
      r.priority_sort,
      r.similarity_sort,
      lower(r.food_name) as food_name_sort,
      r.food_id
    from ranked r
    where p_after_name is not null
      and p_after_id is not null
      and r.food_id = p_after_id
      and lower(r.food_name) = lower(btrim(p_after_name))
    limit 1
  )
  select f.*
  from ranked r
  join public.foods f on f.id = r.food_id
  left join cursor_key c on true
  where (
    p_after_name is null
    or p_after_id is null
    or (
      c.food_id is not null
      and (
        r.match_tier,
        r.locale_rank,
        r.preferred_rank,
        r.priority_sort,
        r.similarity_sort,
        lower(f.name),
        f.id
      ) > (
        c.match_tier,
        c.locale_rank,
        c.preferred_rank,
        c.priority_sort,
        c.similarity_sort,
        c.food_name_sort,
        c.food_id
      )
    )
  )
  order by
    r.match_tier,
    r.locale_rank,
    r.preferred_rank,
    r.priority_sort,
    r.similarity_sort,
    lower(f.name),
    f.id
  limit v_page_size;
end;
$$;

revoke all on function public.fmz_phase4_search_foods(text, integer, text, uuid) from public;
revoke all on function public.fmz_phase4_search_foods(text, integer, text, uuid) from anon;
revoke all on function public.fmz_phase4_search_foods(text, integer, text, uuid) from authenticated;
grant execute on function public.fmz_phase4_search_foods(text, integer, text, uuid) to authenticated;

commit;
