-- 6E-10 synthetic trainer sources and managed windows. Staging only.
begin;
create schema fmz6e10_private;
revoke all on schema fmz6e10_private from public,anon,authenticated,service_role;
grant usage on schema fmz6e10_private to authenticated;

create table fmz6e10_private.config (
 id boolean primary key default true check(id), enabled boolean not null default false,
 proof_hash text check(proof_hash ~ '^[0-9a-f]{64}$')
);
insert into fmz6e10_private.config(id) values(true);
create table fmz6e10_private.identities (
 user_id uuid primary key references auth.users(id), role text not null unique
 check(role in ('a_member','a_trainer','b_member')), provenance_sha text not null
 check(provenance_sha ~ '^[0-9a-f]{64}$'), enabled boolean not null default true
);
create table fmz6e10_private.operators (
 user_id uuid primary key references fmz6e10_private.identities(user_id),
 enabled boolean not null default false
);
create table fmz6e10_private.windows (
 id uuid primary key default gen_random_uuid(), operator_id uuid not null references fmz6e10_private.operators(user_id),
 package_version text not null check(package_version='6e10@1'),
 scenario text not null check(scenario in ('kg','lb')), created_at timestamptz not null default clock_timestamp(),
 starts_at timestamptz not null, ends_at timestamptz not null,
 status text not null default 'prepared' check(status in ('prepared','active','revoked','cleaned')),
 revision bigint not null default 0, feature_enabled boolean not null default false,
 cleanup jsonb, check(ends_at>starts_at and ends_at<=starts_at+interval '24 hours'
 and starts_at>=created_at-interval '30 seconds' and ends_at<=created_at+interval '24 hours')
);
create index windows_operator_idx on fmz6e10_private.windows(operator_id);
create table fmz6e10_private.participants (
 window_id uuid not null references fmz6e10_private.windows(id),
 user_id uuid not null references fmz6e10_private.identities(user_id),
 role text not null check(role in ('a_member','a_trainer','b_member')),
 primary key(window_id,user_id),unique(window_id,role)
);
create index participants_user_idx on fmz6e10_private.participants(user_id);
create table fmz6e10_private.workspaces (
 id uuid primary key default gen_random_uuid(),window_id uuid not null references fmz6e10_private.windows(id),
 route text not null check(route in ('A','B')),member_id uuid not null references auth.users(id),
 trainer_id uuid references auth.users(id),active_version integer not null default 1,
 goal_ref text not null default 'syn-strength-goal@1', observations jsonb not null,
 consent boolean not null default true, guard text not null default 'clear'
 check(guard in ('clear','current','serious','recurring','unclassified','self_reported','missing')),
 unique(window_id,route),check((route='A' and trainer_id is not null) or (route='B' and trainer_id is null))
);
create index workspaces_member_idx on fmz6e10_private.workspaces(member_id);
create index workspaces_trainer_idx on fmz6e10_private.workspaces(trainer_id);
create table fmz6e10_private.source_versions (
 workspace_id uuid not null references fmz6e10_private.workspaces(id) on delete cascade,
 version integer not null check(version>0),source_id uuid not null,trainer_id uuid not null references auth.users(id),
 body jsonb not null, hash text not null check(hash ~ '^[0-9a-f]{64}$'),
 valid_from timestamptz not null,valid_until timestamptz not null,created_at timestamptz not null default clock_timestamp(),
 primary key(workspace_id,version),check(valid_until>valid_from)
);
create index source_trainer_idx on fmz6e10_private.source_versions(trainer_id);
create table fmz6e10_private.source_heads (
 workspace_id uuid primary key references fmz6e10_private.workspaces(id) on delete cascade,
 version integer not null, status text not null check(status in ('active','withdrawn')),
 foreign key(workspace_id,version) references fmz6e10_private.source_versions(workspace_id,version)
);
create table fmz6e10_private.plans (
 workspace_id uuid not null references fmz6e10_private.workspaces(id) on delete cascade,
 version integer not null, content jsonb not null,hash text not null,
 source_ref jsonb,restored_from jsonb,created_at timestamptz not null default clock_timestamp(),
 primary key(workspace_id,version)
);
create table fmz6e10_private.proposals (
 id uuid primary key default gen_random_uuid(),workspace_id uuid not null references fmz6e10_private.workspaces(id) on delete cascade,
 version integer not null,source_version integer not null,source_hash text not null,
 base_version integer not null,base_hash text not null,target jsonb,target_hash text,
 reflection jsonb not null,status text not null check(status in ('member_pending','member_accepted','approved','applied','rejected','blocked')),
 member_actor uuid references auth.users(id),trainer_actor uuid references auth.users(id),
 member_binding text,trainer_binding text,restored_from jsonb,
 created_at timestamptz not null default clock_timestamp(),unique(workspace_id,version),
 foreign key(workspace_id,source_version) references fmz6e10_private.source_versions(workspace_id,version),
 foreign key(workspace_id,base_version) references fmz6e10_private.plans(workspace_id,version)
);
create index proposals_member_idx on fmz6e10_private.proposals(member_actor);
create index proposals_trainer_idx on fmz6e10_private.proposals(trainer_actor);
create table fmz6e10_private.audit (
 id bigint generated always as identity primary key,window_id uuid not null references fmz6e10_private.windows(id),
 actor uuid not null references auth.users(id),action text not null,receipt jsonb not null,
 at timestamptz not null default clock_timestamp()
);
create index audit_window_idx on fmz6e10_private.audit(window_id);
create index audit_actor_idx on fmz6e10_private.audit(actor);
create table fmz6e10_private.requests (
 actor uuid not null references auth.users(id),key uuid not null,payload_hash text not null,
 window_id uuid not null references fmz6e10_private.windows(id),receipt jsonb not null,
 at timestamptz not null default clock_timestamp(),primary key(actor,key)
);
create index requests_window_idx on fmz6e10_private.requests(window_id);

do $d$ declare t record;begin
 for t in select tablename from pg_tables where schemaname='fmz6e10_private' loop
 execute format('alter table fmz6e10_private.%I enable row level security',t.tablename);
 execute format('revoke all on table fmz6e10_private.%I from public,anon,authenticated,service_role',t.tablename);
 end loop;
end $d$;
revoke all on all sequences in schema fmz6e10_private from public,anon,authenticated,service_role;

create function fmz6e10_private.sha(p jsonb) returns text language sql immutable
set search_path=pg_catalog,pg_temp as $f$ select encode(sha256(convert_to(p::text,'UTF8')),'hex') $f$;
create function fmz6e10_private.exact(p jsonb,allowed text[],required text[]) returns void
language plpgsql immutable set search_path=pg_catalog,pg_temp as $f$
begin
 if p is null or jsonb_typeof(p)<>'object' or exists(select 1 from jsonb_object_keys(p) k where not k=any(allowed))
 or exists(select 1 from unnest(required) k where not p?k) then
 raise exception using errcode='22023',message='synthetic_payload_invalid';end if;
end $f$;
create function fmz6e10_private.number(p jsonb,lo numeric,hi numeric,whole boolean default false) returns numeric
language plpgsql immutable set search_path=pg_catalog,pg_temp as $f$
declare v numeric;begin
 if p is null or jsonb_typeof(p)<>'number' then raise exception using errcode='22023',message='synthetic_number_missing_or_invalid';end if;
 v:=p::text::numeric;
 if v<lo or v>hi or (whole and v<>trunc(v)) or v<>trunc(v,6) then raise exception using errcode='22023',message='synthetic_number_range';end if;
 return v;
end $f$;
create function fmz6e10_private.validate_source(b jsonb) returns void
language plpgsql immutable set search_path=pg_catalog,pg_temp as $f$
declare r jsonb; e jsonb; v numeric; minimum numeric; maximum numeric; ids text[]:='{}';
begin
 perform fmz6e10_private.exact(b,array['goal_ref','comparable_plan_versions','minimum_sessions','note','rules'],array['goal_ref','comparable_plan_versions','minimum_sessions','note','rules']);
 if b->>'goal_ref' is distinct from 'syn-strength-goal@1' or jsonb_typeof(b->'note')<>'string' or length(b->>'note')>160
 or jsonb_typeof(b->'comparable_plan_versions')<>'array' or jsonb_array_length(b->'comparable_plan_versions') not between 1 and 20
 or jsonb_typeof(b->'rules')<>'array' or jsonb_array_length(b->'rules')>12 then
 raise exception using errcode='22023',message='synthetic_source_invalid';end if;
 perform fmz6e10_private.number(b->'minimum_sessions',1,10,true);
 for e in select value from jsonb_array_elements(b->'comparable_plan_versions') loop perform fmz6e10_private.number(e,1,500,true);end loop;
 for r in select value from jsonb_array_elements(b->'rules') loop
 perform fmz6e10_private.exact(r,array['id','selector','unit','reps_min','reps_max','reps_step','reset_reps','weight_step','available_weights','sets_min','sets_max','rir','rpe','priority','progression'],
 array['id','selector','unit','reps_min','reps_max','reps_step','reset_reps','weight_step','available_weights','sets_min','sets_max','rir','rpe','priority','progression']);
 if jsonb_typeof(r->'id')<>'string' or (r->>'id') !~ '^syn-[a-z0-9-]{1,40}$' or (r->>'id')=any(ids)
 or coalesce(r->>'unit','') not in ('kg','lb') or r->>'progression' is distinct from 'targets_then_reps_then_weight_else_hold' then
 raise exception using errcode='22023',message='synthetic_rule_invalid';end if;
 ids:=array_append(ids,r->>'id');
 perform fmz6e10_private.exact(r->'selector',array['kind','id'],array['kind','id']);
 if (r#>>'{selector,kind}'='exercise' and coalesce(r#>>'{selector,id}','') not in ('syn-squat','syn-press','syn-row'))
 or (r#>>'{selector,kind}'='type' and coalesce(r#>>'{selector,id}','') not in ('syn-lower','syn-push','syn-pull'))
 or coalesce(r#>>'{selector,kind}','') not in ('exercise','type') then raise exception using errcode='22023',message='synthetic_selector_invalid';end if;
 minimum:=fmz6e10_private.number(r->'reps_min',1,50,true);maximum:=fmz6e10_private.number(r->'reps_max',minimum,50,true);
 perform fmz6e10_private.number(r->'reps_step',1,10,true);perform fmz6e10_private.number(r->'reset_reps',minimum,maximum,true);
 perform fmz6e10_private.number(r->'weight_step',0.000001,1000);
 minimum:=fmz6e10_private.number(r->'sets_min',1,10,true);perform fmz6e10_private.number(r->'sets_max',minimum,10,true);
 if r->'priority'<>'null'::jsonb then perform fmz6e10_private.number(r->'priority',0,1000,true);end if;
 if jsonb_typeof(r->'available_weights')<>'array' or jsonb_array_length(r->'available_weights') not between 1 and 100 then raise exception using errcode='22023',message='synthetic_weights_missing';end if;
 minimum:=-1;
 for e in select value from jsonb_array_elements(r->'available_weights') loop
 v:=fmz6e10_private.number(e,0,10000);if v<=minimum then raise exception using errcode='22023',message='synthetic_weights_order';end if;minimum:=v;
 end loop;
 for e in select value from jsonb_each(jsonb_build_object('rir',r->'rir','rpe',r->'rpe')) loop
 perform fmz6e10_private.exact(e,array['required','min','max'],array['required','min','max']);
 if jsonb_typeof(e->'required')<>'boolean' then raise exception using errcode='22023',message='synthetic_effort_invalid';end if;
 minimum:=fmz6e10_private.number(e->'min',0,10);perform fmz6e10_private.number(e->'max',minimum,10);
 end loop;
 if (r#>>'{rpe,min}')::numeric<1 then raise exception using errcode='22023',message='synthetic_rpe_zero_invalid';end if;
 end loop;
end $f$;

create function fmz6e10_private.fixture(unit text) returns jsonb language plpgsql immutable
set search_path=pg_catalog,pg_temp as $f$
declare exercises jsonb:='[]';observed jsonb:='[]';rules jsonb:='[]';e text;typ text;sets jsonb;logs jsonb;i int;reps int;actual int;load numeric;step numeric;begin
 if unit not in ('kg','lb') then raise exception 'synthetic_unit';end if;
 load:=case when unit='kg' then 40 else 100 end;step:=case when unit='kg' then 2.5 else 5 end;
 foreach e in array array['syn-squat','syn-press','syn-row'] loop
 typ:=case e when 'syn-squat' then 'syn-lower' when 'syn-press' then 'syn-push' else 'syn-pull' end;
 reps:=case when e='syn-press' then 12 else 8 end;
 actual:=case when e='syn-row' then 6 else reps end;sets:='[]';logs:='[]';
 for i in 1..3 loop
 sets:=sets||jsonb_build_array(jsonb_build_object('index',i,'load',load,'reps',reps,'rir',null,'rpe',null));
 logs:=logs||jsonb_build_array(jsonb_build_object('index',i,'load',load,'reps',actual,'rir',case when e='syn-squat' then 0 else 2 end,'rpe',8));
 end loop;
 exercises:=exercises||jsonb_build_array(jsonb_build_object('id',e,'type',typ,'unit',unit,'sets',sets));
 observed:=observed||jsonb_build_array(jsonb_build_object('id',e,'unit',unit,'sets',logs));
 rules:=rules||jsonb_build_array(jsonb_build_object('id',e||'-rule','selector',jsonb_build_object('kind','exercise','id',e),
 'unit',unit,'reps_min',8,'reps_max',12,'reps_step',1,'reset_reps',8,'weight_step',step,'available_weights',jsonb_build_array(load,load+step,load+step*2),
 'sets_min',3,'sets_max',3,'rir',jsonb_build_object('required',false,'min',0,'max',10),'rpe',jsonb_build_object('required',false,'min',1,'max',10),
 'priority',null,'progression','targets_then_reps_then_weight_else_hold'));
 end loop;
 return jsonb_build_object('plan',jsonb_build_object('goal_ref','syn-strength-goal@1','exercises',exercises),
 'observations',jsonb_build_array(jsonb_build_object('snapshot','syn-session@1','plan_version',1,'goal_ref','syn-strength-goal@1','completed',true,'exercises',observed)),
 'source_template',jsonb_build_object('goal_ref','syn-strength-goal@1','comparable_plan_versions',jsonb_build_array(1),'minimum_sessions',1,'note','Synthetische trainerregels voor deze oefeningenset.','rules',rules));
end $f$;

create function fmz6e10_private.validate_history(p jsonb,logs jsonb) returns void
language plpgsql immutable set search_path=pg_catalog,pg_temp as $f$
declare doc jsonb;e jsonb;st jsonb;seen text[];snapshots text[]:='{}';idx int;historical boolean;begin
 perform fmz6e10_private.exact(p,array['goal_ref','exercises'],array['goal_ref','exercises']);
 if jsonb_typeof(logs) is distinct from 'array' or jsonb_array_length(logs) not between 1 and 10 then raise exception 'synthetic_history_invalid';end if;
 for doc in select value from jsonb_array_elements(jsonb_build_array(p)||logs) loop
 historical:=doc is distinct from p;
 if historical then
 perform fmz6e10_private.exact(doc,array['snapshot','plan_version','goal_ref','completed','exercises'],array['snapshot','plan_version','goal_ref','completed','exercises']);
 if coalesce(doc->>'snapshot','') !~ '^syn-[a-z0-9@-]{1,60}$' or doc->>'snapshot'=any(snapshots)
 or doc->'completed' is distinct from 'true'::jsonb then raise exception 'synthetic_history_invalid';end if;
 snapshots:=array_append(snapshots,doc->>'snapshot');perform fmz6e10_private.number(doc->'plan_version',1,500,true);
 end if;
 if jsonb_typeof(doc->'goal_ref') is distinct from 'string' or jsonb_typeof(doc->'exercises') is distinct from 'array'
 or jsonb_array_length(doc->'exercises') not between 1 and 3 then raise exception 'synthetic_history_invalid';end if;
 seen:='{}';
 for e in select value from jsonb_array_elements(doc->'exercises') loop
 perform fmz6e10_private.exact(e,case when historical then array['id','unit','sets'] else array['id','type','unit','sets'] end,
 case when historical then array['id','unit','sets'] else array['id','type','unit','sets'] end);
 if coalesce(e->>'id','') not in ('syn-squat','syn-press','syn-row') or e->>'id'=any(seen)
 or coalesce(e->>'unit','') not in ('kg','lb') or jsonb_typeof(e->'sets') is distinct from 'array'
 or jsonb_array_length(e->'sets') not between 1 and 10 then raise exception 'synthetic_history_invalid';end if;
 if not historical and e->>'type' is distinct from (case e->>'id' when 'syn-squat' then 'syn-lower' when 'syn-press' then 'syn-push' else 'syn-pull' end) then raise exception 'synthetic_exercise_type_invalid';end if;
 seen:=array_append(seen,e->>'id');idx:=0;
 for st in select value from jsonb_array_elements(e->'sets') loop
 perform fmz6e10_private.exact(st,array['index','load','reps','rir','rpe'],array['index','load','reps']);idx:=idx+1;
 if fmz6e10_private.number(st->'index',1,10,true)<>idx then raise exception 'synthetic_set_binding_invalid';end if;
 perform fmz6e10_private.number(st->'load',0,10000);perform fmz6e10_private.number(st->'reps',case when historical then 0 else 1 end,100,true);
 if st?'rir' and st->'rir'<>'null'::jsonb then perform fmz6e10_private.number(st->'rir',0,10);end if;
 if st?'rpe' and st->'rpe'<>'null'::jsonb then perform fmz6e10_private.number(st->'rpe',1,10);end if;
 end loop;
 end loop;
 end loop;
end $f$;

create function fmz6e10_private.calculate(b jsonb,p jsonb,logs jsonb,plan_version int) returns jsonb
language plpgsql immutable set search_path=pg_catalog,pg_temp as $f$
declare e jsonb;r jsonb;candidates jsonb;planned jsonb;actual jsonb;session jsonb;observed jsonb;
rows jsonb:='[]';next_exercises jsonb:='[]';target_sets jsonb;reason text;blocked text;ok boolean;
n int;reps numeric;load numeric;new_reps numeric;new_load numeric;idx int;priority numeric;count_valid int;effort text;
begin
 perform fmz6e10_private.validate_source(b);
 begin
 perform fmz6e10_private.validate_history(p,logs);
 exception when others then
 return jsonb_build_object('allowed',false,'reason','history_invalid_or_incomplete','rows','[]'::jsonb,'target',null);
 end;
 if p->>'goal_ref'<>b->>'goal_ref' or not (b->'comparable_plan_versions')@>jsonb_build_array(plan_version)
 or jsonb_typeof(logs)<>'array' or jsonb_array_length(logs)<(b->>'minimum_sessions')::int then
 return jsonb_build_object('allowed',false,'reason','source_or_history_missing','rows','[]'::jsonb,'target',null);end if;
 for e in select value from jsonb_array_elements(p->'exercises') loop
 blocked:=null;r:=null;reason:='hold';ok:=true;
 select coalesce(jsonb_agg(value),'[]') into candidates from jsonb_array_elements(b->'rules')
 where (value#>>'{selector,kind}'='exercise' and value#>>'{selector,id}'=e->>'id')
 or (value#>>'{selector,kind}'='type' and value#>>'{selector,id}'=e->>'type');
 if jsonb_array_length(candidates)=0 then blocked:='rule_missing';
 elsif jsonb_array_length(candidates)>1 then
 if exists(select 1 from jsonb_array_elements(candidates) x where x->'priority'='null') then blocked:='W1_ambiguous_rules';
 else
 select min((x->>'priority')::numeric) into priority from jsonb_array_elements(candidates) x;
 if (select count(*) from jsonb_array_elements(candidates) x where (x->>'priority')::numeric=priority)<>1 then blocked:='W1_ambiguous_rules';
 else select x into r from jsonb_array_elements(candidates) x where (x->>'priority')::numeric=priority;end if;
 end if;
 else r:=candidates->0;end if;
 if blocked is null then
 if r->>'unit'<>e->>'unit' then blocked:='unit_mismatch';
 elsif jsonb_typeof(e->'sets')<>'array' or jsonb_array_length(e->'sets') not between (r->>'sets_min')::int and (r->>'sets_max')::int then blocked:='sets_incomplete';
 else
 reps:=fmz6e10_private.number(e#>'{sets,0,reps}',1,50,true);load:=fmz6e10_private.number(e#>'{sets,0,load}',0,10000);
 if reps not between (r->>'reps_min')::numeric and (r->>'reps_max')::numeric or not (r->'available_weights')@>jsonb_build_array(load) then blocked:='plan_outside_bounds';end if;
 count_valid:=0;
 for session in select value from jsonb_array_elements(logs) loop
 if session->>'goal_ref'<>b->>'goal_ref' or session->'completed'<>'true'::jsonb
 or not (b->'comparable_plan_versions')@>jsonb_build_array((session->>'plan_version')::int) then blocked:='history_not_comparable';exit;end if;
 if (select count(*) from jsonb_array_elements(session->'exercises') x where x->>'id'=e->>'id')<>1 then blocked:='exercise_binding_invalid';exit;end if;
 select x into observed from jsonb_array_elements(session->'exercises') x where x->>'id'=e->>'id';
 if observed->>'unit'<>e->>'unit' or jsonb_array_length(observed->'sets')<>jsonb_array_length(e->'sets') then blocked:='sets_incomplete';exit;end if;
 idx:=0;
 for planned in select value from jsonb_array_elements(e->'sets') loop
 actual:=observed->'sets'->idx;idx:=idx+1;
 if planned->>'index'<>idx::text or actual->>'index'<>idx::text or planned->'reps'<>to_jsonb(reps) or planned->'load'<>to_jsonb(load) then blocked:='set_binding_or_range_invalid';exit;end if;
 if jsonb_typeof(actual->'reps')<>'number' or jsonb_typeof(actual->'load')<>'number' then blocked:='sets_incomplete';exit;end if;
 if fmz6e10_private.number(actual->'load',0,10000)<>load then blocked:='history_not_comparable';exit;end if;
 if fmz6e10_private.number(actual->'reps',0,100,true)<reps then ok:=false;end if;
 foreach effort in array array['rir','rpe'] loop
 if not actual?effort or actual->effort='null'::jsonb then
 if (r#>>array[effort,'required'])::boolean then blocked:='effort_missing';end if;
 else
 n:=case when effort='rpe' then 1 else 0 end;
 perform fmz6e10_private.number(actual->effort,n,10);
 if (actual->>effort)::numeric not between (r#>>array[effort,'min'])::numeric and (r#>>array[effort,'max'])::numeric then ok:=false;end if;
 end if;
 end loop;
 end loop;count_valid:=count_valid+1;
 end loop;
 if count_valid<(b->>'minimum_sessions')::int then blocked:=coalesce(blocked,'history_incomplete');end if;
 new_reps:=reps;new_load:=load;
 if blocked is null and ok then
 if reps<(r->>'reps_max')::numeric then
 new_reps:=reps+(r->>'reps_step')::numeric;reason:='reps';
 if new_reps>(r->>'reps_max')::numeric then blocked:='full_reps_step_does_not_fit';end if;
 else
 new_load:=load+(r->>'weight_step')::numeric;new_reps:=(r->>'reset_reps')::numeric;reason:='weight';
 if not (r->'available_weights')@>jsonb_build_array(new_load) then blocked:='W2_full_weight_step_does_not_fit';end if;
 end if;
 end if;
 end if;
 end if;
 if blocked is null then
 target_sets:='[]';
 for planned in select value from jsonb_array_elements(e->'sets') loop
 target_sets:=target_sets||jsonb_build_array(planned||jsonb_build_object('load',new_load,'reps',new_reps));
 end loop;
 next_exercises:=next_exercises||jsonb_build_array(e||jsonb_build_object('sets',target_sets));
 end if;
 rows:=rows||jsonb_build_array(jsonb_build_object('exercise',e->>'id','current',e->'sets','kind',case when blocked is null then reason else 'blocked' end,
 'reason',coalesce(blocked,reason),'rule_id',r->>'id','weight_step',r->'weight_step','unit',e->>'unit',
 'attempted_load',case when blocked='W2_full_weight_step_does_not_fit' then new_load else null end,
 'available_weights',r->'available_weights','next',case when blocked is null then target_sets else null end));
 end loop;
 if exists(select 1 from jsonb_array_elements(rows) x where x->>'kind'='blocked') then return jsonb_build_object('allowed',false,'reason','blocked','rows',rows,'target',null);end if;
 if not exists(select 1 from jsonb_array_elements(rows) x where x->>'kind' in ('reps','weight')) then return jsonb_build_object('allowed',false,'reason','hold_only','rows',rows,'target',null);end if;
 return jsonb_build_object('allowed',true,'reason','candidate_only','rows',rows,'target',p||jsonb_build_object('exercises',next_exercises));
end $f$;

create function fmz6e10_private.principal() returns jsonb language plpgsql security definer
set search_path=pg_catalog,pg_temp as $f$
declare u uuid:=auth.uid();r fmz6e10_private.identities;p public.profiles;h jsonb;c fmz6e10_private.config;
begin
 select * into c from fmz6e10_private.config where id for share;
 h:=coalesce(nullif(current_setting('request.headers',true),''),'{}')::jsonb;
 if not c.enabled or c.proof_hash is null or c.proof_hash is distinct from encode(sha256(convert_to(coalesce(h->>'x-fmz6e10-proof',''),'UTF8')),'hex') then
 raise exception using errcode='42501',message='synthetic_disabled_or_proof_required';end if;
 if u is null or not exists(select 1 from auth.sessions s where s.user_id=u
 and s.id=(coalesce(nullif(current_setting('request.jwt.claims',true),''),'{}')::jsonb->>'session_id')::uuid
 and (s.not_after is null or s.not_after>clock_timestamp())) then raise exception using errcode='42501',message='synthetic_session_required';end if;
 select * into r from fmz6e10_private.identities where user_id=u and enabled for share;
 if not found then raise exception using errcode='42501',message='synthetic_identity_required';end if;
 select * into p from public.profiles where id=u for share;
 if not found or p.role is distinct from (case when r.role='a_trainer' then 'trainer' else 'client' end)
 or not exists(select 1 from auth.users a where a.id=u and a.email=case r.role
 when 'a_trainer' then 'zorgeyouri+6e9-a-trainer@gmail.com' when 'a_member' then 'zorgeyouri+6e9-a-lid@gmail.com' else 'zorgeyouri+6e9-b-lid@gmail.com' end)
 then raise exception using errcode='42501',message='synthetic_identity_changed';end if;
 return jsonb_build_object('uid',u,'role',r.role,'operator',r.role='a_trainer' and exists(select 1 from fmz6e10_private.operators o where o.user_id=u and o.enabled));
end $f$;
create function fmz6e10_private.window_at(w fmz6e10_private.windows,at_time timestamptz) returns boolean language sql immutable
set search_path=pg_catalog,pg_temp as $f$
 select w.status='active' and w.feature_enabled and w.starts_at<=at_time and at_time<w.ends_at
$f$;
create function fmz6e10_private.live_window(w fmz6e10_private.windows) returns boolean language sql volatile
set search_path=pg_catalog,pg_temp as $f$
 select fmz6e10_private.window_at(w,clock_timestamp())
$f$;
create function fmz6e10_private.workspace_guard(w fmz6e10_private.windows,x fmz6e10_private.workspaces,u uuid) returns text
language plpgsql set search_path=pg_catalog,pg_temp as $f$
declare acting_role text;member public.profiles;begin
 if not fmz6e10_private.live_window(w) then raise exception using errcode='42501',message='synthetic_window_inactive';end if;
 select p.role into acting_role from fmz6e10_private.participants p join fmz6e10_private.identities i on i.user_id=p.user_id and i.role=p.role and i.enabled
 where p.window_id=w.id and p.user_id=u;
 if acting_role is null or x.window_id<>w.id or (u<>x.member_id and u is distinct from x.trainer_id)
 then raise exception using errcode='42501',message='synthetic_workspace_denied';end if;
 perform 1 from public.profiles where id in (x.member_id,x.trainer_id) order by id for share;
 select * into member from public.profiles where id=x.member_id;
 if member.role is distinct from 'client' or
 (x.route='A' and (member.trainer_id is distinct from x.trainer_id or not exists(select 1 from public.profiles where id=x.trainer_id and role='trainer')))
 or (x.route='B' and (member.trainer_id is not null or x.trainer_id is not null or acting_role<>'b_member'))
 then raise exception using errcode='42501',message='synthetic_relation_changed';end if;
 return acting_role;
end $f$;
create function fmz6e10_private.immutable() returns trigger language plpgsql
set search_path=pg_catalog,pg_temp as $f$begin raise exception using errcode='42501',message='synthetic_version_immutable';end$f$;
create trigger source_immutable before update on fmz6e10_private.source_versions for each row execute function fmz6e10_private.immutable();
create trigger plan_immutable before update on fmz6e10_private.plans for each row execute function fmz6e10_private.immutable();

create function fmz6e10_private.read_workspace(w fmz6e10_private.windows,x fmz6e10_private.workspaces,u uuid) returns jsonb
language plpgsql set search_path=pg_catalog,pg_temp as $f$
declare role text;head fmz6e10_private.source_heads;begin
 role:=fmz6e10_private.workspace_guard(w,x,u);
 select * into head from fmz6e10_private.source_heads where workspace_id=x.id;
 return jsonb_build_object('window',jsonb_build_object('id',w.id,'revision',w.revision,'starts_at',w.starts_at,'ends_at',w.ends_at),
 'workspace',x.id,'route',x.route,'role',role,'active_version',x.active_version,'guard',x.guard,'consent',x.consent,
 'goal_ref',x.goal_ref,'observations',case when x.route='A' then x.observations else null end,
 'source_template',case when x.route='A' and role='a_trainer' then fmz6e10_private.fixture(w.scenario)->'source_template' else null end,
 'sources',case when x.route='B' then '[]'::jsonb else
 coalesce((select jsonb_agg(to_jsonb(s)||jsonb_build_object('status',case
 when exists(select 1 from fmz6e10_private.audit a where a.window_id=w.id and a.action='source_withdraw'
 and a.receipt->>'workspace'=x.id::text and a.receipt->>'source_version'=s.version::text) then 'withdrawn'
 when s.valid_until<=clock_timestamp() then 'expired' when s.valid_from>clock_timestamp() then 'not_yet_valid'
 when s.version is distinct from head.version then 'replaced' else head.status end) order by s.version)
 from fmz6e10_private.source_versions s where s.workspace_id=x.id),'[]') end,
 'plans',case when x.route='B' then '[]'::jsonb else coalesce((select jsonb_agg(to_jsonb(p) order by p.version) from fmz6e10_private.plans p where p.workspace_id=x.id),'[]') end,
 'proposals',case when x.route='B' then '[]'::jsonb else coalesce((select jsonb_agg(to_jsonb(p)||jsonb_build_object('stale',
 p.source_version is distinct from head.version or head.status is distinct from 'active' or p.base_version<>x.active_version
 or not exists(select 1 from fmz6e10_private.source_versions s where s.workspace_id=x.id and s.version=p.source_version and s.hash=p.source_hash and s.valid_from<=clock_timestamp() and clock_timestamp()<s.valid_until)
 ) order by p.version) from fmz6e10_private.proposals p where p.workspace_id=x.id),'[]') end,
 'audit',case when x.route='B' then '[]'::jsonb else coalesce((select jsonb_agg(to_jsonb(a) order by a.id) from fmz6e10_private.audit a
 where a.window_id=w.id and a.receipt->>'workspace'=x.id::text),'[]') end,
 'synthetic_only',true,'automatic_actions_allowed',false,'physical_advice_authorized',false);
end $f$;

create function fmz6e10_private.call(q jsonb) returns jsonb language plpgsql security definer
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
revoke all on all functions in schema fmz6e10_private from public,anon,authenticated,service_role;
grant execute on function fmz6e10_private.call(jsonb) to authenticated;
create function public.fmz6e10_call(p jsonb) returns jsonb language sql security invoker
set search_path=pg_catalog,pg_temp as $f$select fmz6e10_private.call(p)$f$;
revoke all on function public.fmz6e10_call(jsonb) from public,anon,authenticated,service_role;
grant execute on function public.fmz6e10_call(jsonb) to authenticated;
commit;
