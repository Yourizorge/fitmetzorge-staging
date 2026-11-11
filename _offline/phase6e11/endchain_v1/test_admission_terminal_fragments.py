"""Execute exact recovery fragments through the real isolated reader child."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import uuid

import admission_terminal_process as process

READER = """import hashlib
def verify_exported_terminal(payloads,case,**kw):
    trusted_root=kw['trusted_root']
    # FRAGMENT
    return dict(status='CASE_TERMINAL_UNVERIFIED',case_name=case['case_name'],
        run_id=case['run_id'],case_sha256=hashlib.sha256(payloads['case-execution.json']).hexdigest(),
        missing=['numeric_originals_pending'],invalid=[],checks={},full_chain_admission=False,hosted_admitted=False)
"""


class RecoveryFragmentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='fragment-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.sources = {}
        here = Path(__file__).parent
        for name in ('admission_trusted_loader.py','admission_terminal_process.py'):
            self.put(process.PREFIX+name, (here/name).read_bytes())
        self.put(process.PACKAGE, b'')
        self.case = dict(case_name='normal', run_id=str(uuid.uuid4()))

    def put(self, name, raw):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        self.sources[name] = hashlib.sha256(raw).hexdigest()

    def inspect(self):
        path = self.root/process.SELF
        scope = {'__name__':'test_installed_parent', '__file__':str(path)}
        exec(compile(path.read_bytes(),str(path),'exec',dont_inherit=True),scope)
        return scope['inspect_terminal']({'case-execution.json':json.dumps(self.case).encode()},
            self.case, {'original.json':b'{}'}, head='a'*40,candidate='b'*64,run='123',
            expected_sources=self.sources,trusted_root=self.root)

    def no_go(self, report, reason=None):
        self.assertEqual(report['reader_process']['status'],'NO_GO')
        self.assertFalse(report['full_chain_admission'])
        if reason:
            self.assertIn(reason,report['missing'])

    def source(self, selected, *, alter='', caught=False):
        root = Path(__file__).resolve().parents[3]
        name, names = selected
        raw = (root / name).read_bytes()
        self.put(name, raw)
        body = """    import ast,pathlib
    path=pathlib.Path(trusted_root)/%r
    tree=ast.parse(path.read_bytes())
    found=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in %r]
    tree=ast.Module(body=found,type_ignores=[])
%s
    exec(compile(tree,str(path),'exec'),{'__name__':'offline_test'})
""" % (name, names, alter)
        if caught:
            body = '    try:\n' + '\n'.join('    '+line for line in body.splitlines()) + '\n    except Exception:\n        pass\n'
        reader = READER.replace('    # FRAGMENT', body)
        self.put(process.READER_PATH, reader.encode())
        return name, raw

    def test_all_four_exact_pinned_fragments_in_actual_child(self):
        for name, (_, selections) in process.RECOVERY_FRAGMENTS.items():
            for names in selections:
                with self.subTest(path=name, names=names):
                    self.source((name, names))
                    report = self.inspect()
                    self.assertEqual(report['reader_process']['status'], 'INSPECTED_UNVERIFIED')
                    self.assertFalse(report['full_chain_admission'])

    def test_constants_match_existing_recorder_and_reviewed_runner(self):
        import admission_budget_recovery_program as recorder
        from assembly_checks import run
        self.assertEqual(process.RECOVERY_FRAGMENTS, run.RECOVERY_FRAGMENTS)
        self.assertEqual({Path(n).name:h for n,(h,_) in process.RECOVERY_FRAGMENTS.items()}, recorder.PINS)

    def test_candidate_repin_cannot_admit_changed_recovery_body(self):
        name = process.PREFIX+'control_recovery.py'
        _, raw = self.source((name, ('replace_setup','recover')))
        self.put(name, raw+b'\n# different reviewed revision required\n')
        self.no_go(self.inspect())

    def test_wrong_selection_or_extra_code_is_sticky_even_when_caught(self):
        name = process.PREFIX+'control_recovery.py'
        for names, alteration in ((('recover',), ''),
                (('replace_setup','recover'), "    tree.body.append(ast.parse('injected=1').body[0])")):
            with self.subTest(names=names, alteration=alteration):
                self.source((name, names), alter=alteration, caught=True)
                self.no_go(self.inspect(), 'unsupported_or_unbound_replay')


if __name__ == '__main__':
    unittest.main()
