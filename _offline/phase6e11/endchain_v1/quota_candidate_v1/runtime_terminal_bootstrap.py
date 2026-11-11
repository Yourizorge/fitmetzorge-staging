"""Read-only validation of two early-fault witnesses, never case admission."""
import ast
import hashlib
import json
import pathlib
import re
import uuid

from . import runtime_bootstrap_closeout as producer

PREFIX = '_offline/phase6e11/endchain_v1/'
OWN = PREFIX + 'quota_candidate_v1/runtime_terminal_bootstrap.py'
PRODUCER = PREFIX + 'quota_candidate_v1/runtime_bootstrap_closeout.py'
BOUNDARY = PREFIX + 'migration_failure_boundaries.py'
RUNTIME = PREFIX + 'integral_failure_runtime.py'
STACK = PREFIX + 'case_stack_v1/bootstrap.py'
M45 = 'supabase/migrations/20261018070231_phase6e11_recovery_run_quota.sql'
M45_SHA = '64498fa910966497e92705dcf66b76f40c40f01c006aed98c191ce109dd88635'
PARENT = '11a909f4-7113-424a-aa4b-ce9964720a3e'
EARLY = {'pre_migration': ('before45', 44, 1), 'post_migration': ('after45', 45, 2)}
COUNTS = ('runs', 'windows', 'workspaces', 'identities', 'auth_users',
          'auth_sessions', 'auth_refresh_tokens')
DOCKER_ARGV = ['docker', 'ps', '-a', '--no-trunc', '--format',
    '{"id":"{{.ID}}","image":"{{.Image}}","name":"{{.Names}}"}']


def require(value, code):
    if not value:
        raise ValueError('bootstrap_terminal_' + code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def object_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_json_key')
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=unique,
                       parse_constant=lambda _: require(False, 'nonfinite_json'))
    require(type(value) is dict, 'json_object')
    return value


def literal(raw, name):
    hits = [n.value for n in ast.parse(raw).body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    require(len(hits) == 1, 'source_literal')
    value = ast.literal_eval(hits[0])
    require(type(value) is str, 'source_literal')
    return value


def read_under(root, name, maximum=2000000):
    root = pathlib.Path(root).resolve(strict=True)
    require(isinstance(name, str) and re.fullmatch('[A-Za-z0-9_./-]+', name)
            and all(p not in ('', '.', '..') for p in name.split('/')), 'path')
    path = root / name
    require(not path.is_symlink() and not any(p.is_symlink() for p in path.parents)
            and not any(getattr(p, 'is_junction', lambda: False)() for p in (path, *path.parents))
            and path.resolve(strict=True).is_relative_to(root), 'path_escape')
    require(path.stat().st_size <= maximum, 'bytes')
    raw = path.read_bytes()
    require(len(raw) <= maximum, 'bytes')
    return raw


def validate_bootstrap_termination(gate, binding, case_name, fault, isolation):
    """Return hash-referenced diagnostics; no SQL, Docker, writes or PASS promotion."""
    require(case_name in EARLY, 'case')
    stage, count, observations = EARLY[case_name]
    require(binding.get('parent_id') == PARENT and binding.get('environment') == 'disposable_ci'
            and binding.get('hosted_permission') is False and binding.get('execution_admitted') is False,
            'binding_scope')
    identity = binding['run_id']
    require(str(uuid.UUID(identity)) == identity and uuid.UUID(identity).version == 4
            and identity not in (PARENT, '6f8c8909-9b79-4011-a9d1-db5e23c6b6c1',
                                '1c3bf7e7-bc78-40c5-9ac1-5ba3512ec66d',
                                '4b0bb35f-02b5-4a9d-92d7-c29995691460'), 'run_id')
    expected = dict(source_commit=binding['source_commit'], ci_run=binding['ci_run'],
                    candidate_sha256=binding['candidate_sha'])
    require(re.fullmatch('[a-f0-9]{40}', expected['source_commit'])
            and re.fullmatch('[a-f0-9]{64}', expected['candidate_sha256'])
            and re.fullmatch('[1-9][0-9]{0,18}', expected['ci_run'])
            and int(expected['ci_run']) <= 9223372036854775807, 'source_shape')
    commit = gate.result.get('commit', gate.result.get('head'))
    require(commit == expected['source_commit'] and gate.result.get('head', commit) == commit
            and gate.result.get('run_id') == expected['ci_run']
            and gate.result.get('candidate_sha256') == expected['candidate_sha256'], 'gate_binding')
    refs = {}
    def raw(name):
        require(isinstance(name, str) and pathlib.PurePosixPath(name).name == name, 'receipt_basename')
        data = read_under(gate.out, name)
        refs[name] = dict(path=name, sha256=digest(data), bytes=len(data))
        return data
    def receipt(name):
        return object_json(raw(name))
    def reference(ref, name):
        require(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'}
                and ref['path'] == name, 'reference_shape')
        data = raw(name)
        require(type(ref['bytes']) is int and ref == refs[name], 'reference_hash')
        return object_json(data)
    def bound(value, *, run=True):
        require(all(value.get(k) == v for k, v in expected.items())
                and (not run or value.get('run_id') == identity), 'receipt_binding')

    candidate = receipt('candidate.json')
    require(candidate.get('sha256') == expected['candidate_sha256'], 'candidate')
    sources = candidate['sources']
    require(type(sources) is dict and 1 <= len(sources) <= 4096, 'source_inventory')
    migrations = sorted(p for p in sources if p.startswith('supabase/migrations/') and p.endswith('.sql'))
    require(len(migrations) == 45 and migrations[-1] == M45 and sources[M45] == M45_SHA,
            'migration_sources')
    required = migrations + [OWN, PRODUCER, BOUNDARY, RUNTIME, STACK, PREFIX + 'native_runtime.py']
    source_hashes = {}
    for name in required:
        observed = digest(read_under(gate.sources, name))
        require(sources.get(name) == observed, 'source_changed')
        source_hashes[name] = observed
    require(digest(pathlib.Path(__file__).read_bytes()) == sources[OWN]
            and digest(pathlib.Path(producer.__file__).read_bytes()) == sources[PRODUCER],
            'loaded_source')
    versions = [pathlib.PurePosixPath(p).name.split('_')[0] for p in migrations]
    require(len(set(versions)) == 45, 'migration_identity')
    boundary_commands = ['BEGIN TRANSACTION READ ONLY', literal(read_under(gate.sources, RUNTIME), 'CHECK'),
        literal(read_under(gate.sources, BOUNDARY), 'METADATA'), 'ROLLBACK'] * 2

    observed_fault = receipt('case-fault-boundary.json')
    require(fault.case == case_name and fault.binding == binding and fault.fired == observed_fault,
            'fault_object')
    require(observed_fault.get('case') == case_name and observed_fault.get('run_id') == identity
            and observed_fault.get('source_commit') == expected['source_commit']
            and observed_fault.get('ci_run') == expected['ci_run']
            and observed_fault.get('candidate_sha') == expected['candidate_sha256']
            and observed_fault.get('original_error_code') == 'case_injected_' + case_name
            and type(observed_fault.get('observations_before_fault')) is int
            and observed_fault['observations_before_fault'] == observations
            and observed_fault.get('automatic_retry') is False
            and observed_fault.get('full_chain_admission') is False, 'fault_binding')
    snapshot = receipt('case-stack-boundary-' + stage + '.json')
    bound(snapshot, run=False)
    require(snapshot.get('stage') == stage and type(snapshot.get('history_count')) is int
            and snapshot['history_count'] == count and snapshot.get('full_chain_admission') is False
            and snapshot.get('hosted_admission') is False, 'snapshot')
    names = ['migration-boundary-pre.json'] if count == 44 else [
        'cli-predispatch-canonical-45.json', 'migration-boundary-post.json']
    require([r.get('path') for r in snapshot['evidence_refs']] == names, 'boundary_references')
    for ref, name in zip(snapshot['evidence_refs'], names): reference(ref, name)
    event = observed_fault['event']
    require(event == dict(stage=stage, history_count=count, evidence_refs=snapshot['evidence_refs'],
                          dispatch_confirmed=count == 45), 'fault_event')

    def boundary(name, phase, history_count):
        value = receipt(name)
        require(value.get('phase') == phase and value.get('component_verified') is True
                and value.get('reader_connections_closed') is True
                and value.get('secondary_failures') == [] and value.get('unknown_outcome') is False
                and value.get('safe_closure_no_fixtures') is True
                and value.get('local_diagnostic_commands') == 8
                and value.get('full_chain_admission') is False
                and value.get('hosted_admission') is False, 'boundary_complete')
        source = value['source_binding']
        bound(source, run=False)
        require(value['source_binding_sha256'] == digest(canonical(source)), 'boundary_source_hash')
        require(all(sources.get(p) == h and digest(read_under(gate.sources, p)) == h
                    for p, h in source['sources'].items())
                and all(source['sources'].get(p) == sources[p] for p in migrations),
                'boundary_sources')
        events = value['read_only_dispatches']
        require(len(events) == 8 and all(type(e.get('ordinal')) is int and e['ordinal'] == i+1
                and type(e.get('cost')) is int and e['cost'] == 1
                and e.get('kind') == 'sql' and e.get('confirmed') is True
                and e.get('reply_delivered') is True
                and e.get('sha256') == digest(boundary_commands[i].encode())
                for i, e in enumerate(events)), 'boundary_trace')
        final = value['after_failure']
        require(final == value['before' if phase == 'pre_migration' else 'after_m45']
                and all(type(final.get(k)) is int and final[k] == 0 for k in COUNTS)
                and type(final.get('history_count')) is int and final['history_count'] == history_count
                and final.get('history_sha256') == digest(canonical(versions[:history_count]))
                and re.fullmatch('[a-f0-9]{64}', str(final.get('m44_function'))), 'boundary_state')
        return value
    pre = boundary('migration-boundary-pre.json', 'pre_migration', 44)
    require(pre.get('dispatcher_called') is False and pre.get('dispatcher_command_count_delta') == 0
            and pre['before']['m45_function'] is None and pre['before']['m45_trigger'] is None,
            'pre_dispatch')
    if count == 45:
        post = boundary('migration-boundary-post.json', 'post_migration', 45)
        require(post['before'] == pre['before'] and post.get('migration_rollback_claim') is False
                and post['after_m45']['m44_function'] == pre['before']['m44_function']
                and all(re.fullmatch('[a-f0-9]{64}', str(post['after_m45'].get(k)))
                        for k in ('m45_function', 'm45_trigger', 'quota_constraint'))
                and post['after_m45']['quota_constraint'] != pre['before']['quota_constraint'], 'post_dispatch')
        actual = post['actual_migration_result']
        cli = receipt('cli-predispatch-canonical-45.json')
        require(cli.get('source_commit') == expected['source_commit']
                and cli.get('candidate_sha256') == expected['candidate_sha256'], 'canonical_source')
        require(actual.get('receipt') == 'cli-predispatch-canonical-45.json'
                and actual.get('receipt_sha256') == refs[actual['receipt']]['sha256']
                and actual.get('returncode') == 0 and actual.get('parent_bootstrap_dispatches') == 1
                and cli.get('complete') is True and type(cli.get('cli_exit_code')) is int
                and cli['cli_exit_code'] == 0 and cli.get('profile') == 'canonical_45'
                and cli.get('expected_migration') == M45 and cli.get('expected_migration_sha256') == M45_SHA
                and cli.get('actual_migration_execution') is True
                and cli.get('app_profile_mutated') is False and cli.get('application_run_started') is False
                and cli.get('numeric_coverage', {}).get('all_protocol_visible') is True
                and cli.get('numeric_coverage', {}).get('temp_written') == 0
                and cli.get('observer_commands') == 8,
                'canonical_confirmation')
        for key, hash_key, name, maximum in (
                ('ledger_ref', 'ledger_sha256', 'cli-predispatch-canonical-45.ledger.txt', 262144),
                ('policy_ref', 'policy_file_sha256', 'cli-predispatch-canonical-45.policy.json', 16384)):
            ref = cli[key]
            require(type(ref) is dict and set(ref) == {'path', 'sha256'} and ref['path'] == name,
                    'canonical_raw_reference')
            data = raw(ref['path'])
            require(len(data) <= maximum and ref['sha256'] == refs[name]['sha256']
                    and digest(data) == actual[hash_key], 'canonical_raw_hash')
    else:
        require(not (gate.out / 'cli-predispatch-canonical-45.json').exists()
                and not (gate.out / 'migration-boundary-post.json').exists(), 'unexpected_m45')

    reservation = receipt('case-preauth-closeout-reservation.json')
    accounts = receipt('case-preauth-account-absence.json')
    containers = receipt('case-preauth-container-absence.json')
    hashes = [digest(s.encode()) for s in producer.COMMANDS]
    require(len(hashes) == 4, 'command_count')
    for value in (reservation, accounts, containers):
        bound(value)
        require(value.get('scope') == producer.SCOPE, 'scope')
    for value in (reservation, accounts):
        require(value.get('case_name') == case_name and value.get('reserved_sql_commands') == 4
                and value.get('no_refund') is True and value.get('no_retry') is True
                and all(value.get(k) is False for k in ('auth_started', 'worker_started',
                    'quota_appended', 'full_chain_admission', 'hosted_admission')), 'reservation')
    require(reservation.get('command_sha256') == hashes and reservation.get('docker_inventory_calls') == 1
            and reservation.get('docker_inventory_argv_sha256') == digest(canonical(DOCKER_ARGV))
            and reservation.get('complete') is False and reservation.get('commands') == [], 'prepayment')
    require(accounts.get('complete') is True and accounts.get('rollback_confirmed') is True
            and accounts.get('connection_closed') is True and accounts.get('error_class') is None
            and accounts.get('commands') == [dict(ordinal=i+1, sql_sha256=h, confirmed=True)
                                           for i, h in enumerate(hashes)], 'account_trace')
    require(all(type(row['ordinal']) is int for row in accounts['commands']), 'account_ordinal')
    producer.check_samples(accounts['identity'], accounts['account_counts'], case_name)
    require(type(accounts['account_counts']['history_count']) is int
            and type(accounts['identity']['version']) is int, 'history_type')
    rows = containers.get('inventory_rows')
    require(type(rows) is list and 1 <= len(rows) <= 32
            and len({r['id'] for r in rows}) == len(rows)
            and len({r['name'] for r in rows}) == len(rows), 'inventory_rows')
    parsed = producer.inventory('\n'.join(json.dumps(r) for r in rows), gate.container)
    require(all(containers.get(k) == v for k, v in parsed.items())
            and containers.get('inventory_command') == dict(argv=DOCKER_ARGV, exitcode=0,
                timeout_seconds=5, dispatch_calls=1), 'inventory_evidence')
    require(all(type(containers['inventory_command'][k]) is int
                for k in ('exitcode', 'timeout_seconds', 'dispatch_calls')), 'inventory_numeric')
    require(gate.container == 'supabase_db_fmz-db41-ci', 'pg_name')
    ident = accounts['identity']
    target = digest(canonical(dict(pg_container=parsed['pg_container'],
        pg_system_identifier=ident['pg_system_identifier'], database_oid=ident['database_oid'])))
    require(isolation.get('run_id') == identity and isolation.get('ci_run') == expected['ci_run']
            and isolation.get('source_commit') == expected['source_commit'], 'isolation_binding')
    require(isolation.get('environment') == 'disposable_ci' and isolation.get('reused') is False
            and isolation.get('auth_state') == 'not_started' and isolation.get('auth_container') is None
            and isolation.get('auth_database_bound') is False and isolation.get('auth_target_sha256') is None
            and isolation.get('pg_container') == parsed['pg_container']
            and isolation.get('database_oid') == ident['database_oid']
            and isolation.get('pg_system_identifier') == ident['pg_system_identifier']
            and isolation.get('db_target_sha256') == target, 'isolation')
    absence = isolation['auth_absence']
    require(absence.get('verified') is True, 'absence')
    reference(absence['container_inventory_ref'], 'case-preauth-container-absence.json')
    reference(absence['account_inventory_ref'], 'case-preauth-account-absence.json')
    require(not getattr(gate, 'cli_protocol', []) and not (gate.out / 'case-stack-bootstrap.json').exists()
            and not any((gate.out / ('cli-protocol-' + str(i) + '.json')).exists() for i in range(4)),
            'execution_continued')
    return dict(format='quota-bootstrap-termination-v1', status='BOOTSTRAP_TERMINATION_VERIFIED',
        case_name=case_name, run_id=identity, **expected, history_count=count, boundary_stage=stage,
        isolation_sha256=digest(canonical(isolation)),
        auth_state='not_started', auth_absence_scope='docker_inventory_and_global_database_counts_at_closeout',
        non_docker_process_absence_proven=False, historical_never_started_proven=False,
        evidence_refs=list(refs.values()), source_hashes=source_hashes, closeout_sql_commands=4,
        closeout_docker_calls=1, accounting_scope=producer.SCOPE, case_pass=False,
        full_chain_admission=False, hosted_admission=False, parent_terminal_validation_required=True)
