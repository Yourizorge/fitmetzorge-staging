"""Persist a fresh offline preparation receipt; never a hosted admission."""
import datetime,hashlib,io,json,os,pathlib,shutil,subprocess,sys,unittest,uuid
import xml.etree.ElementTree as ET
from admission import plan
from sequence import compile_sequence,validate_sequence,ROOT

HERE=pathlib.Path(__file__).resolve().parent

def digest(raw):return hashlib.sha256(raw).hexdigest()

def sources():
    paths={*(ROOT/p for p in compile_sequence()['sources']),*HERE.glob('*.py'),*HERE.glob('*.mjs'),
        *(HERE.parent/'controller_v1').glob('*.mjs'),*(HERE.parent/'controller_guard_v1').glob('*.mjs')}
    return {p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(paths)}

def write(path,value):
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    # A new directory and exclusive create preserve every earlier receipt.
    with path.open('xb') as handle:handle.write(raw);handle.flush();os.fsync(handle.fileno())
    return digest(raw)

def main():
    before=sources();sequence=compile_sequence()
    suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_*.py')
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=2).run(suite)
    node=shutil.which('node')
    if not node:raise RuntimeError('local_node_missing')
    paths=sorted(p.relative_to(ROOT).as_posix() for folder in
        [HERE,HERE.parent/'controller_v1',HERE.parent/'controller_guard_v1'] for p in folder.glob('*.test.mjs'))
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP')}
    process=subprocess.run([node,'--test','--test-reporter=junit',*(str(ROOT/p) for p in paths)],
      cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
    tree=ET.fromstring(process.stdout)
    cases=tree.findall('.//testcase')
    failures=[x.get('name') for x in cases if x.find('failure') is not None or x.find('error') is not None]
    skipped=[x.get('name') for x in cases if x.find('skipped') is not None]
    node_ok=process.returncode==0 and len(cases)==263 and not failures and not skipped
    node_result={'tests':len(cases),'failures':failures,'skipped':skipped,
      'exitcode':process.returncode,'status':'PASS' if node_ok else 'NO_GO',
      'scope':'complete_controller_guard_and_endchain_unit_regressions'}
    unchanged=before==sources()
    folder=ROOT/'supabase/.temp'/('phase6e11-endchain-'+uuid.uuid4().hex)
    folder.mkdir(exist_ok=False)
    status='OFFLINE_PREPARATION_PASS' if result.wasSuccessful() and node_ok and unchanged else 'NO_GO'
    checks={'status':status,'tests':result.testsRun,'failures':[t.id() for t,_ in result.failures],
      'errors':[t.id() for t,_ in result.errors],'skipped':[t.id() for t,_ in result.skipped],
      'sources_unchanged':unchanged,'scope':'sequence_and_preregistration_unit_tests_only',
      'hosted_calls':0,'hosted_admitted':False,'full_chain_pass':False,'node_regressions':node_result}
    files={}
    for name,value in [('preregistration.json',plan()),('sequence.json',sequence),('checks.json',checks)]:
        files[name]=write(folder/name,value)
    manifest={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'sources':before,'files':files,'status':status,'hosted_admitted':False,
      'existing_hosted_budget_unchanged':128,'owner_approved_one_run_limit':1280,
      'full_query_ledger_compiled':False}
    seal=write(folder/'manifest.json',manifest)
    print(json.dumps({'folder':str(folder),'manifest_sha256':seal,'checks':checks,
      'sequence':validate_sequence(sequence)}))
    return 0 if status=='OFFLINE_PREPARATION_PASS' else 1

if __name__=='__main__':sys.exit(main())
