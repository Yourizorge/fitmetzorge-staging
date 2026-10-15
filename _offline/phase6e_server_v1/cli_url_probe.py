"""Offline-only CLI URL diagnostic component; NOT a live probe or admission.

The parent can run test_cli_url_probe.py in app CI without a database hook.
replay_saved(hosted_folder, ci_folder) rechecks existing sanitized receipts.
CliUrlProbe.analyze() consumes already captured, invocation-scoped PG logs in
memory, using the existing cli_meter parser. It never starts a CLI or connects.

A future live adapter must use NativeRuntime.disposable(gate), verify its
loopback TLS endpoint, bind the pinned binary, bound CLI output to 8 KiB and
execution to 45 seconds, and restore exact logging settings on every exit.
Queries retain statement_timeout=5000 and lock_timeout=1000. The local URL
must omit the hosted JIT lease option, not emulate it with a PG server GUC.
That adapter is deliberately NOT implemented here. Dry runs cannot establish
the cause of the hosted migration's two-call excess.
"""
import hashlib
import json
import os
import pathlib
import re
import sys

ENDCHAIN = pathlib.Path(__file__).resolve().parents[1] / 'phase6e11/endchain_v1'
if str(ENDCHAIN) not in sys.path:
    sys.path.insert(0, str(ENDCHAIN))
from cli_meter import TAG, parse
from cli_stat_reader import SQL, compare
from sql_protocol import statements

CLI_SHA256 = '40efbaffd04e4cbf501b4f29a52c88ca23f81c636ef211e3b255c4e7b81eeb01'
MAX_OUTPUT = 8192
MAX_LOG = 2000000
MAX_COMMANDS = 64
CLI_SECONDS = 45
QUERY_MS = 5000
URL_OPTIONS = '-c default_transaction_read_only=on -c statement_timeout=5000 -c lock_timeout=1000'
OBSERVER = ('BEGIN TRANSACTION READ ONLY',
            "select current_setting('transaction_read_only')='on' readonly", SQL, 'ROLLBACK')
NOISE = ('SELECT 1 AS cli_probe_noise', 'SELECT 2 AS cli_probe_noise')
CLI_APPS = (TAG, '@effect/sql-pg', 'fmz6e11_jit_cli_dryrun_v1')
LIMITATIONS = ['Offline replay only; no CLI, NativeRuntime, or TLS session executed by this helper.',
               'Local PG does not exercise hosted pooler/JIT lease access.',
               'Dry-run counts do not establish migration execution counts or the hosted failure cause.']


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def argument_template(route):
    if route == 'local':
        return ['db', 'push', '--local', '--dry-run', '--skip-vault']
    if route == 'db_url':
        return ['db', 'push', '--db-url', '<private-loopback-tls-url>', '--skip-vault',
                '--yes', '--output-format', 'json', '--dry-run']
    raise ValueError('probe_route')


def _hashes(texts):
    return [statements(text)[0]['sha256'] for text in texts]


def _groups(raw, prefix):
    """Keep PID boundaries before passing SQL to the existing hashing parser."""
    if not isinstance(raw, str) or len(raw.encode()) > MAX_LOG:
        raise ValueError('probe_log_budget')
    if not re.fullmatch(r'FMZSQL[0-9a-f]{32}\|', prefix):
        raise ValueError('probe_invocation_prefix')
    groups = {}
    frame = None

    def finish():
        if frame is None:
            return
        app, pid, ordinal, lines = frame
        if len('\n'.join(lines).encode()) > MAX_OUTPUT:
            raise ValueError('probe_frame_budget')
        group = groups.setdefault(pid, {'app': app, 'ordinal': 0, 'lines': []})
        if group['app'] != app or ordinal <= group['ordinal']:
            raise ValueError('probe_session_frame')
        group['ordinal'] = ordinal
        group['lines'].extend(lines)

    for line in raw.splitlines():
        if line.startswith(prefix):
            finish()
            parts = line.split('|', 4)
            if len(parts) != 5 or not parts[2].isdigit() or not parts[3].isdigit():
                raise ValueError('probe_log_frame')
            frame = (parts[1], int(parts[2]), int(parts[3]), [line])
        elif re.match(r'^FMZSQL[0-9a-f]{32}\|', line):
            finish()
            frame = None
        elif frame is not None:
            frame[3].append(line)
    finish()
    return groups


class CliUrlProbe:
    """Analyze captures only. Does not expose a live run(gate) method."""

    def __init__(self):
        self.prefixes = set()

    def analyze(self, *, route, cli_sha256, prefix, raw_log, before, after,
                cli_pid, observer_pids, noise_pid=None, cli_output=b'', exit_code=0):
        template = argument_template(route)
        if cli_sha256 != CLI_SHA256:
            raise ValueError('probe_cli_binding')
        if not isinstance(cli_output, bytes) or len(cli_output) > MAX_OUTPUT:
            raise ValueError('probe_output_budget')
        if prefix in self.prefixes:
            raise ValueError('probe_reused_invocation')
        pids = [cli_pid, *observer_pids] + ([] if noise_pid is None else [noise_pid])
        if len(observer_pids) != 2 or any(type(p) is not int or p <= 0 for p in pids) or len(set(pids)) != len(pids):
            raise ValueError('probe_pid_binding')
        self.prefixes.add(prefix)
        try:
            groups = _groups(raw_log, prefix)
            if set(groups) != set(pids) or groups[cli_pid]['app'] not in CLI_APPS:
                raise ValueError('probe_unattributed_session')
            commands = {pid: parse('\n'.join(g['lines']), prefix, (g['app'],)) for pid, g in groups.items()}
            if sum(map(len, commands.values())) > MAX_COMMANDS:
                raise ValueError('probe_command_budget')
            for pid in observer_pids:
                if [c['sha256'] for c in commands[pid]] != _hashes(OBSERVER):
                    raise ValueError('probe_observer_protocol')
            noise = [] if noise_pid is None else commands[noise_pid]
            if noise_pid is not None and [c['sha256'] for c in noise] != _hashes(NOISE):
                raise ValueError('probe_noise_protocol')
            numeric = compare(before, after, len(commands[cli_pid]), between=3)
            controlled = compare(before, after, len(commands[cli_pid]) + len(noise), between=3)
        except Exception:
            # Parser/driver errors can contain SQL text. Never export them.
            raise ValueError('probe_capture_incomplete') from None
        return {'scope': 'LOCAL_CI_OFFLINE_DIAGNOSTIC_ONLY', 'hosted_admission': False,
                'limitations': LIMITATIONS, 'route': route, 'argument_template': template,
                'cli_sha256': cli_sha256, 'invocation_prefix': prefix, 'exit_code': exit_code,
                'output_sha256': hashlib.sha256(cli_output).hexdigest(),
                'commands': commands[cli_pid], 'protocol_commands': len(commands[cli_pid]),
                'observer_commands': 8, 'observer_calls_inside_window': 4,
                'controlled_interference_commands': noise,
                'numeric_calls_minus_reader': numeric['numeric_calls_minus_reader'],
                'cli_only_equality': numeric['all_protocol_visible'],
                'controlled_total_equality': controlled['all_protocol_visible'],
                'temp_written': numeric['temp_written'],
                'before_sha256': digest(before), 'after_sha256': digest(after),
                'raw_sql_exported': False, 'raw_output_exported': False,
                'runtime_executed': False, 'migration_cause_proven': False}


def _read(folder, name):
    path = pathlib.Path(folder).resolve() / name
    if os.name == 'nt' and not str(path).startswith('\\\\?\\'):
        path = pathlib.Path('\\\\?\\' + str(path))
    with path.open('rb') as source:
        raw = source.read(MAX_LOG + 1)
    if len(raw) > MAX_LOG:
        raise ValueError('probe_saved_receipt_budget')
    return json.loads(raw)


def replay_saved(hosted_folder, ci_folder):
    before = _read(hosted_folder, 'hosted-cli-before-0.json')
    after = _read(hosted_folder, 'hosted-cli-after-0.json')
    stored = _read(hosted_folder, 'cli-numeric-coverage-0.json')
    protocol = _read(ci_folder, 'cli-protocol-0.json')
    ci = _read(ci_folder, 'cli-numeric-coverage-0.json')
    if protocol['cli_sha256'] != CLI_SHA256 or protocol['protocol_commands'] != 14:
        raise ValueError('probe_saved_cli_binding')
    observed = compare(before['stats'], after['stats'], 14, between=3)
    if observed != stored:
        raise ValueError('probe_saved_receipt_mismatch')
    for value in (before, after):
        if len(value['commands']) != 4 or not all(c['confirmed'] for c in value['commands']):
            raise ValueError('probe_saved_observer_incomplete')
    ci_total = sum(row['calls'] for row in ci['statements'])
    if (ci_total - 4 != ci['numeric_calls_minus_reader'] or ci['protocol_commands'] != 14
            or not ci['all_protocol_visible'] or ci['numeric_calls_minus_reader'] != 14
            or not protocol['complete'] or not protocol['numeric_protocol_coverage']):
        raise ValueError('probe_saved_ci_incomplete')
    return {'scope': 'SAVED_EVIDENCE_REPLAY_ONLY', 'hosted_raw_calls': sum(r['calls'] for r in observed['statements']),
            'ci_raw_calls': ci_total, 'observer_calls_inside_window': 4,
            'hosted_net_calls': observed['numeric_calls_minus_reader'], 'ci_net_calls': ci['numeric_calls_minus_reader'],
            'hosted_exact_equality': observed['all_protocol_visible'], 'hosted_temp_written': observed['temp_written'],
            'cli_sha256': CLI_SHA256, 'hosted_receipt_sha256': digest(stored), 'ci_receipt_sha256': digest(ci),
            'hosted_admission': False, 'migration_cause_proven': False, 'limitations': LIMITATIONS}


if __name__ == '__main__':
    try:
        if len(sys.argv) != 3:
            raise ValueError('expected_hosted_and_ci_receipt_directories')
        print(json.dumps(replay_saved(*sys.argv[1:]), sort_keys=True))
    except Exception:
        print(json.dumps({'status': 'INCOMPLETE', 'scope': 'OFFLINE_ONLY', 'raw_values_exported': False}))
        sys.exit(2)
