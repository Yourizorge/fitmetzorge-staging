"""Local source-only candidate preparation. No upload/dispatch/network mode."""
import argparse
import base64
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pg_auth_component import inventory


def source_path(checkout, overlay, name):
    root = overlay if name in set(inventory.OWN) | {inventory.WORKFLOW} else checkout
    path = root/name
    if pathlib.PurePosixPath(name).is_absolute() or '..' in pathlib.PurePosixPath(name).parts:
        raise ValueError('component_source_path')
    current = root
    for part in pathlib.PurePosixPath(name).parts:
        current = current/part
        if current.is_symlink(): raise ValueError('component_source_link')
    if not path.resolve(strict=True).is_relative_to(root): raise ValueError('component_source_path')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--checkout-root', type=pathlib.Path,
        help='Explicit read-only complete checkout; only this component is overlaid from the script root.')
    args = parser.parse_args()
    overlay = pathlib.Path(__file__).resolve().parents[4]
    root = (args.checkout_root or overlay).resolve(strict=True)
    sys.path.insert(0, str(root/'_offline/phase6e11/endchain_v1'))
    import admission_ci
    import source_scan
    files = {}; sources = {}
    for name in inventory.paths(admission_ci, root):
        path = source_path(root, overlay, name)
        raw = path.read_bytes(); source_scan.check(name, raw)
        files[name] = base64.b64encode(raw).decode('ascii')
        sources[name] = hashlib.sha256(raw).hexdigest()
    raw = (json.dumps({'format':1,'files':files},sort_keys=True,separators=(',',':'))+'\n').encode()
    if len(raw) > 12*1024*1024: raise ValueError('candidate_payload_limit')
    args.output.mkdir(exist_ok=False)
    (args.output/'candidate.json').write_bytes(raw)
    (args.output/'source-inventory.json').write_text(json.dumps(sources,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'candidate_sha256':hashlib.sha256(raw).hexdigest(),
        'files':len(files),'bytes':len(raw),'workflow':inventory.WORKFLOW,
        'upload_or_dispatch_performed':False,'full_chain_admission':False}))


if __name__ == '__main__': main()
