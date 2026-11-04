"""Opt-in source-bound bootstrap; partial cleanup reuses the parent Auth engine.

Only ci_auth.environment invokes run, before yielding its context. Known creates
are journaled/bound before login. Any sent create without a validated subject,
nonterminal HTTP, changed source/journal or failed C attestation remains NO_GO.
No SQL mutation, hosted endpoint, caller owner list, retry or global-zero claim.
"""
import copy
import inspect
import pathlib
import secrets
import sys
import uuid
import weakref

import admission_journal as durable
import admission_module_binding as binding
import auth_failure as af
import auth_failure_parent_finalizer as parent
import auth_failure_tracked as tracked
import auth_failure_transport as transport
import auth_pre_fixture_closure as pre
import fixture_producer_scope as producer
from admission_binding import NEW_RUN

PREFIX = 'auth-partial-bootstrap'
_ISSUED = weakref.WeakKeyDictionary()


def require(value, reason):
    parent.require(value, 'partial_' + reason)


def selected(environment):
    return [sys.modules[__name__], environment, inspect.getmodule(environment.LocalAuth), parent, af, tracked, transport,
            pre, producer, binding, durable,
            sys.modules[producer.NativeRuntime.__module__]]


class Prerequisite:
    def __init__(self):
        raise TypeError('only_actual_partial_bootstrap')

    def state(self):
        require(type(self) is Prerequisite and self in _ISSUED, 'unissued')
        return _ISSUED[self]

    @property
    def roles(self):
        return tuple(self.state().owned)

    @property
    def hashes(self):
        return dict(self.state().hashes)

    @property
    def original_error_class(self):
        return type(self.state().primary).__name__

    def consume(self, gate, ctx, auth, seal):
        state = self.state()
        require(not state.consumed, 'proof_replay')
        state.consumed = True
        require(gate is state.gate and ctx is state.ctx and auth is state.auth
                and seal is state.seal and sys.exception() is state.primary, 'proof_context')
        self.unchanged()
        return self.owners()

    def owners(self):
        self.unchanged()
        return copy.deepcopy(self.state().owned)

    def unchanged(self):
        state = self.state()
        state.check(closed=True)
        pre._scope_unchanged({'closure': state, 'gate': state.gate,
            'scope': state.catalog, 'scope_result': state.catalog_result,
            'scope_contract': state.catalog_contract})
        for path, expected in state.hashes.items():
            parent.cparent.reference(state.gate.out, {'path': path, 'sha256': expected})

    def bind_snapshot(self, role, value):
        state = self.state()
        self.unchanged()
        require(role in state.owned and role not in state.snapshots, 'snapshot_replay')
        item = state.owned[role]
        af.validate_snapshot(value)
        require(value['users'] == [{'id': item['actor'], 'email': item['email'], 'marker': None}],
                'snapshot_owner')
        # Sessions are selected by the original confirmed actor after mint-close,
        # never by caller-supplied JWTs or an email-only discovery.
        state.journal.save('sessions-' + role + '.json', {
            'actor_sha256': tracked.sha(item['actor'].encode()),
            'session_hashes': [tracked.sha(s.encode()) for s in sorted(value['session_ids'])]})
        state.snapshots.add(role)
        item['session_ids'] = list(value['session_ids'])

    def delete(self, role, ledger):
        state = self.state()
        self.unchanged()
        require(state.consumed and role in state.snapshots and role not in state.deleted, 'delete_scope_or_replay')
        state.deleted.add(role)  # Unknown dispatch is never retried.
        return state.auth.registry.dispatch('parent-cleanup',
            tracked.existing_prepaid(ledger, role + ':delete'), state.auth._wire.request,
            'DELETE', '/admin/users/' + state.owned[role]['actor'], proof=state.seal)


class _Bootstrap:
    def __init__(self, gate, ctx, auth, environment, delete_costs):
        caller = inspect.currentframe().f_back
        require(caller.f_code is run.__code__ and caller.f_locals.get('environment') is environment,
                'bootstrap_constructor_origin')
        del caller
        require(type(auth) is tracked.TrackedAuth and ctx.get('auth') is auth
                and ctx.get('auth_request_registry') is auth.registry, 'live_auth')
        require(auth._base_type is environment.LocalAuth, 'actual_auth_class')
        require(auth.registry.run_id == NEW_RUN and auth.registry.phase == 'OPEN'
                and not auth.registry.requests and not auth.registry.workers
                and not auth._created and not auth._owners, 'fresh_exclusive_registry')
        require(all(ctx.get(k) == {} for k in ('tokens', 'claims', 'accounts')), 'empty_bootstrap')
        require(ctx.get('test_admin_token') and callable(ctx.get('suspend_admin')), 'local_capabilities')
        require(auth.url in af.ORIGINS, 'local_url')
        # Only the existing three-role local diagnostic contract is accepted.
        require(delete_costs == dict.fromkeys(parent.ROLES, 128)
                and all(type(v) is int for v in delete_costs.values()), 'delete_cost_contract')
        self.gate, self.ctx, self.auth = gate, ctx, auth
        self.environment, self.costs = environment, dict(delete_costs)
        self.modules = selected(environment)
        self.source = binding.verify(gate, self.modules)
        ci = [r for r in self.source['modules'] if r['module'] == environment.__name__]
        require(len(ci) == 1 and ci[0]['relative_path'] == '_offline/phase6e_server_v1/ci_auth.py',
                'exact_environment_source')
        self.owned, self.created, self.hashes = {}, {}, {}
        self.calls, self.snapshots, self.deleted = [], set(), set()
        self.pending_create, self.seal, self.primary = None, None, None
        self.returned, self.consumed = False, False
        self.scope, self.started = None, False
        self._scope_attempted, self._scope_units = False, 0
        self.journal = durable.Journal(pathlib.Path(gate.out) / (PREFIX + '-private'),
                                       lambda *_: None, PREFIX)
        self.journal.save('intent.json', {
            'preparation_run': NEW_RUN, 'source_binding': self.source,
            'parent_roles': list(parent.ROLES), 'cleanup_reserved_units': 412,
            'catalog_reserved_units': 10, 'maximum_parent_engine_units': 402,
            'budget_domain': 'additional_disposable_diagnostic_not_2349',
            'managed_costs_observed': False, 'refunds': False, 'retries': False,
            'original_claims_released': False})

    def check(self, *, closed=False):
        require(not self.returned, 'bootstrap_already_returned')
        require(binding.verify(self.gate, self.modules) == self.source, 'source_changed')
        self.journal._inventory()
        for name, ref in self.journal.entries.items():
            self.journal._read(name, ref)
        registry = self.auth.registry
        require(not registry.workers and registry.next_id == len(self.calls) + len(self.deleted), 'unowned_producer')
        records = registry.records.export()
        all_admitted = [r['content'] for r in records.values() if r['content']['kind'] == 'admitted']
        admitted = [r for r in all_admitted if r['cleanup_only'] is False]
        cleanup = [r for r in all_admitted if r['cleanup_only'] is True]
        require(len(cleanup) == len(self.deleted) and all(r['method'] == 'DELETE'
                and r['route'] == '/admin/users/{subject}'
                and r['owner_sha256'] == tracked.sha('parent-cleanup'.encode()) for r in cleanup), 'cleanup_inventory')
        require(len(admitted) == len(self.calls), 'request_inventory')
        for row, (method, route) in zip(admitted, self.calls):
            require(row['method'] == method and row['route'] == route
                    and row['owner_sha256'] == tracked.sha('parent'.encode())
                    and row['cleanup_only'] is False, 'unowned_request')
        require(self.auth._created == self.created
                and self.auth._owners == {r: v['actor'] for r, v in self.owned.items()}, 'owner_changed')
        bound = [r['content'] for r in records.values() if r['content']['kind'] == 'parent_owner']
        require(len(bound) == len(self.owned), 'owner_record_count')
        for role, item in self.owned.items():
            require(sum(row.get('role') == role
                        and row.get('subject_sha256') == tracked.sha(item['actor'].encode())
                        and row.get('email_sha256') == tracked.sha(item['email'].encode())
                        for row in bound) == 1, 'original_owner_journal')
        if closed:
            require(self.pending_create is None and registry.valid_proof(self.seal), 'unknown_create_or_mint')
            require(self.primary is not None, 'original_failure')

    def call(self, method, route, action):
        self.check()
        before = self.auth.registry.next_id
        try:
            return action()
        finally:
            emitted = self.auth.registry.next_id - before
            require(emitted in (0, 1), 'unexpected_dispatch_count')
            if emitted:
                self.calls.append((method, route))

    def execute(self):
        for role in parent.ROLES:
            email = 'fmz-' + uuid.uuid4().hex + '@example.invalid'
            account = {'email': email, 'password': secrets.token_urlsafe(32)}
            self.journal.save('create-intent-' + role + '.json', {
                'role': role, 'email_sha256': tracked.sha(email.encode()), 'preparation_run': NEW_RUN})
            before = self.auth.registry.next_id
            self.pending_create = role
            try:
                user = self.call('POST', '/admin/users', lambda: self.auth.call(
                    '/admin/users', self.ctx['test_admin_token'], {**account, 'email_confirm': True}))
            except BaseException:
                if self.auth.registry.next_id == before:
                    self.pending_create = None  # No admitted create, not a refund.
                raise
            actor = user['id']
            require(str(uuid.UUID(actor)) == actor and actor not in (NEW_RUN, af.OLD_RUN)
                    and self.auth._created.get(actor) == tracked.sha(email.encode()), 'confirmed_create')
            self.auth.bind_owner(role, actor)
            self.journal.save('created-' + role + '.json', {
                'role': role, 'subject_sha256': tracked.sha(actor.encode()),
                'email_sha256': tracked.sha(email.encode()), 'create_response_confirmed': True})
            self.created[actor] = tracked.sha(email.encode())
            self.owned[role] = {'actor': actor, 'email': email, 'session_ids': None}
            self.pending_create = None
            self.ctx['accounts'][role] = account
            issued = self.call('POST', '/token?grant_type=password',
                               lambda: self.auth.call('/token?grant_type=password', data=account))
            token = issued['access_token']
            claim = self.call('GET', '/user', lambda: self.auth.verify(token))
            require(claim['sub'] == actor, 'verified_subject')
            self.ctx['tokens'][role], self.ctx['claims'][role] = token, claim
        self.check()
        self.journal.save('bootstrap-complete.json', {'created_owners': 3, 'requests': len(self.calls)})
        self.returned = True

    def cleanup(self, primary):
        caller = inspect.currentframe().f_back
        require(caller.f_code is run.__code__ and caller.f_locals.get('state') is self
                and primary is sys.exception() and not self.returned, 'cleanup_origin')
        del caller
        self.primary = primary
        self.seal = self.auth.close_and_drain()
        self.check(closed=True)
        close_name, close_hash = self.auth.registry._close_ref
        self.hashes = {
            (self.auth.registry.records.folder / close_name).relative_to(self.gate.out).as_posix(): close_hash,
            'candidate.json': self.source['candidate_manifest_sha256']}
        original_save = self.gate.save
        def publish(name, value):
            require(not (pathlib.Path(self.gate.out) / name).exists(), 'publication_exists')
            original_save(name, value)
            actual, raw_hash = parent.cparent.read_record(self.gate.out, name)
            require(durable.raw(actual) == durable.raw(value), 'publication_readback')
            require(name not in self.hashes, 'publication_replay')
            self.hashes[name] = raw_hash
        self.catalog, self.catalog_result, self.catalog_contract = pre._attest_scope(
            self, self.ctx, self, self.journal, publish)
        for name, ref in self.journal.entries.items():
            self.hashes[(self.journal.folder / name).relative_to(self.gate.out).as_posix()] = ref['sha256']
        proof = object.__new__(Prerequisite)
        _ISSUED[proof] = self
        costs = {r: self.costs[r] for r in self.owned}
        result = parent.finalize(self.gate, self.ctx, self.auth, self.seal, None,
            delete_costs=costs, partial_bootstrap_proof=proof)
        return result


def run(gate, ctx, auth, *, delete_costs):
    """Called only by the opt-in environment BEFORE yield; re-raises original."""
    frame = inspect.currentframe().f_back
    environment = sys.modules.get(frame.f_globals.get('__name__'))
    require(environment is not None and getattr(environment, 'environment', None) is not None
            and frame.f_code is environment.environment.__wrapped__.__code__
            and frame.f_locals.get('ctx') is ctx and frame.f_locals.get('auth') is auth
            and frame.f_locals.get('partial_bootstrap') is True, 'actual_environment_call_required')
    del frame
    try:
        state = _Bootstrap(gate, ctx, auth, environment, delete_costs)
    except BaseException as primary:
        # Rejection cannot leave registered producers able to mint. Nonempty
        # state is NOT adopted for ownership/cleanup, but must still be closed.
        if (type(auth) is tracked.TrackedAuth and type(auth.registry) is tracked.Registry
                and auth.registry.phase == 'OPEN'):
            try: auth.close_and_drain()
            except BaseException as error:
                primary.add_note('secondary_partial_preflight_close:' + type(error).__name__)
        raise
    try:
        state.execute()
    except BaseException as primary:
        report = {'status': 'NO_GO', 'original_error_class': type(primary).__name__,
            'cleanup_reserved_units': 412, 'refunds': 0, 'original_claims_released': False,
            'global_auth_zero_claim': False, 'full_chain_admission': False,
            'full_auth_cleanup_proven': False}
        try:
            result = state.cleanup(primary)
            report.update(suffix_status=result['suffix_status'],
                catalog_prepaid=state._scope_units, parent_prepaid=result['prepaid_consumed'],
                local_diagnostic_prepaid=state._scope_units + result['prepaid_consumed'],
                known_owners=len(state.owned), unknown_create=False)
        except BaseException as error:
            primary.add_note('secondary_partial_bootstrap_cleanup:' + type(error).__name__)
            report.update(suffix_status='NO_GO', cleanup_error_class=type(error).__name__,
                catalog_prepaid=state._scope_units, known_owners=len(state.owned),
                unknown_create=state.pending_create is not None,
                parent_engine_accounting='separate_engine_receipt_if_dispatched')
        try:
            state.journal.save('result.json', report)
            report['original_journal'] = {n: {**ref, 'content': __import__('json').loads(state.journal._read(n, ref))}
                                          for n, ref in state.journal.entries.items()}
        except BaseException as error:
            primary.add_note('secondary_partial_bootstrap_receipt:' + type(error).__name__)
            report.update(suffix_status='NO_GO', evidence_error_class=type(error).__name__)
        try: gate.save(PREFIX + '.json', report)
        except BaseException as error:
            primary.add_note('secondary_partial_bootstrap_publication:' + type(error).__name__)
        raise

