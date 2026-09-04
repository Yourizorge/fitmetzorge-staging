-- FitMetZorge Phase 6A consent-event ordering correction (STAGING first)
-- Additive trust fix: a withdrawal must always sort after the grant it follows.

begin;

alter table public.ai_consent_events
  add column if not exists event_sequence bigint generated always as identity;

create unique index if not exists ai_consent_events_event_sequence_idx
  on public.ai_consent_events(event_sequence);

revoke all on sequence public.ai_consent_events_event_sequence_seq
  from public, anon, authenticated;

create or replace function ai_private.current_consent(
  p_user_id uuid,
  p_consent_kind text
)
returns table (
  consent_state text,
  document_version text,
  purpose_code text,
  categories text[],
  locale text,
  consented_at timestamptz,
  document_active boolean
)
language sql
stable
security definer
set search_path = pg_catalog, public, ai_private, pg_temp
as $$
  select e.consent_state, e.document_version, e.purpose_code, e.categories,
    e.locale, e.created_at,
    exists (
      select 1
      from ai_private.consent_documents d
      where d.consent_kind = e.consent_kind
        and d.document_version = e.document_version
        and d.locale = e.locale
        and d.status = 'active'
        and d.effective_at <= now()
    )
  from public.ai_consent_events e
  where e.user_id = p_user_id
    and e.consent_kind = p_consent_kind
  order by e.event_sequence desc
  limit 1;
$$;

revoke all on function ai_private.current_consent(uuid,text)
  from public, anon, authenticated;

commit;
