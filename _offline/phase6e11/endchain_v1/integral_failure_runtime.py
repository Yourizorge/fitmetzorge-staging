"""Local component fault boundaries, not an alternative endchain/WAL admission.

Main supplies gate.integral_failure_driver with describe(), run_case(case, s),
cleanup(case, s), and observe(case, s). describe() is pure metadata; its cases
map contains limits, cleanup_reserve, and artifact_files/artifact_bytes. Every
method and declared dependency must be in the exact candidate/loaded checkout.

run_case calls s.step(case, callback) at the REAL phase boundary. All native
commands use s.connect()/s.query(); Auth uses s.auth() with LocalTransport.
cleanup runs once even after a fault. observe returns an s.snapshot() result,
not a fabricated dictionary. No old runner/reset/quota path is invoked here.
The built-in TimeoutDriver executes a real bounded PG cancellation without
fixtures. Other phases require their source-owned adapters, not fake tables.
"""
import copy
import hashlib
import inspect
import json
import os
import pathlib
import re
import time
import uuid

from admission_binding import NEW_RUN, OLD_RUN

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREFIX = '_offline/phase6e11/endchain_v1/'
REQUIRED = ('pre_migration', 'post_migration', 'mid_auth', 'mid_controller',
            'mid_route_a', 'mid_route_b', 'mid_restore', 'lost_reply', 'duplicate',
            'timeout', 'partial_cleanup', 'cleanup_failure', 'final_check_failure',
            'closure_failure')
MODES = {name: 'after' for name in REQUIRED}
MODES.update(pre_migration='before', lost_reply='lost_reply', duplicate='duplicate',
             timeout='timeout', cleanup_failure='database_error')
OWNERS = {name: 'main actual workflow adapter' for name in REQUIRED}
OWNERS.update(pre_migration='C pre-dispatch CLI', post_migration='C confirmed CLI',
              mid_auth='E actual Auth prefix', partial_cleanup='fixture cleanup runtime',
              cleanup_failure='fixture cleanup runtime', timeout='built-in native PG17')
LIMITS = {'commands_per_case': 200, 'matrix_seconds': 180, 'sql_seconds': 5,
          'lock_seconds': 1, 'files': 2200, 'bytes': 80000000, 'file_bytes': 2000000}
RECEIPT_BYTES = 131072
CHECK = """select current_setting('server_version_num')::int/10000=17 pg17,
 current_setting('statement_timeout') in ('5s','5000ms') bounded_statement,
 current_setting('lock_timeout') in ('1s','1000ms') bounded_lock,
 current_setting('transaction_read_only')='on' readonly,
 exists(select 1 from pg_stat_ssl where pid=pg_backend_pid() and ssl) tls"""
TIMEOUT_SQL = 'SELECT pg_sleep(6)'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


class Blocked(RuntimeError):
    pass


class InjectedFailure(RuntimeError):
    pass


def error_record(error):
    # Never persist messages, SQL, parameters, URLs, tokens or driver reprs.
    state = getattr(error, 'sqlstate', None)
    return {'class': type(error).__name__,
            'sqlstate': state if isinstance(state, str) and re.fullmatch('[A-Z0-9]{5}', state) else None,
            'injected': isinstance(error, InjectedFailure)}


def registry():
    return [{'id': name, 'mode': MODES[name], 'owner': OWNERS[name],
             'standalone_adapter': name == 'timeout'} for name in REQUIRED]


def _uuid(value):
    if str(uuid.UUID(value)) != value or value in (NEW_RUN, OLD_RUN):
        raise Blocked('failure_fresh_case_uuid_required')
    return value


def _no_old_binding(text, args):
    values = text + json.dumps(args, sort_keys=True, default=str)
    if any(value in values.lower() for value in (OLD_RUN, NEW_RUN)):
        raise Blocked('failure_preparation_or_historical_uuid_not_database_authority')


def parser_sql(text, parameters):
    """Mirror positional driver placeholders; never interpolate parameter values."""
    if parameters is None:
        return text
    if not isinstance(parameters, (list, tuple)):
        raise Blocked('failure_positional_parameters_required')
    parts = text.split('%s')
    if len(parts) != len(parameters) + 1:
        raise Blocked('failure_placeholder_count')
    return ''.join(part + ('$' + str(i + 1) if i < len(parameters) else '')
                   for i, part in enumerate(parts)).replace('%%', '%')


def inventory(out):
    result = {'files': 0, 'bytes': 0, 'largest': 0}
    for path in pathlib.Path(out).rglob('*'):
        if path.is_symlink():
            raise Blocked('failure_artifact_symlink')
        if path.is_file():
            size = path.stat().st_size
            result['files'] += 1
            result['bytes'] += size
            result['largest'] = max(result['largest'], size)
    return result


def _source_binding(gate, driver, descriptor):
    candidate = json.loads((pathlib.Path(gate.out) / 'candidate.json').read_text())
    if not re.fullmatch('[a-f0-9]{64}', str(candidate.get('sha256', ''))):
        raise Blocked('failure_candidate_identity')
    files = set(descriptor.get('sources', [])) | {PREFIX + name for name in
        ('integral_failures.py', 'test_integral_failures.py', 'integral_failure_runtime.py',
         'admission_binding.py', 'native_runtime.py', 'sql_protocol.py')}
    for method in ('describe', 'run_case', 'cleanup', 'observe', 'open', 'close'):
        callback = getattr(driver, method, None)
        if callback is None and method in ('open', 'close'):
            continue
        if not callable(callback):
            raise Blocked('failure_driver_method_' + method)
        source = inspect.getsourcefile(callback)
        if source is None or not pathlib.Path(source).resolve().is_relative_to(ROOT):
            raise Blocked('failure_driver_not_checkout_source')
        files.add(pathlib.Path(source).resolve().relative_to(ROOT).as_posix())
    hashes = {}
    for name in sorted(files):
        if not isinstance(name, str) or pathlib.PurePosixPath(name).as_posix() != name:
            raise Blocked('failure_source_path')
        expected = candidate.get('sources', {}).get(name)
        if not isinstance(expected, str) or not re.fullmatch('[a-f0-9]{64}', expected):
            raise Blocked('failure_source_not_packaged')
        for folder in (ROOT, pathlib.Path(gate.sources).resolve()):
            path = folder / name
            if (not path.resolve().is_relative_to(folder) or path.is_symlink() or
                    not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
                raise Blocked('failure_source_drift')
        hashes[name] = expected
    return {'source_commit': os.environ['GITHUB_SHA'], 'ci_run': os.environ['GITHUB_RUN_ID'],
            'candidate_sha256': candidate['sha256'], 'sources': hashes}


def preflight(gate, driver, selection, diagnostic_only):
    """No SQL, process, reset, HTTP, Auth creation, or mutation in this function."""
    if (os.environ.get('GITHUB_ACTIONS') != 'true' or
            os.environ.get('GITHUB_REPOSITORY') != 'Yourizorge/fitmetzorge-staging' or
            os.environ.get('GITHUB_REF') != 'refs/heads/main' or
            not re.fullmatch('[a-f0-9]{40}', os.environ.get('GITHUB_SHA', '')) or
            not re.fullmatch('[1-9][0-9]*', os.environ.get('GITHUB_RUN_ID', ''))):
        raise Blocked('ci_only')
    if (os.environ.get('PGHOSTADDR', '127.0.0.1') != '127.0.0.1' or
            os.environ.get('PGSERVICE') or os.environ.get('PGSERVICEFILE')):
        raise Blocked('failure_inherited_remote_connection_setting')
    selected = list(REQUIRED if selection is None else selection)
    if (type(diagnostic_only) is not bool or not selected or
            any(type(x) is not str or x not in REQUIRED for x in selected) or
            len(set(selected)) != len(selected)):
        raise Blocked('failure_selection')
    if not diagnostic_only and set(selected) != set(REQUIRED):
        raise Blocked('failure_subset_requires_diagnostic_mode')
    if driver is None:
        return {'ready': False, 'missing': ['integral_failure_driver:' + x for x in selected],
                'selection': selected, 'registry': registry()}
    description = driver.describe()
    if (description.get('preparation_run') != NEW_RUN or
            description.get('environment') != 'disposable_ci' or
            description.get('reuse_existing_stack') is not True or
            description.get('historical_registry_read_only') is not True):
        raise Blocked('failure_driver_scope')
    sources = _source_binding(gate, driver, description)
    cases = description.get('cases', {})
    missing = ['real_phase_adapter:' + x for x in selected if x not in cases]
    before = inventory(gate.out)
    files, size = 4 + len(selected), RECEIPT_BYTES * (4 + len(selected))
    for key in ('bootstrap_artifact_files', 'bootstrap_artifact_bytes'):
        if type(description.get(key, 0)) is not int or description.get(key, 0) < 0:
            raise Blocked('failure_bootstrap_artifact_reservation')
    files += description.get('bootstrap_artifact_files', 0)
    size += description.get('bootstrap_artifact_bytes', 0)
    for name in selected:
        if name not in cases:
            continue
        spec = cases[name]
        for key in ('limit', 'cleanup_reserve', 'artifact_files', 'artifact_bytes'):
            if type(spec.get(key)) is not int or spec[key] < 0:
                raise Blocked('failure_case_bounds')
        if not 8 <= spec['cleanup_reserve'] < spec['limit'] <= LIMITS['commands_per_case']:
            raise Blocked('failure_cleanup_not_prepaid')
        files += spec['artifact_files']
        size += spec['artifact_bytes']
    if (before['files'] + files > LIMITS['files'] or before['bytes'] + size > LIMITS['bytes'] or
            before['largest'] > LIMITS['file_bytes']):
        raise Blocked('failure_artifact_capacity')
    return {'ready': not missing, 'missing': missing, 'selection': selected,
            'diagnostic_only': diagnostic_only, 'registry': registry(), 'cases': cases,
            'sources': sources, 'source_binding_sha256': digest(sources),
            'artifacts': {'before': before, 'reserved_files': files, 'reserved_bytes': size},
            'limits': LIMITS, 'preparation_run': NEW_RUN, 'no_stack_reset': True,
            'blocked_phase_details': description.get('blocked', {}),
            'prerequisite_details': description.get('prerequisite_details', []),
            'local_diagnostic_commands_separate_from_2349': True}


class Snapshot:
    def __init__(self, owner, values, event):
        self.owner, self.values, self.event = owner, copy.deepcopy(values), event


class Session:
    """Actual native/HTTP dispatch wrapper; unit doubles are not CI receipts."""
    def __init__(self, runtime, case, spec, deadline):
        self.runtime, self.case, self.spec, self.deadline = runtime, case, spec, deadline
        self.case_id = _uuid(str(uuid.uuid4()))
        self.events, self.connections, self.claims = [], [], set()
        self.used = 0
        self.safety = self.stopped = self.injected = self.unknown = False
        self.primary = None
        self._primary_error = None
        self.secondary = []
        self.native_confirmed = 0
        self.matched = False
        self.snapshot_token = object()

    def fail(self, error):
        if error is self._primary_error:
            return
        if self.primary is None:
            self.primary = error_record(error)
            self._primary_error = error
        else:
            self.secondary.append(error_record(error))
        self.stopped = True

    def charge(self, phase, kind, cost, fingerprint):
        if (not isinstance(phase, str) or not re.fullmatch('[a-z][a-z0-9_]{0,63}', phase) or
                type(cost) is not int or cost < 1):
            raise Blocked('failure_dispatch_shape')
        ceiling = self.spec['limit'] if self.safety else self.spec['limit'] - self.spec['cleanup_reserve']
        if self.stopped and not self.safety:
            raise Blocked('failure_stopped_no_normal_dispatch')
        if self.used + cost > ceiling or time.monotonic() >= self.deadline:
            raise Blocked('failure_prepaid_or_time_exhausted')
        self.used += cost
        event = {'ordinal': len(self.events) + 1, 'phase': phase, 'kind': kind, 'cost': cost,
                 'sha256': fingerprint, 'confirmed': False, 'reply_delivered': False}
        self.events.append(event)
        return event

    def connect(self):
        connection = self.runtime.connect()
        self.connections.append(connection)
        return connection

    def query(self, connection, phase, text, parameters=None):
        from sql_protocol import single
        if connection not in self.connections:
            raise Blocked('failure_unregistered_connection')
        _no_old_binding(text, parameters)
        single(parser_sql(text, parameters))
        event = self.charge(phase, 'sql', 1, hashlib.sha256(text.encode()).hexdigest())
        event['request_sha256'] = hashlib.sha256((text + json.dumps(parameters,
            sort_keys=True, default=str)).encode()).hexdigest()
        try:
            cursor = connection.execute(text, parameters)
            rows = cursor.fetchall() if cursor.description else []
        except BaseException as error:
            event['error'] = error_record(error)
            if getattr(error, 'sqlstate', None) is None:
                self.unknown = True
            self.fail(error)
            raise
        event['confirmed'] = event['reply_delivered'] = True
        self.native_confirmed += 1
        return rows

    def auth(self, phase, transport, method, path, *, cost, data=None, token=None, fault=None):
        from auth_failure_transport import LocalTransport, UnknownOutcome
        if type(transport) is not LocalTransport:
            raise Blocked('failure_real_local_auth_transport_required')
        _no_old_binding(path, data)
        event = self.charge(phase, 'auth', cost, digest({'method': method, 'path': path.split('?')[0]}))
        self.claims.add('auth')
        try:
            result = transport.request(method, path, data=data, token=token, fault=fault)
        except UnknownOutcome as error:
            self.unknown = True
            event['terminal'] = error.terminal is True
            self.fail(error)
            raise
        except BaseException as error:
            self.unknown = True
            self.fail(error)
            raise
        event['confirmed'] = event['reply_delivered'] = result.get('terminal') is True
        if not event['confirmed']:
            self.unknown = True
            error = Blocked('failure_auth_terminal_unproven')
            self.fail(error)
            raise error
        return result

    def step(self, phase, call):
        """Wrap a source-owned operation, never run an entire legacy chain here."""
        if phase != self.case or self.matched:
            raise Blocked('failure_exact_one_boundary')
        self.matched = True
        mode = MODES[self.case]
        if mode == 'before':
            self.injected = True
            error = InjectedFailure('failure_before_dispatch')
            self.fail(error)
            raise error
        before = len(self.events)
        try:
            value = call()
        except BaseException as error:
            if ((mode == 'timeout' and getattr(error, 'sqlstate', None) == '57014') or
                    (mode == 'database_error' and getattr(error, 'sqlstate', None) == '23503')):
                self.injected = True
            self.fail(error)
            raise
        executed = self.events[before:]
        if not executed or not all(e['confirmed'] for e in executed):
            raise Blocked('failure_boundary_without_actual_dispatch')
        if mode in ('timeout', 'database_error'):
            raise Blocked('failure_expected_native_timeout_missing')
        if mode == 'duplicate':
            # Explicit second dispatch is a test, never an automatic recovery retry.
            second = len(self.events)
            value = call()
            replay = self.events[second:]
            if [(e['kind'], e['sha256'], e.get('request_sha256'), e['cost']) for e in executed] != [
                    (e['kind'], e['sha256'], e.get('request_sha256'), e['cost']) for e in replay]:
                raise Blocked('failure_duplicate_protocol_changed')
        if mode == 'lost_reply':
            self.unknown = True
            for event in executed:
                event['reply_delivered'] = False
        self.injected = True
        error = InjectedFailure('failure_' + mode)
        self.fail(error)
        raise error

    def snapshot(self, text, parameters=None):
        """Independent read-only numeric observation; not deletion/revocation proof."""
        connection = self.connect()
        try:
            self.query(connection, 'snapshot_begin', 'BEGIN TRANSACTION READ ONLY')
            check = self.query(connection, 'snapshot_check', CHECK)
            if len(check) != 1 or set(check[0]) != {'pg17', 'bounded_statement', 'bounded_lock', 'readonly', 'tls'} or not all(v is True for v in check[0].values()):
                raise Blocked('failure_snapshot_session_limits')
            rows = self.query(connection, 'snapshot', text, parameters)
            if (len(rows) != 1 or not rows[0] or any(type(v) is not int or v < 0 for v in rows[0].values()) or
                    any(not re.fullmatch('[a-z][a-z0-9_]{0,63}', k) for k in rows[0])):
                raise Blocked('failure_numeric_snapshot_required')
            index = len(self.events)
            self.query(connection, 'snapshot_rollback', 'ROLLBACK')
            return Snapshot(self.snapshot_token, rows[0], index)
        finally:
            connection.close()
            self.connections.remove(connection)

    def close(self):
        self.safety = True
        for connection in list(self.connections):
            try:
                self.query(connection, 'terminal_rollback', 'ROLLBACK')
            except BaseException as error:
                self.fail(error)
            try:
                connection.close()
                self.connections.remove(connection)
            except BaseException as error:
                self.fail(error)


class TimeoutDriver:
    """One actual PG17 driver-timeout component, not workflow/worker coverage."""
    def describe(self):
        return {'preparation_run': NEW_RUN, 'environment': 'disposable_ci',
                'reuse_existing_stack': True, 'historical_registry_read_only': True,
                'sources': [], 'cases': {'timeout': {'limit': 20, 'cleanup_reserve': 8,
                    'artifact_files': 0, 'artifact_bytes': 0}}}

    def run_case(self, case, session):
        connection = session.connect()
        session.timeout_backend = connection.info.backend_pid
        session.query(connection, 'timeout_begin', 'BEGIN TRANSACTION READ ONLY')
        row = session.query(connection, 'timeout_check', CHECK)
        if len(row) != 1 or set(row[0]) != {'pg17', 'bounded_statement', 'bounded_lock', 'readonly', 'tls'} or not all(v is True for v in row[0].values()):
            raise Blocked('failure_timeout_session_limits')
        session.step('timeout', lambda: session.query(connection, 'timeout', TIMEOUT_SQL))

    def cleanup(self, case, session):
        session.close()

    def observe(self, case, session):
        return session.snapshot('SELECT count(*)::integer remaining_case_backends '
                                'FROM pg_stat_activity WHERE pid = %s', [session.timeout_backend])


def cleanup_verified(cleanup):
    if cleanup is None:
        return True  # Drivers without an Auth bootstrap have only per-case cleanup.
    return (cleanup.get('close_error', cleanup.get('error')) is None and
            (cleanup.get('owned_auth_cleanup_required') is False or
             cleanup.get('all_component_owned_auth_zero') is True))


def run(gate, *, selection=None, diagnostic_only=False):
    """Main entry point. Missing real adapters block before native setup/mutation."""
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise Blocked('ci_only')
    names = ('integral-component-preflight.json', 'integral-component-matrix.json')
    claim = pathlib.Path(gate.out) / 'integral-component-claim.json'
    if claim.exists() or any((pathlib.Path(gate.out) / name).exists() for name in names):
        raise Blocked('failure_existing_evidence_preserved')
    driver = getattr(gate, 'integral_failure_driver', None)
    plan = preflight(gate, driver, selection, diagnostic_only)
    common = {'preparation_run': NEW_RUN, 'full_chain_admission': False, 'hosted_admission': False,
              'hosted_calls': 0, 'strict_wal': 'UNCHANGED_NOT_PROVEN_BY_COMPONENT',
              'historical_registry': 'READ_ONLY_REFERENCE', 'automatic_retry': False}
    if plan['ready']:
        # Exclusive even when Main prefixes gate.save. A crash never authorizes replay.
        with claim.open('x', encoding='ascii') as stream:
            json.dump({'preparation_run': NEW_RUN, 'selection': plan['selection'],
                       'source_binding_sha256': plan['source_binding_sha256'],
                       'released': False, 'full_chain_admission': False}, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
    gate.save(names[0], {**common, **plan})
    if not plan['ready']:
        return {**common, 'status': 'BLOCKED', 'missing_prerequisites': plan['missing'],
                'mutation_started': False, 'complete_failure_coverage': False}
    from native_runtime import NativeRuntime
    runtime = NativeRuntime.disposable(gate)
    if type(runtime) is not NativeRuntime or runtime.environment != 'disposable_ci':
        raise Blocked('failure_actual_loopback_runtime_required')
    deadline = time.monotonic() + LIMITS['matrix_seconds']
    reports = []
    bootstrap_failure = None
    driver_cleanup = None
    try:
        if callable(getattr(driver, 'open', None)):
            driver.deadline = deadline
            driver.open(runtime, plan['selection'])
        for case in plan['selection']:
            # No source drift between registration and the first case dispatch.
            if _source_binding(gate, driver, driver.describe()) != plan['sources']:
                raise Blocked('failure_sources_changed_after_preflight')
            session = Session(runtime, case, plan['cases'][case], deadline)
            observation = None
            try:
                driver.run_case(case, session)
            except BaseException as error:
                session.fail(error)
            finally:
                session.safety = True
                try:
                    driver.cleanup(case, session)
                except BaseException as error:
                    session.fail(error)
                session.close()
                try:
                    observation = driver.observe(case, session)
                    if type(observation) is not Snapshot or observation.owner is not session.snapshot_token:
                        raise Blocked('failure_independent_numeric_observation_required')
                except BaseException as error:
                    session.fail(error)
                    observation = None
                session.close()
            observed = session.injected and session.native_confirmed > 0 and observation is not None
            if session.connections or session.secondary:
                session.phase_semantics = False
            report = {**common, 'case': case, 'case_id': session.case_id,
                      'status': 'REAL_COMPONENT_BOUNDARY_OBSERVED' if observed else 'NO_GO',
                      'execution_status': 'NO_GO', 'primary_failure': session.primary,
                      'secondary_failures': session.secondary, 'fault_injected': session.injected,
                      'actual_dispatches': session.events, 'consumed': session.used,
                      'limit': session.spec['limit'], 'cleanup_reserved': session.spec['cleanup_reserve'],
                      'refunds': 0, 'unknown_outcome': session.unknown,
                      'remaining_claims': sorted(session.claims), 'claims_released': False,
                      'revocation_claim': False, 'numeric_snapshot': observation.values if observation else None,
                      'snapshot_is_not_cleanup_proof': True, 'writers_closed': not session.connections,
                      'source_binding_sha256': plan['source_binding_sha256'],
                      'component_phase_semantics_verified': getattr(session, 'phase_semantics', False),
                      'component_scope': 'rollback_isolated_native_and_separately_owned_real_auth',
                      'full_phase_semantics_verified': False,
                      'prefix_numeric_observations': getattr(session, 'prefix_samples', []),
                      'delegated_auth_units': getattr(session, 'delegated_auth', {}).get('prepaid_consumed', 0),
                      'delegated_native_dispatches': getattr(session, 'delegated_auth', {}).get('native_sql_dispatches', 0),
                      'delegated_managed_sql_observed': sum(getattr(session, 'delegated_auth', {}).get('observed_managed_sql', {}).values()),
                      'component_observation_is_not_full_failure_coverage': True}
            encoded = json.dumps(report, sort_keys=True, allow_nan=False).encode()
            if len(encoded) > RECEIPT_BYTES:
                raise Blocked('failure_component_receipt_capacity')
            gate.save('integral-component-' + case + '.json', report)
            reports.append(report)
            actual = inventory(gate.out)
            reserved = plan['artifacts']
            if (actual['files'] > reserved['before']['files'] + reserved['reserved_files'] or
                    actual['bytes'] > reserved['before']['bytes'] + reserved['reserved_bytes'] or
                    actual['largest'] > LIMITS['file_bytes']):
                raise Blocked('failure_artifact_reservation_exceeded')
            if time.monotonic() >= deadline:
                break
    except BaseException as error:
        bootstrap_failure = error_record(error)
    finally:
        if callable(getattr(driver, 'close', None)):
            try:
                driver_cleanup = driver.close()
            except BaseException as error:
                driver_cleanup = {'confirmed': False, 'error': error_record(error)}
        runtime.clear()
    cleanup_summary = None if driver_cleanup is None else {
        'receipt': 'integral-component-auth-cleanup.json', 'sha256': digest(driver_cleanup),
        'owned_auth_cleanup_required': driver_cleanup.get('owned_auth_cleanup_required', True),
        'all_component_owned_auth_zero': driver_cleanup.get('all_component_owned_auth_zero', False),
        'bootstrap_and_cleanup_units': driver_cleanup.get('bootstrap_and_cleanup_units', 0),
        'close_error': driver_cleanup.get('close_error', driver_cleanup.get('error'))}
    case_refs = [{'case': r['case'], 'receipt': 'integral-component-' + r['case'] + '.json',
                  'sha256': digest(r), 'component_phase_semantics_verified': r['component_phase_semantics_verified'],
                  'consumed': r['consumed'], 'delegated_auth_units': r['delegated_auth_units']} for r in reports]
    result = {**common, 'status': 'NO_GO_FAILURE_COVERAGE', 'cases': case_refs,
              'required': list(REQUIRED), 'observed_boundaries': [r['case'] for r in reports
                  if r['status'] == 'REAL_COMPONENT_BOUNDARY_OBSERVED'],
              'complete_failure_coverage': False,
              'component_covered': [r['case'] for r in reports if r['component_phase_semantics_verified']],
              'missing_component_phases': [x for x in REQUIRED if x not in
                  {r['case'] for r in reports if r['component_phase_semantics_verified']}],
              'missing_full_chain_semantics': ['strict_wal', 'registered_cli_migration',
                  'durable_endchain_request_pairs', 'all_prefix_2349', 'independent_review'],
              'bootstrap_or_runner_failure': bootstrap_failure, 'driver_cleanup': cleanup_summary,
              'diagnostic_subset_verified': len(reports) == len(plan['selection']) and bootstrap_failure is None and
                  all(r['component_phase_semantics_verified'] for r in reports) and cleanup_verified(driver_cleanup),
              'local_diagnostic_prepaid_units': sum(r['consumed'] + r['delegated_auth_units'] for r in reports)
                  + (driver_cleanup or {}).get('bootstrap_and_cleanup_units', 0),
              'local_native_dispatches': sum(sum(e['kind'] == 'sql' for e in r['actual_dispatches']) +
                  r['delegated_native_dispatches'] for r in reports) + (driver_cleanup or {}).get('bootstrap_native_dispatches', 0),
              'local_managed_sql_observed': sum(r['delegated_managed_sql_observed'] for r in reports) +
                  (driver_cleanup or {}).get('bootstrap_managed_sql_observed', 0),
              'global_2349_budget_proven': False,
              'source_binding_sha256': plan['source_binding_sha256']}
    gate.save(names[1], result)
    return result
