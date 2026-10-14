"""Bound CI artifacts: reject wrong source/run/bytes and preserve previous evidence."""
import contextlib,hashlib,importlib.util,io,json,pathlib,tempfile,unittest,zipfile
spec=importlib.util.spec_from_file_location('endchain_artifact_test',pathlib.Path(__file__).with_name('artifact.py'))
ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)

class Artifact(unittest.TestCase):
    def run_case(self,fault=None):
        folder=pathlib.Path(tempfile.mkdtemp(prefix='fmz-endchain-artifact-'))
        (folder/'blob.json').write_text(json.dumps({'sha256':'a'*64}))
        (folder/'dispatch.json').write_text(json.dumps({'head':'b'*40}))
        result=json.dumps({'status':'CLEAN_CI_PASS','candidate_sha256':'a'*64,
            'commit':'b'*40,'run_id':'124' if fault=='result' else '123',
            'full_chain_admission':False}).encode()
        manifest={'result.json':hashlib.sha256(result).hexdigest()}
        if fault=='file_digest':manifest['result.json']='0'*64
        buff=io.BytesIO()
        with zipfile.ZipFile(buff,'w') as z:
            z.writestr('result.json',result);z.writestr('artifact-manifest.json',json.dumps(manifest))
            if fault=='path':z.writestr('../escape.json','{}')
            if fault=='extra':z.writestr('extra.json','{}')
            if fault=='count':
                for i in range(1400):z.writestr('bounded'+str(i)+'.json','{}')
        raw=buff.getvalue()
        artifact={'id':1,'name':'phase6e11-endchain-123-1','expired':fault=='expired',
                  'size_in_bytes':len(raw),'digest':'sha256:'+hashlib.sha256(raw).hexdigest()}
        if fault=='archive_digest':artifact['digest']='sha256:'+'0'*64
        if fault=='name':artifact['name']='phase6e11-guard-123-1'
        meta={'status':'completed','run_attempt':2 if fault=='attempt' else 1,
              'display_title':'a'*64,'head_sha':'c'*40 if fault=='head' else 'b'*40}
        def api(path,**kwargs):
            return {'/actions/runs/123':meta,'/actions/runs/123/artifacts':{'artifacts':[artifact]},
                    '/actions/artifacts/1/zip':raw}[path]
        with contextlib.redirect_stdout(io.StringIO()):
            if fault:
                with self.assertRaises(RuntimeError):ops.collect(folder,123,api)
            else:
                partial=folder/'artifact-run-123'
                partial.mkdir();(partial/'evidence.zip').write_bytes(raw)
                ops.collect(folder,123,api,recover=True)
                self.assertEqual((partial/'evidence.zip').read_bytes(),raw)
                self.assertEqual(list(p.name for p in partial.iterdir()),['evidence.zip'])
                recovered=folder/'artifact-run-123-recovered'
                self.assertEqual((recovered/'result.json').read_bytes(),result)
                # Use another empty output root for the ordinary no-overwrite test.
                folder2=pathlib.Path(tempfile.mkdtemp(prefix='fmz-endchain-artifact-'))
                for name in ('blob.json','dispatch.json'):(folder2/name).write_bytes((folder/name).read_bytes())
                folder=folder2
                ops.collect(folder,123,api)
                target=folder/'artifact-run-123'
                self.assertEqual((target/'result.json').read_bytes(),result)
                receipt=json.loads((target/'collection.json').read_text())
                self.assertTrue(receipt['all_file_hashes_valid'])
                self.assertFalse(receipt['full_chain_admission'])
                with self.assertRaises(FileExistsError):ops.collect(folder,123,api)
                self.assertEqual((target/'result.json').read_bytes(),result)
    def test_exact_and_no_overwrite(self):self.run_case()
    def test_archive_digest(self):self.run_case('archive_digest')
    def test_file_digest(self):self.run_case('file_digest')
    def test_paths(self):self.run_case('path')
    def test_extra(self):self.run_case('extra')
    def test_expired(self):self.run_case('expired')
    def test_attempt(self):self.run_case('attempt')
    def test_head(self):self.run_case('head')
    def test_result_run(self):self.run_case('result')
    def test_wrong_artifact_name(self):self.run_case('name')
    def test_finite_file_bound(self):self.run_case('count')
if __name__=='__main__':unittest.main()
