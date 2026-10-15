"""Append-only sanitized diagnosis archive; no network or database operations."""
import hashlib, json, os, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'endchain_v1'))
from source_scan import check


def disk(path):
    return pathlib.Path('\\\\?\\' + str(path.resolve())) if os.name == 'nt' else path


def archive(run):
    if not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', run):
        raise ValueError('archive_run')
    source = disk(ROOT / 'supabase/.temp' / ('phase6e11-recovery-readonly-' + run))
    target = disk(HERE / 'receipts' / run)
    if target.exists():
        raise ValueError('historical_archive_exists')
    files = {}
    for path in sorted(source.iterdir()):
        if not path.is_file() or not re.fullmatch(r'[a-zA-Z0-9_.-]+\.json', path.name):
            raise ValueError('archive_source_shape')
        raw = path.read_bytes()
        check(path.name, raw)
        json.loads(raw)
        files[path.name] = raw
    result = json.loads(files['result.json'])
    if json.loads(files['preregistration.json'])['run_id'] != run or not result.get('jit_revoked'):
        raise ValueError('archive_binding_or_access_closure')
    target.mkdir(parents=True)
    hashes = {}
    for name, raw in files.items():
        with (target / name).open('xb') as output:
            output.write(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    manifest = dict(run_id=run, status=result['status'], files=hashes,
                    originals_unchanged=True, application_writes=0, auth_writes=0,
                    not_workflow_admission=True, protected_row_fingerprint_performed=False)
    with (target / 'MANIFEST.json').open('xb') as output:
        output.write((json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode())
    return dict(run=run, files=len(files), status=result['status'])


if __name__ == '__main__':
    print(json.dumps(archive(sys.argv[1])))
