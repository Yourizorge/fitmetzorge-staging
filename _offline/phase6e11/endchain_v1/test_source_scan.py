import pathlib,unittest
from source_scan import check

class Tests(unittest.TestCase):
    def test_exact_retained_validation_literal_not_a_credential(self):
        name='_offline/phase6e11/access_v1/cli_check.py'
        raw=(pathlib.Path(__file__).resolve().parents[3]/name).read_bytes()
        check(name,raw)
        for path,value in [('wrong.py',raw),(name,raw+b' '),(name,raw+b' sbp_'+b'x'*40)]:
            with self.assertRaises(ValueError):check(path,value)
    def test_other_sources_remain_strict(self):
        for prefix in (b'sbp_',b'sb_secret_',b'ghp_'):
            with self.assertRaises(ValueError):check('source.py',prefix+b'a'*32)
        check('source.py',b'ordinary source')
if __name__=='__main__':unittest.main()
