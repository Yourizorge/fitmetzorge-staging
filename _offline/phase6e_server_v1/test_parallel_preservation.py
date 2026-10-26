import hashlib,unittest
from parallel_preservation import APPENDS,attributes_preserved,inspect

class Preservation(unittest.TestCase):
    def test_only_four_exact_appends(self):
        old='prior\n'
        current=old+''.join(x+'\n' for x in APPENDS)
        self.assertTrue(attributes_preserved(old,current))
        self.assertTrue(attributes_preserved(old,current.replace('\n','\r\n')))
        for bad in (current+'extra\n',current.replace('prior','changed'),current.replace('eol=lf','eol=crlf'),current.replace(APPENDS[0]+'\n','')):
            self.assertFalse(attributes_preserved(old,bad))
    def test_unexpected_source_change_and_removal_fail(self):
        old={'source.cjs':b'original','missing.md':b'keep'}
        baseline={'retained':{name:hashlib.sha256(raw).hexdigest() for name,raw in old.items()}}
        result=inspect(baseline,lambda name:b'changed' if name=='source.cjs' else None,old.__getitem__)
        self.assertEqual(result['status'],'NO_GO')
        self.assertEqual(result['unexpected'],list(old))
        self.assertFalse(result['baseline_rewritten'])
    def test_prior_hash_must_match_even_for_authorized_path(self):
        old=b'prior\n';current=old+''.join(x+'\n' for x in APPENDS).encode()
        baseline={'retained':{'.gitattributes':hashlib.sha256(old).hexdigest()}}
        self.assertEqual(inspect(baseline,lambda _:current,lambda _:b'other')['status'],'NO_GO')
        result=inspect(baseline,lambda _:current,lambda _:old)
        self.assertEqual(result['status'],'PASS_SCOPED_PRESERVATION')
        self.assertTrue(result['does_not_prove_hosted_data_preservation'])

if __name__=='__main__':unittest.main()
