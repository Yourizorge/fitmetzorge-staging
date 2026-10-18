import json,pathlib,unittest
from runtime_budget import RuntimeBudget,BudgetStop
from closure import RUN_ID,PURPOSE
from metered_composition import capacity

def register():
    return capacity()

class RuntimeBudgetTests(unittest.TestCase):
    def meter(self,**kw):return RuntimeBudget(register(),run_id=RUN_ID,purpose=PURPOSE,**kw)
    def test_every_command_including_protocol_is_counted(self):
        m=self.meter()
        for action in ['BEGIN','metadata','history','ROLLBACK']:
            n=m.charge('preflight',1,action=action);m.confirm(n)
        self.assertEqual(m.used,4)
        with self.assertRaisesRegex(BudgetStop,'phase_exhausted'):m.charge('preflight',1,action='extra')
    def test_full_normal_capacity_and_safety_reserve(self):
        m=self.meter()
        for phase,cost in register()['phase_budgets'].items():
            n=m.charge(phase,cost,action=phase,mutation=phase in ('guard','setup','route_a','route_b','restore'))
            m.confirm(n)
        self.assertEqual(m.used,2338);self.assertTrue(m.close()['complete'])
    def test_pending_statement_prevents_next_mutation(self):
        m=self.meter();m.charge('setup',1,action='prepare',mutation=True)
        with self.assertRaisesRegex(BudgetStop,'unconfirmed'):m.charge('setup',1,action='next',mutation=True)
        m.stop('transport_timeout')
        with self.assertRaisesRegex(BudgetStop,'stopped'):m.charge('setup',1,action='retry')
        n=m.safety('rollback_writer',1);m.confirm_safety(n)
        with self.assertRaises(BudgetStop):m.safety('rollback_writer',1)
        self.assertFalse(m.close()['complete'])
    def test_auth_drift_never_refunds_or_hides_commands(self):
        m=self.meter();n=m.charge('auth',21,action='verify',kind='managed_auth',mutation=True)
        with self.assertRaisesRegex(BudgetStop,'count_mismatch'):m.confirm(n,actual=22)
        self.assertEqual(m.used,22);self.assertTrue(m.stopped)
    def test_managed_escrow_allows_metered_after_evidence_not_invisible_sql(self):
        m=self.meter();a=m.charge('auth',11,action='issue',kind='managed_auth')
        n=m.charge('auth',1,action='after_stats');m.confirm(n)
        self.assertEqual(m.used,12)
        with self.assertRaisesRegex(BudgetStop,'unconfirmed'):m.close()
        m.confirm(a,actual=11);self.assertTrue(m.close()['complete'])
    def test_failed_managed_action_keeps_reserved_cost_and_failure(self):
        m=self.meter();m.charge('auth',21,action='verify',kind='managed_auth')
        m.stop('http_deadline')
        self.assertEqual(m.close()['used'],21);self.assertFalse(m.close()['complete'])
    def test_only_registered_run_has_allowance(self):
        with self.assertRaises(BudgetStop):RuntimeBudget(register(),run_id='other',purpose=PURPOSE)
        r=register();r['phase_budgets']['cleanup']=192
        with self.assertRaisesRegex(BudgetStop,'complete_capacity'):RuntimeBudget(r,run_id=RUN_ID,purpose=PURPOSE)
    def test_deadline_is_not_extended_for_slow_commands(self):
        now=[0];m=self.meter(clock=lambda:now[0]);now[0]=600
        with self.assertRaisesRegex(BudgetStop,'deadline'):m.charge('auth',1,action='issue')
    def test_safety_is_not_permission_for_blind_cleanup(self):
        m=self.meter();m.stop('pair_missing')
        with self.assertRaises(BudgetStop):m.safety('delete_all_fixtures',1)
    def test_last_minute_is_reserved_for_safety_not_ordinary_work(self):
        now=[0];m=self.meter(clock=lambda:now[0]);now[0]=540
        with self.assertRaisesRegex(BudgetStop,'ordinary_deadline'):m.charge('auth',1,action='issue')
        n=m.safety('rollback_writer',1);m.confirm_safety(n)
        now[0]=600
        with self.assertRaisesRegex(BudgetStop,'safety_deadline'):m.safety('rollback_reader',1)

if __name__=='__main__':unittest.main()
