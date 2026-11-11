"""Offline orchestration regressions; fake owners do not prove actual execution."""
import hashlib
import copy
import pathlib
import types
import json
import tempfile
import unittest
from unittest import mock

import hosted_gate
import registered_runner
from quota_candidate_v1 import runtime_case_entry as e
from quota_candidate_v1.compiler import CandidateStop
from admission_quota_readonly import QUERIES
from integral_io import SNAPSHOT
from integral_stream import GUARD


class EntryJoinTests(unittest.TestCase):
    def setUp(self):
        self.gate=mock.Mock()
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.gate.out=pathlib.Path(tmp.name)
        self.gate.save.side_effect=lambda name,value:(self.gate.out/name).write_text(json.dumps(value))
        self.binding={'run_id':'00000000-0000-4000-8000-000000000001'}
        self.isolation={'unit':'not measured'}
        sources={e.PREFIX+n:hashlib.sha256(pathlib.Path(m.__file__).read_bytes()).hexdigest()
                 for m,n in ((hosted_gate,'hosted_gate.py'),(registered_runner,'registered_runner.py'))}
        guard_file=pathlib.Path(e.__file__)
        sources[e.RENDERERS['guard']]=hashlib.sha256(guard_file.read_bytes()).hexdigest()
        self.quota={'root':str(guard_file.parent),'manifest':{'sources':sources},
                    'binding':self.binding,'isolation':self.isolation}
        self.prepared=mock.Mock(spec=e.PreparedCase)
        self.prepared.config.return_value=self.quota
        self.ids={'a_member':'a','a_trainer':'t','b_member':'b'}
        self.context=types.SimpleNamespace(isolation=self.isolation,ids=self.ids,runtime=object(),
            config={'registeredIds':self.ids,'environment':'disposable_ci','mode':'registered_synthetic'},
            bind_case=mock.Mock())
        self.artifact={'manifest':self.quota['manifest'],'sql':'unit fake, never SQL'}
        self.c=mock.Mock();self.c.meter.receipt.return_value={'unit':True};self.c.commands=[]
        self.identity=mock.Mock();self.scalar=mock.Mock();self.lifecycle=mock.Mock(worker_owned=False,http_journal=None)
        self.faults=mock.Mock();self.faults.receipt.return_value={'fault_observed':False}
        self.preservation=mock.Mock()
        modules={'runtime_lifecycle':types.SimpleNamespace(CasePreservation=mock.Mock(return_value=self.preservation)),
                 'runtime_catalog':types.SimpleNamespace(CaseCatalog=mock.Mock())}
        renderers={'guard':object(),'audit':types.SimpleNamespace(g=types.SimpleNamespace(__file__=str(guard_file))),
                   'contract':types.SimpleNamespace(Contract=object())}
        self.order=[]
        self.context.bind_case.side_effect=lambda *a:self.order.append('bind')
        self.preservation.prepare_prefix.side_effect=lambda *a:self.order.append('prefix')
        self.c.confirm_case_prefix.side_effect=lambda *a:self.order.append('confirm')
        self.result={'unit_worker_result':True}
        def execute(*args):
            self.order.append('execute')
            return self.result
        patches=[mock.patch.object(e,'dependency',side_effect=lambda r,s,n:modules[n]),
            mock.patch.object(e,'bound_module',side_effect=lambda r,s,n:next(renderers[k] for k,v in e.RENDERERS.items() if v==n)),
            mock.patch.object(e,'CaseComposition',return_value=self.c),
            mock.patch.object(e,'CaseLifecycle',return_value=self.lifecycle),
            mock.patch.object(e,'PendingPrefix'),mock.patch.object(e,'PrefixGate'),
            mock.patch.object(e,'CaseHistory'),mock.patch.object(e,'CaseStream'),
            mock.patch.object(e,'execute_case',side_effect=execute),
            mock.patch.object(hosted_gate,'ScalarSession',return_value=self.scalar),
            mock.patch.object(registered_runner,'IdentitySession',return_value=self.identity)]
        for p in patches:p.start();self.addCleanup(p.stop)

    def run_body(self):
        return e.execute_registered(self.gate,self.prepared,self.context,self.artifact,{},self.faults)

    def test_actual_entry_calls_prefix_confirm_then_existing_runner(self):
        value=self.run_body()
        self.assertEqual(self.order,['bind','prefix','confirm','execute'])
        self.context.bind_case.assert_called_once_with(self.lifecycle,self.c)
        self.assertIs(value['result'],self.result)
        self.assertNotIn('status',value)
        self.identity.close.assert_called_once_with();self.scalar.close.assert_called_once_with()
        self.lifecycle.parent_auth_cleanup.assert_not_called()
        self.lifecycle.close_temporary.assert_not_called()
        self.assertEqual(e.CaseLifecycle.call_args.kwargs['ids'],self.ids)

    def test_prefix_failure_never_starts_worker_and_closes_both_sessions(self):
        error=RuntimeError('unit original')
        self.preservation.prepare_prefix.side_effect=error
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,error)
        e.execute_case.assert_not_called()
        self.identity.close.assert_called_once();self.scalar.close.assert_called_once()
        self.c.abort.assert_any_call('case_registered_body_failed')

    def test_worker_failure_remains_primary_after_both_close_and_save_failures(self):
        original=RuntimeError('unit worker')
        e.execute_case.side_effect=original
        self.identity.close.side_effect=ValueError('unit close')
        self.scalar.close.side_effect=OSError('unit close2')
        self.gate.save.side_effect=OSError('unit save')
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.scalar.close.assert_called_once()
        self.assertEqual(len(original.__notes__),3)
        self.lifecycle.parent_auth_cleanup.assert_not_called()

    def test_close_failure_cannot_return_success_after_worker_result(self):
        self.identity.close.side_effect=OSError('unit close')
        with self.assertRaisesRegex(CandidateStop,'case_registered_close_incomplete'):self.run_body()
        self.scalar.close.assert_called_once()
        self.assertFalse(self.gate.save.call_args.args[1]['complete'])

    def test_save_failure_without_prior_failure_is_not_swallowed(self):
        self.gate.save.side_effect=OSError('unit save')
        with self.assertRaises(OSError):self.run_body()
        self.c.abort.assert_any_call('case_finally_receipt_failed')

    def test_meter_snapshot_failure_does_not_replace_worker_failure(self):
        original=RuntimeError('unit worker')
        e.execute_case.side_effect=original
        self.c.meter.receipt.side_effect=ValueError('unit receipt')
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertIn('case_finally_save_secondary:ValueError',original.__notes__)

    def test_foreign_context_rejected_before_loading_or_dispatch(self):
        self.context.isolation={'unit':'different'}
        with self.assertRaisesRegex(CandidateStop,'case_entry_context_binding'):self.run_body()
        e.dependency.assert_not_called();e.execute_case.assert_not_called()

    def test_wrong_registeredids_rejected_before_loading_or_dispatch(self):
        self.context.config['registeredIds']={}
        with self.assertRaisesRegex(CandidateStop,'case_entry_context_scope'):self.run_body()
        e.dependency.assert_not_called();e.execute_case.assert_not_called()

    def test_transitive_guard_source_mismatch_stops_before_prefix(self):
        self.quota['manifest']['sources'][e.RENDERERS['guard']]='f'*64
        with self.assertRaisesRegex(CandidateStop,'case_entry_audit_guard_source'):self.run_body()
        e.execute_case.assert_not_called()

    def test_failure_handoff_retains_actual_owners_for_context_cleanup(self):
        original=RuntimeError('unit prefix')
        self.preservation.prepare_prefix.side_effect=original
        owners={}
        with self.assertRaises(RuntimeError) as caught:
            e.execute_registered(self.gate,self.prepared,self.context,self.artifact,{},self.faults,owners=owners)
        self.assertIs(caught.exception,original)
        self.assertIs(owners['composition'],self.c)
        self.assertIs(owners['lifecycle'],self.lifecycle)
        self.assertIs(owners['original_error'],original)
        self.assertIsNone(owners['result'])

    def test_bind_failure_prevents_prefix_and_worker_without_losing_owners(self):
        original=RuntimeError('unit context bind')
        self.context.bind_case.side_effect=original
        owners={}
        with self.assertRaises(RuntimeError):
            e.execute_registered(self.gate,self.prepared,self.context,self.artifact,{},self.faults,owners=owners)
        self.preservation.prepare_prefix.assert_not_called()
        e.execute_case.assert_not_called()
        self.assertIs(owners['lifecycle'],self.lifecycle)

    def test_second_session_constructor_failure_closes_first(self):
        original=RuntimeError('unit identity initialization')
        registered_runner.IdentitySession.side_effect=original
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.scalar.close.assert_called_once()
        self.identity.close.assert_not_called()
        self.context.bind_case.assert_not_called()

    def test_abort_failure_cannot_replace_original_worker_error(self):
        original=RuntimeError('unit worker')
        e.execute_case.side_effect=original
        self.c.abort.side_effect=ValueError('unit abort')
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertIn('case_abort_secondary:ValueError',original.__notes__)


class NumericConnection:
    """In-memory protocol model for real QueryIO, not PG/WAL evidence."""
    def __init__(self, *, fail_at=None, wal=0, close_failure=False):
        self.calls=[];self.closed=False;self.fail_at=fail_at
        self.wal=wal;self.close_failure=close_failure
        self.original=RuntimeError('unit transport result lost')
        self.qids={SNAPSHOT:1,**{sql:i+2 for i,sql in enumerate(QUERIES.values())}}
        self.counts={qid:0 for qid in self.qids.values()}

    def execute(self, text, args=()):
        self.calls.append(text)
        if len(self.calls)==self.fail_at:raise self.original
        if text.startswith('EXPLAIN '):
            sql=text.split(') ',1)[1]
            plan={'Query Identifier':self.qids[sql],'Plan':{'Actual Rows':1},'Execution Time':0}
            rows=[{'QUERY PLAN':[plan]}]
        elif text==SNAPSHOT:
            stats=[{'queryid':str(q),'calls':n,'since':'unit','temp_read':0,'temp_written':0,
                    'wal':self.wal if q==2 and n else 0,'exec_ms':0,
                    'wal_records':0,'wal_fpi':0} for q,n in self.counts.items() if n]
            rows=[{'value':{'reset':'unit','dealloc':0,'statements':copy.deepcopy(stats),
                'background':{'reset':'unit','temp_bytes':0},'health':{'io_wait':0,'long_active':0}}}]
            self.counts[1]+=1
        elif text in QUERIES.values():
            self.counts[self.qids[text]]+=1
            rows=[{'unit_secret_not_exported':'synthetic function body'}]
        elif text==GUARD:
            rows=[{'ro':'on','db':'postgres','role':'postgres','ssl':True}]
        else:rows=[]
        return types.SimpleNamespace(description=bool(rows),fetchall=lambda:rows)

    def close(self):
        self.closed=True
        if self.close_failure:raise OSError('unit close failure')


class QuotaReadTests(unittest.TestCase):
    def setUp(self):
        # Keep the real QueryIO; parameter conversion is irrelevant to this model.
        p=mock.patch('integral_ci.bind_parameters',side_effect=lambda text,args:(text,args))
        p.start();self.addCleanup(p.stop)
        self.gate=mock.Mock();self.ledger=mock.Mock()
        self.ledger.precharge.return_value='unit fixed ticket'

    def runtime(self, connection):
        return types.SimpleNamespace(environment='disposable_ci',connect=mock.Mock(return_value=connection))

    def test_twenty_commands_one_macro_and_no_function_body_exported(self):
        connection=NumericConnection()
        samples=e.quota_samples(self.gate,self.runtime(connection),self.ledger)
        self.assertEqual(set(samples),set(QUERIES))
        self.assertEqual(len(connection.calls),20)
        self.assertEqual(connection.calls.count('ROLLBACK'),1)
        self.assertTrue(connection.closed)
        self.ledger.precharge.assert_called_once_with('case.quota_read')
        self.ledger.confirm.assert_called_once_with('unit fixed ticket',observed_sql_commands=20)
        self.ledger.unknown.assert_not_called()
        name,receipt=self.gate.save.call_args.args
        self.assertEqual(name,'case-quota-read.json')
        self.assertNotIn('unit_secret_not_exported',str(receipt))
        self.assertNotIn('synthetic function body',str(receipt))
        self.assertTrue(all(c['confirmed'] and c['covered_by']=='case.quota_read'
                            for c in receipt['commands']))
        self.assertEqual(receipt['io']['last_pair']['own_wal_bytes'],0)
        program=e.quota_read_program()
        self.assertEqual(program['sql_command_bound'],20)
        self.assertEqual([r['id'] for r in program['commands']],
                         [r['id'] for r in receipt['commands']])
        self.assertEqual([r['sql_sha256'] for r in program['commands']],
                         [r['sql_sha256'] for r in receipt['commands']])

    def test_every_lost_response_retains_original_and_rolls_back_at_most_once(self):
        for failed in range(1,21):
            with self.subTest(failed=failed):
                self.ledger.reset_mock()
                connection=NumericConnection(fail_at=failed)
                self.ledger.unknown.side_effect=lambda *a,**k:self.assertTrue(connection.closed)
                with self.assertRaises(RuntimeError) as caught:
                    e.quota_samples(self.gate,self.runtime(connection),self.ledger)
                self.assertIs(caught.exception,connection.original)
                self.assertEqual(connection.calls.count('ROLLBACK'),1)
                self.assertLessEqual(len(connection.calls),20)
                self.assertTrue(connection.closed)
                self.ledger.confirm.assert_not_called()
                self.ledger.unknown.assert_called_once_with('unit fixed ticket',reason='not_terminal')

    def test_root_rejection_precedes_connection(self):
        runtime=self.runtime(NumericConnection())
        self.ledger.precharge.side_effect=RuntimeError('unit blocked')
        with self.assertRaises(RuntimeError):e.quota_samples(self.gate,runtime,self.ledger)
        runtime.connect.assert_not_called()

    def test_wal_nonzero_not_relaxed_and_failure_receipt_adds_no_sql(self):
        connection=NumericConnection(wal=1)
        with self.assertRaisesRegex(ValueError,'io_read_wal'):
            e.quota_samples(self.gate,self.runtime(connection),self.ledger)
        self.assertEqual(len(connection.calls),19)
        self.assertEqual(connection.calls[-1],'ROLLBACK')
        self.ledger.confirm.assert_not_called()
        evidence=self.gate.save.call_args.args[1]
        self.assertEqual(evidence['reason'],'io_read_wal')
        self.assertEqual(evidence['additional_sql_commands'],0)
        self.assertFalse(evidence['query_text_read'])

    def test_close_and_ledger_failure_do_not_replace_original(self):
        connection=NumericConnection(fail_at=8,close_failure=True)
        self.ledger.unknown.side_effect=ValueError('unit ledger')
        with self.assertRaises(RuntimeError) as caught:
            e.quota_samples(self.gate,self.runtime(connection),self.ledger)
        self.assertIs(caught.exception,connection.original)
        self.assertEqual(len(connection.original.__notes__),2)

    def test_receipt_failure_is_no_go_after_confirmed_rollback(self):
        connection=NumericConnection()
        self.gate.save.side_effect=OSError('unit receipt')
        with self.assertRaises(OSError):e.quota_samples(self.gate,self.runtime(connection),self.ledger)
        self.assertEqual(len(connection.calls),20)
        self.ledger.confirm.assert_not_called()
        self.ledger.unknown.assert_called_once()

    def test_remote_environment_never_precharged_or_connected(self):
        runtime=self.runtime(NumericConnection());runtime.environment='hosted'
        with self.assertRaisesRegex(CandidateStop,'case_quota_local_only'):
            e.quota_samples(self.gate,runtime,self.ledger)
        self.ledger.precharge.assert_not_called();runtime.connect.assert_not_called()


class ContextJoinTests(unittest.TestCase):
    def setUp(self):
        self.real_terminal=e.terminal_witness
        self.order=[]
        self.gate=mock.Mock()
        self.owners={}
        self.ledger=mock.Mock()
        self.ledger.precharge.side_effect=lambda name:self.order.append(name) or name
        self.ledger.confirm.side_effect=lambda *a,**k:self.order.append(('confirm',a[0],k['observed_sql_commands']))
        self.ledger.defer.side_effect=lambda *a,**k:self.order.append(('defer',a[0],k['partial_observed_sql_commands']))
        self.ledger.defer_fault.side_effect=lambda *a,**k:self.order.append(('defer_fault',a[0],k['partial_observed_sql_commands']))
        self.ledger.unknown.side_effect=lambda *a,**k:self.order.append(('unknown',a[0]))
        self.ledger.fault.side_effect=lambda *a,**k:self.order.append(('fault',a[0],k['observed_sql_commands']))
        outer=self
        class Context:
            runtime=object()
            isolation={'unit':True}
            admission_connection={'unit':True}
            ca_path='unit'
            execution_ledger=outer.ledger
            close_error=None
            enter_error=None
            suppress=False
            closeout=None
            def __enter__(self):
                outer.order.append('enter')
                if self.enter_error:raise self.enter_error
                return self
            def __exit__(self,kind,original,tb):
                outer.order.append('exit')
                self.closeout={'unit_not_evidence':True}
                if self.close_error:raise self.close_error
                return self.suppress
        self.context=Context()
        self.report={'dag':{},'dag_sha256':'unit'}
        def body(*args,owners):
            self.order.append('worker')
            owners.update(result={'unit':True},composition=object(),lifecycle=object(),gate=self.gate)
        patches=[
            mock.patch.object(e,'quota_samples',side_effect=lambda g,r,l:self.order.append('quota') or {}),
            mock.patch('quota_candidate_v1.compiler.compile_candidate',return_value={'unit':True}),
            mock.patch('quota_candidate_v1.runtime_adapter.prepare_case',return_value=object()),
            mock.patch.object(e,'execute_registered',side_effect=body),
            mock.patch.object(e,'observed_core',return_value=51),
            mock.patch.object(e,'terminal_witness',side_effect=lambda *a:
                self.order.append('terminal') or {'case_pass':False,'unit':True}),
            mock.patch.object(e,'observed_fault_core',side_effect=CandidateStop('unit unknown partition'))]
        self.compiled=patches[1].start();self.addCleanup(patches[1].stop)
        for patcher in (patches[0],*patches[2:]):
            patcher.start();self.addCleanup(patcher.stop)

    def run_body(self):
        return e.execute_context(self.gate,self.context,'unit',{'sources':{}},'unit',self.report,mock.Mock(),owners=self.owners)

    def test_quota_prepare_core_use_only_context_child_and_exit_last(self):
        self.assertIs(self.run_body(),self.owners)
        self.assertEqual(self.order,['enter','quota','case.prepare',('confirm','case.prepare',0),
            'case.core','worker',('defer','case.core',51),'terminal','exit'])
        self.assertIs(e.quota_samples.call_args.args[2],self.ledger)
        self.ledger.unknown.assert_not_called()

    def test_pure_preparation_failure_records_zero_then_cleanup(self):
        original=ValueError('unit compiler')
        self.compiled.side_effect=original
        with self.assertRaises(ValueError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertEqual(self.order[-2:],[('fault','case.prepare',0),'exit'])
        self.ledger.fault.assert_called_once_with('case.prepare',observed_sql_commands=0,reason='validation_failed')
        e.execute_registered.assert_not_called()
        self.ledger.unknown.assert_not_called()

    def test_core_unknown_marked_before_context_cleanup(self):
        original=RuntimeError('unit worker')
        e.execute_registered.side_effect=original
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertEqual(self.order[-2:],[('unknown','case.core'),'exit'])
        self.ledger.confirm.assert_called_once_with('case.prepare',observed_sql_commands=0)
        self.ledger.defer.assert_not_called()

    def test_cleanup_secondary_cannot_replace_body_primary(self):
        original=RuntimeError('unit worker')
        e.execute_registered.side_effect=original
        self.context.close_error=OSError('unit context')
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertIn('case_context_close_secondary:OSError',original.__notes__)

    def test_context_suppression_cannot_turn_fault_into_success(self):
        original=RuntimeError('unit worker')
        e.execute_registered.side_effect=original
        self.context.suppress=True
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)

    def test_enter_failure_has_no_child_dispatch(self):
        original=RuntimeError('unit startup')
        self.context.enter_error=original
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertEqual(self.order,['enter'])
        e.quota_samples.assert_not_called();self.ledger.precharge.assert_not_called()

    def test_unknown_receipt_failure_retains_primary_and_runs_cleanup(self):
        original=RuntimeError('unit worker')
        e.execute_registered.side_effect=original
        self.ledger.unknown.side_effect=OSError('unit ledger')
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertEqual(self.order[-1],'exit')
        self.assertIn('case_core_ledger_secondary:OSError',original.__notes__)

    def test_context_error_not_relabelled_as_registered_worker_error(self):
        original=RuntimeError('unit context close')
        owners={'gate':self.gate,'composition':object(),'lifecycle':object(),
                'result':{'unit_worker':True},'original_error':None}
        validator=mock.Mock(return_value={'status':'REGISTERED_WORKER_COMPLETE','case_pass':False})
        with mock.patch.object(e,'dependency',return_value=types.SimpleNamespace(
                validate_runtime_termination=validator)):
            # This test calls the real helper, not the orchestration stub.
            proof=self.real_terminal(self.gate,'unit',{},owners,self.context,'normal',object(),original)
        self.assertIsNone(validator.call_args.kwargs['original_error'])
        self.assertFalse(proof['case_pass'])

    def test_fault_terminal_available_before_context_exit_without_hiding_original(self):
        original=RuntimeError('unit worker')
        def fail(*args,owners):
            owners.update(lifecycle=object(),original_error=original)
            raise original
        e.execute_registered.side_effect=fail
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertEqual(self.order[-3:],['terminal',('unknown','case.core'),'exit'])
        self.assertFalse(self.owners['terminal_proof']['case_pass'])

    def test_terminal_validator_failure_is_secondary_and_never_retried(self):
        original=RuntimeError('unit worker')
        def fail(*args,owners):
            owners.update(lifecycle=object(),original_error=original)
            raise original
        e.execute_registered.side_effect=fail
        e.terminal_witness.side_effect=ValueError('unit missing evidence')
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertIn('case_worker_terminal_secondary:ValueError',original.__notes__)
        e.terminal_witness.assert_called_once()
        self.assertEqual(self.order[-1],'exit')
        self.assertNotIn('terminal_proof',self.owners)

    def test_known_fault_defers_only_confirmed_native_partition_before_cleanup(self):
        original=RuntimeError('unit worker')
        def fail(*args,owners):
            owners.update(lifecycle=object(),original_error=original)
            raise original
        e.execute_registered.side_effect=fail
        e.observed_fault_core.side_effect=None;e.observed_fault_core.return_value=51
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertEqual(self.order[-3:],['terminal',('defer_fault','case.core',51),'exit'])
        self.ledger.unknown.assert_not_called()


class NativePartitionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.gate=types.SimpleNamespace(out=pathlib.Path(self.temp.name),save=mock.Mock())
        self.preflight={'complete':True,'connection_closed':True,'rollback_confirmed':True,
                        'commands':[{'confirmed':True} for _ in range(4)]}
        (self.gate.out/'integral-preflight.json').write_text(json.dumps(self.preflight))
        self.c=types.SimpleNamespace(quota={'binding':{'run_id':'unit'}},meter_stack=[],
            commands=[{'command':1,'phase':'unit','confirmed':True}],
            meter=types.SimpleNamespace(stopped=True,events=[
                {'kind':'native','commands':5,'confirmed':True},
                {'kind':'managed_auth','commands':400,'confirmed':False},
                *[{'kind':'cli_reserved','commands':n,'confirmed':True} for n in (72,36)]]))
        self.cli=[{'slot':slot,'protocol_commands':n,'observer_commands':[{}]*8}
                  for slot,n in (('quota',17),('pre_auth',7))]
        self.owners={'composition':self.c,'terminal_proof':{
            'status':'REGISTERED_FAULT_TERMINATED','run_id':'unit'},
            'session_close_errors':[], 'gate':types.SimpleNamespace(cli_protocol=self.cli,
            prefix=types.SimpleNamespace(attempts=['quota','pre_auth']))}
        patcher=mock.patch('cli_envelope.charged',side_effect=lambda x:72 if x['slot']=='quota' else 36)
        patcher.start();self.addCleanup(patcher.stop)

    def test_actual_native_counts_exclude_managed_and_cli_reservations(self):
        self.assertEqual(e.observed_fault_core(self.gate,self.owners),45)
        self.assertFalse(self.gate.save.call_args.args[1]['managed_auth_included'])
        self.assertFalse(self.gate.save.call_args.args[1]['case_pass'])

    def test_unknown_native_or_mismatched_meter_never_returns_partition(self):
        self.c.commands[0]['confirmed']=False
        with self.assertRaisesRegex(CandidateStop,'native_unknown'):e.observed_fault_core(self.gate,self.owners)
        self.c.commands[0]['confirmed']=True
        self.c.meter.events[0]['commands']=6
        with self.assertRaisesRegex(CandidateStop,'native_partition'):e.observed_fault_core(self.gate,self.owners)
        self.gate.save.assert_not_called()

    def test_unreceipted_cli_attempt_cannot_disappear(self):
        self.owners['gate'].prefix.attempts.append('final')
        with self.assertRaisesRegex(CandidateStop,'cli_unknown'):e.observed_fault_core(self.gate,self.owners)

    def test_unclosed_session_or_unknown_preflight_cannot_be_zero(self):
        self.owners['session_close_errors']=[{'stage':'identity'}]
        with self.assertRaisesRegex(CandidateStop,'native_termination'):e.observed_fault_core(self.gate,self.owners)
        self.owners['session_close_errors']=[]
        self.preflight['commands'][0]['confirmed']=False
        (self.gate.out/'integral-preflight.json').write_text(json.dumps(self.preflight))
        with self.assertRaisesRegex(CandidateStop,'preflight_unknown'):e.observed_fault_core(self.gate,self.owners)


class PreparedOwnerTests(unittest.TestCase):
    """Owner/ordering regression models, not real root admission evidence."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name)
        self.gate=types.SimpleNamespace(sources=self.root,out=self.root,save=mock.Mock(),
            result={'candidate_sha256':'a'*64,'run_id':'123','commit':'b'*40})
        self.sources={'unit.txt':hashlib.sha256(b'unit').hexdigest()}
        (self.root/'unit.txt').write_bytes(b'unit')
        self.candidate={'sha256':'a'*64,'sources':self.sources}
        (self.root/'candidate.json').write_text(json.dumps(self.candidate))
        self.binding={'run_id':'00000000-0000-4000-8000-000000000001',
            'parent_id':'unit','source_commit':'b'*40,'ci_run':'123','candidate_sha':'a'*64}
        self.ledger=mock.Mock();self.faults=mock.Mock()
        self.faults.receipt.return_value={'unit':True}
        self.registered=types.SimpleNamespace(context=mock.Mock())

    def owner(self):
        return e.PreparedExecution(e._PREPARED_KEY,gate=self.gate,root=self.root,
            sources=self.sources,report={},manifest={},binding=self.binding,
            faults=self.faults,ledger=self.ledger,registered=self.registered,case_name='normal')

    def test_properties_are_readonly_and_binding_is_a_copy(self):
        owner=self.owner()
        self.assertIs(owner.ledger,self.ledger)
        owner.binding['run_id']='changed'
        self.assertEqual(owner.binding,self.binding)
        with self.assertRaises(AttributeError):owner.ledger=mock.Mock()
        self.assertEqual(owner.case_name,'normal')

    def test_constructor_requires_private_factory_key(self):
        with self.assertRaisesRegex(CandidateStop,'case_prepared_factory_only'):
            e.PreparedExecution(None,gate=self.gate,root=self.root,sources={},report={},
                manifest={},binding={},faults=None,ledger=None,registered=None,case_name='normal')

    def test_foreign_gate_or_case_cannot_consume_owner(self):
        owner=self.owner()
        for gate,case in ((types.SimpleNamespace(**self.gate.__dict__),'normal'),(self.gate,'route_a')):
            with self.assertRaisesRegex(CandidateStop,'case_prepared_owner_mismatch'):
                owner._consume(gate,case)
        owner._consume(self.gate,'normal')
        with self.assertRaisesRegex(CandidateStop,'case_prepared_already_consumed'):
            owner._consume(self.gate,'normal')

    def test_identity_or_candidate_or_source_change_is_terminal(self):
        for change,reason in (('identity','identity'),('candidate','candidate'),('source','source')):
            with self.subTest(change=change):
                self.gate.result['run_id']='123'
                (self.root/'candidate.json').write_text(json.dumps(self.candidate))
                (self.root/'unit.txt').write_bytes(b'unit')
                owner=self.owner()
                if change=='identity':self.gate.result['run_id']='456'
                elif change=='candidate':(self.root/'candidate.json').write_text('{}')
                else:(self.root/'unit.txt').write_bytes(b'changed')
                with self.assertRaisesRegex(CandidateStop,'case_prepared_'+reason+'_changed'):
                    owner._consume(self.gate,'normal')
                with self.assertRaisesRegex(CandidateStop,'case_prepared_already_consumed'):
                    owner._consume(self.gate,'normal')

    def test_run_reuses_exact_owner_ledger_and_does_not_prepare_again(self):
        owner=self.owner();bootstrap=mock.Mock()
        original=RuntimeError('unit bootstrap stop')
        with mock.patch.object(e,'prepare_execution') as prepare, mock.patch.object(
                e,'execute_bootstrap',side_effect=original) as execute:
            with self.assertRaises(RuntimeError) as caught:
                e.run(self.gate,[],'normal',bootstrap=bootstrap,prepared=owner)
            self.assertIs(caught.exception,original)
            self.assertIs(execute.call_args.args[3],self.ledger)
            self.assertEqual(execute.call_args.args[4],self.binding)
            prepare.assert_not_called()
            with self.assertRaisesRegex(CandidateStop,'case_prepared_already_consumed'):
                e.run(self.gate,[],'normal',bootstrap=bootstrap,prepared=owner)
            self.assertEqual(execute.call_count,1)
        self.registered.context.assert_not_called()

    def test_prepare_factory_rejects_second_owner_before_source_or_uuid_work(self):
        import sys
        import complete_register
        factory=mock.Mock(return_value=self.ledger)
        report={'root_dag':{'unit':True},'root_model':{'unit':True}}
        with mock.patch.object(e,'source_preflight',return_value=(self.root,self.sources,report)), \
             mock.patch.object(e,'dependency',return_value=self.registered), \
             mock.patch('quota_candidate_v1.compiler.prepare',return_value={}) as compile_manifest, \
             mock.patch('quota_candidate_v1.compiler.binding_for_case',return_value=self.binding), \
             mock.patch('quota_candidate_v1.runtime_faults.PhaseFaults',return_value=self.faults), \
             mock.patch.object(complete_register.scenario_source,'capture',return_value={'workflow_actions':[]}), \
             mock.patch.dict(sys.modules,{'admission_budget_root_runtime':types.SimpleNamespace(open_execution_ledger=factory)}), \
             mock.patch.dict(e.os.environ,{'GITHUB_SHA':'b'*40,'GITHUB_RUN_ID':'123'}):
            owner=e.prepare_execution(self.gate,'normal')
            self.assertIs(owner.ledger,self.ledger)
            with self.assertRaisesRegex(CandidateStop,'case_prepared_already_created'):
                e.prepare_execution(self.gate,'normal')
            self.assertEqual(compile_manifest.call_count,1)
            factory.assert_called_once_with(self.gate,dag=report['root_dag'],model=report['root_model'],binding=self.binding)
        self.registered.context.assert_not_called()


class BootstrapJoinTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.gate=mock.Mock(out=pathlib.Path(temp.name));self.ledger=mock.Mock()
        self.gate.save.side_effect=lambda name,value:(self.gate.out/name).write_text(
            json.dumps(value),encoding='ascii')
        self.ledger.precharge.side_effect=lambda name:name
        self.bootstrap=mock.Mock(return_value={'bootstrap_total_sql_commands':57})
        self.binding={'run_id':'ec75cc79-c246-4c83-8055-fbfc3d23738c'}
        self.fault=types.SimpleNamespace(case='normal',fired=None)
        self.closeout=types.SimpleNamespace(collect=mock.Mock(return_value={'unit':True}),
                                          COMMANDS=('unit',)*4)
        self.terminal=types.SimpleNamespace(validate_bootstrap_termination=mock.Mock(
            return_value={'full_chain_admission':False,'unit':True}))
        patcher=mock.patch.object(e,'dependency',side_effect=lambda root,sources,name:
            {'runtime_bootstrap_closeout':self.closeout,'runtime_terminal_bootstrap':self.terminal}[name])
        patcher.start();self.addCleanup(patcher.stop)
        patcher=mock.patch.object(e,'bootstrap_closeout_numeric',return_value={
            'proof':{'observed_sql_commands':4},'ref':{'path':'unit-closeout.json'}})
        self.numeric_closeout=patcher.start();self.addCleanup(patcher.stop)

    def run_body(self):
        return e.execute_bootstrap(self.gate,[],self.bootstrap,self.ledger,self.binding,self.fault,'unit',{})

    def test_case_uuid_is_explicit_before_bootstrap(self):
        self.run_body()
        self.bootstrap.assert_called_once_with(self.gate,[],hooks=self.fault,
            run_id=self.binding['run_id'])

    def test_missing_uuid_never_dispatches_or_precharges(self):
        self.binding={}
        with self.assertRaisesRegex(CandidateStop,'case_bootstrap_run_binding'):self.run_body()
        self.bootstrap.assert_not_called();self.ledger.precharge.assert_not_called()

    def test_invalid_or_parent_uuid_never_dispatches(self):
        for value in (None,False,'not-a-uuid','EC75CC79-C246-4C83-8055-FBFC3D23738C',
                '11a909f4-7113-424a-aa4b-ce9964720a3e','6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'):
            with self.subTest(value=value):
                self.binding={'run_id':value}
                with self.assertRaisesRegex(CandidateStop,'case_bootstrap_run_binding'):self.run_body()
        self.bootstrap.assert_not_called();self.ledger.precharge.assert_not_called()

    def test_failed_dispatch_uses_same_uuid_once(self):
        original=RuntimeError('unit dispatch failure')
        self.bootstrap.side_effect=original
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.bootstrap.assert_called_once_with(self.gate,[],hooks=self.fault,
            run_id=self.binding['run_id'])

    def test_confirmed_count_not_declared_allowance(self):
        self.assertEqual(self.run_body()['bootstrap_total_sql_commands'],57)
        self.ledger.confirm.assert_called_once_with('case.bootstrap.clean47',observed_sql_commands=57)
        self.closeout.collect.assert_not_called()

    def test_both_early_faults_collect_only_after_source_ledger_allows(self):
        for case in ('pre_migration','post_migration'):
            with self.subTest(case=case):
                self.ledger.reset_mock()
                self.fault.case=case;self.fault.fired={'unit':True}
                original=RuntimeError('unit migration boundary')
                self.bootstrap.side_effect=original
                with self.assertRaises(RuntimeError) as caught:self.run_body()
                self.assertIs(caught.exception,original)
                self.ledger.unknown.assert_called_once_with('case.bootstrap.clean47',reason='not_terminal')
                self.ledger.confirm.assert_called_once_with('case.bootstrap.failure_closeout',observed_sql_commands=4)
                self.assertEqual(self.gate.save.call_args.args[0],'case-bootstrap-termination.json')

    def test_unselected_or_unfired_bootstrap_fault_never_collects(self):
        for case,fired in (('normal',None),('pre_migration',None),('route_a',{'unit':True})):
            self.fault.case=case;self.fault.fired=fired
            self.bootstrap.side_effect=RuntimeError('unit unexpected')
            with self.assertRaises(RuntimeError):self.run_body()
            self.closeout.collect.assert_not_called()

    def test_unknown_ledger_failure_never_dispatches_closeout(self):
        original=RuntimeError('unit bootstrap')
        self.bootstrap.side_effect=original
        self.ledger.unknown.side_effect=OSError('unit ledger')
        self.fault.case='pre_migration';self.fault.fired={'unit':True}
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.closeout.collect.assert_not_called()

    def test_closeout_failure_retains_primary_and_its_unknown_reservation(self):
        original=RuntimeError('unit bootstrap')
        self.bootstrap.side_effect=original
        self.closeout.collect.side_effect=OSError('unit observer')
        self.fault.case='pre_migration';self.fault.fired={'unit':True}
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertEqual(self.ledger.unknown.call_count,2)
        self.ledger.confirm.assert_not_called()
        self.assertIn('case_bootstrap_closeout_secondary:OSError',original.__notes__)

    def test_unknown_bootstrap_count_is_no_go_without_fictional_zero(self):
        self.bootstrap.return_value={'bootstrap_total_sql_commands':None}
        with self.assertRaisesRegex(CandidateStop,'case_bootstrap_total_unmeasured'):self.run_body()
        self.ledger.confirm.assert_not_called()
        self.closeout.collect.assert_not_called()

    def test_complete_numeric_fault_uses_fault_edge_never_success_or_unknown(self):
        self.fault.case='pre_migration'
        self.fault.fired={'original_error_code':'case_injected_pre_migration'}
        original=RuntimeError('unit original migration failure')
        self.bootstrap.side_effect=original
        prefix={'proof':{'observed_sql_commands':89},'ref':{'path':'unit-prefix.json'}}
        with mock.patch.object(e,'bootstrap_fault_prefix',return_value=prefix):
            with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.ledger.fault.assert_called_once_with('case.bootstrap.clean47',
            observed_sql_commands=89,reason='validation_failed')
        self.ledger.unknown.assert_not_called()
        self.ledger.confirm.assert_called_once_with('case.bootstrap.failure_closeout',observed_sql_commands=4)
        retained=json.loads((self.gate.out/'case-bootstrap-failure-original.json').read_bytes())
        self.assertEqual(retained['original_exception_class'],'RuntimeError')
        self.assertEqual(retained['original_fault_code'],'case_injected_pre_migration')
        self.assertTrue(retained['bootstrap_numeric_confirmed'])

    def test_numeric_validation_failure_keeps_unknown_even_with_valid_absence(self):
        self.fault.case='post_migration'
        self.fault.fired={'original_error_code':'case_injected_post_migration'}
        original=RuntimeError('unit original')
        self.bootstrap.side_effect=original
        with mock.patch.object(e,'bootstrap_fault_prefix',side_effect=CandidateStop('missing canonical1..44')):
            with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.ledger.fault.assert_not_called()
        self.ledger.unknown.assert_called_once_with('case.bootstrap.clean47',reason='not_terminal')
        self.closeout.collect.assert_called_once()
        retained=json.loads((self.gate.out/'case-bootstrap-failure-original.json').read_bytes())
        self.assertFalse(retained['bootstrap_numeric_confirmed'])
        self.assertIsNone(retained['bootstrap_numeric_prefix_ref'])

    def test_fault_ledger_save_failure_does_not_reclassify_or_dispatch_closeout(self):
        self.fault.case='pre_migration';self.fault.fired={'unit':True}
        original=RuntimeError('unit original');self.bootstrap.side_effect=original
        self.ledger.fault.side_effect=OSError('unit journal failure')
        with mock.patch.object(e,'bootstrap_fault_prefix',return_value={
                'proof':{'observed_sql_commands':89},'ref':{'path':'unit-prefix.json'}}):
            with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.ledger.unknown.assert_not_called()
        self.closeout.collect.assert_not_called()
        self.assertIn('case_bootstrap_ledger_secondary:OSError',original.__notes__)

    def test_original_save_failure_attaches_secondary_without_masking_or_retry(self):
        self.fault.case='pre_migration';self.fault.fired={'unit':True}
        original=RuntimeError('unit original');self.bootstrap.side_effect=original
        original_save=self.gate.save.side_effect
        def save(name,value):
            if name=='case-bootstrap-failure-original.json':raise OSError('unit disk')
            return original_save(name,value)
        self.gate.save.side_effect=save
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.assertIn('case_bootstrap_original_save_secondary:OSError',original.__notes__)
        self.bootstrap.assert_called_once()
        self.closeout.collect.assert_called_once()

    def test_explicit_four_commands_do_not_override_unknown_driver_sql(self):
        self.fault.case='pre_migration';self.fault.fired={'unit':True}
        original=RuntimeError('unit original');self.bootstrap.side_effect=original
        self.numeric_closeout.side_effect=CandidateStop('unit driver contract not proven')
        with self.assertRaises(RuntimeError) as caught:self.run_body()
        self.assertIs(caught.exception,original)
        self.ledger.confirm.assert_not_called()
        self.assertEqual(self.ledger.unknown.call_count,2)
        self.assertTrue((self.gate.out/'case-bootstrap-termination.json').exists())


class BootstrapPrefixContractTests(unittest.TestCase):
    """Boundary validation models, not actual measured migration/CI evidence."""
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=pathlib.Path(temp.name)
        self.gate=types.SimpleNamespace(out=self.root)
        self.gate.save=lambda name,value:(self.root/name).write_text(json.dumps(value),encoding='ascii')
        self.binding=dict(run_id='ec75cc79-c246-4c83-8055-fbfc3d23738c',source_commit='a'*40,
                          ci_run='123',candidate_sha='b'*64)
        self.fault=types.SimpleNamespace(case='pre_migration',
            fired={'original_error_code':'case_injected_pre_migration'})
        path=self.root/e.BOOTSTRAP_NUMERIC_SOURCE;path.parent.mkdir(parents=True);path.write_bytes(b'# synthetic source')
        self.sources={e.BOOTSTRAP_NUMERIC_SOURCE:e.sha(path.read_bytes())}
        raw=b'{"unit_original":"not actual SQL"}'
        (self.root/'unit-prefix-original.json').write_bytes(raw)
        self.proof=dict(format='admission-bootstrap-fault-prefix-v1',
            status='BOOTSTRAP_FAULT_PREFIX_NUMERICALLY_VERIFIED',case_name=self.fault.case,
            run_id=self.binding['run_id'],source_commit=self.binding['source_commit'],
            ci_run=self.binding['ci_run'],candidate_sha256=self.binding['candidate_sha'],
            original_fault_code='case_injected_pre_migration',complete_numeric_prefix=True,
            observed_sql_commands=89,full_chain_admission=False,hosted_admitted=False,
            evidence_refs=[dict(path='unit-prefix-original.json',sha256=e.sha(raw),bytes=len(raw))])
        self.module=types.SimpleNamespace(__file__=str(path),
            validate_bootstrap_fault_prefix=mock.Mock(return_value=self.proof))
        patcher=mock.patch.object(e.importlib,'import_module',return_value=self.module)
        patcher.start();self.addCleanup(patcher.stop)

    def call(self):
        return e.bootstrap_fault_prefix(self.gate,self.binding,self.fault,self.root,self.sources)

    def test_validated_originals_are_retained_before_a_root_fault_can_be_called(self):
        value=self.call()
        self.module.validate_bootstrap_fault_prefix.assert_called_once_with(
            self.gate,binding=self.binding,case_name='pre_migration',fault=self.fault)
        self.assertEqual(json.loads((self.root/value['ref']['path']).read_bytes()),self.proof)

    def test_missing_real_validator_cannot_use_declared_total(self):
        del self.module.validate_bootstrap_fault_prefix
        with self.assertRaisesRegex(CandidateStop,'validator_missing'):self.call()

    def test_absence_or_partial_coverage_is_not_full_numeric_prefix(self):
        self.proof['complete_numeric_prefix']=False
        with self.assertRaisesRegex(CandidateStop,'prefix_binding'):self.call()

    def test_wrong_case_source_or_parent_run_rejects(self):
        for field in ('case_name','run_id','ci_run','source_commit','candidate_sha256'):
            with self.subTest(field=field):
                original=self.proof[field];self.proof[field]='wrong'
                with self.assertRaisesRegex(CandidateStop,'prefix_binding'):self.call()
                self.proof[field]=original

    def test_zero_boolean_or_negative_is_not_observed_prefix(self):
        for value in (0,True,-1,None):
            self.proof['observed_sql_commands']=value
            with self.assertRaisesRegex(CandidateStop,'prefix_numeric'):self.call()

    def test_missing_or_altered_original_cannot_be_covered_by_status(self):
        (self.root/'unit-prefix-original.json').write_bytes(b'altered')
        with self.assertRaisesRegex(CandidateStop,'reference_hash'):self.call()

    def test_empty_original_inventory_is_not_numeric_proof(self):
        self.proof['evidence_refs']=[]
        with self.assertRaisesRegex(CandidateStop,'prefix_originals'):self.call()

    def test_source_hash_change_rejects_before_validator(self):
        (self.root/e.BOOTSTRAP_NUMERIC_SOURCE).write_bytes(b'changed')
        with self.assertRaisesRegex(CandidateStop,'prefix_source'):self.call()
        self.module.validate_bootstrap_fault_prefix.assert_not_called()

    def test_replay_cannot_overwrite_retained_prefix_receipt(self):
        self.call()
        with self.assertRaisesRegex(CandidateStop,'receipt_exists'):self.call()

    def closeout(self):
        numeric={**self.proof,'format':'admission-bootstrap-closeout-numeric-v1',
            'status':'BOOTSTRAP_CLOSEOUT_NUMERICALLY_VERIFIED','complete_numeric_closeout':True,
            'observed_sql_commands':6,'explicit_sql_commands':4,'driver_sql_commands':2}
        self.module.validate_bootstrap_failure_closeout=mock.Mock(return_value=numeric)
        return numeric

    def call_closeout(self):
        return e.bootstrap_closeout_numeric(self.gate,self.binding,self.fault,
            {'unit':'isolation'},{'unit':'absence'},self.root,self.sources)

    def test_closeout_total_includes_proven_driver_commands(self):
        numeric=self.closeout()
        self.assertEqual(self.call_closeout()['proof']['observed_sql_commands'],6)
        self.assertEqual(numeric['explicit_sql_commands'],4)

    def test_missing_driver_field_never_defaults_to_zero(self):
        numeric=self.closeout();del numeric['driver_sql_commands']
        with self.assertRaisesRegex(CandidateStop,'closeout_numeric'):self.call_closeout()

    def test_closeout_partial_or_inconsistent_total_rejected(self):
        numeric=self.closeout();numeric['observed_sql_commands']=4
        with self.assertRaisesRegex(CandidateStop,'closeout_numeric'):self.call_closeout()
        numeric['observed_sql_commands']=6;numeric['complete_numeric_closeout']=False
        with self.assertRaisesRegex(CandidateStop,'closeout_binding'):self.call_closeout()


class BootstrapRootMechanicsTests(unittest.TestCase):
    """Actual A ledger mechanics on a UNIT graph, never runtime admission."""
    def setUp(self):
        import admission_budget_root_runtime as budget
        self.budget=budget
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        out=pathlib.Path(temp.name)
        self.gate=types.SimpleNamespace(out=out)
        self.gate.save=lambda name,value:(out/name).write_text(json.dumps(value),encoding='ascii')
        self.binding={'run_id':'ec75cc79-c246-4c83-8055-fbfc3d23738c'}
        self.fault=types.SimpleNamespace(case='pre_migration',
            fired={'original_error_code':'case_injected_pre_migration'})
        def row(name,units,reserve,*,next_ok=None,next_bad=None,safety=False):
            return dict(command_id=name,units=units,reserve_after=reserve,hosted_units=0,
                hosted_reserve_after=0,domain='unit_local_bootstrap',next_confirmed=next_ok,
                next_unknown=next_bad,safety_only=safety)
        program=dict(entry='case.bootstrap.clean47',events=[
            row('case.bootstrap.clean47',100,4,next_ok='unit.normal',next_bad='case.bootstrap.failure_closeout'),
            row('unit.normal',0,0),row('case.bootstrap.failure_closeout',4,0,safety=True)])
        self.ledger=budget._Ledger(budget._KEY,self.gate,program=program,
            binding=self.binding,register_sha256='a'*64)
        closeout=types.SimpleNamespace(COMMANDS=('unit',)*4,collect=lambda *args:{'unit':True})
        terminal=types.SimpleNamespace(validate_bootstrap_termination=lambda *args:{'unit':True})
        patcher=mock.patch.object(e,'dependency',side_effect=lambda root,sources,name:{
            'runtime_bootstrap_closeout':closeout,'runtime_terminal_bootstrap':terminal}[name])
        patcher.start();self.addCleanup(patcher.stop)
        self.original=RuntimeError('unit planned boundary')
        patcher=mock.patch.object(e,'bootstrap_closeout_numeric',return_value={
            'proof':{'observed_sql_commands':4},'ref':{'path':'unit-closeout.json'}})
        patcher.start();self.addCleanup(patcher.stop)

    def run_body(self,prefix):
        with mock.patch.object(e,'bootstrap_fault_prefix',**prefix):
            with self.assertRaises(RuntimeError) as caught:
                e.execute_bootstrap(self.gate,[],mock.Mock(side_effect=self.original),self.ledger,
                    self.binding,self.fault,'unused',{})
        self.assertIs(caught.exception,self.original)

    def test_actual_root_known_fault_retains_charge_stopped_and_separate_closeout(self):
        self.run_body({'return_value':{'proof':{'observed_sql_commands':89},
                                      'ref':{'path':'unit-prefix.json'}}})
        self.ledger.close()
        value=self.ledger.receipt()
        self.assertEqual(value['events'][0]['state'],'fault_numeric_confirmed')
        self.assertEqual(value['observed_sql_commands'],93)
        self.assertEqual(value['reserved_consumed'],104)
        self.assertTrue(value['stopped'])
        self.assertTrue(value['closed'])
        self.assertFalse(value['runtime_admitted'])
        self.assertFalse(value['full_chain_admission'])
        self.assertEqual([row['command_id'] for row in value['events']],
            ['case.bootstrap.clean47','case.bootstrap.failure_closeout'])
        self.ledger.validate_journal()

    def test_actual_root_unknown_stays_unknown_after_confirmed_absence(self):
        self.run_body({'side_effect':CandidateStop('unit missing canonical numeric prefix')})
        self.ledger.close()
        value=self.ledger.receipt()
        self.assertEqual(value['events'][0]['state'],'unknown_consumed')
        self.assertFalse(value['events'][0]['numeric_confirmed'])
        self.assertEqual(value['observed_sql_commands'],4)
        self.assertEqual(value['reserved_consumed'],104)
        self.assertTrue(value['stopped'])
        self.assertFalse(value['runtime_admitted'])
        self.ledger.validate_journal()

    def test_actual_root_fault_over_capacity_does_not_fall_back_to_zero_or_resume(self):
        self.run_body({'return_value':{'proof':{'observed_sql_commands':101},
                                      'ref':{'path':'unit-prefix.json'}}})
        value=self.ledger.receipt()
        self.assertEqual(value['observed_sql_commands'],0)
        self.assertTrue(value['pending'])
        self.assertEqual(value['events'][0]['state'],'precharged')
        self.assertEqual(len(value['events']),1)
        with self.assertRaises(self.budget.RootBlocked):self.ledger.close()


if __name__=='__main__':unittest.main()
