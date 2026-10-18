"""Immutable sanitized receipt export; no network or database operations."""
import hashlib,json,os,pathlib,re,sys
from closure import RUN_ID
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def disk(p):return pathlib.Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def digest(raw):return hashlib.sha256(raw).hexdigest()

def safe(raw):
    if len(raw)>2000000:raise ValueError('receipt_size')
    if re.search(rb'(sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]+\.',raw):
        raise ValueError('receipt_secret_pattern')
    json.loads(raw)

def export(source,kind):
    source=source.resolve()
    if not source.is_relative_to(ROOT/'supabase/.temp'):raise ValueError('receipt_scope')
    if kind=='hosted':
        if source.name!='phase6e11-reserved-hosted-'+RUN_ID:raise ValueError('receipt_run_binding')
        names=sorted(p.name for p in disk(source).glob('*.json'))
        label='reserved-'+RUN_ID
    elif kind=='ci':
        if not re.fullmatch(r'artifact-run-[0-9]+(?:-recovered)?',source.name):raise ValueError('receipt_ci_binding')
        names=['result.json','collection.json','artifact-manifest.json','endchain-sources.json',
               'complete-command-register.json','runtime-command-meter.json','integral-real-failure-matrix.json',
               'integral-closure.json','integral-migration-pair.json','integral-workflow.json',
               'stream-filter-pg17.json','stream-capacity-pg17.json','utility-binding-pg17.json','register-prefix-reserves.json',
               'endchain-budget-database.json','integral-control-enable-pair.json','integral-control-restore-pair.json',
               'registered-worker-terminal.json']
        names=[n for n in names if disk(source/n).is_file()]
        names+=sorted(p.name for p in disk(source).glob('*cli-isolation-*.json'))
        names+=sorted(p.name for p in disk(source).glob('*stop*.json'))
        names+=sorted(p.name for p in disk(source).glob('register-phase-*.json'))
        names+=sorted(p.name for p in disk(source).glob('integral-stream-*-binding.json'))
        names+=sorted(p.name for p in disk(source).glob('integral-stream-*-capacity.json'))
        label='reserved-ci-'+source.name.removeprefix('artifact-run-').removesuffix('-recovered')
    else:raise ValueError('receipt_kind')
    if not names or len(names)>1500 or len(names)!=len(set(names)):raise ValueError('receipt_set')
    values={}
    for name in names:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.json',name):raise ValueError('receipt_path')
        raw=disk(source/name).read_bytes();safe(raw);values[name]=raw
    target=disk(HERE/'receipts'/label);target.mkdir(exist_ok=False)
    for name,raw in values.items():
        with (target/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    receipt={'run_id':RUN_ID,'kind':kind,'source_folder':source.name,
             'files':{n:digest(v) for n,v in values.items()},'originals_unchanged':True}
    raw=(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode()
    with (target/'MANIFEST.json').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return {'path':str(target),'files':len(values),'manifest_sha256':digest(raw)}

if __name__=='__main__':print(json.dumps(export(pathlib.Path(sys.argv[1]),sys.argv[2])))
