"""Candidate-only import tests; no database, network or CI admission claim."""
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

import admission_ci as admission

ROOT = pathlib.Path(__file__).resolve().parents[3]
CHECKOUT = pathlib.Path(os.environ.get('GITHUB_WORKSPACE', ROOT)).resolve()
IMPORT = r'''
import json,pathlib,socket,sys,traceback
root=pathlib.Path(sys.argv[1]).resolve()
def denied(*args,**kwargs):
    raise RuntimeError('network_disabled_in_import_test')
socket.create_connection=denied
socket.socket.connect=denied
sys.path.insert(0,str(root/'_offline/phase6e11/endchain_v1'))
for dependency in json.loads(sys.argv[3]):sys.path.append(dependency)
try:
    import admission_ci
    if sys.argv[2]=='budget':
        import admission_budget_register
        report=admission_budget_register.assemble()
        print(json.dumps({'status':'ASSEMBLED_NOT_ADMITTED',
            'hosted_admitted':report['hosted_admitted']}))
        sys.exit(0)
    paths=[]
    for cls in admission_ci.Gate.__mro__:
        if cls is object:continue
        method=next(m for m in vars(cls).values() if hasattr(m,'__code__'))
        paths.append(pathlib.Path(method.__code__.co_filename).resolve().relative_to(root).as_posix())
    print(json.dumps({'status':'IMPORTED','classes':len(paths),'paths':paths}))
except FileNotFoundError as error:
    print(json.dumps({'status':'MISSING','path':pathlib.Path(error.filename).resolve().relative_to(root).as_posix()}))
    sys.exit(2)
except Exception as error:
    print(json.dumps({'status':'BLOCKED','error_class':type(error).__name__,
        'frames':[{'file':pathlib.Path(f.filename).name,'line':f.lineno,'function':f.name}
                  for f in traceback.extract_tb(error.__traceback__)]}))
    sys.exit(3)
'''


class PackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = set(admission.app.previous.prior.old.old.EXTRAS) | admission.app.previous.prior.old.EXTRA
        cls.temporary = tempfile.TemporaryDirectory(prefix='fmz-candidate-import-')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.copy = pathlib.Path(cls.temporary.name)
        for name in sorted(cls.paths):
            # This copies only the explicit candidate inventory, never a checkout.
            source = ROOT / name
            target = cls.copy / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def execute(self, overrides=None, *, operation='import'):
        env = dict(os.environ, GITHUB_ACTIONS='true',
            GITHUB_REPOSITORY='Yourizorge/fitmetzorge-staging', GITHUB_REF='refs/heads/main',
            GITHUB_WORKSPACE=str(CHECKOUT))
        env.update(overrides or {})
        from sql_protocol import parser
        parser()  # Load the existing pinned PG17 parser before locating its dependency directory.
        spec = importlib.util.find_spec('pglast')
        dependencies = [str(pathlib.Path(spec.origin).parent.parent)] if spec else []
        result = subprocess.run([sys.executable, '-I', '-B', '-c', IMPORT, str(self.copy),
            operation, json.dumps(dependencies)],
            cwd=self.copy, env=env, text=True, capture_output=True, timeout=60, check=False)
        self.assertEqual(result.stderr, '')
        return result.returncode, json.loads(result.stdout)

    def test_every_actual_gate_ancestor_is_in_explicit_candidate(self):
        for cls in admission.Gate.__mro__:
            if cls is object:
                continue
            method = next(m for m in vars(cls).values() if hasattr(m, '__code__'))
            relative = pathlib.Path(method.__code__.co_filename).resolve().relative_to(ROOT).as_posix()
            self.assertIn(relative, self.paths)
        self.assertTrue(set(admission.CI_INHERITANCE_SOURCES) <= self.paths)

    def test_fresh_candidate_imports_full_gate_with_only_pinned_frozen_bodies_in_checkout(self):
        code, value = self.execute()
        self.assertEqual(code, 0, value)
        self.assertEqual(value['status'], 'IMPORTED')
        self.assertEqual(value['classes'], 7)
        self.assertEqual(len(set(value['paths'])), 7)
        self.assertTrue(set(value['paths']) <= self.paths)

    def test_budget_assembly_has_complete_explicit_candidate_sources(self):
        code, value = self.execute(operation='budget')
        self.assertEqual(code, 0, value)
        self.assertEqual(value, {'status':'ASSEMBLED_NOT_ADMITTED','hosted_admitted':False})

    def test_missing_pinned_frozen_bodies_do_not_fall_back_to_actual_checkout(self):
        code, value = self.execute({'GITHUB_WORKSPACE': str(self.copy)})
        self.assertEqual(code, 3, value)
        self.assertEqual(value['status'], 'BLOCKED')
        self.assertEqual(value['error_class'], 'ValueError')

    def test_foreign_ci_scope_cannot_select_the_checkout_for_frozen_bodies(self):
        code, value = self.execute({'GITHUB_REPOSITORY': 'example/unrelated'})
        self.assertEqual(code, 3, value)
        self.assertEqual(value['status'], 'BLOCKED')

    def test_candidate_layout_preserves_the_original_checkout_for_frozen_pins(self):
        env = dict(os.environ, GITHUB_ACTIONS='true',
            GITHUB_REPOSITORY='Yourizorge/fitmetzorge-staging', GITHUB_REF='refs/heads/main',
            GITHUB_WORKSPACE=str(CHECKOUT))
        env.pop('PYTHONPATH', None)
        env.pop('PYTHONHOME', None)
        target = self.copy / '_offline/phase6e11/endchain_v1/test_admission_packaging.py'
        result = subprocess.run([sys.executable, '-B', str(target),
            'PackagingTests.test_fresh_candidate_imports_full_gate_with_only_pinned_frozen_bodies_in_checkout'],
            cwd=self.copy, env=env, capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_inherited_module_reproduces_failure_before_any_connection(self):
        for name in ('_offline/phase6e11/controller_v1/ci.py', '_offline/phase6e11/ci42/runner.py'):
            with self.subTest(name=name):
                path = self.copy / name
                held = path.with_suffix('.held')
                path.rename(held)
                try:
                    code, value = self.execute()
                    self.assertEqual(code, 2, value)
                    self.assertEqual(value, {'status': 'MISSING', 'path': name})
                finally:
                    held.rename(path)


if __name__ == '__main__':
    unittest.main()
