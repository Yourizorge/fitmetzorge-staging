"""Source-only staging CI orchestration. No Supabase token or hosted call."""
import base64,hashlib,importlib.util,io,json,os,pathlib,re,sys,uuid,zipfile
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('controller_github_ops',HERE.parent/'ci41/ops.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
import ci
ROOT=g.ROOT
HEAD='9772d9f0d58f21386515b716de00e3880f7c6438'
PREFIX='phase6e11-controller-'
def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def sha(p):return hashlib.sha256(disk(p).read_bytes()).hexdigest()
def baseline():
    if g.git('branch','--show-current')!='main' or g.git('rev-parse','HEAD')!=HEAD:raise RuntimeError('baseline_head')
    if g.git('ls-remote','origin','refs/heads/main').split()[0]!=HEAD:raise RuntimeError('remote_head')
    folder=ROOT/'supabase/.temp'/(PREFIX+uuid.uuid4().hex);folder.mkdir()
    names=set(g.git('ls-files','--cached','--others','--exclude-standard','-z').split('\0'))
    new=lambda n:n.startswith('_offline/phase6e11/controller_v1/') or n in {
      'docs/PHASE6E11_CONTROLLER_DESIGN.md','.github/workflows/phase6e11-controller-ci.yml',
      'supabase/migrations/'+ci.M43}
    retained={n:sha(ROOT/n) for n in names if n and not new(n) and disk(ROOT/n).is_file()}
    prior=json.loads((ROOT/'docs/PHASE6E11_EXTRA_EDGE_EVIDENCE.json').read_text())
    g.write(folder/'before.json',{'head':HEAD,'retained':retained,'status':g.git('status','--short'),'extra_edge_evidence_sha':sha(ROOT/'docs/PHASE6E11_EXTRA_EDGE_EVIDENCE.json')})
    print(json.dumps({'folder':str(folder),'retained_files':len(retained)}))
def prepare(folder):
    files=sorted((ROOT/'supabase/migrations').glob('*.sql'))+sorted((ROOT/'supabase/tests').glob('*.sql'))
    files += [ROOT/p for p in sorted(ci.old.EXTRAS|ci.EXTRA)]
    bundle={}
    for path in files:
        name=path.relative_to(ROOT).as_posix()
        if not ci.old.allowed(name) and name not in ci.EXTRA:raise RuntimeError('candidate_path')
        data=path.read_bytes()
        if re.search(rb'(sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}',data):raise RuntimeError('source_secret_pattern')
        bundle[name]=base64.b64encode(data).decode()
    digest=g.write(folder/'candidate.json',{'format':1,'files':bundle})
    print(json.dumps({'sha256':digest,'files':len(bundle)}))
def upload(folder):g.upload(folder)
def dispatch(folder):
    if (folder/'dispatch.json').exists():raise RuntimeError('no_retry')
    blob=json.loads((folder/'blob.json').read_text())
    inputs={'candidate_blob':blob['blob'],'candidate_sha256':blob['sha256']}
    g.api('/actions/workflows/phase6e11-controller-ci.yml/dispatches','POST',{'ref':'main','inputs':inputs})
    g.write(folder/'dispatch.json',{'head':g.git('rev-parse','HEAD'),'inputs':inputs})
    print('DISPATCHED_ONCE')
def status(folder):
    digest=json.loads((folder/'blob.json').read_text())['sha256']
    runs=g.api('/actions/workflows/phase6e11-controller-ci.yml/runs?per_page=10&event=workflow_dispatch')['workflow_runs']
    print(json.dumps([{k:r[k] for k in ('id','status','conclusion','head_sha','html_url')} for r in runs if digest in r['display_title']]))
def corrected_ci(folder):
    prior=json.loads((folder/'run-38239427354/result.json').read_text())
    if prior['phase']!='candidate' or prior['error']!='historical_migration_changed' or prior['migrations_applied']!=0:raise RuntimeError('wrong_retry_cause')
    blob=json.loads((folder/'blob.json').read_text())
    inputs={'candidate_blob':blob['blob'],'candidate_sha256':blob['sha256']}
    g.write(folder/'corrected-ci-dispatch.json',{'head':g.git('rev-parse','HEAD'),'inputs':inputs,'cause':'proven_CRLF_LF_only','prior_run':38239427354})
    g.api('/actions/workflows/phase6e11-controller-ci.yml/dispatches','POST',{'ref':'main','inputs':inputs})
    print('ONE_CORRECTED_CI_DISPATCH')
def preserve(folder):
    b=json.loads((folder/'before.json').read_text());changed=[n for n,h in b['retained'].items() if not disk(ROOT/n).is_file() or sha(ROOT/n)!=h]
    value={'changed':changed,'retained':len(b['retained']),'status':'PASS' if not changed else 'NO_GO'}
    g.write(disk(folder/('preservation-'+uuid.uuid4().hex+'.json')),value);print(json.dumps(value))
    if changed:raise RuntimeError('retained_file_changed')
def recover_ci(folder,run):
    target=folder/('run-'+str(run));raw=disk(target/'logs.zip').read_bytes();evidence={}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for name in archive.namelist():
            current=None;parts=[]
            for line in archive.read(name).decode(errors='replace').splitlines():
                line=re.sub(r'^\d{4}-\d\d-\d\dT\S+\s+','',line)
                if line.startswith('FMZ_EVIDENCE_BEGIN '):_,current,expected=line.split();parts=[]
                elif current and line.startswith('FMZ_DATA '):parts.append(line[9:])
                elif current and line=='FMZ_EVIDENCE_END '+current:
                    value=base64.b64decode(''.join(parts),validate=True);h=hashlib.sha256(value).hexdigest()
                    if h!=expected or not re.fullmatch(r'[a-zA-Z0-9_.-]+\.(json|txt)',current):raise RuntimeError('evidence_invalid')
                    path=disk(target/current)
                    if path.exists():
                        if path.read_bytes()!=value:raise RuntimeError('existing_evidence_conflict')
                    else:
                        with path.open('xb') as out:out.write(value)
                    evidence[current]=h;current=None
    g.write(disk(target/'recovered-manifest.json'),{'log_sha256':hashlib.sha256(raw).hexdigest(),'evidence':evidence,
      'run':run,'recovery':'Windows extended-length path; previously extracted bytes verified and preserved'})
    print(json.dumps({'run':run,'files':len(evidence),'result':json.loads(disk(target/'result.json').read_text())}))
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='baseline':baseline()
    else:
        folder=pathlib.Path(sys.argv[2]).resolve()
        if folder.parent!=(ROOT/'supabase/.temp').resolve() or not folder.name.startswith(PREFIX):raise RuntimeError('scope')
        if mode=='collect':g.collect(folder,int(sys.argv[3]))
        elif mode=='recover_ci':recover_ci(folder,int(sys.argv[3]))
        elif mode in ['prepare','upload','dispatch','status','preserve','corrected_ci']:globals()[mode](folder)
        else:raise RuntimeError('mode')
