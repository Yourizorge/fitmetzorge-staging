"""Mock native protocol and actual immutable journal/parser tests, no PG claim."""
import copy
import json
import os
import pathlib
import tempfile
import types
import unittest
from unittest.mock import patch

import fixture_parent_physical_zero as m
from fixture_cleanup_runtime import Blocked,digest
from fixture_cleanup_runtime_test import Cursor,CONTEXT,row
from test_fixture_parent_closure import ENV,IDS
from test_fixture_producer_scope import contract,samples


class Database:
    environment='disposable_ci'
    def __init__(self,c):
        self.samples=samples(c); self.registry=m.parent.expected_registry(IDS)
        self.rows={}; self.calls=[]; self.fail=None; self.connections=[]; self.lost_commit=False
        self.foreign_registry=False; self.bad_returning=False
        self.fail_at=None
    def clear(self): pass
    def connect(self):
        db=self
        class Raw:
            autocommit=True
            def __init__(self): self.locked=False; self.backup=None; self.closed=False
            def close(self):
                if self.backup is not None: db.registry,db.rows=copy.deepcopy(self.backup)
                self.backup=None; self.closed=True
            def execute(self,text,args=None):
                phase=next((name for name,sql in m.producer.QUERIES if text==sql.replace('$1','%s')),text)
                db.calls.append((phase,text,args))
                if len(db.calls)==db.fail_at: raise TimeoutError('injected dispatch-prefix failure')
                if phase==db.fail: raise TimeoutError('private transport information')
                if phase in db.samples: return Cursor(copy.deepcopy(db.samples[phase]))
                if text.startswith('BEGIN'):
                    self.backup=copy.deepcopy((db.registry,db.rows)); return Cursor([])
                if text.startswith('LOCK TABLE'):
                    self.locked=True; return Cursor([])
                if text=='ROLLBACK':
                    db.registry,db.rows=copy.deepcopy(self.backup); self.backup=None
                    self.locked=False; return Cursor([])
                if text=='COMMIT':
                    self.backup=None; self.locked=False
                    if db.lost_commit: raise ConnectionError('lost after actual server commit')
                    return Cursor([])
                if "'rows',coalesce" in text:
                    if not self.locked: raise AssertionError('absence outside physical exclusion')
                    case_id=next(a for a in args if isinstance(a,str))
                    return Cursor([{'value':{'rows':copy.deepcopy(db.rows.get(case_id,[])),'xid':None}}])
                if 'from fmz6e11_private.identities where user_id=any' in text:
                    return Cursor([{'value':copy.deepcopy(db.registry)}])
                if text.startswith('delete from fmz6e11_private.'):
                    if not self.locked: raise AssertionError('delete outside physical exclusion')
                    key='operators' if '.operators' in text else 'identities'
                    value=db.registry[key]; db.registry[key]=[]
                    return Cursor([] if db.bad_returning else copy.deepcopy(value))
                if text.startswith('with removed as'):
                    if not self.locked: raise AssertionError('fixture delete outside lock')
                    expected=json.loads(args[0])
                    removed=[]
                    for case,rows in db.rows.items():
                        for value in list(rows):
                            trimmed={k:v for k,v in value.items() if k!='scope_ok'}
                            if trimmed in expected: rows.remove(value); removed.append(trimmed)
                    return Cursor([{'value':removed}])
                raise AssertionError('unrecognized test protocol')
        raw=Raw(); self.connections.append(raw); return raw


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.contract=contract()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='physical-zero-test-'); self.addCleanup(self.temp.cleanup)
        self.out=pathlib.Path(self.temp.name).resolve()
        self.gate=types.SimpleNamespace(out=self.out,container='supabase_db_fmz-db41-ci',
                                       fixture_cleanup_ids=copy.deepcopy(IDS),save=self.save)
        self.db=Database(self.contract)
        for context in (patch.dict(os.environ,ENV),patch.object(m.binding,'verify',return_value={'bound':True}),
                        patch.object(m.producer,'source_contract',return_value=self.contract),
                        patch.object(m.NativeRuntime,'disposable',side_effect=lambda gate:self.db)):
            context.start(); self.addCleanup(context.stop)
        self.scope=m.producer.Scope(self.gate)
        # Before-bootstrap observation uses real collector/validator over mocked rows.
        self.scope.before_bootstrap(); self.db.calls.clear()
        self.tracked=object.__new__(m.db_terminal.TrackedRuntime)
        zero=patch.object(m.db_terminal.TrackedRuntime,'physical_zero',side_effect=self.zero)
        self.zero_mock=zero.start(); self.addCleanup(zero.stop)
        self.actors={k:m.parent.sha(v.encode()) for k,v in IDS.items()}
        self.original={'preparation_run':m.NEW_RUN,'case':CONTEXT['window'],
            'scope_sha256':digest(m.parameters(CONTEXT)),'component_only':True,
            'status':'NO_GO','commit_unknown':True,'commit_confirmed':False,
            'cleanup_complete':False,'deletion_proven':False}
        self.cases=[{'case':'lost_commit','fixture_case':CONTEXT['window'],'receipt':copy.deepcopy(self.original)}]
        self.contexts={CONTEXT['window']:copy.deepcopy(CONTEXT)}
        self.terminal={'preparation_run':m.NEW_RUN,'classification':'TRACKED_DB_BACKENDS_TERMINAL',
                       'db_terminality_proven':True,'registered_sessions':1,'terminal_commands':2}
        self.save('terminal.json',self.terminal); self.terminal_ref=self.ref('terminal.json')
        self.save('auth-closed.json',{'kind':'closed','active_requests':0,'all_registered_upstream_terminal':True,
             'future_regular_dispatch_denied':True,'scope':'registered_request_set_only',
             'server_writers_quiescent_proven':False})
        self.auth_ref=self.ref('auth-closed.json')
        self.bootstrap={'status':'DISPOSABLE_BOOTSTRAP_PASS','commit_confirmed':True,
             'registered_accounts':3,'existing_rows_overwritten':False,'after_registry_confirmed':True,
             'before':{'identities':0,'operators':0},'actor_hashes':self.actors}
        self.save('admission-fixture-bootstrap.json',self.bootstrap)
    def save(self,name,value):
        with (self.out/name).open('xb') as stream:
            stream.write((json.dumps(value,sort_keys=True)+'\n').encode()); stream.flush(); os.fsync(stream.fileno())
    def ref(self,name): return {'path':name,'sha256':m.parent.sha((self.out/name).read_bytes())}
    def zero(self,context,ref):
        m.parent.reference(self.out,ref)
        return {'physical_zero':True,'terminal_sha256':digest(self.terminal),'original_ref':ref,
                'scope_sha256':digest(m.parameters(context))}
    def seed(self,*,extra=False,bad_scope=False):
        if extra:
            context={k:'78000000-0000-4000-8000-%012d'%i for i,k in enumerate(CONTEXT,10)}
            self.contexts[context['window']]=context
            self.cases.append({'case':'missing_barrier','fixture_case':context['window'],
                'receipt':{'status':'BLOCKED','reason':'cleanup_writer_barrier_required','deletion_proven':False}})
            self.db.rows[context['window']]=[row('windows')]
        journal=m.Journal(self.out/'admission-fixture-private-journal',self.save,'admission-fixture-journal')
        for case in self.cases:
            uid=case['fixture_case']; context=self.contexts[uid]; prefix='fixture-cleanup-'+uid+'-'
            bound={'preparation_run':m.NEW_RUN,'case':uid,'scope_sha256':digest(m.parameters(context)),
                   'component_only':True}
            journal.save(prefix+'parent-setup.json',{**bound,'context':context,
                         'actor_hashes':{} if bad_scope else self.actors,'before_writer_begin':True})
            journal.save(prefix+'baseline.json',{**bound,'rows':[],'source':'actual_empty_inventory'})
            if case['receipt'].get('commit_unknown'): journal.save(prefix+'result.json',case['receipt'])
            else: journal.save(prefix+'writer-0000.json',{**bound,'rows':[row('windows')],
                                'xid':'41','before_commit':True,'previous':digest([])})
        journal.save('fixture-cleanup-component-detail.json',{'status':'COMPONENT_PASS',
                     'preparation_run':m.NEW_RUN,'cases':self.cases})
        journal.save('fixture-cleanup-db-terminal.json',{'terminal':self.terminal,
                     'fixture_case_ids':list(self.contexts),'component_status':'COMPONENT_PASS'})
        journal.seal()
    def run_case(self):
        return m.run(self.gate,scope=self.scope,tracked=self.tracked,terminal_ref=self.terminal_ref,
                     auth_close_ref=self.auth_ref)
    def test_unknown_commit_current_zero_allows_owned_registry_not_historical_claim_release(self):
        self.seed()
        original=(self.out/'admission-fixture-private-journal'/('fixture-cleanup-'+CONTEXT['window']+'-result.json')).read_bytes()
        result=self.run_case()
        self.assertEqual(result['classification'],'REGISTRY_CLOSED_WITH_ORIGINAL_COMMIT_UNKNOWN')
        self.assertEqual(result['status'],'NO_GO')
        self.assertTrue(result['registry_deletion_proven']); self.assertTrue(result['physical_zero'])
        self.assertFalse(result['original_claims_released']); self.assertFalse(result['original_commit_reclassified'])
        self.assertFalse(result['global_auth_barrier']); self.assertFalse(result['future_privileged_connections_excluded'])
        self.assertEqual(result['emitted_attempts'],22); self.assertEqual(result['protocol_limit'],23)
        self.assertEqual(len(self.db.calls),32)  # Ten additional post-mint observation commands.
        self.assertEqual(sum(text=='COMMIT' for _,text,_ in self.db.calls),1)
        self.assertFalse(any(text.startswith('with removed') for _,text,_ in self.db.calls))
        self.assertEqual(original,(self.out/'admission-fixture-private-journal'/('fixture-cleanup-'+CONTEXT['window']+'-result.json')).read_bytes())
        self.assertEqual(self.zero_mock.call_count,1)
        self.assertEqual(self.db.registry,{'identities':[],'operators':[]})
    def test_retained_owned_partial_fixture_closes_under_same_lock_before_registry(self):
        self.seed(extra=True)
        result=self.run_case()
        self.assertEqual(result.get('reason'),None)
        self.assertTrue(result['registry_deletion_proven'])
        self.assertEqual(result['fixture_returned_delete_count'],1)
        self.assertEqual(result['emitted_attempts'],38)
        self.assertEqual(result['protocol_limit'],39)
        self.assertEqual(sum(text=='COMMIT' for _,text,_ in self.db.calls),1)
    def test_current_rows_after_earlier_unknown_zero_block_without_delete_replay(self):
        self.seed(); self.db.rows[CONTEXT['window']]=[row('windows')]
        result=self.run_case()
        self.assertEqual(result['reason'],'physical_zero_scope_still_present')
        self.assertFalse(result['registry_deletion_proven'])
        self.assertFalse(any(text.startswith('delete') for _,text,_ in self.db.calls))
    def test_foreign_row_in_known_case_rolls_back_all_without_adopting(self):
        self.seed(extra=True)
        key=next(k for k in self.db.rows); self.db.rows[key]=[row('windows',n=9)]
        result=self.run_case()
        self.assertEqual(result['reason'],'physical_zero_unowned_row')
        self.assertFalse(result['registry_deletion_proven'])
    def test_bad_scope_or_actors_blocks_before_any_new_db_dispatch(self):
        self.seed(bad_scope=True)
        result=self.run_case()
        self.assertEqual(result['reason'],'physical_zero_original_scope_binding')
        self.assertEqual(self.db.calls,[])
    def test_extra_writer_is_not_ignored(self):
        self.seed(); self.db.samples['activity']=[{'pid':876,'usename':'postgres','state':'active'}]
        result=self.run_case()
        self.assertEqual(result['reason'],'producer_external_backend_present')
        self.assertFalse(any(text.startswith('delete') for _,text,_ in self.db.calls))
    def test_catalog_rechecked_under_locks_not_just_saved_receipt(self):
        self.seed()
        original=self.scope.after_mint_closure
        def mutate(ref):
            receipt=original(ref); self.db.samples['privileges'][0]['direct_write']=True
            return receipt
        with patch.object(self.scope,'after_mint_closure',side_effect=mutate): result=self.run_case()
        self.assertEqual(result['reason'],'producer_unexpected_privilege')
        self.assertFalse(any(text.startswith('delete') for _,text,_ in self.db.calls))
    def test_wrong_actual_factory_rejected_not_a_caller_boolean(self):
        self.seed()
        with self.assertRaisesRegex(Blocked,'actual_tracked_factory'):
            m.run(self.gate,scope=self.scope,tracked=types.SimpleNamespace(terminal=True),
                  terminal_ref=self.terminal_ref,auth_close_ref=self.auth_ref)
    def test_lost_registry_commit_not_replayed_or_reclassified(self):
        self.seed(); self.db.lost_commit=True
        result=self.run_case()
        self.assertTrue(result['registry_commit_unknown']); self.assertFalse(result['registry_deletion_proven'])
        self.assertEqual(sum(text=='COMMIT' for _,text,_ in self.db.calls),1)
        self.assertEqual(self.db.calls[-1][1],'COMMIT')
    def test_registry_changed_or_delete_mismatch_refuses_confirmation(self):
        self.seed(); self.db.registry['identities'][0]['provenance_sha']='f'*64
        result=self.run_case()
        self.assertEqual(result['reason'],'physical_zero_registry_not_exact_owned')
        self.assertFalse(result['registry_deletion_proven'])
    def test_missing_auth_close_ref_is_not_an_auth_barrier(self):
        self.seed(); self.auth_ref={'path':'missing.json','sha256':'a'*64}
        result=self.run_case()
        self.assertEqual(result['classification'],'NO_GO')
        self.assertEqual(self.db.calls,[])
    def test_duplicate_uses_exclusive_journal_no_retry(self):
        self.seed(); self.run_case(); count=len(self.db.calls)
        with self.assertRaises(FileExistsError): self.run_case()
        self.assertEqual(len(self.db.calls),count)
    def test_failure_on_final_rollback_is_not_retried(self):
        self.seed()
        original=self.scope.after_mint_closure
        def later(ref):
            result=original(ref); self.db.fail='ROLLBACK'; return result
        with patch.object(self.scope,'after_mint_closure',side_effect=later): result=self.run_case()
        self.assertFalse(result['registry_deletion_proven'])
        self.assertEqual(sum(text=='ROLLBACK' for _,text,_ in self.db.calls),2)  # Scope + one suffix attempt.
    def test_every_normal_dispatch_failure_prefix_is_bounded_and_never_claims_closure(self):
        # Each invocation has its own exclusive evidence namespace and no retries.
        for ordinal in range(1,23):
            with self.subTest(ordinal=ordinal):
                case=Tests(); case.setUp()
                try:
                    case.seed(); case.db.fail_at=10+ordinal
                    result=case.run_case()
                    self.assertFalse(result['registry_deletion_proven'])
                    self.assertLessEqual(result['admitted_attempts'],23)
                    self.assertEqual(sum(text=='COMMIT' for _,text,_ in case.db.calls),int(ordinal>=16))
                    self.assertTrue(all(c.closed for c in case.db.connections))
                finally: case.doCleanups()
    def test_real_fsync_failure_poison_keeps_file_no_complete_journal_or_continuation(self):
        self.seed()
        original=m.Journal.save
        def fail(storage,name,value):
            if name==m.PREFIX+'-charge-003.json':
                with patch('os.fsync',side_effect=OSError('simulated fsync failure')):
                    return original(storage,name,value)
            return original(storage,name,value)
        with patch.object(m.Journal,'save',fail):
            with self.assertRaises(OSError): self.run_case()
        self.assertEqual(len(self.db.calls),12)  # Scope ten; only BEGIN and LOCK dispatched.
        self.assertTrue((self.out/(m.PREFIX+'-private')/(m.PREFIX+'-charge-003.json')).is_file())
        self.assertFalse((self.out/(m.PREFIX+'-journal-index.json')).exists())
        self.assertTrue(all(c.closed for c in self.db.connections))
    def test_source_defined_protocol_and_cap_match_all_bounded_case_counts(self):
        for total in range(1,12):
            for eligible in range(total):
                plan=m.protocol_plan(total,eligible)
                self.assertEqual(len(plan),20+2*total+14*eligible)
                self.assertEqual(len(plan)+1,m.FIXED_LIMIT+2*total+14*eligible)
                self.assertEqual(sum(text=='COMMIT' for _,text in plan),1)


if __name__=='__main__': unittest.main()
