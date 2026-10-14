import hashlib,json,pathlib,tempfile,unittest,zipfile
from receipt_export import export

def checked(folder):
    return export(folder,1,hashlib.sha256((folder/'artifact-run-1/evidence.zip').read_bytes()).hexdigest())

class ExportTests(unittest.TestCase):
    def fixture(self,fault=None):
        folder=pathlib.Path(tempfile.mkdtemp(prefix='phase6e11-endchain-ci-'))
        (folder/'candidate.json').write_bytes(b'{}')
        sha=hashlib.sha256(b'{}').hexdigest()
        (folder/'blob.json').write_text(json.dumps({'sha256':sha}))
        (folder/'dispatch.json').write_text(json.dumps({'head':'b'*40}))
        original=folder/'artifact-run-1';original.mkdir()
        files={'result.json':json.dumps({'run_id':1,'candidate_sha256':sha,
            'commit':'c'*40 if fault=='source' else 'b'*40,'status':'CLEAN_CI_PASS',
            'full_chain_admission':False}).encode()}
        for i in range(1017):files[str(i)+'.json']=b'{}'
        if fault=='path':files['../escape.json']=b'{}'
        if fault=='count':
            for i in range(1400):files['extra'+str(i)+'.json']=b'{}'
        manifest={k:hashlib.sha256(v).hexdigest() for k,v in files.items()}
        if fault=='hash':manifest['0.json']='0'*64
        with zipfile.ZipFile(original/'evidence.zip','w') as z:
            for name,value in files.items():z.writestr(name,value)
            z.writestr('artifact-manifest.json',json.dumps(manifest))
        return folder
    def test_complete_bundle_and_no_overwrite(self):
        folder=self.fixture();before=(folder/'artifact-run-1/evidence.zip').read_bytes()
        one=checked(folder);two=checked(folder)
        self.assertNotEqual(one['folder'],two['folder'])
        self.assertEqual(one['files'],1018)
        self.assertFalse(one['full_chain_admission'])
        self.assertEqual((folder/'artifact-run-1/evidence.zip').read_bytes(),before)
    def test_reject_path(self):
        with self.assertRaisesRegex(ValueError,'archive_paths'):checked(self.fixture('path'))
    def test_reject_count(self):
        with self.assertRaisesRegex(ValueError,'archive_paths'):checked(self.fixture('count'))
    def test_reject_hash(self):
        with self.assertRaisesRegex(ValueError,'manifest_hash'):checked(self.fixture('hash'))
    def test_reject_source(self):
        with self.assertRaisesRegex(ValueError,'source_binding'):checked(self.fixture('source'))
    def test_reject_archive(self):
        with self.assertRaisesRegex(ValueError,'archive_digest'):export(self.fixture(),1,'0'*64)

if __name__=='__main__':unittest.main()
