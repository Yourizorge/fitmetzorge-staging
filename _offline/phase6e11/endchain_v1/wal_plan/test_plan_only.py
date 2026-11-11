import copy
import unittest
from plan_only import prepare,sha,numeric_only,METRICS

class PlanTests(unittest.TestCase):
    def compile(self,sql):return prepare(sql,sha(sql.encode()))
    def sample(self):return [{'Plan':dict.fromkeys(METRICS,0)}]
    def test_select_with_parameter(self):self.assertTrue(self.compile('select $1::uuid')['pg17_parse_ok'])
    def test_changed_source_denied(self):
        with self.assertRaisesRegex(ValueError,'source_changed'):prepare('select 2',sha(b'select 1'))
    def test_multiple_statements_denied(self):
        with self.assertRaises(ValueError):self.compile('select 1;select 2')
    def test_select_into_denied(self):
        with self.assertRaisesRegex(ValueError,'write_shape'):self.compile('select 1 into tmp')
    def test_writable_cte_denied(self):
        with self.assertRaisesRegex(ValueError,'write_shape'):
            self.compile('with gone as(delete from t returning id) select * from gone')
    def test_missing_metric_is_unknown_not_zero(self):
        value=self.sample();del value[0]['Plan']['WAL Bytes']
        with self.assertRaises(ValueError):numeric_only(value)
    def test_noninteger_negative_boolean_denied(self):
        for bad in (True,-1,0.5,'0',None):
            with self.subTest(bad=bad):
                value=self.sample();value[0]['Plan']['WAL Bytes']=bad
                with self.assertRaises(ValueError):numeric_only(value)
    def test_plan_text_private_fields_not_exported(self):
        value=self.sample();value[0]['Plan'].update({'Filter':'PRIVATE_REVIEW_SENTINEL',
            'Relation Name':'PRIVATE_REVIEW_SENTINEL','Output':['PRIVATE_REVIEW_SENTINEL']})
        value[0]['Query Text']='PRIVATE_REVIEW_SENTINEL'
        result=numeric_only(value)
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL',str(result))
        self.assertFalse(result['full_chain_admission'])
    def test_child_counters_are_not_summed(self):
        value=self.sample();value[0]['Plan']['WAL Bytes']=7
        child=copy.deepcopy(value[0]['Plan']);child['WAL Bytes']=5
        value[0]['Plan']['Plans']=[child]
        result=numeric_only(value)
        self.assertEqual([n['metrics']['WAL Bytes'] for n in result['nodes']],[7,5])
        self.assertFalse(result['summed_across_nodes'])
    def test_unknown_child_counter_denied(self):
        value=self.sample();value[0]['Plan']['Plans']=[{}]
        with self.assertRaises(ValueError):numeric_only(value)

if __name__=='__main__':unittest.main()
