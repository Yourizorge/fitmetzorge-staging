"""Pure error preservation; does not claim a native worker/PG execution."""
import io
import pathlib
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from quota_candidate_v1.runtime_parent_workflow import dispatch_reply


class DispatchTests(unittest.TestCase):
    def test_success_reply(self):
        stream = io.StringIO()
        dispatch_reply(types.SimpleNamespace(stdin=stream), {'rows': []})
        self.assertEqual(stream.getvalue(), '{"rows": []}\n')

    def test_first_error_is_exact_object_and_terminal(self):
        error = RuntimeError('original_failure')
        stream = io.StringIO()
        reached = []
        with self.assertRaises(RuntimeError) as caught:
            dispatch_reply(types.SimpleNamespace(stdin=stream), {'error': 'ci_query_failed'}, error)
            reached.append('later_child_complete')
        self.assertIs(caught.exception, error)
        self.assertEqual(reached, [])
        self.assertNotIn('original_failure', stream.getvalue())

    def test_lost_error_reply_preserves_original(self):
        class Broken:
            def write(self, value): raise BrokenPipeError('PRIVATE_REVIEW_SENTINEL')
        original = RuntimeError('original_commit_outcome_unknown')
        with self.assertRaises(RuntimeError) as caught:
            dispatch_reply(types.SimpleNamespace(stdin=Broken()), {'error': 'ci_query_failed'}, original)
        self.assertIs(caught.exception, original)
        self.assertEqual(original.__notes__, ['workflow_error_reply_secondary:BrokenPipeError'])

    def test_flush_failure_preserves_original(self):
        class Broken(io.StringIO):
            def flush(self): raise TimeoutError('PRIVATE_REVIEW_SENTINEL')
        original = RuntimeError('original_timeout')
        with self.assertRaises(RuntimeError) as caught:
            dispatch_reply(types.SimpleNamespace(stdin=Broken()), {}, original)
        self.assertIs(caught.exception, original)
        self.assertEqual(original.__notes__, ['workflow_error_reply_secondary:TimeoutError'])

    def test_no_original_preserves_pipe_failure(self):
        class Broken:
            def write(self, value): raise BrokenPipeError('closed')
        with self.assertRaises(BrokenPipeError): dispatch_reply(types.SimpleNamespace(stdin=Broken()), {})


if __name__ == '__main__':
    unittest.main()
