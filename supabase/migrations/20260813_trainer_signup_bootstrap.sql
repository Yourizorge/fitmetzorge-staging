-- FitMetZorge staging trainer signup bootstrap.
-- Run only in staging Supabase project: mokxyyullfhkfalopbzd
-- Safe rules:
-- - No DROP TABLE
-- - No DELETE
-- - No TRUNCATE
-- - No production data copy

create or replace function public.fmz_bootstrap_trainer_profile(
  p_user_id uuid,
  p_email text default null,
  p_name text default null
)
returns public.profiles
language plpgsql
security definer
set search_path = public, auth, pg_temp
as $$
declare
  v_email text := lower(trim(coalesce(p_email, '')));
  v_name text := nullif(trim(coalesce(p_name, '')), '');
  v_profile public.profiles;
begin
  if p_user_id is null then
    raise exception 'User id is verplicht.';
  end if;

  insert into public.profiles (
    id,
    role,
    name,
    email,
    trainer_id,
    client_id
  )
  values (
    p_user_id,
    'trainer',
    coalesce(v_name, nullif(split_part(v_email, '@', 1), ''), 'Trainer'),
    coalesce(v_email, ''),
    null,
    null
  )
  on conflict (id) do update
  set
    role = case
      when public.profiles.role = 'client' then public.profiles.role
      else 'trainer'
    end,
    name = coalesce(v_name, nullif(public.profiles.name, ''), nullif(split_part(v_email, '@', 1), ''), 'Trainer'),
    email = coalesce(nullif(v_email, ''), public.profiles.email),
    trainer_id = case
      when public.profiles.role = 'client' then public.profiles.trainer_id
      else null
    end,
    updated_at = now()
  returning * into v_profile;

  if v_profile.role = 'trainer' then
    insert into public.coach_workspaces (
      trainer_id,
      state,
      updated_at
    )
    values (
      p_user_id,
      '{}'::jsonb,
      now()
    )
    on conflict (trainer_id) do nothing;
  end if;

  return v_profile;
end;
$$;

create or replace function public.fmz_handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public, auth, pg_temp
as $$
declare
  v_metadata jsonb := coalesce(new.raw_user_meta_data, '{}'::jsonb);
  v_role text := coalesce(v_metadata ->> 'role', '');
  v_name text := coalesce(v_metadata ->> 'name', new.email, '');
begin
  if v_role = 'trainer' then
    perform public.fmz_bootstrap_trainer_profile(new.id, new.email, v_name);
  end if;

  return new;
end;
$$;

revoke all on function public.fmz_bootstrap_trainer_profile(uuid, text, text) from public;
revoke all on function public.fmz_handle_new_auth_user() from public;

grant execute on function public.fmz_bootstrap_trainer_profile(uuid, text, text) to service_role;

do $$
begin
  if not exists (
    select 1
    from pg_trigger
    where tgname = 'fmz_after_auth_user_insert_bootstrap'
  ) then
    create trigger fmz_after_auth_user_insert_bootstrap
    after insert on auth.users
    for each row execute function public.fmz_handle_new_auth_user();
  end if;
end $$;

-- Optional staging-only manual repair for existing test Auth users:
-- Run one statement per known trainer Auth user if they already exist without a profile:
-- select public.fmz_bootstrap_trainer_profile(
--   'AUTH_USER_UUID_HERE'::uuid,
--   'trainer-email@example.com',
--   'Trainer Naam'
-- );
