"""Pure registered-worker terminal witness, never whole-case admission.

The root ledger and the independent fixture/Auth context remain separate owners.
This verifier neither executes artifact code nor converts a removal barrier into
proof that an outstanding HTTP request completed.
"""
import collections
import hashlib
import json
import pathlib
import re
import sys

PREFIX = '_offline/phase6e11/endchain_v1/'
OWN = PREFIX + 'quota_candidate_v1/'
PRODUCERS = {
    'registered_runner': PREFIX + 'registered_runner.py',
    'registered_lifecycle': PREFIX + 'registered_lifecycle.py',
    'integral_ci': PREFIX + 'integral_ci.py',
    'metered_composition': PREFIX + 'metered_composition.py',
    'runtime_budget': PREFIX + 'runtime_budget.py',
    'integral_io': PREFIX + 'integral_io.py',
    'cli_envelope': PREFIX + 'cli_envelope.py',
    'quota_candidate_v1.runtime_adapter': OWN + 'runtime_adapter.py',
    'quota_candidate_v1.runtime_case_entry': OWN + 'runtime_case_entry.py',
    'quota_candidate_v1.runtime_faults': OWN + 'runtime_faults.py',
    'quota_candidate_v1.runtime_recovery': OWN + 'runtime_recovery.py',
    'quota_candidate_v1.runtime_lifecycle': OWN + 'runtime_lifecycle.py',
    'quota_candidate_v1.runtime_catalog': OWN + 'runtime_catalog.py',
    'quota_candidate_v1.runtime_history': OWN + 'runtime_history.py',
    'quota_candidate_v1.runtime_stream': OWN + 'runtime_stream.py',
    'quota_candidate_v1.runtime_prefix': OWN + 'runtime_prefix.py',
    'quota_candidate_v1.runtime_parent_workflow': OWN + 'runtime_parent_workflow.py',
}
WORKERS = ('runtime_auth.mjs', 'runtime_integral_workflow.mjs', 'runtime_node.mjs')
INPUTS = ('runtime_refs.json',)
LABELS = ('before', 'after_migration', 'before_cleanup', 'after_cleanup', 'final_post')


def require(condition, code):
    if not condition:
        raise ValueError('runtime_terminal_' + code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def decode(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'duplicate_key')
            value[key] = item
        return value
    value = json.loads(raw, object_pairs_hook=unique,
                       parse_constant=lambda _: require(False, 'nonfinite'))
    require(type(value) is dict, 'object')
    return value


def read_under(root, name, maximum=4000000):
    root = pathlib.Path(root).resolve(strict=True)
    require(type(name) is str and re.fullmatch(r'[A-Za-z0-9_./-]+', name)
            and all(part not in ('', '.', '..') for part in name.split('/')), 'path')
    path = root / name
    require(path.resolve(strict=True).is_relative_to(root)
            and all(not p.is_symlink() and not getattr(p, 'is_junction', lambda: False)()
                    for p in (path, *path.parents)), 'path_escape')
    require(path.stat().st_size <= maximum, 'size')
    raw = path.read_bytes()
    require(len(raw) <= maximum, 'size')
    return raw


class Evidence:
    def __init__(self, gate):
        self.root = gate.out
        self.prefix = getattr(gate, 'evidence_prefix', '')
        require(type(self.prefix) is str and re.fullmatch(r'[A-Za-z0-9_-]*', self.prefix), 'prefix')
        self.refs = {}

    def read(self, name, *, prefixed=True):
        require(pathlib.PurePosixPath(name).name == name, 'basename')
        path = (self.prefix if prefixed else '') + name
        raw = read_under(self.root, path)
        self.refs[path] = dict(path=path, sha256=digest(raw), bytes=len(raw))
        return decode(raw)

    def original(self, ref, expected, maximum):
        require(type(ref) is dict and ref.get('path') == expected
                and pathlib.PurePosixPath(expected).name == expected, 'raw_ref')
        raw = read_under(self.root, expected, maximum)
        require(ref.get('sha256') == digest(raw)
                and ('bytes' not in ref or type(ref['bytes']) is int and ref['bytes'] == len(raw)), 'raw_hash')
        self.refs[expected] = dict(path=expected, sha256=digest(raw), bytes=len(raw))
        return raw


def source_binding(gate, c, evidence):
    quota = c.quota
    binding = quota['binding']
    result = gate.result
    commit = result.get('commit', result.get('head'))
    require(type(commit) is str and re.fullmatch('[a-f0-9]{40}', commit)
            and result.get('head', commit) == commit
            and result.get('commit', commit) == commit
            and commit == binding['source_commit']
            and result.get('run_id') == binding['ci_run']
            and result.get('candidate_sha256') == binding['candidate_sha'], 'source_run')
    require(binding['environment'] == 'disposable_ci'
            and binding['hosted_permission'] is False and binding['execution_admitted'] is False,
            'local_only')
    require(pathlib.Path(gate.sources).resolve(strict=True)
            == pathlib.Path(quota['root']).resolve(strict=True), 'source_root')
    candidate = evidence.read('candidate.json', prefixed=False)
    sources = candidate['sources']
    require(candidate['sha256'] == binding['candidate_sha']
            and sources == quota['manifest']['sources'], 'candidate_inventory')
    required = set(PRODUCERS.values()) | {OWN + n for n in (*WORKERS, *INPUTS)} | {OWN + 'runtime_terminal.py'}
    hashes = {}
    for name in sorted(required):
        observed = digest(read_under(gate.sources, name))
        require(sources.get(name) == observed, 'producer_source')
        hashes[name] = observed
    require(digest(pathlib.Path(__file__).read_bytes()) == hashes[OWN + 'runtime_terminal.py'],
            'validator_source')
    for name, relative in PRODUCERS.items():
        module = sys.modules.get(name)
        # Recovery is imported only after entering the workflow body.
        if name.endswith('.runtime_recovery') and not hasattr(c, 'workflow_recovery'):
            continue
        require(module is not None and getattr(module, '__file__', None) is not None
                and digest(pathlib.Path(module.__file__).read_bytes()) == hashes[relative],
                'loaded_producer')
    return hashes


def meter_summary(value, register):
    require(type(value) is dict and type(value.get('used')) is int
            and type(value.get('limit')) is int and 0 < value['used'] <= value['limit'] <= 2349,
            'meter_limit')
    require(register.get('complete_register') is True and register.get('fits') is True
            and register['approved_limit'] == value['limit']
            and type(register.get('worst_including_safety')) is int
            and register['worst_including_safety'] <= value['limit'], 'register')
    events = value['events']
    require(type(events) is list and 0 < len(events) <= 2349, 'meter_events')
    used, phases, unknown = 0, collections.Counter(), 0
    for index, event in enumerate(events, 1):
        count = event.get('commands')
        require(type(count) is int and count > 0 and event.get('number') == index
                and event.get('first_command') == used + 1
                and type(event.get('confirmed')) is bool, 'meter_sequence')
        require('actual_commands' not in event or event['actual_commands'] == count,
                'meter_mismatch')
        used += count
        if event['phase'] != 'safety':
            require(event['phase'] in register['phase_budgets'], 'meter_phase')
            phases[event['phase']] += count
        if not event['confirmed']:
            unknown += count
        if event.get('mutation') is True:
            require(type(event.get('reserved_cleanup')) is int
                    and event['reserved_cleanup'] >= 0
                    and used + event['reserved_cleanup'] <= value['limit'], 'prefix_reserve')
    require(used == value['used'] and dict(phases) == value['phases']
            and all(count <= register['phase_budgets'][phase] for phase, count in phases.items())
            and value['complete'] is (unknown == 0), 'meter_totals')
    return dict(charged_commands=used, unknown_commands=unknown, phase_commands=dict(phases))


def check_io(value, *, readonly=False):
    require(type(value.get('closing_temp_written')) is int and value['closing_temp_written'] == 0
            and type(value.get('closing_wal_bytes')) is int and value['closing_wal_bytes'] == 0
            and value.get('query_text_read') is False, 'io_closing')
    last = value['last_pair']
    require(last.get('own_temp_written') == 0, 'io_temp')
    classes = value['source_classes']
    require(type(classes) is dict and classes
            and all(type(row.get('readonly')) is bool for row in classes.values()), 'io_classes')
    reads = set(value['readonly_queryids'])
    require(reads == {row['queryid'] for row in classes.values() if row['readonly'] is True}
            and (not readonly or all(row['readonly'] is True for row in classes.values())), 'io_read_class')
    require(type(last['queries']) is list and last['queries'], 'io_queries')
    for row in last['queries']:
        require(all(type(row[k]) is int for k in ('temp_read','temp_written','calls','wal'))
                and row['temp_read'] == row['temp_written'] == 0
                and row['calls'] > 0 and 0 <= row['exec_ms'] <= 5000 * row['calls']
                and row['wal'] >= 0 and (row['queryid'] not in reads or row['wal'] == 0), 'io_numeric')
    require(last['own_wal_bytes'] == sum(row['wal'] for row in last['queries'])
            and (not readonly or last['own_wal_bytes'] == 0), 'io_wal')


def validate_runtime_termination(gate, composition, lifecycle, *, case_name, fault,
                                 worker_result, original_error, fixture_closeout, isolation):
    """Return a bounded component witness, with whole-case admission always false.

    Caller invokes this AFTER execute_registered's finally and retains its owners
    on failure. fixture_closeout is deliberately not consumed as a PASS flag;
    B's independently verified context closeout and root ledger must be joined by
    the final producer. Missing/invalid evidence raises without writing a receipt.
    """
    c = composition
    from .runtime_adapter import CaseComposition, CaseLifecycle, validate_isolation, verify_runtime_sources
    from .runtime_faults import PhaseFaults, CASES
    require(type(c) is CaseComposition and type(lifecycle) is CaseLifecycle
            and type(fault) is PhaseFaults and lifecycle.composition is c
            and lifecycle.gate is gate and c.phase_faults is fault, 'owners')
    require(case_name in CASES and case_name not in ('pre_migration', 'post_migration'), 'case')
    require(fault.case == case_name and fault.binding == c.quota['binding']
            and lifecycle.run_id == c.quota['binding']['run_id'], 'case_binding')
    evidence = Evidence(gate)
    sources = source_binding(gate, c, evidence)
    verify_runtime_sources(c.quota['root'], c.quota['manifest'])
    require(isolation == c.quota['isolation'], 'isolation_binding')
    validate_isolation(isolation, c.quota['binding'])
    terminal = evidence.read('registered-worker-terminal.json')
    final = evidence.read('case-registered-finally.json')
    require(terminal.get('worker_terminated') is True
            and terminal.get('automatic_retry') is False and terminal.get('secrets_exported') is False
            and type(terminal.get('messages')) is int and 0 < terminal['messages'] <= 200
            and terminal.get('termination_error_class') is None, 'worker_terminal')
    require(final.get('retry') is False and final.get('worker_owned') is True
            and final.get('covered_by') == 'case.core'
            and final.get('fault') == fault.receipt()
            and final.get('runtime_meter') == c.meter.receipt()
            and final.get('commands') == [{**row, 'covered_by': 'case.core'} for row in c.commands],
            'finally_binding')
    require(final.get('original_exception_class') ==
            (type(original_error).__name__ if original_error is not None else None), 'original_error')
    summary = meter_summary(final['runtime_meter'], c.quota['register'])
    require([row.get('command') for row in c.commands] == list(range(1, len(c.commands) + 1)),
            'trace_sequence')
    blockers = ['root_ledger_terminal_join', 'independent_fixture_auth_closeout_join']
    if terminal.get('cleanup_errors') or final.get('secondary'):
        blockers.append('registered_cleanup_secondary')
    if summary['unknown_commands']:
        blockers.append('unknown_consumed_commands')
    cli_summary = None
    if case_name == 'normal':
        require(original_error is None and fault.fired is None
                and terminal.get('complete') is True and final.get('complete') is True
                and not terminal.get('cleanup_errors') and not final.get('secondary')
                and summary['unknown_commands'] == 0, 'normal_terminal')
        require(type(worker_result) is dict
                and worker_result.get('status') == 'INTEGRAL_REAL_AUTH_WORKFLOW_CI_PASS'
                and worker_result.get('checks') == 18 and worker_result.get('durable_steps') == 89
                and worker_result.get('closure') == 'confirmed'
                and worker_result.get('environment') == 'disposable_ci'
                and worker_result.get('hosted_requests') == worker_result.get('emails_sent') == 0
                and worker_result['workflow'].get('pairs') == 71
                and worker_result['workflow'].get('deletes') == 123
                and worker_result['workflow'].get('next_step') == 83, 'worker_result')
        proof = worker_result.get('proof')
        operations = ('issue', 'verify', 'getUser', 'refresh', 'logout', 'revoked_denial')
        require(type(proof) is list and len(proof) == 18
                and {(row.get('role'), row.get('operation')) for row in proof}
                == {(role, op) for role in ('a_member', 'a_trainer', 'b_member') for op in operations}
                and all(row['after'].get('pair_complete') is True
                        and row['after'].get('exact_contract') is True for row in proof), 'auth_pairs')
        require(lifecycle.removed and lifecycle.workflow_complete and not lifecycle.failed
                and terminal['guard_audit_removed'] is True and c.meter.closed and not c.meter.stopped
                and c.final_pre_complete and c.final_dry_complete and c.final_post_complete
                and c.case_preservation.attempts == list(LABELS)
                and c.auth_zero_proof is not None, 'normal_lifecycle')
        require(hasattr(c, 'workflow_recovery') and c.workflow_recovery.get('complete') is True
                and c.workflow_recovery.get('worker_terminated') is True
                and c.workflow_recovery.get('secondary') == [], 'normal_recovery')
        require(all(row.get('confirmed') is True for row in c.commands)
                and c.commands[-1]['phase'] == 'final_closure', 'normal_trace')
        trace = evidence.read('integral-complete-protocol-trace.json')
        require(trace['commands'] == c.commands and trace['outer_sql_commands'] == len(c.commands)
                and trace['environment'] == 'disposable_ci' and trace['full_chain_admission'] is False,
                'complete_trace')
        closure = evidence.read('integral-closure.json')
        require(closure == {**c.closing_receipt, 'confirmed': True}
                and closure['run_id'] == lifecycle.run_id
                and closure['global_commands'] == summary['charged_commands']
                and evidence.read('runtime-command-meter.json') == c.meter.receipt(), 'closure')
        cli_summary = _normal_receipts(evidence, c, gate)
        outcome = 'REGISTERED_WORKER_COMPLETE'
    else:
        require(original_error is not None and worker_result is None and c.meter.stopped
                and terminal.get('complete') is False and final.get('complete') is False,
                'fault_terminal')
        fired = evidence.read('case-fault-boundary.json')
        require(fault.fired is not None and fired == fault.fired
                and fired['original_error_code'] == 'case_injected_' + case_name
                and all(fired['event'].get(k) == v for k, v in fault.selector.items())
                and fired['automatic_retry'] is False, 'fault_boundary')
        trace = evidence.read('registered-incomplete-protocol-trace.json')
        require(trace['commands'] == c.commands and trace['runtime_meter'] == c.meter.receipt()
                and trace['complete'] is False and trace['automatic_retry'] is False, 'fault_trace')
        # The runner may wrap the injected fault. Preserve BOTH facts; never
        # relabel its RuntimeError as the injected exception itself.
        outcome = 'REGISTERED_FAULT_TERMINATED'
        blockers.append('fault_cleanup_independent_proof_required')
    if hasattr(c, 'workflow_recovery'):
        recovery = evidence.read('case-workflow-recovery.json')
        require(recovery == c.workflow_recovery, 'recovery_binding')
        if recovery.get('complete') is not True or recovery.get('secondary'):
            blockers.append('workflow_recovery_incomplete')
    return dict(format='registered-runtime-terminal-witness-v1', status=outcome,
        run_id=lifecycle.run_id, source_commit=c.quota['binding']['source_commit'],
        ci_run=c.quota['binding']['ci_run'], candidate_sha256=c.quota['binding']['candidate_sha'],
        case_name=case_name, worker_terminated=True,
        original_exception_class=type(original_error).__name__ if original_error is not None else None,
        original_fault_code=fault.fired['original_error_code'] if fault.fired else None,
        worker_result_sha256=digest(canonical(worker_result)) if worker_result is not None else None,
        isolation_sha256=digest(canonical(isolation)),
        meter=summary, cli=cli_summary, source_hashes=sources, evidence_refs=list(evidence.refs.values()),
        fixture_closeout_validated=False, pending_proofs=blockers,
        case_pass=False, full_chain_admission=False, hosted_admitted=False, additional_sql_commands=0)


def _normal_receipts(evidence, c, gate):
    from cli_envelope import charged
    from .runtime_adapter import counted_close
    from .runtime_prefix import compatible
    cli = [evidence.read('cli-protocol-' + str(i) + '.json') for i in range(3)]
    require(cli == gate.cli_protocol and [row.get('slot') for row in cli] == ['quota', 'pre_auth', 'final']
            and [charged(row) for row in cli] == [72, 36, 36], 'cli_slots')
    for item in cli:
        slot = item['slot']
        full = evidence.read('case-cli-' + slot + '.json')
        require(compatible(full) == item and full.get('run_id') == c.quota['binding']['run_id']
                and full.get('source_commit') == c.quota['binding']['source_commit']
                and full.get('candidate_sha256') == c.quota['binding']['candidate_sha']
                and full['terminal']['complete'] is True and full['terminal']['unknown_consumed'] == 0
                and full['terminal']['sql_dispatches'] == item['protocol_commands']
                and full['numeric_coverage']['all_protocol_visible'] is True
                and full['numeric_coverage']['numeric_calls_minus_reader'] == item['protocol_commands']
                and full['numeric_coverage']['temp_written'] == 0, 'cli_actual_binding')
        policy = decode(evidence.original(full['policy_ref'], 'case-cli-'+slot+'.policy.json', 16384))
        require(policy == full['policy'] and policy['slot'] == slot
                and policy['invocation_id'] == full['invocation_id'], 'cli_policy')
        evidence.original(full['ledger_ref'], 'case-cli-'+slot+'.ledger.txt', 262144)
        isolated = decode(evidence.original(full['isolation_ref'],
            'case-'+slot+'-cli-predispatch-cli-isolation-0.json', 524288))
        require(isolated['restored'] is True and isolated['commands'] in (4,8)
                and len(isolated['protocol']) == isolated['commands']
                and all(row['confirmed'] is True for row in isolated['protocol']), 'cli_restoration')
    auth = [evidence.read('auth-protocol-%02d.json' % i) for i in range(18)]
    workflow = evidence.read('workflow-auth-protocol.json')
    recomputed = counted_close(c.commands[:-1], evidence.read('integral-preflight.json'),
        cli, auth, workflow, c.quota['binding']['run_id'], c.quota['binding']['purpose'], c.quota['binding'])
    require(recomputed == c.closing_receipt, 'counted_close')
    for label in ('before', 'after_migration', 'final_pre', 'after_cleanup'):
        value = evidence.read('integral-gates-' + label + '.json')
        require(value['unchanged'] is True, 'preservation')
        check_io(value['io'], readonly=True)
    post = evidence.read('integral-gates-after_cleanup.json')
    require(post['stage'] == 'post' and post['catalog_excluded_schemas'] == []
            and post['temporary_schema_names'] == []
            and post['migrations'] == c.case_history.after and len(post['migrations']) == 48
            and post['absence'] and all(type(n) is int and n == 0 for n in post['absence'].values()),
            'final_absence')
    require(all(c.meter.state[k] is False for k in ('auth_maybe_live', 'guard', 'observer', 'controls')),
            'unreleased_state')
    workflow_io = evidence.read('integral-workflow-io.json')
    check_io(workflow_io['terminal'])
    require(len(workflow_io['pairs']) == 71, 'workflow_pairs')
    for index, pair in enumerate(workflow_io['pairs']):
        require(evidence.read('integral-io-pair-%03d.json' % index) == pair, 'workflow_pair_binding')
        check_io({**workflow_io['terminal'], 'last_pair': pair})
    for label in ('fixture_setup', 'fixture_closeout'):
        check_io(evidence.read('integral-' + label + '-io.json'))
    baseline = None
    stream_sha = c.quota['manifest']['sources'][OWN + 'runtime_stream.py']
    for label in ('before', 'before_cleanup', 'after_cleanup'):
        stream = evidence.read('integral-stream-' + label + '.json')
        require(stream['label'] == label and stream['source_sha256'] == stream_sha
                and stream['protected_equal'] is True and stream['query_text_read'] is False
                and stream['complete_by_same_snapshot_capacity'] is True
                and type(stream['rows']) is int and 0 <= stream['rows'] <= 106496
                and stream['rows'] == stream['protected_rows_bounded'], 'stream')
        require(baseline is None or (stream['tables'] == baseline['tables']
                and stream['plan'] == baseline['plan']), 'stream_drift')
        if baseline is None:
            baseline = stream
        require(stream['profiles'], 'stream_profiles')
        for profile in stream['profiles']:
            require(profile['own_wal_bytes'] == profile['own_temp_written'] == 0
                    and all(row['wal'] == row['temp_written'] == row['temp_read'] == 0
                            and 0 <= row['exec_ms'] <= 2500 for row in profile['queries']), 'stream_io')
    return [dict(slot=row['slot'], reserved_sql_commands=row['capacity_reserved'],
        charged_commands=row['charged_commands'], observed_sql_commands=row['protocol_commands'],
        observer_commands=len(row['observer_commands'])) for row in cli]
