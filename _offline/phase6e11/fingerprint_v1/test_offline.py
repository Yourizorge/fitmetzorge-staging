"""Synthetic integration and fault tests. Never connects to Supabase."""
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from guard import Ledger, Stop, encoded, save
from fingerprint import Reducer, collect, configure, plan, predicates, SCHEMA_SQL, stream_sql
from local_cluster import Cluster, EXPECTED, SELECTION, uid
from pq import LocalDB


class Bounds(unittest.TestCase):
    def setUp(self):
        self.path = pathlib.Path(tempfile.mkdtemp(prefix='fmz-fp-test-'))

    def test_649_full_repetitions_stop_at_fourth_admission(self):
        g = Ledger(self.path / 'guard')
        try:
            admitted = 0
            for i in range(649):
                try:
                    g.begin_cycle()
                    admitted += 1
                    g.active = False  # Simulated completed collector, not a hidden reset of counters.
                except Stop:
                    break
            self.assertEqual(admitted, 3)
            self.assertEqual(g.full, 3)
            self.assertTrue(g.halted)
        finally:
            g.close()
        with self.assertRaisesRegex(Stop, 'retained_halt'):
            Ledger(self.path / 'guard')

    def test_budget_survives_new_run_id(self):
        for _ in range(3):
            g = Ledger(self.path / 'guard')
            g.begin_cycle()
            g.active = False
            g.close()
        g = Ledger(self.path / 'guard')
        try:
            with self.assertRaisesRegex(Stop, 'full_cycle_budget'):
                g.begin_cycle()
        finally:
            g.close()

    def test_cross_process_lock(self):
        g = Ledger(self.path / 'guard')
        try:
            with self.assertRaisesRegex(Stop, 'concurrent_or_interrupted_run'):
                Ledger(self.path / 'guard')
            with self.assertRaisesRegex(Stop, 'concurrent_or_interrupted_run'):
                Ledger(self.path / 'different-budget')
            script = "from guard import Ledger; import sys; Ledger(sys.argv[1])"
            child = subprocess.run([sys.executable,'-c',script,str(self.path/'child-budget')],
                cwd=pathlib.Path(__file__).parent,capture_output=True,timeout=10)
            self.assertNotEqual(child.returncode,0)
            self.assertIn(b'concurrent_or_interrupted_run',child.stderr)
        finally:
            g.close()

    def test_query_budget(self):
        g = Ledger(self.path / 'guard')
        try:
            for _ in range(128):
                g.reserve_query()
            with self.assertRaisesRegex(Stop, 'query_budget'):
                g.reserve_query()
        finally:
            g.close()

    def test_targeted_mode_not_silently_enabled(self):
        g = Ledger(self.path / 'guard')
        try:
            with self.assertRaisesRegex(Stop, 'write_coverage_not_proven'):
                g.targeted()
        finally:
            g.close()

    def test_step_timeout(self):
        g = Ledger(self.path / 'guard')
        g.started -= 901
        try:
            with self.assertRaisesRegex(Stop, 'run_deadline'):
                g.reserve_query()
        finally:
            g.close()

    def identity(self):
        return {'status':'complete','algorithm':'synthetic','schema_sha256':'schema',
                'selection_sha256':'selection','canonical':{},
                'tables':[{'name':str(i),'cohorts':{'protected':{'rows':0,'sha256':'empty'},
                                                 'raw':{'rows':0,'sha256':'empty'}}} for i in range(143)]}

    def test_missing_after_blocks_action_and_cleanup(self):
        p=self.path/'identity.json';save(p,self.identity())
        g=Ledger(self.path/'guard')
        try:
            g.before(p);g.start_action();g.confirm_action({'status':200})
            with self.assertRaisesRegex(Stop,'cleanup_without_valid_pair'):
                g.cleanup_allowed()
        finally:
            g.close()
        events=[json.loads(x.read_text()) for x in (self.path/'guard').glob('event-*.json')]
        self.assertEqual(events[-1]['phase'],'action_confirmed')

    def test_valid_pair_and_protected_drift(self):
        a=self.path/'a.json';b=self.path/'b.json'
        save(a,self.identity());save(b,self.identity())
        g=Ledger(self.path/'guard')
        try:
            g.before(a);g.start_action();g.confirm_action({'status':200});g.after(b)
            self.assertTrue(g.cleanup_allowed())
            value=self.identity();value['tables'][0]['cohorts']['protected']['rows']=1
            c=self.path/'c.json';save(c,value)
            g.before(a);g.start_action();g.confirm_action({'status':200})
            with self.assertRaisesRegex(Stop,'protected_drift'):
                g.after(c,allowed_raw=['0'])
        finally:
            g.close()

    def test_interruption_keeps_halt(self):
        p=self.path/'identity.json';save(p,self.identity())
        g=Ledger(self.path/'guard');g.before(p);g.start_action();g.close()
        with self.assertRaisesRegex(Stop,'retained_halt'):
            Ledger(self.path/'guard')

    def test_killed_process_keeps_lock(self):
        script = "from guard import Ledger; import sys,os; g=Ledger(sys.argv[1],lock_scope=sys.argv[2]); g.begin_cycle(); os._exit(17)"
        child = subprocess.run([sys.executable,'-c',script,str(self.path/'killed'),str(self.path/'test-scope')],
            cwd=pathlib.Path(__file__).parent,capture_output=True,timeout=10)
        self.assertEqual(child.returncode,17)
        with self.assertRaisesRegex(Stop,'concurrent_or_interrupted_run'):
            Ledger(self.path/'killed',lock_scope=self.path/'test-scope')

    def test_unvalidated_pair_blocks_next_action(self):
        p=self.path/'identity.json';save(p,self.identity());g=Ledger(self.path/'guard')
        try:
            g.before(p);g.start_action();g.confirm_action({'status':200})
            with self.assertRaisesRegex(Stop,'previous_pair_not_validated'):g.before(p)
        finally:g.close()

    def test_changed_ledger_chain_blocks_restart(self):
        g=Ledger(self.path/'guard');g.reserve_query();g.close()
        p=self.path/'guard'/'event-000001.json'
        value=json.loads(p.read_text());value['kind']='tampered'
        p.write_bytes(encoded(value))
        with self.assertRaisesRegex(Stop,'ledger_chain'):Ledger(self.path/'guard')

    def test_local_transport_rejects_remote_port_contract(self):
        with self.assertRaisesRegex(Stop,'local_port_only'):
            LocalDB(5432)


class SortTests(unittest.TestCase):
    def setUp(self):
        self.path=pathlib.Path(tempfile.mkdtemp(prefix='fmz-fp-sort-'))
        self.plans=[{'name':'synthetic.t','cohorts':{'protected':'true'}}]

    def reduce(self, rows, folder='chunks'):
        r=Reducer(self.plans,self.path/folder,chunk_rows=2)
        for row in rows:r.add(row)
        return r,r.finish(len(rows))

    def test_order_and_duplicates(self):
        a=hashlib.sha256(b'a').hexdigest();b=hashlib.sha256(b'b').hexdigest()
        rows=[['0',a,'1'],['0',b,'0'],['0',a,'1']]
        _,x=self.reduce(rows);_,y=self.reduce(list(reversed(rows)),'second')
        self.assertEqual(x,y)
        self.assertEqual(x[0]['cohorts']['raw']['rows'],3)
        self.assertEqual(x[0]['cohorts']['protected']['rows'],2)
        self.assertEqual(x[0]['cohorts']['raw']['sha256'],hashlib.sha256(','.join(sorted([a,b,a])).encode()).hexdigest())

    def test_partial_stream(self):
        r=Reducer(self.plans,self.path/'chunks')
        r.add(['0','a'*64,'1'])
        with self.assertRaisesRegex(Stop,'incomplete_stream'):r.finish(2)

    def test_no_terminal(self):
        r=Reducer(self.plans,self.path/'chunks')
        with self.assertRaisesRegex(Stop,'incomplete_stream'):r.finish(None)

    def test_corrupt_chunk(self):
        r=Reducer(self.plans,self.path/'chunks',1);r.add(['0','a'*64,'1'])
        r.chunks[0][0].write_bytes(b'corrupt synthetic test')
        with self.assertRaisesRegex(Stop,'chunk_corrupt'):r.finish(1)

    def test_row_limit(self):
        r=Reducer(self.plans,self.path/'chunks');r.MAX_ROWS=0
        with self.assertRaisesRegex(Stop,'row_budget'):r.add(['0','a'*64,'1'])

    def test_byte_limit(self):
        r=Reducer(self.plans,self.path/'chunks',1);r.MAX_BYTES=1
        with self.assertRaisesRegex(Stop,'byte_budget'):r.add(['0','a'*64,'1'])

    def test_chunk_limit(self):
        r=Reducer(self.plans,self.path/'chunks',1);r.MAX_CHUNKS=0
        with self.assertRaisesRegex(Stop,'chunk_budget'):r.add(['0','a'*64,'1'])

    def test_invalid_digest(self):
        r=Reducer(self.plans,self.path/'chunks')
        with self.assertRaisesRegex(Stop,'hash_or_flag'):r.add(['0','personal raw data','1'])

    def test_sort_timeout(self):
        r=Reducer(self.plans,self.path/'chunks');r.started-=121
        with self.assertRaisesRegex(Stop,'cycle_timeout'):r.add(['0','a'*64,'1'])

    def test_empty_hash(self):
        _,out=self.reduce([])
        self.assertEqual(out[0]['cohorts']['raw']['sha256'],hashlib.sha256(b'').hexdigest())

    def test_retained_workspace_only_branch(self):
        expr=predicates('fmz6e11_private.plans',['workspace_id'],SELECTION)
        self.assertIn('select id from fmz6e11_private.workspaces',expr['retained'])

    def test_null_owner_and_fixed_account_not_control(self):
        expr=predicates('public.workout_sessions',['user_id'],SELECTION)['protected']
        self.assertIn('user_id is null',expr)
        self.assertIn(uid(4),expr)
        self.assertNotIn(uid(1),expr)


class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cluster=Cluster()
        try:
            cls.db=cls.cluster.start();cls.cluster.fixture(cls.db)
        except BaseException:
            cls.cluster.stop()
            raise
        cls.output=cls.cluster.path/'evidence';cls.output.mkdir()
        cls.number=0

    @classmethod
    def tearDownClass(cls):
        cls.db.close();cls.cluster.stop()

    def measure(self,method='stream',setting=None):
        type(self).number+=1
        p=self.output/str(self.number);p.mkdir()
        g=Ledger(p/'ledger')
        db=LocalDB(self.cluster.port,g)
        try:
            if setting:db.query(setting)
            return collect(db,g,p/'cycle',EXPECTED,SELECTION,method)[0]
        finally:
            db.close();g.close()

    def test_old_new_and_repeated_bytes(self):
        old=self.measure('legacy');new=self.measure();again=self.measure()
        self.assertEqual(encoded(old),encoded(new))
        self.assertEqual(encoded(new),encoded(again))

    def test_ambient_timezone_and_output_settings(self):
        a=self.measure()
        b=self.measure(setting="set timezone='America/New_York'")
        c=self.measure(setting="set datestyle='SQL, DMY'")
        d=self.measure(setting="set bytea_output='escape'")
        self.assertEqual(encoded(a),encoded(b));self.assertEqual(encoded(a),encoded(c));self.assertEqual(encoded(a),encoded(d))
        e=self.measure(setting="set lc_numeric='English_United States.1252'")
        f=self.measure(setting="set intervalstyle='iso_8601'")
        self.assertEqual(encoded(a),encoded(e));self.assertEqual(encoded(a),encoded(f))

    def test_unpinned_legacy_timezone_diff_is_recorded(self):
        q="select encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') from public.foods t where stamp not in ('infinity','-infinity') order by 1"
        self.db.query("set timezone='UTC'");a=self.db.query(q)
        self.db.query("set timezone='America/New_York'");b=self.db.query(q)
        self.db.query("set timezone='UTC'")
        self.assertNotEqual(a,b)

    def test_insert_update_delete_multiplicity(self):
        before=self.measure()
        self.db.query("insert into public.exercises(word) values ('synthetic')")
        inserted=self.measure();self.assertNotEqual(before['tables'],inserted['tables'])
        self.db.query("update public.exercises set word='changed synthetic'")
        updated=self.measure();self.assertNotEqual(inserted['tables'],updated['tables'])
        self.db.query("insert into public.exercises select * from public.exercises")
        duplicate=self.measure();self.assertNotEqual(updated['tables'],duplicate['tables'])
        self.db.query("delete from public.exercises")
        after=self.measure();self.assertEqual(before['tables'],after['tables'])

    def test_cohort_exclusions(self):
        value=self.measure();tables={x['name']:x['cohorts'] for x in value['tables']}
        self.assertEqual(tables['auth.users']['raw']['rows'],5)
        self.assertEqual(tables['auth.users']['protected']['rows'],1)
        self.assertEqual(tables['auth.mfa_amr_claims']['protected']['rows'],1)
        self.assertEqual(tables['auth.audit_log_entries']['protected']['rows'],1)
        self.assertEqual(tables['public.profiles']['protected']['rows'],1)
        self.assertEqual(tables['public.food_logs']['protected']['rows'],2)
        self.assertEqual(tables['cron.job_run_details']['protected']['rows'],0)
        self.assertEqual(tables['fmz6e11_private.windows']['protected']['rows'],0)
        self.assertEqual(tables['fmz6e11_private.windows']['retained']['rows'],1)

    def test_missing_table_no_identity(self):
        self.db.query('alter table public.exercises rename to missing_exercises')
        try:
            with self.assertRaisesRegex(Stop,'inventory_mismatch'):self.measure()
        finally:
            self.db.query('alter table public.missing_exercises rename to exercises')

    def test_schema_change_bound(self):
        a=self.measure();self.db.query('alter table public.exercises add column synthetic_extra text')
        try:
            b=self.measure();self.assertNotEqual(a['schema_sha256'],b['schema_sha256'])
        finally:
            self.db.query('alter table public.exercises drop column synthetic_extra')

    def test_query_error_and_partial_stream(self):
        db=LocalDB(self.cluster.port)
        try:
            seen=[]
            with self.assertRaisesRegex(Stop,'sqlstate_22012'):
                for row in db.rows('select (10/(3-g))::text from generate_series(1,4) g'):seen.append(row)
            self.assertIsNone(db.terminal_count)
        finally:db.close()

    def test_concurrent_write_does_not_split_snapshot(self):
        db=LocalDB(self.cluster.port)
        try:
            configure(db);plans=plan(db.query(SCHEMA_SQL),SELECTION,EXPECTED)
            reducer=Reducer(plans,self.output/'concurrent-chunks')
            rows=db.rows(stream_sql(plans));reducer.add(next(rows))
            self.db.query("insert into public.exercises(word) values ('concurrent synthetic')")
            for row in rows:reducer.add(row)
            tables=reducer.finish(db.terminal_count);db.query('commit')
            prior=next(x for x in tables if x['name']=='public.exercises')
            self.assertEqual(prior['cohorts']['raw']['rows'],0)
            current=self.measure()
            changed=next(x for x in current['tables'] if x['name']=='public.exercises')
            self.assertEqual(changed['cohorts']['raw']['rows'],1)
        finally:
            db.close();self.db.query('delete from public.exercises')

    def test_timeout_no_retry(self):
        db=LocalDB(self.cluster.port)
        try:
            with self.assertRaisesRegex(Stop,'query_timeout'):db.query('select pg_sleep(0.3)',timeout=0.02)
            self.assertEqual(db.queries,1)
        finally:db.close()

    def test_sql_shape_has_no_remote_sort_or_ctid(self):
        schema=self.db.query(SCHEMA_SQL)
        sql=stream_sql(plan(schema,SELECTION,EXPECTED))
        self.assertNotIn('order by',sql.lower());self.assertNotIn('ctid',sql.lower())
        self.assertEqual(sql.count(' union all '),142)


if __name__=='__main__':
    unittest.main()
