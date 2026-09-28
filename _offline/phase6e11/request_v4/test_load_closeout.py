import copy,json,unittest
import load_closeout as l
from guard import Stop

class LoadTests(unittest.TestCase):
    def setUp(self):
        read=lambda p:json.loads(p.read_text())
        self.b=read(l.RUN/'before/identity.json');self.a=read(l.RUN/'after/identity.json')
        self.profiles=[(read(p),read(p.with_name(p.name.replace('-profile','-frame'))))
            for p in sorted((l.RUN/'before').glob('fetch_*-profile.json'))]
    def run_check(self):return l.reconcile(self.b['cli_numeric'],self.a['cli_numeric'],self.profiles,self.b['bindings']['fetch'])
    def test_saved_interval(self):self.assertEqual(l.verify()['status'],'SAVED_INTERVAL_LOAD_PASS')
    def test_missing(self):
        self.profiles.pop()
        with self.assertRaisesRegex(Stop,'missing_or_extra'):self.run_check()
    def test_duplicate(self):
        self.profiles.append(copy.deepcopy(self.profiles[0]))
        with self.assertRaisesRegex(Stop,'missing_or_extra'):self.run_check()
    def test_spill(self):
        self.profiles[0][0]['delta']['temp_blks_written']=1
        with self.assertRaisesRegex(Stop,'binding_or_load'):self.run_check()
    def test_slow_single(self):
        self.profiles[0][0]['delta']['total_exec_time']=2501
        with self.assertRaisesRegex(Stop,'binding_or_load'):self.run_check()
    def test_unaccounted(self):
        self.profiles[0][0]['delta']['total_exec_time']+=1
        with self.assertRaisesRegex(Stop,'not_fully_accounted'):self.run_check()
    def test_wrong_query(self):
        self.profiles[0][1]['sql_sha256']='wrong'
        with self.assertRaisesRegex(Stop,'binding_or_load'):self.run_check()

if __name__=='__main__':unittest.main()
