"""Offline entry contracts; no database, CLI, fetch, pip or Docker execution."""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = pathlib.Path(os.environ.get('CASE_STACK_SOURCE_ROOT', str(HERE.parent)))
sys.path.insert(0, str(SOURCE))
package = types.ModuleType('case_entry_test_package')
package.__path__ = [str(SOURCE / 'case_stack_v1')]
sys.modules[package.__name__] = package
spec = importlib.util.spec_from_file_location(package.__name__ + '.ci', HERE / 'ci.py')
c = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = c
spec.loader.exec_module(c)


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.temp_path = pathlib.Path(self.temp.name).resolve()
        self.env = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'Yourizorge/fitmetzorge-staging',
            'GITHUB_REF': 'refs/heads/main', 'GITHUB_RUN_ATTEMPT': '1',
            'GITHUB_SHA': 'a'*40, 'GITHUB_RUN_ID': '123456789',
            'CANDIDATE_BLOB': 'c'*40, 'CANDIDATE_SHA256': 'b'*64,
            'CASE_NAME': 'normal', 'GITHUB_WORKSPACE': str(self.temp_path / 'checkout'),
            'RUNNER_TEMP': str(self.temp_path)}
        self.adapter = types.SimpleNamespace(READY=True,
            CASE_NAMES=('normal',) + tuple('fault_' + str(i) for i in range(14)),
            SOURCES=(c.PREFIX + 'quota_candidate_v1/case_ci.py',),
            prepare_execution=Mock(), run=Mock())
        self.gate = types.SimpleNamespace(temp=self.temp_path, serial=0)
        for attr, name in (('out', 'fmz-db41-evidence'), ('work', 'fmz-db41-stack'),
                           ('sources', 'fmz-db41-sources')):
            value = self.temp_path / name
            value.mkdir()
            setattr(self.gate, attr, value)
        self.gate.result = dict.fromkeys(c.RESULT_FIELDS, False)
        self.gate.result.update(status='NO_GO', phase='candidate', run_id='123456789',
            commit='a'*40, cli='2.117.0', cli_sha256='d'*64, migrations_applied=0,
            hosted_requests=0, external_ai_calls=0, case_name='normal', cli_profile='local_app',
            candidate_sha256='b'*64, admission_components={})
        self.migrations = ['supabase/migrations/%014d_fixture.sql' % i for i in range(45)]
        self.manifest = {'blob': 'c'*40, 'sha256': 'b'*64,
                         'sources': {name: 'd'*64 for name in self.migrations}}
        (self.gate.out / 'candidate.json').write_text(json.dumps(self.manifest))

    def save(self, name, value):
        with (self.gate.out / name).open('x') as f:
            json.dump(value, f)
            f.flush()
            os.fsync(f.fileno())

    def state(self):
        raw = (self.gate.out / 'candidate.json').read_bytes()
        value = {'format': 'case-preinstall-handoff-v1', 'manifest_sha256': c._sha(raw),
                 'migrations': self.migrations, 'result': self.gate.result, 'serial': 0}
        self.save(c.HANDOFF, value)
        return c._sha((self.gate.out / c.HANDOFF).read_bytes())

    def execute(self, root=None):
        root = types.SimpleNamespace(install_platform=Mock()) if root is None else root
        with patch.object(c, '_parser_dependency'), patch.object(c, '_check_origin'), \
             patch.dict(sys.modules, {'admission_budget_root_runtime': root}):
            return c._execute(self.gate, self.migrations, 'normal', self.adapter)

    def test_environment_unchanged_and_exact_inventory(self):
        before = dict(self.env)
        self.assertEqual(c._environment(self.env, self.adapter)[0], 'normal')
        self.assertEqual(before, self.env)
        self.adapter.SOURCES += ('_offline/../outside.py',)
        with self.assertRaises(ValueError): c._environment(self.env, self.adapter)

    def test_bad_environment_and_not_ready_stop(self):
        for key, value in [('CASE_NAME', '../secret'), ('GITHUB_RUN_ATTEMPT', '2'),
                           ('GITHUB_SHA', 'bad'), ('CANDIDATE_BLOB', 'not-a-sha')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                c._environment({**self.env, key: value}, self.adapter)
        self.adapter.READY = False
        with patch.object(c, '_adapter', return_value=self.adapter), patch.dict(os.environ, self.env), \
             patch.dict(sys.modules, {'admission_ci': None}), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(c.main([]), 1)
        self.assertEqual(json.loads(out.getvalue())['status'], 'ADAPTER_NOT_READY')

    def test_help_has_no_adapter_import(self):
        with patch.object(c, '_adapter', side_effect=AssertionError('import')), \
             contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as error:
            c.main(['--help'])
        self.assertEqual(error.exception.code, 0)

    def test_preflight_failure_never_installs_or_runs(self):
        root = types.SimpleNamespace(install_platform=Mock())
        self.adapter.prepare_execution.side_effect = ValueError('incomplete_bound')
        with self.assertRaisesRegex(ValueError, 'incomplete_bound'): self.execute(root)
        root.install_platform.assert_not_called()
        self.adapter.run.assert_not_called()

    def test_missing_observer_does_not_use_thirteen_or_zero(self):
        self.gate.install = Mock()
        with self.assertRaisesRegex(ValueError, 'case_platform_observer_missing'):
            self.execute(types.SimpleNamespace())
        self.gate.install.assert_not_called()
        self.adapter.run.assert_not_called()

    def test_same_prepared_owner_and_order(self):
        events = []
        owner = types.SimpleNamespace(ledger=object())
        def prepare(*args): events.append('prepare'); return owner
        def install(gate, *, ledger):
            events.append('install')
            self.assertIs(gate, self.gate)
            self.assertIs(ledger, owner.ledger)
        def run(gate, migrations, name, *, bootstrap, prepared):
            events.append('run')
            self.assertIs(prepared, owner)
            self.assertIs(bootstrap, c.bootstrap)
            self.assertEqual(migrations, self.migrations)
            return {'component': 'not-real-PG-proof'}
        self.adapter.prepare_execution.side_effect = prepare
        self.adapter.run.side_effect = run
        self.execute(types.SimpleNamespace(install_platform=install))
        self.assertEqual(events, ['prepare', 'install', 'run'])
        self.adapter.prepare_execution.assert_called_once_with(self.gate, 'normal')

    def test_failed_install_never_starts_case(self):
        root = types.SimpleNamespace(install_platform=Mock(side_effect=OSError('failed')))
        with self.assertRaises(OSError): self.execute(root)
        self.assertFalse(self.gate.result['case_execution_started'])
        self.adapter.run.assert_not_called()

    def test_parser_is_only_the_pinned_process_not_platform(self):
        self.gate.command = Mock()
        self.gate.install = Mock()
        protocol = types.SimpleNamespace(parser=Mock())
        old_path = list(sys.path)
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), old_path))
        with patch.object(c, '_check_origin'), patch.dict(sys.modules, {'sql_protocol': protocol}):
            c._parser_dependency(self.gate)
        args = self.gate.command.call_args
        self.assertEqual(args.args[0], 'case-parser-install')
        self.assertEqual(args.args[1][-2:], ['pglast==7.20', 'psycopg[binary]==3.2.10'])
        self.assertEqual(args.kwargs, {'timeout': 120})
        self.gate.install.assert_not_called()
        protocol.parser.assert_called_once()

    def test_handoff_exec_is_isolated_no_credentials_or_second_process_retry(self):
        class Gate:
            save = lambda _, name, value: self.save(name, value)
        gate = Gate()
        gate.__dict__.update(vars(self.gate))
        with patch.dict(os.environ, {**self.env, 'GH_READ_TOKEN': 'PRIVATE', 'PYTHONPATH': 'PRIVATE'}), \
             patch.object(c.os, 'execve', side_effect=OSError('noexec')) as execute:
            with self.assertRaises(OSError): c._handoff(gate, self.migrations)
        execute.assert_called_once()
        args = execute.call_args.args
        self.assertEqual(args[1][1:3], ['-B', '-I'])
        self.assertNotIn('GH_READ_TOKEN', args[2])
        self.assertNotIn('PYTHONPATH', args[2])
        self.assertNotIn('PRIVATE', (gate.out / c.HANDOFF).read_text())
        self.assertEqual(args[1][-1], c._sha((gate.out / c.HANDOFF).read_bytes()))

    def test_handoff_forbids_started_serial_and_extra_live_state(self):
        for attr, value in [('serial', 1), ('container', 'unexpected')]:
            gate = types.SimpleNamespace(**vars(self.gate))
            setattr(gate, attr, value)
            with patch.object(c.os, 'execve') as execute, self.assertRaises(ValueError):
                c._handoff(gate, self.migrations)
            execute.assert_not_called()

    def restore(self, digest):
        class Gate:
            def __init__(self): raise AssertionError('constructor/refetch forbidden')
        with patch.dict(os.environ, self.env), \
             patch.object(c, '__file__', str(self.gate.sources / c.PREFIX / 'case_stack_v1/ci.py')):
            return c._restore(types.SimpleNamespace(Gate=Gate), digest)

    def test_restore_has_no_constructor_refetch_or_ledger(self):
        gate, migrations = self.restore(self.state())
        self.assertEqual(migrations, self.migrations)
        self.assertEqual(vars(gate), vars(self.gate))

    def test_restore_rejects_tampered_state_manifest_identity_and_migrations(self):
        digest = self.state()
        with self.assertRaisesRegex(ValueError, 'handoff_hash'): self.restore('0'*64)
        path = self.gate.out / c.HANDOFF
        original = json.loads(path.read_text())
        for kind in ('identity', 'migrations', 'serial', 'secret'):
            value = json.loads(json.dumps(original))
            if kind == 'identity': value['result']['commit'] = '0'*40
            if kind == 'migrations': value['migrations'] = value['migrations'][:-1]
            if kind == 'serial': value['serial'] = 1
            if kind == 'secret': value['result']['credential'] = 'PRIVATE'
            path.write_text(json.dumps(value))
            with self.subTest(kind=kind), self.assertRaises(ValueError): self.restore(c._sha(path.read_bytes()))
        path.write_text(json.dumps(original))
        (self.gate.out / 'candidate.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'handoff_manifest'): self.restore(c._sha(path.read_bytes()))

    def test_origin_rejects_checkout_module(self):
        self.gate.bind_modules = Mock()
        wrong = types.SimpleNamespace(__file__=str(self.temp_path / 'checkout/x.py'))
        with patch.dict(os.environ, self.env), self.assertRaisesRegex(ValueError, 'candidate_origin'):
            c._check_origin(self.gate, wrong)
        self.gate.bind_modules.assert_not_called()

    def test_origin_rejects_transitive_checkout_module(self):
        self.gate.bind_modules = Mock()
        own = types.SimpleNamespace(__file__=str(self.gate.sources / 'own.py'))
        stale = types.ModuleType('stale_candidate_dependency')
        stale.__file__ = str(self.temp_path / 'checkout/dependency.py')
        with patch.dict(os.environ, self.env), patch.dict(sys.modules, {stale.__name__: stale}), \
             self.assertRaisesRegex(ValueError, 'checkout_module_loaded'):
            c._check_origin(self.gate, own)
        self.gate.bind_modules.assert_not_called()

    def test_source_bytes_verified_before_receipt(self):
        self.gate.save = Mock()
        source = self.gate.sources / 'example.py'
        source.write_bytes(b'fixture = 1\n')
        self.manifest['sources'] = {'example.py': c._sha(source.read_bytes())}
        (self.gate.out / 'candidate.json').write_text(json.dumps(self.manifest))
        binding = types.SimpleNamespace(HARNESS={}, verify_all=Mock(return_value={'status': 'test-only'}))
        with patch.dict(os.environ, self.env), patch.dict(sys.modules, {'ci_source_binding': binding}):
            c._source_check(self.gate, {'example.py'}, receipt='source.json')
            binding.verify_all.assert_called_once()
            source.write_bytes(b'fixture = 2\n')
            self.gate.save.reset_mock()
            with self.assertRaisesRegex(ValueError, 'candidate_bytes'):
                c._source_check(self.gate, {'example.py'}, receipt='changed.json')
            self.gate.save.assert_not_called()

    def test_harness_must_be_inside_candidate_inventory(self):
        self.gate.save = Mock()
        self.manifest['sources'] = {}
        (self.gate.out / 'candidate.json').write_text(json.dumps(self.manifest))
        binding = types.SimpleNamespace(HARNESS={'required_runner.py': 'd'*64}, verify_all=Mock())
        with patch.dict(os.environ, self.env), patch.dict(sys.modules, {'ci_source_binding': binding}), \
             self.assertRaisesRegex(ValueError, 'sources_missing'):
            c._source_check(self.gate, set(), receipt='source.json')
        binding.verify_all.assert_not_called()
        self.gate.save.assert_not_called()

    def test_fresh_isolated_interpreter_restores_candidate_without_checkout_import(self):
        folder = self.gate.sources / c.PREFIX
        package_dir = folder / 'case_stack_v1'
        package_dir.mkdir(parents=True)
        entry = package_dir / 'ci.py'
        entry.write_bytes((HERE / 'ci.py').read_bytes())
        (package_dir / '__init__.py').write_text('')
        (package_dir / 'bootstrap.py').write_text(
            'SOURCES=()\ndef bootstrap(*a,**k): raise AssertionError("no DB")\n'
            'def require(v,c):\n if not v: raise ValueError(c)\n')
        (folder / 'admission_module_binding.py').write_bytes((SOURCE / 'admission_module_binding.py').read_bytes())
        digest = self.state()
        code = ('import runpy,sys,types,json; m=runpy.run_path(sys.argv[1]); '
                'G=type("G",(),{"__init__":lambda s: (_ for _ in ()).throw(AssertionError("ctor"))}); '
                'g,n=m["_restore"](types.SimpleNamespace(Gate=G),sys.argv[2]); '
                'print(json.dumps({"source":m["__file__"],"count":len(n),"serial":g.serial}))')
        result = subprocess.run([sys.executable, '-B', '-I', '-c', code, str(entry), digest],
            env={**os.environ, **self.env, 'PYTHONPATH': 'deliberately-ignored'},
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {'source': str(entry), 'count': 45, 'serial': 0})

    def test_final_save_does_not_mask_original(self):
        self.gate.save = Mock(side_effect=OSError('PRIVATE_SAVE'))
        admission = types.SimpleNamespace(EXTRA=set(), app=types.SimpleNamespace(
            previous=types.SimpleNamespace(prior=types.SimpleNamespace(old=types.SimpleNamespace(EXTRA=set())))))
        with patch.dict(os.environ, self.env), patch.object(c, '_adapter', return_value=self.adapter), \
             patch.dict(sys.modules, {'admission_ci': admission}), \
             patch.object(c, '_restore', return_value=(self.gate, self.migrations)), \
             patch.object(c, '_source_check'), patch.object(c, '_check_origin'), \
             patch.object(c, '_execute', side_effect=ValueError('PRIVATE_PRIMARY')), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(c.main(['--candidate-state-sha256', '0'*64]), 1)
        value = json.loads(out.getvalue())
        self.assertEqual(value['error_type'], 'ValueError')
        self.assertEqual(value['result_write_error_type'], 'OSError')
        self.assertFalse(value['full_chain_admission'])
        self.assertNotIn('PRIVATE', out.getvalue())


if __name__ == '__main__':
    unittest.main()
