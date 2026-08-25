-- FitMetZorge Phase 4 Slice 4F OFF catalog import verification
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- One SELECT/CTE statement. No application function invocation and no side effects.

with
expected as (
  select
    '4b487f4f-ac8e-5579-a2a2-d4164c4b368a'::uuid as release_id,
    'e544a38353692b2df59df78f47393990a578eb8e'::text as source_revision,
    '38D7A48D32F574812490024AA77FB064E84B041CB2687E46DF87AFCE441100C2'::text as source_sha,
    '3E826B252B484081CB6D271C73AFFEE70A4B177CAB10E228E46963C5BF63D07D'::text as artifact_sha,
    'BFB88DFC6C57E2EC4EDA05E29C5F19515E678B7509C0EC4D62BD9686C57F6A9D'::text as product_sha,
    '04E56D0D237CABB77DE2A574D8CEC4A440C15D6824645820920CCB4B220FFAC6'::text as names_sha,
    24458::bigint as product_count,
    74184::bigint as name_count
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
    ('product_market_quality', (select bool_and(is_netherlands_associated and countries_tags @> array['en:netherlands']::text[] and quality_status in ('complete','reviewed') and lifecycle_status = 'active' and license_code = 'ODbL-1.0' and source_checksum ~ '^[A-F0-9]{64}$') from product_rows)),
    ('product_basis', (select count(*) filter (where nutrition_basis = 'per_100_g') = 20355 and count(*) filter (where nutrition_basis = 'per_100_ml') = 4103 from product_rows)),
    ('product_nutrients', (select bool_and(energy_kcal_100 between 0 and 900 and protein_grams_100 between 0 and 100 and carbohydrate_grams_100 between 0 and 100 and fat_grams_100 between 0 and 100 and (fiber_grams_100 is null or fiber_grams_100 between 0 and 100)) from product_rows)),
    ('product_images_absent', (select bool_and(image_reference_url is null and image_license_code is null and image_attribution is null) from product_rows)),
    ('name_count', (select count(*) = max(e.name_count) from name_rows cross join expected e)),
    ('name_parent_and_normalization', (select bool_and(n.normalized_name = public.fmz_phase4_normalize_catalog_text(n.name) and n.source_revision = e.source_revision and n.license_code = 'ODbL-1.0' and n.quality_status in ('complete','reviewed') and n.lifecycle_status = 'active') from name_rows n cross join expected e)),
    ('name_identity_unique', (select count(*) = count(distinct (product_id, language_code, name_type, normalized_name)) from name_rows)),
    ('name_preferred_unique', not exists (select 1 from name_rows where is_preferred group by product_id, language_code having count(*) > 1)),
    ('frozen_usda_foods', (select count(*) = (select (metadata #>> '{frozen_counts,usda_canonical_foods}')::bigint from release_row) from public.foods where catalog_scope = 'canonical' and source_provider = 'usda_fdc')),
    ('frozen_usda_aliases', (select count(*) = (select (metadata #>> '{frozen_counts,usda_aliases}')::bigint from release_row) from public.food_aliases where source_provider = 'usda_fdc')),
    ('frozen_custom_foods', (select count(*) = (select (metadata #>> '{frozen_counts,custom_foods}')::bigint from release_row) from public.foods where catalog_scope = 'custom')),
    ('frozen_portions', (select count(*) = (select (metadata #>> '{frozen_counts,food_portions}')::bigint from release_row) from public.food_portions)),
    ('frozen_member_days', (select count(*) = (select (metadata #>> '{frozen_counts,food_logs}')::bigint from release_row) from public.food_logs)),
    ('frozen_member_items', (select count(*) = (select (metadata #>> '{frozen_counts,food_log_items}')::bigint from release_row) from public.food_log_items)),
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
