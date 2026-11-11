"""Fresh interpreter tests; never relax project guards for optional imports."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class BootstrapTests(unittest.TestCase):
    def child(self, before='', after='', isolated=True):
        source=Path(__file__).with_name('admission_trusted_loader.py').resolve()
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        script='''import pathlib,sys,json,hashlib,os,types
p=pathlib.Path(sys.argv[1]);raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()==sys.argv[2]
namespace={'__name__':'bootstrap_test','__file__':str(p)}
exec(compile(raw,str(p),'exec',dont_inherit=True),namespace)
''' + before + '''
try:
    result=namespace['bootstrap_reader_stdlib']()
except namespace['TrustedImportError'] as error:
    print(json.dumps({'blocked':str(error)}))
else:
''' + '\n'.join('    '+line for line in (after or "print(json.dumps(result))").splitlines())
        run=subprocess.run([sys.executable,*(['-I','-S'] if isolated else []),'-B','-c',
            script,str(source),digest],capture_output=True,timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        self.assertEqual(run.returncode,0,run.stderr.decode())
        return json.loads(run.stdout)

    def test_source_bootstrap_then_same_guard_rejects_optional_import(self):
        # Remove the Windows extension directory and registry name to reproduce
        # a Linux-absent optional dependency, without substituting any module.
        before="""sys.path[:]=[p for p in sys.path if pathlib.Path(p).name.lower()!='dlls']
sys.stdlib_module_names=frozenset(n for n in sys.stdlib_module_names if n!='_wmi')"""
        after="""assert '_wmi' not in sys.modules
assert [x['module'] for x in result['modules']]==['platform','uuid']
for row in result['modules']:
    module=sys.modules[row['module']]
    assert row['sha256']==hashlib.sha256(pathlib.Path(module.__file__).read_bytes()).hexdigest()
import tempfile
with tempfile.TemporaryDirectory() as temp:
    root=pathlib.Path(temp);target=root/namespace['PREFIX']/'bootstrap_fixture.py'
    target.parent.mkdir(parents=True);target.write_bytes(b'import uuid\\nVALUE=uuid.UUID(int=0).int\\n')
    loader=namespace['TrustedImports'](root,{namespace['PREFIX']+'bootstrap_fixture.py':hashlib.sha256(target.read_bytes()).hexdigest()})
    try:
        with loader:
            assert loader.module('bootstrap_fixture').VALUE==0
            loader.imported('_wmi')
    except namespace['TrustedImportError']:
        assert loader.failed
    else:
        raise AssertionError('unbound optional module escaped guard')
print(json.dumps(result))"""
        result=self.child(before,after)
        self.assertEqual(result['status'],'STDLIB_SOURCE_BOOTSTRAPPED')

    def test_preexisting_target_not_replaced(self):
        self.assertEqual(self.child('import platform')['blocked'],'stdlib_bootstrap_preexisting_target')

    def test_nonisolated_interpreter_rejected(self):
        self.assertEqual(self.child(isolated=False)['blocked'],'stdlib_bootstrap_fresh_isolated_interpreter')

    def test_external_search_path_rejected_before_execution(self):
        self.assertEqual(self.child('sys.path.append(os.getcwd())')['blocked'],'stdlib_bootstrap_search_origin')

    def test_external_cached_optional_module_rejected(self):
        result=self.child("sys.stdlib_module_names=frozenset(n for n in sys.stdlib_module_names if n!='_wmi')\nsys.modules['_wmi']=types.ModuleType('_wmi')")
        self.assertEqual(result['blocked'],'stdlib_bootstrap_external_cache')

    def test_custom_import_finder_rejected(self):
        self.assertEqual(self.child('sys.meta_path.insert(0,object())')['blocked'],'stdlib_bootstrap_import_hooks')

    def test_bootstrap_cannot_run_twice(self):
        result=self.child(after="""try:
    namespace['bootstrap_reader_stdlib']()
except namespace['TrustedImportError'] as error:
    print(json.dumps({'blocked':str(error)}))""")
        self.assertEqual(result['blocked'],'stdlib_bootstrap_reuse_or_active')


if __name__=='__main__':
    unittest.main()
