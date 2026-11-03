"""Pure collector validation of two early-fault witnesses, never admission.

Input is the original payload map returned by the trusted ZIP verifier, and a
source map obtained from the prepared candidate (not from the artifact alone).
No artifact Python is imported or executed. Trusted source literals are parsed
only after raw-byte hash comparison. Cross-case uniqueness remains the caller's
responsibility; this proof establishes point-in-time absence, not lifetime absence.
"""
import ast
import hashlib
import json
import pathlib
import re

PREFIX = '_offline/phase6e11/endchain_v1/'
COLLECTOR = PREFIX + 'admission_matrix_bootstrap.py'
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
        raise ValueError('matrix_bootstrap_' + code)


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


def source_literals(raw, names):
    """Restricted literal/name/tuple parser; never execute trusted or artifact Python."""
    wanted = set(names)
    values = {}
    def value(node):
        if isinstance(node, ast.Constant) and type(node.value) is str:
            return node.value
        if isinstance(node, ast.Name) and node.id in values:
            return values[node.id]
        if isinstance(node, ast.Tuple):
            return tuple(value(item) for item in node.elts)
        raise ValueError('matrix_bootstrap_source_expression')
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in wanted:
                    require(target.id not in values, 'source_literal_duplicate')
                    values[target.id] = value(node.value)
    require(set(values) == wanted, 'source_literal_missing')
    return values


def check_samples(identity, counts, count):
    require(type(identity) is dict and identity.get('database') == 'postgres'
            and identity.get('role') == 'postgres'
            and type(identity.get('version')) is int and identity['version'] == 17
            and identity.get('readonly') == 'on' and identity.get('ssl') is True
            and identity.get('statement_timeout') in ('5s', '5000ms')
            and identity.get('lock_timeout') in ('1s', '1000ms')
            and isinstance(identity.get('pg_system_identifier'), str)
            and re.fullmatch('[1-9][0-9]{0,19}', identity['pg_system_identifier'])
            and type(identity.get('database_oid')) is int and identity['database_oid'] > 0,
            'closeout_identity')
    require(type(counts) is dict
            and set(counts) == {'users', 'sessions', 'refresh_tokens', 'controller_runs', 'history_count'}
            and all(type(v) is int for v in counts.values())
            and all(counts[k] == 0 for k in ('users', 'sessions', 'refresh_tokens', 'controller_runs'))
            and counts['history_count'] == count, 'account_absence')


def inventory(rows):
    require(type(rows) is list and 1 <= len(rows) <= 32
            and len(canonical(rows)) <= 65536, 'inventory_rows')
    ids, names = set(), set()
    for row in rows:
        require(type(row) is dict and set(row) == {'id', 'image', 'name'}
                and all(type(v) is str for v in row.values()), 'inventory_shape')
        require(re.fullmatch('[a-f0-9]{64}', row['id'])
                and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_./:@-]{0,511}', row['image'])
                and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,254}', row['name'])
                and row['id'] not in ids and row['name'] not in names, 'inventory_identity')
        require('gotrue' not in row['image'].lower()
                and row['name'] not in ('fmz-guard-auth-ci', 'fmz-integration-auth-ci'), 'auth_present')
        ids.add(row['id'])
        names.add(row['name'])
    pg = [r for r in rows if r['name'] == 'supabase_db_fmz-db41-ci']
    require(len(pg) == 1, 'pg_inventory')
    return dict(pg_container=pg[0]['id'], gotrue_containers=0, containers_inspected=len(rows),
        inventory_rows=rows, inventory_sha256=digest(canonical(rows)),
        coverage='all_existing_disposable_docker_containers; Auth uses Docker only')


def verify_bootstrap_case(payloads, *, case_name, source_commit, ci_run,
                          candidate_sha256, expected_sources, trusted_root):
    """Verify exactly one early case; return scoped identity, never CASE_PASS.

    Raises ValueError for invalid/incomplete evidence. All receipts stay in memory;
    only hash-verified, explicitly trusted local source files are read from disk.
    """
    require(case_name in EARLY, 'case')
    stage, count, observations = EARLY[case_name]
    require(type(payloads) is dict and 1 <= len(payloads) <= 1100, 'payloads')
    require(len({n.casefold() for n in payloads if isinstance(n, str)}) == len(payloads),
            'payload_alias')
    require(all(isinstance(n, str) and re.fullmatch(r'[A-Za-z0-9_.-]+\.(json|txt|png)', n)
                and type(data) is bytes and len(data) <= 2000000
                for n, data in payloads.items()), 'payload_member')
    require(sum(map(len, payloads.values())) <= 30000000, 'payload_bytes')
    expected = dict(source_commit=source_commit, ci_run=ci_run,
                    candidate_sha256=candidate_sha256)
    require(isinstance(source_commit, str) and re.fullmatch('[a-f0-9]{40}', source_commit)
            and isinstance(candidate_sha256, str) and re.fullmatch('[a-f0-9]{64}', candidate_sha256)
            and isinstance(ci_run, str) and re.fullmatch('[1-9][0-9]{0,18}', ci_run)
            and int(ci_run) <= 9223372036854775807, 'source_shape')
    require(type(expected_sources) is dict and 1 <= len(expected_sources) <= 4096,
            'expected_sources')
    require(len({p.casefold() for p in expected_sources if isinstance(p, str)}) == len(expected_sources),
            'source_alias')
    for name, value in expected_sources.items():
        require(isinstance(name, str) and re.fullmatch('[A-Za-z0-9_./-]+', name)
                and all(part not in ('', '.', '..') for part in name.split('/'))
                and isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value), 'source_entry')
    cache = {}
    def source_raw(name):
        if name not in cache:
            require(name in expected_sources, 'source_missing')
            cache[name] = read_under(trusted_root, name)
            require(digest(cache[name]) == expected_sources[name], 'source_changed')
        return cache[name]
    require(expected_sources.get(COLLECTOR) == digest(pathlib.Path(__file__).read_bytes()),
            'loaded_collector')
    source_raw(COLLECTOR)
    case = object_json(payloads.get('case-execution.json', b'{}'))
    isolation = case.get('isolation')
    require(type(isolation) is dict, 'isolation_missing')
    identity = isolation.get('run_id')
    require(isinstance(identity, str) and re.fullmatch(
        '[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}', identity)
        and identity not in (PARENT, '6f8c8909-9b79-4011-a9d1-db5e23c6b6c1',
                            '1c3bf7e7-bc78-40c5-9ac1-5ba3512ec66d',
                            '4b0bb35f-02b5-4a9d-92d7-c29995691460'), 'run_id')
    require(case.get('case_name') == case_name and case.get('run_id') == identity
            and case.get('parent_id') == PARENT
            and all(case.get(k) == v for k, v in expected.items()), 'case_binding')
    result = object_json(payloads.get('result.json', b'{}'))
    require(result.get('commit') == source_commit and result.get('head', source_commit) == source_commit
            and str(result.get('run_id')) == ci_run and result.get('candidate_sha256') == candidate_sha256
            and result.get('case_name') == case_name
            and result.get('hosted_admitted') is not True
            and result.get('full_chain_admission') is not True, 'result_binding')
    refs = {}
    collector_only_refs = set()
    def raw(name):
        require(isinstance(name, str) and pathlib.PurePosixPath(name).name == name, 'receipt_basename')
        require(name in payloads, 'receipt_missing')
        data = payloads[name]
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
    require(sources == expected_sources, 'source_inventory')
    migrations = sorted(p for p in sources if p.startswith('supabase/migrations/') and p.endswith('.sql'))
    require(len(migrations) == 45 and migrations[-1] == M45 and sources[M45] == M45_SHA,
            'migration_sources')
    required = migrations + [OWN, PRODUCER, BOUNDARY, RUNTIME, STACK, PREFIX + 'native_runtime.py']
    source_hashes = {}
    for name in required:
        observed = digest(source_raw(name))
        require(sources.get(name) == observed, 'source_changed')
        source_hashes[name] = observed
    legacy = set()
    for name in migrations:
        legacy.update(re.findall(
            r'[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}',
            source_raw(name).decode('utf-8').lower()))
    require(identity not in legacy, 'historical_migration_uuid')
    command_values = source_literals(source_raw(PRODUCER),
                                     ('IDENTITY', 'ACCOUNTS', 'COMMANDS', 'SCOPE', 'DOCKER_ARGS'))
    commands = command_values['COMMANDS']
    scope = command_values['SCOPE']
    require(type(commands) is tuple and commands == ('BEGIN TRANSACTION READ ONLY',
            command_values['IDENTITY'], command_values['ACCOUNTS'], 'ROLLBACK')
            and all(type(c) is str for c in commands)
            and command_values['DOCKER_ARGS'] == tuple(DOCKER_ARGV)
            and scope == 'CI_BOOTSTRAP_CLOSEOUT_SEPARATE_FROM_CASE_2349', 'producer_contract')
    versions = [pathlib.PurePosixPath(p).name.split('_')[0] for p in migrations]
    require(len(set(versions)) == 45, 'migration_identity')
    boundary_commands = ['BEGIN TRANSACTION READ ONLY', literal(source_raw(RUNTIME), 'CHECK'),
        literal(source_raw(BOUNDARY), 'METADATA'), 'ROLLBACK'] * 2

    observed_fault = receipt('case-fault-boundary.json')
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
    require(type(event.get('history_count')) is int
            and event.get('dispatch_confirmed') is (count == 45)
            and event == dict(stage=stage, history_count=count, evidence_refs=snapshot['evidence_refs'],
                          dispatch_confirmed=count == 45), 'fault_event')

    def boundary(name, phase, history_count):
        value = receipt(name)
        require(value.get('phase') == phase and value.get('component_verified') is True
                and value.get('reader_connections_closed') is True
                and value.get('secondary_failures') == [] and value.get('unknown_outcome') is False
                and value.get('safe_closure_no_fixtures') is True
                and type(value.get('local_diagnostic_commands')) is int and value['local_diagnostic_commands'] == 8
                and value.get('full_chain_admission') is False
                and value.get('hosted_admission') is False, 'boundary_complete')
        source = value['source_binding']
        bound(source, run=False)
        require(value['source_binding_sha256'] == digest(canonical(source)), 'boundary_source_hash')
        require(all(sources.get(p) == h and digest(source_raw(p)) == h
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
    require(pre.get('dispatcher_called') is False and type(pre.get('dispatcher_command_count_delta')) is int and pre['dispatcher_command_count_delta'] == 0
            and pre['before']['m45_function'] is None and pre['before']['m45_trigger'] is None
            and re.fullmatch('[a-f0-9]{64}', str(pre['before'].get('quota_constraint'))),
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
        require(len(payloads['cli-predispatch-canonical-45.json']) <= 524288, 'canonical_bytes')
        require(actual.get('receipt') == 'cli-predispatch-canonical-45.json'
                and actual.get('receipt_sha256') == refs[actual['receipt']]['sha256']
                and type(actual.get('returncode')) is int and actual['returncode'] == 0
                and type(actual.get('parent_bootstrap_dispatches')) is int and actual['parent_bootstrap_dispatches'] == 1
                and cli.get('complete') is True and type(cli.get('cli_exit_code')) is int
                and cli['cli_exit_code'] == 0 and cli.get('profile') == 'canonical_45'
                and cli.get('expected_migration') == M45 and cli.get('expected_migration_sha256') == M45_SHA
                and cli.get('actual_migration_execution') is True
                and cli.get('app_profile_mutated') is False and cli.get('application_run_started') is False
                and cli.get('numeric_coverage', {}).get('all_protocol_visible') is True
                and type(cli.get('numeric_coverage', {}).get('temp_written')) is int
                and cli['numeric_coverage']['temp_written'] == 0
                and type(cli.get('observer_commands')) is int and cli['observer_commands'] == 8,
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
        name = 'canonical-45-cli-predispatch-cli-isolation-0.json'
        require(cli.get('isolation_receipt') == name, 'canonical_isolation_name')
        data = raw(name)
        collector_only_refs.add(name)
        require(len(data) <= 16384 and digest(data) == cli.get('isolation_receipt_sha256')
                and digest(data) == actual.get('isolation_receipt_sha256'), 'canonical_isolation_hash')
        restored = object_json(data)
        isolation_source = '_offline/phase6e_server_v1/cli_isolation.py'
        setting = literal(source_raw(isolation_source), 'SETTING')
        active = literal(source_raw(isolation_source), 'ACTIVE')
        original = restored.get('original')
        require(original in ('on', 'off'), 'canonical_isolation_original')
        trace = [setting]
        if original == 'on':
            trace += ["alter system set cron.launch_active_jobs='off'", 'select pg_reload_conf()']
        trace += [setting, active]
        if original == 'on':
            trace += ["alter system set cron.launch_active_jobs='on'", 'select pg_reload_conf()']
        trace += [setting]
        require(restored.get('restored') is True and restored.get('primary_error_class') is None
                and restored.get('protocol') == [
                    dict(statement_sha256=digest(sql.encode()), confirmed=True) for sql in trace]
                and all(row.get('confirmed') is True for row in restored['protocol'])
                and type(restored.get('commands')) is int and restored['commands'] == len(trace)
                and cli.get('ci_cron_restored') is True
                and type(cli.get('ci_bootstrap_sql_commands')) is int
                and cli['ci_bootstrap_sql_commands'] == len(trace)
                and type(actual.get('isolation_commands')) is int
                and actual['isolation_commands'] == len(trace), 'canonical_isolation_trace')
    else:
        require('cli-predispatch-canonical-45.json' not in payloads
                and 'migration-boundary-post.json' not in payloads, 'unexpected_m45')

    reservation = receipt('case-preauth-closeout-reservation.json')
    accounts = receipt('case-preauth-account-absence.json')
    containers = receipt('case-preauth-container-absence.json')
    hashes = [digest(s.encode()) for s in commands]
    require(len(hashes) == 4, 'command_count')
    for value in (reservation, accounts, containers):
        bound(value)
        require(value.get('scope') == scope, 'scope')
    for value in (reservation, accounts):
        require(value.get('case_name') == case_name and type(value.get('reserved_sql_commands')) is int and value['reserved_sql_commands'] == 4
                and value.get('no_refund') is True and value.get('no_retry') is True
                and all(value.get(k) is False for k in ('auth_started', 'worker_started',
                    'quota_appended', 'full_chain_admission', 'hosted_admission')), 'reservation')
    require(reservation.get('command_sha256') == hashes and type(reservation.get('docker_inventory_calls')) is int and reservation['docker_inventory_calls'] == 1
            and reservation.get('docker_inventory_argv_sha256') == digest(canonical(DOCKER_ARGV))
            and reservation.get('complete') is False and reservation.get('commands') == [], 'prepayment')
    require(accounts.get('complete') is True and accounts.get('rollback_confirmed') is True
            and accounts.get('connection_closed') is True and accounts.get('error_class') is None
            and accounts.get('commands') == [dict(ordinal=i+1, sql_sha256=h, confirmed=True)
                                           for i, h in enumerate(hashes)], 'account_trace')
    require(all(type(row['ordinal']) is int and row['confirmed'] is True
                for row in accounts['commands']), 'account_ordinal')
    check_samples(accounts['identity'], accounts['account_counts'], count)
    require(type(accounts['account_counts']['history_count']) is int
            and type(accounts['identity']['version']) is int, 'history_type')
    rows = containers.get('inventory_rows')
    parsed = inventory(rows)
    images = source_literals(source_raw(STACK), ('IMAGE', 'DIGEST'))
    require(next(row['image'] for row in rows if row['id'] == parsed['pg_container'])
            in images.values(), 'pg_image')
    require(all(containers.get(k) == v for k, v in parsed.items())
            and containers.get('inventory_command') == dict(argv=DOCKER_ARGV, exitcode=0,
                timeout_seconds=5, dispatch_calls=1), 'inventory_evidence')
    require(type(containers.get('gotrue_containers')) is int
            and type(containers.get('containers_inspected')) is int, 'inventory_count_type')
    require(all(type(containers['inventory_command'][k]) is int
                for k in ('exitcode', 'timeout_seconds', 'dispatch_calls')), 'inventory_numeric')
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
    require('case-stack-bootstrap.json' not in payloads
            and not any(re.fullmatch(r'cli-protocol-[0-9]+\.json', name) for name in payloads),
            'execution_continued')
    proof = reference(case.get('bootstrap_termination_ref'), 'case-bootstrap-termination.json')
    bound(proof)
    require(proof.get('format') == 'quota-bootstrap-termination-v1'
            and proof.get('status') == 'BOOTSTRAP_TERMINATION_VERIFIED'
            and proof.get('case_name') == case_name
            and type(proof.get('history_count')) is int and proof['history_count'] == count
            and proof.get('boundary_stage') == stage
            and proof.get('isolation_sha256') == digest(canonical(isolation))
            and proof.get('source_hashes') == source_hashes, 'terminal_binding')
    require(proof.get('auth_state') == 'not_started'
            and proof.get('auth_absence_scope') == 'docker_inventory_and_global_database_counts_at_closeout'
            and all(proof.get(k) is False for k in ('non_docker_process_absence_proven',
                'historical_never_started_proven', 'case_pass', 'full_chain_admission', 'hosted_admission'))
            and proof.get('parent_terminal_validation_required') is True
            and type(proof.get('closeout_sql_commands')) is int and proof['closeout_sql_commands'] == 4
            and type(proof.get('closeout_docker_calls')) is int and proof['closeout_docker_calls'] == 1
            and proof.get('accounting_scope') == scope, 'terminal_scope')
    needed = set(refs) - {'case-bootstrap-termination.json'} - collector_only_refs
    evidence = proof.get('evidence_refs')
    require(type(evidence) is list and len(evidence) == len(needed)
            and all(type(r) is dict and type(r.get('path')) is str for r in evidence)
            and {r['path'] for r in evidence} == needed, 'terminal_evidence_set')
    for ref in evidence:
        require(set(ref) == {'path', 'sha256', 'bytes'} and type(ref['bytes']) is int
                and ref == refs[ref['path']], 'terminal_evidence_hash')
    return dict(format='matrix-bootstrap-absence-v1', status='BOOTSTRAP_ABSENCE_VERIFIED',
        case_name=case_name, run_id=identity, **expected, history_count=count, boundary_stage=stage,
        pg_container=parsed['pg_container'], pg_system_identifier=ident['pg_system_identifier'],
        database_oid=ident['database_oid'], db_target_sha256=target, auth_container=None,
        isolation_sha256=digest(canonical(isolation)),
        auth_state='not_started', auth_absence_scope='docker_inventory_and_global_database_counts_at_closeout',
        non_docker_process_absence_proven=False, historical_never_started_proven=False,
        evidence_refs=list(refs.values()), source_hashes=source_hashes,
        collector_source_hashes={name: digest(raw) for name, raw in cache.items()},
        cli_hashchain_replayed=False, closeout_sql_commands=4,
        closeout_docker_calls=1, accounting_scope=scope, case_pass=False,
        full_chain_admission=False, hosted_admission=False, parent_terminal_validation_required=True)
