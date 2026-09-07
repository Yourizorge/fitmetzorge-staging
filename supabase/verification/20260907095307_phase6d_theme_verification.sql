-- SELECT-only theme contract verification, staging mokxyyullfhkfalopbzd.
begin read only;
with checks(name,pass) as (values
 ('one_nullable_text_column_no_default',(select count(*)=1 from information_schema.columns where table_schema='public' and table_name='member_app_preferences' and column_name='theme_mode' and data_type='text' and is_nullable='YES' and column_default is null)),
 ('validated_three_mode_constraint',(select count(*)=1 from pg_constraint where conrelid='public.member_app_preferences'::regclass and conname='member_app_preferences_theme_mode_check' and convalidated and pg_get_constraintdef(oid) like '%system%' and pg_get_constraintdef(oid) like '%light%' and pg_get_constraintdef(oid) like '%dark%')),
 ('rls_retained',(select relrowsecurity from pg_class where oid='public.member_app_preferences'::regclass)),
 ('no_direct_authenticated_write',not has_table_privilege('authenticated','public.member_app_preferences','INSERT,UPDATE,DELETE')),
 ('no_anon_rpc',not has_function_privilege('anon','public.fmz_phase6d_get_member_settings()','EXECUTE') and not has_function_privilege('anon','public.fmz_phase6d_update_member_settings(jsonb,bigint)','EXECUTE')),
 ('authenticated_rpc',has_function_privilege('authenticated','public.fmz_phase6d_get_member_settings()','EXECUTE') and has_function_privilege('authenticated','public.fmz_phase6d_update_member_settings(jsonb,bigint)','EXECUTE')),
 ('two_definer_functions_safe_path',(select count(*)=2 from pg_proc where oid in ('public.fmz_phase6d_get_member_settings()'::regprocedure,'public.fmz_phase6d_update_member_settings(jsonb,bigint)'::regprocedure) and prosecdef and proconfig @> array['search_path=pg_catalog, public, ai_private, pg_temp'])),
 ('own_user_read_and_system_default',(select prosrc like '%v_user uuid:=auth.uid()%' and prosrc like '%coalesce(v_app.theme_mode,''system'')%' from pg_proc where oid='public.fmz_phase6d_get_member_settings()'::regprocedure)),
 ('own_user_revision_lock_and_validation',(select prosrc like '%v_user uuid:=auth.uid()%' and prosrc like '%pg_advisory_xact_lock%' and prosrc like '%settings_stale_conflict%' and prosrc like '%jsonb_typeof(p_patch->''theme_mode'')<>''string''%' from pg_proc where oid='public.fmz_phase6d_update_member_settings(jsonb,bigint)'::regprocedure)),
 ('canonical_live_identity',(select count(*)=1 from supabase_migrations.schema_migrations where version='20260907095307' and name='phase6d_theme_preference')),
 ('no_theme_fixture_accounts',not exists(select 1 from auth.users where email like 'phase6d-theme-%@example.invalid'))
)
select bool_and(pass) as overall_pass,count(*) filter(where pass) as pass_count,count(*) filter(where not coalesce(pass,false)) as fail_count,jsonb_agg(jsonb_build_object('name',name,'pass',pass)) as checks from checks;
rollback;
