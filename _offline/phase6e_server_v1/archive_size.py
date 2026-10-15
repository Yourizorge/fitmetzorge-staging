"""Archive only sanitized numeric diagnosis metadata, never a new connection."""
import hashlib,json,pathlib,re,sys
from size_diagnosis import RUN,disk
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def main():
    source=ROOT/'supabase/.temp'/('phase6e11-numeric-size-'+RUN)
    read=lambda n:json.loads(disk(source/n).read_bytes())
    result=read('result.json');closed=read('closed.json')
    if result.get('status')!='NUMERIC_DIAGNOSIS_PASS_NOT_WORKFLOW_PASS' or not result.get('rollback_confirmed') or not result.get('jit_revoked') or closed.get('remaining_mappings')!=0 or not closed.get('confirmed'):raise ValueError('numeric_closure')
    if result['commands']>128 or result['capacity']['hash_rows_transported'] or result['io']['own_temp_written']:raise ValueError('numeric_limits')
    target=disk(HERE/'receipts'/('numeric-'+RUN));target.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(HERE.parent/'phase6e11/endchain_v1'));from source_scan import check
    saved={}
    for path in sorted(disk(source).glob('*.json')):
        if path.name=='offline-capacity-proposal.json':continue
        if not re.fullmatch('[A-Za-z0-9_.-]+\\.json',path.name):raise ValueError('numeric_filename')
        raw=path.read_bytes();check(path.name,raw)
        with (target/path.name).open('xb') as f:f.write(raw)
        saved[path.name]=hashlib.sha256(raw).hexdigest()
    proposal=read('offline-capacity-proposal.json')
    derived={k:v for k,v in proposal.items() if k not in ('rows','prefixes')}
    derived['derived_register_hashes']={k:hashlib.sha256(json.dumps(proposal[k],sort_keys=True,separators=(',',':')).encode()).hexdigest() for k in ('rows','prefixes')}
    derived['reproduce']='capacity_proposal.load_register + build with retained numeric result; not hosted admission'
    raw=json.dumps(derived,sort_keys=True,indent=2).encode();check('capacity-summary.json',raw)
    with (target/'capacity-summary.json').open('xb') as f:f.write(raw)
    saved['capacity-summary.json']=hashlib.sha256(raw).hexdigest()
    with (target/'MANIFEST.json').open('x') as f:json.dump({'run_id':RUN,'files':saved,'historical_evidence_unchanged':True,'metadata_only':True,'workflow_pass':False},f,sort_keys=True,indent=2)
    print(json.dumps({'files':len(saved),'path':str(target),'workflow_pass':False}))
if __name__=='__main__':main()
