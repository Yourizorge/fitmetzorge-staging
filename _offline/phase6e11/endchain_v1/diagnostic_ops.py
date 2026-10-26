"""Prepare/collect a diagnostic candidate using the unchanged existing ops."""
import importlib.util,json,pathlib,sys
import diagnostic_ci
spec=importlib.util.spec_from_file_location('wal_diagnostic_endchain_ops',diagnostic_ci.ci.HERE/'ops.py')
ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)
WORKFLOW='phase6e11-wal-diagnostic.yml'

def main():
    if len(sys.argv)>=2 and sys.argv[1]=='dispatch' and len(sys.argv)==4 and sys.argv[3]=='--enable':
        folder=pathlib.Path(sys.argv[2]).resolve()
        if folder.parent!=ops.ROOT/'supabase/.temp' or not folder.name.startswith('phase6e11-endchain-ci-'):
            raise ValueError('diagnostic_folder_scope')
        if (folder/'dispatch.json').exists():raise ValueError('no_retry')
        head=ops.g.git('rev-parse','HEAD')
        if ops.g.git('branch','--show-current')!='main' or json.loads((folder/'before.json').read_text())['head']!=head:
            raise ValueError('diagnostic_source_changed')
        blob=json.loads((folder/'blob.json').read_text())
        inputs={'candidate_blob':blob['blob'],'candidate_sha256':blob['sha256'],'enabled':True}
        ops.g.write(folder/'dispatch.json',{'head':head,'inputs':inputs,'workflow':WORKFLOW,'diagnostic_only':True})
        ops.g.api('/actions/workflows/'+WORKFLOW+'/dispatches','POST',{'ref':'main','inputs':inputs})
        print('DIAGNOSTIC_DISPATCHED_ONCE')
        return
    if len(sys.argv)<2 or sys.argv[1] not in (
            'prepare','upload','artifact','artifact-recover'):
        raise ValueError('diagnostic_ops_mode_use_separate_workflow_for_dispatch')
    diagnostic_ci.activate_sources()
    return ops.main()

if __name__=='__main__':main()
