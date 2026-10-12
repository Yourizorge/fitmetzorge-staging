import copy,json,unittest,uuid
import probe
from failure import safe_reason

class Probe(unittest.TestCase):
    def test_empty_shape(self):
        with self.assertRaises(ValueError):probe.plan_summary('[]')
    def test_no_spill(self):
        p=[{'Plan':{'Temp Written Blocks':0},'Execution Time':1.5,'Query Identifier':42,'Triggers':[{'Calls':1}]}]
        self.assertEqual(probe.plan_summary(json.dumps(p))['trigger_calls'],1)
    def test_spill_nested(self):
        with self.assertRaises(ValueError):probe.plan_summary(json.dumps([{'Plan':{'Plans':[{'Temp Written Blocks':1}]},'Execution Time':1}]))
    def test_latency(self):
        with self.assertRaises(ValueError):probe.plan_summary(json.dumps([{'Plan':{},'Execution Time':1001}]))
    def test_parameter_injection(self):
        with self.assertRaises(ValueError):probe.sql_sequence("';delete from auth.users",str(uuid.uuid4()))
    def test_missing_write(self):
        with self.assertRaises(ValueError):probe.validate([],str(uuid.uuid4()),str(uuid.uuid4()),str(uuid.uuid4()))
    def test_exact_three(self):
        self.assertEqual(len(probe.sql_sequence(str(uuid.uuid4()),str(uuid.uuid4()))),3)
    def test_protocol_reason(self):self.assertEqual(safe_reason(RuntimeError('terminal_row_count')),'terminal_row_count')
    def test_sqlstate_reason(self):self.assertEqual(safe_reason(RuntimeError('sqlstate_42501')),'sqlstate_42501')
    def test_secret_redaction(self):self.assertEqual(safe_reason(RuntimeError('password=private-value')),'scoped_action_failed')

if __name__=='__main__':unittest.main()
