"""Pure offline evidence-state verifier. Does not execute SQL or make requests."""
import json
import pathlib
import sys
import time
import uuid
from registry import PHASES, contracts

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'fingerprint_v1'))
from guard import save, digest, Stop

CANARY_BUDGET = {'full_cycles': 1, 'query_commands': 14, 'max_retries': 0,
                 'statement_seconds': 30, 'run_seconds': 120, 'temp_write_bytes': 0}
REQUIRED_GATES = ('pg17_equivalent', 'complete_write_coverage', 'io_recovered',
                  'stable_latency', 'no_worker', 'historical_expectation_bound', 'stream_transport_verified')


def canary_decision(gates):
    missing = [name for name in REQUIRED_GATES if gates.get(name) is not True]
    return {'allowed': not missing, 'blockers': missing, 'budget': CANARY_BUDGET,
            'automatic_retry': False, 'workflow_proofrun_allowed': False}


def query_plan(actions, full_cycles=3):
    # Every scoped pair: BEGIN/settings/snapshot/COMMIT twice, plus action RPC(s).
    parts = {'full_collectors': full_cycles * 6, 'targeted_pairs': actions * 8,
             'action_requests_upper_bound': actions * 3, 'metadata_reserve': 8}
    total = sum(parts.values())
    return {'actions': actions, 'parts': parts, 'total_commands': total,
            'current_limit': 128, 'admitted_under_current_limit': total <= 128,
            'limits_silently_changed': False}


class EvidenceGate:
    def __init__(self, path, query_limit=128):
        self.path = pathlib.Path(path)
        self.path.mkdir()
        self.run_id = str(uuid.uuid4())
        self.limit = min(query_limit, 128)
        self.used = 0
        self.current = None
        self.step = 0
        self.halted = False
        self.history = []
        self.write('run_created')

    def write(self, status, **extra):
        entry = {'run_id': self.run_id, 'step_id': self.step, 'status': status,
                 'timestamp_ns': time.time_ns(),
                 'previous_sha256': digest(self.history[-1]) if self.history else None, **extra}
        save(self.path / ('%04d.json' % len(self.history)), entry)
        self.history.append(entry)

    def fail(self, reason):
        if not self.halted:
            self.halted = True
            self.write('NO_GO', reason=reason, next_step_allowed=False, cleanup_allowed=False)
        raise Stop(reason)

    def check(self):
        if self.halted:
            raise Stop('retained_NO_GO')

    def query(self, retry=False):
        self.check()
        if retry or self.used >= self.limit:
            self.fail('retry_or_query_budget')
        self.used += 1
        self.write('query_reserved', used=self.used)

    def before(self, route_id, evidence):
        self.check()
        if self.current:
            self.fail('previous_pair_not_validated')
        route = next((x for x in contracts() if x['route_id'] == route_id), None)
        if route is None:
            self.fail('unregistered_write_route')
        required = {'actor_sha256','request_sha256','scope_sha256','snapshot_sha256','table_names'}
        if not required <= evidence.keys() or any(not isinstance(evidence[k], str) or len(evidence[k]) != 64 for k in required - {'table_names'}):
            self.fail('before_binding_missing')
        tables = sorted({x['table'] for x in route['effects']})
        if evidence['table_names'] != tables:
            self.fail('table_coverage_missing')
        self.step += 1
        self.current = {'route': route, 'before': evidence, 'phase': 'before_saved'}
        self.write('before_saved', route_id=route_id, evidence_sha256=save(self.path / ('before-%d.json' % self.step), evidence))

    def advance(self, status, receipt=None):
        self.check()
        if not self.current:
            self.fail('no_current_step')
        prior = self.current['phase']
        if status not in ('action_started', 'action_confirmed') or PHASES.index(status) != PHASES.index(prior) + 1:
            self.fail('phase_order')
        if status == 'action_confirmed':
            required = {'actor_sha256','request_sha256','scope_sha256','transaction_sha256','outcome'}
            if not isinstance(receipt, dict) or not required <= receipt.keys() or receipt['outcome'] not in ('committed','denied','replayed'):
                self.fail('transaction_receipt_missing')
            if any(receipt[k] != self.current['before'][k] for k in ('actor_sha256','request_sha256','scope_sha256')):
                self.fail('receipt_binding_mismatch')
            if len(receipt['transaction_sha256']) != 64:
                self.fail('transaction_binding_missing')
            self.write(status, receipt_sha256=save(self.path / ('receipt-%d.json' % self.step), receipt))
        else:
            self.write(status)
        self.current['phase'] = status

    def after(self, evidence):
        self.check()
        if not self.current or self.current['phase'] != 'action_confirmed':
            self.fail('phase_order')
        if evidence is None:
            self.fail('after_saved_missing')
        before = self.current['before']
        if set(evidence) != set(before) or any(evidence[k] != before[k] for k in
                ('actor_sha256','request_sha256','scope_sha256','table_names')):
            self.fail('after_binding_mismatch')
        if not isinstance(evidence['snapshot_sha256'], str) or len(evidence['snapshot_sha256']) != 64:
            self.fail('after_snapshot_missing')
        self.write('after_saved', evidence_sha256=save(self.path / ('after-%d.json' % self.step), evidence))
        self.current['phase'] = 'after_saved'

    def validate_pair(self, protected_equal, explained_changes):
        self.check()
        if not self.current or self.current['phase'] != 'after_saved':
            self.fail('after_saved_missing')
        # Inputs are synthetic assertions in this simulator, NOT hosted verification.
        if protected_equal is not True or explained_changes is not True:
            self.fail('drift_or_unexplained_change')
        self.write('pair_validated', verifier='offline-synthetic-only')
        self.current = None
        self.write('next_step_allowed')

    def cleanup(self, sealed_manifest=False):
        self.check()
        if self.current or not self.history or self.history[-1]['status'] != 'next_step_allowed' or not sealed_manifest:
            self.fail('cleanup_before_validated_sealed_pair')
        self.write('cleanup_admitted_offline_simulation')

    def close(self):
        if self.current and not self.halted:
            self.fail('missing_pair_on_close')
