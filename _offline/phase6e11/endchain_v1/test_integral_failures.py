"""Selector/validator unit regressions only; no real PG/GoTrue execution or PASS.

Fabricated adversarial report fixtures exercise rejection and incompleteness.
They are never written as CI evidence and never count as scenario coverage.
"""
import copy
import hashlib
import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import integral_failures as f


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

    def test_register_has_twelve_requirements_and_three_distinct_legacy_cases(self):
        rows=f.scenario_register()
        self.assertEqual(len(f.REQUIRED),12)
        self.assertEqual(len(rows),15)
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
        self.assertEqual(len(plan['missing_hooks']),12)
        self.assertIn('selected_cases_exceed_existing_three_case_bound',plan['blockers'])
        for case in f.REQUIRED:
            self.assertIn('required_hook_not_implemented:'+case,plan['blockers'])

    def test_old_three_cannot_be_full_selection(self):
        plan=self.plan(diagnostic_only=False)
        self.assertFalse(plan['ready_for_execution'])
        self.assertIn('required_scenario_not_selected:normal',plan['blockers'])
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

    def test_blocked_run_never_imports_or_calls_actual_backend(self):
        plan=self.plan(selection=None,diagnostic_only=False)
        saved=[]
        gate=SimpleNamespace(save=lambda name,value:saved.append((name,value)))
        with patch.object(f,'prepare',return_value=plan), \
                patch.dict(sys.modules,{'metered_composition':None}):
            with self.assertRaises(f.FailureCoverageBlocked):
                f.run(gate)
        self.assertEqual([name for name,_ in saved],['integral-failure-preflight.json'])

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


if __name__=='__main__':unittest.main()
