"""Actual local GoTrue context for the independent component, never root admission."""
import base64
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.parse
import urllib.request

import psycopg
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
import auth_failure_tracked as tracked
from native_runtime import NativeRuntime
from . import lifecycle, scope, subset
from .lifecycle import need
from quota_candidate_v1 import runtime_registered_startup as startup


class Context:
    """Same LocalAuth/Session/tracker APIs; exact owned lifecycle replaces name-only rm."""
    def __init__(self, gate, stack, run_id):
        import ci_auth
        self.gate, self.stack, self.run_id = gate, stack, run_id
        self.records = lifecycle.Records(gate, 'component-parent-lifecycle',
            [sys.modules[__name__], ci_auth, startup, scope, subset, tracked, sys.modules[NativeRuntime.__module__]])
        need(json.loads((gate.out/'case-stack-bootstrap.json').read_bytes()) == stack
             and stack.get('status') == 'CLEAN47_BOOTSTRAP_PASS' and stack.get('registry_empty') is True
             and stack.get('auth_database_bound') is False and stack.get('ssl') is True,
             'actual_clean47_required')
        self.server = self.runtime = self.db = self.counter = self.owners = None
        self.ctx = None
        self.body_started = self.body_terminal = self.closed = False
        self.discovery_attempts = 0
        self.native_events = []
        self.native_attempts = 0
        self.records.save('command-plan.json', {'private_docker_ceiling':5,
            'owned_auth_docker_ceiling':16,'image_pull_attempts':1,'health_attempts':1,
            'local_profile_normal_sql':10,'local_profile_sql_ceiling':11,
            'scope_sql_ceiling':24,'parent_snapshot_sql_ceiling':6,
            'parent_observer_sql_ceiling':5,
            'stopped_counter_sql':{'before':1,'post_stop_activity':1,'post_stop_after':1},
            'parent_http_ceiling':12,'native_and_managed_total_bound':None,
            'budget_domain':'separate_disposable_diagnostic_not_2349','full_chain_admission':False})
        self.unknown = []
        self.result = {'status':'NO_GO','parent_subset_absent':False,
            'auth_process_stopped':False,'auth_container_absent':False,'post_stop_counters':False,
            'claims_released':False,'global_auth_zero':False,'full_chain_admission':False}

    def private(self, phase, args, *, timeout=10):
        self.records.check()
        need(self.discovery_attempts < 5, 'private_docker_bound')
        self.discovery_attempts += 1
        self.records.save(phase+'-before.json', {'phase':phase,'private_values_exported':False})
        response = subprocess.run(['docker','--context','default', *args],
            env=lifecycle.local_environment(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, timeout=timeout, check=False)
        need(response.returncode == 0 and len(response.stdout) <= 16384, 'private_discovery')
        self.records.save(phase+'-after.json', {'confirmed':True})
        return response.stdout.strip()

    def connect(self):
        connection = self.runtime.connect()
        try:
            self.records.save('connection-%d.json' % self.connections, {'ordinal':self.connections,
                'explicit_connect':True,'implicit_native_sql_bound':None})
        except BaseException as primary:
            try: connection.close()
            except BaseException as secondary:
                primary.add_note('component_connect_close_secondary:'+type(secondary).__name__)
            raise
        self.connections += 1
        return connection

    def observe(self, event):
        if event['phase'] == 'started':
            need(self.native_attempts < 5, 'parent_observer_bound')
            self.native_attempts += 1
        self.records.save('observer-%02d.json' % len(self.native_events), event)
        self.native_events.append(dict(event))

    def tracked_originals(self):
        if self.ctx is None or 'auth' not in self.ctx:
            return
        originals = {}
        total = 0
        for records in self.ctx['auth'].registry._recordsets:
            lifecycle.binding.checked_path(records.folder)
            for name, raw in records.validate().items():
                relative = (records.folder/name).relative_to(self.gate.out).as_posix()
                need(relative not in originals and len(originals) < 96, 'parent_original_bound')
                total += len(raw)
                need(total <= 500000, 'parent_original_bytes')
                originals[relative] = {'sha256':lifecycle.durable.sha(raw),'bytes':len(raw),
                    'base64':base64.b64encode(raw).decode('ascii')}
        self.records.save('tracked-originals.json', {'format':'component-parent-originals-v1',
            'files':originals,'lossless':True,'raw_bytes':total,'source_binding':self.records.source})

    def __enter__(self):
        import ci_auth
        from protocol import Session
        from store import LocalAuth, Denied
        self.records.check()
        self.connections = 0
        try:
            lifecycle.local_environment()
            need(self.private('docker-endpoint', ['context','inspect','default','--format',
                '{{.Endpoints.docker.Host}}']) == 'unix:///var/run/docker.sock', 'local_docker_endpoint')
            self.gate.command('component-auth-image', ['docker','--context','default','pull',startup.IMAGE], timeout=180)
            self.server = lifecycle.AuthContainer(self.gate, self.run_id)
            pg = self.stack['container']['id']
            password = self.private('database-password', ['exec',pg,'sh','-c','printf %s "$POSTGRES_PASSWORD"'])
            network = self.private('database-network', ['inspect','--format',
                '{{range $key, $value := .NetworkSettings.Networks}}{{$key}}{{end}}',pg])
            ports = self.private('database-port', ['port',pg,'5432/tcp']).splitlines()
            import re
            endpoints = [p for p in ports if re.fullmatch(r'(127\.0\.0\.1|0\.0\.0\.0):\d+',p)]
            need(len(endpoints) == 1, 'database_endpoint')
            ca = self.gate.work/'fmz-ci-ca.crt'
            need(not ca.is_symlink() and hashlib.sha256(ca.read_bytes()).hexdigest() == self.stack['ca_sha256'], 'database_ca')
            params = dict(host='127.0.0.1',hostaddr='127.0.0.1',port=int(endpoints[0].split(':')[1]),
                dbname='postgres',user='postgres',password=password,sslmode='verify-full',sslrootcert=str(ca),
                connect_timeout=5,options='-c statement_timeout=5000 -c lock_timeout=1000')
            dsn = make_conninfo(**params)
            self.runtime = NativeRuntime(params, 'http://127.0.0.1:59999', environment='disposable_ci')
            scope.reduce_profile(self.gate, self.runtime,
                {'pg_system_identifier':self.stack['pg_system_identifier'],'database_oid':self.stack['database_oid']}, self.server)
            self.db = self.connect()
            admin = Session(self.db, self.observe, 'component_parent_admin')
            self.counter = lifecycle.StoppedCounters(self.records, admin, self.server)
            secret = secrets.token_hex(32)
            def b64(value): return base64.urlsafe_b64encode(json.dumps(value,separators=(',',':')).encode()).decode().rstrip('=')
            raw = b64({'alg':'HS256','typ':'JWT'})+'.'+b64({'role':'service_role','iss':'supabase','exp':int(time.time())+900})
            token = raw+'.'+base64.urlsafe_b64encode(hmac.new(secret.encode(),raw.encode(),hashlib.sha256).digest()).decode().rstrip('=')
            env = {'GOTRUE_DB_DATABASE_URL':lifecycle.database_url(password,self.server.name),
                   'GOTRUE_JWT_SECRET':secret}
            try: self.server.create(network, env)
            finally: env.clear(); password=None; secret=None; params.clear()
            self.server.start()
            readiness = json.loads(self.private('auth-listener', ['exec', self.server.id,
                'sh','-c',startup.READINESS_SCRIPT], timeout=startup.READINESS_TIMEOUT))
            need(readiness.get('status') == 'ready' and type(readiness.get('polls')) is int
                 and 1 <= readiness['polls'] <= startup.READINESS_POLLS, 'auth_listener')
            startup.health()
            target = admin.execute(startup.BOUND, [self.stack['database_oid'],self.server.name,
                                                   self.server.auth_ip]).fetchone()
            need(target == {'n':1,'tls':1}, 'actual_auth_target_tls')
            self.records.save('actual-auth-tls.json', {'backend_count':1,'tls_backend_count':1,
                'database_oid':self.stack['database_oid'],'application_name':self.server.name,
                'auth_container':self.server.id,'ca_sha256':self.stack['ca_sha256'],
                'sslmode':'verify-full','hostname':startup.PG_NAME,'source_binding':self.records.source})
            registry = tracked.Registry(self.gate.out/'component-parent-request-private', run_id=self.run_id)
            plan = [v for _ in range(3) for v in (
                {'method':'POST','route':'/admin/users','units':128},
                {'method':'POST','route':'/token?grant_type=password','units':128},
                {'method':'GET','route':'/user','units':128})]
            budget = tracked.ParentBudget(self.gate.out/'component-parent-budget-private', plan, run_id=self.run_id)
            auth = tracked.TrackedAuth('http://127.0.0.1:59999', LocalAuth, registry, budget,
                admin_token=token, denied_type=Denied)
            self.ctx = dict(dsn=dsn, auth=auth, admin=admin, tokens={},claims={},accounts={},
                test_admin_token=token,auth_request_registry=registry,image=startup.IMAGE,digests=[startup.IMAGE])
            self.owners = subset.ParentSubset(self.gate, auth, self.ctx, self.run_id)
            self.owners.bootstrap()
            self.body_started = True
            return self.ctx
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise

    def confirm_body_terminal(self, worker, auth):
        from . import parent
        import inspect
        frame = inspect.currentframe().f_back
        need(frame.f_code is parent.run.__code__ and frame.f_locals.get('context') is self,
             'body_terminal_caller')
        del frame
        need(worker['cases'] and all(c['producer_reaped'] for c in worker['cases'])
             and auth['registered_requests_closed'] is True, 'body_producers_unknown')
        self.body_terminal = True

    def __exit__(self, kind, primary, traceback):
        if self.closed: return False
        self.closed = True
        failures = []
        def attempt(phase, action):
            try: return action()
            except BaseException as error:
                failures.append(error)
                self.unknown.append({'phase':phase,'error_class':type(error).__name__})
                if primary is not None: primary.add_note('component_'+phase+'_secondary:'+type(error).__name__)
                return None
        def cleanup_parent():
            need(not self.body_started or self.body_terminal, 'body_not_terminal')
            self.owners.close()
            if self.db is not None:
                self.db.close(); need(self.db.closed, 'admin_before_locks')
            lease = scope.ScopeLease(self.gate, self.runtime, self.run_id)
            try:
                with lease:
                    value = self.owners.cleanup(lease)
            finally:
                original = sys.exception()
                try: lease.records.seal()
                except BaseException as secondary:
                    if original is None: raise
                    original.add_note('component_scope_archive_secondary:'+type(secondary).__name__)
            self.result['parent_subset_absent'] = value['known_parent_subset_absent']
        try:
            if self.owners is not None: attempt('parent_cleanup', cleanup_parent)
            if self.db is not None: attempt('admin_close', self.db.close)
            if self.server is not None and self.server.create_attempted:
                attempt('auth_stop', self.server.stop)
                self.result['auth_process_stopped'] = self.server.stopped
            if self.counter is not None and self.server.stopped:
                def counters():
                    from protocol import Session
                    self.db = self.connect()
                    self.counter.admin = Session(self.db, self.observe, 'component_post_stop')
                    try:
                        self.counter.finish()
                        self.result['post_stop_counters'] = True
                    finally: self.db.close()
                attempt('after_stop_counters', counters)
            if self.server is not None and self.server.stopped:
                attempt('auth_remove', self.server.remove)
                self.result['auth_container_absent'] = self.server.removed
            attempt('tracked_originals', self.tracked_originals)
            self.result.update(original_error_class=type(primary).__name__ if primary else None,
                               closing_errors=list(getattr(self.server,'closing_errors',())),
                               unknown=list(self.unknown))
            if primary is None and not failures and all(self.result[k] for k in (
                    'parent_subset_absent','auth_process_stopped','auth_container_absent','post_stop_counters')):
                self.result['status'] = 'LOCAL_PARENT_LIFECYCLE_CONFIRMED'
            attempt('lifecycle_export', lambda: self.records.save('result.json', self.result))
            if self.server is not None: attempt('container_archive', self.server.records.seal)
            if self.server is not None: attempt('container_safety_archive', self.server.safety.seal)
            if self.owners is not None: attempt('owners_archive', self.owners.records.seal)
            attempt('lifecycle_archive', self.records.seal)
        finally:
            if self.runtime is not None: self.runtime.clear()
            if self.ctx is not None:
                self.ctx.pop('test_admin_token', None)
                self.ctx.pop('dsn', None)
        if primary is None and failures: raise failures[0]
        return False
