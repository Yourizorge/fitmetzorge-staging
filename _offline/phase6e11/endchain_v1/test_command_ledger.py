import unittest
from command_ledger import ledger,reader_trace,arm_trace
TRACE={'counts':{'evidence':5,'workflow':8,'issuance_guard':6},'hosted_calls':0}
class BudgetLedgerTests(unittest.TestCase):
    def test_reader(self):self.assertEqual(reader_trace(),4)
    def test_auth(self):self.assertEqual(arm_trace(),{'arm':4,'disarm':1})
    def test_exact_bound(self):
        p=ledger(TRACE);self.assertEqual(p['current_adapter_lower_bound'],1323)
        self.assertEqual(len(p['actions']),63);self.assertFalse(p['hosted_admitted'])
        self.assertEqual(p['status'],'NO_GO_PRE_HOSTED_BUDGET')
    def test_components(self):
        p=ledger(TRACE)
        self.assertEqual(sum(p[k] for k in ['evidence_commands','workflow_transaction_commands',
          'scoped_reader_commands','auth_observer_commands','identity_guard_commands']),1323)
    def test_lifecycle_not_claimed_complete(self):
        p=ledger(TRACE);self.assertIn('fixture_cleanup',p['not_yet_included'])
        self.assertEqual(p['hosted_commands'],0)
    def test_bad_trace(self):
        with self.assertRaises(ValueError):ledger({'counts':{},'hosted_calls':0})
if __name__=='__main__':unittest.main()
