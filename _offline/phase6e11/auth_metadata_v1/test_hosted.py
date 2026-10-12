"""Exercise the actual read-only adapter's registration gate, without a socket."""
import importlib.util,pathlib,sys,types,unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('auth_metadata_native_runner',pathlib.Path(__file__).with_name('hosted.py'))
hosted=importlib.util.module_from_spec(spec);spec.loader.exec_module(hosted)

class Admission(unittest.TestCase):
    def run_query(self,sql):
        Transaction=hosted.m.stream.t.old.s.Transaction
        tx=object.__new__(Transaction)
        tx.transaction={'read_only':'on'};tx.began=True;tx.connection_pid=42;tx.commands_bound=0
        tx.status=lambda:2
        tx.raw=types.SimpleNamespace(conn=True,lib=types.SimpleNamespace(PQbackendPID=lambda _:42))
        tx.ledger=types.SimpleNamespace(queries=1,event=lambda *a,**kw:None)
        with patch.object(Transaction.__mro__[1],'command',return_value=[['metadata']]):
            return tx.command(sql,'test')
    def test_original_rejected(self):
        with self.assertRaisesRegex(Exception,'unregistered_readonly_query'):self.run_query(hosted.m.p.jit.META_SQL)
    def test_exact_query_registered(self):
        self.assertEqual(self.run_query(hosted.tagged_metadata(hosted.m.p.jit.META_SQL)),[['metadata']])
    def test_payload_unchanged(self):
        original=hosted.m.p.jit.META_SQL
        self.assertTrue(hosted.tagged_metadata(original).endswith(original))

if __name__=='__main__':unittest.main()
