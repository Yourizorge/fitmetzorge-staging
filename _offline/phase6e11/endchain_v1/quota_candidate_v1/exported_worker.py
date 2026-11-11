"""Pure collector-side worker component verification; never case admission.

Inputs are original bytes from an independently verified ZIP. Only trusted source
files are read from disk, as bytes, never imported or executed. Missing original
result/wait evidence cannot be replaced by a producer's hash or success flag.
"""
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import uuid

PREFIX = '_offline/phase6e11/endchain_v1/'
OWN = PREFIX + 'quota_candidate_v1/'
SOURCE = OWN + 'exported_worker.py'
REQUIRED_SOURCES = (
    SOURCE, OWN + 'runtime_terminal.py', OWN + 'runtime_adapter.py',
    OWN + 'runtime_faults.py', OWN + 'runtime_case_entry.py',
    OWN + 'runtime_auth.mjs', OWN + 'runtime_node.mjs',
    OWN + 'runtime_integral_workflow.mjs', PREFIX + 'registered_runner.py',
    PREFIX + 'registered_lifecycle.py', PREFIX + 'runtime_budget.py',
    PREFIX + 'metered_composition.py', PREFIX + 'closure.py',
    PREFIX + 'cli_envelope.py',
    OWN + 'runtime_worker_runner.py', OWN + 'runtime_worker_evidence.py',
    OWN + 'runtime_parent_workflow.py', OWN + 'runtime_recovery.py',
)
CASES = ('normal', 'mid_auth', 'controller', 'route_a', 'route_b', 'restore',
         'lost_response', 'duplicate', 'timeout', 'partial_fixture_cleanup',
         'cleanup_failure', 'final_check_failure', 'closure_failure')
ROLES = ('a_member', 'a_trainer', 'b_member')
AUTH_COST = {'issue': 11, 'verify': 21, 'getUser': 5,
             'refresh': 27, 'logout': 10, 'revoked_denial': 4}
BOOTSTRAP = {'local_fixture_cleanup', 'local_observer_schema', 'local_observer_triggers',
             'profile_seed_a_member', 'profile_seed_a_trainer',
             'profile_seed_b_member', 'operator_seed'}
BASE_REFS = {
    'terminal_ref': 'registered-worker-terminal.json',
    'finally_ref': 'case-registered-finally.json',
    'register_ref': 'runtime-command-meter.json',
    'terminal_witness_ref': 'case-runtime-terminal.json',
    'wait_ref': 'registered-worker-wait.json',
}
MAX_BYTES = 4_000_000


@dataclass(frozen=True)
class RawReference:
    path: str
    sha256: str
    bytes: int


@dataclass(frozen=True)
class MeterReplay:
    charged_commands: int
    unknown_commands: int
    phase_commands: tuple


@dataclass(frozen=True)
class WorkerVerification:
    status: str
    case_name: str
    missing: tuple = ()
    failures: tuple = ()
    evidence_refs: tuple = ()
    meter: MeterReplay | None = None
    returncode: int | None = None
    pending_proofs: tuple = ()

    @property
    def case_pass(self):
        return False

    @property
    def full_chain_admission(self):
        return False

    @property
    def hosted_admitted(self):
        return False


class Invalid(ValueError):
    pass


class Missing(ValueError):
    def __init__(self, *names):
        self.names = tuple(sorted(set(names)))


def need(value, code):
    if not value:
        raise Invalid(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def integer(value, minimum=0, maximum=2349):
    return type(value) is int and minimum <= value <= maximum


def decode(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            need(key not in value, 'duplicate_json_key')
            value[key] = item
        return value
    try:
        result = json.loads(raw, object_pairs_hook=unique,
                            parse_constant=lambda _: need(False, 'nonfinite_json'))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise Invalid('invalid_json') from None
    need(type(result) is dict, 'json_object')
    return result


def valid_path(name):
    return (type(name) is str and len(name) <= 240
            and re.fullmatch(r'[A-Za-z0-9_./-]+', name) is not None
            and all(part not in ('', '.', '..') for part in name.split('/')))


class Originals:
    def __init__(self, values):
        need(isinstance(values, Mapping) and len(values) <= 8192, 'originals_mapping')
        self.values, self.used = values, {}

    def read(self, name, ref=None):
        need(valid_path(name), 'original_path')
        if ref is not None:
            need(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'}
                 and ref['path'] == name and integer(ref['bytes'], 1, MAX_BYTES)
                 and re.fullmatch('[a-f0-9]{64}', str(ref['sha256'])), 'original_ref')
        if name not in self.values:
            raise Missing(name)
        raw = self.values[name]
        need(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, 'original_bytes')
        found = RawReference(name, sha(raw), len(raw))
        if ref is not None:
            need(found.sha256 == ref['sha256'] and found.bytes == ref['bytes'], 'original_hash')
        self.used[name] = found
        need(sum(item.bytes for item in self.used.values()) <= 96_000_000, 'originals_total_bound')
        return raw

    def object(self, name, ref=None):
        return decode(self.read(name, ref))


def source_bytes(root, name):
    need(valid_path(name), 'source_path')
    path = root / name
    if not path.exists():
        raise Missing('trusted_source:' + name)
    need(path.is_file() and path.resolve(strict=True).is_relative_to(root), 'source_escape')
    need(all(not p.is_symlink() and not getattr(p, 'is_junction', lambda: False)()
             for p in (path, *path.parents)), 'source_link')
    need(path.stat().st_size <= MAX_BYTES, 'source_size')
    raw = path.read_bytes()
    need(len(raw) <= MAX_BYTES, 'source_size')
    return raw


def check_sources(root, expected):
    need(isinstance(expected, Mapping) and len(expected) <= 8192, 'expected_sources')
    for name in REQUIRED_SOURCES:
        need(name in expected and type(expected[name]) is str
             and re.fullmatch('[a-f0-9]{64}', expected[name]), 'required_source')
        need(sha(source_bytes(root, name)) == expected[name], 'trusted_source_hash')
    need(sha(Path(__file__).read_bytes()) == expected[SOURCE], 'loaded_verifier_source')


def check_binding(binding):
    need(type(binding) is dict, 'binding_object')
    need(binding.get('environment') == 'disposable_ci'
         and binding.get('hosted_permission') is False
         and binding.get('execution_admitted') is False, 'binding_local_only')
    for key, pattern in (('source_commit', '[a-f0-9]{40}'),
                         ('candidate_sha', '[a-f0-9]{64}'), ('ci_run', '[1-9][0-9]{0,18}')):
        need(type(binding.get(key)) is str and re.fullmatch(pattern, binding[key]), 'binding_identity')
    need(type(binding.get('run_id')) is str, 'binding_run')
    try:
        run = uuid.UUID(binding['run_id'])
    except ValueError:
        raise Invalid('binding_run') from None
    need(str(run) == binding['run_id'] and run.version == 4, 'binding_run')
    need(integer(binding.get('cap'), 1) and type(binding.get('purpose')) is str
         and 0 < len(binding['purpose']) <= 256, 'binding_budget')


def replay_meter(value, cap):
    need(integer(value.get('limit'), 1, cap) and integer(value.get('used'), 1, cap), 'meter_limit')
    events = value.get('events')
    need(type(events) is list and 0 < len(events) <= cap, 'meter_events')
    used, unknown, phases = 0, 0, Counter()
    for number, event in enumerate(events, 1):
        need(type(event) is dict and type(event.get('confirmed')) is bool, 'meter_event')
        count = event.get('commands')
        need(integer(count, 1, cap) and type(event.get('number')) is int
             and event['number'] == number and type(event.get('first_command')) is int
             and event['first_command'] == used + 1, 'meter_sequence')
        need('actual_commands' not in event or type(event['actual_commands']) is int
             and event['actual_commands'] == count, 'meter_actual')
        phase = event.get('phase')
        need(type(phase) is str and re.fullmatch('[a-z0-9_]+', phase), 'meter_phase')
        used += count
        need(used <= value['limit'], 'meter_limit')
        if phase != 'safety':
            phases[phase] += count
        if not event['confirmed']:
            unknown += count
        if event.get('mutation') is True:
            reserve = event.get('reserved_cleanup')
            need(integer(reserve) and used + reserve <= value['limit'], 'prefix_reserve')
    need(used == value['used'] and type(value.get('phases')) is dict
         and all(type(n) is int for n in value['phases'].values())
         and dict(phases) == value['phases'] and value.get('complete') is (unknown == 0),
         'meter_totals')
    return MeterReplay(used, unknown, tuple(sorted(phases.items())))


def numeric_statements(value, commands):
    rows = value.get('statements')
    need(type(rows) is list and rows, 'managed_statement_rows')
    for row in rows:
        need(type(row) is dict and integer(row.get('calls'), 1)
             and type(row.get('temp_written')) is int and row['temp_written'] == 0,
             'managed_statement_numeric')
    need(sum(row['calls'] for row in rows) == commands, 'managed_calls')


def normal_replay(evidence, export, worker, commands, meter, binding):
    need(worker.get('status') == 'INTEGRAL_REAL_AUTH_WORKFLOW_CI_PASS'
         and type(worker.get('checks')) is int and worker['checks'] == 18
         and type(worker.get('durable_steps')) is int and worker['durable_steps'] == 89
         and worker.get('closure') == 'confirmed' and worker.get('environment') == 'disposable_ci'
         and type(worker.get('hosted_requests')) is int and worker['hosted_requests'] == 0
         and type(worker.get('emails_sent')) is int and worker['emails_sent'] == 0, 'worker_result')
    workflow = worker.get('workflow')
    need(type(workflow) is dict and all(type(workflow.get(k)) is int and workflow[k] == n
         for k, n in (('pairs', 71), ('deletes', 123), ('next_step', 83))), 'workflow_result')
    proof = worker.get('proof')
    need(type(proof) is list and len(proof) == 18, 'auth_proof')
    expected_order = ([(r, op) for r in ROLES for op in ('issue', 'verify', 'getUser', 'refresh')]
                      + [(r, op) for r in ROLES for op in ('logout', 'revoked_denial')])
    need([(r.get('role'), r.get('operation')) for r in proof] == expected_order, 'auth_order')
    need(all(type(r.get('after')) is dict and r['after'].get('pair_complete') is True
             and r['after'].get('exact_contract') is True for r in proof), 'auth_pairs')
    auth_refs = export.get('auth_refs')
    need(type(auth_refs) is list and len(auth_refs) == 18, 'auth_refs')
    managed = 0
    for i, (role, operation) in enumerate(expected_order):
        row = evidence.object('auth-protocol-%02d.json' % i, auth_refs[i])
        count = AUTH_COST[operation]
        need(row.get('role') == role and row.get('operation') == operation
             and type(row.get('commands')) is int and row['commands'] == count, 'auth_protocol')
        numeric_statements(row, count)
        managed += count
    work = evidence.object('workflow-auth-protocol.json', export.get('workflow_ref'))
    need(type(work.get('commands')) is int and work['commands'] == 360
         and type(work.get('verified_calls')) is int and work['verified_calls'] == 72, 'workflow_protocol')
    numeric_statements(work, 360)
    managed += 360
    pre = evidence.object('integral-preflight.json', export.get('preflight_ref'))
    need(type(pre.get('commands')) is list and len(pre['commands']) == 4
         and all(row.get('confirmed') is True for row in pre['commands']), 'preflight_commands')
    refs = export.get('cli_refs')
    need(type(refs) is list and len(refs) == 3, 'cli_refs')
    cli_charge = 0
    for i, (slot, capacity) in enumerate((('quota', 64), ('pre_auth', 28), ('final', 28))):
        item = evidence.object('cli-protocol-%d.json' % i, refs[i])
        need(item.get('slot') == slot and type(item.get('capacity_reserved')) is int
             and item['capacity_reserved'] == capacity
             and type(item.get('charged_commands')) is int
             and item['charged_commands'] == capacity + 8
             and integer(item.get('protocol_commands'), 0, capacity)
             and type(item.get('observer_commands')) is list and len(item['observer_commands']) == 8,
             'cli_charges')
        cli_charge += capacity + 8
    need(commands and commands[-1].get('phase') == 'final_closure'
         and all(r.get('phase') != 'final_closure' for r in commands[:-1]), 'closure_order')
    native = sum(row['phase'] not in BOOTSTRAP for row in commands[:-1])
    total = native + 4 + cli_charge + managed + 1
    need(total <= binding['cap'] and total == meter.charged_commands, 'closure_total')
    closure = evidence.object('integral-closure.json', export.get('closure_ref'))
    expected = dict(run_id=binding['run_id'], purpose=binding['purpose'],
                    native_before_close=native, managed_auth=managed, preflight=4,
                    cli=cli_charge, closing_commands=1, global_commands=total, confirmed=True)
    need(all(type(closure.get(k)) is type(v) and closure[k] == v for k, v in expected.items()),
         'closure_binding')


def verify_exported_worker(originals, *, case, binding, expected_sources, trusted_root):
    """Verify one worker component; other semantic owners remain mandatory.

    No artifact code imports, subprocesses, network or DB access. The supplied
    source inventory and binding must originate from the prepared candidate, not
    be copied from this artifact. ZIP authenticity is the caller's prerequisite.
    """
    evidence = None
    try:
        need(case in CASES, 'worker_case_not_early')
        check_binding(binding)
        root = Path(trusted_root).resolve(strict=True)
        check_sources(root, expected_sources)
        evidence = Originals(originals)
        if 'case-worker-export.json' not in originals:
            names = ['case-worker-export.json', 'registered-worker-wait.json']
            if case == 'normal':
                names.append('case-worker-result.json')
            raise Missing(*(name for name in names if name not in originals))
        export = evidence.object('case-worker-export.json')
        need(export.get('format') == 'case-worker-export-v1' and export.get('binding') == binding
             and export.get('case_name') == case, 'export_binding')
        hashes = export.get('source_hashes')
        need(type(hashes) is dict and set(REQUIRED_SOURCES) <= set(hashes)
             and all(expected_sources.get(name) == value for name, value in hashes.items()), 'export_sources')
        # Every named source is independently checked as raw bytes, never run.
        for name, value in hashes.items():
            need(sha(source_bytes(root, name)) == value, 'producer_source_hash')
        trace_name = ('integral-complete-protocol-trace.json' if case == 'normal'
                      else 'registered-incomplete-protocol-trace.json')
        refs = dict(BASE_REFS, trace_ref=trace_name)
        if case == 'normal':
            refs['worker_result_ref'] = 'case-worker-result.json'
        else:
            refs['fault_ref'] = 'case-fault-boundary.json'
            need(export.get('worker_result_ref') is None, 'fault_result_not_null')
        values, missing = {}, []
        for key, name in refs.items():
            need(key in export and export[key] is not None, 'missing_export_ref_' + key)
            try:
                values[key] = evidence.object(name, export[key])
            except Missing as error:
                missing.extend(error.names)
        if missing:
            raise Missing(*missing)
        terminal, final = values['terminal_ref'], values['finally_ref']
        witness, wait = values['terminal_witness_ref'], values['wait_ref']
        trace, registered = values['trace_ref'], values['register_ref']
        need(wait.get('format') == 'registered-worker-wait-v1' and wait.get('binding') == binding
             and wait.get('case_name') == case and integer(wait.get('pid'), 1, 2**31-1)
             and wait.get('wait_completed') is True and wait.get('reaped') is True
             and integer(wait.get('returncode'), -255, 255)
             and wait.get('wait_error_class') is None and wait.get('automatic_retry') is False
             and wait.get('termination_error_class') is None and wait.get('watchdog_fired') is False
             and wait.get('watchdog_stopped') is True and wait.get('watchdog_error_class') is None,
             'actual_wait')
        need(terminal.get('worker_terminated') is True and terminal.get('automatic_retry') is False
             and terminal.get('secrets_exported') is False
             and integer(terminal.get('messages'), 1, 200)
             and terminal.get('termination_error_class') is None, 'terminal')
        need(final.get('retry') is False and final.get('worker_owned') is True
             and final.get('covered_by') == 'case.core'
             and final.get('runtime_meter') == registered, 'finally_meter')
        meter = replay_meter(registered, binding['cap'])
        commands = trace.get('commands')
        need(type(commands) is list and 0 < len(commands) <= 8192
             and all(type(row) is dict and type(row.get('command')) is int
                     and row['command'] == i and type(row.get('confirmed')) is bool
                     and type(row.get('phase')) is str for i, row in enumerate(commands, 1)), 'trace_sequence')
        need(final.get('commands') == [{**row, 'covered_by': 'case.core'} for row in commands], 'trace_finally')
        need(witness.get('format') == 'registered-runtime-terminal-witness-v1'
             and witness.get('case_name') == case and witness.get('run_id') == binding['run_id']
             and witness.get('source_commit') == binding['source_commit']
             and witness.get('ci_run') == binding['ci_run']
             and witness.get('candidate_sha256') == binding['candidate_sha']
             and witness.get('case_pass') is False and witness.get('full_chain_admission') is False
             and witness.get('hosted_admitted') is False, 'witness_binding')
        witness_hashes = witness.get('source_hashes')
        need(type(witness_hashes) is dict and witness_hashes
             and all(hashes.get(name) == value for name, value in witness_hashes.items()), 'witness_sources')
        need(witness.get('meter') == dict(charged_commands=meter.charged_commands,
             unknown_commands=meter.unknown_commands, phase_commands=dict(meter.phase_commands)), 'witness_meter')
        raw_refs = witness.get('evidence_refs')
        need(type(raw_refs) is list and 0 < len(raw_refs) <= 512, 'witness_refs')
        names = set()
        for ref in raw_refs:
            need(type(ref) is dict and type(ref.get('path')) is str and ref['path'] not in names,
                 'witness_duplicate_ref')
            names.add(ref['path'])
            evidence.read(ref['path'], ref)
        required_originals = {BASE_REFS[k] for k in ('terminal_ref', 'finally_ref')} | {trace_name}
        need(required_originals <= names, 'witness_missing_originals')
        normal = case == 'normal'
        need(terminal.get('complete') is normal and final.get('complete') is normal, 'terminal_complete')
        pending = ['root_register_and_phase_budget_replay', 'independent_fixture_auth_closeout',
                   'source_bound_lifecycle_and_read_io', 'original_cli_ledger_policy_replay',
                   'auth_pair_metadata_semantics']
        if normal:
            need(wait['returncode'] == 0 and meter.unknown_commands == 0
                 and final.get('original_exception_class') is None
                 and terminal.get('cleanup_errors') == [] and final.get('secondary') == []
                 and terminal.get('guard_audit_removed') is True
                 and all(row['confirmed'] is True for row in commands)
                 and trace.get('environment') == 'disposable_ci'
                 and type(trace.get('outer_sql_commands')) is int
                 and trace['outer_sql_commands'] == len(commands)
                 and trace.get('full_chain_admission') is False, 'normal_terminal')
            worker = values['worker_result_ref']
            need(witness.get('worker_result_sha256') == sha(canonical(worker)), 'worker_result_hash')
            need(witness.get('status') == 'REGISTERED_WORKER_COMPLETE'
                 and witness.get('original_exception_class') is None
                 and witness.get('original_fault_code') is None, 'normal_witness')
            fault = final.get('fault')
            need(type(fault) is dict and fault.get('case') == case
                 and fault.get('run_id') == binding['run_id'] and fault.get('fault_observed') is False
                 and fault.get('fault') is None, 'normal_fault')
            normal_replay(evidence, export, worker, commands, meter, binding)
        else:
            fired = values['fault_ref']
            need(fired.get('case') == case and fired.get('run_id') == binding['run_id']
                 and fired.get('source_commit') == binding['source_commit']
                 and fired.get('ci_run') == binding['ci_run']
                 and fired.get('candidate_sha') == binding['candidate_sha']
                 and fired.get('original_error_code') == 'case_injected_' + case
                 and fired.get('automatic_retry') is False, 'fault_binding')
            fault = final.get('fault')
            need(type(fault) is dict and fault.get('fault') == fired
                 and fault.get('case') == case and fault.get('run_id') == binding['run_id']
                 and fault.get('fault_observed') is True, 'fault_finally')
            need(type(final.get('original_exception_class')) is str
                 and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,127}', final['original_exception_class'])
                 and witness.get('original_exception_class') == final['original_exception_class']
                 and witness.get('original_fault_code') == fired['original_error_code']
                 and witness.get('worker_result_sha256') is None
                 and witness.get('status') == 'REGISTERED_FAULT_TERMINATED'
                 and trace.get('runtime_meter') == registered and trace.get('complete') is False
                 and trace.get('automatic_retry') is False, 'fault_terminal')
            pending += ['source_derived_fault_selector_and_recovery_edge', 'fault_cleanup_independent_proof']
        if meter.unknown_commands:
            pending.append('unknown_consumed_commands')
        if terminal.get('cleanup_errors') or final.get('secondary'):
            pending.append('registered_cleanup_secondary')
        return WorkerVerification('VERIFIED_COMPONENT', case,
            evidence_refs=tuple(sorted(evidence.used.values(), key=lambda r: r.path)),
            meter=meter, returncode=wait['returncode'], pending_proofs=tuple(pending))
    except Missing as error:
        return WorkerVerification('MISSING_EVIDENCE', case, missing=error.names)
    except Invalid as error:
        return WorkerVerification('INVALID_EVIDENCE', case, failures=(str(error),))
    except (OSError, TypeError, KeyError, ValueError, RecursionError):
        # Never echo artifact values, OS paths, query text or exception messages.
        return WorkerVerification('INVALID_EVIDENCE', case, failures=('malformed_input',))
