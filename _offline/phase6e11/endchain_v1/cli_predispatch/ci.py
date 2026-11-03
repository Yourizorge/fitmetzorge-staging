"""Real source-instrumented CLI empty dry-run on the parent's disposable PG17.

Import via a unique spec name; run(gate) never provisions a stack or touches Auth.
FMZ_CLI_PREDISPATCH_UPSTREAM must name the separately prepared upstream checkout.
All output is hashed in memory. No raw CLI/SQL/credential output is saved.
"""
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import threading
import uuid
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
UPSTREAM = '21db855916f2c2b12f61cde923a27094b8528b23'


def run_pending(gate, args, expected_file):
    """Replace one existing local app apply; never append a migration or retry."""
    spec = importlib.util.spec_from_file_location('fmz_cli_predispatch_pending', HERE / 'pending.py')
    pending = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pending)
    return pending.run_pending(gate, args, expected_file)


def run_canonical(gate, args, expected_file):
    """One disposable canonical M45 apply; never consumes an app CLI index."""
    spec = importlib.util.spec_from_file_location('fmz_cli_predispatch_canonical', HERE / 'pending.py')
    pending = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pending)
    return pending.run_canonical(gate, args, expected_file)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def tracking_evidence(before, after):
    # cli_stat_reader.SQL explicitly selects toplevel. Both modes retain those
    # statements; nested server work is not claimed by this protocol comparison.
    modes = [s.get('track') if s.get('track') in ('none', 'top', 'all') else 'UNKNOWN'
             for s in (before, after)]
    utility = [s.get('track_utility') if s.get('track_utility') in ('on', 'off') else 'UNKNOWN'
               for s in (before, after)]
    return {'before': modes[0], 'after': modes[1], 'utility_before': utility[0],
            'utility_after': utility[1], 'scope': 'toplevel_protocol_commands_only',
            'nested_server_work_proven': False,
            'valid': modes[0] in ('top', 'all') and modes[0] == modes[1]
                     and utility == ['on', 'on']}


def invocation_diagnostic(code, output, ledger_file):
    """Export only fixed classifications, never an upstream message or argv."""
    known = {
        'history_policy': 'hook_policy_validation',
        'migration_policy': 'hook_policy_validation',
        'policy': 'hook_policy_validation',
        'policy_size': 'hook_policy_validation',
        'environment': 'hook_environment_validation',
        'pg17': 'hook_parser_validation',
        'connection_boundary': 'hook_connection_boundary',
    }
    text = output.decode('utf-8', errors='replace')
    stage = 'cli_exit_unclassified' if code else 'cli_returned'
    reason = None
    for name, phase in known.items():
        if re.search(r'(?m)^(?:Error|error): cli_predispatch_' + name + r'\s*$', text):
            stage, reason = phase, 'cli_predispatch_' + name
            break
    if reason is None:
        # Only stable argument-error headings are classified; values stay private.
        if re.search(r'(?m)^(?:Error|error): (?:Unknown|Unrecognized) (?:argument|option|flag)(?::| )', text):
            stage, reason = 'cli_argument_parse', 'unrecognized_argument'
    return dict(stage=stage, reason=reason, cli_exit_code=code,
        ledger_present=pathlib.Path(ledger_file).is_file(), output_bytes=len(output),
        output_sha256=sha(output), raw_output_exported=False,
        classification_is_admission_evidence=False)


def check_invocation(receipt, code, output, ledger_file):
    receipt.update(cli_exit_code=code, output_sha256=sha(output),
        cli_diagnostic=invocation_diagnostic(code, output, ledger_file))
    if code:
        raise ValueError('cli_predispatch_cli_exit:' + receipt['cli_diagnostic']['stage'])
    if not receipt['cli_diagnostic']['ledger_present']:
        raise ValueError('cli_predispatch_ledger_missing_after_success')


def bounded(args, *, cwd, env, limit=8192, seconds=45):
    """One child, bounded output while running, no retry; always reap on failure."""
    process = subprocess.Popen(args, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = bytearray()
    exceeded = threading.Event()
    def drain():
        while True:
            chunk = process.stdout.read(1024)
            if not chunk:
                return
            if len(output) + len(chunk) > limit:
                exceeded.set()
                process.kill()
                return
            output.extend(chunk)
    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    try:
        code = process.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise ValueError('cli_predispatch_timeout') from None
    finally:
        reader.join(timeout=5)
        process.stdout.close()
    if exceeded.is_set() or reader.is_alive():
        raise ValueError('cli_predispatch_output_limit')
    return code, bytes(output)


def replay(file, *, allow_incomplete=False):
    raw = pathlib.Path(file).read_bytes()
    if len(raw) > 262144 or not raw.endswith(b'\n'):
        raise ValueError('cli_predispatch_journal_bound')
    previous = '0' * 64
    dispatches = []
    outcomes = {}
    events = []
    frames = Counter()
    returned = Counter()
    connection_attempts = 0
    for number, line in enumerate(raw.splitlines(), 1):
        row = json.loads(line)
        if row.get('sequence') != number or row.get('previous_sha256') != previous:
            raise ValueError('cli_predispatch_journal_chain')
        previous = sha(line)
        events.append(row)
        if row['event'] == 'preregister' and number != 1:
            raise ValueError('cli_predispatch_duplicate_header')
        if any(event['event'] == 'terminal' for event in events[:-1]):
            raise ValueError('cli_predispatch_after_terminal')
        if row['event'] == 'dispatch':
            if row['id'] != len(dispatches) + 1 or row['outcome'] != 'unknown_consumed':
                raise ValueError('cli_predispatch_dispatch_identity')
            dispatches.append(row)
        if row['event'] == 'outcome':
            if row['id'] in outcomes or not 1 <= row['id'] <= len(dispatches) or row['outcome'] != 'command_complete':
                raise ValueError('cli_predispatch_confirmation')
            outcomes[row['id']] = row['outcome']
        if row['event'] == 'frontend_frame':
            frames[row['type']] += 1
            if any(not isinstance(i, int) or not 1 <= i <= len(dispatches) for i in row['sql_ids']):
                raise ValueError('cli_predispatch_unpaid_frame')
        if row['event'] == 'frontend_write_returned':
            returned[row['type']] += 1
            if returned[row['type']] > frames[row['type']]:
                raise ValueError('cli_predispatch_unpaid_write')
        if row['event'] == 'connect_attempt':
            connection_attempts += 1
            if connection_attempts != 1 or row['id'] != 1 or row['tls_verify_full'] is not True:
                raise ValueError('cli_predispatch_connection_count')
    if not events or events[0]['event'] != 'preregister':
        raise ValueError('cli_predispatch_incomplete_journal')
    terminal_recorded = events[-1]['event'] == 'terminal'
    if not terminal_recorded and not allow_incomplete:
        raise ValueError('cli_predispatch_incomplete_journal')
    terminal = events[-1] if terminal_recorded else dict(event='incomplete_summary',
        sql_dispatches=len(dispatches), confirmed_sql=len(outcomes),
        unknown_consumed=len(dispatches) - len(outcomes), frontend_frames_by_type=dict(frames),
        frontend_write_returned_by_type=dict(returned), connection_attempts=connection_attempts,
        complete=False, hosted_admission=False)
    if terminal['sql_dispatches'] != len(dispatches) or terminal['confirmed_sql'] != len(outcomes) or \
            terminal['unknown_consumed'] != len(dispatches) - len(outcomes) or \
            terminal['frontend_frames_by_type'] != dict(frames) or \
            terminal['frontend_write_returned_by_type'] != dict(returned) or \
            terminal['connection_attempts'] != connection_attempts:
        raise ValueError('cli_predispatch_totals')
    header = events[0]
    if header['environment'] != 'disposable_ci' or header['hosted_admission'] is not False or \
            terminal['hosted_admission'] is not False or len(dispatches) > header['cap'] or \
            header['cap'] != {'quota': 64, 'pre_auth': 28, 'final': 28}.get(header['slot']) or \
            header['dry_run'] is not (header['slot'] != 'quota') or \
            sum(frames.values()) > 512 or (terminal['complete'] and len(outcomes) != len(dispatches)):
        raise ValueError('cli_predispatch_scope_or_capacity')
    return {'header': header, 'terminal': terminal, 'events': events,
            'terminal_recorded': terminal_recorded,
            'journal_sha256': sha(raw), 'event_count': len(events)}


def source_binding(upstream):
    spec = importlib.util.spec_from_file_location('fmz_predispatch_prepare', HERE / 'prepare.py')
    prepare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prepare)
    build = json.loads((upstream / 'apps/cli/cli_predispatch/build.json').read_bytes())
    if build['upstream_commit'] != UPSTREAM or build['hosted_admission'] is not False or \
            build['source_before_lf'] != prepare.PINS or set(build['hook_sources']) != set(prepare.COPY) or \
            build['entry_sha256'] != sha(prepare.PATCHED_ENTRY.encode()):
        raise ValueError('cli_predispatch_build_binding')
    def git(*args):
        result = subprocess.run(['git', '-C', str(upstream), *args], capture_output=True, timeout=5, check=True)
        return result.stdout.decode().strip()
    if git('rev-parse', 'HEAD') != UPSTREAM or \
            git('diff', 'HEAD', '--name-only').splitlines() != ['apps/cli/src/main.ts']:
        raise ValueError('cli_predispatch_checkout_changed')
    if sha((upstream / 'apps/cli/src/main.ts').read_bytes()) != build['entry_sha256']:
        raise ValueError('cli_predispatch_entry_changed')
    for name, expected in build['hook_sources'].items():
        if name not in ('hook.cjs', 'entry.mjs', 'package.json', 'pnpm-lock.yaml', 'pnpm-workspace.yaml') or \
                sha((HERE / name).read_bytes()) != expected or \
                sha((upstream / 'apps/cli/cli_predispatch' / name).read_bytes()) != expected:
            raise ValueError('cli_predispatch_hook_changed')
    for name, expected in prepare.PINS.items():
        if name == 'apps/cli/src/main.ts':
            continue
        if sha((upstream / name).read_bytes().replace(b'\r\n', b'\n')) != expected:
            raise ValueError('cli_predispatch_upstream_changed')
    return build


def migration_inventory(gate):
    """The app stack is canonical 45 plus its two separately sourced migrations."""
    if gate.result.get('clean_rebuild') != '47/47_PASS_LOCAL_CANDIDATE' or \
            gate.result.get('migrations_applied') != 47:
        raise ValueError('cli_predispatch_clean47_required')
    manifest = json.loads((gate.out / 'candidate.json').read_bytes())
    if manifest['sha256'] != gate.result['candidate_sha256']:
        raise ValueError('cli_predispatch_inventory_binding')
    expected = list((gate.sources / 'supabase/migrations').glob('*.sql'))
    expected += list((gate.sources / '_offline/phase6e_server_v1/supabase/migrations').glob('*.sql'))
    files = sorted((gate.work / 'supabase/migrations').glob('*.sql'))
    if len(expected) != 47 or len({p.name for p in expected}) != 47 or \
            {p.name for p in files} != {p.name for p in expected}:
        raise ValueError('cli_predispatch_migration_inventory')
    source_by_name = {p.name: p for p in expected}
    bound = {}
    for file in files:
        source = source_by_name[file.name]
        relative = source.relative_to(gate.sources).as_posix()
        digest = sha(source.read_bytes())
        if manifest['sources'].get(relative) != digest or sha(file.read_bytes()) != digest:
            raise ValueError('cli_predispatch_migration_bytes')
        bound[relative] = digest
    return files, bound


def isolated(gate, receipt, measure):
    """Reuse the app's CI-only cron isolation without changing its CLI profile."""
    from cli_isolation import measured
    class Context:
        container = gate.container
        cli_protocol = []
        def rows(self, text):
            return gate.rows(text)
        def command(self, label, *args, **kwargs):
            return gate.command('cli-predispatch-' + label, *args, **kwargs)
        def save(self, name, value):
            safe = {k: v for k, v in value.items() if k != 'protocol'}
            safe['protocol'] = [dict(statement_sha256=sha(p['statement'].encode()),
                                     confirmed=p['confirmed']) for p in value['protocol']]
            receipt['ci_bootstrap_sql_commands'] = value['commands']
            receipt['ci_cron_restored'] = value['restored']
            gate.save('cli-predispatch-' + name, safe)
    context = Context()
    def invoke(_context, _args, _timeout):
        result = measure()
        context.cli_protocol.append(dict(complete=result['complete'],
            numeric_protocol_coverage=result['numeric_coverage']['all_protocol_visible']))
        return result
    return measured(context, (), 45, invoke)


def run(gate):
    if os.environ.get('GITHUB_REPOSITORY') != 'Yourizorge/fitmetzorge-staging' or \
            gate.container != 'supabase_db_fmz-db41-ci':
        raise ValueError('cli_predispatch_disposable_only')
    from cli_meter import source_commit
    from cli_stat_reader import snapshot, compare
    from native_runtime import NativeRuntime
    commit = source_commit(gate.result)
    candidate = gate.result.get('candidate_sha256')
    if not isinstance(candidate, str) or not re.fullmatch('[a-f0-9]{64}', candidate):
        raise ValueError('cli_predispatch_candidate_binding')
    files, migration_sources = migration_inventory(gate)
    upstream = pathlib.Path(os.environ['FMZ_CLI_PREDISPATCH_UPSTREAM']).resolve()
    build = source_binding(upstream)
    bun = shutil.which(os.environ.get('FMZ_BUN', 'bun'))
    if not bun:
        raise ValueError('cli_predispatch_bun_missing')
    def private(args):
        code, output = bounded(args, cwd=gate.work, env=os.environ.copy(), seconds=5)
        if code:
            raise ValueError('cli_predispatch_bootstrap')
        return output.decode().strip()
    if private([bun, '--version']) != '1.4.1':
        raise ValueError('cli_predispatch_bun_pin')
    password = private(['docker', 'exec', gate.container, 'sh', '-c', 'printf %s "$POSTGRES_PASSWORD"'])
    endpoints = private(['docker', 'port', gate.container, '5432/tcp']).splitlines()
    endpoints = [x for x in endpoints if re.fullmatch(r'(127\.0\.0\.1|0\.0\.0\.0):\d+', x)]
    if len(endpoints) != 1 or not password or password.startswith('sbp_'):
        raise ValueError('cli_predispatch_loopback')
    port = int(endpoints[0].split(':')[1])
    ca = gate.work / 'fmz-ci-ca.crt'
    work = gate.work / ('cli-predispatch-' + uuid.uuid4().hex)
    (work / 'supabase/migrations').mkdir(parents=True)
    (work / 'private-home').mkdir()
    for file in files:
        shutil.copyfile(file, work / 'supabase/migrations' / file.name)
    # A distinct config port keeps explicit --db-url on the upstream TLS route.
    config_port = 65534 if port != 65534 else 65532
    (work / 'supabase/config.toml').write_text(
        'project_id = "fmz-cli-predispatch"\n[db]\nmajor_version = 17\nport = ' + str(config_port) +
        '\nshadow_port = 65533\n[db.migrations]\nenabled = true\n[db.seed]\nenabled = false\n')
    policy = {'version': 1, 'environment': 'disposable_ci', 'upstream_commit': UPSTREAM,
        'source_commit': commit, 'candidate_sha256': candidate, 'invocation_id': str(uuid.uuid4()),
        'slot': 'final', 'cap': 28, 'closure_reserve': 0, 'dry_run': True,
        'host': '127.0.0.1', 'port': port, 'database': 'postgres', 'user': 'postgres',
        'ca_sha256': sha(ca.read_bytes()), 'migrations': []}
    policy_file = work / 'policy.json'
    policy_file.write_text(json.dumps(policy))
    ledger_file = work / 'ledger.jsonl'
    from urllib.parse import urlencode
    url = 'postgresql://postgres@127.0.0.1:' + str(port) + '/postgres?' + urlencode({
        'sslmode': 'verify-full', 'sslrootcert': str(ca), 'connect_timeout': '5',
        'options': '-c statement_timeout=5000 -c lock_timeout=1000'})
    env = {k: v for k, v in os.environ.items() if not k.startswith(('PG', 'SUPABASE_', 'GH', 'NODE_', 'BUN_'))}
    env.update(PGPASSWORD=password, DO_NOT_TRACK='1', SUPABASE_NO_UPDATE_NOTIFIER='1',
        SUPABASE_TELEMETRY_DISABLED='1', HOME=str(work / 'private-home'),
        USERPROFILE=str(work / 'private-home'), XDG_CONFIG_HOME=str(work / 'private-home'),
        FMZ_CLI_PREDISPATCH_POLICY=str(policy_file), FMZ_CLI_PREDISPATCH_LEDGER=str(ledger_file))
    runtime = NativeRuntime.disposable(gate)
    receipt = {'scope': 'DISPOSABLE_CI_ONLY', 'hosted_admission': False, 'complete': False,
        'build': build, 'source_commit': commit, 'candidate_sha256': candidate,
        'migration_sources': migration_sources,
        'query_ms': 5000, 'cli_seconds': 45, 'output_max_bytes': 8192,
        'actual_migration_execution': False, 'actual_empty_dry_run': False}
    def measure():
        before, first = snapshot(runtime)
        try:
            code, output = bounded([bun, str(upstream / 'apps/cli/src/main.ts'), 'db', 'push',
                '--db-url', url, '--dry-run', '--skip-vault', '--yes', '--output-format', 'json'], cwd=work, env=env)
        finally:
            after, last = snapshot(runtime)
            receipt['observer_trace'] = first + last
            receipt['observer_commands'] = len(first) + len(last)
        if password.encode() in output:
            raise ValueError('cli_predispatch_private_output')
        receipt['tracking'] = tracking_evidence(before, after)
        check_invocation(receipt, code, output, ledger_file)
        evidence = replay(ledger_file)
        receipt.update(evidence)
        header = evidence['header']
        if header['source_commit'] != commit or header['candidate_sha256'] != candidate or \
                header['invocation_id'] != policy['invocation_id'] or \
                header['policy_sha256'] != sha(json.dumps(policy, separators=(',', ':')).encode()) or \
                receipt['observer_commands'] != 8 or receipt['tracking']['valid'] is not True:
            raise ValueError('cli_predispatch_runtime_binding')
        numeric = compare(before, after, evidence['terminal']['sql_dispatches'], between=3)
        receipt['numeric_coverage'] = numeric
        terminal = evidence['terminal']
        if code or not terminal['complete'] or not 0 < terminal['sql_dispatches'] <= 28 or \
                terminal['unknown_consumed'] or not numeric['all_protocol_visible'] or numeric['temp_written'] != 0:
            raise ValueError('cli_predispatch_evidence_incomplete')
        if b'up to date' not in output.lower() or b'would push' in output.lower():
            raise ValueError('cli_predispatch_not_empty')
        receipt.update(complete=True, actual_empty_dry_run=True)
        return receipt
    try:
        return isolated(gate, receipt, measure)
    except Exception as error:
        receipt['complete'] = False
        receipt['failure_class'] = type(error).__name__
        # A killed child cannot refund unused-looking reservation. Preserve its
        # durable prefix separately; a reconstructed summary is never a terminal.
        receipt['reserved_sql_consumed_on_failure'] = policy['cap']
        try:
            receipt['failure_ledger'] = replay(ledger_file, allow_incomplete=True)
        except (OSError, ValueError, KeyError, TypeError):
            receipt['failure_ledger_unverifiable'] = True
        raise
    finally:
        env.pop('PGPASSWORD', None)
        password = None
        runtime.clear()
        gate.save('cli-predispatch.json', receipt)
