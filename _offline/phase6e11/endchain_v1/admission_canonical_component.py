"""Separate offline canonical-original component. Never case/root admission.

The caller authenticates the artifact and external source map. Only installed,
hash-checked code runs; original bytes are data, including in the fresh child.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

PREFIX = '_offline/phase6e11/endchain_v1/'
SELF = PREFIX + 'admission_canonical_component.py'
SUPPORT = PREFIX + 'admission_terminal_process.py'
LOADER = PREFIX + 'admission_trusted_loader.py'
REPLAY = PREFIX + 'admission_canonical_replay.py'
READER = PREFIX + 'quota_candidate_v1/runtime_exported_terminal.py'
SUMMARY = 'case-stack-canonical-prefix.json'
PINS = {
    SUPPORT: '959149a64c35c4c28c551ab2638157c6bab59e334e426877bdc186ca2c11aeec',
    LOADER: '044aee41ad8bbc7b21f30427ce66eb13205001066b36b2d39478409b59e989c5',
    REPLAY: 'fa8ec7b385295b883719209a195e41fee87b777c6f1bb68fefd43cf4ebe98ace',
    READER: 'cbf01a6183941d6fa2a76621ad1c94503c5676bd37039629b141b6578866b24b',
}
MAX_REQUEST = 64 * 1024 * 1024
MAX_RESPONSE = 2_000_000
MAX_ORIGINALS = 16_000_000
BOOTSTRAP = r'''
import hashlib,pathlib,sys
root=pathlib.Path(sys.argv[1]).resolve(strict=True)
path=root/'_offline/phase6e11/endchain_v1/admission_canonical_component.py'
assert all(not p.is_symlink() and not getattr(p,'is_junction',lambda:False)() for p in (path,*path.parents))
assert path.resolve(strict=True).is_relative_to(root) and path.stat().st_size<=2000000
raw=path.read_bytes()
assert len(raw)<=2000000 and hashlib.sha256(raw).hexdigest()==sys.argv[2]
ns={'__name__':'_installed_canonical_component','__file__':str(path)}
exec(compile(raw,str(path),'exec',dont_inherit=True),ns)
raise SystemExit(ns['child'](root,sys.argv[2],pathlib.Path(sys.argv[3]),sys.argv[4],pathlib.Path(sys.argv[5])))
'''


def need(value):
    if not value:
        raise ValueError('canonical_component_contract')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value)
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: need(False))


def raw_source(root, name, sources):
    path = root / name
    need(name in sources and type(sources[name]) is str and re.fullmatch('[a-f0-9]{64}', sources[name]))
    need(path.resolve(strict=True).is_relative_to(root) and path.is_file()
         and all(not p.is_symlink() and not getattr(p, 'is_junction', lambda: False)()
                 for p in (path, *path.parents)) and path.stat().st_size <= 2_000_000)
    raw = path.read_bytes()
    need(len(raw) <= 2_000_000 and sha(raw) == sources[name])
    return raw


def support(root, sources):
    need(all(sources.get(name) == digest for name, digest in PINS.items()))
    for name in PINS:
        raw_source(root, name, sources)
    raw = raw_source(root, SUPPORT, sources)
    namespace = {'__name__': '_installed_canonical_support', '__file__': str(root / SUPPORT)}
    exec(compile(raw, str(root / SUPPORT), 'exec', dont_inherit=True), namespace)
    from types import SimpleNamespace
    return SimpleNamespace(**namespace)


def identity(source_commit, candidate_sha256, ci_run, run_id):
    need(type(source_commit) is str and re.fullmatch('[a-f0-9]{40}', source_commit))
    need(type(candidate_sha256) is str and re.fullmatch('[a-f0-9]{64}', candidate_sha256))
    need(type(ci_run) is str and re.fullmatch('[1-9][0-9]{0,18}', ci_run))
    # Do not import uuid before the existing fresh-child stdlib bootstrap.
    need(type(run_id) is str and re.fullmatch('[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}', run_id))
    need(run_id not in ('6f8c8909-9b79-4011-a9d1-db5e23c6b6c1', '11a909f4-7113-424a-aa4b-ce9964720a3e'))
    return dict(source_commit=source_commit, candidate_sha256=candidate_sha256, ci_run=ci_run, run_id=run_id)


def required_names(summary):
    """Select only original refs, not executable sources or a fabricated case."""
    need(type(summary) is dict and summary.get('format') == 'case-stack-canonical-prefix-v1')
    rows = summary.get('invocations')
    need(type(rows) is list and len(rows) == 44 and [r.get('ordinal') for r in rows] == list(range(1, 45)))
    refs = []
    for row in rows:
        group = row['original_refs']
        need(type(group) is dict and set(group) == {'receipt', 'preregister', 'policy', 'ledger', 'isolation'})
        refs.extend(group.values())
    catalog = summary['catalog_original_refs']
    need(type(catalog) is dict and set(catalog) == {'command', 'reservation', 'intent'})
    refs.extend(catalog.values())
    refs.append(summary['catalog_before41_ref'])
    provision = summary['history_provision_refs']
    need(type(provision) is list and 0 < len(provision) <= 32)
    refs.extend(provision)
    names = {SUMMARY, 'candidate.json', 'case-stack-catalog-before41-intent.json'}
    for ref in refs:
        need(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'})
        name = ref['path']
        need(type(name) is str and len(name) <= 240 and re.fullmatch('[A-Za-z0-9_-][A-Za-z0-9_.-]*', name)
             and name.endswith(('.json', '.txt')))
        need(type(ref['bytes']) is int and 0 < ref['bytes'] <= 1_400_000
             and type(ref['sha256']) is str and re.fullmatch('[a-f0-9]{64}', ref['sha256']))
        names.add(name)
    need(len(names) <= 512 and len({n.casefold() for n in names}) == len(names))
    need('case-execution.json' not in names and not any(n.startswith('root-original-') for n in names))
    return sorted(names)


def originals_shape(originals, helper):
    helper.blob_map(originals, 512, MAX_ORIGINALS)
    need(set(originals) == set(required_names(decode(originals[SUMMARY]))))
    need(all(0 < len(raw) <= 1_400_000 for raw in originals.values()))


def result(binding, *, replay=None, reason=None):
    return dict(format='canonical-component-inspection-v1', status='CANONICAL_COMPONENT_UNVERIFIED',
        binding=binding, canonical_replay=replay, missing=[] if reason is None else [reason],
        total_sql_commands=None, implicit_driver_sql_commands=None, numeric_bound_complete=False,
        hosted_equivalent_commands=None, hosted_projection='not_applicable_local_clean_stack_creation',
        READY=False, full_chain_admission=False, hosted_admitted=False, actual_old_history_claim=False)


def check_report(report, binding):
    need(type(report) is dict and set(report) == set(result(binding)))
    need(all(report[k] == v and type(report[k]) is type(v)
             for k, v in result(binding).items() if k not in ('canonical_replay', 'missing')))
    replay = report['canonical_replay']
    need(type(replay) is dict and replay.get('status') == 'CANONICAL_ORIGINAL_CORRELATION_REPLAYED_UNVERIFIED'
         and type(replay.get('invocation_count')) is int and replay['invocation_count'] == 44
         and len(replay.get('invocations', [])) == 44 and replay.get('total_sql_commands') is None
         and replay.get('hosted_equivalent_commands') is None and replay.get('full_chain_admission') is False
         and replay.get('hosted_admitted') is False and report['missing'] == replay['missing'])
    return report


def child(root, own_sha, request_path, request_sha, response_path):
    envelope = dict(format='canonical-component-child-v1', status='NO_GO', request_sha256=request_sha,
                    report=None, reason='input_or_source_invalid', phase='request', error_class=None)
    helper = None
    try:
        need(request_path.is_file() and request_path.stat().st_size <= MAX_REQUEST)
        raw = request_path.read_bytes()
        need(len(raw) <= MAX_REQUEST and sha(raw) == request_sha)
        request = decode(raw)
        need(type(request) is dict and set(request) == {'binding', 'sources', 'originals'})
        binding = identity(**request['binding'])
        sources = request['sources']
        need(sources.get(SELF) == own_sha)
        raw_source(root, SELF, sources)
        helper = support(root, sources)
        helper.source_map(sources)
        originals = helper.blob_map(request['originals'], 512, MAX_ORIGINALS, unpack=True)
        originals_shape(originals, helper)
        envelope['phase'] = 'loader'
        namespace = {'__name__': '_canonical_loader', '__file__': str(root / LOADER)}
        exec(compile(raw_source(root, LOADER, sources), str(root / LOADER), 'exec', dont_inherit=True), namespace)
        namespace['bootstrap_reader_stdlib']()
        loader = namespace['TrustedImports'](root, sources)
        helper.enable_legacy(loader)
        helper.install_audit(loader, request_path.parent.resolve(strict=True))
        with loader:
            envelope['phase'] = 'originals'
            reader = loader.module('quota_candidate_v1.runtime_exported_terminal')
            evidence = reader.Originals(originals, [dict(path=n, sha256=sha(v), bytes=len(v))
                                                  for n, v in sorted(originals.items())])
            trusted = reader.Trusted(root, sources)
            bound = dict(run_id=binding['run_id'], source_commit=binding['source_commit'],
                         ci_run=binding['ci_run'], candidate_sha=binding['candidate_sha256'], environment='disposable_ci')
            envelope['phase'] = 'replay'
            replayed = loader.module('admission_canonical_replay').replay(evidence, trusted, bound)
            report = result(binding, replay=replayed)
            report['missing'] = replayed['missing']
            check_report(report, binding)
        envelope.update(status='INSPECTED_UNVERIFIED', report=report, reason=None, phase='terminal')
    except BaseException as error:
        envelope.update(status='NO_GO', report=None, reason='input_source_or_replay_incomplete', error_class=type(error).__name__)
    try:
        if helper is None:
            return 2
        helper.save(response_path, envelope, MAX_RESPONSE)
        return 0
    except BaseException:
        return 2


def inspect_canonical(originals, *, source_commit, candidate_sha256, ci_run, run_id,
                      expected_sources, trusted_root):
    """External identity/source pins only; caller authenticates artifact bytes first."""
    bound = identity(source_commit, candidate_sha256, ci_run, run_id)
    root = Path(trusted_root).absolute()
    need(all(not p.is_symlink() and not getattr(p, 'is_junction', lambda: False)()
             for p in (root, *root.parents)))
    root = root.resolve(strict=True)
    sources = dict(expected_sources)
    need(Path(__file__).resolve(strict=True) == (root / SELF).resolve(strict=True))
    raw_source(root, SELF, sources)
    helper = support(root, sources)
    helper.source_map(sources)
    originals_shape(originals, helper)
    request = dict(binding=bound, sources=sources, originals=helper.blob_map(originals, 512, MAX_ORIGINALS))
    encoded = helper.encode(request)
    need(len(encoded) <= MAX_REQUEST)
    process = dict(status='NO_GO', source_sha256=sources[SELF], trusted_pins=dict(PINS),
        request_sha256=sha(encoded), bootstrap_sha256=sha(BOOTSTRAP.encode()), parent_cache_modified=False,
        limits=dict(input_bytes=MAX_REQUEST, output_bytes=MAX_RESPONSE, original_bytes=MAX_ORIGINALS,
                    original_members=512, member_bytes=1_400_000, wait_seconds=60, reap_seconds=5))
    report = result(bound, reason='canonical_child_incomplete')
    directory = tempfile.TemporaryDirectory(prefix='canonical-component-', ignore_cleanup_errors=True)
    cleanup_allowed = True
    try:
        private = Path(directory.name).resolve(strict=True)
        request_path, response_path = private/'request.json', private/'response.json'
        helper.save(request_path, request, MAX_REQUEST)
        command = [sys.executable, '-I', '-S', '-B', '-c', BOOTSTRAP, str(root), sources[SELF],
                   str(request_path), process['request_sha256'], str(response_path)]
        cleanup_allowed = False
        waited = helper.wait_child(command, helper.child_environment(private), str(private))
        cleanup_allowed = waited.get('wait_completed') is True
        process['wait'] = waited
        need(waited.get('accepted') is True)
        need(response_path.is_file() and not response_path.is_symlink() and response_path.stat().st_size <= MAX_RESPONSE)
        raw = response_path.read_bytes()
        need(len(raw) <= MAX_RESPONSE)
        envelope = decode(raw)
        need(type(envelope) is dict and set(envelope) == {'format', 'status', 'request_sha256', 'report', 'reason', 'phase', 'error_class'}
             and envelope['format'] == 'canonical-component-child-v1'
             and envelope['request_sha256'] == process['request_sha256'])
        need(envelope['phase'] in ('request', 'loader', 'originals', 'replay', 'terminal'))
        need(envelope['error_class'] is None or type(envelope['error_class']) is str
             and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,99}', envelope['error_class']))
        process.update(response_sha256=sha(raw), response_bytes=len(raw), child_phase=envelope['phase'],
                       child_error_class=envelope['error_class'])
        if envelope['status'] == 'INSPECTED_UNVERIFIED':
            need(envelope['reason'] is None and envelope['phase'] == 'terminal' and envelope['error_class'] is None)
            report = check_report(envelope['report'], bound)
            process['status'] = 'INSPECTED_UNVERIFIED'
        else:
            need(envelope['status'] == 'NO_GO' and envelope['report'] is None
                 and envelope['reason'] == 'input_source_or_replay_incomplete')
            report = result(bound, reason=envelope['reason'])
        # Recheck every executed/critical source through the child's loader and
        # these entry sources again in the parent after the original wait.
        for name in (SELF, *PINS):
            raw_source(root, name, sources)
    except BaseException as error:
        report = result(bound, reason='canonical_child_incomplete')
        process.update(status='NO_GO', error_class=type(error).__name__)
    finally:
        if not cleanup_allowed:
            directory._finalizer.detach()
            process.update(status='NO_GO', private_cleanup='deferred_unconfirmed_reap',
                           retained_directory_id=Path(directory.name).name)
            report = result(bound, reason='canonical_child_reap_unconfirmed')
        else:
            try:
                directory.cleanup()
                need(not Path(directory.name).exists())
                process['private_cleanup'] = 'completed'
            except BaseException:
                process.update(status='NO_GO', private_cleanup='incomplete')
                report = result(bound, reason='canonical_private_cleanup_incomplete')
    report['reader_process'] = process
    return report
