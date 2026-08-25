"""Render the hash-gated psql importer and read-only live verifier."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    catalog = root / "supabase" / "catalog" / "20260825_phase4_off_catalog"
    manifest_path = catalog / "20260825_phase4_off_artifact_manifest.json"
    release_path = catalog / "20260825_phase4_off_release.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    release = json.loads(release_path.read_text(encoding="utf-8"))
    expected_names = manifest["counts"]["names"]
    release_id = release["id"]
    product_sha = release["product_manifest_sha256"]
    names_sha = release["names_manifest_sha256"]
    normalized_sha = release["normalized_artifact_sha256"]
    release_provenance = canonical_json(release["provenance"])
    release_metadata = canonical_json(release["metadata"])

    importer_path = root / "supabase" / "imports" / "20260825_phase4_off_catalog_import.psql"
    importer_path.parent.mkdir(parents=True, exist_ok=True)
    importer = f"""-- FitMetZorge Phase 4 Slice 4F - 24,458 Dutch OFF products
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Execute from the repository root with psql after byte-exact hash review.
-- One transaction, fail-on-drift, replay-safe. No remote calls or frozen-domain writes.

\\set ON_ERROR_STOP on
\\echo 'FitMetZorge Slice 4F OFF catalog import: hash-gated files must already be verified.'

begin;

select pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('fmz_phase4_off_catalog_import:{release_id}', 0)
);

create temporary table fmz_off_products_stage
(like public.nutrition_off_products including defaults)
on commit drop;

create temporary table fmz_off_names_stage
(like public.nutrition_off_product_names including defaults)
on commit drop;

\\copy fmz_off_products_stage (id,release_id,source_provider,off_code,barcode_original,normalized_gtin14,provider_identity_name,product_name,product_name_nl,generic_name,brand,normalized_brand,quantity_text,serving_size_text,nutrition_basis,energy_kcal_100,protein_grams_100,carbohydrate_grams_100,fat_grams_100,fiber_grams_100,countries_tags,is_netherlands_associated,off_revision,source_updated_at,source_checksum,provenance,license_code,license_url,attribution_text,image_reference_url,image_license_code,image_attribution,completeness,quality_status,lifecycle_status,imported_at,refreshed_at,metadata,created_at,updated_at,archived_at) from 'supabase/catalog/20260825_phase4_off_catalog/20260825_phase4_off_products.csv' with (format csv, header true, encoding 'UTF8');

\\copy fmz_off_names_stage (id,product_id,language_code,name_type,name,normalized_name,is_preferred,source_provider,source_revision,license_code,provenance,quality_status,lifecycle_status,metadata,created_at,updated_at,archived_at) from 'supabase/catalog/20260825_phase4_off_catalog/20260825_phase4_off_product_names.csv' with (format csv, header true, encoding 'UTF8');

create unique index fmz_off_products_stage_id_idx on fmz_off_products_stage (id);
create unique index fmz_off_products_stage_gtin_idx on fmz_off_products_stage (normalized_gtin14);
create unique index fmz_off_products_stage_identity_idx on fmz_off_products_stage (provider_identity_name);
create unique index fmz_off_names_stage_id_idx on fmz_off_names_stage (id);
create index fmz_off_names_stage_product_idx on fmz_off_names_stage (product_id);
create index fmz_off_names_stage_identity_idx
  on fmz_off_names_stage (product_id, language_code, name_type, normalized_name);
analyze fmz_off_products_stage;
analyze fmz_off_names_stage;

do $fmz_validate$
declare
  v_product_count bigint;
  v_name_count bigint;
begin
  select count(*) into v_product_count from fmz_off_products_stage;
  select count(*) into v_name_count from fmz_off_names_stage;
  if v_product_count <> 24458 then
    raise exception 'OFF product artifact count drift: %', v_product_count;
  end if;
  if v_name_count <> {expected_names} then
    raise exception 'OFF name artifact count drift: %', v_name_count;
  end if;
  if (select count(distinct id) from fmz_off_products_stage) <> 24458
     or (select count(distinct normalized_gtin14) from fmz_off_products_stage) <> 24458
     or (select count(distinct provider_identity_name) from fmz_off_products_stage) <> 24458 then
    raise exception 'OFF product identity drift';
  end if;
  if exists (
    select 1 from fmz_off_products_stage p
    where p.release_id <> {sql_literal(release_id)}::uuid
       or p.source_provider <> 'open_food_facts'
       or p.off_revision <> {sql_literal(release['source_revision'])}
       or p.normalized_gtin14 <> public.fmz_phase4_normalize_gtin14(p.barcode_original)
       or p.provider_identity_name <> 'open_food_facts:' || p.normalized_gtin14
       or p.id <> public.fmz_phase4_provider_candidate_uuid_v5(p.provider_identity_name)
       or p.quality_status <> 'complete'
       or p.lifecycle_status <> 'active'
       or p.nutrition_basis not in ('per_100_g', 'per_100_ml')
       or p.energy_kcal_100 is null or p.energy_kcal_100 not between 0 and 900
       or p.protein_grams_100 is null or p.protein_grams_100 not between 0 and 100
       or p.carbohydrate_grams_100 is null or p.carbohydrate_grams_100 not between 0 and 100
       or p.fat_grams_100 is null or p.fat_grams_100 not between 0 and 100
       or (p.fiber_grams_100 is not null and p.fiber_grams_100 not between 0 and 100)
       or not p.is_netherlands_associated
       or not (p.countries_tags @> array['en:netherlands']::text[])
       or p.license_code <> 'ODbL-1.0'
       or p.image_reference_url is not null
       or p.image_license_code is not null
       or p.image_attribution is not null
  ) then
    raise exception 'OFF product validation drift';
  end if;
  if (select count(*) from fmz_off_products_stage where nutrition_basis = 'per_100_g') <> 20355
     or (select count(*) from fmz_off_products_stage where nutrition_basis = 'per_100_ml') <> 4103 then
    raise exception 'OFF basis split drift';
  end if;
  if (select count(distinct id) from fmz_off_names_stage) <> {expected_names}
     or exists (
       select 1 from fmz_off_names_stage n
       left join fmz_off_products_stage p on p.id = n.product_id
       where p.id is null
          or n.source_provider <> 'open_food_facts'
          or n.source_revision <> {sql_literal(release['source_revision'])}
          or n.license_code <> 'ODbL-1.0'
          or n.normalized_name <> public.fmz_phase4_normalize_catalog_text(n.name)
          or n.quality_status <> 'complete'
          or n.lifecycle_status <> 'active'
     ) then
    raise exception 'OFF name validation drift';
  end if;
  if exists (
    select 1 from fmz_off_names_stage
    where lifecycle_status = 'active'
    group by product_id, language_code, name_type, normalized_name
    having count(*) > 1
  ) or exists (
    select 1 from fmz_off_names_stage
    where lifecycle_status = 'active' and quality_status in ('complete', 'reviewed') and is_preferred
    group by product_id, language_code
    having count(*) > 1
  ) then
    raise exception 'OFF name uniqueness drift';
  end if;
end
$fmz_validate$;

do $fmz_release$
begin
  if exists (
    select 1 from public.nutrition_off_catalog_releases r
    where r.source_provider = 'open_food_facts' and r.id <> {sql_literal(release_id)}::uuid
  ) then
    raise exception 'Unexpected OFF predecessor/current release; new reviewed artifact required';
  end if;

  if not exists (
    select 1 from public.nutrition_off_catalog_releases r
    where r.id = {sql_literal(release_id)}::uuid
  ) then
    insert into public.nutrition_off_catalog_releases (
      id, source_provider, source_revision, source_snapshot_at, source_file_sha256,
      normalized_artifact_sha256, license_code, license_url, attribution_text,
      netherlands_source_count, eligible_product_count, imported_product_count,
      mapping_version, predecessor_release_id, status, reviewed_by, reviewed_at,
      imported_at, provenance, metadata, created_at, updated_at
    ) values (
      {sql_literal(release_id)}::uuid, 'open_food_facts', {sql_literal(release['source_revision'])},
      {sql_literal(release['source_snapshot_at'])}::timestamptz, {sql_literal(release['source_file_sha256'])},
      {sql_literal(normalized_sha)}, 'ODbL-1.0', {sql_literal(release['license_url'])},
      {sql_literal(release['attribution_text'])}, 106650, 24458, 0,
      {sql_literal(release['mapping_version'])}, null, 'reviewed', {sql_literal(release['reviewed_by'])},
      {sql_literal(release['reviewed_at'])}::timestamptz, null,
      $fmz_json${release_provenance}$fmz_json$::jsonb,
      $fmz_json${release_metadata}$fmz_json$::jsonb || jsonb_build_object(
        'expected_name_count', {expected_names},
        'product_manifest_sha256', {sql_literal(product_sha)},
        'names_manifest_sha256', {sql_literal(names_sha)},
        'frozen_counts', jsonb_build_object(
          'usda_canonical_foods', (select count(*) from public.foods where catalog_scope = 'canonical' and source_provider = 'usda_fdc'),
          'usda_aliases', (select count(*) from public.food_aliases where source_provider = 'usda_fdc'),
          'custom_foods', (select count(*) from public.foods where catalog_scope = 'custom'),
          'food_portions', (select count(*) from public.food_portions),
          'food_logs', (select count(*) from public.food_logs),
          'food_log_items', (select count(*) from public.food_log_items)
        )
      ),
      {sql_literal(release['reviewed_at'])}::timestamptz, {sql_literal(release['reviewed_at'])}::timestamptz
    );
  end if;

  if not exists (
    select 1 from public.nutrition_off_catalog_releases r
    where r.id = {sql_literal(release_id)}::uuid
      and r.source_revision = {sql_literal(release['source_revision'])}
      and r.source_file_sha256 = {sql_literal(release['source_file_sha256'])}
      and r.normalized_artifact_sha256 = {sql_literal(normalized_sha)}
      and r.netherlands_source_count = 106650
      and r.eligible_product_count = 24458
      and r.mapping_version = {sql_literal(release['mapping_version'])}
      and r.license_code = 'ODbL-1.0'
      and r.metadata ->> 'expected_name_count' = {sql_literal(str(expected_names))}
      and r.metadata ->> 'product_manifest_sha256' = {sql_literal(product_sha)}
      and r.metadata ->> 'names_manifest_sha256' = {sql_literal(names_sha)}
  ) then
    raise exception 'OFF release identity drift';
  end if;
end
$fmz_release$;

do $fmz_drift$
begin
  if exists (
    select 1 from fmz_off_products_stage s
    join public.nutrition_off_products p
      on p.id = s.id or p.normalized_gtin14 = s.normalized_gtin14 or p.provider_identity_name = s.provider_identity_name
    where to_jsonb(p) is distinct from to_jsonb(s)
  ) then
    raise exception 'OFF product drift against existing identity';
  end if;
  if exists (
    select 1 from fmz_off_names_stage s
    join public.nutrition_off_product_names n
      on n.id = s.id
      or (
        n.lifecycle_status = 'active'
        and n.product_id = s.product_id
        and n.language_code = s.language_code
        and n.name_type = s.name_type
        and n.normalized_name = s.normalized_name
      )
    where to_jsonb(n) is distinct from to_jsonb(s)
  ) then
    raise exception 'OFF name drift against existing identity';
  end if;
end
$fmz_drift$;

insert into public.nutrition_off_products
select * from fmz_off_products_stage
on conflict (id) do nothing;

insert into public.nutrition_off_product_names
select * from fmz_off_names_stage
on conflict (id) do nothing;

do $fmz_finalize$
begin
  if (select count(*) from public.nutrition_off_products where release_id = {sql_literal(release_id)}::uuid) <> 24458
     or (select count(*) from public.nutrition_off_product_names n join public.nutrition_off_products p on p.id = n.product_id where p.release_id = {sql_literal(release_id)}::uuid) <> {expected_names}
     or (
       select array_agg(p.id order by p.id)
       from public.nutrition_off_products p
       where p.release_id = {sql_literal(release_id)}::uuid
     ) is distinct from (
       select array_agg(s.id order by s.id)
       from fmz_off_products_stage s
     )
     or (
       select array_agg(n.id order by n.id)
       from public.nutrition_off_product_names n
       join public.nutrition_off_products p on p.id = n.product_id
       where p.release_id = {sql_literal(release_id)}::uuid
     ) is distinct from (
       select array_agg(s.id order by s.id)
       from fmz_off_names_stage s
     ) then
    raise exception 'OFF finalization count or membership drift';
  end if;
end
$fmz_finalize$;

update public.nutrition_off_catalog_releases
set status = 'imported',
    imported_product_count = 24458,
    imported_at = {sql_literal(release['reviewed_at'])}::timestamptz,
    updated_at = {sql_literal(release['reviewed_at'])}::timestamptz
where id = {sql_literal(release_id)}::uuid
  and status = 'reviewed';

do $fmz_commit_gate$
begin
  if not exists (
    select 1 from public.nutrition_off_catalog_releases
    where id = {sql_literal(release_id)}::uuid
      and status = 'imported'
      and imported_product_count = 24458
  ) then
    raise exception 'OFF release finalization gate failed';
  end if;
end
$fmz_commit_gate$;

commit;
"""
    importer_path.write_text(importer, encoding="utf-8", newline="\n")

    verifier_path = root / "supabase" / "verification" / "20260825_phase4_nutrition_slice4f_off_catalog_import_verification.sql"
    verifier = f"""-- FitMetZorge Phase 4 Slice 4F OFF catalog import verification
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- One SELECT/CTE statement. No application function invocation and no side effects.

with
expected as (
  select
    {sql_literal(release_id)}::uuid as release_id,
    {sql_literal(release['source_revision'])}::text as source_revision,
    {sql_literal(release['source_file_sha256'])}::text as source_sha,
    {sql_literal(normalized_sha)}::text as artifact_sha,
    {sql_literal(product_sha)}::text as product_sha,
    {sql_literal(names_sha)}::text as names_sha,
    24458::bigint as product_count,
    {expected_names}::bigint as name_count
),
release_row as (
  select r.* from public.nutrition_off_catalog_releases r join expected e on e.release_id = r.id
),
product_rows as (
  select p.* from public.nutrition_off_products p join expected e on e.release_id = p.release_id
),
name_rows as (
  select n.* from public.nutrition_off_product_names n join product_rows p on p.id = n.product_id
),
relation_state as (
  select c.relname::text as table_name, c.relrowsecurity, c.relacl, c.relowner
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname in ('nutrition_off_catalog_releases','nutrition_off_products','nutrition_off_product_names')
),
relation_acl as (
  select r.table_name, a.grantee, a.privilege_type
  from relation_state r
  cross join lateral pg_catalog.aclexplode(coalesce(r.relacl, pg_catalog.acldefault('r', r.relowner))) a
),
column_acl as (
  select c.relname::text as table_name, a.attname::text as column_name, x.grantee, x.privilege_type
  from pg_catalog.pg_attribute a
  join pg_catalog.pg_class c on c.oid = a.attrelid
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  cross join lateral pg_catalog.aclexplode(a.attacl) x
  where n.nspname = 'public'
    and c.relname in ('nutrition_off_catalog_releases','nutrition_off_products','nutrition_off_product_names')
    and a.attnum > 0 and not a.attisdropped and a.attacl is not null
),
role_ids as (
  select
    (select oid from pg_catalog.pg_roles where rolname = 'authenticated') as authenticated_oid,
    (select oid from pg_catalog.pg_roles where rolname = 'anon') as anon_oid,
    (select oid from pg_catalog.pg_roles where rolname = 'service_role') as service_oid
),
policy_state as (
  select tablename::text as table_name, policyname::text as policy_name, cmd::text, roles::text[]
  from pg_catalog.pg_policies
  where schemaname = 'public'
    and tablename in ('nutrition_off_catalog_releases','nutrition_off_products','nutrition_off_product_names')
),
checks as (
  select * from (values
    ('release_identity', (select count(*) = 1 and bool_and(r.source_revision = e.source_revision and r.source_file_sha256 = e.source_sha and r.normalized_artifact_sha256 = e.artifact_sha and r.status = 'imported' and r.imported_product_count = e.product_count and r.eligible_product_count = e.product_count and r.netherlands_source_count = 106650 and r.license_code = 'ODbL-1.0' and r.metadata ->> 'product_manifest_sha256' = e.product_sha and r.metadata ->> 'names_manifest_sha256' = e.names_sha) from release_row r cross join expected e)),
    ('product_count', (select count(*) = max(e.product_count) from product_rows cross join expected e)),
    ('product_identity', (select count(distinct id) = 24458 and count(distinct normalized_gtin14) = 24458 and count(distinct provider_identity_name) = 24458 and bool_and(provider_identity_name = 'open_food_facts:' || normalized_gtin14 and id = public.fmz_phase4_provider_candidate_uuid_v5(provider_identity_name)) from product_rows)),
    ('product_market_quality', (select bool_and(is_netherlands_associated and countries_tags @> array['en:netherlands']::text[] and quality_status in ('complete','reviewed') and lifecycle_status = 'active' and license_code = 'ODbL-1.0' and source_checksum ~ '^[A-F0-9]{{64}}$') from product_rows)),
    ('product_basis', (select count(*) filter (where nutrition_basis = 'per_100_g') = 20355 and count(*) filter (where nutrition_basis = 'per_100_ml') = 4103 from product_rows)),
    ('product_nutrients', (select bool_and(energy_kcal_100 between 0 and 900 and protein_grams_100 between 0 and 100 and carbohydrate_grams_100 between 0 and 100 and fat_grams_100 between 0 and 100 and (fiber_grams_100 is null or fiber_grams_100 between 0 and 100)) from product_rows)),
    ('product_images_absent', (select bool_and(image_reference_url is null and image_license_code is null and image_attribution is null) from product_rows)),
    ('name_count', (select count(*) = max(e.name_count) from name_rows cross join expected e)),
    ('name_parent_and_normalization', (select bool_and(n.normalized_name = public.fmz_phase4_normalize_catalog_text(n.name) and n.source_revision = e.source_revision and n.license_code = 'ODbL-1.0' and n.quality_status in ('complete','reviewed') and n.lifecycle_status = 'active') from name_rows n cross join expected e)),
    ('name_identity_unique', (select count(*) = count(distinct (product_id, language_code, name_type, normalized_name)) from name_rows)),
    ('name_preferred_unique', not exists (select 1 from name_rows where is_preferred group by product_id, language_code having count(*) > 1)),
    ('frozen_usda_foods', (select count(*) = (select (metadata #>> '{{frozen_counts,usda_canonical_foods}}')::bigint from release_row) from public.foods where catalog_scope = 'canonical' and source_provider = 'usda_fdc')),
    ('frozen_usda_aliases', (select count(*) = (select (metadata #>> '{{frozen_counts,usda_aliases}}')::bigint from release_row) from public.food_aliases where source_provider = 'usda_fdc')),
    ('frozen_custom_foods', (select count(*) = (select (metadata #>> '{{frozen_counts,custom_foods}}')::bigint from release_row) from public.foods where catalog_scope = 'custom')),
    ('frozen_portions', (select count(*) = (select (metadata #>> '{{frozen_counts,food_portions}}')::bigint from release_row) from public.food_portions)),
    ('frozen_member_days', (select count(*) = (select (metadata #>> '{{frozen_counts,food_logs}}')::bigint from release_row) from public.food_logs)),
    ('frozen_member_items', (select count(*) = (select (metadata #>> '{{frozen_counts,food_log_items}}')::bigint from release_row) from public.food_log_items)),
    ('rls_enabled', (select count(*) = 3 and bool_and(relrowsecurity) from relation_state)),
    ('catalog_roles_present', (select authenticated_oid is not null and anon_oid is not null and service_oid is not null from role_ids)),
    ('policy_contract', (select count(*) = 2 and bool_and(cmd = 'SELECT' and roles = array['authenticated']::text[]) from policy_state)),
    ('relation_acl_isolation', not exists (select 1 from relation_acl a cross join role_ids r where a.grantee in (0,r.authenticated_oid,r.anon_oid,r.service_oid))),
    ('column_acl_read_only', not exists (select 1 from column_acl a cross join role_ids r where a.grantee in (0,r.anon_oid,r.service_oid) or (a.grantee = r.authenticated_oid and a.privilege_type <> 'SELECT'))),
    ('column_acl_exact_count', (select count(*) = 34 and count(*) filter (where table_name = 'nutrition_off_products') = 25 and count(*) filter (where table_name = 'nutrition_off_product_names') = 9 from column_acl a cross join role_ids r where a.grantee = r.authenticated_oid and a.privilege_type = 'SELECT')),
    ('release_browser_isolated', not exists (select 1 from column_acl a cross join role_ids r where a.table_name = 'nutrition_off_catalog_releases' and a.grantee = r.authenticated_oid))
  ) v(check_name, pass)
),
result as (
  select jsonb_build_object(
    'overall_pass', bool_and(coalesce(pass, false)),
    'pass_count', count(*) filter (where coalesce(pass, false)),
    'fail_count', count(*) filter (where not coalesce(pass, false)),
    'checks', jsonb_agg(jsonb_build_object('check', check_name, 'pass', coalesce(pass, false)) order by check_name)
  ) as verification_result
  from checks
)
select verification_result from result;
"""
    verifier_path.write_text(verifier, encoding="utf-8", newline="\n")

    normalization_verifier_path = root / "supabase" / "verification" / "20260825_phase4_off_normalization_contract_verification.sql"
    if not normalization_verifier_path.is_file():
        raise SystemExit("PostgreSQL normalization contract verifier is missing")

    manifest["execution_files"] = {
        str(importer_path.relative_to(root)).replace("\\", "/"): {
            "sha256": sha256_file(importer_path),
            "bytes": importer_path.stat().st_size,
            "transaction_model": "single_transaction",
            "transport": "psql_file_copy",
        },
        str(verifier_path.relative_to(root)).replace("\\", "/"): {
            "sha256": sha256_file(verifier_path),
            "bytes": verifier_path.stat().st_size,
            "mode": "read_only_select_cte",
        },
        str(normalization_verifier_path.relative_to(root)).replace("\\", "/"): {
            "sha256": sha256_file(normalization_verifier_path),
            "bytes": normalization_verifier_path.stat().st_size,
            "mode": "read_only_postgresql_contract_select_cte",
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(canonical_json(manifest["execution_files"]))


if __name__ == "__main__":
    main()
