import copy,itertools,json,pathlib,tempfile,types,unittest
from unittest.mock import patch
import ci_wal_diagnostic as d

ENV={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'Yourizorge/fitmetzorge-staging',
     'GITHUB_REF':'refs/heads/main','FMZ6E11_LOCAL_WAL_DIAGNOSTIC':'1'}
IDS={r:'00000000-0000-0000-0000-%012d'%i for i,r in enumerate(sorted(d.ROLES),1)}
CONTEXT={'window':'00000000-0000-0000-0000-000000000004',
 'temporary_schemas':['fmz6e11_guard_'+'a'*32,'fmz6e11_am_'+'a'*32]}
COUNTERS={'calls':0,'wal_bytes':0,'wal_records':0,'wal_fpi':0,'temp_read':0,'temp_written':0}

# Frozen sanitized metadata only. Inspection rows below remain MOCK control-flow
# responses, not classifications obtained from either historical CI run.
RECEIPT_METADATA={
 '41466921367':{
  'sha256':'4e9e275a45f3bb4bd825e8ae824d3a5d887ec3df37b8bc32bc5bb99b27c4b53f',
  'commands':70,'outcome':'INCOMPLETE',
  'rows':(
   ('access','0/281A248','0/281A308','0/281A1F8','0/281A248',192,3),
   ('migrations','0/281A308','0/281A308','0/281A248','0/281A248',0,0),
   ('catalog','0/281A370','0/281A770','0/281A370','0/281A370',972,15),
   ('absence','0/281A770','0/281A770','0/281A370','0/281A370',0,0),
   ('snapshot','0/281A770','0/281A770','0/281A370','0/281A370',0,0),
   ('rowhash','0/281A770','0/281A770','0/281A370','0/281A7A8',0,0))},
 '41467755577':{
  'sha256':'1feb6a95ddd3d955468c5ae109cbae05500fd7037c6874c3e3832c11a699eada',
  'commands':70,'outcome':'INCOMPLETE',
  'rows':(
   ('access','0/281B3F8','0/281B4F0','0/281B3A8','0/281B3F8',246,4),
   ('migrations','0/281B4F0','0/281B4F0','0/281B3F8','0/281B3F8',0,0),
   ('catalog','0/281B558','0/281BA00','0/281B558','0/281B558',1110,19),
   ('absence','0/281BA00','0/281BA00','0/281B558','0/281B558',0,0),
   ('snapshot','0/281BA00','0/281BA00','0/281B558','0/281B558',0,0),
   ('rowhash','0/281BA00','0/281BA00','0/281B558','0/281B558',0,0))}
}

class Cursor:
    def __init__(self,value=None,rows=None):self.value=value;self.rows=rows or []
    def fetchone(self):return copy.deepcopy(self.value)
    def fetchall(self):return copy.deepcopy(self.rows)

class Connection:
    def __init__(self,installed='extensions',zero=False):
        self.calls=[];self.autocommit=True;self.closed=False;self.fail=None
        self.parameters={'options':'-c statement_timeout=5000 -c lock_timeout=1000',
            'sslmode':'verify-full','connect_timeout':'5'}
        self.info=types.SimpleNamespace(host='127.0.0.1',hostaddr='127.0.0.1',
            dbname='postgres',user='postgres',server_version=170006,transaction_status=0,
            get_parameters=lambda:dict(self.parameters))
        self.preflight={'statement_timeout':'5s','lock_timeout':'1s','version':170006,
            'readonly':'off','ssl':True,'fsync':True,'available':True,
            'installed_schema':installed,'target_schema':True}
        self.bound={name:d.bind_parameters(source,args) for name,source,args in d.families(IDS,CONTEXT)}
        self.qids={name:str(100+i) for i,name in enumerate(d.QUERY_NAMES)}
        self.reader_sql=d.bind_parameters(d.STATS,['0'])[0]
        self.measured={name:0 for name in d.QUERY_NAMES}
        self.starts=dict.fromkeys(d.QUERY_NAMES,'0/100')
        self.ends={name:'0/100' if zero else '0/200' for name in d.QUERY_NAMES}
        self.flush={name:[] for name in d.QUERY_NAMES}
        self.wal={name:{} for name in d.QUERY_NAMES};self.stats_mutate=None
        self.technical_mutate=None;self.inspect_mutate=None;self.row_count=45
        self.start_readonly=True;self.end_readonly=True
        self.current=None;self.keep_open=False;self.collision=False
    def execute(self,sql,args=()):
        self.calls.append((sql,args,self.info.transaction_status,self.current))
        if self.fail and self.fail(sql):raise RuntimeError('SECRET SQL URL PASSWORD MUST NOT EXPORT')
        if sql==d.PREFLIGHT:return Cursor(self.preflight)
        if sql.startswith('EXPLAIN '):
            inner=sql.split(') ',1)[1]
            if inner==self.reader_sql:return Cursor({'QUERY PLAN':[{'Query Identifier':1}]})
            name=next(n for n,(q,p) in self.bound.items() if q==inner)
            self.current=name
            return Cursor({'QUERY PLAN':[{'Query Identifier':1 if self.collision else int(self.qids[name])}]})
        if sql==self.reader_sql:
            name=next(n for n,qid in self.qids.items() if qid==args[0])
            calls=self.measured[name]
            counters={**COUNTERS,**self.wal[name],'calls':calls}
            row=dict(queryid=self.qids[name],since='entry-1',**counters)
            value={'track':'top','reset':'reset-1','dealloc':0,
                'rows':[row] if calls else [],'database':{'temp_bytes':0,'reset':'db-1'},'other_active':0}
            if self.stats_mutate:self.stats_mutate(value,name,bool(calls))
            return Cursor({'value':value})
        if sql=='BEGIN TRANSACTION READ ONLY':
            self.info.transaction_status=2;return Cursor()
        if sql=='ROLLBACK':
            if not self.keep_open:self.info.transaction_status=0
            return Cursor()
        if sql==d.START:return Cursor({'start_lsn':self.starts[self.current],'readonly':self.start_readonly})
        if sql==d.END:return Cursor({'end_lsn':self.ends[self.current],'readonly':self.end_readonly})
        if sql==d.COVERAGE:
            queue=self.flush[self.current]
            return Cursor({'flush_lsn':queue.pop(0) if queue else self.ends[self.current]})
        if sql.startswith('with bounds as materialized'):
            value={'record_count':2,'block_count':2,'outside_records':0,'outside_blocks':0,
                'first_lsn':args[0],'last_lsn':args[1],
                'groups':[{'rmgr':'Heap2','record_type':'PRUNE','records':2}],
                'object_classes':[{'object_class':'current_pg_catalog','blocks':2}]}
            if self.technical_mutate:self.technical_mutate(value,self.current)
            if self.inspect_mutate:self.inspect_mutate(value,args)
            return Cursor({'technical':value})
        for name,(query,params) in self.bound.items():
            if sql==query:
                self.measured[name]+=1
                return Cursor({'PRIVATE_FIXTURE_CONTENTS':'never export'},
                    [{'i':'0','h':'PRIVATE_HASH_VALUE','keep':'1'}]*self.row_count if name=='rowhash' else [])
        if sql==d.CONFIG or sql==d.WAIT or sql.startswith('CREATE EXTENSION '):return Cursor()
        raise AssertionError('unexpected mock command')
    def close(self):self.closed=True

class Tests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        self.ca=pathlib.Path(folder.name)/'fmz-ci-ca.crt'
        self.ca.write_text('Mock CA only; no database connection.',encoding='ascii')
    def connection(self,**kwargs):
        c=Connection(**kwargs);c.parameters['sslrootcert']=str(self.ca);return c
    def run_probe(self,c):
        return d.run(c,environment='disposable_ci',ids=IDS,context=CONTEXT,
            ci_ca_path=self.ca,environ=ENV)

    def test_durable_coverage_requires_fsync_enabled(self):
        for value in (False,None,'on',1):
            c=self.connection();c.preflight['fsync']=value;r=self.run_probe(c)
            self.assertEqual(r['outcome'],'INCOMPLETE')
            self.assertNotIn('fsync_attested',r)
            self.assertEqual(r['commands'],1)
            self.assertEqual(sum(c.measured.values()),0)
        r=self.run_probe(self.connection(zero=True))
        self.assertTrue(r['fsync_attested'])

    def test_six_first_executions_fixed_source_no_warmup(self):
        c=self.connection();r=self.run_probe(c)
        self.assertEqual(d.QUERY_NAMES,('access','migrations','catalog','absence','snapshot','rowhash'))
        self.assertEqual([q['name'] for q in r['queries']],list(d.QUERY_NAMES))
        self.assertEqual(c.measured,dict.fromkeys(d.QUERY_NAMES,1))
        self.assertEqual(r['warmup_executions'],0)
        self.assertTrue(r['rollback_confirmed']);self.assertTrue(r['intervals_complete'])
        self.assertFalse(r['diagnostic_complete']);self.assertEqual(r['outcome'],'INCOMPLETE')
        self.assertFalse(r['full_chain_admission']);self.assertFalse(r['wal_zero_pass'])
        self.assertFalse(r['causal_attribution']);self.assertEqual(r['historical_cause'],'UNKNOWN')
        self.assertEqual(r['hosted_read_wal_limit_unchanged'],0)
        for name,source,args in d.families(IDS,CONTEXT):
            matches=[x for x in c.calls if x[0]==d.bind_parameters(source,args)[0]]
            self.assertEqual(len(matches),1);self.assertEqual(matches[0][1],d.bind_parameters(source,args)[1])
        all_sql=' '.join(x[0].upper() for x in c.calls)
        for forbidden in ('ANALYZE','CHECKPOINT','PG_SWITCH_WAL','PG_STAT_RESET','PG_STAT_FORCE_NEXT_FLUSH'):
            self.assertNotIn(forbidden,all_sql)

    def metadata_connection(self,run):
        c=self.connection(installed=None)
        for name,start,end,first,last,wal,records in RECEIPT_METADATA[run]['rows']:
            c.starts[name]=start;c.ends[name]=end;c.flush[name]=[first,last]
            c.wal[name]={'wal_bytes':wal,'wal_records':records}
        def mock_inspect(value,args):
            value.update(record_count=1,block_count=0,object_classes=[],
                groups=[{'rmgr':'MOCK','record_type':'MOCK_RECORD','records':1}])
        c.inspect_mutate=mock_inspect
        return c

    def assert_metadata_preserved(self,c,r,run):
        self.assertEqual(c.measured,dict.fromkeys(d.QUERY_NAMES,1))
        self.assertEqual(r['last_coverage']['command_number'],70)
        self.assertEqual(r['last_coverage']['family'],'rowhash')
        self.assertEqual(r['last_coverage']['phase'],'coverage_after_wait')
        row=r['command_ledger'][69]
        self.assertEqual(row['phase'],'coverage_after_wait');self.assertTrue(row['confirmed'])
        self.assertEqual(sum(x[0]==d.COVERAGE for x in c.calls),12)
        self.assertEqual(sum(x[0]==d.WAIT for x in c.calls),6)
        self.assertEqual(sum(x[0]==d.START for x in c.calls),6)
        self.assertEqual(sum(x[0]==d.END for x in c.calls),6)
        self.assertEqual(sum(x[0]=='ROLLBACK' for x in c.calls),6)
        self.assertEqual(r['wait_ms'],1800);self.assertTrue(r['rollback_confirmed'])
        self.assertFalse(r['full_chain_admission']);self.assertFalse(r['wal_zero_pass'])
        self.assertFalse(r['causal_attribution']);self.assertEqual(r['outcome'],'INCOMPLETE')
        self.assertEqual(RECEIPT_METADATA[run]['outcome'],'INCOMPLETE')
        for q,meta in zip(r['queries'],RECEIPT_METADATA[run]['rows']):
            name,start,end,first,last,wal,records=meta
            self.assertEqual((q['name'],q['start_lsn'],q['end_lsn']),(name,start,end))
            self.assertEqual([x['flush_lsn'] for x in q['coverage_checks']],[first,last])
            self.assertEqual(q['flush_lsn'],last)
            self.assertEqual(q['query_stats']['delta']['wal_bytes'],wal)
            self.assertEqual(q['query_stats']['delta']['wal_records'],records)
            self.assertEqual(q['query_stats']['delta']['calls'],1)
            for sample in q['coverage_checks']:
                command=r['command_ledger'][sample['command_number']-1]
                self.assertEqual(command['family'],name)
                self.assertEqual(command['phase'],sample['phase'])
            if 'deferred_coverage' in q:
                self.assertEqual(q['deferred_coverage'],{**r['last_coverage'],'covers_end':True})
                self.assertIn('wal_not_flushed_through_fixed_end',q['limitations'])
                self.assertIn('wal_not_flushed_through_fixed_end',q['resolved_limitations'])

    def test_sample1_metadata_counterfactual_adds_only_two_mock_classifications(self):
        c=self.metadata_connection('41466921367');r=self.run_probe(c)
        self.assert_metadata_preserved(c,r,'41466921367')
        self.assertEqual(r['commands'],72);self.assertTrue(r['intervals_complete'])
        self.assertFalse(r['diagnostic_complete'])
        deferred=[x for x in r['command_ledger'] if x['phase']=='classify_deferred_fixed_interval']
        self.assertEqual([(x['number'],x['family']) for x in deferred],[(71,'access'),(72,'catalog')])
        inspections=[x for x in c.calls if x[0].startswith('with bounds as materialized')]
        self.assertEqual([x[1] for x in inspections],
            [['0/281A248','0/281A308'],['0/281A370','0/281A770']])
        self.assertTrue(all(x[2]==0 for x in inspections))
        self.assertTrue(all(q['coverage_complete'] for q in r['queries']))

    def test_sample2_metadata_counterfactual_only_access_not_catalog_is_classifiable(self):
        c=self.metadata_connection('41467755577');r=self.run_probe(c)
        self.assert_metadata_preserved(c,r,'41467755577')
        self.assertEqual(r['commands'],71);self.assertFalse(r['intervals_complete'])
        self.assertEqual([q['name'] for q in r['queries'] if q['coverage_complete']],
                         ['access','migrations'])
        self.assertEqual([q['name'] for q in r['queries'] if q['classification_attempted']],['access'])
        for q in r['queries'][2:]:
            self.assertFalse(q['complete']);self.assertNotIn('technical',q)
            self.assertNotIn('deferred_coverage',q)
            self.assertEqual(q['resolved_limitations'],[])
        inspections=[x for x in c.calls if x[0].startswith('with bounds as materialized')]
        self.assertEqual([x[1] for x in inspections],[['0/281B3F8','0/281B4F0']])

    def test_all_729_wait_coverage_branch_combinations_stay_at_most_76(self):
        largest=0
        for states in itertools.product(range(3),repeat=6):
            # 0: covered immediately; 1: covered after the one wait;
            # 2: still uncovered. Increasing intervals keep samples monotonic.
            c=self.connection(installed=None)
            for i,(name,state) in enumerate(zip(d.QUERY_NAMES,states)):
                start='0/%X'%(0x100+i*0x100);end='0/%X'%(0x180+i*0x100)
                c.starts[name]=start;c.ends[name]=end
                c.flush[name]=[end] if state==0 else [start,end if state==1 else start]
            r=self.run_probe(c);waits=sum(x!=0 for x in states)
            classified=6-(states[-1]==2)
            expected=58+2*waits+classified
            self.assertEqual(r['commands'],expected,states);largest=max(largest,expected)
            self.assertEqual(sum(x[0]==d.COVERAGE for x in c.calls),6+waits,states)
            self.assertEqual(sum(x[0]==d.WAIT for x in c.calls),waits,states)
            self.assertEqual(c.measured,dict.fromkeys(d.QUERY_NAMES,1),states)
            self.assertEqual(sum(q['classification_attempted'] for q in r['queries']),classified,states)
            self.assertEqual(sum(x[0].startswith('with bounds as materialized') for x in c.calls),classified,states)
            self.assertLessEqual(expected,d.MAX_COMMANDS)
        self.assertEqual(largest,76)

    def test_all_zero_nonzero_masks_and_extension_branches_have_exact_cost(self):
        for installed in (None,'extensions'):
            for mask in range(64):
                c=self.connection(installed=installed)
                for i,name in enumerate(d.QUERY_NAMES):
                    start=0x100+i*0x100;end=start+(0x80 if mask&(1<<i) else 0)
                    c.starts[name]='0/%X'%start;c.ends[name]='0/%X'%end
                    c.flush[name]=['0/%X'%(start-8),'0/%X'%(end if i==5 else start-8)]
                r=self.run_probe(c)
                self.assertEqual(r['commands'],69+(installed is None)+mask.bit_count(),(installed,mask))
                self.assertEqual(sum(x[0]==d.COVERAGE for x in c.calls),12)
                self.assertEqual(sum(x[0]==d.WAIT for x in c.calls),6)
                self.assertTrue(all(q['coverage_complete'] for q in r['queries']))
                self.assertFalse(r['wal_zero_pass']);self.assertFalse(r['full_chain_admission'])

    def test_failed_or_unconfirmed_inspection_is_never_retried_in_deferred_round(self):
        c=self.connection()
        c.technical_mutate=lambda v,n:v.update(last_lsn='0/1FF') if n=='access' else None
        r=self.run_probe(c)
        self.assertEqual(sum(x[0].startswith('with bounds as materialized') for x in c.calls),6)
        self.assertTrue(r['queries'][0]['classification_attempted'])
        self.assertNotIn('deferred_coverage',r['queries'][0])
        self.assertFalse(r['queries'][0]['complete'])
        c=self.metadata_connection('41466921367')
        c.inspect_mutate=lambda value,args:value.update(last_lsn=args[0])
        r=self.run_probe(c)
        self.assertEqual(r['commands'],72)
        self.assertFalse(r['queries'][0]['complete']);self.assertFalse(r['queries'][2]['complete'])
        self.assertNotIn('technical',r['queries'][0]);self.assertNotIn('technical',r['queries'][2])
        self.assertEqual(r['outcome'],'INCOMPLETE')

    def test_fatal_last_family_or_deferred_transport_error_stops_without_more_sql(self):
        c=self.metadata_connection('41466921367')
        c.fail=lambda sql:sql==c.bound['rowhash'][0]
        r=self.run_probe(c)
        self.assertFalse(any(x['phase']=='classify_deferred_fixed_interval' for x in r['command_ledger']))
        self.assertTrue(r['rollback_confirmed']);self.assertEqual(r['outcome'],'INCOMPLETE')
        c=self.metadata_connection('41466921367')
        c.fail=lambda sql:sql.startswith('with bounds as materialized')
        r=self.run_probe(c)
        self.assertEqual(r['commands'],71)
        self.assertEqual(sum(x[0].startswith('with bounds as materialized') for x in c.calls),1)
        self.assertEqual(r['command_ledger'][-1]['family'],'access')
        self.assertFalse(r['command_ledger'][-1]['confirmed'])
        self.assertFalse(r['queries'][2]['classification_attempted'])
        self.assertEqual(r['outcome'],'INCOMPLETE')

    def test_deferred_stage_preserves_stats_temp_and_interval_failures(self):
        for kind in ('stats','temp','capacity'):
            c=self.metadata_connection('41466921367')
            if kind=='stats':
                c.stats_mutate=lambda v,n,after:v.update(reset='changed') if n=='access' and after else None
            elif kind=='temp':c.wal['access']['temp_written']=1
            else:c.ends['access']='0/282A249'
            r=self.run_probe(c)
            self.assertFalse(r['queries'][0]['complete'],kind)
            self.assertEqual(r['outcome'],'INCOMPLETE',kind)
            self.assertEqual(c.measured,dict.fromkeys(d.QUERY_NAMES,1))
            if kind=='capacity':self.assertFalse(r['queries'][0]['classification_attempted'])
            else:self.assertTrue(r['queries'][0]['classification_attempted'])

    def test_deferred_stage_obeys_command_cap_without_retry_or_extra_wait(self):
        c=self.metadata_connection('41466921367')
        with patch.object(d,'MAX_COMMANDS',70):r=self.run_probe(c)
        self.assertEqual(r['commands'],70)
        self.assertFalse(any(q['classification_attempted'] for q in r['queries']))
        self.assertFalse(any('classification_command_number' in q for q in r['queries']))
        self.assertFalse(any(x[0].startswith('with bounds as materialized') for x in c.calls))
        self.assertEqual(sum(x[0]==d.WAIT for x in c.calls),6)
        self.assertEqual(sum(x[0]==d.COVERAGE for x in c.calls),12)
        self.assertEqual(r['outcome'],'INCOMPLETE')

    def test_normal_and_worst_exact_command_ledger(self):
        for installed,wait,expected in ((None,False,64),('extensions',False,63),(None,True,76)):
            with self.subTest(installed=installed,wait=wait):
                c=self.connection(installed=installed)
                if wait:c.flush={name:['0/1FF','0/200'] for name in d.QUERY_NAMES}
                r=self.run_probe(c)
                self.assertEqual(r['commands'],expected);self.assertEqual(len(c.calls),expected)
                self.assertEqual(len(r['command_ledger']),expected)
                self.assertEqual([x['number'] for x in r['command_ledger']],list(range(1,expected+1)))
                self.assertTrue(all(x['commands']==1 and x['confirmed'] for x in r['command_ledger']))
                self.assertEqual(r['command_cap'],80);self.assertLessEqual(expected,d.MAX_COMMANDS)
                self.assertEqual(r['wait_ms'],1800 if wait else 0)
                self.assertEqual(r['automatic_retries'],0)

    def test_fixed_end_rollback_immediate_before_stats_coverage_and_inspection(self):
        c=self.connection();r=self.run_probe(c)
        for i,(sql,args,tx,name) in enumerate(c.calls):
            if sql==d.END:self.assertEqual(c.calls[i+1][0],'ROLLBACK')
            if sql in (d.COVERAGE,d.WAIT) or sql.startswith('with bounds as materialized'):
                self.assertEqual(tx,0)
            if sql.startswith('with bounds as materialized'):
                self.assertEqual(args,['0/100','0/200'])
        self.assertEqual(sum(x[0]==d.START for x in c.calls),6)
        self.assertEqual(sum(x[0]==d.END for x in c.calls),6)
        self.assertNotIn('pg_current_wal_insert_lsn',d.INSPECT)
        self.assertNotIn('pg_sleep',d.INSPECT)
        self.assertTrue(all(q['coverage_complete'] for q in r['queries']))

    def test_first_incomplete_flush_does_not_hide_other_five_families(self):
        c=self.connection();c.flush['access']=['0/1FF','0/1FF'];r=self.run_probe(c)
        self.assertEqual(c.measured,dict.fromkeys(d.QUERY_NAMES,1))
        self.assertEqual(len(r['queries']),6);first=r['queries'][0]
        self.assertEqual(first['end_lsn'],'0/200');self.assertEqual(first['flush_lsn'],'0/1FF')
        self.assertEqual(first['wait_ms'],300);self.assertEqual(len(first['coverage_checks']),2)
        self.assertTrue(first['complete']);self.assertTrue(first['coverage_complete'])
        self.assertEqual(first['classification_mode'],'deferred')
        self.assertIn('wal_not_flushed_through_fixed_end',first['limitations'])
        self.assertIn('wal_not_flushed_through_fixed_end',first['resolved_limitations'])
        self.assertFalse(any(x['covers_end'] for x in first['coverage_checks']))
        self.assertEqual(first['query_stats']['delta']['calls'],1)
        self.assertTrue(all(q['complete'] for q in r['queries'][1:]))
        self.assertEqual(sum(x[0]==d.WAIT for x in c.calls),1)
        self.assertEqual(sum(x[0].startswith('with bounds as materialized') for x in c.calls),6)
        self.assertEqual(r['outcome'],'INCOMPLETE');self.assertFalse(r['diagnostic_complete'])
        self.assertTrue(r['rollback_confirmed'])

    def test_all_incomplete_flushes_count_six_bounded_waits_without_inspection(self):
        c=self.connection();c.flush={name:['0/1FF','0/1FF'] for name in d.QUERY_NAMES}
        r=self.run_probe(c)
        self.assertEqual(r['commands'],69);self.assertEqual(r['wait_ms'],1800)
        self.assertEqual(c.measured,dict.fromkeys(d.QUERY_NAMES,1))
        self.assertFalse(any(x[0].startswith('with bounds as materialized') for x in c.calls))
        self.assertTrue(all(not q['complete'] for q in r['queries']))

    def test_zero_still_requires_coverage_and_is_never_admission(self):
        c=self.connection(zero=True);r=self.run_probe(c)
        self.assertEqual(r['commands'],57);self.assertEqual(r['outcome'],'WAL_ZERO')
        self.assertTrue(r['diagnostic_complete']);self.assertEqual(r['limitations'],[])
        self.assertFalse(r['wal_zero_pass']);self.assertFalse(r['full_chain_admission'])
        self.assertTrue(all(q['technical']['record_count']==0 for q in r['queries']))
        c=self.connection(zero=True);c.flush['access']=['0/FF','0/FF'];r=self.run_probe(c)
        self.assertEqual(r['outcome'],'WAL_ZERO');self.assertTrue(r['queries'][0]['deferred_coverage']['covers_end'])
        self.assertEqual(r['queries'][0]['technical']['record_count'],0)
        self.assertFalse(any(x['covers_end'] for x in r['queries'][0]['coverage_checks']))
        self.assertFalse(r['wal_zero_pass']);self.assertFalse(r['full_chain_admission'])
        self.assertEqual(c.measured,dict.fromkeys(d.QUERY_NAMES,1))

    def test_query_fingerprint_wal_deltas_not_cluster_or_historical_attribution(self):
        c=self.connection();c.wal['access']={'wal_bytes':'108','wal_records':2,'wal_fpi':0}
        c.wal['catalog']={'wal_bytes':'836','wal_records':15,'wal_fpi':0}
        r=self.run_probe(c);access=r['queries'][0];catalog=r['queries'][2]
        self.assertEqual(access['query_stats']['delta']['wal_bytes'],108)
        self.assertEqual(catalog['query_stats']['delta']['wal_records'],15)
        self.assertEqual(access['span_bytes'],256)
        self.assertEqual(access['technical']['record_count'],2)
        self.assertEqual(access['query_stats']['before_counters']['calls'],0)
        self.assertEqual(access['query_stats']['after_counters']['calls'],1)
        self.assertTrue(access['query_stats']['baseline_absent'])
        self.assertIn('not_backend',access['query_stats']['scope'])
        self.assertFalse(access['technical']['record_owner_attribution'])
        self.assertEqual(access['technical']['object_mapping_scope'],
                         'inspection_time_catalog_not_interval_object_proof')
        self.assertFalse(r['causal_attribution']);self.assertEqual(r['historical_cause'],'UNKNOWN')

    def test_ambiguous_stats_or_reset_fail_closed_but_do_not_repeat_queries(self):
        def mutate(case):
            def apply(v,n,after):
                if n!='access' or not after:return
                if case=='reset':v['reset']='reset-2'
                elif case=='dealloc':v['dealloc']=1
                elif case=='database':v['database']['reset']='db-2'
                elif case=='calls':v['rows'][0]['calls']=2
                elif case=='missing':v['rows']=[]
                elif case=='duplicate':v['rows']*=2
                elif case=='track':v['track']='none'
                elif case=='wrongid':v['rows'][0]['queryid']='999'
            return apply
        for case in ('reset','dealloc','database','calls','missing','duplicate','track','wrongid'):
            with self.subTest(case=case):
                c=self.connection();c.stats_mutate=mutate(case);r=self.run_probe(c)
                self.assertFalse(r['queries'][0]['query_stats']['reliable'])
                self.assertIn('query_statistics_unconfirmed',r['queries'][0]['limitations'])
                self.assertEqual(c.measured,dict.fromkeys(d.QUERY_NAMES,1))
                self.assertFalse(r['diagnostic_complete'])

    def test_since_replacement_and_negative_counter_rejected(self):
        b={'track':'top','reset':'r','dealloc':0,'database':{'reset':'d','temp_bytes':0},
           'other_active':0,'rows':[dict(COUNTERS,queryid='1',since='s',calls=5)]}
        for change in ({'since':'new','calls':6},{'calls':4}):
            a=copy.deepcopy(b);a['rows'][0].update(change)
            with self.assertRaises(ValueError):d.stats_delta(b,a,'1')

    def test_query_stats_wal_with_zero_cluster_and_temp_io_are_not_zero(self):
        for counters in ({'wal_bytes':1},{'temp_read':1},{'temp_written':1}):
            c=self.connection(zero=True);c.wal['access']=counters;r=self.run_probe(c)
            self.assertFalse(r['queries'][0]['complete']);self.assertEqual(r['outcome'],'INCOMPLETE')
            self.assertEqual(c.measured,dict.fromkeys(d.QUERY_NAMES,1))

    def test_classification_tail_or_shape_incomplete_continues_safely(self):
        for change in ({'last_lsn':'0/1FF'},{'outside_records':1},{'record_count':513},
                       {'block_count':513},{'description':'SECRET_ROW_PAYLOAD'}):
            with self.subTest(change=change):
                c=self.connection()
                c.technical_mutate=lambda v,n:v.update(change) if n=='access' else None
                r=self.run_probe(c)
                self.assertNotIn('technical',r['queries'][0])
                self.assertFalse(r['queries'][0]['complete'])
                self.assertEqual(c.measured,dict.fromkeys(d.QUERY_NAMES,1))
                self.assertNotIn('SECRET_ROW_PAYLOAD',json.dumps(r))

    def test_span_capacity_skips_inspection_not_remaining_measurements(self):
        c=self.connection();c.ends['access']='0/10101';r=self.run_probe(c)
        self.assertIn('wal_interval_capacity',r['queries'][0]['limitations'])
        self.assertEqual(c.measured,dict.fromkeys(d.QUERY_NAMES,1))
        self.assertEqual(sum(x[0].startswith('with bounds as materialized') for x in c.calls),5)

    def test_transport_failure_stops_after_rollback_without_retry(self):
        c=self.connection();target=c.bound['access'][0];c.fail=lambda sql:sql==target
        r=self.run_probe(c)
        self.assertEqual(sum(x[0]==target for x in c.calls),1)
        self.assertEqual(c.calls[-1][0],'ROLLBACK');self.assertTrue(r['rollback_confirmed'])
        self.assertEqual(len(r['queries']),1);self.assertFalse(r['diagnostic_complete'])
        self.assertNotIn('SECRET',json.dumps(r))
        self.assertFalse(r['command_ledger'][-2]['confirmed'])

    def test_rollback_failure_never_retries_or_continues(self):
        c=self.connection();c.fail=lambda sql:sql=='ROLLBACK';r=self.run_probe(c)
        self.assertEqual(sum(x[0]=='ROLLBACK' for x in c.calls),1)
        self.assertEqual(len(r['queries']),1);self.assertFalse(r['rollback_confirmed'])
        self.assertFalse(any(x[0]==d.COVERAGE for x in c.calls))
        self.assertEqual(r['outcome'],'INCOMPLETE')

    def test_unclosed_transaction_stops_even_if_rollback_command_returned(self):
        c=self.connection();c.keep_open=True;r=self.run_probe(c)
        self.assertEqual(sum(x[0]=='ROLLBACK' for x in c.calls),1)
        self.assertEqual(len(r['queries']),1);self.assertFalse(r['rollback_confirmed'])
        self.assertFalse(any(x[0]==d.COVERAGE for x in c.calls))

    def test_security_readonly_assertion_and_binding_collision_stop(self):
        for kind in ('start','end','collision'):
            c=self.connection()
            if kind=='start':c.start_readonly=False
            elif kind=='end':c.end_readonly=False
            else:c.collision=True
            r=self.run_probe(c)
            self.assertEqual(len(r['queries']),1);self.assertFalse(r['diagnostic_complete'])
            self.assertFalse(any(x[0]==d.COVERAGE for x in c.calls))
            self.assertEqual(c.measured['migrations'],0)
            self.assertEqual(c.measured['access'],1 if kind=='end' else 0)

    def test_cap_reserves_single_rollback_before_next_command(self):
        c=self.connection()
        with patch.object(d,'MAX_COMMANDS',7):r=self.run_probe(c)
        self.assertLessEqual(r['commands'],7)
        self.assertEqual(c.calls[-1][0],'ROLLBACK');self.assertTrue(r['rollback_confirmed'])
        self.assertEqual(len(r['queries']),1)

    def test_environment_role_peer_tls_and_limits_rejected_before_sql(self):
        for key,value in (('host','hosted.example'),('hostaddr','203.0.113.1'),
                          ('user','supabase_admin'),('server_version',160000),
                          ('transaction_status',2),('dbname','other')):
            c=self.connection();setattr(c.info,key,value)
            with self.assertRaises(ValueError):self.run_probe(c)
            self.assertEqual(c.calls,[])
        for key,value in (('sslmode','require'),('connect_timeout','6'),
                          ('sslrootcert',None),('options','-c statement_timeout=6000')):
            c=self.connection();c.parameters[key]=value
            with self.assertRaises(ValueError):self.run_probe(c)
            self.assertEqual(c.calls,[])
        for env in ({},{**ENV,'FMZ6E11_LOCAL_WAL_DIAGNOSTIC':'0'},
                    {**ENV,'GITHUB_REPOSITORY':'other/project'}):
            c=self.connection()
            with self.assertRaises(ValueError):
                d.run(c,environment='disposable_ci',ids=IDS,context=CONTEXT,
                      ci_ca_path=self.ca,environ=env)
            self.assertEqual(c.calls,[])

    def test_unavailable_extension_or_privilege_failure_stops_without_elevation(self):
        c=self.connection(installed=None);c.preflight['available']=False;r=self.run_probe(c)
        self.assertEqual(r['commands'],1);self.assertEqual(r['queries'],[])
        c=self.connection(installed=None);c.fail=lambda sql:sql.startswith('CREATE EXTENSION')
        r=self.run_probe(c)
        self.assertEqual(r['commands'],2);self.assertEqual(r['queries'],[])
        self.assertIn('pg_walinspect_install_unavailable',r['limitations'])
        self.assertNotIn('SECRET',json.dumps(r))

    def test_prefight_ssl_server_limits_and_missing_ca_fail_closed(self):
        for key,value in (('ssl',False),('statement_timeout','6s'),('lock_timeout','2s'),
                          ('version',180000),('readonly','on')):
            c=self.connection();c.preflight[key]=value;r=self.run_probe(c)
            self.assertEqual(r['commands'],1);self.assertEqual(r['queries'],[])
        c=self.connection();self.ca.unlink()
        with self.assertRaises(ValueError):self.run_probe(c)
        self.assertEqual(c.calls,[])

    def test_raw_sql_secrets_rows_and_hashes_are_not_exported(self):
        c=self.connection();r=self.run_probe(c);text=json.dumps(r)
        for prohibited in ('PRIVATE_FIXTURE_CONTENTS','PRIVATE_HASH_VALUE',str(self.ca),
                           'select ',IDS['a_member'],'password','description','block_data'):
            self.assertNotIn(prohibited,text)
        self.assertFalse(r['row_contents_exported']);self.assertFalse(r['query_text_exported'])
        self.assertNotIn('description',d.INSPECT);self.assertNotIn('block_data',d.INSPECT)
        self.assertIn('(select hi from bounds),false)',d.INSPECT)
        self.assertIn('extensions.pg_stat_statements(false)',d.STATS)
        self.assertIn('and toplevel and queryid::text=$1',d.STATS)

    def test_rowhash_is_bounded_expression_not_full_stream_or_auth_fixture(self):
        c=self.connection();r=self.run_probe(c)
        self.assertIn('not_full_cursor_cycle',r['rowhash_scope'])
        self.assertEqual(r['queries'][-1]['hash_rows_discarded'],45)
        self.assertEqual(sum(x[0]==d.CONFIG for x in c.calls),1)
        index=next(i for i,x in enumerate(c.calls) if x[0]==d.CONFIG)
        self.assertEqual(c.calls[index+1][0],d.START)
        self.assertIn('limit 8193',d.ROW_HASH)
        c=self.connection();c.row_count=d.PAGE+1;r=self.run_probe(c)
        self.assertFalse(r['diagnostic_complete']);self.assertTrue(r['rollback_confirmed'])

    def test_safe_object_class_and_group_count_validation(self):
        c=self.connection();r=self.run_probe(c);v=r['queries'][0]['technical']
        v={k:x for k,x in v.items() if k not in ('object_mapping_scope','record_owner_attribution')}
        for mutation in ({'groups':[{'rmgr':'Heap2','record_type':'PRUNE','records':1}]},
                         {'object_classes':[{'object_class':'arbitrary_relation_name','blocks':2}]}):
            with self.assertRaises(ValueError):d.technical_only({**v,**mutation},'0/100','0/200')

    def test_save_closes_and_forced_diagnostic_stop(self):
        c=self.connection(zero=True);saved={}
        with self.assertRaises(d.DiagnosticOnlyStop):
            d.run_and_stop(c,lambda n,v:saved.update({n:v}),environment='disposable_ci',
                ids=IDS,context=CONTEXT,ci_ca_path=self.ca,environ=ENV)
        self.assertTrue(c.closed);self.assertEqual(list(saved),['ci-wal-diagnostic.json'])
        self.assertFalse(saved['ci-wal-diagnostic.json']['full_chain_admission'])

    def test_each_sql_is_one_pg17_statement_no_hidden_command_batch(self):
        from sql_protocol import statements
        sources=[d.PREFLIGHT,d.START,d.END,d.COVERAGE,d.WAIT,d.STATS,d.CONFIG,
                 d.INSPECT.format(schema='"extensions"').replace('%s',"'0/100'"),
                 'BEGIN TRANSACTION READ ONLY','ROLLBACK',
                 'CREATE EXTENSION pg_walinspect WITH SCHEMA extensions']
        sources.extend(source for name,source,args in d.families(IDS,CONTEXT))
        for source in sources:
            with self.subTest(sql_sha256=d.sha(source)):
                self.assertEqual(len(statements(source)),1)

if __name__=='__main__':unittest.main()
