import copy,unittest
import admission

class Preregistration(unittest.TestCase):
    def setUp(self):self.plan=admission.plan()
    def test_original_45_paths(self):
        rows=self.plan['workflow_actions'];self.assertEqual(len(rows),45)
        self.assertIn('restore applied as v3',[r['label'] for r in rows])
        self.assertIn('b_reopen',[r['request']['action'] for r in rows])
    def test_separate_routes_and_auth(self):
        for row in self.plan['workflow_actions']:self.assertEqual(row['role']=='b',row['route']=='B')
        self.assertEqual(len(self.plan['auth_actions']),18)
    def test_writesets_known_before_execution(self):
        for row in self.plan['workflow_actions']:
            self.assertTrue(row['writes']);self.assertTrue(all(op in ('INSERT','UPDATE','DELETE') for t,op,k in row['writes']))
    def test_duplicate_keys_retained(self):
        keys=[r['request']['key'] for r in self.plan['workflow_actions']]
        self.assertEqual(len(keys)-len(set(keys)),2)
    def test_minimum_queries_exceeds_old_limit(self):self.assertEqual(self.plan['minimum_evidence_commands'],315)
    def test_no_hosted_admission_for_incomplete_plan(self):
        with self.assertRaisesRegex(ValueError,'lifecycle_uncompiled'):admission.validate(self.plan)
    def test_old_128_limit_still_denies(self):
        with self.assertRaisesRegex(ValueError,'query_budget'):admission.validate(self.plan,compiled_sql_commands=315,lifecycle_compiled=True)
    def test_expanded_limit_alone_insufficient(self):
        with self.assertRaisesRegex(ValueError,'ci_missing'):admission.validate(self.plan,approved_sql_limit=2226,compiled_sql_commands=1000,lifecycle_compiled=True)
    def test_ci_without_access_denied(self):
        with self.assertRaisesRegex(ValueError,'access_missing'):admission.validate(self.plan,approved_sql_limit=2226,compiled_sql_commands=1000,lifecycle_compiled=True,source_bound_ci=True)
    def test_mutated_plan_denied(self):
        self.plan['automatic_retries']=1
        with self.assertRaisesRegex(ValueError,'manifest_changed'):admission.validate(self.plan)
    def test_request_budget_must_include_all_commands(self):
        for n in (314,2227):
            with self.subTest(n=n),self.assertRaisesRegex(ValueError,'query_budget'):
                admission.validate(self.plan,approved_sql_limit=2226,compiled_sql_commands=n,lifecycle_compiled=True)
    def test_fully_specified_input_not_hosted_pass(self):
        r=admission.validate(self.plan,approved_sql_limit=2226,compiled_sql_commands=1000,lifecycle_compiled=True,source_bound_ci=True,hosted_access_attested=True)
        self.assertFalse(r['hosted_pass'])

if __name__=='__main__':unittest.main()
