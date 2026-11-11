"""Pure local negatives for the portable runner; no process/socket execution."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from assembly_checks import run as r


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'dep.py').write_bytes(b'# synthetic fixture\n')
        self.row = dict(path='dep.py',sha256=r.sha((self.root/'dep.py').read_bytes()),bytes=20)

    def manifest(self, rows=None):
        raw = json.dumps(dict(format='portable-assembly-source-v1',files=rows or [self.row])).encode()
        (self.root/'sources.json').write_bytes(raw)
        return r.sha(raw)

    def test_exact_source_bytes_verified(self):
        expected=self.manifest()
        _, sources=r.verify_manifest(self.root,'sources.json',expected)
        self.assertEqual(sources,{'dep.py':self.row['sha256']})

    def test_manifest_pin_cannot_be_omitted_or_substituted(self):
        self.manifest()
        for value in (None,'','g'*64,'0'*64):
            with self.subTest(value=value), self.assertRaises(ValueError):
                r.verify_manifest(self.root,'sources.json',value)

    def test_changed_source_is_rejected_before_import(self):
        expected=self.manifest()
        (self.root/'dep.py').write_bytes(b'raise RuntimeError("must not execute")\n')
        with self.assertRaisesRegex(ValueError,'source_hash'):
            r.verify_manifest(self.root,'sources.json',expected)

    def test_missing_fresh_clone_dependency_is_not_a_pass(self):
        expected=self.manifest([{**self.row,'path':'missing_dependency.py'}])
        with self.assertRaises(FileNotFoundError):
            r.verify_manifest(self.root,'sources.json',expected)

    def test_duplicate_and_self_entries_rejected(self):
        for rows in ([self.row,self.row],[{**self.row,'path':'sources.json'}]):
            with self.subTest(rows=rows):
                expected=self.manifest(rows)
                with self.assertRaisesRegex(ValueError,'duplicate_or_self'):
                    r.verify_manifest(self.root,'sources.json',expected)

    def test_bool_size_not_numeric_evidence(self):
        expected=self.manifest([{**self.row,'bytes':True}])
        with self.assertRaisesRegex(ValueError,'manifest_row'):
            r.verify_manifest(self.root,'sources.json',expected)

    def test_duplicate_json_key_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate_json_key'):
            r.decode(b'{"a":1,"a":2}')

    def test_paths_and_link_aliases_rejected(self):
        for name in ('../dep.py','/dep.py','C:/dep.py','folder\\dep.py','./dep.py'):
            with self.subTest(name=name), self.assertRaises(ValueError): r.read(self.root,name)
        with patch.object(Path,'is_symlink',return_value=True):
            with self.assertRaisesRegex(ValueError,'source_link'):r.read(self.root,'dep.py')

    def test_source_origin_and_hash_are_both_required(self):
        module=types.SimpleNamespace(__name__='synthetic',__file__=str(self.root/'dep.py'))
        self.assertEqual(r.check_origin(module,self.root,{'dep.py':self.row['sha256']}),'dep.py')
        with self.assertRaisesRegex(ValueError,'module_hash'):r.check_origin(module,self.root,{})
        other=self.root/'other';other.mkdir()
        with self.assertRaisesRegex(ValueError,'module_origin'):r.check_origin(module,other,{})

    def test_conflicting_test_environment_rejected(self):
        with patch.dict(os.environ,{'A_RECOVERY_SOURCE_ROOT':str(self.root)}):
            with self.assertRaisesRegex(ValueError,'test_environment_root'):
                r.configure_environment(r.SOURCE_ROOT)

    def test_historical_code_cannot_execute(self):
        code=compile('pass','/repo/assembly_checks/historical/old.py','exec')
        with self.assertRaisesRegex(ValueError,'historical_execution_forbidden'):
            r.pure_guard('exec',(code,))

    def test_process_and_network_are_not_pure(self):
        for event in r.DENIED_EVENTS:
            with self.subTest(event=event),self.assertRaisesRegex(RuntimeError,'pure_tests_forbidden'):
                r.pure_guard(event,())

    def test_actual_fixture_inventory_is_four_plus_48_no_policy_copy(self):
        original=r.decode(r.read(r.SOURCE_ROOT,r.CHECKS+'fixture_pins.json'))
        pairs=r.approved_byte_pairs(r.SOURCE_ROOT)
        rows={}
        for path, expected in original['policy'].items():
            raw=r.read(r.SOURCE_ROOT,path)
            rows[path]=pairs.get(path,dict(path=path,sha256=expected,bytes=len(raw)))
        for path, expected in original['historical'].items():
            name=r.CHECKS+'historical/'+path
            rows[name]=dict(path=name,sha256=expected,bytes=len(r.read(r.SOURCE_ROOT,name)))
        # Fixture-only context uses independently pinned definitions, not a self-repinned manifest.
        manifest=dict(format='portable-assembly-source-v2',files=list(rows.values()))
        pins=dict(format='portable-assembly-fixtures-v2',historical=original['historical'],
                  policy={p:rows[p] for p in original['policy']})
        r.verify_fixtures(r.SOURCE_ROOT,pins,manifest)
        self.assertEqual((len(pins['historical']),len(pins['policy'])),(4,48))
        self.assertFalse((r.SOURCE_ROOT/r.CHECKS/'policy').exists())
        changed={**pins,'historical':{**pins['historical']}}
        changed['historical'][next(iter(changed['historical']))]='0'*64
        with self.assertRaisesRegex(ValueError,'fixture_v2_inventory'):
            r.verify_fixtures(r.SOURCE_ROOT,changed,manifest)

    def test_full_selection_is_explicit_and_external_suites_are_separate(self):
        selection=r.decode(r.read(r.SOURCE_ROOT,r.CHECKS+'selection.json'))
        self.assertEqual(selection['full_expected_tests'],452)
        self.assertEqual(len(selection['full']),23)
        self.assertNotIn('assembly_checks.test_runner',selection['full'])
        for entry in selection['separate_external_suites']:
            self.assertFalse(entry['allowed_in_pure_runner'])
            self.assertNotIn(entry['name'],selection['full'])

    def test_all_19_dependencies_are_declared_and_present(self):
        data=r.decode(r.read(r.SOURCE_ROOT,r.CHECKS+'dependency_needed.json'))
        self.assertEqual(len(data['files']),19)
        for row in data['files']:
            self.assertTrue(row['required_by_portable_source_manifest'])
            self.assertEqual(r.sha(r.read(r.SOURCE_ROOT,row['path'])),row['sha256'])

    def test_default_recovery_paths_are_repository_relative_without_env(self):
        file=r.SOURCE_ROOT/r.PREFIX/'test_admission_budget_recovery_program.py'
        with patch.dict(os.environ,{},clear=True):
            spec=importlib.util.spec_from_file_location('_portable_recovery_defaults',file)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertEqual(module.ROOT,r.SOURCE_ROOT)
        self.assertEqual(module.RUNTIME,r.SOURCE_ROOT/r.PREFIX/'quota_candidate_v1')

    def test_new_test_defaults_have_no_machine_paths(self):
        for name in ('test_admission_budget_recovery_program.py','test_admission_budget_root_runtime.py',
                     'test_admission_budget_bootstrap_prefix.py','test_admission_budget_bootstrap_checkpoint.py'):
            raw=r.read(r.SOURCE_ROOT,r.PREFIX+name)
            self.assertNotIn(b'C:/Users/',raw)
            self.assertNotIn(b'agent-d-quota-candidate',raw)


if __name__=='__main__':unittest.main()
