import unittest
from receipt_accounting import LABELS,meter_controls

class Tests(unittest.TestCase):
    def fixture(self):
        data={f'{i*10+j:03d}-{name}.json':{'exitcode':0} for i in range(4) for j,name in enumerate(LABELS)}
        data.update({f'cli-log-location-{i}.json':dict(collector='on',destination='stderr',directory='/synthetic',file='test.log') for i in range(4)})
        return data
    def test_selected_first_two_not_double_counted(self):
        data=self.fixture();r=meter_controls({n:'a'*64 for n in data},data.__getitem__)
        self.assertEqual(r['commands'],10);self.assertEqual(len({v['file'] for v in r['evidence']}),10)
        self.assertEqual(meter_controls({n:'a'*64 for n in data},data.__getitem__,4)['commands'],20)
    def test_missing_or_failed_control_rejected(self):
        for fault in ('missing','failed','location'):
            data=self.fixture()
            if fault=='missing':
                for n in list(data):
                    if 'ci-meter-prefix' in n:del data[n]
            elif fault=='failed':data['000-ci-meter-prefix.json']['exitcode']=3
            else:del data['cli-log-location-1.json']['file']
            with self.assertRaises(ValueError):meter_controls({n:'a'*64 for n in data},data.__getitem__)
if __name__=='__main__':unittest.main()
