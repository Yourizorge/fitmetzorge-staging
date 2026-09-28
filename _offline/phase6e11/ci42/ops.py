"""Repo-scoped CI42 orchestration; inherits credential redaction and immutable evidence."""
import argparse,base64,json,pathlib,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'ci41'))
import ops
def prepare():
    folder=ops.ROOT/'supabase/.temp'/('phase6e11-ci42-'+uuid.uuid4().hex);folder.mkdir()
    import runner
    candidates=sorted((ops.ROOT/'supabase/migrations').glob('*.sql'))+sorted((ops.ROOT/'supabase/tests').glob('*.sql'))
    candidates += [ops.ROOT/p for p in sorted(runner.EXTRAS)]
    files={}
    for path in candidates:
        name=path.relative_to(ops.ROOT).as_posix();data=path.read_bytes()
        if not runner.allowed(name) or ops.re.search(rb'(sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}',data):raise RuntimeError('source_boundary')
        files[name]=base64.b64encode(data).decode()
    if len(list((ops.ROOT/'supabase/migrations').glob('*.sql')))!=42:raise RuntimeError('42_required')
    digest=ops.write(folder/'candidate.json',{'format':1,'files':files})
    ops.write(folder/'before.json',{'head':ops.git('rev-parse','HEAD'),'branch':ops.git('branch','--show-current'),'canonical_count':42})
    print(json.dumps({'folder':str(folder),'sha256':digest,'files':len(files)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','upload','dispatch','status','collect']);p.add_argument('folder',nargs='?');p.add_argument('--run',type=int);a=p.parse_args()
    ops.WORKFLOW='phase6e11-db42.yml'
    if a.mode=='prepare':prepare()
    else:
        folder=pathlib.Path(a.folder).resolve()
        if folder.parent!=(ops.ROOT/'supabase/.temp').resolve() or not folder.name.startswith('phase6e11-ci42-'):raise RuntimeError('evidence_scope')
        if a.mode=='collect':ops.collect(folder,a.run)
        else:getattr(ops,a.mode)(folder)
