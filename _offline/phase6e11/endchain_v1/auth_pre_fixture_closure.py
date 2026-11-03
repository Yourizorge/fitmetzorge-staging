"""Opt-in pre-fixture prerequisite for the existing parent Auth delete engine.

Main integration contract (not installed by this module): Closure.__init__ sets
fixture_mutation_started=False then pre_fixture=Guard(self). Its exact method is
    def before_bootstrap_write(self):
        self.pre_fixture.before_bootstrap_write()
        self.fixture_mutation_started = True
Gate calls closure.before_bootstrap_write() immediately before its sole direct
admission_fixture_context.run(self, ctx, runtime=tracked) call.

observe requires the actual complete bootstrap, closed tracked HTTP registry,
and no fixture runtime ever handed out. It can record body/scope failures but
does not authorize cleanup. Neither API admits partial/unknown bootstrap or
failures after runtime creation; cleanup also rejects any prior scope attempt.
Six extra prepaid local read-only observations; no use of the 2349 allowance.
It preserves the original failure, no refunds/retries, and never releases claims.

cleanup() instead closes the guard and passes a live one-use Prerequisite into
parent.finalize: the existing 402-unit engine performs all 18 observations and
three prepaid deletes, ONLY after a fresh successful C producer Scope observation
(10 additional prepaid reads, including rollback). Any prior scope attempt is
rejected without retry. Total local reservation at128/delete is412, not2349.
It does NOT first run observe(); no hidden extra six reads.
These are alternative one-shot APIs. Main must preserve its original exception
when cleanup returns; cleanup failure re-raises that exact original object.
No C receipt is manufactured. Neither API proves external/global quiescence.
"""
import ast
import copy
import inspect
import pathlib
import re
import sys
import textwrap
import threading
import weakref

import admission_journal as durable
import admission_module_binding as binding
import auth_failure as af
import auth_failure_parent_finalizer as parent
import auth_failure_tracked as tracked
from admission_binding import NEW_RUN

PREFIX = 'auth-pre-fixture-closure'
KEYS = ('boundary', 'fk_before', 'a:before', 'trainer:before', 'b:before', 'fk_after')
_GUARDS = weakref.WeakKeyDictionary()
_ISSUED = weakref.WeakKeyDictionary()


def require(ok, reason):
    parent.require(ok, 'pre_fixture_' + reason)


def _tree(function):
    return ast.parse(textwrap.dedent(inspect.getsource(function)))


def wiring(closure):
    """Verify exact loaded compositor hooks, not caller-provided hashes/flags."""
    import admission_cleanup_composition as composition
    import admission_fixture_context
    gate_module = sys.modules.get(type(closure.gate).__module__)
    require(type(closure) is composition.Closure and gate_module is not None
            and type(closure.gate) is getattr(gate_module, 'Gate', None),
            'actual_compositor_required')
    selected = [sys.modules[__name__], binding, composition, gate_module,
                admission_fixture_context, parent, tracked, af, durable]
    receipt = binding.verify(closure.gate, selected)
    require(receipt['modules'][3]['relative_path'] == '_offline/phase6e11/endchain_v1/admission_ci.py',
            'actual_gate_source_required')
    require(hasattr(composition.Closure, 'before_bootstrap_write'), 'write_hook_missing_or_changed')
    source = pathlib.Path(gate_module.__file__).read_text(encoding='utf-8-sig')
    _validate_wiring(_tree(composition.Closure.__init__),
                     _tree(composition.Closure.before_bootstrap_write), ast.parse(source))
    return receipt


def _validate_wiring(constructor, hook, tree):
    """Syntax contract only; wiring() also requires actual loaded-source binding."""
    expected = ast.parse('def before_bootstrap_write(self):\n'
                         '    self.pre_fixture.before_bootstrap_write()\n'
                         '    self.fixture_mutation_started = True\n')
    require(ast.dump(hook, include_attributes=False)
            == ast.dump(expected, include_attributes=False), 'write_hook_missing_or_changed')
    assignments = [n for n in ast.walk(constructor) if isinstance(n, ast.Assign)]
    for name, expression in (('fixture_mutation_started', 'False'),
                             ('pre_fixture', 'auth_pre_fixture_closure.Guard(self)')):
        matches = [n for n in assignments if any(isinstance(t, ast.Attribute)
                   and isinstance(t.value, ast.Name) and t.value.id == 'self' and t.attr == name
                   for t in n.targets)]
        require(len(matches) == 1 and ast.dump(matches[0].value) == ast.dump(ast.parse(expression, mode='eval').body),
                'constructor_registration')
    target = ast.dump(ast.parse('admission_fixture_context.run(self, ctx, runtime=tracked)', mode='eval').body)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
             and n.func.value.id == 'admission_fixture_context']
    require(len(calls) == 1 and ast.dump(calls[0]) == target, 'single_fixture_dispatch')
    expected_hook = ast.dump(ast.parse('closure.before_bootstrap_write()').body[0])
    adjacent = False
    for node in ast.walk(tree):
        for _, value in ast.iter_fields(node):
            if not isinstance(value, list):
                continue
            for previous, current in zip(value, value[1:]):
                if (isinstance(current, ast.Expr) and current.value is calls[0]
                        and ast.dump(previous) == expected_hook):
                    adjacent = True
    require(adjacent, 'predispatch_hook_required')


class Guard:
    """Live one-shot capability: close permanently denies future hooked writes."""
    def __init__(self, closure):
        import admission_cleanup_composition as composition
        require(type(closure) is composition.Closure and closure not in _GUARDS
                and closure.started is False and closure.tracked is None
                and closure.fixture_mutation_started is False, 'initial_registration')
        self._owner = weakref.ref(closure)
        self._thread = threading.get_ident()
        self._lock = threading.Lock()
        self._closed = self._mutation = False
        self._binding = None
        self._scope_attempted = False
        self._scope_units = 0
        _GUARDS[closure] = self

    def _live(self):
        owner = self._owner()
        require(owner is not None and _GUARDS.get(owner) is self
                and owner.pre_fixture is self and threading.get_ident() == self._thread,
                'registered_owner_thread')
        return owner

    def before_bootstrap_write(self):
        with self._lock:
            owner = self._live()
            require(not self._closed and not self._mutation, 'write_closed_or_repeated')
            require(owner.fixture_mutation_started is False, 'mutation_state_changed')
            self._mutation = True  # Never reset even when subsequent dispatch fails.

    def close(self, ctx, auth, seal):
        with self._lock:
            owner = self._live()
            require(not self._closed, 'duplicate_close')
            self._closed = True  # Failure permanently denies later dispatch too.
            require(not self._mutation and owner.fixture_mutation_started is False
                    and owner.tracked is None, 'fixture_runtime_or_mutation_started')
            require(getattr(auth._finalizer, '__self__', None) is owner
                    and getattr(auth._finalizer, '__func__', None) is type(owner).finalize,
                    'actual_auth_finalizer_owner')
            owned = parent.owners(ctx, auth, seal)
            self._binding = wiring(owner)
            return owned

    def unchanged(self, ctx, auth, seal, owned):
        with self._lock:
            owner = self._live()
            require(self._closed and not self._mutation and owner.fixture_mutation_started is False
                    and owner.tracked is None, 'closed_state_changed')
            require(parent.owners(ctx, auth, seal) == owned and wiring(owner) == self._binding,
                    'source_or_owner_changed')


class ObservationLedger(parent.Ledger):
    """Reuse parent's immutable ledger and prepaid dispatch interface; six reads."""
    def __init__(self, folder):
        self.charges = dict.fromkeys(KEYS, 1)
        self.plan = {'charges': self.charges, 'reserved_units': 6, 'native_sql_maximum': 6,
                     'http_maximum': 0, 'budget_domain': 'additional_disposable_diagnostic_not_2349',
                     'refunds': False, 'retries': False}
        self.entries, self.spent, self.dispatched = [], 0, set()
        self.storage = durable.Journal(folder, lambda *_: None, PREFIX)
        self.folder = self.storage.folder
        self.write('claim.json', {'run_id': NEW_RUN, 'released': False, 'plan': self.plan})


class Prerequisite:
    """Opaque live capability; serialized flags/hashes cannot instantiate proof."""
    def __init__(self):
        raise TypeError('use_pre_fixture_cleanup')

    def _state(self):
        require(type(self) is Prerequisite and self in _ISSUED, 'unissued_prerequisite')
        return _ISSUED[self]

    @property
    def hashes(self):
        return dict(self._state()['hashes'])

    @property
    def original_error_class(self):
        return type(self._state()['primary']).__name__

    def consume(self, gate, ctx, auth, seal, owned):
        state = self._state()
        require(not state['consumed'], 'prerequisite_replay')
        state['consumed'] = True  # Even failed validation cannot be retried.
        require(gate is state['closure'].gate and ctx is state['ctx']
                and auth is state['auth'] and seal is state['seal'] and owned == state['owned'],
                'prerequisite_context_changed')
        require(state['primary'] is sys.exception(), 'active_original_failure_lost')
        self.unchanged()

    def unchanged(self):
        state = self._state()
        require(state['closure'].gate is state['gate'], 'prerequisite_gate_changed')
        state['guard'].unchanged(state['ctx'], state['auth'], state['seal'], state['owned'])
        _scope_unchanged(state)
        journal = state['journal']
        require(journal.sealed and not journal.poisoned, 'prerequisite_journal_unsealed')
        journal._inventory()
        for name, ref in journal.entries.items():
            journal._read(name, ref)
        for path, expected in state['hashes'].items():
            parent.cparent.reference(state['gate'].out, {'path': path, 'sha256': expected})


def _scope_unchanged(state):
    import fixture_producer_scope as producer
    scope, result = state['scope'], state['scope_result']
    require(state['closure'].scope is None and state['closure'].started is False,
            'prior_scope_attempt_changed')
    require(type(scope) is producer.Scope and scope.gate is state['gate']
            and scope.attempted == {'before'} and scope.baseline == result
            and scope.binding == result['source_binding'] and scope.contract == state['scope_contract'],
            'scope_live_attestation_changed')
    modules = [sys.modules[item['module']] for item in result['source_binding']['modules']]
    require(binding.verify(state['gate'], modules) == result['source_binding']
            and producer.source_contract(state['gate']) == state['scope_contract'], 'scope_sources_changed')


def _attest_scope(closure, ctx, guard, journal, publish):
    """Reuse C's actual validator; the returned receipt is not a global barrier."""
    import fixture_producer_scope as producer
    require(closure.scope is None and closure.started is False and not guard._scope_attempted,
            'prior_scope_attempt_forbids_cleanup')
    require(callable(ctx.get('suspend_admin')) and producer.LIMIT == 10, 'scope_admin_suspension_required')
    guard._scope_attempted = True
    seen = set()
    def save(name, value):
        require(re.fullmatch(r'fixture-producer-scope-before-(intent|result|charge-[0-9]{3})\.json', name)
                is not None and name not in seen, 'scope_record_name_or_replay')
        seen.add(name)
        if '-charge-' in name:
            require(type(value.get('admitted')) is int
                    and value['admitted'] == guard._scope_units + 1
                    and value.get('limit') == 10, 'scope_prepaid_sequence')
            guard._scope_units = value['admitted']  # No refund on save/dispatch uncertainty.
        target = name.replace('fixture-producer-scope-', 'auth-pre-fixture-scope-', 1)
        journal.save(target, value)
        journal._read(target, journal.entries[target])
        publish(target, value)
    gate, original_save = closure.gate, closure.gate.save
    try:
        with ctx['suspend_admin']():
            gate.save = save
            scope = producer.Scope(gate)
            result = scope.before_bootstrap()
    finally:
        gate.save = original_save
    require(type(scope) is producer.Scope and scope.baseline == result and scope.attempted == {'before'},
            'scope_actual_baseline_required')
    require(result.get('status') == 'SCOPE_METADATA_CONFIRMED_NOT_A_BARRIER'
            and result.get('stage') == 'before' and result.get('preparation_run') == NEW_RUN
            and result.get('terminal_ref') is None and result.get('source_binding') == scope.binding
            and result.get('migration_sources_sha256') == producer.digest(scope.contract['hashes'])
            and all(result.get(k) is False for k in ('global_auth_barrier', 'physical_exclusion_held', 'mutation_admitted'))
            and all(type(result.get(k)) is int and result[k] == 10 for k in
                    ('protocol_limit', 'admitted_attempts', 'emitted_attempts')),
            'scope_confirmation_required')
    parent.CProof.protocol(result.get('protocol'), (('begin', 'BEGIN TRANSACTION READ ONLY'),
                                                   *producer.QUERIES, ('rollback', 'ROLLBACK')))
    expected = {'fixture-producer-scope-before-' + n + '.json' for n in
                ['intent', 'result', *('charge-%03d' % i for i in range(1, 11))]}
    require(seen == expected and guard._scope_units == 10, 'scope_complete_recordset')
    return scope, copy.deepcopy(result), copy.deepcopy(scope.contract)


def _issue(closure, ctx, auth, seal, primary):
    """Issue only after actual guard/registry close; immutable local evidence."""
    require(isinstance(primary, BaseException) and primary is sys.exception(), 'active_original_failure_required')
    guard = _GUARDS.get(closure)
    require(type(guard) is Guard and closure.pre_fixture is guard, 'registered_guard_required')
    owned = guard.close(ctx, auth, seal)
    require(closure.scope is None and closure.started is False, 'prior_scope_attempt_forbids_cleanup')
    out = pathlib.Path(closure.gate.out)
    name, digest = auth.registry._close_ref
    close_path = (auth.registry.records.folder / name).relative_to(out).as_posix()
    hashes = {close_path: digest, 'candidate.json': guard._binding['candidate_manifest_sha256']}
    for path, expected in hashes.items():
        parent.cparent.reference(out, {'path': path, 'sha256': expected})
    prefix = 'auth-pre-fixture-prerequisite'
    original_save = closure.gate.save
    def publish(name, value):
        require(not (out / name).exists(), 'prerequisite_publication_exists')
        original_save(name, value)
        observed, original_hash = parent.cparent.read_record(out, name)
        require(durable.raw(observed) == durable.raw(value), 'prerequisite_publication_readback')
        require(name not in hashes, 'prerequisite_duplicate_publication')
        hashes[name] = original_hash
    journal = durable.Journal(out / (prefix + '-private'), publish, prefix)
    scope, scope_result, scope_contract = _attest_scope(closure, ctx, guard, journal, publish)
    journal.save('intent.json', {'status': 'NO_GO', 'preparation_run': NEW_RUN,
        'classification': 'LIVE_PRE_FIXTURE_PREREQUISITE_NOT_CLEANUP',
        'source_binding': guard._binding, 'original_hashes': dict(hashes),
        'owner_hashes': {r: {'subject': tracked.sha(v['actor'].encode()),
                            'email': tracked.sha(v['email'].encode())} for r, v in owned.items()},
        'original_component_error_class': type(primary).__name__,
        'original_claims_released': False, 'global_auth_barrier': False,
        'full_cleanup_proven': False, 'sql_commands': 10, 'http_requests': 0,
        'scope_result_ref': {'path': 'auth-pre-fixture-scope-before-result.json',
                             'sha256': hashes['auth-pre-fixture-scope-before-result.json']},
        'additional_catalog_reserved_units': 10, 'additional_catalog_admitted_attempts': guard._scope_units})
    index = journal.seal()
    # Capture ORIGINAL expected bytes, never adopt a freshly read altered hash.
    for name, ref in index['records'].items():
        hashes[prefix + '-private/' + name] = ref['sha256']
    durable.verify(index, lambda name: parent.cparent.reference(out, {'path': name, 'sha256': hashes[name]}))
    proof = object.__new__(Prerequisite)
    _ISSUED[proof] = {'closure': closure, 'gate': closure.gate, 'guard': guard,
        'ctx': ctx, 'auth': auth, 'seal': seal, 'owned': copy.deepcopy(owned),
        'hashes': hashes, 'primary': primary, 'journal': journal, 'consumed': False,
        'scope': scope, 'scope_result': scope_result, 'scope_contract': scope_contract}
    proof.unchanged()
    return proof


def cleanup(closure, ctx, auth, seal, *, primary, delete_costs):
    """C catalog10 + same delete engine402 =412. Retain original body error.

Successful scoped cleanup returns NO_GO with original error classification. Any
cleanup failure records its class separately and re-raises the original object.
No partial bootstrap, source-free capability, C receipt, replay or refunds.
"""
    require(isinstance(primary, BaseException), 'original_failure_required')
    try:
        # Validate explicit costs before issuing a one-use capability.
        engine_plan = parent.plan(delete_costs)
        proof = _issue(closure, ctx, auth, seal, primary)
        result = parent.finalize(closure.gate, ctx, auth, seal, None,
            delete_costs=delete_costs, pre_fixture_proof=proof)
        summary = {'status': 'NO_GO', 'suffix_status': result['suffix_status'],
            'original_component_error_class': type(primary).__name__,
            'additional_catalog_reserved_units': 10, 'additional_catalog_admitted_attempts': 10,
            'parent_engine_reserved_units': engine_plan['reserved_units'],
            'parent_engine_prepaid_consumed': result['prepaid_consumed'],
            'local_diagnostic_reserved_units': 10 + engine_plan['reserved_units'],
            'local_diagnostic_prepaid_consumed': 10 + result['prepaid_consumed'],
            'budget_domain': 'additional_disposable_diagnostic_not_2349',
            'original_claims_released': False, 'global_auth_zero_claim': False, 'full_chain_admission': False,
            'scope_result_ref': {'path': 'auth-pre-fixture-scope-before-result.json',
                                 'sha256': proof.hashes['auth-pre-fixture-scope-before-result.json']}}
        closure.gate.save('auth-pre-fixture-cleanup.json', summary)
        return {**result, 'pre_fixture_accounting': summary}
    except BaseException as error:
        report = {'status': 'NO_GO', 'preparation_run': NEW_RUN,
            'original_error_class': type(primary).__name__, 'cleanup_error_class': type(error).__name__,
            'original_claims_released': False, 'original_commit_reclassified': False,
            'full_auth_cleanup_proven': False, 'global_auth_zero_claim': False,
            'refunds': 0, 'hosted_requests': 0,
            'additional_catalog_reserved_units': 10,
            'additional_catalog_admitted_attempts': getattr(_GUARDS.get(closure), '_scope_units', 0),
            'parent_engine_accounting': 'separate_auth_parent_finalizer_receipt_if_dispatched',
            'budget_domain': 'additional_disposable_diagnostic_not_2349'}
        try: closure.gate.save('auth-pre-fixture-cleanup-failure.json', report)
        except BaseException as save_error:
            primary.add_note('secondary_pre_fixture_receipt:' + type(save_error).__name__)
        primary.add_note('secondary_pre_fixture_cleanup:' + type(error).__name__)
        raise primary


def observe(closure, ctx, auth, seal, *, primary):
    """Return read-only checkpoint on success; on failure re-raise original object.

Caller must retain/re-raise primary even on successful observation. No engine
dispatch is authorized by this return value. All tokens/raw identities stay private.
"""
    import os
    require(isinstance(primary, BaseException), 'original_failure_required')
    gate = closure.gate
    report = {'status': 'NO_GO', 'preparation_run': NEW_RUN, 'checkpoint': 'BLOCKED',
              'original_error_class': type(primary).__name__, 'secondary_errors': [],
              'cleanup_blocker': 'read_only_api_not_cleanup_use_separate_cleanup_entrypoint',
              'original_claims_released': False, 'original_commit_reclassified': False,
              'full_auth_cleanup_proven': False, 'global_auth_zero_claim': False,
              'server_quiescence_proven': False, 'deletes': 0, 'hosted_requests': 0,
              'refunds': 0, 'snapshots': {}}
    ledger = backend = None
    failed = False
    def secondary(phase, error):
        nonlocal failed
        failed = True
        report['secondary_errors'].append({'phase': phase, 'class': type(error).__name__})
    def native(key, action):
        ledger.before(key)
        try:
            value = action()
            ledger.event({'phase': 'confirmed', 'key': key})
            return value
        except BaseException as error:
            try: ledger.event({'phase': 'unknown', 'key': key, 'error_class': type(error).__name__})
            except BaseException as saved: secondary('observer_unknown_receipt', saved)
            raise
    try:
        require(os.environ.get('GITHUB_ACTIONS') == 'true'
                and os.environ.get('GITHUB_REPOSITORY') == 'Yourizorge/fitmetzorge-staging'
                and os.environ.get('GITHUB_REF') == 'refs/heads/main'
                and gate.container == 'supabase_db_fmz-db41-ci', 'disposable_only')
        ledger = ObservationLedger(pathlib.Path(gate.out) / (PREFIX + '-private'))
        guard = _GUARDS.get(closure)
        require(type(guard) is Guard and closure.pre_fixture is guard, 'registered_guard_required')
        owned = guard.close(ctx, auth, seal)
        report['source_binding'] = guard._binding
        name, digest = auth.registry._close_ref
        report['auth_close_ref'] = {
            'path': (auth.registry.records.folder / name).relative_to(pathlib.Path(gate.out)).as_posix(),
            'sha256': digest}
        parent.cparent.reference(gate.out, report['auth_close_ref'])
        report['owner_hashes'] = {r: {'subject': tracked.sha(v['actor'].encode()),
                                     'email': tracked.sha(v['email'].encode())} for r, v in owned.items()}
        require(ctx.get('test_admin_token') and auth.url in af.ORIGINS, 'private_local_context')
        backend = af.RealBackend({'dsn': ctx['dsn'], 'auth_url': auth.url,
                                  'admin_token': ctx['test_admin_token']})
        require(backend.db.autocommit is True, 'autocommit_required')
        boundary = native('boundary', lambda: backend.db.execute(parent.BOUNDARY).fetchone()['value'])
        require(isinstance(boundary, dict) and set(boundary) == {
            'pg17', 'tls', 'bounded_statement', 'bounded_lock', 'privileged', 'fresh'}
            and all(v is True for v in boundary.values()), 'observer_boundary')
        ids = [v['actor'] for v in owned.values()]
        def fk(key):
            value = native(key, lambda: backend.db.execute(parent.FK, [ids, ids]).fetchone()['value'])
            require(value == {'identities': 0, 'operators': 0}, 'scoped_fk_not_zero')
            report[key] = value
        fk('fk_before')
        for role, item in owned.items():
            guard.unchanged(ctx, auth, seal, owned)
            value = native(role + ':before', lambda: backend.snapshot(
                item['email'], None, item['actor'], item['session_ids']))
            af.validate_snapshot(value)
            require(value['users'] == [{'id': item['actor'], 'email': item['email'], 'marker': None}]
                    and sorted(value['session_ids']) == sorted(item['session_ids']), 'observed_owner_changed')
            report['snapshots'][role] = {'counts': value['counts'],
                'session_hashes': [tracked.sha(s.encode()) for s in value['session_ids']]}
        fk('fk_after')
        guard.unchanged(ctx, auth, seal, owned)
        report['checkpoint'] = 'SCOPED_READ_ONLY_PREFLIGHT_CONFIRMED_NOT_CLEANUP'
    except BaseException as error:
        secondary('pre_fixture_observation', error)
    finally:
        if backend is not None:
            try: backend.close()
            except BaseException as error: secondary('observer_close', error)
        if failed: report['checkpoint'] = 'BLOCKED'
        report['prepaid_consumed'] = ledger.spent if ledger else 0
        report['native_dispatches'] = len(ledger.dispatched) if ledger else 0
        try:
            if ledger:
                ledger.write('result.json', report)
                report['retained_journal'] = ledger.receipt()
            gate.save(PREFIX + '.json', report)
        except BaseException as error:
            secondary('final_receipt', error)
    if failed:
        raise primary
    return report
