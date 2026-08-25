"""Run the corrected OFF importer against a local schema-equivalent PostgreSQL."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path


def run_psql(psql: Path, root: Path, host: str, port: int, database: str, *arguments: str) -> str:
    result = subprocess.run(
        [
            str(psql),
            "-X",
            "-q",
            "-v",
            "ON_ERROR_STOP=1",
            "-h",
            host,
            "-p",
            str(port),
            "-U",
            "postgres",
            "-d",
            database,
            *arguments,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def catalog_snapshot(psql: Path, root: Path, host: str, port: int, database: str) -> dict[str, object]:
    sql = """
      select jsonb_build_object(
        'releases', (select count(*) from public.nutrition_off_catalog_releases),
        'products', (select count(*) from public.nutrition_off_products),
        'names', (select count(*) from public.nutrition_off_product_names),
        'imported_releases', (select count(*) from public.nutrition_off_catalog_releases where status = 'imported'),
        'product_ids', (select count(distinct id) from public.nutrition_off_products),
        'name_ids', (select count(distinct id) from public.nutrition_off_product_names),
        'usda_foods', (select count(*) from public.foods where catalog_scope = 'canonical' and source_provider = 'usda_fdc'),
        'usda_aliases', (select count(*) from public.food_aliases where source_provider = 'usda_fdc'),
        'custom_foods', (select count(*) from public.foods where catalog_scope = 'custom'),
        'food_logs', (select count(*) from public.food_logs),
        'food_log_items', (select count(*) from public.food_log_items)
      );
    """
    output = run_psql(psql, root, host, port, database, "-t", "-A", "-c", sql)
    return json.loads(output.splitlines()[-1])


def require_verifier_pass(output: str, label: str) -> None:
    if not re.search(r'"overall_pass"\s*:\s*true', output):
        raise SystemExit(f"{label} did not return overall_pass=true")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--psql", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--database", default="postgres")
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Dry run refuses every non-local PostgreSQL host")
    root = args.repo_root.resolve()
    importer = root / "supabase/imports/20260825_phase4_off_catalog_import.psql"
    post_verifier = root / "supabase/verification/20260825_phase4_nutrition_slice4f_off_catalog_import_verification.sql"
    normalization_verifier = root / "supabase/verification/20260825_phase4_off_normalization_contract_verification.sql"

    before = catalog_snapshot(args.psql, root, args.host, args.port, args.database)
    if any(before[key] != 0 for key in ("releases", "products", "names")):
        raise SystemExit("Local dry-run database is not import-empty")
    require_verifier_pass(
        run_psql(args.psql, root, args.host, args.port, args.database, "-t", "-A", "-f", str(normalization_verifier)),
        "Normalization contract verifier",
    )

    importer_text = importer.read_text(encoding="utf-8")
    rollback_text, replacements = re.subn(r"commit;\s*$", "rollback;\n", importer_text, count=1, flags=re.IGNORECASE)
    if replacements != 1:
        raise SystemExit("Importer does not end in one COMMIT")
    rollback_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            suffix=".psql",
            prefix="phase4-off-rollback-",
            dir=root,
            delete=False,
        ) as handle:
            handle.write(rollback_text)
            rollback_path = Path(handle.name)
        run_psql(args.psql, root, args.host, args.port, args.database, "-f", str(rollback_path))
    finally:
        if rollback_path is not None:
            rollback_path.unlink(missing_ok=True)
    after_rollback = catalog_snapshot(args.psql, root, args.host, args.port, args.database)
    if after_rollback != before:
        raise SystemExit("Rollback dry run changed local persistent state")

    run_psql(args.psql, root, args.host, args.port, args.database, "-f", str(importer))
    after_import = catalog_snapshot(args.psql, root, args.host, args.port, args.database)
    expected = {"releases": 1, "products": 24_458, "names": 74_184, "imported_releases": 1, "product_ids": 24_458, "name_ids": 74_184}
    if any(after_import[key] != value for key, value in expected.items()):
        raise SystemExit(f"Local import count mismatch: {after_import}")
    require_verifier_pass(
        run_psql(args.psql, root, args.host, args.port, args.database, "-t", "-A", "-f", str(post_verifier)),
        "Post-import verifier",
    )

    run_psql(args.psql, root, args.host, args.port, args.database, "-f", str(importer))
    after_replay = catalog_snapshot(args.psql, root, args.host, args.port, args.database)
    if after_replay != after_import:
        raise SystemExit("Idempotent replay changed local catalog state")

    print(json.dumps({
        "status": "PASS",
        "host_guard": args.host,
        "normalization_contract": "PASS",
        "rollback": "PASS",
        "import": "PASS",
        "post_import_verifier": "PASS",
        "idempotent_replay": "PASS",
        "snapshot": after_replay,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
