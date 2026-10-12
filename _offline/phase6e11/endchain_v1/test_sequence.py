"""Offline assembly coverage, not Auth, SQL or hosted execution evidence."""
import copy,unittest
from sequence import compile_sequence,validate_sequence,ROLES,auth
from scenario import capture

class Sequence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=compile_sequence()
    def test_auth_is_bracketed_around_workflow(self):
        actions=self.plan['actions']
        self.assertEqual([x['kind'] for x in actions],['auth']*12+['workflow']*45+['auth']*6)
        for role in ROLES:
            self.assertEqual([x['operation'] for x in actions if x['kind']=='auth' and x['role']==role],list(auth.SEQUENCE))
    def test_all_original_product_cases_kept_exactly(self):
        self.assertEqual([a['scenario_contract'] for a in self.plan['actions'] if a['kind']=='workflow'],capture()['workflow_actions'])
    def test_every_action_has_independent_step(self):
        self.assertEqual([x['step'] for x in self.plan['actions']],list(range(63)))
    def test_auth_expected_counts_match_proven_local_contract(self):
        for a in self.plan['actions']:
            if a['kind']!='auth':continue
            self.assertEqual({(c['table'].removeprefix('auth.'),c['operation']):c['count'] for c in a['expected_counts']},auth.COUNTS[a['operation']])
            self.assertFalse(a['app_writes_allowed'])
    def test_auth_delete_proof_is_mandatory(self):
        for a in self.plan['actions']:
            if a['kind']=='auth' and a['operation'] in ('verify','logout'):
                self.assertTrue(any(c['operation']=='DELETE' for c in a['expected_counts']))
                self.assertEqual(a['required_validator'],'auth_contract.Contract')
    def test_counts_never_replace_row_binding_validator(self):
        for a in self.plan['actions']:
            self.assertTrue(a['request_metadata_required'])
            if a['kind']=='workflow':self.assertEqual(a['required_validator'],'workflow_evidence.validateWorkflow')
    def test_duplicate_requests_remain_separate_evidence_steps(self):
        workflows=[x['scenario_contract'] for x in self.plan['actions'] if x['kind']=='workflow']
        replays=[x for x in workflows if x['expected_outcome']=='replayed']
        self.assertEqual(len(replays),2)
        for x in replays:self.assertEqual([(t,op) for t,op,_ in x['writes']],[('events','INSERT')])
    def test_denials_cannot_create_plan_versions(self):
        for a in self.plan['actions']:
            if a['kind']=='workflow' and a['scenario_contract']['expected_http']!=200:
                self.assertEqual(a['expected_counts'],[{'table':'fmz6e11_private.events','operation':'INSERT','count':1}])
    def test_session_closure_follows_fixture_cleanup_gate(self):
        gate=next(x for x in self.plan['lifecycle_gates'] if x['name']=='revoke_and_scoped_fixture_delete_pairs')
        self.assertEqual(gate['position'],'after_workflow_before_logout')
    def test_safety_removal_not_blocked_by_invalid_workflow_pair(self):
        gates={x['name']:x['position'] for x in self.plan['lifecycle_gates']}
        for key in ('exact_observer_and_guard_removal','jit_revocation'):
            self.assertEqual(gates[key],'always_safety_finally')
    def test_missing_lifecycle_never_becomes_hosted_admission(self):
        self.assertTrue(all(not g['compiled'] for g in self.plan['lifecycle_gates']))
        self.assertFalse(self.plan['hosted_admitted'])
        self.assertFalse(self.plan['full_sql_budget_compiled'])
        self.assertFalse(validate_sequence(self.plan)['hosted_admitted'])
    def test_source_hash_change_rejected(self):
        value=copy.deepcopy(self.plan);value['sources'][next(iter(value['sources']))]='0'*64
        with self.assertRaisesRegex(ValueError,'source_changed'):validate_sequence(value)
    def test_reordered_or_missing_action_rejected(self):
        for mutation in ('reverse','delete'):
            value=copy.deepcopy(self.plan)
            if mutation=='reverse':value['actions'].reverse()
            else:value['actions'].pop()
            with self.assertRaisesRegex(ValueError,'sequence_or_source_changed'):validate_sequence(value)
    def test_lifecycle_or_budget_false_pass_rejected(self):
        for key in ('hosted_admitted','full_sql_budget_compiled'):
            value=copy.deepcopy(self.plan);value[key]=True
            with self.assertRaises(ValueError):validate_sequence(value)
    def test_minimum_is_not_a_full_execution_budget(self):
        self.assertEqual(self.plan['minimum_evidence_sql_commands'],315)
        self.assertGreater(self.plan['minimum_evidence_sql_commands'],128)

if __name__=='__main__':unittest.main()
