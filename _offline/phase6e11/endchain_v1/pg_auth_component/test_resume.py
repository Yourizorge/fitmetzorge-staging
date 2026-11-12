"""Candidate-shaped fresh-process tests; no Docker, SQL or network execution."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

from . import entry, inventory

PREFIX = inventory.PREFIX
COSTS = PREFIX+'quota_candidate_v1/runtime_registered_costs.py'
OWN_ROOT = Path(__file__).resolve().parents[4]
CHECKOUT = Path(os.environ.get('PG_COMPONENT_TEST_CHECKOUT', str(OWN_ROOT))).resolve()

CHILD = r'''
import hashlib,json,os,pathlib,sys
def audit(event,args):
    if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.exec','os.posix_spawn'):
        raise RuntimeError('test_external_operation_denied')
sys.addaudithook(audit)
root=pathlib.Path(sys.argv[1]);mode=sys.argv[2]
sys.path.extend(sys.argv[3:])
sys.path.insert(0,str(root/'_offline/phase6e11/endchain_v1'))
import psycopg
def denied_connection(*args,**kwargs):raise RuntimeError('test_database_connection_denied')
psycopg.connect=denied_connection
psycopg.Connection.connect=denied_connection
psycopg.AsyncConnection.connect=denied_connection
from pg_auth_component import entry
out=pathlib.Path(os.environ['RUNNER_TEMP'])/'fmz-db41-evidence'
pin=hashlib.sha256((out/entry.HANDOFF).read_bytes()).hexdigest()
if mode=='missing':
    # Only the host OS check is replaced. Imports and diagnostic persistence are real.
    entry.environment=lambda env:None
    raise SystemExit(entry.main(['--state-sha256',pin]))
import admission_ci
from case_stack_v1.ci import _source_check,_check_origin
from pg_auth_component import parent,inventory
names=inventory.register(admission_ci)
gate,migrations,run_id=entry.restore(admission_ci,pin)
os.environ['GITHUB_WORKSPACE']=str(pathlib.Path(os.environ['RUNNER_TEMP'])/'checkout-peer')
native_sources=gate.sources
if os.name=='nt':
    gate.sources=pathlib.Path('\\\\?\\'+str(gate.sources))
    os.environ['GITHUB_WORKSPACE']='\\\\?\\'+os.environ['GITHUB_WORKSPACE']
_source_check(gate,names,receipt='test-candidate-source.json')
gate.sources=native_sources
_check_origin(gate,entry,inventory,parent,admission_ci)
assert len(migrations)==45 and gate.result['migrations_applied']==0
assert 'quota_candidate_v1.runtime_registered_costs' in sys.modules
import types
pending=list(sys.modules.values());seen=set();loaded={}
expected=json.loads((out/'candidate.json').read_bytes())['sources']
checkout=pathlib.Path(os.environ['PG_COMPONENT_ORIGINAL_CHECKOUT']).resolve()
while pending:
    module=pending.pop()
    if not isinstance(module,types.ModuleType) or id(module) in seen:continue
    seen.add(id(module));name=getattr(module,'__file__',None)
    if not name:continue
    path=pathlib.Path(name).resolve()
    if path.is_relative_to(checkout) and not any(path.is_relative_to(pathlib.Path(p).resolve()) for p in sys.argv[3:]):
        raise RuntimeError('test_checkout_import_denied')
    if path.is_relative_to(root.resolve()):
        relative=path.relative_to(root.resolve()).as_posix()
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        assert expected[relative]==digest
        loaded[relative]=digest
        pending.extend(v for v in vars(module).values() if isinstance(v,types.ModuleType))
print(json.dumps({'status':'IMPORT_RESTORE_SOURCE_PASS','actual_pg':False,'parent_run_called':False,
    'loaded_project_sources':loaded,'checkout_imports':False}))
'''


def disk(path):
    path=Path(path).absolute()
    return Path('\\\\?\\'+str(path)) if os.name=='nt' and not str(path).startswith('\\\\?\\') else path


class ResumeTests(unittest.TestCase):
    def fixture(self, temp, missing):
        import admission_ci
        sources=temp/'fmz-db41-sources'
        out=temp/'fmz-db41-evidence'
        for path in (sources,out,temp/'fmz-db41-stack',temp/'checkout-peer'):path.mkdir()
        hashes={}
        for name in inventory.paths(admission_ci,CHECKOUT):
            origin=OWN_ROOT/name if name in inventory.OWN and disk(OWN_ROOT/name).is_file() else CHECKOUT/name
            raw=disk(origin).read_bytes()
            if missing and name==COSTS:continue
            target=disk(sources/name);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            peer=disk(temp/'checkout-peer'/name);peer.parent.mkdir(parents=True,exist_ok=True);peer.write_bytes(raw)
            hashes[name]=hashlib.sha256(raw).hexdigest()
        manifest={'sources':hashes,'blob':'b'*40,'sha256':'c'*64}
        raw=json.dumps(manifest).encode();(out/'candidate.json').write_bytes(raw)
        state={'format':'pg-auth-component-handoff-v1','manifest_sha256':hashlib.sha256(raw).hexdigest(),
            'migrations':sorted(n for n in hashes if n.startswith('supabase/migrations/')),
            'run_id':str(uuid.uuid4()),'result':{'commit':'a'*40,'run_id':'123',
            'candidate_sha256':'c'*64,'migrations_applied':0,'status':'NO_GO',
            'full_chain_admission':False,'hosted_admitted':False}}
        (out/entry.HANDOFF).write_text(json.dumps(state))
        return sources,out

    def child(self,missing):
        import psycopg
        with tempfile.TemporaryDirectory(prefix='pg-resume-',dir=str(disk(tempfile.gettempdir()))) as folder:
            temp=Path(folder[4:] if os.name=='nt' and folder.startswith('\\\\?\\') else folder)
            sources,out=self.fixture(temp,missing)
            # Checkout contains original tested overlay bytes in CI. A local patch
            # composition has only authored component files over the trusted checkout.
            env={k:v for k,v in os.environ.items() if k in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP')}
            env.update(GITHUB_ACTIONS='true',GITHUB_REPOSITORY='Yourizorge/fitmetzorge-staging',
                GITHUB_REF='refs/heads/main',GITHUB_RUN_ATTEMPT='1',GITHUB_WORKSPACE=str(CHECKOUT),
                GITHUB_SHA='a'*40,GITHUB_RUN_ID='123',CANDIDATE_BLOB='b'*40,
                CANDIDATE_SHA256='c'*64,RUNNER_TEMP=str(temp))
            env['PG_COMPONENT_ORIGINAL_CHECKOUT']=str(CHECKOUT)
            deps=[str(Path(psycopg.__file__).resolve().parent.parent)]
            command=[sys.executable,'-I','-B','-c',CHILD,str(sources),'missing' if missing else 'fixed',*deps]
            result=subprocess.run(command,env=env,capture_output=True,timeout=30)
            detail=json.loads(result.stdout) if result.stdout else None
            failure=out/'pg-component-entry-failure.json'
            original=json.loads(failure.read_bytes()) if failure.exists() else None
            return result.returncode,detail,original,result.stderr.decode()

    def test_missing_dependency_original_importerror_saved_without_result(self):
        code,value,original,stderr=self.child(True)
        self.assertEqual(code,1,stderr)
        self.assertEqual(value['error_class'],'ImportError')
        self.assertEqual(value['failure_phase'],'parent_import')
        self.assertEqual(original['original_error']['error_class'],'ImportError')
        self.assertEqual(original['original_error']['phase'],'parent_import')
        self.assertFalse(original['full_chain_admission'])

    def test_fixed_candidate_import_restore_source_before_platform(self):
        code,value,original,stderr=self.child(False)
        self.assertEqual(code,0,stderr)
        self.assertEqual(value['status'],'IMPORT_RESTORE_SOURCE_PASS')
        self.assertFalse(value['actual_pg']);self.assertFalse(value['parent_run_called'])
        self.assertIsNone(original)

    def test_inventory_contains_transitive_costs(self):
        self.assertIn(COSTS,inventory.additions())

    def test_diagnostic_never_exports_exception_text(self):
        error=ImportError('PRIVATE_REVIEW_SENTINEL',name='quota_candidate_v1')
        value=entry.diagnostic(error,'parent_import')
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL',json.dumps(value))
        self.assertEqual(value['error_class'],'ImportError')

    def test_diagnostic_failure_preserves_primary(self):
        import builtins
        original=builtins.__import__
        def denied(name,*args,**kwargs):
            if name=='admission_ci':raise ImportError('PRIVATE_REVIEW_SENTINEL')
            return original(name,*args,**kwargs)
        import io
        from contextlib import redirect_stdout
        stream=io.StringIO()
        with patch.object(entry,'environment'),patch.object(builtins,'__import__',side_effect=denied), \
             patch.object(entry,'save_early_failure',side_effect=OSError('PRIVATE_REVIEW_SENTINEL')),redirect_stdout(stream):
            code=entry.main(['--state-sha256','a'*64])
        value=json.loads(stream.getvalue())
        self.assertEqual(code,1);self.assertEqual(value['error_class'],'ImportError')
        self.assertEqual(value['diagnostic_error_class'],'OSError')
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL',stream.getvalue())

if __name__=='__main__':unittest.main()
