"""Additional eleven-case local diagnostic, never a substitute for phase cases.

Reuse the actual source-admitted Context/server, without parent bootstrap users
or a fixture. Every case keeps its original ownership, reserve and NO_GO claims.
Main owns the separate clean47 job, source packaging and CI dispatch.
"""
import copy
import inspect
import json
import pathlib
import sys

import auth_failure as engine
import auth_failure_tracked as tracked
import admission_module_binding as binding
import admission_case_archive as archive
from . import runtime_registered_bootstrap as bootstrap
from . import runtime_registered_costs as costs
from . import runtime_auth_failure_witness as witness

CASES = ('before_dispatch', 'create_lost_reply', 'partial_user', 'partial_session',
         'login_timeout', 'logout_timeout', 'admin_unknown', 'duplicate_request',
         'cleanup_interrupted', 'missing_mint_barrier', 'duplicate_cleanup')
SOURCES = ('quota_candidate_v1/runtime_auth_failure_component.py',
           'quota_candidate_v1/runtime_auth_failure_witness.py',
           'quota_candidate_v1/runtime_registered_bootstrap.py',
           'quota_candidate_v1/runtime_registered_startup.py',
           'quota_candidate_v1/runtime_registered_costs.py',
           'quota_candidate_v1/runtime_registered_cleanup.py',
           'auth_failure.py', 'auth_failure_transport.py', 'auth_failure_tracked.py',
           'auth_protocol.py', 'native_runtime.py', 'admission_module_binding.py',
           'admission_budget_root_runtime.py', 'admission_auth_runtime_profile.py',
           'admission_case_archive.py', 'quota_candidate_v1/runtime_auth_failure_verify.py')


def require(value, code):
    if not value:
        raise ValueError('auth_component_' + code)


def command_register():
    plan = engine.contract(dict.fromkeys(engine.OPERATIONS, 128))
    require(engine.CASES == CASES and plan['reserved_units'] == 524,
            'case_contract_changed')
    return {'scope': 'LOCAL_DIAGNOSTIC_ONLY', 'envelope': 'case.auth.failures',
        'command_id': 'auth.failure_component', 'cases': list(CASES),
        'per_case': plan, 'declared_local_capacity': len(CASES) * plan['reserved_units'],
        'native_sql_capacity': len(CASES) * plan['native_sql_maximum'] + 6,
        'reconciliation_native_capacity': 6,
        'http_capacity': len(CASES) * plan['http_dispatch_maximum'] + 1,
        'reconciliation': 'draws unused original per-case capacity; no second allowance',
        'connections': {'open': 1, 'close': 1, 'implicit_sql_guard': 'native_proof'},
        'parent_bootstrap_http': 0, 'parent_bootstrap_sql': 0,
        'startup_profile_stop': 'separate registered LocalServer source program',
        'covered_managed_group': 'auth.managed_lifetime',
        'managed_costs_proven': False, 'hosted_units': 0,
        'planned_2349_run_changed': False, 'full_chain_admission': False}


def execute(context):
    frame = inspect.currentframe().f_back
    require(frame.f_code is bootstrap.Context.run_auth_failures.__code__
            and frame.f_locals.get('self') is context, 'actual_context_caller')
    del frame
    require(type(context) is bootstrap.Context and context._diagnostic_mode
            and context._admitted and not context._closing and not context._seed_attempted
            and context.producer is None and context.auth is None and context.ids is None,
            'no_parent_or_fixture')
    context._validate()
    binding.verify(context.gate, [sys.modules[__name__], engine, tracked, costs, witness, archive])
    command_register()
    from psycopg.conninfo import conninfo_to_dict
    costs.native_proof(conninfo_to_dict(context.server.dsn))
    registry = tracked.Registry(pathlib.Path(context.gate.out) / 'auth-failure-request-private',
                                run_id=context.binding['run_id'])
    context._diagnostic_registry = registry
    context._diagnostic_witness = witness.Witnesses(context.gate.out)
    gate = context.gate
    require(not hasattr(gate, 'auth_failure_context'), 'private_context_already_present')
    gate.auth_failure_context = {'dsn': context.server.dsn,
        'auth_url': bootstrap.ORIGIN, 'admin_token': context.server.admin,
        'api_key': context.server.anon, 'run_id': context.binding['run_id'],
        'environment': 'disposable_ci', 'exclusive_local_auth': True,
        'managed_costs': dict.fromkeys(engine.OPERATIONS, 128)}
    ledger = context.execution_ledger
    ticket = None
    try:
        ticket = ledger.precharge('auth.failure_component')
        report = engine.run(gate, safety_reconciliation=True,
                            transport_factory=registry.case_transport_factory,
                            read_witness=context._diagnostic_witness.record)
        # The engine has already published its immutable result. Keep that
        # result even if validation or the enclosing ledger subsequently fails.
        context._diagnostic_report = report
        require(report.get('status') == 'LOCAL_AUTH_FAILURE_COMPONENT_PASS'
                and tuple(r['case'] for r in report['cases']) == CASES,
                'exact_eleven_cases_not_completed')
        native = (report['diagnostic_totals']['native_sql_dispatched']
                  + report['reconciliation_diagnostic_totals']['native_sql_dispatches'])
        require(type(native) is int and 0 <= native <= command_register()['native_sql_capacity'],
                'native_count')
        require(report['diagnostic_totals']['all_managed_observations_complete'] is True,
                'managed_observation_missing')
        # The union observes managed SQL once, including startup overlap. Only
        # the separately counted native partition is recorded at this point.
        ledger.defer(ticket, partial_observed_sql_commands=native)
        context._deferred.append(ticket)
        ticket = None
        return report
    except BaseException as primary:
        if ticket is not None:
            try: ledger.unknown(ticket, reason='component_native_or_terminal_unknown')
            except BaseException as secondary:
                primary.add_note('secondary_component_ledger:' + type(secondary).__name__)
        raise
    finally:
        del gate.auth_failure_context


def original_refs(context):
    """Verify case originals against the already-published engine journal hashes."""
    from .runtime_registered_cleanup import parent
    refs = {}
    def add(path, expected, size=None):
        value = parent.cparent.reference(context.gate.out, {'path': path, 'sha256': expected})
        raw = (pathlib.Path(context.gate.out) / path).read_bytes()
        require(size is None or len(raw) == size, 'original_size')
        ref = {'path': path, 'sha256': expected, 'bytes': len(raw)}
        require(path not in refs or refs[path] == ref, 'conflicting_original')
        refs[path] = ref
        return value
    report = context._diagnostic_report
    if report is not None:
        original, digest = parent.cparent.read_record(context.gate.out, 'auth-failure-component.json')
        require(original == report, 'original_component_changed')
        add('auth-failure-component.json', digest)
    for row in (report['cases'] + report['safety_reconciliations']) if report else ():
        if 'retained_journal' not in row:
            continue
        folder = 'auth_failure_' + context.binding['run_id'] + '/' + row['case']
        if row in report['safety_reconciliations']:
            folder += '/safety-reconciliation'
        for name, ref in row['retained_journal']['files'].items():
            require(pathlib.PurePosixPath(name).name == name and name.endswith('.json'),
                    'journal_name')
            add(folder + '/' + name, ref['sha256'], ref['bytes'])
    collections = [context.records]
    if context._diagnostic_witness is not None:
        collections.append(context._diagnostic_witness.records)
    if context._diagnostic_registry is not None:
        collections.extend(context._diagnostic_registry._recordsets)
    for records in filter(None, collections):
        for name, raw in records.validate().items():
            add((records.folder / name).relative_to(context.gate.out).as_posix(),
                records._hashes[name], len(raw))
    profile = context.server.profile_receipt if context.server else None
    for ref in profile.get('evidence_refs', ()) if profile else ():
        add(ref['path'], ref['sha256'], ref['bytes'])
    return [refs[name] for name in sorted(refs)]


def consume_context(context):
    """Live local closure only. The independent archive verifier owns coverage."""
    from .runtime_registered_cleanup import parent
    from . import runtime_registered_startup as startup
    import admission_budget_root_runtime as root
    require(type(context) is bootstrap.Context and context._diagnostic_mode
            and context._finished and context._closing and context._admitted
            and not context._seed_attempted and not context._yielded
            and context.producer is None and context.auth is None and context.ids is None,
            'actual_diagnostic_context')
    context._validate()
    require(binding.verify(context.gate, context._extra_modules) == context._extra_binding,
            'dependencies_changed')
    report = context.closeout
    original = parent.cparent.reference(context.gate.out, context.closeout_ref)
    require(original.get('kind') == 'closeout' and
            {k: v for k, v in original.items() if k not in ('kind', 'sequence')} == report,
            'original_closeout_changed')
    require(not report['secondary_errors'] and not report.get('cleanup_missing')
            and report.get('numeric_lifetime_complete') is True, 'numeric_closure_missing')
    require(context._diagnostic_registry.valid_proof(context._diagnostic_seal),
            'actual_request_seal')
    require(context.server.closed and report['process']['process_stopped'] is True,
            'actual_process_close')
    profile = context.server.profile_receipt
    require(profile == report['runtime_profile'] and profile['evidence_refs']
            and profile['receipt']['status'] == 'LOCALONLY_RUNTIME_CAPABILITY_REDUCED'
            and profile['receipt']['commit_confirmed'] is True
            and profile['receipt']['commit_unknown'] is False
            and parent.cparent.reference(context.gate.out, profile['ref']) == profile['receipt'],
            'actual_profile_originals')
    accounting = context.execution_ledger.receipt()
    require(accounting == report['root_accounting'], 'root_receipt_changed')
    numeric = root.validate_terminal(context.execution_ledger, context.gate, context.binding)
    require(numeric['status'] == 'NUMERIC_ACCOUNTING_CLOSED', 'actual_numeric_root')
    records = [json.loads(raw) for raw in context.records.validate().values()]
    observations = [r for r in records if r['kind'] == 'startup-observation']
    expected = ['auth.' + name for name in startup.source_program()['native_reads']]
    require([r['command_id'] for r in observations] == expected, 'startup_original_read_set')
    observed = {r['command_id']: r['value'] for r in observations}
    require(observed['auth.auth_backend_before']['n'] == 0
            and observed['auth.auth_target_connection'] == {'n': 1, 'tls': 1}
            and observed['auth.auth_backend_after_stop']['n'] == 0, 'actual_auth_backend_boundary')
    measured = witness.managed_difference(observed['auth.managed_stats_before_start']['value'],
                                          observed['auth.managed_stats_after_stop']['value'])
    require(measured == report['process']['managed_sql'], 'original_lifetime_counters')
    stopped = [r for r in records if r['kind'] == 'startup-process-stopped']
    require(len(stopped) == 1 and stopped[0]['container_id'] == context.server.container_id
            and stopped[0]['running'] is False and stopped[0]['pid'] == 0, 'original_process_stop')
    refs = original_refs(context)
    typed_refs = [(ref, 'bytes') for ref in numeric['evidence_refs']]
    typed_refs += [(ref, 'size') for ref in numeric['journal_refs']]
    for ref, size_key in typed_refs:
        path = pathlib.PurePosixPath(ref['path'])
        require(not path.is_absolute() and len(path.parts) == 1 and path.name not in ('.', '..'),
                'root_original_path')
        file = pathlib.Path(context.gate.out) / path.name
        require(not file.is_symlink(), 'root_original_symlink')
        raw = file.read_bytes()
        require(type(ref[size_key]) is int and tracked.sha(raw) == ref['sha256']
                and len(raw) == ref[size_key], 'root_original_changed')
        refs.append({'path': path.name, 'sha256': ref['sha256'], 'bytes': len(raw)})
    return {'status': 'LOCAL_DIAGNOSTIC_LIFETIME_CLOSED', 'numeric_terminal': numeric,
            'original_refs': refs, 'global_auth_zero_claim': False,
            'original_claims_released': False, 'full_chain_admission': False}


def run(gate, *, binding, stack, ledger):
    """Parent supplies actual clean47 receipt and a separate admitted root ledger."""
    context = bootstrap.Context(gate, binding=binding, stack=stack, ledger=ledger)
    primary = terminal = None
    try:
        context.run_auth_failures()
        terminal = consume_context(context)
    except BaseException as error:
        primary = error
        raise
    finally:
        # Original exceptions/claims survive a packaging error; no retry.
        try:
            refs = terminal['original_refs'] if terminal else original_refs(context)
            record = {'scope': 'additional_actual_11_auth_fault_component',
                'status': 'RAW_AUTH_COMPONENT_RECORDED' if terminal else 'AUTH_JOB_INCOMPLETE',
                'coverage_verification': 'PENDING_INDEPENDENT_ARCHIVE_VERIFIER',
                'case_names': list(CASES), 'terminal': terminal,
                'original_refs_complete': terminal is not None,
                'source_commit': binding['source_commit'], 'ci_run': binding['ci_run'],
                'candidate_sha256': binding['candidate_sha'], 'parent_id': binding['run_id'],
                'command_register': command_register(),
                'component_status': (context._diagnostic_report or {}).get('status'),
                'parent_closeout_ref': context.closeout_ref,
                'component_ref': next((r for r in refs if r['path'] == 'auth-failure-component.json'), None),
                'profile_ref': (context.server.profile_receipt or {}).get('ref') if context.server else None,
                'original_refs': refs,
                'registered_requests_closed': context._diagnostic_seal is not None,
                'numeric_lifetime_complete': bool((context.closeout or {}).get('numeric_lifetime_complete')),
                'original_error_class': type(primary).__name__ if primary else None,
                'parent_bootstrap_accounts_created': 0,
                'parent_account_deletion_claim': False, 'global_auth_zero_claim': False,
                'full_auth_cleanup_proven': False, 'full_chain_admission': False,
                'hosted_admitted': False, 'planned_2349_run_changed': False,
                'retained_claims': copy.deepcopy(context._diagnostic_report['retained_claims'])
                    if context._diagnostic_report is not None else None,
                'cleanup_status': 'ORIGINAL_CASE_CLAIMS_RETAINED_NOT_FULL_AUTH_PASS'}
            record['original_archive_ref'] = archive.pack(gate, refs) if refs else None
            gate.save('auth-job-result.json', record)
        except BaseException as secondary:
            if primary is None: raise
            primary.add_note('secondary_auth_job_receipt:' + type(secondary).__name__)
    return record
