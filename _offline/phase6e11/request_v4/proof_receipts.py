"""Read-only CI receipts; archive only fixed diagnostic fields, never JWT/log bodies."""
import hashlib,importlib.util,io,json,pathlib,sys,uuid,zipfile
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('github_ci_ops',HERE.parent/'ci41/ops.py')
ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)
RUNS=[36426447746,36426724594,36427380641,36427882283]
def main():
    folder=ops.ROOT/'supabase/.temp'/('phase6e11-request-ci-receipts-'+uuid.uuid4().hex);folder.mkdir()
    summaries=[]
    allowed={'status','bound','readonly','migrations','synthetic_identities','bridge_enabled','proof_present',
      'auth_admin_present','application_writes','auth_calls','secrets_returned','error','sqlstate','error_type'}
    for rid in RUNS:
        meta=ops.api('/actions/runs/'+str(rid))
        if meta['status']!='completed':raise RuntimeError('ci_run_still_active')
        summary={k:meta[k] for k in ('id','head_sha','status','conclusion','html_url','created_at','updated_at')}
        raw=ops.api('/actions/runs/'+str(rid)+'/logs',raw=True)
        findings=[]
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for name in z.namelist():
                for line in z.read(name).decode(errors='replace').splitlines():
                    text=line.split(' ',1)[-1]
                    if not text.startswith('{'):continue
                    try:value=json.loads(text)
                    except ValueError:continue
                    if not isinstance(value,dict) or set(value)-allowed:continue
                    if value not in findings:findings.append(value)
        summary.update(log_sha256=hashlib.sha256(raw).hexdigest(),sanitized_results=findings)
        ops.write(folder/(str(rid)+'.json'),summary);summaries.append(summary)
    ops.write(folder/'result.json',{'runs':summaries,'raw_logs_saved':False,'tokens_saved':False})
    print(json.dumps({'folder':str(folder),'runs':summaries}))
if __name__=='__main__':main()
