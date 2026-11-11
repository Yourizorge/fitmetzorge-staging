"""Local model/SQL-parser regressions. No PostgreSQL or Docker is contacted."""
import copy
import importlib.util
import json
import pathlib
import os
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent
from quota_candidate_v1 import runtime_registered_fixture_closeout as m


def uid(n):
    return '77777777-7777-4777-8777-%012d' % n


ROW = {'table': 'windows', 'key_sha': 'a'*64, 'row_sha': 'b'*64,
       'xmin': '123', 'scope_ok': True, 'insert_owned': True, 'version_owned': True}
HELD = {'cluster_id': '123', 'postmaster_start': 'start', 'datid': '5',
        'migration_sources_sha256': 'c'*64}


class Journal:
    def __init__(self, fail=None):
        self.records, self.fail = {}, fail
    def save(self, name, value):
        if name == self.fail:
            raise OSError('synthetic_storage_failure')
        if name in self.records:
            raise AssertionError('overwrite')
        self.records[name] = copy.deepcopy(value)


class Cursor:
    description = True
    def __init__(self, rows): self.rows = rows
    def fetchall(self): return self.rows


class Connection:
    autocommit = True
    def __init__(self, owner): self.owner, self.closed = owner, False
    def close(self):
        self.closed = True
        if self.owner.fail_close:
            raise OSError('synthetic_close')
    def execute(self, text, args=None):
        o = self.owner
        phase = o.phase.removeprefix('fixture.')
        o.dispatched.append(phase)
        if phase == o.fail_phase or (phase == 'failure_rollback' and o.fail_rollback):
            raise TimeoutError('synthetic_lost_response')
        if phase == 'ownership_inventory':
            return Cursor([{'value': {'rows': copy.deepcopy(o.rows), 'xid': None}}])
        if phase == 'registry_before':
            return Cursor([{'value': copy.deepcopy(o.registry)}])
        if phase in ('registry_after', 'absence_registry'):
            return Cursor([{'value': {'identities': [], 'operators': []}}])
        if phase in ('fixture_zero', 'absence_fixture'):
            rows = [ROW] if phase == o.nonzero else []
            return Cursor([{'value': {'rows': [{k:v for k,v in r.items()
                if k not in ('insert_owned','version_owned')} for r in rows], 'xid': None}}])
        if phase == 'delete_operator':
            return Cursor(copy.deepcopy(o.expected['operators']))
        if phase == 'delete_identities':
            return Cursor(copy.deepcopy(o.expected['identities']))
        if phase.startswith('delete_'):
            table = phase.removeprefix('delete_')
            rows = [{k:v for k,v in r.items() if k not in ('scope_ok','insert_owned','version_owned')}
                    for r in o.rows if r['table'] == table]
            if phase == o.bad_return: rows *= 2
            return Cursor([{'value': rows}])
        if phase == 'absence_session':
            return Cursor([{**{k:HELD[k] for k in ('cluster_id','postmaster_start','datid')},'pid':124,
                **dict.fromkeys(('pg17','statement_bounded','lock_bounded',
                'no_prepared','tracked','fresh','origin','privileged'), True)}])
        return Cursor([])


class Owner:
    def __init__(self):
        self.ids = dict(zip(m.parent.ROLES, (uid(1),uid(2),uid(3))))
        self.expected = m.parent.expected_registry(self.ids)
        self.registry = copy.deepcopy(self.expected)
        self.rows = [copy.deepcopy(ROW)]
        self.gate = object()
        self.isolation = {'pg_system_identifier': '123', 'database_oid': 5}
        self.phase, self.calls, self.dispatched, self.connections = None, [], [], []
        self.fail_phase = self.reject_phase = self.bad_return = self.nonzero = None
        self.fail_rollback = self.fail_close = False
        self.runtime = types.SimpleNamespace(connect=self.connect)
    def connect(self):
        c = Connection(self)
        self.connections.append(c)
        return c
    def _local_call(self, name, kind, action):
        self.calls.append((name,kind))
        self.phase = name
        if name == self.reject_phase: raise RuntimeError('synthetic_root_denial')
        return action()


class State:
    def __init__(self):
        self.owner = Owner()
        self.context = dict(window=uid(10), a=uid(11), b=uid(12))
        self.ids = self.owner.ids
        self.journal = Journal()
        self.original_commit_unknown = False
        self.changed = False
    def unchanged(self):
        m.require(not self.changed, 'test_original_changed')


def collect(raw, meter, contract, *, before):
    assert before is False
    for phase, text in m.scope.QUERIES:
        meter.query(raw, phase, text)
    return dict(HELD)


class CloseoutTests(unittest.TestCase):
    def run_state(self, state):
        with patch.object(m.scope, 'source_contract', return_value={}), patch.object(m.scope, 'collect', collect):
            return m._execute(state, [], [])

    def test_fixed_program_and_all_templates_parse(self):
        from sql_protocol import statements
        self.assertEqual((m.NORMAL_COMMANDS, m.PROTOCOL_LIMIT), (36,37))
        self.assertEqual(len(m.protocol_plan(physical_only=True)),23)
        for phase, text in m.protocol_plan():
            with self.subTest(phase=phase): self.assertEqual(len(statements(text)),1)
        self.assertEqual(len(set(p for p,_ in m.protocol_plan())),36)

    def test_all_actual_returns_have_original_protocol_observations(self):
        s=State();result,error=self.run_state(s)
        self.assertIsNone(error)
        records=[v for k,v in s.journal.records.items() if k.startswith('query-')]
        self.assertEqual(len(records),36)
        self.assertEqual([r['protocol'] for r in records],result['protocol'])
        for row in records:
            self.assertEqual(row['rows_sha256'],m.engine.digest(row['rows']))
            self.assertEqual(row['raw_rows_sha256'],m.engine.digest(row['rows']))
            self.assertFalse(row['query_io']['observed'])
            self.assertNotIn('sql',row)
        by_phase={r['phase']:r for r in records}
        self.assertTrue(by_phase['ownership_inventory']['rows'][0]['value']['rows'][0]['insert_owned'])
        self.assertEqual(by_phase['absence_fixture']['rows'],[{'value':{'rows':[],'xid':None}}])
        self.assertEqual(by_phase['commit']['rows'],[])
        self.assertTrue(by_phase['commit']['protocol']['confirmed'])

    def test_bound_catalog_originals_replay_existing_semantic_validator(self):
        import test_fixture_producer_scope as source
        contract=source.contract();samples=source.samples(contract)
        samples['session'][0]['cluster_id']='123'
        original=Connection.execute
        def execute(connection,text,args=None):
            phase=connection.owner.phase.removeprefix('fixture.')
            if phase in samples:
                connection.owner.dispatched.append(phase)
                return Cursor(copy.deepcopy(samples[phase]))
            return original(connection,text,args)
        s=State()
        with patch.object(m.scope,'source_contract',return_value=contract),patch.object(Connection,'execute',execute):
            result,error=m._execute(s,[],[])
        self.assertIsNone(error)
        exported={r['phase']:r['rows'] for name,r in s.journal.records.items()
                  if name.startswith('query-') and r['phase'] in samples}
        self.assertEqual(exported,samples)
        self.assertEqual(m.scope.validate(exported,contract,before=False),
                         s.journal.records['predelete.json']['scope'])
        exported['privileges'][0]['direct_write']=True
        with self.assertRaises(m.scope.PrivilegeViolation):m.scope.validate(exported,contract,before=False)
        self.assertEqual(result['emitted_attempts'],36)

    def test_unbound_function_config_is_digest_only_and_replay_rejects_it(self):
        import test_fixture_producer_scope as source
        contract=source.contract();samples=source.samples(contract)
        samples['functions'][0]['config']=['app.secret=DO_NOT_EXPORT']
        rows=m.observation_rows('functions',samples['functions'],contract)
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(rows))
        self.assertTrue(rows[0]['config']['redacted'])
        self.assertEqual(rows[0]['config']['count'],1)
        samples['functions']=rows
        with self.assertRaisesRegex(m.engine.Blocked,'changed_function'):
            m.scope.validate(samples,contract,before=False)

    def test_observation_shape_cannot_export_unselected_secret_fields(self):
        bad={'role':'supabase_auth_admin',**dict.fromkeys(m.scope.PRIVILEGE_FLAGS,False),
             'dsn':'DO_NOT_EXPORT'}
        with self.assertRaisesRegex(m.engine.Blocked,'observation_fields'):
            m.observation_rows('privileges',[bad],{})
        del bad['dsn'];bad['superuser']='DO_NOT_EXPORT'
        with self.assertRaisesRegex(m.engine.Blocked,'observation_boolean'):
            m.observation_rows('privileges',[bad],{})

    def test_result_storage_failure_before_delete_and_after_commit_no_replay(self):
        for name in ('query-11-ownership_inventory.json','query-30-commit.json'):
            with self.subTest(name=name):
                s=State();s.journal.fail=name
                result,error=self.run_state(s)
                self.assertIsInstance(error,OSError)
                self.assertFalse(result['physical_zero'])
                if 'commit' in name:
                    self.assertTrue(result['registry_commit_unknown'])
                    self.assertEqual(s.owner.dispatched.count('commit'),1)
                    self.assertNotIn('failure_rollback',s.owner.dispatched)
                    self.assertEqual(len(s.owner.connections),1)
                else:
                    self.assertFalse(any(p.startswith('delete_') for p in s.owner.dispatched))
                    self.assertEqual(s.owner.dispatched[-1],'failure_rollback')

    def test_real_key_conventions_and_source_audit_binding(self):
        self.assertEqual(m.AUDIT_KEYS['audit'], ('window_id','actor','action'))
        self.assertEqual(m.AUDIT_KEYS['proposals'], ('workspace_id','version'))
        self.assertIn('w.backend=a.backend',m.OWNED_INVENTORY)
        self.assertIn('w.actor=a.actor',m.OWNED_INVENTORY)
        self.assertIn('t.xmin::text',m.OWNED_INVENTORY)
        self.assertIn('limit 1001',m.OWNED_INVENTORY)
        self.assertNotIn('project_key(',m.OWNED_INVENTORY)

    def test_owned_version_cleanup_uses_thirteen_existing_deletes(self):
        s=State(); result,error=self.run_state(s)
        self.assertIsNone(error)
        self.assertTrue(result['physical_zero'])
        self.assertEqual(result['emitted_attempts'],36)
        self.assertEqual(result['returned_fixture_deletes'],1)
        self.assertEqual([p for p in s.owner.dispatched if p in {'delete_'+t for t in m.sql.ORDER}],
                         ['delete_'+t for t in m.sql.ORDER])
        self.assertTrue(all(c.closed for c in s.owner.connections))
        self.assertFalse(result['full_chain_admission'])
        self.assertFalse(result['original_claims_released'])

    def test_each_table_has_a_nonempty_exact_returning_set(self):
        s=State()
        s.owner.rows=[{**ROW,'table':table,'key_sha':'%064x'%(i+1)}
                      for i,table in enumerate(m.sql.ORDER)]
        result,error=self.run_state(s)
        self.assertIsNone(error)
        self.assertEqual(result['returned_fixture_deletes'],13)
        self.assertEqual(result['emitted_attempts'],36)
        for table in m.sql.ORDER:
            record=s.journal.records['delete-'+table+'.json']
            self.assertEqual(len(record['expected']),1)
            self.assertEqual(record['returned'],record['expected'])
            self.assertFalse(record['commit_confirmed'])

    def test_duplicate_returning_at_each_table_rolls_back_without_commit(self):
        for table in m.sql.ORDER:
            with self.subTest(table=table):
                s=State()
                s.owner.rows=[{**ROW,'table':t,'key_sha':'%064x'%(i+1)}
                              for i,t in enumerate(m.sql.ORDER)]
                s.owner.bad_return='delete_'+table
                result,error=self.run_state(s)
                self.assertIn('delete_multiset',str(error))
                self.assertFalse(result['physical_zero'])
                self.assertNotIn('commit',s.owner.dispatched)
                self.assertEqual(s.owner.dispatched[-1],'failure_rollback')
                self.assertEqual(s.owner.dispatched.count('delete_'+table),1)
                self.assertLessEqual(result['emitted_attempts'],37)

    def test_origin_and_current_version_independently_required(self):
        for field in ('insert_owned','version_owned'):
            s=State();s.owner.rows[0][field]=False
            result,error=self.run_state(s)
            self.assertIn('unowned_version',str(error))
            self.assertFalse(any(p.startswith('delete_') for p in s.owner.dispatched))
            self.assertEqual(s.owner.dispatched[-1],'failure_rollback')

    def test_duplicate_rows_and_bound_overflow_block(self):
        for rows in ([ROW,ROW],[ROW]*1001):
            with self.assertRaises((m.engine.Blocked, ValueError)):
                m.validate_owned({'rows':rows,'xid':None})

    def test_foreign_scope_blocks(self):
        s=State();s.owner.rows[0]['scope_ok']=False
        result,error=self.run_state(s)
        self.assertIsNotNone(error)
        self.assertFalse(result['physical_zero'])
        self.assertNotIn('delete_windows',s.owner.dispatched)

    def test_changed_seed_registry_no_delete(self):
        s=State();s.owner.registry['identities'][0]['provenance_sha']='d'*64
        result,error=self.run_state(s)
        self.assertIn('registry_not_original_seed',str(error))
        self.assertFalse(any(p.startswith('delete_') for p in s.owner.dispatched))

    def test_delete_multiset_mismatch_rolls_back_no_commit(self):
        s=State();s.owner.bad_return='delete_windows'
        result,error=self.run_state(s)
        self.assertIn('delete_multiset',str(error))
        self.assertNotIn('commit',s.owner.dispatched)
        self.assertFalse(result['physical_zero'])

    def test_lost_begin_rolls_back_once(self):
        s=State();s.owner.fail_phase='begin'
        result,error=self.run_state(s)
        self.assertIsInstance(error,TimeoutError)
        self.assertEqual(s.owner.dispatched,['begin','failure_rollback'])

    def test_lost_commit_no_replay_or_rollback_or_new_connection(self):
        s=State();s.owner.fail_phase='commit'
        result,error=self.run_state(s)
        self.assertTrue(result['registry_commit_unknown'])
        self.assertFalse(result['physical_zero'])
        self.assertEqual(s.owner.dispatched.count('commit'),1)
        self.assertNotIn('failure_rollback',s.owner.dispatched)
        self.assertEqual(len(s.owner.connections),1)

    def test_original_unknown_physical_zero_no_fixture_delete_replay(self):
        s=State();s.original_commit_unknown=True;s.owner.rows=[]
        result,error=self.run_state(s)
        self.assertIsNone(error)
        self.assertTrue(result['physical_zero'])
        self.assertTrue(result['original_commit_unknown'])
        self.assertFalse(result['original_commit_reclassified'])
        self.assertEqual(result['emitted_attempts'],23)
        self.assertFalse(any(p in {'delete_'+t for t in m.sql.ORDER} for p in s.owner.dispatched))

    def test_original_unknown_with_remaining_rows_no_retry_delete(self):
        s=State();s.original_commit_unknown=True
        result,error=self.run_state(s)
        self.assertIn('unknown_original_commit_nonzero_no_replay',str(error))
        self.assertFalse(any(p.startswith('delete_') for p in s.owner.dispatched))

    def test_inventory_storage_failure_rolls_back_before_delete(self):
        s=State();s.journal.fail='predelete.json'
        result,error=self.run_state(s)
        self.assertIsInstance(error,OSError)
        self.assertNotIn('delete_inbox_state',s.owner.dispatched)
        self.assertEqual(s.owner.dispatched[-1],'failure_rollback')

    def test_root_denial_precedes_database_dispatch(self):
        s=State();s.owner.reject_phase='fixture.delete_inbox_state'
        result,error=self.run_state(s)
        self.assertNotIn('delete_inbox_state',s.owner.dispatched)
        self.assertIsInstance(error,RuntimeError)

    def test_charge_storage_failure_precedes_dispatch(self):
        s=State();s.journal.fail='charge-13.json'
        result,error=self.run_state(s)
        self.assertNotIn('delete_inbox_state',s.owner.dispatched)
        self.assertIsInstance(error,OSError)

    def test_each_sql_failure_prefix_bounded_and_closed(self):
        for phase,_ in m.protocol_plan():
            with self.subTest(phase=phase):
                s=State();s.owner.fail_phase=phase
                result,error=self.run_state(s)
                self.assertIsNotNone(error)
                self.assertFalse(result['physical_zero'])
                self.assertLessEqual(result['emitted_attempts'],37)
                self.assertEqual(s.owner.dispatched.count(phase),1)
                self.assertLessEqual(s.owner.dispatched.count('failure_rollback'),1)
                self.assertTrue(all(c.closed for c in s.owner.connections))

    def test_rollback_secondary_does_not_replace_primary(self):
        s=State();s.owner.fail_phase='ownership_inventory';s.owner.fail_rollback=True
        result,error=self.run_state(s)
        self.assertIsInstance(error,TimeoutError)
        self.assertTrue(any('rollback_secondary' in n for n in error.__notes__))

    def test_absence_failure_never_claims_cleanup(self):
        s=State();s.owner.nonzero='absence_fixture'
        result,error=self.run_state(s)
        self.assertTrue(result['registry_commit_confirmed'])
        self.assertFalse(result['registry_absence_confirmed'])
        self.assertFalse(result['physical_zero'])

    def test_close_failure_no_positive_proof(self):
        s=State();s.owner.fail_close=True
        result,error=self.run_state(s)
        self.assertFalse(result['physical_zero'])
        self.assertIsNotNone(error)

    def test_no_caller_constructed_capability(self):
        for cls in (m.Registration,m.Proof):
            with self.assertRaises(TypeError): cls()
        fake=object.__new__(m.Proof)
        with self.assertRaisesRegex(m.engine.Blocked,'unissued_proof'):fake.unchanged()

    def test_evidence_refs_are_exact_copies_not_guessed_filenames(self):
        # The property is tested separately; bypassing unchanged here grants no
        # runtime capability and the public constructor remains forbidden.
        raw=pathlib.Path(__file__).read_bytes()
        name=pathlib.Path(__file__).name
        state=types.SimpleNamespace(owner=types.SimpleNamespace(gate=types.SimpleNamespace(out=HERE)),
            originals={name:m.parent.sha(raw)},
            journal=types.SimpleNamespace(folder=HERE/'private',entries={
                'result.json':{'sha256':'e'*64,'bytes':17}}))
        proof=object.__new__(m.Proof)
        m._PROOFS[proof]=state
        try:
            with patch.object(m.Proof,'unchanged',return_value=None):
                refs=proof.evidence_refs
                self.assertEqual(refs,[{'path':'private/result.json','sha256':'e'*64,'bytes':17},
                    {'path':name,'sha256':m.parent.sha(raw),'bytes':len(raw)}])
                refs[0]['sha256']='changed'
                self.assertEqual(proof.evidence_refs[0]['sha256'],'e'*64)
        finally:del m._PROOFS[proof]

    def test_old_uuid_and_preparation_uuid_refused(self):
        for value in (m.OLD_RUN,m.NEW_RUN):
            with self.assertRaises(m.engine.Blocked):m.fresh(value)

    def test_scope_validator_unchanged_not_active_window_exception(self):
        # The adapter delegates all eight catalog queries to the original
        # validator. A rejection must occur before any table mutation.
        s=State()
        with patch.object(m.scope,'source_contract',return_value={}), patch.object(
                m.scope,'collect',side_effect=m.engine.Blocked('producer_rpc_or_bootstrap_open')):
            result,error=m._execute(s,[],[])
        self.assertFalse(result['physical_zero'])
        self.assertEqual(s.owner.dispatched,['begin','lock','failure_rollback'])


LIVE_JOIN = r'''
import copy
import json
import types
import unittest
from unittest.mock import patch
import test_runtime_registered_bootstrap as base
from quota_candidate_v1 import runtime_registered_fixture_closeout as physical
from test_runtime_registered_fixture_closeout import Owner, collect


class LiveJoin(unittest.TestCase):
    stop_server = base.ContextTests.stop_server
    producer = base.ContextTests.producer

    def setUp(self):
        # Real loopback HTTP, B producer, Registry, seal and immutable journals.
        # Root admission, D worker termination and database replies are doubles.
        base.ContextTests.setUp(self)
        self.gate.save = self.publish
        self.producing = self.producer()
        ids = self.producing.create_all()
        self.seal = self.producing.close()
        self.assertTrue(self.registry.valid_proof(self.seal))
        self.wire = Owner()
        self.wire.ids = ids
        self.wire.expected = physical.parent.expected_registry(ids)
        self.wire.registry = copy.deepcopy(self.wire.expected)
        self.wire.runtime.environment = 'disposable_ci'
        owner = base.proposed.Context(self.gate, binding={'run_id': self.run_id}, stack={}, ledger=None)
        self.owner = owner
        owner._source_snapshot = base.proposed._source(self.gate)
        owner.ids, owner.producer, owner.runtime = ids, self.producing, self.wire.runtime
        owner.isolation = self.wire.isolation
        owner._local_call = self.wire._local_call
        owner._yielded = owner._closing = True
        context = {k: str(base.uuid.uuid4()) for k in ('window','a','b','key')}
        context['runs'] = {k: str(base.uuid.uuid4()) for k in ('seed','activate','delete_window')}
        self.composition = types.SimpleNamespace(fixture_context=context, runtime=owner.runtime,
            commands=[], events=[], workflow_recovery={'complete':True,'worker_terminated':True,'secondary':[]})
        owner._case = (object(), self.composition)
        owner._case_owners = {'gate': self.gate}
        owner.records = base.tracked.Records(self.out/'context')
        owner._seed_ref = owner.records.save('seed', {
            'provenance_sha256': self.wire.expected['identities'][0]['provenance_sha'],
            'actor_hashes': {k: physical.parent.sha(v.encode()) for k,v in ids.items()},
            'explicit_commands':9,'adopted_existing_rows':False})
        raw = physical.durable.raw({'test_boundary':'D worker terminal, not actual D proof'})
        (self.out/'worker.json').write_bytes(raw)
        ref = {'path':'worker.json','sha256':physical.parent.sha(raw),'bytes':len(raw)}
        self.body = {'worker':{'evidence_refs':[ref]},'evidence_refs':[],
                     'test_only_D_terminal_boundary':True}
        owner._body_terminal = lambda: copy.deepcopy(self.body)
        self.state = physical._State(owner)

    def publish(self, name, value):
        with (self.out/name).open('xb') as stream:
            stream.write(physical.durable.raw(value))

    def execute(self):
        actions, requests = self.state.inputs()
        with patch.object(physical.scope,'source_contract',return_value={}), patch.object(
                physical.scope,'collect',collect):
            return physical._execute(self.state,actions,requests)

    def test_original_live_seal_to_counted_delete_commit_and_absence(self):
        self.assertIs(self.state.handoff['seal'],self.seal)
        result,error = self.execute()
        self.assertIsNone(error)
        self.assertTrue(result['physical_zero'])
        self.assertEqual(result['emitted_attempts'],36)
        self.assertEqual(self.wire.dispatched.count('commit'),1)
        self.state.journal.save('result.json',result)
        index=self.state.journal.seal()
        self.assertTrue(index['complete'])
        self.state.unchanged()
        with self.assertRaisesRegex(base.tracked.Blocked,'future_request_denied'):
            self.auth.call('/admin/users','PRIVATE_TEST_ADMIN',{'email':'blocked@example.invalid'})
        self.assertEqual(len(self.requests),3)
        # This unit boundary deliberately does NOT register or issue a C Proof.
        self.assertFalse(any(s is self.state for s in physical._PROOFS.values()))

    def test_live_seal_revoked_by_original_record_tamper_before_delete(self):
        name=next(iter(self.producing.records._hashes))
        path=self.producing.records.folder/name
        path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises(base.tracked.Blocked):self.execute()
        self.assertFalse(self.registry.valid_proof(self.seal))
        self.assertEqual(self.wire.dispatched,[])

    def test_original_seed_tamper_blocks_before_any_connection(self):
        path=self.owner.records.folder/self.owner._seed_ref['name']
        path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises((base.tracked.Blocked,physical.engine.Blocked)):self.execute()
        self.assertEqual(self.wire.connections,[])

    def test_writer_terminality_rejection_preserves_primary_and_no_sql(self):
        primary=RuntimeError('D worker still live')
        def reject():raise primary
        self.owner._body_terminal=reject
        with self.assertRaises(RuntimeError) as caught:self.execute()
        self.assertIs(caught.exception,primary)
        self.assertEqual(self.wire.connections,[])

    def test_incomplete_workflow_recovery_blocks_before_delete(self):
        self.composition.workflow_recovery['complete']=False
        with self.assertRaisesRegex(physical.engine.Blocked,'writer_close_unknown'):self.execute()
        self.assertEqual(self.wire.connections,[])

    def test_live_ownership_change_during_delete_prevents_next_dispatch(self):
        original=self.wire._local_call
        def call(name,kind,action):
            value=original(name,kind,action)
            if name=='fixture.delete_inbox_state':
                self.producing._owned['a_member']['id']=str(base.uuid.uuid4())
            return value
        self.owner._local_call=call
        result,error=self.execute()
        self.assertIsNotNone(error)
        self.assertFalse(result['physical_zero'])
        deletes=[p for p in self.wire.dispatched if p.startswith('delete_')]
        self.assertEqual(deletes,['delete_inbox_state'])
        self.assertNotIn('commit',self.wire.dispatched)
        self.assertTrue(all(c.closed for c in self.wire.connections))

    def test_lost_commit_with_live_originals_retains_unknown_no_replay(self):
        self.wire.fail_phase='commit'
        result,error=self.execute()
        self.assertIsInstance(error,TimeoutError)
        self.assertTrue(result['registry_commit_unknown'])
        self.assertFalse(result['physical_zero'])
        self.assertNotIn('failure_rollback',self.wire.dispatched)
        self.assertEqual(len(self.wire.connections),1)
        self.assertTrue(self.registry.valid_proof(self.seal))

    def test_live_B_seal_does_not_authorize_direct_C_entrypoints(self):
        self.assertTrue(self.registry.valid_proof(self.seal))
        with self.assertRaisesRegex(physical.engine.Blocked,'prepare_caller'):
            physical.prepare(self.owner)
        with self.assertRaisesRegex(physical.engine.Blocked,'run_caller'):
            physical.run(self.owner)
        self.assertEqual(self.wire.connections,[])
        self.assertIsNone(self.owner._fixture_registration)

    def test_existing_body_QueryIO_original_bytes_are_retained_not_resummarized(self):
        name='integral-io-pair-000.json'
        value={'test_boundary':True,'queries':[{'queryid':'123','wal':0,'temp_written':0}],
               'original_unknown_classification':None}
        raw=physical.durable.raw(value)
        (self.out/name).write_bytes(raw)
        ref={'path':name,'sha256':physical.parent.sha(raw),'bytes':len(raw)}
        self.body['worker']['evidence_refs'].append(ref)
        self.state.inputs()
        self.assertEqual(self.state.originals[name],ref['sha256'])
        self.assertEqual((self.out/name).read_bytes(),raw)
        self.state.unchanged()
        (self.out/name).write_bytes(raw+b' ')
        with self.assertRaises(physical.parent.Blocked):self.state.unchanged()


result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LiveJoin))
raise SystemExit(not result.wasSuccessful())
'''


class LiveOwnershipJoinTests(unittest.TestCase):
    def test_nine_live_original_ownership_boundaries(self):
        # Separate interpreter prevents checkout/candidate module cache mixing.
        # The canonical bundle imports its own B test helper; the isolated
        # delivery uses only the explicitly named sibling B delivery.
        sibling = HERE.parent/'agent-b-tracked-context-20261103'
        helper = sibling if HERE.name == 'agent-c-registered-fixture-closeout-20261103' else HERE
        self.assertTrue((helper/'test_runtime_registered_bootstrap.py').is_file())
        env = dict(os.environ)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        paths = env.get('PYTHONPATH','').split(os.pathsep)
        if helper == sibling:
            source_core = pathlib.Path(env['AUTH_CONTEXT_SOURCE_ROOT'])/'_offline/phase6e11/endchain_v1'
            paths = [p for p in paths if p and pathlib.Path(p).resolve() != source_core.resolve()]
        env['PYTHONPATH'] = os.pathsep.join((str(helper),str(HERE),*paths))
        result = subprocess.run([sys.executable,'-c',LIVE_JOIN],cwd=helper,env=env,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
        self.assertEqual(result.returncode,0,result.stdout)
        self.assertIn('Ran 9 tests',result.stdout)


if __name__=='__main__':unittest.main()
