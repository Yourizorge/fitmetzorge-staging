"""Two CI-only components around ONE parent-owned clean M45 application.

Parent Gate.cli, only for phase=migration_45 and migration up --local:
    token = before(self)
    result = super().cli(*args, timeout=timeout)  # exactly once; exceptions propagate
    after(self, token, result)
    return result

The pre component terminates before its real dispatcher can be entered. The
parent's subsequent clean-build call is separate bootstrap work, not its retry.
The post component terminates after that confirmed bootstrap call. Neither is
a failed full-chain run, migration rollback, strict-WAL proof or admission.
No migration, fixture, Auth or quota mutation is issued by this module.
"""
import inspect
import json
import os
import pathlib
import re
import subprocess
import time

import integral_failure_runtime as rt
from admission_failure import secondary
from admission_binding import M45, PRESERVED, REPOSITORY, sha

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DISPATCHER = rt.PREFIX + 'admission_ci.py'
SOURCES = tuple(rt.PREFIX + x for x in (
    'migration_failure_boundaries.py', 'test_migration_failure_boundaries.py',
    'integral_failure_runtime.py', 'native_runtime.py', 'admission_binding.py',
    'admission_failure.py', 'ci_source_binding.py', 'sql_protocol.py')) + (
    M45, DISPATCHER)
CHECKOUT_HARNESS = ('_offline/phase6e11/ci41/runner.py',)
VERSION = pathlib.PurePosixPath(M45).name.split('_')[0]
NAMES = ('migration-boundary-claim.json', 'migration-boundary-pre.json',
         'migration-boundary-post.json')
SQL_LIMIT = 12  # Per hook: 8 normal commands, 4 reserved for failed-session closure.
RECEIPT_LIMIT = 65536
COUNTS = ('runs', 'windows', 'workspaces', 'identities', 'auth_users',
          'auth_sessions', 'auth_refresh_tokens')
COMMON = {'scope': 'actual_migration_boundary_component', 'full_chain_admission': False,
          'full_phase_semantics_verified': False, 'complete_failure_coverage': False,
          'strict_wal_proven': False, 'hosted_admission': False, 'hosted_calls': 0,
          'fixture_mutations': 0, 'migration_dispatches_by_helper': 0,
          'historical_binding': 'READ_ONLY_REFERENCE', 'automatic_retry': False,
          'terminal_complete': False, 'execution_status': 'NO_GO',
          'accounting_scope': 'local_diagnostic_separate_from_planned_2349'}
METADATA = """select
 (select coalesce(jsonb_agg(version order by version),'[]'::jsonb)
  from supabase_migrations.schema_migrations) history,
 (select count(*)::integer from fmz6e11_controller_private.runs) runs,
 (select count(*)::integer from fmz6e11_private.windows) windows,
 (select count(*)::integer from fmz6e11_private.workspaces) workspaces,
 (select count(*)::integer from fmz6e11_private.identities) identities,
 (select count(*)::integer from auth.users) auth_users,
 (select count(*)::integer from auth.sessions) auth_sessions,
 (select count(*)::integer from auth.refresh_tokens) auth_refresh_tokens,
 (select encode(sha256(convert_to(prosrc,'UTF8')),'hex') from pg_proc
  where oid=to_regprocedure('fmz6e11_controller_private.single_endchain_receipt()')) m44_function,
 (select encode(sha256(convert_to(prosrc,'UTF8')),'hex') from pg_proc
  where oid=to_regprocedure('fmz6e11_controller_private.recovery_run_receipt()')) m45_function,
 (select encode(sha256(convert_to(pg_get_triggerdef(oid),'UTF8')),'hex') from pg_trigger
  where tgrelid='fmz6e11_controller_private.runs'::regclass and tgname='recovery_run_receipt') m45_trigger,
 (select encode(sha256(convert_to(pg_get_constraintdef(oid),'UTF8')),'hex') from pg_constraint
  where conrelid='fmz6e11_controller_private.runs'::regclass
   and conname='runs_command_count_check') quota_constraint
"""


class Boundary:
    def __init__(self, gate, binding, history):
        self.gate, self.binding, self.history = gate, binding, history
        self.serial = gate.serial
        self.sample = None
        self.consumed = False


def byte_binding(checkout, candidate, expected, *, historical):
    # Same sole canonicalization as ci_source_binding; candidate raw stays pinned.
    checkout_lf = checkout.replace(b'\r\n', b'\n')
    candidate_lf = candidate.replace(b'\r\n', b'\n')
    if sha(candidate) != expected or (checkout_lf != candidate_lf if historical else checkout != candidate):
        raise rt.Blocked('migration_boundary_source_changed')
    return {'candidate_sha256': expected, 'checkout_sha256': sha(checkout),
            'candidate_lf_sha256': sha(candidate_lf), 'checkout_lf_sha256': sha(checkout_lf),
            'canonicalization': 'CRLF-to-LF-only' if historical else 'byte-exact'}


def harness_binding(checkout):
    from ci_source_binding import HARNESS
    found = {}
    for name in CHECKOUT_HARNESS:
        path = checkout / name
        if (path.is_symlink() or not path.resolve().is_relative_to(checkout) or not path.is_file()):
            raise rt.Blocked('migration_boundary_checkout_harness_missing')
        raw = path.read_bytes()
        canonical_sha = sha(raw.replace(b'\r\n', b'\n'))
        if canonical_sha != HARNESS.get(name):
            raise rt.Blocked('migration_boundary_checkout_harness_changed')
        found[name] = {'checkout_sha256': sha(raw), 'lf_sha256': canonical_sha,
                       'distribution': 'pinned_checkout_harness', 'candidate_required': False}
    return found


def binding(gate):
    if (os.environ.get('GITHUB_ACTIONS') != 'true' or
            os.environ.get('GITHUB_REPOSITORY') != REPOSITORY or
            os.environ.get('GITHUB_REF') != 'refs/heads/main' or
            not re.fullmatch('[a-f0-9]{40}', os.environ.get('GITHUB_SHA', '')) or
            not re.fullmatch('[1-9][0-9]*', os.environ.get('GITHUB_RUN_ID', ''))):
        raise rt.Blocked('migration_boundary_ci_only')
    if (os.environ.get('PGHOSTADDR', '127.0.0.1') != '127.0.0.1' or
            os.environ.get('PGSERVICE') or os.environ.get('PGSERVICEFILE')):
        raise rt.Blocked('migration_boundary_remote_override')
    if gate.result.get('phase') != 'migration_45' or gate.result.get('migrations_applied') != 44:
        raise rt.Blocked('migration_boundary_clean44_only')
    candidate = json.loads((pathlib.Path(gate.out) / 'candidate.json').read_text())
    if not re.fullmatch('[a-f0-9]{64}', str(candidate.get('sha256', ''))):
        raise rt.Blocked('migration_boundary_candidate_identity')
    workspace = os.environ.get('GITHUB_WORKSPACE')
    if not workspace or not pathlib.Path(workspace).is_absolute():
        raise rt.Blocked('migration_boundary_checkout_root')
    checkout = pathlib.Path(workspace).resolve()
    candidate_root = pathlib.Path(gate.sources).resolve()
    if ROOT.resolve() not in (checkout, candidate_root):
        raise rt.Blocked('migration_boundary_helper_source')
    # The entry Gate stays in checkout; install() puts candidate modules first.
    source = inspect.getsourcefile(gate.cli)
    source_path = pathlib.Path(source) if source else None
    if source_path is not None and not source_path.is_absolute():
        source_path = checkout / source_path
    if (not inspect.ismethod(gate.cli) or source_path is None or
            source_path.resolve() != (checkout / DISPATCHER).resolve()):
        raise rt.Blocked('migration_boundary_dispatcher_source')
    names = set(SOURCES)
    migrations = sorted(n for n in candidate['sources'] if n.startswith('supabase/migrations/'))
    if len(migrations) != 45 or migrations[-1] != M45:
        raise rt.Blocked('migration_boundary_canonical45')
    names.update(migrations)
    hashes, byte_hashes = {}, {}
    historical = set(migrations[:-1])
    for name in sorted(names):
        expected = candidate['sources'].get(name)
        if not isinstance(expected, str) or not re.fullmatch('[a-f0-9]{64}', expected):
            raise rt.Blocked('migration_boundary_source_missing')
        raw = []
        for root in (checkout, candidate_root):
            path = root / name
            if (path.is_symlink() or not path.resolve().is_relative_to(root) or
                    not path.is_file()):
                raise rt.Blocked('migration_boundary_source_changed')
            raw.append(path.read_bytes())
        byte_hashes[name] = byte_binding(raw[0], raw[1], expected, historical=name in historical)
        hashes[name] = expected
    mirror = pathlib.Path(gate.work) / M45
    if hashes[M45] != PRESERVED[M45] or mirror.is_symlink() or sha(mirror.read_bytes()) != hashes[M45]:
        raise rt.Blocked('migration_boundary_m45_preservation')
    versions = [pathlib.PurePosixPath(n).name.split('_')[0] for n in migrations]
    if len(set(versions)) != 45:
        raise rt.Blocked('migration_boundary_history_identity')
    return {'source_commit': os.environ['GITHUB_SHA'], 'ci_run': os.environ['GITHUB_RUN_ID'],
            'candidate_sha256': candidate['sha256'], 'sources': hashes,
            'checkout_harness': harness_binding(checkout),
            'loaded_locations': {'dispatcher': 'checkout',
                'boundary_helper': 'checkout' if ROOT.resolve() == checkout else 'candidate'},
            'source_bytes': byte_hashes}, versions


def save(gate, name, value):
    raw = json.dumps(value, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'
    if len(raw) > RECEIPT_LIMIT or (pathlib.Path(gate.out) / name).exists():
        raise rt.Blocked('migration_boundary_receipt_capacity_or_replay')
    usage = rt.inventory(gate.out)
    if (usage['files'] + 1 > rt.LIMITS['files'] or
            usage['bytes'] + len(raw) > rt.LIMITS['bytes']):
        raise rt.Blocked('migration_boundary_artifact_capacity')
    gate.save(name, value)


def snapshot(session):
    connection = session.connect()
    rolled_back = False
    try:
        session.query(connection, 'boundary_begin', 'BEGIN TRANSACTION READ ONLY')
        guard = session.query(connection, 'boundary_readonly_tls', rt.CHECK)
        if (len(guard) != 1 or set(guard[0]) != {'pg17', 'bounded_statement', 'bounded_lock', 'readonly', 'tls'} or
                not all(x is True for x in guard[0].values())):
            raise rt.Blocked('migration_boundary_readonly_tls_limits')
        rows = session.query(connection, 'boundary_metadata', METADATA)
        if len(rows) != 1:
            raise rt.Blocked('migration_boundary_metadata_shape')
        sample = rows[0]
        if set(sample) != set(COUNTS) | {'history', 'm44_function', 'm45_function', 'm45_trigger', 'quota_constraint'}:
            raise rt.Blocked('migration_boundary_metadata_shape')
        if any(type(sample[k]) is not int or sample[k] != 0 for k in COUNTS):
            raise rt.Blocked('migration_boundary_requires_empty_fixture_and_controller_registry')
        if not isinstance(sample['history'], list) or any(not isinstance(x, str) for x in sample['history']):
            raise rt.Blocked('migration_boundary_history_shape')
        for key in ('m44_function', 'm45_function', 'm45_trigger', 'quota_constraint'):
            if sample[key] is not None and not re.fullmatch('[a-f0-9]{64}', sample[key]):
                raise rt.Blocked('migration_boundary_object_hash')
        session.query(connection, 'boundary_rollback', 'ROLLBACK')
        rolled_back = True
        return sample
    finally:
        # Failed commands are rolled back by session.close, preserving their charge/error.
        if rolled_back:
            connection.close()
            session.connections.remove(connection)


def compact(sample):
    return {**{k: v for k, v in sample.items() if k != 'history'},
            'history_count': len(sample['history']), 'history_sha256': rt.digest(sample['history'])}


def reject_before_dispatch(dispatcher):
    """The injected exception is before the actual bound dispatcher invocation."""
    def deny():
        raise rt.InjectedFailure('migration_boundary_pre_dispatch')
    deny()
    return dispatcher('migration', 'up', '--local')  # Unreachable, including on lost reply.


def native_session(gate, case):
    from native_runtime import NativeRuntime
    runtime = NativeRuntime.disposable(gate)
    if type(runtime) is not NativeRuntime or runtime.environment != 'disposable_ci':
        raise rt.Blocked('migration_boundary_actual_loopback_required')
    return runtime, rt.Session(runtime, case, {'limit': SQL_LIMIT, 'cleanup_reserve': 4},
                               time.monotonic() + rt.LIMITS['matrix_seconds'])


def observed(gate, token, case, operation, name):
    runtime, session = native_session(gate, case)
    verified, detail = False, {}
    primary = None
    try:
        detail = operation(session)
        verified = True
    except BaseException as error:
        primary = error
        session.fail(error)
        raise
    finally:
        session.close()
        runtime.clear()
        report = {**COMMON, 'phase': case, 'case_id': session.case_id,
                  'source_binding': token.binding, 'source_binding_sha256': rt.digest(token.binding),
                  'component_verified': verified and not session.connections and not session.secondary,
                  'original_failure': session.primary, 'secondary_failures': session.secondary,
                  'unknown_outcome': session.unknown, 'read_only_dispatches': session.events,
                  'local_diagnostic_commands': session.used, 'command_limit': SQL_LIMIT,
                  'cleanup_reserve': 4, 'refunds': 0, 'reader_connections_closed': not session.connections,
                  **detail}
        # Evidence failure never replaces an existing database/validation exception.
        try:
            save(gate, name, report)
        except BaseException as error:
            secondary(gate, case + '_receipt_storage', error, primary)
            if primary is None:
                raise
        if verified and (session.connections or session.secondary):
            raise rt.Blocked('migration_boundary_reader_close_failed')
    return report


def before(gate):
    source, history = binding(gate)
    if hasattr(gate, '_migration_failure_boundary') or any((pathlib.Path(gate.out) / n).exists() for n in NAMES):
        raise rt.Blocked('migration_boundary_once_only')
    usage = rt.inventory(gate.out)
    if usage['files'] + 3 > rt.LIMITS['files'] or usage['bytes'] + 3 * RECEIPT_LIMIT > rt.LIMITS['bytes']:
        raise rt.Blocked('migration_boundary_artifact_reservation')
    token = Boundary(gate, source, history)
    gate._migration_failure_boundary = token
    save(gate, NAMES[0], {**COMMON, 'source_binding_sha256': rt.digest(source),
                         'reserved_files': 3, 'reserved_bytes': 3 * RECEIPT_LIMIT,
                         'normal_diagnostic_sql_commands': 16, 'maximum_diagnostic_sql_commands': 24})
    def operation(session):
        start = snapshot(session)
        if (start['history'] != history[:-1] or start['m45_function'] is not None or
                start['m45_trigger'] is not None or start['m44_function'] is None or
                start['quota_constraint'] is None):
            raise rt.Blocked('migration_boundary_not_before_m45')
        serial = gate.serial
        try:
            reject_before_dispatch(gate.cli)
        except rt.InjectedFailure as error:
            session.fail(error)
        else:
            raise rt.Blocked('migration_boundary_pre_fault_not_observed')
        session.safety = True
        end = snapshot(session)
        if gate.serial != serial or start != end:
            raise rt.Blocked('migration_boundary_predispatch_changed_state')
        token.sample = start
        return {'before': compact(start), 'after_failure': compact(end), 'dispatcher_called': False,
                'dispatcher_command_count_delta': gate.serial - serial, 'safe_closure_no_fixtures': True}
    observed(gate, token, 'pre_migration', operation, NAMES[1])
    return token


def confirmed_result(gate, token, result):
    expected = [str(gate.binary), '--workdir', str(gate.work), 'migration', 'up', '--local']
    if (type(result) is not subprocess.CompletedProcess or type(result.returncode) is not int or
            result.returncode != 0 or result.args != expected or gate.serial != token.serial + 1):
        raise rt.Blocked('migration_boundary_unconfirmed_or_extra_cli_dispatch')
    if any(not isinstance(x, str) or len(x.encode()) > 2000000 for x in (result.stdout, result.stderr)):
        raise rt.Blocked('migration_boundary_cli_output_bound')
    path = pathlib.Path(gate.out) / ('%03d-cli-migration.json' % gate.serial)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2000000:
        raise rt.Blocked('migration_boundary_cli_receipt_missing')
    raw = path.read_bytes()
    receipt = json.loads(raw)
    if receipt.get('phase') != 'migration_45' or type(receipt.get('exitcode')) is not int or receipt['exitcode'] != 0:
        raise rt.Blocked('migration_boundary_cli_receipt_unconfirmed')
    return {'receipt': path.name, 'receipt_sha256': sha(raw), 'returncode': 0,
            'command_sha256': rt.digest(expected), 'stdout_sha256': sha(result.stdout.encode()),
            'stderr_sha256': sha(result.stderr.encode()), 'parent_bootstrap_dispatches': 1}


def after(gate, token, result):
    if (type(token) is not Boundary or token.gate is not gate or token.consumed or
            getattr(gate, '_migration_failure_boundary', None) is not token or token.sample is None):
        raise rt.Blocked('migration_boundary_invalid_or_consumed_token')
    token.consumed = True  # Unknown/nonzero results cannot be retried into coverage.
    try:
        source, history = binding(gate)
        if source != token.binding or history != token.history:
            raise rt.Blocked('migration_boundary_source_changed_between_hooks')
        confirmation = confirmed_result(gate, token, result)
    except BaseException as error:
        try:
            save(gate, NAMES[2], {**COMMON, 'phase': 'post_migration', 'component_verified': False,
                'original_failure': rt.error_record(error), 'unknown_outcome': True,
                'source_binding_sha256': rt.digest(token.binding), 'local_diagnostic_commands': 0,
                'migration_result_confirmed': False, 'safe_closure_no_fixtures': False})
        except BaseException as save_error:
            secondary(gate, 'post_migration_receipt_storage', save_error, error)
        raise
    def operation(session):
        start = snapshot(session)
        if (start['history'] != history or start['m45_function'] is None or start['m45_trigger'] is None or
                start['quota_constraint'] is None or start['quota_constraint'] == token.sample['quota_constraint'] or
                start['m44_function'] != token.sample['m44_function']):
            raise rt.Blocked('migration_boundary_m45_result_not_observed')
        try:
            raise rt.InjectedFailure('migration_boundary_post_confirmed')
        except rt.InjectedFailure as error:
            session.fail(error)
        session.safety = True
        end = snapshot(session)
        if start != end:
            raise rt.Blocked('migration_boundary_post_failure_changed_state')
        return {'before': compact(token.sample), 'after_m45': compact(start), 'after_failure': compact(end),
                'actual_migration_result': confirmation, 'safe_closure_no_fixtures': True,
                'migration_rollback_claim': False}
    return observed(gate, token, 'post_migration', operation, NAMES[2])
