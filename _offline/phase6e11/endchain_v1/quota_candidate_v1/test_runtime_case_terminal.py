"""Local receipt/ordering models only; successful models are not real case proof."""
import copy
import json
import pathlib
import tempfile
import types
import unittest
from unittest import mock

from quota_candidate_v1 import runtime_case_entry as e
from quota_candidate_v1 import runtime_case_terminal as t
from quota_candidate_v1.compiler import CandidateStop, sha


class TerminalJoinTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name)
        self.binding={'run_id':'unit','parent_id':'unit-parent','source_commit':'a'*40,
            'ci_run':'123','candidate_sha':'b'*64}
        self.gate=types.SimpleNamespace(sources=self.root,out=self.root,
            result={'candidate_sha256':'b'*64,'run_id':'123','commit':'a'*40})
        self.gate.save=lambda name,value:(self.root/name).write_text(json.dumps(value),encoding='ascii')
        sources={}
        for relative,raw in ((e.OWN+'runtime_case_terminal.py',pathlib.Path(t.__file__).read_bytes()),
                             (e.ROOT_ADMISSION,b'unit-only root module, not executable admission'),
                             (e.ARCHIVE_SOURCE,b'unit-only packer module, not an archive implementation')):
            target=self.root/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            sources[relative]=sha(raw)
        self.ledger=mock.Mock()
        self.fault=types.SimpleNamespace(case='normal',fired=None,receipt=lambda:{'unit':True})
        self.owner=e.PreparedExecution(e._PREPARED_KEY,gate=self.gate,root=self.root,sources=sources,
            report={'root_dag':{'full_register_sha256':'c'*64}},manifest={},binding=self.binding,
            faults=self.fault,ledger=self.ledger,registered=None,case_name='normal')
        self.owner._used=True
        self.gate.save('unit-worker-io.json',{'unit':'not real IO evidence'})
        self.worker={'status':'REGISTERED_WORKER_COMPLETE','unit':True,'evidence_refs':[
            {'path':'unit-worker-io.json','sha256':sha((self.root/'unit-worker-io.json').read_bytes())}]}
        self.gate.save('case-runtime-terminal.json',self.worker)
        self.context=types.SimpleNamespace(isolation={'unit':'not real isolation'},closeout={'unit':True})
        self.owners={'terminal_proof':copy.deepcopy(self.worker),'composition':object(),
            'lifecycle':object(),'gate':self.gate,'result':{'unit':True},'original_error':None}
        def ref(name):
            return {'path':name,'sha256':sha((self.root/name).read_bytes())}
        self.gate.save('unit-b-closeout.json',{'unit':True})
        self.auth={'status':'SCOPED_REGISTERED_CONTEXT_CLOSED','binding':self.binding,
            'evidence_refs':[ref('unit-b-closeout.json')],'closeout_ref':ref('unit-b-closeout.json')}
        self.fixture={'status':'SCOPED_PHYSICAL_CLOSURE_CONFIRMED_ORIGINAL_STATUS_UNCHANGED',
            'physical_zero':True,'registry_absence_confirmed':True,'registry_commit_confirmed':True,
            'registry_commit_unknown':False}
        self.gate.save('unit-c-closeout.json',self.fixture)
        class ModelProof:
            def unchanged(self):pass
        proof=ModelProof();proof.owner=self.context;proof.receipt=self.fixture;proof.ref=ref('unit-c-closeout.json')
        proof.evidence_refs=[proof.ref]
        self.context._fixture_proof=proof
        self.modules={'runtime_terminal':types.SimpleNamespace(validate_runtime_termination=mock.Mock(return_value=self.worker)),
            'runtime_registered_bootstrap':types.SimpleNamespace(validate_closeout=mock.Mock(return_value=self.auth)),
            'runtime_registered_fixture_closeout':types.SimpleNamespace(Proof=ModelProof)}
        raw=(json.dumps({'sequence':1,'closed':True,'register_sha256':'c'*64})+'\n').encode()
        (self.root/'root.ledger.txt').write_bytes(raw)
        self.gate.save('unit-root-register.json',{'unit':'not a real root program'})
        self.accounting={'status':'NUMERIC_ACCOUNTING_CLOSED','run_id':'unit','register_sha256':'c'*64,
            'hosted_limit':2349,'fault_retained':False,'journal_refs':[ref('root.ledger.txt')],
            'evidence_refs':[ref('unit-root-register.json')]}
        self.root_module=types.SimpleNamespace(__file__=str(self.root/e.ROOT_ADMISSION),
            validate_terminal=mock.Mock(return_value=self.accounting))
        def pack(gate, original_refs):
            self.assertIs(gate,self.gate)
            self.ledger.close.assert_called_once_with()
            self.root_module.validate_terminal.assert_called_once()
            self.assertIsNone(self.owner._terminal_proof)
            gate.save('case-original-index.json',{'unit_only':True,'original_refs':original_refs})
            raw=(self.root/'case-original-index.json').read_bytes()
            return {'path':'case-original-index.json','sha256':sha(raw),'bytes':len(raw)}
        self.archive_module=types.SimpleNamespace(__file__=str(self.root/e.ARCHIVE_SOURCE),
            pack=mock.Mock(side_effect=pack))
        patcher=mock.patch.object(e,'dependency',side_effect=lambda root,sources,name:self.modules[name])
        patcher.start();self.addCleanup(patcher.stop)
        self.gate.save('unit-worker-export.json',{'unit_only':True,'case_pass':False})
        patcher=mock.patch('quota_candidate_v1.runtime_worker_evidence.export',
            return_value=(ref('unit-worker-export.json'),[ref('unit-worker-io.json')]))
        self.worker_export=patcher.start();self.addCleanup(patcher.stop)
        patcher=mock.patch.object(t.importlib,'import_module',side_effect=lambda name:{
            'admission_budget_root_runtime':self.root_module,
            'admission_case_archive':self.archive_module}[name])
        patcher.start();self.addCleanup(patcher.stop)

    def finish(self,error=None):
        return t.finish(self.owner,self.gate,self.context,self.owners,original_error=error)

    def test_simulated_join_calls_all_independent_validators_and_closes_root_once(self):
        result=self.finish()
        self.ledger.close.assert_called_once_with()
        self.root_module.validate_terminal.assert_called_once_with(self.ledger,self.gate,self.binding)
        self.modules['runtime_registered_bootstrap'].validate_closeout.assert_called_once_with(
            self.context,gate=self.gate,binding=self.binding)
        self.assertEqual(result['scope'],'single_disposable_case_only')
        self.assertFalse(result['full_chain_admission']);self.assertFalse(result['hosted_admitted'])
        self.assertTrue(result['matrix_aggregation_required'])
        self.assertEqual(result['format'],'disposable-case-terminal-v1')
        names=[row['path'] for row in result['original_refs']]
        self.assertEqual(names,sorted(set(names)))
        self.assertIn('root.ledger.txt',names)
        self.assertIn('unit-worker-io.json',names)
        self.assertIn('unit-c-closeout.json',names)
        self.archive_module.pack.assert_called_once_with(self.gate,result['original_refs'])
        self.assertEqual(result['original_archive_ref']['path'],'case-original-index.json')
        self.assertNotIn('case-original-index.json',names)
        self.assertEqual(result['terminal_source_hashes'],self.owner._sources)
        with self.assertRaisesRegex(CandidateStop,'execution_owner'):self.finish()
        self.ledger.close.assert_called_once()

    def test_normal_body_or_cleanup_error_cannot_be_pass(self):
        with self.assertRaisesRegex(CandidateStop,'normal_failed'):self.finish(RuntimeError('unit error'))
        self.ledger.close.assert_not_called()

    def test_missing_wait_or_lost_result_export_cannot_close_root_or_pass(self):
        self.worker_export.side_effect=CandidateStop('worker_wait_unconfirmed')
        with self.assertRaisesRegex(CandidateStop,'worker_wait_unconfirmed'):self.finish()
        self.ledger.close.assert_not_called();self.archive_module.pack.assert_not_called()
        self.assertIsNone(self.owner._terminal_proof)

    def test_unfired_fault_cannot_be_promoted_by_other_proofs(self):
        self.owner._case_name='route_a'
        with self.assertRaisesRegex(CandidateStop,'expected_fault_missing'):self.finish(RuntimeError('unit'))
        self.ledger.close.assert_not_called()

    def test_early_absence_without_complete_numeric_prefix_cannot_close_case(self):
        self.owner._case_name='pre_migration'
        self.fault.fired={'original_error_code':'case_injected_pre_migration'}
        self.owner._bootstrap_termination={'isolation':{'unit':True},
            'proof':{'status':'BOOTSTRAP_TERMINATION_VERIFIED'}}
        with self.assertRaisesRegex(CandidateStop,'bootstrap_numeric_missing'):
            t.finish(self.owner,self.gate,None,{},original_error=RuntimeError('unit planned'))
        self.ledger.close.assert_not_called()
        self.archive_module.pack.assert_not_called()

    def test_source_change_rejects_before_any_validator_or_close(self):
        (self.root/e.ROOT_ADMISSION).write_bytes(b'changed')
        with self.assertRaisesRegex(CandidateStop,'source_changed'):self.finish()
        self.ledger.close.assert_not_called()
        self.modules['runtime_terminal'].validate_runtime_termination.assert_not_called()

    def test_original_worker_receipt_must_equal_live_revalidation(self):
        self.gate.save('case-runtime-terminal.json',{'status':'changed'})
        with self.assertRaisesRegex(CandidateStop,'worker_original'):self.finish()
        self.ledger.close.assert_not_called()

    def test_missing_auth_validator_cannot_be_replaced_by_status_boolean(self):
        del self.modules['runtime_registered_bootstrap'].validate_closeout
        with self.assertRaisesRegex(CandidateStop,'auth_validator_missing'):self.finish()
        self.ledger.close.assert_not_called()

    def test_unknown_auth_remains_no_go_even_with_worker_complete(self):
        self.modules['runtime_registered_bootstrap'].validate_closeout.side_effect=ValueError('unit unknown mint')
        with self.assertRaisesRegex(ValueError,'unknown mint'):self.finish()
        self.ledger.close.assert_not_called()

    def test_altered_auth_original_ref_rejects(self):
        self.gate.save('unit-b-closeout.json',{'changed':True})
        with self.assertRaisesRegex(CandidateStop,'reference_hash'):self.finish()
        self.ledger.close.assert_not_called()

    def test_fixture_proof_requires_exact_issued_type_and_context(self):
        self.context._fixture_proof=types.SimpleNamespace(owner=self.context,receipt=self.fixture)
        with self.assertRaisesRegex(CandidateStop,'fixture_owner'):self.finish()
        self.ledger.close.assert_not_called()

    def test_unconfirmed_fixture_commit_stays_no_go(self):
        self.fixture['registry_commit_unknown']=True
        with self.assertRaisesRegex(CandidateStop,'fixture_unconfirmed'):self.finish()
        self.ledger.close.assert_not_called()

    def test_unlisted_fixture_originals_prevent_terminal_join(self):
        self.context._fixture_proof.evidence_refs=[]
        with self.assertRaisesRegex(CandidateStop,'fixture_evidence_missing'):self.finish()
        self.ledger.close.assert_not_called()

    def test_altered_original_io_receipt_cannot_hide_behind_worker_summary(self):
        self.gate.save('unit-worker-io.json',{'unit':'changed'})
        with self.assertRaisesRegex(CandidateStop,'reference_hash'):self.finish()
        self.ledger.close.assert_not_called()

    def test_root_unknown_cannot_be_replaced_by_closed_boolean(self):
        self.root_module.validate_terminal.side_effect=ValueError('unit unknown consumed')
        with self.assertRaisesRegex(ValueError,'unknown consumed'):self.finish()
        self.assertIsNone(self.owner._terminal_proof)
        self.ledger.close.assert_called_once()

    def test_root_journal_must_match_original_bytes_and_closed_sequence(self):
        (self.root/'root.ledger.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(CandidateStop,'reference_hash'):self.finish()
        self.assertIsNone(self.owner._terminal_proof)

    def test_root_hash_without_original_program_payloads_is_insufficient(self):
        self.accounting.pop('evidence_refs')
        with self.assertRaisesRegex(CandidateStop,'root_originals_missing'):self.finish()
        self.archive_module.pack.assert_not_called()
        self.assertIsNone(self.owner._terminal_proof)

    def test_reference_path_escape_denied(self):
        with self.assertRaisesRegex(CandidateStop,'reference_path'):
            t.original(self.gate,{'path':'../outside','sha256':'0'*64})

    def test_unbound_packer_source_rejects_without_packing(self):
        del self.owner._sources[e.ARCHIVE_SOURCE]
        with self.assertRaisesRegex(CandidateStop,'archive_source'):self.finish()
        self.archive_module.pack.assert_not_called()
        self.assertIsNone(self.owner._terminal_proof)

    def test_pack_failure_never_emits_case_pass(self):
        failure=OSError('unit original archive write failure')
        self.archive_module.pack.side_effect=failure
        with self.assertRaises(OSError) as caught:self.finish()
        self.assertIs(caught.exception,failure)
        self.assertIsNone(self.owner._terminal_proof)

    def test_pack_return_must_be_exact_flat_index_reference(self):
        for reference in ({'path':'wrong-index.json','sha256':'0'*64,'bytes':1},
                          {'path':'case-original-index.json','sha256':'0'*64,'bytes':1,'ok':True},
                          {'ref':{'path':'case-original-index.json','sha256':'0'*64,'bytes':1}}):
            with self.subTest(reference=reference):
                self.owner._terminal_attempted=False
                self.ledger.close.reset_mock();self.root_module.validate_terminal.reset_mock()
                for name in ('case-auth-context-terminal.json','case-root-terminal.json'):
                    (self.root/name).unlink(missing_ok=True)
                self.archive_module.pack.side_effect=None
                self.archive_module.pack.return_value=reference
                with self.assertRaisesRegex(CandidateStop,'archive_ref'):self.finish()
                self.assertIsNone(self.owner._terminal_proof)

    def test_corrupt_packed_index_cannot_be_claimed_complete(self):
        self.gate.save('case-original-index.json',{'unit':'corrupt'})
        self.archive_module.pack.side_effect=None
        self.archive_module.pack.return_value={'path':'case-original-index.json','sha256':'0'*64,'bytes':1}
        with self.assertRaisesRegex(CandidateStop,'reference_hash'):self.finish()
        self.assertIsNone(self.owner._terminal_proof)

    def test_original_nested_journal_is_explicitly_sent_to_main_packer(self):
        path=self.root/'registered-unit-private'/'001.json';path.parent.mkdir()
        path.write_bytes(b'{"unit":"no real evidence"}')
        self.auth['evidence_refs'].append({'path':path.relative_to(self.root).as_posix(),
                                         'sha256':sha(path.read_bytes()),'bytes':path.stat().st_size})
        result=self.finish()
        refs=self.archive_module.pack.call_args.args[1]
        self.assertEqual(refs,result['original_refs'])
        self.assertIn('registered-unit-private/001.json',[row['path'] for row in refs])

    def test_main_packer_round_trip_preserves_every_explicit_original_byte(self):
        import admission_case_archive as archive
        self.archive_module=archive
        raw=pathlib.Path(archive.__file__).read_bytes()
        (self.root/e.ARCHIVE_SOURCE).write_bytes(raw)
        self.owner._sources[e.ARCHIVE_SOURCE]=sha(raw)
        path=self.root/'registered-unit-private'/'001.json';path.parent.mkdir()
        path.write_bytes(b'{"unit":"not real case evidence"}\r\n')
        self.auth['evidence_refs'].append({'path':path.relative_to(self.root).as_posix(),
            'sha256':sha(path.read_bytes()),'bytes':path.stat().st_size})
        result=self.finish()
        payloads={p.name:p.read_bytes() for p in self.root.glob('case-original-*.json')}
        restored=archive.verify(payloads,result['original_archive_ref'],result['original_refs'])
        self.assertEqual(set(restored),{ref['path'] for ref in result['original_refs']})
        for name,data in restored.items():
            self.assertEqual(data,(self.root/name).read_bytes())
        self.assertFalse(result['full_chain_admission'])
        self.assertFalse(result['hosted_admitted'])


if __name__=='__main__':unittest.main()
