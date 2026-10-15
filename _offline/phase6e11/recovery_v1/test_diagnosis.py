import copy, json, pathlib, sys, tempfile, unittest
from unittest.mock import patch
import diagnosis as d
import test_migration_boundary as boundary_fixtures


def fixtures(present=True):
    root, before, after = boundary_fixtures.Tests().make()
    paths = sorted((root/'supabase/migrations').glob('*.sql'))
    rows = [{'version':p.stem.split('_',1)[0], 'name':p.stem.split('_',1)[1]} for p in paths[:44 if present else 43]]
    return rows, (after if present else before)['catalog']['m44']


def stats(calls=10):
    return dict(reset='same',dealloc=0,track_utility='on',track='all',
                statements=[dict(queryid='7',calls=calls,since='same',temp_written=0,wal='0')])


class Cursor:
    description = True
    def __init__(self, rows): self.rows = rows
    def fetchall(self): return self.rows


class Connection:
    def __init__(self, fail=None): self.fail=fail; self.sql=[]; self.closed=False
    def execute(self, sql, **kwargs):
        self.sql.append(sql)
        if sql==self.fail: raise TimeoutError('sensitive value must not be copied')
        rows,obj=fixtures()
        return Cursor({d.GUARD:[dict(ro='on',db='postgres',role='postgres',ssl=True,instance_sha=d.INSTANCE)],
                       d.TX:[dict(pid=11,vxid='2/3',readonly='on')],d.MIGRATIONS:rows,
                       d.OBJECTS:[dict(value=obj)],d.HEALTH:[dict(io_wait=0,long_active=0)],
                       d.STATS:[dict(value=stats())]}.get(sql,[]))
    def close(self): self.closed=True


class Runtime:
    environment='staging'
    def __init__(self, fail=None): self.c=Connection(fail)
    def connect(self): return self.c


class Tests(unittest.TestCase):
    def test_real_historical_versions_not_reconstructed_by_validator(self):
        archive=d.ROOT/'_offline/phase6e11/endchain_v1/receipts/reserved-1c3bf7e7-bc78-40c5-9ac1-5ba3512ec66d/integral-preflight.json'
        rows=json.loads(d.disk(archive).read_bytes())['migrations']
        self.assertEqual([r['version'] for r in rows if len(r['version'])!=14],['20260813','20260818'])
        self.assertEqual(d.identity(rows,fixtures(False)[1])['hosted'],43)
        rows.append({'version':d.boundary.VERSION,'name':'phase6e11_single_endchain_budget'})
        self.assertEqual(d.identity(rows,fixtures()[1])['hosted'],44)
    def test_exact_pending_and_already_installed_are_distinct(self):
        for present in (False,True):
            result=d.identity(*fixtures(present))
            self.assertEqual(result['hosted'],44 if present else 43)
            self.assertEqual(result['pending'],[] if present else [d.boundary.FILE])
    def test_changed_registered_sql_cannot_reapply(self):
        rows,obj=fixtures(); obj['migration_statements']=['select 1']
        with self.assertRaisesRegex(ValueError,'registered_sql'):d.identity(rows,obj)
    def test_changed_rights_trigger_and_constraint_block(self):
        for part,key,value in [('function','public_execute',True),('function','path',['public']),
                               ('trigger','enabled','D'),('constraint','expression','command_count<9999')]:
            rows,obj=fixtures();obj[part][key]=value
            with self.assertRaises(ValueError):d.identity(rows,obj)
    def test_wrong_history_and_unregistered_objects_block(self):
        rows,obj=fixtures();rows[0]['version']='wrong'
        with self.assertRaises(ValueError):d.identity(rows,obj)
        rows,obj=fixtures(False);obj['function_oid']=999
        with self.assertRaises(ValueError):d.identity(rows,obj)
    def test_background_never_called_cli_actual(self):
        for cli_and_background in (2,4,16,25,64):
            value=d.attributable(stats(),stats(10+8+cli_and_background),7)
            self.assertIsNone(value['cli_confirmed_commands'])
            self.assertEqual(value['unattributed_calls'],cli_and_background)
            self.assertEqual(value['conservative_budget_charge'],64)
    def test_unknown_over_budget_stops(self):
        with self.assertRaises(ValueError):d.attributable(stats(),stats(83),7)
    def test_top_level_counters_do_not_require_nested_tracking(self):
        before=stats();after=stats(20);before['track']=after['track']='top'
        self.assertEqual(d.attributable(before,after,7)['unattributed_calls'],2)
    def test_missing_reset_duplicates_and_temp_stop(self):
        for change in ('reset','missing','duplicate','temp','track'):
            after=stats(20)
            if change=='reset':after['reset']='other'
            if change=='missing':after['statements']=[]
            if change=='duplicate':after['statements']*=2
            if change=='temp':after['statements'][0]['temp_written']=1
            if change=='track':after['track']='none'
            with self.assertRaises(ValueError):d.attributable(stats(),after,7)
    def test_complete_explicit_readonly_protocol(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime=Runtime();reader=d.Reader(runtime,pathlib.Path(temp));value=reader.capture('before')
            self.assertEqual(runtime.c.sql,[d.__dict__[name] if name in d.__dict__ else name for name in
                ['BEGIN TRANSACTION READ ONLY','GUARD','TX','MIGRATIONS','OBJECTS','HEALTH','STATS','ROLLBACK']])
            self.assertTrue(runtime.c.closed);self.assertEqual(len(reader.commands),8)
            self.assertEqual(value['transaction']['readonly'],'on')
            with self.assertRaises(FileExistsError):d.save(pathlib.Path(temp),'before.json',{})
    def test_all_query_failures_close_and_rollback_no_retry(self):
        for failed in (d.GUARD,d.TX,d.MIGRATIONS,d.OBJECTS,d.HEALTH,d.STATS):
            with tempfile.TemporaryDirectory() as temp:
                runtime=Runtime(failed);reader=d.Reader(runtime,pathlib.Path(temp))
                with self.assertRaises(TimeoutError):reader.capture('before')
                self.assertEqual(runtime.c.sql[-1],'ROLLBACK');self.assertTrue(runtime.c.closed)
                self.assertEqual(runtime.c.sql.count(failed),1)
                self.assertFalse((pathlib.Path(temp)/'before.json').exists())
    def test_cli_failure_still_gets_distinct_after(self):
        class R:
            def capture(self,label):seen.append(label);return {'label':label}
        with tempfile.TemporaryDirectory() as temp:
            seen=[];r=R();r.folder=pathlib.Path(temp)
            def fail():raise TimeoutError('secret')
            before,outcome,after=d.paired_dry_run(r,fail)
            self.assertEqual(seen,['before','after']);self.assertEqual(outcome['error_class'],'TimeoutError')
            self.assertNotIn('secret',(r.folder/'cli-dry-run.json').read_text())
    def test_no_data_scan_or_auth_reads(self):
        self.assertNotIn('run_hashes',d.OBJECTS)
        for text in (d.OBJECTS,d.MIGRATIONS,d.HEALTH,d.TX,d.STATS):
            self.assertNotIn('auth.users',text);self.assertNotIn('s.query',text)
    def test_dryrun_cli_pinned_safe_arguments(self):
        sys.path.insert(0,str(d.HERE.parent/'access_v1'));import migration_run
        seen={}
        def subprocess_run(args,**kw):
            seen.update(args=args,kw=kw)
            return type('P',(),dict(stdout=b'Remote database is up to date.',stderr=b'',returncode=0))()
        with patch.object(migration_run.cli_check,'connection_url',return_value='postgresql://synthetic?jit%3Dtrue&default_transaction_read_only%3Don'), \
                patch.object(migration_run.subprocess,'run',side_effect=subprocess_run):
            value=migration_run.cli_run('cli',{},None,'synthetic-private',True)
        self.assertTrue(value['up_to_date'])
        self.assertIn('--skip-vault',seen['args']);self.assertIn('--dry-run',seen['args'])
        self.assertNotIn('--include-seed',seen['args']);self.assertNotIn('--include-roles',seen['args'])
        self.assertNotIn('synthetic-private',' '.join(seen['args']))
        self.assertEqual(seen['kw']['timeout'],45)
        self.assertNotIn('PGPASSWORD',seen['kw']['env'])


if __name__=='__main__': unittest.main()
