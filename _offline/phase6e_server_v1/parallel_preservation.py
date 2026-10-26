"""New scoped receipt; never rewrites the original strict preservation result."""
import hashlib,json,os,pathlib,subprocess,sys,uuid
from workday_preservation import BASELINE,DOCS,preserved_body
from ops import ROOT,disk,g

APPENDS=(
 'supabase/migrations/20261018070231_phase6e11_recovery_run_quota.sql text eol=lf',
 'docs/PHASE6E11_RECOVERY_RUN_AUTHORIZATION_20261018.md text eol=lf',
 'docs/PHASE6E11_PARALLEL_RUN_AUTHORIZATION_20261018.md text eol=lf',
 '_offline/phase6e11/endchain_v1/history_pin.json text eol=lf')

def attributes_preserved(old,current):
    before=old.replace('\r\n','\n')
    after=current.replace('\r\n','\n')
    return after==before+''.join(line+'\n' for line in APPENDS)

def inspect(baseline,read_current,read_original):
    unchanged=[];authorized=[];unexpected=[]
    for name,expected in baseline['retained'].items():
        raw=read_current(name)
        actual=hashlib.sha256(raw).hexdigest() if raw is not None else None
        if actual==expected:
            unchanged.append(name);continue
        if raw is None or name not in {*DOCS,'.gitattributes'}:
            unexpected.append(name);continue
        old=read_original(name)
        if hashlib.sha256(old).hexdigest()!=expected:
            unexpected.append(name);continue
        before=old.decode('utf8');current=raw.decode('utf8')
        allowed=attributes_preserved(before,current) if name=='.gitattributes' else preserved_body(before,current,DOCS[name])
        if not allowed:
            unexpected.append(name);continue
        authorized.append({'path':name,'before':expected,'after':actual,
            'scope':'four exact LF rules appended' if name=='.gitattributes' else 'existing current-status prefix and historical heading',
            'prior_content_preserved':True})
    return {'status':'PASS_SCOPED_PRESERVATION' if not unexpected else 'NO_GO',
        'total':len(baseline['retained']),'byte_identical':len(unchanged),
        'authorized':authorized,'unexpected':unexpected,'baseline_rewritten':False,
        'historical_checks_unchanged':True,'does_not_prove_hosted_data_preservation':True}

def main():
    folder=pathlib.Path(sys.argv[1]).resolve()
    if folder.parent!=ROOT/'supabase/.temp' or not folder.name.startswith('phase6e-server-ci-'):
        raise ValueError('output_scope')
    raw=disk(BASELINE).read_bytes();baseline=json.loads(raw)
    def current(name):
        path=disk(ROOT/name)
        return path.read_bytes() if path.is_file() else None
    def original(name):
        return subprocess.run([os.environ.get('FMZ_GIT','git'),'show',baseline['head']+':'+name],
            cwd=ROOT,capture_output=True,check=True).stdout
    result=inspect(baseline,current,original)
    result['baseline_sha256']=hashlib.sha256(raw).hexdigest()
    g.write(disk(folder/('parallel-preservation-'+uuid.uuid4().hex+'.json')),result)
    print(json.dumps(result))
    if result['status']=='NO_GO':raise ValueError('preservation_failed')

if __name__=='__main__':main()
