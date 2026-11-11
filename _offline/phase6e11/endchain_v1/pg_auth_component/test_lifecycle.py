"""Offline control tests. Fake Docker/SQL never count as actual stack proof."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from . import lifecycle as m

RUN = 'a0d72b98-f5f4-4971-999d-402cf43bc802'


def secrets_for(container):
    return {'GOTRUE_DB_DATABASE_URL':m.database_url('PRIVATE_REVIEW_SENTINEL',container.name),
            'GOTRUE_JWT_SECRET':'PRIVATE_REVIEW_SENTINEL'}


class Docker:
    def __init__(self):
        self.calls = []
        self.container = None
        self.phase_fault = None
        self.corrupt = None
        self.endpoint = 'unix:///var/run/docker.sock'

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        args = args[3:]
        command = args[0]
        reply = ''
        if command == 'context': reply = self.endpoint
        elif command == 'image': reply = json.dumps({'id':'sha256:'+'1'*64,'digests':[m.IMAGE]})
        elif command == 'ps': reply = '' if self.container is None else self.container['id']
        elif command == 'create':
            labels = dict(args[i+1].split('=', 1) for i, x in enumerate(args) if x == '--label')
            self.container = {'id':'2'*64,'name':'/'+args[args.index('--name')+1],
                'image':'sha256:'+'1'*64,'labels':labels,'running':False,'pid':0,'status':'created'}
            env=[]
            for i,x in enumerate(args):
                if x == '-e':
                    item=args[i+1]
                    env.append(item if '=' in item else item+'='+kwargs['env'][item])
            mount=args[args.index('--mount')+1]
            fields=dict(p.split('=',1) for p in mount.split(',') if '=' in p)
            network=args[args.index('--network')+1]
            self.container.update(cmd=args[-2:],environment=env,network=network,
                networks={network:{'IPAddress':'172.19.0.2'}},
                mounts=[{'Type':'bind','Source':fields['src'],'Destination':fields['dst'],'RW':False}])
            reply = self.container['id']
        elif command == 'inspect':
            value = copy.deepcopy(self.container)
            if self.corrupt: self.corrupt(value)
            reply = json.dumps(value)
        elif command == 'start':
            self.container.update(running=True,pid=123,status='running')
            reply = self.container['id']
        elif command == 'stop':
            self.container.update(running=False,pid=0,status='exited')
        elif command == 'rm': self.container=None
        else: raise AssertionError(command)
        if self.phase_fault == command:
            raise subprocess.TimeoutExpired('PRIVATE_REVIEW_SENTINEL', 5)
        return SimpleNamespace(returncode=0, stdout=reply)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.gate = SimpleNamespace(out=Path(self.temp.name), work=Path(self.temp.name), save=lambda *args: None)
        ca=self.gate.work/'fmz-ci-ca.crt';ca.write_bytes(b'unit synthetic CA bytes')
        (self.gate.out/'case-stack-bootstrap.json').write_text(json.dumps({'ca_sha256':m.durable.sha(ca.read_bytes())}))
        self.docker = Docker()
        for target, value in ((m.binding, 'verify'),):
            p = patch.object(target, value, return_value={'unit_only': True})
            p.start(); self.addCleanup(p.stop)
        patches = [patch.object(m.sys, 'platform', 'linux'),
            patch.dict(os.environ, {'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging',
                'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'123','GH_READ_TOKEN':'PRIVATE_REVIEW_SENTINEL'}, clear=True),
            patch.object(m.subprocess, 'run', side_effect=self.docker)]
        for p in patches: p.start(); self.addCleanup(p.stop)

    def ready(self):
        value = m.AuthContainer(self.gate, RUN)
        value.create('local_stack', secrets_for(value))
        value.start()
        return value

    def test_preregister_then_actual_command_order(self):
        value = self.ready(); value.stop()
        self.assertTrue(value.stopped)
        self.assertEqual(value.commands, 14)
        self.assertTrue((value.records.journal.folder/'intent.json').exists())
        self.assertFalse(any('rm' in args for args, _ in self.docker.calls))
        raw = b''.join(p.read_bytes() for p in value.records.journal.folder.iterdir())
        self.assertNotIn(b'PRIVATE_REVIEW_SENTINEL', raw)
        for args, kwargs in self.docker.calls:
            self.assertNotIn('GH_READ_TOKEN', kwargs['env'])
            if 'create' not in args:
                self.assertNotIn('GOTRUE_JWT_SECRET', kwargs['env'])

    def test_remote_docker_denied_before_image_or_create(self):
        self.docker.endpoint = 'tcp://remote.invalid:2376'
        with self.assertRaisesRegex(RuntimeError, 'local_docker_endpoint'): m.AuthContainer(self.gate, RUN)
        self.assertEqual(len(self.docker.calls), 1)

    def test_docker_env_denied_before_any_command(self):
        with patch.dict(os.environ, {'DOCKER_HOST':'unix:///alternate'}):
            with self.assertRaisesRegex(RuntimeError, 'docker_override'): m.AuthContainer(self.gate, RUN)
        self.assertEqual(self.docker.calls, [])

    def test_lost_create_adopts_only_for_stop(self):
        value = m.AuthContainer(self.gate, RUN); self.docker.phase_fault = 'create'
        with self.assertRaises(subprocess.TimeoutExpired):
            value.create('net', secrets_for(value))
        self.docker.phase_fault = None
        value.stop()
        self.assertTrue(value.stopped)
        self.assertEqual(value.original_errors[0]['phase'], 'create')
        self.assertFalse(value.start_attempted)

    def test_lost_start_sticky_even_after_stop(self):
        value = m.AuthContainer(self.gate, RUN)
        value.create('net', secrets_for(value))
        self.docker.phase_fault = 'start'
        with self.assertRaises(subprocess.TimeoutExpired): value.start()
        self.docker.phase_fault = None; value.stop()
        self.assertTrue(value.stopped)
        record = json.loads((value.safety.journal.folder/'stopped.json').read_bytes())
        self.assertFalse(record['original_outcome_reclassified'])
        self.assertFalse(record['auth_commit_known'])

    def test_lost_stop_inspection_known_but_error_preserved(self):
        value = self.ready(); self.docker.phase_fault = 'stop'
        with self.assertRaises(subprocess.TimeoutExpired): value.stop()
        self.assertTrue(value.stopped)

    def test_wrong_nonce_blocks_stop(self):
        value = self.ready()
        self.docker.corrupt = lambda v: v['labels'].update({'fmz.nonce':'foreign'})
        with self.assertRaisesRegex(RuntimeError, 'ownership'): value.stop()
        self.assertFalse(any(args[3] == 'stop' for args, _ in self.docker.calls))

    def test_missing_label_blocks_stop(self):
        value = self.ready()
        self.docker.corrupt = lambda v: v['labels'].pop('fmz.source')
        with self.assertRaisesRegex(RuntimeError, 'ownership'): value.stop()
        self.assertFalse(value.stopped)

    def test_wrong_image_blocks_stop(self):
        value = self.ready(); self.docker.corrupt = lambda v: v.update(image='sha256:'+'3'*64)
        with self.assertRaisesRegex(RuntimeError, 'ownership'): value.stop()

    def test_wrong_name_blocks_stop(self):
        value = self.ready(); self.docker.corrupt = lambda v: v.update(name='/another')
        with self.assertRaisesRegex(RuntimeError, 'ownership'): value.stop()

    def test_wrong_id_blocks_stop(self):
        value = self.ready(); self.docker.container['id'] = '4'*64
        with self.assertRaisesRegex(RuntimeError, 'identity_changed'): value.stop()

    def test_missing_container_not_inferred_zero(self):
        value = self.ready(); self.docker.container = None
        with self.assertRaisesRegex(RuntimeError, 'created_identity_missing'): value.stop()
        self.assertFalse(value.stopped)

    def test_changed_intent_blocks_stop(self):
        value = self.ready()
        (value.records.journal.folder/'intent.json').write_bytes(b'{}')
        with self.assertRaises(ValueError): value.stop()
        self.assertFalse(value.stopped)

    def test_changed_source_blocks_stop(self):
        value = self.ready()
        with patch.object(m.binding, 'verify', return_value={'changed':True}):
            with self.assertRaisesRegex(RuntimeError, 'source_changed'): value.stop()

    def test_create_not_admitted_if_intent_save_failed(self):
        original = m.Records.save
        def save(records, name, value):
            if name == 'intent.json': raise OSError('unit')
            original(records, name, value)
        with patch.object(m.Records, 'save', save):
            with self.assertRaises(OSError): m.AuthContainer(self.gate, RUN)
        self.assertFalse(any(args[3] == 'create' for args, _ in self.docker.calls))

    def test_second_stop_denied(self):
        value = self.ready(); value.stop()
        with self.assertRaisesRegex(RuntimeError, 'stop_scope'): value.stop()

    def test_unknown_stop_no_stopped_receipt(self):
        value = self.ready()
        self.docker.corrupt = lambda v: v.update(running=True,pid=123,status='running')
        with self.assertRaisesRegex(RuntimeError, 'stop_unknown'): value.stop()
        self.assertFalse(value.stopped)
        self.assertFalse((value.safety.journal.folder/'stopped.json').exists())

    def test_exact_remove_and_absence_within_original_sixteen(self):
        value=self.ready();value.stop();value.remove()
        self.assertTrue(value.removed)
        self.assertEqual(value.commands,16)
        command=next(args for args,_ in self.docker.calls if args[3]=='rm')
        self.assertEqual(command,['docker','--context','default','rm','2'*64])
        original=json.loads((value.safety.journal.folder/'absent.json').read_bytes())
        self.assertTrue(original['exact_container_absent'])
        self.assertFalse(original['global_cleanup'])

    def test_remove_before_stop_denied(self):
        value=self.ready()
        with self.assertRaisesRegex(RuntimeError,'remove_scope'):value.remove()
        self.assertFalse(any(args[3]=='rm' for args,_ in self.docker.calls))

    def test_remove_lost_reply_preserves_error_after_absence(self):
        value=self.ready();value.stop();self.docker.phase_fault='rm'
        with self.assertRaises(subprocess.TimeoutExpired):value.remove()
        self.assertTrue(value.removed)
        with self.assertRaisesRegex(RuntimeError,'remove_scope'):value.remove()

    def test_remove_without_original_stop_denied(self):
        value=self.ready();value.stopped=True
        with self.assertRaisesRegex(RuntimeError,'original_stop_required'):value.remove()

    def test_changed_ca_before_create_denied(self):
        value=m.AuthContainer(self.gate,RUN)
        value.ca.write_bytes(b'changed unit CA')
        with self.assertRaisesRegex(RuntimeError,'original_ca'):value.create('net',secrets_for(value))
        self.assertFalse(any(args[3]=='create' for args,_ in self.docker.calls))

    def test_missing_verify_full_url_denied(self):
        value=m.AuthContainer(self.gate,RUN)
        env=secrets_for(value);env['GOTRUE_DB_DATABASE_URL']='postgres://supabase_auth_admin:x@'+m.startup.PG_NAME+':5432/postgres'
        with self.assertRaisesRegex(RuntimeError,'auth_verify_full'):value.create('net',env)

    def test_wrong_auth_application_name_denied(self):
        value=m.AuthContainer(self.gate,RUN)
        env=secrets_for(value);env['GOTRUE_DB_DATABASE_URL']=m.database_url('x','foreign')
        with self.assertRaisesRegex(RuntimeError,'auth_verify_full'):value.create('net',env)

    def test_writable_ca_mount_denied(self):
        value=self.ready()
        self.docker.corrupt=lambda v:v['mounts'][0].update(RW=True)
        with self.assertRaisesRegex(RuntimeError,'readonly_ca_mount'):value.stop()

    def test_missing_ca_mount_denied(self):
        value=self.ready();self.docker.corrupt=lambda v:v.update(mounts=[])
        with self.assertRaisesRegex(RuntimeError,'readonly_ca_mount'):value.stop()

    def test_changed_private_auth_url_denied_without_export(self):
        value=self.ready()
        self.docker.corrupt=lambda v:v.update(environment=[x.replace('sslmode=verify-full','sslmode=disable') for x in v['environment']])
        with self.assertRaisesRegex(RuntimeError,'private_config_changed'):value.stop()

    def test_serve_only_command_required(self):
        value=self.ready();self.docker.corrupt=lambda v:v.update(cmd=['auth','migrate'])
        with self.assertRaisesRegex(RuntimeError,'serve_only_config'):value.stop()

    def test_poisoned_normal_journal_still_stops_and_removes_exact_owned(self):
        value=self.ready();value.records.journal.poisoned=True
        value.stop();value.remove()
        self.assertTrue(value.stopped and value.removed)
        self.assertEqual(value.commands,16)
        with self.assertRaisesRegex(RuntimeError,'journal_poisoned'):value.records.seal()
        value.safety.seal()

    def test_lost_normal_after_record_still_stops_created_container(self):
        value=m.AuthContainer(self.gate,RUN)
        original=value.records.save
        def save(name,record):
            if name.endswith('create-after.json'):
                value.records.journal.poisoned=True
                raise OSError('original_receipt_failure')
            return original(name,record)
        value.records.save=save
        with self.assertRaisesRegex(OSError,'original_receipt_failure'):
            value.create('net',secrets_for(value))
        value.stop();value.remove()
        self.assertTrue(value.removed)
        self.assertFalse(value.start_attempted)

    def test_poisoned_safety_journal_stops_but_never_terminal_pass(self):
        value=self.ready();value.safety.journal.poisoned=True
        with self.assertRaisesRegex(RuntimeError,'journal_poisoned'):value.stop()
        self.assertFalse(self.docker.container['running'])
        self.assertEqual(sum(args[3]=='stop' for args,_ in self.docker.calls),1)
        self.assertFalse((value.safety.journal.folder/'stopped.json').exists())
        with self.assertRaisesRegex(RuntimeError,'original_stop_required'):value.remove()
        self.assertFalse(value.removed)

    def fail_safety_append(self,suffix):
        value=self.ready();first=OSError('original_audit_failure')
        save=value.safety.save
        def broken(name,record):
            if name.endswith(suffix):
                value.safety.journal.poisoned=True
                raise first
            return save(name,record)
        value.safety.save=broken
        with self.assertRaises(OSError) as caught:value.stop()
        self.assertIs(caught.exception,first)
        self.assertFalse(self.docker.container['running'])
        self.assertEqual(sum(args[3]=='stop' for args,_ in self.docker.calls),1)
        self.assertLessEqual(value.commands,16)
        self.assertFalse((value.safety.journal.folder/'stopped.json').exists())
        return value,first

    def test_safety_before_append_failure_still_physical_stop(self):
        self.fail_safety_append('inventory-before.json')

    def test_safety_after_append_failure_still_physical_stop(self):
        self.fail_safety_append('inventory-after.json')

    def test_safety_fsync_failure_still_physical_stop_without_terminal(self):
        value=self.ready();first=OSError('original_fsync')
        with patch.object(m.durable.os,'fsync',side_effect=first):
            with self.assertRaises(OSError) as caught:value.stop()
        self.assertIs(caught.exception,first)
        self.assertFalse(self.docker.container['running'])
        self.assertFalse((value.safety.journal.folder/'stopped.json').exists())
        self.assertEqual(value.commands,14)

    def test_safety_append_failure_does_not_waive_fresh_ownership(self):
        value=self.ready();value.safety.journal.poisoned=True
        self.docker.corrupt=lambda v:v['labels'].update({'fmz.nonce':'foreign'})
        with self.assertRaisesRegex(RuntimeError,'journal_poisoned'):value.stop()
        self.assertTrue(self.docker.container['running'])
        self.assertFalse(any(args[3]=='stop' for args,_ in self.docker.calls))

    def test_safety_append_failure_does_not_waive_source_pin(self):
        value=self.ready();value.safety.journal.poisoned=True
        with patch.object(m.binding,'verify',return_value={'changed':True}):
            with self.assertRaisesRegex(RuntimeError,'source_changed'):value.stop()
        self.assertFalse(any(args[3]=='stop' for args,_ in self.docker.calls))

    def test_changed_original_safety_authority_denies_every_closing_command(self):
        value=self.ready()
        (value.safety.journal.folder/'authority.json').write_bytes(b'{}')
        count=len(self.docker.calls)
        with self.assertRaises(ValueError):value.stop()
        self.assertEqual(len(self.docker.calls),count)

    def test_exhausted_command_reserve_never_dispatches_fallback(self):
        value=self.ready();value.commands=16;value.safety.journal.poisoned=True
        count=len(self.docker.calls)
        with self.assertRaisesRegex(RuntimeError,'docker_command_bound'):value.stop()
        self.assertEqual(len(self.docker.calls),count)

    def test_extra_nonclosing_inspection_cannot_spend_seven_closing_slots(self):
        value=self.ready();self.assertEqual(value.commands,9)
        before=len(self.docker.calls)
        with self.assertRaisesRegex(RuntimeError,'closing_reserve_required'):value.inspect()
        self.assertEqual(value.commands,9)
        self.assertEqual(len(self.docker.calls),before)
        value.stop();value.remove()
        self.assertEqual(value.commands,16)
        self.assertTrue(value.removed)

    def test_audit_failure_remains_primary_when_physical_stop_reply_lost(self):
        self.docker.phase_fault='stop'
        value,first=self.fail_safety_append('inventory-before.json')
        self.assertIn('component_docker_stop_secondary:TimeoutExpired',first.__notes__)
        self.assertFalse(value.removed)

    def test_fallback_cannot_create_start_retry_force_or_prune(self):
        value=self.ready();value._closing=True
        for phase,args in (('create',['create']),('start',['start',value.id]),
            ('prune',['container','prune']),('stop',['stop','--force',value.id])):
            with self.assertRaises(RuntimeError):value._command(phase,args)
        self.assertFalse(any(args[3]=='stop' for args,_ in self.docker.calls))

    def chronology(self,operation,when):
        value=self.ready()
        if operation=='remove':value.stop()
        audit=OSError('PRIVATE_REVIEW_SENTINEL')
        save=value.safety.save
        def broken(name,record):
            if name.endswith(operation+'-'+when+'.json'):raise audit
            return save(name,record)
        value.safety.save=broken
        self.docker.phase_fault='rm' if operation=='remove' else 'stop'
        expected=OSError if when=='before' else subprocess.TimeoutExpired
        with self.assertRaises(expected) as caught:getattr(value,operation)()
        self.assertIs(caught.exception,value.closing_failure)
        if when=='before':self.assertIs(caught.exception,audit)
        else:self.assertIn('component_safety_append_secondary:OSError',caught.exception.__notes__)
        self.assertEqual([e['ordinal'] for e in value.closing_errors],[1,2])
        expected_phases=['safety_append','docker_'+operation] if when=='before' else ['docker_'+operation,'safety_append']
        self.assertEqual([e['phase'] for e in value.closing_errors],expected_phases)
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL',str(value.closing_errors))
        self.assertNotIn('PRIVATE_REVIEW_SENTINEL',str(getattr(caught.exception,'__notes__',[])))
        self.assertLessEqual(value.commands,16)
        self.assertEqual(sum(args[3]==self.docker.phase_fault for args,_ in self.docker.calls),1)

    def test_stop_audit_before_timeout_remains_primary(self):self.chronology('stop','before')
    def test_stop_timeout_before_audit_remains_primary(self):self.chronology('stop','after')
    def test_remove_audit_before_timeout_remains_primary(self):self.chronology('remove','before')
    def test_remove_timeout_before_audit_remains_primary(self):self.chronology('remove','after')


def sample(calls=1):
    return {'reset':'x','dealloc':0,'track_utility':'on','statements':[
        {'queryid':'1','since':'x','calls':calls,'temp_read':0,'temp_written':0,'wal_bytes':0,'exec_ms':calls}]}


class CounterTests(unittest.TestCase):
    setUp = LifecycleTests.setUp
    ready = LifecycleTests.ready
    def counter(self, value, replies):
        class Admin:
            def execute(self, *args):
                result = replies.pop(0)
                return SimpleNamespace(fetchone=lambda: result)
        return m.StoppedCounters(value.records, Admin(), value)

    def test_before_start_required(self):
        value = self.ready()
        with self.assertRaisesRegex(RuntimeError, 'counter_before_start'): self.counter(value, [])

    def test_cannot_sample_before_stop(self):
        value = m.AuthContainer(self.gate, RUN)
        counter = self.counter(value, [{'value':sample()}])
        with self.assertRaisesRegex(RuntimeError, 'counter_before_producer_stop'): counter.finish()

    def test_post_stop_sample_and_no_refund(self):
        value = m.AuthContainer(self.gate, RUN)
        counter = self.counter(value, [{'value':sample()}, {'n':0}, {'value':sample(5)}])
        value.create('net', secrets_for(value))
        value.start(); value.stop()
        result = counter.finish()
        self.assertEqual(result['commands'], 4)
        self.assertFalse(result['original_claims_released'])
        self.assertIsNone(result['implicit_native_sql_bound'])
        with self.assertRaises(RuntimeError): counter.finish()

    def test_live_backend_after_stop_not_complete(self):
        value = m.AuthContainer(self.gate, RUN)
        counter = self.counter(value, [{'value':sample()}, {'n':1}])
        value.create('net', secrets_for(value))
        value.start(); value.stop()
        with self.assertRaisesRegex(RuntimeError, 'managed_backends_remain'): counter.finish()

    def test_counter_reset_never_complete(self):
        value = m.AuthContainer(self.gate, RUN)
        after = sample(5); after['reset']='changed'
        counter = self.counter(value, [{'value':sample()}, {'n':0}, {'value':after}])
        value.create('net', secrets_for(value))
        value.start(); value.stop()
        with self.assertRaises(ValueError): counter.finish()
        self.assertFalse((value.records.journal.folder/'managed-lifetime.json').exists())

    def test_stopped_flag_without_original_receipt_cannot_sample(self):
        value=m.AuthContainer(self.gate,RUN)
        counter=self.counter(value,[{'value':sample()}])
        value.create('net',secrets_for(value));value.stopped=True
        with self.assertRaisesRegex(RuntimeError,'stop_original_missing'):counter.finish()


if __name__ == '__main__': unittest.main()
