"""44 synthetic original sets through the installed real readers in a child.

No PG/CLI execution. Synthetic AST identities deliberately do not prove SQL.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import uuid

import admission_budget_prefix_originals as audit
import admission_canonical_replay as replay
import admission_terminal_process as process
import cli_stat_reader as stat
from test_admission_canonical_replay import numeric_receipt

P = process.PREFIX
READER = '''import hashlib,json
from types import SimpleNamespace
from canonical_fixture_originals import Originals
import admission_canonical_replay
def verify_exported_terminal(payloads,case,**kw):
    loader=globals()['__trusted_imports__']
    values=kw['originals']
    refs=[dict(path=n,sha256=hashlib.sha256(v).hexdigest(),bytes=len(v)) for n,v in values.items()]
    evidence=Originals(values,refs)
    trusted=SimpleNamespace(root=loader.root,sources=loader.sources,raw=loader.raw,module=loader.module)
    binding=dict(run_id=case['run_id'],source_commit=kw['source_commit'],ci_run=kw['ci_run'],
                 candidate_sha=kw['candidate_sha256'],environment='disposable_ci')
    result=admission_canonical_replay.replay(evidence,trusted,binding)
    return dict(status='CASE_TERMINAL_UNVERIFIED',case_name=case['case_name'],run_id=case['run_id'],
        case_sha256=hashlib.sha256(payloads['case-execution.json']).hexdigest(),
        checks={'canonical':result,'used':sorted(evidence.used)},missing=result['missing'],invalid=[],
        full_chain_admission=False,hosted_admitted=False)
'''


def encoded(value):
    return json.dumps(value, separators=(',', ':'), allow_nan=False).encode()


class CanonicalChildTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='canonical-child-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.sources, self.originals = {}, {}
        installed = Path(__file__).resolve().parents[3]
        names = set(audit.CURRENT_PINS) | {
            audit.prefix.REVIEWED_BYTE_PAIRS, audit.prefix.HARNESS, replay.ISOLATION,
            P+'admission_canonical_replay.py', P+'admission_budget_prefix_originals.py',
            P+'admission_budget_bootstrap_prefix.py', P+'cli_stat_reader.py',
            process.SELF, process.LOADER}
        names.update(p.relative_to(installed).as_posix()
                     for p in (installed/'supabase/migrations').glob('*.sql'))
        for name in names:
            self.put(name, (installed/name).read_bytes())
        self.put(process.PACKAGE, b'')
        self.put(P+'canonical_fixture_originals.py', (installed/process.READER_PATH).read_bytes())
        self.put(process.READER_PATH, READER.encode())
        self.case = dict(case_name='normal', run_id=str(uuid.uuid4()))
        self.identity = dict(run_id=self.case['run_id'],source_commit='a'*40,ci_run='123',candidate_sha256='b'*64)
        self.candidate = dict(sha256='b'*64,sources=self.sources)
        _, producers, catalog_sha, setup = audit._source_contract(self.root,self.candidate)
        candidate_ref = self.save('candidate.json',self.candidate)
        spec = importlib.util.spec_from_file_location('canonical_fixture_common',installed/(P+'cli_predispatch/ci.py'))
        self.common = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.common)
        migrations = sorted(n for n in self.sources if n.startswith('supabase/migrations/'))
        self.assertEqual(len(migrations),45)
        invocations = []
        for index,name in enumerate(migrations[:44],1):
            versions=[Path(n).name.split('_',1)[0] for n in migrations[:index-1]]
            identifier=str(uuid.uuid4())
            policy=dict(**self.identity,invocation_id=identifier,slot='ci_prefix',local_bootstrap_only=True,
                prefix_index=index,environment='disposable_ci',version=1,upstream_commit=self.common.UPSTREAM,
                host='127.0.0.1',port=54321,database='postgres',user='postgres',dry_run=False,
                closure_reserve=1,sql_bytes=8192,cap=17,frame_cap=152,expected_history_versions=versions,
                migrations=[dict(sha256=self.sources[name],version=Path(name).name.split('_',1)[0],
                                 ast_hashes=['c'*64])])
            tag='cli-predispatch-prefix-'+str(index)
            policy_ref=self.save(tag+'.policy.json',policy)
            ledger=self.ledger(policy)
            ledger_ref=self.save_raw(tag+'.ledger.txt',ledger)
            evidence_path=self.root/('fixture-ledger-'+str(index)+'.txt')
            evidence_path.write_bytes(ledger)
            replayed=self.common.replay(evidence_path,prefix_policy=policy)
            setting="select current_setting('cron.launch_active_jobs') setting"
            isolation=dict(original='off',restored=True,primary_error_class=None,commands=4,
                protocol=[dict(statement_sha256=replay.sha(s.encode()),confirmed=True) for s in
                    (setting,setting,"select count(*) n from pg_stat_activity where application_name='pg_cron' and state='active'",setting)])
            iso=self.save('prefix-'+str(index)+'-cli-predispatch-cli-isolation-0.json',isolation)
            receipt=dict(**self.identity,profile='canonical_prefix',prefix_index=index,invocation_id=identifier,
                expected_migration=name,expected_migration_sha256=self.sources[name],policy=policy,
                complete=False,local_bootstrap_only=True,actual_migration_execution=False)
            pre=self.save(tag+'-preregister.json',receipt)
            numeric=numeric_receipt()
            numeric['numeric_after']['statements'][0]['calls']=7
            numeric['numeric_coverage']=stat.compare(numeric['numeric_before'],numeric['numeric_after'],3,between=3)
            receipt.update(numeric)
            receipt.update(replayed)
            receipt.update(complete=True,actual_migration_execution=True,cli_exit_code=0,
                policy_ref={k:policy_ref[k] for k in ('path','sha256')},
                ledger_ref={k:ledger_ref[k] for k in ('path','sha256')},
                isolation_receipt=iso['path'],isolation_receipt_sha256=iso['sha256'],
                ci_bootstrap_sql_commands=4,ci_cron_restored=True)
            invocations.append(dict(ordinal=index,migration_path=name,migration_sha256=self.sources[name],
                invocation_id=identifier,requested_arguments=audit.ARGS,executed_argument_shape=audit.EXECUTED,
                original_refs=dict(receipt=self.save(tag+'.json',receipt),preregister=pre,
                                   policy=policy_ref,ledger=ledger_ref,isolation=iso)))
        reserve=self.save('case-stack-reserve-catalog-before41.json',dict(commands=['catalog'],reserved=1))
        catalog=dict(**self.identity,migrations_applied=40,attempted=True,confirmed=False,
            implicit_driver_sql_commands=None,sql_sha256=catalog_sha,command_serial_before=9,reservation_ref=reserve)
        intent=self.save('case-stack-catalog-before41-intent.json',catalog)
        command=self.save('010-psql.json',dict(phase='migration_41',exitcode=0))
        catalog.update(confirmed=True,command_serial_after=10,command_ref=command)
        catalog_ref=self.save('case-stack-catalog-before41.json',catalog)
        provision=dict(**self.identity,complete=False,implicit_driver_sql_proven=False,explicit_reserve=8,protocol=[])
        prepaid=self.save('cli-prefix-history-provision-reserve.json',provision)
        sidecars=[]
        for index,sql in enumerate(setup,1):
            row=dict(ordinal=index,sql_sha256=replay.sha(sql.encode()),confirmed=True)
            provision['protocol'].append(row)
            for suffix,value in (('intent',{**row,'confirmed':False}),('confirmed',row)):
                sidecars.append(self.save('cli-prefix-history-provision-%d-%s.json'%(index,suffix),value))
        provision.update(complete=True,secondary_error_classes=[])
        self.summary=dict(**self.identity,format='case-stack-canonical-prefix-v1',
            candidate_manifest_sha256=candidate_ref['sha256'],original_refs_complete=True,
            independent_numeric_validation=False,implicit_driver_sql_commands=None,total_sql_commands=None,
            hosted_admission=False,producer_sources=producers,invocations=invocations,
            catalog_before41_ref=catalog_ref,catalog_original_refs=dict(command=command,reservation=reserve,intent=intent),
            history_provision_refs=[self.save('cli-prefix-history-provision.json',provision),prepaid,*sidecars])
        self.save(audit.NAME,self.summary)
        self.save('unrelated-not-replayed.json',{'unrelated':True})

    def put(self,name,raw):
        path=self.root/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(raw)
        self.sources[name]=replay.sha(raw)

    def save_raw(self,name,raw):
        self.originals[name]=raw
        return dict(path=name,sha256=replay.sha(raw),bytes=len(raw))

    def save(self,name,value):
        return self.save_raw(name,encoded(value))

    def ledger(self,policy):
        rows=[dict(event='preregister',**policy,policy_sha256=replay.sha(encoded(policy)),
                   hosted_admission=False,migration_statements=1),
              dict(event='connect_attempt',id=1,tls_verify_full=True)]
        for ident,category in enumerate(('history','migration','migration_history'),1):
            rows.extend([dict(event='dispatch',id=ident,protocol='simple',outcome='unknown_consumed',
                              category=category,kind='SelectStmt',ast_sha256='c'*64),
                         dict(event='frontend_frame',type='Q',sql_ids=[ident]),
                         dict(event='frontend_write_returned',type='Q'),
                         dict(event='outcome',id=ident,outcome='command_complete')])
            if ident==1:
                versions=policy['expected_history_versions']
                rows.append(dict(event='history_snapshot',command_id=ident,matches_policy=True,
                                 count=len(versions),versions_sha256=replay.sha(encoded(versions))))
        migration=policy['migrations'][0]
        rows.append(dict(event='history_bind',migration_sha256=migration['sha256'],
                         version=migration['version'],statement_count=1))
        rows.append(dict(event='terminal',sql_dispatches=3,confirmed_sql=3,unknown_consumed=0,
            frontend_frames_by_type={'Q':3},frontend_write_returned_by_type={'Q':3},
            connection_attempts=1,complete=True,hosted_admission=False))
        return self.chain(rows)

    def chain(self,rows):
        previous='0'*64
        result=[]
        for index,row in enumerate(rows,1):
            raw=encoded(dict(row,sequence=index,previous_sha256=previous))
            result.append(raw+b'\n');previous=replay.sha(raw)
        return b''.join(result)

    def inspect(self):
        path=self.root/process.SELF
        scope={'__name__':'test_installed_parent','__file__':str(path)}
        exec(compile(path.read_bytes(),str(path),'exec',dont_inherit=True),scope)
        return scope['inspect_terminal']({'case-execution.json':encoded(self.case)},self.case,self.originals,
            head='a'*40,candidate='b'*64,run='123',expected_sources=self.sources,trusted_root=self.root)

    def test_actual_child_replays_all_44_without_bound_promotion(self):
        report=self.inspect()
        self.assertEqual(report['reader_process']['status'],'INSPECTED_UNVERIFIED',report)
        check=report['checks']['canonical']
        self.assertEqual(check['invocation_count'],44)
        self.assertEqual(len(check['invocations']),44)
        self.assertIsNone(check['total_sql_commands'])
        self.assertIsNone(check['hosted_equivalent_commands'])
        self.assertEqual(check['hosted_projection'],'not_applicable_local_clean_stack_creation')
        self.assertFalse(check['full_chain_admission'])
        self.assertNotIn('unrelated-not-replayed.json',report['checks']['used'])

    def test_rehashed_unpaid_frame_is_not_semantic_proof(self):
        refs=self.summary['invocations'][0]['original_refs']
        rows=[json.loads(line) for line in self.originals[refs['ledger']['path']].splitlines()]
        rows[2],rows[3]=rows[3],rows[2]
        refs['ledger']=self.save_raw(refs['ledger']['path'],self.chain(rows))
        receipt=json.loads(self.originals[refs['receipt']['path']])
        receipt['ledger_ref']={k:refs['ledger'][k] for k in ('path','sha256')}
        refs['receipt']=self.save(refs['receipt']['path'],receipt)
        self.save(audit.NAME,self.summary)
        report=self.inspect()
        self.assertEqual(report['reader_process']['status'],'NO_GO')
        self.assertFalse(report['full_chain_admission'])


if __name__=='__main__':
    unittest.main()
