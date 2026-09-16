-- Forward-only correction: reject NULL/string version arguments before comparison.
-- Previous source/window migration remains unchanged. Existing rows are untouched.
begin;
create or replace function fmz6e10_private.call(q jsonb) returns jsonb language plpgsql security definer
set search_path=pg_catalog,pg_temp as $f$
declare actor jsonb;u uuid;acting_role text;is_operator boolean;op text;action text;d jsonb;request_key uuid;request_hash text;
w fmz6e10_private.windows;x fmz6e10_private.workspaces;prior fmz6e10_private.requests;
head fmz6e10_private.source_heads;s fmz6e10_private.source_versions;p fmz6e10_private.proposals;plan fmz6e10_private.plans;oldplan fmz6e10_private.plans;
receipt jsonb;result jsonb;source_ref jsonb;restored jsonb;f jsonb;bound text;ver int;a_id uuid;t_id uuid;b_id uuid;until_at timestamptz;from_at timestamptz;
begin
 actor:=fmz6e10_private.principal();u:=(actor->>'uid')::uuid;is_operator:=(actor->>'operator')::boolean;op:=q->>'op';
 if op='home' then
 perform fmz6e10_private.exact(q,array['op'],array['op']);
 return jsonb_build_object('operator',is_operator,'role',actor->>'role',
 'windows',coalesce((select jsonb_agg(jsonb_build_object('id',v.id,'revision',v.revision,'package_version',v.package_version,
 'scenario',v.scenario,'starts_at',v.starts_at,'ends_at',v.ends_at,'status',case when v.status in ('prepared','active') and v.ends_at<=clock_timestamp() then 'expired' else v.status end,'cleanup',v.cleanup)
 order by v.created_at desc) from fmz6e10_private.windows v where (is_operator and v.operator_id=u)
 or exists(select 1 from fmz6e10_private.participants participant where participant.window_id=v.id and participant.user_id=u)),'[]'),
 'workspaces',coalesce((select jsonb_agg(jsonb_build_object('window',v.id,'workspace',z.id,'route',z.route)) from fmz6e10_private.windows v
 join fmz6e10_private.workspaces z on z.window_id=v.id where fmz6e10_private.live_window(v) and (z.member_id=u or z.trainer_id=u)),'[]'));
 elsif op='read' then
 perform fmz6e10_private.exact(q,array['op','window','workspace'],array['op','window','workspace']);
 select * into w from fmz6e10_private.windows where id=(q->>'window')::uuid for share;
 select * into x from fmz6e10_private.workspaces where id=(q->>'workspace')::uuid and window_id=w.id for share;
 if w.id is null or x.id is null then raise exception using errcode='42501',message='synthetic_workspace_denied';end if;
 return fmz6e10_private.read_workspace(w,x,u);
 elsif op is distinct from 'command' then raise exception using errcode='22023',message='synthetic_operation_invalid';end if;
 perform fmz6e10_private.exact(q,array['op','window','workspace','key','expected','action','data'],array['op','window','workspace','key','expected','action','data']);
 request_key:=(q->>'key')::uuid;if request_key is null then raise exception 'synthetic_key_required';end if;
 perform fmz6e10_private.number(q->'expected',0,1000000,true);
 action:=q->>'action';d:=q->'data';request_hash:=fmz6e10_private.sha(q);
 if action in ('member_accept','member_reject','trainer_approve','trainer_reject','trainer_block','apply') then
 perform fmz6e10_private.number(d->'proposal_version',1,500,true);
 elsif action='source_withdraw' then perform fmz6e10_private.number(d->'source_version',1,500,true);
 elsif action='restore' then perform fmz6e10_private.number(d->'plan_version',1,501,true);
 end if;
 if action in ('prepare','activate','revoke','cleanup') then
 if not is_operator then raise exception using errcode='42501',message='synthetic_operator_required';end if;
 perform 1 from fmz6e10_private.operators where user_id=u for update;
 if action<>'prepare' then
 select * into w from fmz6e10_private.windows where id=(q->>'window')::uuid and operator_id=u for update;
 if w.id is null then raise exception using errcode='42501',message='synthetic_window_denied';end if;
 end if;
 else
 select * into w from fmz6e10_private.windows where id=(q->>'window')::uuid for update;
 select * into x from fmz6e10_private.workspaces where id=(q->>'workspace')::uuid and window_id=w.id for update;
 if w.id is null or x.id is null then raise exception using errcode='42501',message='synthetic_workspace_denied';end if;
 acting_role:=fmz6e10_private.workspace_guard(w,x,u);
 if x.route<>'A' then raise exception using errcode='42501',message='synthetic_route_b_no_trainer_sources';end if;
 if action in ('source_append','source_withdraw','trainer_approve','trainer_reject','trainer_block','apply') and acting_role<>'a_trainer' then
 raise exception using errcode='42501',message='synthetic_trainer_required';end if;
 if action in ('member_accept','member_reject','restore') and acting_role<>'a_member' then raise exception using errcode='42501',message='synthetic_member_required';end if;
 end if;
 select * into prior from fmz6e10_private.requests where requests.actor=u and requests.key=request_key;
 if found then
 if prior.payload_hash<>request_hash then raise exception using errcode='40001',message='synthetic_idempotency_conflict';end if;
 return prior.receipt||jsonb_build_object('replay',true);
 end if;
 if (select count(*) from fmz6e10_private.requests where requests.actor=u and at>clock_timestamp()-interval '1 minute')>=60 then
 raise exception using errcode='54000',message='synthetic_rate_limit';end if;
 if action<>'prepare' and (q->>'expected')::bigint<>w.revision then raise exception using errcode='40001',message='synthetic_stale_revision';end if;
 if action='prepare' then
 perform fmz6e10_private.exact(d,array['scenario','starts_at','ends_at'],array['scenario','starts_at','ends_at']);
 if q->'window'<>'null'::jsonb or q->'workspace'<>'null'::jsonb or (q->>'expected')::int<>0 then raise exception 'synthetic_prepare_identity_invalid';end if;
 if coalesce(d->>'scenario','') not in ('kg','lb') then raise exception 'synthetic_scenario_invalid';end if;
 perform 1 from fmz6e10_private.identities order by user_id for share;
 select user_id into a_id from fmz6e10_private.identities where identities.role='a_member' and enabled;
 select user_id into t_id from fmz6e10_private.identities where identities.role='a_trainer' and enabled;
 select user_id into b_id from fmz6e10_private.identities where identities.role='b_member' and enabled;
 if a_id is null or t_id is null or b_id is null then raise exception 'synthetic_registry_incomplete';end if;
 if not exists(select 1 from public.profiles where id=a_id and role='client' and trainer_id=t_id)
 or not exists(select 1 from public.profiles where id=t_id and role='trainer')
 or not exists(select 1 from public.profiles where id=b_id and role='client' and trainer_id is null) then raise exception 'synthetic_relation_changed';end if;
 if (select count(*) from fmz6e10_private.windows where operator_id=u and status<>'cleaned')>=20 then raise exception 'synthetic_cleanup_required';end if;
 insert into fmz6e10_private.windows(operator_id,package_version,scenario,starts_at,ends_at)
 values(u,'6e10@1',d->>'scenario',(d->>'starts_at')::timestamptz,(d->>'ends_at')::timestamptz) returning * into w;
 insert into fmz6e10_private.participants(window_id,user_id,role) values(w.id,a_id,'a_member'),(w.id,t_id,'a_trainer'),(w.id,b_id,'b_member');
 f:=fmz6e10_private.fixture(w.scenario);
 insert into fmz6e10_private.workspaces(window_id,route,member_id,trainer_id,observations)
 values(w.id,'A',a_id,t_id,f->'observations') returning * into x;
 insert into fmz6e10_private.plans(workspace_id,version,content,hash) values(x.id,1,f->'plan',fmz6e10_private.sha(f->'plan'));
 insert into fmz6e10_private.workspaces(window_id,route,member_id,observations) values(w.id,'B',b_id,'[]');
 receipt:=jsonb_build_object('window',w.id,'status','prepared');
 elsif action in ('activate','revoke','cleanup') then
 perform fmz6e10_private.exact(d,'{}','{}');
 if q->'workspace'<>'null'::jsonb then raise exception 'synthetic_management_workspace_invalid';end if;
 if action='activate' then
 if w.status<>'prepared' or clock_timestamp()<w.starts_at or clock_timestamp()>=w.ends_at then raise exception using errcode='42501',message='synthetic_activation_denied';end if;
 -- Lock the fixed registry to serialize admission even across different operators/windows.
 perform pg_advisory_xact_lock(hashtextextended('fmz6e10:window-admission',0));
 if exists(select 1 from fmz6e10_private.participants a join fmz6e10_private.participants b on a.user_id=b.user_id
 join fmz6e10_private.windows v on v.id=b.window_id where a.window_id=w.id and b.window_id<>w.id and fmz6e10_private.live_window(v)) then
 raise exception using errcode='40001',message='synthetic_participant_window_conflict';end if;
 update fmz6e10_private.windows set status='active',feature_enabled=true where id=w.id;
 elsif action='revoke' then
 if w.status='cleaned' then raise exception 'synthetic_window_cleaned';end if;
 update fmz6e10_private.windows set status='revoked',feature_enabled=false where id=w.id;
 else
 if fmz6e10_private.live_window(w) then raise exception using errcode='42501',message='synthetic_revoke_before_cleanup';end if;
 if w.status<>'cleaned' then
 result:=jsonb_build_object('workspaces',(select count(*) from fmz6e10_private.workspaces where window_id=w.id),
 'audit_count',(select count(*) from fmz6e10_private.audit where window_id=w.id),
 'audit_hash',(select fmz6e10_private.sha(coalesce(jsonb_agg(to_jsonb(a) order by a.id),'[]')) from fmz6e10_private.audit a where window_id=w.id),
 'accounts_deleted',0);
 delete from fmz6e10_private.workspaces where window_id=w.id;
 delete from fmz6e10_private.participants where window_id=w.id;
 delete from fmz6e10_private.audit where window_id=w.id;
 delete from fmz6e10_private.requests where window_id=w.id;
 update fmz6e10_private.windows set status='cleaned',feature_enabled=false,cleanup=result where id=w.id;
 end if;
 end if;
 receipt:=jsonb_build_object('window',w.id,'status',case action when 'activate' then 'active' when 'revoke' then 'revoked' else 'cleaned' end);
 elsif action='source_append' then
 perform fmz6e10_private.exact(d,array['body','valid_from','valid_until'],array['body','valid_from','valid_until']);
 perform fmz6e10_private.validate_source(d->'body');
 from_at:=(d->>'valid_from')::timestamptz;until_at:=(d->>'valid_until')::timestamptz;
 if until_at>w.ends_at or until_at<=clock_timestamp() or from_at<w.created_at-interval '30 seconds' then raise exception 'synthetic_source_window_invalid';end if;
 select * into head from fmz6e10_private.source_heads where workspace_id=x.id;
 ver:=coalesce(head.version,0)+1;if ver>500 then raise exception 'synthetic_source_limit';end if;
 insert into fmz6e10_private.source_versions(workspace_id,version,source_id,trainer_id,body,hash,valid_from,valid_until)
 values(x.id,ver,coalesce((select source_id from fmz6e10_private.source_versions where workspace_id=x.id and version=head.version),gen_random_uuid()),u,
 d->'body',fmz6e10_private.sha(jsonb_build_object('workspace',x.id,'trainer',u,'version',ver,'body',d->'body','valid_from',from_at,'valid_until',until_at)),from_at,until_at);
 insert into fmz6e10_private.source_heads values(x.id,ver,'active') on conflict(workspace_id) do update set version=excluded.version,status='active';
 receipt:=jsonb_build_object('window',w.id,'workspace',x.id,'source_version',ver);
 elsif action='source_withdraw' then
 perform fmz6e10_private.exact(d,array['source_version'],array['source_version']);
 select * into head from fmz6e10_private.source_heads where workspace_id=x.id;
 if head.version is distinct from (d->>'source_version')::int or head.status<>'active' then raise exception using errcode='40001',message='synthetic_source_stale';end if;
 update fmz6e10_private.source_heads set status='withdrawn' where workspace_id=x.id;
 receipt:=jsonb_build_object('window',w.id,'workspace',x.id,'source_version',head.version,'status','withdrawn');
 elsif action in ('propose','restore','member_accept','member_reject','trainer_approve','trainer_reject','trainer_block','apply') then
 if action in ('member_reject','trainer_reject','trainer_block') then
 perform fmz6e10_private.exact(d,array['proposal','proposal_version'],array['proposal','proposal_version']);
 select * into p from fmz6e10_private.proposals where id=(d->>'proposal')::uuid and workspace_id=x.id for update;
 if p.id is null or p.version<>(d->>'proposal_version')::int or p.status not in ('member_pending','member_accepted','approved') then raise exception 'synthetic_proposal_status';end if;
 if action='member_reject' and p.status<>'member_pending' then raise exception 'synthetic_member_order';end if;
 if action in ('trainer_reject','trainer_block') and p.status<>'member_accepted' then raise exception 'synthetic_trainer_order';end if;
 update fmz6e10_private.proposals set status=case when action='trainer_block' then 'blocked' else 'rejected' end where id=p.id;
 receipt:=jsonb_build_object('window',w.id,'workspace',x.id,'proposal',p.id,'status',case when action='trainer_block' then 'blocked' else 'rejected' end);
 else
 if not x.consent or x.guard<>'clear' then raise exception using errcode='42501',message='synthetic_safety_or_consent_block';end if;
 select * into head from fmz6e10_private.source_heads where workspace_id=x.id;
 select * into s from fmz6e10_private.source_versions where workspace_id=x.id and version=head.version;
 if s.version is null or head.status<>'active' or s.valid_from>clock_timestamp() or s.valid_until<=clock_timestamp() or s.trainer_id<>x.trainer_id then
 raise exception using errcode='42501',message='synthetic_source_unavailable';end if;
 select * into plan from fmz6e10_private.plans where workspace_id=x.id and version=x.active_version;
 source_ref:=jsonb_build_object('id',s.source_id,'version',s.version,'hash',s.hash,'trainer',s.trainer_id,'workspace',x.id);
 if action in ('propose','restore') then
 if action='propose' then
 perform fmz6e10_private.exact(d,'{}','{}');
 result:=fmz6e10_private.calculate(s.body,plan.content,x.observations,x.active_version);
 else
 perform fmz6e10_private.exact(d,array['plan_version'],array['plan_version']);
 select * into oldplan from fmz6e10_private.plans where workspace_id=x.id and version=(d->>'plan_version')::int;
 if oldplan.version is null or oldplan.version=plan.version then raise exception 'synthetic_restore_invalid';end if;
 -- Validate historical target against current declared bounds without reinterpreting its origin.
 perform fmz6e10_private.validate_source(s.body);
 if exists(select 1 from jsonb_array_elements(oldplan.content->'exercises') e where
 (select count(*) from jsonb_array_elements(s.body->'rules') r where
 (r#>>'{selector,kind}'='exercise' and r#>>'{selector,id}'=e->>'id') or
 (r#>>'{selector,kind}'='type' and r#>>'{selector,id}'=e->>'type'))<>1) then raise exception 'synthetic_restore_rule_conflict';end if;
 if exists(select 1 from jsonb_array_elements(oldplan.content->'exercises') e
 cross join lateral jsonb_array_elements(e->'sets') st
 join jsonb_array_elements(s.body->'rules') r on (r#>>'{selector,kind}'='exercise' and r#>>'{selector,id}'=e->>'id')
 or (r#>>'{selector,kind}'='type' and r#>>'{selector,id}'=e->>'type')
 where r->>'unit'<>e->>'unit' or not (r->'available_weights')@>jsonb_build_array((st->>'load')::numeric)
 or (st->>'reps')::numeric not between (r->>'reps_min')::numeric and (r->>'reps_max')::numeric
 or jsonb_array_length(e->'sets') not between (r->>'sets_min')::int and (r->>'sets_max')::int) then raise exception 'synthetic_restore_outside_bounds';end if;
 restored:=jsonb_build_object('plan_version',oldplan.version,'plan_hash',oldplan.hash,'original_source_ref',oldplan.source_ref);
 result:=jsonb_build_object('allowed',true,'reason','restore_candidate','target',oldplan.content,'rows','[]'::jsonb);
 end if;
 select coalesce(max(version),0)+1 into ver from fmz6e10_private.proposals where workspace_id=x.id;
 if ver>500 then raise exception 'synthetic_proposal_limit';end if;
 insert into fmz6e10_private.proposals(workspace_id,version,source_version,source_hash,base_version,base_hash,target,target_hash,reflection,status,restored_from)
 values(x.id,ver,s.version,s.hash,plan.version,plan.hash,result->'target',
 case when result->'target'<>'null'::jsonb then fmz6e10_private.sha(result->'target') else null end,result,
 case when (result->>'allowed')::boolean then 'member_pending' else 'blocked' end,restored) returning * into p;
 receipt:=jsonb_build_object('window',w.id,'workspace',x.id,'proposal',p.id,'proposal_version',p.version,'source_version',s.version,'status',p.status);
 else
 perform fmz6e10_private.exact(d,array['proposal','proposal_version'],array['proposal','proposal_version']);
 select * into p from fmz6e10_private.proposals where id=(d->>'proposal')::uuid and workspace_id=x.id for update;
 if p.id is null or p.version<>(d->>'proposal_version')::int then raise exception using errcode='40001',message='synthetic_proposal_version_conflict';end if;
 if p.source_version<>s.version or p.source_hash<>s.hash or p.base_version<>plan.version or p.base_hash<>plan.hash then
 raise exception using errcode='40001',message='synthetic_source_or_plan_stale';end if;
 bound:=fmz6e10_private.sha(jsonb_build_object('proposal',p.id,'version',p.version,'source',source_ref,'base',plan.hash,'target',p.target_hash));
 if action='member_accept' then
 if p.status<>'member_pending' or p.target is null or p.target='null'::jsonb then raise exception 'synthetic_member_order';end if;
 update fmz6e10_private.proposals set status='member_accepted',member_actor=u,member_binding=bound where id=p.id;
 elsif action='trainer_approve' then
 if p.status<>'member_accepted' or p.member_actor<>x.member_id or p.member_binding<>bound then raise exception 'synthetic_trainer_order';end if;
 update fmz6e10_private.proposals set status='approved',trainer_actor=u,trainer_binding=bound where id=p.id;
 else
 if p.status<>'approved' or p.member_actor<>x.member_id or p.trainer_actor<>x.trainer_id
 or p.member_binding is distinct from bound or p.trainer_binding is distinct from bound
 or p.target_hash is distinct from fmz6e10_private.sha(p.target) then raise exception 'synthetic_apply_requires_exact_approvals';end if;
 insert into fmz6e10_private.plans(workspace_id,version,content,hash,source_ref,restored_from)
 values(x.id,plan.version+1,p.target,p.target_hash,source_ref,p.restored_from);
 update fmz6e10_private.workspaces set active_version=plan.version+1 where id=x.id;
 update fmz6e10_private.proposals set status='applied' where id=p.id;
 end if;
 receipt:=jsonb_build_object('window',w.id,'workspace',x.id,'proposal',p.id,'source_version',s.version,'plan_version',case when action='apply' then plan.version+1 else plan.version end);
 end if;
 end if;
 else raise exception using errcode='22023',message='synthetic_action_invalid';end if;
 if action not in ('prepare','activate','revoke','cleanup') and not fmz6e10_private.live_window(w) then
 raise exception using errcode='42501',message='synthetic_window_inactive';end if;
 if action in ('member_accept','trainer_approve','apply') and s.valid_until<=clock_timestamp() then
 raise exception using errcode='42501',message='synthetic_source_unavailable';end if;
 update fmz6e10_private.windows set revision=revision+1 where id=w.id returning revision into w.revision;
 receipt:=receipt||jsonb_build_object('revision',w.revision,'action',action,'synthetic_only',true,'automatic_actions_allowed',false);
 insert into fmz6e10_private.audit(window_id,actor,action,receipt) values(w.id,u,action,receipt);
 insert into fmz6e10_private.requests(actor,key,payload_hash,window_id,receipt) values(u,request_key,request_hash,w.id,receipt);
 return receipt;
end $f$;
commit;
