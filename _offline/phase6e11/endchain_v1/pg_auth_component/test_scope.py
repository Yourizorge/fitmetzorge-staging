"""Strict existing validators plus local protocol doubles, not PG evidence."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_admission_auth_runtime_profile as fixtures
from . import lifecycle, scope as m


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.gate=SimpleNamespace(out=Path(self.temp.name),save=lambda *a:None)
        p=patch.object(lifecycle.binding,'verify',return_value={'unit_only':True})
        p.start(); self.addCleanup(p.stop)
        self.runtime=object.__new__(m.NativeRuntime); self.runtime.environment='disposable_ci'
        self.container=object.__new__(lifecycle.AuthContainer); self.container.create_attempted=False
        self.isolation={'pg_system_identifier':'123','database_oid':5}
        self.calls=[]; self.connections=[]; self.failure=None; self.changed=None
        self.count=0
        def connect():
            self.count+=1; index=self.count
            conn=SimpleNamespace(closed=False)
            def close(): conn.closed=True
            def execute(sql,args=None):
                phase=next((p for p,s in m.profile.PLAN if s.replace('$1','%s')==sql), sql)
                if sql=='ROLLBACK': phase='rollback'
                if sql==m.profile.META:
                    phase='witness_metadata' if index==2 else ('after_metadata' if any(p=='restrict' for p in self.calls) else 'before_metadata')
                self.calls.append(phase)
                if phase==self.failure: raise TimeoutError('original_dispatch')
                if phase.endswith('_metadata'):
                    value=fixtures.metadata(pid=11 if index==2 else 10,
                        restricted=phase!='before_metadata',readonly=index==2)
                    if self.changed: self.changed(phase,value)
                    rows=[{'value':value}]
                elif sql==m.producer.PRIVILEGES.replace('$1','%s'):
                    rows=fixtures.privileges(index==1)
                else: rows=[]
                return SimpleNamespace(description=bool(rows),fetchall=lambda: rows)
            conn.close, conn.execute=close, execute
            self.connections.append(conn); return conn
        self.runtime.connect=connect

    def call(self):return m.reduce_profile(self.gate,self.runtime,self.isolation,self.container)

    def test_exact_reduction_ten_commands_original_witnesses(self):
        record=self.call()
        self.assertEqual(len(self.calls),10)
        self.assertTrue(all(c.closed for c in self.connections))
        self.assertEqual(len(list(record.journal.folder.glob('*observation.json'))),5)

    def test_started_container_cannot_reduce_profile(self):
        self.container.create_attempted=True
        with self.assertRaisesRegex(RuntimeError,'profile_before_container_creation'):self.call()
        self.assertEqual(self.calls,[])

    def test_wrong_database_denied_before_alter(self):
        self.isolation['database_oid']=7
        with self.assertRaises(Exception):self.call()
        self.assertNotIn('restrict',self.calls)

    def test_extra_privilege_change_denied(self):
        self.changed=lambda p,v: v['roles'][0].update(createdb=True) if p=='after_metadata' else None
        with self.assertRaises(Exception):self.call()
        self.assertNotIn('commit',self.calls)

    def test_commit_lost_reply_stays_unknown(self):
        self.failure='commit'
        with self.assertRaisesRegex(TimeoutError,'original_dispatch'):self.call()
        self.assertEqual(self.calls.count('commit'),1)
        self.assertEqual(len(self.connections),1)
        self.assertFalse((self.gate.out/'component-auth-profile-private/result.json').exists())

    def test_changed_witness_never_complete(self):
        self.changed=lambda p,v: v.update(cluster_id='foreign') if p=='witness_metadata' else None
        with self.assertRaises(Exception):self.call()
        self.assertFalse((self.gate.out/'component-auth-profile-private/result.json').exists())

    def test_profile_source_change_blocks_any_sql(self):
        with patch.object(lifecycle.binding,'verify',side_effect=[{'unit':1},{'unit':2}]):
            with self.assertRaisesRegex(RuntimeError,'source_changed'):self.call()
        self.assertEqual(self.calls,[])

    def test_failed_profile_seals_original_incomplete_after_cleanup(self):
        self.failure='commit'; sealed=[]
        original=m.Records.seal
        def seal(records):
            self.assertTrue(all(c.closed for c in self.connections))
            raw=(records.journal.folder/'incomplete.json').read_bytes()
            self.assertFalse(json.loads(raw)['commit_known'])
            sealed.append(raw)
            return original(records)
        with patch.object(m.Records,'seal',seal):
            with self.assertRaisesRegex(TimeoutError,'original_dispatch'):self.call()
        self.assertEqual(len(sealed),1)
        self.assertFalse((self.gate.out/'component-auth-profile-private/result.json').exists())

    def test_failed_profile_archive_does_not_replace_dispatch_error(self):
        self.failure='commit'
        with patch.object(m.Records,'seal',side_effect=OSError('secondary')):
            with self.assertRaisesRegex(TimeoutError,'original_dispatch') as caught:self.call()
        self.assertIn('component_profile_archive_secondary:OSError',caught.exception.__notes__)

    def test_profile_close_failure_never_publishes_success(self):
        connect=self.runtime.connect
        def broken():
            connection=connect()
            if len(self.connections)==2:
                connection.close=lambda:(_ for _ in ()).throw(OSError('original_close'))
            return connection
        self.runtime.connect=broken
        with self.assertRaisesRegex(OSError,'original_close'):self.call()
        self.assertFalse((self.gate.out/'component-auth-profile-private/result.json').exists())


class ReferenceTests(unittest.TestCase):
    def test_rollback_and_close_failure_preserve_first_error(self):
        lease=object.__new__(m.ScopeLease)
        first=TimeoutError('original_rollback')
        lease.query=SimpleNamespace(execute=lambda *a:(_ for _ in ()).throw(first))
        lease.connection=SimpleNamespace(close=lambda:(_ for _ in ()).throw(OSError('secondary')))
        with self.assertRaises(TimeoutError) as caught:lease.__exit__(None,None,None)
        self.assertIs(caught.exception,first)
        self.assertEqual(first.__notes__,['component_scope_close_secondary:OSError'])

    def test_body_primary_survives_rollback_and_close_errors(self):
        lease=object.__new__(m.ScopeLease);first=ValueError('original_body')
        lease.query=SimpleNamespace(execute=lambda *a:(_ for _ in ()).throw(TimeoutError()))
        lease.connection=SimpleNamespace(close=lambda:(_ for _ in ()).throw(OSError()))
        self.assertFalse(lease.__exit__(type(first),first,None))
        self.assertEqual(first.__notes__,['component_scope_rollback_secondary:TimeoutError',
            'component_scope_close_secondary:OSError'])

    def test_all_nine_queries_receive_same_actor_generator_values(self):
        lease=object.__new__(m.ScopeLease); lease.check=lambda:None
        lease.contract={'fks':[{'target_schema':'auth','relation':m.producer.TABLES[0],
            'columns':['user_id'],'on_delete':'a','on_update':'a'} for _ in range(9)]}
        args=[]
        def execute(c,p,s,a):args.append(a);return [{'n':0}]
        lease.query=SimpleNamespace(execute=execute); lease.connection=None
        lease.no_references(v for v in ['first','second'])
        self.assertEqual(args,[[['first','second']]]*9)

    def test_any_product_reference_blocks(self):
        lease=object.__new__(m.ScopeLease);lease.check=lambda:None
        lease.contract={'fks':[{'target_schema':'auth','relation':m.producer.TABLES[0],
            'columns':['user_id'],'on_delete':'a','on_update':'a'} for _ in range(9)]}
        lease.connection=None;lease.query=SimpleNamespace(execute=lambda *a:[{'n':1}])
        with self.assertRaisesRegex(RuntimeError,'parent_has_product_references'):lease.no_references(['actor'])

    def test_cascade_relation_cannot_be_waived(self):
        lease=object.__new__(m.ScopeLease);lease.check=lambda:None
        lease.contract={'fks':[{'target_schema':'auth','relation':m.producer.TABLES[0],
            'columns':['user_id'],'on_delete':'c','on_update':'a'} for _ in range(9)]}
        with self.assertRaisesRegex(RuntimeError,'scope_fk_shape'):lease.no_references(['actor'])


if __name__=='__main__':unittest.main()
