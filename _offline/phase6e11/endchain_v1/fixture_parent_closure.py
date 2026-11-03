"""Separate disposable suffix; never changes original claims or touches Auth.

Main must bind this module and its project imports before calling:
    run(gate, contexts={case_uuid: original_context}, barrier={path, sha256})
Call AFTER fixture journal packaging, with the original gate.save restored.
contexts are original window/a/b UUIDs, checked against the original scope hash;
do not reconstruct ownership from current rows. A missing context blocks its case.
The separately persisted parent/B barrier must bind NEW_RUN, actor_hashes and
all fixture_case_ids, with worker_joined/writers_closed/mint_barrier true and
nonempty evidence_refs ({path, sha256}). Main/B owns the truth of that evidence.
This helper does not manufacture a GoTrue barrier or remove Auth objects.

Only confirmed original rollback or previously undispatched cleanup may get a
new suffix. Unknown COMMIT is never replayed. Registry deletion requires every
case resolved plus the exact committed bootstrap. All charges are additional
local diagnostic protocol commands, never an expansion of the 2349 run budget.
"""
import copy
import hashlib
import json
import os
import pathlib
import re
import uuid

from admission_binding import NEW_RUN
from admission_journal import Journal, verify as verify_journal
from fixture_cleanup_runtime import Blocked, Cleanup, Protocol, digest, validate_rows
import fixture_cleanup_runtime_sql as sql
from native_runtime import NativeRuntime
from fixture_control_ownership import row_multiset, validate_ownership

PREFIX = 'fixture-parent-closure'
ROLES = ('a_member', 'a_trainer', 'b_member')
REGISTRY = """select jsonb_build_object(
 'identities',coalesce((select jsonb_agg(jsonb_build_object('id',user_id::text,
 'role',role,'provenance_sha',provenance_sha,'enabled',enabled))
 from fmz6e11_private.identities where user_id=any($1::uuid[])),'[]'::jsonb),
 'operators',coalesce((select jsonb_agg(jsonb_build_object('id',user_id::text,'enabled',enabled))
 from fmz6e11_private.operators where user_id=any($1::uuid[])),'[]'::jsonb)) value"""
DELETE_OPERATOR = """delete from fmz6e11_private.operators
 where user_id=$1::uuid and enabled=true returning user_id::text id,enabled"""
DELETE_IDENTITIES = """delete from fmz6e11_private.identities i
 using jsonb_to_recordset($1::jsonb) e(id uuid,role text,provenance_sha text)
 where i.user_id=e.id and i.role=e.role and i.provenance_sha=e.provenance_sha
 and i.enabled=true returning i.user_id::text id,i.role,i.provenance_sha,i.enabled"""
REGISTRY_LOCK = sql.LOCK.replace(' IN SHARE',
    ',fmz6e11_private.identities,fmz6e11_private.operators IN SHARE')
REGISTRY_LIMIT = 11  # 7 transaction commands + 4 fresh absence commands; failure prefixes <=11.
CASE_LIMIT = len(sql.plan()['normal'])


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read_record(out, relative, expected=None):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise Blocked('parent_receipt_path')
    name = pathlib.PurePosixPath(relative)
    if name.is_absolute() or any(p in ('.', '..') for p in name.parts):
        raise Blocked('parent_receipt_path')
    root = pathlib.Path(out)
    if not root.is_absolute(): raise Blocked('parent_receipt_root')
    for part in (root, *root.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise Blocked('parent_receipt_symlink')
    root = root.resolve(strict=True)
    path = root.joinpath(*name.parts)
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise Blocked('parent_receipt_symlink')
    if not path.resolve(strict=True).is_relative_to(root) or path.stat().st_size > 2000000:
        raise Blocked('parent_receipt_size_or_escape')
    raw = path.read_bytes()
    if len(raw) > 2000000: raise Blocked('parent_receipt_size_or_escape')
    if expected is not None and sha(raw) != expected:
        raise Blocked('parent_receipt_changed')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise Blocked('parent_receipt_shape')
    return value, sha(raw)


def reference(out, ref):
    if (not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}
            or not isinstance(ref['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', ref['sha256'])):
        raise Blocked('parent_receipt_reference')
    return read_record(out, ref['path'], ref['sha256'])[0]


class Evidence:
    def __init__(self, gate):
        self.gate, self.hashes = gate, {}
        self.index, index_sha = read_record(gate.out, 'admission-fixture-journal-index.json')
        def chunk(name):
            value, value_sha = read_record(gate.out, name)
            self.hashes[name] = value_sha
            return value
        verify_journal(self.index, chunk)
        self.hashes['admission-fixture-journal-index.json'] = index_sha

    def get(self, name):
        entry = self.index['records'].get(name)
        if not isinstance(entry, dict): raise Blocked('parent_original_record_missing')
        path = 'admission-fixture-private-journal/' + name
        value, value_sha = read_record(self.gate.out, path, entry['sha256'])
        self.hashes[path] = value_sha
        return value

    def unchanged(self):
        for path, expected in self.hashes.items(): read_record(self.gate.out, path, expected)


def ownership(evidence, case, context, *, actor_hashes=None):
    # Cleanup validates fresh UUIDs before any connection is possible.
    from fixture_cleanup_evidence import parameters
    args = parameters(context)
    prefix = 'fixture-cleanup-' + case['fixture_case'] + '-'
    bound = {'preparation_run': NEW_RUN, 'case': args[0], 'scope_sha256': digest(args), 'component_only': True}
    if args[0] != case['fixture_case']: raise Blocked('parent_scope_changed')
    def original(name):
        value = evidence.get(prefix + name + '.json')
        if any(value.get(k) != v for k, v in bound.items()): raise Blocked('parent_original_binding')
        return value
    baseline = original('baseline')
    if baseline.get('rows') != [] or baseline.get('source') != 'actual_empty_inventory':
        raise Blocked('parent_original_baseline')
    if case['case'] == 'foreign_row':
        if any(n.startswith(prefix + 'writer-') for n in evidence.index['records']):
            raise Blocked('parent_negative_case_not_unowned')
        intent = original('parent-setup')
        if intent.get('context') != context or actor_hashes is None:
            raise Blocked('parent_negative_context_or_actors')
        return [validate_ownership(intent, original('parent-negative-owner'),
                  original('parent-negative-checked'), case['receipt'], actor_hashes)]
    terminal = case['receipt']
    if terminal.get('commit_unknown') or terminal.get('commit_confirmed'):
        raise Blocked('parent_original_commit_not_replayable')
    if case['case'] == 'missing_barrier':
        if terminal.get('reason') != 'cleanup_writer_barrier_required':
            raise Blocked('parent_original_barrier_reason')
    elif terminal.get('rollback_confirmed') is not True or terminal.get('close_unknown'):
        raise Blocked('parent_original_transaction_not_closed')
    snapshots = []
    names = sorted(n for n in evidence.index['records'] if n.startswith(prefix + 'writer-'))
    if not names or len(names) > 16: raise Blocked('parent_no_original_writer_ownership')
    prior = set()
    for i, name in enumerate(names):
        if name != prefix + 'writer-%04d.json' % i: raise Blocked('parent_writer_sequence')
        record = original('writer-%04d' % i)
        snapshot = {k: record[k] for k in ('rows', 'xid', 'previous', 'before_commit')}
        if snapshot['previous'] != digest(snapshots) or snapshot['before_commit'] is not True:
            raise Blocked('parent_writer_chain')
        rows = validate_rows({'rows': snapshot['rows'], 'xid': snapshot['xid']})
        if not isinstance(snapshot['xid'], str) or not snapshot['xid'].isdigit():
            raise Blocked('parent_writer_xid')
        for row in rows:
            if digest(row) not in prior and row['xmin'] != str(int(snapshot['xid']) % (2**32)):
                raise Blocked('parent_writer_row_not_owned')
        prior.update(map(digest, rows)); snapshots.append(snapshot)
    return snapshots


class NegativeControlClosure(Cleanup):
    """Unlike general partial cleanup, a known control must be wholly unchanged."""
    def inventory(self, connection, phase):
        value = super().inventory(connection, phase)
        if phase == 'inventory':
            observed = validate_rows(value)
            if len(self.snapshots) != 1 or row_multiset(observed) != row_multiset(self.snapshots[0]['rows']):
                raise Blocked('parent_negative_changed_before_delete')
        return value


def expected_registry(ids):
    provenance = sha(json.dumps(ids, sort_keys=True).encode())
    return {'identities': [{'id': ids[r], 'role': r, 'provenance_sha': provenance, 'enabled': True}
                           for r in ROLES],
            'operators': [{'id': ids['a_trainer'], 'enabled': True}]}


def same_rows(actual, expected):
    return isinstance(actual, list) and sorted(map(digest, actual)) == sorted(map(digest, expected))


def close_registry(runtime, ids, save, charge):
    """Exact bootstrap-only deletion; retained fixture FKs are never cascaded."""
    expected = expected_registry(ids)
    protocol = Protocol(charge)
    result = {'status': 'NO_GO', 'commit_confirmed': False, 'commit_unknown': False,
              'absence_confirmed': False, 'deletion_proven': False}
    connection = None
    commit_attempted = False
    def query(db, phase, text, args=()): return protocol.execute(db, phase, text, args)
    def limits(db, readonly):
        rows = query(db, 'registry_check', sql.CHECK)
        fields = {'pg17', 'bounded_statement', 'bounded_lock', 'privileged', 'origin', 'unbound', 'readonly'}
        if (len(rows) != 1 or set(rows[0]) != fields or rows[0]['readonly'] is not readonly
                or any(rows[0][k] is not True for k in fields - {'readonly'})):
            raise Blocked('parent_registry_session_limits')
    def inventory(db, phase):
        rows = query(db, phase, REGISTRY, [list(ids.values())])
        if len(rows) != 1 or set(rows[0].get('value', {})) != set(expected):
            raise Blocked('parent_registry_inventory_shape')
        return rows[0]['value']
    try:
        connection = runtime.connect()
        query(connection, 'registry_begin', 'BEGIN')
        limits(connection, False)
        query(connection, 'registry_lock', REGISTRY_LOCK)
        before = inventory(connection, 'registry_before')
        if any(not same_rows(before[k], expected[k]) for k in expected):
            raise Blocked('parent_bootstrap_changed_or_not_owned')
        save('registry-before.json', {'expected': expected, 'observed': before})
        operators = query(connection, 'registry_delete_operator', DELETE_OPERATOR, [ids['a_trainer']])
        if not same_rows(operators, expected['operators']): raise Blocked('parent_operator_delete_mismatch')
        save('registry-delete-operator.json', {'returned': operators, 'commit_confirmed': False})
        identities = query(connection, 'registry_delete_identities', DELETE_IDENTITIES,
                           [json.dumps(expected['identities'])])
        if not same_rows(identities, expected['identities']): raise Blocked('parent_identity_delete_mismatch')
        save('registry-delete-identities.json', {'returned': identities, 'commit_confirmed': False})
        save('registry-commit-intent.json', {'identities': 3, 'operators': 1})
        commit_attempted = True
        query(connection, 'registry_commit', 'COMMIT')
        result['commit_confirmed'] = True
    except BaseException as error:
        result.update(error_class=type(error).__name__, reason=str(error) if isinstance(error, Blocked)
                      else 'parent_registry_transport_or_storage_error')
        result['commit_unknown'] = commit_attempted and not result['commit_confirmed']
        if connection is not None and not commit_attempted:
            try:
                query(connection, 'registry_rollback', 'ROLLBACK')
                result['rollback_confirmed'] = True
            except BaseException: result['rollback_confirmed'] = False
    finally:
        if connection is not None:
            try: connection.close()
            except BaseException: result['close_unknown'] = True
    witness = None
    try:
        witness = runtime.connect()
        query(witness, 'registry_absence_begin', 'BEGIN TRANSACTION READ ONLY')
        limits(witness, True)
        remaining = inventory(witness, 'registry_absence')
        query(witness, 'registry_absence_rollback', 'ROLLBACK')
        result['remaining_counts'] = {k: len(v) for k, v in remaining.items()}
        result['absence_confirmed'] = all(v == [] for v in remaining.values())
    except BaseException as error: result['absence_error_class'] = type(error).__name__
    finally:
        if witness is not None:
            try: witness.close()
            except BaseException: result['close_unknown'] = True
    good = (result['commit_confirmed'] and result['absence_confirmed']
            and not result.get('error_class') and not result.get('close_unknown'))
    result.update(status='SCOPED_CLOSURE_CONFIRMED' if good else 'NO_GO', deletion_proven=good,
                  deleted_identities=3 if good else None, deleted_operators=1 if good else None,
                  protocol=copy.deepcopy(protocol.events))
    save('registry-result.json', result)
    return result


def run(gate, *, contexts=None, barrier):
    """Return NO_GO global status even when the independent scoped suffix succeeds."""
    if (os.environ.get('GITHUB_ACTIONS') != 'true'
            or os.environ.get('GITHUB_REPOSITORY') != 'Yourizorge/fitmetzorge-staging'
            or os.environ.get('GITHUB_REF') != 'refs/heads/main'
            or getattr(gate, 'container', None) != 'supabase_db_fmz-db41-ci'):
        raise Blocked('parent_disposable_ci_required')
    # Exclusive claim directory also prevents a second process or invocation retry.
    journal = Journal(pathlib.Path(gate.out)/(PREFIX+'-private'), gate.save, PREFIX+'-journal')
    result = {'status': 'NO_GO', 'suffix_status': 'BLOCKED', 'preparation_run': NEW_RUN,
        'hosted_admitted': False, 'full_chain_admission': False, 'full_cleanup_proven': False,
        'auth_objects_touched': False, 'original_claims_released': False,
        'budget_domain': 'additional_disposable_local_diagnostic_not_2349',
        'cases': [], 'protocol': [], 'planned_protocol_limit': 0, 'registry': None}
    runtime = None
    evidence = None
    fixed_hashes = {}
    def save(name, value): journal.save(PREFIX+'-'+name, value)
    def charge(event):
        if len(result['protocol']) >= result['planned_protocol_limit']:
            raise Blocked('parent_protocol_limit')
        item = {**event, 'parent_ordinal': len(result['protocol']) + 1}
        save('charge-%04d.json' % item['parent_ordinal'], item)
        result['protocol'].append(item)
    try:
        evidence = Evidence(gate)
        detail = evidence.get('fixture-cleanup-component-detail.json')
        if detail.get('status') != 'COMPONENT_PASS' or detail.get('preparation_run') != NEW_RUN:
            raise Blocked('parent_durable_component_completion_required')
        cases = detail['cases']
        if not isinstance(cases, list) or not 1 <= len(cases) <= 11:
            raise Blocked('parent_case_bound')
        case_ids = [case['fixture_case'] for case in cases]
        if contexts is None:
            contexts = {case_id: evidence.get('fixture-cleanup-'+case_id+'-parent-setup.json')['context']
                        for case_id in case_ids}
        if len(set(case_ids)) != len(case_ids) or not isinstance(contexts, dict) or set(contexts) - set(case_ids):
            raise Blocked('parent_case_scope')
        bootstrap, bootstrap_sha = read_record(gate.out, 'admission-fixture-bootstrap.json')
        fixed_hashes['admission-fixture-bootstrap.json'] = bootstrap_sha
        ids = copy.deepcopy(gate.fixture_cleanup_ids)
        if (set(ids) != set(ROLES) or len(set(ids.values())) != 3
                or any(not isinstance(v, str) or str(uuid.UUID(v)) != v for v in ids.values())
                or bootstrap.get('status') != 'DISPOSABLE_BOOTSTRAP_PASS'
                or bootstrap.get('registered_accounts') != 3
                or bootstrap.get('existing_rows_overwritten') is not False
                or bootstrap.get('commit_confirmed') is not True
                or bootstrap.get('after_registry_confirmed') is not True
                or bootstrap.get('before') != {'identities': 0, 'operators': 0}
                or bootstrap.get('actor_hashes') != {k: sha(v.encode()) for k, v in ids.items()}):
            raise Blocked('parent_bootstrap_ownership_required')
        terminal = reference(gate.out, barrier)
        fixed_hashes[barrier['path']] = barrier['sha256']
        if (terminal.get('preparation_run') != NEW_RUN
                or terminal.get('actor_hashes') != bootstrap['actor_hashes']
                or sorted(terminal.get('fixture_case_ids', [])) != sorted(case_ids)
                or any(terminal.get(k) is not True for k in ('worker_joined', 'writers_closed', 'mint_barrier'))
                or not isinstance(terminal.get('evidence_refs'), list)
                or not 1 <= len(terminal['evidence_refs']) <= 16):
            raise Blocked('parent_independent_terminal_barrier_required')
        for ref in terminal['evidence_refs']:
            reference(gate.out, ref); fixed_hashes[ref['path']] = ref['sha256']
        eligible = []
        unresolved = []
        for case in cases:
            previous = case['receipt']
            if previous.get('status') == 'COMPONENT_PASS' and previous.get('cleanup_complete') is True:
                result['cases'].append({'case': case['case'], 'suffix': 'ORIGINAL_CONFIRMED_NOT_REPLAYED'})
                continue
            try:
                if case['fixture_case'] not in contexts: raise Blocked('parent_original_context_required')
                snapshots = ownership(evidence, case, contexts[case['fixture_case']],
                                      actor_hashes=bootstrap['actor_hashes'])
                eligible.append((case, snapshots))
            except (Blocked, ValueError, KeyError) as error:
                unresolved.append(case['fixture_case'])
                result['cases'].append({'case': case['case'], 'suffix': 'NO_GO',
                    'reason': str(error) if isinstance(error, Blocked) else 'parent_ownership_invalid'})
        result['planned_protocol_limit'] = len(eligible) * CASE_LIMIT + (0 if unresolved else REGISTRY_LIMIT)
        save('intent.json', {'original_hashes': {**evidence.hashes, **fixed_hashes},
             'bootstrap': bootstrap, 'terminal_barrier': terminal, 'unresolved_cases': unresolved,
             'planned_protocol_limit': result['planned_protocol_limit'], 'original_claims_released': False})
        if eligible or not unresolved:
            runtime = NativeRuntime.disposable(gate)
            if runtime.environment != 'disposable_ci': raise Blocked('parent_runtime_not_disposable')
        for case, snapshots in eligible:
            evidence.unchanged()
            for path, value_sha in fixed_hashes.items(): read_record(gate.out, path, value_sha)
            cls = NegativeControlClosure if case['case'] == 'foreign_row' else Cleanup
            cleanup = cls(runtime, contexts[case['fixture_case']], journal.save, charge)
            cleanup.prefix = PREFIX+'-'+cleanup.case+'-'
            cleanup.binding['original_scope_receipts_sha256'] = digest(evidence.hashes)
            cleanup.prepared, cleanup.snapshots = True, snapshots
            outcome = cleanup.run(worker_joined=True, writers_closed=True, mint_barrier=True)
            result['cases'].append({'case': case['case'], 'suffix': outcome['status'], 'receipt': outcome})
            if outcome['status'] != 'COMPONENT_PASS': unresolved.append(case['fixture_case'])
        if not unresolved:
            evidence.unchanged()
            for path, value_sha in fixed_hashes.items(): read_record(gate.out, path, value_sha)
            result['registry'] = close_registry(runtime, ids, save, charge)
        result['unresolved_case_ids'] = unresolved
        result['suffix_status'] = ('SCOPED_PARENT_CLOSURE_CONFIRMED' if not unresolved
            and result['registry']['status'] == 'SCOPED_CLOSURE_CONFIRMED' else 'PARTIAL_CLOSURE_NO_GO')
    except BaseException as error:
        result.update(reason=str(error) if isinstance(error, Blocked) else 'parent_closure_execution_error',
                      error_class=type(error).__name__)
    finally:
        if runtime is not None:
            try: runtime.clear()
            except BaseException as error:
                result.update(suffix_status='NO_GO', clear_error_class=type(error).__name__)
    try:
        if evidence is not None: evidence.unchanged()
        for path, value_sha in fixed_hashes.items(): read_record(gate.out, path, value_sha)
        result['original_receipts_unchanged'] = True
    except Exception as error:
        result.update(suffix_status='NO_GO', original_receipts_unchanged=False,
                      evidence_error_class=type(error).__name__)
    result['protocol_attempts'] = len(result['protocol'])
    save('result.json', result)
    index = journal.seal()  # Poison or incomplete packaging raises; never a fake closure PASS.
    verify_journal(index, lambda name: read_record(gate.out, name)[0])
    flat = {k: v for k, v in result.items() if k not in ('cases', 'protocol', 'registry', 'unresolved_case_ids')}
    flat['unresolved_cases'] = len(result.get('unresolved_case_ids', []))
    gate.save(PREFIX+'.json', flat)
    return result
