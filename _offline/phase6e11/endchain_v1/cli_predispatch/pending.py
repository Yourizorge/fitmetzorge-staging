"""Instrument the parent's existing private app apply exactly once, not M48."""
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import uuid
from urllib.parse import urlencode

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fmz_predispatch_pending_common', HERE / 'ci.py')
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
APP = '_offline/phase6e_server_v1/supabase/migrations/'
FILES = ('20261014105919_phase6e_synthetic_server_candidate.sql',
         '20261014160019_phase6e_local_outbox.sql')


def plan_pending(gate, args, expected_file):
    import ci_profile
    from cli_meter import source_commit
    index = len(getattr(gate, 'cli_protocol', []))
    phase = gate.result.get('phase')
    if getattr(gate, 'cli_profile', None) != 'local_app' or index not in (0, 2) or \
            phase != ('local_app_schema' if index == 0 else 'local_app_outbox'):
        raise ValueError('cli_predispatch_pending_slot')
    logical = ci_profile.cli_arguments(tuple(args), phase, index)
    target = gate.sources / APP / FILES[index // 2]
    if pathlib.Path(expected_file).resolve() != target.resolve():
        raise ValueError('cli_predispatch_pending_target')
    commit = source_commit(gate.result)
    candidate = gate.result.get('candidate_sha256')
    if not isinstance(candidate, str) or not re.fullmatch('[a-f0-9]{64}', candidate):
        raise ValueError('cli_predispatch_candidate_binding')
    manifest = json.loads((gate.out / 'candidate.json').read_bytes())
    if manifest['sha256'] != candidate:
        raise ValueError('cli_predispatch_pending_source')
    canonical = ci_profile.canonical([p.relative_to(gate.sources).as_posix()
        for p in (gate.sources / 'supabase/migrations').glob('*.sql')])
    relative = canonical + [APP + name for name in FILES[:index // 2 + 1]]
    files = sorted((gate.work / 'supabase/migrations').glob('*.sql'))
    if {p.name for p in files} != {pathlib.PurePosixPath(p).name for p in relative}:
        raise ValueError('cli_predispatch_pending_inventory')
    hashes = {}
    for name in relative:
        source = gate.sources / name
        digest = common.sha(source.read_bytes())
        if manifest['sources'].get(name) != digest or \
                common.sha((gate.work / 'supabase/migrations' / source.name).read_bytes()) != digest:
            raise ValueError('cli_predispatch_pending_bytes')
        hashes[name] = digest
    history = sorted(pathlib.PurePosixPath(p).name.split('_')[0] for p in relative[:-1])
    return dict(index=index, phase=phase, requested_arguments=list(args), logical_arguments=list(logical),
        source_commit=commit, candidate_sha256=candidate, files=files, migration_sources=hashes,
        target=target, expected_history_versions=history, target_sha256=hashes[APP + target.name])


def prove_execution(evidence, policy):
    header, terminal = evidence['header'], evidence['terminal']
    if evidence.get('terminal_recorded') is not True or terminal['complete'] is not True or \
            terminal['unknown_consumed'] or not 0 < terminal['sql_dispatches'] <= 64 or \
            header['slot'] != 'quota' or header['dry_run'] is not False or header['cap'] != 64 or \
            header['policy_sha256'] != common.sha(json.dumps(policy, separators=(',', ':')).encode()):
        raise ValueError('cli_predispatch_pending_terminal')
    migration = policy['migrations'][0]
    events = evidence['events']
    dispatches = [e for e in events if e['event'] == 'dispatch']
    body = [e['ast_sha256'] for e in dispatches if e['category'] in ('migration', 'transaction')]
    inserts = [e for e in dispatches if e['category'] == 'migration_history']
    binds = [e for e in events if e['event'] == 'history_bind']
    snapshots = [e for e in events if e['event'] == 'history_snapshot']
    if body != migration['ast_hashes'] or len(inserts) != 1 or len(binds) != 1 or len(snapshots) != 1 or \
            binds[0]['migration_sha256'] != migration['sha256'] or binds[0]['version'] != migration['version'] or \
            binds[0]['statement_count'] != len(body) or snapshots[0]['matches_policy'] is not True or \
            snapshots[0]['count'] != len(policy['expected_history_versions']) or \
            snapshots[0]['versions_sha256'] != common.sha(json.dumps(policy['expected_history_versions'], separators=(',', ':')).encode()) or \
            any(e['category'] == 'closure' for e in dispatches):
        raise ValueError('cli_predispatch_pending_execution')
    return dispatches


def app_receipt(plan, receipt):
    evidence = receipt.get('failure_ledger', receipt)
    commands = [dict(sha256=e['ast_sha256'], hash_kind='pg17_normalized_ast', kind=e['kind'],
                     protocol_commands=1, predispatch_id=e['id'])
                for e in evidence.get('events', []) if e['event'] == 'dispatch']
    observers = receipt.get('observer_trace', [])
    return dict(profile='local_app', slot='app_' + str(plan['index']), dry_run=False,
        arguments=plan['logical_arguments'], requested_arguments=plan['requested_arguments'],
        arguments_semantics='logical app profile command; executed transport is separately identified',
        execution_mode='source_instrumented_db_url',
        executed_argument_shape=['db', 'push', '--db-url', '<private-loopback-verify-full>',
                                 '--skip-vault', '--yes', '--include-all', '--output-format', 'json'],
        source_commit=plan['source_commit'], candidate_sha256=plan['candidate_sha256'],
        upstream_commit=common.UPSTREAM, protocol_commands=len(commands), commands=commands,
        observer_commands=observers, total_commands=len(commands) + len(observers),
        numeric_protocol_coverage=receipt.get('numeric_coverage', {}).get('all_protocol_visible') is True,
        complete=receipt.get('complete') is True, exitcode=receipt.get('cli_exit_code', -1),
        environment='disposable_ci', hosted_admitted=False, hosted_calls=0, sql_text_exported=False,
        actual_migration_execution=receipt.get('actual_migration_execution', False),
        instrumented_receipt='cli-predispatch-pending-' + str(plan['index']) + '.json')


def run_pending(gate, args, expected_file):
    if os.environ.get('GITHUB_REPOSITORY') != 'Yourizorge/fitmetzorge-staging' or \
            gate.container != 'supabase_db_fmz-db41-ci':
        raise ValueError('cli_predispatch_disposable_only')
    from cli_stat_reader import snapshot, compare
    from native_runtime import NativeRuntime
    import ci_profile
    plan = plan_pending(gate, args, expected_file)
    index = plan['index']
    upstream = pathlib.Path(os.environ['FMZ_CLI_PREDISPATCH_UPSTREAM']).resolve()
    build = common.source_binding(upstream)
    bun = shutil.which(os.environ.get('FMZ_BUN', 'bun'))
    if not bun:
        raise ValueError('cli_predispatch_bun_missing')
    def private(argv):
        code, output = common.bounded(argv, cwd=gate.work, env=os.environ.copy(), seconds=5)
        if code:
            raise ValueError('cli_predispatch_pending_bootstrap')
        return output.decode().strip()
    if private([bun, '--version']) != '1.4.1':
        raise ValueError('cli_predispatch_bun_pin')
    endpoints = [p for p in private(['docker', 'port', gate.container, '5432/tcp']).splitlines()
                 if re.fullmatch(r'(127\.0\.0\.1|0\.0\.0\.0):\d+', p)]
    if len(endpoints) != 1:
        raise ValueError('cli_predispatch_loopback')
    port = int(endpoints[0].split(':')[1])
    ca = gate.work / 'fmz-ci-ca.crt'
    work = gate.work / ('cli-predispatch-pending-' + uuid.uuid4().hex)
    (work / 'supabase/migrations').mkdir(parents=True)
    (work / 'private-home').mkdir()
    for file in plan['files']:
        shutil.copyfile(file, work / 'supabase/migrations' / file.name)
    config_port = 65534 if port != 65534 else 65532
    (work / 'supabase/config.toml').write_text('project_id = "fmz-cli-predispatch"\n[db]\n'
        'major_version = 17\nport = ' + str(config_port) + '\nshadow_port = 65533\n'
        '[db.migrations]\nenabled = true\n[db.seed]\nenabled = false\n')
    input_policy = dict(version=1, environment='disposable_ci', upstream_commit=common.UPSTREAM,
        source_commit=plan['source_commit'], candidate_sha256=plan['candidate_sha256'],
        invocation_id=str(uuid.uuid4()), slot='quota', cap=64, closure_reserve=1, dry_run=False,
        host='127.0.0.1', port=port, database='postgres', user='postgres', ca_sha256=common.sha(ca.read_bytes()),
        expected_history_versions=plan['expected_history_versions'],
        migration_paths=[str(work / 'supabase/migrations' / plan['target'].name)])
    input_file = work / 'policy-input.json'
    input_file.write_text(json.dumps(input_policy))
    code, output = common.bounded([bun, str(HERE / 'policy.cjs'), str(input_file)],
                                 cwd=work, env=os.environ.copy(), seconds=5)
    if code:
        raise ValueError('cli_predispatch_pending_policy')
    policy = json.loads(output)
    if len(policy['migrations']) != 1 or policy['migrations'][0]['sha256'] != plan['target_sha256']:
        raise ValueError('cli_predispatch_pending_policy_binding')
    policy_file = work / 'policy.json'
    policy_file.write_text(json.dumps(policy))
    ledger_file = work / 'ledger.jsonl'
    receipt = dict(scope='DISPOSABLE_CI_ONLY', hosted_admission=False, complete=False,
        source_commit=plan['source_commit'], candidate_sha256=plan['candidate_sha256'], build=build,
        phase=plan['phase'], app_index=index, migration_sources=plan['migration_sources'], policy=policy,
        actual_migration_execution=False, query_ms=5000, cli_seconds=45, output_max_bytes=8192)
    gate.save('cli-predispatch-pending-' + str(index) + '-preregister.json', receipt)
    password = private(['docker', 'exec', gate.container, 'sh', '-c', 'printf %s "$POSTGRES_PASSWORD"'])
    if not password or password.startswith('sbp_'):
        raise ValueError('cli_predispatch_private_password')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('PG', 'SUPABASE_', 'GH', 'NODE_', 'BUN_'))}
    env.update(PGPASSWORD=password, DO_NOT_TRACK='1', SUPABASE_NO_UPDATE_NOTIFIER='1',
        SUPABASE_TELEMETRY_DISABLED='1', HOME=str(work / 'private-home'), USERPROFILE=str(work / 'private-home'),
        XDG_CONFIG_HOME=str(work / 'private-home'), FMZ_CLI_PREDISPATCH_POLICY=str(policy_file),
        FMZ_CLI_PREDISPATCH_LEDGER=str(ledger_file))
    url = 'postgresql://postgres@127.0.0.1:' + str(port) + '/postgres?' + urlencode(dict(
        sslmode='verify-full', sslrootcert=str(ca), connect_timeout='5',
        options='-c statement_timeout=5000 -c lock_timeout=1000'))
    runtime = NativeRuntime.disposable(gate)
    class View:
        container = gate.container
        def rows(self, sql): return gate.rows(sql)
        def command(self, label, *a, **kw): return gate.command('pending-' + str(index) + '-' + label, *a, **kw)
        def save(self, name, value): return gate.save('pending-' + str(index) + '-' + name, value)
    def measure():
        before, first = snapshot(runtime)
        try:
            code, output = common.bounded([bun, str(upstream / 'apps/cli/src/main.ts'), 'db', 'push',
                '--db-url', url, '--skip-vault', '--yes', '--include-all', '--output-format', 'json'], cwd=work, env=env)
        finally:
            after, last = snapshot(runtime)
            receipt['observer_trace'] = first + last
            receipt['observer_commands'] = len(first) + len(last)
        if password.encode() in output:
            raise ValueError('cli_predispatch_private_output')
        common.check_invocation(receipt, code, output, ledger_file)
        evidence = common.replay(ledger_file)
        receipt.update(evidence)
        rows = prove_execution(evidence, policy)
        receipt['actual_migration_execution'] = True
        numeric = compare(before, after, len(rows), between=3)
        receipt['numeric_coverage'] = numeric
        if code or receipt['observer_commands'] != 8 or before['track'] != 'all' or after['track'] != 'all' or \
                numeric['all_protocol_visible'] is not True or numeric['temp_written'] != 0:
            raise ValueError('cli_predispatch_pending_numeric')
        receipt['complete'] = True
        return receipt
    try:
        common.isolated(View(), receipt, measure)
        ci_profile.cli_receipt(app_receipt(plan, receipt), index)
        return subprocess.CompletedProcess(list(args), 0, stdout='', stderr='')
    except Exception as error:
        receipt.update(complete=False, failure_class=type(error).__name__, reserved_sql_consumed_on_failure=64)
        try: receipt['failure_ledger'] = common.replay(ledger_file, allow_incomplete=True)
        except (OSError, ValueError, KeyError, TypeError): receipt['failure_ledger_unverifiable'] = True
        raise
    finally:
        env.pop('PGPASSWORD', None)
        password = None
        runtime.clear()
        if not hasattr(gate, 'cli_protocol'): gate.cli_protocol = []
        if len(gate.cli_protocol) != index:
            raise ValueError('cli_predispatch_concurrent_profile')
        compatible = app_receipt(plan, receipt)
        gate.cli_protocol.append(compatible)
        gate.save(getattr(gate, 'cli_namespace', '') + 'cli-protocol-' + str(index) + '.json', compatible)
        gate.save('cli-predispatch-pending-' + str(index) + '.json', receipt)
