import copy,json,pathlib,tempfile,types,unittest
import ci_wal_diagnostic as d

ENV={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging',
     'GITHUB_REF':'refs/heads/main','FMZ6E11_LOCAL_WAL_DIAGNOSTIC':'1'}
IDS={r:'00000000-0000-0000-0000-%012d'%i for i,r in enumerate(sorted(d.ROLES),1)}
CONTEXT={'window':'00000000-0000-0000-0000-000000000004',
 'temporary_schemas':['fmz6e11_guard_'+'a'*32,'fmz6e11_am_'+'a'*32]}
class Connection:
    def __init__(self,installed=None,available=True):
        self.calls=[];self.autocommit=True;self.closed=False;self.fail=None
        self.start_readonly=True
        self.parameters={'options':'-c statement_timeout=5000 -c lock_timeout=1000',
            'sslmode':'verify-full','connect_timeout':'5'}
        self.info=types.SimpleNamespace(host='127.0.0.1',hostaddr='127.0.0.1',
            dbname='postgres',user='postgres',server_version=170006,transaction_status=0,
            get_parameters=lambda:dict(self.parameters))
        self.preflight={'statement_timeout':'5s','lock_timeout':'1s','version':170006,
            'readonly':'off','ssl':True,'server_addr':'172.18.0.2','available':available,
            'installed_schema':installed,'target_schema':True}
        self.observed={'end_lsn':'0/200','flush_lsn':'0/200','span_bytes':108,
            'technical':{'record_count':2,'groups':[{'rmgr':'Heap2','record_type':'PRUNE',
                'records':2,'blockcount':2}]}}
    def execute(self,sql,args=()):
        self.calls.append((sql,args))
        if self.fail and self.fail(sql):raise RuntimeError('secret-raw-sql-must-not-export')
        if sql==d.PREFLIGHT:value=self.preflight
        elif sql==d.START:value={'start_lsn':'0/100','readonly':self.start_readonly}
        elif sql.startswith('with boundary'):value=self.observed
        else:value={'private_fixture_contents':'never-export'}
        return types.SimpleNamespace(fetchone=lambda:copy.deepcopy(value))
    def close(self):self.closed=True

class Tests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        self.ca=pathlib.Path(folder.name)/'fmz-ci-ca.crt'
        self.ca.write_text('Mock CA path only; no TLS connection is made.',encoding='ascii')
    def connection(self,*args,**kwargs):
        c=Connection(*args,**kwargs);c.parameters['sslrootcert']=str(self.ca);return c
    def run_probe(self,c,**kwargs):
        return d.run(c,environment='disposable_ci',ids=IDS,context=CONTEXT,
            ci_ca_path=self.ca,environ=ENV,**kwargs)
    def test_new_extension_has_exact_16_commands_same_queries_and_no_pass(self):
        c=self.connection();r=self.run_probe(c)
        self.assertEqual(r['commands'],16);self.assertEqual(len(c.calls),16)
        self.assertEqual([x['name'] for x in r['queries']],['access','migrations','catalog','absence'])
        self.assertEqual(r['limitations'],[]);self.assertTrue(r['rollback_confirmed'])
        self.assertTrue(all(x['complete'] for x in r['queries']))
        self.assertFalse(r['full_chain_admission']);self.assertFalse(r['wal_zero_pass'])
        self.assertEqual(r['status'],'DIAGNOSTIC_ONLY')
        self.assertEqual(c.calls[1][0],'CREATE EXTENSION pg_walinspect WITH SCHEMA extensions')
        self.assertEqual(c.calls[2][0],'BEGIN TRANSACTION READ ONLY')
        self.assertEqual(c.calls[-1][0],'ROLLBACK')
        for i,source in enumerate((d.ACCESS,d.MIGRATIONS,d.CATALOG,d.ABSENCE)):
            args=([list(IDS.values())],[],[CONTEXT['temporary_schemas']],
                  [CONTEXT['temporary_schemas'],list(IDS.values()),CONTEXT['window']])[i]
            self.assertEqual(c.calls[4+3*i],d.bind_parameters(source,args))
        self.assertNotIn('private_fixture_contents',json.dumps(r))
        self.assertNotIn(str(self.ca),json.dumps(r))
    def test_installed_extension_has_15_commands_no_ddl(self):
        c=self.connection('extensions');r=self.run_probe(c)
        self.assertEqual(r['commands'],15)
        self.assertFalse(any(sql.startswith('CREATE') for sql,args in c.calls))
    def test_environment_and_remote_peer_rejected_before_sql(self):
        cases=[('staging',ENV,'127.0.0.1','127.0.0.1'),
               ('disposable_ci',{},'127.0.0.1','127.0.0.1'),
               ('disposable_ci',ENV,'hosted.example','127.0.0.1'),
               ('disposable_ci',ENV,'127.0.0.1','203.0.113.1')]
        for mode,env,host,addr in cases:
            with self.subTest(mode=mode,host=host,addr=addr):
                c=self.connection();c.info.host=host;c.info.hostaddr=addr
                with self.assertRaises(ValueError):
                    d.run(c,environment=mode,ids=IDS,context=CONTEXT,ci_ca_path=self.ca,environ=env)
                self.assertEqual(c.calls,[])
    def test_missing_existing_timeout_rejected_before_sql(self):
        c=self.connection();c.info.get_parameters=lambda:{'options':''}
        with self.assertRaises(ValueError):self.run_probe(c)
        self.assertEqual(c.calls,[])
    def test_extension_unavailable_is_limitation_without_install(self):
        c=self.connection(available=False);r=self.run_probe(c)
        self.assertEqual(r['commands'],1)
        self.assertEqual(r['limitations'],['pg_walinspect_unavailable'])
        self.assertFalse(r['wal_zero_pass'])
    def test_extension_install_failure_is_not_admission(self):
        c=self.connection();c.fail=lambda sql:sql.startswith('CREATE')
        r=self.run_probe(c)
        self.assertEqual(r['limitations'],['pg_walinspect_install_unavailable'])
        self.assertEqual(r['commands'],2)
        self.assertNotIn('secret',json.dumps(r))
    def test_failed_metadata_query_rolls_back_without_retry(self):
        c=self.connection('extensions');target=d.bind_parameters(d.ACCESS,[list(IDS.values())])[0]
        c.fail=lambda sql:sql==target
        r=self.run_probe(c)
        self.assertEqual(r['limitations'],['probe_unconfirmed'])
        self.assertTrue(r['rollback_confirmed'])
        self.assertEqual(sum(sql==target for sql,args in c.calls),1)
        self.assertNotIn('secret',json.dumps(r))
    def test_interval_and_record_caps_are_fail_closed(self):
        for kind in ('span','records'):
            c=self.connection('extensions')
            if kind=='span':c.observed['span_bytes']=65537
            else:c.observed['technical']['record_count']=513
            r=self.run_probe(c)
            self.assertTrue(r['limitations']);self.assertTrue(r['rollback_confirmed'])
            self.assertFalse(r['queries'][0]['complete']);self.assertLessEqual(r['commands'],16)
    def test_no_description_block_data_or_row_content_export(self):
        c=self.connection('extensions')
        c.observed['technical']['groups'][0]['description']='secret-row'
        r=self.run_probe(c)
        self.assertIn('probe_unconfirmed',r['limitations'])
        self.assertNotIn('secret-row',json.dumps(r))
        self.assertNotIn('description',d.INSPECT)
        self.assertNotIn('block_data',d.INSPECT)
        self.assertIn('boundary.end_lsn,false)',d.INSPECT)
    def test_zero_span_is_still_diagnostic_only(self):
        c=self.connection('extensions');c.observed.update(span_bytes=0,end_lsn='0/100',technical=None)
        r=self.run_probe(c)
        self.assertFalse(r['wal_zero_pass']);self.assertFalse(r['causal_attribution'])
        self.assertTrue(all(x['technical']['record_count']==0 for x in r['queries']))
    def test_diagnostic_entry_saves_closes_then_stops(self):
        c=self.connection('extensions');saved={}
        with self.assertRaises(d.DiagnosticOnlyStop):
            d.run_and_stop(c,lambda n,v:saved.update({n:v}),environment='disposable_ci',
                ids=IDS,context=CONTEXT,ci_ca_path=self.ca,environ=ENV)
        self.assertTrue(c.closed);self.assertEqual(list(saved),['ci-wal-diagnostic.json'])
        self.assertFalse(saved['ci-wal-diagnostic.json']['full_chain_admission'])

    def test_driver_tls_connect_timeout_and_wrong_ca_rejected_before_sql(self):
        other=self.ca.with_name('other.crt');other.write_text('Mock only.',encoding='ascii')
        for key,value in [('sslmode','require'),('sslmode',None),('connect_timeout','6'),
                          ('connect_timeout',None),('sslrootcert',None),
                          ('sslrootcert',str(other)),('sslrootcert',str(self.ca/'missing'))]:
            with self.subTest(key=key,value=value):
                c=self.connection();c.parameters[key]=value
                with self.assertRaises(ValueError) as caught:self.run_probe(c)
                self.assertEqual(c.calls,[])
                self.assertNotIn(str(self.ca),str(caught.exception))

    def test_expected_bound_ci_ca_must_exist(self):
        c=self.connection();self.ca.unlink()
        with self.assertRaisesRegex(ValueError,'wal_diagnostic_ci_ca_binding'):self.run_probe(c)
        self.assertEqual(c.calls,[])

    def test_preflight_ssl_attested_before_any_extension_install(self):
        for value in (False,None,1):
            with self.subTest(value=value):
                c=self.connection();c.preflight['ssl']=value;r=self.run_probe(c)
                self.assertEqual(r['commands'],1);self.assertEqual(c.calls[0][0],d.PREFLIGHT)
                self.assertEqual(r['queries'],[]);self.assertIn('probe_unconfirmed',r['limitations'])
                self.assertFalse(r['extension_installed'])
        self.assertIn('select ssl from pg_stat_ssl where pid=pg_backend_pid()',d.PREFLIGHT)

    def test_start_readonly_attested_before_metadata(self):
        for value in (False,None,1):
            with self.subTest(value=value):
                c=self.connection('extensions');c.start_readonly=value;r=self.run_probe(c)
                self.assertEqual([sql for sql,args in c.calls],
                    [d.PREFLIGHT,'BEGIN TRANSACTION READ ONLY',d.START,'ROLLBACK'])
                self.assertEqual(r['queries'],[]);self.assertTrue(r['rollback_confirmed'])
                self.assertIn('probe_unconfirmed',r['limitations'])
        self.assertIn("current_setting('transaction_read_only')='on' readonly",d.START)

    def test_group_record_sum_must_match_total(self):
        for records in (1,3):
            with self.subTest(records=records):
                c=self.connection('extensions')
                c.observed['technical']['groups'][0]['records']=records
                r=self.run_probe(c)
                self.assertIn('probe_unconfirmed',r['limitations'])
                self.assertTrue(r['rollback_confirmed']);self.assertFalse(r['queries'][0]['complete'])
                self.assertNotIn('technical',r['queries'][0])

    def test_unflushed_boundary_stays_incomplete_without_retry_or_force_flush(self):
        for partial_result in (None,{'record_count':0,'groups':[]}):
            with self.subTest(partial_result=partial_result):
                c=self.connection('extensions')
                c.observed.update(flush_lsn='0/1FF',technical=partial_result)
                r=self.run_probe(c)
                self.assertEqual(r['limitations'],['wal_not_flushed_through_end'])
                self.assertEqual(r['commands'],6);self.assertEqual(len(r['queries']),1)
                self.assertTrue(r['rollback_confirmed']);self.assertFalse(r['queries'][0]['complete'])
                self.assertEqual(r['queries'][0]['flush_lsn'],'0/1FF')
                self.assertEqual(r['queries'][0]['end_lsn'],'0/200')
                self.assertNotIn('technical',r['queries'][0])
                self.assertEqual(sum(sql==d.START for sql,args in c.calls),1)
                self.assertEqual(sum(sql.startswith('with boundary') for sql,args in c.calls),1)
                self.assertFalse(r['wal_zero_pass']);self.assertFalse(r['full_chain_admission'])
        self.assertIn('pg_current_wal_flush_lsn() flush_lsn',d.INSPECT)
        self.assertIn('case when flush_lsn>=end_lsn and',d.INSPECT)
        self.assertLess(d.INSPECT.index('flush_lsn>=end_lsn'),d.INSPECT.index('pg_get_wal_records_info'))

if __name__=='__main__':unittest.main()
