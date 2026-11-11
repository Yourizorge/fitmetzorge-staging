"""Synthetic runner regressions and real LOCAL process exits, not PG/Auth proof."""
import copy
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest import mock

from quota_candidate_v1 import runtime_worker_evidence as e
from quota_candidate_v1 import runtime_worker_runner as runner

BINDING={'run_id':'ec75cc79-c246-4c83-8055-fbfc3d23738c','parent_id':'11a909f4-7113-424a-aa4b-ce9964720a3e',
    'environment':'disposable_ci','hosted_permission':False,'execution_admitted':False,
    'source_commit':'a'*40,'candidate_sha':'b'*64,'ci_run':'123','cap':2349,
    'purpose':'6e11_disposable_quota_candidate_v1','expiry':'2026-11-11T23:59:00Z','binding_sha':'c'*64}


def result():
    order=[(r,o) for r in e.ROLES for o in e.OPERATIONS[:4]]+[(r,o) for r in e.ROLES for o in e.OPERATIONS[4:]]
    return {'status':'INTEGRAL_REAL_AUTH_WORKFLOW_CI_PASS','checks':18,'proof':[
        {'role':r,'operation':o,'result':{'http_status':200},
         'after':{'events':[],'pair_complete':True,'exact_contract':True}} for r,o in order],
        'workflow':{'status':'REAL_AUTH_THROUGH_71_WORKFLOW_PAIRS','pairs':71,'deletes':123,
            'outer_sql_commands_so_far':2000,'next_step':83,'hosted_admitted':False},
        'durable_steps':89,'closure':'confirmed','protocolCount':2300,
        'hosted_requests':0,'emails_sent':0,'environment':'disposable_ci'}


class Gate:
    def __init__(self,path):self.out=path;self.fail=None
    def save(self,name,value):
        if name==self.fail:raise OSError('synthetic_storage_failure')
        (self.out/name).write_bytes(e.canonical(value))


class FakeProcess:
    """Failure injection only. These records are NEVER actual worker evidence."""
    def __init__(self,message=None,code=0,wait_error=None,kill_error=None):
        self.pid=123;self.returncode=None;self.code=code;self.wait_error=wait_error;self.kill_error=kill_error
        self.stdin=io.StringIO();self.stdout=io.StringIO(message or '');self.stderr=io.StringIO()
        self.wait_calls=0;self.kill_calls=0
    def wait(self,timeout):
        self.wait_calls+=1
        if self.wait_error:
            error=self.wait_error;self.wait_error=None;raise error
        self.returncode=self.code;return self.code
    def poll(self):return self.returncode
    def kill(self):
        self.kill_calls+=1
        if self.kill_error:raise self.kill_error
        self.code=-9


class RunnerTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.gate=Gate(pathlib.Path(tmp.name));self.config={'mode':'registered_synthetic',
            'environment':'disposable_ci','identityBinding':{'preexisting':True},'admin':'DO_NOT_EXPORT','anon':'DO_NOT_EXPORT'}
        self.composition=types.SimpleNamespace(runner='unit-worker.mjs',commands=[],
            confirm_closure=mock.Mock(),abort=mock.Mock(),meter=types.SimpleNamespace(receipt=lambda:{'unit':True}))
        self.lifecycle=types.SimpleNamespace(own_worker=mock.Mock(),removed=True,failed=False,
            parent_auth_cleanup=mock.Mock(),close_temporary=mock.Mock(),dispatch=mock.Mock())
        patch=mock.patch.object(runner,'bind',return_value=(BINDING,
            {e.OWN+'runtime_worker_runner.py':e.sha(pathlib.Path(runner.__file__).read_bytes())},'normal'))
        patch.start();self.addCleanup(patch.stop)
        patch=mock.patch.object(runner.threading,'Timer');self.timer=patch.start().return_value
        self.timer.is_alive.return_value=False;self.addCleanup(patch.stop)

    def run_worker(self,process):
        actual=runner.save
        def save(gate,name,value):
            if name==gate.fail:raise OSError('synthetic_storage_failure')
            return actual(gate,name,value)
        with mock.patch.object(runner.subprocess,'Popen',return_value=process),mock.patch.object(runner,'save',side_effect=save):
            return runner.execute(self.gate,self.composition,self.lifecycle,self.config)

    def read(self,name):return json.loads((self.gate.out/name).read_bytes())
    def complete(self,**kwargs):return FakeProcess(json.dumps({'op':'complete','result':result()})+'\n',**kwargs)

    def test_complete_result_is_preserved_only_with_actual_wait_call(self):
        process=self.complete();actual=self.run_worker(process)
        self.assertEqual(actual,result());self.assertEqual(process.wait_calls,1)
        self.assertEqual(self.read('case-worker-result.json'),actual)
        e.validate_wait(self.read('registered-worker-wait.json'),BINDING,'normal',normal=True)
        self.assertTrue(self.read('registered-worker-terminal.json')['complete'])
        self.assertNotIn('DO_NOT_EXPORT',''.join(p.read_text() for p in self.gate.out.glob('*.json')))
        self.assertIsNone(self.config['admin'])

    def test_complete_then_nonzero_is_incomplete_and_abort(self):
        with self.assertRaisesRegex(RuntimeError,'registered_worker_incomplete'):
            self.run_worker(self.complete(code=2))
        self.assertFalse(self.read('registered-worker-terminal.json')['complete'])
        self.assertEqual(self.read('registered-worker-wait.json')['returncode'],2)
        self.composition.confirm_closure.assert_not_called();self.composition.abort.assert_called()

    def test_complete_then_wait_timeout_never_becomes_pass_after_reap(self):
        error=subprocess.TimeoutExpired('unit',5);process=self.complete(wait_error=error)
        with self.assertRaises(subprocess.TimeoutExpired) as caught:self.run_worker(process)
        self.assertIs(caught.exception,error)
        wait=self.read('registered-worker-wait.json')
        self.assertTrue(wait['reaped']);self.assertEqual(wait['wait_error_class'],'TimeoutExpired')
        self.assertFalse(self.read('registered-worker-terminal.json')['complete'])
        with self.assertRaisesRegex(ValueError,'worker_wait_unconfirmed'):
            e.validate_wait(wait,BINDING,'normal',normal=True)
        self.composition.confirm_closure.assert_not_called()

    def test_exit_zero_without_complete_does_not_invent_result(self):
        with self.assertRaisesRegex(RuntimeError,'registered_worker_incomplete'):self.run_worker(FakeProcess())
        self.assertFalse((self.gate.out/'case-worker-result.json').exists())
        self.assertIsNone(self.read('registered-worker-observation.json')['result_ref'])
        self.assertFalse(self.read('registered-worker-terminal.json')['complete'])

    def test_terminate_error_preserves_original_failure_and_no_reap_claim(self):
        process=FakeProcess('{"op":"failed"}\n',kill_error=OSError('unit terminate'))
        with self.assertRaisesRegex(RuntimeError,'registered_worker_failed'):self.run_worker(process)
        wait=self.read('registered-worker-wait.json')
        self.assertFalse(wait['reaped']);self.assertEqual(wait['termination_error_class'],'OSError')
        self.lifecycle.parent_auth_cleanup.assert_called_once_with(worker_terminated=False)
        self.assertFalse(self.read('registered-worker-terminal.json')['complete'])

    def test_reap_error_preserves_original_failure(self):
        process=FakeProcess('{"op":"failed"}\n',wait_error=OSError('unit reap'))
        with self.assertRaisesRegex(RuntimeError,'registered_worker_failed'):self.run_worker(process)
        wait=self.read('registered-worker-wait.json')
        self.assertFalse(wait['wait_completed']);self.assertEqual(wait['wait_error_class'],'OSError')
        self.assertFalse(self.read('registered-worker-terminal.json')['complete'])

    def test_wait_save_failure_denies_complete_and_runs_cleanup(self):
        self.gate.fail='registered-worker-wait.json'
        with self.assertRaisesRegex(RuntimeError,'registered_worker_cleanup_incomplete'):
            self.run_worker(self.complete())
        self.lifecycle.parent_auth_cleanup.assert_called_once_with(worker_terminated=True)
        self.assertFalse(self.read('registered-worker-terminal.json')['complete'])

    def test_result_save_failure_is_original_and_no_closure(self):
        self.gate.fail='case-worker-result.json'
        with self.assertRaises(OSError):self.run_worker(self.complete())
        self.composition.confirm_closure.assert_not_called()
        self.assertFalse(self.read('registered-worker-terminal.json')['complete'])

    def test_original_not_replaced_by_abort_failure(self):
        self.composition.abort.side_effect=OSError('unit abort')
        with self.assertRaisesRegex(RuntimeError,'registered_worker_failed') as caught:
            self.run_worker(FakeProcess('{"op":"failed"}\n'))
        self.assertIn('worker_secondary:abort:OSError',caught.exception.__notes__)

    def test_invalid_secret_bearing_result_is_not_saved(self):
        value=result();value['proof'][0]['result']['access_token']='DO_NOT_EXPORT'
        with self.assertRaisesRegex(ValueError,'worker_metadata_fields'):
            self.run_worker(FakeProcess(json.dumps({'op':'complete','result':value})+'\n'))
        self.assertFalse((self.gate.out/'case-worker-result.json').exists())
        self.assertNotIn('DO_NOT_EXPORT',''.join(p.read_text() for p in self.gate.out.glob('*.json')))

    def test_complete_with_unknown_watchdog_closure_is_not_pass(self):
        self.timer.is_alive.return_value=True
        with self.assertRaisesRegex(RuntimeError,'registered_worker_incomplete'):self.run_worker(self.complete())
        self.assertFalse(self.read('registered-worker-terminal.json')['complete'])
        self.assertEqual(self.read('registered-worker-wait.json')['watchdog_error_class'],'WatchdogStillAlive')
        self.composition.confirm_closure.assert_not_called()

    def test_join_failure_preserves_original_error(self):
        self.timer.join.side_effect=OSError('unit join')
        with self.assertRaisesRegex(RuntimeError,'registered_worker_failed'):
            self.run_worker(FakeProcess('{"op":"failed"}\n'))
        self.assertFalse(self.read('registered-worker-wait.json')['watchdog_stopped'])
        self.assertFalse(self.read('registered-worker-terminal.json')['complete'])

    def test_stop_receipt_failure_cannot_replace_dispatch_primary(self):
        original=ValueError('unit dispatch');self.lifecycle.dispatch.side_effect=original
        self.gate.fail='registered-worker-stop-001.json'
        child=FakeProcess('{"op":"query"}\n{"op":"failed"}\n')
        with self.assertRaises(ValueError) as caught:self.run_worker(child)
        self.assertIs(caught.exception,original)
        self.assertIn('worker_secondary:stop_receipt:OSError',original.__notes__)
        terminal=self.read('registered-worker-terminal.json')
        self.assertFalse(terminal['complete'])
        self.assertIn({'stage':'stop_receipt','exception_class':'OSError'},terminal['cleanup_errors'])
        self.lifecycle.parent_auth_cleanup.assert_called_once_with(worker_terminated=True)

    def test_unknown_child_operation_is_denied_before_dispatch_or_export(self):
        canary='PRIVATE_REVIEW_SENTINEL'
        self.lifecycle.dispatch.side_effect=ValueError('unit dispatch')
        with self.assertRaisesRegex(ValueError,'registered_operation_denied'):
            self.run_worker(FakeProcess(json.dumps({'op':canary})+'\n'))
        self.lifecycle.dispatch.assert_not_called()
        self.assertNotIn(canary,''.join(p.read_text() for p in self.gate.out.glob('*.json')))
        self.assertFalse((self.gate.out/'registered-worker-stop-001.json').exists())

    def test_complete_after_dispatch_error_cannot_promote_case(self):
        original=ValueError('unit dispatch');self.lifecycle.dispatch.side_effect=original
        child=FakeProcess('{"op":"query"}\n'+json.dumps({'op':'complete','result':result()})+'\n')
        with self.assertRaises(ValueError) as caught:self.run_worker(child)
        self.assertIs(caught.exception,original);self.composition.confirm_closure.assert_not_called()
        self.assertFalse(self.read('registered-worker-terminal.json')['complete'])

    def test_auth_operation_not_allowed_into_composition_action(self):
        with self.assertRaisesRegex(ValueError,'registered_auth_operation_denied'):
            self.run_worker(FakeProcess('{"op":"before","role":"a_member","operation":"PRIVATE_REVIEW_SENTINEL"}\n'))
        self.lifecycle.dispatch.assert_not_called()
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL',''.join(p.read_text() for p in self.gate.out.glob('*.json')))

    def test_sqlstate_metadata_does_not_export_arbitrary_exception_attribute(self):
        original=ValueError('unit dispatch');original.sqlstate='PRIVATE_REVIEW_SENTINEL'
        self.lifecycle.dispatch.side_effect=original
        with self.assertRaises(ValueError):self.run_worker(FakeProcess('{"op":"query"}\n{"op":"failed"}\n'))
        self.assertIsNone(self.read('registered-worker-stop-001.json')['sqlstate'])
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL',''.join(p.read_text() for p in self.gate.out.glob('*.json')))


class MetadataTests(unittest.TestCase):
    def test_sql_text_and_credential_patterns_rejected(self):
        for text in ('select * from auth.users','Bearer secret','sb_secret_x','eyJpayload'):
            value=result();value['proof'][0]['result']['status']=text
            with self.subTest(text=text),self.assertRaises(ValueError):e.validate_result(value,'registered')

    def test_bool_count_denied(self):
        value=result();value['checks']=True
        with self.assertRaises(ValueError):e.validate_result(value,'registered')

    def test_inner_current_shape_and_metadata_proofs(self):
        value={'status':'LOCAL_COMPOSED_71_PASS','pairs':71,'writes':200,'deletes':123,
            'proofs':[{'pair_complete':True,'protected_equal':True,'count':1,'changes':[]}],
            'next_step':83,'hosted_admitted':False,'missing':['fixture_lifecycle_evidence','full_protocol_register'],
            'real_local_auth':True,'commandCount':100,'worker_cpu_ms':0.5,'worker_wall_ms':1.5,
            'worker_cpu_limit_ms':2000,'worker_wall_limit_ms':120000}
        self.assertIs(e.validate_result(value,'workflow'),value)

    def test_watchdog_failure_latched_even_if_wait_later_returns_zero(self):
        observed=e.WaitEvidence(BINDING,'normal','registered');observed.attach(FakeProcess(kill_error=OSError('unit')))
        observed.kill(watchdog=True);observed.wait();observed.close()
        self.assertFalse(observed.known)
        with self.assertRaises(ValueError):e.validate_wait(observed.receipt(),BINDING,'normal',normal=True)


class ExportTests(unittest.TestCase):
    """Synthetic original files test rejection; never actual CI evidence."""
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.gate=Gate(pathlib.Path(tmp.name));self.hashes={'unit_source':'a'*64}
        self.composition=types.SimpleNamespace(quota={'manifest':{'sources':self.hashes}})
        patch=mock.patch.object(e,'bind',return_value=(BINDING,self.hashes,'normal'))
        patch.start();self.addCleanup(patch.stop)
        for name in ('registered-worker-terminal.json','case-registered-finally.json',
                'runtime-command-meter.json','case-runtime-terminal.json','integral-complete-protocol-trace.json',
                'workflow-auth-protocol.json','integral-preflight.json','integral-closure.json'):
            self.gate.save(name,{'synthetic_unit_only':True})
        for name in ['auth-protocol-%02d.json'%i for i in range(18)]+['cli-protocol-%d.json'%i for i in range(3)]:
            self.gate.save(name,{'synthetic_unit_only':True})
        for kind in ('registered','workflow'):
            observed=e.WaitEvidence(BINDING,'normal',kind);observed.attach(FakeProcess())
            observed.wait();observed.close()
            self.gate.save(kind+'-worker-wait.json',observed.receipt())
        self.gate.save('case-workflow-worker-result.json',{'status':'LOCAL_COMPOSED_71_PASS',
            'real_local_auth':True,'pairs':71,'deletes':123,'next_step':83,'hosted_admitted':False})
        self.gate.save('case-worker-result.json',result())
        self.observation={'binding':BINDING,'case_name':'normal','source_hashes':self.hashes,
            'wait_ref':self.ref('registered-worker-wait.json'),
            'result_ref':self.ref('case-worker-result.json'),'complete_received':True}
        self.gate.save('registered-worker-observation.json',self.observation)

    def ref(self,name):
        raw=(self.gate.out/name).read_bytes()
        return {'path':name,'sha256':e.sha(raw),'bytes':len(raw)}

    def call(self):return e.export(self.gate,self.composition,'normal',result())

    def test_export_retains_both_original_waits_results_and_observation(self):
        reference,refs=self.call()
        record=json.loads((self.gate.out/reference['path']).read_bytes())
        names={r['path'] for r in refs}
        self.assertTrue({'case-worker-result.json','registered-worker-wait.json',
            'case-workflow-worker-result.json','workflow-worker-wait.json',
            'registered-worker-observation.json'}<=names)
        self.assertEqual(reference,self.ref('case-worker-export.json'))
        for item in refs:self.assertEqual(item,self.ref(item['path']))
        self.assertFalse(record['full_chain_admission']);self.assertFalse(record['hosted_admitted'])
        self.assertNotIn('status',record)

    def test_lost_result_never_exports_partial_success(self):
        (self.gate.out/'case-worker-result.json').unlink()
        with self.assertRaises(FileNotFoundError):self.call()
        self.assertFalse((self.gate.out/'case-worker-export.json').exists())

    def test_changed_result_ref_rejected(self):
        self.observation['result_ref']['sha256']='0'*64
        self.gate.save('registered-worker-observation.json',self.observation)
        with self.assertRaisesRegex(ValueError,'worker_export_result_original'):self.call()

    def test_missing_inner_result_rejected(self):
        (self.gate.out/'case-workflow-worker-result.json').unlink()
        with self.assertRaisesRegex(ValueError,'workflow_export_result_lost'):self.call()

    def test_inner_partial_no_go_with_completed_counts_is_not_promoted(self):
        name='case-workflow-worker-result.json';value=json.loads((self.gate.out/name).read_bytes())
        value['status']='NO_GO';self.gate.save(name,value)
        with self.assertRaisesRegex(ValueError,'workflow_export_incomplete_result'):self.call()

    def test_incomplete_wait_any_worker_denies_export(self):
        for name in ('registered-worker-wait.json','workflow-worker-wait.json'):
            original=json.loads((self.gate.out/name).read_bytes())
            for field,value in (('wait_error_class','TimeoutExpired'),('termination_error_class','OSError'),
                    ('reaped',False),('wait_completed',False),('watchdog_fired',True),('returncode',7)):
                changed={**original,field:value};self.gate.save(name,changed)
                with self.subTest(name=name,field=field),self.assertRaisesRegex(ValueError,'worker_wait_unconfirmed'):
                    self.call()
                self.assertFalse((self.gate.out/'case-worker-export.json').exists())
            self.gate.save(name,original)

    def test_claimed_exit_without_actual_wait_events_rejected(self):
        name='registered-worker-wait.json';record=json.loads((self.gate.out/name).read_bytes())
        record['events']=[];self.gate.save(name,record)
        with self.assertRaisesRegex(ValueError,'worker_wait_events'):self.call()

    def test_missing_complete_is_not_promoted(self):
        self.observation['complete_received']=False
        self.gate.save('registered-worker-observation.json',self.observation)
        with self.assertRaisesRegex(ValueError,'worker_export_result_lost'):self.call()

    def test_export_write_failure_is_not_success(self):
        with mock.patch.object(e.os,'fsync',side_effect=OSError('unit fsync')):
            with self.assertRaises(OSError):self.call()

    def collector(self):
        # Stub only A1's independent meter proof to isolate the new wait checks.
        # These unit records never prove a real worker or full-chain component.
        from quota_candidate_v1 import runtime_exported_terminal as terminal
        from quota_candidate_v1 import exported_worker as verifier
        raw={p.name:p.read_bytes() for p in self.gate.out.glob('*.json')}
        evidence=terminal.Originals(raw,[self.ref(name) for name in raw])
        trusted=types.SimpleNamespace(sources=self.hashes,root=self.gate.out,
            module=lambda name:e if name.endswith('runtime_worker_evidence') else verifier)
        with mock.patch.object(verifier,'verify_exported_worker',return_value=
                verifier.WorkerVerification('VERIFIED_COMPONENT','normal')):
            return terminal.worker(evidence,trusted,{'case_name':'normal'},BINDING)

    def test_collector_rechecks_inner_timeout_even_with_verified_outer_component(self):
        self.call()
        name='workflow-worker-wait.json';value=json.loads((self.gate.out/name).read_bytes())
        value['wait_error_class']='TimeoutExpired';self.gate.save(name,value)
        export=json.loads((self.gate.out/'case-worker-export.json').read_bytes())
        export['workflow_wait_ref']=self.ref(name);self.gate.save('case-worker-export.json',export)
        with self.assertRaisesRegex(ValueError,'worker_wait_unconfirmed'):self.collector()

    def test_collector_rejects_missing_inner_original(self):
        self.call();(self.gate.out/'case-workflow-worker-result.json').unlink()
        with self.assertRaisesRegex(ValueError,'case-workflow-worker-result.json'):self.collector()

    def test_collector_rejects_partial_result_even_with_updated_hash(self):
        self.call();name='case-workflow-worker-result.json'
        value=json.loads((self.gate.out/name).read_bytes());value['status']='NO_GO';self.gate.save(name,value)
        export=json.loads((self.gate.out/'case-worker-export.json').read_bytes())
        export['workflow_worker_result_ref']=self.ref(name);self.gate.save('case-worker-export.json',export)
        with self.assertRaisesRegex(ValueError,'worker_inner_result_incomplete'):self.collector()


class DurableSaveTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.gate=types.SimpleNamespace(out=pathlib.Path(tmp.name),save=mock.Mock(side_effect=AssertionError('Gate.save forbidden')))

    def test_exclusive_fsync_same_file_readback_without_gate_save(self):
        with mock.patch.object(e.os,'fsync',wraps=e.os.fsync) as sync:
            ref=e.save(self.gate,'unit-original.json',{'unit':True})
        sync.assert_called_once();self.gate.save.assert_not_called()
        raw=(self.gate.out/ref['path']).read_bytes()
        self.assertEqual(ref,{'path':'unit-original.json','bytes':len(raw),'sha256':e.sha(raw)})

    def test_existing_original_never_overwritten(self):
        ref=e.save(self.gate,'unit-original.json',{'unit':True})
        with self.assertRaisesRegex(ValueError,'worker_evidence_fresh_path'):
            e.save(self.gate,'unit-original.json',{'unit':False})
        self.assertEqual(e.sha((self.gate.out/ref['path']).read_bytes()),ref['sha256'])

    def test_fsync_failure_retains_file_but_returns_no_reference_or_retry(self):
        with mock.patch.object(e.os,'fsync',side_effect=OSError('unit sync')):
            with self.assertRaises(OSError):e.save(self.gate,'unit-original.json',{'unit':True})
        self.assertTrue((self.gate.out/'unit-original.json').exists())
        with self.assertRaises(ValueError):e.save(self.gate,'unit-original.json',{'unit':True})

    def test_corrupt_same_descriptor_readback_rejected(self):
        sync=e.os.fsync
        def corrupt(fd):
            e.os.lseek(fd,0,0);e.os.write(fd,b'X');sync(fd)
        with mock.patch.object(e.os,'fsync',side_effect=corrupt):
            with self.assertRaisesRegex(ValueError,'worker_evidence_readback'):
                e.save(self.gate,'unit-original.json',{'unit':True})

    def test_bound_and_path_rejected_before_creation(self):
        with self.assertRaisesRegex(ValueError,'worker_evidence_size'):
            e.save(self.gate,'unit-original.json',{'unit':'x'*2_000_000})
        with self.assertRaisesRegex(ValueError,'worker_evidence_fresh_path'):
            e.save(self.gate,'../escape.json',{})
        self.assertEqual(list(self.gate.out.iterdir()),[])

    def test_named_path_must_still_identify_same_open_file(self):
        with mock.patch.object(e.os,'fstat',return_value=types.SimpleNamespace(st_dev=-1,st_ino=-1,st_size=13)):
            with self.assertRaisesRegex(ValueError,'worker_evidence_file_identity'):
                e.save(self.gate,'unit-original.json',{'unit':True})


class WatchdogRaceTests(unittest.TestCase):
    """Real timer threads, synthetic process. No worker/PG/Auth proof."""
    def test_active_callback_cannot_be_canceled_into_known_exit(self):
        started=threading.Event();release=threading.Event()
        observed=e.WaitEvidence(BINDING,'normal','registered');observed.attach(FakeProcess());observed.wait()
        def callback():
            started.set();release.wait(5);observed.kill(watchdog=True)
        timer=threading.Timer(0,callback)
        def close():release.set();timer.join(timeout=5)
        self.addCleanup(close)
        observed.start_timer(timer,deadline=time.monotonic())
        self.assertTrue(started.wait(1))
        observed.stop_timer(timer)
        saved=observed.receipt()
        self.assertFalse(saved['watchdog_stopped']);self.assertFalse(observed.known)
        release.set();timer.join(timeout=5);self.assertFalse(timer.is_alive())
        self.assertFalse(saved['watchdog_stopped'])
        with self.assertRaises(ValueError):e.validate_wait(saved,BINDING,'normal',normal=True)
        observed.stop_timer(timer)
        self.assertFalse(observed.known)

    def test_cancel_and_join_stops_real_timer_before_snapshot(self):
        observed=e.WaitEvidence(BINDING,'normal','registered');observed.attach(FakeProcess());observed.wait()
        timer=threading.Timer(180,lambda:observed.kill(watchdog=True))
        self.addCleanup(lambda:(timer.cancel(),timer.join(timeout=5)))
        observed.start_timer(timer,deadline=time.monotonic()+180);observed.stop_timer(timer)
        self.assertFalse(timer.is_alive());self.assertTrue(observed.known)
        e.validate_wait(observed.receipt(),BINDING,'normal',normal=True)

    def test_join_cannot_grant_time_after_existing_deadline(self):
        observed=e.WaitEvidence(BINDING,'normal','registered');timer=mock.Mock()
        timer.is_alive.return_value=False
        observed.start_timer(timer,deadline=10)
        with mock.patch.object(e.time,'monotonic',return_value=20):observed.stop_timer(timer)
        timer.join.assert_called_once_with(timeout=0)
        self.assertEqual(observed.watchdog_error,'WatchdogDeadlineElapsed')


class SourceBindingTests(unittest.TestCase):
    def test_source_drift_rejected_before_worker_ownership_or_spawn(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        root=pathlib.Path(tmp.name);sources={}
        import registered_runner
        for name in e.SOURCES:
            source=pathlib.Path(registered_runner.__file__) if name==e.BASELINE else pathlib.Path(e.__file__).parent/pathlib.PurePosixPath(name).name
            raw=source.read_bytes();target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw);sources[name]=e.sha(raw)
        composition=types.SimpleNamespace(quota={'root':root,'binding':BINDING,'manifest':{'sources':sources}},
            phase_faults=types.SimpleNamespace(case='normal'))
        self.assertEqual(e.bind(composition)[0],BINDING)
        (root/e.BASELINE).write_bytes(b'drift')
        lifecycle=mock.Mock()
        with mock.patch.object(runner.subprocess,'Popen') as popen:
            with self.assertRaisesRegex(ValueError,'worker_evidence_source'):
                runner.execute(mock.Mock(),composition,lifecycle,{'mode':'registered_synthetic',
                    'environment':'disposable_ci','identityBinding':{'preexisting':True}})
        popen.assert_not_called();lifecycle.own_worker.assert_not_called()


class ActualLocalProcessTests(unittest.TestCase):
    """Real OS wait/kill calls; tiny synthetic Python workers, no Node/Auth/PG claim."""
    def spawn(self,code):
        process=subprocess.Popen([sys.executable,'-c',code],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        def close():
            if process.poll() is None:process.kill()
            process.wait(timeout=5)
            for stream in (process.stdin,process.stdout,process.stderr):stream.close()
        self.addCleanup(close)
        return process

    def test_actual_zero_exit(self):
        observed=e.WaitEvidence(BINDING,'normal','registered');observed.attach(self.spawn('pass'))
        self.assertEqual(observed.wait(),0);observed.close()
        e.validate_wait(observed.receipt(),BINDING,'normal',normal=True)

    def test_actual_nonzero_exit_is_not_normal_success(self):
        observed=e.WaitEvidence(BINDING,'normal','registered');observed.attach(self.spawn('raise SystemExit(7)'))
        self.assertEqual(observed.wait(),7);observed.close()
        with self.assertRaises(ValueError):e.validate_wait(observed.receipt(),BINDING,'normal',normal=True)

    def test_actual_timeout_and_kill_reap_keeps_timeout(self):
        observed=e.WaitEvidence(BINDING,'timeout','registered');observed.attach(self.spawn('import time;time.sleep(30)'))
        with self.assertRaises(subprocess.TimeoutExpired):observed.wait()
        observed.close()
        self.assertTrue(observed.reaped);self.assertEqual(observed.wait_error,'TimeoutExpired')
        with self.assertRaises(ValueError):e.validate_wait(observed.receipt(),BINDING,'timeout',normal=False)

    def test_actual_cleanup_kill_and_wait_records_both(self):
        observed=e.WaitEvidence(BINDING,'controller','registered');observed.attach(self.spawn('import time;time.sleep(30)'))
        observed.close();self.assertTrue(observed.reaped)
        self.assertEqual([r['operation'] for r in observed.events],['kill','wait','wait_return'])
        e.validate_wait(observed.receipt(),BINDING,'controller',normal=False)


if __name__=='__main__':unittest.main()
