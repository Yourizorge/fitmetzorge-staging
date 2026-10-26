-- One additional owner-authorized run. M44 and its closed receipts are retained.
begin;
set local lock_timeout='1s';
set local statement_timeout='5s';
alter table fmz6e11_controller_private.runs drop constraint runs_command_count_check;
alter table fmz6e11_controller_private.runs add constraint runs_command_count_check
 check(command_count>=0 and command_count<=case
 when id='1c3bf7e7-bc78-40c5-9ac1-5ba3512ec66d'::uuid then 2237
 when id='6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'::uuid then 2349 else 128 end);

create function fmz6e11_controller_private.recovery_run_receipt()
returns trigger language plpgsql security invoker
set search_path=pg_catalog,pg_temp as $f$
begin
 if TG_OP='DELETE' then
  if OLD.id in ('4b0bb35f-02b5-4a9d-92d7-c29995691460'::uuid,
                '6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'::uuid) then
   raise exception using errcode='42501',message='recovery_run_receipt_retained';
  end if;
  return OLD;
 end if;
 if OLD.id='4b0bb35f-02b5-4a9d-92d7-c29995691460'::uuid
    or NEW.id='4b0bb35f-02b5-4a9d-92d7-c29995691460'::uuid then
  raise exception using errcode='42501',message='recovery_run_receipt_retained';
 end if;
 if OLD.id in ('4b0bb35f-02b5-4a9d-92d7-c29995691460'::uuid,
               '6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'::uuid)
    or NEW.id in ('4b0bb35f-02b5-4a9d-92d7-c29995691460'::uuid,
                  '6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'::uuid) then
  if (OLD.id,OLD.github_run,OLD.head_sha,OLD.manifest_sha,OLD.created_at,OLD.expires_at)
     is distinct from
     (NEW.id,NEW.github_run,NEW.head_sha,NEW.manifest_sha,NEW.created_at,NEW.expires_at)
     or (OLD.state in ('stopped','complete','closed') and NEW.state='running')
     or NEW.command_count<OLD.command_count then
   raise exception using errcode='42501',message='recovery_run_identity_immutable';
  end if;
 end if;
 return NEW;
end $f$;
revoke all on function fmz6e11_controller_private.recovery_run_receipt()
 from public,anon,authenticated,service_role;
create trigger recovery_run_receipt before update or delete
 on fmz6e11_controller_private.runs for each row
 execute function fmz6e11_controller_private.recovery_run_receipt();
commit;
