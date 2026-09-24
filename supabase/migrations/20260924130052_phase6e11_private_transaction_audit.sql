-- Additive, private and disabled by default. No existing table/function is changed.
begin;
set local lock_timeout='1s';
create schema fmz6e11_audit_private;
revoke all on schema fmz6e11_audit_private from public,anon,authenticated,service_role;
create table fmz6e11_audit_private.runs(
 id uuid primary key,enabled boolean not null default false,
 expires_at timestamptz not null,created_at timestamptz not null default clock_timestamp(),
 check(expires_at<=created_at+interval '10 minutes'));
create table fmz6e11_audit_private.actors(
 id uuid primary key,run_id uuid not null references fmz6e11_audit_private.runs,
 provenance text not null check(provenance='synthetic_fixture_only'));
create table fmz6e11_audit_private.actions(
 id uuid primary key,run_id uuid not null references fmz6e11_audit_private.runs,
 actor uuid not null references fmz6e11_audit_private.actors,workspace uuid not null,
 expected jsonb not null check(jsonb_typeof(expected)='array'),
 before_sha text not null check(before_sha~'^[0-9a-f]{64}$'),
 after_sha text check(after_sha~'^[0-9a-f]{64}$'),evidence_sha text check(evidence_sha~'^[0-9a-f]{64}$'),
 state text not null default 'before_saved' check(state in('before_saved','action_started','action_confirmed','pair_validated')),
 xid xid8,backend integer,started_at timestamptz,confirmed_at timestamptz,validated_at timestamptz);
create unique index one_live_audit_action on fmz6e11_audit_private.actions(run_id)
 where state in ('before_saved','action_started','action_confirmed');
create table fmz6e11_audit_private.bindings(
 xid xid8 primary key,backend integer not null,action_id uuid not null unique references fmz6e11_audit_private.actions);
create table fmz6e11_audit_private.relations(
 rel oid primary key,table_name text not null unique,pk_columns name[] not null,
 actor_column name,workspace_column name);
create table fmz6e11_audit_private.writes(
 action_id uuid not null references fmz6e11_audit_private.actions,
 ordinal integer not null,run_id uuid not null,xid xid8 not null,backend integer not null,
 actor uuid not null,workspace uuid not null,table_name text not null,
 operation text not null check(operation in('INSERT','UPDATE','DELETE')),
 old_key_sha text,new_key_sha text,at timestamptz not null default clock_timestamp(),
 primary key(action_id,ordinal),check(old_key_sha is not null or new_key_sha is not null));
create table fmz6e11_audit_private.fixture(
 id uuid primary key,actor_id uuid not null,workspace_id uuid not null,n integer not null,
 constraint synthetic_fixture_value check(n between 0 and 10));
create table fmz6e11_audit_private.forbidden_fixture(
 id uuid primary key,actor_id uuid not null,workspace_id uuid not null,n integer not null);

create function fmz6e11_audit_private.pk_hash(r uuid,t text,k jsonb) returns text
language sql immutable set search_path=pg_catalog,pg_temp as $f$
 select encode(sha256(convert_to(jsonb_build_array('fmz6e11-key-v1',r::text,t,k)::text,'UTF8')),'hex')
$f$;

-- Only configured key/ownership columns are projected; never serialize the whole row.
create function fmz6e11_audit_private.project_key(v anyelement,cols name[]) returns jsonb
language plpgsql set search_path=pg_catalog,pg_temp as $f$
declare q text;result jsonb;begin
 if cardinality(cols)<1 then raise exception using errcode='P0001',message='audit_key_missing';end if;
 select 'select jsonb_build_array('||string_agg(format('($1).%I',c),',' order by ord)||')'
 into q from unnest(cols) with ordinality u(c,ord);
 execute q into result using v;
 return result;
end $f$;

create function fmz6e11_audit_private.observe() returns trigger
language plpgsql security definer set search_path=pg_catalog,pg_temp as $f$
declare b fmz6e11_audit_private.bindings;a fmz6e11_audit_private.actions;
 r fmz6e11_audit_private.relations;oldh text;newh text;expected_count integer;actual_count integer;
begin
 select * into b from fmz6e11_audit_private.bindings
 where xid=pg_current_xact_id_if_assigned() and backend=pg_backend_pid();
 if not found then return null;end if;
 select * into a from fmz6e11_audit_private.actions where id=b.action_id;
 if a.state<>'action_started' or not exists(select 1 from fmz6e11_audit_private.runs
   where id=a.run_id and enabled and expires_at>clock_timestamp()) then
 raise exception using errcode='P0001',message='audit_binding_inactive';end if;
 select * into r from fmz6e11_audit_private.relations where rel=TG_RELID;
 if not found then raise exception using errcode='P0001',message='audit_relation_missing';end if;
 if TG_OP in ('UPDATE','DELETE') then
  oldh:=fmz6e11_audit_private.pk_hash(a.run_id,r.table_name,fmz6e11_audit_private.project_key(OLD,r.pk_columns));
  if r.actor_column is not null and fmz6e11_audit_private.project_key(OLD,array[r.actor_column])<>jsonb_build_array(a.actor) then
   raise exception using errcode='P0001',message='audit_actor_mismatch';end if;
  if r.workspace_column is not null and fmz6e11_audit_private.project_key(OLD,array[r.workspace_column])<>jsonb_build_array(a.workspace) then
   raise exception using errcode='P0001',message='audit_workspace_mismatch';end if;
 end if;
 if TG_OP in ('UPDATE','INSERT') then
  newh:=fmz6e11_audit_private.pk_hash(a.run_id,r.table_name,fmz6e11_audit_private.project_key(NEW,r.pk_columns));
  if r.actor_column is not null and fmz6e11_audit_private.project_key(NEW,array[r.actor_column])<>jsonb_build_array(a.actor) then
   raise exception using errcode='P0001',message='audit_actor_mismatch';end if;
  if r.workspace_column is not null and fmz6e11_audit_private.project_key(NEW,array[r.workspace_column])<>jsonb_build_array(a.workspace) then
   raise exception using errcode='P0001',message='audit_workspace_mismatch';end if;
 end if;
 select count(*) into expected_count from jsonb_array_elements(a.expected) e
 where e->>'table'=r.table_name and e->>'op'=TG_OP
 and e->>'old' is not distinct from oldh and e->>'new' is not distinct from newh;
 select count(*) into actual_count from fmz6e11_audit_private.writes w
 where w.action_id=a.id and w.table_name=r.table_name and w.operation=TG_OP
 and w.old_key_sha is not distinct from oldh and w.new_key_sha is not distinct from newh;
 if expected_count<=actual_count then
  raise exception using errcode='P0001',message='audit_unexpected_write';
 end if;
 insert into fmz6e11_audit_private.writes(action_id,ordinal,run_id,xid,backend,actor,workspace,table_name,operation,old_key_sha,new_key_sha)
 select a.id,coalesce(max(ordinal),0)+1,a.run_id,b.xid,b.backend,a.actor,a.workspace,r.table_name,TG_OP,oldh,newh
 from fmz6e11_audit_private.writes where action_id=a.id;
 return null;
end $f$;

create function fmz6e11_audit_private.attach(t regclass,ac name default null,wc name default null) returns void
language plpgsql set search_path=pg_catalog,pg_temp as $f$
declare keys name[];qualified text;begin
 if current_user<>'postgres' then raise exception using errcode='42501',message='audit_server_only';end if;
 select array_agg(a.attname order by k.ord) into keys from pg_index i
 cross join lateral unnest(i.indkey) with ordinality k(att,ord)
 join pg_attribute a on a.attrelid=i.indrelid and a.attnum=k.att
 where i.indrelid=t and i.indisprimary;
 if cardinality(keys) is null then raise exception using errcode='P0001',message='audit_pk_required';end if;
 select n.nspname||'.'||c.relname into qualified from pg_class c join pg_namespace n on n.oid=c.relnamespace where c.oid=t;
 insert into fmz6e11_audit_private.relations values(t,qualified,keys,ac,wc);
 execute format('create trigger fmz6e11_tx_observer after insert or update or delete on %s for each row execute function fmz6e11_audit_private.observe()',t);
end $f$;

create function fmz6e11_audit_private.start_action(p uuid) returns xid8
language plpgsql set search_path=pg_catalog,pg_temp as $f$
declare a fmz6e11_audit_private.actions;tx xid8:=pg_current_xact_id();begin
 if current_user<>'postgres' then raise exception using errcode='42501',message='audit_server_only';end if;
 select * into a from fmz6e11_audit_private.actions where id=p for update;
 if not found or a.state<>'before_saved' or not exists(select 1 from fmz6e11_audit_private.runs
 where id=a.run_id and enabled and expires_at>clock_timestamp()) then
 raise exception using errcode='P0001',message='audit_not_admitted';end if;
 if (select run_id from fmz6e11_audit_private.actors where id=a.actor) is distinct from a.run_id then
 raise exception using errcode='P0001',message='audit_actor_registry';end if;
 if exists(select 1 from fmz6e11_audit_private.relations r left join pg_trigger g
 on g.tgrelid=r.rel and g.tgname='fmz6e11_tx_observer'
 where g.oid is null or g.tgenabled<>'O' or g.tgfoid<>'fmz6e11_audit_private.observe()'::regprocedure) then
 raise exception using errcode='P0001',message='audit_trigger_coverage';end if;
 if jsonb_array_length(a.expected)>32 or exists(select 1 from jsonb_array_elements(a.expected) e
 where e->>'op' not in ('INSERT','UPDATE','DELETE') or not exists(select 1 from fmz6e11_audit_private.relations r where r.table_name=e->>'table')) then
 raise exception using errcode='P0001',message='audit_contract';end if;
 insert into fmz6e11_audit_private.bindings values(tx,pg_backend_pid(),p);
 update fmz6e11_audit_private.actions set state='action_started',xid=tx,backend=pg_backend_pid(),started_at=clock_timestamp() where id=p;
 return tx;
end $f$;

create function fmz6e11_audit_private.confirm_action(p uuid) returns jsonb
language plpgsql set search_path=pg_catalog,pg_temp as $f$
declare a fmz6e11_audit_private.actions;actual jsonb;expected jsonb;begin
 select * into a from fmz6e11_audit_private.actions where id=p for update;
 if a.state is distinct from 'action_started' or a.xid is distinct from pg_current_xact_id_if_assigned()
 or a.backend<>pg_backend_pid() then raise exception using errcode='P0001',message='audit_transaction_binding';end if;
 select coalesce(jsonb_agg(e order by e::text),'[]') into expected from jsonb_array_elements(a.expected) e;
 select coalesce(jsonb_agg(x.e order by x.e::text),'[]') into actual from
 (select jsonb_build_object('table',table_name,'op',operation,'old',old_key_sha,'new',new_key_sha) e
 from fmz6e11_audit_private.writes where action_id=p) x;
 if actual<>expected then raise exception using errcode='P0001',message='audit_missing_write';end if;
 update fmz6e11_audit_private.actions set state='action_confirmed',confirmed_at=clock_timestamp() where id=p;
 return jsonb_build_object('run_id',a.run_id,'action_id',p,'xid',a.xid::text,'backend',a.backend,
 'expected',expected,'actual',actual,'forbidden_linked_writes',0,'scope','registered_relations_only');
end $f$;

create function fmz6e11_audit_private.seal_pair(p uuid,after_hash text,evidence_hash text) returns void
language plpgsql set search_path=pg_catalog,pg_temp as $f$
begin
 if current_user<>'postgres' or after_hash is null or evidence_hash is null or after_hash!~'^[0-9a-f]{64}$' or evidence_hash!~'^[0-9a-f]{64}$' then
 raise exception using errcode='P0001',message='audit_pair_metadata';end if;
 update fmz6e11_audit_private.actions set state='pair_validated',after_sha=after_hash,
 evidence_sha=evidence_hash,validated_at=clock_timestamp() where id=p and state='action_confirmed'
 and xid<>pg_current_xact_id();
 if not found then raise exception using errcode='P0001',message='audit_pair_order';end if;
 update fmz6e11_audit_private.runs set enabled=false where id=(select run_id from fmz6e11_audit_private.actions where id=p);
end $f$;


create function fmz6e11_audit_private.fixture_probe(p uuid,row_id uuid) returns jsonb
language plpgsql set search_path=pg_catalog,pg_temp as $f$
declare a fmz6e11_audit_private.actions;begin
 perform fmz6e11_audit_private.start_action(p);
 select * into a from fmz6e11_audit_private.actions where id=p;
 if exists(select 1 from fmz6e11_audit_private.fixture where id=row_id) then
 raise exception using errcode='P0001',message='audit_fixture_exists';end if;
 insert into fmz6e11_audit_private.fixture values(row_id,a.actor,a.workspace,0);
 update fmz6e11_audit_private.fixture set n=1 where id=row_id;
 delete from fmz6e11_audit_private.fixture where id=row_id;
 return fmz6e11_audit_private.confirm_action(p);
end $f$;
select fmz6e11_audit_private.attach('fmz6e11_audit_private.fixture','actor_id','workspace_id');
select fmz6e11_audit_private.attach('fmz6e11_audit_private.forbidden_fixture','actor_id','workspace_id');

do $d$ declare t record;begin
 for t in select tablename from pg_tables where schemaname='fmz6e11_audit_private' loop
 execute format('alter table fmz6e11_audit_private.%I enable row level security',t.tablename);
 execute format('revoke all on fmz6e11_audit_private.%I from public,anon,authenticated,service_role',t.tablename);
 end loop;
end $d$;
revoke all on all functions in schema fmz6e11_audit_private from public,anon,authenticated,service_role;
commit;
