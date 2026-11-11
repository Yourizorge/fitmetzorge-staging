"""Compile and verify an appended quota delta. Never connects or executes SQL."""
import datetime as dt
import hashlib
import json
import pathlib
import re
import uuid

import admission_binding as binding
import admission_quota_readonly as baseline
import sql_protocol as protocol

HERE = pathlib.Path(__file__).resolve().parent
PREFIX = '_offline/phase6e11/endchain_v1/'
FORMAT = 'fmz6e11-disposable-quota-candidate-v1'
PURPOSE = '6e11_disposable_quota_candidate_v1'
M44 = 'supabase/migrations/20261012185121_phase6e11_single_endchain_budget.sql'
M41 = 'supabase/migrations/20261012104331_phase6e11_controller_evidence.sql'
PINS = {**binding.PRESERVED,
    M44: 'b21650fa40e2143fb11faff8aeb486ce07bdbead15c7e33b9695b2845e6e4d3e',
    M41: 'bab79b7ca5876c2dcef055d0e95997595772aebc051283e69bbeb2ca1dc4bd57'}
SUPPORT = ('admission_binding.py', 'admission_quota_readonly.py', 'sql_protocol.py')
OWN = ('__init__.py', 'compiler.py', 'candidate.sql.in', 'test_quota_candidate.py')
SCHEMA = 'fmz6e11_controller_private'
FUNCTION = 'quota_candidate_v1_receipt'
UUID_TEXT = r'[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}'


class CandidateStop(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise CandidateStop(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def moment(value):
    require(isinstance(value, str) and re.fullmatch(
        r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', value), 'candidate_timestamp')
    try:
        return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise CandidateStop('candidate_timestamp') from None


def hex_digest(value, size=64):
    require(isinstance(value, str) and re.fullmatch('[a-f0-9]{%d}' % size, value),
            'candidate_digest')


def read_source(root, name):
    try:
        path = binding.source_path(pathlib.Path(root), name)
        require(path.is_file(), 'candidate_source_missing')
        return path.read_bytes()
    except (OSError, ValueError):
        raise CandidateStop('candidate_source_missing_or_unsafe') from None


def source_files(root):
    """Explicit raw hashes. No implicit checkout or environment fallback."""
    names = set(PINS) | {PREFIX + n for n in SUPPORT} | {
        PREFIX + 'quota_candidate_v1/' + n for n in OWN}
    return {name: sha(read_source(root, name)) for name in sorted(names)}


def verify_sources(root, sources):
    require(type(sources) is dict and 1 <= len(sources) <= 4096,
            'candidate_sources')
    required = set(PINS) | {PREFIX + n for n in SUPPORT} | {
        PREFIX + 'quota_candidate_v1/' + n for n in OWN}
    require(required <= set(sources), 'candidate_required_sources')
    require(len({n.casefold() for n in sources}) == len(sources), 'candidate_source_alias')
    for name, expected in sources.items():
        hex_digest(expected)
        require(sha(read_source(root, name)) == expected, 'candidate_source_hash')
    for name, expected in PINS.items():
        require(sources[name] == expected, 'candidate_frozen_pin')
    # Validate the loaded implementation as well as the caller's source tree.
    for module, name in ((binding, 'admission_binding.py'),
                         (baseline, 'admission_quota_readonly.py'),
                         (protocol, 'sql_protocol.py')):
        require(sha(pathlib.Path(module.__file__).read_bytes()) == sources[PREFIX + name],
                'candidate_loaded_source')
    for name in OWN:
        require(sha((HERE / name).read_bytes()) == sources[PREFIX + 'quota_candidate_v1/' + name],
                'candidate_loaded_source')


def legacy_ids(root):
    """Reject every UUID in the pinned legacy contracts, not only October's ID."""
    result = {binding.NEW_RUN, binding.OLD_RUN}
    for name in PINS:
        result.update(re.findall(UUID_TEXT, read_source(root, name).decode('ascii').lower()))
    return result


def prepare(root, *, source_commit, candidate_sha256, github_run, created_at,
            expires_at, cases, sources=None):
    value = dict(format=FORMAT, parent_run=binding.NEW_RUN, purpose=PURPOSE,
        environment='disposable_ci', repository=binding.REPOSITORY, branch='main',
        source_commit=source_commit, candidate_sha256=candidate_sha256,
        github_run=github_run, created_at=created_at, expires_at=expires_at,
        maximum_sql=2349, cases=cases, sources=source_files(root) if sources is None else sources,
        preserved=dict(PINS), hosted_permission=False, clean47_baseline=False,
        runtime_integrated=False, status='OFFLINE_CANDIDATE_NOT_EXECUTED')
    validate_manifest(value, root, now=created_at)
    return json.loads(canonical(value))


def validate_manifest(value, root, *, now):
    require(type(value) is dict and set(value) == {
        'format', 'parent_run', 'purpose', 'environment', 'repository', 'branch',
        'source_commit', 'candidate_sha256', 'github_run', 'created_at', 'expires_at',
        'maximum_sql', 'cases', 'sources', 'preserved', 'hosted_permission',
        'clean47_baseline', 'runtime_integrated', 'status'}, 'candidate_manifest_shape')
    for key, expected in dict(format=FORMAT, parent_run=binding.NEW_RUN, purpose=PURPOSE,
        environment='disposable_ci', repository=binding.REPOSITORY, branch='main',
        maximum_sql=2349, preserved=PINS, hosted_permission=False,
        clean47_baseline=False, runtime_integrated=False,
        status='OFFLINE_CANDIDATE_NOT_EXECUTED').items():
        require(baseline.typed_equal(value[key], expected), 'candidate_scope_' + key)
    hex_digest(value['source_commit'], 40)
    hex_digest(value['candidate_sha256'])
    run = value['github_run']
    require(isinstance(run, str) and re.fullmatch('[1-9][0-9]{0,18}', run)
            and int(run) <= 9223372036854775807, 'candidate_github_run')
    start, end, current = moment(value['created_at']), moment(value['expires_at']), moment(now)
    require(dt.timedelta(0) < end - start <= dt.timedelta(minutes=10), 'candidate_expiry_window')
    require(start <= current < end, 'candidate_expired_or_future')
    verify_sources(root, value['sources'])
    cases, ids, labels = value['cases'], set(), set()
    require(type(cases) is list and 1 <= len(cases) <= 14, 'candidate_cases')
    forbidden = legacy_ids(root)
    for case in cases:
        require(type(case) is dict and set(case) == {'id', 'label', 'cap'}, 'candidate_case_shape')
        uid, label, cap = case['id'], case['label'], case['cap']
        try:
            parsed = uuid.UUID(uid)
        except (ValueError, TypeError, AttributeError):
            raise CandidateStop('candidate_case_uuid') from None
        require(str(parsed) == uid and parsed.version == 4, 'candidate_case_uuid')
        require(uid not in forbidden and uid not in ids, 'candidate_legacy_or_repeated_case')
        require(isinstance(label, str) and re.fullmatch('[a-z][a-z0-9_]{0,47}', label)
                and label not in labels, 'candidate_case_label')
        require(type(cap) is int and 1 <= cap <= 2349, 'candidate_case_cap')
        ids.add(uid); labels.add(label)
    return sha(canonical(value))


def literal(value):
    require(isinstance(value, str) and '\x00' not in value and '\\' not in value,
            'candidate_sql_literal')
    return "'" + value.replace("'", "''") + "'"


def compile_candidate(root, manifest, samples, *, now):
    """samples are the existing four readonly quota queries, not a PASS boolean."""
    manifest_sha = validate_manifest(manifest, root, now=now)
    contract = baseline.source_contract(read_source(root, binding.M45))
    try:
        require(set(samples) == set(baseline.QUERIES), 'candidate_baseline_shape')
        baseline.validate(samples, contract)
    except (KeyError, TypeError, baseline.QuotaStop):
        raise CandidateStop('candidate_baseline_invalid') from None
    expression = samples['constraint'][0]['expression']
    require('$qc_' not in expression and '@@' not in expression, 'candidate_baseline_literal')
    cases = manifest['cases']
    case_array = 'array[' + ','.join(literal(c['id']) + '::uuid' for c in cases) + ']'
    # The M45 expression is source-bound. Only append new, exact CASE branches.
    old_check = ('command_count>=0 and command_count<=case\n'
        " when id='1c3bf7e7-bc78-40c5-9ac1-5ba3512ec66d'::uuid then 2237\n"
        " when id='6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'::uuid then 2349\n")
    branches = ''.join(' when id=' + literal(c['id']) + '::uuid then ' + str(c['cap']) + '\n'
                       for c in cases)
    replacements = {
        'PARENT': manifest['parent_run'], 'PURPOSE': manifest['purpose'],
        'MANIFEST_SHA': manifest_sha, 'START': manifest['created_at'],
        'END': manifest['expires_at'], 'CASES': case_array,
        'BASELINE_EXPRESSION': literal(expression),
        'M45_BODY': literal(contract['body']),
        'CHECK': old_check + branches + ' else 128 end',
        'CATALOG_ROWS': ',\n'.join('(' + ','.join((literal(case['id']) + '::uuid',
            literal(PURPOSE), str(case['cap']), literal(binding.NEW_RUN) + '::uuid',
            literal(manifest['source_commit']), literal(manifest['candidate_sha256']),
            manifest['github_run'], literal(manifest['created_at']) + '::timestamptz',
            literal(manifest['expires_at']) + '::timestamptz', literal(manifest_sha))) + ')'
            for case in cases),
    }
    sql = (HERE / 'candidate.sql.in').read_text(encoding='ascii')
    require(set(re.findall(r'@@([A-Z0-9_]+)@@', sql)) == set(replacements), 'candidate_template_keys')
    for key, text in replacements.items():
        sql = sql.replace('@@' + key + '@@', text)
    require('@@' not in sql, 'candidate_template_unresolved')
    nodes = baseline.parser().parse_sql(sql)
    plan = dict(format=FORMAT, manifest_sha256=manifest_sha, sql_sha256=sha(sql.encode('ascii')),
        baseline_sha256=sha(canonical(samples)), source_commit=manifest['source_commit'],
        candidate_sha256=manifest['candidate_sha256'], parent_run=binding.NEW_RUN,
        purpose=PURPOSE, case_ids=[c['id'] for c in cases],
        top_level_statements=len(nodes), setup_accounting='SEPARATE_LOCAL_DIAGNOSTIC_PENDING',
        actual_protocol_commands=None, runtime_budget_verified=False, execution_admitted=False,
        fresh_case_absence='PENDING_LOCKED_DATABASE_CHECK',
        clean47_baseline=False, hosted_permission=False, executed=False,
        existing_github_run_unique_preserved=True, existing_running_slot_unique_preserved=True)
    return {'manifest': json.loads(canonical(manifest)), 'plan': plan, 'sql': sql}


def validate_candidate(root, artifact, samples, *, now):
    require(type(artifact) is dict and set(artifact) == {'manifest', 'plan', 'sql'},
            'candidate_artifact_shape')
    expected = compile_candidate(root, artifact['manifest'], samples, now=now)
    require(baseline.typed_equal(artifact, expected), 'candidate_artifact_changed')
    return expected['plan']


def binding_for_case(root, manifest, run_id, *, now):
    """Source-verified flat integration binding; never a full execution admission."""
    manifest_sha = validate_manifest(manifest, root, now=now)
    value = manifest
    cases = [case for case in value['cases'] if case['id'] == run_id]
    require(len(cases) == 1, 'candidate_case_not_registered')
    return dict(run_id=run_id, purpose=value['purpose'], cap=cases[0]['cap'],
        parent_id=value['parent_run'], source_commit=value['source_commit'],
        candidate_sha=value['candidate_sha256'], ci_run=value['github_run'],
        expiry=value['expires_at'], binding_sha=manifest_sha,
        environment='disposable_ci', execution_admitted=False, hosted_permission=False)


def validate_case_binding(root, manifest, value, *, now):
    require(type(value) is dict, 'candidate_case_binding_shape')
    expected = binding_for_case(root, manifest, value.get('run_id'), now=now)
    require(baseline.typed_equal(value, expected), 'candidate_case_binding_changed')
    return expected


def validate_target(root, manifest, *, environment, connection, ca_path, now):
    """Pure preflight for Main's future executor. Does not attest a live session."""
    validate_manifest(manifest, root, now=now)
    require(type(environment) is dict and type(connection) is dict, 'candidate_target_shape')
    for key, expected in {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': binding.REPOSITORY,
        'GITHUB_REF': 'refs/heads/main', 'GITHUB_SHA': manifest['source_commit'],
        'GITHUB_RUN_ID': manifest['github_run']}.items():
        require(environment.get(key) == expected, 'candidate_ci_binding')
    require(not any(environment.get(k) for k in ('PGSERVICE', 'PGSERVICEFILE'))
            and environment.get('PGHOSTADDR', '127.0.0.1') == '127.0.0.1', 'candidate_target_alias')
    require(set(connection) == {'host', 'hostaddr', 'port', 'dbname', 'user', 'sslmode',
        'sslrootcert', 'connect_timeout'}, 'candidate_connection_shape')
    for key, expected in dict(host='127.0.0.1', hostaddr='127.0.0.1', dbname='postgres',
        user='postgres', sslmode='verify-full', connect_timeout=5).items():
        require(baseline.typed_equal(connection[key], expected), 'candidate_loopback_tls')
    require(type(connection['port']) is int and 1 <= connection['port'] <= 65535,
            'candidate_port')
    ca = pathlib.Path(ca_path)
    require(ca.is_absolute() and ca.is_file() and not ca.is_symlink()
            and pathlib.Path(connection['sslrootcert']).resolve() == ca.resolve(), 'candidate_ca')
    require(moment(manifest['created_at']) <= moment(now) < moment(manifest['expires_at']),
            'candidate_expired_or_future')
    return {'scope': 'DISPOSABLE_CI_TARGET_PREFLIGHT_ONLY', 'hosted_permission': False,
            'live_ssl_attested': False, 'executed': False}
