with checks(name, pass, detail) as (
  values
    (
      'migration_recorded',
      exists (
        select 1 from supabase_migrations.schema_migrations
        where version = '20260904230850'
      ),
      'schema_migrations contains 20260904230850'
    ),
    (
      'tables_exist',
      to_regclass('public.ai_analysis_preferences') is not null
        and to_regclass('public.ai_analysis_results') is not null
        and to_regclass('public.ai_analysis_lifecycle_requests') is not null
        and to_regclass('ai_private.phase6d_runtime_config') is not null,
      '6D public/private tables exist'
    ),
    (
      'rls_enabled',
      coalesce((select relrowsecurity from pg_class where oid = 'public.ai_analysis_preferences'::regclass), false)
        and coalesce((select relrowsecurity from pg_class where oid = 'public.ai_analysis_results'::regclass), false)
        and coalesce((select relrowsecurity from pg_class where oid = 'public.ai_analysis_lifecycle_requests'::regclass), false),
      'RLS enabled on public 6D tables'
    ),
    (
      'rpc_only_browser_tables',
      not has_table_privilege('authenticated', 'public.ai_analysis_preferences', 'select')
        and not has_table_privilege('authenticated', 'public.ai_analysis_results', 'select')
        and not has_table_privilege('authenticated', 'public.ai_analysis_lifecycle_requests', 'select')
        and not has_table_privilege('anon', 'public.ai_analysis_results', 'select'),
      'direct table grants absent for anon/authenticated'
    ),
    (
      'analysis_consent_kind_allowed',
      exists (
        select 1 from pg_constraint
        where conrelid = 'public.ai_consent_events'::regclass
          and conname = 'ai_consent_events_kind_check'
          and pg_get_constraintdef(oid) like '%ai_analysis%'
      )
      and exists (
        select 1 from pg_constraint
        where conrelid = 'ai_private.consent_documents'::regclass
          and conname = 'ai_consent_documents_kind_check'
          and pg_get_constraintdef(oid) like '%ai_analysis%'
      ),
      'ai_analysis included in consent constraints'
    ),
    (
      'active_analysis_contracts',
      (select count(*) from ai_private.consent_documents where consent_kind = 'ai_analysis' and document_version = 'phase6d-analysis-v1' and status = 'active') = 3,
      'NL/EN/DE ai_analysis consent docs active'
    ),
    (
      'provider_disabled',
      exists (
        select 1 from ai_private.phase6d_runtime_config
        where singleton and mock_analyses_enabled and not external_provider_enabled
      ),
      'mock-only runtime config'
    ),
    (
      'schema_registered',
      exists (
        select 1 from ai_private.structured_schemas
        where schema_code = 'read_only_ai_analysis'
          and schema_version = 'phase6d.analysis.v1'
          and active
      ),
      'phase6d output schema active'
    ),
    (
      'functions_exist',
      to_regprocedure('public.fmz_phase6d_get_status()') is not null
        and to_regprocedure('public.fmz_phase6d_prepare_analysis(uuid,text,text,uuid)') is not null
        and to_regprocedure('public.fmz_phase6d_service_begin_analysis(uuid,uuid,uuid,text,text,jsonb,text[])') is not null
        and to_regprocedure('public.fmz_phase6d_service_complete_analysis(uuid,uuid,jsonb,bigint,integer,integer)') is not null
        and to_regprocedure('public.fmz_phase6d_service_fail_analysis(uuid,uuid,text)') is not null
        and to_regprocedure('public.fmz_phase6d_export_analyses(uuid)') is not null
        and to_regprocedure('public.fmz_phase6d_delete_analysis(uuid,bigint,uuid)') is not null,
      'member and service RPCs exist'
    ),
    (
      'member_grants',
      has_function_privilege('authenticated', 'public.fmz_phase6d_get_status()', 'execute')
        and has_function_privilege('authenticated', 'public.fmz_phase6d_record_analysis_consent(text,text,text,boolean,uuid)', 'execute')
        and has_function_privilege('authenticated', 'public.fmz_phase6d_list_analyses(integer,timestamptz,uuid)', 'execute')
        and not has_function_privilege('authenticated', 'public.fmz_phase6d_service_begin_analysis(uuid,uuid,uuid,text,text,jsonb,text[])', 'execute'),
      'authenticated can call only member RPCs'
    ),
    (
      'service_grants',
      has_function_privilege('service_role', 'public.fmz_phase6d_service_begin_analysis(uuid,uuid,uuid,text,text,jsonb,text[])', 'execute')
        and has_function_privilege('service_role', 'public.fmz_phase6d_service_complete_analysis(uuid,uuid,jsonb,bigint,integer,integer)', 'execute')
        and has_function_privilege('service_role', 'public.fmz_phase6d_service_select_due_analyses(integer)', 'execute'),
      'service_role can call service RPCs'
    ),
    (
      'model_routes',
      ai_private.phase6d_model_tier('daily') = 'luna'
        and ai_private.phase6d_model_tier('post_workout') = 'luna'
        and ai_private.phase6d_model_tier('weekly') = 'terra',
      'daily/post_workout Luna and weekly Terra'
    ),
    (
      'retention_cron',
      exists (
        select 1 from cron.job
        where jobname = 'fmz-phase6d-analysis-retention-sweep'
          and schedule = '*/15 * * * *'
      ),
      '6D retention sweep scheduled through pg_cron'
    )
)
select name, pass, detail
from checks
order by name;

with checks(name, pass) as (
  values
    ('migration_recorded', exists (select 1 from supabase_migrations.schema_migrations where version = '20260904230850')),
    ('tables_exist', to_regclass('public.ai_analysis_results') is not null),
    ('provider_disabled', exists (select 1 from ai_private.phase6d_runtime_config where singleton and not external_provider_enabled)),
    ('retention_cron', exists (select 1 from cron.job where jobname = 'fmz-phase6d-analysis-retention-sweep'))
)
select
  count(*) filter (where pass) as pass_count,
  count(*) filter (where not pass) as fail_count,
  bool_and(pass) as overall_pass
from checks;
