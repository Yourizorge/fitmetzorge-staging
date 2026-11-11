"""Source-bound local component receipts and preregistered Docker ownership.

No Docker execution occurs on import. Unknown command outcomes stay unknown even
when a later exact-identity inspection permits stopping the owned producer.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import uuid
import urllib.parse

import admission_journal as durable
import admission_module_binding as binding
import auth_failure as engine
from quota_candidate_v1 import runtime_registered_startup as startup


def need(value, reason):
    if not value:
        raise RuntimeError('component_lifecycle_' + reason)


def local_environment():
    need(sys.platform == 'linux' and os.environ.get('GITHUB_ACTIONS') == 'true'
         and os.environ.get('GITHUB_REPOSITORY') == 'Yourizorge/fitmetzorge-staging', 'local_ci')
    need(not any(k.startswith('DOCKER_') and v for k, v in os.environ.items()), 'docker_override')
    return {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}


class Records:
    def __init__(self, gate, prefix, modules):
        self.gate, self.modules = gate, [sys.modules[__name__], binding, durable, *modules]
        self.source = binding.verify(gate, self.modules)
        self.journal = durable.Journal(pathlib.Path(gate.out)/(prefix+'-private'), gate.save, prefix)
        self.save('source.json', self.source)

    def check(self):
        need(binding.verify(self.gate, self.modules) == self.source, 'source_changed')
        need(not self.journal.poisoned, 'journal_poisoned')
        self.journal._inventory()
        for name, ref in self.journal.entries.items():
            self.journal._read(name, ref)

    def save(self, name, value):
        self.check()
        self.journal.save(name, value)
        need(self.journal._read(name, self.journal.entries[name]) == durable.raw(value), 'readback')

    def seal(self):
        self.check()
        return self.journal.seal()


FORMAT = ('{"id":"{{.Id}}","name":"{{.Name}}","image":"{{.Image}}",'
          '"labels":{{json .Config.Labels}},"running":{{.State.Running}},'
          '"pid":{{.State.Pid}},"status":"{{.State.Status}}",'
          '"cmd":{{json .Config.Cmd}},"environment":{{json .Config.Env}},'
          '"mounts":{{json .Mounts}},"network":{{json .HostConfig.NetworkMode}},'
          '"networks":{{json .NetworkSettings.Networks}}}')
IMAGE = startup.IMAGE
CLOSING_PLAN = {'docker_total_ceiling':16,'stop_ceiling':5,'remove_ceiling':2,
    'stop':['exact_name_inventory','exact_identity_inspect','stop_once_if_running',
            'exact_name_inventory','exact_identity_inspect'],
    'remove':['exact_id_rm_only_with_original_stop','exact_name_absence'],
    'create_start_retry_force_prune':False}


def database_url(password, name):
    return ('postgres://supabase_auth_admin:'+urllib.parse.quote(password,safe='')+
        '@'+startup.PG_NAME+':5432/postgres?'+urllib.parse.urlencode({
            'application_name':name,'sslmode':'verify-full','sslrootcert':startup.AUTH_CA}))


class AuthContainer:
    """One exact local container; no name-only rm, retry, broad stop or prune."""
    def __init__(self, gate, run_id):
        engine.binding(run_id)
        need(str(uuid.UUID(run_id)) == run_id and uuid.UUID(run_id).version == 4, 'fresh_uuid4')
        self.env = local_environment()
        self.records = Records(gate, 'component-auth-container', [startup])
        self.ca = binding.checked_path(pathlib.Path(gate.work)/'fmz-ci-ca.crt')
        self.ca_sha = json.loads((pathlib.Path(gate.out)/'case-stack-bootstrap.json').read_bytes())['ca_sha256']
        need(durable.sha(self.ca.read_bytes()) == self.ca_sha
             and not any(c in str(self.ca) for c in (',','\r','\n')), 'original_ca')
        self.name = 'fmz-pg-component-' + uuid.uuid4().hex
        self.labels = {'fmz.component': 'pg-auth-v1', 'fmz.run': run_id,
            'fmz.nonce': uuid.uuid4().hex, 'fmz.source': os.environ['GITHUB_SHA'],
            'fmz.ci-run': os.environ['GITHUB_RUN_ID']}
        need(re.fullmatch('[a-f0-9]{40}', self.labels['fmz.source'])
             and re.fullmatch('[1-9][0-9]*', self.labels['fmz.ci-run']), 'ci_binding')
        self.id = self.image = None
        self.intent = self.create_attempted = self.start_attempted = self.stop_attempted = False
        self.stopped = self.removed = self.remove_attempted = False
        self.config_sha = self.network = self.auth_ip = None
        self._closing = False
        self.authority = None
        self.authority_refs = None
        self.safety_failure = None
        self.closing_failure = None
        self.closing_errors = []
        self._closing_seen = []
        self.closing_commands = 0
        self.stop_dispatched = self.remove_dispatched = False
        self.stop_verified_running = False
        self.original_errors = []
        self.commands = 0
        endpoint = self._command('context', ['context', 'inspect', 'default', '--format',
                                 '{{.Endpoints.docker.Host}}'])
        need(endpoint == 'unix:///var/run/docker.sock', 'local_docker_endpoint')
        need(not self._ids(), 'name_preexists')
        image = json.loads(self._command('image', ['image', 'inspect', '--format',
            '{"id":"{{.Id}}","digests":{{json .RepoDigests}}}', IMAGE]))
        need(set(image) == {'id','digests'} and re.fullmatch('sha256:[a-f0-9]{64}', image['id'])
             and type(image['digests']) is list and IMAGE in image['digests'], 'local_image_identity')
        self.image = image['id']
        self.records.save('intent.json', {'name': self.name, 'labels': self.labels,
            'image': self.image, 'image_reference': IMAGE, 'preexisting': False,
            'ca_sha256': self.ca_sha, 'auth_ca_mount': startup.AUTH_CA,
            'docker_command_ceiling': 16, 'auth_container_remove_allowed': True,
            'closing_allowance':CLOSING_PLAN,
            'retries': 0, 'delete_volume_authority': False, 'full_chain_admission': False})
        self.intent = True
        # Issued before any creation dispatch; independent of later normal-log IO.
        self.safety = Records(gate, 'component-auth-safety', [startup])

    def _authority(self):
        need(self.authority is not None and self.intent and self.create_attempted, 'stop_authority_missing')
        need(binding.verify(self.records.gate, self.records.modules) == self.records.source, 'source_changed')
        journal = self.records.journal
        binding.checked_path(journal.folder)
        for name, ref in self.authority['originals'].items():
            need(journal._read(name, ref) is not None, 'stop_authority_original')
        need(self.authority['labels'] == self.labels and self.authority['name'] == self.name
             and self.authority['image'] == self.image and self.authority['config_sha'] == self.config_sha
             and self.authority['ca_sha'] == self.ca_sha and self.authority['network'] == self.network,
             'stop_authority_changed')
        saved = self.safety.journal
        need(self.authority_refs is not None and self.authority['closing_allowance'] == CLOSING_PLAN,
             'closing_allowance_missing')
        need(binding.verify(self.safety.gate,self.safety.modules) == self.safety.source, 'source_changed')
        binding.checked_path(saved.folder)
        for name, ref in self.authority_refs.items():
            saved._read(name,ref)
        need(json.loads(saved._read('authority.json', self.authority_refs['authority.json'])) == self.authority,
             'stop_authority_receipt')

    def _save(self, records, name, value):
        if not self._closing:
            records.save(name,value)
            return
        # Only immutable preissued authority admits safety operations. A later
        # append failure remains sticky, but is not authority to keep running.
        self._authority()
        try:
            records.save(name,value)
        except BaseException as error:
            self._failure(error,'safety_append',record=name)
            if self.safety_failure is None:
                self.safety_failure = error

    def _failure(self, error, phase, *, record=None):
        if any(error is prior for prior in self._closing_seen): return
        self._closing_seen.append(error)
        self.closing_errors.append({'ordinal':len(self.closing_errors)+1,'phase':phase,
            'command_ordinal':self.commands,'record':record,'error_class':type(error).__name__})
        if self.closing_failure is None:
            self.closing_failure = error
        elif error is not self.closing_failure:
            self.closing_failure.add_note('component_'+phase+'_secondary:'+type(error).__name__)

    def _closing_command(self, phase, args):
        need(self.closing_commands < 7, 'closing_command_bound')
        if phase == 'inventory':
            expected = ['ps','--all','--no-trunc','--filter','name=^/'+self.name+'$','--format','{{.ID}}']
        elif phase == 'inspect':
            need(len(args) == 4 and re.fullmatch('[a-f0-9]{64}',args[-1]), 'closing_inspect_identity')
            expected = ['inspect','--format',FORMAT,args[-1]]
        elif phase == 'stop':
            need(self.stop_verified_running and not self.stop_dispatched, 'closing_stop_scope')
            expected = ['stop','--time','5',self.id]
        elif phase == 'remove':
            need(self.stopped and self.remove_attempted and not self.remove_dispatched,
                 'closing_remove_scope')
            expected = ['rm',self.id]
        else:
            raise RuntimeError('component_lifecycle_closing_operation_denied')
        need(args == expected, 'closing_arguments')
        self.closing_commands += 1
        if phase == 'stop': self.stop_dispatched = True
        if phase == 'remove': self.remove_dispatched = True

    def _records(self):
        if self._closing:
            self._authority()
            return self.safety
        return self.records

    def _command(self, phase, args, *, private_env=None, timeout=5):
        records = self._records()
        if not self._closing: records.check()
        need(self.commands < 16, 'docker_command_bound')
        need(self._closing or self.commands < 9, 'closing_reserve_required')
        if self._closing: self._closing_command(phase,args)
        self.commands += 1
        key = '%02d-%s' % (self.commands, phase)
        self._save(records,key+'-before.json', {'phase': phase, 'timeout': timeout,
            'command_ordinal': self.commands, 'arguments_exported': False})
        try:
            response = subprocess.run(['docker', '--context', 'default', *args],
                env=self.env if private_env is None else private_env, timeout=timeout,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False)
            need(response.returncode == 0, 'docker_nonzero')
            need(len(response.stdout) <= 16384, 'docker_output_bound')
        except BaseException as error:
            if self._closing: self._failure(error,'docker_'+phase)
            self.original_errors.append({'phase': phase, 'class': type(error).__name__})
            try:
                self._save(records,key+'-after.json', {'phase': phase, 'result_received': False,
                    'error_class': type(error).__name__, 'original_outcome_unknown': True})
            except BaseException as secondary:
                error.add_note('component_docker_receipt_secondary:'+type(secondary).__name__)
            raise
        self._save(records,key+'-after.json', {'phase': phase, 'result_received': True,
                          'returncode': response.returncode, 'output_exported': False})
        return response.stdout.strip()

    def _ids(self):
        rows = self._command('inventory', ['ps', '--all', '--no-trunc', '--filter',
            'name=^/'+self.name+'$', '--format', '{{.ID}}']).splitlines()
        need(len(rows) <= 1 and all(re.fullmatch('[a-f0-9]{64}', r) for r in rows), 'inventory')
        return rows

    def inspect(self):
        records = self._records()
        if not self._closing: records.check()
        need(self.intent and self.create_attempted, 'no_creation_intent')
        ids = self._ids()
        need(len(ids) == 1, 'created_identity_missing')
        value = json.loads(self._command('inspect', ['inspect', '--format', FORMAT, ids[0]]))
        need(set(value) == {'id','name','image','labels','running','pid','status',
                           'cmd','environment','mounts','network','networks'}
            and value['id'] == ids[0] and value['name'] == '/'+self.name
            and value['image'] == self.image and type(value['labels']) is dict
            and all(value['labels'].get(k) == v for k, v in self.labels.items())
            and type(value['running']) is bool and type(value['pid']) is int
            and value['pid'] >= 0 and value['status'] in ('created','running','exited'), 'ownership')
        need(value['cmd'] == ['auth','serve'] and value['network'] == self.network
             and type(value['environment']) is list and len(value['environment']) <= 128,
             'serve_only_config')
        entries = [v.split('=',1) for v in value['environment']]
        need(all(len(v) == 2 for v in entries) and len({v[0] for v in entries}) == len(entries), 'config_keys')
        selected = {k:v for k,v in entries if k.startswith(('GOTRUE_','DATABASE_URL')) or k == 'API_EXTERNAL_URL'}
        need(durable.sha(durable.raw(selected)) == self.config_sha, 'private_config_changed')
        mounts = [v for v in value['mounts'] if v.get('Destination') == startup.AUTH_CA]
        need(len(mounts) == 1 and mounts[0].get('Type') == 'bind'
             and mounts[0].get('Source') == str(self.ca) and mounts[0].get('RW') is False
             and durable.sha(binding.checked_path(self.ca).read_bytes()) == self.ca_sha, 'readonly_ca_mount')
        if value['running']:
            import ipaddress
            address = value['networks'][self.network]['IPAddress']
            need(ipaddress.ip_address(address).is_private, 'auth_container_ip')
            self.auth_ip = address
        need(self.id is None or self.id == value['id'], 'identity_changed')
        self.id = value['id']
        # Only the registered labels, never image-supplied arbitrary values, escape.
        value = {k:value[k] for k in ('id','name','image','running','pid','status')}
        value.update(labels=dict(self.labels), ca_sha256=self.ca_sha,
                     tls_config_verified=True, serve_only=True)
        self._save(records,'observation-%02d.json' % self.commands, value)
        return value

    def create(self, network, secret_env):
        need(self.intent and not self.create_attempted and self.id is None, 'create_replay')
        need(re.fullmatch('[A-Za-z0-9_-]+', network), 'network')
        need(set(secret_env) == {'GOTRUE_DB_DATABASE_URL','GOTRUE_JWT_SECRET'}, 'secret_env_scope')
        parsed = urllib.parse.urlsplit(secret_env['GOTRUE_DB_DATABASE_URL'])
        need(parsed.scheme == 'postgres' and parsed.hostname == startup.PG_NAME
             and parsed.port == 5432 and parsed.username == 'supabase_auth_admin'
             and parsed.path == '/postgres' and not parsed.fragment
             and urllib.parse.parse_qs(parsed.query,strict_parsing=True) == {
                 'application_name':[self.name],'sslmode':['verify-full'],'sslrootcert':[startup.AUTH_CA]},
             'auth_verify_full_database_url')
        need(durable.sha(binding.checked_path(self.ca).read_bytes()) == self.ca_sha, 'original_ca')
        self.network = network
        args = ['create', '--name', self.name, '--network', network,
                '--mount','type=bind,src='+str(self.ca)+',dst='+startup.AUTH_CA+',readonly',
                '-p', '127.0.0.1:59999:9999']
        for key, value in sorted(self.labels.items()):
            args += ['--label', key+'='+value]
        for key in secret_env:
            args += ['-e', key]
        config = startup.configuration()
        self.config_sha = durable.sha(durable.raw({**config, **secret_env}))
        self.records.save('create-config.json', {'config_sha256':self.config_sha,
            'ca_sha256':self.ca_sha,'sslmode':'verify-full','database_hostname':startup.PG_NAME,
            'application_name':self.name,'network_sha256':durable.sha(network.encode()),
            'argv':['auth','serve']})
        self.authority = {'name':self.name,'labels':dict(self.labels),'image':self.image,
            'config_sha':self.config_sha,'ca_sha':self.ca_sha,'network':self.network,
            'closing_allowance':CLOSING_PLAN,
            'originals':{name:dict(self.records.journal.entries[name])
                         for name in ('source.json','intent.json','create-config.json')}}
        self.safety.save('authority.json', self.authority)
        self.authority_refs = {name:dict(self.safety.journal.entries[name])
                               for name in ('source.json','authority.json')}
        for key, value in config.items():
            args += ['-e', key+'='+value]
        args.extend([IMAGE, 'auth', 'serve'])
        self.create_attempted = True
        reply = self._command('create', args, private_env={**self.env, **secret_env}, timeout=30)
        value = self.inspect()
        need(reply == value['id'] and value['status'] == 'created'
             and value['running'] is False and value['pid'] == 0, 'create_confirmation')

    def start(self):
        need(self.id is not None and not self.start_attempted and not self.stopped, 'start_scope')
        self.start_attempted = True
        reply = self._command('start', ['start', self.id], timeout=30)
        value = self.inspect()
        need(reply == self.id and value['running'] and value['pid'] > 0, 'start_confirmation')

    def stop(self):
        need(self.intent and self.create_attempted and not self.stop_attempted, 'stop_scope')
        self.stop_attempted = True
        self._closing = True
        # Lost create/start reply may be resolved only for stop authority, not success.
        primary = None
        try:
            value = self.inspect()
            self.stop_verified_running = value['running'] and value['pid'] > 0
            if value['running']:
                try:
                    self._command('stop', ['stop', '--time', '5', self.id], timeout=10)
                except BaseException as error:
                    primary = error
            after = self.inspect()
            need(after['running'] is False and after['pid'] == 0
                 and after['status'] in ('created','exited'), 'stop_unknown')
            self.stopped = True
            self._save(self.safety,'stopped.json', {'id': self.id, 'name': self.name, 'image': self.image,
                'labels': self.labels, 'process_stopped': True, 'container_removed': False,
                'original_errors': list(self.original_errors), 'original_outcome_reclassified': False,
                'closing_errors': list(self.closing_errors),
                'auth_commit_known': False, 'claim_release_authorized': False})
        except BaseException as error:
            if primary is None:
                primary = error
            else: primary.add_note('component_stop_inspection_secondary:'+type(error).__name__)
        if primary is not None: self._failure(primary,'stop')
        if self.closing_failure is not None: raise self.closing_failure
        if primary is not None:
            raise primary

    def remove(self):
        """Only after the same owned process stop receipt; no -f or volume flag."""
        self._authority()
        need(self.stopped and not self.remove_attempted and self.id is not None, 'remove_scope')
        journal = self.safety.journal
        need('stopped.json' in journal.entries, 'remove_original_stop_required')
        original = json.loads(journal._read('stopped.json', journal.entries['stopped.json']))
        need(original['id'] == self.id and original['labels'] == self.labels, 'remove_identity')
        self.remove_attempted = True  # Lost result is never retried.
        primary = None
        try:
            self._command('remove', ['rm', self.id], timeout=10)
        except BaseException as error:
            primary = error
        try:
            need(not self._ids(), 'removed_container_still_present')
            self._save(self.safety,'absent.json', {'id':self.id,'name':self.name,'labels':self.labels,
                'exact_container_absent':True,'volumes_removed':False,'global_cleanup':False,
                'original_outcome_reclassified':False})
            self.removed = self.safety_failure is None
        except BaseException as error:
            if primary is None: raise
            primary.add_note('component_remove_absence_secondary:'+type(error).__name__)
        if primary is not None: self._failure(primary,'remove')
        if self.closing_failure is not None: raise self.closing_failure
        if primary is not None: raise primary


class StoppedCounters:
    """Actual role counters before startup and after confirmed process stop."""
    ACTIVITY = "SELECT count(*) AS n FROM pg_stat_activity WHERE datid=(SELECT oid FROM pg_database WHERE datname=current_database()) AND usename='supabase_auth_admin'"

    def __init__(self, records, admin, container):
        from auth_protocol import STATS
        need(type(container) is AuthContainer and not container.start_attempted, 'counter_before_start')
        self.records, self.admin, self.container = records, admin, container
        self.done = False
        self.before = admin.execute('select '+STATS+' value').fetchone()['value']
        records.save('managed-before.json', self.before)

    def finish(self):
        from auth_protocol import STATS, difference
        need(not self.done and self.container.stopped is True, 'counter_before_producer_stop')
        self.done = True
        self.container._authority()
        journal = self.container.safety.journal
        need('stopped.json' in journal.entries, 'counter_stop_original_missing')
        stopped = json.loads(journal._read('stopped.json', journal.entries['stopped.json']))
        need(stopped.get('id') == self.container.id and stopped.get('labels') == self.container.labels
             and stopped.get('process_stopped') is True, 'counter_stop_original_binding')
        need(self.admin.execute(self.ACTIVITY).fetchone() == {'n': 0}, 'managed_backends_remain')
        after = self.admin.execute('select '+STATS+' value').fetchone()['value']
        self.records.save('managed-after-stop.json', after)
        result = difference(self.before, after)
        result.update(post_stop_observed=True, original_claims_released=False,
            actual_component_only=True, implicit_native_sql_bound=None, full_chain_admission=False)
        self.records.save('managed-lifetime.json', result)
        return result
