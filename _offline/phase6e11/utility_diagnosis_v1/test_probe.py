import copy,json,pathlib,tempfile,unittest
from unittest.mock import patch
import probe as p

ID=lambda n:'78000000-0000-4000-8000-'+str(n).zfill(12)
IDENTITY=dict(ro='on',isolation='repeatable read',db='postgres',role='postgres',ssl=True,instance_sha=p.INSTANCE,backend=123,snapshot='1:1:')
def sample(n):
    return dict(reset='r',dealloc=0,statements=[dict(queryid='1',calls=n,since='s',temp_read=0,temp_written=0,wal='0',exec_ms=n)],health=dict(io_wait=0,long_active=0),background=dict(temp_bytes=0,reset='r'))
class Fake:
    def __init__(self):self.calls=[];self.samples=0;self.fail=None;self.rollback_fail=False
    def __call__(self,sql):
        self.calls.append(sql)
        if self.fail and self.fail in sql:raise ValueError('original_fault')
        if sql=='ROLLBACK' and self.rollback_fail:raise RuntimeError('secondary_secret_must_not_escape')
        if sql==p.GUARD:return [IDENTITY.copy()]
        if sql==p.SETTINGS:return [dict(track_utility='off',migrations=43)]
        if sql==p.INVENTORY:return [dict(schema='public',name='synthetic_'+str(i),columns=['id']) for i in range(100)]
        if sql==p.ALL_STATS:self.samples+=1;return [{'value':sample(self.samples)}]
        if sql.startswith('EXPLAIN'):return [{'QUERY PLAN':[{'Query Identifier':1,'Execution Time':0.1,'Plan':{'Actual Rows':1}}]}]
        if sql.startswith('FETCH'):return [{'value':None},{'value':'1'},{'value':'1'}]
        return []

class Tests(unittest.TestCase):
    def run_probe(self,fake=None,fail_save=None):
        fake=fake or Fake();saved={}
        def save(name,value):
            if name==fail_save:raise OSError('injected_storage')
            self.assertNotIn(name,saved);saved[name]=copy.deepcopy(value)
        probe=p.Probe(fake,save)
        result=probe.run({'member':ID(1)},dict(window=ID(2),a=ID(3),b=ID(4),runs={'seed':ID(5)}))
        return result,saved,fake
    def test_full_metadata_probe_never_fetches_real_tables(self):
        result,saved,fake=self.run_probe()
        self.assertEqual(result['status'],'READ_ONLY_DIAGNOSIS_COLLECTED_NOT_WORKFLOW_PASS')
        self.assertLess(result['commands'],128);self.assertEqual(fake.calls[0],p.BEGIN);self.assertEqual(fake.calls[-1],'ROLLBACK')
        self.assertEqual([s for s in fake.calls if s.startswith('FETCH')],['FETCH FORWARD 4 FROM fmz_utility_diagnosis'])
        self.assertEqual(result['pairs'],5);self.assertTrue(saved['synthetic_fetch-comparison.json']['synthetic_null_duplicates_preserved'])
        self.assertFalse(saved['original_declare-comparison.json']['old_rule_passes'])
        self.assertEqual(saved['original_declare-comparison.json']['background_attribution'],'UNRESOLVED')
        self.assertTrue(all(x['sent'] and x['confirmed'] for x in saved['ledger-final.json']['commands']))
    def test_failures_before_during_after_each_sample_save_rollback(self):
        _,normal,_=self.run_probe()
        labels=[x for x in normal if x.startswith(('sample-','command-','synthetic_','original_','observer-','stream-binding','reader-witness','transaction'))]
        for label in labels:
            with self.subTest(label=label):
                result,saved,fake=self.run_probe(fail_save=label)
                self.assertEqual(result['status'],'NO_GO')
                if label.startswith('command-022'):
                    self.assertIsNone(result['original_error']);self.assertEqual(result['closure_errors'][0]['phase'],'rollback')
                else:self.assertIsNotNone(result['original_error'])
                if label!='command-001-started.json':self.assertIn('ROLLBACK',fake.calls)
                self.assertIn('ledger-final.json',saved)
    def test_rollback_failure_does_not_mask_original_phase(self):
        fake=Fake();fake.fail='DECLARE';fake.rollback_fail=True
        result,saved,_=self.run_probe(fake)
        self.assertEqual(result['original_error']['phase'],'synthetic_declare')
        self.assertEqual(result['original_error']['reason'],'original_fault')
        self.assertEqual(result['closure_errors'][0]['phase'],'rollback')
        self.assertNotIn('secondary_secret',json.dumps(saved))
    def test_bad_readonly_denies_before_config(self):
        fake=Fake();orig=fake.__call__
        def query(sql):return [{**IDENTITY,'ro':'off'}] if sql==p.GUARD else orig(sql)
        result,_,_=self.run_probe(query)
        self.assertEqual(result['original_error']['reason'],'read_only_project_binding')
        self.assertNotIn(p.CONFIG,fake.calls)
    def test_atomic_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            e=p.Evidence(directory);e.save('before.json',{'n':1})
            with self.assertRaises(FileExistsError):e.save('before.json',{'n':2})
            self.assertEqual(json.loads((pathlib.Path(directory)/'before.json').read_text()),{'n':1})
            with patch('probe.os.link',side_effect=OSError('fault')):
                with self.assertRaises(OSError):e.save('after.json',{'n':3})
            self.assertFalse((pathlib.Path(directory)/'after.json').exists())
    def test_counters_reset_negative_and_temp_visible(self):
        a=sample(1);b=sample(2);b['statements'][0]['temp_written']=1
        self.assertEqual(p.changes(a,b)[0]['temp_written'],1)
        b['reset']='other'
        with self.assertRaises(ValueError):p.changes(a,b)
        with self.assertRaises(ValueError):p.changes(sample(2),sample(1))
    def test_budget_reserved_rollback_and_timeout(self):
        q=p.Probe(lambda s:[],lambda *x:None,clock=lambda:0)
        q.commands=[{}]*127
        with self.assertRaises(ValueError):q.command('ordinary','SELECT 1')
        q.command('rollback','ROLLBACK');self.assertEqual(len(q.commands),128)
        q=p.Probe(lambda s:[],lambda *x:None,clock=lambda:0);q.clock=lambda:541
        with self.assertRaises(ValueError):q.command('ordinary','SELECT 1')
        q.command('rollback','ROLLBACK')

if __name__=='__main__':unittest.main()
