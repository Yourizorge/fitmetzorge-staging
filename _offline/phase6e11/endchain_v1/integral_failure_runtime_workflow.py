"""Concrete rollback-isolated native workflow components on the existing 47 stack.

Main provides the SAME private gate.auth_failure_context used by auth_failure.run.
No app actors are reused. The existing Auth Case owns creation/cleanup of three
fresh, marker-bound registered-alias accounts. No Auth or fixture implementation
is substituted. Product setup/control changes exist only in a transaction that
is always rolled back; no controller quota is activated. Consequently these are
actual component boundaries, not durable full-chain/HTTP/strict-WAL evidence.

Two migration boundaries remain explicitly unsupported: the app stack is already
47/47; this component must not reapply migrations or reset it to manufacture them.
"""
import copy
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import threading
import time
import uuid

import integral_failure_runtime as rt

HERE = pathlib.Path(__file__).resolve().parent
PREFIX = rt.PREFIX
SUPPORTED = tuple(x for x in rt.REQUIRED if x not in ('pre_migration', 'post_migration'))
SOURCES = tuple(PREFIX + x for x in (
    'integral_failure_runtime_workflow.py', 'integral_failure_runtime_worker.mjs',
    'auth_failure.py', 'auth_failure_transport.py', 'auth_protocol.py',
    'fixture_lifecycle.py', 'fixture_cleanup_runtime.py', 'fixture_cleanup_runtime_sql.py',
    'fixture_cleanup_evidence.py', 'scenario.py', 'native_store.mjs', 'budget.mjs')) + (
    '_offline/phase6e11/controller_v1/core.mjs', '_offline/phase6e11/controller_v1/store.mjs',
    '_offline/phase6e11/edge/core.mjs', '_offline/phase6e11/edge/frozen.mjs',
    '_offline/phase6e11/readiness_v1/workflow_audit_v1/workflow_local.py',
    'supabase/migrations/20260916162120_phase6e11_final_app_integration.sql',
    'supabase/migrations/20261012104331_phase6e11_controller_evidence.sql',
    'supabase/migrations/20261012185121_phase6e11_single_endchain_budget.sql',
    'supabase/migrations/20261018070231_phase6e11_recovery_run_quota.sql')
ALIASES = {'member': 'zorgeyouri+6e9-a-lid@gmail.com',
           'trainer': 'zorgeyouri+6e9-a-trainer@gmail.com',
           'b': 'zorgeyouri+6e9-b-lid@gmail.com'}
ROLES = {'member': 'a_member', 'trainer': 'a_trainer', 'b': 'b_member'}
# The unchanged bridge calls this function. This tests the native product
# boundary, not the registered transport, evidence pairs or strict WAL gate.
API = 'select fmz6e11_private.api_call(%s::jsonb) value'
BIND = "select set_config('request.jwt.claims',%s,true),set_config('request.headers',%s,true)"
CONTROL = """select
 (select count(*) from fmz6e11_private.identities)::integer identities,
 (select count(*) from fmz6e11_controller_private.runs where state='running')::integer running,
 (select count(*) from fmz6e11_private.config where enabled)::integer enabled,
 (select count(*) from fmz6e11_request_private.control where enabled)::integer bridge,
 (select count(*) from supabase_migrations.schema_migrations)::integer migrations"""


class DeadlineBackend:
    """Same real Auth implementation; reject new work that cannot fit its timeout."""
    def __init__(self, backend, deadline):
        self.backend, self.deadline = backend, deadline
        self.db, self.evidence_kind = backend.db, backend.evidence_kind

    def remaining(self, bound):
        if time.monotonic() + bound >= self.deadline:
            raise rt.Blocked('failure_auth_component_deadline')

    def stats(self):
        self.remaining(5)
        return self.backend.stats()

    def snapshot(self, *args):
        self.remaining(5)
        return self.backend.snapshot(*args)

    def http(self, *args, **kwargs):
        # Includes the existing relay's bounded joins; changes no HTTP timeout.
        self.remaining(15)
        return self.backend.http(*args, **kwargs)

    @property
    def transport(self):
        return self.backend.transport

    def guarded_factory(self, factory):
        if factory is None:
            return None
        backend = self
        def create(owner, ledger, upstream):
            if upstream is not backend.transport:
                raise rt.Blocked('failure_auth_transport_identity')
            adapter = factory(owner, ledger, upstream)
            class Guarded:
                def request(self, *args, **kwargs):
                    # Keep the original per-dispatch deadline, including suffixes.
                    backend.remaining(15)
                    return adapter.request(*args, **kwargs)
            return Guarded()
        return create

    def difference(self, before, after):
        return self.backend.difference(before, after)

    def close(self):
        self.backend.close()


def dollar(text, args):
    values = []
    def replace(match):
        value = args[int(match[1]) - 1]
        values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
        return '%s'
    return re.sub(r'\$(\d+)', replace, text.replace('%', '%%')), values


class WorkflowDriver:
    def __init__(self, gate, *, local_component_authorized=False, transport_factory=None):
        if transport_factory is not None and not callable(transport_factory):
            raise ValueError('failure_auth_transport_factory')
        self.gate = gate
        self.transport_factory = transport_factory
        self.local_component_authorized = local_component_authorized is True
        self.config = getattr(gate, 'auth_failure_context', None)
        self.actors, self.auth_results = {}, []
        self.backend = None
        self.bootstrap_units = 0
        self.bootstrap_native = 0
        self.bootstrap_managed = 0
        self.opened = False

    def describe(self):
        from auth_failure import prerequisites, contract
        available = SUPPORTED
        missing = []
        try:
            missing = prerequisites(self.config)
            if self.config and self.config.get('run_id') != rt.NEW_RUN:
                missing.append('central_new_preparation_binding')
        except (ValueError, TypeError, AttributeError):
            missing = ['source_owned_local_auth_context_and_costs']
        if missing:
            available = ('timeout', 'mid_controller', 'closure_failure')
        if not self.local_component_authorized:
            available = ()
            missing.append('explicit_local_component_authorization')
        costs = contract(self.config['managed_costs'])['reserved_units'] if not missing else 0
        cases = {name: {'limit': 128, 'cleanup_reserve': 16,
                       'artifact_files': 0, 'artifact_bytes': 0} for name in available}
        for name in ('mid_auth', 'lost_reply'):
            if name in cases:
                # The Auth component owns its separate exact pre-dispatch ledger.
                cases[name].update(artifact_files=100, artifact_bytes=262144,
                                   delegated_auth_reserved=costs)
        return {'preparation_run': rt.NEW_RUN, 'environment': 'disposable_ci',
                'reuse_existing_stack': True, 'historical_registry_read_only': True,
                'sources': list(SOURCES), 'cases': cases,
                'bootstrap_artifact_files': 200 if not missing else 0,
                'bootstrap_artifact_bytes': 1048576 if not missing else 0,
                'prerequisite_details': missing,
                'blocked': {'pre_migration': 'clean47_already_applied_no_reset_or_reapply',
                            'post_migration': 'need_C_actual_migration_dispatch_receipt_no_replay'}}

    def open(self, runtime, selection):
        if not self.local_component_authorized or runtime.environment != 'disposable_ci':
            raise rt.Blocked('failure_explicit_local_component_authorization_required')
        self.opened = True
        if not set(selection) - {'timeout', 'mid_controller', 'closure_failure'}:
            return
        from auth_failure import RealBackend, Case
        if not hasattr(self, 'deadline'):
            raise rt.Blocked('failure_parent_deadline_required')
        self.backend = DeadlineBackend(RealBackend(self.config), self.deadline)
        witness = runtime.connect()
        try:
            if (witness.info.host, witness.info.port, witness.info.dbname) != (
                    self.backend.db.info.host, self.backend.db.info.port, self.backend.db.info.dbname):
                raise rt.Blocked('failure_auth_must_share_disposable_database')
        finally:
            witness.close()
        folder = pathlib.Path(self.gate.out) / ('integral-component-auth-' + uuid.uuid4().hex)
        folder.mkdir()
        self.folder = folder
        # A fresh exact alias is required by the unchanged product principal.
        # Existing aliases or unknown markers are refused, never adopted/deleted.
        for role, email in ALIASES.items():
            case = Case(self.backend, folder / role, str(uuid.uuid4()), 'partial_session',
                        self.config['managed_costs'],
                        transport_factory=self.backend.guarded_factory(self.transport_factory))
            self.actors[role] = case
            case.email = email
            baseline = case.snapshot('preflight')
            if any(baseline['counts'].values()):
                raise rt.Blocked('failure_alias_not_fresh')
            case.baseline_absent = True
            case.auth('create')
            # Login does not require a guessed user id; prefix independently binds both.
            case.auth('login')
            prefix = case.snapshot('prefix')
            if prefix['counts']['users'] != 1 or prefix['counts']['sessions'] != 1 or len(case.session_ids) != 1:
                raise rt.Blocked('failure_actual_auth_prefix')
            case.mint_closed = True

    def close(self):
        reports = []
        close_error = None
        try:
            for role, case in self.actors.items():
                try:
                    cleanup = case.cleanup()
                except BaseException as error:
                    cleanup = {'confirmed': False, 'error_class': type(error).__name__}
                self.bootstrap_units += case.journal.spent
                self.bootstrap_native += len(case.journal.dispatched - {'create','login','logout','delete'})
                self.bootstrap_managed += sum(case.observed_costs.values())
                try:
                    journal = case.journal.receipt()
                except BaseException as error:
                    journal = {'retained_on_disk': True, 'error_class': type(error).__name__}
                reports.append({'role': role, 'cleanup': cleanup,
                                'consumed': case.journal.spent, 'refunds': 0, 'journal': journal})
        finally:
            if self.backend is not None:
                try:
                    self.backend.close()
                except BaseException as error:
                    close_error = rt.error_record(error)
        value = {'actors': reports, 'delegated_cases': self.auth_results,
                 'bootstrap_and_cleanup_units': self.bootstrap_units,
                 'bootstrap_native_dispatches': self.bootstrap_native,
                 'bootstrap_managed_sql_observed': self.bootstrap_managed,
                 'full_chain_admission': False, 'access_token_revocation_claim': False,
                 'owned_auth_cleanup_required': bool(self.actors or self.auth_results),
                 'close_error': close_error,
                 'all_component_owned_auth_zero': bool(reports) and close_error is None and
                     all(r['cleanup'].get('confirmed') is True for r in reports + self.auth_results)}
        self.gate.save('integral-component-auth-cleanup.json', value)
        return value

    def query(self, session, phase, text, args=()):
        bound, values = dollar(text, args)
        return session.query(session.writer, phase, bound, values or None)

    def worker(self, session, payload):
        """Actual PG responses cross private IPC; no recorded/mock database rows."""
        process = subprocess.Popen(['node', str(HERE / 'integral_failure_runtime_worker.mjs')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            creationflags=0x08000000 if os.name == 'nt' else 0)
        timer = threading.Timer(max(0.01, min(125, session.deadline - time.monotonic())), process.kill)
        timer.start()
        terminal = None
        try:
            process.stdin.write(json.dumps(payload, default=str) + '\n'); process.stdin.flush()
            for _ in range(200):
                line = process.stdout.readline(2000001)
                if not line or len(line.encode()) > 2000000:
                    raise rt.Blocked('failure_worker_output_limit_or_exit')
                message = json.loads(line)
                if message.get('op') == 'complete':
                    terminal = message
                    break
                if message.get('op') != 'sql' or payload['op'] == 'compute_b':
                    raise rt.Blocked('failure_worker_protocol')
                text, args = message['sql'], message['args']
                phase = 'controller_evidence'
                hook = ((session.case == 'mid_controller' and len(args) == 6 and args[2] == 'action_started') or
                        (session.case == 'closure_failure' and len(args) == 3 and args[1] == 'closed'))
                safety = session.safety
                try:
                    # Controller.execute owns its real halt path after the injected failure.
                    if session.stopped and "state='stopped'" in text:
                        session.safety = True
                        phase = 'controller_halt'
                    call = lambda: self.query(session, phase, text, args)
                    rows = session.step(session.case, call) if hook else call()
                    reply = {'rows': rows}
                except BaseException as error:
                    session.fail(error)
                    reply = {'error': 'component_boundary_failed'}
                finally:
                    session.safety = safety
                process.stdin.write(json.dumps(reply, default=str) + '\n'); process.stdin.flush()
            if terminal is None:
                raise rt.Blocked('failure_worker_message_limit')
            process.wait(timeout=max(0.01, min(5, session.deadline - time.monotonic())))
            if process.returncode != 0:
                raise rt.Blocked('failure_worker_nonzero')
            if terminal.get('failed') and not session.injected:
                raise rt.Blocked('failure_real_worker_failed_before_hook')
            return terminal.get('value')
        finally:
            timer.cancel()
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            process.stdin.close(); process.stdout.close()

    def controller(self, session, close=False):
        session.writer = session.connect()
        session.query(session.writer, 'controller_begin', 'BEGIN')
        row = session.query(session.writer, 'controller_guard', rt.CHECK)[0]
        if any(row.get(k) is not True for k in ('pg17', 'bounded_statement', 'bounded_lock', 'tls')):
            raise rt.Blocked('failure_controller_session_limits')
        baseline = session.query(session.writer, 'controller_absence',
            "select count(*)::integer n from fmz6e11_controller_private.runs where state='running'")[0]['n']
        if baseline != 0:
            raise rt.Blocked('failure_existing_controller_preserved')
        session.claims.add('controller_transaction')
        contract = {'step': 0, 'actor': str(uuid.uuid4()), 'action_id': str(uuid.uuid4()),
                    'request_id': str(uuid.uuid4()), 'workspace': None, 'kind': 'workflow',
                    'operation': 'component_boundary', 'writes': []}
        self.worker(session, {'op': 'closure' if close else 'controller', 'run': session.case_id,
            'github_run': os.environ['GITHUB_RUN_ID'], 'source_commit': os.environ['GITHUB_SHA'],
            'count': session.used + 2, 'contract': contract})
        session.safety = True
        sample = session.query(session.writer, 'controller_terminal_prefix',
            "select (select count(*) from fmz6e11_controller_private.runs where id=%s and state=%s)::integer runs,"
            "(select count(*) from fmz6e11_controller_private.steps where run_id=%s and state='stopped')::integer stopped_steps,"
            "(select count(*) from fmz6e11_controller_private.evidence where run_id=%s and phase='stopped')::integer stopped_evidence",
            [session.case_id, 'closed' if close else 'stopped', session.case_id, session.case_id])[0]
        session.prefix_samples = [sample]
        expected = {'runs': 1, 'stopped_steps': 0 if close else 1, 'stopped_evidence': 0 if close else 1}
        session.phase_semantics = session.injected and session.primary is not None and sample == expected

    def prepare_workflow(self, session):
        from fixture_lifecycle import SEED
        from scenario import capture
        session.writer = session.connect()
        session.query(session.writer, 'workflow_begin', 'BEGIN')
        limits = session.query(session.writer, 'workflow_limits', rt.CHECK)[0]
        if any(limits.get(k) is not True for k in ('pg17', 'bounded_statement', 'bounded_lock', 'tls')):
            raise rt.Blocked('failure_workflow_session_limits')
        session.query(session.writer, 'workflow_fixture_barrier',
            'LOCK TABLE fmz6e11_private.identities, fmz6e11_private.config IN SHARE ROW EXCLUSIVE MODE')
        baseline = session.query(session.writer, 'workflow_baseline', CONTROL)[0]
        if baseline != {'identities': 0, 'running': 0, 'enabled': 0, 'bridge': 0, 'migrations': 47}:
            raise rt.Blocked('failure_clean47_inactive_registry_required')
        session.claims.add('workflow_transaction')
        session.context = {'window': str(uuid.uuid4()), 'a': str(uuid.uuid4()), 'b': str(uuid.uuid4()),
                           'key': str(uuid.uuid4()), 'proof': uuid.uuid4().hex, 'request_keys': {}}
        for role in ('trainer', 'member', 'b'):
            actor = self.actors[role]
            uid = actor.actor
            trainer = self.actors['trainer'].actor if role == 'member' else None
            session.query(session.writer, 'profile_fixture',
                "insert into public.profiles(id,email,role,name,trainer_id) values(%s,%s,%s,'CI synthetic',%s) "
                'on conflict(id) do update set role=excluded.role,trainer_id=excluded.trainer_id',
                [uid, actor.email, 'trainer' if role == 'trainer' else 'client', trainer])
            session.query(session.writer, 'identity_fixture',
                'insert into fmz6e11_private.identities(user_id,role,provenance_sha) values(%s,%s,%s)',
                [uid, ROLES[role], rt.digest(session.case_id)])
        session.query(session.writer, 'operator_fixture',
            'insert into fmz6e11_private.operators(user_id,enabled) values(%s,true)', [self.actors['trainer'].actor])
        session.query(session.writer, 'transaction_local_control',
            "update fmz6e11_private.config set enabled=true,proof_hash=encode(sha256(convert_to(%s,'UTF8')),'hex') where id",
            [session.context['proof']])
        self.bind(session, 'trainer')
        now = datetime.datetime.now(datetime.timezone.utc)
        session.context.update(starts=now.isoformat(), ends=(now + datetime.timedelta(minutes=5)).isoformat())
        c = session.context
        value = self.query(session, 'existing_fixture_seed', SEED,
            [c['window'], c['a'], c['b'], self.actors['trainer'].actor, self.actors['member'].actor,
             self.actors['b'].actor, c['key'], c['starts'], c['ends'], {'component': session.case_id}])
        if len(value) != 1 or value[0].get('value', {}).get('revision') != 1:
            raise rt.Blocked('failure_actual_fixture_seed')
        self.api(session, 'trainer', {'op': 'command', 'window': c['window'], 'workspace': None,
            'key': str(uuid.uuid4()), 'expected': 1, 'action': 'activate', 'data': {}})
        session.actions = capture()['workflow_actions']

    def bind(self, session, role):
        actor = self.actors[role]
        # Claims are backed by the real login's independently inventoried session.
        claims = {'sub': actor.actor, 'session_id': actor.session_ids[0], 'role': 'authenticated'}
        session.query(session.writer, 'bind_actual_session', BIND,
            [json.dumps(claims), json.dumps({'x-fmz6e11-proof': session.context['proof']})])

    def api(self, session, role, request):
        self.bind(session, role)
        value = session.query(session.writer, 'existing_product_call', API, [json.dumps(request)])[0]['value']
        return value

    def action(self, session, action):
        c = session.context
        row = session.query(session.writer, 'request_state',
            "select revision,(select fixture->'source_template' from (select fmz6e11_private.fixture('kg') fixture) f) template "
            'from fmz6e11_private.windows where id=%s', [c['window']])[0]
        proposals = session.query(session.writer, 'request_proposals',
            'select id::text,version from fmz6e11_private.proposals where workspace_id=%s order by version', [c['a']])
        mapping = {'68000000-0000-4000-8000-000000000010': c['window'],
                   '68000000-0000-4000-8000-000000000011': c['a'],
                   '68000000-0000-4000-8000-000000000012': c['b']}
        mapping.update({'68000000-0000-4000-8000-' + str(100 + p['version']).zfill(12): p['id'] for p in proposals})
        def resolve(value):
            if isinstance(value, dict):
                if value.get('$trusted_source_template'):
                    return row['template']
                return {k: resolve(v) for k, v in value.items()}
            if isinstance(value, list):
                return [resolve(v) for v in value]
            if isinstance(value, str):
                if value == '$window_starts_at': return c['starts']
                if value == '$window_ends_at': return c['ends']
                if value.startswith('68000000-0000-4000-8001-'):
                    return c['request_keys'].setdefault(value, str(uuid.uuid4()))
                return mapping.get(value, value)
            return value
        request = resolve(action['request'])
        request['expected'] += 1  # Existing capture starts at revision 1; activation made 2.
        if action['request']['action'] == 'b_build':
            request['expected'] = row['revision']
            state = self.api(session, 'b', {'op': 'read', 'window': c['window'], 'workspace': c['b']})
            computed = self.worker(session, {'op': 'compute_b', 'row': state['b_row'], 'action': 'build', 'data': {}})
            return action['role'], {'op': 'internal_b', 'request': request, 'computed': computed}
        return action['role'], request

    def invoke_checked(self, session, role, request, expected=200):
        value = self.api(session, role, request)
        if value.get('http_status', 200) != expected:
            raise rt.Blocked('failure_product_prefix_outcome')
        session.prefix_observed = True
        c = session.context
        sample = session.query(session.writer, 'prefix_numeric',
            'select (select count(*) from fmz6e11_private.source_versions where workspace_id=%s)::integer sources,'
            '(select count(*) from fmz6e11_private.plans where workspace_id=%s)::integer plans,'
            '(select count(*) from fmz6e11_private.proposals where workspace_id=%s)::integer proposals,'
            '(select count(*) from fmz6e11_private.requests where window_id=%s)::integer requests,'
            '(select count(*) from fmz6e11_private.events where window_id=%s)::integer events,'
            '(select proposal_version from fmz6e11_private.b_states where workspace_id=%s)::integer b_proposal',
            [c['a'], c['a'], c['a'], c['window'], c['window'], c['b']])[0]
        session.prefix_samples = getattr(session, 'prefix_samples', []) + [sample]
        if session.case in ('mid_route_a', 'duplicate'):
            session.phase_condition = sample['sources'] == 1 and sample['plans'] == 1
        elif session.case == 'mid_route_b':
            session.phase_condition = sample['b_proposal'] == 1
        elif session.case == 'mid_restore':
            session.phase_condition = sample['proposals'] == 2 and sample['plans'] == 2
        if session.case == 'duplicate' and len(session.prefix_samples) == 2:
            first, second = session.prefix_samples
            session.phase_condition = (session.phase_condition and second['events'] == first['events'] + 1 and
                all(first[k] == second[k] for k in first if k != 'events') and value.get('replay') is True)
        return value

    def fixture_delete(self, session, table):
        from fixture_cleanup_runtime import validate_rows, digest
        import fixture_cleanup_runtime_sql as sql
        c = session.context
        args = [c['window'], '{' + c['a'] + ',' + c['b'] + '}']
        rows = validate_rows(self.query(session, 'cleanup_owned_inventory', sql.INVENTORY, args)[0]['value'])
        expected = [{k: v for k, v in r.items() if k != 'scope_ok'} for r in rows if r['table'] == table]
        actual = self.query(session, 'cleanup_' + table, sql.delete(table), [*args, expected])[0]['value']
        if sorted(map(digest, actual)) != sorted(map(digest, expected)):
            raise rt.Blocked('failure_actual_cleanup_multiset')
        session.deleted_prefix = getattr(session, 'deleted_prefix', 0) + len(actual)
        session.phase_condition = session.deleted_prefix > 0

    def delegated_auth(self, session, name):
        from auth_failure import Case, contract
        case = Case(self.backend, self.folder / session.case, session.case_id, name,
                    self.config['managed_costs'],
                    transport_factory=self.backend.guarded_factory(self.transport_factory))
        result = case.execute()
        self.auth_results.append(result)
        session.delegated_auth = result
        session.delegated_actor = case.actor
        session.native_confirmed = result['native_sql_dispatches']
        session.injected = result['component_case_pass'] is True
        session.matched = True
        session.phase_semantics = session.injected
        session.unknown = name in ('partial_session', 'create_lost_reply')
        session.claims.add('auth_delegated')
        session.fail(rt.InjectedFailure(result['primary_failure']))

    def run_case(self, case, session):
        if case == 'timeout':
            rt.TimeoutDriver().run_case(case, session)
            return
        if case in ('mid_controller', 'closure_failure'):
            self.controller(session, case == 'closure_failure')
            return
        if case in ('mid_auth', 'lost_reply'):
            self.delegated_auth(session, 'partial_session' if case == 'mid_auth' else 'create_lost_reply')
            return
        self.prepare_workflow(session)
        if case == 'final_check_failure':
            self.cleanup(case, session)
            session.phase_condition = True
            session.step(case, lambda: self.observe(case, session))
        elif case in ('partial_cleanup', 'cleanup_failure'):
            self.fixture_delete(session, 'b_states')
            if case == 'partial_cleanup':
                session.step(case, lambda: self.fixture_delete(session, 'requests'))
            else:
                # Genuine FK failure after one scoped removal, never a fake delete result.
                session.step(case, lambda: self.fixture_delete(session, 'windows'))
        else:
            target = next(a for a in session.actions if a['request']['action'] ==
                          ('b_build' if case == 'mid_route_b' else 'restore' if case == 'mid_restore' else 'source_append'))
            if case == 'mid_restore':
                for action in session.actions[:target['step']]:
                    role, request = self.action(session, action)
                    self.invoke_checked(session, role, request, action['expected_http'])
            role, request = self.action(session, target)
            session.step(case, lambda: self.invoke_checked(session, role, request, target['expected_http']))

    def cleanup(self, case, session):
        session.close()
        session.rollback_closed = not session.connections and not session.secondary

    def observe(self, case, session):
        if case == 'timeout':
            result = rt.TimeoutDriver().observe(case, session)
            session.phase_semantics = session.injected and result.values == {'remaining_case_backends': 0}
            return result
        if case in ('mid_auth', 'lost_reply'):
            result = session.snapshot('select (select count(*) from auth.users where id=%s)::integer users,'
                '(select count(*) from auth.sessions where user_id=%s)::integer sessions,'
                '(select count(*) from auth.refresh_tokens where user_id=%s)::integer refresh_tokens',
                [session.delegated_actor] * 3)
            session.phase_semantics = session.phase_semantics and not any(result.values.values())
            return result
        if case in ('mid_controller', 'closure_failure'):
            result = session.snapshot('select (select count(*) from fmz6e11_controller_private.runs where id=%s)::integer runs,'
                '(select count(*) from fmz6e11_controller_private.steps where run_id=%s)::integer steps,'
                '(select count(*) from fmz6e11_controller_private.evidence where run_id=%s)::integer evidence',
                [session.case_id] * 3)
        else:
            from fixture_cleanup_evidence import TABLE_SCOPE
            c = session.context
            text = 'select ' + ','.join('(select count(*) from fmz6e11_private.' + table + ' where ' +
                scope + ')::integer ' + table for table, scope in TABLE_SCOPE.items())
            text, values = dollar(text, [c['window'], '{' + c['a'] + ',' + c['b'] + '}'])
            result = session.snapshot(text, values)
            session.phase_semantics = (session.injected and getattr(session, 'rollback_closed', False)
                                       and getattr(session, 'phase_condition', False))
        session.phase_semantics = getattr(session, 'phase_semantics', False) and not any(result.values.values())
        return result
