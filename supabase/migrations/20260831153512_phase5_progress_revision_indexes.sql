-- Phase 5 Progress: cover immutable revision foreign keys.
begin;

create index if not exists weight_logs_supersedes_idx
  on public.weight_logs (supersedes_weight_log_id)
  where supersedes_weight_log_id is not null;

create index if not exists body_measurements_supersedes_idx
  on public.body_measurements (supersedes_body_measurement_id)
  where supersedes_body_measurement_id is not null;

commit;
