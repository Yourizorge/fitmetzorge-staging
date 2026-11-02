"""Lost-response safety contract tests; hosted behavior is not inferred."""
import copy,unittest
from control_recovery import CLOSED,intent,recover

RUN='69000000-0000-4000-8000-000000000099'
EXPIRY='2026-11-02T12:03:00+00:00'

class Tests(unittest.TestCase):
    def test_identity_and_expiry_precede_mutation(self):
        proof,expected=intent(CLOSED,RUN,EXPIRY)
        other=intent(CLOSED,'69000000-0000-4000-8000-000000000098',EXPIRY)[1]
        self.assertNotEqual(expected['config']['proof_hash'],other['config']['proof_hash'])
        self.assertIn(RUN,proof);self.assertEqual(expected['request']['expires_at'],EXPIRY)
        for expiry in ('2026-11-02T12:03:00','invalid'):
            with self.assertRaises(ValueError):intent(CLOSED,RUN,expiry)
        with self.assertRaises(RuntimeError):intent(expected,RUN,EXPIRY)

    def test_all_partial_enable_outcomes_restore_in_four_commands(self):
        expected=intent(CLOSED,RUN,EXPIRY)[1]
        for config in (False,True):
            for request in (False,True):
                state=copy.deepcopy(CLOSED);calls=[]
                if config:state['config']=copy.deepcopy(expected['config'])
                if request:state['request']=copy.deepcopy(expected['request'])
                def query(channel,phase,sql,args=()):
                    calls.append((channel,phase,sql,args))
                    if phase in ('safety_control_before','safety_control_after'):
                        return [{'value':copy.deepcopy(state)}]
                    if 'fmz6e11_request_private' in sql:
                        self.assertEqual(args,[EXPIRY]);state['request']=copy.deepcopy(CLOSED['request'])
                    else:
                        self.assertEqual(args,[expected['config']['proof_hash']]);state['config']=copy.deepcopy(CLOSED['config'])
                    return []
                value=recover(query,CLOSED,expected)
                self.assertTrue(value['original_restored']);self.assertEqual(len(calls),4)
                self.assertEqual(state,CLOSED)

    def test_foreign_value_never_overwritten(self):
        expected=intent(CLOSED,RUN,EXPIRY)[1];state=copy.deepcopy(expected)
        state['config']['proof_hash']='not-this-run';calls=[]
        def query(*args):calls.append(args);return [{'value':state}]
        with self.assertRaisesRegex(RuntimeError,'foreign_state'):recover(query,CLOSED,expected)
        self.assertEqual(len(calls),1)

    def test_failed_after_read_never_claims_restoration(self):
        expected=intent(CLOSED,RUN,EXPIRY)[1]
        def query(channel,phase,sql,args=()):
            if phase=='safety_control_after':raise TimeoutError('not exported')
            return [{'value':expected}]
        with self.assertRaises(TimeoutError):recover(query,CLOSED,expected)

    def test_no_false_success_on_unrestored_state(self):
        expected=intent(CLOSED,RUN,EXPIRY)[1]
        with self.assertRaisesRegex(RuntimeError,'not_restored'):
            recover(lambda *args:[{'value':expected}],CLOSED,expected)

if __name__=='__main__':unittest.main()
