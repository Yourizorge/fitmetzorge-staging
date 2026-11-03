"""Strict local request registry. Closure proves registered requests, not server quiescence."""
import hashlib
import json
import os
import pathlib
import threading
import time
import uuid
import urllib.error
import urllib.request

from auth_failure_transport import (LocalTransport, UnknownOutcome, NoRedirect,
                                    StrictHTTPHandler, complete_body)


class Blocked(RuntimeError):
    pass


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode('ascii')


def route(path):
    if path.startswith('/admin/users/'):
        actor = path[13:]
        if str(uuid.UUID(actor)) != actor:
            raise Blocked('tracked_subject')
        return '/admin/users/{subject}'
    if path not in ('/admin/users', '/token?grant_type=password', '/logout?scope=global', '/user'):
        raise Blocked('tracked_route')
    return path


class Records:
    def __init__(self, folder):
        self.folder = pathlib.Path(folder)
        self.folder.mkdir()
        self.n = 0
        self.poisoned = False
        self._hashes = {}

    def validate(self):
        if self.poisoned:
            raise Blocked('tracked_storage_poisoned')
        try:
            paths = list(self.folder.iterdir())
            if {p.name for p in paths} != set(self._hashes):
                raise Blocked('tracked_recordset_changed')
            snapshot = {}
            for path in paths:
                if path.is_symlink() or not path.is_file():
                    raise Blocked('tracked_record_type_changed')
                raw = path.read_bytes()
                if sha(raw) != self._hashes[path.name]:
                    raise Blocked('tracked_record_changed')
                snapshot[path.name] = raw
            return snapshot
        except BaseException:
            self.poisoned = True
            raise

    def save(self, kind, value):
        self.validate()
        raw = encoded({'sequence': self.n, 'kind': kind, **value})
        name = '%04d-%s.json' % (self.n, kind)
        expected = sha(raw)
        self._hashes[name] = expected
        try:
            with (self.folder / name).open('xb') as stream:
                if stream.write(raw) != len(raw):
                    raise Blocked('tracked_record_short_write')
                stream.flush()
                os.fsync(stream.fileno())
            if (self.folder / name).read_bytes() != raw:
                raise Blocked('tracked_record_readback_mismatch')
        except BaseException:
            self.poisoned = True
            raise
        self.n += 1
        return {'name': name, 'sha256': expected}

    def export(self):
        snapshot = self.validate()
        return {name: {'sha256': self._hashes[name], 'content': json.loads(snapshot[name])}
                for name in sorted(snapshot)}


class ParentBudget:
    """Explicit HTTP-only preregistration; no SQL observers are hidden here."""
    def __init__(self, folder, plan, *, run_id):
        from auth_failure import binding
        self.run_id = binding(run_id)
        if not isinstance(plan, list) or not 1 <= len(plan) <= 128:
            raise Blocked('tracked_parent_plan')
        self.plan = json.loads(json.dumps(plan))
        for entry in self.plan:
            if (set(entry) != {'method', 'route', 'units'}
                    or entry['method'] not in ('GET', 'POST', 'DELETE')
                    or type(entry['units']) is not int or entry['units'] < 1
                    or entry['route'] not in ('/admin/users', '/token?grant_type=password',
                        '/logout?scope=global', '/user', '/admin/users/{subject}')):
                raise Blocked('tracked_parent_plan_entry')
        self.records = Records(folder)
        self.claim = self.records.save('claim', {'run_id': self.run_id, 'plan': self.plan,
            'reserved': sum(x['units'] for x in plan), 'budget_domain': 'local_diagnostic_only',
            'managed_cost_bound_observed': False, 'refunds': False})
        self.index = self.spent = 0

    def reserve(self, method, path):
        if self.index >= len(self.plan):
            raise Blocked('tracked_parent_budget_exhausted')
        entry = self.plan[self.index]
        if entry['method'] != method or entry['route'] != route(path):
            raise Blocked('tracked_parent_unregistered_request')
        ref = self.records.save('prepaid', {'ordinal': self.index, **entry})
        self.index += 1
        self.spent += entry['units']
        return {'claim_sha256': self.claim['sha256'], 'event_sha256': ref['sha256'],
                'units': entry['units'], 'domain': 'parent_HTTP_prepaid_not_SQL_measurement'}


def existing_prepaid(ledger, key):
    """Consume evidence of an ALREADY charged Case/finalizer entry; never charge twice."""
    def reserve(method, path):
        rows = ledger.entries
        if (key not in ledger.dispatched or not rows or rows[-1].get('phase') != 'before_dispatch'
                or rows[-1].get('key') != key or type(rows[-1].get('units')) is not int
                or rows[-1]['units'] < 1):
            raise Blocked('tracked_existing_precharge_required')
        event_path = ledger.folder / ('event-%03d.json' % rows[-1]['sequence'])
        raw = event_path.read_bytes()
        if json.loads(raw) != rows[-1]:
            raise Blocked('tracked_precharge_changed')
        claim = (ledger.folder / 'claim.json').read_bytes()
        return {'claim_sha256': sha(claim), 'event_sha256': sha(raw),
                'units': rows[-1]['units'], 'domain': 'already_charged_original_ledger'}
    return reserve


class _Seal:
    def __init__(self, registry, refs):
        self.registry = registry
        self.refs = refs


class Registry:
    def __init__(self, folder, *, run_id, drain_timeout=10):
        from auth_failure import binding
        self.run_id = binding(run_id)
        if type(drain_timeout) not in (int, float) or not 0 < drain_timeout <= 60:
            raise Blocked('tracked_drain_timeout')
        self.records = Records(folder)
        self._recordsets = [self.records]
        self.condition = threading.Condition()
        self.phase, self.active = 'OPEN', 0
        self.next_id = 0
        self.requests = {}
        self.workers, self.workers_running, self.worker_failures = [], 0, []
        self.reservations = set()
        self._proof, self._close_ref = None, None
        self.drain_timeout = drain_timeout
        self.records.save('registry', {'run_id': self.run_id, 'scope': 'registered_local_HTTP_requests_only',
            'server_ingress_isolated': False, 'gotrue_background_quiescence_proven': False})

    def dispatch(self, owner, reserve, wire, method, path, data=None, token=None, fault=None, *, proof=None):
        route_name = route(path)
        expected_method = 'GET' if route_name == '/user' else 'DELETE' if route_name == '/admin/users/{subject}' else 'POST'
        if method != expected_method:
            raise Blocked('tracked_method_route')
        with self.condition:
            cleanup = proof is not None
            if cleanup:
                if (not self.valid_proof(proof) or self.phase != 'CLOSED' or self.active
                        or method != 'DELETE' or route_name != '/admin/users/{subject}'):
                    raise Blocked('tracked_cleanup_capability_closed')
            elif self.phase != 'OPEN':
                raise Blocked('tracked_future_request_denied')
            if self.records.poisoned:
                raise Blocked('tracked_journal_failed')
            reservation = reserve(method, path)
            reservation_id = (reservation['claim_sha256'], reservation['event_sha256'])
            if reservation_id in self.reservations:
                raise Blocked('tracked_reservation_replay')
            self.reservations.add(reservation_id)
            request_id = self.next_id
            self.next_id += 1
            self.records.save('admitted', {'request_id': request_id, 'owner_sha256': sha(owner.encode()),
                'method': method, 'route': route_name, 'reservation': reservation, 'cleanup_only': cleanup})
            self.requests[request_id] = {'terminal': False, 'delivery_confirmed': False}
            self.active += 1
        terminal, delivered, primary = False, False, None
        try:
            response = wire(method, path, data, token=token, fault=fault)
            terminal = response['terminal'] is True
            if not terminal:
                raise UnknownOutcome(False)
            if cleanup and not 200 <= response['status'] < 300:
                raise Blocked('tracked_cleanup_http_status')
            delivered = True
            return response
        except BaseException as error:
            primary = error
            if isinstance(error, UnknownOutcome): terminal = error.terminal is True
            raise
        finally:
            with self.condition:
                self.requests[request_id] = {'terminal': terminal, 'delivery_confirmed': delivered}
                try:
                    self.records.save('completed', {'request_id': request_id, 'terminal': terminal,
                        'delivery_confirmed': delivered, 'error_class': type(primary).__name__ if primary else None})
                except BaseException as save_error:
                    self.phase = 'FAILED'
                    if primary is None: raise
                    primary.add_note('secondary_receipt_failure:' + type(save_error).__name__)
                finally:
                    self.active -= 1
                    if not terminal or (cleanup and not delivered): self.phase = 'FAILED'
                    self.condition.notify_all()

    @property
    def proof(self):
        return self._proof if self.valid_proof(self._proof) else None

    def _validate_records(self):
        try:
            for records in self._recordsets:
                records.validate()
        except BaseException:
            self.phase = 'FAILED'
            raise

    def valid_proof(self, proof):
        with self.condition:
            if type(proof) is not _Seal or proof is not self._proof or self._close_ref is None:
                return False
            try:
                self._validate_records()
            except Exception:
                return False
            name, expected = self._close_ref
            return self.phase == 'CLOSED' and self.records._hashes.get(name) == expected

    def start_worker(self, function):
        """Own the thread from start through join; no caller 'joined' attestation."""
        with self.condition:
            if self.phase != 'OPEN':
                raise Blocked('tracked_future_worker_denied')
            self.workers_running += 1
            def target():
                try:
                    function()
                except BaseException as error:
                    with self.condition:
                        self.worker_failures.append(type(error).__name__)
                finally:
                    with self.condition:
                        self.workers_running -= 1
                        self.condition.notify_all()
            worker = threading.Thread(target=target)
            self.workers.append(worker)
            try:
                worker.start()
            except BaseException:
                self.workers_running -= 1
                self.phase = 'FAILED'
                raise
            return worker

    def close_and_drain(self):
        with self.condition:
            if self.phase != 'OPEN':
                raise Blocked('tracked_registry_not_closeable')
            self._validate_records()
            self.phase = 'CLOSING'
            try:
                self.records.save('closing', {'admitted_requests': self.next_id})
            except BaseException:
                self.phase = 'FAILED'
                raise
            deadline = time.monotonic() + self.drain_timeout
            while (self.active or self.workers_running) and self.phase == 'CLOSING':
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.phase = 'FAILED'
                    self.records.save('drain_timeout', {'active_requests': self.active,
                        'running_workers': self.workers_running})
                    raise Blocked('tracked_drain_timeout')
                self.condition.wait(remaining)
            workers = list(self.workers)
        for worker in workers:
            worker.join(max(0, deadline - time.monotonic()))
        with self.condition:
            if (self.phase != 'CLOSING' or self.records.poisoned
                    or self.worker_failures or any(worker.is_alive() for worker in workers)
                    or any(not r['terminal'] for r in self.requests.values())):
                self.phase = 'FAILED'
                raise Blocked('tracked_unknown_upstream_request')
            try:
                self._validate_records()
                ref = self.records.save('closed', {'admitted_requests': self.next_id, 'active_requests': 0,
                    'registered_workers_joined': len(workers),
                    'all_registered_upstream_terminal': True, 'future_regular_dispatch_denied': True,
                    'server_writers_quiescent_proven': False, 'scope': 'registered_request_set_only'})
                self._validate_records()
            except BaseException:
                self.phase = 'FAILED'
                raise
            self.phase = 'CLOSED'
            self._close_ref = (ref['name'], ref['sha256'])
            self._proof = _Seal(self, ref)
            return self._proof

    def case_transport_factory(self, owner, ledger, upstream):
        if type(upstream) is not LocalTransport:
            raise Blocked('tracked_case_strict_transport_required')
        registry = self
        class Adapter:
            def request(self, method, path, data=None, token=None, fault=None):
                operation = {'/admin/users': 'create', '/token?grant_type=password': 'login',
                    '/logout?scope=global': 'logout', '/admin/users/{subject}': 'delete'}[route(path)]
                return registry.dispatch(owner, existing_prepaid(ledger, operation), upstream.request,
                    method, path, data, token, fault)
        return Adapter()


class TrackedAuth:
    def __init__(self, url, base_type, registry, budget, *, finalizer=None, admin_token, denied_type):
        self.url = url
        self.registry, self.budget = registry, budget
        with registry.condition:
            if registry.phase != 'OPEN':
                raise Blocked('tracked_factory_registry_closed')
            registry._recordsets.append(budget.records)
            registry._validate_records()
        self._base_type, self._finalizer = base_type, finalizer
        self._denied_type = denied_type
        self._wire = LocalTransport(url, admin_token)
        self._created, self._owners, self._delete_attempts = {}, {}, set()

    def _request(self, method, path, data=None, token=None, fault=None):
        # Parent admin bearer is supplied per call, not retained in exported evidence.
        if path != '/user':
            wire = LocalTransport(self.url, token or 'not-used-for-this-route')
            return wire.request(method, path, data, token=token, fault=fault)
        if method != 'GET' or data is not None or fault is not None:
            raise Blocked('tracked_user_read_shape')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(), StrictHTTPHandler())
        request = urllib.request.Request(self.url + path, headers={'Authorization': 'Bearer ' + (token or '')}, method='GET')
        terminal = False
        try:
            try: response = opener.open(request, timeout=5)
            except urllib.error.HTTPError as error: response = error
            with response:
                raw, status = complete_body(response), response.status
            terminal = True
            return {'terminal': True, 'status': status, 'body': json.loads(raw) if raw else {}}
        except Exception:
            raise UnknownOutcome(terminal) from None

    def call(self, path, token=None, data=None, method=None):
        method = method or ('GET' if data is None else 'POST')
        if method == 'DELETE':
            raise Blocked('tracked_delete_requires_cleanup_capability')
        try:
            response = self.registry.dispatch('parent', self.budget.reserve, self._request, method, path, data, token)
        except UnknownOutcome:
            raise self._denied_type('auth_denied') from None
        if not 200 <= response['status'] < 300:
            raise self._denied_type('auth_denied')
        if path == '/logout?scope=global' and response['status'] != 204:
            raise Blocked('tracked_logout_status')
        body = response['body']
        if method == 'POST' and path == '/admin/users':
            subject = body['id']
            if (str(uuid.UUID(subject)) != subject or subject in self._created
                    or body.get('email') != data['email'] or not data['email'].endswith('@example.invalid')):
                raise Blocked('tracked_parent_creation_binding')
            self._created[subject] = sha(data['email'].encode())
        return body

    def verify(self, token):
        return self._base_type.verify(self, token)

    def bind_owner(self, role, subject):
        if (role not in ('a', 'trainer', 'b') or role in self._owners
                or subject not in self._created or subject in self._owners.values()):
            raise Blocked('tracked_parent_owner')
        self._owners[role] = subject
        with self.registry.condition:
            self.registry.records.save('parent_owner', {'role': role,
                'subject_sha256': sha(subject.encode()), 'email_sha256': self._created[subject]})

    def close_and_drain(self):
        return self.registry.close_and_drain()

    def finalize(self, ctx, proof):
        if not self.registry.valid_proof(proof) or self.registry.phase != 'CLOSED':
            raise Blocked('tracked_finalizer_requires_actual_close')
        if self._finalizer is not None:
            result = self._finalizer(ctx, self, proof)
            if not self.registry.valid_proof(proof) or self.registry.phase != 'CLOSED':
                raise Blocked('tracked_finalizer_lost_terminal_proof')
            return result

    def delete_owned(self, proof, subject, ledger, key):
        if (set(self._owners) != {'a', 'trainer', 'b'} or subject not in self._owners.values()
                or subject in self._delete_attempts):
            raise Blocked('tracked_cleanup_owner_or_repeat')
        role = next(r for r, s in self._owners.items() if s == subject)
        if key not in ('delete', role + ':delete'):
            raise Blocked('tracked_delete_wrong_reservation')
        self._delete_attempts.add(subject)
        return self.registry.dispatch('parent-cleanup', existing_prepaid(ledger, key), self._wire.request,
            'DELETE', '/admin/users/' + subject, proof=proof)

    def evidence(self):
        with self.registry.condition:
            self.registry._validate_records()
            return {'run_id': self.registry.run_id, 'scope': 'registered_requests_only', 'phase': self.registry.phase,
                'requests': len(self.registry.requests), 'active': self.registry.active,
                'workers': len(self.registry.workers), 'worker_failures': list(self.registry.worker_failures),
                'parent_prepaid': self.budget.spent, 'parent_reserved': sum(x['units'] for x in self.budget.plan),
                'case_entries_already_charged_not_added_again': True, 'extra_SQL_by_tracker': 0,
                'full_chain_admission': False, 'global_auth_zero_claim': False,
                'server_ingress_isolated': False, 'gotrue_background_quiescence_proven': False,
                'registry_journal': self.registry.records.export(), 'parent_budget_journal': self.budget.records.export()}


class Factory:
    """Parent supplies explicit budget and optional C/Auth finalizer; no auto-cleanup."""
    def __init__(self, registry, budget, *, finalizer=None):
        if registry.run_id != budget.run_id:
            raise Blocked('tracked_budget_run_mismatch')
        self.registry, self.budget, self.finalizer = registry, budget, finalizer
        self.instance = None

    def __call__(self, url, base_type, admin_token, denied_type):
        if self.instance is not None:
            raise Blocked('tracked_factory_not_reusable')
        self.instance = TrackedAuth(url, base_type, self.registry, self.budget,
                                    finalizer=self.finalizer, admin_token=admin_token, denied_type=denied_type)
        return self.instance
