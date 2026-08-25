"""Verify Phase 4 Slice 4F OFF artifacts without database access."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import uuid
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from generate_phase4_off_catalog import (
    ELIGIBLE_PRODUCT_COUNT,
    EXPECTED_DUTCH_PRODUCT_COUNT,
    EXPECTED_MASS_COUNT,
    EXPECTED_VOLUME_COUNT,
    LICENSE_CODE,
    NETHERLANDS_SOURCE_COUNT,
    PROVIDER_NAMESPACE,
    RELEASE_ID,
    SOURCE_FILE_SHA256,
    SOURCE_REVISION,
    gs1_mod10_valid,
)


NORMALIZATION_CONTRACT_CASES = {
    "trademark": ("A™ B", "a b"),
    "ordinal": ("Penne Nº 41", "penne nº 41"),
    "subscript": ("CO₂ test", "co test"),
    "decomposed_accent": ("Mango dri\u0302nk", "mango dri nk"),
    "precomposed_accent": ("Mango drînk", "mango drînk"),
    "thai": ("ผงทำหมูแดง", "ผงทำหม แดง"),
    "korean": ("ㅋㄴ타블러ㅣ", "ㅋㄴ타블러ㅣ"),
    "punctuation": ("Red-Bull / Zero", "red bull zero"),
    "multiple_whitespace": ("Red   Bull\tZero", "red bull zero"),
    "leading_trailing": ("  Red Bull  ", "red bull"),
    "mixed_unicode_ascii": ("Barkleys™ Nº5 CO₂", "barkleys nº5 co"),
    "brand": ("Albert Heijn, AH Biologisch", "albert heijn ah biologisch"),
    "product_name": ("Ben & Jerry's Glace 465ml", "ben jerry s glace 465ml"),
}


def postgres_catalog_text_oracle(value: str) -> str:
    """Independent Python oracle for the locked PostgreSQL POSIX contract."""
    lowered = str(value or "").lower().strip()
    alphanumeric = "".join(char if char.isalpha() or char.isdecimal() else " " for char in lowered)
    return re.sub(r"\s+", " ", alphanumeric).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def require(condition: bool, label: str, checks: list[int]) -> None:
    if not condition:
        raise AssertionError(label)
    checks[0] += 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-dir", type=Path, required=True)
    parser.add_argument("--import-script", type=Path, required=True)
    parser.add_argument("--verifier", type=Path, required=True)
    args = parser.parse_args()

    checks = [0]
    generator_source = Path(__file__).with_name("generate_phase4_off_catalog.py").read_text(encoding="utf-8")
    require("unicodedata.normalize" not in generator_source, "generator_has_no_unicode_normalization", checks)
    for case_id, (source, expected) in NORMALIZATION_CONTRACT_CASES.items():
        require(postgres_catalog_text_oracle(source) == expected, f"postgres_normalization_fixture:{case_id}", checks)
    manifest_path = args.catalog_dir / "20260825_phase4_off_artifact_manifest.json"
    release_path = args.catalog_dir / "20260825_phase4_off_release.json"
    product_path = args.catalog_dir / "20260825_phase4_off_products.csv"
    names_path = args.catalog_dir / "20260825_phase4_off_product_names.csv"
    fixtures_path = args.catalog_dir / "20260825_phase4_off_search_fixtures.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    release = json.loads(release_path.read_text(encoding="utf-8"))
    require(manifest["source"]["revision"] == SOURCE_REVISION, "source_revision_exact", checks)
    require(manifest["source"]["file_sha256"] == SOURCE_FILE_SHA256, "source_sha256_exact", checks)
    require(manifest["source"]["netherlands_count"] == NETHERLANDS_SOURCE_COUNT, "netherlands_count_exact", checks)
    require(release["id"] == str(RELEASE_ID), "release_uuid_exact", checks)
    require(release["license_code"] == LICENSE_CODE, "release_odbl_license", checks)

    for filename, metadata in manifest["files"].items():
        path = args.catalog_dir / filename
        require(path.is_file(), f"artifact_present:{filename}", checks)
        require(path.stat().st_size == metadata["bytes"], f"artifact_size:{filename}", checks)
        require(sha256_file(path) == metadata["sha256"], f"artifact_sha256:{filename}", checks)

    with product_path.open("r", encoding="utf-8", newline="") as handle:
        products = list(csv.DictReader(handle))
    with names_path.open("r", encoding="utf-8", newline="") as handle:
        names = list(csv.DictReader(handle))

    require(len(products) == ELIGIBLE_PRODUCT_COUNT, "eligible_product_count", checks)
    require(manifest["counts"]["products"] == ELIGIBLE_PRODUCT_COUNT, "manifest_product_count", checks)
    require(len(names) == manifest["counts"]["names"], "name_count_exact", checks)
    require(sum(bool(row["product_name_nl"]) for row in products) == EXPECTED_DUTCH_PRODUCT_COUNT, "dutch_name_count", checks)

    ids: set[str] = set()
    gtins: set[str] = set()
    identities: set[str] = set()
    basis = Counter()
    for row in products:
        code = row["barcode_original"]
        gtin14 = row["normalized_gtin14"]
        require(gs1_mod10_valid(code), f"valid_gtin:{gtin14}", checks)
        require(gtin14 == code.zfill(14), f"normalized_gtin:{gtin14}", checks)
        identity = f"open_food_facts:{gtin14}"
        expected_id = str(uuid.uuid5(PROVIDER_NAMESPACE, identity))
        require(row["provider_identity_name"] == identity, f"provider_identity:{gtin14}", checks)
        require(row["id"] == expected_id, f"deterministic_uuid:{gtin14}", checks)
        require(row["release_id"] == str(RELEASE_ID), f"release_link:{gtin14}", checks)
        require(row["off_revision"] == SOURCE_REVISION, f"source_revision:{gtin14}", checks)
        require(row["license_code"] == LICENSE_CODE, f"product_license:{gtin14}", checks)
        require(row["is_netherlands_associated"] == "true" and "en:netherlands" in row["countries_tags"], f"netherlands_association:{gtin14}", checks)
        require(row["quality_status"] == "complete" and row["lifecycle_status"] == "active", f"loggable_state:{gtin14}", checks)
        require(row["normalized_brand"] == postgres_catalog_text_oracle(row["brand"]), f"brand_normalization:{gtin14}", checks)
        require(re.fullmatch(r"[A-F0-9]{64}", row["source_checksum"]) is not None, f"source_checksum:{gtin14}", checks)
        bounds = {
            "energy_kcal_100": Decimal("900"),
            "protein_grams_100": Decimal("100"),
            "carbohydrate_grams_100": Decimal("100"),
            "fat_grams_100": Decimal("100"),
        }
        for field, upper in bounds.items():
            value = Decimal(row[field])
            require(value.is_finite() and Decimal("0") <= value <= upper, f"macro_bounds:{gtin14}:{field}", checks)
        if row["fiber_grams_100"]:
            fiber = Decimal(row["fiber_grams_100"])
            require(fiber.is_finite() and Decimal("0") <= fiber <= Decimal("100"), f"fiber_bounds:{gtin14}", checks)
        require(not row["image_reference_url"] and not row["image_license_code"] and not row["image_attribution"], f"image_policy:{gtin14}", checks)
        ids.add(row["id"])
        gtins.add(gtin14)
        identities.add(identity)
        basis[row["nutrition_basis"]] += 1

    require(len(ids) == ELIGIBLE_PRODUCT_COUNT, "unique_product_uuids", checks)
    require(len(gtins) == ELIGIBLE_PRODUCT_COUNT, "unique_normalized_gtins", checks)
    require(len(identities) == ELIGIBLE_PRODUCT_COUNT, "unique_provider_identities", checks)
    require(basis == Counter({"per_100_g": EXPECTED_MASS_COUNT, "per_100_ml": EXPECTED_VOLUME_COUNT}), "nutrition_basis_split", checks)

    name_ids: set[str] = set()
    name_identity: set[tuple[str, str, str, str]] = set()
    preferred = defaultdict(int)
    for row in names:
        require(row["product_id"] in ids, f"name_parent:{row['id']}", checks)
        require(row["normalized_name"] == postgres_catalog_text_oracle(row["name"]), f"name_normalization:{row['id']}", checks)
        identity = (row["product_id"], row["language_code"], row["name_type"], row["normalized_name"])
        expected_id = str(uuid.uuid5(PROVIDER_NAMESPACE, "open_food_facts_name:" + ":".join(identity)))
        require(row["id"] == expected_id, f"name_uuid:{row['id']}", checks)
        require(row["source_revision"] == SOURCE_REVISION and row["license_code"] == LICENSE_CODE, f"name_provenance:{row['id']}", checks)
        require(row["name_type"] != "search_variant", f"no_fabricated_search_variant:{row['id']}", checks)
        name_ids.add(row["id"])
        name_identity.add(identity)
        if row["is_preferred"] == "true":
            preferred[(row["product_id"], row["language_code"])] += 1

    require(len(name_ids) == len(names), "unique_name_uuids", checks)
    require(len(name_identity) == len(names), "unique_active_name_identity", checks)
    require(all(count == 1 for count in preferred.values()), "preferred_name_uniqueness", checks)
    require(all(query in manifest["brand_coverage"] for query in ("red bull", "coca cola", "ah", "plus")), "brand_coverage_recorded", checks)
    require(all(query in manifest["concept_coverage"] for query in ("kwark", "skyr", "protein pudding", "protein bar")), "concept_coverage_recorded", checks)

    importer = args.import_script.read_text(encoding="utf-8")
    require("\\set ON_ERROR_STOP on" in importer, "importer_stop_on_error", checks)
    require(re.search(r"\bbegin\s*;", importer, flags=re.IGNORECASE) is not None, "importer_transaction_begin", checks)
    require(re.search(r"\bcommit\s*;", importer, flags=re.IGNORECASE) is not None, "importer_transaction_commit", checks)
    require("pg_advisory_xact_lock" in importer, "importer_advisory_lock", checks)
    require("on conflict (id) do nothing" in importer.lower(), "importer_replay_path", checks)
    require("drift" in importer.lower(), "importer_fail_on_drift", checks)
    require(re.search(r"\b(delete|truncate)\b", importer, flags=re.IGNORECASE) is None, "importer_no_delete_or_truncate", checks)
    for frozen_table in ("foods", "food_aliases", "food_portions", "food_logs", "food_log_items"):
        require(re.search(rf"\b(insert\s+into|update)\s+public\.{frozen_table}\b", importer, flags=re.IGNORECASE) is None, f"no_frozen_write:{frozen_table}", checks)

    verifier = args.verifier.read_text(encoding="utf-8")
    stripped = re.sub(r"--[^\n]*", "", verifier).strip().lower()
    require(stripped.startswith("with"), "verifier_cte_select_only", checks)
    require(re.search(r"\b(insert|update|delete|truncate|create|alter|drop|grant|revoke|call|do)\b", stripped) is None, "verifier_no_mutation", checks)
    require("overall_pass" in verifier, "verifier_overall_pass", checks)

    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    require(len(fixtures["exact_gtin"]) >= 5, "gtin_acceptance_fixtures", checks)
    require(len(fixtures["text_queries"]) >= 15, "text_search_acceptance_fixtures", checks)

    print(json.dumps({"status": "PASS", "checks": checks[0], "products": len(products), "names": len(names)}, sort_keys=True))


if __name__ == "__main__":
    main()
