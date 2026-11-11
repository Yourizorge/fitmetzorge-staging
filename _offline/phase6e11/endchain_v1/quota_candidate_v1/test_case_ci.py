"""Readiness must fail before bootstrap, SQL, Auth, or a prepared PASS."""
import pathlib
import unittest
from unittest import mock
from quota_candidate_v1 import case_ci as c
from quota_candidate_v1.compiler import CandidateStop
from admission_budget import CASES


class EntryTests(unittest.TestCase):
    def test_exact_main_case_names_and_no_ready_claim(self):
        self.assertEqual(c.CASE_NAMES,('normal',*CASES));self.assertFalse(c.READY)

    def test_every_case_uses_actual_source_admission_before_bootstrap(self):
        for case in c.CASE_NAMES:
            gate=mock.Mock();bootstrap=mock.Mock()
            with mock.patch('quota_candidate_v1.runtime_case_entry.source_preflight',
                    side_effect=CandidateStop('case_entry_root_bound_incomplete')) as preflight:
                with self.assertRaisesRegex(CandidateStop,'case_entry_root_bound_incomplete'):
                    c.run(gate,[],case,bootstrap=bootstrap)
                preflight.assert_called_once_with(gate,case)
            bootstrap.assert_not_called();self.assertEqual(gate.mock_calls,[])

    def test_preinstall_owner_creation_checks_actual_source_model_not_ready_flag(self):
        for case in c.CASE_NAMES:
            gate=mock.Mock()
            with mock.patch('quota_candidate_v1.runtime_case_entry.source_preflight',
                    side_effect=CandidateStop('case_entry_root_bound_incomplete')) as preflight:
                with self.assertRaisesRegex(CandidateStop,'case_entry_root_bound_incomplete'):
                    c.prepare_execution(gate,case)
                preflight.assert_called_once_with(gate,case)
            self.assertEqual(gate.mock_calls,[])

    def test_all_new_package_files_are_explicitly_bundled(self):
        own=pathlib.Path(c.__file__).parent
        expected={c._PREFIX+p.name for p in own.iterdir() if p.is_file() and p.suffix in ('.py','.mjs','.json','.in','.md')}
        self.assertTrue(expected <= set(c.SOURCES));self.assertEqual(len(c.SOURCES),len(set(c.SOURCES)))

    def test_old_component_aliases_are_not_silently_admitted(self):
        with self.assertRaisesRegex(CandidateStop,'case_name_denied'):c.run(mock.Mock(),[],'mid_route_a',bootstrap=mock.Mock())


if __name__=='__main__':unittest.main()
