"""Artifact receipts: exact bytes, run, SHA and safe paths; no network calls."""
import contextlib,hashlib,importlib.util,io,json,pathlib,tempfile,unittest,zipfile
spec=importlib.util.spec_from_file_location('guard_artifact_ops_test',pathlib.Path(__file__).with_name('ops.py'))
ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)

class Artifact(unittest.TestCase):
    def run_case(self,fault=None):
        folder=pathlib.Path(tempfile.mkdtemp(prefix='fmz-guard-artifact-'))
        (folder/'blob.json').write_text(json.dumps({'sha256':'a'*64}))
        (folder/'dispatch.json').write_text(json.dumps({'head':'b'*40}))
        result=json.dumps({'status':'CLEAN_CI_PASS','candidate_sha256':'a'*64,'commit':'b'*40,'run_id':'123'}).encode()
        manifest={'result.json':hashlib.sha256(result).hexdigest()}
        if fault=='file_digest':manifest['result.json']='0'*64
        buff=io.BytesIO()
        with zipfile.ZipFile(buff,'w') as z:
            z.writestr('result.json',result);z.writestr('artifact-manifest.json',json.dumps(manifest))
            if fault=='path':z.writestr('../escape.json','{}')
            if fault=='extra':z.writestr('extra.json','{}')
        raw=buff.getvalue()
        artifact={'id':1,'name':'phase6e11-guard-123-1','expired':fault=='expired','size_in_bytes':len(raw),'digest':'sha256:'+hashlib.sha256(raw).hexdigest()}
        if fault=='archive_digest':artifact['digest']='sha256:'+'0'*64
        meta={'status':'completed','run_attempt':2 if fault=='attempt' else 1,'display_title':'a'*64,'head_sha':'c'*40 if fault=='head' else 'b'*40}
        def api(path,**kwargs):
            return {'/actions/runs/123':meta,'/actions/runs/123/artifacts':{'artifacts':[artifact]},'/actions/artifacts/1/zip':raw}[path]
        old=ops.g.api;ops.g.api=api
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                if fault:
                    with self.assertRaises(RuntimeError):ops.collect_artifact(folder,123)
                else:
                    ops.collect_artifact(folder,123)
                    self.assertEqual((folder/'run-123/result.json').read_bytes(),result)
                    self.assertTrue(json.loads((folder/'run-123/collection.json').read_text())['all_file_hashes_valid'])
        finally:ops.g.api=old
    def test_exact(self):self.run_case()
    def test_archive_digest(self):self.run_case('archive_digest')
    def test_file_digest(self):self.run_case('file_digest')
    def test_paths(self):self.run_case('path')
    def test_extra(self):self.run_case('extra')
    def test_expired(self):self.run_case('expired')
    def test_attempt(self):self.run_case('attempt')
    def test_head(self):self.run_case('head')
if __name__=='__main__':unittest.main()
