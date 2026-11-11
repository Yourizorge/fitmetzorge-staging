"""Exact-source Linux import checks, not database or endchain admission."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import socket
import sys
import time
import types
import unittest

PREFIX = '_offline/phase6e11/endchain_v1/'
HERE = PREFIX + 'linux_import_component/'
MANIFEST = HERE + 'sources-r2.json'
WORKFLOW = '.github/workflows/phase6e-linux-import-component.yml'
PATHS = (HERE + 'check.py', HERE + 'test_check.py', WORKFLOW,
         PREFIX + 'admission_trusted_loader.py',
         PREFIX + 'test_admission_trusted_loader.py',
         PREFIX + 'quota_candidate_v1/runtime_exported_terminal.py')


def need(value, reason):
    if not value:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(root, name):
    path = root / name
    need(all(not p.is_symlink() for p in (path, *path.parents)), 'source_symlink')
    need(path.resolve(strict=True).is_relative_to(root), 'source_escape')
    raw = path.read_bytes()
    need(len(raw) <= 2_000_000, 'source_size')
    return raw


def verify(root, expected):
    need(re.fullmatch('[a-f0-9]{64}', expected), 'manifest_pin')
    raw = read(root, MANIFEST)
    need(digest(raw) == expected, 'manifest_hash')
    manifest = json.loads(raw)
    need(manifest.get('format') == 1 and set(manifest['files']) == set(PATHS), 'source_set')
    buffers = {name: read(root, name) for name in PATHS}
    need(all(digest(raw) == manifest['files'][name] for name, raw in buffers.items()), 'source_hash')
    return manifest, buffers


def complete(result, selected):
    return (result.wasSuccessful() and result.testsRun == selected
            and not result.skipped and not result.expectedFailures)


def interfaces():
    names = [name for _, name in socket.if_nameindex()]
    need(names == ['lo'], 'external_interface')
    return names


def install(name, path, raw):
    need(name not in sys.modules, 'preloaded_module')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ''
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--expected', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--run', required=True)
    parser.add_argument('--host-network', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    need(sys.platform == 'linux' and sys.flags.isolated and sys.flags.no_site, 'isolated_linux_required')
    need(sys.version_info[:2] == (3, 12), 'python_version')
    need(re.fullmatch('[a-f0-9]{40}', args.commit) and re.fullmatch('[1-9][0-9]*', args.run), 'ci_binding')
    need(os.geteuid() != 0, 'unprivileged_required')
    need(os.readlink('/proc/self/ns/net') != args.host_network, 'network_namespace_required')
    interface_names = interfaces()
    need(not args.report.exists(), 'report_exists')
    manifest, buffers = verify(root, args.expected)
    started = time.monotonic()
    for name in ('admission_trusted_loader', 'test_admission_trusted_loader'):
        relative = PREFIX + name + '.py'
        install(name, root / relative, buffers[relative])
    suite = unittest.defaultTestLoader.loadTestsFromName('test_admission_trusted_loader')
    selected = suite.countTestCases()
    need(selected == 29, 'selection_count')
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    verify(root, args.expected)
    receipt = dict(format='linux-import-component-v1', status='PASS' if complete(result, selected) else 'FAIL',
        commit=args.commit, ci_run=args.run, manifest_sha256=args.expected, sources=manifest['files'],
        python=sys.version, selected=selected, executed=result.testsRun, failures=len(result.failures),
        errors=len(result.errors), skips=len(result.skipped), seconds=round(time.monotonic()-started, 3),
        network_isolated=True, interface_names=interface_names, log=log.getvalue(), hosted_calls=0, database_calls=0,
        full_chain_admission=False, READY=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({key:receipt[key] for key in ('status','executed','failures','errors','skips','READY')}))
    return 0 if complete(result, selected) else 1


if __name__ == '__main__':
    raise SystemExit(main())
