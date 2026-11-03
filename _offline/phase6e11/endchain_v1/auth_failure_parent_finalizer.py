"""One-shot local parent Auth suffix after actual source-bound C closure.

Main callback: finalize(gate, ctx, auth, seal, c_receipt_ref, delete_costs=...).
No partial-bootstrap adoption, SQL mutations, retries, or global-zero claim.

C must first seal fixture-parent-closure-journal-index.json; the receipt reference
is its private fixture-parent-closure-result.json, not the flat summary. Its
intent binds the same three actor hashes, this live Auth registry's closed-record
reference and a TRACKED_DB_BACKENDS_TERMINAL record with confirmed native protocol.
Main/C still own complete producer coverage and loaded-source binding; matching
receipt bytes alone cannot establish coverage of unregistered writers.

The separate fixture-parent-physical-zero-private/result.json route requires its
sealed journal, original fixture journal and complete case set, matching producer
observations/source bindings, native terminal/zero protocols and C.protocol_plan
(N,E). Original fixture COMMITs remain unknown and their claims remain held.
Neither route admits the before-fixture/partial-bootstrap case without C proof.

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
import re
import sys
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


class PhysicalCProof(CProof):
    """Separate C route: current locked absence never resolves historic COMMIT."""
    def __init__(self, gate, ref, owned, auth, seal):
        import fixture_parent_physical_zero as physical
        import fixture_producer_scope as producer
        import fixture_db_terminality as db
        self.out, self.hashes = pathlib.Path(gate.out), {}
        self.auth, self.seal = auth, seal
        self.original_commit_unknown = True
        prefix = physical.PREFIX
        require(isinstance(ref, dict) and ref.get('path') == prefix + '-private/result.json', 'physical_receipt_path')
        result = self.reference(ref)
        index = self.read(prefix + '-journal-index.json')
        durable.verify(index, lambda name: self.read(name))

        def record(name):
            return self.reference({'path': prefix + '-private/' + name,
                                   'sha256': index['records'][name]['sha256']})

        require(record('result.json') == result, 'physical_sealed_result')
        intent = record('intent.json')
        require(result.get('status') == 'NO_GO' and result.get('preparation_run') == NEW_RUN
                and result.get('classification') == 'REGISTRY_CLOSED_WITH_ORIGINAL_COMMIT_UNKNOWN', 'physical_not_ready')
        for key in ('physical_zero', 'registry_commit_confirmed', 'registry_absence_confirmed',
                    'registry_deletion_proven', 'fixture_suffix_commit_confirmed', 'original_receipts_unchanged'):
            require(result.get(key) is True, 'physical_confirmation_' + key)
        for key in ('registry_commit_unknown', 'original_claims_released', 'original_commit_reclassified',
                    'unknown_fixture_delete_replayed', 'auth_objects_touched', 'global_auth_barrier',
                    'future_privileged_connections_excluded', 'full_cleanup_proven'):
            require(result.get(key) is False, 'physical_historical_or_global_claim')
        require(not any(k in result for k in ('error_class', 'evidence_error_class', 'reason'))
                and result.get('registry_remaining_counts') == {'identities': 0, 'operators': 0}
                and result.get('deleted_identities') == 3 and result.get('deleted_operators') == 1,
                'physical_registry_result')
        hashes = {C_ROLES[r]: tracked.sha(v['actor'].encode()) for r, v in owned.items()}
        require(result.get('actor_hashes') == hashes and intent.get('actor_hashes') == hashes
                and intent.get('preparation_run') == NEW_RUN, 'physical_actor_binding')

        selected = [physical, producer, db, cparent, physical.binding, physical.sql, durable,
                    sys.modules[physical.parameters.__module__], sys.modules[physical.NativeRuntime.__module__],
                    sys.modules[physical.Blocked.__module__]]
        require(result.get('source_binding') == physical.binding.verify(gate, selected), 'physical_source_binding')
        # Pin the manifest itself: later per-delete checks cannot adopt a changed candidate.
        self.read('candidate.json')
        contract = producer.source_contract(gate)
        original = intent.get('original_hashes')
        require(isinstance(original, dict) and 1 <= len(original) <= 1800, 'physical_original_hashes')
        for path, expected in original.items():
            self.reference({'path': path, 'sha256': expected})
        bootstrap = self.reference({'path': 'admission-fixture-bootstrap.json',
                                    'sha256': original.get('admission-fixture-bootstrap.json')})
        require(bootstrap == intent.get('bootstrap') and bootstrap.get('actor_hashes') == hashes
                and bootstrap.get('status') == 'DISPOSABLE_BOOTSTRAP_PASS'
                and bootstrap.get('registered_accounts') == 3
                and bootstrap.get('before') == {'identities': 0, 'operators': 0}
                and bootstrap.get('existing_rows_overwritten') is False
                and bootstrap.get('commit_confirmed') is True
                and bootstrap.get('after_registry_confirmed') is True, 'physical_original_bootstrap')

        evidence = cparent.Evidence(gate)
        cases = physical.load_cases(evidence, hashes)
        ids = [case['fixture_case'] for case, _, _ in cases]
        unknown = [(case, context, original_ref) for case, context, original_ref in cases if original_ref is not None]
        eligible = []
        for case, context, original_ref in cases:
            if original_ref is None and not (case['receipt'].get('status') == 'COMPONENT_PASS'
                                            and case['receipt'].get('cleanup_complete') is True):
                cparent.ownership(evidence, case, context, actor_hashes=hashes)
                eligible.append(case['fixture_case'])
        require(unknown and result.get('case_ids') == ids and intent.get('case_ids') == ids
                and result.get('eligible_case_ids') == eligible and intent.get('eligible_case_ids') == eligible
                and result.get('unknown_case_ids') == [c['fixture_case'] for c, _, _ in unknown], 'physical_complete_scope')
        expected_plan = physical.protocol_plan(len(cases), len(eligible))
        self.protocol(result.get('protocol'), expected_plan)
        require(all(type(result.get(k)) is int and result[k] == len(expected_plan)
                    for k in ('expected_protocol_commands', 'admitted_attempts', 'emitted_attempts'))
                and result.get('protocol_limit') == len(expected_plan) + 1
                and intent.get('protocol_limit') == len(expected_plan) + 1
                and intent.get('additional_scope_observation_limit') == producer.LIMIT
                and intent.get('additional_unknown_zero_limit') == len(unknown) * db.ZERO_LIMIT,
                'physical_protocol_counts')
        close_name, close_hash = auth.registry._close_ref
        close_ref = {'path': (auth.registry.records.folder / close_name).relative_to(self.out).as_posix(), 'sha256': close_hash}
        require(result.get('auth_close_ref') == close_ref and intent.get('auth_close_ref') == close_ref
                and original.get(close_ref['path']) == close_hash, 'physical_same_live_auth_seal')
        self.reference(close_ref)
        terminal_ref = result.get('terminal_ref')
        terminal = self.reference(terminal_ref)
        require(intent.get('terminal_ref') == terminal_ref and original.get(terminal_ref['path']) == terminal_ref['sha256'],
                'physical_terminal_reference')
        component = evidence.get('fixture-cleanup-db-terminal.json')
        require(component.get('terminal') == terminal and component.get('component_status') == 'COMPONENT_PASS'
                and sorted(component.get('fixture_case_ids', [])) == sorted(ids), 'physical_original_terminal_binding')
        require(terminal.get('status') == 'NO_GO' and terminal.get('preparation_run') == NEW_RUN
                and terminal.get('classification') == 'TRACKED_DB_BACKENDS_TERMINAL'
                and terminal.get('db_terminality_proven') is True
                and type(terminal.get('registered_sessions')) is int and 1 <= terminal['registered_sessions'] <= db.MAX_CONNECTIONS
                and terminal.get('terminal_commands') == db.TERMINAL_LIMIT
                and terminal.get('auth_mint_barrier_proven') is False
                and terminal.get('external_producers_covered') is False
                and terminal.get('full_cleanup_proven') is False, 'physical_actual_db_terminal_required')
        self.hexhash(terminal.get('registered_sessions_sha256'))
        self.protocol(terminal.get('protocol'), (('observer_identity', db.SESSION), ('backend_absence', db.ACTIVITY)))

        zero_records = result.get('cases')
        require(isinstance(zero_records, list) and len(zero_records) == len(unknown), 'physical_zero_case_records')
        zero_plan = (('zero_begin', 'BEGIN TRANSACTION READ ONLY'), ('zero_session', db.SESSION),
                     ('backend_absence', db.ACTIVITY), ('zero_inventory', physical.sql.INVENTORY), ('zero_rollback', 'ROLLBACK'))
        for entry, (case, context, original_ref) in zip(zero_records, unknown):
            uid = case['fixture_case']
            historical = self.reference(original_ref)
            require(historical.get('status') == 'NO_GO' and historical.get('commit_unknown') is True
                    and all(historical.get(k) is False for k in ('commit_confirmed', 'cleanup_complete', 'deletion_proven')),
                    'physical_unknown_history_preserved')
            require(entry.get('case') == uid and entry.get('original_ref') == original_ref
                    and entry.get('classification') == 'physical_zero_original_commit_unknown'
                    and entry.get('original_status') == 'NO_GO'
                    and entry.get('physical_zero_record') == uid + '-physical-zero.json', 'physical_zero_entry')
            zero = record(uid + '-physical-zero.json')
            require(physical.digest(zero) == entry.get('zero_sha256') and zero.get('status') == 'NO_GO'
                    and zero.get('classification') == 'physical_zero_original_commit_unknown'
                    and zero.get('preparation_run') == NEW_RUN and zero.get('case') == uid
                    and zero.get('scope_sha256') == physical.digest(physical.parameters(context))
                    and zero.get('terminal_sha256') == physical.digest(terminal)
                    and zero.get('original_ref') == original_ref and zero.get('original_commit_unknown') is True
                    and zero.get('physical_zero') is True, 'physical_zero_binding')
            require(all(zero.get(k) is False for k in ('delete_replayed', 'deletion_proven', 'original_claims_released',
                        'full_cleanup_proven', 'external_producers_covered', 'registry_cleanup_admitted')),
                    'physical_zero_not_historical_authority')
            require(zero.get('protocol_limit') == db.ZERO_LIMIT and zero.get('admitted_attempts') == db.ZERO_LIMIT,
                    'physical_zero_protocol_counts')
            self.protocol(zero.get('protocol'), zero_plan)

        scope_binding = physical.binding.verify(gate, [producer, producer.binding, sys.modules[producer.Protocol.__module__],
            producer.fixture_sql, sys.modules[producer.NativeRuntime.__module__], sys.modules[producer.parser.__module__],
            sys.modules[producer.reference.__module__]])
        before = self.read('fixture-producer-scope-before-result.json')
        after = self.read('fixture-producer-scope-after-result.json')
        identity_keys = ('cluster_id', 'postmaster_start', 'datid', 'migration_sources_sha256')
        for stage, observation in (('before', before), ('after', after)):
            require(observation.get('status') == 'SCOPE_METADATA_CONFIRMED_NOT_A_BARRIER'
                    and observation.get('stage') == stage and observation.get('preparation_run') == NEW_RUN
                    and observation.get('terminal_ref') == (None if stage == 'before' else terminal_ref)
                    and observation.get('source_binding') == scope_binding
                    and all(observation.get(k) is False for k in ('global_auth_barrier', 'physical_exclusion_held', 'mutation_admitted')),
                    'physical_scope_observation')
            require(observation.get('protocol_limit') == producer.LIMIT
                    and observation.get('admitted_attempts') == producer.LIMIT
                    and observation.get('emitted_attempts') == producer.LIMIT, 'physical_scope_protocol_counts')
            self.protocol(observation.get('protocol'), (('begin', 'BEGIN TRANSACTION READ ONLY'),
                                                       *producer.QUERIES, ('rollback', 'ROLLBACK')))
            require(all(isinstance(observation.get(k), str) and observation[k] for k in identity_keys)
                    and observation.get('migration_sources_sha256') == physical.digest(contract['hashes'])
                    and observation.get('tables') == list(producer.TABLES) and observation.get('auth_fk_noaction_count') == 9,
                    'physical_scope_identity')
            self.hexhash(observation.get('metadata_sha256'))
        require(physical.digest(after) == intent.get('scope_sha256')
                and all(before[k] == after[k] for k in identity_keys), 'physical_scope_chain')
        held = record('locked-zero-before-delete.json')
        require(held.get('all_case_ids') == ids and held.get('lock_mode') == 'SHARE ROW EXCLUSIVE'
                and held.get('original_claims_released') is False
                and all(held['scope'].get(k) == after[k] for k in identity_keys)
                and held['scope'].get('tables') == list(producer.TABLES)
                and held['scope'].get('auth_fk_noaction_count') == 9, 'physical_locked_scope')
        self.hexhash(held['scope'].get('metadata_sha256'))
        expected_registry = cparent.expected_registry({C_ROLES[r]: v['actor'] for r, v in owned.items()})
        require(isinstance(held.get('registry'), dict) and set(held['registry']) == set(expected_registry)
                and all(cparent.same_rows(held['registry'][k], expected_registry[k]) for k in expected_registry),
                'physical_locked_registry_ownership')
        for label, key in (('delete-operator.json', 'operators'), ('delete-identities.json', 'identities')):
            deleted = record(label)
            require(cparent.same_rows(deleted.get('returned'), expected_registry[key]) and deleted.get('commit_confirmed') is False,
                    'physical_registry_returning')
        absent = record('locked-absence.json')
        require(absent.get('all_scopes_physically_zero') is True and absent.get('registry_absent') is True
                and absent.get('original_commit_reclassified') is False
                and absent.get('future_privileged_connections_excluded') is False, 'physical_locked_absence')
        evidence.unchanged()
        require(all(original.get(path) == expected for path, expected in evidence.hashes.items()), 'physical_original_hash_coverage')
        self.unchanged()

    @staticmethod
    def hexhash(value):
        require(isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None, 'physical_digest')

    def reference(self, ref):
        value = cparent.reference(self.out, ref)
        require(ref['path'] not in self.hashes or self.hashes[ref['path']] == ref['sha256'], 'physical_reference_changed')
        self.hashes[ref['path']] = ref['sha256']
        return value


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
        proof_type = PhysicalCProof if isinstance(c_receipt_ref, dict) and c_receipt_ref.get('path') == (
            'fixture-parent-physical-zero-private/result.json') else CProof
        proof = proof_type(gate, c_receipt_ref, owned, auth, seal)
        result['original_fixture_commit_unknown'] = getattr(proof, 'original_commit_unknown', False)
        result['original_commit_reclassified'] = False
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
