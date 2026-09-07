-- Synthetic settings checks only; always rollback, no mail/provider/domain writes.
begin;
create temporary table theme_checks(name text primary key, pass boolean not null);
create function pg_temp.check_theme(p_name text,p_pass boolean)
returns void language plpgsql as $$
begin
 if p_pass is distinct from true then raise exception 'THEME CHECK FAILED: %',p_name; end if;
 insert into theme_checks values(p_name,true);
end;
$$;
create temporary table theme_ids(key text primary key,id uuid not null default gen_random_uuid());
insert into theme_ids(key) values('member'),('other'),('trainer');
insert into auth.users(id,aud,role,email,created_at,updated_at)
 select id,'authenticated','authenticated','phase6d-theme-'||key||'@example.invalid',now(),now() from theme_ids;
insert into public.profiles(id,role,name,email)
 select id,case when key='trainer' then 'trainer' else 'client' end,'Theme fixture '||key,'phase6d-theme-'||key||'@example.invalid' from theme_ids;
do $test$
declare
 u uuid:=(select id from theme_ids where key='member');
 b uuid:=(select id from theme_ids where key='other');
 trainer uuid:=(select id from theme_ids where key='trainer');
 v jsonb; bad jsonb; failed boolean; before_profile jsonb;
begin
 perform set_config('request.jwt.claim.sub',u::text,true);
 select to_jsonb(p) into before_profile from public.profiles p where id=u;
 perform pg_temp.check_theme('no preference defaults to system',public.fmz_phase6d_get_member_settings()->'display'->>'theme_mode'='system');
 perform pg_temp.check_theme('read does not create preferences',not exists(select 1 from public.member_app_preferences where user_id=u));
 v:=public.fmz_phase6d_update_member_settings('{"theme_mode":"dark"}',0);
 perform pg_temp.check_theme('dark own server preference saved',v->'display'->>'theme_mode'='dark' and v->>'revision'='1');
 perform pg_temp.check_theme('theme only does not create language row',not exists(select 1 from public.user_settings where user_id=u));
 perform pg_temp.check_theme('profile unchanged',before_profile=(select to_jsonb(p) from public.profiles p where id=u));
 perform pg_temp.check_theme('other member preference not created',not exists(select 1 from public.member_app_preferences where user_id=b));
 v:=public.fmz_phase6d_update_member_settings('{"language":"en","avatar_side":"left"}',1);
 perform pg_temp.check_theme('non-theme update retains dark',v->'display'->>'theme_mode'='dark' and v->>'revision'='2');
 perform pg_temp.check_theme('old language and avatar patch retained',v->>'language'='en' and v->'avatar'->>'side'='left');
 v:=public.fmz_phase6d_update_member_settings('{"theme_mode":"light"}',2);
 perform pg_temp.check_theme('explicit light saved',v->'display'->>'theme_mode'='light' and v->>'revision'='3');
 v:=public.fmz_phase6d_update_member_settings('{"theme_mode":"system"}',3);
 perform pg_temp.check_theme('explicit system saved',v->'display'->>'theme_mode'='system' and v->>'revision'='4');
 perform pg_temp.check_theme('reread preserves saved preference',public.fmz_phase6d_get_member_settings()=v);
 foreach bad in array array['{"theme_mode":"auto"}','{"theme_mode":1}','{"theme_mode":true}','{"theme_mode":[]}','{"theme_mode":{}}','{"theme_mode":null}']::jsonb[] loop
  failed:=false;
  begin perform public.fmz_phase6d_update_member_settings(bad,4); exception when invalid_parameter_value then failed:=true; end;
  perform pg_temp.check_theme('reject invalid theme '||bad::text,failed);
 end loop;
 failed:=false;
 begin perform public.fmz_phase6d_update_member_settings(jsonb_build_object('theme_mode','light','user_id',b),4); exception when invalid_parameter_value then failed:=true; end;
 perform pg_temp.check_theme('cross-user patch rejected',failed);
 failed:=false;
 begin perform public.fmz_phase6d_update_member_settings('{"theme_mode":"dark"}',3); exception when serialization_failure then failed:=true; end;
 perform pg_temp.check_theme('stale revision rejected',failed);
 failed:=false;
 begin perform public.fmz_phase6d_update_member_settings('{"theme_mode":"dark"}',null); exception when invalid_parameter_value then failed:=true; end;
 perform pg_temp.check_theme('null revision rejected',failed);
 perform pg_temp.check_theme('failed writes preserve current revision',public.fmz_phase6d_get_member_settings()=v);
 perform set_config('request.jwt.claim.sub',b::text,true);
 perform pg_temp.check_theme('other login defaults to own system',public.fmz_phase6d_get_member_settings()->'display'->>'theme_mode'='system');
 perform public.fmz_phase6d_update_member_settings('{"theme_mode":"dark"}',0);
 perform set_config('request.jwt.claim.sub',u::text,true);
 perform pg_temp.check_theme('other user cannot change member preference',public.fmz_phase6d_get_member_settings()=v);
 perform set_config('request.jwt.claim.sub',trainer::text,true);
 perform pg_temp.check_theme('trainer own settings remain supported',public.fmz_phase6d_update_member_settings('{"theme_mode":"light"}',0)->'display'->>'theme_mode'='light');
 perform set_config('request.jwt.claim.sub','',true);
 failed:=false;
 begin perform public.fmz_phase6d_get_member_settings(); exception when insufficient_privilege then failed:=true; end;
 perform pg_temp.check_theme('no auth read denied',failed);
 failed:=false;
 begin perform public.fmz_phase6d_update_member_settings('{"theme_mode":"dark"}',0); exception when insufficient_privilege then failed:=true; end;
 perform pg_temp.check_theme('no auth write denied',failed);
 perform set_config('request.jwt.claim.sub',gen_random_uuid()::text,true);
 failed:=false;
 begin perform public.fmz_phase6d_update_member_settings('{"theme_mode":"dark"}',0); exception when insufficient_privilege then failed:=true; end;
 perform pg_temp.check_theme('missing profile denied',failed);
 perform pg_temp.check_theme('anon RPC denied',not has_function_privilege('anon','public.fmz_phase6d_get_member_settings()','execute') and not has_function_privilege('anon','public.fmz_phase6d_update_member_settings(jsonb,bigint)','execute'));
 perform pg_temp.check_theme('authenticated RPC allowed',has_function_privilege('authenticated','public.fmz_phase6d_get_member_settings()','execute') and has_function_privilege('authenticated','public.fmz_phase6d_update_member_settings(jsonb,bigint)','execute'));
 perform pg_temp.check_theme('browser direct tables revoked',not has_table_privilege('authenticated','public.member_app_preferences','select,insert,update,delete') and not has_table_privilege('anon','public.member_app_preferences','select,insert,update,delete'));
 perform pg_temp.check_theme('RLS retained',(select relrowsecurity from pg_class where oid='public.member_app_preferences'::regclass));
end;
$test$;
grant select on theme_ids to authenticated;
grant insert on theme_checks to authenticated;
set local role authenticated;
select set_config('request.jwt.claim.sub',(select id::text from theme_ids where key='member'),true);
select pg_temp.check_theme('real authenticated role can read own theme',public.fmz_phase6d_get_member_settings()->'display'->>'theme_mode'='system');
select pg_temp.check_theme('real authenticated role can change own theme',public.fmz_phase6d_update_member_settings('{"theme_mode":"dark"}',4)->'display'->>'theme_mode'='dark');
reset role;
select jsonb_build_object('overall_pass',bool_and(pass),'pass_count',count(*),'checks',jsonb_agg(to_jsonb(theme_checks) order by name)) as result from theme_checks;
rollback;
