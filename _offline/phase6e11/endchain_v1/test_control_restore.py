"""Control reserves require a returned, validated read; no hosted operations."""
import copy,unittest
from complete_register import bind_auth_states,reserve_prefixes,safety_path
from metered_composition import MeteredComposition
from runtime_budget import BudgetStop

ORIGINAL={'config':{'id':True,'enabled':False,'proof_hash':None},
    'request':{'id':True,'enabled':False,'expires_at':None}}

class ControlRestoreTests(unittest.TestCase):
    def composition(self):
        c=MeteredComposition();c.meter.state['controls']=True
        c.action={'kind':'workflow','step':70}
        return c

    def safety_read(self,c):
        c.abort('control_read_not_confirmed')
        c.before_sql('safety_control_before','SELECT 1')
        c.after_sql('safety_control_before','SELECT 1')
        self.assertTrue(c.meter.state['controls'])
        self.assertEqual(c.meter.safety_spent['control_before'],1)

    def test_lost_restore_read_keeps_safety_reserve(self):
        c=self.composition();c.before_sql('control_restored','SELECT 1')
        self.assertTrue(c.meter.state['controls'])
        self.safety_read(c)
        self.assertFalse(any(row.get('controls_restored_validated') for row in c.commands))

    def test_mismatch_keeps_reserve_after_sql_confirmation(self):
        c=self.composition();c.before_sql('control_restored','SELECT 1');c.after_sql('control_restored','SELECT 1')
        bad=copy.deepcopy(ORIGINAL);bad['request']['enabled']=True
        with self.assertRaisesRegex(RuntimeError,'restore_mismatch'):c.confirm_controls_restored(bad,ORIGINAL)
        self.safety_read(c)
        self.assertFalse(any(row.get('controls_restored_validated') for row in c.commands))

    def test_confirmation_only_after_exact_returned_read(self):
        c=self.composition();c.before_sql('control_restored','SELECT 1')
        with self.assertRaisesRegex(RuntimeError,'unconfirmed'):c.confirm_controls_restored(ORIGINAL,ORIGINAL)
        self.assertTrue(c.meter.state['controls'])
        c.after_sql('control_restored','SELECT 1');used=c.meter.used
        c.confirm_controls_restored(copy.deepcopy(ORIGINAL),ORIGINAL)
        self.assertFalse(c.meter.state['controls']);self.assertEqual(c.meter.used,used)
        self.assertTrue(c.commands[-1]['controls_restored_validated'])
        self.assertEqual(c.meter.state_confirmations[-1]['reason'],'validated_original_controls')

    def test_no_release_for_wrong_phase_or_precharge(self):
        c=self.composition();c.before_sql('control_restore_before','SELECT 1');c.after_sql('control_restore_before','SELECT 1')
        with self.assertRaisesRegex(RuntimeError,'unconfirmed'):c.confirm_controls_restored(ORIGINAL,ORIGINAL)
        with self.assertRaisesRegex(BudgetStop,'requires_confirmation'):
            c.meter.charge('cleanup',1,action='forged',state_after={'controls':False})
        self.assertTrue(c.meter.state['controls'])

    def test_prefix_includes_lost_reply_until_confirmation(self):
        rows=[dict(phase='setup',action='enable',sql=1,state_after={'controls':True}),
              dict(phase='cleanup',action='control_restored',sql=1,controls_restored_validated=True),
              dict(phase='closure',action='close',sql=1)]
        original=copy.deepcopy(rows);prefixes=reserve_prefixes(bind_auth_states(rows))
        self.assertEqual(rows,original)
        self.assertEqual(prefixes[2]['unconfirmed_emergency_sql'],13)
        self.assertEqual(prefixes[2]['emergency_sql'],9)
        self.assertEqual(prefixes[2]['reserve'],13)
        self.assertEqual(prefixes[3]['reserve'],9)
        rows[1]['state_after']={'controls':False}
        with self.assertRaisesRegex(ValueError,'before_confirmation'):reserve_prefixes(bind_auth_states(rows))

if __name__=='__main__':unittest.main()
