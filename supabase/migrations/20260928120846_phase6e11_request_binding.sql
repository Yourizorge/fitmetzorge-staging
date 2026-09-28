-- 6E-11 private request binding. M38 workflow and M40/M41 bodies are immutable.
begin;
create schema fmz6e11_request_private;
revoke all on schema fmz6e11_request_private from public, anon, authenticated, service_role;
alter default privileges in schema fmz6e11_request_private revoke execute on functions from public;
create table fmz6e11_request_private.control (
 id boolean primary key default true check(id),
 enabled boolean not null default false,
 expires_at timestamptz
);
insert into fmz6e11_request_private.control(id) values(true);
create table fmz6e11_request_private.receipts (
 request_id uuid primary key, action_id uuid not null unique,
 run_id uuid not null, actor uuid not null, session_id uuid not null,
 issuer text not null, audience text not null check(audience='authenticated'),
 token_expires_at timestamptz not null, actor_role text not null,
 window_id uuid not null, workspace_id uuid not null, route text not null check(route in ('A','B')),
 action text not null, idempotency_key uuid not null, payload_sha text not null,
 source_version integer, source_sha text, versions_before jsonb not null,
 versions_after jsonb, branches jsonb not null, selected_branch text,
 before_sha text not null, after_sha text,
 xid xid8 not null default pg_current_xact_id(), backend integer not null default pg_backend_pid(),
 state text not null check(state in ('intent','confirmed','pair_validated')),
 receipt jsonb, created_at timestamptz not null default clock_timestamp(),
 check(payload_sha ~ '^[0-9a-f]{64}$'),check(before_sha ~ '^[0-9a-f]{64}$'),
 check(after_sha is null or after_sha ~ '^[0-9a-f]{64}$')
);
create index receipts_actor_key on fmz6e11_request_private.receipts(actor,idempotency_key);
create index receipts_window on fmz6e11_request_private.receipts(window_id,created_at);
alter table fmz6e11_request_private.control enable row level security;
alter table fmz6e11_request_private.receipts enable row level security;

create function fmz6e11_request_private.entry(r uuid,t text,op text,k jsonb) returns jsonb
language sql security invoker immutable set search_path=pg_catalog,pg_temp as $f$
 select jsonb_build_array(jsonb_build_object('table','fmz6e11_private.'||t,'op',op,
 'old',case when op<>'INSERT' then fmz6e11_audit_private.pk_hash(r,'fmz6e11_private.'||t,k) end,
 'new',case when op<>'DELETE' then fmz6e11_audit_private.pk_hash(r,'fmz6e11_private.'||t,k) end))
$f$;

-- Only bounded, already-authorized synthetic workspace state, never managed data.
create function fmz6e11_request_private.snapshot(w uuid,x uuid) returns jsonb
language plpgsql security invoker stable set search_path=pg_catalog,pg_temp as $f$
declare result jsonb:='[]';t text;rows jsonb;n integer;
begin
 foreach t in array array['windows','participants','workspaces','source_versions','source_heads',
 'plans','proposals','audit','requests','b_states','b_versions','inbox_state','events'] loop
 execute format('select count(*),coalesce(jsonb_agg(h order by h),''[]'') from
 (select fmz6e11_private.sha(to_jsonb(t)) h from fmz6e11_private.%I t where %s limit 1001) z',t,
 case when t='windows' then 'id=$1' when t='workspaces' then 'id=$2'
 when t in ('participants','audit','requests','events') then 'window_id=$1' else 'workspace_id=$2' end)
 into n,rows using w,x;
 if n>1000 then raise exception 'request_scoped_budget';end if;
 result:=result||jsonb_build_array(jsonb_build_object('table',t,'count',n,'sha',fmz6e11_private.sha(rows)));
 end loop;
 return result;
end $f$;

-- Plans are derived from the locked pre-state, not from observed writes.
create function fmz6e11_request_private.branches(r uuid,q jsonb,u uuid) returns jsonb
language plpgsql security invoker stable set search_path=pg_catalog,pg_temp as $f$
declare w uuid:=(q->>'window')::uuid;x uuid:=(q->>'workspace')::uuid;k uuid:=(q->>'key')::uuid;
 a text:=q->>'action';s jsonb:='[]';d jsonb;re jsonb;pv integer;sv integer;av integer;op text;
begin
 d:=fmz6e11_request_private.entry(r,'events','INSERT',jsonb_build_array(w,x,u,k,a,'denied'));
 re:=fmz6e11_request_private.entry(r,'events','INSERT',jsonb_build_array(w,x,u,k,a,'replayed'));
 s:=fmz6e11_request_private.entry(r,'events','INSERT',jsonb_build_array(w,x,u,k,a,'committed'))
 ||fmz6e11_request_private.entry(r,'requests','INSERT',jsonb_build_array(u,k));
 if a in ('viewed','later') then
 pv:=(q->'data'->>'proposal_version')::integer;
 op:=case when exists(select 1 from fmz6e11_private.inbox_state where workspace_id=x and actor=u and proposal_version=pv)
 then 'UPDATE' else 'INSERT' end;
 s:=s||fmz6e11_request_private.entry(r,'inbox_state',op,jsonb_build_array(x,u,pv));
 else
 s:=s||fmz6e11_request_private.entry(r,'windows','UPDATE',jsonb_build_array(w));
 if a like 'b_%' then
 s:=s||fmz6e11_request_private.entry(r,'b_states','UPDATE',jsonb_build_array(x));
 if a='b_apply' then
 select active_version into av from fmz6e11_private.b_states where workspace_id=x;
 s:=s||fmz6e11_request_private.entry(r,'b_versions','INSERT',jsonb_build_array(x,av+1));end if;
 else
 s:=s||fmz6e11_request_private.entry(r,'audit','INSERT',jsonb_build_array(w,u,a));
 select coalesce(max(version),0) into pv from fmz6e11_private.proposals where workspace_id=x;
 select active_version into av from fmz6e11_private.workspaces where id=x;
 if a='source_append' then
 select coalesce(max(version),0)+1 into sv from fmz6e11_private.source_versions where workspace_id=x;
 op:=case when exists(select 1 from fmz6e11_private.source_heads where workspace_id=x) then 'UPDATE' else 'INSERT' end;
 s:=s||fmz6e11_request_private.entry(r,'source_versions','INSERT',jsonb_build_array(x,sv))
 ||fmz6e11_request_private.entry(r,'source_heads',op,jsonb_build_array(x));
 elsif a='source_withdraw' then s:=s||fmz6e11_request_private.entry(r,'source_heads','UPDATE',jsonb_build_array(x));
 elsif a in ('propose','restore') then s:=s||fmz6e11_request_private.entry(r,'proposals','INSERT',jsonb_build_array(x,pv+1));
 else
 select version into pv from fmz6e11_private.proposals where workspace_id=x and id=(q->'data'->>'proposal')::uuid;
 s:=s||fmz6e11_request_private.entry(r,'proposals','UPDATE',jsonb_build_array(x,pv));
 if a='apply' then s:=s||fmz6e11_request_private.entry(r,'plans','INSERT',jsonb_build_array(x,av+1))
 ||fmz6e11_request_private.entry(r,'workspaces','UPDATE',jsonb_build_array(x));end if;
 end if;
 end if;
 end if;
 return jsonb_build_object('committed',s,'denied',d,'replayed',re);
end $f$;

create function fmz6e11_request_private.call(input jsonb,rid uuid) returns jsonb
language plpgsql security invoker set search_path=pg_catalog,pg_temp as $f$
declare q jsonb:=case when input->>'op'='internal_b' then input->'request' else input end;
 c jsonb:=coalesce(nullif(current_setting('request.jwt.claims',true),''),'{}')::jsonb;
 p jsonb;w fmz6e11_private.windows;x fmz6e11_private.workspaces;role_name text;
 old fmz6e11_request_private.receipts;run uuid:=gen_random_uuid();aid uuid:=gen_random_uuid();
 branches jsonb;expected jsonb;before_state jsonb;after_state jsonb;result jsonb;branch text;
 payload_sha text:=fmz6e11_private.sha(input);vbefore jsonb;vafter jsonb;source_v integer;source_h text;
 cleanup_table text;cleanup_rows tid[];cleanup_expected jsonb;
begin
 if current_user<>'postgres' or rid is null then raise exception 'request_server_only';end if;
 if not exists(select 1 from fmz6e11_request_private.control where id and enabled
 and expires_at>clock_timestamp() and expires_at<=clock_timestamp()+interval '24 hours') then raise exception 'request_disabled';end if;
 if c->>'iss' is distinct from 'https://mokxyyullfhkfalopbzd.supabase.co/auth/v1'
 or c->>'aud' is distinct from 'authenticated' or c->>'role' is distinct from 'authenticated'
 or coalesce((c->>'exp')::numeric,0)<=extract(epoch from clock_timestamp())
 or c->>'sub' is null or c->>'session_id' is null then raise exception 'request_claims_invalid';end if;
 perform fmz6e11_private.exact(c,array['sub','session_id','iss','aud','exp','role'],array['sub','session_id','iss','aud','exp','role']);
 p:=fmz6e11_private.principal();
 if (select encode(sha256(convert_to(prosrc,'UTF8')),'hex') from pg_proc
 where oid='fmz6e11_private.api_call(jsonb)'::regprocedure)
 is distinct from '4cb3383993916475f1da1562c0fbb557c850d95505869361a9336220bf7aed92'
 then raise exception 'request_workflow_source_changed';end if;
 if q->>'op' is distinct from 'command' or not coalesce(q->>'action'=any(array[
 'source_append','source_withdraw','propose','restore','member_accept','trainer_approve',
 'member_reject','trainer_reject','trainer_block','apply','b_build','b_edit','b_confirm',
 'b_apply','b_restore','b_reopen','b_reject','viewed','later','revoke','cleanup_batch']),false) then raise exception 'request_action_invalid';end if;
 perform pg_advisory_xact_lock(611,20260928);
 select * into w from fmz6e11_private.windows where id=(q->>'window')::uuid for update;
 select * into x from fmz6e11_private.workspaces where id=(q->>'workspace')::uuid and window_id=w.id for update;
 if w.id is null or x.id is null then raise exception 'request_workspace_missing';end if;
 if q->>'action'='cleanup_batch' then
 if not coalesce((p->>'operator')::boolean,false) or w.operator_id<>(p->>'uid')::uuid
 or w.status<>'revoked' or w.feature_enabled or (q->>'expected')::bigint<>w.revision
 then raise exception 'request_cleanup_guard';end if;
 role_name:=p->>'role';
 cleanup_table:=q->'data'->>'table';
 if not coalesce(cleanup_table=any(array['inbox_state','events','proposals','source_heads','source_versions','plans','b_versions','b_states','audit','requests','participants','workspaces']),false)
 then raise exception 'request_cleanup_table';end if;
 perform fmz6e11_private.exact(q->'data',array['table'],array['table']);
 execute format('select array_agg(z.ctid),coalesce(jsonb_agg(jsonb_build_object(
 ''table'',%L,''op'',''DELETE'',''old'',fmz6e11_audit_private.pk_hash($3,%L,z.k),''new'',null)),''[]'')
 from (select t.ctid,fmz6e11_audit_private.project_key(t,r.pk_columns) k
 from fmz6e11_private.%I t cross join fmz6e11_audit_private.relations r
 where r.table_name=%L and t.%I=$1 order by t.ctid limit 8 for update of t) z',
 'fmz6e11_private.'||cleanup_table,'fmz6e11_private.'||cleanup_table,cleanup_table,
 'fmz6e11_private.'||cleanup_table,case when cleanup_table in ('audit','requests','participants') then 'window_id'
 when cleanup_table='workspaces' then 'id' else 'workspace_id' end)
 into cleanup_rows,cleanup_expected using case when cleanup_table in ('audit','requests','participants') then w.id else x.id end,x.id,run;
 else
 role_name:=fmz6e11_private.workspace_guard(w,x,(p->>'uid')::uuid);
 if q->>'action'='revoke' and (not coalesce((p->>'operator')::boolean,false) or w.operator_id<>(p->>'uid')::uuid)
 then raise exception 'request_operator_required';end if;
 end if;
 if q->>'action'<>'cleanup_batch' and (x.route='B') is distinct from (input->>'op'='internal_b' or q->>'action' in ('viewed','later') and x.route='B')
 then raise exception 'request_route_invalid';end if;
 select * into old from fmz6e11_request_private.receipts where request_id=rid;
 if found then
 if old.actor<>(p->>'uid')::uuid or old.session_id<>(c->>'session_id')::uuid
 or old.payload_sha<>payload_sha or old.idempotency_key<>(q->>'key')::uuid
 then raise exception 'request_id_conflict';end if;
 if old.state<>'pair_validated' then raise exception 'request_pair_incomplete';end if;
 return old.receipt||jsonb_build_object('replay',true,'request_id',rid);end if;
 if exists(select 1 from fmz6e11_request_private.receipts where state<>'pair_validated')
 then raise exception 'request_previous_pair_incomplete';end if;
 -- A managed schema observer would violate this request's explicit scope.
 if exists(select 1 from fmz6e11_audit_private.relations where table_name ~ '^(auth|storage|realtime)\.')
 then raise exception 'request_managed_observer_forbidden';end if;
 if exists(select 1 from pg_class z join pg_namespace n on n.oid=z.relnamespace
 where z.relkind='r' and n.nspname in ('public','fmz6e11_private') and not exists(
 select 1 from fmz6e11_audit_private.relations a where a.rel=z.oid))
 then raise exception 'request_observer_coverage_missing';end if;
 before_state:=fmz6e11_request_private.snapshot(w.id,x.id);
 vbefore:=coalesce(fmz6e11_workflow_audit.versions(w.id),'{}');
 if x.route='A' then select h.version,s.hash into source_v,source_h from fmz6e11_private.source_heads h
 join fmz6e11_private.source_versions s on s.workspace_id=h.workspace_id and s.version=h.version where h.workspace_id=x.id;
 else select source_version,source_hash into source_v,source_h from fmz6e11_private.b_states where workspace_id=x.id;end if;
 branches:=fmz6e11_request_private.branches(run,q,(p->>'uid')::uuid);
 if q->>'action'='cleanup_batch' then branches:=jsonb_build_object('committed',cleanup_expected);
 elsif q->>'action'='revoke' then
 branches:=jsonb_build_object('committed',
 fmz6e11_request_private.entry(run,'windows','UPDATE',jsonb_build_array(w.id))
 ||fmz6e11_request_private.entry(run,'windows','UPDATE',jsonb_build_array(w.id))
 ||fmz6e11_request_private.entry(run,'audit','INSERT',jsonb_build_array(w.id,(p->>'uid')::uuid,'revoke'))
 ||fmz6e11_request_private.entry(run,'requests','INSERT',jsonb_build_array((p->>'uid')::uuid,(q->>'key')::uuid)));
 end if;
 select jsonb_agg(v) into expected from jsonb_each(branches) e cross join lateral jsonb_array_elements(e.value) v;
 insert into fmz6e11_audit_private.runs values(run,true,clock_timestamp()+interval '5 minutes',clock_timestamp());
 insert into fmz6e11_audit_private.actors values((p->>'uid')::uuid,run,'synthetic_fixture_only')
 on conflict(id) do update set run_id=excluded.run_id;
 insert into fmz6e11_audit_private.actions(id,run_id,actor,workspace,expected,before_sha)
 values(aid,run,(p->>'uid')::uuid,x.id,expected,fmz6e11_private.sha(before_state));
 insert into fmz6e11_request_private.receipts(request_id,action_id,run_id,actor,session_id,issuer,audience,
 token_expires_at,actor_role,window_id,workspace_id,route,action,idempotency_key,payload_sha,source_version,
 source_sha,versions_before,branches,before_sha,state)
 values(rid,aid,run,(p->>'uid')::uuid,(c->>'session_id')::uuid,c->>'iss',c->>'aud',to_timestamp((c->>'exp')::numeric),
 role_name,w.id,x.id,x.route,q->>'action',(q->>'key')::uuid,payload_sha,source_v,source_h,vbefore,branches,
 fmz6e11_private.sha(before_state),'intent');
 perform fmz6e11_audit_private.start_action(aid);
 if q->>'action'='cleanup_batch' then
 execute format('delete from fmz6e11_private.%I where ctid=any($1)',cleanup_table) using coalesce(cleanup_rows,'{}'::tid[]);
 result:=jsonb_build_object('deleted',coalesce(cardinality(cleanup_rows),0),'table',cleanup_table);
 elsif q->>'action'='revoke' then result:=fmz6e11_private.api_call(input||'{"workspace":null}'::jsonb);
 else result:=fmz6e11_private.api_call(input);end if;
 -- The original API normalizes non-product SQL exceptions. Never accept such a
 -- normalized error as an ordinary product denial: it may be an audit failure.
 if result->>'error'='synthetic_operation_denied' then raise exception 'request_unclassified_workflow_failure';end if;
 branch:=case when result ? 'error' then 'denied' when result->>'replay'='true' then 'replayed' else 'committed' end;
 if not branches ? branch then raise exception 'request_unplanned_outcome';end if;
 update fmz6e11_audit_private.actions set expected=branches->branch where id=aid;
 perform fmz6e11_audit_private.confirm_action(aid);
 after_state:=fmz6e11_request_private.snapshot(w.id,x.id);vafter:=coalesce(fmz6e11_workflow_audit.versions(w.id),'{}');
 update fmz6e11_request_private.receipts set selected_branch=branch,versions_after=vafter,
 after_sha=fmz6e11_private.sha(after_state),state='confirmed',receipt=result where request_id=rid;
 return result||jsonb_build_object('request_id',rid);
end $f$;

-- Must be a separate committed transaction. A missing pair prevents the next action.
create function fmz6e11_request_private.seal(rid uuid) returns void
language plpgsql security invoker set search_path=pg_catalog,pg_temp as $f$
declare r fmz6e11_request_private.receipts;h text;
begin
 if current_user<>'postgres' then raise exception 'request_server_only';end if;
 select * into r from fmz6e11_request_private.receipts where request_id=rid for update;
 if found and r.state='pair_validated' then return;end if;
 if not found or r.state<>'confirmed' or r.xid=pg_current_xact_id()
 then raise exception 'request_seal_state';end if;
 h:=fmz6e11_private.sha(fmz6e11_request_private.snapshot(r.window_id,r.workspace_id));
 if h<>r.after_sha then raise exception 'request_after_drift';end if;
 perform fmz6e11_audit_private.seal_pair(r.action_id,r.after_sha,fmz6e11_private.sha(to_jsonb(r)));
 update fmz6e11_request_private.receipts set state='pair_validated' where request_id=rid;
end $f$;

revoke all on all tables in schema fmz6e11_request_private from public,anon,authenticated,service_role;
revoke all on all functions in schema fmz6e11_request_private from public,anon,authenticated,service_role;
-- Only application-owned tables. No managed schema alteration or managed-row write.
do $d$ declare r record;begin
 for r in select c.oid from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where c.relkind='r' and n.nspname in ('public','fmz6e11_private') order by c.oid loop
 perform fmz6e11_audit_private.attach(r.oid::regclass);
 end loop;
 update fmz6e11_audit_private.relations set pk_columns=array['workspace_id','version']::name[]
 where table_name='fmz6e11_private.proposals';
 update fmz6e11_audit_private.relations set pk_columns=array['window_id','actor','action']::name[]
 where table_name='fmz6e11_private.audit';
 update fmz6e11_audit_private.relations set pk_columns=array['window_id','workspace_id','actor','request_key','action','outcome']::name[]
 where table_name='fmz6e11_private.events';
end $d$;
commit;
