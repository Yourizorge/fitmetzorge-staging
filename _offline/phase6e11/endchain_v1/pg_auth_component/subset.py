"""Exact known parent subset, never discovery/adoption of unknown create results."""
import secrets
import inspect
import sys
import uuid

import auth_failure as engine
import auth_failure_tracked as tracked
from . import scope
from .lifecycle import Records, need

ROLES = ('a', 'trainer', 'b')


class _SnapshotDB:
    """Only the existing source-bound snapshot method can emit these reads."""
    def __init__(self, lease, records):
        self.lease, self.records, self.used = lease, records, 0

    def execute(self, sql, args):
        caller = inspect.currentframe().f_back
        need(caller.f_code is engine.RealBackend.snapshot.__code__, 'snapshot_caller')
        del caller
        self.lease.check()
        need(self.used < 6, 'snapshot_bound')
        self.used += 1
        name = 'snapshot-%d' % self.used
        self.records.save(name+'-before.json', {'sql_sha256': tracked.sha(sql.encode()),
            'ordinal': self.used, 'arguments_exported': False})
        cursor = self.lease.connection.execute(sql, args)
        self.records.save(name+'-after.json', {'confirmed': True, 'ordinal': self.used})
        return cursor


class ParentSubset:
    def __init__(self, gate, auth, ctx, run_id):
        need(type(auth) is tracked.TrackedAuth and type(auth.registry) is tracked.Registry
             and auth.registry.run_id == run_id and auth.registry.phase == 'OPEN'
             and not auth.registry.requests and not auth.registry.workers
             and not auth._owners and not auth._created
             and ctx['auth'] is auth and ctx['auth_request_registry'] is auth.registry,
             'subset_fresh_parent')
        need(auth.url == 'http://127.0.0.1:59999', 'subset_loopback')
        self.gate, self.auth, self.ctx, self.run_id = gate, auth, ctx, run_id
        self.records = Records(gate, 'component-parent-owners',
            [sys.modules[__name__], scope, engine, tracked])
        self.known = {}
        self.pending_create = None
        self.calls = self.deletes = 0
        self.cleanup_attempted = False
        self.seal = None
        self.records.save('intent.json', {'run_id': run_id, 'maximum_owners': 3,
            'maximum_parent_requests': 9, 'maximum_delete_requests': 3,
            'delete_declared_units_each': 128, 'managed_sql_cost_known': False,
            'budget_domain': 'additional_disposable_diagnostic_not_2349',
            'unknown_create_cleanup_allowed': False, 'claim_release_allowed': False})
        self.cleanup_budget = tracked.ParentBudget(gate.out/'component-parent-delete-budget-private',
            [{'method':'DELETE','route':'/admin/users/{subject}','units':128} for _ in ROLES], run_id=run_id)
        auth.registry._recordsets.append(self.cleanup_budget.records)

    def check(self):
        self.records.check()
        self.auth.registry._validate_records()
        need(not self.auth.registry.workers and not self.auth.registry.workers_running,
             'subset_unregistered_worker')
        need(self.auth.registry.next_id == self.calls+self.deletes, 'subset_foreign_request')
        need(self.auth._owners == {r: v['actor'] for r, v in self.known.items()}
             and self.auth._created == {v['actor']:tracked.sha(v['email'].encode()) for v in self.known.values()},
             'subset_owner_changed')
        originals = self.auth.registry.records.export()
        owners = [v['content'] for v in originals.values() if v['content']['kind'] == 'parent_owner']
        need(len(owners) == len(self.known), 'subset_owner_records')
        for role, value in self.known.items():
            need(sum(r.get('role') == role and r.get('subject_sha256') == tracked.sha(value['actor'].encode())
                and r.get('email_sha256') == tracked.sha(value['email'].encode()) for r in owners) == 1,
                'subset_original_owner')

    def call(self, action):
        before = self.auth.registry.next_id
        try:
            return action()
        finally:
            delta = self.auth.registry.next_id-before
            need(delta in (0, 1), 'subset_dispatch_count')
            self.calls += delta

    def bootstrap(self):
        need(not self.known and not self.calls and not self.cleanup_attempted, 'subset_bootstrap_replay')
        for role in ROLES:
            self.check()
            email = 'fmz-'+uuid.uuid4().hex+'@example.invalid'
            account = {'email': email, 'password': secrets.token_urlsafe(32)}
            self.records.save('create-intent-'+role+'.json', {
                'role': role, 'email_sha256': tracked.sha(email.encode())})
            self.pending_create = role
            before = self.auth.registry.next_id
            try:
                user = self.call(lambda: self.auth.call('/admin/users', self.ctx['test_admin_token'],
                                                       {**account, 'email_confirm': True}))
            except BaseException:
                if self.auth.registry.next_id == before:
                    self.pending_create = None
                raise
            actor = user['id']
            need(str(uuid.UUID(actor)) == actor and actor not in (self.run_id, engine.OLD_RUN)
                 and self.auth._created.get(actor) == tracked.sha(email.encode()), 'subset_confirmed_create')
            self.auth.bind_owner(role, actor)
            self.known[role] = {'actor': actor, 'email': email}
            self.records.save('created-'+role+'.json', {'role': role,
                'actor_sha256': tracked.sha(actor.encode()), 'email_sha256': tracked.sha(email.encode())})
            self.pending_create = None
            self.ctx['accounts'][role] = account
            issued = self.call(lambda: self.auth.call('/token?grant_type=password', data=account))
            token = issued['access_token']
            claim = self.call(lambda: self.auth.verify(token))
            need(claim['sub'] == actor, 'subset_verified_subject')
            self.ctx['tokens'][role], self.ctx['claims'][role] = token, claim
        self.check()

    def close(self):
        need(self.seal is None, 'subset_close_replay')
        self.seal = self.auth.close_and_drain()
        self.check()
        need(self.pending_create is None and self.auth.registry.valid_proof(self.seal)
             and all(r['terminal'] and r['delivery_confirmed'] for r in self.auth.registry.requests.values()),
             'subset_unknown_create_or_mint')
        return self.seal

    def cleanup(self, lease):
        need(not self.cleanup_attempted, 'subset_cleanup_replay')
        self.cleanup_attempted = True
        self.check()
        need(type(lease) is scope.ScopeLease and lease.gate is self.gate and lease.run_id == self.run_id,
             'subset_live_scope_required')
        lease.check()
        need(self.pending_create is None and self.auth.registry.valid_proof(self.seal)
             and all(r['terminal'] and r['delivery_confirmed'] for r in self.auth.registry.requests.values()),
             'subset_unknown_terminal')
        lease.no_references(v['actor'] for v in self.known.values())
        # Reuse the existing exact-key read query; no separate discovery SQL.
        reader = type('Reader', (), {'db': _SnapshotDB(lease, self.records)})()
        for role, owner in self.known.items():
            self.check(); lease.check()
            snapshot = engine.RealBackend.snapshot(reader, owner['email'], None, owner['actor'], [])
            engine.validate_snapshot(snapshot)
            need(snapshot['users'] == [{'id': owner['actor'], 'email': owner['email'], 'marker': None}],
                 'subset_snapshot_owner')
            self.records.save('delete-intent-'+role+'.json', {'role': role,
                'actor_sha256': tracked.sha(owner['actor'].encode()),
                'counts': snapshot['counts'], 'session_hashes': [tracked.sha(v.encode()) for v in snapshot['session_ids']]})
            self.deletes += 1  # Attempt is sticky; no retry after lost reply.
            self.auth.registry.dispatch('parent-cleanup', self.cleanup_budget.reserve, self.auth._wire.request,
                'DELETE', '/admin/users/'+owner['actor'], proof=self.seal)
            after = engine.RealBackend.snapshot(reader, owner['email'], None, owner['actor'], snapshot['session_ids'])
            engine.validate_snapshot(after)
            need(not any(after['counts'].values()), 'subset_residual_auth_rows')
            self.records.save('absence-'+role+'.json', {'role': role, 'counts': after['counts'],
                'stateless_token_revocation_claim': False})
        self.records.save('result.json', {'status': 'KNOWN_PARENT_SUBSET_ABSENT', 'owners': len(self.known),
            'delete_attempts': self.deletes, 'parent_subset_zero': True,
            'unknown_outcomes_reclassified': False, 'global_auth_zero': False,
            'claims_released': False, 'full_chain_admission': False})
        return {'known_parent_subset_absent': True, 'owners': len(self.known), 'global_auth_zero': False}
