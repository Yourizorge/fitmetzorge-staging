"""Distinct parent ownership of a deliberately unowned disposable negative control.

An intent precedes writer BEGIN. Actual rowversions are captured on that writer
before COMMIT, never added to the testcase's snapshots. A fresh, counted witness
after rejection must match every original rowversion. Old receipts without this
separate chain cannot be upgraded or reconstructed from current database rows.
"""
import copy
import re

from fixture_cleanup_runtime import Blocked, digest, validate_rows
import fixture_cleanup_runtime_sql as sql

OWNER = 'parent_disposable_negative_control'
CONTROL_LIMIT = 5  # One capture + BEGIN/CHECK/inventory/ROLLBACK; no retries.
ROLES = ('a_member', 'a_trainer', 'b_member')
COUNTS = {table: 3 if table == 'participants' else 2 if table == 'workspaces' else 1
          for table in sql.ORDER}


def row_multiset(rows):
    return digest(sorted(map(digest, rows)))


def retain_context(cleanup, case_name, commands, ids):
    """Durable setup intent, not ownership of rows that do not yet exist."""
    import hashlib
    if not cleanup.prepared or cleanup.attempted or cleanup.snapshots:
        raise Blocked('parent_setup_intent_sequence')
    context = dict(zip(('window', 'a', 'b'), (cleanup.args[0], *cleanup.args[1])))
    intent = {**cleanup.binding, 'case_name': case_name, 'context': context,
        'before_writer_begin': True, 'row_ownership_proven': False,
        'owner': OWNER if case_name == 'foreign_row' else 'parent_disposable_setup',
        'actor_hashes': {role: hashlib.sha256(ids[role].encode()).hexdigest() for role in ROLES},
        'planned_writes': [{'table': table, 'sql_sha256': hashlib.sha256(text.encode()).hexdigest(),
                            'args_sha256': digest(args)} for table, text, args in commands]}
    cleanup.write('parent-setup', intent)
    return copy.deepcopy(intent)


def rejected_case(receipt):
    if (receipt.get('status') != 'NO_GO' or receipt.get('reason') != 'cleanup_unowned_or_changed_row'
            or receipt.get('rollback_confirmed') is not True or receipt.get('commit_confirmed') is not False
            or receipt.get('commit_unknown') is not False or receipt.get('close_unknown')
            or receipt.get('returned_delete_count') != 0
            or not isinstance(receipt.get('protocol'), list)
            or any(e.get('phase', '').startswith('delete_') for e in receipt['protocol'])):
        raise Blocked('parent_negative_case_must_still_reject')
    for phase in ('inventory', 'rollback'):
        events = [e for e in receipt['protocol'] if e.get('phase') == phase]
        if len(events) != 1 or events[0].get('confirmed') is not True:
            raise Blocked('parent_negative_case_observation_missing')


def capture_rows(snapshot):
    rows = validate_rows({'rows': snapshot['rows'], 'xid': snapshot['xid']})
    xid = snapshot['xid']
    if (not isinstance(xid, str) or not xid.isdigit()
            or any(r['xmin'] != str(int(xid) % (2**32)) for r in rows)
            or {t: sum(r['table'] == t for r in rows) for t in sql.ORDER} != COUNTS):
        raise Blocked('parent_negative_writer_ownership')
    return rows


def validate_ownership(intent, owned, checked, receipt, actor_hashes):
    """Validate only the distinct negative-control chain, never arbitrary foreign rows."""
    if (intent.get('owner') != OWNER or intent.get('case_name') != 'foreign_row'
            or intent.get('before_writer_begin') is not True or intent.get('row_ownership_proven') is not False
            or intent.get('actor_hashes') != actor_hashes):
        raise Blocked('parent_negative_intent_binding')
    writes = intent.get('planned_writes')
    if (not isinstance(writes, list) or len(writes) != len(COUNTS)
            or {w.get('table') for w in writes} != set(COUNTS)
            or any(not isinstance(w.get(k), str) or not re.fullmatch('[a-f0-9]{64}', w[k])
                   for w in writes for k in ('sql_sha256', 'args_sha256'))):
        raise Blocked('parent_negative_write_plan')
    if (owned.get('owner') != OWNER or owned.get('setup_intent_sha256') != digest(intent)
            or owned.get('before_commit') is not True or owned.get('not_testcase_ownership') is not True
            or owned.get('previous') != digest([])):
        raise Blocked('parent_negative_capture_binding')
    rows = capture_rows(owned)
    rejected_case(receipt)
    if (checked.get('owner') != OWNER or checked.get('ownership_sha256') != digest(owned)
            or checked.get('case_receipt_sha256') != digest(receipt)
            or checked.get('row_multiset_sha256') != row_multiset(rows)
            or checked.get('unchanged') is not True or checked.get('read_only') is not True
            or checked.get('connection_closed') is not True or checked.get('original_claim_promoted') is not False):
        raise Blocked('parent_negative_unchanged_proof')
    return {k: copy.deepcopy(owned[k]) for k in ('rows', 'xid', 'previous', 'before_commit')}


class NegativeControl:
    def __init__(self, cleanup, intent):
        context = dict(zip(('window', 'a', 'b'), (cleanup.args[0], *cleanup.args[1])))
        if (intent.get('owner') != OWNER or intent.get('case_name') != 'foreign_row' or cleanup.snapshots
                or intent.get('context') != context
                or any(intent.get(k) != v for k, v in cleanup.binding.items())):
            raise Blocked('parent_negative_intent_required')
        self.cleanup, self.intent, self.owned = cleanup, copy.deepcopy(intent), None
        self.admitted_attempts = 0
        self.capture_attempted = self.check_attempted = False
        self.rollback_error_class = self.close_error_class = None

    def _execute(self, execute, connection, phase, text, args=(), *, rollback=False):
        # Reserve the last slot for rollback. The supplied Protocol durably charges
        # before dispatch; failed admission/uncertain sends still consume this slot.
        if self.admitted_attempts >= CONTROL_LIMIT - (0 if rollback else 1):
            raise Blocked('parent_negative_protocol_limit')
        self.admitted_attempts += 1
        return execute(connection, phase, text, args)

    def capture(self, writer, execute):
        if self.capture_attempted or self.cleanup.snapshots or self.cleanup.attempted:
            raise Blocked('parent_negative_duplicate_capture')
        self.capture_attempted = True
        if self.admitted_attempts != 0:
            raise Blocked('parent_negative_protocol_limit')
        rows = self._execute(execute, writer, 'foreign_row_parent_ownership', sql.INVENTORY, self.cleanup.args)
        if len(rows) != 1: raise Blocked('parent_negative_capture_shape')
        value = rows[0]['value']
        capture_rows(value)
        owned = {**self.cleanup.binding, **copy.deepcopy(value), 'owner': OWNER,
            'setup_intent_sha256': digest(self.intent), 'previous': digest([]),
            'before_commit': True, 'not_testcase_ownership': True}
        self.cleanup.write('parent-negative-owner', owned)
        self.owned = owned

    def check_after_case(self, receipt, execute):
        if self.owned is None or self.cleanup.snapshots:
            raise Blocked('parent_negative_not_independent')
        rejected_case(receipt)
        if self.check_attempted:
            raise Blocked('parent_negative_duplicate_check')
        self.check_attempted = True
        if CONTROL_LIMIT - self.admitted_attempts < 4:
            raise Blocked('parent_negative_protocol_limit')
        connection = self.cleanup.runtime.connect()
        begin_attempted = False
        primary = None
        try:
            # A lost BEGIN response can still leave an open transaction.
            begin_attempted = True
            self._execute(execute, connection, 'foreign_row_parent_check_begin', 'BEGIN TRANSACTION READ ONLY')
            limits = self._execute(execute, connection, 'foreign_row_parent_check_limits', sql.CHECK)
            fields = {'pg17', 'bounded_statement', 'bounded_lock', 'privileged', 'origin', 'unbound', 'readonly'}
            if len(limits) != 1 or set(limits[0]) != fields or any(v is not True for v in limits[0].values()):
                raise Blocked('parent_negative_readonly_limits')
            rows = self._execute(execute, connection, 'foreign_row_parent_check_inventory', sql.INVENTORY, self.cleanup.args)
            if len(rows) != 1: raise Blocked('parent_negative_witness_shape')
            observed = validate_rows(rows[0]['value'])
            if row_multiset(observed) != row_multiset(self.owned['rows']):
                raise Blocked('parent_negative_changed_during_case')
        except BaseException as error:
            primary = error
            raise
        finally:
            terminal_error = None
            if begin_attempted:
                try:
                    self._execute(execute, connection, 'foreign_row_parent_check_rollback', 'ROLLBACK', rollback=True)
                except BaseException as error:
                    self.rollback_error_class = type(error).__name__
                    if primary is not None:
                        primary.add_note('negative-control rollback failed: ' + type(error).__name__)
                    else:
                        terminal_error = error
            try:
                connection.close()
            except BaseException as error:
                self.close_error_class = type(error).__name__
                earlier = primary if primary is not None else terminal_error
                if earlier is not None:
                    earlier.add_note('negative-control close failed: ' + type(error).__name__)
                else:
                    terminal_error = error
            if primary is None and terminal_error is not None:
                raise terminal_error
        checked = {**self.cleanup.binding, 'owner': OWNER, 'ownership_sha256': digest(self.owned),
            'case_receipt_sha256': digest(receipt), 'row_multiset_sha256': row_multiset(observed),
            'unchanged': True, 'read_only': True, 'connection_closed': True, 'original_claim_promoted': False,
            'protocol_limit': CONTROL_LIMIT, 'admitted_attempts': self.admitted_attempts}
        self.cleanup.write('parent-negative-checked', checked)
        return checked
