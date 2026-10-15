"""Keep the original baseline; allow only the explicit current-status doc prefixes."""
import hashlib,json,os,pathlib,subprocess,sys,uuid
from ops import ROOT,disk,g
BASELINE=ROOT/'supabase/.temp/phase6e11-controller-590796353d7344778ee8efb69454065c/before.json'
DOCS={
 'docs/ARCHITECTURE.md':'## 6E-11 Historical Request Binding (28 September 2026)',
 'docs/MASTER_BUILD_PLAN.md':'## Historical: 6E-11 M42 Installed / Hosted Edge Configuration Blocked',
 'docs/TEST_MATRIX.md':'## 6E-11 Historical Request/M42 Evidence'}

def preserved_body(old,current,marker):
    before=old.replace('\r\n','\n').splitlines(keepends=True)
    after=current.replace('\r\n','\n')
    if len(before)<4 or not before[2].startswith('## '):return False
    if after.count(marker+'\n')!=1 or not after.startswith(''.join(before[:2])):return False
    prefix,tail=after.split(marker+'\n')
    return len(prefix)>len(''.join(before[:2])) and tail==''.join(before[3:])

def main():
    folder=pathlib.Path(sys.argv[1]).resolve()
    if folder.parent!=ROOT/'supabase/.temp' or not folder.name.startswith('phase6e-server-ci-'):raise ValueError('output_scope')
    raw=disk(BASELINE).read_bytes();baseline=json.loads(raw);unchanged=[];authorized=[];unexpected=[]
    for name,expected in baseline['retained'].items():
        path=disk(ROOT/name)
        actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual==expected:unchanged.append(name);continue
        if name not in DOCS or actual is None:unexpected.append(name);continue
        old=subprocess.run([os.environ.get('FMZ_GIT','git'),'show',baseline['head']+':'+name],
          cwd=ROOT,capture_output=True,check=True).stdout
        # Preserve terminal blank lines; the ordinary git helper strips them.
        original=old.decode('utf8') if hashlib.sha256(old).hexdigest()==expected else None
        if original is None or not preserved_body(original,path.read_text(),DOCS[name]):unexpected.append(name);continue
        authorized.append({'path':name,'before':expected,'after':actual,'prior_body_preserved':True,'scope':'current-status prefix and historical heading only'})
    result={'status':'PASS_SCOPED_DOCUMENTATION_ONLY' if not unexpected and len(authorized)==3 else 'NO_GO',
      'baseline_sha256':hashlib.sha256(raw).hexdigest(),'baseline_rewritten':False,'total':len(baseline['retained']),
      'byte_identical':len(unchanged),'authorized_documentation':authorized,'unexpected':unexpected,
      'prior_strict_check':'NO_GO for three authorized docs; historical result unchanged'}
    g.write(disk(folder/('workday-preservation-'+uuid.uuid4().hex+'.json')),result)
    print(json.dumps(result))
    if result['status']=='NO_GO':raise ValueError('preservation_failed')
if __name__=='__main__':main()
