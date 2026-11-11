"""Bounded staging-only matrix packaging and independent ZIP verification."""
import base64
import hashlib
import io
import json
import pathlib
import re
import sys
import zipfile

import admission_matrix_ci as matrix
import admission_case_archive as case_archive
from auth_failure import CASES as AUTH_CASES
import admission_ops as single

MAX_ARCHIVE = 30000000
MAX_FILES = 1100
MAX_MEMBER = 2000000
TERMINAL_MODULE = 'quota_candidate_v1.runtime_exported_terminal'
TERMINAL_SOURCE = '_offline/phase6e11/endchain_v1/quota_candidate_v1/runtime_exported_terminal.py'
TERMINAL_PACKAGE = '_offline/phase6e11/endchain_v1/quota_candidate_v1/__init__.py'
TERMINAL_PROCESS = '_offline/phase6e11/endchain_v1/admission_terminal_process.py'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def object_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'matrix_duplicate_json_key')
            result[key] = value
        return result
    result = json.loads(raw, object_pairs_hook=pairs)
    require(type(result) is dict, 'matrix_json_object')
    return result


def source_map(value):
    require(type(value) is dict and bool(value), 'matrix_source_map')
    require(len({p.casefold() for p in value if isinstance(p, str)}) == len(value),
            'matrix_source_alias')
    for path, digest in value.items():
        require(isinstance(path, str) and re.fullmatch('[A-Za-z0-9_./-]+', path)
                and not path.startswith('/') and all(p not in ('', '.', '..') for p in path.split('/'))
                and isinstance(digest, str) and re.fullmatch('[a-f0-9]{64}', digest),
                'matrix_source_entry')
    return value


def prepared_sources(raw, candidate):
    require(len(raw) <= MAX_ARCHIVE and hashlib.sha256(raw).hexdigest() == candidate,
            'matrix_prepared_candidate_digest')
    bundle = object_json(raw)
    require(bundle.get('format') == 1 and type(bundle.get('files')) is dict
            and bool(bundle['files']), 'matrix_prepared_candidate_format')
    expected = {}
    for path, encoded in bundle['files'].items():
        require(isinstance(encoded, str), 'matrix_prepared_source_encoding')
        data = base64.b64decode(encoded, validate=True)
        expected[path] = hashlib.sha256(data).hexdigest()
    return source_map(expected)


def inspect_terminal(payloads, case, originals, *, head, candidate, run,
                     expected_sources, trusted_root):
    """Use a fresh bounded reader process; never clear the parent's import cache."""
    root = pathlib.Path(trusted_root).absolute()
    file = root/TERMINAL_PROCESS
    expected = expected_sources.get(TERMINAL_PROCESS)
    require(type(expected) is str and re.fullmatch('[a-f0-9]{64}', expected),
            'matrix_terminal_process_missing')
    require(file.resolve(strict=True).is_relative_to(root)
            and all(not p.is_symlink() and not getattr(p, 'is_junction', lambda: False)()
                    for p in (file, *file.parents)), 'matrix_terminal_process_path')
    require(file.is_file() and file.stat().st_size <= MAX_MEMBER, 'matrix_terminal_process_size')
    raw = file.read_bytes()
    require(len(raw) <= MAX_MEMBER and hashlib.sha256(raw).hexdigest() == expected,
            'matrix_terminal_process_hash')
    namespace = {'__name__': '_installed_terminal_parent', '__file__': str(file)}
    exec(compile(raw, str(file), 'exec', dont_inherit=True), namespace)
    result = namespace['inspect_terminal'](payloads, case, originals, head=head,
        candidate=candidate, run=run, expected_sources=expected_sources, trusted_root=root)
    require(type(result) is dict and result.get('status') == 'CASE_TERMINAL_UNVERIFIED'
            and result.get('case_name') == case.get('case_name')
            and result.get('run_id') == case.get('run_id')
            and result.get('case_sha256') == hashlib.sha256(payloads['case-execution.json']).hexdigest()
            and result.get('full_chain_admission') is False
            and result.get('hosted_admitted') is False,
            'matrix_terminal_reader_unreviewed_admission')
    # This reader currently has explicit missing domains. Do not promote a
    # producer label or a truthy inspection object to semantic admission.
    return result


def verify_archive(raw, *, name, head, candidate, run, expected_sources, trusted_root=None):
    source_map(expected_sources)
    require(name in matrix.NAMES and len(raw) <= MAX_ARCHIVE, 'matrix_archive_scope')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        require(1 <= len(names) <= MAX_FILES and len(set(names)) == len(names)
                and len({n.casefold() for n in names}) == len(names), 'matrix_archive_members')
        require(all(re.fullmatch(r'[A-Za-z0-9_.-]+\.(json|txt|png)', n) for n in names), 'matrix_archive_paths')
        require(all(not re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?',
                                     n, re.IGNORECASE) for n in names), 'matrix_archive_device_path')
        require(sum(i.file_size for i in infos) <= MAX_ARCHIVE
                and all(0 <= i.file_size <= MAX_MEMBER and not i.flag_bits & 1
                        and (i.external_attr >> 16) & 0o170000 != 0o120000 for i in infos),
                'matrix_archive_size_or_link')
        manifest = object_json(archive.read('artifact-manifest.json'))
        require(set(names) == set(manifest) | {'artifact-manifest.json'}, 'matrix_manifest_members')
        payloads = {}
        for path, expected in manifest.items():
            data = archive.read(path)
            require(re.fullmatch('[a-f0-9]{64}', expected) and hashlib.sha256(data).hexdigest() == expected,
                    'matrix_member_digest')
            payloads[path] = data
        result = object_json(payloads['result.json'])
        sources = object_json(payloads['candidate.json'])
        require(source_map(sources.get('sources')) == expected_sources, 'matrix_source_contents')
        require(result.get('commit') == head and str(result.get('run_id')) == str(run)
                and result.get('candidate_sha256') == candidate and sources.get('sha256') == candidate,
                'matrix_result_binding')
        case = None
        if name != 'application':
            require(result.get('case_name') == name, 'matrix_case_binding')
            if 'case-execution.json' in payloads:
                case = object_json(payloads['case-execution.json'])
                require(case.get('case_name') == name and case.get('source_commit') == head
                        and str(case.get('ci_run')) == str(run) and case.get('candidate_sha256') == candidate,
                        'matrix_case_receipt_binding')
        require(result.get('hosted_admitted') is not True and result.get('full_chain_admission') is not True,
                'matrix_unreviewed_admission')
        payloads['artifact-manifest.json'] = archive.read('artifact-manifest.json')
        bootstrap, originals, terminal = None, None, None
        if name != 'application' and result.get('status') == 'CASE_PASS':
            require(case is not None and case.get('format') == 'disposable-case-terminal-v1'
                    and case.get('case_pass') is True and case.get('matrix_aggregation_required') is True
                    and case.get('full_chain_admission') is False and case.get('hosted_admitted') is False,
                    'matrix_terminal_contract')
            require(source_map(case.get('terminal_source_hashes')) == expected_sources,
                    'matrix_terminal_source_binding')
            originals = case_archive.verify(payloads, case.get('original_archive_ref'),
                                            case.get('original_refs'))
        if name in ('pre_migration', 'post_migration') and result.get('status') == 'CASE_PASS':
            require(trusted_root is not None, 'matrix_bootstrap_trusted_sources_required')
            from admission_matrix_bootstrap import verify_bootstrap_case
            bootstrap = verify_bootstrap_case(payloads, case_name=name, source_commit=head,
                ci_run=str(run), candidate_sha256=candidate, expected_sources=expected_sources,
                trusted_root=trusted_root)
        if originals is not None and trusted_root is not None:
            terminal = inspect_terminal(payloads, case, originals, head=head,
                candidate=candidate, run=run, expected_sources=expected_sources,
                trusted_root=trusted_root)
        return {'result': result, 'case': case, 'payloads': payloads, 'bootstrap_verified': bootstrap,
            'originals': originals, 'terminal_verified': terminal, 'auth_verified': None,
            'case_sha256': hashlib.sha256(payloads['case-execution.json']).hexdigest() if case else None,
            'manifest_sha256': hashlib.sha256(archive.read('artifact-manifest.json')).hexdigest(),
            'source_manifest_sha256': hashlib.sha256(payloads['candidate.json']).hexdigest(),
            'archive_sha256': hashlib.sha256(raw).hexdigest(), 'files': len(manifest)}


def aggregate(verified, *, run_conclusion):
    require(set(verified) == set(matrix.NAMES), 'matrix_incomplete_case_set')
    require(len({v['source_manifest_sha256'] for v in verified.values()}) == 1,
            'matrix_different_source_manifests')
    blockers = []
    if run_conclusion != 'success':
        blockers.append('ci_execution_not_successful')
    app = verified['application']['result']
    if app.get('status') != 'CLEAN_CI_PASS':
        blockers.append('application_or_combined_admission_incomplete')
    app_value = verified['application']
    auth = app_value.get('auth_verified')
    if not (type(auth) is dict and auth.get('status') == 'AUTH_FAILURE_COVERAGE_VERIFIED'
            and auth.get('case_names') == list(AUTH_CASES)
            and auth.get('source_manifest_sha256') == app_value['source_manifest_sha256']
            and auth.get('archive_sha256') == app_value['archive_sha256']):
        blockers.append('auth_failure_coverage_unverified')
    databases, clusters, containers, auth_containers, identities = set(), set(), set(), set(), set()
    for name in matrix.NAMES[1:]:
        value = verified[name]
        case = value['case']
        if value['result'].get('status') != 'CASE_PASS' or not case or case.get('status') != 'CASE_PASS':
            blockers.append(name + ':actual_case_incomplete')
            continue
        terminal = value.get('terminal_verified')
        if not (type(terminal) is dict and terminal.get('status') == 'CASE_TERMINAL_VERIFIED'
                and terminal.get('case_name') == name
                and terminal.get('run_id') == case.get('run_id')
                and terminal.get('case_sha256') == value.get('case_sha256')
                and isinstance(value.get('case_sha256'), str)
                and re.fullmatch('[a-f0-9]{64}', value['case_sha256'])):
            blockers.append(name + ':terminal_semantics_unverified')
        isolation = case.get('isolation')
        if not isinstance(isolation, dict):
            blockers.append(name + ':isolation_evidence_missing')
            continue
        identity = (isolation.get('pg_system_identifier'), isolation.get('database_oid'))
        container = isolation.get('pg_container')
        auth_container = isolation.get('auth_container')
        early = name in ('pre_migration', 'post_migration')
        run_id = isolation.get('run_id')
        target = isolation.get('db_target_sha256')
        require(isinstance(identity[0], str) and re.fullmatch('[1-9][0-9]{0,19}', identity[0])
                and type(identity[1]) is int and identity[1] > 0
                and isinstance(container, str) and re.fullmatch('[a-f0-9]{64}', container)
                and (early or isinstance(auth_container, str) and re.fullmatch('[a-f0-9]{64}', auth_container))
                and isinstance(run_id, str) and re.fullmatch('[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}', run_id)
                and isinstance(target, str) and re.fullmatch('[a-f0-9]{64}', target),
                'matrix_isolation_identity')
        require(identity not in databases and identity[0] not in clusters and container not in containers
                and (early or auth_container not in auth_containers) and run_id not in identities,
                'matrix_database_reuse')
        if early:
            proof = value.get('bootstrap_verified')
            require(isinstance(proof, dict) and proof.get('status') == 'BOOTSTRAP_ABSENCE_VERIFIED'
                    and proof.get('case_name') == name and proof.get('run_id') == run_id
                    and proof.get('pg_container') == container
                    and proof.get('pg_system_identifier') == identity[0]
                    and proof.get('database_oid') == identity[1]
                    and proof.get('db_target_sha256') == target
                    and proof.get('isolation_sha256') == hashlib.sha256(json.dumps(isolation,
                        sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
                    and isolation.get('auth_state') == 'not_started' and auth_container is None
                    and isolation.get('auth_database_bound') is False
                    and isolation.get('auth_target_sha256') is None and isolation.get('reused') is False,
                    'matrix_bootstrap_absence_unverified')
        else:
            require(isolation.get('reused') is False and isolation.get('auth_database_bound') is True
                    and auth_container != container and isolation.get('auth_target_sha256') == target,
                    'matrix_auth_database_isolation')
        databases.add(identity); clusters.add(identity[0]); containers.add(container)
        if not early: auth_containers.add(auth_container)
        identities.add(run_id)
    return {'status': 'NO_GO' if blockers else 'LOCAL_MATRIX_VERIFIED_PENDING_REVIEW',
        'blockers': blockers, 'cases': {name: {'status': v['result'].get('status'),
            'archive_sha256': v['archive_sha256'], 'manifest_sha256': v['manifest_sha256'],
            'files': v['files']} for name, v in verified.items()},
        'same_source_manifest_sha256': next(iter(verified.values()))['source_manifest_sha256'],
        'ci_conclusion': run_conclusion, 'hosted_admitted': False,
        'owner_window_allowed': False, 'independent_review_required': True}


def collect(folder, run):
    ops = single.ops
    metadata = ops.g.api('/actions/runs/' + str(run))
    blob = object_json(ops.disk(folder/'blob.json').read_bytes())
    expected_sources = prepared_sources(ops.disk(folder/'candidate.json').read_bytes(), blob['sha256'])
    head = object_json(ops.disk(folder/'dispatch.json').read_bytes())['head']
    require(metadata['status'] == 'completed' and metadata['run_attempt'] == 1
            and metadata['head_sha'] == head and blob['sha256'] in metadata['display_title'],
            'matrix_run_binding')
    artifacts = ops.g.api('/actions/runs/' + str(run) + '/artifacts?per_page=100')['artifacts']
    expected = {'phase6e-admission-' + str(run) + '-' + n + '-1': n for n in matrix.NAMES}
    matches = [a for a in artifacts if a['name'] in expected]
    require(len({a['name'] for a in matches}) == len(matches), 'matrix_artifacts_ambiguous')
    target = ops.disk(folder/('verified-matrix-' + str(run)))
    target.mkdir(exist_ok=False)
    verified, failures = {}, {}
    for artifact in matches:
        require(not artifact['expired'] and artifact['size_in_bytes'] <= MAX_ARCHIVE,
                'matrix_artifact_expired_or_large')
        name = expected[artifact['name']]
        raw = ops.g.api('/actions/artifacts/' + str(artifact['id']) + '/zip', raw=True)
        digest = hashlib.sha256(raw).hexdigest()
        require(artifact['digest'] == 'sha256:' + digest, 'matrix_archive_digest')
        path = target/name; path.mkdir(exist_ok=False)
        with (path/'evidence.zip').open('xb') as stream: stream.write(raw)
        # Invalid ZIP remains historical evidence, never retried or overwritten.
        try:
            checked = verify_archive(raw, name=name, head=head, candidate=blob['sha256'], run=run,
                                     expected_sources=expected_sources, trusted_root=ops.ROOT)
        except Exception as error:
            failures[name] = {'error_class': type(error).__name__, 'archive_sha256': digest}
            ops.g.write(path/'incomplete-collection.json', failures[name])
            continue
        verified[name] = checked
        for relative, data in checked['payloads'].items():
            with (path/relative).open('xb') as stream: stream.write(data)
    if set(verified) == set(matrix.NAMES):
        result = aggregate(verified, run_conclusion=metadata.get('conclusion'))
    else:
        result = {'status': 'NO_GO', 'blockers': ['matrix_incomplete_case_set'],
            'missing_or_invalid': sorted(set(matrix.NAMES) - set(verified)), 'failures': failures,
            'verified_archives': {n: v['archive_sha256'] for n, v in verified.items()},
            'hosted_admitted': False, 'owner_window_allowed': False}
    result.update(commit=head, ci_run=str(run), candidate_sha256=blob['sha256'])
    ops.g.write(target/'matrix-collection.json', result)
    print(json.dumps({'path': str(target), 'status': result['status'], 'blockers': result['blockers']}))


def main():
    mode = sys.argv[1]
    single.ops.WORKFLOW = matrix.WORKFLOW
    if mode in ('prepare', 'dispatch'):
        matrix.source_contract()  # No upload/runner attempt with an unfinished adapter.
    if mode == 'dispatch':
        single.dispatch_preflight(sys.argv[2])
    if mode == 'artifact':
        folder = pathlib.Path(sys.argv[2]).resolve()
        require(folder.parent == single.ops.ROOT/'supabase/.temp'
                and folder.name.startswith('phase6e-server-ci-'), 'matrix_collection_scope')
        return collect(folder, int(sys.argv[3]))
    return single.ops.main()


if __name__ == '__main__':
    main()
