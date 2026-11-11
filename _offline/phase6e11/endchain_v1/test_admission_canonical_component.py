"""Synthetic originals through genuine installed readers; never live PG proof."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

import test_admission_canonical_child as fixture

HERE = Path(__file__).resolve().parent
SELF = '_offline/phase6e11/endchain_v1/admission_canonical_component.py'


class ComponentTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.CanonicalChildTests(methodName='runTest')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        f = self.fixture
        installed = Path(fixture.__file__).resolve().parents[3]
        # Reuse receipt DATA construction only. Restore the unmodified installed
        # reader: no fixture reader or fake case/root enters the new component.
        f.put(fixture.process.READER_PATH, (installed/fixture.process.READER_PATH).read_bytes())
        f.put(fixture.process.PACKAGE, (installed/fixture.process.PACKAGE).read_bytes())
        artificial = fixture.P+'canonical_fixture_originals.py'
        del f.sources[artificial]
        (f.root/artificial).unlink()
        f.put(SELF, (HERE/'admission_canonical_component.py').read_bytes())
        candidate = f.save('candidate.json', f.candidate)
        f.summary['candidate_manifest_sha256'] = candidate['sha256']
        f.save(fixture.audit.NAME, f.summary)
        del f.originals['unrelated-not-replayed.json']
        scope = {'__name__': '_reviewed_component_test', '__file__': str(f.root/SELF)}
        exec(compile((f.root/SELF).read_bytes(), str(f.root/SELF), 'exec', dont_inherit=True), scope)
        self.component = SimpleNamespace(**scope)
        self.namespace = scope
        self.kw = dict(source_commit='a'*40, candidate_sha256='b'*64, ci_run='123',
                       run_id=f.case['run_id'], expected_sources=f.sources, trusted_root=f.root)

    def call(self, **changes):
        return self.component.inspect_canonical(self.fixture.originals, **{**self.kw, **changes})

    def test_real_installed_reader_44_sets_without_case_or_root(self):
        self.assertNotIn('case-execution.json', self.fixture.originals)
        self.assertFalse(any(n.startswith('root-original-') for n in self.fixture.originals))
        before = {name: sys.modules.get(name) for name in (
            'admission_canonical_replay', 'admission_terminal_process', 'admission_budget_prefix_originals')}
        report = self.call()
        self.assertEqual(report['reader_process']['status'], 'INSPECTED_UNVERIFIED', report)
        self.assertEqual(report['canonical_replay']['invocation_count'], 44)
        self.assertEqual(report['status'], 'CANONICAL_COMPONENT_UNVERIFIED')
        self.assertIsNone(report['total_sql_commands'])
        self.assertIsNone(report['hosted_equivalent_commands'])
        for key in ('READY', 'full_chain_admission', 'hosted_admitted', 'numeric_bound_complete', 'actual_old_history_claim'):
            self.assertIs(report[key], False)
        self.assertEqual(report['reader_process']['limits']['wait_seconds'], 60)
        self.assertEqual(report['reader_process']['limits']['reap_seconds'], 5)
        self.assertTrue(report['reader_process']['wait']['wait_completed'])
        for name, value in before.items(): self.assertIs(sys.modules.get(name), value)

    def test_cross_case_uuid_denied(self):
        report = self.call(run_id=str(uuid.uuid4()))
        self.assertEqual(report['reader_process']['status'], 'NO_GO')
        self.assertIsNone(report['canonical_replay'])

    def test_external_commit_candidate_and_run_must_match(self):
        for changes in (dict(source_commit='d'*40), dict(candidate_sha256='e'*64), dict(ci_run='124')):
            with self.subTest(changes=changes):
                self.assertEqual(self.call(**changes)['reader_process']['status'], 'NO_GO')

    def test_reserved_uuid_never_dispatches_child(self):
        for run in ('6f8c8909-9b79-4011-a9d1-db5e23c6b6c1', '11a909f4-7113-424a-aa4b-ce9964720a3e'):
            with self.assertRaises(ValueError): self.call(run_id=run)

    def test_missing_or_extra_original_denied(self):
        f = self.fixture
        raw = f.originals.pop('case-stack-catalog-before41-intent.json')
        with self.assertRaises(ValueError): self.call()
        f.originals['case-stack-catalog-before41-intent.json'] = raw
        f.originals['case-execution.json'] = b'{}'
        with self.assertRaises(ValueError): self.call()

    def test_rehashed_unpaid_frame_cannot_pass(self):
        f = self.fixture
        refs = f.summary['invocations'][0]['original_refs']
        rows = [json.loads(line) for line in f.originals[refs['ledger']['path']].splitlines()]
        rows[2], rows[3] = rows[3], rows[2]
        refs['ledger'] = f.save_raw(refs['ledger']['path'], f.chain(rows))
        receipt = json.loads(f.originals[refs['receipt']['path']])
        receipt['ledger_ref'] = {k:refs['ledger'][k] for k in ('path', 'sha256')}
        refs['receipt'] = f.save(refs['receipt']['path'], receipt)
        f.save(fixture.audit.NAME, f.summary)
        self.assertEqual(self.call()['reader_process']['status'], 'NO_GO')

    def test_artifact_code_is_only_data(self):
        f = self.fixture
        ref = f.summary['invocations'][0]['original_refs']['ledger']
        sentinel = f.root/'should-not-exist'
        f.originals[ref['path']] = ("open("+repr(str(sentinel))+",'w').write('bad')").encode()
        self.assertEqual(self.call()['reader_process']['status'], 'NO_GO')
        self.assertFalse(sentinel.exists())

    def test_tampered_installed_reader_denied_even_with_new_digest(self):
        f = self.fixture
        f.put(fixture.process.READER_PATH, b'raise RuntimeError("unreviewed")\n')
        with self.assertRaises(ValueError): self.call()

    def test_changed_transitive_source_denied(self):
        path = self.fixture.root/(fixture.P+'cli_predispatch/pending.py')
        path.write_bytes(path.read_bytes()+b'\n# changed\n')
        self.assertEqual(self.call()['reader_process']['status'], 'NO_GO')

    def test_member_limit_and_parent_output_claim_validation(self):
        f = self.fixture
        f.originals['candidate.json'] = b' ' * 1_400_001
        with self.assertRaises(ValueError): self.call()
        report = self.component.result(self.component.identity('a'*40, 'b'*64, '123', f.case['run_id']))
        report['READY'] = True
        with self.assertRaises(ValueError): self.component.check_report(report, report['binding'])

    def test_total_original_bytes_never_silently_truncated(self):
        for name in list(self.fixture.originals)[:12]:
            self.fixture.originals[name] = b' ' * 1_400_000
        with self.assertRaises(ValueError): self.call()

    def test_duplicate_json_summary_rejected(self):
        raw = self.fixture.originals[fixture.audit.NAME]
        self.fixture.originals[fixture.audit.NAME] = b'{"format":"unexpected",'+raw[1:]
        with self.assertRaises(ValueError): self.call()

    def test_unconfirmed_reap_retains_private_directory(self):
        helper = self.component.support(self.fixture.root, self.fixture.sources)
        directories = []
        def wait(command, environment, cwd):
            directories.append(Path(cwd))
            return dict(wait_completed=False, accepted=False, error_class='OSError')
        helper.wait_child = wait
        with patch.dict(self.namespace, {'support': lambda *args: helper}):
            report = self.call()
        self.assertEqual(report['reader_process']['status'], 'NO_GO')
        self.assertEqual(report['reader_process']['private_cleanup'], 'deferred_unconfirmed_reap')
        self.assertTrue(directories[0].is_dir())
        self.assertTrue((directories[0]/'request.json').is_file())
        # No child was launched by this double, so test-owned cleanup is safe.
        self.addCleanup(__import__('shutil').rmtree, directories[0])

    def test_failed_wait_never_accepts_response(self):
        helper = self.component.support(self.fixture.root, self.fixture.sources)
        helper.wait_child = lambda *args: dict(wait_completed=True, accepted=False, timed_out=True, returncode=-9)
        with patch.dict(self.namespace, {'support': lambda *args: helper}): report = self.call()
        self.assertEqual(report['reader_process']['status'], 'NO_GO')
        self.assertEqual(report['reader_process']['private_cleanup'], 'completed')


if __name__ == '__main__': unittest.main()
