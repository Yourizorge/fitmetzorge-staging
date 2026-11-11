"""Actual disposable PG worker observations, not fullchain worker substitutes."""
import hashlib
import json
import os
import pathlib
import subprocess
import sys

import admission_module_binding as module_binding
from quota_candidate_v1 import compiler
from quota_candidate_v1 import runtime_worker_evidence as evidence
from . import pg_worker
from .runner import preflight, require

SOURCES = tuple('_offline/phase6e11/endchain_v1/' + name for name in (
    'pg_auth_component/worker.py', 'pg_auth_component/pg_worker.py',
    'pg_auth_component/test_worker.py', 'quota_candidate_v1/runtime_worker_evidence.py',
    'quota_candidate_v1/compiler.py', 'quota_candidate_v1/__init__.py',
    'admission_binding.py', 'admission_quota_readonly.py', 'sql_protocol.py'))
FIELDS = {'case', 'pg17_tls_readonly', 'query_confirmed', 'sqlstate', 'rollback_confirmed',
          'explicit_commands', 'connection_closed', 'libpq_version',
          'implicit_native_sql_bound', 'full_chain_admission'}


def child_environment(environ):
    """Closed allowlist: no credentials, PG settings, Python or loader overrides."""
    result = {key: environ[key] for key in (
        'GITHUB_ACTIONS', 'GITHUB_REPOSITORY', 'GITHUB_SHA', 'GITHUB_RUN_ID')}
    result.update(PATH='/usr/bin:/bin', LANG='C.UTF-8', LC_ALL='C.UTF-8')
    return result


def checked_result(raw, case):
    require(type(raw) is bytes and len(raw) <= 4096, 'worker_result_bound')
    if case == 'lost_result':
        require(raw == b'', 'worker_lost_result_not_lost')
        return None
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'worker_duplicate_key')
            result[key] = value
        return result
    result = json.loads(raw, object_pairs_hook=unique)
    require(type(result) is dict and set(result) == FIELDS, 'worker_result_fields')
    require(raw == compiler.canonical(result), 'worker_original_bytes')
    require(result['case'] == case and result['pg17_tls_readonly'] is True
            and result['rollback_confirmed'] is True and result['connection_closed'] is True
            and type(result['explicit_commands']) is int and result['explicit_commands'] == 4
            and type(result['libpq_version']) is int and result['libpq_version'] > 0
            and result['implicit_native_sql_bound'] is None and result['full_chain_admission'] is False,
            'worker_result_observation')
    require((case == 'readonly' and result['query_confirmed'] is True and result['sqlstate'] is None)
            or (case == 'statement_timeout' and result['query_confirmed'] is False and result['sqlstate'] == '57014'),
            'worker_result_case')
    return result


def run(gate, ctx, *, run_id):
    source = preflight(gate, ctx, run_id)
    bound = module_binding.verify(gate, [sys.modules[__name__], pg_worker, evidence,
        compiler, compiler.binding, compiler.baseline, compiler.protocol])
    child = pathlib.Path(pg_worker.__file__).resolve(strict=True)
    child_sha = hashlib.sha256(child.read_bytes()).hexdigest()
    require(not any((pathlib.Path(gate.out) / ('pg-worker-' + case.replace('_','-') + '-wait.json')).exists()
                    for case in pg_worker.CASES), 'worker_no_retry')
    binding = {'run_id': run_id, 'source_commit': os.environ['GITHUB_SHA'],
               'ci_run': os.environ['GITHUB_RUN_ID'], 'scope': 'readonly_pg_component',
               'child_sha256': child_sha}
    cases = []; refs = []
    for case in pg_worker.CASES:
        label = case.replace('_', '-')
        observed = evidence.WaitEvidence(binding, case, 'workflow')
        primary = None; raw = b''; result_ref = None
        try:
            process = subprocess.Popen([sys.executable, '-I', '-B', str(child)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                env=child_environment(os.environ))
            observed.attach(process)
            private = (json.dumps({'dsn': ctx['dsn'], 'case': case}) + '\n').encode('utf8')
            try:
                raw, _ = process.communicate(input=private, timeout=15)
            except subprocess.TimeoutExpired as error:
                observed.wait_error = type(error).__name__
                observed.event('wait_error', exception_class=type(error).__name__)
                raise
            finally:
                private = None
            observed.wait()
            require(observed.known and observed.returncode == 0, 'worker_exit')
            result = checked_result(raw, case)
            if result is not None:
                # Persist the exact child JSON payload, with no reconstructed completion.
                result_ref = evidence.save(gate, 'pg-worker-' + label + '-result.json', result)
                refs.append(result_ref)
        except BaseException as error:
            primary = error
            raise
        finally:
            observed.close()
            try:
                wait_ref = evidence.save(gate, 'pg-worker-' + label + '-wait.json', observed.receipt())
                refs.append(wait_ref)
                record = {'case': case, 'binding': binding, 'wait_ref': wait_ref, 'result_ref': result_ref,
                    'result_received': bool(raw), 'result_validated': result_ref is not None,
                    'producer_reaped': observed.reaped, 'worker_known': observed.known,
                    'original_error_class': type(primary).__name__ if primary else None,
                    'lost_result_remains_no_go': case == 'lost_result',
                    'cleanup_authorized': False, 'full_chain_admission': False, 'hosted_admitted': False}
                refs.append(evidence.save(gate, 'pg-worker-' + label + '-export.json', record))
                cases.append(record)
            except BaseException as secondary:
                if primary is None: raise
                primary.add_note('component_worker_export_secondary:' + type(secondary).__name__)
            if primary is None:
                require(observed.known and observed.reaped, 'worker_stop_unknown')
        # No actor/object cleanup is present in this module, even after a known exit.
    receipt = {'status': 'READONLY_PG_WORKER_COMPONENT_RECORDED', 'binding': binding,
        'source_binding': [source, bound], 'cases': cases, 'original_refs': refs,
        'explicit_sql_capacity': 12, 'implicit_native_sql_bound': None,
        'lost_result_execution_unproven': True, 'original_unknown_retained': True,
        'actual_fullchain_worker': False, 'full_chain_admission': False,
        'hosted_admitted': False, 'wal_diagnostic_executed': False,
        'strict_wal_admission_checked': False}
    evidence.save(gate, 'pg-worker-component-result.json', receipt)
    return receipt
