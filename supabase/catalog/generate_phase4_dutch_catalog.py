"""Build the reviewed Phase 4 Dutch USDA catalog artifacts from pinned exports."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROVIDER_NAMESPACE = uuid.UUID("23440733-7e58-4c21-ad15-591eae6ab8ac")
INGESTION_NAME = "https://fitmetzorge.nl/nutrition/ingestions/usda_fdc/phase4_nl_generic_v1_20260822"
INGESTION_ID = uuid.uuid5(uuid.NAMESPACE_URL, INGESTION_NAME)
ARTIFACT_VERSION = "phase4_nl_generic_usda_v1_20260822"
MAPPING_VERSION = "phase4_usda_v1"
REVIEWED_AT = "2026-08-22T00:00:00Z"
RETRIEVED_AT = "2026-08-22T00:00:00Z"
LICENSE_CODE = "CC0-1.0"
ATTRIBUTION_URL = "https://fdc.nal.usda.gov/"
ACCEPTED_DATA_TYPES = {"Foundation", "Survey (FNDDS)", "SR Legacy"}
NUTRIENT_IDS = {
    "protein": 1003,
    "fat": 1004,
    "carbohydrates": 1005,
    "fiber": 1079,
    "energy_legacy_kcal": 1008,
    "energy_atwater_general_kcal": 2047,
    "energy_atwater_specific_kcal": 2048,
    "energy_kj": 1062,
}

SOURCE_SPECS = {
    "Foundation": {
        "relative_json": "foundation/FoodData_Central_foundation_food_json_2026-04-30.json",
        "json_key": "FoundationFoods",
        "archive": "foundation-2026-04-30.zip",
        "archive_sha256": "186E988EC542E913F51EF62B86A47758E8CDD0D1DC3889E7B055581F3C09C77A",
        "source_version": "foundation_2026-04-30",
        "download_url": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_json_2026-04-30.zip",
    },
    "Survey (FNDDS)": {
        "relative_json": "fndds/surveyDownload.json",
        "json_key": "SurveyFoods",
        "archive": "fndds-2024-10-31.zip",
        "archive_sha256": "DFB06AE7DDC397CCD570B91C14B75438AB2BA39F64F22D321F61D4A52A77F3EB",
        "source_version": "fndds_2021-2023_release_2024-10-31",
        "download_url": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_survey_food_json_2024-10-31.zip",
    },
    "SR Legacy": {
        "relative_json": "sr/FoodData_Central_sr_legacy_food_json_2018-04.json",
        "json_key": "SRLegacyFoods",
        "archive": "sr-legacy-2018-04.zip",
        "archive_sha256": "0FE8AE486A2C8EB42CB96413F058DEB51863A46C8FB8EEB4B1FB45006DD338EF",
        "source_version": "sr_legacy_2018-04",
        "download_url": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_json_2018-04.zip",
    },
}


@dataclass(frozen=True)
class Selection:
    fdc_id: int
    category: str
    preparation_state: str
    dutch_label: str
    aliases: tuple[str, ...]
    pair_key: str | None = None
    preferred_aliases: tuple[str, ...] = ()
    reviewer_notes: str = "USDA identity retained; Dutch terms preserve the source meaning."


SELECTED = (
    Selection(2646170, "protein", "raw", "Kipfilet, rauw", ("rauwe kipfilet",), "chicken_breast"),
    Selection(331960, "protein", "cooked", "Kipfilet, bereid", ("kipfilet", "kipfilet gebakken"), "chicken_breast", ("kipfilet",), "Prepared skinless chicken breast is the intentional default for the ambiguous NL alias kipfilet."),
    Selection(2514747, "protein", "raw", "Kalkoengehakt, rauw", ("rauw kalkoengehakt",), "ground_turkey"),
    Selection(746785, "protein", "cooked", "Kalkoengehakt, bereid", ("kalkoengehakt",), "ground_turkey", ("kalkoengehakt",), "Prepared 93% lean ground turkey is the intentional default for kalkoengehakt."),
    Selection(746760, "protein", "raw", "Mager rundvlees, rauw", ("rauw mager rundvlees",), "lean_beef"),
    Selection(168741, "protein", "cooked", "Mager rundvlees, bereid", ("mager rundvlees",), "lean_beef", ("mager rundvlees",), "Prepared lean top-round beef is the intentional default for mager rundvlees."),
    Selection(2514743, "protein", "raw", "Mager rundergehakt 90%, rauw", ("rundergehakt 90 procent",)),
    Selection(748967, "protein", "raw", "Ei, heel", ("ei",)),
    Selection(747997, "protein", "raw", "Eiwit", ("eiwit rauw",)),
    Selection(2684441, "protein", "raw", "Zalm, rauw", ("rauwe zalm",), "atlantic_salmon"),
    Selection(175168, "protein", "cooked", "Zalm, bereid", ("zalm",), "atlantic_salmon", ("zalm",), "Prepared Atlantic salmon is the intentional default for the ambiguous NL alias zalm."),

    Selection(2346384, "dairy", "ready_to_eat", "Cottage cheese, volvet", ("cottage cheese",)),
    Selection(330137, "dairy", "ready_to_eat", "Griekse yoghurt, mager", ("magere griekse yoghurt",)),
    Selection(2647437, "dairy", "ready_to_eat", "Yoghurt naturel, mager", ("magere yoghurt",)),
    Selection(2259793, "dairy", "ready_to_eat", "Yoghurt naturel, vol", ("volle yoghurt",)),
    Selection(746776, "dairy", "ready_to_drink", "Magere melk", ("melk 0 procent vet",)),
    Selection(746778, "dairy", "ready_to_drink", "Melk, 2% vet", ("halfvolle melk", "melk"), None, ("melk",), "USDA 2% reduced-fat milk is the closest approved generic record; the label keeps 2% explicit. It is the intentional generic melk default."),
    Selection(746782, "dairy", "ready_to_drink", "Volle melk", ("melk 3,25 procent vet",)),

    Selection(2512381, "carbohydrates", "dry", "Witte rijst, droog", ("rijst droog",), "white_rice"),
    Selection(168878, "carbohydrates", "cooked", "Witte rijst, gekookt", ("rijst gekookt", "rijst"), "white_rice", ("rijst",), "Cooked white long-grain rice is the intentional default for the ambiguous NL alias rijst."),
    Selection(2512380, "carbohydrates", "dry", "Zilvervliesrijst, droog", ("bruine rijst droog",), "brown_rice"),
    Selection(2708414, "carbohydrates", "cooked", "Zilvervliesrijst, gekookt", ("bruine rijst gekookt",), "brown_rice"),
    Selection(169736, "carbohydrates", "dry", "Pasta, droog", ("droge pasta",), "pasta"),
    Selection(169737, "carbohydrates", "cooked", "Pasta, gekookt", ("gekookte pasta", "pasta"), "pasta", ("pasta",), "Cooked plain pasta is the intentional default for the ambiguous NL alias pasta."),
    Selection(169738, "carbohydrates", "dry", "Volkoren pasta, droog", ("droge volkoren pasta",), "whole_wheat_pasta"),
    Selection(168910, "carbohydrates", "cooked", "Volkoren pasta, gekookt", ("gekookte volkoren pasta",), "whole_wheat_pasta"),
    Selection(2708489, "carbohydrates", "dry", "Havermout", ("havervlokken",)),
    Selection(172688, "carbohydrates", "ready_to_eat", "Volkoren brood", ("volkorenbrood",)),
    Selection(174924, "carbohydrates", "ready_to_eat", "Wit brood", ("witte boterham",)),
    Selection(170026, "carbohydrates", "raw", "Aardappel, rauw", ("rauwe aardappel",), "potato"),
    Selection(170440, "carbohydrates", "cooked", "Aardappel, gekookt", ("gekookte aardappel", "aardappel"), "potato", ("aardappel",), "Boiled potato without skin is the intentional default for the ambiguous NL alias aardappel."),
    Selection(168482, "carbohydrates", "raw", "Zoete aardappel, rauw", ("rauwe zoete aardappel",), "sweet_potato"),
    Selection(168483, "carbohydrates", "cooked", "Zoete aardappel, bereid", ("zoete aardappel",), "sweet_potato", ("zoete aardappel",), "Baked sweet-potato flesh is the intentional default for zoete aardappel."),
    Selection(168917, "carbohydrates", "cooked", "Quinoa, gekookt", ("gekookte quinoa",)),
    Selection(169700, "carbohydrates", "cooked", "Couscous, gekookt", ("gekookte couscous",)),

    Selection(173944, "fruit", "raw", "Banaan", ("bananen",)),
    Selection(171688, "fruit", "raw", "Appel met schil", ("appel",)),
    Selection(169097, "fruit", "raw", "Sinaasappel", ("sinaasappels",)),
    Selection(167762, "fruit", "raw", "Aardbeien", ("aardbei",)),
    Selection(171711, "fruit", "raw", "Blauwe bessen", ("blauwe bes",)),
    Selection(174683, "fruit", "raw", "Druiven", ("druif",)),
    Selection(169118, "fruit", "raw", "Peer", ("peren",)),
    Selection(2710831, "fruit", "raw", "Kiwi, geschild", ("kiwi",)),

    Selection(747447, "vegetables", "raw", "Broccoli, rauw", ("broccoli",)),
    Selection(168462, "vegetables", "raw", "Spinazie, rauw", ("spinazie",)),
    Selection(170108, "vegetables", "raw", "Rode paprika, rauw", ("paprika",)),
    Selection(170457, "vegetables", "raw", "Tomaat, rauw", ("tomaat",)),
    Selection(168409, "vegetables", "raw", "Komkommer met schil", ("komkommer",)),
    Selection(2258586, "vegetables", "raw", "Wortel, rauw", ("wortel",)),
    Selection(2685573, "vegetables", "raw", "Bloemkool, rauw", ("bloemkool",)),
    Selection(2346400, "vegetables", "raw", "Sperziebonen, rauw", ("sperzieboon",)),
    Selection(169291, "vegetables", "raw", "Courgette, rauw", ("courgette",)),
    Selection(790646, "vegetables", "raw", "Ui, rauw", ("ui",)),

    Selection(171413, "fats_basics", "ready_to_use", "Olijfolie", ("olijfolie om te bakken",)),
    Selection(171705, "fats_basics", "raw", "Avocado", ("avocado rauw",)),
    Selection(2262072, "fats_basics", "ready_to_eat", "Pindakaas, glad", ("pindakaas",)),
    Selection(173430, "fats_basics", "ready_to_use", "Boter, ongezouten", ("ongezouten boter",)),
    Selection(2346393, "fats_basics", "raw", "Amandelen, rauw", ("amandelen",)),
    Selection(2346394, "fats_basics", "raw", "Walnoten, rauw", ("walnoten",)),
    Selection(170554, "fats_basics", "dried", "Chiazaad, gedroogd", ("chiazaad",)),

    Selection(173757, "legumes", "cooked", "Kikkererwten, gekookt", ("gekookte kikkererwten",)),
    Selection(172421, "legumes", "cooked", "Linzen, gekookt", ("gekookte linzen",)),
    Selection(173740, "legumes", "cooked", "Kidneybonen, gekookt", ("rode kidneybonen",)),
    Selection(321358, "legumes", "ready_to_eat", "Hummus", ("hoemoes",)),
)

REQUIRED_SEARCH_TERMS = (
    "kipfilet", "rijst", "havermout", "banaan", "broccoli", "olijfolie",
    "ei", "appel", "aardappel", "melk", "volkoren brood", "halfvolle melk",
)

COVERAGE_GAPS = (
    {
        "term": "magere kwark",
        "reason": "No approved generic USDA identity preserves Dutch quark composition and product meaning.",
    },
    {
        "term": "halfvolle kwark",
        "reason": "No approved generic USDA identity preserves Dutch quark composition and product meaning.",
    },
    {
        "term": "skyr",
        "reason": "No defensible generic non-branded USDA Skyr identity exists in the pinned accepted datasets.",
    },
    {
        "term": "specific Dutch bread types",
        "reason": "Volkorenbrood is covered generically; Dutch product-specific breads require a later approved local source.",
    },
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def canonical_value(value: object) -> object:
    if isinstance(value, dict):
        return {key: canonical_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonical_value(item) for item in value]
    if isinstance(value, tuple):
        return [canonical_value(item) for item in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def canonical_json(value: object) -> bytes:
    return json.dumps(canonical_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalize_alias(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", value.lower(), flags=re.UNICODE)).strip()


def iso_date(value: str) -> str:
    return datetime.strptime(value, "%m/%d/%Y").strftime("%Y-%m-%dT00:00:00Z")


def nutrient_map(food: dict) -> dict[int, tuple[float, str]]:
    result: dict[int, tuple[float, str]] = {}
    for item in food.get("foodNutrients", []):
        nutrient = item.get("nutrient") or {}
        nutrient_id = item.get("nutrientId", nutrient.get("id"))
        amount = item.get("value", item.get("amount"))
        if nutrient_id is None or amount is None:
            continue
        nutrient_id = int(nutrient_id)
        if nutrient_id in result:
            continue
        unit = str(item.get("unitName", nutrient.get("unitName", ""))).upper()
        result[nutrient_id] = (float(amount), unit)
    return result


def round_value(value: float) -> float:
    return round(value + 1e-12, 3)


def normalize_nutrients(food: dict) -> tuple[dict, dict]:
    values = nutrient_map(food)
    data_type = food["dataType"]
    preferred_energy = (
        ((2048, "2048_kcal"), (2047, "2047_kcal"), (1008, "1008_kcal"))
        if data_type == "Foundation"
        else ((1008, "1008_kcal"),)
    )
    energy = None
    derivation = None
    for nutrient_id, label in preferred_energy:
        if nutrient_id in values:
            energy, unit = values[nutrient_id]
            if unit and unit != "KCAL":
                raise ValueError(f"FDC {food['fdcId']} has invalid kcal unit {unit}")
            derivation = label
            break
    if energy is None and 1062 in values:
        energy, unit = values[1062]
        if unit and unit != "KJ":
            raise ValueError(f"FDC {food['fdcId']} has invalid kJ unit {unit}")
        energy /= 4.184
        derivation = "1062_kj_converted"
    if energy is None or not 0 <= energy <= 1500:
        raise ValueError(f"FDC {food['fdcId']} lacks valid energy")

    result = {"kcal": round_value(energy)}
    for name, nutrient_id in (("protein", 1003), ("carbohydrates", 1005), ("fat", 1004)):
        if nutrient_id not in values:
            raise ValueError(f"FDC {food['fdcId']} lacks required nutrient {nutrient_id}")
        amount, unit = values[nutrient_id]
        if unit and unit not in {"G", "GRAM"}:
            raise ValueError(f"FDC {food['fdcId']} has invalid {name} unit {unit}")
        if not 0 <= amount <= 100:
            raise ValueError(f"FDC {food['fdcId']} has invalid {name} value {amount}")
        result[name] = round_value(amount)
    if 1079 in values:
        fiber, unit = values[1079]
        if unit and unit not in {"G", "GRAM"}:
            raise ValueError(f"FDC {food['fdcId']} has invalid fiber unit {unit}")
        if not 0 <= fiber <= 100:
            raise ValueError(f"FDC {food['fdcId']} has invalid fiber value {fiber}")
        result["fiber"] = round_value(fiber)
    else:
        result["fiber"] = None
    return result, {"energy": derivation, "reference_basis": "per_100_g"}


def load_sources(source_root: Path) -> tuple[dict[int, dict], list[dict]]:
    records: dict[int, dict] = {}
    source_metadata = []
    for data_type, spec in SOURCE_SPECS.items():
        archive_path = source_root / spec["archive"]
        archive_hash = sha256_bytes(archive_path.read_bytes())
        if archive_hash != spec["archive_sha256"]:
            raise ValueError(f"Pinned source archive hash mismatch for {archive_path.name}")
        json_path = source_root / spec["relative_json"]
        json_bytes = json_path.read_bytes()
        payload = json.loads(json_bytes.decode("utf-8"))
        for food in payload[spec["json_key"]]:
            if isinstance(food, dict):
                records[int(food["fdcId"])] = food
        source_metadata.append({
            "data_type": data_type,
            "source_version": spec["source_version"],
            "download_url": spec["download_url"],
            "archive_filename": spec["archive"],
            "archive_sha256": archive_hash,
            "json_filename": Path(spec["relative_json"]).name,
            "json_sha256": sha256_bytes(json_bytes),
        })
    return records, source_metadata


def alias_record(food_id: uuid.UUID, food: dict, selection: Selection, alias: str, alias_type: str, language: str, priority: int, preferred: bool) -> dict:
    market = "NL" if language == "nl" else None
    normalized = normalize_alias(alias)
    alias_id = uuid.uuid5(food_id, f"food_alias:{language}:{market or ''}:{normalized}")
    source_spec = SOURCE_SPECS[food["dataType"]]
    return {
        "alias_id": str(alias_id),
        "language_code": language,
        "alias": alias,
        "normalized_alias": normalized,
        "alias_type": alias_type,
        "review_status": "reviewed",
        "source_provider": "usda_fdc",
        "source_version": source_spec["source_version"],
        "license_code": LICENSE_CODE,
        "market_code": market,
        "priority": priority,
        "is_preferred": preferred,
        "source_updated_at": iso_date(food["publicationDate"]),
        "provenance": {
            "provider": "usda_fdc",
            "provider_food_id": str(food["fdcId"]),
            "source_description": food["description"],
            "curation": "FitMetZorge Dutch alias review",
            "reviewed_at": REVIEWED_AT,
        },
        "metadata": {
            "dutch_display_label": alias == selection.dutch_label,
            "preparation_state": selection.preparation_state,
        },
    }


def build_manifest(source_root: Path) -> dict:
    source_records, source_metadata = load_sources(source_root)
    foods = []
    for selection in SELECTED:
        food = source_records.get(selection.fdc_id)
        if not food:
            raise ValueError(f"Selected FDC ID {selection.fdc_id} is missing")
        if food.get("dataType") not in ACCEPTED_DATA_TYPES:
            raise ValueError(f"FDC {selection.fdc_id} has disallowed data type")
        if food.get("brandOwner") or food.get("brandName"):
            raise ValueError(f"FDC {selection.fdc_id} has branded identity")
        nutrients, derivation = normalize_nutrients(food)
        canonical_id = uuid.uuid5(PROVIDER_NAMESPACE, f"usda_fdc:{selection.fdc_id}")
        aliases = [
            alias_record(canonical_id, food, selection, selection.dutch_label, "primary", "nl", 90, selection.dutch_label in selection.preferred_aliases)
        ]
        for offset, alias in enumerate(selection.aliases):
            aliases.append(alias_record(canonical_id, food, selection, alias, "search", "nl", 80 - offset, alias in selection.preferred_aliases))
        aliases.append(alias_record(canonical_id, food, selection, food["description"], "provider", "en", 20, False))
        source_spec = SOURCE_SPECS[food["dataType"]]
        record = {
            "canonical_uuid": str(canonical_id),
            "fdc_id": str(selection.fdc_id),
            "usda_data_type": food["dataType"],
            "usda_source_description": food["description"],
            "usda_food_category": (food.get("foodCategory") or {}).get("description"),
            "category": selection.category,
            "preparation_state": selection.preparation_state,
            "pair_key": selection.pair_key,
            "canonical_slug": f"usda-fdc-{selection.fdc_id}",
            "canonical_name": food["description"],
            "dutch_display_label": selection.dutch_label,
            "aliases": aliases,
            "nutrition_per_100_g": nutrients,
            "source_version": source_spec["source_version"],
            "source_updated_at": iso_date(food["publicationDate"]),
            "retrieved_at": RETRIEVED_AT,
            "mapping_version": MAPPING_VERSION,
            "license": LICENSE_CODE,
            "attribution": {
                "label": "USDA FoodData Central",
                "url": ATTRIBUTION_URL,
            },
            "nutrient_derivation": derivation,
            "reviewer_decision": "include",
            "reviewer_notes": selection.reviewer_notes,
        }
        record["checksum"] = sha256_bytes(canonical_json(record))
        foods.append(record)

    foods.sort(key=lambda item: (item["category"], item["dutch_display_label"].lower(), item["fdc_id"]))
    alias_count = sum(len(food["aliases"]) for food in foods)
    preferred = [
        {
            "alias": alias["alias"],
            "normalized_alias": alias["normalized_alias"],
            "food_uuid": food["canonical_uuid"],
            "dutch_display_label": food["dutch_display_label"],
            "decision": food["reviewer_notes"],
        }
        for food in foods
        for alias in food["aliases"]
        if alias["is_preferred"]
    ]
    pair_map: dict[str, list[dict]] = {}
    for food in foods:
        if food["pair_key"]:
            pair_map.setdefault(food["pair_key"], []).append({
                "food_uuid": food["canonical_uuid"],
                "fdc_id": food["fdc_id"],
                "preparation_state": food["preparation_state"],
                "dutch_display_label": food["dutch_display_label"],
            })
    manifest = {
        "artifact_version": ARTIFACT_VERSION,
        "ingestion_id": str(INGESTION_ID),
        "source_provider": "usda_fdc",
        "mapping_version": MAPPING_VERSION,
        "reviewed_by": "FitMetZorge USDA detail-record curation",
        "reviewed_at": REVIEWED_AT,
        "retrieval_date": RETRIEVED_AT,
        "provider_candidate_uuid_namespace": str(PROVIDER_NAMESPACE),
        "provider_identity_format": "usda_fdc:<fdcId>",
        "license": LICENSE_CODE,
        "attribution_url": ATTRIBUTION_URL,
        "source_archives": source_metadata,
        "manifest_food_count": len(foods),
        "manifest_alias_count": alias_count,
        "expected_portion_count": 0,
        "category_counts": {category: sum(food["category"] == category for food in foods) for category in sorted({food["category"] for food in foods})},
        "preferred_ambiguous_aliases": preferred,
        "raw_cooked_pairs": [{"pair_key": key, "members": members} for key, members in sorted(pair_map.items())],
        "required_search_terms": list(REQUIRED_SEARCH_TERMS),
        "coverage_gaps": list(COVERAGE_GAPS),
        "foods": foods,
    }
    manifest["records_sha256"] = sha256_bytes(canonical_json(foods))
    return manifest


def sql_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_seed(manifest: dict, manifest_sha: str) -> str:
    embedded = sql_json(manifest)
    food_count = manifest["manifest_food_count"]
    alias_count = manifest["manifest_alias_count"]
    return f"""-- FitMetZorge Phase 4 Nutrition - Slice 4E Dutch Catalog Seed
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- Exact manifest SHA-256: {manifest_sha}
-- Owner-reviewed execution artifact. No portions, custom-food mutation, provider call,
-- legacy mutation, trainer access, frontend change, Edge change, AI or production action.

begin;

do $fmz_catalog_seed$
declare
  v_manifest constant jsonb := $fmz_catalog_manifest${embedded}$fmz_catalog_manifest$::jsonb;
  v_ingestion_id constant uuid := '{manifest['ingestion_id']}'::uuid;
  v_artifact_sha constant text := '{manifest_sha}';
  v_food_count constant integer := {food_count};
  v_alias_count constant integer := {alias_count};
  v_existing jsonb;
begin
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('fmz_phase4_catalog_seed:' || v_artifact_sha, 0)
  );

  if v_manifest->>'artifact_version' <> '{ARTIFACT_VERSION}'
     or v_manifest->>'mapping_version' <> '{MAPPING_VERSION}'
     or (v_manifest->>'manifest_food_count')::integer <> v_food_count
     or (v_manifest->>'manifest_alias_count')::integer <> v_alias_count then
    raise exception 'catalog manifest identity or count mismatch' using errcode = '22023';
  end if;

  if exists (
    select 1 from public.nutrition_food_ingestions i
    where i.source_provider = 'usda_fdc' and i.id <> v_ingestion_id
  ) then
    raise exception 'unexpected predecessor state for first USDA catalog artifact' using errcode = '55000';
  end if;

  insert into public.nutrition_food_ingestions (
    id, artifact_version, artifact_sha256, source_provider, mapping_version,
    status, predecessor_ingestion_id, manifest_food_count, manifest_alias_count,
    reviewed_by, reviewed_at, imported_at, provenance, metadata
  )
  values (
    v_ingestion_id, '{ARTIFACT_VERSION}', v_artifact_sha, 'usda_fdc', '{MAPPING_VERSION}',
    'reviewed', null, v_food_count, v_alias_count,
    'FitMetZorge USDA detail-record curation', '{REVIEWED_AT}'::timestamptz, null,
    pg_catalog.jsonb_build_object(
      'provider', 'usda_fdc',
      'records_sha256', v_manifest->>'records_sha256',
      'source_archives', v_manifest->'source_archives',
      'license', '{LICENSE_CODE}',
      'attribution_url', '{ATTRIBUTION_URL}'
    ),
    pg_catalog.jsonb_build_object('expected_portion_count', 0, 'catalog_locale', 'nl-NL')
  )
  on conflict do nothing;

  select pg_catalog.jsonb_build_object(
    'id', i.id, 'artifact_version', i.artifact_version, 'artifact_sha256', i.artifact_sha256,
    'source_provider', i.source_provider, 'mapping_version', i.mapping_version,
    'predecessor_ingestion_id', i.predecessor_ingestion_id,
    'manifest_food_count', i.manifest_food_count, 'manifest_alias_count', i.manifest_alias_count,
    'reviewed_by', i.reviewed_by, 'reviewed_at', i.reviewed_at
  ) into v_existing
  from public.nutrition_food_ingestions i where i.id = v_ingestion_id;

  if v_existing is distinct from pg_catalog.jsonb_build_object(
    'id', v_ingestion_id, 'artifact_version', '{ARTIFACT_VERSION}', 'artifact_sha256', v_artifact_sha,
    'source_provider', 'usda_fdc', 'mapping_version', '{MAPPING_VERSION}',
    'predecessor_ingestion_id', null, 'manifest_food_count', v_food_count,
    'manifest_alias_count', v_alias_count, 'reviewed_by', 'FitMetZorge USDA detail-record curation',
    'reviewed_at', '{REVIEWED_AT}'::timestamptz
  ) then
    raise exception 'existing ingestion identity differs from reviewed manifest' using errcode = '55000';
  end if;

  insert into public.foods (
    id, owner_user_id, catalog_scope, canonical_slug, name, brand, barcode,
    source_provider, provider_food_id, source_version, license_code, provenance,
    quality_status, reference_amount, reference_unit, reference_mass_grams,
    reference_volume_ml, density_g_per_ml, energy_kcal, protein_grams,
    carbohydrate_grams, fat_grams, fiber_grams, status, source_updated_at,
    metadata, ingestion_id
  )
  select
    (f->>'canonical_uuid')::uuid, null, 'canonical', f->>'canonical_slug',
    f->>'canonical_name', null, null, 'usda_fdc', f->>'fdc_id', f->>'source_version',
    '{LICENSE_CODE}',
    pg_catalog.jsonb_build_object(
      'provider', 'usda_fdc', 'provider_food_id', f->>'fdc_id',
      'data_type', f->>'usda_data_type', 'source_description', f->>'usda_source_description',
      'source_version', f->>'source_version', 'source_updated_at', f->>'source_updated_at',
      'retrieved_at', f->>'retrieved_at', 'mapping_version', f->>'mapping_version',
      'nutrient_derivation', f->'nutrient_derivation', 'attribution', f->'attribution'
    ),
    'reviewed', 100, 'g', 100, null, null,
    (f->'nutrition_per_100_g'->>'kcal')::numeric,
    (f->'nutrition_per_100_g'->>'protein')::numeric,
    (f->'nutrition_per_100_g'->>'carbohydrates')::numeric,
    (f->'nutrition_per_100_g'->>'fat')::numeric,
    case when f->'nutrition_per_100_g'->'fiber' = 'null'::jsonb then null else (f->'nutrition_per_100_g'->>'fiber')::numeric end,
    'active', (f->>'source_updated_at')::timestamptz,
    pg_catalog.jsonb_build_object(
      'category', f->>'category', 'preparation_state', f->>'preparation_state',
      'pair_key', f->'pair_key', 'dutch_display_label', f->>'dutch_display_label',
      'usda_food_category', f->'usda_food_category', 'manifest_record_sha256', f->>'checksum'
    ),
    v_ingestion_id
  from pg_catalog.jsonb_array_elements(v_manifest->'foods') f
  on conflict do nothing;

  if exists (
    select 1
    from pg_catalog.jsonb_array_elements(v_manifest->'foods') f
    left join public.foods actual on actual.id = (f->>'canonical_uuid')::uuid
    where actual.id is null
       or pg_catalog.jsonb_build_object(
         'canonical_uuid', actual.id, 'canonical_slug', actual.canonical_slug,
         'canonical_name', actual.name, 'brand', actual.brand, 'catalog_scope', actual.catalog_scope,
         'source_provider', actual.source_provider, 'fdc_id', actual.provider_food_id,
         'source_version', actual.source_version, 'license_code', actual.license_code,
         'quality_status', actual.quality_status, 'reference_amount', actual.reference_amount,
         'reference_unit', actual.reference_unit, 'reference_mass_grams', actual.reference_mass_grams,
         'energy_kcal', actual.energy_kcal, 'protein_grams', actual.protein_grams,
         'carbohydrate_grams', actual.carbohydrate_grams, 'fat_grams', actual.fat_grams,
         'fiber_grams', actual.fiber_grams, 'status', actual.status,
         'source_updated_at', actual.source_updated_at, 'ingestion_id', actual.ingestion_id,
         'provenance', actual.provenance, 'metadata', actual.metadata
       ) is distinct from pg_catalog.jsonb_build_object(
         'canonical_uuid', (f->>'canonical_uuid')::uuid, 'canonical_slug', f->>'canonical_slug',
         'canonical_name', f->>'canonical_name', 'brand', null, 'catalog_scope', 'canonical',
         'source_provider', 'usda_fdc', 'fdc_id', f->>'fdc_id',
         'source_version', f->>'source_version', 'license_code', '{LICENSE_CODE}',
         'quality_status', 'reviewed', 'reference_amount', 100::numeric,
         'reference_unit', 'g', 'reference_mass_grams', 100::numeric,
         'energy_kcal', (f->'nutrition_per_100_g'->>'kcal')::numeric,
         'protein_grams', (f->'nutrition_per_100_g'->>'protein')::numeric,
         'carbohydrate_grams', (f->'nutrition_per_100_g'->>'carbohydrates')::numeric,
         'fat_grams', (f->'nutrition_per_100_g'->>'fat')::numeric,
         'fiber_grams', case when f->'nutrition_per_100_g'->'fiber' = 'null'::jsonb then null else (f->'nutrition_per_100_g'->>'fiber')::numeric end,
         'status', 'active', 'source_updated_at', (f->>'source_updated_at')::timestamptz,
         'ingestion_id', v_ingestion_id,
         'provenance', pg_catalog.jsonb_build_object(
           'provider', 'usda_fdc', 'provider_food_id', f->>'fdc_id',
           'data_type', f->>'usda_data_type', 'source_description', f->>'usda_source_description',
           'source_version', f->>'source_version', 'source_updated_at', f->>'source_updated_at',
           'retrieved_at', f->>'retrieved_at', 'mapping_version', f->>'mapping_version',
           'nutrient_derivation', f->'nutrient_derivation', 'attribution', f->'attribution'
         ),
         'metadata', pg_catalog.jsonb_build_object(
           'category', f->>'category', 'preparation_state', f->>'preparation_state',
           'pair_key', f->'pair_key', 'dutch_display_label', f->>'dutch_display_label',
           'usda_food_category', f->'usda_food_category', 'manifest_record_sha256', f->>'checksum'
         )
       )
  ) then
    raise exception 'existing canonical food differs from reviewed manifest' using errcode = '55000';
  end if;

  insert into public.food_aliases (
    id, food_id, language_code, alias, normalized_alias, alias_type, review_status,
    source_provider, source_version, license_code, market_code, priority, provenance,
    source_updated_at, metadata, status, ingestion_id, is_preferred
  )
  select
    (a->>'alias_id')::uuid, (f->>'canonical_uuid')::uuid, a->>'language_code',
    a->>'alias', a->>'normalized_alias', a->>'alias_type', a->>'review_status',
    a->>'source_provider', a->>'source_version', a->>'license_code', a->>'market_code',
    (a->>'priority')::smallint, a->'provenance', (a->>'source_updated_at')::timestamptz,
    a->'metadata', 'active', v_ingestion_id, (a->>'is_preferred')::boolean
  from pg_catalog.jsonb_array_elements(v_manifest->'foods') f
  cross join lateral pg_catalog.jsonb_array_elements(f->'aliases') a
  on conflict do nothing;

  if exists (
    select 1
    from pg_catalog.jsonb_array_elements(v_manifest->'foods') f
    cross join lateral pg_catalog.jsonb_array_elements(f->'aliases') a
    left join public.food_aliases actual on actual.id = (a->>'alias_id')::uuid
    where actual.id is null
       or pg_catalog.jsonb_build_object(
         'id', actual.id, 'food_id', actual.food_id, 'language_code', actual.language_code,
         'alias', actual.alias, 'normalized_alias', actual.normalized_alias,
         'alias_type', actual.alias_type, 'review_status', actual.review_status,
         'source_provider', actual.source_provider, 'source_version', actual.source_version,
         'license_code', actual.license_code, 'market_code', actual.market_code,
         'priority', actual.priority, 'provenance', actual.provenance,
         'source_updated_at', actual.source_updated_at, 'metadata', actual.metadata,
         'status', actual.status, 'ingestion_id', actual.ingestion_id,
         'is_preferred', actual.is_preferred
       ) is distinct from pg_catalog.jsonb_build_object(
         'id', (a->>'alias_id')::uuid, 'food_id', (f->>'canonical_uuid')::uuid,
         'language_code', a->>'language_code', 'alias', a->>'alias',
         'normalized_alias', a->>'normalized_alias', 'alias_type', a->>'alias_type',
         'review_status', a->>'review_status', 'source_provider', a->>'source_provider',
         'source_version', a->>'source_version', 'license_code', a->>'license_code',
         'market_code', a->>'market_code', 'priority', (a->>'priority')::smallint,
         'provenance', a->'provenance', 'source_updated_at', (a->>'source_updated_at')::timestamptz,
         'metadata', a->'metadata', 'status', 'active', 'ingestion_id', v_ingestion_id,
         'is_preferred', (a->>'is_preferred')::boolean
       )
  ) then
    raise exception 'existing food alias differs from reviewed manifest' using errcode = '55000';
  end if;

  if (select pg_catalog.count(*) from public.foods where ingestion_id = v_ingestion_id) <> v_food_count
     or (select pg_catalog.count(*) from public.food_aliases where ingestion_id = v_ingestion_id) <> v_alias_count then
    raise exception 'catalog import count mismatch' using errcode = '55000';
  end if;

  if exists (
    select 1 from public.food_portions p
    join public.foods f on f.id = p.food_id
    where f.ingestion_id = v_ingestion_id
  ) then
    raise exception 'initial catalog artifact must not create portions' using errcode = '55000';
  end if;

  update public.nutrition_food_ingestions
  set status = 'imported', imported_at = pg_catalog.clock_timestamp()
  where id = v_ingestion_id and status = 'reviewed';

  if not exists (
    select 1 from public.nutrition_food_ingestions
    where id = v_ingestion_id and status = 'imported' and imported_at is not null
  ) then
    raise exception 'catalog ingestion did not reach imported state' using errcode = '55000';
  end if;
end;
$fmz_catalog_seed$;

commit;
"""


def build_verifier(manifest: dict, manifest_sha: str) -> str:
    embedded = sql_json(manifest)
    return f"""-- FitMetZorge Phase 4 Nutrition - Slice 4E Dutch Catalog Post-Import Verifier
-- STAGING ONLY: mokxyyullfhkfalopbzd
-- READ-ONLY: one SELECT/CTE statement; no application RPC or provider call.

with
expected as (
  select $fmz_catalog_manifest${embedded}$fmz_catalog_manifest$::jsonb as manifest
),
identity as (
  select
    '{manifest['ingestion_id']}'::uuid as ingestion_id,
    '{manifest_sha}'::text as artifact_sha,
    {manifest['manifest_food_count']}::integer as food_count,
    {manifest['manifest_alias_count']}::integer as alias_count
),
expected_foods as (
  select rows.food
  from expected e
  cross join lateral pg_catalog.jsonb_array_elements(e.manifest->'foods') as rows(food)
),
expected_aliases as (
  select ef.food->>'canonical_uuid' as food_uuid, rows.alias
  from expected_foods ef
  cross join lateral pg_catalog.jsonb_array_elements(ef.food->'aliases') as rows(alias)
),
actual_ingestion as (
  select i.* from public.nutrition_food_ingestions i join identity x on x.ingestion_id = i.id
),
actual_foods as (
  select f.* from public.foods f join identity x on x.ingestion_id = f.ingestion_id
),
actual_aliases as (
  select a.* from public.food_aliases a join identity x on x.ingestion_id = a.ingestion_id
),
checks as (
  select * from (values
    ('ingestion_artifact_identity', exists (
      select 1 from actual_ingestion i cross join identity x
      where i.artifact_sha256 = x.artifact_sha and i.artifact_version = '{ARTIFACT_VERSION}'
        and i.source_provider = 'usda_fdc' and i.mapping_version = '{MAPPING_VERSION}'
        and i.status = 'imported' and i.imported_at is not null
        and i.manifest_food_count = x.food_count and i.manifest_alias_count = x.alias_count
    )),
    ('exact_food_count', (select pg_catalog.count(*) from actual_foods) = (select food_count from identity)),
    ('exact_alias_count', (select pg_catalog.count(*) from actual_aliases) = (select alias_count from identity)),
    ('all_expected_food_ids_and_provider_ids', not exists (
      select 1 from expected_foods ef
      left join actual_foods af on af.id = (ef.food->>'canonical_uuid')::uuid
      where af.id is null or af.provider_food_id <> ef.food->>'fdc_id'
    )),
    ('deterministic_uuid_manifest_contract', not exists (
      select 1 from expected_foods ef join actual_foods af on af.id = (ef.food->>'canonical_uuid')::uuid
      where af.provenance->>'provider_food_id' <> ef.food->>'fdc_id'
         or af.metadata->>'manifest_record_sha256' <> ef.food->>'checksum'
    )),
    ('reviewed_active_generic_usda_only', not exists (
      select 1 from actual_foods f
      where f.catalog_scope <> 'canonical' or f.owner_user_id is not null or f.status <> 'active'
         or f.quality_status not in ('reviewed', 'verified') or f.source_provider <> 'usda_fdc'
         or f.brand is not null or f.barcode is not null
    )),
    ('accepted_usda_datatypes_only', not exists (
      select 1 from actual_foods f
      where f.provenance->>'data_type' not in ('Foundation', 'Survey (FNDDS)', 'SR Legacy')
    )),
    ('per_100_gram_reference_contract', not exists (
      select 1 from actual_foods f
      where f.reference_amount <> 100 or f.reference_unit <> 'g' or f.reference_mass_grams <> 100
         or f.reference_volume_ml is not null or f.density_g_per_ml is not null
    )),
    ('nutrient_bounds_and_missing_fiber_preserved', not exists (
      select 1 from actual_foods f
      where f.energy_kcal < 0 or f.energy_kcal > 1500
         or f.protein_grams < 0 or f.protein_grams > 100
         or f.carbohydrate_grams < 0 or f.carbohydrate_grams > 100
         or f.fat_grams < 0 or f.fat_grams > 100
         or (f.fiber_grams is not null and (f.fiber_grams < 0 or f.fiber_grams > 100))
    )),
    ('provenance_mapping_license_attribution', not exists (
      select 1 from actual_foods f
      where f.license_code <> '{LICENSE_CODE}' or f.source_version is null
         or f.source_updated_at is null or f.provenance->>'mapping_version' <> '{MAPPING_VERSION}'
         or f.provenance->'attribution'->>'url' <> '{ATTRIBUTION_URL}'
         or f.provenance->'nutrient_derivation'->>'reference_basis' <> 'per_100_g'
    )),
    ('all_expected_aliases_linked', not exists (
      select 1 from expected_aliases ea
      left join actual_aliases aa on aa.id = (ea.alias->>'alias_id')::uuid
      where aa.id is null or aa.food_id <> ea.food_uuid::uuid
         or aa.normalized_alias <> ea.alias->>'normalized_alias'
         or aa.ingestion_id <> (select ingestion_id from identity)
    )),
    ('aliases_reviewed_active_and_attributed', not exists (
      select 1 from actual_aliases a
      where a.status <> 'active' or a.review_status not in ('reviewed', 'verified')
         or a.source_provider <> 'usda_fdc' or a.license_code <> '{LICENSE_CODE}'
         or a.provenance->>'provider_food_id' is null
    )),
    ('preferred_nl_alias_uniqueness', not exists (
      select 1 from actual_aliases a
      where a.is_preferred and (a.language_code <> 'nl' or a.market_code <> 'NL')
    ) and not exists (
      select 1 from actual_aliases a where a.is_preferred
      group by a.normalized_alias, a.market_code having pg_catalog.count(*) > 1
    )),
    ('required_dutch_search_terms_present', not exists (
      select 1
      from pg_catalog.jsonb_array_elements_text((select manifest->'required_search_terms' from expected)) as terms(term)
      where not exists (
        select 1 from actual_aliases a join actual_foods f on f.id = a.food_id
        where a.language_code = 'nl' and a.market_code = 'NL'
          and a.normalized_alias = terms.term and a.status = 'active'
          and a.review_status in ('reviewed', 'verified') and f.status = 'active'
      )
    )),
    ('raw_cooked_pairs_remain_distinct', not exists (
      select 1
      from pg_catalog.jsonb_array_elements((select manifest->'raw_cooked_pairs' from expected)) as pairs(pair)
      where pg_catalog.jsonb_array_length(pairs.pair->'members') <> 2
         or (select pg_catalog.count(distinct members.member->>'food_uuid') from pg_catalog.jsonb_array_elements(pairs.pair->'members') as members(member)) <> 2
         or not exists (select 1 from pg_catalog.jsonb_array_elements(pairs.pair->'members') as members(member) where members.member->>'preparation_state' in ('raw', 'dry'))
         or not exists (select 1 from pg_catalog.jsonb_array_elements(pairs.pair->'members') as members(member) where members.member->>'preparation_state' = 'cooked')
    )),
    ('zero_imported_portions', not exists (
      select 1 from public.food_portions p join actual_foods f on f.id = p.food_id
    )),
    ('custom_foods_untouched_by_ingestion', not exists (
      select 1 from public.foods f join identity x on x.ingestion_id = f.ingestion_id
      where f.catalog_scope = 'custom' or f.owner_user_id is not null
    )),
    ('no_unexpected_rows_linked_to_artifact',
      (select pg_catalog.count(*) from actual_foods) = (select pg_catalog.count(*) from expected_foods)
      and (select pg_catalog.count(*) from actual_aliases) = (select pg_catalog.count(*) from expected_aliases)
    )
  ) as c(check_name, pass)
),
result as (
  select
    pg_catalog.bool_and(pass) as overall_pass,
    pg_catalog.count(*) filter (where pass) as pass_count,
    pg_catalog.count(*) filter (where not pass) as fail_count,
    pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object('check', check_name, 'pass', pass) order by check_name) as checks
  from checks
)
select pg_catalog.jsonb_pretty(pg_catalog.jsonb_build_object(
  'overall_pass', overall_pass,
  'pass_count', pass_count,
  'fail_count', fail_count,
  'checks', checks
)) as verification_result
from result;
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()

    if len(SELECTED) != 64 or len({item.fdc_id for item in SELECTED}) != 64:
        raise ValueError("The reviewed selection must contain exactly 64 unique FDC IDs")

    manifest = build_manifest(args.source_root)
    catalog_dir = args.repo_root / "supabase" / "catalog"
    seed_dir = args.repo_root / "supabase" / "seeds"
    verification_dir = args.repo_root / "supabase" / "verification"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    seed_dir.mkdir(parents=True, exist_ok=True)
    verification_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = catalog_dir / "20260822_phase4_dutch_catalog_manifest.json"
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    manifest_sha = sha256_bytes(manifest_bytes)

    seed_path = seed_dir / "20260822_phase4_dutch_catalog_seed.sql"
    seed_path.write_text(build_seed(manifest, manifest_sha), encoding="utf-8", newline="\n")
    verifier_path = verification_dir / "20260822_phase4_dutch_catalog_import_verification.sql"
    verifier_path.write_text(build_verifier(manifest, manifest_sha), encoding="utf-8", newline="\n")

    print(json.dumps({
        "manifest": str(manifest_path),
        "manifest_sha256": manifest_sha,
        "food_count": manifest["manifest_food_count"],
        "alias_count": manifest["manifest_alias_count"],
        "ingestion_id": manifest["ingestion_id"],
        "seed": str(seed_path),
        "seed_sha256": sha256_bytes(seed_path.read_bytes()),
        "verifier": str(verifier_path),
        "verifier_sha256": sha256_bytes(verifier_path.read_bytes()),
    }, indent=2))


if __name__ == "__main__":
    main()
