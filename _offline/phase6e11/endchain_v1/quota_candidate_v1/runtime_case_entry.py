"""Source admission and real registered-worker join, never a component PASS.

The root bootstrap/Auth cost admission is intentionally mandatory. The original
47-stack and Auth context remain their owners' implementations, not copied here.
"""
import importlib
import importlib.util
import copy
import datetime as dt
import json
import os
import pathlib
import sys
import uuid

from .compiler import CandidateStop, canonical, read_source, require, sha
from .runtime_adapter import CaseComposition, CaseLifecycle, PreparedCase, execute_case
from .runtime_prefix import PendingPrefix, PrefixGate
from .runtime_history import CaseHistory
from .runtime_stream import CaseStream

PREFIX = '_offline/phase6e11/endchain_v1/'
OWN = PREFIX + 'quota_candidate_v1/'
ROOT_ADMISSION = PREFIX + 'admission_budget_root_runtime.py'
BOOTSTRAP_NUMERIC_SOURCE = PREFIX + 'admission_budget_bootstrap_prefix.py'
ARCHIVE_SOURCE = PREFIX + 'admission_case_archive.py'
RENDERERS = {
    'guard': '_offline/phase6e11/controller_guard_v1/guard.py',
    'audit': '_offline/phase6e11/auth_metadata_v1/audit.py',
    'contract': '_offline/phase6e11/auth_metadata_v1/auth_contract.py',
}


def bound_module(root, sources, name):
    """Explicit candidate file, plus its raw hash; no search-path fallback."""
    require(name in sources and sha(read_source(root, name)) == sources[name],
            'case_entry_module_source')
    spec = importlib.util.spec_from_file_location('case_bound_' + sources[name], pathlib.Path(root) / name)
    require(spec is not None and spec.loader is not None, 'case_entry_module_loader')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(sha(pathlib.Path(module.__file__).read_bytes()) == sources[name],
            'case_entry_loaded_source')
    return module


def dependency(root, sources, name):
    relative = OWN + name + '.py'
    require(relative in sources and sha(read_source(root, relative)) == sources[relative],
            'case_entry_dependency_missing:' + name)
    module = importlib.import_module('quota_candidate_v1.' + name)
    require(sha(pathlib.Path(module.__file__).read_bytes()) == sources[relative],
            'case_entry_dependency_source:' + name)
    return module


def source_preflight(gate, case_name):
    """No connection/process starts; an incomplete authoritative model stops here."""
    from .runtime_adapter import DAG_SOURCE, source_inputs, verify_runtime_sources
    from .runtime_faults import CASES
    from .case_ci import SOURCES
    require(case_name in CASES, 'case_name_denied')
    root = pathlib.Path(gate.sources).resolve(strict=True)
    candidate = json.loads((gate.out / 'candidate.json').read_bytes())
    sources = candidate['sources']
    require(os.environ.get('GITHUB_ACTIONS') == 'true'
            and os.environ.get('GITHUB_REPOSITORY') == 'Yourizorge/fitmetzorge-staging'
            and os.environ.get('GITHUB_REF') == 'refs/heads/main'
            and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'case_entry_ci_only')
    require(candidate.get('sha256') == gate.result['candidate_sha256']
            == os.environ.get('CANDIDATE_SHA256')
            and gate.result['run_id'] == os.environ.get('GITHUB_RUN_ID')
            and gate.result.get('commit', gate.result.get('head')) == os.environ.get('GITHUB_SHA'),
            'case_entry_source_run')
    required = source_inputs(root)
    for name in (*required, *RENDERERS.values(), *SOURCES, ARCHIVE_SOURCE):
        require(name in sources and sha(read_source(root, name)) == sources[name],
                'case_entry_input_missing')
    verify_runtime_sources(root, {'sources': sources})
    import admission_budget_current_release as current
    require(sha(pathlib.Path(current.__file__).read_bytes()) == sources[DAG_SOURCE],
            'case_entry_compiler_source')
    report = current.build_current_execution(root, runtime_dir=pathlib.Path(__file__).parent)
    model = report['model']
    gate.save('case-source-preflight.json', {
        'case_name': case_name, 'source_commit': os.environ['GITHUB_SHA'],
        'ci_run': os.environ['GITHUB_RUN_ID'], 'candidate_sha256': candidate['sha256'],
        'dag_sha256': report['dag_sha256'], 'model': model, 'stack_started': False,
        'full_chain_admission': False, 'hosted_admitted': False})
    require(model.get('bound_complete') is True and model.get('fits') is True
            and type(model.get('minimal_cap')) is int and 0 < model['minimal_cap'] <= 2349
            and model.get('missing_costs') == [], 'case_entry_root_bound_incomplete')
    # The core 2340 register cannot authorize unbounded bootstrap/startup work.
    require(ROOT_ADMISSION in sources, 'case_entry_root_ledger_source_missing')
    root_admission = importlib.import_module('admission_budget_root_runtime')
    require(sha(pathlib.Path(root_admission.__file__).read_bytes()) == sources[ROOT_ADMISSION]
            and sha(read_source(root, ROOT_ADMISSION)) == sources[ROOT_ADMISSION],
            'case_entry_root_ledger_source')
    require(callable(getattr(root_admission, 'open_execution_ledger', None)),
            'case_entry_root_ledger_api_missing')
    root_register = root_admission.build_root_register(root, runtime_dir=pathlib.Path(__file__).parent)
    fields = ('bound_complete', 'total_local_ci_upper_bound',
              'total_hosted_equivalent_upper_bound', 'hosted_scope_complete',
              'source_inventory_complete', 'missing_costs', 'hosted_limit')
    require(tuple(root_admission.MODEL_FIELDS) == fields, 'case_entry_root_model_contract')
    root_model = {k: root_register[k] for k in fields}
    require(root_model['bound_complete'] is True
            and root_model['hosted_scope_complete'] is True
            and root_model['source_inventory_complete'] is True
            and root_model['hosted_limit'] == 2349
            and type(root_model['total_local_ci_upper_bound']) is int
            and root_model['total_local_ci_upper_bound'] > 0
            and type(root_model['total_hosted_equivalent_upper_bound']) is int
            and 0 < root_model['total_hosted_equivalent_upper_bound'] <= 2349
            and root_model['total_hosted_equivalent_upper_bound'] <= root_model['total_local_ci_upper_bound']
            and root_model['missing_costs'] == [], 'case_entry_root_bound_incomplete')
    return root, sources, {**report, 'root_dag': root_register, 'root_model': root_model}


def execute_registered(gate, prepared, context, artifact, samples, faults, *, owners=None):
    """Actual prefix/worker/finally path after root admission and tracked bootstrap.

    Returns private in-memory owners for terminal validation, never CASE_PASS.
    Context is B's already-yielded registered bootstrap; it is not serialized.
    """
    require(isinstance(prepared, PreparedCase), 'case_entry_prepared_required')
    if owners is None:
        owners = {}
    require(type(owners) is dict and not owners, 'case_entry_owner_handoff')
    quota = prepared.config()
    root, sources, binding = quota['root'], quota['manifest']['sources'], quota['binding']
    require(artifact['manifest'] == quota['manifest'] and context.isolation == quota['isolation'],
            'case_entry_context_binding')
    require(context.config.get('registeredIds') == context.ids
            and context.config.get('environment') == 'disposable_ci'
            and context.config.get('mode') == 'registered_synthetic', 'case_entry_context_scope')
    lifecycle_module = dependency(root, sources, 'runtime_lifecycle')
    catalog_module = dependency(root, sources, 'runtime_catalog')
    renderers = {name: bound_module(root, sources, path) for name, path in RENDERERS.items()}
    # audit.py loads guard.py itself; bind that transitive loaded renderer too.
    require(sha(pathlib.Path(renderers['audit'].g.__file__).read_bytes())
            == sources[RENDERERS['guard']], 'case_entry_audit_guard_source')
    from hosted_gate import ScalarSession
    from registered_runner import IdentitySession
    for module, name in ((importlib.import_module('hosted_gate'), 'hosted_gate.py'),
                         (importlib.import_module('registered_runner'), 'registered_runner.py')):
        require(sha(pathlib.Path(module.__file__).read_bytes()) == sources.get(PREFIX + name),
                'case_entry_session_source')
    c = CaseComposition(prepared, runtime=context.runtime, phase_faults=faults)
    prefix = PendingPrefix(gate, c, artifact, samples)
    view = PrefixGate(gate, prefix)
    history = CaseHistory(root, sources, local_version=prefix.version, local_sql=artifact['sql'])
    stream = CaseStream(prepared, prefix.version)
    catalog = catalog_module.CaseCatalog(root, sources, artifact, history)
    c.case_history = history
    c.case_preservation = lifecycle_module.CasePreservation(c, history=history, stream=stream, catalog=catalog)
    owners.update(composition=c, gate=view, lifecycle=None, result=None, original_error=None)
    scalar = identity = lifecycle = None
    primary = None
    secondary = []
    result = None
    try:
        scalar = ScalarSession(context.runtime, c)
        identity = IdentitySession(context.runtime, c, binding['run_id'], context.ids)
        lifecycle = CaseLifecycle(gate=view, composition=c, run_id=binding['run_id'], ids=context.ids,
            guard=renderers['guard'], audit=renderers['audit'], contract_type=renderers['contract'].Contract,
            sql=scalar.query, lock_query=identity.query)
        owners['lifecycle'] = lifecycle
        context.bind_case(lifecycle, c)
        c.case_preservation.prepare_prefix(view, lifecycle, prefix)
        c.confirm_case_prefix(view)
        result = execute_case(view, c, lifecycle, dict(context.config))
        owners['result'] = result
        return owners
    except BaseException as error:
        primary = error
        owners['original_error'] = error
        try:
            c.abort('case_registered_body_failed')
        except BaseException as secondary_error:
            error.add_note('case_abort_secondary:' + type(secondary_error).__name__)
        raise
    finally:
        # The registered runner alone reaps its worker, closes Auth and removes
        # temporary objects. Do not retry any of those actions here.
        for name, session in (('identity', identity), ('scalar', scalar)):
            if session is None:
                continue
            try:
                session.close()
            except BaseException as error:
                secondary.append({'stage': name, 'exception_class': type(error).__name__})
                if primary is not None:
                    primary.add_note('case_close_secondary:' + name + ':' + type(error).__name__)
                try:
                    c.abort('case_session_close_incomplete')
                except BaseException as abort_error:
                    secondary.append({'stage': 'abort_' + name,
                                      'exception_class': type(abort_error).__name__})
                    if primary is not None:
                        primary.add_note('case_abort_secondary:' + type(abort_error).__name__)
        try:
            if lifecycle is not None and getattr(lifecycle, 'http_journal', None) is not None:
                gate.save('case-auth-http-terminal.json', lifecycle.http_journal.receipt())
            receipt = {'complete': primary is None and not secondary and result is not None,
                'original_exception_class': type(primary).__name__ if primary is not None else None,
                'secondary': secondary, 'fault': faults.receipt(),
                'worker_owned': lifecycle.worker_owned if lifecycle is not None else False,
                'runtime_meter': c.meter.receipt(), 'retry': False,
                'covered_by': 'case.core',
                'commands': [{**row, 'covered_by': 'case.core'} for row in c.commands],
                'full_chain_admission': False, 'hosted_admitted': False}
            meter_path=gate.out/'runtime-command-meter.json'
            if meter_path.exists():
                require(canonical(json.loads(meter_path.read_bytes()))==canonical(receipt['runtime_meter']),
                    'case_worker_meter_original_changed')
            else:
                from .runtime_worker_evidence import save as save_worker_original
                save_worker_original(gate,'runtime-command-meter.json',receipt['runtime_meter'])
            gate.save('case-registered-finally.json', receipt)
        except BaseException as error:
            try:
                c.abort('case_finally_receipt_failed')
            except BaseException as abort_error:
                error.add_note('case_abort_secondary:' + type(abort_error).__name__)
            if primary is not None:
                primary.add_note('case_finally_save_secondary:' + type(error).__name__)
            elif not secondary:
                raise
            secondary.append({'stage': 'receipt', 'exception_class': type(error).__name__})
        owners['session_close_errors'] = list(secondary)
        if secondary and primary is None:
            raise CandidateStop('case_registered_close_incomplete')


def quota_read_program():
    """Exact ordered query hashes for the root compiler; no SQL/body export."""
    from admission_quota_readonly import QUERIES
    from integral_io import SNAPSHOT
    from integral_stream import GUARD
    commands = [
        ('begin', 'BEGIN TRANSACTION READ ONLY'),
        ('timeout', "SET LOCAL statement_timeout='5s'"),
        ('identity', GUARD),
        ('io_bind', 'EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) ' + SNAPSHOT),
        ('io_sample', SNAPSHOT)]
    for name, text in QUERIES.items():
        commands.extend([('io_bind', 'EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) ' + text),
                         ('io_sample', SNAPSHOT), (name, text)])
    commands.extend([
        ('io_sample', SNAPSHOT),
        ('io_closing_witness', 'EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) ' + SNAPSHOT),
        ('rollback', 'ROLLBACK')])
    counts = {}
    rows = []
    for phase, text in commands:
        counts[phase] = counts.get(phase, 0) + 1
        rows.append({'id': 'case.quota_read.' + phase + '.' + str(counts[phase]),
                     'phase': phase, 'sql_sha256': sha(text.encode())})
    return {
        'format': 'case-quota-read-program-v1', 'command_id': 'case.quota_read',
        'commands': rows, 'sql_command_bound': len(rows),
        'source_hashes': {PREFIX + name + '.py': sha(pathlib.Path(
            importlib.import_module(name).__file__).read_bytes()) for name in
            ('admission_quota_readonly', 'integral_io', 'integral_stream')},
        'caller_sha256': sha(pathlib.Path(__file__).read_bytes()),
        'failure_suffix': {'commands': [rows[-1]], 'only_if_begin_attempted': True,
                           'only_if_rollback_not_attempted': True},
        'native_only': True, 'automatic_retry': False,
        'command_text_exported': False, 'full_chain_admission': False}


def quota_samples(gate, runtime, ledger):
    """Four real catalog reads within the original strict QueryIO protocol.

    The root register must bind the complete 20-command macro and its recovery
    before this may be called. Child IDs document coverage, not extra charges.
    """
    from admission_quota_readonly import QUERIES
    from integral_ci import bind_parameters
    from integral_io import QueryIO
    from integral_stream import GUARD
    require(runtime.environment == 'disposable_ci', 'case_quota_local_only')
    program = quota_read_program()
    ticket = ledger.precharge('case.quota_read')
    connection = None
    attempted = False
    rollback_attempted = False
    primary = None
    counts = {}
    trace = []
    def query(phase, text, args=()):
        nonlocal attempted, rollback_attempted
        counts[phase] = counts.get(phase, 0) + 1
        command_id = 'case.quota_read.' + phase + '.' + str(counts[phase])
        require(len(trace) < program['sql_command_bound'], 'case_quota_command_ceiling')
        expected = program['commands'][-1] if text == 'ROLLBACK' else program['commands'][len(trace)]
        require(expected['id'] == command_id and expected['sql_sha256'] == sha(text.encode()),
                'case_quota_program_changed')
        item = {'id': command_id, 'sql_sha256': sha(text.encode()), 'confirmed': False,
                'covered_by': 'case.quota_read'}
        trace.append(item)
        if text == 'BEGIN TRANSACTION READ ONLY': attempted = True
        if text == 'ROLLBACK': rollback_attempted = True
        bound, values = bind_parameters(text, args)
        cursor = connection.execute(bound, values)
        rows = cursor.fetchall() if cursor.description else []
        item['confirmed'] = True
        return rows
    def failure(value):
        error = sys.exception()
        try: gate.save('case-quota-io-failure.json', value)
        except BaseException as secondary:
            if error is None: raise
            error.add_note('quota_io_receipt_secondary:' + type(secondary).__name__)
    try:
        connection = runtime.connect()
        query('begin', 'BEGIN TRANSACTION READ ONLY')
        query('timeout', "SET LOCAL statement_timeout='5s'")
        identity = query('identity', GUARD)[0]
        require(identity['ro'] == 'on' and identity['db'] == 'postgres'
                and identity['role'] == 'postgres' and identity['ssl'] is True,
                'case_quota_read_identity')
        io = QueryIO(lambda channel, phase, text, args=(): query(phase, text, args), on_failure=failure)
        io.start()
        samples = {}
        for name, text in QUERIES.items():
            qid = io.bind(text, [], read_only=True)
            samples[name] = query(name, text)
            io.executed(qid)
        evidence = io.close()
        query('rollback', 'ROLLBACK')
        gate.save('case-quota-read.json', {'commands': trace, 'io': evidence,
            'samples_sha256': sha(canonical(samples)), 'sql_text_exported': False,
            'source_program_sha256': sha(canonical(program)),
            'function_body_exported': False, 'full_chain_admission': False})
        return samples
    except BaseException as error:
        primary = error
        raise
    finally:
        close_error = None
        if attempted and not rollback_attempted:
            try: query('rollback', 'ROLLBACK')
            except BaseException as error:
                if primary is None: close_error = error
                else: primary.add_note('quota_rollback_secondary:' + type(error).__name__)
        if connection is not None:
            try: connection.close()
            except BaseException as error:
                if primary is None and close_error is None: close_error = error
                else: (primary or close_error).add_note('quota_close_secondary:' + type(error).__name__)
        error = primary or close_error
        try:
            if error is None:
                ledger.confirm(ticket, observed_sql_commands=len(trace))
            else:
                ledger.unknown(ticket, reason='not_terminal')
        except BaseException as secondary:
            if error is None: raise
            error.add_note('quota_ledger_secondary:' + type(secondary).__name__)
        if primary is None and close_error is not None: raise close_error


def observed_core(gate, owners):
    """Confirmed native/CLI partition; B settles managed Auth once after stop."""
    from cli_envelope import charged
    c = owners['composition']
    require(c.meter.closed and c.final_post_complete and c.closing_receipt is not None,
            'case_core_close_unconfirmed')
    require(c.commands and all(row.get('confirmed') is True for row in c.commands)
            and c.commands[-1]['phase'] == 'final_closure', 'case_core_trace_unconfirmed')
    prefix = getattr(gate, 'evidence_prefix', '')
    closure = json.loads((gate.out / (prefix + 'integral-closure.json')).read_bytes())
    require(closure.get('confirmed') is True
            and closure['global_commands'] == c.closing_receipt['global_commands']
            and closure['run_id'] == c.quota['binding']['run_id'], 'case_core_closure_binding')
    cli = owners['gate'].cli_protocol
    require(len(cli) == 3, 'case_core_cli_count')
    for item in cli: charged(item)
    observed = len(c.commands) + 4 + sum(
        item['protocol_commands'] + len(item['observer_commands']) for item in cli)
    return observed


def observed_fault_core(gate, owners):
    """A failed case can have a known native partition, never an assumed zero."""
    from cli_envelope import charged
    c = owners['composition']
    proof = owners.get('terminal_proof')
    require(type(proof) is dict and proof.get('status') == 'REGISTERED_FAULT_TERMINATED'
            and proof.get('run_id') == c.quota['binding']['run_id']
            and c.meter.stopped and not owners.get('session_close_errors')
            and not c.meter_stack, 'case_fault_native_termination')
    require(c.commands and all(row.get('confirmed') is True for row in c.commands)
            and [row.get('command') for row in c.commands] == list(range(1,len(c.commands)+1)),
            'case_fault_native_unknown')
    prefix = getattr(gate, 'evidence_prefix', '')
    raw = (gate.out / (prefix+'integral-preflight.json')).read_bytes()
    preflight = json.loads(raw)
    require(preflight.get('complete') is True and preflight.get('connection_closed') is True
            and preflight.get('rollback_confirmed') is True
            and len(preflight['commands']) == 4
            and all(row.get('confirmed') is True for row in preflight['commands']),
            'case_fault_preflight_unknown')
    native = [event for event in c.meter.events if event['kind'] == 'native']
    require(native and all(event['confirmed'] is True and type(event['commands']) is int
                           and event['commands'] > 0 for event in native)
            and sum(event['commands'] for event in native) == len(c.commands)+4,
            'case_fault_native_partition')
    cli = owners['gate'].cli_protocol
    attempted = owners['gate'].prefix.attempts
    require(attempted == [row.get('slot') for row in cli]
            and attempted in (['quota','pre_auth'], ['quota','pre_auth','final']),
            'case_fault_cli_unknown')
    tickets = [event for event in c.meter.events if event['kind'] == 'cli_reserved']
    require(len(tickets) == len(cli) and all(event['confirmed'] is True for event in tickets),
            'case_fault_cli_ticket_unknown')
    for event, item in zip(tickets, cli):
        require(event['commands'] == charged(item), 'case_fault_cli_ticket_count')
    observed = len(c.commands)+4+sum(
        item['protocol_commands']+len(item['observer_commands']) for item in cli)
    gate.save('case-core-native-partition.json', {
        'format':'case-core-native-partition-v1', 'run_id':c.quota['binding']['run_id'],
        'native_commands':len(c.commands), 'preflight_commands':4,
        'cli_observed_commands':observed-len(c.commands)-4,
        'partial_observed_sql_commands':observed, 'managed_auth_included':False,
        'preflight_sha256':sha(raw), 'trace_sha256':sha(canonical(c.commands)),
        'case_pass':False, 'full_chain_admission':False})
    return observed


def execute_context(gate, context, root, manifest, run_id, report, faults, *, owners):
    """Consume only B's source-owned child ledger within its Auth lifetime."""
    from . import compiler
    from .runtime_adapter import prepare_case
    require(type(owners) is dict and not owners, 'case_context_owner_handoff')
    primary = None
    try:
        with context as entered:
            require(entered is context, 'case_context_identity')
            execution = context.execution_ledger
            active = None
            known_zero = False
            terminal_attempted = False
            def record_worker_terminal():
                nonlocal terminal_attempted
                if owners.get('lifecycle') is None or terminal_attempted:
                    return
                terminal_attempted = True
                owners['terminal_proof'] = terminal_witness(gate, root, manifest['sources'],
                    owners, context, faults.case, faults, owners.get('original_error'))
            try:
                samples = quota_samples(gate, context.runtime, execution)
                active = execution.precharge('case.prepare')
                known_zero = True
                current = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                artifact = compiler.compile_candidate(root, manifest, samples, now=current)
                prepared = prepare_case(root, manifest, run_id, current_plan=report['dag'],
                    current_plan_sha256=report['dag_sha256'], isolation=context.isolation,
                    environment=dict(os.environ), connection=context.admission_connection,
                    ca_path=context.ca_path, now=current)
                execution.confirm(active, observed_sql_commands=0)
                active = None
                known_zero = False
                active = execution.precharge('case.core')
                execute_registered(gate, prepared, context, artifact, samples, faults, owners=owners)
                execution.defer(active, partial_observed_sql_commands=observed_core(gate, owners))
                active = None
                record_worker_terminal()
            except BaseException as error:
                primary = error
                try:
                    record_worker_terminal()
                except BaseException as secondary:
                    error.add_note('case_worker_terminal_secondary:' + type(secondary).__name__)
                # B's __exit__ can now follow only the precompiled safety edge.
                # Keep this before __exit__, never refund an incomplete child.
                if active is not None:
                    try:
                        if known_zero:
                            execution.fault(active, observed_sql_commands=0, reason='validation_failed')
                        else:
                            partial = None
                            if owners.get('terminal_proof') is not None:
                                try:
                                    partial = observed_fault_core(gate, owners)
                                except BaseException as secondary:
                                    error.add_note('case_fault_partition_secondary:' + type(secondary).__name__)
                            if partial is None:
                                execution.unknown(active, reason='not_terminal')
                            else:
                                execution.defer_fault(active, partial_observed_sql_commands=partial)
                    except BaseException as secondary:
                        error.add_note('case_core_ledger_secondary:' + type(secondary).__name__)
                raise
    except BaseException as error:
        if primary is not None and error is not primary:
            primary.add_note('case_context_close_secondary:' + type(error).__name__)
            raise primary from error
        raise
    # A context must not suppress the actual body fault.
    if primary is not None:
        raise primary
    return owners


def terminal_witness(gate, root, sources, owners, context, case_name, faults, original):
    """No SQL; validate after both registered and Auth-context finally paths."""
    require(owners.get('lifecycle') is not None, 'case_terminal_worker_not_constructed')
    terminal = dependency(root, sources, 'runtime_terminal')
    proof = terminal.validate_runtime_termination(
        owners['gate'], owners['composition'], owners['lifecycle'],
        case_name=case_name, fault=faults, worker_result=owners['result'],
        original_error=owners['original_error'], fixture_closeout=context.closeout, isolation=context.isolation)
    gate.save('case-runtime-terminal.json', proof)
    return proof


def bootstrap_fault_prefix(gate, binding, faults, root, sources):
    """Consume A's source-bound numeric validator, never an absence/count hint.

    Current uninstrumented canonical1..44 cannot produce this proof. Missing
    validator or original numeric prefix must keep the bootstrap ticket unknown.
    """
    from .runtime_case_terminal import original, saved
    require(faults.case in ('pre_migration', 'post_migration')
            and type(faults.fired) is dict and faults.fired.get('original_error_code')
            == 'case_injected_' + faults.case, 'case_bootstrap_prefix_fault')
    require(sha(read_source(root, BOOTSTRAP_NUMERIC_SOURCE)) == sources.get(BOOTSTRAP_NUMERIC_SOURCE),
            'case_bootstrap_prefix_source')
    module = importlib.import_module('admission_budget_bootstrap_prefix')
    require(sha(pathlib.Path(module.__file__).read_bytes()) == sources[BOOTSTRAP_NUMERIC_SOURCE],
            'case_bootstrap_prefix_loaded_source')
    validator = getattr(module, 'validate_bootstrap_fault_prefix', None)
    require(callable(validator), 'case_bootstrap_prefix_validator_missing')
    proof = validator(gate, binding=binding, case_name=faults.case, fault=faults)
    require(type(proof) is dict and proof.get('format') == 'admission-bootstrap-fault-prefix-v1'
            and proof.get('status') == 'BOOTSTRAP_FAULT_PREFIX_NUMERICALLY_VERIFIED'
            and proof.get('case_name') == faults.case and proof.get('run_id') == binding['run_id']
            and proof.get('source_commit') == binding['source_commit']
            and proof.get('ci_run') == binding['ci_run']
            and proof.get('candidate_sha256') == binding['candidate_sha']
            and proof.get('original_fault_code') == 'case_injected_' + faults.case
            and proof.get('complete_numeric_prefix') is True
            and proof.get('full_chain_admission') is False and proof.get('hosted_admitted') is False,
            'case_bootstrap_prefix_binding')
    require(type(proof.get('observed_sql_commands')) is int and proof['observed_sql_commands'] > 0,
            'case_bootstrap_prefix_numeric')
    refs = proof.get('evidence_refs')
    require(type(refs) is list and refs and all(type(ref) is dict
            and set(ref) == {'path', 'sha256', 'bytes'} for ref in refs),
            'case_bootstrap_prefix_originals')
    paths = []
    for ref in refs:
        original(gate, ref)
        paths.append(ref['path'])
    require(len(set(paths)) == len(paths), 'case_bootstrap_prefix_duplicate_original')
    return dict(proof=proof, ref=saved(gate, 'case-bootstrap-prefix-numeric.json', proof))


def bootstrap_closeout_numeric(gate, binding, faults, isolation, proof, root, sources):
    """The four explicit reads are not a claim of zero implicit driver SQL."""
    from .runtime_case_terminal import original, saved
    require(sha(read_source(root, BOOTSTRAP_NUMERIC_SOURCE)) == sources.get(BOOTSTRAP_NUMERIC_SOURCE),
            'case_bootstrap_closeout_source')
    module = importlib.import_module('admission_budget_bootstrap_prefix')
    require(sha(pathlib.Path(module.__file__).read_bytes()) == sources[BOOTSTRAP_NUMERIC_SOURCE],
            'case_bootstrap_closeout_loaded_source')
    validator = getattr(module, 'validate_bootstrap_failure_closeout', None)
    require(callable(validator), 'case_bootstrap_closeout_validator_missing')
    numeric = validator(gate, binding=binding, case_name=faults.case,
                        fault=faults, isolation=isolation, proof=proof)
    require(type(numeric) is dict
            and numeric.get('format') == 'admission-bootstrap-closeout-numeric-v1'
            and numeric.get('status') == 'BOOTSTRAP_CLOSEOUT_NUMERICALLY_VERIFIED'
            and numeric.get('case_name') == faults.case and numeric.get('run_id') == binding['run_id']
            and numeric.get('source_commit') == binding['source_commit']
            and numeric.get('ci_run') == binding['ci_run']
            and numeric.get('candidate_sha256') == binding['candidate_sha']
            and numeric.get('complete_numeric_closeout') is True
            and numeric.get('full_chain_admission') is False and numeric.get('hosted_admitted') is False,
            'case_bootstrap_closeout_binding')
    require(all(type(numeric.get(key)) is int for key in
                ('observed_sql_commands', 'explicit_sql_commands', 'driver_sql_commands'))
            and numeric['explicit_sql_commands'] == 4 and numeric['driver_sql_commands'] >= 0
            and numeric['observed_sql_commands'] == 4 + numeric['driver_sql_commands'],
            'case_bootstrap_closeout_numeric')
    refs = numeric.get('evidence_refs')
    require(type(refs) is list and refs and all(type(ref) is dict
            and set(ref) == {'path', 'sha256', 'bytes'} for ref in refs),
            'case_bootstrap_closeout_originals')
    for ref in refs:
        original(gate, ref)
    require(len({ref['path'] for ref in refs}) == len(refs), 'case_bootstrap_closeout_duplicate_original')
    return dict(proof=numeric, ref=saved(gate, 'case-bootstrap-closeout-numeric.json', numeric))


def execute_bootstrap(gate, migrations, bootstrap, ledger, binding, faults, root, sources, *, termination=None):
    """Keep expected faults, admitting numeric closure only with complete originals."""
    from .compiler import binding as preparation
    run_id = binding.get('run_id') if type(binding) is dict else None
    require(type(run_id) is str, 'case_bootstrap_run_binding')
    try:
        parsed = uuid.UUID(run_id)
    except ValueError:
        raise CandidateStop('case_bootstrap_run_binding') from None
    require(str(parsed)==run_id and parsed.version==4
            and run_id not in (preparation.NEW_RUN,preparation.OLD_RUN),
            'case_bootstrap_run_binding')
    active = ledger.precharge('case.bootstrap.clean47')
    try:
        stack = bootstrap(gate, migrations, hooks=faults, run_id=run_id)
        observed = stack.get('bootstrap_total_sql_commands')
        require(type(observed) is int and observed >= 0, 'case_bootstrap_total_unmeasured')
        ledger.confirm(active, observed_sql_commands=observed)
        return stack
    except BaseException as original:
        early = faults.case in ('pre_migration', 'post_migration') and faults.fired is not None
        prefix = None
        if early:
            try:
                prefix = bootstrap_fault_prefix(gate, binding, faults, root, sources)
            except BaseException as secondary:
                original.add_note('case_bootstrap_prefix_secondary:' + type(secondary).__name__)
        ledger_stopped = False
        try:
            if prefix is None:
                ledger.unknown(active, reason='not_terminal')
            else:
                ledger.fault(active, observed_sql_commands=prefix['proof']['observed_sql_commands'],
                             reason='validation_failed')
            ledger_stopped = True
        except BaseException as secondary:
            original.add_note('case_bootstrap_ledger_secondary:' + type(secondary).__name__)
        failure_ref = None
        try:
            from .runtime_case_terminal import saved
            failure_ref = saved(gate, 'case-bootstrap-failure-original.json', {
                'format':'case-bootstrap-original-failure-v1', 'case_name':faults.case,
                'run_id':binding.get('run_id'), 'source_commit':binding.get('source_commit'),
                'ci_run':binding.get('ci_run'), 'candidate_sha256':binding.get('candidate_sha'),
                'original_exception_class':type(original).__name__,
                'original_fault_code':'case_injected_' + faults.case
                    if type(faults.fired) is dict and faults.fired.get('original_error_code')
                    == 'case_injected_' + faults.case else None,
                'bootstrap_numeric_prefix_ref':prefix['ref'] if prefix is not None else None,
                'bootstrap_numeric_confirmed':prefix is not None and ledger_stopped,
                'ledger_stopped':ledger_stopped, 'automatic_retry':False,
                'full_chain_admission':False, 'hosted_admitted':False})
        except BaseException as secondary:
            original.add_note('case_bootstrap_original_save_secondary:' + type(secondary).__name__)
        if early and ledger_stopped:
            close_ticket = None
            try:
                closeout = dependency(root, sources, 'runtime_bootstrap_closeout')
                terminal = dependency(root, sources, 'runtime_terminal_bootstrap')
                close_ticket = ledger.precharge('case.bootstrap.failure_closeout')
                isolation = closeout.collect(gate, binding, faults.case, faults)
                # collect() checks four confirmed rows/rollback and no Auth
                # process; the independent validator binds their raw receipts.
                proof = terminal.validate_bootstrap_termination(
                    gate, binding, faults.case, faults, isolation)
                gate.save('case-bootstrap-termination.json', proof)
                close_numeric = bootstrap_closeout_numeric(
                    gate, binding, faults, isolation, proof, root, sources)
                ledger.confirm(close_ticket, observed_sql_commands=close_numeric['proof']['observed_sql_commands'])
                close_ticket = None
                if termination is not None:
                    require(type(termination) is dict and not termination, 'case_bootstrap_terminal_owner')
                    termination.update(isolation=isolation, proof=proof,
                        numeric_prefix=prefix, original_failure_ref=failure_ref,
                        closeout_numeric=close_numeric)
            except BaseException as secondary:
                original.add_note('case_bootstrap_closeout_secondary:' + type(secondary).__name__)
                if close_ticket is not None:
                    try:
                        ledger.unknown(close_ticket, reason='not_terminal')
                    except BaseException as ledger_error:
                        original.add_note('case_bootstrap_closeout_ledger_secondary:'
                                          + type(ledger_error).__name__)
        raise


_PREPARED_KEY = object()


class PreparedExecution:
    """Single-use local owner shared with preinstall; never an admission flag."""
    __slots__ = ('_key', '_gate', '_root', '_sources', '_report', '_manifest',
                 '_binding', '_faults', '_ledger', '_registered', '_case_name',
                 '_identity', '_used', '_terminal_attempted', '_terminal_proof',
                 '_bootstrap_termination')

    def __init__(self, key, *, gate, root, sources, report, manifest, binding,
                 faults, ledger, registered, case_name):
        require(key is _PREPARED_KEY, 'case_prepared_factory_only')
        self._key = key
        self._gate = gate
        self._root = root
        self._sources = copy.deepcopy(sources)
        self._report = copy.deepcopy(report)
        self._manifest = copy.deepcopy(manifest)
        self._binding = copy.deepcopy(binding)
        self._faults = faults
        self._ledger = ledger
        self._registered = registered
        self._case_name = case_name
        self._identity = self._current_identity(gate)
        self._used = False
        self._terminal_attempted = False
        self._terminal_proof = None
        self._bootstrap_termination = {}

    @staticmethod
    def _current_identity(gate):
        return (str(pathlib.Path(gate.sources).resolve(strict=True)),
                str(pathlib.Path(gate.out).resolve(strict=True)),
                gate.result['candidate_sha256'], gate.result['run_id'],
                gate.result.get('commit', gate.result.get('head')),
                tuple(os.environ.get(name) for name in ('GITHUB_ACTIONS',
                    'GITHUB_REPOSITORY', 'GITHUB_REF', 'GITHUB_RUN_ATTEMPT',
                    'GITHUB_SHA', 'GITHUB_RUN_ID', 'CANDIDATE_SHA256')))

    @property
    def ledger(self):
        return self._ledger

    @property
    def binding(self):
        return copy.deepcopy(self._binding)

    @property
    def case_name(self):
        return self._case_name

    def _consume(self, gate, case_name):
        require(self._key is _PREPARED_KEY and self._gate is gate
                and case_name == self._case_name, 'case_prepared_owner_mismatch')
        require(not self._used, 'case_prepared_already_consumed')
        # A failed revalidation is terminal for this owner, not a retry grant.
        self._used = True
        require(self._current_identity(gate) == self._identity, 'case_prepared_identity_changed')
        candidate = json.loads((gate.out / 'candidate.json').read_bytes())
        require(candidate.get('sha256') == self._binding['candidate_sha']
                and candidate.get('sources') == self._sources, 'case_prepared_candidate_changed')
        for name, digest in self._sources.items():
            require(sha(read_source(self._root, name)) == digest, 'case_prepared_source_changed')


def prepare_execution(gate, case_name):
    """Prepare once BEFORE platform install; performs no SQL/network/process."""
    require(gate.__dict__.get('_quota_case_prepared') is None, 'case_prepared_already_created')
    root, sources, report = source_preflight(gate, case_name)
    from . import compiler
    from .runtime_faults import PhaseFaults
    from complete_register import scenario_source
    registered = dependency(root, sources, 'runtime_registered_bootstrap')
    dependency(root, sources, 'runtime_lifecycle')
    dependency(root, sources, 'runtime_catalog')
    dependency(root, sources, 'runtime_terminal')
    import admission_budget_root_runtime as root_admission
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    stamp = lambda value: value.strftime('%Y-%m-%dT%H:%M:%SZ')
    run_id = str(uuid.uuid4())
    manifest = compiler.prepare(root, source_commit=os.environ['GITHUB_SHA'],
        candidate_sha256=gate.result['candidate_sha256'], github_run=os.environ['GITHUB_RUN_ID'],
        created_at=stamp(now), expires_at=stamp(now + dt.timedelta(seconds=600)),
        cases=[{'id': run_id, 'label': case_name, 'cap': 2349}], sources=sources)
    binding = compiler.binding_for_case(root, manifest, run_id, now=stamp(now))
    faults = PhaseFaults(case_name, binding, scenario_source.capture()['workflow_actions'][:45],
                         out=gate.out, save=gate.save)
    ledger = root_admission.open_execution_ledger(gate, dag=report['root_dag'],
        model=report['root_model'], binding=binding)
    owner = PreparedExecution(_PREPARED_KEY, gate=gate, root=root, sources=sources,
        report=report, manifest=manifest, binding=binding, faults=faults,
        ledger=ledger, registered=registered, case_name=case_name)
    gate._quota_case_prepared = owner
    return owner


def run(gate, migrations, case_name, *, bootstrap, prepared=None):
    owner = prepare_execution(gate, case_name) if prepared is None else prepared
    require(type(owner) is PreparedExecution, 'case_prepared_owner_required')
    owner._consume(gate, case_name)
    root, sources, report = owner._root, owner._sources, owner._report
    manifest, binding, faults = owner._manifest, owner._binding, owner._faults
    ledger, registered = owner.ledger, owner._registered
    run_id = binding['run_id']
    primary = None
    context = None
    owners = {}
    result = None
    try:
        stack = execute_bootstrap(gate, migrations, bootstrap, ledger, binding, faults, root, sources,
                                  termination=owner._bootstrap_termination)
        context = registered.context(gate, binding=binding, stack=stack, ledger=ledger)
        execute_context(gate, context, root, manifest, run_id, report, faults, owners=owners)
    except BaseException as error:
        primary = error
    try:
        terminal = dependency(root, sources, 'runtime_case_terminal')
        result = terminal.finish(owner, gate, context, owners, original_error=primary)
    except BaseException as error:
        if primary is not None:
            primary.add_note('case_terminal_join_secondary:' + type(error).__name__)
            raise primary from error
        primary = error
        raise
    finally:
        try:
            gate.save('case-root-execution.json', {'case_name': case_name, 'run_id': run_id,
                'parent_id': binding['parent_id'], 'source_commit': binding['source_commit'],
                'ci_run': binding['ci_run'], 'candidate_sha256': binding['candidate_sha'],
                'fault': faults.receipt(), 'ledger': ledger.receipt(),
                'status': 'CASE_PASS' if result is not None else 'NO_GO',
                'original_exception_class': type(primary).__name__ if primary is not None else None,
                'full_chain_admission': False, 'hosted_admitted': False})
        except BaseException as error:
            if primary is None: raise
            primary.add_note('case_root_receipt_secondary:' + type(error).__name__)
            raise primary from error
    return result
