import unittest
import auth_arm as new
class ArmTests(unittest.TestCase):
    def setUp(self):
        self.ids={r:'69000000-0000-4000-8000-'+str(i).zfill(12) for i,r in enumerate(new.audit.g.ROLES,1)}
        self.args=('69000000-0000-4000-8000-000000000010',self.ids,'69000000-0000-4000-8000-000000000011','a_member','verify')
    def test_atomic_single_statement_and_same_body(self):
        old=new.audit.arm(*self.args);v=new.render(*self.args)
        body=old.split('DO $arm$ BEGIN\n',1)[1].rsplit('END $arm$; COMMIT;',1)[0]
        self.assertIn(body,v);self.assertTrue(v.startswith('DO $arm$ BEGIN'))
        self.assertNotIn('COMMIT',v);self.assertIn("set_config('lock_timeout','1s',true)",v)
    def test_unregistered_role_rejected(self):
        with self.assertRaises(ValueError):new.render(*self.args[:3],'owner','verify')
    def test_unregistered_operation_rejected(self):
        with self.assertRaises(ValueError):new.render(*self.args[:4],'delete_account')
    def test_original_remains_unchanged(self):
        self.assertTrue(new.audit.arm(*self.args).startswith('BEGIN; SET LOCAL'))
if __name__=='__main__':unittest.main()
