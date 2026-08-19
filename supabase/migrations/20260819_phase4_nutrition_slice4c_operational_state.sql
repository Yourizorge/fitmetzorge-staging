-- FitMetZorge Phase 4 Nutrition - Slice 4C Provider Operational State
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Additive backend-only cache, rate-limit and circuit state. No provider call,
-- food import, canonical-food mutation, frontend change or production change.

begin;

create table if not exists public.nutrition_provider_query_cache (
  provider_code text not null,
  query_hmac text not null,
  locale text not null,
  country_code text not null,
  page_number smallint not null,
  page_size smallint not null,
  data_type_filter text[] not null,
  filter_key text not null,
  filter_identity jsonb not null default '{}'::jsonb,
  mapping_version text not null,
  result_payload jsonb not null,
  payload_checksum text not null,
  result_count smallint not null,
  cache_status text not null,
  source_version text,
  fetched_at timestamptz not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint nutrition_provider_query_cache_pkey primary key (
    provider_code,
    query_hmac,
    locale,
    country_code,
    page_number,
    page_size,
    filter_key,
    mapping_version
  ),
  constraint nutrition_provider_query_cache_provider_check
    check (provider_code = 'usda_fdc'),
  constraint nutrition_provider_query_cache_query_hmac_check
    check (query_hmac ~ '^[0-9a-f]{64}$'),
  constraint nutrition_provider_query_cache_locale_check
    check (locale in ('nl', 'en', 'de')),
  constraint nutrition_provider_query_cache_country_check
    check (country_code ~ '^[A-Z]{2}$'),
  constraint nutrition_provider_query_cache_page_check
    check (page_number between 1 and 3 and page_size between 1 and 10),
  constraint nutrition_provider_query_cache_data_types_check
    check (data_type_filter = array['Foundation', 'Survey (FNDDS)', 'SR Legacy']::text[]),
  constraint nutrition_provider_query_cache_filter_key_check
    check (filter_key ~ '^[0-9a-f]{64}$'),
  constraint nutrition_provider_query_cache_filter_identity_check
    check (
      jsonb_typeof(filter_identity) = 'object'
      and octet_length(filter_identity::text) <= 4096
      and not (filter_identity ?| array['query', 'raw_query', 'user_id', 'auth_uid'])
    ),
  constraint nutrition_provider_query_cache_mapping_version_check
    check (
      char_length(mapping_version) between 1 and 80
      and mapping_version ~ '^[a-z0-9][a-z0-9._:-]*$'
    ),
  constraint nutrition_provider_query_cache_payload_check
    check (
      jsonb_typeof(result_payload) = 'array'
      and octet_length(result_payload::text) <= 131072
    ),
  constraint nutrition_provider_query_cache_checksum_check
    check (payload_checksum ~ '^[0-9a-f]{64}$'),
  constraint nutrition_provider_query_cache_result_count_check
    check (
      result_count between 0 and 10
      and result_count = jsonb_array_length(result_payload)
    ),
  constraint nutrition_provider_query_cache_status_check
    check (cache_status in ('positive', 'empty', 'quarantined')),
  constraint nutrition_provider_query_cache_status_payload_check
    check (
      (cache_status = 'positive' and result_count > 0)
      or (cache_status = 'empty' and result_count = 0)
      or cache_status = 'quarantined'
    ),
  constraint nutrition_provider_query_cache_source_version_check
    check (source_version is null or char_length(btrim(source_version)) between 1 and 120),
  constraint nutrition_provider_query_cache_expiry_check
    check (
      expires_at > fetched_at
      and expires_at <= fetched_at + interval '7 days'
    )
);

create table if not exists public.nutrition_provider_food_cache (
  provider_code text not null,
  provider_food_id text not null,
  provider_data_type text not null,
  mapping_version text not null,
  candidate_id uuid not null,
  normalized_payload jsonb not null,
  payload_checksum text not null,
  quality_state text not null default 'candidate',
  rejection_code text,
  source_version text,
  source_updated_at timestamptz,
  provenance jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  fetched_at timestamptz not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint nutrition_provider_food_cache_pkey primary key (
    provider_code,
    provider_food_id,
    mapping_version
  ),
  constraint nutrition_provider_food_cache_provider_check
    check (provider_code = 'usda_fdc'),
  constraint nutrition_provider_food_cache_provider_food_id_check
    check (char_length(btrim(provider_food_id)) between 1 and 160),
  constraint nutrition_provider_food_cache_data_type_check
    check (provider_data_type in ('Foundation', 'Survey (FNDDS)', 'SR Legacy')),
  constraint nutrition_provider_food_cache_mapping_version_check
    check (
      char_length(mapping_version) between 1 and 80
      and mapping_version ~ '^[a-z0-9][a-z0-9._:-]*$'
    ),
  constraint nutrition_provider_food_cache_payload_check
    check (
      jsonb_typeof(normalized_payload) = 'object'
      and octet_length(normalized_payload::text) <= 131072
    ),
  constraint nutrition_provider_food_cache_checksum_check
    check (payload_checksum ~ '^[0-9a-f]{64}$'),
  constraint nutrition_provider_food_cache_quality_check
    check (quality_state in ('candidate', 'validated', 'quarantined', 'rejected')),
  constraint nutrition_provider_food_cache_rejection_check
    check (
      (
        quality_state in ('candidate', 'validated')
        and rejection_code is null
      )
      or (
        quality_state in ('quarantined', 'rejected')
        and rejection_code is not null
        and char_length(rejection_code) between 1 and 80
        and rejection_code ~ '^[a-z0-9][a-z0-9._:-]*$'
      )
    ),
  constraint nutrition_provider_food_cache_source_version_check
    check (source_version is null or char_length(btrim(source_version)) between 1 and 120),
  constraint nutrition_provider_food_cache_json_objects_check
    check (
      jsonb_typeof(provenance) = 'object'
      and jsonb_typeof(metadata) = 'object'
      and octet_length(provenance::text) <= 32768
      and octet_length(metadata::text) <= 8192
    ),
  constraint nutrition_provider_food_cache_expiry_check
    check (
      expires_at > fetched_at
      and expires_at <= fetched_at + interval '180 days'
    )
);

create table if not exists public.nutrition_provider_rate_buckets (
  provider_code text not null,
  bucket_scope text not null,
  subject_hmac text not null,
  window_start timestamptz not null,
  window_end timestamptz not null,
  window_seconds integer not null,
  limit_value integer not null,
  request_count integer not null default 0,
  consumed_request_ids uuid[] not null default '{}'::uuid[],
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint nutrition_provider_rate_buckets_pkey primary key (
    provider_code,
    bucket_scope,
    subject_hmac,
    window_start
  ),
  constraint nutrition_provider_rate_buckets_provider_check
    check (provider_code = 'usda_fdc'),
  constraint nutrition_provider_rate_buckets_scope_check
    check (bucket_scope in ('user_30_seconds', 'user_10_minutes', 'user_day', 'provider_hour')),
  constraint nutrition_provider_rate_buckets_contract_check
    check (
      (
        bucket_scope = 'user_30_seconds'
        and subject_hmac ~ '^[0-9a-f]{64}$'
        and window_seconds = 30
        and limit_value = 3
      )
      or (
        bucket_scope = 'user_10_minutes'
        and subject_hmac ~ '^[0-9a-f]{64}$'
        and window_seconds = 600
        and limit_value = 12
      )
      or (
        bucket_scope = 'user_day'
        and subject_hmac ~ '^[0-9a-f]{64}$'
        and window_seconds = 86400
        and limit_value = 100
      )
      or (
        bucket_scope = 'provider_hour'
        and subject_hmac = 'global'
        and window_seconds = 3600
        and limit_value = 800
      )
    ),
  constraint nutrition_provider_rate_buckets_window_check
    check (
      window_end = window_start + make_interval(secs => window_seconds)
      and window_start = to_timestamp(
        (floor(extract(epoch from window_start) / window_seconds) * window_seconds)::double precision
      )
    ),
  constraint nutrition_provider_rate_buckets_count_check
    check (
      request_count between 0 and limit_value
      and request_count = cardinality(consumed_request_ids)
      and cardinality(consumed_request_ids) <= 1000
    )
);

create table if not exists public.nutrition_provider_runtime_state (
  provider_code text primary key,
  circuit_state text not null default 'closed',
  consecutive_failures integer not null default 0,
  opened_at timestamptz,
  next_probe_at timestamptz,
  last_success_at timestamptz,
  last_failure_at timestamptz,
  last_error_class text,
  upstream_rate_limit integer,
  upstream_rate_remaining integer,
  upstream_rate_reset_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint nutrition_provider_runtime_state_provider_check
    check (provider_code = 'usda_fdc'),
  constraint nutrition_provider_runtime_state_circuit_check
    check (circuit_state in ('closed', 'open', 'half_open')),
  constraint nutrition_provider_runtime_state_failure_count_check
    check (consecutive_failures between 0 and 1000000),
  constraint nutrition_provider_runtime_state_transition_shape_check
    check (
      (
        circuit_state = 'closed'
        and opened_at is null
        and next_probe_at is null
      )
      or (
        circuit_state = 'open'
        and opened_at is not null
        and next_probe_at is not null
        and next_probe_at >= opened_at
      )
      or (
        circuit_state = 'half_open'
        and opened_at is not null
        and next_probe_at is null
      )
    ),
  constraint nutrition_provider_runtime_state_error_class_check
    check (
      last_error_class is null
      or (
        char_length(last_error_class) between 1 and 80
        and last_error_class ~ '^[a-z0-9][a-z0-9._:-]*$'
      )
    ),
  constraint nutrition_provider_runtime_state_upstream_rate_check
    check (
      (
        upstream_rate_limit is null
        and upstream_rate_remaining is null
      )
      or (
        upstream_rate_limit between 0 and 1000000
        and upstream_rate_remaining between 0 and upstream_rate_limit
      )
    ),
  constraint nutrition_provider_runtime_state_metadata_check
    check (
      jsonb_typeof(metadata) = 'object'
      and octet_length(metadata::text) <= 4096
    )
);

create unique index if not exists nutrition_provider_food_cache_candidate_mapping_uidx
  on public.nutrition_provider_food_cache(candidate_id, mapping_version);

create index if not exists nutrition_provider_query_cache_expires_idx
  on public.nutrition_provider_query_cache(expires_at);

create index if not exists nutrition_provider_query_cache_status_expires_idx
  on public.nutrition_provider_query_cache(provider_code, cache_status, expires_at);

create index if not exists nutrition_provider_food_cache_expires_idx
  on public.nutrition_provider_food_cache(expires_at);

create index if not exists nutrition_provider_food_cache_quality_expires_idx
  on public.nutrition_provider_food_cache(provider_code, quality_state, expires_at, provider_food_id);

create index if not exists nutrition_provider_rate_buckets_window_end_idx
  on public.nutrition_provider_rate_buckets(window_end);

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
  if v_provider_code is null or v_provider_code <> 'usda_fdc' then
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
    pg_catalog.hashtextextended(
      'fmz_phase4_provider_rate:' || v_provider_code || ':user:' || p_user_subject_hmac,
      0
    )
  );

  for v_index in 1..4 loop
    v_subject := case when v_scopes[v_index] = 'provider_hour' then 'global' else p_user_subject_hmac end;
    v_window_start := pg_catalog.to_timestamp(
      (
        pg_catalog.floor(extract(epoch from v_now) / v_window_seconds[v_index])
        * v_window_seconds[v_index]
      )::double precision
    );
    v_window_starts := pg_catalog.array_append(v_window_starts, v_window_start);

    insert into public.nutrition_provider_rate_buckets (
      provider_code,
      bucket_scope,
      subject_hmac,
      window_start,
      window_end,
      window_seconds,
      limit_value
    ) values (
      v_provider_code,
      v_scopes[v_index],
      v_subject,
      v_window_start,
      v_window_start + pg_catalog.make_interval(secs => v_window_seconds[v_index]),
      v_window_seconds[v_index],
      v_limits[v_index]
    )
    on conflict (provider_code, bucket_scope, subject_hmac, window_start) do nothing;
  end loop;

  select
    count(*)::integer,
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

  if v_row_count <> 4 then
    raise exception 'provider rate bucket integrity failure';
  end if;

  if v_replay_count not in (0, 4) then
    raise exception 'provider rate replay integrity failure';
  end if;

  if v_replay_count = 4 then
    select pg_catalog.jsonb_agg(
      pg_catalog.jsonb_build_object(
        'scope', b.bucket_scope,
        'limit', b.limit_value,
        'remaining', greatest(b.limit_value - b.request_count, 0),
        'reset_at', b.window_end
      ) order by b.window_seconds, b.bucket_scope
    )
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
      'allowed', true,
      'replayed', true,
      'provider', v_provider_code,
      'checked_at', v_now,
      'buckets', coalesce(v_bucket_payload, '[]'::jsonb)
    );
  end if;

  select
    max(b.window_end),
    pg_catalog.jsonb_agg(
      pg_catalog.jsonb_build_object(
        'scope', b.bucket_scope,
        'limit', b.limit_value,
        'remaining', 0,
        'reset_at', b.window_end
      ) order by b.window_end
    )
  into v_failed_until, v_failed_buckets
  from public.nutrition_provider_rate_buckets b
  where b.provider_code = v_provider_code
    and b.request_count >= b.limit_value
    and (
      (b.bucket_scope = v_scopes[1] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[1])
      or (b.bucket_scope = v_scopes[2] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[2])
      or (b.bucket_scope = v_scopes[3] and b.subject_hmac = p_user_subject_hmac and b.window_start = v_window_starts[3])
      or (b.bucket_scope = v_scopes[4] and b.subject_hmac = 'global' and b.window_start = v_window_starts[4])
    );

  if v_failed_until is not null then
    return pg_catalog.jsonb_build_object(
      'allowed', false,
      'replayed', false,
      'provider', v_provider_code,
      'checked_at', v_now,
      'retry_at', v_failed_until,
      'retry_after_seconds', greatest(
        0,
        pg_catalog.ceil(extract(epoch from (v_failed_until - v_now)))::integer
      ),
      'buckets', coalesce(v_failed_buckets, '[]'::jsonb)
    );
  end if;

  for v_index in 1..4 loop
    v_subject := case when v_scopes[v_index] = 'provider_hour' then 'global' else p_user_subject_hmac end;

    update public.nutrition_provider_rate_buckets
    set
      request_count = request_count + 1,
      consumed_request_ids = pg_catalog.array_append(consumed_request_ids, p_request_id)
    where provider_code = v_provider_code
      and bucket_scope = v_scopes[v_index]
      and subject_hmac = v_subject
      and window_start = v_window_starts[v_index];

    if not found then
      raise exception 'provider rate bucket update failure';
    end if;
  end loop;

  select pg_catalog.jsonb_agg(
    pg_catalog.jsonb_build_object(
      'scope', b.bucket_scope,
      'limit', b.limit_value,
      'remaining', greatest(b.limit_value - b.request_count, 0),
      'reset_at', b.window_end
    ) order by b.window_seconds, b.bucket_scope
  )
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
    'allowed', true,
    'replayed', false,
    'provider', v_provider_code,
    'checked_at', v_now,
    'buckets', coalesce(v_bucket_payload, '[]'::jsonb)
  );
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
  if v_provider_code is null or v_provider_code <> 'usda_fdc' then
    raise exception 'unsupported nutrition provider';
  end if;

  if v_event is null or v_event not in ('success', 'failure', 'rate_limited', 'begin_probe') then
    raise exception 'unsupported provider runtime event';
  end if;

  if p_retry_after_seconds is not null and p_retry_after_seconds not between 1 and 3600 then
    raise exception 'invalid provider retry interval';
  end if;

  if p_error_class is not null and (
    char_length(p_error_class) not between 1 and 80
    or p_error_class !~ '^[a-z0-9][a-z0-9._:-]*$'
  ) then
    raise exception 'invalid provider error class';
  end if;

  if v_event in ('failure', 'rate_limited') and p_error_class is null then
    raise exception 'provider error class is required';
  end if;

  if (p_upstream_limit is null) <> (p_upstream_remaining is null) then
    raise exception 'upstream limit and remaining must be supplied together';
  end if;

  if p_upstream_limit is not null and (
    p_upstream_limit not between 0 and 1000000
    or p_upstream_remaining not between 0 and p_upstream_limit
  ) then
    raise exception 'invalid upstream rate metadata';
  end if;

  if p_metadata is null
    or jsonb_typeof(p_metadata) <> 'object'
    or octet_length(p_metadata::text) > 4096
  then
    raise exception 'invalid provider runtime metadata';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('fmz_phase4_provider_runtime:' || v_provider_code, 0)
  );

  insert into public.nutrition_provider_runtime_state(provider_code)
  values (v_provider_code)
  on conflict (provider_code) do nothing;

  select *
  into v_state
  from public.nutrition_provider_runtime_state
  where provider_code = v_provider_code
  for update;

  if not found then
    raise exception 'provider runtime state integrity failure';
  end if;

  if v_event = 'begin_probe' then
    if v_state.circuit_state = 'closed' then
      v_probe_allowed := true;
    elsif v_state.circuit_state = 'open' and v_state.next_probe_at <= v_now then
      update public.nutrition_provider_runtime_state
      set
        circuit_state = 'half_open',
        next_probe_at = null,
        metadata = p_metadata
      where provider_code = v_provider_code
      returning * into v_state;
      v_probe_allowed := true;
    end if;

    return pg_catalog.jsonb_build_object(
      'provider', v_provider_code,
      'event', v_event,
      'probe_allowed', v_probe_allowed,
      'state', pg_catalog.to_jsonb(v_state)
    );
  end if;

  if v_event = 'success' then
    update public.nutrition_provider_runtime_state
    set
      circuit_state = 'closed',
      consecutive_failures = 0,
      opened_at = null,
      next_probe_at = null,
      last_success_at = v_now,
      last_error_class = null,
      upstream_rate_limit = coalesce(p_upstream_limit, upstream_rate_limit),
      upstream_rate_remaining = coalesce(p_upstream_remaining, upstream_rate_remaining),
      upstream_rate_reset_at = coalesce(p_upstream_reset_at, upstream_rate_reset_at),
      metadata = p_metadata
    where provider_code = v_provider_code
    returning * into v_state;
  elsif v_event = 'rate_limited' then
    v_failure_count := v_state.consecutive_failures + 1;
    v_backoff_seconds := coalesce(p_retry_after_seconds, 3600);

    update public.nutrition_provider_runtime_state
    set
      circuit_state = 'open',
      consecutive_failures = v_failure_count,
      opened_at = coalesce(opened_at, v_now),
      next_probe_at = v_now + pg_catalog.make_interval(secs => v_backoff_seconds),
      last_failure_at = v_now,
      last_error_class = p_error_class,
      upstream_rate_limit = coalesce(p_upstream_limit, upstream_rate_limit),
      upstream_rate_remaining = coalesce(p_upstream_remaining, upstream_rate_remaining),
      upstream_rate_reset_at = coalesce(p_upstream_reset_at, upstream_rate_reset_at),
      metadata = p_metadata
    where provider_code = v_provider_code
    returning * into v_state;
  else
    v_failure_count := v_state.consecutive_failures + 1;
    v_backoff_seconds := coalesce(
      p_retry_after_seconds,
      case
        when v_failure_count <= 5 then 60
        when v_failure_count = 6 then 120
        when v_failure_count = 7 then 300
        when v_failure_count = 8 then 900
        else 3600
      end
    );

    if v_state.circuit_state = 'half_open' or v_failure_count >= 5 then
      update public.nutrition_provider_runtime_state
      set
        circuit_state = 'open',
        consecutive_failures = v_failure_count,
        opened_at = coalesce(opened_at, v_now),
        next_probe_at = v_now + pg_catalog.make_interval(secs => v_backoff_seconds),
        last_failure_at = v_now,
        last_error_class = p_error_class,
        upstream_rate_limit = coalesce(p_upstream_limit, upstream_rate_limit),
        upstream_rate_remaining = coalesce(p_upstream_remaining, upstream_rate_remaining),
        upstream_rate_reset_at = coalesce(p_upstream_reset_at, upstream_rate_reset_at),
        metadata = p_metadata
      where provider_code = v_provider_code
      returning * into v_state;
    else
      update public.nutrition_provider_runtime_state
      set
        consecutive_failures = v_failure_count,
        last_failure_at = v_now,
        last_error_class = p_error_class,
        upstream_rate_limit = coalesce(p_upstream_limit, upstream_rate_limit),
        upstream_rate_remaining = coalesce(p_upstream_remaining, upstream_rate_remaining),
        upstream_rate_reset_at = coalesce(p_upstream_reset_at, upstream_rate_reset_at),
        metadata = p_metadata
      where provider_code = v_provider_code
      returning * into v_state;
    end if;
  end if;

  return pg_catalog.jsonb_build_object(
    'provider', v_provider_code,
    'event', v_event,
    'probe_allowed', false,
    'state', pg_catalog.to_jsonb(v_state)
  );
end;
$$;

create trigger nutrition_provider_query_cache_90_touch_updated_at
before update on public.nutrition_provider_query_cache
for each row execute function public.fmz_phase4_touch_updated_at();

create trigger nutrition_provider_food_cache_90_touch_updated_at
before update on public.nutrition_provider_food_cache
for each row execute function public.fmz_phase4_touch_updated_at();

create trigger nutrition_provider_rate_buckets_90_touch_updated_at
before update on public.nutrition_provider_rate_buckets
for each row execute function public.fmz_phase4_touch_updated_at();

create trigger nutrition_provider_runtime_state_90_touch_updated_at
before update on public.nutrition_provider_runtime_state
for each row execute function public.fmz_phase4_touch_updated_at();

alter table public.nutrition_provider_query_cache enable row level security;
alter table public.nutrition_provider_food_cache enable row level security;
alter table public.nutrition_provider_rate_buckets enable row level security;
alter table public.nutrition_provider_runtime_state enable row level security;

revoke all on table public.nutrition_provider_query_cache from public;
revoke all on table public.nutrition_provider_query_cache from anon;
revoke all on table public.nutrition_provider_query_cache from authenticated;
revoke all on table public.nutrition_provider_query_cache from service_role;
grant select, insert, update on table public.nutrition_provider_query_cache to service_role;

revoke all on table public.nutrition_provider_food_cache from public;
revoke all on table public.nutrition_provider_food_cache from anon;
revoke all on table public.nutrition_provider_food_cache from authenticated;
revoke all on table public.nutrition_provider_food_cache from service_role;
grant select, insert, update on table public.nutrition_provider_food_cache to service_role;

revoke all on table public.nutrition_provider_rate_buckets from public;
revoke all on table public.nutrition_provider_rate_buckets from anon;
revoke all on table public.nutrition_provider_rate_buckets from authenticated;
revoke all on table public.nutrition_provider_rate_buckets from service_role;

revoke all on table public.nutrition_provider_runtime_state from public;
revoke all on table public.nutrition_provider_runtime_state from anon;
revoke all on table public.nutrition_provider_runtime_state from authenticated;
revoke all on table public.nutrition_provider_runtime_state from service_role;
grant select on table public.nutrition_provider_runtime_state to service_role;

revoke all on function public.fmz_phase4_provider_consume_rate_limits(text, text, uuid) from public;
revoke all on function public.fmz_phase4_provider_consume_rate_limits(text, text, uuid) from anon;
revoke all on function public.fmz_phase4_provider_consume_rate_limits(text, text, uuid) from authenticated;
revoke all on function public.fmz_phase4_provider_consume_rate_limits(text, text, uuid) from service_role;
grant execute on function public.fmz_phase4_provider_consume_rate_limits(text, text, uuid) to service_role;

revoke all on function public.fmz_phase4_provider_transition_runtime_state(
  text, text, integer, text, integer, integer, timestamptz, jsonb
) from public;
revoke all on function public.fmz_phase4_provider_transition_runtime_state(
  text, text, integer, text, integer, integer, timestamptz, jsonb
) from anon;
revoke all on function public.fmz_phase4_provider_transition_runtime_state(
  text, text, integer, text, integer, integer, timestamptz, jsonb
) from authenticated;
revoke all on function public.fmz_phase4_provider_transition_runtime_state(
  text, text, integer, text, integer, integer, timestamptz, jsonb
) from service_role;
grant execute on function public.fmz_phase4_provider_transition_runtime_state(
  text, text, integer, text, integer, integer, timestamptz, jsonb
) to service_role;

commit;
