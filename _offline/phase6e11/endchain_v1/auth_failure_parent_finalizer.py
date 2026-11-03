"""One-shot local parent Auth suffix after actual source-bound C closure.

Main callback: finalize(gate, ctx, auth, seal, c_receipt_ref, delete_costs=...).
No partial-bootstrap adoption, SQL mutations, retries, or global-zero claim.

C must first seal fixture-parent-closure-journal-index.json; the receipt reference
is its private fixture-parent-closure-result.json, not the flat summary. Its
intent binds the same three actor hashes, this live Auth registry's closed-record
reference and a TRACKED_DB_BACKENDS_TERMINAL record with confirmed native protocol.
Main/C still own complete producer coverage and loaded-source binding; matching
receipt bytes alone cannot establish coverage of unregistered writers.

At explicitly preregistered 128/delete, the separate maximum is402: 3 deletes,
18 observers (boundary1, scoped FK2, ownership3, stats6, per-delete absence3,
final absence3). No allowance is inferred from the parent bootstrap budget.
All raw users/emails/session keys stay private; receipts contain hashes/counts.
The existing strict-TLS RealBackend supplies actual observations in CI, but this
module's tests mock SQL/C and prove only local HTTP/control/accounting behavior.
Session-row absence is not immediate revocation of every stateless access JWT.
"""
import json
import os
import pathlib
import uuid

import auth_failure as af
import auth_failure_tracked as tracked
import admission_journal as durable
import fixture_parent_closure as cparent
from admission_binding import NEW_RUN

ROLES = ('a', 'trainer', 'b')
C_ROLES = dict(zip(ROLES, ('a_member', 'a_trainer', 'b_member')))
PREFIX = 'auth-parent-finalizer'
NATIVE = ('boundary', 'fk_before') + tuple(r + ':before' for r in ROLES) + tuple(
    r + ':' + op for r in ROLES for op in ('stats_before_delete', 'stats_after_delete', 'after')) + (
    'fk_after',) + tuple(r + ':final' for r in ROLES)
BOUNDARY = """select jsonb_build_object(
 'pg17',current_setting('server_version_num')::int/10000=17,
 'tls',exists(select 1 from pg_stat_ssl where pid=pg_backend_pid() and ssl),
 'bounded_statement',current_setting('statement_timeout') in ('5s','5000ms'),
 'bounded_lock',current_setting('lock_timeout') in ('1s','1000ms'),
 'privileged',current_user='postgres' and current_database()='postgres',
 'fresh',current_setting('transaction_isolation')='read committed') value"""
FK = """select jsonb_build_object(
 'identities',(select count(*) from fmz6e11_private.identities where user_id=any(%s::uuid[])),
 'operators',(select count(*) from fmz6e11_private.operators where user_id=any(%s::uuid[]))) value"""


def require(condition, reason):
    if not condition:
        raise tracked.Blocked('parent_auth_' + reason)


def plan(delete_costs):
    require(isinstance(delete_costs, dict) and set(delete_costs) == set(ROLES)
            and all(type(v) is int and v > 0 for v in delete_costs.values()), 'explicit_delete_costs')
    charges = {**dict.fromkeys(NATIVE, 1), **{r + ':delete': delete_costs[r] for r in ROLES}}
    return {'charges': charges, 'reserved_units': sum(charges.values()),
            'native_sql_maximum': len(NATIVE), 'http_maximum': 3,
            'budget_domain': 'additional_disposable_diagnostic_not_2349',
            'observed_cost_bound': False, 'refunds': False, 'retries': False}


class Ledger(af.Journal):
    """Existing before/event interface, with immutable verified durable bytes."""
    def __init__(self, folder, delete_costs):
        self.plan = plan(delete_costs)
        self.charges = self.plan['charges']
        self.entries, self.spent, self.dispatched = [], 0, set()
        self.storage = durable.Journal(folder, lambda *_: None, PREFIX)
        self.folder = self.storage.folder
        self.write('claim.json', {'run_id': NEW_RUN, 'released': False, 'plan': self.plan})

    def validate(self):
        require(not self.storage.poisoned, 'journal_poisoned')
        try:
            self.storage._inventory()
            return {name: self.storage._read(name, ref) for name, ref in self.storage.entries.items()}
        except BaseException as error:
            self.storage._poison('validate', None, error)
            raise

    def write(self, name, value):
        self.validate()
        try:
            self.storage.save(name, value)
            require(self.storage._read(name, self.storage.entries[name]) == durable.raw(value), 'journal_readback')
        except BaseException as error:
            self.storage._poison('write_readback', name, error)
            raise

    def receipt(self):
        snapshot = self.validate()
        return {'format': 'sanitized_parent_auth_journal_v1', 'files': {
            name: {**self.storage.entries[name], 'content': json.loads(raw)}
            for name, raw in snapshot.items()}}


def owners(ctx, auth, seal):
    require(type(auth) is tracked.TrackedAuth and ctx.get('auth') is auth
            and ctx.get('auth_request_registry') is auth.registry, 'live_auth_context')
    require(auth.registry.run_id == NEW_RUN and auth.registry.valid_proof(seal), 'live_terminal_seal')
    require(set(auth._owners) == set(ROLES) and set(ctx['claims']) == set(ROLES)
            and set(ctx['accounts']) == set(ROLES), 'complete_original_bootstrap_required')
    records = auth.registry.records.export()
    bound = [r['content'] for r in records.values() if r['content']['kind'] == 'parent_owner']
    require(len(bound) == 3, 'original_owner_records')
    result = {}
    for role in ROLES:
        actor, email = ctx['claims'][role]['sub'], ctx['accounts'][role]['email']
        sid = ctx['claims'][role]['session_id']
        require(isinstance(actor, str) and str(uuid.UUID(actor)) == actor
                and actor not in (NEW_RUN, af.OLD_RUN)
                and isinstance(sid, str) and str(uuid.UUID(sid)) == sid
                and isinstance(email, str) and email.endswith('@example.invalid'), 'synthetic_owner')
        require(auth._owners[role] == actor and auth._created.get(actor) == tracked.sha(email.encode()), 'owner_changed')
        require(sum(r.get('role') == role and r.get('subject_sha256') == tracked.sha(actor.encode())
                    and r.get('email_sha256') == tracked.sha(email.encode()) for r in bound) == 1,
                'original_bootstrap_binding')
        result[role] = {'actor': actor, 'email': email, 'session_ids': [sid]}
    require(len({v['actor'] for v in result.values()}) == 3, 'distinct_owners')
    return result


class CProof:
    """Verify C's sealed scope/command evidence, never just caller barrier flags."""
    def __init__(self, gate, ref, owned, auth, seal):
        self.out, self.hashes = pathlib.Path(gate.out), {}
        self.auth, self.seal = auth, seal
        require(isinstance(ref, dict) and ref.get('path') ==
                'fixture-parent-closure-private/fixture-parent-closure-result.json', 'c_receipt_required')
        result = cparent.reference(self.out, ref)
        self.hashes[ref['path']] = ref['sha256']
        index = self.read('fixture-parent-closure-journal-index.json')
        durable.verify(index, lambda name: self.read(name))
        def record(name):
            expected = index['records'][name]['sha256']
            return self.read('fixture-parent-closure-private/' + name, expected)
        require(record('fixture-parent-closure-result.json') == result, 'c_sealed_result')
        intent = record('fixture-parent-closure-intent.json')
        hashes = {C_ROLES[r]: tracked.sha(v['actor'].encode()) for r, v in owned.items()}
        require(result.get('preparation_run') == NEW_RUN
                and result.get('suffix_status') == 'SCOPED_PARENT_CLOSURE_CONFIRMED'
                and result.get('unresolved_case_ids') == []
                and result.get('original_receipts_unchanged') is True
                and result.get('auth_objects_touched') is False, 'c_not_ready')
        require(intent['bootstrap'].get('actor_hashes') == hashes
                and intent['bootstrap'].get('commit_confirmed') is True
                and intent.get('unresolved_cases') == [], 'c_owner_scope')
        original = intent['original_hashes']
        require(isinstance(original, dict) and 1 <= len(original) <= 1800, 'c_original_chain')
        for path, expected in original.items():
            self.read(path, expected)
        registry = record('fixture-parent-closure-registry-result.json')
        require(registry == result.get('registry') and registry.get('status') == 'SCOPED_CLOSURE_CONFIRMED'
                and all(registry.get(k) is True for k in ('commit_confirmed', 'absence_confirmed', 'deletion_proven'))
                and registry.get('commit_unknown') is False and not registry.get('close_unknown')
                and registry.get('remaining_counts') == {'identities': 0, 'operators': 0}
                and registry.get('deleted_identities') == 3 and registry.get('deleted_operators') == 1,
                'c_registry_not_closed')
        self.protocol(registry['protocol'], (
            ('registry_begin', 'BEGIN'), ('registry_check', cparent.sql.CHECK),
            ('registry_lock', cparent.REGISTRY_LOCK), ('registry_before', cparent.REGISTRY),
            ('registry_delete_operator', cparent.DELETE_OPERATOR),
            ('registry_delete_identities', cparent.DELETE_IDENTITIES), ('registry_commit', 'COMMIT'),
            ('registry_absence_begin', 'BEGIN TRANSACTION READ ONLY'), ('registry_check', cparent.sql.CHECK),
            ('registry_absence', cparent.REGISTRY), ('registry_absence_rollback', 'ROLLBACK')))
        terminal = intent['terminal_barrier']
        require(terminal.get('preparation_run') == NEW_RUN and terminal.get('actor_hashes') == hashes,
                'c_terminal_scope')
        refs = terminal.get('evidence_refs')
        require(isinstance(refs, list) and 1 <= len(refs) <= 16, 'c_terminal_evidence')
        close_name, close_hash = auth.registry._close_ref
        close_path = (auth.registry.records.folder / close_name).relative_to(self.out).as_posix()
        require({'path': close_path, 'sha256': close_hash} in refs, 'c_same_live_auth_seal_required')
        db_terminal = []
        for item in refs:
            value = self.read(item['path'], item['sha256'])
            require(original.get(item['path']) == item['sha256'], 'c_terminal_original_binding')
            if value.get('classification') == 'TRACKED_DB_BACKENDS_TERMINAL':
                db_terminal.append(value)
        require(len(db_terminal) == 1, 'c_actual_db_terminal_evidence_required')
        db = db_terminal[0]
        require(db.get('preparation_run') == NEW_RUN and db.get('db_terminality_proven') is True
                and type(db.get('registered_sessions')) is int and db['registered_sessions'] > 0
                and db.get('terminal_commands') == 2, 'c_db_terminal_record')
        from fixture_db_terminality import SESSION, ACTIVITY
        self.protocol(db['protocol'], (('observer_identity', SESSION), ('backend_absence', ACTIVITY)))
        self.unchanged()

    @staticmethod
    def protocol(events, expected):
        require(isinstance(events, list) and len(events) == len(expected), 'c_protocol_length')
        for ordinal, (event, (phase, sql)) in enumerate(zip(events, expected), 1):
            require(event.get('ordinal') == ordinal and event.get('phase') == phase
                    and event.get('confirmed') is True and event.get('sql_sha256') == tracked.sha(sql.encode()),
                    'c_protocol_unconfirmed')

    def read(self, path, expected=None):
        value, actual = cparent.read_record(self.out, path, expected)
        require(path not in self.hashes or self.hashes[path] == actual, 'c_receipt_changed')
        self.hashes[path] = actual
        return value

    def unchanged(self):
        require(self.auth.registry.valid_proof(self.seal), 'live_terminal_seal_lost')
        for path, expected in self.hashes.items():
            cparent.read_record(self.out, path, expected)


def finalize(gate, ctx, auth, seal, c_receipt_ref, *, delete_costs):
    """Return scoped confirmation; on ANY failure persist NO_GO then raise primary."""
    require(os.environ.get('GITHUB_ACTIONS') == 'true'
            and os.environ.get('GITHUB_REPOSITORY') == 'Yourizorge/fitmetzorge-staging'
            and os.environ.get('GITHUB_REF') == 'refs/heads/main'
            and getattr(gate, 'container', None) == 'supabase_db_fmz-db41-ci', 'disposable_only')
    ledger = Ledger(pathlib.Path(gate.out) / (PREFIX + '-private'), delete_costs)
    result = {'status': 'NO_GO', 'suffix_status': 'BLOCKED', 'preparation_run': NEW_RUN,
        'full_auth_cleanup_proven': False, 'full_chain_admission': False, 'global_auth_zero_claim': False,
        'server_quiescence_proven': False, 'original_claims_released': False, 'refunds': 0,
        'hosted_requests': 0, 'plan': ledger.plan, 'deletes': {}, 'snapshots': {}, 'secondary_errors': []}
    backend = proof = None
    primary = None
    phase = 'ownership'

    def secondary(stage, error):
        result['secondary_errors'].append({'phase': stage, 'class': type(error).__name__})

    def native(key, call):
        ledger.before(key)
        try:
            value = call()
            ledger.event({'phase': 'confirmed', 'key': key})
            return value
        except BaseException as error:
            try: ledger.event({'phase': 'unknown', 'key': key, 'error_class': type(error).__name__})
            except BaseException as save_error: secondary('native_unknown_receipt', save_error)
            raise

    def snapshot(role, label, *, absent):
        item = owned[role]
        value = native(role + ':' + label, lambda: backend.snapshot(
            item['email'], None, item['actor'], item['session_ids']))
        af.validate_snapshot(value)
        result['snapshots'][role + ':' + label] = {'counts': value['counts'],
            'session_hashes': [tracked.sha(s.encode()) for s in value['session_ids']]}
        if absent:
            require(not any(value['counts'].values()), 'scoped_auth_residual')
        else:
            require(value['users'] == [{'id': item['actor'], 'email': item['email'], 'marker': None}]
                    and sorted(value['session_ids']) == sorted(item['session_ids']), 'observed_owner_or_session_changed')
        return value

    def fk(key):
        ids = [v['actor'] for v in owned.values()]
        observed = native(key, lambda: backend.db.execute(FK, [ids, ids]).fetchone()['value'])
        require(observed == {'identities': 0, 'operators': 0}, 'parent_fixture_fk_remains')

    try:
        owned = owners(ctx, auth, seal)
        result['owner_hashes'] = {r: {'subject': tracked.sha(v['actor'].encode()),
                                    'email': tracked.sha(v['email'].encode())} for r, v in owned.items()}
        phase = 'c_closure'
        proof = CProof(gate, c_receipt_ref, owned, auth, seal)
        ledger.write('c-binding.json', {'original_hashes': proof.hashes, 'owners': result['owner_hashes']})
        phase = 'local_observer'
        require(ctx.get('test_admin_token') and auth.url in af.ORIGINS, 'private_local_context')
        backend = af.RealBackend({'dsn': ctx['dsn'], 'auth_url': auth.url, 'admin_token': ctx['test_admin_token']})
        require(backend.db.autocommit is True, 'autocommit_observer_required')
        boundary = native('boundary', lambda: backend.db.execute(BOUNDARY).fetchone()['value'])
        require(isinstance(boundary, dict)
                and set(boundary) == {'pg17', 'tls', 'bounded_statement', 'bounded_lock', 'privileged', 'fresh'}
                and all(v is True for v in boundary.values()),
                'observer_boundary')
        fk('fk_before')
        for role in ROLES:
            snapshot(role, 'before', absent=False)
        for role in ROLES:
            phase = role + ':delete'
            proof.unchanged()
            require(owners(ctx, auth, seal) == owned, 'context_owner_changed')
            before = native(role + ':stats_before_delete', backend.stats)
            ledger.before(role + ':delete')
            delete_error = None
            try:
                response = auth.delete_owned(seal, owned[role]['actor'], ledger, role + ':delete')
                require(response['terminal'] is True and 200 <= response['status'] < 300, 'delete_unconfirmed')
                ledger.event({'phase': 'confirmed', 'key': role + ':delete'})
                result['deletes'][role] = {'acknowledged': True}
            except BaseException as error:
                delete_error = error
                result['deletes'][role] = {'acknowledged': False, 'error_class': type(error).__name__}
                try: ledger.event({'phase': 'unknown', 'key': role + ':delete', 'error_class': type(error).__name__})
                except BaseException as save_error: secondary('delete_unknown_receipt', save_error)
            for stage, action in (
                    ('measure', lambda: backend.difference(before, native(role + ':stats_after_delete', backend.stats))),
                    ('absence', lambda: snapshot(role, 'after', absent=True))):
                try:
                    value = action()
                    if stage == 'measure':
                        result['deletes'][role]['observed_managed_sql'] = value
                        require(type(value['commands']) is int and 0 <= value['commands'] <= delete_costs[role],
                                'delete_cost_exceeded')
                except BaseException as error:
                    if delete_error is None: delete_error = error
                    else: secondary(role + ':' + stage, error)
            if delete_error is not None:
                raise delete_error
        phase = 'final_scoped_absence'
        fk('fk_after')
        for role in ROLES:
            snapshot(role, 'final', absent=True)
        proof.unchanged()
        ledger.validate()
        result['suffix_status'] = 'SCOPED_PARENT_AUTH_CLEANUP_CONFIRMED'
    except BaseException as error:
        primary = error
        result['primary_failure'] = {'phase': phase, 'class': type(error).__name__}
        if isinstance(error, tracked.Blocked): result['reason'] = str(error)
    finally:
        if backend is not None:
            try: backend.close()
            except BaseException as error:
                if primary is None: primary = error
                else: secondary('observer_close', error)
        if proof is not None:
            try: proof.unchanged()
            except BaseException as error:
                if primary is None: primary = error
                else: secondary('final_evidence', error)
        if primary is not None:
            result['suffix_status'] = 'NO_GO'
        result['prepaid_consumed'] = ledger.spent
        result['native_dispatches'] = len(ledger.dispatched.intersection(NATIVE))
        result['http_attempts'] = len(ledger.dispatched - set(NATIVE))
        try:
            ledger.write('result.json', result)
            result['retained_journal'] = ledger.receipt()
            gate.save(PREFIX + '.json', result)
        except BaseException as error:
            if primary is None: primary = error
            else: secondary('final_receipt', error)
    if primary is not None:
        raise primary
    return result
