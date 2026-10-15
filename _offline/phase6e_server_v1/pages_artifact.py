"""Verify the exact deployed Pages artifact and bounded HTTP probes, no Supabase."""
import hashlib,io,json,os,pathlib,subprocess,sys,tarfile,urllib.error,urllib.request,uuid,zipfile
from ops import ROOT,disk,g

def inspect(raw,expected):
    names=set();matched=set()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as archive:
        members=archive.getmembers()
        if len(members)>10000 or sum(m.size for m in members)>200000000:raise ValueError('artifact_bounds')
        for member in members:
            name=member.name.removeprefix('./').rstrip('/')
            if not name:continue
            if name in names or name.startswith('/') or '..' in name.split('/') or not (member.isfile() or member.isdir()):raise ValueError('artifact_path')
            names.add(name)
            if name.split('/')[0] in ('_offline','supabase','.github'):raise ValueError('private_path_published')
            if name in expected:
                if not member.isfile() or hashlib.sha256(archive.extractfile(member).read()).hexdigest()!=expected[name]:raise ValueError('runtime_mismatch')
                matched.add(name)
    if matched!=set(expected):raise ValueError('runtime_missing')
    return {'entries':len(names),'runtime_assets':len(matched),'all_private_roots_absent':True}

def main():
    folder=pathlib.Path(sys.argv[1]).resolve()
    if folder.parent!=ROOT/'supabase/.temp' or not folder.name.startswith('phase6e-server-ci-'):raise ValueError('scope')
    head=g.git('rev-parse','HEAD')
    if g.git('branch','--show-current')!='main' or g.git('ls-remote','origin','refs/heads/main').split()[0]!=head:raise ValueError('head_binding')
    runs=g.api('/actions/runs?per_page=30')['workflow_runs']
    runs=[r for r in runs if r['head_sha']==head and 'pages' in r['name'].lower() and r['conclusion']=='success']
    if len(runs)!=1:raise ValueError('pages_success_binding')
    run=runs[0];meta=g.api('/actions/runs/'+str(run['id'])+'/artifacts')['artifacts']
    artifacts=[a for a in meta if a['name']=='github-pages' and not a['expired'] and a['size_in_bytes']<20000000]
    if len(artifacts)!=1:raise ValueError('pages_artifact')
    a=artifacts[0];raw=g.api('/actions/artifacts/'+str(a['id'])+'/zip',raw=True);sha=hashlib.sha256(raw).hexdigest()
    if a['digest']!='sha256:'+sha:raise ValueError('artifact_sha')
    expected={}
    for x in json.loads((ROOT/'docs/PHASE6E10_FREEZE_EVIDENCE.json').read_bytes())['protected']:
        if not x['file'].startswith(('_','supabase/')):expected[x['file']]=x['sha256']
    for number in range(12,21):
        for x in json.loads((ROOT/('docs/PHASE6E'+str(number)+'_FREEZE_EVIDENCE.json')).read_bytes())['sources']:
            if not x['file'].startswith(('_','docs/')):expected[x['file']]=x['git_sha256']
    for p in (ROOT/'complete-recording-demo').iterdir():
        name=p.relative_to(ROOT).as_posix()
        value=subprocess.run([os.environ['FMZ_GIT'],'show',head+':'+name],cwd=ROOT,capture_output=True,check=True).stdout
        expected[name]=hashlib.sha256(value).hexdigest()
    if len(expected)!=152:raise ValueError('runtime_inventory')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.namelist()!=['artifact.tar'] or z.infolist()[0].file_size>200000000:raise ValueError('zip_members')
        checked=inspect(z.read('artifact.tar'),expected)
    probes=['_offline/phase6e_server_v1/ui.js','_offline/phase6e_server_v1/store.py','_offline/phase6e_server_v1/draft_queue.js','_offline/phase6e_server_v1/queue_ui.js',
      '_offline/phase6e_server_v1/receipts/ci-38739029524-completion/registration12-transport-pair-0091df8d-0a8a-41fd-8604-a1c20fd7254c-validated.json',
      'supabase/migrations/20261012185121_phase6e11_single_endchain_budget.sql','.github/workflows/phase6e-server-local-ci.yml']
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    opener=urllib.request.build_opener(NoRedirect());statuses=[]
    for name in probes:
        request=urllib.request.Request('https://yourizorge.github.io/fitmetzorge-staging/'+name+'?verified='+head,method='HEAD')
        try:
            with opener.open(request,timeout=15) as response:status=response.status
        except urllib.error.HTTPError as e:status=e.code
        statuses.append({'path':name,'status':status})
        if status!=404:raise ValueError('private_http_incomplete')
    value={'status':'PAGES_ARTIFACT_AND_PROBES_PASS','head':head,'pages_run':run['id'],'artifact_id':a['id'],'artifact_sha256':sha,
      'artifact':checked,'private_probes':statuses,'supabase_calls':0,'previous_http_503_remains_incomplete':True}
    g.write(disk(folder/('pages-artifact-'+uuid.uuid4().hex+'.json')),value);print(json.dumps(value))
if __name__=='__main__':main()
