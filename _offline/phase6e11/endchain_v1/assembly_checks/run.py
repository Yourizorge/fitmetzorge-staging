"""Portable pure-test entry. No process, socket, SQL or hosted authority."""
import argparse
import ast
import hashlib
import importlib
import importlib.machinery
import importlib.metadata
import importlib.util
import io
import json
import ntpath
import os
from pathlib import Path, PurePosixPath
import re
import sys
import time
import unittest

PREFIX = '_offline/phase6e11/endchain_v1/'
CHECKS = PREFIX + 'assembly_checks/'
SOURCE_ROOT = Path(__file__).resolve().parents[4]
BYTE_PAIRS = CHECKS + 'byte_pairs_20261111.json'
BYTE_PAIRS_SHA = 'ca1684d1139f600c94b871cc2376602738ef103c5ea6f3d35666ea09abd345f2'
ORIGINAL_FIXTURES_SHA = '8dbcf87ac02295d6997af6f2f5854ebf4864e05d708f3b9875dcf9083f8bf6b3'
VARIANT_PATHS = frozenset((
    PREFIX+'case_stack_v1/__init__.py', PREFIX+'case_stack_v1/__main__.py',
    PREFIX+'case_stack_v1/bootstrap.py', PREFIX+'case_stack_v1/ci.py',
    PREFIX+'case_stack_v1/README.txt', PREFIX+'case_stack_v1/test_bootstrap.py',
    PREFIX+'case_stack_v1/test_ci.py',
    'supabase/migrations/20260813_trainer_signup_bootstrap.sql',
    'supabase/migrations/20260818_phase4_nutrition_schema_slice1.sql',
    'supabase/migrations/20260819134024_phase4_nutrition_slice3_atomic_log_item_replacement.sql',
    'supabase/migrations/20260819163738_phase4_nutrition_slice4b_alias_search.sql',
    'supabase/migrations/20260819175756_phase4_nutrition_slice4c_operational_state.sql',
    'supabase/migrations/20260820082018_phase4_nutrition_slice4d_provider_snapshot_logging.sql',
    'supabase/migrations/20260820150513_phase4_nutrition_slice4d_historical_provider_resolver.sql',
    'supabase/migrations/20260822172635_phase4_nutrition_slice4e_ingestion_alias_search.sql',
    'supabase/migrations/20260824113551_phase4_nutrition_slice4f_off_catalog_search.sql',
))
RECOVERY_FRAGMENTS = {
    PREFIX + 'control_recovery.py': (
        '28489db090803bb1df868570c87a9f2a3dbc5c842fbbb81faa5ea837b55520eb',
        (('replace_setup', 'recover'),)),
    PREFIX + 'quota_candidate_v1/runtime_worker_evidence.py': (
        '57c4737921d87abc1bfe9cc62bfc67236359c79e0d66fdd109fae2f422bf6e5d',
        (('WaitEvidence',), ('save',))),
    PREFIX + 'quota_candidate_v1/runtime_recovery.py': (
        '44d315a22a782871f3c1cc4a825537814b80f266f1bfb114ccb0b14234d189a9',
        (('finish',),)),
}
DENIED_EVENTS = {'subprocess.Popen', 'os.system', 'os.spawn', 'os.posix_spawn',
                 'os.fork', 'os.exec', 'socket.connect', 'socket.connect_ex',
                 'socket.bind', 'socket.getaddrinfo', 'socket.gethostbyname',
                 'socket.gethostbyaddr'}


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_json_key')
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique)


def windows_extended(path):
    """Convert an absolute drive/UNC path, never a device or relative path."""
    text = str(path).replace('/', '\\')
    require(not text.startswith('\\\\.\\'), 'source_device_path')
    if text.startswith('\\\\?\\'):
        text = ('\\\\' + text[8:]) if text.startswith('\\\\?\\UNC\\') else text[4:]
    drive, tail = ntpath.splitdrive(text)
    require(drive and tail.startswith('\\') and
            (re.fullmatch('[a-zA-Z]:', drive) or drive.startswith('\\\\')),
            'source_absolute_path')
    normalized = ntpath.normpath(text)
    return '\\\\?\\UNC\\' + normalized[2:] if normalized.startswith('\\\\') else '\\\\?\\' + normalized


def io_path(path):
    path = Path(path)
    return Path(windows_extended(os.path.abspath(path))) if os.name == 'nt' else path


def read(root, name):
    require(type(name) is str and name and '\\' not in name and ':' not in name,
            'source_path')
    rel = PurePosixPath(name)
    require(not rel.is_absolute() and '..' not in rel.parts and rel.as_posix() == name,
            'source_path')
    root = io_path(root).resolve(strict=True)
    path = root / name
    require(all(not p.is_symlink() and not (hasattr(p, 'is_junction') and p.is_junction())
                for p in (path, *path.parents) if p != root and p.is_relative_to(root)),
            'source_link')
    require(path.resolve(strict=True).is_relative_to(root), 'source_escape')
    raw = path.read_bytes()
    require(len(raw) <= 8_000_000, 'source_size')
    return raw


def checked_digest(value):
    return type(value) is str and re.fullmatch('[a-f0-9]{64}', value)


def approved_byte_pairs(root):
    raw = read(root, BYTE_PAIRS)
    require(sha(raw) == BYTE_PAIRS_SHA, 'byte_pairs_pin')
    value = decode(raw)
    require(type(value) is dict and set(value) == {'source_head', 'kind', 'pairs'}
            and value['source_head'] == '320ef27c08781330289b93118cd313f2bc1fbb47'
            and value['kind'] == 'independently_verified_git_lf_and_preserved_worktree_crlf'
            and type(value['pairs']) is list and len(value['pairs']) == 16, 'byte_pairs_shape')
    result = {}
    for row in value['pairs']:
        require(type(row) is dict and set(row) == {'path', 'git_blob', 'canonical_lf_sha256', 'variants'}
                and row['path'] in VARIANT_PATHS and row['path'] not in result
                and type(row['git_blob']) is str and re.fullmatch('[a-f0-9]{40}', row['git_blob']),
                'byte_pairs_shape')
        result[row['path']] = {k: v for k, v in row.items() if k != 'git_blob'}
    require(set(result) == VARIANT_PATHS, 'byte_pairs_paths')
    return result


def verify_record(raw, row, pairs):
    require(type(row) is dict and type(row.get('path')) is str, 'manifest_row')
    if set(row) == {'path', 'sha256', 'bytes'}:
        require(type(row['bytes']) is int and 0 <= row['bytes'] <= 8_000_000
                and checked_digest(row['sha256']), 'manifest_row')
        require(sha(raw) == row['sha256'] and len(raw) == row['bytes'], 'source_hash:' + row['path'])
    else:
        require(set(row) == {'path', 'canonical_lf_sha256', 'variants'}
                and row['path'] in VARIANT_PATHS and checked_digest(row['canonical_lf_sha256'])
                and type(row['variants']) is list and len(row['variants']) == 2, 'variant_record')
        for variant, encoding in zip(row['variants'], ('lf', 'crlf')):
            require(type(variant) is dict and set(variant) == {'encoding', 'sha256', 'bytes'}
                    and variant['encoding'] == encoding and checked_digest(variant['sha256'])
                    and type(variant['bytes']) is int and 0 <= variant['bytes'] <= 8_000_000,
                    'variant_record')
        require(row == pairs.get(row['path']), 'variant_not_independently_pinned')
        require(any(sha(raw) == v['sha256'] and len(raw) == v['bytes'] for v in row['variants']),
                'variant_raw_bytes:' + row['path'])
        canonical = raw.replace(b'\r\n', b'\n')
        require(b'\r' not in canonical and sha(canonical) == row['canonical_lf_sha256'],
                'variant_canonical')
    return sha(raw)


def verify_manifest(root, name, expected):
    require(type(expected) is str and re.fullmatch('[a-f0-9]{64}', expected), 'manifest_pin')
    raw = read(root, name)
    require(sha(raw) == expected, 'manifest_hash')
    value = decode(raw)
    require(type(value) is dict and value.get('format') in
            ('portable-assembly-source-v1', 'portable-assembly-source-v2'), 'manifest_format')
    v2 = value['format'].endswith('-v2')
    required = {'format', 'files'} | ({'fixtures', 'byte_pairs_sha256'} if v2 else set())
    optional = {'excluded_self_and_digest', 'historical_authority', 'full_selection_tests', 'READY'}
    require(required <= set(value) <= required | optional, 'manifest_shape')
    for flag in ('historical_authority', 'READY'):
        require(flag not in value or value[flag] is False, 'manifest_authority')
    require('full_selection_tests' not in value or type(value['full_selection_tests']) is int
            and value['full_selection_tests'] == 452, 'manifest_selection')
    if 'excluded_self_and_digest' in value:
        excluded = value['excluded_self_and_digest']
        require(type(excluded) is list and len(excluded) == 2 and excluded[0] == name
                and all(type(p) is str and p.startswith(CHECKS) for p in excluded), 'manifest_excluded')
    pairs = approved_byte_pairs(root) if v2 else {}
    if v2:
        require(value['byte_pairs_sha256'] == BYTE_PAIRS_SHA and type(value['fixtures']) is str
                and value['fixtures'].startswith(CHECKS) and value['fixtures'].endswith('.json')
                and value['fixtures'] != name, 'manifest_v2_binding')
    rows = value.get('files')
    require(type(rows) is list and 0 < len(rows) <= 4096, 'manifest_files')
    sources, folded, variants = {}, set(), set()
    for row in rows:
        require(type(row) is dict and type(row.get('path')) is str
                and (v2 or set(row) == {'path', 'sha256', 'bytes'}),
                'manifest_row')
        path = row['path']
        require(path.casefold() not in folded and path != name, 'manifest_duplicate_or_self')
        folded.add(path.casefold())
        data = read(root, path)
        sources[path] = verify_record(data, row, pairs)
        if 'variants' in row:
            variants.add(path)
    if v2:
        require(variants == VARIANT_PATHS and sources.get(BYTE_PAIRS) == BYTE_PAIRS_SHA
                and value['fixtures'] in sources, 'manifest_v2_inventory')
    return value, sources


def verify_fixtures(root, pins, manifest=None):
    if type(manifest) is dict and manifest.get('format') == 'portable-assembly-source-v2':
        require(type(pins) is dict and set(pins) == {'format', 'historical', 'policy'}
                and pins['format'] == 'portable-assembly-fixtures-v2', 'fixture_v2_shape')
        original_raw = read(root, CHECKS+'fixture_pins.json')
        require(sha(original_raw) == ORIGINAL_FIXTURES_SHA, 'original_fixture_pins_changed')
        original = decode(original_raw)
        require(pins['historical'] == original['historical'] and type(pins['policy']) is dict
                and set(pins['policy']) == set(original['policy']), 'fixture_v2_inventory')
        rows = {row['path']: row for row in manifest['files']}
        pairs = approved_byte_pairs(root)
        for path, expected in pins['historical'].items():
            name = CHECKS+'historical/'+path
            row = rows.get(name)
            require(type(row) is dict and set(row) == {'path', 'sha256', 'bytes'}
                    and row['sha256'] == expected, 'historical_fixture_exact')
            verify_record(read(root, name), row, {})
        for path, record in pins['policy'].items():
            require(type(record) is dict and record.get('path') == path, 'policy_record')
            verify_record(read(root, path), record, pairs)
            require(record == rows.get(path), 'policy_source_mismatch')
            if path not in pairs:
                require(record.get('sha256') == original['policy'][path], 'policy_original_pin')
        return
    require(set(pins) == {'historical', 'policy'} and len(pins['historical']) == 4
            and len(pins['policy']) == 48, 'fixture_inventory')
    for group, paths in pins.items():
        for path, expected in paths.items():
            name = CHECKS + 'historical/' + path if group == 'historical' else path
            require(sha(read(root, name)) == expected, 'fixture_hash:' + path)


def configure_environment(root):
    root = Path(root).resolve(strict=True)
    expected = {
        'A_RECOVERY_SOURCE_ROOT': root,
        'A_RECOVERY_RUNTIME_DIR': root / PREFIX / 'quota_candidate_v1',
        'A_BOOTSTRAP_HISTORICAL_ROOT': root / CHECKS / 'historical',
        'A_BOOTSTRAP_POLICY_ROOT': root,
        'AUTH_CONTEXT_SOURCE_ROOT': root,
    }
    for name, path in expected.items():
        supplied = os.environ.get(name)
        require(supplied is None or Path(supplied).resolve(strict=True) == path.resolve(strict=True),
                'test_environment_root:' + name)
    for name, path in expected.items():
        os.environ[name] = str(path)
    return {name: path.relative_to(root).as_posix() for name, path in expected.items()}


def check_origin(module, root, sources):
    path = Path(module.__file__).resolve(strict=True)
    require(path.is_relative_to(root), 'module_origin:' + module.__name__)
    name = path.relative_to(root).as_posix()
    require(not name.startswith(CHECKS + 'historical/'), 'historical_execution_forbidden')
    require(sources.get(name) == sha(path.read_bytes()), 'module_hash:' + module.__name__)
    return name


def pure_guard(event, values):
    if event in DENIED_EVENTS:
        raise RuntimeError('pure_tests_forbidden:' + event)
    if event == 'exec' and values:
        filename = getattr(values[0], 'co_filename', '').replace('\\', '/')
        require('/assembly_checks/historical/' not in filename, 'historical_execution_forbidden')


class ExactSourceImports:
    """One-shot CLI import policy, not a sandbox for hostile Python code."""

    def __init__(self, root, sources, search_roots, dependency_roots=()):
        self.root = Path(root).resolve(strict=True)
        self.sources = dict(sources)
        self.search_roots = tuple(Path(p).resolve(strict=True) for p in search_roots)
        self.dependency_roots = tuple(Path(p).resolve(strict=True) for p in dependency_roots)
        self.allowed_external = (*self.dependency_roots, Path(sys.base_prefix).resolve())
        self.names = set()
        self.executed = set()
        self.loaded = {}
        self.active = False
        self.failed = False
        for name in sources:
            if not name.endswith('.py') or name.startswith(CHECKS + 'historical/'):
                continue
            path = self.root / name
            for base in self.search_roots:
                if path.is_relative_to(base):
                    parts = list(path.relative_to(base).with_suffix('').parts)
                    if parts[-1] == '__init__':
                        parts.pop()
                    self.names.update('.'.join(parts[:i]) for i in range(1, len(parts) + 1))

    def project(self, path):
        path = Path(path).resolve()
        return path.is_relative_to(self.root) and not any(
            path.is_relative_to(dep) for dep in self.dependency_roots)

    def code(self, path):
        path = Path(path)
        require(self.project(path), 'import_source_outside')
        name = path.relative_to(self.root).as_posix()
        require(not name.startswith(CHECKS + 'historical/'), 'historical_execution_forbidden')
        require(name.endswith('.py') and name in self.sources, 'import_source_unlisted:' + name)
        raw = read(self.root, name)
        require(sha(raw) == self.sources[name], 'import_source_hash:' + name)
        return compile(raw, str(path), 'exec', dont_inherit=True, optimize=sys.flags.optimize)

    def reject_cached(self):
        for name, module in tuple(sys.modules.items()):
            # The launched runner is part of the caller's trusted bootstrap.
            if module is sys.modules.get(__name__):
                continue
            filename = getattr(module, '__file__', None)
            paths = tuple(getattr(module, '__path__', ()) or ())
            dependency_name = name.split('.')[0] in ('psycopg', 'psycopg_binary', 'pglast')
            owned = name in self.names or dependency_name or any(
                self.project(p) or any(Path(p).resolve().is_relative_to(d)
                                       for d in self.dependency_roots)
                for p in ((filename,) if filename else ()) + paths)
            require(not owned, 'import_preloaded:' + name)

    def recovery_fragment(self, path, code):
        name = Path(path).relative_to(self.root).as_posix()
        entry = RECOVERY_FRAGMENTS.get(name)
        if entry is None:
            return False
        original_pin, selections = entry
        raw = read(self.root, name)
        require(self.sources.get(name) == original_pin and sha(raw) == original_pin,
                'import_fragment_source_binding')
        tree = ast.parse(raw)
        for names in selections:
            found = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                     and node.name in names]
            require(len(found) == len(names) and {node.name for node in found} == set(names),
                    'import_fragment_definition')
            expected = compile(ast.Module(body=found, type_ignores=[]), str(path), 'exec',
                               dont_inherit=True, optimize=sys.flags.optimize)
            if code == expected:
                return True
        return False

    def find_spec(self, fullname, path=None, target=None):
        try:
            require(not self.failed, 'import_previous_failure')
            return self._find_spec(fullname, path, target)
        except BaseException:
            self.failed = True
            raise

    def find_distributions(self, context=None):
        # Metadata lookup is separate from loading Python code. Preserve it only
        # for the explicitly trusted dependency/interpreter roots.
        context = context or importlib.metadata.DistributionFinder.Context()
        paths = [p for p in context.path if any(
            Path(p).resolve().is_relative_to(base) for base in self.allowed_external)]
        bound = importlib.metadata.DistributionFinder.Context(name=context.name, path=paths)
        return importlib.machinery.PathFinder.find_distributions(context=bound)

    def _find_spec(self, fullname, path=None, target=None):
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        if spec is None:
            require(fullname not in self.names, 'import_expected_missing:' + fullname)
            return None
        if spec.origin is None:
            locations = tuple(spec.submodule_search_locations or ())
            require(locations and all(self.project(p) for p in locations)
                    and fullname in self.names, 'import_namespace_unbound:' + fullname)
            return spec
        origin = Path(spec.origin)
        if self.project(origin):
            self.code(origin)  # Validate before importlib creates the module.
            spec.loader = ExactSourceLoader(self, origin)
            spec.cached = None
        else:
            require(fullname not in self.names, 'import_shadow:' + fullname)
            require(any(origin.resolve().is_relative_to(p) for p in self.allowed_external),
                    'import_external_unbound:' + fullname)
        return spec

    def audit(self, event, values):
        if not self.active or event != 'exec' or not values:
            return
        try:
            require(not self.failed, 'import_previous_failure')
            self._audit_execution(values[0])
        except BaseException:
            self.failed = True
            raise

    def _audit_execution(self, code):
        filename = getattr(code, 'co_filename', '')
        if filename and not filename.startswith('<') and self.project(filename):
            # Also covers explicit spec_from_file_location and custom loaders.
            # Compare actual code before execution, not just its claimed filename.
            expected = self.code(Path(filename))
            require(code == expected or self.recovery_fragment(Path(filename), code),
                    'import_execution_not_exact_source')
            self.executed.add(str(Path(filename).resolve()))
        elif filename and not filename.startswith('<'):
            require(any(Path(filename).resolve().is_relative_to(p) for p in self.allowed_external),
                    'import_execution_external_unbound')

    def install(self):
        self.reject_cached()
        self.active = True
        sys.addaudithook(self.audit)
        # Do not permit an earlier custom finder to bypass this policy.
        sys.meta_path[:] = [self, importlib.machinery.BuiltinImporter,
                           importlib.machinery.FrozenImporter]

    def verify_loaded(self):
        require(not self.failed, 'import_previous_failure')
        for name, module in tuple(sys.modules.items()):
            if module is sys.modules.get(__name__):
                continue
            filename = getattr(module, '__file__', None)
            if filename and self.project(filename):
                require(str(Path(filename).resolve()) in self.executed,
                        'import_cache_without_execution:' + name)
                require(self.loaded.get(name) is module, 'import_cache_replaced:' + name)
                check_origin(module, self.root, self.sources)
            elif name in self.names:
                locations = tuple(getattr(module, '__path__', ()) or ())
                require(filename is None and locations and all(self.project(p) for p in locations),
                        'import_cache_shadow:' + name)


class ExactSourceLoader:
    def __init__(self, policy, path):
        self.policy, self.path = policy, path

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        # Never read or write pyc. Hash and compile the same raw bytes.
        try:
            require(not self.policy.failed, 'import_previous_failure')
            exec(self.policy.code(self.path), module.__dict__)
            self.policy.loaded[module.__name__] = module
        except BaseException:
            self.policy.failed = True
            raise


def complete_result(result, count):
    return (result.wasSuccessful() and result.testsRun == count
            and not result.skipped)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=SOURCE_ROOT)
    parser.add_argument('--manifest', default=CHECKS + 'sources.json')
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--scope', choices=('portable', 'full'), default='portable')
    parser.add_argument('--list-only', action='store_true')
    parser.add_argument('--deps', type=Path)
    parser.add_argument('--parser-deps', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    root = args.source_root.resolve(strict=True)
    require(root == SOURCE_ROOT, 'runner_source_root_mismatch')
    if args.report:
        require(not args.report.exists(), 'report_already_exists')
    sys.addaudithook(pure_guard)
    manifest, sources = verify_manifest(root, args.manifest, args.manifest_sha256)
    require(sources.get(CHECKS + 'run.py') == sha(Path(__file__).read_bytes()), 'runner_source_pin')
    fixture_path = manifest.get('fixtures', CHECKS + 'fixture_pins.json')
    pins = decode(read(root, fixture_path))
    verify_fixtures(root, pins, manifest)
    environment = configure_environment(root)
    selection = decode(read(root, CHECKS + 'selection.json'))
    require(selection['full_expected_tests'] == 452, 'full_selection_count_contract')
    dependency_rows = decode(read(root, CHECKS + 'dependency_needed.json'))['files']
    require(len(dependency_rows) == 19 and all(sources.get(r['path']) == r['sha256']
                                             for r in dependency_rows), 'dependency_inventory')
    deps = (args.deps or root / 'supabase/.temp/phase6e-server-deps').resolve(strict=True)
    pg = (args.parser_deps or root / 'supabase/.temp/phase6e11-pg17-parser').resolve(strict=True)
    imports = ExactSourceImports(root, sources,
        (root / PREFIX, root / '_offline/phase6e_server_v1', root), (deps, pg))
    imports.install()
    sys.path[:0] = [str(root / PREFIX), str(root / '_offline/phase6e_server_v1'), str(deps), str(pg)]
    import psycopg
    import psycopg.pq
    import pglast
    require(Path(psycopg.__file__).resolve().is_relative_to(deps)
            and Path(pglast.__file__).resolve().is_relative_to(pg), 'dependency_origin')
    require(psycopg.__version__ == '3.2.10' and psycopg.pq.__impl__ == 'binary'
            and psycopg.pq.version() in (160009, 170006) and pglast.__version__ == 'v7.20',
            'dependency_versions')
    import source_scan
    check_origin(source_scan, root, sources)
    for name in sources:
        source_scan.check(name, read(root, name))
    from quota_candidate_v1 import runtime_registered_costs
    check_origin(runtime_registered_costs, root, sources)
    driver = runtime_registered_costs.native_proof({'host':'127.0.0.1','hostaddr':'127.0.0.1'})
    require(driver['server_connection_executed'] is False, 'unexpected_driver_connection')
    names = selection[args.scope]
    origins = []
    for name in names:
        parts = name.split('.')
        module_name = '.'.join(parts[:next((i for i,p in enumerate(parts) if p[0].isupper()),len(parts))])
        module = importlib.import_module(module_name)
        origins.append(check_origin(module, root, sources))
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    imports.verify_loaded()
    count = suite.countTestCases()
    if args.scope == 'full':
        require(count == selection['full_expected_tests'], 'full_selection_count')
    output = io.StringIO()
    started = time.monotonic()
    result = None if args.list_only else unittest.TextTestRunner(stream=output,verbosity=1).run(suite)
    verify_manifest(root, args.manifest, args.manifest_sha256)
    verify_fixtures(root, pins, manifest)
    imports.verify_loaded()
    expected_modules = {name[len(PREFIX):-3].replace('/','.') for name in sources
                        if name.startswith(PREFIX) and name.endswith('.py')
                        and not name.startswith(CHECKS + 'historical/')}
    for name,module in tuple(sys.modules.items()):
        if name in expected_modules and getattr(module,'__file__',None):
            origins.append(check_origin(module,root,sources))
    report = dict(format='portable-pure-tests-v1',scope=args.scope,
        status='SELECTION_CHECKED_NOT_RUN' if result is None else ('PASS' if complete_result(result, count) else 'FAIL'),
        manifest_sha256=args.manifest_sha256,selected_tests=count,
        tests_run=0 if result is None else result.testsRun,
        failures=0 if result is None else len(result.failures),errors=0 if result is None else len(result.errors),
        skips=0 if result is None else len(result.skipped),seconds=round(time.monotonic()-started,3),
        source_scan_files=len(sources),dependency_needed=dependency_rows,environment=environment,
        checked_module_origins=sorted(set(origins)),log=output.getvalue(),
        historical_fixture_files=4,policy_files_in_source_root=48,
        publication_proven=False,real_execution_evidence=False,READY=False,hosted_admitted=False)
    if args.report:
        with args.report.open('x',encoding='utf-8') as stream:
            json.dump(report,stream,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k in ('status','scope','selected_tests','tests_run',
        'failures','errors','skips','seconds','source_scan_files','READY')}))
    if result is not None and not complete_result(result, count):
        print(output.getvalue(),file=sys.stderr)
    return 0 if result is None or complete_result(result, count) else 1


if __name__ == '__main__':
    raise SystemExit(main())
