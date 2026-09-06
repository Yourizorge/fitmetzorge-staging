-- New synthetic identities only; every write and fixture is rolled back.
begin;
create temporary table mobile_checks(name text primary key,pass boolean);
create function pg_temp.mobile_check(n text,b boolean) returns void language plpgsql as $$
begin if b is distinct from true then raise exception 'MOBILE FAILED: %',n; end if;insert into mobile_checks values(n,b);end;
$$;
create temporary table mobile_ids(k text primary key,id uuid default gen_random_uuid());
insert into mobile_ids(k) values('member'),('other'),('trainer'),('workout'),('legacy'),('other_result'),('pending'),('failed'),('stale'),('expired'),('content_deleted'),('deleted');
insert into auth.users(id,aud,role,email,created_at,updated_at)
 select id,'authenticated','authenticated','mobile-final-'||k||'@example.invalid',now(),now() from mobile_ids where k in ('member','other','trainer');
insert into public.profiles(id,role,name,email)
 select id,case when k='trainer' then 'trainer' else 'client' end,'Mobile synthetic','mobile-final-'||k||'@example.invalid' from mobile_ids where k in ('member','other','trainer');
select set_config('request.jwt.claim.sub',(select id::text from mobile_ids where k='member'),true);
do $test$
declare u uuid:=(select id from mobile_ids where k='member'); other_u uuid:=(select id from mobile_ids where k='other');
 a uuid:=(select id from mobile_ids where k='workout'); b uuid:=(select id from mobile_ids where k='legacy');
 x uuid; r jsonb; before_row jsonb; fail boolean; n integer;
begin
 insert into public.ai_analysis_results(id,user_id,analysis_kind,feature_code,event_key,request_id,status,adapter_code,model_tier)
 values(a,u,'post_workout','post_workout','mobile:'||a,gen_random_uuid(),'pending','mock','luna');
 perform pg_temp.mobile_check('pending omitted from dashboard',jsonb_array_length(public.fmz_phase6d_get_inbox()->'recent')=0);
 update public.ai_analysis_results set status='ready',summary_text='Synthetic completed workout',result_payload='{"mock":true,"actions":[]}',completed_at=now() where id=a;
 r:=public.fmz_phase6d_get_inbox();
 perform pg_temp.mobile_check('completion automatically visible',r->'recent'->0->>'analysis_id'=a::text);
 perform pg_temp.mobile_check('new badge authoritative',r->'recent'->0->>'state'='new');
 perform pg_temp.mobile_check('short server title',r->'recent'->0->>'title'='Synthetic completed workout');
 perform public.fmz_phase6d_mark_notification(a,'later');
 perform pg_temp.mobile_check('Later remains new unread',public.fmz_phase6d_get_inbox()->'recent'->0->>'state'='later' and (public.fmz_phase6d_get_inbox()->>'unread_count')::integer=1);
 perform public.fmz_phase6d_mark_notification(a,'opened');
 perform pg_temp.mobile_check('Now reads exact result',public.fmz_phase6d_read_analysis(a)->'result'->>'id'=a::text);
 r:=public.fmz_phase6d_get_inbox();
 perform pg_temp.mobile_check('viewed stays in recent',r->'recent'->0->>'analysis_id'=a::text);
 perform pg_temp.mobile_check('viewed is read without New',r->'recent'->0->>'state'='opened' and (r->>'unread_count')::integer=0);
 perform pg_temp.mobile_check('viewed leaves unread notification queue',jsonb_array_length(r->'items')=0);
 perform public.fmz_phase6d_mark_notification(a,'later');
 perform pg_temp.mobile_check('late Later cannot undo read',public.fmz_phase6d_get_inbox()->'recent'->0->>'state'='opened');
 perform set_config('request.jwt.claim.sub','',true);perform set_config('request.jwt.claim.sub',u::text,true);
 perform pg_temp.mobile_check('fresh identity hydration keeps read card',public.fmz_phase6d_get_inbox()->'recent'->0->>'analysis_id'=a::text);
 update public.ai_analysis_results set status='ready' where id=a;
 perform pg_temp.mobile_check('repeat completion makes no duplicate',(select count(*) from public.member_notifications where user_id=u and analysis_id=a)=1 and jsonb_array_length(public.fmz_phase6d_get_inbox()->'recent')=1);

 insert into public.ai_analysis_results(id,user_id,analysis_kind,feature_code,event_key,request_id,status,summary_text,result_payload,completed_at)
 values(b,u,'daily','daily_analysis','mobile:'||b,gen_random_uuid(),'partial',repeat('Long title ',30),'{"mock":true,"actions":[]}',now()-interval '1 hour');
 delete from public.member_notifications where user_id=u and analysis_id=b;
 select to_jsonb(t) into before_row from public.ai_analysis_results t where id=b;
 r:=public.fmz_phase6d_get_inbox();
 perform pg_temp.mobile_check('legacy result without notification visible',exists(select 1 from jsonb_array_elements(r->'recent')i where i->>'analysis_id'=b::text));
 perform pg_temp.mobile_check('read RPC never backfills notifications',not exists(select 1 from public.member_notifications where user_id=u and analysis_id=b));
 perform pg_temp.mobile_check('title bounded at 120',(select char_length(i->>'title')=120 from jsonb_array_elements(r->'recent')i where i->>'analysis_id'=b::text));
 perform pg_temp.mobile_check('no private ownership/run/context keys',not exists(select 1 from jsonb_array_elements(r->'recent')i where i ?| array['user_id','context_manifest_id','run_id','request_id','result_payload']));
 perform public.fmz_phase6d_mark_notification(b,'opened');perform public.fmz_phase6d_mark_notification(b,'opened');
 perform pg_temp.mobile_check('explicit action creates one missing state',(select count(*)=1 and bool_and(state='opened') from public.member_notifications where user_id=u and analysis_id=b));
 perform pg_temp.mobile_check('mark does not rewrite result',before_row=(select to_jsonb(t) from public.ai_analysis_results t where id=b));
 perform public.fmz_phase6d_mark_notification(a,'archived');
 perform pg_temp.mobile_check('archive removes only exact recent card',jsonb_array_length(public.fmz_phase6d_get_inbox()->'recent')=1 and public.fmz_phase6d_get_inbox()->'recent'->0->>'analysis_id'=b::text);
 perform pg_temp.mobile_check('archive preserves result and history',exists(select 1 from jsonb_array_elements(public.fmz_phase6d_list_analyses()->'results')i where i->>'id'=a::text and i->>'status'='ready'));
 perform public.fmz_phase6d_mark_notification(a,'opened');
 perform pg_temp.mobile_check('late open cannot unarchive',(select state='archived' from public.member_notifications where analysis_id=a and user_id=u));

 for n in 1..5 loop
  x:=gen_random_uuid();insert into mobile_ids values('recent'||n,x);
  insert into public.ai_analysis_results(id,user_id,analysis_kind,feature_code,event_key,request_id,status,summary_text,result_payload,completed_at)
  values(x,u,case when n=5 then 'weekly' else 'daily' end,case when n=5 then 'weekly_checkin' else 'daily_analysis' end,'mobile:'||x,gen_random_uuid(),
    case when n=5 then 'insufficient_data' else 'partial' end,'Synthetic recent '||n,'{"mock":true,"actions":[]}',now()+n*interval '1 second');
 end loop;
 r:=public.fmz_phase6d_get_inbox();
 perform pg_temp.mobile_check('maximum three recent',jsonb_array_length(r->'recent')=3);
 perform pg_temp.mobile_check('newest deterministic first',r->'recent'->0->>'analysis_id'=(select id::text from mobile_ids where k='recent5'));
 perform pg_temp.mobile_check('newer replaces oldest only',r->'recent'->2->>'analysis_id'=(select id::text from mobile_ids where k='recent3'));
 perform pg_temp.mobile_check('weekly insufficient result available',r->'recent'->0->>'status'='insufficient_data');
 perform pg_temp.mobile_check('unread queue independent limit five',jsonb_array_length(r->'items')=5 and (r->>'unread_count')::integer=5);
 perform pg_temp.mobile_check('read refresh yields same IDs',public.fmz_phase6d_get_inbox()->'recent'=r->'recent');
 perform pg_temp.mobile_check('all authorized history remains',(select jsonb_array_length(public.fmz_phase6d_list_analyses()->'results'))=7);

 for n in select ordinality::integer from unnest(array['pending','failed','stale','expired','content_deleted','deleted']) with ordinality loop
  select id into x from mobile_ids where k=(array['pending','failed','stale','expired','content_deleted','deleted'])[n];
  insert into public.ai_analysis_results(id,user_id,analysis_kind,feature_code,event_key,request_id,status,summary_text,result_payload,completed_at,result_expires_at,content_deleted_at)
  values(x,u,'daily','daily_analysis','mobile:'||x,gen_random_uuid(),(array['pending','failed','stale','ready','ready','deleted'])[n],
   case when n=6 then null else 'Not dashboard eligible' end,case when n=6 then null else '{"mock":true,"actions":[]}'::jsonb end,
   now()+interval '1 day',case when n=4 then now()-interval '1 second' else now()+interval '30 days' end,case when n=5 then now() end);
 end loop;
 perform pg_temp.mobile_check('pending failed stale expired deleted excluded',public.fmz_phase6d_get_inbox()->'recent'=r->'recent');
 perform public.fmz_phase6d_delete_analysis((select id from mobile_ids where k='recent5'),1,gen_random_uuid());
 r:=public.fmz_phase6d_get_inbox();
 perform pg_temp.mobile_check('delete removes exact result',not exists(select 1 from jsonb_array_elements(r->'recent')i where i->>'analysis_id'=(select id::text from mobile_ids where k='recent5')));
 perform pg_temp.mobile_check('deletion preserves other recent',r->'recent'->0->>'analysis_id'=(select id::text from mobile_ids where k='recent4'));

 select id into x from mobile_ids where k='other_result';
 insert into public.ai_analysis_results(id,user_id,analysis_kind,feature_code,event_key,request_id,status,summary_text,result_payload)
 values(x,other_u,'daily','daily_analysis','mobile:'||x,gen_random_uuid(),'ready','Other fixture','{"mock":true,"actions":[]}');
 fail:=false;begin perform public.fmz_phase6d_read_analysis(x);exception when insufficient_privilege then fail:=true;end;
 perform pg_temp.mobile_check('cross-member detail denied',fail);
 fail:=false;begin perform public.fmz_phase6d_mark_notification(x,'archived');exception when insufficient_privilege then fail:=true;end;
 perform pg_temp.mobile_check('cross-member archive denied',fail);
 perform pg_temp.mobile_check('other notification unchanged',(select state='new' from public.member_notifications where user_id=other_u and analysis_id=x));
 perform set_config('request.jwt.claim.sub',other_u::text,true);
 perform pg_temp.mobile_check('other dashboard own-only',jsonb_array_length(public.fmz_phase6d_get_inbox()->'recent')=1 and public.fmz_phase6d_get_inbox()->'recent'->0->>'analysis_id'=x::text);
 perform set_config('request.jwt.claim.sub',(select id::text from mobile_ids where k='trainer'),true);
 fail:=false;begin perform public.fmz_phase6d_get_inbox();exception when insufficient_privilege then fail:=true;end;
 perform pg_temp.mobile_check('trainer has no private analyses',fail);
 perform set_config('request.jwt.claim.sub','',true);
 fail:=false;begin perform public.fmz_phase6d_get_inbox();exception when insufficient_privilege then fail:=true;end;
 perform pg_temp.mobile_check('anonymous denied',fail);
 perform pg_temp.mobile_check('anon has no RPC grants',not has_function_privilege('anon','public.fmz_phase6d_get_inbox()','execute') and not has_function_privilege('anon','public.fmz_phase6d_mark_notification(uuid,text)','execute'));
 perform pg_temp.mobile_check('no browser table grants',not has_table_privilege('authenticated','public.member_notifications','select,insert,update,delete') and not has_table_privilege('authenticated','public.ai_analysis_results','insert,update,delete'));
 perform pg_temp.mobile_check('own tables retain RLS',(select bool_and(relrowsecurity) from pg_class where oid in ('public.member_notifications'::regclass,'public.ai_analysis_results'::regclass)));
end;
$test$;
select count(*) as pass_count,bool_and(pass) as overall_pass,jsonb_agg(name order by name) as checks from mobile_checks;
rollback;

