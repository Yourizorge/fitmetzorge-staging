-- FitMetZorge Phase 6A pgcrypto resolution correction (STAGING first)
-- Keep fixed SECURITY DEFINER search paths while resolving Supabase's extensions.digest.

begin;

alter function public.fmz_phase6a_get_context_manifest(text)
  set search_path = pg_catalog, extensions, public, ai_private, pg_temp;

alter function public.fmz_phase6a_service_begin_run(
  uuid,uuid,uuid,text,text,text,text,text,text,bigint,jsonb,text[]
)
  set search_path = pg_catalog, extensions, public, ai_private, pg_temp;

alter function public.fmz_phase6a_service_complete_run(uuid,jsonb,bigint,integer,integer)
  set search_path = pg_catalog, extensions, public, ai_private, pg_temp;

commit;
