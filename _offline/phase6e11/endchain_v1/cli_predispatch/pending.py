"""One shared apply runner for exact disposable canonical/app migrations."""
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
CANONICAL = 'supabase/migrations/20261018070231_phase6e11_recovery_run_quota.sql'
CANONICAL_SHA = '64498fa910966497e92705dcf66b76f40c40f01c006aed98c191ce109dd88635'
CANONICAL_RECEIPT = 'cli-predispatch-canonical-45.json'
CANONICAL_ISOLATION = 'canonical-45-cli-predispatch-cli-isolation-0.json'
CANONICAL_LEDGER = 'cli-predispatch-canonical-45.ledger.txt'
CANONICAL_POLICY = 'cli-predispatch-canonical-45.policy.json'


def bounded_raw(path, limit):
    if path.is_symlink() or not path.is_file():
        raise ValueError('cli_predispatch_raw_source')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('cli_predispatch_raw_bound')
    return raw


def exclusive_raw(root, name, raw, limit):
    root = pathlib.Path(root).resolve()
    path = root / name
    if pathlib.Path(name).name != name or path.parent != root or len(raw) > limit:
        raise ValueError('cli_predispatch_raw_destination')
    # Keep original serialization, including a truncated final ledger record.
    with path.open('xb') as stream:
        if stream.write(raw) != len(raw):
            raise ValueError('cli_predispatch_raw_short_write')
        stream.flush()
        os.fsync(stream.fileno())
    if bounded_raw(path, limit) != raw:
        raise ValueError('cli_predispatch_raw_copy_mismatch')
    return dict(path=name, sha256=common.sha(raw))


def save_canonical(gate, receipt, policy_file, policy_raw, ledger_file, primary, *, prefix=None):
    tag = 'cli-predispatch-prefix-' + str(prefix) if prefix is not None else 'cli-predispatch-canonical-45'
    policy_limit = 262144 if prefix is not None else 16384
    ledger_limit = 2000000 if prefix is not None else 262144
    errors = []
    for artifact in ('policy', 'ledger'):
        try:
            if artifact == 'policy':
                receipt['policy_ref'] = exclusive_raw(gate.out, tag + '.policy.json', policy_raw, policy_limit)
                receipt['policy_file_unchanged'] = bounded_raw(policy_file, policy_limit) == policy_raw
                if not receipt['policy_file_unchanged']:
                    raise ValueError('cli_predispatch_raw_policy_changed')
            else:
                raw = bounded_raw(ledger_file, ledger_limit)
                receipt['ledger_ref'] = exclusive_raw(gate.out, tag + '.ledger.txt', raw, ledger_limit)
        except Exception as error:
            errors.append(dict(artifact=artifact, error_class=type(error).__name__))
    if getattr(gate, 'cli_protocol', []):
        errors.append(dict(artifact='app_profile', error_class='ValueError'))
    if errors:
        receipt.update(complete=False, reserved_sql_consumed_on_failure=receipt.get('policy', {}).get('cap', 64), durability_errors=errors)
    try:
        raw = json.dumps(receipt, sort_keys=True, indent=2).encode('utf-8')
        exclusive_raw(gate.out, tag + '.json', raw, 2000000 if prefix is not None else 524288)
    except Exception as error:
        errors.append(dict(artifact='receipt', error_class=type(error).__name__))
    if errors:
        # A storage failure must not replace the original execution failure.
        if primary is not None:
            primary.add_note('cli_predispatch_canonical_durability_secondary:' +
                             ','.join(row['artifact'] for row in errors))
        else:
            raise ValueError('cli_predispatch_canonical_evidence_durability') from None


def finish_canonical(runtime, gate, receipt, policy_file, policy_raw, ledger_file, primary, *, prefix=None):
    # A teardown error must not skip the original dispatch ledger or replace
    # an earlier execution error. Keep both failures visible, never retry.
    secondary = None
    try:
        runtime.clear()
    except Exception as error:
        secondary = error
        receipt.update(complete=False, runtime_clear_error_class=type(error).__name__)
        if primary is not None:
            primary.add_note('cli_predispatch_runtime_clear:' + type(error).__name__)
    save_canonical(gate, receipt, policy_file, policy_raw, ledger_file,
        primary if primary is not None else secondary, prefix=prefix)
    if primary is None and secondary is not None:
        raise secondary


def plan_pending(gate, args, expected_file):
    return plan_apply(gate, args, expected_file, canonical_apply=False)


def plan_canonical(gate, args, expected_file):
    return plan_apply(gate, args, expected_file, canonical_apply=True)


def plan_apply(gate, args, expected_file, *, canonical_apply):
    import ci_profile
    from cli_meter import source_commit
    index = len(getattr(gate, 'cli_protocol', []))
    phase = gate.result.get('phase')
    if getattr(gate, 'cli_profile', None) != 'local_app':
        raise ValueError('cli_predispatch_pending_slot')
    if canonical_apply:
        if phase != 'migration_45' or type(gate.result.get('migrations_applied')) is not int or \
                gate.result['migrations_applied'] != 44 or index != 0 or \
                tuple(args) != ('migration', 'up', '--local'):
            raise ValueError('cli_predispatch_canonical_clean44')
        if hasattr(gate, '_cli_predispatch_canonical_attempted') or any((gate.out / name).exists()
                for name in (CANONICAL_RECEIPT, 'cli-predispatch-canonical-45-preregister.json',
                             CANONICAL_ISOLATION, CANONICAL_LEDGER, CANONICAL_POLICY)):
            raise ValueError('cli_predispatch_canonical_reuse')
        logical = tuple(args)
        index = None
        target = gate.sources / CANONICAL
    else:
        if index not in (0, 2) or phase != ('local_app_schema' if index == 0 else 'local_app_outbox'):
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
    relative = canonical if canonical_apply else canonical + [APP + name for name in FILES[:index // 2 + 1]]
    if canonical_apply and (canonical[-1] != CANONICAL or manifest['sources'].get(CANONICAL) != CANONICAL_SHA):
        raise ValueError('cli_predispatch_canonical_immutable')
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
    return dict(index=index, phase=phase, canonical_apply=canonical_apply,
        requested_arguments=list(args), logical_arguments=list(logical),
        source_commit=commit, candidate_sha256=candidate, files=files, migration_sources=hashes,
        target=target, expected_history_versions=history,
        target_sha256=hashes[target.relative_to(gate.sources).as_posix()])


def prove_execution(evidence, policy):
    header, terminal = evidence['header'], evidence['terminal']
    prefix = policy.get('slot') == 'ci_prefix'
    if type(policy.get('cap')) is not int or policy.get('slot') not in ('quota', 'ci_prefix'):
        raise ValueError('cli_predispatch_pending_terminal')
    if evidence.get('terminal_recorded') is not True or terminal['complete'] is not True or \
            terminal['unknown_consumed'] or not 0 < terminal['sql_dispatches'] <= policy['cap'] or \
            header['slot'] != policy['slot'] or header['dry_run'] is not False or header['cap'] != policy['cap'] or \
            (not prefix and policy['cap'] != 64) or \
            header['policy_sha256'] != common.sha(json.dumps(policy, separators=(',', ':')).encode()):
        raise ValueError('cli_predispatch_pending_terminal')
    migration = policy['migrations'][0]
    events = evidence['events']
    dispatches = [e for e in events if e['event'] == 'dispatch']
    # Only the migration body after the unique history snapshot can match SQL.
    snapshot_ids = [e.get('command_id') for e in events if e['event'] == 'history_snapshot']
    body = [e['ast_sha256'] for e in dispatches if e['category'] in ('migration', 'transaction')
            and (not prefix or len(snapshot_ids) == 1 and e['id'] > snapshot_ids[0])]
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
    return run_apply(gate, args, plan_pending(gate, args, expected_file))


def run_canonical(gate, args, expected_file):
    plan = plan_canonical(gate, args, expected_file)
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('GITHUB_REF') != 'refs/heads/main' or \
            os.environ.get('GITHUB_RUN_ATTEMPT') != '1' or os.environ.get('GITHUB_SHA') != plan['source_commit']:
        raise ValueError('cli_predispatch_canonical_source_scope')
    # Consumed on any subsequent setup/transport failure; never retry into a pass.
    gate._cli_predispatch_canonical_attempted = True
    return run_apply(gate, args, plan)


def run_apply(gate, args, plan):
    if os.environ.get('GITHUB_REPOSITORY') != 'Yourizorge/fitmetzorge-staging' or \
            gate.container != 'supabase_db_fmz-db41-ci':
        raise ValueError('cli_predispatch_disposable_only')
    from cli_stat_reader import snapshot, compare
    from native_runtime import NativeRuntime
    import ci_profile
    index = plan['index']
    canonical_apply = plan['canonical_apply']
    prefix = plan.get('prefix_index')
    tag = 'prefix-' + str(prefix) if prefix is not None else 'canonical-45' if canonical_apply else 'pending-' + str(index)
    isolation_name = tag + '-cli-predispatch-cli-isolation-0.json'
    receipt_name = 'cli-predispatch-' + tag + '.json'
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
    if prefix is not None:
        input_policy.update(slot='ci_prefix', prefix_index=prefix, local_bootstrap_only=True,
            run_id=plan['run_id'], ci_run=plan['ci_run'])
    input_file = work / 'policy-input.json'
    input_file.write_text(json.dumps(input_policy))
    code, output = common.bounded([bun, str(HERE / 'policy.cjs'), str(input_file)],
                                 cwd=work, env=os.environ.copy(), seconds=5,
                                 **({'limit':262144} if prefix is not None else {}))
    if code:
        raise ValueError('cli_predispatch_pending_policy')
    policy = json.loads(output)
    if len(policy['migrations']) != 1 or policy['migrations'][0]['sha256'] != plan['target_sha256']:
        raise ValueError('cli_predispatch_pending_policy_binding')
    policy_file = work / 'policy.json'
    policy_file.write_text(json.dumps(policy))
    policy_raw = bounded_raw(policy_file, 262144 if prefix is not None else 16384) if canonical_apply else None
    ledger_file = work / 'ledger.jsonl'
    receipt = dict(scope='DISPOSABLE_CI_ONLY', hosted_admission=False, complete=False,
        source_commit=plan['source_commit'], candidate_sha256=plan['candidate_sha256'], build=build,
        phase=plan['phase'], app_index=index, migration_sources=plan['migration_sources'], policy=policy,
        actual_migration_execution=False, query_ms=5000, cli_seconds=45, output_max_bytes=8192)
    if canonical_apply:
        receipt.update(profile='canonical_prefix' if prefix is not None else 'canonical_45', invocation_id=policy['invocation_id'],
            expected_migration=plan['target'].relative_to(gate.sources).as_posix(), expected_migration_sha256=plan['target_sha256'],
            requested_arguments=list(args), execution_mode='source_instrumented_db_url',
            executed_argument_shape=['db', 'push', '--db-url', '<private-loopback-verify-full>',
                '--skip-vault', '--yes', '--include-all', '--output-format', 'json'],
            app_profile_mutated=False, application_run_started=False,
            isolation_receipt=isolation_name)
        if prefix is not None:
            receipt.update(prefix_index=prefix, local_bootstrap_only=True, hosted_budget_changed=False,
                run_id=plan['run_id'], ci_run=plan['ci_run'])
    gate.save('cli-predispatch-' + tag + '-preregister.json', receipt)
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
        def command(self, label, *a, **kw): return gate.command(tag + '-' + label, *a, **kw)
        def save(self, name, value): return gate.save(tag + '-' + name, value)
    def measure():
        receipt['after_measurement_complete'] = False
        try:
            before, first = snapshot(runtime)
        except Exception as error:
            receipt['failure_phase'] = 'before'
            receipt['measurement_failures'] = [dict(phase='before', error_class=type(error).__name__)]
            raise
        receipt['observer_before_commands'] = len(first)
        receipt['observer_trace'] = first
        if prefix is not None:
            receipt['numeric_before'] = before
        execution_error = None
        try:
            code, output = common.bounded([bun, str(upstream / 'apps/cli/src/main.ts'), 'db', 'push',
                '--db-url', url, '--skip-vault', '--yes', '--include-all', '--output-format', 'json'], cwd=work, env=env)
        except Exception as error:
            execution_error = error
            receipt['failure_phase'] = 'execution'
            raise
        finally:
            try:
                after, last = snapshot(runtime)
                receipt['observer_trace'] = first + last
                receipt['observer_commands'] = len(first) + len(last)
                receipt['after_measurement_complete'] = True
                if prefix is not None:
                    receipt['numeric_after'] = after
            except Exception as error:
                receipt['measurement_failures'] = [dict(phase='after', error_class=type(error).__name__)]
                if execution_error is None:
                    receipt['failure_phase'] = 'after'
                    raise
                execution_error.add_note('cli_predispatch_after_measurement:' + type(error).__name__)
        if password.encode() in output:
            raise ValueError('cli_predispatch_private_output')
        receipt['tracking'] = common.tracking_evidence(before, after)
        common.check_invocation(receipt, code, output, ledger_file)
        evidence = common.replay(ledger_file, **({'prefix_policy':policy} if prefix is not None else {}))
        receipt.update(evidence)
        rows = prove_execution(evidence, policy)
        receipt['actual_migration_execution'] = True
        numeric = compare(before, after, len(rows), between=3)
        receipt['numeric_coverage'] = numeric
        if code or receipt['observer_commands'] != 8 or receipt['tracking']['valid'] is not True or \
                numeric['all_protocol_visible'] is not True or numeric['temp_written'] != 0:
            raise ValueError('cli_predispatch_pending_numeric')
        receipt['complete'] = True
        return receipt
    primary = None
    try:
        common.isolated(View(), receipt, measure)
        if canonical_apply:
            raw = (gate.out / isolation_name).read_bytes()
            isolation = json.loads(raw)
            if isolation['restored'] is not True or isolation['commands'] != receipt['ci_bootstrap_sql_commands'] or \
                    isolation['commands'] not in (4, 8) or len(isolation['protocol']) != isolation['commands'] or \
                    not all(row['confirmed'] is True for row in isolation['protocol']):
                raise ValueError('cli_predispatch_canonical_isolation')
            receipt['isolation_receipt_sha256'] = common.sha(raw)
        else:
            ci_profile.cli_receipt(app_receipt(plan, receipt), index)
    except Exception as error:
        primary = error
        receipt.update(complete=False, failure_class=type(error).__name__, reserved_sql_consumed_on_failure=policy['cap'])
        try: receipt['failure_ledger'] = common.replay(ledger_file, allow_incomplete=True,
            **({'prefix_policy':policy} if prefix is not None else {}))
        except (OSError, ValueError, KeyError, TypeError): receipt['failure_ledger_unverifiable'] = True
        raise
    finally:
        env.pop('PGPASSWORD', None)
        password = None
        if canonical_apply:
            finish_canonical(runtime, gate, receipt, policy_file, policy_raw, ledger_file, primary, prefix=prefix)
        else:
            runtime.clear()
            if not hasattr(gate, 'cli_protocol'): gate.cli_protocol = []
            if len(gate.cli_protocol) != index:
                raise ValueError('cli_predispatch_concurrent_profile')
            compatible = app_receipt(plan, receipt)
            gate.cli_protocol.append(compatible)
            gate.save(getattr(gate, 'cli_namespace', '') + 'cli-protocol-' + str(index) + '.json', compatible)
            gate.save(receipt_name, receipt)
    if canonical_apply:
        return dict(instrumented_receipt=receipt_name, sha256=common.sha((gate.out / receipt_name).read_bytes()))
    return subprocess.CompletedProcess(list(args), 0, stdout='', stderr='')
