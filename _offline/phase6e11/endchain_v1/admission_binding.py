"""Offline preparation only. Evidence binding never grants hosted authority."""
import datetime as dt
import hashlib
import json
import pathlib
import re
import uuid

FORMAT = 'fmz6e11-admission-preparation-v1'
NEW_RUN = '11a909f4-7113-424a-aa4b-ce9964720a3e'
OLD_RUN = '6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'
PROJECT = 'mokxyyullfhkfalopbzd'
REPOSITORY = 'Yourizorge/fitmetzorge-staging'
MAXIMUM = 2349
M45 = 'supabase/migrations/20261018070231_phase6e11_recovery_run_quota.sql'
PRESERVED = {
    M45: '64498fa910966497e92705dcf66b76f40c40f01c006aed98c191ce109dd88635',
    '_offline/phase6e11/endchain_v1/authorization.json':
        'ad79d3c4c0dd79879567cee7c20999ba7ae05e2205ddc3c89a6597767286ef7e',
}
REQUIRED = frozenset(('migration_bundle', 'python_register', 'node_register',
    'sql_register', 'command_budget', 'auth_register', 'fixture_inventory',
    'cleanup_plan', 'owner_preparation_instruction'))
GATES = frozenset(('cli_predispatch', 'auth_cleanup', 'fixture_cleanup',
    'fault_matrix', 'budget_prefixes', 'strict_wal', 'same_source_ci',
    'independent_review'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def digest(value):
    if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value):
        raise ValueError('binding_digest')
    return value


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', value):
        raise ValueError('binding_timestamp')
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))


def source_path(root, name):
    if not isinstance(name, str) or '\\' in name or ':' in name:
        raise ValueError('binding_source_path')
    relative = pathlib.PurePosixPath(name)
    if relative.is_absolute() or any(p in ('..', '.') for p in relative.parts) or str(relative) != name:
        raise ValueError('binding_source_path')
    path = root / name
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('binding_source_path')
    return path


def verify_sources(root, sources):
    if not isinstance(sources, dict) or not sources:
        raise ValueError('binding_sources_empty')
    aliases = set()
    for name, expected in sources.items():
        if name.casefold() in aliases:
            raise ValueError('binding_source_alias')
        aliases.add(name.casefold())
        path = source_path(root, name)
        if sha(path.read_bytes()) != digest(expected):
            raise ValueError('binding_source_changed')
    return len(sources)


def prepare(root, *, source_commit, candidate_sha256, sources, registers,
            created_at, expires_at):
    """Caller stores this immutable receipt separately, never inside its candidate ZIP."""
    if not isinstance(source_commit, str) or not re.fullmatch('[a-f0-9]{40}', source_commit):
        raise ValueError('binding_source_commit')
    digest(candidate_sha256)
    start, end = timestamp(created_at), timestamp(expires_at)
    if not dt.timedelta(0) < end-start <= dt.timedelta(hours=24):
        raise ValueError('binding_preparation_expiry')
    verify_sources(root, sources)
    verify_sources(root, PRESERVED)
    if set(registers) != REQUIRED:
        raise ValueError('binding_register_set')
    for name, item in registers.items():
        if not isinstance(item, dict) or set(item) != {'path', 'sha256'}:
            raise ValueError('binding_register_shape')
        if sources.get(item['path']) != digest(item['sha256']):
            raise ValueError('binding_register_not_source_bound')
    value = {
        'format': FORMAT, 'run_id': NEW_RUN, 'repository': REPOSITORY,
        'branch': 'main', 'project': PROJECT, 'source_commit': source_commit,
        'candidate_sha256': candidate_sha256, 'sources': dict(sources),
        'registers': registers, 'created_at': created_at, 'expires_at': expires_at,
        'maximum_sql': MAXIMUM, 'preserved': dict(PRESERVED),
        'old_run_id': OLD_RUN, 'old_run_reused': False,
        'hosted_permission': False, 'hosted_admitted': False,
        'ci': None, 'gates': {name: 'PENDING' for name in sorted(GATES)},
        'status': 'PREPARATION_ONLY_NOT_EXECUTABLE',
    }
    return value


def validate(value, root, now):
    if not isinstance(value, dict) or value.get('format') != FORMAT:
        raise ValueError('binding_format')
    if (value.get('run_id') != NEW_RUN or str(uuid.UUID(value['run_id'])) != NEW_RUN
            or value.get('old_run_id') != OLD_RUN or value.get('old_run_reused') is not False):
        raise ValueError('binding_run_identity')
    if (value.get('project'), value.get('repository'), value.get('branch')) != (PROJECT, REPOSITORY, 'main'):
        raise ValueError('binding_scope')
    if (value.get('hosted_permission') is not False or value.get('hosted_admitted') is not False
            or value.get('maximum_sql') != MAXIMUM or type(value.get('maximum_sql')) is not int):
        raise ValueError('binding_preparation_not_authority')
    recreated = prepare(root, **{k: value[k] for k in ('source_commit', 'candidate_sha256',
        'sources', 'registers', 'created_at', 'expires_at')})
    if value.get('preserved') != recreated['preserved']:
        raise ValueError('binding_preserved_changed')
    if not timestamp(value['created_at']) <= timestamp(now) < timestamp(value['expires_at']):
        raise ValueError('binding_expired_or_future')
    gates = value.get('gates')
    if not isinstance(gates, dict) or set(gates) != GATES or any(v not in ('PENDING', 'PASS', 'NO_GO') for v in gates.values()):
        raise ValueError('binding_gate_set')
    ci = value.get('ci')
    if ci is not None:
        if (not isinstance(ci, dict) or set(ci) != {'run', 'source_commit',
                'chain_archive_sha256', 'chain_manifest_sha256', 'chain_candidate_sha256',
                'app_archive_sha256', 'app_manifest_sha256', 'app_candidate_sha256', 'result_sha256'}
                or ci['source_commit'] != value['source_commit']
                or not isinstance(ci['run'], str) or not re.fullmatch('[1-9][0-9]*', ci['run'])):
            raise ValueError('binding_ci_shape')
        for key in (key for key in ci if key.endswith('_sha256')):
            digest(ci[key])
    return recreated


def attach_ci(value, *, chain, app, root, now):
    """Use the full existing verifier; a caller's PASS dictionary is not evidence."""
    validate(value, root, now)
    if value.get('ci') is not None:
        raise ValueError('binding_ci_already_bound')
    from closure_ops import validate_bundle, verify_archive, object_json, bounded_read
    result = validate_bundle(chain, app, root=root)
    if (result.get('status') != 'COMPOSED_CI_PASS_PENDING_INDEPENDENT_REVIEW'
            or result.get('commit') != value['source_commit']
            or result.get('hosted_admitted') is not False
            or not re.fullmatch('[1-9][0-9]*', str(result.get('run_id', '')))):
        raise ValueError('binding_complete_ci_required')
    evidence = {'run': str(result['run_id']), 'source_commit': result['commit'],
                'result_sha256': sha(canonical(result))}
    for kind, folder in (('chain', chain), ('app', app)):
        bundle = verify_archive(folder, kind)
        item = object_json(bundle['payloads']['result.json'])
        if (item.get('commit') != value['source_commit']
                or str(item.get('run_id')) != evidence['run']):
            raise ValueError('binding_ci_identity_changed')
        evidence[kind+'_candidate_sha256'] = digest(item['candidate_sha256'])
        evidence[kind+'_archive_sha256'] = digest(bundle['archive_sha256'])
        evidence[kind+'_manifest_sha256'] = sha(bounded_read(pathlib.Path(folder)/'artifact-manifest.json', 2000000))
    if evidence['chain_candidate_sha256'] != value['candidate_sha256']:
        raise ValueError('binding_candidate_mismatch')
    new = json.loads(canonical(value))
    new['ci'] = evidence
    new['gates']['same_source_ci'] = 'PASS'
    return new


def readiness(value, root, now):
    validate(value, root, now)
    blockers = sorted(name for name, status in value['gates'].items() if status != 'PASS')
    if value.get('ci') is None and 'same_source_ci' not in blockers:
        blockers.append('same_source_ci')
    # This manifest is preparation, not a substitute for closure_ops ZIP validation
    # or an independently signed-off review of the actual artifacts.
    blockers.extend(('verified_composed_artifacts_required', 'independent_artifact_review_required'))
    return {'run_id': NEW_RUN, 'blockers': blockers,
        'status': 'NO_GO',
        'hosted_admitted': False, 'owner_window_allowed': False,
        'hosted_calls': 0, 'old_binding_unchanged': True}
