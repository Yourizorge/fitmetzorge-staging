import copy, unittest
import capacity as c


class Tests(unittest.TestCase):
    def test_full_original_register_and_all_prefixes_retained(self):
        old=c.historical(); result=c.build(old)
        self.assertEqual(result['normal_capacity'],2338)
        self.assertEqual(result['worst_including_safety'],2349)
        self.assertEqual(result['extra_above_limit'],112)
        self.assertEqual(sum(result['phase_budgets'].values()),2338)
        self.assertEqual(len(result['prefixes']),2339)
        preserved=[r for r in result['rows'] if not r.get('reservation_only')]
        self.assertEqual(len(preserved),len(old['rows']))
        for before,after in zip(old['rows'],preserved):
            self.assertEqual(before.get('writeset'),after.get('writeset'))
            self.assertEqual(before.get('template_sha'),after.get('template_sha'))
            self.assertEqual(before.get('action_binding'),after.get('action_binding'))
    def test_no_silent_raise_or_actual_claim(self):
        r=c.build(c.historical())
        self.assertFalse(r['fits_current_limit']);self.assertFalse(r['hosted_admitted'])
        self.assertFalse(r['attempt_consumed']);self.assertTrue(r['no_budget_increase_applied'])
        for e in r['cli_envelopes']:
            self.assertIsNone(e['observed_cli_commands']);self.assertEqual(e['cli_reserved'],64)
    def test_cleanup_and_safety_not_removed_to_fit(self):
        old=c.historical();result=c.build(old)
        for phase in ('cleanup','auth','controller','route_a','route_b','restore','io'):
            self.assertEqual(result['phase_budgets'][phase],old['phase_budgets'][phase])
        self.assertEqual(result['phase_budgets']['cleanup'],633)
        for p in result['prefixes']:
            self.assertGreaterEqual(p['reserve'],p['emergency_sql'])
            self.assertGreaterEqual(p['reserve'],p['remaining_normal_cleanup'])
            self.assertEqual(p['required_total'],p['used']+p['reserve'])
    def test_historical_missing_protocol_blocks(self):
        for mutate in ('row','cost','group','total'):
            old=copy.deepcopy(c.historical())
            if mutate=='row':old['rows'].pop()
            if mutate=='cost':old['rows'][0]['sql']=0
            if mutate=='group':next(r for r in old['rows'] if r['action']=='empty_cli_dry_run')['action']='hidden'
            if mutate=='total':old['normal_capacity']=1
            with self.assertRaises(ValueError):c.build(old)
    def test_no_unproved_smaller_cli_envelope(self):
        for cap in (0,2,13,True,1.5):
            with self.assertRaises(ValueError):c.build(c.historical(),cap)


if __name__=='__main__':unittest.main()
