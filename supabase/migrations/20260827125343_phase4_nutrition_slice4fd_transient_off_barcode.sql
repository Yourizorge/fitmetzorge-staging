-- FitMetZorge Phase 4 Nutrition - Slice 4F-D Transient OFF Barcode Foundation
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Additive trusted barcode lookup and transient Open Food Facts snapshot logging.
-- No persistent OFF catalog mutation, seed/import, legacy mutation, trainer access,
-- frontend deployment, Edge deployment, AI, or production change.

begin;

do $$
begin
  if to_regclass('public.nutrition_provider_food_cache') is null
     or to_regclass('public.nutrition_provider_rate_buckets') is null
     or to_regclass('public.nutrition_provider_runtime_state') is null
     or to_regclass('public.nutrition_off_products') is null
     or to_regclass('public.nutrition_off_catalog_releases') is null
     or to_regclass('public.foods') is null
     or to_regclass('public.food_logs') is null
     or to_regclass('public.food_log_items') is null
     or to_regprocedure('public.fmz_phase4_normalize_gtin14(text)') is null
     or to_regprocedure('public.fmz_phase4_provider_candidate_uuid_v5(text)') is null
     or to_regprocedure('public.fmz_phase4_has_full_nutrition_access(uuid)') is null
     or to_regprocedure('public.fmz_phase4_day_payload(uuid,date)') is null
     or to_regprocedure('public.fmz_phase4_upsert_custom_food(uuid,text,text,numeric,text,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,timestamp with time zone)') is null
     or to_regprocedure('public.fmz_phase4_log_provider_food_item(uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb)') is null
     or to_regprocedure('public.fmz_phase4_log_off_food_item(uuid,uuid,date,text,smallint,text,uuid,numeric,text,text,timestamp with time zone)') is null then
    raise exception 'Phase 4F-D prerequisites are unavailable';
  end if;
end $$;

-- The operational tables remain service-only. They now isolate USDA and OFF by
-- provider_code while retaining the frozen USDA row shapes and limits.
alter table public.nutrition_provider_food_cache
  drop constraint if exists nutrition_provider_food_cache_provider_check;
alter table public.nutrition_provider_food_cache
  add constraint nutrition_provider_food_cache_provider_check
  check (provider_code in ('usda_fdc', 'open_food_facts'));

alter table public.nutrition_provider_food_cache
  drop constraint if exists nutrition_provider_food_cache_data_type_check;
alter table public.nutrition_provider_food_cache
  add constraint nutrition_provider_food_cache_data_type_check
  check (
    (provider_code = 'usda_fdc' and provider_data_type in ('Foundation', 'Survey (FNDDS)', 'SR Legacy'))
    or (provider_code = 'open_food_facts' and provider_data_type = 'off_branded')
  );

alter table public.nutrition_provider_rate_buckets
  drop constraint if exists nutrition_provider_rate_buckets_provider_check;
alter table public.nutrition_provider_rate_buckets
  add constraint nutrition_provider_rate_buckets_provider_check
  check (provider_code in ('usda_fdc', 'open_food_facts'));

alter table public.nutrition_provider_runtime_state
  drop constraint if exists nutrition_provider_runtime_state_provider_check;
alter table public.nutrition_provider_runtime_state
  add constraint nutrition_provider_runtime_state_provider_check
  check (provider_code in ('usda_fdc', 'open_food_facts'));

do $$
begin
  if exists (
    select 1
    from public.foods f
    where f.catalog_scope = 'custom'
      and f.status = 'active'
      and public.fmz_phase4_normalize_gtin14(f.barcode) is not null
    group by f.owner_user_id, public.fmz_phase4_normalize_gtin14(f.barcode)
    having count(*) > 1
  ) then
    raise exception 'duplicate active custom-food GTINs require owner review before Phase 4F-D';
  end if;
end $$;

create unique index if not exists foods_active_custom_gtin_owner_uidx
  on public.foods(owner_user_id, public.fmz_phase4_normalize_gtin14(barcode))
  where catalog_scope = 'custom'
    and status = 'active'
    and public.fmz_phase4_normalize_gtin14(barcode) is not null;

create or replace function public.fmz_phase4_provider_consume_rate_limits(
  p_provider_code text,
  p_user_subject_hmac text,
  p_request_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog
as $$
declare
  v_provider_code text := lower(btrim(p_provider_code));
  v_now timestamptz := statement_timestamp();
  v_scopes text[] := array['user_30_seconds', 'user_10_minutes', 'user_day', 'provider_hour'];
  v_window_seconds integer[] := array[30, 600, 86400, 3600];
  v_limits integer[] := array[3, 12, 100, 800];
  v_window_starts timestamptz[] := array[]::timestamptz[];
  v_subject text;
  v_window_start timestamptz;
  v_row_count integer;
  v_replay_count integer;
  v_failed_until timestamptz;
  v_failed_buckets jsonb;
  v_bucket_payload jsonb;
  v_index integer;
begin
  if v_provider_code is null or v_provider_code not in ('usda_fdc', 'open_food_facts') then
    raise exception 'unsupported nutrition provider';
  end if;
  if p_user_subject_hmac is null or p_user_subject_hmac !~ '^[0-9a-f]{64}$' then
    raise exception 'invalid provider rate subject';
  end if;
  if p_request_id is null then
    raise exception 'provider rate request id is required';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('fmz_phase4_provider_rate:' || v_provider_code || ':global', 0)
  );
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('fmz_phase4_provider_rate:' || v_provider_code || ':user:' || p_user_subject_hmac, 0)
  );

  for v_index in 1..4 loop
    v_subject := case when v_scopes[v_index] = 'provider_hour' then 'global' else p_user_subject_hmac end;
    v_window_start := pg_catalog.to_timestamp(
      (pg_catalog.floor(extract(epoch from v_now) / v_window_seconds[v_index]) * v_window_seconds[v_index])::double precision
    );
    v_window_starts := pg_catalog.array_append(v_window_starts, v_window_start);
    insert into public.nutrition_provider_rate_buckets(
      provider_code, bucket_scope, subject_hmac, window_start, window_end,
      window_seconds, limit_value
    ) values (
      v_provider_code, v_scopes[v_index], v_subject, v_window_start,
      v_window_start + pg_catalog.make_interval(secs => v_window_seconds[v_index]),
      v_window_seconds[v_index], v_limits[v_index]
    ) on conflict (provider_code, bucket_scope, subject_hmac, window_start) do nothing;
  end loop;

  select count(*)::integer,
    count(*) filter (where p_request_id = any(b.consumed_request_ids))::integer
  into v_row_count, v_replay_count
  from public.nutrition_provider_rate_buckets b
  where b.provider_code = v_provider_code
    and (
      (b.bucket_scope = v_scopes[1] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[1])
      or (b.bucket_scope = v_scopes[2] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[2])
      or (b.bucket_scope = v_scopes[3] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[3])
      or (b.bucket_scope = v_scopes[4] and b.subject_hmac = 'global' and b.window_start = v_window_starts[4])
    );
  if v_row_count <> 4 or v_replay_count not in (0, 4) then
    raise exception 'provider rate bucket integrity failure';
  end if;

  if v_replay_count = 4 then
    select pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
      'scope', b.bucket_scope, 'limit', b.limit_value,
      'remaining', greatest(b.limit_value - b.request_count, 0), 'reset_at', b.window_end
    ) order by b.window_seconds, b.bucket_scope)
    into v_bucket_payload
    from public.nutrition_provider_rate_buckets b
    where b.provider_code = v_provider_code
      and p_request_id = any(b.consumed_request_ids)
      and (
        (b.bucket_scope = v_scopes[1] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[1])
        or (b.bucket_scope = v_scopes[2] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[2])
        or (b.bucket_scope = v_scopes[3] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[3])
        or (b.bucket_scope = v_scopes[4] and b.subject_hmac = 'global' and b.window_start = v_window_starts[4])
      );
    return pg_catalog.jsonb_build_object(
      'allowed', true, 'replayed', true, 'provider', v_provider_code,
      'checked_at', v_now, 'buckets', coalesce(v_bucket_payload, '[]'::jsonb)
    );
  end if;

  select max(b.window_end), pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
    'scope', b.bucket_scope, 'limit', b.limit_value, 'remaining', 0, 'reset_at', b.window_end
  ) order by b.window_end)
  into v_failed_until, v_failed_buckets
  from public.nutrition_provider_rate_buckets b
  where b.provider_code = v_provider_code and b.request_count >= b.limit_value
    and (
      (b.bucket_scope = v_scopes[1] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[1])
      or (b.bucket_scope = v_scopes[2] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[2])
      or (b.bucket_scope = v_scopes[3] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[3])
      or (b.bucket_scope = v_scopes[4] and b.subject_hmac = 'global' and b.window_start = v_window_starts[4])
    );
  if v_failed_until is not null then
    return pg_catalog.jsonb_build_object(
      'allowed', false, 'replayed', false, 'provider', v_provider_code,
      'checked_at', v_now, 'retry_at', v_failed_until,
      'retry_after_seconds', greatest(0, pg_catalog.ceil(extract(epoch from (v_failed_until - v_now)))::integer),
      'buckets', coalesce(v_failed_buckets, '[]'::jsonb)
    );
  end if;

  for v_index in 1..4 loop
    v_subject := case when v_scopes[v_index] = 'provider_hour' then 'global' else p_user_subject_hmac end;
    update public.nutrition_provider_rate_buckets
    set request_count = request_count + 1,
      consumed_request_ids = pg_catalog.array_append(consumed_request_ids, p_request_id)
    where provider_code = v_provider_code and bucket_scope = v_scopes[v_index]
      and subject_hmac = v_subject and window_start = v_window_starts[v_index];
    if not found then raise exception 'provider rate bucket update failure'; end if;
  end loop;

  select pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
    'scope', b.bucket_scope, 'limit', b.limit_value,
    'remaining', greatest(b.limit_value - b.request_count, 0), 'reset_at', b.window_end
  ) order by b.window_seconds, b.bucket_scope)
  into v_bucket_payload
  from public.nutrition_provider_rate_buckets b
  where b.provider_code = v_provider_code and p_request_id = any(b.consumed_request_ids)
    and (
      (b.bucket_scope = v_scopes[1] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[1])
      or (b.bucket_scope = v_scopes[2] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[2])
      or (b.bucket_scope = v_scopes[3] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[3])
      or (b.bucket_scope = v_scopes[4] and b.subject_hmac = 'global' and b.window_start = v_window_starts[4])
    );
  return pg_catalog.jsonb_build_object(
    'allowed', true, 'replayed', false, 'provider', v_provider_code,
    'checked_at', v_now, 'buckets', coalesce(v_bucket_payload, '[]'::jsonb)
  );
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
  v_off_internal_user_id uuid;
  v_transient_off_user_id uuid;
  v_user_id uuid;
  v_operation text;
begin
  begin
    v_internal_user_id := nullif(current_setting('fmz.phase4_provider_snapshot_user_id', true), '')::uuid;
    v_off_internal_user_id := nullif(current_setting('fmz.phase4_off_snapshot_user_id', true), '')::uuid;
    v_transient_off_user_id := nullif(current_setting('fmz.phase4_transient_off_snapshot_user_id', true), '')::uuid;
  exception when invalid_text_representation then
    raise exception 'invalid internal provider write context' using errcode = '42501';
  end;

  v_user_id := coalesce(
    v_authenticated_user_id,
    v_internal_user_id,
    v_off_internal_user_id,
    v_transient_off_user_id
  );
  if v_user_id is null or new.user_id is distinct from v_user_id
     or (v_authenticated_user_id is not null and v_authenticated_user_id is distinct from v_user_id)
     or (v_internal_user_id is not null and v_internal_user_id is distinct from v_user_id)
     or (v_off_internal_user_id is not null and v_off_internal_user_id is distinct from v_user_id)
     or (v_transient_off_user_id is not null and v_transient_off_user_id is distinct from v_user_id) then
    raise exception 'food log item owner must match authorized user' using errcode = '42501';
  end if;

  if tg_op = 'UPDATE' then
    if (to_jsonb(new) - array['status', 'archived_at', 'updated_at']::text[])
       is distinct from
       (to_jsonb(old) - array['status', 'archived_at', 'updated_at']::text[]) then
      raise exception 'historical food log item snapshots are immutable' using errcode = '42501';
    end if;
    return new;
  end if;

  if not exists (
    select 1 from public.food_logs l
    where l.id = new.food_log_id and l.user_id = v_user_id and l.status = 'active'
  ) then
    raise exception 'food log item day must belong to authorized user' using errcode = '42501';
  end if;

  if new.food_id is null then
    v_operation := new.metadata ->> 'operation';
    if new.source_provider_snapshot = 'usda_fdc' then
      if v_authenticated_user_id is not null
         or v_internal_user_id is distinct from new.user_id
         or v_off_internal_user_id is not null
         or v_transient_off_user_id is not null
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
         or v_operation is null or v_operation not in ('provider_log', 'provider_replace')
         or new.metadata ->> 'candidate_id' is null
         or new.metadata ->> 'mapping_version' is distinct from 'phase4_usda_v1'
         or new.provenance_snapshot ->> 'provider' is distinct from 'usda_fdc'
         or new.provenance_snapshot ->> 'provider_food_id' is distinct from new.provider_food_id_snapshot
         or new.provenance_snapshot ->> 'candidate_id' is distinct from new.metadata ->> 'candidate_id'
         or new.provenance_snapshot ->> 'mapping_version' is distinct from 'phase4_usda_v1'
         or new.provenance_snapshot ->> 'reference_basis' is distinct from 'per_100_g' then
        raise exception 'provider snapshot item requires trusted USDA backend context' using errcode = '42501';
      end if;
      return new;
    end if;

    if new.source_provider_snapshot = 'open_food_facts'
       and v_operation in ('transient_off_log', 'transient_off_replace') then
      if v_authenticated_user_id is not null
         or v_internal_user_id is not null
         or v_off_internal_user_id is not null
         or v_transient_off_user_id is distinct from new.user_id
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
         or new.metadata ->> 'source_type' is distinct from 'transient_off_snapshot'
         or new.metadata ->> 'candidate_id' is null
         or (new.metadata ->> 'candidate_id')::uuid is distinct from
            public.fmz_phase4_provider_candidate_uuid_v5('open_food_facts:' || new.provider_food_id_snapshot)
         or new.metadata ->> 'mapping_version' is distinct from 'phase4_off_barcode_v1'
         or new.metadata ->> 'reference_basis' is distinct from (
           case when new.reference_unit_snapshot = 'ml' then 'per_100_ml' else 'per_100_g' end
         )
         or new.metadata ->> 'source_checksum' !~ '^[0-9a-f]{64}$'
         or new.provenance_snapshot ->> 'provider' is distinct from 'open_food_facts'
         or new.provenance_snapshot ->> 'provider_food_id' is distinct from new.provider_food_id_snapshot
         or new.provenance_snapshot ->> 'candidate_id' is distinct from new.metadata ->> 'candidate_id'
         or new.provenance_snapshot ->> 'mapping_version' is distinct from 'phase4_off_barcode_v1'
         or new.provenance_snapshot ->> 'reference_basis' is distinct from new.metadata ->> 'reference_basis'
         or new.provenance_snapshot ->> 'source_revision' is distinct from new.source_version_snapshot
         or new.provenance_snapshot ->> 'source_checksum' is distinct from new.metadata ->> 'source_checksum'
         or new.provenance_snapshot ->> 'license_code' is distinct from 'ODbL-1.0'
         or new.provenance_snapshot ->> 'license_url' is distinct from 'https://opendatacommons.org/licenses/odbl/1-0/'
         or jsonb_typeof(new.provenance_snapshot -> 'derivation') is distinct from 'object'
         or jsonb_typeof(new.provenance_snapshot -> 'attribution') is distinct from 'object' then
        raise exception 'transient OFF snapshot requires trusted backend context' using errcode = '42501';
      end if;
      return new;
    end if;

    if new.source_provider_snapshot = 'open_food_facts' then
      if v_authenticated_user_id is distinct from new.user_id
         or v_off_internal_user_id is distinct from new.user_id
         or v_internal_user_id is not null
         or v_transient_off_user_id is not null
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
         or v_operation not in ('off_log', 'off_replace')
         or new.metadata ->> 'off_product_id' is null
         or new.metadata ->> 'candidate_id' is distinct from new.metadata ->> 'off_product_id'
         or new.metadata ->> 'mapping_version' is null
         or new.metadata ->> 'reference_basis' is distinct from (
           case when new.reference_unit_snapshot = 'ml' then 'per_100_ml' else 'per_100_g' end
         )
         or new.provenance_snapshot ->> 'provider' is distinct from 'open_food_facts'
         or new.provenance_snapshot ->> 'provider_food_id' is distinct from new.provider_food_id_snapshot
         or new.provenance_snapshot ->> 'candidate_id' is distinct from new.metadata ->> 'off_product_id'
         or new.provenance_snapshot ->> 'mapping_version' is distinct from new.metadata ->> 'mapping_version'
         or new.provenance_snapshot ->> 'reference_basis' is distinct from new.metadata ->> 'reference_basis'
         or new.provenance_snapshot ->> 'source_revision' is distinct from new.source_version_snapshot
         or new.provenance_snapshot ->> 'license_code' is distinct from 'ODbL-1.0'
         or new.provenance_snapshot ->> 'license_url' is distinct from 'https://opendatacommons.org/licenses/odbl/1-0/'
         or new.provenance_snapshot -> 'derivation' is null
         or new.provenance_snapshot -> 'attribution' is null then
        raise exception 'OFF snapshot item requires trusted authenticated catalog context' using errcode = '42501';
      end if;
      return new;
    end if;
    raise exception 'unsupported provider snapshot source' using errcode = '42501';
  end if;

  if not exists (
    select 1 from public.foods f
    where f.id = new.food_id and f.status = 'active'
      and (f.catalog_scope = 'canonical' or (f.catalog_scope = 'custom' and f.owner_user_id = v_user_id))
  ) then
    raise exception 'food must be active and visible to authorized user' using errcode = '42501';
  end if;
  if new.food_portion_id is not null and not exists (
    select 1 from public.food_portions p
    where p.id = new.food_portion_id and p.food_id = new.food_id and p.status = 'active'
  ) then
    raise exception 'food portion must be active and belong to selected food' using errcode = '42501';
  end if;
  return new;
exception when invalid_text_representation then
  raise exception 'invalid provider snapshot identity' using errcode = '42501';
end;
$$;


create or replace function public.fmz_phase4_provider_transition_runtime_state(
  p_provider_code text,
  p_event text,
  p_retry_after_seconds integer default null,
  p_error_class text default null,
  p_upstream_limit integer default null,
  p_upstream_remaining integer default null,
  p_upstream_reset_at timestamptz default null,
  p_metadata jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog
as $$
declare
  v_provider_code text := lower(btrim(p_provider_code));
  v_event text := lower(btrim(p_event));
  v_now timestamptz := statement_timestamp();
  v_state public.nutrition_provider_runtime_state%rowtype;
  v_failure_count integer;
  v_backoff_seconds integer;
  v_probe_allowed boolean := false;
begin
  if v_provider_code is null or v_provider_code not in ('usda_fdc', 'open_food_facts') then
    raise exception 'unsupported nutrition provider';
  end if;
  if v_event is null or v_event not in ('success', 'failure', 'rate_limited', 'begin_probe') then
    raise exception 'unsupported provider runtime event';
  end if;
  if p_retry_after_seconds is not null and p_retry_after_seconds not between 1 and 3600 then
    raise exception 'invalid provider retry interval';
  end if;
  if p_error_class is not null and (
    char_length(p_error_class) not between 1 and 80 or p_error_class !~ '^[a-z0-9][a-z0-9._:-]*$'
  ) then raise exception 'invalid provider error class'; end if;
  if v_event in ('failure', 'rate_limited') and p_error_class is null then
    raise exception 'provider error class is required';
  end if;
  if (p_upstream_limit is null) <> (p_upstream_remaining is null) then
    raise exception 'upstream limit and remaining must be supplied together';
  end if;
  if p_upstream_limit is not null and (
    p_upstream_limit not between 0 and 1000000 or p_upstream_remaining not between 0 and p_upstream_limit
  ) then raise exception 'invalid upstream rate metadata'; end if;
  if p_metadata is null or jsonb_typeof(p_metadata) <> 'object' or octet_length(p_metadata::text) > 4096 then
    raise exception 'invalid provider runtime metadata';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('fmz_phase4_provider_runtime:' || v_provider_code, 0)
  );
  insert into public.nutrition_provider_runtime_state(provider_code)
  values (v_provider_code) on conflict (provider_code) do nothing;
  select * into v_state from public.nutrition_provider_runtime_state
  where provider_code = v_provider_code for update;
  if not found then raise exception 'provider runtime state integrity failure'; end if;

  if v_event = 'begin_probe' then
    if v_state.circuit_state = 'closed' then
      v_probe_allowed := true;
    elsif v_state.circuit_state = 'open' and v_state.next_probe_at <= v_now then
      update public.nutrition_provider_runtime_state
      set circuit_state = 'half_open', next_probe_at = null, metadata = p_metadata
      where provider_code = v_provider_code returning * into v_state;
      v_probe_allowed := true;
    end if;
    return pg_catalog.jsonb_build_object(
      'provider', v_provider_code, 'event', v_event,
      'probe_allowed', v_probe_allowed, 'state', pg_catalog.to_jsonb(v_state)
    );
  end if;

  if v_event = 'success' then
    update public.nutrition_provider_runtime_state
    set circuit_state = 'closed', consecutive_failures = 0, opened_at = null,
      next_probe_at = null, last_success_at = v_now, last_error_class = null,
      upstream_rate_limit = coalesce(p_upstream_limit, upstream_rate_limit),
      upstream_rate_remaining = coalesce(p_upstream_remaining, upstream_rate_remaining),
      upstream_rate_reset_at = coalesce(p_upstream_reset_at, upstream_rate_reset_at), metadata = p_metadata
    where provider_code = v_provider_code returning * into v_state;
  elsif v_event = 'rate_limited' then
    v_failure_count := v_state.consecutive_failures + 1;
    v_backoff_seconds := coalesce(p_retry_after_seconds, 3600);
    update public.nutrition_provider_runtime_state
    set circuit_state = 'open', consecutive_failures = v_failure_count,
      opened_at = coalesce(opened_at, v_now),
      next_probe_at = v_now + pg_catalog.make_interval(secs => v_backoff_seconds),
      last_failure_at = v_now, last_error_class = p_error_class,
      upstream_rate_limit = coalesce(p_upstream_limit, upstream_rate_limit),
      upstream_rate_remaining = coalesce(p_upstream_remaining, upstream_rate_remaining),
      upstream_rate_reset_at = coalesce(p_upstream_reset_at, upstream_rate_reset_at), metadata = p_metadata
    where provider_code = v_provider_code returning * into v_state;
  else
    v_failure_count := v_state.consecutive_failures + 1;
    v_backoff_seconds := coalesce(p_retry_after_seconds, case
      when v_failure_count <= 5 then 60 when v_failure_count = 6 then 120
      when v_failure_count = 7 then 300 when v_failure_count = 8 then 900 else 3600 end);
    if v_state.circuit_state = 'half_open' or v_failure_count >= 5 then
      update public.nutrition_provider_runtime_state
      set circuit_state = 'open', consecutive_failures = v_failure_count,
        opened_at = coalesce(opened_at, v_now),
        next_probe_at = v_now + pg_catalog.make_interval(secs => v_backoff_seconds),
        last_failure_at = v_now, last_error_class = p_error_class,
        upstream_rate_limit = coalesce(p_upstream_limit, upstream_rate_limit),
        upstream_rate_remaining = coalesce(p_upstream_remaining, upstream_rate_remaining),
        upstream_rate_reset_at = coalesce(p_upstream_reset_at, upstream_rate_reset_at), metadata = p_metadata
      where provider_code = v_provider_code returning * into v_state;
    else
      update public.nutrition_provider_runtime_state
      set consecutive_failures = v_failure_count, last_failure_at = v_now,
        last_error_class = p_error_class,
        upstream_rate_limit = coalesce(p_upstream_limit, upstream_rate_limit),
        upstream_rate_remaining = coalesce(p_upstream_remaining, upstream_rate_remaining),
        upstream_rate_reset_at = coalesce(p_upstream_reset_at, upstream_rate_reset_at), metadata = p_metadata
      where provider_code = v_provider_code returning * into v_state;
    end if;
  end if;
  return pg_catalog.jsonb_build_object(
    'provider', v_provider_code, 'event', v_event,
    'probe_allowed', false, 'state', pg_catalog.to_jsonb(v_state)
  );
end;
$$;

create or replace function public.fmz_phase4_resolve_member_barcode(
  p_user_id uuid,
  p_normalized_gtin14 text
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_result jsonb;
begin
  if p_user_id is null
     or not exists (select 1 from public.profiles p where p.id = p_user_id) then
    raise exception 'trusted member profile required' using errcode = '42501';
  end if;
  if p_normalized_gtin14 is null
     or p_normalized_gtin14 !~ '^[0-9]{14}$'
     or public.fmz_phase4_normalize_gtin14(p_normalized_gtin14) is distinct from p_normalized_gtin14 then
    raise exception 'valid normalized GTIN-14 required' using errcode = '22023';
  end if;

  select jsonb_build_object(
    'result_type', 'off_branded_food',
    'source_provider', p.source_provider,
    'source_id', p.id,
    'barcode', p.barcode_original,
    'display_name', coalesce(p.product_name_nl, p.product_name),
    'brand', p.brand,
    'nutrition_basis', p.nutrition_basis,
    'reference_amount', 100,
    'reference_unit', case when p.nutrition_basis = 'per_100_ml' then 'ml' else 'g' end,
    'energy_kcal_reference', p.energy_kcal_100,
    'protein_grams_reference', p.protein_grams_100,
    'carbohydrate_grams_reference', p.carbohydrate_grams_100,
    'fat_grams_reference', p.fat_grams_100,
    'fiber_grams_reference', p.fiber_grams_100,
    'quality_status', p.quality_status,
    'loggable', true,
    'local_barcode_match', true
  ) into v_result
  from public.nutrition_off_products p
  join public.nutrition_off_catalog_releases r on r.id = p.release_id
  where p.normalized_gtin14 = p_normalized_gtin14
    and p.lifecycle_status = 'active'
    and p.quality_status in ('complete', 'reviewed')
    and r.status in ('imported', 'superseded')
  limit 1;
  if v_result is not null then return v_result; end if;

  select jsonb_build_object(
    'result_type', case when f.catalog_scope = 'custom' then 'custom_food' else 'generic_food' end,
    'source_provider', f.source_provider,
    'source_id', f.id,
    'id', f.id,
    'catalog_scope', f.catalog_scope,
    'barcode', f.barcode,
    'display_name', coalesce(nullif(btrim(f.metadata ->> 'dutch_display_label'), ''), f.name),
    'name', f.name,
    'brand', f.brand,
    'reference_amount', f.reference_amount,
    'reference_unit', f.reference_unit,
    'reference_mass_grams', f.reference_mass_grams,
    'reference_volume_ml', f.reference_volume_ml,
    'density_g_per_ml', f.density_g_per_ml,
    'energy_kcal', f.energy_kcal,
    'protein_grams', f.protein_grams,
    'carbohydrate_grams', f.carbohydrate_grams,
    'fat_grams', f.fat_grams,
    'fiber_grams', f.fiber_grams,
    'quality_status', f.quality_status,
    'status', f.status,
    'metadata', f.metadata,
    'local_barcode_match', true
  ) into v_result
  from public.foods f
  where public.fmz_phase4_normalize_gtin14(f.barcode) = p_normalized_gtin14
    and f.status = 'active'
    and (
      (f.catalog_scope = 'custom' and f.owner_user_id = p_user_id)
      or (
        f.catalog_scope = 'canonical'
        and f.owner_user_id is null
        and f.quality_status in ('reviewed', 'verified')
      )
    )
  order by (f.catalog_scope = 'custom') desc, f.id
  limit 1;
  return v_result;
end;
$$;

create or replace function public.fmz_phase4_upsert_custom_food_with_barcode(
  p_food_id uuid,
  p_name text,
  p_brand text,
  p_barcode text,
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
  v_gtin14 text := public.fmz_phase4_normalize_gtin14(p_barcode);
  v_before public.foods%rowtype;
  v_upserted jsonb;
  v_food public.foods%rowtype;
begin
  if v_user_id is null then
    raise exception 'authenticated user required' using errcode = '42501';
  end if;
  if v_gtin14 is null then
    raise exception 'valid EAN-8, UPC-A, EAN-13, or GTIN-14 required' using errcode = '22023';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('fmz_phase4_custom_food_barcode:' || v_user_id::text || ':' || v_gtin14, 0)
  );

  select * into v_before from public.foods f where f.id = p_food_id;
  if found and (
    v_before.catalog_scope <> 'custom'
    or v_before.owner_user_id is distinct from v_user_id
  ) then
    raise exception 'custom food does not belong to authenticated user' using errcode = '42501';
  end if;
  if found and p_expected_updated_at is null
     and public.fmz_phase4_normalize_gtin14(v_before.barcode) is distinct from v_gtin14 then
    raise exception 'custom food changed; refresh before saving' using errcode = '40001';
  end if;
  if exists (
    select 1 from public.foods f
    where f.owner_user_id = v_user_id and f.catalog_scope = 'custom' and f.status = 'active'
      and f.id <> p_food_id and public.fmz_phase4_normalize_gtin14(f.barcode) = v_gtin14
  ) then
    raise exception 'this barcode is already assigned to another active custom food' using errcode = '23505';
  end if;

  v_upserted := public.fmz_phase4_upsert_custom_food(
    p_food_id, p_name, p_brand, p_reference_amount, p_reference_unit,
    p_reference_mass_grams, p_reference_volume_ml, p_density_g_per_ml,
    p_energy_kcal, p_protein_grams, p_carbohydrate_grams, p_fat_grams,
    p_fiber_grams, p_expected_updated_at
  );

  select * into v_food from public.foods f where f.id = p_food_id and f.owner_user_id = v_user_id;
  if not found then raise exception 'custom food save failed' using errcode = '40001'; end if;
  if public.fmz_phase4_normalize_gtin14(v_food.barcode) is distinct from v_gtin14 then
    update public.foods set barcode = v_gtin14
    where id = p_food_id and owner_user_id = v_user_id and updated_at = v_food.updated_at
    returning * into v_food;
    if not found then raise exception 'custom food changed; refresh before saving' using errcode = '40001'; end if;
  end if;
  return to_jsonb(v_food);
end;
$$;

create or replace function public.fmz_phase4_validate_transient_off_candidate(p_candidate jsonb)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, pg_temp
as $$
declare
  v_gtin14 text;
  v_candidate_id uuid;
  v_reference_unit text;
  v_reference_basis text;
  v_source_version text;
  v_source_checksum text;
  v_retrieved_at timestamptz;
  v_source_updated_at timestamptz;
  v_value numeric;
  v_key text;
begin
  if jsonb_typeof(p_candidate) is distinct from 'object'
     or (select count(*) from pg_catalog.jsonb_object_keys(p_candidate)) <> 21
     or p_candidate - array[
       'provider', 'provider_food_id', 'candidate_id', 'mapping_version',
       'provider_data_type', 'food_name', 'brand', 'barcode_original',
       'normalized_gtin14', 'reference_amount', 'reference_unit',
       'energy_kcal_per_100', 'protein_grams_per_100',
       'carbohydrate_grams_per_100', 'fat_grams_per_100',
       'fiber_grams_per_100', 'source_version', 'source_checksum',
       'retrieved_at', 'source_updated_at', 'provenance'
     ]::text[] <> '{}'::jsonb then
    raise exception 'trusted transient OFF candidate has unsupported fields' using errcode = '22023';
  end if;
  if jsonb_typeof(p_candidate -> 'provider') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'provider_food_id') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'candidate_id') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'mapping_version') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'provider_data_type') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'food_name') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'brand') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'barcode_original') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'normalized_gtin14') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'reference_amount') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'reference_unit') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'energy_kcal_per_100') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'protein_grams_per_100') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'carbohydrate_grams_per_100') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'fat_grams_per_100') is distinct from 'number'
     or jsonb_typeof(p_candidate -> 'fiber_grams_per_100') not in ('number', 'null')
     or jsonb_typeof(p_candidate -> 'source_version') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'source_checksum') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'retrieved_at') is distinct from 'string'
     or jsonb_typeof(p_candidate -> 'source_updated_at') not in ('string', 'null')
     or jsonb_typeof(p_candidate -> 'provenance') is distinct from 'object' then
    raise exception 'trusted transient OFF candidate is malformed' using errcode = '22023';
  end if;

  begin
    v_gtin14 := p_candidate ->> 'normalized_gtin14';
    v_candidate_id := (p_candidate ->> 'candidate_id')::uuid;
    v_retrieved_at := (p_candidate ->> 'retrieved_at')::timestamptz;
    v_source_updated_at := case when p_candidate -> 'source_updated_at' = 'null'::jsonb then null
      else (p_candidate ->> 'source_updated_at')::timestamptz end;
  exception when invalid_text_representation or datetime_field_overflow then
    raise exception 'trusted transient OFF candidate contains invalid typed values' using errcode = '22023';
  end;
  v_reference_unit := p_candidate ->> 'reference_unit';
  v_reference_basis := case when v_reference_unit = 'ml' then 'per_100_ml' else 'per_100_g' end;
  v_source_version := p_candidate ->> 'source_version';
  v_source_checksum := p_candidate ->> 'source_checksum';

  if p_candidate ->> 'provider' is distinct from 'open_food_facts'
     or p_candidate ->> 'provider_food_id' is distinct from v_gtin14
     or public.fmz_phase4_normalize_gtin14(v_gtin14) is distinct from v_gtin14
     or public.fmz_phase4_normalize_gtin14(p_candidate ->> 'barcode_original') is distinct from v_gtin14
     or v_candidate_id is distinct from public.fmz_phase4_provider_candidate_uuid_v5('open_food_facts:' || v_gtin14)
     or p_candidate ->> 'mapping_version' is distinct from 'phase4_off_barcode_v1'
     or p_candidate ->> 'provider_data_type' is distinct from 'off_branded'
     or p_candidate ->> 'reference_amount' is distinct from '100'
     or v_reference_unit not in ('g', 'ml')
     or char_length(btrim(p_candidate ->> 'food_name')) not between 1 and 240
     or char_length(btrim(p_candidate ->> 'brand')) not between 1 and 160
     or v_source_version !~ '^off_rev:[1-9][0-9]{0,19}$'
     or v_source_checksum !~ '^[0-9a-f]{64}$'
     or v_retrieved_at is null or v_retrieved_at > now() + interval '5 minutes'
     or (v_source_updated_at is not null and v_source_updated_at > now() + interval '5 minutes')
     or p_candidate -> 'provenance' ->> 'provider' is distinct from 'open_food_facts'
     or p_candidate -> 'provenance' ->> 'provider_food_id' is distinct from v_gtin14
     or p_candidate -> 'provenance' ->> 'candidate_id' is distinct from v_candidate_id::text
     or p_candidate -> 'provenance' ->> 'mapping_version' is distinct from 'phase4_off_barcode_v1'
     or p_candidate -> 'provenance' ->> 'reference_basis' is distinct from v_reference_basis
     or p_candidate -> 'provenance' ->> 'source_revision' is distinct from v_source_version
     or p_candidate -> 'provenance' ->> 'source_checksum' is distinct from v_source_checksum
     or p_candidate -> 'provenance' ->> 'retrieved_at' is distinct from p_candidate ->> 'retrieved_at'
     or p_candidate -> 'provenance' ->> 'source_updated_at' is distinct from p_candidate ->> 'source_updated_at'
     or p_candidate -> 'provenance' ->> 'license_code' is distinct from 'ODbL-1.0'
     or p_candidate -> 'provenance' ->> 'license_url' is distinct from 'https://opendatacommons.org/licenses/odbl/1-0/'
     or not (p_candidate -> 'provenance' -> 'countries_tags' @> '["en:netherlands"]'::jsonb)
     or jsonb_typeof(p_candidate -> 'provenance' -> 'attribution') is distinct from 'object'
     or jsonb_typeof(p_candidate -> 'provenance' -> 'derivation') is distinct from 'object' then
    raise exception 'trusted transient OFF candidate failed identity validation' using errcode = '22023';
  end if;

  foreach v_key in array array[
    'energy_kcal_per_100', 'protein_grams_per_100',
    'carbohydrate_grams_per_100', 'fat_grams_per_100'
  ] loop
    v_value := (p_candidate ->> v_key)::numeric;
    if v_value::text in ('NaN', 'Infinity', '-Infinity') or v_value < 0
       or (v_key = 'energy_kcal_per_100' and v_value > 900)
       or (v_key <> 'energy_kcal_per_100' and v_value > 100) then
      raise exception 'trusted transient OFF candidate has invalid nutrition' using errcode = '22023';
    end if;
  end loop;
  if p_candidate -> 'fiber_grams_per_100' <> 'null'::jsonb then
    v_value := (p_candidate ->> 'fiber_grams_per_100')::numeric;
    if v_value::text in ('NaN', 'Infinity', '-Infinity') or v_value < 0 or v_value > 100 then
      raise exception 'trusted transient OFF candidate has invalid fiber' using errcode = '22023';
    end if;
  end if;
  return p_candidate;
exception when invalid_text_representation or numeric_value_out_of_range then
  raise exception 'trusted transient OFF candidate contains invalid numeric values' using errcode = '22023';
end;
$$;

create or replace function public.fmz_phase4_transient_off_food_item_mutation(
  p_operation text,
  p_user_id uuid,
  p_original_item_id uuid,
  p_item_id uuid,
  p_request_id uuid,
  p_expected_original_updated_at timestamptz,
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
  v_operation text := lower(btrim(p_operation));
  v_user_id uuid := p_user_id;
  v_candidate jsonb;
  v_gtin14 text;
  v_reference_unit text;
  v_reference_basis text;
  v_normalized_notes text := nullif(btrim(p_notes), '');
  v_timezone text;
  v_saved_timezone text;
  v_today date;
  v_anchor timestamptz;
  v_expected_offset integer;
  v_has_full_access boolean;
  v_target public.nutrition_targets%rowtype;
  v_log public.food_logs%rowtype;
  v_original public.food_log_items%rowtype;
  v_existing public.food_log_items%rowtype;
  v_conflict public.food_log_items%rowtype;
  v_item public.food_log_items%rowtype;
  v_sort_order integer;
  v_factor numeric;
  v_request_payload jsonb;
  v_metadata jsonb;
begin
  if v_operation is null or v_operation not in ('log', 'replace')
     or v_user_id is null or p_item_id is null or p_request_id is null then
    raise exception 'trusted OFF mutation identity is incomplete' using errcode = '22023';
  end if;
  if not exists (select 1 from public.profiles p where p.id = v_user_id) then
    raise exception 'authorized user profile not found' using errcode = '42501';
  end if;
  if v_operation = 'log' and (
    p_original_item_id is not null or p_expected_original_updated_at is not null or p_log_date is null
  ) then raise exception 'transient OFF log parameters are invalid' using errcode = '22023'; end if;
  if v_operation = 'replace' and (
    p_original_item_id is null or p_expected_original_updated_at is null or p_original_item_id = p_item_id
  ) then raise exception 'transient OFF replacement parameters are invalid' using errcode = '22023'; end if;
  if p_meal_moment not in ('breakfast', 'lunch', 'dinner', 'snacks') then
    raise exception 'unsupported meal moment' using errcode = '22023';
  end if;
  if p_consumed_quantity is null or p_consumed_quantity::text in ('NaN', 'Infinity', '-Infinity')
     or p_consumed_quantity <= 0 or p_consumed_quantity > 100000 then
    raise exception 'transient OFF quantity is outside supported bounds' using errcode = '22023';
  end if;
  if p_consumed_unit not in ('g', 'ml') then
    raise exception 'transient OFF unit must be grams or millilitres' using errcode = '22023';
  end if;
  if v_normalized_notes is not null and char_length(v_normalized_notes) > 1000 then
    raise exception 'notes exceed supported length' using errcode = '22023';
  end if;

  v_candidate := public.fmz_phase4_validate_transient_off_candidate(p_candidate);
  v_gtin14 := v_candidate ->> 'provider_food_id';
  v_reference_unit := v_candidate ->> 'reference_unit';
  v_reference_basis := case when v_reference_unit = 'ml' then 'per_100_ml' else 'per_100_g' end;
  if p_consumed_unit is distinct from v_reference_unit then
    raise exception 'transient OFF quantity unit must match its nutrition basis' using errcode = '22023';
  end if;

  -- Keep explicit nullable candidate fields intact so historical replay can
  -- revalidate the exact immutable 21-field snapshot.
  v_request_payload := jsonb_build_object(
    'operation', v_operation,
    'original_item_id', p_original_item_id,
    'item_id', p_item_id,
    'expected_original_updated_at', p_expected_original_updated_at,
    'log_date', p_log_date,
    'timezone_name', p_timezone_name,
    'timezone_offset_minutes', p_timezone_offset_minutes,
    'meal_moment', p_meal_moment,
    'consumed_quantity', p_consumed_quantity,
    'consumed_unit', p_consumed_unit,
    'notes', v_normalized_notes,
    'consumed_at', p_consumed_at,
    'candidate', v_candidate
  );

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('fmz_phase4_food_log_request:' || v_user_id::text || ':' || p_request_id::text, 0)
  );

  if v_operation = 'log' then
    select i.* into v_existing from public.food_log_items i
    where i.user_id = v_user_id and i.request_id = p_request_id;
    if found then
      if v_existing.id is distinct from p_item_id or v_existing.food_id is not null
         or v_existing.metadata ->> 'operation' is distinct from 'transient_off_log'
         or v_existing.metadata -> 'transient_off_request' is distinct from v_request_payload then
        raise exception 'transient OFF request UUID was reused with a different payload' using errcode = '23505';
      end if;
      select l.* into v_log from public.food_logs l
      where l.id = v_existing.food_log_id and l.user_id = v_user_id;
      return jsonb_build_object(
        'item', to_jsonb(v_existing), 'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date),
        'idempotent_replay', true
      );
    end if;

    v_timezone := btrim(p_timezone_name);
    if v_timezone is null or not exists (
      select 1 from pg_catalog.pg_timezone_names tz where tz.name = v_timezone
    ) then raise exception 'valid IANA timezone required' using errcode = '22023'; end if;
    select p.timezone_name into v_saved_timezone from public.nutrition_preferences p where p.user_id = v_user_id;
    if found and v_saved_timezone is distinct from v_timezone then
      raise exception 'timezone differs from Nutrition preference; update preference first' using errcode = '22023';
    end if;
    v_today := (now() at time zone v_timezone)::date;
    v_has_full_access := public.fmz_phase4_has_full_nutrition_access(v_user_id);
    if p_log_date > v_today then raise exception 'future Nutrition logging is not supported' using errcode = '22023'; end if;
    if not v_has_full_access and p_log_date < v_today - 6 then
      raise exception 'Free Nutrition history is limited to seven local calendar days' using errcode = '42501';
    end if;
    if p_consumed_at is not null and (p_consumed_at at time zone v_timezone)::date is distinct from p_log_date then
      raise exception 'consumed timestamp must belong to selected local log date' using errcode = '22023';
    end if;
    v_anchor := coalesce(p_consumed_at, (p_log_date::timestamp + interval '12 hours') at time zone v_timezone);
    v_expected_offset := round(extract(epoch from (
      (v_anchor at time zone v_timezone) - (v_anchor at time zone 'UTC')
    )) / 60);
    if p_timezone_offset_minutes is null or p_timezone_offset_minutes::integer <> v_expected_offset then
      raise exception 'timezone offset does not match selected timezone and date' using errcode = '22023';
    end if;

    perform pg_catalog.pg_advisory_xact_lock(
      pg_catalog.hashtextextended('fmz_phase4_food_log:' || v_user_id::text || ':' || p_log_date::text, 0)
    );
    select i.* into v_conflict from public.food_log_items i where i.id = p_item_id;
    if found then raise exception 'transient OFF item UUID is unavailable' using errcode = '23505'; end if;

    select * into v_target from public.nutrition_targets t
    where t.user_id = v_user_id and t.target_context = 'daily'
      and t.status in ('active', 'superseded') and t.effective_from <= p_log_date
      and (t.effective_to is null or t.effective_to >= p_log_date)
    order by (t.status = 'active') desc, t.effective_from desc, t.created_at desc limit 1;
    if v_saved_timezone is null then
      insert into public.nutrition_preferences(user_id, timezone_name)
      values (v_user_id, v_timezone) on conflict (user_id) do nothing;
    end if;
    insert into public.food_logs(
      id, user_id, log_date, timezone_name, timezone_offset_minutes,
      target_id, target_energy_kcal_snapshot, target_protein_grams_snapshot,
      target_carbohydrate_grams_snapshot, target_fat_grams_snapshot,
      target_fiber_grams_snapshot, status, source, metadata
    ) values (
      pg_catalog.gen_random_uuid(), v_user_id, p_log_date, v_timezone, p_timezone_offset_minutes,
      v_target.id, v_target.energy_kcal, v_target.protein_grams, v_target.carbohydrate_grams,
      v_target.fat_grams, v_target.fiber_grams, 'active', 'phase4_member',
      jsonb_build_object('created_by', 'fmz_phase4_log_transient_off_food_item')
    ) on conflict (user_id, log_date) do nothing;
    select * into v_log from public.food_logs l
    where l.user_id = v_user_id and l.log_date = p_log_date and l.status = 'active' for update;
    if not found then raise exception 'active Nutrition day log unavailable' using errcode = '23514'; end if;
    select coalesce(max(i.sort_order), -1) + 1 into v_sort_order from public.food_log_items i
    where i.user_id = v_user_id and i.food_log_id = v_log.id and i.meal_moment = p_meal_moment;
  else
    perform pg_catalog.pg_advisory_xact_lock(
      pg_catalog.hashtextextended('fmz_phase4_food_log_item_request:' || v_user_id::text || ':' || p_original_item_id::text, 0)
    );
    select i.* into v_original from public.food_log_items i
    where i.id = p_original_item_id and i.user_id = v_user_id for update;
    if not found then raise exception 'transient OFF food log item not found' using errcode = '42501'; end if;
    select l.* into v_log from public.food_logs l
    where l.id = v_original.food_log_id and l.user_id = v_user_id and l.status = 'active' for update;
    if not found then raise exception 'active Nutrition day log unavailable' using errcode = '42501'; end if;

    select i.* into v_existing from public.food_log_items i
    where i.user_id = v_user_id and i.request_id = p_request_id;
    if found then
      if v_existing.id is distinct from p_item_id or v_existing.food_id is not null
         or v_existing.food_log_id is distinct from v_original.food_log_id
         or v_existing.metadata ->> 'operation' is distinct from 'transient_off_replace'
         or v_existing.metadata ->> 'replaces_item_id' is distinct from p_original_item_id::text
         or v_existing.metadata -> 'transient_off_replacement_request' is distinct from v_request_payload then
        raise exception 'transient OFF replacement request UUID was reused with a different payload' using errcode = '23505';
      end if;
      if v_original.status is distinct from 'archived' then
        raise exception 'transient OFF replacement replay found incomplete archive state' using errcode = '40001';
      end if;
      return jsonb_build_object(
        'replacement_item', to_jsonb(v_existing),
        'archived_original', jsonb_build_object(
          'id', v_original.id, 'status', v_original.status,
          'archived_at', v_original.archived_at, 'updated_at', v_original.updated_at
        ),
        'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date), 'idempotent_replay', true
      );
    end if;
    if v_original.status is distinct from 'active'
       or v_original.updated_at is distinct from p_expected_original_updated_at then
      raise exception 'transient OFF food log item changed; refresh before replacing' using errcode = '40001';
    end if;
    select i.* into v_conflict from public.food_log_items i where i.id = p_item_id;
    if found then raise exception 'replacement item UUID is unavailable' using errcode = '23505'; end if;
    perform pg_catalog.pg_advisory_xact_lock(
      pg_catalog.hashtextextended('fmz_phase4_food_log_item_request:' || v_user_id::text || ':' || p_item_id::text, 0)
    );
    select i.* into v_conflict from public.food_log_items i where i.id = p_item_id;
    if found then raise exception 'replacement item UUID is unavailable' using errcode = '23505'; end if;

    select coalesce(p.timezone_name, v_log.timezone_name, 'UTC') into v_timezone
    from (select 1) seed left join public.nutrition_preferences p on p.user_id = v_user_id;
    v_timezone := coalesce(v_timezone, v_log.timezone_name, 'UTC');
    v_today := (now() at time zone v_timezone)::date;
    v_has_full_access := public.fmz_phase4_has_full_nutrition_access(v_user_id);
    if v_log.log_date > v_today then raise exception 'future Nutrition day is unavailable' using errcode = '22023'; end if;
    if not v_has_full_access and v_log.log_date < v_today - 6 then
      raise exception 'Free Nutrition history is limited to seven local calendar days' using errcode = '42501';
    end if;
    if p_meal_moment = v_original.meal_moment then
      v_sort_order := v_original.sort_order;
    else
      select coalesce(max(i.sort_order), -1) + 1 into v_sort_order from public.food_log_items i
      where i.user_id = v_user_id and i.food_log_id = v_original.food_log_id
        and i.meal_moment = p_meal_moment and i.status = 'active';
    end if;
  end if;

  if v_sort_order > 10000 then raise exception 'destination meal order is full' using errcode = '22023'; end if;
  v_factor := p_consumed_quantity / 100;
  v_metadata := jsonb_build_object(
    'calculation_version', 'phase4_transient_off_snapshot_v1',
    'operation', case when v_operation = 'log' then 'transient_off_log' else 'transient_off_replace' end,
    'source_type', 'transient_off_snapshot',
    'replaces_item_id', p_original_item_id,
    'candidate_id', v_candidate ->> 'candidate_id',
    'mapping_version', 'phase4_off_barcode_v1',
    'provider_data_type', 'off_branded',
    'reference_basis', v_reference_basis,
    'barcode_original', v_candidate ->> 'barcode_original',
    'source_checksum', v_candidate ->> 'source_checksum',
    'retrieved_at', v_candidate ->> 'retrieved_at',
    'source_updated_at', v_candidate ->> 'source_updated_at',
    case when v_operation = 'log' then 'transient_off_request' else 'transient_off_replacement_request' end,
    v_request_payload
  );
  perform pg_catalog.set_config('fmz.phase4_transient_off_snapshot_user_id', v_user_id::text, true);

  insert into public.food_log_items(
    id, user_id, food_log_id, food_id, food_portion_id, meal_moment,
    sort_order, consumed_quantity, consumed_unit, food_name_snapshot,
    brand_snapshot, reference_amount_snapshot, reference_unit_snapshot,
    portion_label_snapshot, portion_equivalent_amount_snapshot,
    portion_equivalent_unit_snapshot, density_g_per_ml_snapshot,
    calculation_basis, energy_kcal_snapshot, protein_grams_snapshot,
    carbohydrate_grams_snapshot, fat_grams_snapshot, fiber_grams_snapshot,
    source_provider_snapshot, provider_food_id_snapshot, source_version_snapshot,
    provenance_snapshot, notes, status, request_id, consumed_at, metadata
  ) values (
    p_item_id, v_user_id, v_log.id, null, null, p_meal_moment,
    v_sort_order, p_consumed_quantity, v_reference_unit,
    v_candidate ->> 'food_name', v_candidate ->> 'brand', 100, v_reference_unit,
    null, null, null, null, 'direct_reference',
    round((v_candidate ->> 'energy_kcal_per_100')::numeric * v_factor, 3),
    round((v_candidate ->> 'protein_grams_per_100')::numeric * v_factor, 3),
    round((v_candidate ->> 'carbohydrate_grams_per_100')::numeric * v_factor, 3),
    round((v_candidate ->> 'fat_grams_per_100')::numeric * v_factor, 3),
    case when v_candidate -> 'fiber_grams_per_100' = 'null'::jsonb then null
      else round((v_candidate ->> 'fiber_grams_per_100')::numeric * v_factor, 3) end,
    'open_food_facts', v_gtin14, v_candidate ->> 'source_version',
    v_candidate -> 'provenance', v_normalized_notes, 'active', p_request_id,
    case when v_operation = 'log' then p_consumed_at else v_original.consumed_at end,
    v_metadata
  ) returning * into v_item;

  if v_operation = 'replace' then
    update public.food_log_items set status = 'archived'
    where id = p_original_item_id and user_id = v_user_id and status = 'active'
      and updated_at = p_expected_original_updated_at
    returning * into v_original;
    if not found then
      raise exception 'transient OFF food log item changed; atomic replacement rolled back' using errcode = '40001';
    end if;
    return jsonb_build_object(
      'replacement_item', to_jsonb(v_item),
      'archived_original', jsonb_build_object(
        'id', v_original.id, 'status', v_original.status,
        'archived_at', v_original.archived_at, 'updated_at', v_original.updated_at
      ),
      'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date), 'idempotent_replay', false
    );
  end if;
  return jsonb_build_object(
    'item', to_jsonb(v_item), 'day', public.fmz_phase4_day_payload(v_user_id, v_log.log_date),
    'idempotent_replay', false
  );
end;
$$;

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
language sql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
  select public.fmz_phase4_transient_off_food_item_mutation(
    'log', p_user_id, null, p_item_id, p_request_id, null,
    p_log_date, p_timezone_name, p_timezone_offset_minutes, p_meal_moment,
    p_consumed_quantity, p_consumed_unit, p_notes, p_consumed_at, p_candidate
  );
$$;

create or replace function public.fmz_phase4_replace_transient_off_food_item(
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
language sql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
  select public.fmz_phase4_transient_off_food_item_mutation(
    'replace', p_user_id, p_original_item_id, p_replacement_item_id,
    p_replacement_request_id, p_expected_original_updated_at,
    null, null, null, p_meal_moment, p_consumed_quantity,
    p_consumed_unit, p_notes, null, p_candidate
  );
$$;

create or replace function public.fmz_phase4_resolve_transient_off_food_log_item(
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
  v_candidate jsonb;
  v_request jsonb;
  v_factor numeric;
begin
  if p_user_id is null or p_original_item_id is null then
    raise exception 'trusted user and transient OFF item are required' using errcode = '22023';
  end if;
  select i.* into v_item
  from public.food_log_items i
  join public.food_logs l on l.id = i.food_log_id and l.user_id = p_user_id
  where i.id = p_original_item_id and i.user_id = p_user_id
    and i.status = 'active' and l.status = 'active';
  if not found then
    raise exception 'active transient OFF food log item is unavailable for this user' using errcode = '42501';
  end if;
  if v_item.metadata ->> 'operation' = 'transient_off_log' then
    v_request := v_item.metadata -> 'transient_off_request';
  elsif v_item.metadata ->> 'operation' = 'transient_off_replace' then
    v_request := v_item.metadata -> 'transient_off_replacement_request';
  else
    raise exception 'historical item is not a transient OFF snapshot' using errcode = '42501';
  end if;
  v_candidate := public.fmz_phase4_validate_transient_off_candidate(v_request -> 'candidate');
  v_factor := v_item.consumed_quantity / 100;
  if v_item.food_id is not null or v_item.food_portion_id is not null
     or v_item.source_provider_snapshot is distinct from 'open_food_facts'
     or v_item.provider_food_id_snapshot is distinct from v_candidate ->> 'provider_food_id'
     or v_item.food_name_snapshot is distinct from v_candidate ->> 'food_name'
     or v_item.brand_snapshot is distinct from v_candidate ->> 'brand'
     or v_item.reference_amount_snapshot is distinct from 100::numeric
     or v_item.reference_unit_snapshot is distinct from v_candidate ->> 'reference_unit'
     or v_item.consumed_unit is distinct from v_candidate ->> 'reference_unit'
     or v_item.source_version_snapshot is distinct from v_candidate ->> 'source_version'
     or v_item.provenance_snapshot is distinct from v_candidate -> 'provenance'
     or v_item.metadata ->> 'candidate_id' is distinct from v_candidate ->> 'candidate_id'
     or v_item.metadata ->> 'source_checksum' is distinct from v_candidate ->> 'source_checksum'
     or v_item.energy_kcal_snapshot is distinct from round((v_candidate ->> 'energy_kcal_per_100')::numeric * v_factor, 3)
     or v_item.protein_grams_snapshot is distinct from round((v_candidate ->> 'protein_grams_per_100')::numeric * v_factor, 3)
     or v_item.carbohydrate_grams_snapshot is distinct from round((v_candidate ->> 'carbohydrate_grams_per_100')::numeric * v_factor, 3)
     or v_item.fat_grams_snapshot is distinct from round((v_candidate ->> 'fat_grams_per_100')::numeric * v_factor, 3)
     or v_item.fiber_grams_snapshot is distinct from (case
       when v_candidate -> 'fiber_grams_per_100' = 'null'::jsonb then null
       else round((v_candidate ->> 'fiber_grams_per_100')::numeric * v_factor, 3)
     end) then
    raise exception 'historical transient OFF snapshot failed immutable identity validation' using errcode = '22023';
  end if;
  return v_candidate;
end;
$$;

revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from public;
revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from anon;
revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from authenticated;
revoke all on function public.fmz_phase4_enforce_food_log_item_owner() from service_role;

revoke all on function public.fmz_phase4_validate_transient_off_candidate(jsonb) from public;
revoke all on function public.fmz_phase4_validate_transient_off_candidate(jsonb) from anon;
revoke all on function public.fmz_phase4_validate_transient_off_candidate(jsonb) from authenticated;
revoke all on function public.fmz_phase4_validate_transient_off_candidate(jsonb) from service_role;

revoke all on function public.fmz_phase4_transient_off_food_item_mutation(
  text,uuid,uuid,uuid,uuid,timestamp with time zone,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb
) from public;
revoke all on function public.fmz_phase4_transient_off_food_item_mutation(
  text,uuid,uuid,uuid,uuid,timestamp with time zone,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb
) from anon;
revoke all on function public.fmz_phase4_transient_off_food_item_mutation(
  text,uuid,uuid,uuid,uuid,timestamp with time zone,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb
) from authenticated;
revoke all on function public.fmz_phase4_transient_off_food_item_mutation(
  text,uuid,uuid,uuid,uuid,timestamp with time zone,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb
) from service_role;

revoke all on function public.fmz_phase4_resolve_member_barcode(uuid,text) from public;
revoke all on function public.fmz_phase4_resolve_member_barcode(uuid,text) from anon;
revoke all on function public.fmz_phase4_resolve_member_barcode(uuid,text) from authenticated;
revoke all on function public.fmz_phase4_resolve_member_barcode(uuid,text) from service_role;
grant execute on function public.fmz_phase4_resolve_member_barcode(uuid,text) to service_role;

revoke all on function public.fmz_phase4_upsert_custom_food_with_barcode(
  uuid,text,text,text,numeric,text,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,timestamp with time zone
) from public;
revoke all on function public.fmz_phase4_upsert_custom_food_with_barcode(
  uuid,text,text,text,numeric,text,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,timestamp with time zone
) from anon;
revoke all on function public.fmz_phase4_upsert_custom_food_with_barcode(
  uuid,text,text,text,numeric,text,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,timestamp with time zone
) from authenticated;
revoke all on function public.fmz_phase4_upsert_custom_food_with_barcode(
  uuid,text,text,text,numeric,text,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,timestamp with time zone
) from service_role;
grant execute on function public.fmz_phase4_upsert_custom_food_with_barcode(
  uuid,text,text,text,numeric,text,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,timestamp with time zone
) to authenticated;

revoke all on function public.fmz_phase4_log_transient_off_food_item(
  uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb
) from public;
revoke all on function public.fmz_phase4_log_transient_off_food_item(
  uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb
) from anon;
revoke all on function public.fmz_phase4_log_transient_off_food_item(
  uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb
) from authenticated;
revoke all on function public.fmz_phase4_log_transient_off_food_item(
  uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb
) from service_role;
grant execute on function public.fmz_phase4_log_transient_off_food_item(
  uuid,uuid,uuid,date,text,smallint,text,numeric,text,text,timestamp with time zone,jsonb
) to service_role;

revoke all on function public.fmz_phase4_replace_transient_off_food_item(
  uuid,uuid,uuid,uuid,timestamp with time zone,text,numeric,text,text,jsonb
) from public;
revoke all on function public.fmz_phase4_replace_transient_off_food_item(
  uuid,uuid,uuid,uuid,timestamp with time zone,text,numeric,text,text,jsonb
) from anon;
revoke all on function public.fmz_phase4_replace_transient_off_food_item(
  uuid,uuid,uuid,uuid,timestamp with time zone,text,numeric,text,text,jsonb
) from authenticated;
revoke all on function public.fmz_phase4_replace_transient_off_food_item(
  uuid,uuid,uuid,uuid,timestamp with time zone,text,numeric,text,text,jsonb
) from service_role;
grant execute on function public.fmz_phase4_replace_transient_off_food_item(
  uuid,uuid,uuid,uuid,timestamp with time zone,text,numeric,text,text,jsonb
) to service_role;

revoke all on function public.fmz_phase4_resolve_transient_off_food_log_item(uuid,uuid) from public;
revoke all on function public.fmz_phase4_resolve_transient_off_food_log_item(uuid,uuid) from anon;
revoke all on function public.fmz_phase4_resolve_transient_off_food_log_item(uuid,uuid) from authenticated;
revoke all on function public.fmz_phase4_resolve_transient_off_food_log_item(uuid,uuid) from service_role;
grant execute on function public.fmz_phase4_resolve_transient_off_food_log_item(uuid,uuid) to service_role;

-- Explicitly preserve the existing operational table and provider-control ACLs.
revoke all on table public.nutrition_provider_food_cache from public, anon, authenticated;
revoke all on table public.nutrition_provider_rate_buckets from public, anon, authenticated, service_role;
revoke all on table public.nutrition_provider_runtime_state from public, anon, authenticated;

commit;
