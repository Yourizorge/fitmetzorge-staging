import hashlib,pathlib,tempfile,types,unittest
from ci_source_binding import verify,verify_all

class Binding(unittest.TestCase):
    def test_stale_module_fails_before_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);a=root/'checkout';b=root/'candidate';a.mkdir();b.mkdir()
            (a/'m.py').write_bytes(b'value=1\r\n');(b/'m.py').write_bytes(b'value=1\n')
            modules={'m':types.SimpleNamespace(__file__=str(a/'m.py'))}
            sources={'m.py':hashlib.sha256((b/'m.py').read_bytes()).hexdigest()}
            self.assertEqual(verify(a,b,sources,modules)['status'],'LOADED_SOURCE_BINDING_PASS')
            (a/'m.py').write_bytes(b'value=2\n')
            with self.assertRaisesRegex(ValueError,'loaded_source_mismatch'):verify(a,b,sources,modules)
    def test_unbound_and_modified_candidate_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp);(p/'m.py').write_bytes(b'x=1')
            with self.assertRaisesRegex(ValueError,'candidate_module_changed'):
                verify(p,p,{'m.py':'0'*64},{'m':types.SimpleNamespace(__file__=str(p/'m.py'))})
            with self.assertRaisesRegex(ValueError,'loaded_sources_missing'):verify(p,p,{}, {})
    def test_unimported_and_unregistered_helpers_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);a=root/'checkout';b=root/'candidate';a.mkdir();b.mkdir()
            (a/'helper.py').write_bytes(b'x=1\r\n');(b/'helper.py').write_bytes(b'x=1\n')
            sources={'helper.py':hashlib.sha256((b/'helper.py').read_bytes()).hexdigest()}
            self.assertEqual(len(verify_all(a,b,sources,harness={})['sources']),1)
            (a/'helper.py').write_bytes(b'x=2\n')
            with self.assertRaisesRegex(ValueError,'loaded_source_mismatch'):verify_all(a,b,sources,harness={})
    def test_candidate_only_is_explicit_not_missing_dependency_waiver(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);a=root/'checkout';b=root/'candidate';a.mkdir();b.mkdir()
            (b/'helper.py').write_bytes(b'x=1')
            sources={'helper.py':hashlib.sha256(b'x=1').hexdigest()}
            with self.assertRaisesRegex(ValueError,'dependency_missing'):verify_all(a,b,sources,harness={})
            self.assertEqual(verify_all(a,b,sources,harness={},candidate_only={'helper.py'})['sources']['helper.py']['distribution'],'explicit_candidate_only')
            (b/'helper.py').write_bytes(b'x=2')
            with self.assertRaisesRegex(ValueError,'candidate_module_changed'):verify_all(a,b,sources,harness={},candidate_only={'helper.py'})
    def test_harness_pin_is_required_even_outside_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp);(p/'base.py').write_bytes(b'x=1')
            with self.assertRaisesRegex(ValueError,'harness_changed'):verify_all(p,p,{},harness={'base.py':'0'*64})

if __name__=='__main__':unittest.main()
