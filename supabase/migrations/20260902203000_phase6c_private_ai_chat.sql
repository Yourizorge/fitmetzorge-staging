-- FitMetZorge Package 6C private AI chat (STAGING first)
-- Mock-only member chat on the frozen Phase 6A trust foundation. No provider call.

begin;

create extension if not exists pg_cron with schema pg_catalog;

alter table public.ai_threads
  add column if not exists client_request_id uuid,
  add column if not exists revision bigint not null default 1,
  add column if not exists last_message_sequence bigint not null default 0;

alter table public.ai_threads
  drop constraint if exists ai_threads_revision_check;
alter table public.ai_threads
  add constraint ai_threads_revision_check
    check (revision >= 1 and last_message_sequence >= 0);

create unique index if not exists ai_threads_user_client_request_idx
  on public.ai_threads(user_id, client_request_id)
  where client_request_id is not null;

alter table public.ai_messages
  add column if not exists sequence_number bigint;

with ordered as (
  select id, row_number() over (partition by thread_id order by created_at, id)::bigint as sequence_number
  from public.ai_messages
  where sequence_number is null
)
update public.ai_messages m
set sequence_number = o.sequence_number
from ordered o
where o.id = m.id;

update public.ai_threads t
set last_message_sequence = coalesce((
  select max(m.sequence_number) from public.ai_messages m where m.thread_id = t.id
), 0),
revision = greatest(t.revision, coalesce((
  select max(m.sequence_number) from public.ai_messages m where m.thread_id = t.id
), 0) + 1);

alter table public.ai_messages alter column sequence_number set not null;
alter table public.ai_messages
  drop constraint if exists ai_messages_sequence_positive_check;
alter table public.ai_messages
  add constraint ai_messages_sequence_positive_check check (sequence_number >= 1);
create unique index if not exists ai_messages_thread_sequence_idx
  on public.ai_messages(thread_id, sequence_number);
create unique index if not exists ai_messages_id_user_idx
  on public.ai_messages(id, user_id);

alter table ai_private.runs
  add column if not exists source_message_id uuid;
alter table ai_private.runs
  drop constraint if exists ai_runs_source_message_owner_fk;
alter table ai_private.runs
  add constraint ai_runs_source_message_owner_fk
  foreign key (source_message_id, user_id)
  references public.ai_messages(id, user_id) on delete restrict;
create index if not exists ai_runs_source_message_idx
  on ai_private.runs(source_message_id, started_at desc)
  where source_message_id is not null;

alter table public.ai_data_lifecycle_requests
  add column if not exists scope_thread_id uuid;
create index if not exists ai_data_lifecycle_scope_idx
  on public.ai_data_lifecycle_requests(user_id, scope_thread_id, requested_at desc)
  where scope_thread_id is not null;

create table if not exists ai_private.phase6c_runtime_config (
  singleton boolean primary key default true,
  mock_chat_enabled boolean not null default true,
  external_provider_enabled boolean not null default false,
  max_active_threads integer not null default 20,
  max_messages_per_thread integer not null default 500,
  message_max_characters integer not null default 4000,
  updated_at timestamptz not null default now(),
  constraint phase6c_runtime_singleton_check check (singleton is true),
  constraint phase6c_runtime_provider_off_check check (external_provider_enabled is false),
  constraint phase6c_runtime_bounds_check check (
    max_active_threads between 1 and 50
    and max_messages_per_thread between 10 and 1000
    and message_max_characters between 100 and 4000
  )
);

alter table ai_private.phase6c_runtime_config enable row level security;
revoke all on table ai_private.phase6c_runtime_config from public, anon, authenticated;
insert into ai_private.phase6c_runtime_config(singleton, mock_chat_enabled, external_provider_enabled)
values (true, true, false)
on conflict (singleton) do update
set mock_chat_enabled = true, external_provider_enabled = false, updated_at = now();

create or replace function ai_private.phase6c_age_eligible(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
  select coalesce((
    select o.age >= 18
    from public.user_onboarding o
    where o.user_id = p_user_id
  ), false);
$$;

create or replace function ai_private.phase6c_apply_retention(p_user_id uuid, p_at timestamptz default now())
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_loss_at timestamptz;
  v_started integer := 0;
  v_restored integer := 0;
  v_deleted integer := 0;
begin
  perform ai_private.assert_member(p_user_id);
  if p_at is null then
    raise exception 'ai_retention_input_invalid' using errcode = '22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_retention:' || p_user_id::text, 0));

  update public.ai_messages m
  set content_text = null, structured_output = null, schema_version = null, status = 'deleted'
  from public.ai_threads t
  where t.id = m.thread_id and t.user_id = p_user_id
    and t.feature_code = 'private_chat' and t.retention_state = 'grace'
    and t.retention_due_at <= p_at and m.status = 'active';

  update public.ai_threads
  set retention_state = 'deleted', status = 'content_deleted',
      content_deleted_at = p_at, archived_at = coalesce(archived_at, p_at), updated_at = p_at
  where user_id = p_user_id and feature_code = 'private_chat'
    and retention_state = 'grace' and retention_due_at <= p_at;
  get diagnostics v_deleted = row_count;

  if exists(select 1 from ai_private.current_entitlement(p_user_id, p_at)) then
    update public.ai_threads
    set retention_state = 'active', retention_started_at = null,
        retention_due_at = null, updated_at = p_at
    where user_id = p_user_id and feature_code = 'private_chat'
      and retention_state = 'grace';
    get diagnostics v_restored = row_count;
  else
    select greatest(
      coalesce(max(case
        when e.status = 'active' and e.ends_at is not null and e.ends_at <= p_at then e.ends_at
        when e.status <> 'active' and e.starts_at <= p_at then least(e.updated_at, p_at)
        else null
      end), p_at),
      min(t.created_at)
    )
    into v_loss_at
    from public.ai_threads t
    left join public.entitlements e
      on e.user_id = t.user_id and e.entitlement_code in ('ai', 'personal_coaching')
    where t.user_id = p_user_id and t.feature_code = 'private_chat'
      and t.retention_state = 'active';
    update public.ai_threads
    set retention_state = 'grace', retention_started_at = coalesce(v_loss_at, p_at),
        retention_due_at = coalesce(v_loss_at, p_at) + interval '90 days', updated_at = p_at
    where user_id = p_user_id and feature_code = 'private_chat'
      and retention_state = 'active';
    get diagnostics v_started = row_count;
  end if;

  return jsonb_build_object(
    'grace_started', v_started,
    'restored', v_restored,
    'threads_content_deleted', v_deleted,
    'retention_days', 90
  );
end;
$$;

create or replace function ai_private.phase6c_retention_sweep(p_at timestamptz default now())
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user record;
  v_result jsonb;
  v_started integer := 0;
  v_restored integer := 0;
  v_deleted integer := 0;
begin
  if p_at is null then raise exception 'ai_retention_input_invalid' using errcode='22023'; end if;
  for v_user in select distinct user_id from public.ai_threads where feature_code='private_chat' and retention_state in ('active','grace') loop
    v_result := ai_private.phase6c_apply_retention(v_user.user_id, p_at);
    v_started := v_started + (v_result->>'grace_started')::integer;
    v_restored := v_restored + (v_result->>'restored')::integer;
    v_deleted := v_deleted + (v_result->>'threads_content_deleted')::integer;
  end loop;
  return jsonb_build_object('grace_started',v_started,'restored',v_restored,'threads_content_deleted',v_deleted,'retention_days',90);
end;
$$;

create or replace function ai_private.phase6c_reconcile_member(p_user_id uuid, p_at timestamptz default now())
returns void
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
begin
  perform ai_private.assert_member(p_user_id);
  perform ai_private.phase6c_apply_retention(p_user_id, p_at);
end;
$$;

create or replace function ai_private.phase6c_chat_status(p_user_id uuid, p_at timestamptz default now())
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_entitlement record;
  v_consent record;
  v_age boolean;
  v_safety text;
  v_config ai_private.phase6c_runtime_config%rowtype;
  v_allowed boolean;
  v_reason text;
begin
  perform ai_private.assert_member(p_user_id);
  select * into v_entitlement from ai_private.current_entitlement(p_user_id, p_at);
  select * into v_consent from ai_private.current_consent(p_user_id, 'ai_processing');
  v_age := ai_private.phase6c_age_eligible(p_user_id);
  select coalesce(s.safety_status, 'clear') into v_safety
  from public.ai_member_safety_state s where s.user_id = p_user_id;
  v_safety := coalesce(v_safety, 'clear');
  select * into v_config from ai_private.phase6c_runtime_config where singleton;
  v_allowed := v_entitlement.entitlement_code is not null
    and v_consent.consent_state = 'granted'
    and coalesce(v_consent.document_active, false)
    and v_age
    and v_safety not in ('hard_stop', 'review_required')
    and coalesce(v_config.mock_chat_enabled, false)
    and not coalesce(v_config.external_provider_enabled, true);
  v_reason := case
    when v_entitlement.entitlement_code is null then 'ai_entitlement_required'
    when v_consent.consent_state is distinct from 'granted' or not coalesce(v_consent.document_active, false) then 'ai_consent_required'
    when not v_age then 'ai_age_required'
    when v_safety in ('hard_stop', 'review_required') then 'safety_hard_stop'
    when not coalesce(v_config.mock_chat_enabled, false) then 'mock_disabled'
    when coalesce(v_config.external_provider_enabled, true) then 'external_provider_forbidden'
    else 'allowed'
  end;
  return jsonb_build_object(
    'chat_write_allowed', v_allowed,
    'deny_reason', v_reason,
    'entitlement_code', v_entitlement.entitlement_code,
    'consent_state', coalesce(v_consent.consent_state, 'missing'),
    'consent_document_version', v_consent.document_version,
    'age_eligible', v_age,
    'safety_status', v_safety,
    'mock_mode', coalesce(v_config.mock_chat_enabled, false),
    'external_ai_enabled', false,
    'external_ai_calls', 0,
    'external_ai_cost_eur', 0
  );
end;
$$;

create or replace function ai_private.phase6c_assign_message_sequence()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_next bigint;
begin
  select t.last_message_sequence + 1 into v_next
  from public.ai_threads t
  where t.id = new.thread_id and t.user_id = new.user_id
  for update;
  if v_next is null then
    raise exception 'ai_thread_forbidden' using errcode = '42501';
  end if;
  new.sequence_number := v_next;
  update public.ai_threads
  set last_message_sequence = v_next, revision = revision + 1, updated_at = now()
  where id = new.thread_id and user_id = new.user_id;
  return new;
end;
$$;

create or replace function ai_private.phase6c_protect_message_content()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
begin
  if new is not distinct from old then return new; end if;
  if old.status = 'active'
     and new.status = 'deleted'
     and new.content_text is null
     and new.structured_output is null
     and new.schema_version is null
     and (to_jsonb(new) - array['content_text','structured_output','schema_version','status']::text[])
       = (to_jsonb(old) - array['content_text','structured_output','schema_version','status']::text[]) then
    return new;
  end if;
  raise exception 'ai_message_immutable' using errcode = '42501';
end;
$$;

drop trigger if exists ai_messages_assign_sequence on public.ai_messages;
create trigger ai_messages_assign_sequence
before insert on public.ai_messages
for each row execute function ai_private.phase6c_assign_message_sequence();

drop trigger if exists ai_messages_protect_content on public.ai_messages;
create trigger ai_messages_protect_content
before update on public.ai_messages
for each row execute function ai_private.phase6c_protect_message_content();

create or replace function public.fmz_phase6c_get_chat_status()
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_status jsonb;
begin
  perform ai_private.phase6c_reconcile_member(v_user_id, now());
  v_status := ai_private.phase6c_chat_status(v_user_id, now());
  return v_status || jsonb_build_object(
    'grace_deadline', (select min(t.retention_due_at) from public.ai_threads t where t.user_id = v_user_id and t.feature_code = 'private_chat' and t.retention_state = 'grace'),
    'conversation_count', (select count(*) from public.ai_threads t where t.user_id = v_user_id and t.feature_code = 'private_chat' and t.retention_state <> 'deleted')
  );
end;
$$;

create or replace function public.fmz_phase6c_create_thread(
  p_thread_id uuid,
  p_locale text,
  p_request_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_gate jsonb;
  v_existing public.ai_threads%rowtype;
  v_config ai_private.phase6c_runtime_config%rowtype;
begin
  perform ai_private.phase6c_reconcile_member(v_user_id, now());
  if p_thread_id is null or p_request_id is null or p_locale not in ('nl','en','de') then
    raise exception 'ai_thread_input_invalid' using errcode = '22023';
  end if;
  v_gate := ai_private.phase6c_chat_status(v_user_id, now());
  if not (v_gate ->> 'chat_write_allowed')::boolean then
    raise exception '%', v_gate ->> 'deny_reason' using errcode = '42501';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6c_thread:' || v_user_id::text, 0));
  select * into v_existing from public.ai_threads t
  where t.user_id = v_user_id and t.id = p_thread_id and t.client_request_id = p_request_id;
  if v_existing.id is not null then
    if v_existing.id <> p_thread_id or v_existing.locale <> p_locale or v_existing.feature_code <> 'private_chat' then
      raise exception 'ai_thread_request_conflict' using errcode = '23505';
    end if;
    return jsonb_build_object('replay', true, 'thread_id', v_existing.id, 'revision', v_existing.revision);
  end if;
  if exists(select 1 from public.ai_threads t where t.user_id=v_user_id and (t.id=p_thread_id or t.client_request_id=p_request_id)) then
    raise exception 'ai_thread_request_conflict' using errcode = '23505';
  end if;
  select * into v_config from ai_private.phase6c_runtime_config where singleton;
  if (select count(*) from public.ai_threads t where t.user_id = v_user_id and t.feature_code = 'private_chat' and t.status = 'active') >= v_config.max_active_threads then
    raise exception 'ai_thread_limit_reached' using errcode = '54000';
  end if;
  insert into public.ai_threads(id, user_id, feature_code, locale, client_request_id)
  values (p_thread_id, v_user_id, 'private_chat', p_locale, p_request_id)
  returning * into v_existing;
  return jsonb_build_object('replay', false, 'thread_id', v_existing.id, 'revision', v_existing.revision);
end;
$$;

create or replace function public.fmz_phase6c_list_threads(
  p_limit integer default 20,
  p_before_updated_at timestamptz default null,
  p_before_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
begin
  perform ai_private.phase6c_reconcile_member(v_user_id, now());
  if p_limit not between 1 and 25 or ((p_before_updated_at is null) <> (p_before_id is null)) then
    raise exception 'ai_thread_page_invalid' using errcode = '22023';
  end if;
  return jsonb_build_object('threads', coalesce((
    select jsonb_agg(to_jsonb(x) order by x.updated_at desc, x.id desc)
    from (
      select t.id, t.locale, t.status, t.retention_state, t.retention_due_at,
        t.revision, t.last_message_sequence, t.created_at, t.updated_at,
        (select left(m.content_text,160) from public.ai_messages m where m.thread_id=t.id and m.status='active' order by m.sequence_number desc limit 1) as last_message,
        (select r.status from ai_private.runs r where r.thread_id=t.id order by r.started_at desc, r.id desc limit 1) as processing_status
      from public.ai_threads t
      where t.user_id = v_user_id and t.feature_code = 'private_chat'
        and t.retention_state <> 'deleted'
        and (p_before_updated_at is null or (t.updated_at, t.id) < (p_before_updated_at, p_before_id))
      order by t.updated_at desc, t.id desc
      limit p_limit
    ) x
  ), '[]'::jsonb));
end;
$$;

create or replace function public.fmz_phase6c_read_thread(
  p_thread_id uuid,
  p_limit integer default 50,
  p_before_sequence bigint default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_thread public.ai_threads%rowtype;
begin
  perform ai_private.phase6c_reconcile_member(v_user_id, now());
  if p_thread_id is null or p_limit not between 1 and 100 or (p_before_sequence is not null and p_before_sequence < 1) then
    raise exception 'ai_history_page_invalid' using errcode = '22023';
  end if;
  select * into v_thread from public.ai_threads t
  where t.id = p_thread_id and t.user_id = v_user_id and t.feature_code = 'private_chat';
  if v_thread.id is null or v_thread.retention_state = 'deleted' or v_thread.retention_due_at <= now() then
    raise exception 'ai_thread_unavailable' using errcode = '42501';
  end if;
  return jsonb_build_object(
    'thread', jsonb_build_object('id',v_thread.id,'locale',v_thread.locale,'status',v_thread.status,'retention_state',v_thread.retention_state,'retention_due_at',v_thread.retention_due_at,'revision',v_thread.revision,'last_message_sequence',v_thread.last_message_sequence,'created_at',v_thread.created_at,'updated_at',v_thread.updated_at),
    'messages', coalesce((
      select jsonb_agg(to_jsonb(x) order by x.sequence_number)
      from (
        select m.id, m.message_role, m.content_text, m.status, m.sequence_number, m.created_at,
          case when m.message_role='user' then (
            select r.status from ai_private.runs r
            where r.source_message_id=m.id order by r.started_at desc, r.id desc limit 1
          ) else 'completed' end as processing_status
        from public.ai_messages m
        where m.thread_id=p_thread_id and m.user_id=v_user_id and m.status='active'
          and (p_before_sequence is null or m.sequence_number < p_before_sequence)
        order by m.sequence_number desc
        limit p_limit
      ) x
    ), '[]'::jsonb)
  );
end;
$$;

create or replace function public.fmz_phase6c_submit_message(
  p_thread_id uuid,
  p_request_id uuid,
  p_expected_revision bigint,
  p_locale text,
  p_content text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid := auth.uid();
  v_gate jsonb;
  v_existing public.ai_messages%rowtype;
  v_thread public.ai_threads%rowtype;
  v_message public.ai_messages%rowtype;
  v_config ai_private.phase6c_runtime_config%rowtype;
  v_rate ai_private.rate_policies%rowtype;
  v_window timestamptz;
  v_count integer;
begin
  perform ai_private.phase6c_reconcile_member(v_user_id, now());
  select * into v_config from ai_private.phase6c_runtime_config where singleton;
  if p_thread_id is null or p_request_id is null or p_expected_revision is null or p_expected_revision < 1
     or p_locale not in ('nl','en','de')
     or char_length(btrim(coalesce(p_content,''))) not between 1 and v_config.message_max_characters then
    raise exception 'ai_message_input_invalid' using errcode = '22023';
  end if;
  v_gate := ai_private.phase6c_chat_status(v_user_id, now());
  if not (v_gate ->> 'chat_write_allowed')::boolean then
    raise exception '%', v_gate ->> 'deny_reason' using errcode = '42501';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6c_message:' || v_user_id::text || ':' || p_request_id::text, 0));
  select * into v_existing from public.ai_messages m
  where m.user_id=v_user_id and m.request_id=p_request_id and m.message_role='user';
  if v_existing.id is not null then
    if v_existing.thread_id<>p_thread_id or v_existing.content_text is distinct from btrim(p_content)
       or v_existing.feature_code<>'private_chat' or v_existing.status<>'active' then
      raise exception 'ai_message_request_conflict' using errcode = '23505';
    end if;
    select * into v_thread from public.ai_threads t where t.id=p_thread_id;
    return jsonb_build_object('replay',true,'message_id',v_existing.id,'thread_id',p_thread_id,'revision',v_thread.revision);
  end if;
  select * into v_thread from public.ai_threads t where t.id=p_thread_id for update;
  if v_thread.id is null or v_thread.user_id<>v_user_id or v_thread.feature_code<>'private_chat' or v_thread.status<>'active' or v_thread.retention_state<>'active' then
    raise exception 'ai_thread_forbidden' using errcode = '42501';
  end if;
  if v_thread.locale<>p_locale then raise exception 'ai_thread_locale_conflict' using errcode='23505'; end if;
  if v_thread.revision<>p_expected_revision then raise exception 'ai_thread_stale_conflict' using errcode='40001'; end if;
  if (select count(*) from public.ai_messages m where m.thread_id=p_thread_id and m.status='active') >= v_config.max_messages_per_thread then
    raise exception 'ai_message_limit_reached' using errcode='54000';
  end if;
  select * into v_rate from ai_private.rate_policies where feature_code='private_chat' and active;
  v_window := to_timestamp(floor(extract(epoch from now())/v_rate.window_seconds)*v_rate.window_seconds);
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6a_rate:'||v_user_id::text||':private_chat:'||v_window::text,0));
  insert into ai_private.rate_buckets(user_id,feature_code,window_started_at,window_seconds,request_count)
  values(v_user_id,'private_chat',v_window,v_rate.window_seconds,1)
  on conflict(user_id,feature_code,window_started_at) do update
    set request_count=ai_private.rate_buckets.request_count+1,updated_at=now()
  returning request_count into v_count;
  if v_count>v_rate.max_requests then raise exception 'ai_rate_limit_reached' using errcode='54000'; end if;
  insert into public.ai_messages(id,user_id,thread_id,message_role,feature_code,content_text,status,request_id)
  values(gen_random_uuid(),v_user_id,p_thread_id,'user','private_chat',btrim(p_content),'active',p_request_id)
  returning * into v_message;
  select * into v_thread from public.ai_threads t where t.id=p_thread_id;
  return jsonb_build_object('replay',false,'message_id',v_message.id,'thread_id',p_thread_id,'sequence_number',v_message.sequence_number,'revision',v_thread.revision);
end;
$$;

create or replace function public.fmz_phase6c_service_begin_mock_run(
  p_user_id uuid,
  p_source_message_id uuid,
  p_attempt_id uuid,
  p_payload_hash text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_message public.ai_messages%rowtype;
  v_existing ai_private.runs%rowtype;
  v_gate jsonb;
  v_entitlement record;
  v_period record;
  v_policy ai_private.budget_policies%rowtype;
  v_run_id uuid:=gen_random_uuid();
begin
  perform ai_private.assert_member(p_user_id);
  if p_source_message_id is null or p_attempt_id is null or p_payload_hash!~'^[0-9a-f]{64}$' then
    raise exception 'ai_mock_run_input_invalid' using errcode='22023';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6c_run:'||p_user_id::text||':'||p_attempt_id::text,0));
  select * into v_existing from ai_private.runs r where r.user_id=p_user_id and r.request_id=p_attempt_id;
  if v_existing.id is not null then
    if v_existing.source_message_id is distinct from p_source_message_id or v_existing.payload_hash<>p_payload_hash or v_existing.adapter_code<>'mock' then
      raise exception 'ai_run_request_conflict' using errcode='23505';
    end if;
    return jsonb_build_object('replay',true,'run_id',v_existing.id,'status',v_existing.status);
  end if;
  select * into v_message from public.ai_messages m where m.id=p_source_message_id and m.user_id=p_user_id and m.message_role='user' and m.status='active';
  if v_message.id is null then raise exception 'ai_source_message_forbidden' using errcode='42501'; end if;
  if (select count(*) from ai_private.runs r where r.source_message_id=p_source_message_id)>=3 then
    raise exception 'ai_retry_limit_reached' using errcode='54000';
  end if;
  v_gate:=ai_private.phase6c_chat_status(p_user_id,now());
  if not (v_gate->>'chat_write_allowed')::boolean then raise exception '%',v_gate->>'deny_reason' using errcode='42501'; end if;
  if not exists(select 1 from ai_private.phase6c_runtime_config c where c.singleton and c.mock_chat_enabled and not c.external_provider_enabled) then
    raise exception 'mock_disabled' using errcode='42501';
  end if;
  select * into v_entitlement from ai_private.current_entitlement(p_user_id,now());
  select * into v_period from ai_private.subscription_period(v_entitlement.entitlement_started_at,now());
  select * into v_policy from ai_private.budget_policies where active order by created_at desc limit 1;
  insert into ai_private.budget_accounts(user_id,period_start,period_end,policy_version)
  values(p_user_id,v_period.period_start,v_period.period_end,v_policy.policy_version)
  on conflict(user_id,period_start) do nothing;
  insert into ai_private.runs(id,user_id,request_id,thread_id,source_message_id,feature_code,adapter_code,model_tier,policy_version,schema_version,payload_hash,reserved_cost_micros)
  values(v_run_id,p_user_id,p_attempt_id,v_message.thread_id,v_message.id,'private_chat','mock','luna','phase6c.mock.v1','phase6a.response.v1',p_payload_hash,0);
  insert into ai_private.usage_ledger(id,user_id,run_id,request_id,feature_code,model_tier,ledger_type,amount_micros)
  values(gen_random_uuid(),p_user_id,v_run_id,p_attempt_id,'private_chat','luna','reserve',0);
  insert into ai_private.audit_events(id,user_id,run_id,event_code,safe_metadata)
  values(gen_random_uuid(),p_user_id,v_run_id,'run_reserved',jsonb_build_object('feature_code','private_chat','adapter_code','mock','package','6c'));
  return jsonb_build_object('replay',false,'run_id',v_run_id,'status','reserved');
end;
$$;

create or replace function public.fmz_phase6c_export_chat(p_request_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid:=auth.uid();
  v_audit public.ai_data_lifecycle_requests%rowtype;
  v_replay boolean:=false;
begin
  perform ai_private.phase6c_reconcile_member(v_user_id,now());
  if p_request_id is null then raise exception 'ai_export_input_invalid' using errcode='22023'; end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6c_lifecycle:'||v_user_id::text||':'||p_request_id::text,0));
  select * into v_audit from public.ai_data_lifecycle_requests r where r.user_id=v_user_id and r.request_id=p_request_id;
  if v_audit.id is not null then
    if v_audit.request_type<>'export' or v_audit.scope_thread_id is not null then raise exception 'ai_lifecycle_request_conflict' using errcode='23505'; end if;
    v_replay:=true;
  else
    insert into public.ai_data_lifecycle_requests(id,user_id,request_type,status,request_id,requested_at,completed_at,safe_result_code)
    values(gen_random_uuid(),v_user_id,'export','completed',p_request_id,now(),now(),'chat_json_returned') returning * into v_audit;
  end if;
  return jsonb_build_object(
    'schema_version','phase6c.chat-export.v1','generated_at',now(),'replay',v_replay,
    'conversations',coalesce((select jsonb_agg(jsonb_build_object(
      'id',t.id,'locale',t.locale,'status',t.status,'retention_state',t.retention_state,'retention_due_at',t.retention_due_at,'created_at',t.created_at,'updated_at',t.updated_at,
      'messages',coalesce((select jsonb_agg(jsonb_build_object('id',m.id,'role',m.message_role,'content',m.content_text,'sequence',m.sequence_number,'created_at',m.created_at) order by m.sequence_number) from public.ai_messages m where m.thread_id=t.id and m.user_id=v_user_id and m.status='active'),'[]'::jsonb)
    ) order by t.created_at,t.id) from public.ai_threads t where t.user_id=v_user_id and t.feature_code='private_chat' and t.retention_state<>'deleted'),'[]'::jsonb)
  );
end;
$$;

create or replace function public.fmz_phase6c_delete_thread(
  p_thread_id uuid,
  p_expected_revision bigint,
  p_request_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
declare
  v_user_id uuid:=auth.uid();
  v_thread public.ai_threads%rowtype;
  v_audit public.ai_data_lifecycle_requests%rowtype;
begin
  perform ai_private.phase6c_reconcile_member(v_user_id,now());
  if p_thread_id is null or p_request_id is null or p_expected_revision is null or p_expected_revision<1 then raise exception 'ai_delete_input_invalid' using errcode='22023'; end if;
  perform pg_advisory_xact_lock(hashtextextended('fmz_phase6c_lifecycle:'||v_user_id::text||':'||p_request_id::text,0));
  select * into v_audit from public.ai_data_lifecycle_requests r where r.user_id=v_user_id and r.request_id=p_request_id;
  if v_audit.id is not null then
    if v_audit.request_type<>'delete' or v_audit.scope_thread_id is distinct from p_thread_id then raise exception 'ai_lifecycle_request_conflict' using errcode='23505'; end if;
    return jsonb_build_object('replay',true,'thread_id',p_thread_id,'deleted',true);
  end if;
  select * into v_thread from public.ai_threads t where t.id=p_thread_id for update;
  if v_thread.id is null or v_thread.user_id<>v_user_id or v_thread.feature_code<>'private_chat' then raise exception 'ai_thread_forbidden' using errcode='42501'; end if;
  if v_thread.retention_state='deleted' then
    insert into public.ai_data_lifecycle_requests(id,user_id,request_type,status,request_id,scope_thread_id,requested_at,completed_at,safe_result_code)
    values(gen_random_uuid(),v_user_id,'delete','completed',p_request_id,p_thread_id,now(),now(),'chat_content_already_deleted');
    return jsonb_build_object('replay',false,'thread_id',p_thread_id,'deleted',true);
  end if;
  if v_thread.revision<>p_expected_revision then raise exception 'ai_thread_stale_conflict' using errcode='40001'; end if;
  update public.ai_messages set content_text=null,structured_output=null,schema_version=null,status='deleted'
  where thread_id=p_thread_id and user_id=v_user_id and status='active';
  update public.ai_threads set retention_state='deleted',status='content_deleted',retention_started_at=coalesce(retention_started_at,now()),retention_due_at=coalesce(retention_due_at,now()),content_deleted_at=now(),archived_at=coalesce(archived_at,now()),updated_at=now()
  where id=p_thread_id and user_id=v_user_id;
  insert into public.ai_data_lifecycle_requests(id,user_id,request_type,status,request_id,scope_thread_id,requested_at,completed_at,safe_result_code)
  values(gen_random_uuid(),v_user_id,'delete','completed',p_request_id,p_thread_id,now(),now(),'chat_content_deleted');
  return jsonb_build_object('replay',false,'thread_id',p_thread_id,'deleted',true);
end;
$$;

revoke all on all functions in schema ai_private from public,anon,authenticated;
revoke all on function public.fmz_phase6c_get_chat_status() from public,anon,authenticated;
revoke all on function public.fmz_phase6c_create_thread(uuid,text,uuid) from public,anon,authenticated;
revoke all on function public.fmz_phase6c_list_threads(integer,timestamptz,uuid) from public,anon,authenticated;
revoke all on function public.fmz_phase6c_read_thread(uuid,integer,bigint) from public,anon,authenticated;
revoke all on function public.fmz_phase6c_submit_message(uuid,uuid,bigint,text,text) from public,anon,authenticated;
revoke all on function public.fmz_phase6c_service_begin_mock_run(uuid,uuid,uuid,text) from public,anon,authenticated;
revoke all on function public.fmz_phase6c_export_chat(uuid) from public,anon,authenticated;
revoke all on function public.fmz_phase6c_delete_thread(uuid,bigint,uuid) from public,anon,authenticated;

grant execute on function public.fmz_phase6c_get_chat_status() to authenticated;
grant execute on function public.fmz_phase6c_create_thread(uuid,text,uuid) to authenticated;
grant execute on function public.fmz_phase6c_list_threads(integer,timestamptz,uuid) to authenticated;
grant execute on function public.fmz_phase6c_read_thread(uuid,integer,bigint) to authenticated;
grant execute on function public.fmz_phase6c_submit_message(uuid,uuid,bigint,text,text) to authenticated;
grant execute on function public.fmz_phase6c_export_chat(uuid) to authenticated;
grant execute on function public.fmz_phase6c_delete_thread(uuid,bigint,uuid) to authenticated;
grant execute on function public.fmz_phase6c_service_begin_mock_run(uuid,uuid,uuid,text) to service_role;

select cron.schedule(
  'fmz-phase6c-retention-sweep',
  '* * * * *',
  $cron$select ai_private.phase6c_retention_sweep(now());$cron$
);

commit;
