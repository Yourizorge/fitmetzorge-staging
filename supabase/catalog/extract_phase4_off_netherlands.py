"""Extract the locked Netherlands OFF rows after verifying the full source file.

This helper is local-only. It never performs a network request or connects to
Supabase. DuckDB 1.4.1 is pinned because the compact Parquet bytes are part of
the reviewed artifact chain.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import duckdb


SOURCE_REVISION = "e544a38353692b2df59df78f47393990a578eb8e"
SOURCE_FILE_SIZE = 7_797_955_269
SOURCE_FILE_SHA256 = "38D7A48D32F574812490024AA77FB064E84B041CB2687E46DF87AFCE441100C2"
NETHERLANDS_SOURCE_COUNT = 106_650
EXPECTED_EXTRACT_SIZE = 6_709_044
EXPECTED_EXTRACT_SHA256 = "FF6ED35C50B134E6EAEF0A23E62EC2DC6CBF981DB55D0F33E0BBF125BABEF27C"
DUCKDB_VERSION = "1.4.1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sql_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if duckdb.__version__ != DUCKDB_VERSION:
        raise SystemExit(f"DuckDB version mismatch: {duckdb.__version__} != {DUCKDB_VERSION}")
    if not args.source.is_file() or args.source.stat().st_size != SOURCE_FILE_SIZE:
        raise SystemExit("Pinned OFF source size mismatch")
    if sha256_file(args.source) != SOURCE_FILE_SHA256:
        raise SystemExit("Pinned OFF source SHA-256 mismatch")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    connection.execute("set threads = 4")
    try:
        connection.execute(
            f"""
            copy (
              select
                code,
                product_name,
                generic_name,
                lang,
                brands,
                categories_tags,
                countries_tags,
                product_quantity_unit,
                product_quantity,
                quantity,
                serving_size,
                nutrition_data_per,
                list_filter(
                  nutriments,
                  nutrient -> list_contains(
                    ['energy-kcal', 'energy', 'proteins', 'carbohydrates', 'fat', 'fiber'],
                    nutrient.name
                  )
                ) as nutriments,
                data_quality_errors_tags,
                obsolete,
                rev,
                last_modified_t,
                last_updated_t,
                complete,
                completeness
              from read_parquet('{sql_path(args.source)}')
              where list_contains(countries_tags, 'en:netherlands')
            ) to '{sql_path(args.output)}' (
              format parquet,
              compression zstd,
              row_group_size 10000
            )
            """
        )
        row_count = connection.execute(
            "select count(*) from read_parquet(?)", [str(args.output)]
        ).fetchone()[0]
    finally:
        connection.close()

    if row_count != NETHERLANDS_SOURCE_COUNT:
        raise SystemExit(f"Netherlands extract count mismatch: {row_count} != {NETHERLANDS_SOURCE_COUNT}")
    if args.output.stat().st_size != EXPECTED_EXTRACT_SIZE:
        raise SystemExit("Netherlands extract size mismatch")
    if sha256_file(args.output) != EXPECTED_EXTRACT_SHA256:
        raise SystemExit("Netherlands extract SHA-256 mismatch")
    print(f"PASS: revision={SOURCE_REVISION} rows={row_count}")


if __name__ == "__main__":
    main()
