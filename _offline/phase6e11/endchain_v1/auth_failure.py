"""Local-only Auth failure component. Not a hosted admission or shared runner."""
import argparse
import hashlib
import json
import os
import pathlib
import re
import secrets
import uuid

from auth_failure_transport import LocalTransport, ORIGINS, UnknownOutcome

OLD_RUN = '6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'
CASES = ('before_dispatch', 'create_lost_reply', 'partial_user', 'partial_session',
         'login_timeout', 'logout_timeout', 'admin_unknown', 'duplicate_request',
         'cleanup_interrupted', 'missing_mint_barrier', 'duplicate_cleanup')
OPERATIONS = ('create', 'login', 'logout', 'delete')
SNAPSHOT_COUNTS = frozenset(('users', 'identities', 'sessions', 'refresh_tokens',
                             'mfa_amr_claims', 'mfa_factors', 'one_time_tokens', 'flow_state'))
NATIVE_SLOTS = ('preflight', 'prefix', 'cleanup_before', 'final') + tuple(
    side + '_' + op for op in OPERATIONS for side in ('stats_before', 'stats_after'))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def validate_snapshot(value):
    counts, users, sessions = value['counts'], value['users'], value['session_ids']
    if (not isinstance(counts, dict) or set(counts) != SNAPSHOT_COUNTS
            or any(type(n) is not int or n < 0 for n in counts.values())
            or not isinstance(users, list) or not isinstance(sessions, list)
            or counts['users'] != len(users) or counts['sessions'] != len(sessions)
            or len(sessions) > 2 or len(set(sessions)) != len(sessions)):
        raise ValueError('auth_failure_snapshot_bounds')
    for key in sessions:
        if not isinstance(key, str) or str(uuid.UUID(key)) != key:
            raise ValueError('auth_failure_snapshot_session_key')


def binding(run_id):
    if str(uuid.UUID(run_id)) != run_id or run_id == OLD_RUN:
        raise ValueError('auth_failure_new_run_required')
    return run_id


def contract(costs):
    if set(costs) != set(OPERATIONS) or any(type(v) is not int or v < 1 for v in costs.values()):
        raise ValueError('auth_failure_managed_cost_contract_required')
    return {'scope': 'LOCAL_DIAGNOSTIC_ONLY', 'managed_sql_prepaid': dict(costs),
            'native_sql_slots': list(NATIVE_SLOTS), 'native_sql_maximum': len(NATIVE_SLOTS),
            'http_dispatch_maximum': 4, 'reserved_units': sum(costs.values()) + len(NATIVE_SLOTS),
            'managed_costs_proven': False, 'planned_2349_run_changed': False,
            'refunds': False, 'automatic_retry': False}


class Journal:
    """Exclusive retained claim and fsynced pre-dispatch entries, including unknowns."""
    def __init__(self, folder, run_id, case, costs):
        self.plan = contract(costs)
        self.charges = {**costs, **dict.fromkeys(NATIVE_SLOTS, 1)}
        self.folder = pathlib.Path(folder)
        self.folder.mkdir()  # Existing claim or crash receipt is never resumed/overwritten.
        self.entries, self.spent, self.dispatched = [], 0, set()
        self.write('claim.json', {'run_id': binding(run_id), 'case': case, 'released': False,
                                 'plan': self.plan})

    def write(self, name, value):
        with (self.folder / name).open('x', encoding='ascii') as f:
            f.write(canonical(value) + '\n')
            f.flush()
            os.fsync(f.fileno())

    def event(self, value):
        row = {'sequence': len(self.entries), **value}
        self.write('event-' + str(len(self.entries)).zfill(3) + '.json', row)
        self.entries.append(row)

    def before(self, key):
        if key in self.dispatched:
            raise ValueError('auth_failure_duplicate_dispatch')
        units = self.charges.get(key)
        if units is None:
            raise ValueError('auth_failure_unregistered_dispatch')
        if self.spent + units > self.plan['reserved_units']:
            raise ValueError('auth_failure_prepaid_exhausted')
        self.event({'phase': 'before_dispatch', 'key': key, 'units': units})
        self.dispatched.add(key)
        self.spent += units

    def receipt(self):
        # Flat parent artifact includes every retained claim/event/result verbatim,
        # with hashes of the fsynced bytes; no recursive artifact glob is needed.
        files = {}
        for path in sorted(self.folder.glob('*.json')):
            raw = path.read_bytes()
            files[path.name] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                                'content': json.loads(raw)}
        return {'format': 'sanitized_auth_failure_journal_v1', 'files': files}


class RealBackend:
    evidence_kind = 'REAL_LOCAL_PG17_GOTRUE'

    def __init__(self, config):
        import psycopg
        from psycopg.conninfo import conninfo_to_dict
        from psycopg.rows import dict_row
        p = conninfo_to_dict(config['dsn'])
        if (p.get('host') != '127.0.0.1' or p.get('hostaddr', '127.0.0.1') != '127.0.0.1'
                or os.environ.get('PGHOSTADDR', '127.0.0.1') != '127.0.0.1'
                or p.get('dbname') != 'postgres' or p.get('sslmode') != 'verify-full'
                or not pathlib.Path(p.get('sslrootcert', '')).is_file()
                or any(k in p for k in ('service', 'servicefile'))):
            raise ValueError('auth_failure_local_tls_boundary')
        self.transport = LocalTransport(config['auth_url'], config['admin_token'], config.get('api_key'))
        self.db = psycopg.connect(config['dsn'], hostaddr='127.0.0.1', autocommit=True,
                                 prepare_threshold=None, row_factory=dict_row, connect_timeout=5,
                                 options='-c statement_timeout=5000 -c lock_timeout=1000')
        if self.db.info.server_version // 10000 != 17:
            self.db.close()
            raise ValueError('auth_failure_pg17_required')

    def close(self):
        self.db.close()

    def stats(self):
        from auth_protocol import STATS
        return self.db.execute('select ' + STATS + ' value').fetchone()['value']

    def difference(self, before, after):
        from auth_protocol import difference
        return difference(before, after)

    def snapshot(self, email, marker, actor, session_ids):
        # Exact run marker and previous immutable keys only; never enumerate members.
        sql = """with picked as (
          select id,email,raw_app_meta_data->>'auth_failure_claim' marker
          from auth.users where email=%s or raw_app_meta_data->>'auth_failure_claim'=%s
            or id=%s::uuid limit 3),
        ids as (select id from picked union select %s::uuid where %s::uuid is not null),
        sessions as (select id from auth.sessions where user_id in (select id from ids)),
        session_keys as (select id from sessions union select unnest(%s::uuid[]))
        select jsonb_build_object(
          'users',(select coalesce(jsonb_agg(p),'[]') from picked p),
          'session_ids',(select coalesce(jsonb_agg(id),'[]') from sessions),
          'counts',jsonb_build_object(
            'users',(select count(*) from picked),
            'identities',(select count(*) from auth.identities where user_id in(select id from ids)),
            'sessions',(select count(*) from sessions),
            'refresh_tokens',(select count(*) from auth.refresh_tokens where user_id in(select id::text from ids)),
            'mfa_amr_claims',(select count(*) from auth.mfa_amr_claims where session_id in(select id from session_keys)),
            'mfa_factors',(select count(*) from auth.mfa_factors where user_id in(select id from ids)),
            'one_time_tokens',(select count(*) from auth.one_time_tokens where user_id in(select id from ids)),
            'flow_state',(select count(*) from auth.flow_state where user_id in(select id from ids)))) value"""
        return self.db.execute(sql, (email, marker, actor, actor, actor, session_ids)).fetchone()['value']

    def http(self, *args, **kwargs):
        return self.transport.request(*args, **kwargs)


class Case:
    def __init__(self, backend, folder, run_id, name, costs, transport_factory=None):
        if name not in CASES:
            raise ValueError('auth_failure_case')
        self.backend, self.name = backend, name
        self.transport_factory = transport_factory
        self.run_id = binding(run_id)
        self.email = 'fmz-af-' + uuid.uuid5(uuid.UUID(run_id), name).hex + '@example.invalid'
        self.marker = digest(run_id + ':' + name)
        self.password = secrets.token_urlsafe(32)
        self.actor, self.token, self.session_ids = None, None, []
        self.journal = Journal(folder, run_id, name, costs)
        self.baseline_absent = self.mint_closed = self.cleanup_started = False
        self.terminals, self.observed_costs = {}, {}
        self.http_failures, self.observer_failures = [], []
        self.journal_failures = []
        self.raised_failure = None
        self.injected = False

    def request(self, ledger):
        if self.transport_factory is None:
            return self.backend.http
        return self.transport_factory(self.run_id, ledger, self.backend.transport).request

    def native(self, key, call):
        self.journal.before(key)
        try:
            result = call()
        except Exception as error:
            self.journal.event({'phase': 'unknown', 'key': key, 'error_class': type(error).__name__})
            raise
        self.journal.event({'phase': 'confirmed', 'key': key})
        return result

    def snapshot(self, key):
        value = self.native(key, lambda: self.backend.snapshot(
            self.email, self.marker, self.actor, self.session_ids))
        validate_snapshot(value)
        users = value['users']
        if users:
            if (len(users) != 1 or users[0]['email'] != self.email or users[0]['marker'] != self.marker
                    or (self.actor is not None and users[0]['id'] != self.actor)):
                raise ValueError('auth_failure_ownership_mismatch')
            self.actor = str(uuid.UUID(users[0]['id']))
        self.session_ids = sorted(set(self.session_ids + value['session_ids']))
        if len(self.session_ids) > 2:
            raise ValueError('auth_failure_snapshot_bounds')
        self.journal.event({'phase': 'snapshot', 'key': key, 'counts': value['counts'],
                            'actor_sha256': digest(self.actor) if self.actor else None,
                            'session_sha256': [digest(x) for x in self.session_ids]})
        return value

    def auth(self, op, fault=None):
        self.raised_failure = None
        if op in self.journal.dispatched:
            raise ValueError('auth_failure_duplicate_dispatch')
        if self.mint_closed and op in ('create', 'login'):
            raise ValueError('auth_failure_mint_barrier_closed')
        if any(n > self.journal.plan['managed_sql_prepaid'][key] for key, n in self.observed_costs.items()):
            raise ValueError('auth_failure_managed_contract_exceeded')
        before = self.native('stats_before_' + op, self.backend.stats)
        self.journal.before(op)
        self.terminals[op] = False
        result = None
        error = None
        http_phase = 'http_dispatch'
        http_failure = None
        try:
            if op == 'create':
                result = self.request(self.journal)('POST', '/admin/users', {
                    'email': self.email, 'password': self.password, 'email_confirm': True,
                    'app_metadata': {'auth_failure_claim': self.marker}}, fault=fault)
            elif op == 'login':
                result = self.request(self.journal)('POST', '/token?grant_type=password',
                                           {'email': self.email, 'password': self.password}, fault=fault)
            elif op == 'logout':
                result = self.request(self.journal)('POST', '/logout?scope=global', {}, token=self.token, fault=fault)
            elif op == 'delete':
                result = self.request(self.journal)('DELETE', '/admin/users/' + self.actor, fault=fault)
            http_phase = 'http_response_validation'
            self.terminals[op] = result['terminal'] is True
            if not 200 <= result['status'] < 300:
                raise ValueError('auth_failure_http_status')
            if op == 'login':
                self.token = result['body']['access_token']
            http_phase = 'http_receipt'
            self.journal.event({'phase': 'confirmed', 'key': op, 'http_status': result['status']})
        except Exception as caught:
            error = caught
            if isinstance(caught, UnknownOutcome):
                self.terminals[op] = caught.terminal
            http_failure = {'operation': op, 'phase': http_phase, 'error_class': type(caught).__name__}
            self.http_failures.append(http_failure)
            self.raised_failure = http_failure
            try:
                self.journal.event({'phase': 'unknown', 'key': op, 'terminal': self.terminals[op],
                                    'failure': http_failure})
            except Exception as save_error:
                self.journal_failures.append({'operation': op, 'phase': 'http_unknown_receipt',
                    'error_class': type(save_error).__name__, 'secondary_to_http': True})
                # The existing prepaid entry remains spent even if the outcome
                # cannot be persisted. Never replace the original HTTP exception.
                raise caught from save_error
        # Statistics are evidence, not refunds, and are counted as separate native reads.
        observer_phase = 'stats_after'
        try:
            after = self.native('stats_after_' + op, self.backend.stats)
            observer_phase = 'managed_difference'
            observed = self.backend.difference(before, after)
            observer_phase = 'managed_receipt'
            self.journal.event({'phase': 'managed_observed', 'key': op, 'load': observed,
                                'within_prepaid': observed['commands'] <= self.journal.plan['managed_sql_prepaid'][op]})
            self.observed_costs[op] = observed['commands']
        except Exception as observer_error:
            detail = {'operation': op, 'phase': observer_phase,
                      'error_class': type(observer_error).__name__, 'secondary_to_http': error is not None}
            self.observer_failures.append(detail)
            self.raised_failure = http_failure if error is not None else detail
            try:
                self.journal.event({'phase': 'observer_failed', 'key': op, 'failure': detail,
                                    'primary_http_failure': http_failure})
            except Exception:
                # Failed persistence must not replace the original HTTP/observer error.
                # The pre-dispatch entry and retained in-memory receipt remain NO-GO.
                pass
            if error is not None:
                raise error from observer_error
            raise
        if error is not None:
            self.raised_failure = http_failure
            raise error
        if observed['commands'] > self.journal.plan['managed_sql_prepaid'][op]:
            raise ValueError('auth_failure_managed_contract_exceeded')
        return result

    def cleanup(self):
        if self.cleanup_started:
            raise ValueError('auth_failure_duplicate_cleanup')
        self.cleanup_started = True
        self.mint_closed = True
        if self.name == 'missing_mint_barrier':
            self.terminals['login'] = False
        if not all(self.terminals.values()) or not self.baseline_absent:
            return {'confirmed': False, 'reason': 'mint_barrier_or_ownership_unproven'}
        before = self.snapshot('cleanup_before')
        if not any(before['counts'].values()):
            # Only a stopped prefix with NO HTTP dispatch can release without delete.
            no_dispatch = not self.terminals
            final = self.snapshot('final')
            return {'confirmed': no_dispatch and not any(final['counts'].values()),
                    'reason': 'no_auth_dispatched' if no_dispatch else 'zero_without_delete_proof',
                    'delete_confirmed': False, 'zero_observed': not any(final['counts'].values())}
        if not before['users'] or self.actor is None:
            return {'confirmed': False, 'reason': 'owned_user_not_proven'}
        if self.name == 'cleanup_interrupted':
            return {'confirmed': False, 'reason': 'injected_before_cleanup_dispatch'}
        deleted = False
        try:
            self.auth('delete', 'lost_reply' if self.name == 'admin_unknown' else None)
            deleted = True
        except Exception:
            pass
        final = self.snapshot('final')
        zero = not any(final['counts'].values())
        return {'confirmed': deleted and zero and all(self.terminals.values()),
                'reason': 'delete_and_absence_proven' if deleted and zero else 'delete_unconfirmed_or_residual',
                'delete_confirmed': deleted, 'zero_observed': zero, 'counts': final['counts']}

    def execute(self):
        primary = 'missing_injected_failure'
        primary_detail = None
        cleanup = {'confirmed': False, 'reason': 'not_started'}
        prefix = None
        try:
            baseline = self.snapshot('preflight')
            if any(baseline['counts'].values()):
                raise ValueError('auth_failure_baseline_not_empty')
            self.baseline_absent = True
            if self.name == 'before_dispatch':
                self.injected = True
                raise ValueError('auth_failure_stop_before_dispatch')
            if self.name == 'create_lost_reply':
                self.injected = True
            self.auth('create', 'lost_reply' if self.name == 'create_lost_reply' else None)
            if self.name == 'partial_user':
                self.injected = True
                raise ValueError('auth_failure_stop_after_user')
            if self.name in ('partial_session', 'login_timeout'):
                self.injected = True
            self.auth('login', {'partial_session': 'lost_reply', 'login_timeout': 'timeout'}.get(self.name))
            if self.name == 'logout_timeout':
                self.injected = True
                self.auth('logout', 'timeout')
            if self.name == 'duplicate_request':
                self.injected = True
                self.auth('login')
            self.injected = True
            raise ValueError('auth_failure_injected_' + self.name)
        except Exception as error:
            primary_detail = self.raised_failure or {'phase': 'execution', 'error_class': type(error).__name__}
            primary = str(error) if isinstance(error, (ValueError, UnknownOutcome)) and re.fullmatch(
                r'auth_failure_[a-z_]+', str(error)) else 'auth_failure_unexpected_' + type(error).__name__
        finally:
            self.mint_closed = True
            try:
                prefix = self.snapshot('prefix')['counts']
                cleanup = self.cleanup()
                if self.name == 'duplicate_cleanup':
                    before = len(self.journal.dispatched)
                    try:
                        self.cleanup()
                    except ValueError as error:
                        cleanup['duplicate_blocked'] = str(error) == 'auth_failure_duplicate_cleanup'
                    cleanup['duplicate_zero_dispatch'] = before == len(self.journal.dispatched)
            except Exception as error:
                cleanup = {'confirmed': False, 'reason': 'cleanup_exception', 'error_class': type(error).__name__}
            self.password = self.token = None
        costs_ok = all(n <= self.journal.plan['managed_sql_prepaid'][op] for op, n in self.observed_costs.items())
        expected_unresolved = self.name in ('admin_unknown', 'cleanup_interrupted', 'missing_mint_barrier')
        outcome_matches = cleanup['confirmed'] is (not expected_unresolved)
        http = [k for k in OPERATIONS if k in self.journal.dispatched]
        measured = set(http) == set(self.observed_costs)
        expected_http = {
            'before_dispatch': [], 'create_lost_reply': ['create', 'delete'],
            'partial_user': ['create', 'delete'], 'partial_session': ['create', 'login', 'delete'],
            'login_timeout': ['create', 'login', 'delete'],
            'logout_timeout': ['create', 'login', 'logout', 'delete'],
            'admin_unknown': ['create', 'login', 'delete'],
            'duplicate_request': ['create', 'login', 'delete'],
            'cleanup_interrupted': ['create', 'login'], 'missing_mint_barrier': ['create', 'login'],
            'duplicate_cleanup': ['create', 'login', 'delete']}[self.name]
        expected_primary = {
            'before_dispatch': 'auth_failure_stop_before_dispatch',
            'create_lost_reply': 'auth_failure_http_unknown', 'partial_user': 'auth_failure_stop_after_user',
            'partial_session': 'auth_failure_http_unknown', 'login_timeout': 'auth_failure_http_unknown',
            'logout_timeout': 'auth_failure_http_unknown', 'duplicate_request': 'auth_failure_duplicate_dispatch'
        }.get(self.name, 'auth_failure_injected_' + self.name)
        prefix_ok = prefix is not None and prefix['users'] == (0 if self.name == 'before_dispatch' else 1)
        expected_sessions = 1 if self.name in ('partial_session', 'login_timeout', 'admin_unknown',
            'duplicate_request', 'cleanup_interrupted', 'missing_mint_barrier', 'duplicate_cleanup') else 0
        prefix_ok = prefix_ok and prefix['sessions'] == expected_sessions
        special_ok = True
        if self.name == 'admin_unknown':
            special_ok = cleanup.get('zero_observed') is True and cleanup.get('delete_confirmed') is False
        elif self.name == 'cleanup_interrupted':
            special_ok = cleanup['reason'] == 'injected_before_cleanup_dispatch'
        elif self.name == 'missing_mint_barrier':
            special_ok = cleanup['reason'] == 'mint_barrier_or_ownership_unproven'
        elif self.name == 'duplicate_cleanup':
            special_ok = cleanup.get('duplicate_blocked') is True and cleanup.get('duplicate_zero_dispatch') is True
        journal_complete = not self.journal_failures
        checked = (self.injected and outcome_matches and costs_ok and measured and journal_complete and prefix_ok and special_ok
                   and http == expected_http and primary == expected_primary)
        snapshots = [row for row in self.journal.entries if row['phase'] == 'snapshot']
        report = {'case': self.name, 'run_id': self.run_id, 'execution_status': 'NO_GO',
                  'component_case_pass': checked, 'primary_failure': primary,
                  'primary_failure_detail': primary_detail, 'http_failures': self.http_failures,
                  'observer_failures': self.observer_failures,
                  'journal_failures': self.journal_failures, 'journal_complete': journal_complete,
                  'evidence_kind': self.backend.evidence_kind, 'prefix_counts': prefix,
                  'cleanup': cleanup, 'claim_released': cleanup['confirmed'] and costs_ok and measured and journal_complete,
                  'mint_barrier': self.mint_closed and all(self.terminals.values()),
                  'mint_barrier_scope': 'sealed_client_dispatch_and_complete_upstream_response',
                  'gotrue_process_quiescence_proven': False, 'hosted_mint_barrier_proven': False,
                  'http_dispatches': http, 'native_sql_dispatches': len(self.journal.dispatched) - len(http),
                  'prepaid_consumed': self.journal.spent, 'reserved': self.journal.plan['reserved_units'],
                  'observed_managed_sql': self.observed_costs, 'managed_within_prepaid': costs_ok,
                  'observed_total_sql': sum(self.observed_costs.values()) + len(self.journal.dispatched) - len(http),
                  'http_sql_measurements_complete': measured, 'refunds': 0, 'retry': False,
                  'hosted_requests': 0, 'full_chain_admission': False,
                  'claim_retained_file': True}
        report['owned_scope_audit'] = {'actor_sha256': digest(self.actor) if self.actor else None,
            'session_sha256': [digest(x) for x in self.session_ids],
            'claim_marker_sha256': digest(self.marker),
            'last_observation': snapshots[-1] if snapshots else None,
            'observation_is_global_zero': False, 'observation_is_current_after_teardown': False}
        self.journal.write('result.json', report)
        report['retained_journal'] = self.journal.receipt()
        return report


class ReconciliationJournal(Journal):
    def __init__(self, case, original, original_sha):
        self.charges = {'observe': 1}
        if case.name == 'cleanup_interrupted':
            self.charges.update(stats_before_delete=1, stats_after_delete=1, verify_zero=1,
                                delete=case.journal.plan['managed_sql_prepaid']['delete'])
        reserve = sum(self.charges.values())
        if reserve > original['reserved'] - original['prepaid_consumed']:
            raise ValueError('auth_failure_reconciliation_reserve_unavailable')
        self.plan = {'reserved_units': reserve, 'scope': 'LOCAL_SAFETY_RECONCILIATION',
                     'original_allocation_unchanged': True, 'charges': self.charges}
        self.folder = case.journal.folder / 'safety-reconciliation'
        self.folder.mkdir()
        self.entries, self.spent, self.dispatched = [], 0, set()
        self.write('claim.json', {'run_id': case.run_id, 'case': case.name,
            'original_result_sha256': original_sha, 'plan': self.plan,
            'original_prepaid_consumed': original['prepaid_consumed'], 'refunds': 0})


def reconcile_retained(case):
    """Explicit local suffix; never replay uncertain HTTP or erase original NO-GO."""
    original_path = case.journal.folder / 'result.json'
    raw = original_path.read_bytes()
    original_sha = hashlib.sha256(raw).hexdigest()
    original = json.loads(raw)
    result = {'case': case.name, 'run_id': case.run_id, 'status': 'BLOCKED',
        'original_result_sha256': original_sha, 'original_execution_status': original['execution_status'],
        'original_claim_released': original['claim_released'], 'reconciliation_confirmed': False,
        'scoped_zero_observed': False, 'delete_confirmed': False, 'refunds': 0,
        'global_auth_zero_claim': False, 'full_auth_cleanup_proven': False,
        'hosted_mint_barrier_proven': False, 'hosted_requests': 0, 'full_chain_admission': False,
        'native_sql_dispatches': 0, 'http_dispatches': 0, 'prepaid_consumed': 0}
    if (original['claim_released'] or not original['component_case_pass']
            or original['run_id'] != case.run_id or original['case'] != case.name
            or case.name not in ('admin_unknown', 'cleanup_interrupted', 'missing_mint_barrier')
            or not case.baseline_absent or not original['managed_within_prepaid']
            or not original['http_sql_measurements_complete']):
        return {**result, 'reason': 'original_failure_or_cost_proof_not_eligible'}
    try:
        journal = ReconciliationJournal(case, original, original_sha)
    except ValueError:
        return {**result, 'reason': 'no_complete_reconciliation_reserve'}

    def native(key, call):
        journal.before(key)
        try:
            value = call()
        except Exception as error:
            journal.event({'phase': 'unknown', 'key': key, 'error_class': type(error).__name__})
            raise
        journal.event({'phase': 'confirmed', 'key': key})
        return value

    def observe(key):
        value = native(key, lambda: case.backend.snapshot(case.email, case.marker, case.actor, case.session_ids))
        validate_snapshot(value)
        users = value['users']
        if (case.actor is None or original['owned_scope_audit']['actor_sha256'] != digest(case.actor)
                or len(users) > 1 or any(row != {'id': case.actor, 'email': case.email, 'marker': case.marker}
                                       for row in users)):
            raise ValueError('auth_failure_reconciliation_ownership')
        journal.event({'phase': 'snapshot', 'key': key, 'counts': value['counts'],
                       'actor_sha256': digest(case.actor),
                       'session_sha256': [digest(x) for x in value['session_ids']]})
        return value

    try:
        before = observe('observe')
        result['owned_counts_before'] = before['counts']
        result['scoped_zero_observed'] = not any(before['counts'].values())
        if case.name == 'missing_mint_barrier' or not (case.mint_closed and original['mint_barrier']
                                                      and all(case.terminals.values())):
            result['reason'] = 'missing_mint_barrier_no_new_independent_terminal_evidence'
        elif case.name == 'admin_unknown' or 'delete' in case.journal.dispatched:
            result['reason'] = 'original_delete_unknown_no_replay_no_retroactive_ack'
        elif (not before['users'] or before['counts'] != original['prefix_counts']
              or sorted(before['session_ids']) != sorted(case.session_ids)):
            result['reason'] = 'owned_snapshot_changed_or_absence_without_delete_proof'
        else:
            stats_before = native('stats_before_delete', case.backend.stats)
            journal.before('delete')
            try:
                response = case.request(journal)('DELETE', '/admin/users/' + case.actor)
                if response['terminal'] is not True or not 200 <= response['status'] < 300:
                    raise UnknownOutcome()
                journal.event({'phase': 'confirmed', 'key': 'delete', 'http_status': response['status']})
                result['delete_confirmed'] = True
            except Exception as error:
                result['primary_http_error_class'] = type(error).__name__
                journal.event({'phase': 'unknown', 'key': 'delete', 'error_class': type(error).__name__})
            measured = False
            try:
                stats_after = native('stats_after_delete', case.backend.stats)
                load = case.backend.difference(stats_before, stats_after)
                result['observed_managed_sql'] = load['commands']
                journal.event({'phase': 'managed_observed', 'key': 'delete', 'load': load,
                               'within_prepaid': load['commands'] <= journal.charges['delete']})
                measured = load['commands'] <= journal.charges['delete']
            except Exception as error:
                result['observer_error_class'] = type(error).__name__
                journal.event({'phase': 'observer_failed', 'key': 'delete', 'error_class': type(error).__name__})
            final = observe('verify_zero')
            result['owned_counts_after'] = final['counts']
            result['scoped_zero_observed'] = not any(final['counts'].values())
            if result['delete_confirmed'] and measured and result['scoped_zero_observed']:
                result.update(status='LOCAL_SCOPED_RECONCILIATION_CONFIRMED', reconciliation_confirmed=True,
                              reason='previously_unsent_exact_owned_delete_and_absence_confirmed')
            else:
                result['reason'] = 'reconciliation_delete_measurement_or_absence_unproven'
    except Exception as error:
        result.update(reason='reconciliation_unconfirmed', error_class=type(error).__name__)
    result.update(native_sql_dispatches=len(journal.dispatched - {'delete'}),
                  http_dispatches=int('delete' in journal.dispatched), prepaid_consumed=journal.spent,
                  combined_prepaid_consumed=original['prepaid_consumed'] + journal.spent,
                  original_reserved=original['reserved'],
                  original_result_unchanged=original_path.read_bytes() == raw)
    if not result['original_result_unchanged']:
        result.update(status='BLOCKED', reconciliation_confirmed=False, reason='original_receipt_changed')
    journal.write('result.json', result)
    result['retained_journal'] = journal.receipt()
    return result


def prerequisites(config):
    required = ('dsn', 'auth_url', 'admin_token', 'run_id', 'managed_costs',
                'environment', 'exclusive_local_auth')
    missing = [k for k in required if not isinstance(config, dict) or not config.get(k)]
    if missing:
        return missing
    binding(config['run_id'])
    contract(config['managed_costs'])
    if config['auth_url'] not in ORIGINS:
        raise ValueError('auth_failure_local_origin_required')
    if config['environment'] != 'disposable_ci' or config['exclusive_local_auth'] is not True:
        raise ValueError('auth_failure_exclusive_disposable_required')
    return []


def context_from_ci(ctx, *, run_id, managed_costs, exclusive_local_auth):
    """Memory-only adapter for ci_auth.environment(..., include_test_admin=True)."""
    return {'dsn': ctx['dsn'], 'auth_url': ctx['auth'].url,
            'admin_token': ctx.get('test_admin_token'), 'run_id': run_id,
            'managed_costs': managed_costs, 'environment': 'disposable_ci',
            'exclusive_local_auth': exclusive_local_auth}


def run(gate, *, safety_reconciliation=False, transport_factory=None):
    """Parent provides private gate.auth_failure_context; no bootstrap/CI dispatch."""
    if transport_factory is not None and not callable(transport_factory):
        raise ValueError('auth_failure_transport_factory')
    config = getattr(gate, 'auth_failure_context', None)
    if type(safety_reconciliation) is not bool:
        raise ValueError('auth_failure_explicit_reconciliation_option')
    try:
        missing = prerequisites(config)
    except (ValueError, TypeError, AttributeError):
        missing = ['valid_new_run_local_origin_and_managed_cost_contract']
    if missing:
        report = {'status': 'BLOCKED', 'missing_prerequisites': missing,
                  'mutation_started': False, 'hosted_requests': 0, 'full_chain_admission': False}
        gate.save('auth-failure-prerequisites.json', report)
        return report
    folder = pathlib.Path(gate.out) / ('auth_failure_' + config['run_id'])
    if folder.exists():
        raise ValueError('auth_failure_existing_claims_no_retry')
    try:
        backend = RealBackend(config)
    except Exception as error:
        report = {'status': 'BLOCKED', 'missing_prerequisites': ['validated_loopback_pg17_tls_backend'],
                  'error_class': type(error).__name__, 'mutation_started': False,
                  'hosted_requests': 0, 'full_chain_admission': False}
        gate.save('auth-failure-prerequisites.json', report)
        return report
    try:
        folder.mkdir()
        cases = [Case(backend, folder / name, str(uuid.uuid4()), name, config['managed_costs'], transport_factory=transport_factory) for name in CASES]
        reports = [case.execute() for case in cases]
        reconciliations = [reconcile_retained(case) for case, report in zip(cases, reports)
                           if not report['claim_released']] if safety_reconciliation else []
    finally:
        backend.close()
    result = {'status': 'LOCAL_AUTH_FAILURE_COMPONENT_PASS' if all(r['component_case_pass'] for r in reports)
              else 'LOCAL_AUTH_FAILURE_COMPONENT_FAILED', 'cases': reports,
              'preparation_run_id': config['run_id'], 'fresh_disposable_case_ids': True,
              'contract': contract(config['managed_costs']), 'local_diagnostic_only': True,
              'hosted_requests': 0, 'full_chain_admission': False,
              'global_auth_zero_claim': False, 'full_auth_cleanup_proven': False,
              'full_auth_cleanup_status': 'NOT_PROVEN',
              'safety_reconciliation_requested': safety_reconciliation, 'safety_reconciliations': reconciliations,
              'reconciliation_diagnostic_totals': {
                  'native_sql_dispatches': sum(r['native_sql_dispatches'] for r in reconciliations),
                  'http_dispatches': sum(r['http_dispatches'] for r in reconciliations),
                  'prepaid_consumed': sum(r['prepaid_consumed'] for r in reconciliations),
                  'drawn_from_original_unused_reserve': True},
              'retained_claims': [r['case'] for r in reports if not r['claim_released']],
              'retained_object_audit': [{'case': r['case'], 'run_id': r['run_id'], **r['owned_scope_audit']}
                                       for r in reports if not r['claim_released']],
              'diagnostic_totals': {'native_sql_dispatched': sum(r['native_sql_dispatches'] for r in reports),
                  'http_dispatched': sum(len(r['http_dispatches']) for r in reports),
                  'prepaid_consumed': sum(r['prepaid_consumed'] for r in reports),
                  'reserved': sum(r['reserved'] for r in reports),
                  'observed_managed_sql': sum(sum(r['observed_managed_sql'].values()) for r in reports),
                  'all_managed_observations_complete': all(r['http_sql_measurements_complete'] for r in reports),
                  'parent_environment_setup_and_teardown_included': False},
              'source_sha256': {name: hashlib.sha256((pathlib.Path(__file__).parent / name).read_bytes()).hexdigest()
                                for name in ('auth_failure.py', 'auth_failure_transport.py')}}
    gate.save('auth-failure-component.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--exclusive-disposable', action='store_true',
                        help='attest parent-owned isolated disposable local PG17/GoTrue')
    parser.add_argument('--safety-reconciliation', action='store_true',
                        help='separate exact owned cleanup suffix; never replay unknown requests')
    parser.add_argument('--managed-costs', required=True, help='JSON positive integer costs for create/login/logout/delete')
    args = parser.parse_args()
    class Gate:
        out = args.out
        sources = pathlib.Path(__file__).resolve().parents[3]
        auth_failure_context = {'dsn': os.environ.get('FMZ_AUTH_FAILURE_DSN'),
            'auth_url': os.environ.get('FMZ_AUTH_FAILURE_URL'), 'admin_token': os.environ.get('FMZ_AUTH_FAILURE_ADMIN'),
            'api_key': os.environ.get('FMZ_AUTH_FAILURE_API_KEY'), 'run_id': args.run_id,
            'environment': 'disposable_ci' if args.exclusive_disposable else None,
            'exclusive_local_auth': args.exclusive_disposable,
            'managed_costs': json.loads(args.managed_costs)}

        def save(self, name, value):
            with (pathlib.Path(self.out) / name).open('x', encoding='ascii') as stream:
                stream.write(canonical(value) + '\n')
    try:
        result = run(Gate(), safety_reconciliation=args.safety_reconciliation)
        print(canonical({'status': result['status'], 'full_chain_admission': False}))
        return 0 if result['status'] == 'LOCAL_AUTH_FAILURE_COMPONENT_PASS' else 2
    except Exception as error:
        print(canonical({'status': 'BLOCKED', 'error_class': type(error).__name__, 'full_chain_admission': False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
