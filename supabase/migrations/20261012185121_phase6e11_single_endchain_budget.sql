-- One exact owner-authorized end-run, not a general increase. M43 is unchanged.
begin;
set local lock_timeout='1s';
set local statement_timeout='15s';
alter table fmz6e11_controller_private.runs drop constraint runs_command_count_check;
alter table fmz6e11_controller_private.runs add constraint runs_command_count_check
 check(command_count>=0 and command_count<=case
 when id='32321f17-07f1-4f3d-aa4b-3218bc7368a4'::uuid then 2226 else 128 end);

-- Retaining this one row prevents reuse of its exceptional allowance after
-- stop/cleanup. Ordinary controller rows keep their existing behavior.
create function fmz6e11_controller_private.single_endchain_receipt()
returns trigger language plpgsql security invoker
set search_path=pg_catalog,pg_temp as $f$
begin
 if TG_OP='DELETE' then
  if OLD.id='32321f17-07f1-4f3d-aa4b-3218bc7368a4'::uuid then
   raise exception using errcode='42501',message='single_endchain_receipt_retained';
  end if;
  return OLD;
 end if;
 if OLD.id='32321f17-07f1-4f3d-aa4b-3218bc7368a4'::uuid
    or NEW.id='32321f17-07f1-4f3d-aa4b-3218bc7368a4'::uuid then
  if (OLD.id,OLD.github_run,OLD.head_sha,OLD.manifest_sha,OLD.created_at,OLD.expires_at)
     is distinct from
     (NEW.id,NEW.github_run,NEW.head_sha,NEW.manifest_sha,NEW.created_at,NEW.expires_at)
     or (OLD.state in ('stopped','complete','closed') and NEW.state='running')
     or NEW.command_count<OLD.command_count then
   raise exception using errcode='42501',message='single_endchain_identity_immutable';
  end if;
 end if;
 return NEW;
end $f$;
revoke all on function fmz6e11_controller_private.single_endchain_receipt()
 from public,anon,authenticated,service_role;
create trigger single_endchain_receipt before update or delete
 on fmz6e11_controller_private.runs for each row
 execute function fmz6e11_controller_private.single_endchain_receipt();
commit;
