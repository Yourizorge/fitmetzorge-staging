"""Eleven real Auth fault cases inside an already-owned disposable CI stack.

The parent owns clean47, server start/stop and its bootstrap actors. This module
never starts a server, removes parent actors, dispatches CI or admits endchain.
Run in a fresh source-verified Python process, not through artifact imports.
"""
import hashlib
import json
import os
import pathlib
import re
import sys
import uuid

import admission_case_archive as archive
import admission_module_binding as module_binding
import auth_failure as engine
import auth_failure_tracked as tracked
import auth_failure_transport as transport
import auth_protocol

PREFIX = '_offline/phase6e11/endchain_v1/'
SOURCES = tuple(PREFIX + name for name in (
    'pg_auth_component/__init__.py', 'pg_auth_component/runner.py',
    'pg_auth_component/test_runner.py', 'auth_failure.py',
    'auth_failure_tracked.py', 'auth_failure_transport.py', 'auth_protocol.py',
    'admission_module_binding.py', 'admission_case_archive.py'))
CASES = ('before_dispatch', 'create_lost_reply', 'partial_user', 'partial_session',
         'login_timeout', 'logout_timeout', 'admin_unknown', 'duplicate_request',
         'cleanup_interrupted', 'missing_mint_barrier', 'duplicate_cleanup')
ATTEST = "SELECT current_setting('server_version_num')::int version, ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()"


def require(value, code):
    if not value:
        raise ValueError('pg_auth_component_' + code)


def preflight(gate, ctx, run_id):
    """No SQL/HTTP; private context values are never returned or serialized."""
    from psycopg.conninfo import conninfo_to_dict
    require(sys.platform == 'linux' and os.environ.get('GITHUB_ACTIONS') == 'true'
            and os.environ.get('GITHUB_REPOSITORY') == 'Yourizorge/fitmetzorge-staging', 'ci_linux_only')
    require(re.fullmatch('[a-f0-9]{40}', os.environ.get('GITHUB_SHA', ''))
            and re.fullmatch('[1-9][0-9]*', os.environ.get('GITHUB_RUN_ID', '')), 'ci_identity')
    require(str(uuid.UUID(run_id)) == run_id and run_id != engine.OLD_RUN, 'fresh_uuid')
    require(not hasattr(gate, 'auth_failure_context'), 'context_already_owned')
    require(not (pathlib.Path(gate.out) / ('auth_failure_' + run_id)).exists(), 'no_retry')
    require(not (pathlib.Path(gate.out) / 'component-request-private').exists(), 'no_registry_retry')
    require(not any((pathlib.Path(gate.out) / name).exists() for name in (
        'case-original-index.json', 'auth-failure-component.json', 'pg-auth-component-result.json')), 'output_collision')
    require(ctx.get('test_admin_token') and ctx['auth'].url == 'http://127.0.0.1:59999', 'private_context')
    params = conninfo_to_dict(ctx['dsn'])
    ca = pathlib.Path(gate.work) / 'fmz-ci-ca.crt'
    require(ca.is_file() and not ca.is_symlink()
            and pathlib.Path(params.get('sslrootcert', '')).resolve(strict=True) == ca.resolve(strict=True), 'ca')
    require(params.get('host') == '127.0.0.1' and params.get('hostaddr', '127.0.0.1') == '127.0.0.1'
            and params.get('dbname') == 'postgres' and params.get('sslmode') == 'verify-full'
            and not any(k in params for k in ('service', 'servicefile'))
            and not any(os.environ.get(k) for k in ('PGSERVICE', 'PGSERVICEFILE'))
            and os.environ.get('PGHOSTADDR', '127.0.0.1') == '127.0.0.1', 'local_tls')
    require(tuple(engine.CASES) == CASES and engine.contract(dict.fromkeys(engine.OPERATIONS, 128))['reserved_units'] == 524,
            'engine_contract')
    return module_binding.verify(gate, [sys.modules[__name__], engine, tracked,
                                        transport, auth_protocol, archive, module_binding])


def checked_report(report):
    require(isinstance(report, dict) and report.get('status') == 'LOCAL_AUTH_FAILURE_COMPONENT_PASS', 'cases_incomplete')
    require(tuple(row.get('case') for row in report.get('cases', ())) == CASES, 'case_set')
    require(all(row.get('component_case_pass') is True for row in report['cases']), 'case_failed')
    require(report.get('full_chain_admission') is False and report.get('global_auth_zero_claim') is False
            and report.get('full_auth_cleanup_proven') is False, 'overclaim')
    require(report['diagnostic_totals'].get('all_managed_observations_complete') is True, 'numeric_incomplete')


def originals(gate, registry, report):
    """Only enumerated sanitized journals; no blind recursion/private context."""
    root = pathlib.Path(gate.out)
    refs = {}
    def add(relative, expected, size):
        path = pathlib.PurePosixPath(relative)
        require(not path.is_absolute() and '..' not in path.parts and '\\' not in relative, 'original_path')
        file = root.joinpath(*path.parts)
        require(all(not part.is_symlink() for part in (file, *file.parents))
                and file.resolve(strict=True).is_relative_to(root.resolve(strict=True)), 'original_link')
        raw = file.read_bytes()
        require(len(raw) == size and hashlib.sha256(raw).hexdigest() == expected, 'original_hash')
        ref = {'path': relative, 'sha256': expected, 'bytes': size}
        require(relative not in refs or refs[relative] == ref, 'original_conflict')
        refs[relative] = ref
    for records in registry._recordsets:
        for name, raw in records.validate().items():
            add((records.folder / name).relative_to(root).as_posix(), records._hashes[name], len(raw))
    if report is not None:
        raw = (root / 'auth-failure-component.json').read_bytes()
        require(json.loads(raw) == report, 'engine_original_changed')
        add('auth-failure-component.json', hashlib.sha256(raw).hexdigest(), len(raw))
        for rows, suffix in ((report['cases'], ''), (report['safety_reconciliations'], '/safety-reconciliation')):
            for row in rows:
                require(row['case'] in CASES, 'original_case')
                folder = 'auth_failure_' + report['preparation_run_id'] + '/' + row['case'] + suffix
                for name, ref in row.get('retained_journal', {}).get('files', {}).items():
                    require(pathlib.PurePosixPath(name).name == name and name.endswith('.json'), 'original_name')
                    add(folder + '/' + name, ref['sha256'], ref['bytes'])
    return [refs[k] for k in sorted(refs)]


def run(gate, ctx, *, run_id):
    """Call within the parent's actual ci_auth.environment lifetime, once."""
    source = preflight(gate, ctx, run_id)
    # One explicit local bootstrap observation, not charged to hosted 2349.
    observed = ctx['admin'].execute(ATTEST).fetchone()
    require(type(observed.get('version')) is int and observed['version'] // 10000 == 17
            and observed.get('ssl') is True, 'pg17_tls_observation')
    registry = tracked.Registry(pathlib.Path(gate.out) / 'component-request-private', run_id=run_id)
    report = primary = None
    closed = False
    gate.auth_failure_context = engine.context_from_ci(ctx, run_id=run_id,
        managed_costs=dict.fromkeys(engine.OPERATIONS, 128), exclusive_local_auth=True)
    try:
        report = engine.run(gate, safety_reconciliation=False,
                            transport_factory=registry.case_transport_factory)
        checked_report(report)
    except BaseException as error:
        primary = error
        raise
    finally:
        del gate.auth_failure_context
        try:
            proof = registry.close_and_drain()
            closed = registry.valid_proof(proof)
            require(closed, 'request_drain')
        except BaseException as error:
            if primary is None:
                primary = error
            else:
                primary.add_note('component_drain_secondary:' + type(error).__name__)
        try:
            refs = originals(gate, registry, report)
            require(len(refs) <= 1024 and sum(ref['bytes'] for ref in refs) <= 8_000_000,
                    'component_artifact_bound')
            result = {'status': 'LOCAL_AUTH_COMPONENT_RECORDED' if primary is None and closed else 'NO_GO',
                'scope': 'eleven_actual_auth_faults_not_fullmatrix', 'run_id': run_id,
                'source_commit': os.environ['GITHUB_SHA'], 'ci_run': os.environ['GITHUB_RUN_ID'],
                'source_binding': source, 'pg17_tls_observed': True,
                'local_bootstrap_observation_commands': 1,
                'engine_contract': engine.contract(dict.fromkeys(engine.OPERATIONS, 128)),
                'declared_local_case_capacity': 11 * 524, 'managed_costs_proven': False,
                'registered_requests_closed': closed, 'server_quiescence_proven': False,
                'original_refs_complete': report is not None, 'original_refs': refs,
                'original_archive_ref': archive.pack(gate, refs),
                'original_error_class': type(primary).__name__ if primary else None,
                'retained_claims': report['retained_claims'] if report else None,
                'safety_reconciliation_attempted': False, 'parent_cleanup_authorized': False,
                'unknown_outcomes_reclassified': False, 'worker_exit_coverage': False,
                'global_auth_zero_claim': False, 'full_auth_cleanup_proven': False,
                'full_chain_admission': False, 'hosted_admitted': False,
                'planned_2349_run_changed': False, 'wal_diagnostic_executed': False,
                'strict_wal_admission_checked': False}
            gate.save('pg-auth-component-result.json', result)
        except BaseException as secondary:
            if primary is None:
                raise
            primary.add_note('component_export_secondary:' + type(secondary).__name__)
        if primary is not None and sys.exc_info()[0] is None:
            raise primary
    return result
