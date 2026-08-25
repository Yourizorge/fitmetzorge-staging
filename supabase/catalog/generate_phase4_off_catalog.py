"""Build the deterministic Phase 4 Slice 4F Dutch OFF catalog artifacts.

The input is a read-only Netherlands extract from the pinned Open Food Facts
Parquet snapshot. This script never connects to Supabase and never performs a
network request.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

SOURCE_REVISION = "e544a38353692b2df59df78f47393990a578eb8e"
SOURCE_SNAPSHOT_AT = "2026-08-23T18:34:47Z"
SOURCE_FILE_SIZE = 7_797_955_269
SOURCE_FILE_SHA256 = "38D7A48D32F574812490024AA77FB064E84B041CB2687E46DF87AFCE441100C2"
SOURCE_TOTAL_COUNT = 4_692_771
NETHERLANDS_SOURCE_COUNT = 106_650
SOURCE_EXTRACT_SIZE = 6_709_044
SOURCE_EXTRACT_SHA256 = "FF6ED35C50B134E6EAEF0A23E62EC2DC6CBF981DB55D0F33E0BBF125BABEF27C"
NETHERLANDS_VALID_BARCODE_COUNT = 85_192
NETHERLANDS_REQUIRED_MACROS_PRESENT_COUNT = 56_512
NETHERLANDS_VALID_REQUIRED_MACROS_COUNT = 56_440
ELIGIBLE_PRODUCT_COUNT = 24_458
EXPECTED_MASS_COUNT = 20_355
EXPECTED_VOLUME_COUNT = 4_103
EXPECTED_DUTCH_PRODUCT_COUNT = 18_970
PROVIDER_NAMESPACE = uuid.UUID("23440733-7e58-4c21-ad15-591eae6ab8ac")
MAPPING_VERSION = "phase4_off_nl_v1"
NORMALIZATION_CONTRACT = "public.fmz_phase4_normalize_catalog_text(text)"
GENERATED_AT = "2026-08-25T00:00:00Z"
LICENSE_CODE = "ODbL-1.0"
LICENSE_URL = "https://opendatacommons.org/licenses/odbl/1-0/"
ATTRIBUTION = "Open Food Facts contributors"
REVIEWED_BY = "FitMetZorge owner-reviewed Slice 4F pipeline"

RELEASE_ID = uuid.uuid5(
    PROVIDER_NAMESPACE,
    f"open_food_facts_release:{SOURCE_REVISION}:{MAPPING_VERSION}",
)

PRODUCT_COLUMNS = [
    "id",
    "release_id",
    "source_provider",
    "off_code",
    "barcode_original",
    "normalized_gtin14",
    "provider_identity_name",
    "product_name",
    "product_name_nl",
    "generic_name",
    "brand",
    "normalized_brand",
    "quantity_text",
    "serving_size_text",
    "nutrition_basis",
    "energy_kcal_100",
    "protein_grams_100",
    "carbohydrate_grams_100",
    "fat_grams_100",
    "fiber_grams_100",
    "countries_tags",
    "is_netherlands_associated",
    "off_revision",
    "source_updated_at",
    "source_checksum",
    "provenance",
    "license_code",
    "license_url",
    "attribution_text",
    "image_reference_url",
    "image_license_code",
    "image_attribution",
    "completeness",
    "quality_status",
    "lifecycle_status",
    "imported_at",
    "refreshed_at",
    "metadata",
    "created_at",
    "updated_at",
    "archived_at",
]

NAME_COLUMNS = [
    "id",
    "product_id",
    "language_code",
    "name_type",
    "name",
    "normalized_name",
    "is_preferred",
    "source_provider",
    "source_revision",
    "license_code",
    "provenance",
    "quality_status",
    "lifecycle_status",
    "metadata",
    "created_at",
    "updated_at",
    "archived_at",
]

BRAND_FIXTURES = [
    "red bull",
    "coca cola",
    "campina",
    "optimel",
    "alpro",
    "arla",
    "danone",
    "melkunie",
    "jumbo",
    "albert heijn",
    "ah",
    "plus",
    "lidl",
]

CONCEPT_FIXTURES = [
    "protein pudding",
    "protein bar",
    "kwark",
    "skyr",
    "bread",
    "cereals",
    "sauces",
    "snacks",
    "soft drinks",
]

CONCEPT_TERMS = {
    "protein pudding": ["protein pudding", "protein puddings", "proteine pudding", "eiwitpudding"],
    "protein bar": ["protein bar", "protein bars", "proteine reep", "eiwitreep"],
    "kwark": ["kwark"],
    "skyr": ["skyr"],
    "bread": ["bread", "breads", "brood"],
    "cereals": ["cereal", "cereals", "breakfast cereals", "granen", "muesli"],
    "sauces": ["sauce", "sauces", "saus", "sauzen"],
    "snacks": ["snack", "snacks"],
    "soft drinks": ["soft drink", "soft drinks", "frisdrank", "frisdranken", "sodas"],
}


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Decimal):
        return str(value) if value.is_finite() else None
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def clean_text(value: Any, max_length: int) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text:
        return None
    return text[:max_length].rstrip() or None


def normalize_catalog_text(value: Any) -> str:
    # Mirrors PostgreSQL lower/btrim plus POSIX [[:alnum:]] under UTF-8.
    text = str(value or "").lower().strip()
    text = "".join(char if char.isalpha() or char.isdecimal() else " " for char in text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_language(value: Any) -> str:
    language = str(value or "").lower().strip().split("_")[0].split("-")[0]
    return language if re.fullmatch(r"[a-z]{2,8}", language) else "und"


def iter_localized(entries: Any) -> Iterable[tuple[str, str]]:
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        text = clean_text(entry.get("text"), 240)
        if text:
            yield normalize_language(entry.get("lang")), text


def localized_map(entries: Any) -> dict[str, str]:
    values: dict[str, str] = {}
    for language, text in iter_localized(entries):
        values.setdefault(language, text)
    return values


def decimal_value(value: Any, lower: Decimal, upper: Decimal) -> Decimal | None:
    if value is None:
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number < lower or number > upper:
        return None
    return number.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def decimal_text(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{value:.3f}"


def nutriment_map(entries: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name"))
        value = entry.get("100g")
        if value is not None and result.get(name) is None:
            result[name] = value
        if name == "energy" and value is not None and "_energy_source_unit" not in result:
            result["_energy_source_unit"] = str(entry.get("unit") or "").strip().lower()
    result["_energy_derivation"] = "energy_kcal_100g"
    if result.get("energy-kcal") is None and result.get("energy") is not None:
        source_unit = result.get("_energy_source_unit")
        source_energy = Decimal(str(result["energy"]))
        if source_unit in {"kj", "kilojoule", "kilojoules"}:
            result["energy-kcal"] = source_energy / Decimal("4.184")
            result["_energy_derivation"] = "energy_kj_100g_div_4_184"
        elif source_unit == "kcal":
            result["energy-kcal"] = source_energy
            result["_energy_derivation"] = "energy_kcal_from_energy_100g"
    return result


def gs1_mod10_valid(code: str) -> bool:
    if not re.fullmatch(r"\d{8}|\d{12}|\d{13}|\d{14}", code):
        return False
    body, check_digit = code[:-1], int(code[-1])
    total = 0
    for index, char in enumerate(reversed(body), start=1):
        total += int(char) * (3 if index % 2 == 1 else 1)
    return (10 - total % 10) % 10 == check_digit


def normalize_gtin14(code: str) -> str | None:
    return code.zfill(14) if gs1_mod10_valid(code) else None


def source_timestamp(last_updated: Any, last_modified: Any) -> str | None:
    raw = last_updated if last_updated is not None else last_modified
    if raw is None:
        return None
    try:
        return datetime.fromtimestamp(int(raw), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError, OSError):
        return None


def pg_array(values: Iterable[str]) -> str:
    escaped = [str(value).replace("\\", "\\\\").replace('"', '\\"') for value in values]
    return "{" + ",".join(f'"{value}"' for value in escaped) + "}"


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def row_source_checksum(raw: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(raw).encode("utf-8"))


def select_primary_name(names: dict[str, str], row_language: str) -> str | None:
    for language in ("main", row_language, "nl", "en"):
        if language in names:
            return names[language]
    return next(iter(names.values()), None)


def preferred_language(names: dict[str, str], primary: str, row_language: str) -> str:
    for language in ("nl", row_language, "main", "en"):
        if names.get(language) == primary:
            return normalize_language(row_language if language == "main" else language)
    return normalize_language(row_language)


def add_name(
    bucket: dict[tuple[str, str, str], dict[str, Any]],
    product_id: str,
    language: str,
    name_type: str,
    name: str,
    is_preferred: bool,
    source_field: str,
) -> None:
    clean = clean_text(name, 240)
    normalized = normalize_catalog_text(clean)
    if not clean or not normalized or len(normalized) > 240:
        return
    language = normalize_language(language)
    key = (language, name_type, normalized)
    current = bucket.get(key)
    candidate = {
        "id": str(uuid.uuid5(PROVIDER_NAMESPACE, f"open_food_facts_name:{product_id}:{language}:{name_type}:{normalized}")),
        "product_id": product_id,
        "language_code": language,
        "name_type": name_type,
        "name": clean,
        "normalized_name": normalized,
        "is_preferred": bool_text(is_preferred),
        "source_provider": "open_food_facts",
        "source_revision": SOURCE_REVISION,
        "license_code": LICENSE_CODE,
        "provenance": canonical_json({"source_field": source_field, "source_revision": SOURCE_REVISION}),
        "quality_status": "complete",
        "lifecycle_status": "active",
        "metadata": canonical_json({"mapping_version": MAPPING_VERSION}),
        "created_at": GENERATED_AT,
        "updated_at": GENERATED_AT,
        "archived_at": "",
    }
    if current is None or (is_preferred and current["is_preferred"] != "true"):
        bucket[key] = candidate


def enforce_one_preferred_per_language(names: list[dict[str, Any]]) -> None:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in names:
        grouped.setdefault(row["language_code"], []).append(row)
    for rows in grouped.values():
        preferred = [row for row in rows if row["is_preferred"] == "true"]
        if len(preferred) <= 1:
            continue
        preferred.sort(key=lambda row: (row["name_type"] != "primary", row["normalized_name"], row["id"]))
        for row in preferred[1:]:
            row["is_preferred"] = "false"


def parse_source_rows(source: Path) -> Iterable[dict[str, Any]]:
    import duckdb

    connection = duckdb.connect()
    cursor = connection.execute(
        """
        select
          code, product_name, generic_name, lang, brands, categories_tags,
          countries_tags, product_quantity_unit, product_quantity, quantity,
          serving_size, nutrition_data_per, nutriments, data_quality_errors_tags,
          obsolete, rev, last_modified_t, last_updated_t, complete, completeness
        from read_parquet(?)
        order by code
        """,
        [str(source)],
    )
    columns = [description[0] for description in cursor.description]
    try:
        while True:
            rows = cursor.fetchmany(1000)
            if not rows:
                break
            for row in rows:
                yield dict(zip(columns, row))
    finally:
        connection.close()


def build_product(raw: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
    countries = sorted({str(value) for value in raw.get("countries_tags") or []})
    if "en:netherlands" not in countries:
        return None
    if raw.get("obsolete") is True:
        return None
    categories = {str(value) for value in raw.get("categories_tags") or []}
    if "en:non-food-products" in categories:
        return None
    if raw.get("data_quality_errors_tags"):
        return None

    code = clean_text(raw.get("code"), 14)
    if not code or normalize_gtin14(code) is None:
        return None
    gtin14 = normalize_gtin14(code)
    assert gtin14 is not None

    brand = clean_text(raw.get("brands"), 160)
    normalized_brand = normalize_catalog_text(brand)
    if not brand or not normalized_brand or len(normalized_brand) > 160:
        return None

    unit = str(raw.get("product_quantity_unit") or "").strip().lower()
    if unit not in {"g", "ml"}:
        return None
    basis = "per_100_g" if unit == "g" else "per_100_ml"

    names = localized_map(raw.get("product_name"))
    row_language = normalize_language(raw.get("lang"))
    primary_name = select_primary_name(names, row_language)
    if not primary_name or len(normalize_catalog_text(primary_name)) < 2:
        return None
    dutch_name = names.get("nl")
    generic_names = localized_map(raw.get("generic_name"))
    generic_name = select_primary_name(generic_names, row_language)

    nutrients = nutriment_map(raw.get("nutriments"))
    energy = decimal_value(nutrients.get("energy-kcal"), Decimal("0"), Decimal("900"))
    protein = decimal_value(nutrients.get("proteins"), Decimal("0"), Decimal("100"))
    carbohydrate = decimal_value(nutrients.get("carbohydrates"), Decimal("0"), Decimal("100"))
    fat = decimal_value(nutrients.get("fat"), Decimal("0"), Decimal("100"))
    if None in (energy, protein, carbohydrate, fat):
        return None
    fiber = decimal_value(nutrients.get("fiber"), Decimal("0"), Decimal("100"))

    product_id = str(uuid.uuid5(PROVIDER_NAMESPACE, f"open_food_facts:{gtin14}"))
    updated_at = source_timestamp(raw.get("last_updated_t"), raw.get("last_modified_t"))
    source_fields = {
        "code": code,
        "product_name": raw.get("product_name"),
        "generic_name": raw.get("generic_name"),
        "lang": raw.get("lang"),
        "brands": raw.get("brands"),
        "categories_tags": sorted(categories),
        "countries_tags": countries,
        "product_quantity_unit": unit,
        "product_quantity": raw.get("product_quantity"),
        "quantity": raw.get("quantity"),
        "serving_size": raw.get("serving_size"),
        "nutrition_data_per": raw.get("nutrition_data_per"),
        "nutrients_100": {
            "energy-kcal": nutrients.get("energy-kcal"),
            "proteins": nutrients.get("proteins"),
            "carbohydrates": nutrients.get("carbohydrates"),
            "fat": nutrients.get("fat"),
            "fiber": nutrients.get("fiber"),
            "energy_derivation": nutrients.get("_energy_derivation"),
        },
        "rev": raw.get("rev"),
        "source_updated_at": updated_at,
    }
    quantity = clean_text(raw.get("quantity"), 120) or clean_text(raw.get("product_quantity"), 120)
    serving = clean_text(raw.get("serving_size"), 120)
    completeness = {
        "brand": True,
        "required_macros": True,
        "supported_basis": True,
        "usable_name": True,
        "fiber": fiber is not None,
        "dutch_name": dutch_name is not None,
    }
    product = {
        "id": product_id,
        "release_id": str(RELEASE_ID),
        "source_provider": "open_food_facts",
        "off_code": code,
        "barcode_original": code,
        "normalized_gtin14": gtin14,
        "provider_identity_name": f"open_food_facts:{gtin14}",
        "product_name": clean_text(primary_name, 240),
        "product_name_nl": clean_text(dutch_name, 240) or "",
        "generic_name": clean_text(generic_name, 240) or "",
        "brand": brand,
        "normalized_brand": normalized_brand,
        "quantity_text": quantity or "",
        "serving_size_text": serving or "",
        "nutrition_basis": basis,
        "energy_kcal_100": decimal_text(energy),
        "protein_grams_100": decimal_text(protein),
        "carbohydrate_grams_100": decimal_text(carbohydrate),
        "fat_grams_100": decimal_text(fat),
        "fiber_grams_100": decimal_text(fiber),
        "countries_tags": pg_array(countries),
        "is_netherlands_associated": "true",
        "off_revision": SOURCE_REVISION,
        "source_updated_at": updated_at or "",
        "source_checksum": row_source_checksum(source_fields),
        "provenance": canonical_json(
            {
                "dataset": "openfoodfacts/product-database",
                "source_revision": SOURCE_REVISION,
                "source_snapshot_at": SOURCE_SNAPSHOT_AT,
                "off_code": code,
            }
        ),
        "license_code": LICENSE_CODE,
        "license_url": LICENSE_URL,
        "attribution_text": ATTRIBUTION,
        "image_reference_url": "",
        "image_license_code": "",
        "image_attribution": "",
        "completeness": canonical_json(completeness),
        "quality_status": "complete",
        "lifecycle_status": "active",
        "imported_at": GENERATED_AT,
        "refreshed_at": GENERATED_AT,
        "metadata": canonical_json(
            {
                "mapping_version": MAPPING_VERSION,
                "off_revision_number": raw.get("rev"),
                "source_lang": row_language,
                "source_complete": raw.get("complete"),
                "source_completeness": raw.get("completeness"),
                "categories_tags": sorted(categories),
                "image_policy": "not_imported",
                "energy_derivation": nutrients.get("_energy_derivation"),
            }
        ),
        "created_at": GENERATED_AT,
        "updated_at": GENERATED_AT,
        "archived_at": "",
    }

    name_bucket: dict[tuple[str, str, str], dict[str, Any]] = {}
    primary_language = preferred_language(names, primary_name, row_language)
    add_name(name_bucket, product_id, primary_language, "primary", primary_name, True, "product_name")
    for language, name in iter_localized(raw.get("product_name")):
        effective_language = row_language if language == "main" else language
        if normalize_catalog_text(name) == normalize_catalog_text(primary_name) and normalize_language(effective_language) == primary_language:
            continue
        add_name(
            name_bucket,
            product_id,
            effective_language,
            "localized",
            name,
            language == "nl" and name == dutch_name,
            "product_name",
        )
    for language, name in iter_localized(raw.get("generic_name")):
        effective_language = row_language if language == "main" else language
        add_name(name_bucket, product_id, effective_language, "generic", name, False, "generic_name")
    add_name(name_bucket, product_id, "und", "brand", brand, False, "brands")
    product_names = list(name_bucket.values())
    enforce_one_preferred_per_language(product_names)
    product_names.sort(key=lambda row: (row["language_code"], row["name_type"], row["normalized_name"], row["id"]))
    return product, product_names


def write_csv(path: Path, columns: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def coverage_count(products: list[dict[str, Any]], names: list[dict[str, Any]], query: str) -> int:
    normalized_query = normalize_catalog_text(query)
    product_ids = {
        row["product_id"]
        for row in names
        if normalized_query in row["normalized_name"]
    }
    for product in products:
        searchable = normalize_catalog_text(
            " ".join(
                str(product.get(field) or "")
                for field in ("product_name", "product_name_nl", "generic_name", "brand")
            )
        )
        if normalized_query in searchable:
            product_ids.add(product["id"])
    return len(product_ids)


def brand_coverage_count(products: list[dict[str, Any]], query: str) -> int:
    normalized_query = normalize_catalog_text(query)
    needle = f" {normalized_query} "
    return sum(
        needle in f" {product['normalized_brand']} "
        for product in products
    )


def brand_group_coverage_count(products: list[dict[str, Any]], queries: Iterable[str]) -> int:
    needles = [f" {normalize_catalog_text(query)} " for query in queries]
    return sum(
        any(needle in f" {product['normalized_brand']} " for needle in needles)
        for product in products
    )


def concept_coverage_count(products: list[dict[str, Any]], concept: str) -> int:
    terms = [normalize_catalog_text(term) for term in CONCEPT_TERMS[concept]]
    count = 0
    for product in products:
        metadata = json.loads(product["metadata"])
        searchable = normalize_catalog_text(
            " ".join(
                [
                    str(product.get("product_name") or ""),
                    str(product.get("product_name_nl") or ""),
                    str(product.get("generic_name") or ""),
                    str(product.get("brand") or ""),
                    " ".join(metadata.get("categories_tags", [])),
                ]
            )
        )
        padded = f" {searchable} "
        if any(f" {term} " in padded for term in terms):
            count += 1
    return count


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.write_bytes(payload.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.source.is_file() or args.source.stat().st_size != SOURCE_EXTRACT_SIZE:
        raise SystemExit("Pinned Netherlands source extract size mismatch")
    if sha256_file(args.source) != SOURCE_EXTRACT_SHA256:
        raise SystemExit("Pinned Netherlands source extract SHA-256 mismatch")

    products: list[dict[str, Any]] = []
    names: list[dict[str, Any]] = []
    source_count = 0
    for source_row in parse_source_rows(args.source):
        source_count += 1
        built = build_product(source_row)
        if built is None:
            continue
        product, product_names = built
        products.append(product)
        names.extend(product_names)

    if source_count != NETHERLANDS_SOURCE_COUNT:
        raise SystemExit(f"Netherlands source count mismatch: {source_count} != {NETHERLANDS_SOURCE_COUNT}")

    products.sort(key=lambda row: (row["normalized_gtin14"], row["id"]))
    names.sort(key=lambda row: (row["product_id"], row["language_code"], row["name_type"], row["normalized_name"], row["id"]))

    if len(products) != ELIGIBLE_PRODUCT_COUNT:
        raise SystemExit(f"Eligible product count mismatch: {len(products)} != {ELIGIBLE_PRODUCT_COUNT}")
    gtins = {row["normalized_gtin14"] for row in products}
    ids = {row["id"] for row in products}
    if len(gtins) != ELIGIBLE_PRODUCT_COUNT or len(ids) != ELIGIBLE_PRODUCT_COUNT:
        raise SystemExit("Product identity is not unique")
    basis = Counter(row["nutrition_basis"] for row in products)
    if basis != Counter({"per_100_g": EXPECTED_MASS_COUNT, "per_100_ml": EXPECTED_VOLUME_COUNT}):
        raise SystemExit(f"Nutrition basis mismatch: {basis}")
    dutch_count = sum(bool(row["product_name_nl"]) for row in products)
    if dutch_count != EXPECTED_DUTCH_PRODUCT_COUNT:
        raise SystemExit(f"Dutch product-name count mismatch: {dutch_count} != {EXPECTED_DUTCH_PRODUCT_COUNT}")

    product_path = args.output / "20260825_phase4_off_products.csv"
    names_path = args.output / "20260825_phase4_off_product_names.csv"
    write_csv(product_path, PRODUCT_COLUMNS, products)
    write_csv(names_path, NAME_COLUMNS, names)
    product_sha = sha256_file(product_path)
    names_sha = sha256_file(names_path)
    normalized_descriptor = {
        "eligible_product_count": len(products),
        "mapping_version": MAPPING_VERSION,
        "name_count": len(names),
        "names_sha256": names_sha,
        "normalization_contract": NORMALIZATION_CONTRACT,
        "products_sha256": product_sha,
        "release_id": str(RELEASE_ID),
        "source_file_sha256": SOURCE_FILE_SHA256,
        "source_revision": SOURCE_REVISION,
    }
    normalized_sha = sha256_bytes(canonical_json(normalized_descriptor).encode("utf-8"))

    nutrient_ranges: dict[str, dict[str, str]] = {}
    for field in (
        "energy_kcal_100",
        "protein_grams_100",
        "carbohydrate_grams_100",
        "fat_grams_100",
        "fiber_grams_100",
    ):
        values = [Decimal(row[field]) for row in products if row[field]]
        nutrient_ranges[field] = {
            "min": decimal_text(min(values)) if values else "",
            "max": decimal_text(max(values)) if values else "",
            "present_count": len(values),
        }

    brand_coverage = {query: brand_coverage_count(products, query) for query in BRAND_FIXTURES}
    brand_coverage["albert heijn / ah"] = brand_group_coverage_count(products, ("albert heijn", "ah"))
    concept_coverage = {query: concept_coverage_count(products, query) for query in CONCEPT_FIXTURES}
    exact_gtin_fixtures = [
        {
            "normalized_gtin14": row["normalized_gtin14"],
            "product_id": row["id"],
            "product_name": row["product_name"],
            "brand": row["brand"],
        }
        for row in products[:5]
    ]
    fixtures = {
        "text_queries": [
            "red bull", "optimel", "campina", "coca cola", "alpro", "arla",
            "danone", "melkunie", "jumbo", "ah", "plus", "kwark", "skyr",
            "protein pudding", "protein bar",
        ],
        "coverage": {**brand_coverage, **concept_coverage},
        "exact_gtin": exact_gtin_fixtures,
    }
    fixtures_path = args.output / "20260825_phase4_off_search_fixtures.json"
    write_json(fixtures_path, fixtures)

    source_lock = {
        "dataset": "openfoodfacts/product-database",
        "dataset_file": "food.parquet",
        "immutable_download_url": (
            "https://huggingface.co/datasets/openfoodfacts/product-database/resolve/"
            f"{SOURCE_REVISION}/food.parquet"
        ),
        "immutable_revision": SOURCE_REVISION,
        "published_at": SOURCE_SNAPSHOT_AT,
        "source_file_size": SOURCE_FILE_SIZE,
        "source_file_sha256": SOURCE_FILE_SHA256,
        "source_lfs_oid": SOURCE_FILE_SHA256.lower(),
        "hash_verification_method": "immutable Hugging Face commit-tree LFS SHA-256 OID and byte size",
        "source_total_count": SOURCE_TOTAL_COUNT,
        "netherlands_filter": "countries_tags contains en:netherlands",
        "netherlands_source_count": NETHERLANDS_SOURCE_COUNT,
        "netherlands_valid_barcode_count": NETHERLANDS_VALID_BARCODE_COUNT,
        "netherlands_required_macros_present_count": NETHERLANDS_REQUIRED_MACROS_PRESENT_COUNT,
        "netherlands_valid_required_macros_count": NETHERLANDS_VALID_REQUIRED_MACROS_COUNT,
        "eligible_product_count": ELIGIBLE_PRODUCT_COUNT,
        "eligible_dutch_product_name_count": EXPECTED_DUTCH_PRODUCT_COUNT,
        "eligible_front_image_reference_count": 18_637,
        "license_code": LICENSE_CODE,
        "license_url": LICENSE_URL,
        "attribution_text": ATTRIBUTION,
    }
    source_lock_path = args.output / "20260825_phase4_off_source_lock.json"
    write_json(source_lock_path, source_lock)

    release = {
        "id": str(RELEASE_ID),
        "source_provider": "open_food_facts",
        "source_revision": SOURCE_REVISION,
        "source_snapshot_at": SOURCE_SNAPSHOT_AT,
        "source_file_size": SOURCE_FILE_SIZE,
        "source_file_sha256": SOURCE_FILE_SHA256,
        "normalized_artifact_sha256": normalized_sha,
        "license_code": LICENSE_CODE,
        "license_url": LICENSE_URL,
        "attribution_text": ATTRIBUTION,
        "netherlands_source_count": NETHERLANDS_SOURCE_COUNT,
        "eligible_product_count": ELIGIBLE_PRODUCT_COUNT,
        "expected_name_count": len(names),
        "mapping_version": MAPPING_VERSION,
        "reviewed_by": REVIEWED_BY,
        "reviewed_at": GENERATED_AT,
        "product_manifest_sha256": product_sha,
        "names_manifest_sha256": names_sha,
        "provenance": {
            "dataset": "openfoodfacts/product-database",
            "dataset_file": "food.parquet",
            "immutable_revision": SOURCE_REVISION,
            "published_at": SOURCE_SNAPSHOT_AT,
            "source_total_count": SOURCE_TOTAL_COUNT,
            "filter": "countries_tags contains en:netherlands",
            "license": LICENSE_CODE,
        },
        "metadata": {
            "basis_counts": dict(sorted(basis.items())),
            "dutch_product_name_count": dutch_count,
            "image_policy": "references_not_imported",
            "normalization_contract": NORMALIZATION_CONTRACT,
            "nutrient_ranges": nutrient_ranges,
            "rejected_after_locked_eligibility": 0,
        },
    }
    release_path = args.output / "20260825_phase4_off_release.json"
    write_json(release_path, release)

    artifact_manifest = {
        "schema_version": 1,
        "generated_at": GENERATED_AT,
        "release_id": str(RELEASE_ID),
        "source": {
            "revision": SOURCE_REVISION,
            "snapshot_at": SOURCE_SNAPSHOT_AT,
            "file_size": SOURCE_FILE_SIZE,
            "file_sha256": SOURCE_FILE_SHA256,
            "total_count": SOURCE_TOTAL_COUNT,
            "netherlands_count": NETHERLANDS_SOURCE_COUNT,
            "local_extract_filename": args.source.name,
            "local_extract_sha256": sha256_file(args.source),
            "local_extract_bytes": args.source.stat().st_size,
        },
        "normalized_artifact_sha256": normalized_sha,
        "normalization_contract": {
            "authority": NORMALIZATION_CONTRACT,
            "compatibility_normalization": "none",
            "character_class": "PostgreSQL POSIX [[:alnum:]]",
            "supersedes_normalized_artifact_sha256": "CE35E7A30245430078D28687A0247B8E88B759149556D80CA88A2A7A42D2EC80",
        },
        "counts": {
            "products": len(products),
            "names": len(names),
            "dutch_product_names": dutch_count,
            "per_100_g": basis["per_100_g"],
            "per_100_ml": basis["per_100_ml"],
        },
        "files": {
            product_path.name: {"sha256": product_sha, "bytes": product_path.stat().st_size},
            names_path.name: {"sha256": names_sha, "bytes": names_path.stat().st_size},
            release_path.name: {"sha256": sha256_file(release_path), "bytes": release_path.stat().st_size},
            fixtures_path.name: {"sha256": sha256_file(fixtures_path), "bytes": fixtures_path.stat().st_size},
            source_lock_path.name: {"sha256": sha256_file(source_lock_path), "bytes": source_lock_path.stat().st_size},
        },
        "brand_coverage": brand_coverage,
        "concept_coverage": concept_coverage,
        "nutrient_ranges": nutrient_ranges,
    }
    manifest_path = args.output / "20260825_phase4_off_artifact_manifest.json"
    write_json(manifest_path, artifact_manifest)
    print(canonical_json({"status": "PASS", "manifest": str(manifest_path), **artifact_manifest["counts"]}))


if __name__ == "__main__":
    main()
