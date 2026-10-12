import copy,json,pathlib,sys,unittest
import seal

class Seal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=pathlib.Path(sys.argv[1]);cls.records={n:json.loads((folder/(n+'.json')).read_text()) for n in seal.FILES}
    def change(self,file,path,value,reason):
        records=copy.deepcopy(self.records);target=records[file]
        for key in path[:-1]:target=target[key]
        target[path[-1]]=value
        with self.assertRaisesRegex(ValueError,reason):seal.validate(records)
    def test_real_complete_metadata(self):self.assertEqual(seal.validate(self.records)['status'],'SCOPED_AUDIT_PROOF_SEALED')
    def test_missing_delete(self):self.change('action-events',[2,'operation'],'UPDATE','seal_writes')
    def test_other_row(self):self.change('action-events',[2,'key_sha'],'0'*64,'seal_binding')
    def test_drift(self):self.change('action-after',['fixture_rows'],1,'seal_drift')
    def test_jit_remaining(self):self.change('closed',['remaining_mappings'],1,'seal_access')
    def test_temp_writes(self):self.change('action-pair',['plans',0,'own_temp_written_blocks'],1,'seal_action_io')
    def test_budget(self):self.change('result',['commands'],129,'seal_budget')
    def test_objects_remaining(self):self.change('metadata-removal-pair',['own_additions'],1,'seal_objects')

if __name__=='__main__':unittest.main(argv=[sys.argv[0]],exit=True)
