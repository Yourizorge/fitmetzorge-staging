"""Offline original-byte replay regressions; synthetic HTTP, no Auth/SQL proof."""
import copy
import json
import pathlib
import tempfile
import types
import unittest

from quota_candidate_v1 import runtime_exported_http as v
from quota_candidate_v1 import runtime_http as producer


RUN = 'ec75cc79-c246-4c83-8055-fbfc3d23738c'
BINDING = 'b'*64


def snapshot(*, attempted=False, terminal=False, sealed=False, status=None):
    return dict(format='case-auth-http-v1', sealed=sealed, rows=[dict(
        ordinal=1, role='a_member', operation='verify', safety=False,
        attempted=attempted, terminal=terminal, status=status)])


class ReplayTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        self.sources = {}
        for name in (v.SELF, *v.PRODUCERS):
            raw = (pathlib.Path(v.__file__).parent/pathlib.PurePosixPath(name).name).read_bytes()
            target = self.root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            self.sources[name] = v.digest(raw)
        self.composition = types.SimpleNamespace(quota=dict(root=self.root,
            manifest=dict(sources=self.sources), binding=dict(run_id=RUN, binding_sha=BINDING)))
        self.journal = producer.HttpJournal(types.SimpleNamespace(out=self.root), self.composition)
        self.originals = {}

    def export(self):
        self.originals = {v.JOURNAL: self.journal.path.read_bytes(),
                          v.RECEIPT: v.canonical(self.journal.receipt())}

    def verify(self):
        return v.verify_exported_http(self.originals, run_id=RUN, binding_sha=BINDING,
            expected_sources=self.sources, trusted_root=self.root)

    def complete(self):
        self.journal.accept(snapshot())
        self.journal.accept(snapshot(attempted=True, status=200))
        self.journal.accept(snapshot(attempted=True, terminal=True, status=200, sealed=True))
        self.export()

    def alter_terminal(self, key, value):
        terminal = json.loads(self.originals[v.RECEIPT])
        terminal[key] = value
        self.originals[v.RECEIPT] = v.canonical(terminal)

    def rewrite(self, snapshots):
        raw = self.originals[v.JOURNAL].splitlines(keepends=True)[0]
        for state in snapshots:
            raw += v.canonical(dict(previous_sha256=v.digest(raw), snapshot=state)) + b'\n'
        self.originals[v.JOURNAL] = raw
        self.alter_terminal('journal_ref', dict(path=v.JOURNAL, sha256=v.digest(raw), bytes=len(raw)))

    def test_real_producer_bytes_replay_without_fake_context_or_case_pass(self):
        self.complete()
        value = self.verify()
        self.assertEqual(value['status'], 'HTTP_OBSERVATIONS_REPLAYED')
        self.assertTrue(value['all_responses_terminal'])
        self.assertEqual(value['observed_attempts'], 1)
        for key in ('case_terminal_verified', 'identity_verified', 'revocation_proven',
                    'worker_termination_proven', 'deletion_admitted', 'full_chain_admission', 'hosted_admitted'):
            self.assertIs(value[key], False)
        self.assertEqual(value['additional_sql_commands'], 0)

    def test_http_headers_without_complete_body_remain_unknown_when_sealed(self):
        self.journal.accept(snapshot(attempted=True, status=200, sealed=True))
        self.export()
        value = self.verify()
        self.assertFalse(value['all_responses_terminal'])
        self.assertEqual(value['unknown_attempts'], 1)
        self.assertEqual(value['unresolved_intents'], 1)

    def test_unattempted_intent_is_not_a_lost_response_or_completed_request(self):
        self.journal.accept(snapshot(sealed=True))
        self.export()
        value = self.verify()
        self.assertEqual(value['unknown_attempts'], 0)
        self.assertEqual(value['observed_attempts'], 0)
        self.assertEqual(value['unresolved_intents'], 1)
        self.assertFalse(value['all_responses_terminal'])

    def test_empty_sealed_prefix_does_not_prove_any_requests(self):
        self.journal.accept(dict(format='case-auth-http-v1', sealed=True, rows=[]))
        self.export()
        value = self.verify()
        self.assertTrue(value['all_responses_terminal'])
        self.assertEqual(value['observed_intents'], 0)
        self.assertFalse(value['case_terminal_verified'])

    def test_missing_original_is_rejected(self):
        self.complete()
        del self.originals[v.JOURNAL]
        with self.assertRaisesRegex(ValueError, 'missing_or_oversize'):
            self.verify()

    def test_raw_source_drift_rejected(self):
        self.complete()
        path = self.root/v.PRODUCERS[1]
        path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError, 'source_hash'):
            self.verify()

    def test_source_inventory_is_not_taken_from_terminal(self):
        self.complete()
        del self.sources[v.PRODUCERS[1]]
        with self.assertRaisesRegex(ValueError, 'source_missing'):
            self.verify()

    def test_collector_must_match_its_actual_loaded_bytes(self):
        self.complete()
        raw = (self.root/v.SELF).read_bytes()+b'\n'
        (self.root/v.SELF).write_bytes(raw)
        self.sources[v.SELF] = v.digest(raw)
        with self.assertRaisesRegex(ValueError, 'loaded_collector'):
            self.verify()

    def test_new_outer_hash_does_not_repair_broken_chain(self):
        self.complete()
        raw = self.originals[v.JOURNAL].replace(b'"previous_sha256":"', b'"previous_sha256":"0', 1)
        self.originals[v.JOURNAL] = raw
        self.alter_terminal('journal_ref', dict(path=v.JOURNAL, sha256=v.digest(raw), bytes=len(raw)))
        with self.assertRaisesRegex(ValueError, 'hash_chain'):
            self.verify()

    def test_attempt_retraction_rejected_even_with_rehashed_chain(self):
        self.complete()
        self.rewrite([snapshot(attempted=True), snapshot()])
        with self.assertRaisesRegex(ValueError, 'attempt_retracted'):
            self.verify()

    def test_changed_intent_rejected(self):
        self.complete()
        changed = snapshot(attempted=True)
        changed['rows'][0]['role'] = 'b_member'
        self.rewrite([snapshot(), changed])
        with self.assertRaisesRegex(ValueError, 'intent_changed'):
            self.verify()

    def test_changed_known_status_rejected(self):
        self.complete()
        self.rewrite([snapshot(attempted=True, status=200), snapshot(attempted=True, status=204)])
        with self.assertRaisesRegex(ValueError, 'status_changed'):
            self.verify()

    def test_terminal_retraction_rejected(self):
        self.complete()
        self.rewrite([snapshot(attempted=True, status=200, terminal=True),
                      snapshot(attempted=True, status=200)])
        with self.assertRaisesRegex(ValueError, 'terminal_changed'):
            self.verify()

    def test_sealed_prefix_cannot_be_extended(self):
        self.complete()
        self.rewrite([snapshot(sealed=True), snapshot(sealed=False)])
        with self.assertRaisesRegex(ValueError, 'sealed_changed'):
            self.verify()

    def test_unknown_prefix_cannot_start_another_request(self):
        self.complete()
        state = snapshot(attempted=True)
        row = copy.deepcopy(state['rows'][0])
        row['ordinal'] = 2
        state['rows'].append(row)
        self.rewrite([state])
        with self.assertRaisesRegex(ValueError, 'unresolved_prefix'):
            self.verify()

    def test_claimed_zero_unknown_does_not_override_original(self):
        self.journal.accept(snapshot(attempted=True, sealed=True))
        self.export()
        self.alter_terminal('unknown_attempts', 0)
        with self.assertRaisesRegex(ValueError, 'terminal_mismatch'):
            self.verify()

    def test_duplicate_json_keys_rejected(self):
        self.complete()
        self.originals[v.RECEIPT] = self.originals[v.RECEIPT][:-1]+b',"run_id":"x"}'
        with self.assertRaisesRegex(ValueError, 'duplicate_key'):
            self.verify()

    def test_boolean_cannot_replace_numeric_counter(self):
        self.complete()
        self.alter_terminal('unknown_attempts', False)
        with self.assertRaisesRegex(ValueError, 'terminal_mismatch'):
            self.verify()

    def test_raw_reference_cannot_retarget_another_file(self):
        self.complete()
        ref = json.loads(self.originals[v.RECEIPT])['journal_ref']
        ref['path'] = 'other.ledger.txt'
        self.alter_terminal('journal_ref', ref)
        with self.assertRaisesRegex(ValueError, 'terminal_mismatch'):
            self.verify()

    def test_case_and_candidate_binding_cannot_be_substituted(self):
        self.complete()
        with self.assertRaisesRegex(ValueError, 'header_binding'):
            v.verify_exported_http(self.originals, run_id=RUN, binding_sha='c'*64,
                expected_sources=self.sources, trusted_root=self.root)

    def test_oversize_journal_rejected_before_json_parse(self):
        self.complete()
        self.originals[v.JOURNAL] = b'x'*(v.MAX_JOURNAL+1)
        with self.assertRaisesRegex(ValueError, 'missing_or_oversize'):
            self.verify()

    def test_added_secret_field_rejected(self):
        self.complete()
        state = snapshot()
        state['rows'][0]['token'] = 'synthetic-not-a-real-token'
        self.rewrite([state])
        with self.assertRaisesRegex(ValueError, 'exported_http_row'):
            self.verify()

    def test_artifact_python_is_ignored_not_imported(self):
        self.complete()
        self.originals['runtime_http.py'] = b'raise AssertionError("must not execute")'
        self.assertEqual(self.verify()['status'], 'HTTP_OBSERVATIONS_REPLAYED')

    def test_original_case_alias_rejected(self):
        self.complete()
        self.originals[v.JOURNAL.upper()] = self.originals[v.JOURNAL]
        with self.assertRaisesRegex(ValueError, 'original_alias'):
            self.verify()


if __name__ == '__main__':
    unittest.main()
