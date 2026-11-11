"""Negative pre-Auth witness validation. No containers or database are started."""
import copy
import contextlib
import json
import os
import pathlib
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from quota_candidate_v1 import runtime_bootstrap_closeout as r
from quota_candidate_v1.compiler import CandidateStop
from sql_protocol import statements


class BootstrapCloseoutTests(unittest.TestCase):
    def setUp(self):
        self.pg=dict(id='a'*64,image='supabase/postgres:17.6.1.167',name='supabase_db_fmz-db41-ci')
        self.identity=dict(database='postgres',role='postgres',version=17,readonly='on',ssl=True,
            statement_timeout='5s',lock_timeout='1s',database_oid=5,pg_system_identifier='12345678')
        self.counts=dict(users=0,sessions=0,refresh_tokens=0,controller_runs=0,history_count=44)

    def test_exact_four_readonly_commands_and_no_mutation(self):
        self.assertEqual(len(r.COMMANDS),4)
        self.assertEqual([statements(q)[0]['kind'] for q in r.COMMANDS],
            ['TransactionStmt','SelectStmt','SelectStmt','TransactionStmt'])
        self.assertTrue(all(len(statements(q))==1 for q in r.COMMANDS))

    def test_actual_full_inventory_no_gotrue_returns_pg_only(self):
        value=r.inventory(json.dumps(self.pg),self.pg['name'])
        self.assertEqual(value['pg_container'],self.pg['id'])
        self.assertEqual(value['gotrue_containers'],0)
        self.assertEqual(value['inventory_rows'],[self.pg])
        self.assertEqual(value['inventory_sha256'],r.sha(r.canonical([self.pg])))

    def test_exact_docker_format_renders_one_complete_json_object(self):
        template=r.DOCKER_ARGS[-1]
        rendered=template.replace('{{.ID}}',self.pg['id']).replace(
            '{{.Image}}',self.pg['image']).replace('{{.Names}}',self.pg['name'])
        self.assertEqual(json.loads(rendered),self.pg)
        self.assertEqual(r.inventory(rendered,self.pg['name'])['inventory_rows'],[self.pg])

    def test_duplicate_id_name_and_nontechnical_fields_denied(self):
        for row in [{**self.pg,'name':'different'}, {**self.pg,'id':'b'*64},
                    {**self.pg,'image':'bad\nimage'}, {**self.pg,'name':'bad name'}]:
            with self.subTest(row=row),self.assertRaises(CandidateStop):
                r.inventory(json.dumps(self.pg)+'\n'+json.dumps(row),self.pg['name'])

    def test_existing_gotrue_any_name_or_known_auth_container_rejected(self):
        for row in [dict(id='b'*64,image='supabase/gotrue:v2.197.0',name='unrecognized_name'),
                    dict(id='b'*64,image='sha256:opaque',name='fmz-guard-auth-ci')]:
            with self.subTest(row=row),self.assertRaises(CandidateStop):
                r.inventory(json.dumps(self.pg)+'\n'+json.dumps(row),self.pg['name'])

    def test_truncated_ids_missing_pg_and_unbounded_inventory_denied(self):
        for rows in [[{**self.pg,'id':'a'*12}],[],[self.pg]*33]:
            with self.assertRaises(CandidateStop):
                r.inventory('\n'.join(json.dumps(x) for x in rows),self.pg['name'])

    def test_accounts_tokens_and_claims_must_be_measured_zero(self):
        r.check_samples(self.identity,self.counts,'pre_migration')
        for field in ('users','sessions','refresh_tokens','controller_runs'):
            for value in (1,False,None):
                with self.subTest(field=field,value=value),self.assertRaises(CandidateStop):
                    r.check_samples(self.identity,{**self.counts,field:value},'pre_migration')

    def test_wrong_history_or_nonreadonly_connection_denied(self):
        with self.assertRaises(CandidateStop):r.check_samples(self.identity,self.counts,'post_migration')
        r.check_samples(self.identity,{**self.counts,'history_count':45},'post_migration')
        for field,value in [('ssl',False),('readonly','off'),('version',16),('statement_timeout','0')]:
            with self.assertRaises(CandidateStop):r.check_samples({**self.identity,field:value},self.counts,'pre_migration')


class CollectorDriverTests(unittest.TestCase):
    """Transport doubles prove control flow only, never actual absence or CASE_PASS."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out=pathlib.Path(self.temp.name)
        self.binding=dict(run_id='3d77bbf8-cdce-416a-a63c-9b16ed83c428',ci_run='123',
            source_commit='b'*40,candidate_sha='c'*64,environment='disposable_ci')
        self.env=dict(GITHUB_ACTIONS='true',GITHUB_REPOSITORY='Yourizorge/fitmetzorge-staging',
            GITHUB_REF='refs/heads/main',GITHUB_RUN_ATTEMPT='1',GITHUB_RUN_ID='123',GITHUB_SHA='b'*40)
        self.case='pre_migration'
        self.fault=types.SimpleNamespace(case=self.case,binding=self.binding,
            fired=dict(event=dict(stage='before45')))
        (self.out/'case-fault-boundary.json').write_text(json.dumps(self.fault.fired))
        self.pg=dict(id='a'*64,image='supabase/postgres:17.6.1.167',name='supabase_db_fmz-db41-ci')
        self.identity=dict(database='postgres',role='postgres',version=17,readonly='on',ssl=True,
            statement_timeout='5s',lock_timeout='1s',database_oid=5,pg_system_identifier='12345678')
        self.counts=dict(users=0,sessions=0,refresh_tokens=0,controller_runs=0,history_count=44)
        def save(name,value):
            with (self.out/name).open('x') as stream:json.dump(value,stream)
        def command(label,args,timeout):
            self.assertTrue((self.out/'case-preauth-closeout-reservation.json').is_file())
            self.assertEqual((label,args,timeout),
                ('case-preauth-container-inventory',list(r.DOCKER_ARGS),5))
            return types.SimpleNamespace(returncode=0,stdout=json.dumps(self.pg))
        self.gate=types.SimpleNamespace(out=self.out,container=self.pg['name'],
            result=dict(candidate_sha256='c'*64),bind_modules=Mock(),save=save,
            command=Mock(side_effect=command))
        def execute(sql):
            rows=[self.identity] if sql==r.IDENTITY else [self.counts] if sql==r.ACCOUNTS else []
            return types.SimpleNamespace(description=bool(rows),fetchall=lambda:copy.deepcopy(rows))
        self.connection=types.SimpleNamespace(execute=Mock(side_effect=execute),close=Mock())
        self.runtime=types.SimpleNamespace(connect=Mock(return_value=self.connection),clear=Mock())

    def collect(self):
        with patch.dict(os.environ,self.env),patch.object(r.native_runtime.NativeRuntime,
                'disposable',return_value=self.runtime):
            return r.collect(self.gate,self.binding,self.case,self.fault)

    def test_complete_driver_receipts_retain_recomputable_inventory_and_exact_commands(self):
        result=self.collect()
        self.assertEqual(result['auth_state'],'not_started')
        self.assertIsNone(result['auth_container'])
        self.assertFalse(result['auth_database_bound'])
        docker=json.loads((self.out/'case-preauth-container-absence.json').read_bytes())
        self.assertEqual(docker['inventory_rows'],[self.pg])
        self.assertEqual(docker['inventory_command'],dict(argv=list(r.DOCKER_ARGS),exitcode=0,
            timeout_seconds=5,dispatch_calls=1))
        self.assertEqual(docker['inventory_sha256'],r.sha(r.canonical(docker['inventory_rows'])))
        self.assertEqual([call.args[0] for call in self.connection.execute.call_args_list],list(r.COMMANDS))
        account=json.loads((self.out/'case-preauth-account-absence.json').read_bytes())
        self.assertTrue(account['complete'])
        self.assertTrue(account['rollback_confirmed'] and account['connection_closed'])
        self.assertFalse(account['auth_started'] or account['worker_started'] or account['quota_appended'])
        for ref in result['auth_absence'].values():
            if isinstance(ref,dict):
                raw=(self.out/ref['path']).read_bytes()
                self.assertEqual((len(raw),r.sha(raw)),(ref['bytes'],ref['sha256']))

    def test_fsync_failure_prevents_even_docker_dispatch(self):
        error=OSError('durability')
        with patch.object(r.os,'fsync',side_effect=error),self.assertRaises(OSError) as caught:
            self.collect()
        self.assertIs(caught.exception,error)
        self.gate.command.assert_not_called()
        self.runtime.connect.assert_not_called()
        self.connection.execute.assert_not_called()

    def test_two_byte_reservation_write_prevents_all_dispatch(self):
        original_open=pathlib.Path.open
        reservation=self.out/'case-preauth-closeout-reservation.json'
        @contextlib.contextmanager
        def opened(path,mode='r',*args,**kwargs):
            with original_open(path,mode,*args,**kwargs) as stream:
                if path==reservation and mode=='xb':
                    yield types.SimpleNamespace(write=lambda raw:stream.write(raw[:2]),
                        flush=stream.flush,fileno=stream.fileno)
                else:yield stream
        with patch.object(pathlib.Path,'open',new=opened),self.assertRaisesRegex(
                CandidateStop,'bootstrap_closeout_reservation_short_write'):
            self.collect()
        self.assertEqual(len(reservation.read_bytes()),2)
        self.gate.command.assert_not_called()
        self.runtime.connect.assert_not_called()
        self.connection.execute.assert_not_called()

    def test_corrupt_durable_readback_prevents_all_dispatch(self):
        original_fsync=r.os.fsync
        reservation=self.out/'case-preauth-closeout-reservation.json'
        def corrupt(fd):
            original_fsync(fd)
            with reservation.open('r+b') as stream:
                stream.write(b'!!');stream.flush();original_fsync(stream.fileno())
        with patch.object(r.os,'fsync',side_effect=corrupt),self.assertRaisesRegex(
                CandidateStop,'bootstrap_closeout_reservation_readback'):
            self.collect()
        self.assertTrue(reservation.read_bytes().startswith(b'!!'))
        self.gate.command.assert_not_called()
        self.runtime.connect.assert_not_called()
        self.connection.execute.assert_not_called()

    def test_nonzero_inventory_never_connects_or_claims_complete(self):
        self.gate.command.side_effect=None
        self.gate.command.return_value=types.SimpleNamespace(returncode=1,stdout=json.dumps(self.pg))
        with self.assertRaisesRegex(CandidateStop,'bootstrap_container_inventory_exit'):self.collect()
        self.runtime.connect.assert_not_called()
        receipt=json.loads((self.out/'case-preauth-account-absence.json').read_bytes())
        self.assertFalse(receipt['complete'])
        self.assertIsNone(receipt['account_counts'])

    def test_lost_begin_attempt_rolls_back_once_preserving_original_error(self):
        error=OSError('lost_begin_result')
        self.connection.execute.side_effect=[error,types.SimpleNamespace(description=None)]
        with self.assertRaises(OSError) as caught:self.collect()
        self.assertIs(caught.exception,error)
        self.assertEqual([call.args[0] for call in self.connection.execute.call_args_list],
            [r.COMMANDS[0],r.COMMANDS[3]])
        self.connection.close.assert_called_once()
        self.runtime.clear.assert_called_once()
        receipt=json.loads((self.out/'case-preauth-account-absence.json').read_bytes())
        self.assertFalse(receipt['complete'])
        self.assertTrue(receipt['rollback_confirmed'])

    def test_repeat_reservation_denies_retry_before_second_dispatch(self):
        self.collect()
        with self.assertRaises(FileExistsError):self.collect()
        self.gate.command.assert_called_once()
        self.runtime.connect.assert_called_once()


if __name__=='__main__':unittest.main()
