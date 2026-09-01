-- FitMetZorge Phase 5 metric/imperial preference constraint correction.
-- STAGING target: mokxyyullfhkfalopbzd.

begin;

do $guard$
begin
  if to_regclass('public.user_settings') is null then
    raise exception 'public.user_settings is required';
  end if;

  if not exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'user_settings'
      and column_name = 'unit_system'
      and data_type = 'text'
      and is_nullable = 'NO'
  ) then
    raise exception 'public.user_settings.unit_system contract mismatch';
  end if;

  if exists (
    select 1
    from public.user_settings
    where unit_system not in ('metric', 'imperial')
  ) then
    raise exception 'unsupported existing unit_system value';
  end if;
end
$guard$;

alter table public.user_settings
  drop constraint if exists user_settings_unit_system_check;

alter table public.user_settings
  add constraint user_settings_unit_system_check
  check (unit_system in ('metric', 'imperial')) not valid;

alter table public.user_settings
  validate constraint user_settings_unit_system_check;

commit;
