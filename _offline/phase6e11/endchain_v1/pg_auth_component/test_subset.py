"""Real tracker journals with unit HTTP/SQL doubles, never live Auth evidence."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

import auth_failure_tracked as tracked
from auth_failure_transport import UnknownOutcome
from . import lifecycle, scope, subset as m

RUN = 'a0d72b98-f5f4-4971-999d-402cf43bc802'


class Base:
    def verify(self, token):
        return self.call('/user', token)


class SubsetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.gate = SimpleNamespace(out=Path(self.temp.name), save=lambda *a: None)
        p = patch.object(lifecycle.binding, 'verify', return_value={'unit_only':True})
        p.start(); self.addCleanup(p.stop)
        registry = tracked.Registry(self.gate.out/'registry', run_id=RUN)
        plan = [v for _ in range(3) for v in (
            {'method':'POST','route':'/admin/users','units':128},
            {'method':'POST','route':'/token?grant_type=password','units':128},
            {'method':'GET','route':'/user','units':128})]
        budget = tracked.ParentBudget(self.gate.out/'budget', plan, run_id=RUN)
        self.auth = tracked.TrackedAuth('http://127.0.0.1:59999', Base, registry, budget,
            admin_token='PRIVATE_REVIEW_SENTINEL', denied_type=RuntimeError)
        self.ctx = dict(auth=self.auth, auth_request_registry=registry,
            test_admin_token='PRIVATE_REVIEW_SENTINEL', tokens={}, claims={}, accounts={})
        self.fail = None
        self.created = {}
        self.deleted = []
        self.last_actor = None
        def request(method, path, data=None, token=None, fault=None):
            if self.fail == path:
                raise UnknownOutcome(False)
            if path == '/admin/users':
                actor = str(uuid.uuid4()); self.last_actor=actor
                self.created[actor] = data['email']
                body = {'id':actor,'email':data['email']}
            elif path.startswith('/token'): body = {'access_token':'PRIVATE_REVIEW_SENTINEL'}
            elif path == '/user': body = {'sub':self.last_actor,'session_id':str(uuid.uuid4())}
            else:
                self.deleted.append(path.split('/')[-1]); body={}
            return {'terminal':True,'status':200,'body':body}
        self.auth._request = request
        self.auth._wire.request = request
        self.owner = m.ParentSubset(self.gate, self.auth, self.ctx, RUN)

    def lease(self):
        value = object.__new__(scope.ScopeLease)
        value.gate, value.run_id = self.gate, RUN
        self.lock_checked = self.refs_checked = 0
        def check(): self.lock_checked += 1
        def refs(actors): self.refs_checked += 1; self.assertEqual(set(actors), set(self.created))
        value.check, value.no_references = check, refs
        def execute(sql, args):
            actor = args[2]
            counts = dict.fromkeys(('users','identities','sessions','refresh_tokens',
                'mfa_amr_claims','mfa_factors','one_time_tokens','flow_state'), 0)
            users = []
            if actor not in self.deleted:
                users = [{'id':actor,'email':self.created[actor],'marker':None}]
                counts['users']=1; counts['identities']=1
            result = {'users':users, 'session_ids':[], 'counts':counts}
            return SimpleNamespace(fetchone=lambda: {'value':result})
        value.connection = SimpleNamespace(execute=execute, closed=False)
        return value

    def test_three_known_accounts_cleanup_without_fake_primary(self):
        self.owner.bootstrap(); self.owner.close()
        result = self.owner.cleanup(self.lease())
        self.assertEqual(result['owners'], 3)
        self.assertEqual(len(self.deleted), 3)
        self.assertFalse(result['global_auth_zero'])
        self.assertGreater(self.lock_checked, 6)
        raw = b''.join(p.read_bytes() for p in self.owner.records.journal.folder.iterdir())
        self.assertNotIn(b'PRIVATE_REVIEW_SENTINEL', raw)
        for actor, email in self.created.items():
            self.assertNotIn(actor.encode(), raw); self.assertNotIn(email.encode(), raw)

    def test_partial_known_create_cleanup_without_login(self):
        # Terminal application rejection, not a lost HTTP response.
        original = self.auth._request
        def request(method,path,*args,**kwargs):
            if path.startswith('/token'): return {'terminal':True,'status':400,'body':{}}
            return original(method,path,*args,**kwargs)
        self.auth._request = request
        with self.assertRaises(RuntimeError): self.owner.bootstrap()
        self.assertEqual(len(self.owner.known), 1)
        self.owner.close()
        self.assertEqual(self.owner.cleanup(self.lease())['owners'], 1)
        self.assertEqual(len(self.deleted), 1)

    def test_lost_create_does_not_adopt_email_match(self):
        self.fail = '/admin/users'
        with self.assertRaises(RuntimeError): self.owner.bootstrap()
        self.assertEqual(self.owner.known, {})
        with self.assertRaises(Exception): self.owner.close()
        with self.assertRaises(Exception): self.owner.cleanup(self.lease())
        self.assertEqual(self.deleted, [])

    def test_lost_login_retains_known_owner(self):
        self.fail = '/token?grant_type=password'
        with self.assertRaises(RuntimeError): self.owner.bootstrap()
        self.assertEqual(len(self.owner.known), 1)
        with self.assertRaises(Exception): self.owner.close()
        with self.assertRaises(Exception): self.owner.cleanup(self.lease())
        self.assertEqual(self.deleted, [])

    def test_no_terminal_seal_no_delete(self):
        self.owner.bootstrap()
        with self.assertRaisesRegex(RuntimeError, 'unknown_terminal'): self.owner.cleanup(self.lease())
        self.assertEqual(self.deleted, [])

    def test_serialized_scope_not_capability(self):
        self.owner.bootstrap(); self.owner.close()
        with self.assertRaisesRegex(RuntimeError, 'live_scope_required'):
            self.owner.cleanup({'live':True,'scope_verified':True})
        self.assertEqual(self.deleted, [])

    def test_changed_owner_blocks_cleanup(self):
        self.owner.bootstrap(); self.owner.close()
        self.auth._owners['a']=str(uuid.uuid4())
        with self.assertRaisesRegex(RuntimeError, 'owner_changed'): self.owner.cleanup(self.lease())
        self.assertEqual(self.deleted, [])

    def test_changed_source_no_delete(self):
        self.owner.bootstrap(); self.owner.close()
        with patch.object(lifecycle.binding, 'verify', return_value={'different':True}):
            with self.assertRaisesRegex(RuntimeError, 'source_changed'): self.owner.cleanup(self.lease())
        self.assertEqual(self.deleted, [])

    def test_changed_original_owner_journal_no_delete(self):
        self.owner.bootstrap(); self.owner.close()
        path = next(self.auth.registry.records.folder.glob('*parent_owner.json'))
        path.write_bytes(b'{}')
        with self.assertRaises(Exception): self.owner.cleanup(self.lease())
        self.assertEqual(self.deleted, [])

    def test_lock_loss_before_delete_blocks(self):
        self.owner.bootstrap(); self.owner.close(); lease=self.lease()
        lease.check = lambda: (_ for _ in ()).throw(RuntimeError('scope_not_held'))
        with self.assertRaisesRegex(RuntimeError, 'scope_not_held'): self.owner.cleanup(lease)
        self.assertEqual(self.deleted, [])

    def test_product_reference_blocks_delete(self):
        self.owner.bootstrap(); self.owner.close(); lease=self.lease()
        lease.no_references = lambda actors: (_ for _ in ()).throw(RuntimeError('product_reference'))
        with self.assertRaisesRegex(RuntimeError, 'product_reference'): self.owner.cleanup(lease)
        self.assertEqual(self.deleted, [])

    def test_foreign_run_lease_rejected(self):
        self.owner.bootstrap(); self.owner.close(); lease=self.lease(); lease.run_id=str(uuid.uuid4())
        with self.assertRaisesRegex(RuntimeError, 'live_scope_required'): self.owner.cleanup(lease)

    def test_lost_delete_no_retry_no_absence_claim(self):
        self.owner.bootstrap(); self.owner.close()
        def lost(*args, **kwargs): raise UnknownOutcome(False)
        self.auth._wire.request = lost
        with self.assertRaises(UnknownOutcome): self.owner.cleanup(self.lease())
        with self.assertRaisesRegex(RuntimeError, 'cleanup_replay'): self.owner.cleanup(self.lease())
        self.assertFalse((self.owner.records.journal.folder/'result.json').exists())
        self.assertEqual(self.owner.deletes, 1)

    def test_snapshot_wrong_email_no_delete(self):
        self.owner.bootstrap(); self.owner.close(); lease=self.lease()
        actor=next(iter(self.created)); self.created[actor]='foreign@example.invalid'
        with self.assertRaisesRegex(RuntimeError, 'snapshot_owner'): self.owner.cleanup(lease)
        self.assertEqual(self.deleted, [])

    def test_residual_row_no_partial_pass(self):
        self.owner.bootstrap(); self.owner.close(); lease=self.lease()
        original=lease.connection.execute
        def execute(sql,args):
            result=original(sql,args).fetchone()
            if self.deleted: result['value']['counts']['refresh_tokens']=1
            return SimpleNamespace(fetchone=lambda: result)
        lease.connection.execute=execute
        with self.assertRaisesRegex(RuntimeError, 'residual_auth_rows'): self.owner.cleanup(lease)
        self.assertEqual(len(self.deleted), 1)
        self.assertFalse((self.owner.records.journal.folder/'result.json').exists())


if __name__ == '__main__': unittest.main()
