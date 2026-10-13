"""Publish only sanitized, verified local CI evidence; never hosted admission."""
import hashlib,json,os,pathlib,re,sys

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def disk(path):
    path=pathlib.Path(path).resolve()
    return pathlib.Path('\\\\?\\'+str(path)) if os.name=='nt' and not str(path).startswith('\\\\?\\') else path
def sha(raw):return hashlib.sha256(raw).hexdigest()

def archive(source):
    source=disk(source)
    def read(name):return json.loads((source/name).read_text())
    collection=read('collection.json');result=read('result.json')
    if result['status']!='CLEAN_CI_PASS' or result['hosted_requests']!=0 or not collection['all_file_hashes_valid']:
        raise ValueError('unverified_ci')
    files=read('artifact-manifest.json')
    for name,expected in read('endchain-sources.json')['sources'].items():
        if sha(disk(ROOT/name).read_bytes())!=expected:raise ValueError('source_changed_'+name)
    chosen={'result.json','endchain-sources.json','complete-command-register.json','register-prefix-reserves.json',
        'integral-real-failure-matrix.json','integral-complete-protocol-trace.json',
        'integral-workflow.json','integral-workflow-io.json','integral-fixture_setup-io.json',
        'integral-fixture_closeout-io.json','integral-control-enable-pair.json','integral-control-restore-pair.json',
        'integral-preflight.json','workflow-auth-protocol.json','cli-protocol-0.json','cli-protocol-1.json'}
    chosen.update(name for name in files if name.startswith(('register-phase-','integral-stream-','integral-gates-','lifecycle-')))
    chosen.update('auth-protocol-%02d.json'%i for i in range(18))
    target=disk(HERE/'receipts'/('ci-'+str(collection['run'])))
    if target.exists():raise FileExistsError('receipt_already_archived')
    payloads={}
    for name in sorted(chosen):
        if not re.fullmatch('[A-Za-z0-9_.-]+\\.json',name) or name not in files:raise ValueError('receipt_allowlist')
        raw=(source/name).read_bytes()
        if sha(raw)!=files[name]:raise ValueError('receipt_hash')
        if re.search(rb'(sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.',raw):
            raise ValueError('receipt_secret_pattern')
        payloads[name]=raw
    target.mkdir(parents=True,exist_ok=False)
    for name,raw in payloads.items():
        with (target/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    manifest={**collection,'selected_files':{name:sha(raw) for name,raw in payloads.items()},
        'source_files_match':True,'historical_evidence_unchanged':True,
        'status':'INTEGRAL_CI_CAPACITY_PASS_HOSTED_BUDGET_NO_GO'}
    with (target/'MANIFEST.json').open('x') as f:json.dump(manifest,f,indent=2);f.flush();os.fsync(f.fileno())
    print(json.dumps({'folder':str(target),'files':len(payloads),'source_files_match':True,'manifest_sha256':sha((target/'MANIFEST.json').read_bytes())}))

if __name__=='__main__':archive(sys.argv[1])
