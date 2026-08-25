"""Audit the corrected OFF artifacts against the invalidated Git baseline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
from collections import Counter
from pathlib import Path


OLD_HASHES = {
    "release": "281436E9EC5EDC31EC42814DA7237C85BFB41003865BF94CE0AABAB6740C8CEC",
    "products": "BA0AD94F3B83F15E48B0124E82B1C8027FDE2A97468446CCB8CB3D15453E1ABF",
    "names": "AE2336D03F2BF055241BF81EF06A98937871CC79B9E67CBEF48D613E588A0132",
    "importer": "3927F0F007ED4CFA1D89A01D2AEBE68F7541E4C03951CA71AC4DF2C4FA5801CC",
    "verifier": "A502967BD9B11C2830A9E311173CBC57B1B6FFB95EBF536340E29F4119FC1B12",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def git_bytes(root: Path, baseline_ref: str, relative_path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{baseline_ref}:{relative_path}"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout


def csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))


def stable_name_key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(value for key, value in row.items() if key not in {"id", "normalized_name"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--baseline-ref", default="HEAD")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    catalog = root / "supabase" / "catalog" / "20260825_phase4_off_catalog"
    paths = {
        "release": "supabase/catalog/20260825_phase4_off_catalog/20260825_phase4_off_release.json",
        "products": "supabase/catalog/20260825_phase4_off_catalog/20260825_phase4_off_products.csv",
        "names": "supabase/catalog/20260825_phase4_off_catalog/20260825_phase4_off_product_names.csv",
        "importer": "supabase/imports/20260825_phase4_off_catalog_import.psql",
        "verifier": "supabase/verification/20260825_phase4_nutrition_slice4f_off_catalog_import_verification.sql",
    }

    old_payloads = {name: git_bytes(root, args.baseline_ref, path) for name, path in paths.items()}
    for name, expected_hash in OLD_HASHES.items():
        if sha256_bytes(old_payloads[name]) != expected_hash:
            raise SystemExit(f"Invalid baseline hash for {name}")

    old_products = {row["id"]: row for row in csv_rows(old_payloads["products"])}
    new_products = {
        row["id"]: row
        for row in csv_rows((catalog / "20260825_phase4_off_products.csv").read_bytes())
    }
    if set(old_products) != set(new_products):
        raise SystemExit("Product UUID identity set changed")
    changed_products = [product_id for product_id in old_products if old_products[product_id] != new_products[product_id]]
    changed_brands = [
        product_id
        for product_id in changed_products
        if old_products[product_id]["normalized_brand"] != new_products[product_id]["normalized_brand"]
    ]

    old_names = csv_rows(old_payloads["names"])
    new_names = csv_rows((catalog / "20260825_phase4_off_product_names.csv").read_bytes())
    old_by_source = {stable_name_key(row): row for row in old_names}
    new_by_source = {stable_name_key(row): row for row in new_names}
    if len(old_by_source) != len(old_names) or len(new_by_source) != len(new_names):
        raise SystemExit("Name source identity is not unique")
    if set(old_by_source) != set(new_by_source):
        raise SystemExit("Name parent/source membership changed")
    changed_names = [key for key in old_by_source if old_by_source[key]["normalized_name"] != new_by_source[key]["normalized_name"]]
    changed_name_uuids = [key for key in old_by_source if old_by_source[key]["id"] != new_by_source[key]["id"]]

    if len(changed_products) != 1 or len(changed_brands) != 1:
        raise SystemExit("Unexpected corrected product/brand row count")
    if len(changed_names) != 23 or len(changed_name_uuids) != 23:
        raise SystemExit("Unexpected corrected name/UUID row count")
    if len(new_products) != 24_458 or len(new_names) != 74_184:
        raise SystemExit("Catalog count changed")
    if len({row["id"] for row in new_names}) != len(new_names):
        raise SystemExit("Duplicate name UUID after correction")
    if len({(row["product_id"], row["language_code"], row["name_type"], row["normalized_name"]) for row in new_names}) != len(new_names):
        raise SystemExit("Duplicate active name identity after correction")
    preferred = Counter((row["product_id"], row["language_code"]) for row in new_names if row["is_preferred"] == "true")
    if any(count > 1 for count in preferred.values()):
        raise SystemExit("Conflicting preferred names after correction")

    current_hashes = {
        "release": sha256_file(catalog / "20260825_phase4_off_release.json"),
        "products": sha256_file(catalog / "20260825_phase4_off_products.csv"),
        "names": sha256_file(catalog / "20260825_phase4_off_product_names.csv"),
        "manifest": sha256_file(catalog / "20260825_phase4_off_artifact_manifest.json"),
        "importer": sha256_file(root / paths["importer"]),
        "verifier": sha256_file(root / paths["verifier"]),
        "normalization_verifier": sha256_file(root / "supabase/verification/20260825_phase4_off_normalization_contract_verification.sql"),
    }
    if any(current_hashes[name] == OLD_HASHES[name] for name in OLD_HASHES):
        raise SystemExit("An invalidated artifact hash was retained")

    print(json.dumps({
        "status": "PASS",
        "affected_product_rows": len(changed_products),
        "affected_brand_rows": len(changed_brands),
        "affected_name_rows": len(changed_names),
        "affected_name_uuids": len(changed_name_uuids),
        "product_uuids_unchanged": len(new_products),
        "products": len(new_products),
        "names": len(new_names),
        "new_hashes": current_hashes,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
