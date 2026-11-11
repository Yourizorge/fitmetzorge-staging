"""Source-bound disposable installation observer; incomplete startup is never PASS.

The root owner must admit the entire installation before this wrapper dispatches
anything. This module does not invent its bound. It observes explicit outer SQL
and processes but cannot observe PostgreSQL-image or managed-service startup SQL.
Even a successful legacy install therefore terminates unknown_consumed here.
"""
import hashlib
import importlib
import inspect
import json
import os
import pathlib
import sys
import types

PREFIX = '_offline/phase6e11/endchain_v1/'
COMMAND_ID = 'case.platform.install'
PG_NAME = 'supabase_db_fmz-db41-ci'
UPSTREAM = '21db855916f2c2b12f61cde923a27094b8528b23'
PINS = {
    '_offline/phase6e11/ci41/runner.py': '18f8efaa9dfc91be59926a40c805499cacce73f5717975b0756a52720839dc45',
    '_offline/phase6e_server_v1/ci.py': '0744c1d81751345cf24580ee30e189c02fb5aef2704b9429c441d412b550c92a',
    PREFIX + 'admission_ci.py': '161dc43ea02df6edc9b0e3f05d625a4077816de055a61e686077036f02147b13',
    PREFIX + 'integral_ci.py': '5a6b86e9464aabef93f184db86723090f401d25288a664241c82fc4814c1dbe7',
    PREFIX + 'admission_tools.py': '0b6f68bdfba21742703a05ac81e93e34cf81289761ffbaa4f0251fba6a4f21aa',
    PREFIX + 'cli_predispatch/hook.cjs': '55d6d14c392f760cff0f7abfd3af9aa1794865823195829efcddcf7323524be9',
    PREFIX + 'cli_predispatch/prepare.py': 'a95db183de50cb2ea9947a990a32176d28a3249ef3ada965127014816644883a',
}
UPSTREAM_PINS = {
    'db-bootstrap/start-local-database.ts': '9996097b098dd5e413cb51e968e908cacd414ae1e7335d8fef2a507ff059fe1c',
    'db-bootstrap/start-database.ts': 'e628d3a50c1691af287e4426fa8f6ad2f4ac24738260cd43c90e2793158252cf',
    'db-bootstrap/postgres.service.ts': 'cc898a0e73bf2cf9d7be0390af4925a9acd47a9f5d68811834cfa4640965721b',
    'db-bootstrap/db-setup.ts': '71732e50bbb51042a56f5d518dc9e09846b57862f7011d95247e840d34df032b',
    'legacy-db-connection.sql-pg.layer.ts': '90d2032c3c73849e9baf24a63dc9668d358e879b77209124ab8179a41e9f843c',
    'db-bootstrap/templates/db-schema.sql.ts': '80e89f69c8ebd722496aa5dedba4381a6f4dc3c9fee6140af401dbf5359372cb',
    'db-bootstrap/templates/db-webhook.sql.ts': '091dd89d2c1f6c89db9036a06bd7fed226cc63a1d4a06c543b6c22b46a3a183a',
    'db-bootstrap/templates/db-supabase.sql.ts': '25248422a6819c3815dd044f472819ec35a4087b0c1abc8d34bb58a47037dd6f',
}
TLS_SETTINGS = ('ssl_cert_file', 'ssl_key_file', 'ssl', 'log_parameter_max_length',
    'log_parameter_max_length_on_error', 'log_statement', 'log_min_duration_statement',
    'log_min_duration_sample', 'log_transaction_sample_rate')
UNKNOWN = ('postgres_image_entrypoint_and_psql', 'cli_start_connections_queries_and_retries',
    'managed_realtime_migrate', 'managed_storage_migrate', 'managed_gotrue_migrate',
    'psql_connection_implicit_sql', 'background_or_restart_sql', 'failure_cleanup_sql')


class PlatformIncomplete(RuntimeError):
    pass


def require(value, reason):
    if not value:
        raise PlatformIncomplete(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _pins(root, pins):
    root = pathlib.Path(root).resolve(strict=True)
    result = {}
    for name, expected in pins.items():
        path = root / name
        require(not path.is_symlink() and path.resolve().is_relative_to(root), 'platform_source_path')
        raw = path.read_bytes()
        require(sha(raw.replace(b'\r\n', b'\n')) == expected, 'platform_source_changed:' + name)
        result[name] = {'raw_sha256': sha(raw), 'lf_sha256': expected}
    return result


def _operations():
    rows = []
    def add(label, channel='gate', explicit=None):
        rows.append({'id': 'platform.%02d' % (len(rows) + 1), 'label': label,
            'channel': channel, 'explicit_sql_statements': explicit,
            'covered_by': COMMAND_ID})
    add('pg17-parser-install')
    for label in ('cli---version', 'cli-init', 'cli-db', 'containers', 'image', 'digest'):
        add(label)
    for _ in range(3): add('psql', explicit=1)
    for label in ('generate', 'key_copy', 'ca_copy', 'owner', 'mode'): add(label, 'tls_process')
    for setting in TLS_SETTINGS: add('ci-bootstrap-' + setting, explicit=1)
    add('ci-bootstrap-reload', explicit=1)
    for label in ('admission-tool-version', 'admission-tool-version', 'admission-upstream',
                  'admission-upstream-pin', 'admission-upstream-deps', 'admission-cli-patch',
                  'admission-hook-deps', 'admission-hook-deps', 'admission-hook-tests',
                  'admission-cli-python', 'admission-cli-smoke'):
        add(label)
    return rows


def source_program(source_root, *, upstream_root=None):
    """Actual outer call inventory, NOT executable authority or a total bound."""
    sources = _pins(source_root, PINS)
    upstream = None if upstream_root is None else _pins(
        pathlib.Path(upstream_root) / 'apps/cli/src/command-internal', UPSTREAM_PINS)
    return {'format': 'platform-install-source-inventory-v1', 'command_id': COMMAND_ID,
        'sources': sources, 'upstream_commit': UPSTREAM, 'upstream_sources': upstream,
        'upstream_expected_lf_sha256': UPSTREAM_PINS.copy(),
        'outer_operations': _operations(), 'outer_process_invocations_success_path': 36,
        'explicit_outer_sql_statements_success_path': 13,
        'unknown_atoms': [{'id': name, 'units': None, 'observed_sql_commands': None} for name in UNKNOWN],
        'units': None, 'reserve_after': None, 'observed_sql_commands': None,
        'bound_complete': False, 'source_inventory_complete': False,
        'raw_sql_exported': False, 'release_binary_equivalence_claimed': False,
        'scope': 'Gate.install only; earlier entry parser process and nested subprocesses not included in 36',
        'binary_archive_pins': {
            'supabase_2.117.0_linux_amd64': '69c05f85b9e47ee706d30f1a6ca8a526b4e337bfd12c7ef1ef522d24e7280d24',
            'bun_1.4.1_linux_x64': '74c1c3bee7cd998500c8f969cd8972355ac6a07207e94a39eece1999b56ffabf',
            'pnpm_12.3.0_linux_x64': '64dc4ce87f81ea614a4e4fecd5e6f81d8ef91fae37434602e6a5aebf6dd22939'},
        'known_connection_behavior': {'local_cli_tls': False, 'connect_retry_recurs': 10,
            'local_connect_timeout_default_seconds': 2,
            'pool_probe': 'SELECT 1 per acquired probed pool; actual attempts unknown',
            'role_step_down': 'not installed for isLocal=true; remote-only branch is not counted as local startup'},
        'case_tls_san': ['DNS:localhost', 'IP:127.0.0.1', 'DNS:' + PG_NAME],
        'tls_patch_scope': 'Exact openssl generate argv only; same five processes and ten explicit SQL commands',
        'explicit_psql_startup_parameters': {
            'statement_timeout_ms': 5000, 'lock_timeout_ms': 1000, 'connect_timeout_seconds': 5,
            'scope': 'Thirteen explicit docker-exec psql calls only; no managed-startup coverage claim'},
        'full_chain_admission': False, 'hosted_admitted': False}


class _Journal:
    def __init__(self, out):
        self.path = pathlib.Path(out) / 'case-platform-dispatch.ledger.txt'
        self.fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        self.size = 0
        self.sequence = 0
        self.previous = '0' * 64

    def append(self, data):
        row = dict(data, sequence=self.sequence + 1, previous_sha256=self.previous)
        encoded = json.dumps(row, sort_keys=True, separators=(',', ':')).encode()
        raw = encoded + b'\n'
        require(len(raw) <= 8192 and self.size + len(raw) <= 262144, 'platform_journal_size')
        require(os.write(self.fd, raw) == len(raw), 'platform_journal_short_write')
        os.fsync(self.fd)
        self.size += len(raw)
        self.sequence += 1
        self.previous = sha(encoded)

    def close(self):
        os.close(self.fd)


class _Monitor:
    def __init__(self, journal, plan, count_sql):
        self.journal, self.plan, self.count_sql = journal, plan, count_sql
        self.index = 0
        self.attempted_explicit_sql = 0
        self.confirmed_explicit_sql = 0

    def dispatch(self, channel, label, call, *, sql=None):
        require(self.index < len(self.plan), 'platform_extra_dispatch')
        row = self.plan[self.index]
        require((channel, label) == (row['channel'], row['label']), 'platform_dispatch_order')
        expected = row['explicit_sql_statements']
        if expected is None:
            require(sql is None, 'platform_unregistered_sql')
        else:
            require(isinstance(sql, str) and len(sql.encode()) <= 8192
                    and self.count_sql(sql) == expected, 'platform_statement_shape')
        # Covered by the already-paid root ticket; never add this a second time.
        intent = {'event': 'dispatch_intent', 'operation': row['id'], 'label': label,
            'channel': channel, 'covered_by': COMMAND_ID, 'outcome': 'unknown_consumed',
            'explicit_sql_statements': expected,
            'sql_sha256': sha(sql.encode()) if sql is not None else None}
        self.journal.append(intent)
        self.index += 1
        self.attempted_explicit_sql += expected or 0
        result = call()
        require(type(result.returncode) is int, 'platform_process_exit_missing')
        self.journal.append({'event': 'process_exit', 'operation': row['id'],
            'exitcode': result.returncode, 'explicit_statement_confirmed': expected if result.returncode == 0 else None})
        if result.returncode == 0:
            self.confirmed_explicit_sql += expected or 0
        return result


def _bound(gate, name):
    module = importlib.import_module(name)
    actual = pathlib.Path(module.__file__).resolve(strict=True)
    root = gate.sources.resolve(strict=True)
    require(actual.is_relative_to(root), 'platform_candidate_origin')
    gate.bind_modules(module)
    return module


def _context(gate, ledger):
    require(os.environ.get('GITHUB_ACTIONS') == 'true'
        and os.environ.get('GITHUB_REPOSITORY') == 'Yourizorge/fitmetzorge-staging'
        and os.environ.get('GITHUB_REF') == 'refs/heads/main'
        and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'platform_disposable_only')
    require(pathlib.Path(__file__).resolve() == gate.sources.resolve() / PREFIX / 'install_platform.py',
            'platform_wrapper_origin')
    gate.bind_modules(sys.modules[__name__])
    require(pathlib.Path(inspect.getsourcefile(gate.install)).resolve()
            == gate.sources.resolve() / PREFIX / 'admission_ci.py', 'platform_install_owner')
    root = _bound(gate, 'admission_budget_root_runtime')
    program = source_program(gate.sources)
    # This checks actual factory origin, same gate, pins and next instruction.
    # A test-only ledger or a caller-supplied status dictionary is not authority.
    authority = root.require_runtime_ledger(gate, ledger, command_id=COMMAND_ID)
    tls = _bound(gate, 'integral_ci')
    protocol = _bound(gate, 'sql_protocol')
    return program, authority, tls, lambda sql: len(protocol.statements(sql))


def _tls_generate(gate, args, kwargs):
    """Add the actual private Docker DNS SAN before the existing CA hash is saved."""
    require(gate.container == PG_NAME, 'platform_tls_container')
    expected = ['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
        '-keyout', str(gate.work / 'fmz-ci-server.key'), '-out', str(gate.work / 'fmz-ci-ca.crt'),
        '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1']
    require(args == (expected,) and kwargs == {'capture_output': True, 'timeout': 15},
            'platform_tls_generate_source')
    return ([*expected[:-1], expected[-1] + ',DNS:' + PG_NAME],)


def _native_args(gate, label, args):
    role = 'postgres' if label == 'psql' else 'supabase_admin'
    expected = ['docker', 'exec', '-i', PG_NAME, 'psql', '-X', '-U', role,
                '-d', 'postgres', '-qAt', '-v', 'ON_ERROR_STOP=1']
    require(gate.container == PG_NAME and args == expected, 'platform_native_command')
    # libpq startup options, not extra SQL and not an environment-wide override.
    return ['docker', 'exec', '-e', 'PGOPTIONS=-c statement_timeout=5000 -c lock_timeout=1000',
            '-e', 'PGCONNECT_TIMEOUT=5', *expected[2:]]


def install_platform(gate, *, ledger):
    """Execute the existing installer under a genuine prepaid root instruction.

    Current A admission rejects the unresolved startup bound before this point.
    If a future complete bound admits dispatch, incomplete observation still
    consumes that whole reservation and raises; it never confirms thirteen.
    """
    program, authority, tls, count_sql = _context(gate, ledger)
    gate.save('case-platform-source.json', program)
    ticket = ledger.precharge(COMMAND_ID)
    journal = monitor = None
    old_command = gate.command
    had_command = 'command' in vars(gate)
    old_override = vars(gate).get('command')
    old_subprocess = tls.subprocess
    primary = None
    try:
        journal = _Journal(gate.out)
        journal.append({'event': 'root_reserved', 'command_id': COMMAND_ID, 'authority': authority})
        monitor = _Monitor(journal, program['outer_operations'], count_sql)
        def command(label, args, sql=None, timeout=90, check=True):
            if sql is not None: args = _native_args(gate, label, args)
            return monitor.dispatch('gate', label,
                lambda: old_command(label, args, sql=sql, timeout=timeout, check=check), sql=sql)
        def process(*args, **kwargs):
            row = program['outer_operations'][monitor.index]
            require(row['channel'] == 'tls_process', 'platform_direct_process_order')
            if row['label'] == 'generate': args = _tls_generate(gate, args, kwargs)
            return monitor.dispatch('tls_process', row['label'], lambda: old_subprocess.run(*args, **kwargs))
        gate.command = command
        # Only this source-bound module's reference changes, not global subprocess.run.
        tls.subprocess = types.SimpleNamespace(run=process)
        gate.install()
        require(monitor.index == len(program['outer_operations']), 'platform_install_sequence_incomplete')
        raise PlatformIncomplete('platform_managed_startup_unobserved')
    except BaseException as error:
        primary = error
        try:
            ledger.unknown(ticket, reason='not_terminal')
        except BaseException as secondary:
            error.add_note('platform_ledger_secondary:' + type(secondary).__name__)
        raise
    finally:
        if had_command: gate.command = old_override
        else: vars(gate).pop('command', None)
        tls.subprocess = old_subprocess
        if journal is not None:
            try: journal.close()
            except BaseException as error:
                if primary is not None: primary.add_note('platform_journal_close_secondary:' + type(error).__name__)
                else: raise
        try:
            ref = None
            if journal is not None:
                raw = journal.path.read_bytes()
                ref = {'path': journal.path.name, 'sha256': sha(raw), 'size': len(raw)}
            gate.save('case-platform-install.json', {
                'command_id': COMMAND_ID, 'outcome': 'unknown_consumed',
                'root_reservation': authority, 'ledger_ref': ref,
                'outer_dispatch_attempts': monitor.index if monitor else 0,
                'explicit_sql_attempts': monitor.attempted_explicit_sql if monitor else 0,
                'explicit_sql_confirmed': monitor.confirmed_explicit_sql if monitor else 0,
                'total_observed_sql_commands': None, 'unknown_atoms': program['unknown_atoms'],
                'primary_exception_class': type(primary).__name__ if primary else None,
                'retry': False, 'full_chain_admission': False, 'hosted_admitted': False})
        except BaseException as error:
            if primary is not None: primary.add_note('platform_receipt_secondary:' + type(error).__name__)
            else: raise


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Offline pinned platform source inventory, never installation')
    parser.add_argument('--source-root', type=pathlib.Path, required=True)
    parser.add_argument('--upstream-root', type=pathlib.Path, required=True)
    parser.add_argument('--out', type=pathlib.Path, required=True)
    args = parser.parse_args()
    report = source_program(args.source_root, upstream_root=args.upstream_root)
    raw = (json.dumps(report, sort_keys=True, indent=2) + '\n').encode()
    with args.out.open('xb') as stream:
        require(stream.write(raw) == len(raw), 'platform_inventory_short_write')
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({'artifact_sha256': sha(raw), 'bound_complete': False,
        'outer_processes': 36, 'explicit_outer_sql': 13, 'startup_total': None,
        'unknown_domains': len(UNKNOWN), 'database_invoked': False}))
