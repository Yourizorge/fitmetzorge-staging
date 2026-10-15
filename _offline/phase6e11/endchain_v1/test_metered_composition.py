import unittest
from metered_composition import MeteredComposition,capacity
from runtime_budget import BudgetStop

class Tests(unittest.TestCase):
    def test_phase_and_protocol_charged_before_query(self):
        c=MeteredComposition();c.action={'kind':'lifecycle','operation':'install'}
        c.before_sql('guard_install','BEGIN; SELECT 1; COMMIT')
        self.assertEqual(c.meter.used,3);self.assertEqual(c.meter.phases['guard'],3)
        self.assertTrue(c.meter.state['guard'])
        c.after_sql('guard_install','BEGIN; SELECT 1; COMMIT')
        self.assertIsNone(c.meter.pending)
    def test_auth_expected_commands_reserved_before_call(self):
        c=MeteredComposition();c.auth_before('a_member','verify')
        c.action={'kind':'auth','role':'a_member','operation':'verify'}
        c.before_sql('after','SELECT 1');c.after_sql('after','SELECT 1')
        self.assertEqual(c.meter.used,22);c.auth_after('verify')
        self.assertFalse(c.meter.managed_pending)
    def test_bootstrap_is_not_disguised_as_hosted_action(self):
        c=MeteredComposition()
        c.before_sql('profile_seed_a_member','SELECT 1');c.after_sql('profile_seed_a_member','SELECT 1')
        self.assertEqual(c.meter.used,0);self.assertEqual(len(c.commands),1)
    def test_cleanup_cannot_be_bypassed_on_stop(self):
        c=MeteredComposition();c.abort('synthetic')
        with self.assertRaisesRegex(ValueError,'unknown_safety'):c.before_sql('call','SELECT 1')
        c.safety_label='rollback_writer'
        c.before_sql('safety_rollback','ROLLBACK');c.after_sql('safety_rollback','ROLLBACK')
        with self.assertRaises(BudgetStop):c.before_sql('safety_rollback','ROLLBACK')
    def test_ci_prefix_requires_actual_protocol_evidence(self):
        c=MeteredComposition()
        with self.assertRaises(ValueError):c.admit_ci_prefix({'commands':[]},{})
        c.admit_ci_prefix({'commands':[{'confirmed':True}]*4},{'protocol_commands':14,'complete':True})
        self.assertEqual(c.meter.used,18)
    def test_final_receipt_cannot_exceed_registered_limit(self):
        self.assertEqual(sum(capacity()['phase_budgets'].values()),2226)
        self.assertEqual(capacity()['normal_capacity'],2226)
        self.assertEqual(capacity()['worst_including_safety'],2237)
        self.assertEqual(capacity()['approved_limit'],2237)

if __name__=='__main__':unittest.main()
