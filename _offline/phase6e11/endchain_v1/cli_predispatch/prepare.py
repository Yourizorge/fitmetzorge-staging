"""Apply one checked entry patch to a dedicated, clean upstream CLI checkout.

No download, database connection, hosted endpoint, or dependency installation.
Use a new disposable checkout, never the application repository.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess

UPSTREAM = '21db855916f2c2b12f61cde923a27094b8528b23'
TAG_OBJECT = 'cdcb8e4a8bc8d10658f194186d39739f43c04d1b'
HERE = pathlib.Path(__file__).resolve().parent
PINS = {
    'apps/cli/src/main.ts': '4f153f20dc1930c712b367d5510916b4e12daed3d5ce96dfc1321ea3215d67af',
    'apps/cli/src/command-internal/legacy-db-connection.sql-pg.layer.ts': '90d2032c3c73849e9baf24a63dc9668d358e879b77209124ab8179a41e9f843c',
    'apps/cli/src/command-internal/legacy-migration-apply.ts': '38be04d04510a443bbe9f2b039645e4ec79c711b03843774d32c1b8558d9a5d6',
    'apps/cli/src/command-internal/legacy-migration-history.ts': 'f2a155ab35943b117c3821b1a540131899706523390a9da9c051cebf4b880fff',
    'pnpm-lock.yaml': '39d38c82a0afc71d6970d2e436cd13c59bdaa52754a5c2487cb8327480d1c827',
}
PATCHED_ENTRY = '''#!/usr/bin/env bun
import * as Pg from "pg";
import { start } from "../cli_predispatch/entry.mjs";
await start(Pg.Client);
await import("./cli/main.ts");
'''
COPY = ('hook.cjs', 'entry.mjs', 'package.json', 'pnpm-lock.yaml', 'pnpm-workspace.yaml')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_sources(root):
    hashes = {}
    for name, expected in PINS.items():
        raw = (root / name).read_bytes()
        if digest(raw.replace(b'\r\n', b'\n')) != expected:
            raise ValueError('cli_predispatch_upstream_source_changed')
        hashes[name] = digest(raw)
    return hashes


def prepare(upstream):
    root = pathlib.Path(upstream).resolve()
    def git(*args):
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, timeout=15, check=True)
        return result.stdout.decode().strip()
    if git('rev-parse', 'HEAD') != UPSTREAM or git('status', '--porcelain', '--untracked-files=no'):
        raise ValueError('cli_predispatch_clean_upstream_required')
    before = checked_sources(root)
    target = root / 'apps/cli/cli_predispatch'
    target.mkdir(exist_ok=False)
    for name in COPY:
        (target / name).write_bytes((HERE / name).read_bytes())
    (root / 'apps/cli/src/main.ts').write_bytes(PATCHED_ENTRY.encode())
    result = {'upstream_commit': UPSTREAM, 'tag_object': TAG_OBJECT, 'release': '2.117.0',
        'source_patch': 'main.ts: install bounded pg hook before dynamic CLI import',
        'source_before_raw': before, 'source_before_lf': PINS,
        'entry_sha256': digest(PATCHED_ENTRY.encode()),
        'hook_sources': {name: digest((target / name).read_bytes()) for name in COPY},
        'driver': 'pg 8.23.0 / pg-protocol 1.16.0 (not pgx)',
        'bun': '1.4.1', 'pnpm': '12.3.0', 'build_mode': 'instrumented upstream source entry',
        'hosted_admission': False, 'real_cli_execution': False}
    (target / 'build.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--upstream', required=True)
    print(json.dumps(prepare(parser.parse_args().upstream), sort_keys=True))
