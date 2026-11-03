"""Selector/validator unit regressions only; no real PG/GoTrue execution or PASS.

Fabricated adversarial report fixtures exercise rejection and incompleteness.
They are never written as CI evidence and never count as scenario coverage.
"""
import copy
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import time
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import integral_failures as f
import integral_failure_runtime as rt
import integral_failure_runtime_workflow as workflow


class FailureSelectionTests(unittest.TestCase):
    def candidate(self):
        return {'sha256':'a'*64,'sources':{n:hashlib.sha256((f.ROOT/n).read_bytes()).hexdigest()
                                         for n in f.SOURCE_FILES}}

    def plan(self,**changes):
        values={'root':f.ROOT,'candidate':self.candidate(),
            'context':{'repository':'Yourizorge/fitmetzorge-staging','ref':'refs/heads/main',
                       'commit':'b'*40,'ci_run':'1','environment':'disposable_ci'},
            'inventory':{'files':0,'bytes':0,'largest_file_bytes':0},
            'reserve':{'files_per_case':100,'bytes_per_case':1000000},
            'selection':list(f.LEGACY),'diagnostic_only':True}
        values.update(changes)
        return f.preflight(**values)

    def fake_reports(self,plan):
        """Untrusted JSON fixtures, not execution receipts."""
        cases={r['id']:r for r in plan['register']}
        return [{'case':case,'evidence_kind':'REAL_DISPOSABLE_PG17_GOTRUE',
            'plan_sha256':plan['plan_sha256'],
            'source_binding_sha256':plan['source_binding']['sha256'],
            'observed_hook':cases[case]['hook'],'fault_injected':True,
            'primary_failure':'registered_worker_failed',
            'protocol_artifact':'fault-'+case+'-integral-protocol-trace.json',
            'expected':f.expected_state(case),'actual':f.expected_state(case),
            'hosted_calls':0,'diagnostic_sql_commands':1,'mutation_retried':False,
            'incomplete_pair_preserved':True,'normal_receipt_reused_as_pass':False,
            'three_auth_zero_confirmed':True,'protocol_sha256':'c'*64,
            'runtime_meter':{'stopped':True,'used':100,'limit':2349,'state':{'auth_maybe_live':False}},
            'safety_auth':{'status':'NO_GO','revocation_confirmed':True,'global_zero_claim':False}}
            for case in plan['selection']]

    def test_register_has_fourteen_faults_normal_reference_and_three_legacy_cases(self):
        rows=f.scenario_register()
        self.assertEqual(len(f.REQUIRED),14)
        self.assertEqual(len(rows),18)
        self.assertEqual({r['id'] for r in rows if r['implemented']},set(f.LEGACY))
        for row in rows:
            self.assertIn(row['source'],f.SOURCE_FILES)
            if row['id'] in f.LEGACY:
                self.assertEqual(row['step'],0)
                self.assertEqual(row['required_categories'],[])
            else:
                self.assertTrue(row['missing_hook'])
                self.assertTrue(row['missing_evidence'])
                self.assertTrue(row['owner'])

    def test_normal_requires_existing_evidence_not_new_stack(self):
        normal=next(r for r in f.scenario_register() if r['id']=='normal')
        self.assertIn('no additional replay',normal['missing_hook'])
        self.assertFalse(normal['implemented'])

    def test_default_full_selection_is_blocked(self):
        plan=self.plan(selection=None,diagnostic_only=False)
        self.assertFalse(plan['ready_for_execution'])
        self.assertEqual(plan['selection'],list(f.REQUIRED))
        self.assertEqual(len(plan['missing_hooks']),15)
        self.assertIn('selected_cases_exceed_existing_three_case_bound',plan['blockers'])
        for case in f.REQUIRED:
            self.assertIn('required_hook_not_implemented:'+case,plan['blockers'])

    def test_old_three_cannot_be_full_selection(self):
        plan=self.plan(diagnostic_only=False)
        self.assertFalse(plan['ready_for_execution'])
        self.assertIn('required_scenario_not_selected:pre_migration',plan['blockers'])
        self.assertIn('required_hook_not_implemented:mid_auth',plan['blockers'])

    def test_explicit_diagnostic_selection_only_admits_execution(self):
        plan=self.plan()
        self.assertTrue(plan['ready_for_execution'])
        self.assertEqual(plan['mode'],'diagnostic_only')
        self.assertFalse(plan['full_coverage_possible'])
        self.assertFalse(plan['hosted_admission'])
        self.assertEqual(plan['additional_hosted_commands'],0)

    def test_unknown_duplicate_empty_and_nonstring_selection_fail(self):
        for selection in ([],['unknown'],['before_call','before_call'],[True]):
            with self.subTest(selection=selection),self.assertRaises(ValueError):
                self.plan(selection=selection)
        with self.assertRaises(ValueError):
            self.plan(diagnostic_only=1)

    def test_unsupported_single_case_cannot_dispatch(self):
        plan=self.plan(selection=['mid_restore'])
        self.assertFalse(plan['ready_for_execution'])
        self.assertIn('missing_hook:mid_restore',plan['blockers'])

    def test_case_bound_cannot_be_increased_by_selection(self):
        plan=self.plan(selection=[*f.LEGACY,'timeout'])
        self.assertFalse(plan['ready_for_execution'])
        self.assertIn('selected_cases_exceed_existing_three_case_bound',plan['blockers'])
        self.assertEqual(plan['bounds']['cases'],3)

    def test_bounds_are_existing_limits_not_new_allowances(self):
        self.assertEqual(f.BOUNDS,{'cases':3,'registered_commands_per_case':2349,
            'diagnostic_selects_per_case':1,'worker_seconds':180,'worker_messages':200,
            'workflow_seconds':125,'sql_seconds':5,'lock_seconds':1,
            'files':2200,'bytes':80000000,'file_bytes':2000000})
        with patch.object(f,'allowance',return_value=2350),self.assertRaises(ValueError):
            self.plan()

    def test_missing_artifact_reservation_blocks_before_execution(self):
        plan=self.plan(reserve=None)
        self.assertFalse(plan['ready_for_execution'])
        self.assertIn('ci_failure_artifact_reservation_required',plan['blockers'])

    def test_reservation_invalid_numbers_and_overflow_block(self):
        for reserve in ({'files_per_case':True,'bytes_per_case':1},
                        {'files_per_case':0,'bytes_per_case':1},
                        {'files_per_case':1000,'bytes_per_case':1000000},
                        {'files_per_case':100,'bytes_per_case':30000000}):
            with self.subTest(reserve=reserve):
                self.assertFalse(self.plan(reserve=reserve)['ready_for_execution'])
        plan=self.plan(inventory={'files':1,'bytes':2000001,'largest_file_bytes':2000001})
        self.assertFalse(plan['ready_for_execution'])

    def test_artifact_projection_is_explicit_not_measurement(self):
        plan=self.plan()
        self.assertEqual(plan['artifacts']['projected_files'],303)
        self.assertEqual(plan['artifacts']['projected_bytes'],9000000)
        self.assertTrue(plan['artifacts']['projection_not_measurement'])
        self.assertTrue(plan['artifacts']['collector_limits_unchanged'])

    def test_actual_artifact_reservation_overrun_is_rejected(self):
        before={'files':10,'bytes':100,'largest_file_bytes':100}
        reserve={'files_per_case':2,'bytes_per_case':500}
        for after in ({'files':13,'bytes':200,'largest_file_bytes':100},
                      {'files':11,'bytes':601,'largest_file_bytes':100},
                      {'files':11,'bytes':2000001,'largest_file_bytes':2000001}):
            with self.subTest(after=after),self.assertRaises(RuntimeError):
                f.check_artifact_usage(before,after,reserve)

    def test_source_binding_pins_exact_local_bytes_and_context(self):
        plan=self.plan()
        binding=plan['source_binding']
        self.assertEqual(set(binding['source_hashes']),set(f.SOURCE_FILES))
        self.assertIn(f.PREFIX+'test_integral_failures.py',binding['source_hashes'])
        f.recheck_sources(plan,f.ROOT)

    def test_missing_or_changed_source_fails(self):
        for value in (None,'0'*64):
            candidate=self.candidate()
            if value is None:del candidate['sources'][f.SOURCE_FILES[0]]
            else:candidate['sources'][f.SOURCE_FILES[0]]=value
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.plan(candidate=candidate)

    def test_nonci_remote_and_wrong_source_context_fail(self):
        good=self.plan()['source_binding']['context']
        for field,value in (('repository','other/repository'),('ref','refs/heads/other'),
                            ('environment','staging'),('commit','bad'),('ci_run','0')):
            with self.subTest(field=field),self.assertRaises(ValueError):
                self.plan(context={**good,field:value})

    def test_preflight_does_not_run_process_network_or_write(self):
        with patch('subprocess.Popen',side_effect=AssertionError('process')), \
                patch('subprocess.run',side_effect=AssertionError('process')), \
                patch('socket.socket',side_effect=AssertionError('network')), \
                patch.object(pathlib.Path,'write_text',side_effect=AssertionError('write')), \
                patch.object(pathlib.Path,'write_bytes',side_effect=AssertionError('write')):
            self.assertTrue(self.plan()['ready_for_execution'])

    def test_historical_replays_never_import_or_call_actual_backend(self):
        with patch.dict(sys.modules,{'metered_composition':None}):
            for method in (f.already_present, f._historical_run_disabled,
                           f._historical_already_present_disabled):
                with self.subTest(method=method), self.assertRaises(f.FailureCoverageBlocked):
                    method(SimpleNamespace())

    def test_run_rejects_local_or_hosted_without_reading_candidate(self):
        with patch.dict(f.os.environ,{},clear=True),self.assertRaisesRegex(RuntimeError,'ci_only'):
            f.run(SimpleNamespace())

    def test_existing_evidence_blocks_before_read_or_write(self):
        environment={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging',
                     'GITHUB_REF':'refs/heads/main'}
        gate=SimpleNamespace(out=pathlib.Path('unit-only-not-used'))
        with patch.dict(f.os.environ,environment,clear=True), \
                patch.object(pathlib.Path,'exists',return_value=True), \
                patch.object(pathlib.Path,'read_text',side_effect=AssertionError('read')), \
                self.assertRaisesRegex(RuntimeError,'existing_evidence_preserved'):
            f.run(gate)

    def test_three_fabricated_records_never_claim_full_or_real_pass(self):
        plan=self.plan()
        result=f.coverage(plan,self.fake_reports(plan))
        self.assertEqual(result['status'],'NO_GO_FAILURE_COVERAGE')
        self.assertFalse(result['complete'])
        self.assertFalse(result['hosted_admission'])
        self.assertEqual(result['missing_required'],sorted(f.REQUIRED))
        self.assertEqual(result['covered'],[])
        self.assertTrue(result['independent_artifact_review_required'])
        self.assertTrue(result['unit_tests_are_not_real_ci'])
        with self.assertRaises(f.FailureCoverageBlocked):
            f.require_full_coverage(plan,self.fake_reports(plan))

    def test_missing_duplicate_and_relabelled_records_are_rejected(self):
        plan=self.plan()
        reports=self.fake_reports(plan)
        self.assertTrue(f.coverage(plan,reports[:-1])['missing_selected'])
        self.assertTrue(f.coverage(plan,reports+[reports[0]])['invalid_reports'])
        reports[0]['case']='mid_route_a'
        self.assertTrue(f.coverage(plan,reports)['invalid_reports'])

    def test_mock_stale_wrong_hook_unknown_auth_and_budget_rejected(self):
        plan=self.plan()
        changes=(
            ('evidence_kind','MOCK'),('plan_sha256','0'*64),
            ('source_binding_sha256','0'*64),('observed_hook','other'),
            ('primary_failure','invented'),('protocol_artifact','normal-integral-protocol-trace.json'),
            ('fault_injected',False),('mutation_retried',True),
            ('normal_receipt_reused_as_pass',True),('hosted_calls',True),
            ('diagnostic_sql_commands',True),('protocol_sha256','not-a-hash'),
            ('runtime_meter',{'stopped':True,'used':2350,'limit':2349,'state':{'auth_maybe_live':False}}),
            ('safety_auth',{'status':'NO_GO','revocation_confirmed':False,'global_zero_claim':False}))
        for key,value in changes:
            reports=self.fake_reports(plan);reports[0][key]=value
            with self.subTest(key=key):
                self.assertIn('unvalidated_real_case:before_call',f.coverage(plan,reports)['invalid_reports'])

    def test_boolean_zero_state_and_unconfirmed_auth_cannot_pass(self):
        plan=self.plan()
        reports=self.fake_reports(plan)
        reports[0]['actual']['auth_sessions']=False
        self.assertTrue(f.coverage(plan,reports)['invalid_reports'])
        reports=self.fake_reports(plan)
        reports[0]['runtime_meter']['state']['auth_maybe_live']=True
        self.assertTrue(f.coverage(plan,reports)['invalid_reports'])

    def test_plan_tampering_and_relabelled_capabilities_fail(self):
        plan=self.plan()
        for key,value in (('bounds',{}),('ready_for_execution',False),('register',[])):
            altered=copy.deepcopy(plan);altered[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                f.coverage(altered,[])
        altered=copy.deepcopy(plan)
        altered['register'][-1]['implemented']=True
        altered['plan_sha256']=f.sha({k:v for k,v in altered.items() if k!='plan_sha256'})
        with self.assertRaises(ValueError):
            f.coverage(altered,[])

    def test_original_three_expected_states_preserved(self):
        self.assertEqual([f.expected_state(x)['receipts'] for x in f.LEGACY],[0,1,1])
        self.assertEqual([f.expected_state(x)['sealed'] for x in f.LEGACY],[0,0,1])
        for case in f.LEGACY:
            self.assertEqual(f.expected_state(case)['retained_window'],1)
            self.assertEqual(f.expected_state(case)['auth_accounts'],3)
        with self.assertRaises(ValueError):
            f.expected_state('partial_cleanup')

    def test_original_auth_zero_validation_remains_strict(self):
        composition=SimpleNamespace(safety_auth_result={'status':'NO_GO','revocation_confirmed':True},
            auth_zero_proof={'source':'unit-only'},meter=SimpleNamespace(state={'auth_maybe_live':False}))
        f.check_auth_zero({'auth_accounts':3,'auth_sessions':0,'auth_refresh_tokens':0},composition)
        for row in ({'auth_accounts':3,'auth_sessions':False,'auth_refresh_tokens':0},
                    {'auth_accounts':3,'auth_sessions':1,'auth_refresh_tokens':0}):
            with self.assertRaises(RuntimeError):f.check_auth_zero(row,composition)


class UnitCursor:
    description = True
    def __init__(self, rows): self.rows = rows
    def fetchall(self): return self.rows


class UnitConnection:
    """Unit-only double. Never supplied to run() or emitted as real CI evidence."""
    def __init__(self, rows=None, error=None):
        self.rows = [] if rows is None else rows
        self.error, self.calls, self.closed = error, [], False
        self.info = SimpleNamespace(backend_pid=123)
    def execute(self, text, args=None):
        self.calls.append((text, args))
        if self.error: raise self.error
        return UnitCursor(self.rows)
    def close(self): self.closed = True


class NativeFaultBoundaryUnitTests(unittest.TestCase):
    def session(self, case='mid_route_a', connection=None):
        connection = connection or UnitConnection()
        s = rt.Session(SimpleNamespace(connect=lambda:connection), case,
                       {'limit':128,'cleanup_reserve':16}, time.monotonic()+180)
        s.connect()
        return s, connection

    def setUp(self):
        self.parser = patch('sql_protocol.single', return_value={'kind':'SelectStmt'})
        self.parser.start()
        self.addCleanup(self.parser.stop)

    def test_fourteen_explicit_categories(self):
        self.assertEqual(len(rt.REQUIRED),14)
        self.assertEqual(f.REQUIRED,rt.REQUIRED)
        for name in ('cleanup_failure','final_check_failure','closure_failure'):
            self.assertIn(name,rt.REQUIRED)

    def test_source_owned_driver_has_twelve_real_components_and_two_blockers(self):
        config={'dsn':'unit-only','auth_url':'http://127.0.0.1:59999','admin_token':'unit-only',
                'run_id':rt.NEW_RUN,'managed_costs':dict.fromkeys(('create','login','logout','delete'),10),
                'environment':'disposable_ci','exclusive_local_auth':True}
        driver=workflow.WorkflowDriver(SimpleNamespace(auth_failure_context=config),local_component_authorized=True)
        plan=driver.describe()
        self.assertEqual(set(plan['cases']),set(rt.REQUIRED)-{'pre_migration','post_migration'})
        self.assertEqual(set(plan['blocked']),{'pre_migration','post_migration'})
        self.assertTrue(plan['historical_registry_read_only'])

    def test_missing_auth_still_has_real_controller_closure_and_timeout(self):
        driver=workflow.WorkflowDriver(SimpleNamespace(),local_component_authorized=True)
        self.assertEqual(set(driver.describe()['cases']),{'mid_controller','closure_failure','timeout'})

    def test_unknown_or_failed_auth_cleanup_cannot_verify_subset(self):
        for value in ({}, {'confirmed':False}, {'all_component_owned_auth_zero':False},
                      {'all_component_owned_auth_zero':True,'close_error':{'class':'OSError'}},
                      {'owned_auth_cleanup_required':False,'error':{'class':'OSError'}}):
            with self.subTest(value=value):self.assertFalse(rt.cleanup_verified(value))
        self.assertTrue(rt.cleanup_verified(None))
        self.assertTrue(rt.cleanup_verified({'owned_auth_cleanup_required':False,'close_error':None}))
        self.assertTrue(rt.cleanup_verified({'owned_auth_cleanup_required':True,
                                            'all_component_owned_auth_zero':True,'close_error':None}))

    def test_delegated_auth_needs_independent_zero_not_only_delegated_pass(self):
        for count in (0,1):
            s,_=self.session('mid_auth')
            s.delegated_actor='unit-actor';s.phase_semantics=True
            observation=SimpleNamespace(values={'users':count,'sessions':0,'refresh_tokens':0})
            with patch.object(s,'snapshot',return_value=observation):
                result=workflow.WorkflowDriver(SimpleNamespace()).observe('mid_auth',s)
            self.assertIs(result,observation)
            self.assertEqual(s.phase_semantics,count==0)

    def test_concrete_driver_needs_explicit_local_authorization(self):
        driver=workflow.WorkflowDriver(SimpleNamespace())
        self.assertEqual(driver.describe()['cases'],{})
        with self.assertRaises(rt.Blocked):
            driver.open(SimpleNamespace(environment='disposable_ci'),['timeout'])

    def test_driver_refuses_hosted_even_when_authorized(self):
        driver=workflow.WorkflowDriver(SimpleNamespace(),local_component_authorized=True)
        with self.assertRaises(rt.Blocked):
            driver.open(SimpleNamespace(environment='staging'),['timeout'])

    def test_before_boundary_does_not_dispatch(self):
        s,c=self.session('pre_migration')
        with self.assertRaises(rt.InjectedFailure):
            s.step('pre_migration',lambda:s.query(c,'migration','select 1'))
        self.assertEqual(c.calls,[])
        self.assertEqual(s.used,0)
        self.assertTrue(s.stopped)

    def test_after_boundary_executes_once_and_preserves_charge(self):
        s,c=self.session()
        with self.assertRaises(rt.InjectedFailure):
            s.step('mid_route_a',lambda:s.query(c,'route_a','select 1'))
        self.assertEqual(len(c.calls),1)
        self.assertEqual(s.used,1)
        self.assertTrue(s.events[0]['confirmed'])
        self.assertTrue(s.injected)

    def test_lost_reply_preserves_dispatch_but_not_delivery(self):
        s,c=self.session('lost_reply')
        with self.assertRaises(rt.InjectedFailure):
            s.step('lost_reply',lambda:s.query(c,'route_a','select 1'))
        self.assertTrue(s.events[0]['confirmed'])
        self.assertFalse(s.events[0]['reply_delivered'])
        self.assertTrue(s.unknown)
        self.assertEqual(s.used,1)

    def test_duplicate_is_two_explicit_same_parameter_dispatches(self):
        s,c=self.session('duplicate')
        with self.assertRaises(rt.InjectedFailure):
            s.step('duplicate',lambda:s.query(c,'route_a','select %s',[1]))
        self.assertEqual(len(c.calls),2)
        self.assertEqual(s.used,2)
        self.assertEqual(s.events[0]['request_sha256'],s.events[1]['request_sha256'])

    def test_duplicate_changed_parameter_is_not_accepted(self):
        s,c=self.session('duplicate')
        values=iter((1,2))
        with self.assertRaisesRegex(rt.Blocked,'duplicate_protocol_changed'):
            s.step('duplicate',lambda:s.query(c,'route_a','select %s',[next(values)]))
        self.assertFalse(s.injected)

    def test_successful_query_is_not_a_timeout(self):
        s,c=self.session('timeout')
        with self.assertRaises(rt.Blocked):
            s.step('timeout',lambda:s.query(c,'timeout',rt.TIMEOUT_SQL))
        self.assertFalse(s.injected)

    def test_real_driver_cancel_sqlstate_only_marks_timeout(self):
        error=RuntimeError('never expose query text'); error.sqlstate='57014'
        s,c=self.session('timeout',UnitConnection(error=error))
        with self.assertRaises(RuntimeError):
            s.step('timeout',lambda:s.query(c,'timeout',rt.TIMEOUT_SQL))
        self.assertTrue(s.injected)
        self.assertEqual(s.primary['sqlstate'],'57014')
        self.assertEqual(s.secondary,[])
        self.assertEqual(s.used,1)

    def test_cleanup_failure_requires_real_fk_sqlstate(self):
        for code,expected in [('23503',True),('42501',False)]:
            error=RuntimeError('unit'); error.sqlstate=code
            s,c=self.session('cleanup_failure',UnitConnection(error=error))
            with self.assertRaises(RuntimeError):
                s.step('cleanup_failure',lambda:s.query(c,'cleanup_windows','delete from unit_only'))
            self.assertEqual(s.injected,expected)

    def test_first_failure_survives_cleanup_error(self):
        s,c=self.session()
        first=ValueError('raw secret SQL'); second=OSError('raw password')
        s.fail(first);s.fail(second);s.fail(first)
        self.assertEqual(s.primary['class'],'ValueError')
        self.assertEqual([x['class'] for x in s.secondary],['OSError'])
        self.assertNotIn('secret',json.dumps(s.primary))
        self.assertNotIn('password',json.dumps(s.secondary))

    def test_unknown_native_result_is_charged_and_not_retried(self):
        s,c=self.session(connection=UnitConnection(error=OSError('connection lost')))
        with self.assertRaises(OSError):s.query(c,'native','select 1')
        self.assertTrue(s.unknown)
        self.assertFalse(s.events[0]['confirmed'])
        self.assertEqual(s.used,1)
        with self.assertRaises(rt.Blocked):s.query(c,'native','select 1')
        self.assertEqual(len(c.calls),1)

    def test_cleanup_capacity_is_prepaid_before_normal_dispatch(self):
        s,c=self.session();s.used=112
        with self.assertRaises(rt.Blocked):s.query(c,'native','select 1')
        self.assertEqual(c.calls,[])
        s.safety=True
        s.query(c,'rollback','ROLLBACK')
        self.assertEqual(s.used,113)

    def test_exhausted_cleanup_has_no_refund_or_dispatch(self):
        s,c=self.session();s.safety=True;s.used=128
        with self.assertRaises(rt.Blocked):s.query(c,'rollback','ROLLBACK')
        self.assertEqual(c.calls,[])
        self.assertEqual(s.used,128)

    def test_old_and_preparation_uuid_never_reach_database(self):
        for value in (rt.OLD_RUN,rt.NEW_RUN):
            s,c=self.session()
            with self.assertRaises(rt.Blocked):s.query(c,'native','select %s',[value])
            with self.assertRaises(rt.Blocked):s.query(c,'native',"select '"+value+"'")
            self.assertEqual(c.calls,[])
            self.assertEqual(s.used,0)

    def test_fresh_case_uuid_is_not_historical_or_preparation(self):
        s,_=self.session()
        self.assertNotIn(s.case_id,(rt.OLD_RUN,rt.NEW_RUN))

    def test_receipts_have_hashes_not_raw_sql_or_values(self):
        s,c=self.session()
        s.query(c,'native','select %s',['private unit value'])
        payload=json.dumps(s.events)
        self.assertNotIn('select',payload)
        self.assertNotIn('private unit value',payload)
        self.assertIn('sha256',payload)

    def test_deadline_checked_before_dispatch(self):
        s,c=self.session();s.deadline=time.monotonic()-1
        with self.assertRaises(rt.Blocked):s.query(c,'native','select 1')
        self.assertEqual(c.calls,[])

    def test_raw_or_unregistered_connection_refused(self):
        s,_=self.session()
        with self.assertRaises(rt.Blocked):s.query(UnitConnection(),'native','select 1')

    def test_empty_callback_not_real_boundary(self):
        s,_=self.session()
        with self.assertRaises(rt.Blocked):s.step('mid_route_a',lambda:True)
        self.assertFalse(s.injected)

    def test_scope_mismatch_and_second_fault_refused(self):
        s,_=self.session('pre_migration')
        with self.assertRaises(rt.Blocked):s.step('mid_route_a',lambda:None)
        with self.assertRaises(rt.InjectedFailure):s.step('pre_migration',lambda:None)
        with self.assertRaises(rt.Blocked):s.step('pre_migration',lambda:None)

    def test_no_missing_driver_defaults_to_real_execution(self):
        environment={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging',
                     'GITHUB_REF':'refs/heads/main','GITHUB_SHA':'b'*40,'GITHUB_RUN_ID':'1'}
        with patch.dict(os.environ,environment,clear=True), patch('subprocess.Popen',side_effect=AssertionError('process')):
            value=rt.preflight(SimpleNamespace(),None,None,False)
        self.assertFalse(value['ready'])
        self.assertEqual(len(value['missing']),14)

    def test_inherited_hostaddr_service_cannot_redirect_native_connection(self):
        environment={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging',
                     'GITHUB_REF':'refs/heads/main','GITHUB_SHA':'b'*40,'GITHUB_RUN_ID':'1'}
        for key,value in [('PGHOSTADDR','203.0.113.1'),('PGSERVICE','remote'),('PGSERVICEFILE','unit-file')]:
            with patch.dict(os.environ,{**environment,key:value},clear=True), self.assertRaises(rt.Blocked):
                rt.preflight(SimpleNamespace(),None,None,False)

    def test_dollar_parameters_repeat_without_string_interpolation(self):
        text,args=workflow.dollar('select $2::uuid, $1::jsonb, $2::uuid',[{'a':1},'unit-id'])
        self.assertEqual(text,'select %s::uuid, %s::jsonb, %s::uuid')
        self.assertEqual(args,['unit-id','{"a": 1}','unit-id'])

    def test_real_pg17_parser_accepts_native_placeholders_without_values(self):
        import sql_protocol
        self.parser.stop()
        try:
            single=sql_protocol.single
            parsed=rt.parser_sql(workflow.API,['never insert this into SQL'])
            self.assertIn('$1',parsed)
            self.assertNotIn('never insert',parsed)
            self.assertEqual(single(parsed)['protocol_commands'],1)
            single(rt.parser_sql(workflow.BIND,['{}','{}']))
            with self.assertRaises(ValueError):single(rt.parser_sql('select %s; select 2',[1]))
        finally:
            self.parser.start()

    def test_auth_deadline_rejects_before_backend_dispatch(self):
        backend=SimpleNamespace(db=None,evidence_kind='unit',http=lambda *a,**k:self.fail('dispatch'))
        bounded=workflow.DeadlineBackend(backend,time.monotonic()+1)
        with self.assertRaises(rt.Blocked):bounded.http('POST','/admin/users')

    def test_real_b_worker_reuses_frozen_computation_without_database(self):
        s,_=self.session('mid_route_b')
        row={'route':'B','actor_role':'member','consent':True,'guard':'clear','seed':'normal',
             'events':[],'versions':[],'revision':0,'proposal_version':0,
             'basis':{'model':'1993a8073f40c583f108cc6baa2ef78c1d522d52b81b0f6071f10f109ca4753b','source':1}}
        value=workflow.WorkflowDriver(SimpleNamespace()).worker(s,{'op':'compute_b','row':row,'action':'build','data':{}})
        self.assertEqual(value['event']['action'],'build')
        self.assertEqual(value['status'],'member_pending')
        self.assertEqual(value['row_revision'],0)
        self.assertEqual(len(value['candidate_hash']),64)
        self.assertEqual(s.events,[])

    def test_parent_preserves_nonzero_after_worker_complete(self):
        s,_=self.session('mid_controller')
        process=SimpleNamespace(stdin=SimpleNamespace(write=lambda _:None,flush=lambda:None,close=lambda:None),
            stdout=SimpleNamespace(readline=lambda _:json.dumps({'op':'complete','value':{}})+'\n',close=lambda:None),
            wait=lambda **_:None,poll=lambda:2,returncode=2,kill=lambda:None)
        with patch.object(workflow.subprocess,'Popen',return_value=process), self.assertRaisesRegex(rt.Blocked,'nonzero'):
            workflow.WorkflowDriver(SimpleNamespace()).worker(s,{'op':'controller'})

    def test_parent_kills_joins_on_worker_wait_timeout(self):
        s,_=self.session('mid_controller')
        calls=[]
        def wait(**kwargs):
            calls.append('wait')
            if len(calls)==1:raise workflow.subprocess.TimeoutExpired('node',5)
        process=SimpleNamespace(stdin=SimpleNamespace(write=lambda _:None,flush=lambda:None,close=lambda:None),
            stdout=SimpleNamespace(readline=lambda _:json.dumps({'op':'complete','value':{}})+'\n',close=lambda:None),
            wait=wait,poll=lambda:None,returncode=None,kill=lambda:calls.append('kill'))
        with patch.object(workflow.subprocess,'Popen',return_value=process), self.assertRaises(workflow.subprocess.TimeoutExpired):
            workflow.WorkflowDriver(SimpleNamespace()).worker(s,{'op':'controller'})
        self.assertEqual(calls,['wait','kill','wait'])


class CandidateWorkflowSourceTests(unittest.TestCase):
    """Real candidate capture and poisoned import-cache regression; no database."""
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = pathlib.Path(folder.name)
        self.sources = self.root / 'candidate'
        self.out = self.root / 'out'
        self.out.mkdir()
        self.files = {}
        for key, relative in workflow.SCENARIO_SOURCES.items():
            target = self.sources / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((workflow.HERE.parents[2] / relative).read_bytes())
            self.files[key] = target
        self.manifest = self.out / 'candidate.json'
        self.register()
        self.saved = {}
        self.gate = SimpleNamespace(sources=self.sources, out=self.out,
                                    save=lambda name, value: self.saved.setdefault(name, value))

    def register(self):
        self.manifest.write_text(json.dumps({'sources': {
            relative: hashlib.sha256(self.files[key].read_bytes()).hexdigest()
            for key, relative in workflow.SCENARIO_SOURCES.items()}}))

    def cached_checkout(self):
        module = types.ModuleType('scenario')
        module.__file__ = str(self.root / 'checkout' / workflow.SCENARIO_SOURCES['scenario'])
        exec(compile(self.files['scenario'].read_bytes(), module.__file__, 'exec'), module.__dict__)
        return module

    def test_reproduces_cached_checkout_missing_file_then_uses_real_candidate_capture(self):
        cached = self.cached_checkout()
        with patch.dict(sys.modules, scenario=cached):
            from scenario import capture
            with self.assertRaises(FileNotFoundError):
                capture()
            actions, receipt = workflow.candidate_workflow_actions(self.gate)
            self.assertIs(sys.modules['scenario'], cached)
            self.assertEqual(cached.SOURCE, pathlib.Path(cached.__file__).parents[3] /
                             workflow.SCENARIO_SOURCES['workflow'])
        self.assertEqual(len(actions), 45)
        self.assertEqual(actions[0]['request']['action'], 'source_append')
        self.assertEqual(receipt['origin'], 'gate.sources')
        self.assertFalse(receipt['cached_scenario_used'])
        self.assertEqual(set(receipt['sources']), set(workflow.SCENARIO_SOURCES.values()))
        self.assertEqual(receipt['sql_dispatches'], 0)

    def test_prepare_uses_candidate_before_first_connection_not_after_activation(self):
        calls = []
        def query(connection, phase, text, args=None):
            calls.append(phase)
            if phase == 'workflow_limits':
                return [dict.fromkeys(('pg17', 'bounded_statement', 'bounded_lock', 'tls'), True)]
            if phase == 'workflow_baseline':
                return [dict(identities=0, running=0, enabled=0, bridge=0, migrations=47)]
            if phase == 'existing_fixture_seed':
                return [{'value': {'revision': 1}}]
            return [{'value': {}}]
        session = SimpleNamespace(connect=Mock(side_effect=lambda: calls.append('connect')),
                                  query=query, claims=set(), case_id='unit-case')
        driver = workflow.WorkflowDriver(self.gate)
        driver.actors = {r: SimpleNamespace(actor=r, email='unit@example.invalid', session_ids=['unit'])
                         for r in ('member', 'trainer', 'b')}
        original = workflow.candidate_workflow_actions
        def capture(gate):
            calls.append('candidate_capture')
            return original(gate)
        with patch.dict(sys.modules, scenario=self.cached_checkout()), \
                patch.object(workflow, 'candidate_workflow_actions', side_effect=capture):
            driver.prepare_workflow(session)
        self.assertEqual(calls[:2], ['candidate_capture', 'connect'])
        self.assertEqual(calls[-1], 'existing_product_call')
        self.assertEqual(len(session.actions), 45)

    def test_unregistered_dependency_blocks_before_connect(self):
        for dependency in workflow.SCENARIO_SOURCES:
            self.register()
            value = json.loads(self.manifest.read_text())
            del value['sources'][workflow.SCENARIO_SOURCES[dependency]]
            self.manifest.write_text(json.dumps(value))
            session = SimpleNamespace(connect=Mock())
            with self.subTest(dependency=dependency), self.assertRaises(workflow.WorkflowSourceError) as caught:
                workflow.WorkflowDriver(self.gate).prepare_workflow(session)
            self.assertEqual(caught.exception.reason, 'not_registered')
            self.assertEqual(caught.exception.dependency, dependency)
            session.connect.assert_not_called()

    def test_missing_candidate_does_not_fallback_to_available_checkout(self):
        self.files['workflow'].unlink()
        with self.assertRaises(workflow.WorkflowSourceError) as caught:
            workflow.candidate_workflow_actions(self.gate)
        self.assertEqual((caught.exception.reason, caught.exception.dependency), ('missing', 'workflow'))

    def test_hash_tampering_both_sources(self):
        for key, path in self.files.items():
            before = path.read_bytes()
            path.write_bytes(before + b'\n# changed\n')
            with self.subTest(key=key), self.assertRaises(workflow.WorkflowSourceError) as caught:
                workflow.candidate_workflow_actions(self.gate)
            self.assertEqual((caught.exception.reason, caught.exception.dependency), ('hash_mismatch', key))
            path.write_bytes(before)

    def test_duplicate_manifest_key_rejected(self):
        self.manifest.write_text('{"sources":{},"sources":{}}')
        with self.assertRaisesRegex(workflow.WorkflowSourceError, 'manifest_invalid'):
            workflow.candidate_workflow_actions(self.gate)

    def test_source_symlink_rejected(self):
        target = self.files['workflow']
        outside = self.root / 'outside.py'
        target.replace(outside)
        try:
            target.symlink_to(outside)
        except OSError as error:
            self.skipTest('symlink unavailable: ' + type(error).__name__)
        with self.assertRaisesRegex(workflow.WorkflowSourceError, 'path_invalid'):
            workflow.candidate_workflow_actions(self.gate)

    def test_candidate_module_cannot_redirect_workflow_origin(self):
        path = self.files['scenario']
        path.write_bytes(path.read_bytes() + b'\nSOURCE=ROOT / "outside.py"\n')
        self.register()
        with self.assertRaisesRegex(workflow.WorkflowSourceError, 'origin_mismatch'):
            workflow.candidate_workflow_actions(self.gate)

    def test_changed_workflow_during_capture_rejected(self):
        path = self.files['scenario']
        path.write_bytes(path.read_bytes() + b'\n_original=capture\ndef capture():\n'
            b' value=_original()\n SOURCE.write_bytes(SOURCE.read_bytes()+b"\\n")\n return value\n')
        self.register()
        with self.assertRaisesRegex(workflow.WorkflowSourceError, 'changed_during_capture'):
            workflow.candidate_workflow_actions(self.gate)

    def test_wrong_capture_digest_rejected(self):
        path = self.files['scenario']
        path.write_bytes(path.read_bytes() + b'\n_original=capture\ndef capture():\n'
            b' value=_original()\n value["source_sha256"]="0"*64\n return value\n')
        self.register()
        with self.assertRaisesRegex(workflow.WorkflowSourceError, 'capture_contract'):
            workflow.candidate_workflow_actions(self.gate)

    def test_open_diagnostic_precedes_any_auth_backend_or_runtime_connect(self):
        value = json.loads(self.manifest.read_text())
        del value['sources'][workflow.SCENARIO_SOURCES['workflow']]
        self.manifest.write_text(json.dumps(value))
        runtime = SimpleNamespace(environment='disposable_ci', connect=Mock())
        driver = workflow.WorkflowDriver(self.gate, local_component_authorized=True)
        with patch('auth_failure.RealBackend') as backend, self.assertRaises(workflow.WorkflowSourceError):
            driver.open(runtime, ['mid_route_a'])
        backend.assert_not_called()
        runtime.connect.assert_not_called()
        self.assertFalse(driver.opened)
        receipt = self.saved['integral-component-workflow-source.json']
        self.assertEqual(receipt['status'], 'BLOCKED')
        self.assertEqual(receipt['reason'], 'not_registered')
        self.assertEqual(receipt['dependency'], 'workflow')
        self.assertEqual(receipt['sql_dispatches'], 0)

    def test_receipt_storage_failure_stops_before_auth_backend(self):
        self.gate.save = Mock(side_effect=OSError('storage'))
        driver = workflow.WorkflowDriver(self.gate, local_component_authorized=True)
        with patch('auth_failure.RealBackend') as backend, self.assertRaises(OSError):
            driver.open(SimpleNamespace(environment='disposable_ci'), ['mid_route_a'])
        backend.assert_not_called()
        self.assertFalse(driver.opened)

    def test_primary_binding_error_survives_receipt_storage_failure(self):
        self.files['workflow'].unlink()
        self.gate.save = Mock(side_effect=OSError('storage'))
        driver = workflow.WorkflowDriver(self.gate, local_component_authorized=True)
        with patch('auth_failure.RealBackend') as backend, self.assertRaises(workflow.WorkflowSourceError) as caught:
            driver.open(SimpleNamespace(environment='disposable_ci'), ['mid_route_a'])
        backend.assert_not_called()
        self.assertEqual(caught.exception.reason, 'missing')
        self.assertEqual(caught.exception.__notes__, ['secondary_source_receipt_failure:OSError'])

    def test_source_receipt_is_prepaid_without_changing_case_command_caps(self):
        self.gate.auth_failure_context = {
            'dsn':'unit-only', 'auth_url':'http://127.0.0.1:59999', 'admin_token':'unit-only',
            'run_id':rt.NEW_RUN, 'managed_costs':dict.fromkeys(('create','login','logout','delete'),10),
            'environment':'disposable_ci', 'exclusive_local_auth':True}
        plan = workflow.WorkflowDriver(self.gate, local_component_authorized=True).describe()
        self.assertEqual(plan['bootstrap_artifact_files'], 201)
        self.assertEqual(plan['bootstrap_artifact_bytes'], 1048576 + 4096)
        self.assertTrue(all(c['limit'] == 128 and c['cleanup_reserve'] == 16 for c in plan['cases'].values()))
        self.assertTrue(set(workflow.SCENARIO_SOURCES.values()) <= set(plan['sources']))
        self.assertIn(workflow.PREFIX + 'admission_module_binding.py', plan['sources'])


if __name__=='__main__':unittest.main()
