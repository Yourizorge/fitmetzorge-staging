"""Copy an allowlisted immutable numeric receipt; never perform hosted actions."""
import hashlib,json,os,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def main():
    source=ROOT/'supabase/.temp/phase6e11-utility-diagnosis-e91ae17a-357c-4af3-a10a-dc2de7c471f7'
    names=['authorization.json','closed.json','result.json','settings.json','transaction.json',
           'ledger-before-close.json','ledger-final.json','observer-binding.json','reader-witness.json','stream-binding.json']
    names += [p.name for p in source.glob('sample-*.json')]
    for kind in ('synthetic_declare','synthetic_fetch','synthetic_close','original_declare','original_close'):
        names += [kind+'-'+suffix+'.json' for suffix in ('before','after','comparison')]
    target=disk(HERE/'receipts'/'e91ae17a-357c-4af3-a10a-dc2de7c471f7');target.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(HERE.parent/'endchain_v1'));from source_scan import check
    manifest={}
    for name in sorted(names):
        raw=disk(source/name).read_bytes();check(name,raw)
        with (target/name).open('xb') as out:out.write(raw)
        manifest[name]=hashlib.sha256(raw).hexdigest()
    raw=json.dumps({'files':manifest,'old_failure_cause':'UNRESOLVED_NOT_REPRODUCED','workflow_pass':False,'source_unchanged':True},indent=2,sort_keys=True).encode()
    with (target/'MANIFEST.json').open('xb') as out:out.write(raw)
    print(json.dumps({'files':len(manifest),'manifest_sha256':hashlib.sha256(raw).hexdigest(),'scope':'read_only_diagnosis'}))
if __name__=='__main__':main()
