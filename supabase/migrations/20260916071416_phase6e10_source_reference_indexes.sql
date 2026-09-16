-- Only the new synthetic 6E-10 schema. Cover immutable-version foreign keys.
begin;
create index proposals_source_ref_idx on fmz6e10_private.proposals(workspace_id,source_version);
create index proposals_plan_ref_idx on fmz6e10_private.proposals(workspace_id,base_version);
create index source_heads_version_idx on fmz6e10_private.source_heads(workspace_id,version);
commit;
