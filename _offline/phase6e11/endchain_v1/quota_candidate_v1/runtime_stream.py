"""Versioned case scope; the original three-cycle stream engine is retained."""
import hashlib,json,pathlib,re,uuid
from integral_stream import (ROWS,PAGE,PAGES,PROTOCOL_CAPACITY,ALL_STATS,INVENTORY,CONFIG,
    GUARD,ident,literal,statement,capacity_statement,frame,check_plan,delta,
    UtilityBindings,other_load,predicates as historical_predicates)
from .compiler import require, binding

CATALOG = 'fmz6e11_controller_private.quota_candidate_v1_cases'
CATALOG_COLUMNS = ('run_id','purpose','cap','parent_id','source_commit','candidate_sha',
                   'ci_run','starts_at','expiry','binding_sha')
LABELS = ('before','before_cleanup','after_cleanup')


class CaseStream:
    def __init__(self, prepared, local_version):
        from .runtime_adapter import PreparedCase
        require(isinstance(prepared,PreparedCase), 'case_stream_preflight')
        q=prepared.config()
        require(q['binding']['parent_id']==binding.NEW_RUN
            and re.fullmatch('[0-9]{14}',local_version)
            and local_version>'20261018070231', 'case_stream_scope')
        self.run_id=q['binding']['run_id']
        self.version=local_version
        self.manifest_sha=q['binding']['binding_sha']
        self.attempts=[]

    def run(self,query,save,ids,context,label,expected=None):
        require(len(self.attempts)<3 and label==LABELS[len(self.attempts)],
                'case_stream_cycle_or_retry')
        require(context.get('migration_boundary',False) is False, 'case_stream_legacy_boundary')
        self.attempts.append(label)
        return _run(query,save,ids,{**context,'quota_scope':self},label,expected)


def predicates(row,ids,context):
    scope=context.get('quota_scope')
    require(isinstance(scope,CaseStream), 'case_stream_scope')
    schema,table=row['schema'],row['name']
    if schema=='supabase_migrations' and table=='schema_migrations':
        return "version<>'"+scope.version+"'"
    if schema=='fmz6e11_controller_private':
        require(table in ('runs','steps','evidence'), 'case_stream_unknown_controller_table')
        return ('id' if table=='runs' else 'run_id')+'<>'+literal(scope.run_id)
    return historical_predicates(row,ids,context)


def plan(inventory,ids,context):
    scope=context.get('quota_scope')
    require(isinstance(scope,CaseStream), 'case_stream_scope')
    out=[]
    catalog_seen=False
    for row in inventory:
        name=row['schema']+'.'+row['name']
        if name==CATALOG:
            require(not catalog_seen and tuple(row['columns'])==CATALOG_COLUMNS,
                    'case_stream_catalog_shape')
            catalog_seen=True
            # The new immutable lease has an exact source-bound catalog-row gate.
            # It did not exist at BEFORE; it is not historical business data.
            continue
        if row['schema'] in context.get('temporary_schemas',[]):continue
        out.append(dict(name=name,predicate=predicates(row,ids,context)))
    require(catalog_seen is (scope.attempts[-1]!='before'), 'case_stream_catalog_presence')
    require(100<=len(out)<=200 and len({r['name'] for r in out})==len(out),
            'case_stream_inventory_budget')
    return out


def _run(query,save,ids,context,label,expected=None):
    count=0;frames=[];profiles=[];buffer={};opened=False;active_phase='not_started';original_error=None
    def q(phase,sql,args=()):
        nonlocal count,active_phase
        active_phase=phase
        count+=1
        if count>(96 if phase=='rollback' else 95):raise ValueError('ci_stream_command_ceiling')
        return query('stream_'+label+'_'+phase,sql,args)
    try:
        q('begin','BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');opened=True
        identity=q('guard',GUARD)[0]
        if identity['ro']!='on' or identity['isolation']!='repeatable read' or identity['db']!='postgres' or identity['role']!='postgres' or identity['ssl'] is not True:
            raise ValueError('stream_identity')
        if context.get('instance_sha') and identity['instance_sha']!=context['instance_sha']:raise ValueError('stream_project_instance')
        q('canonical',CONFIG)
        plans=plan(q('inventory',INVENTORY),ids,context)
        if expected is not None and plans!=expected['plan']:raise ValueError('stream_inventory_changed')
        stream=statement(plans);capacity=capacity_statement(plans)
        save('integral-stream-'+label+'-binding.json',{'plan':plans,
            'query_sha256':hashlib.sha256(stream.encode()).hexdigest(),
            'capacity_query_sha256':hashlib.sha256(capacity.encode()).hexdigest(),
            'filter_sha256':hashlib.sha256(json.dumps(plans,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
            'row_limit':ROWS,'page_limit':PAGE,'filter_before_transport':True,
            'limit_scope':'total transported protected row hashes per cycle; duplicate rows count separately',
            'capacity_sentinel_limit':ROWS+1,
            'canonicalization':'PG17 JSONB text UTF8 SHA256 / sorted duplicate-preserving multiset'})
        reader=check_plan(q('reader_bind','EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) '+ALL_STATS)[0]['QUERY PLAN'])
        def sample():
            value=q('io',ALL_STATS)[0]['value']
            if len(value['statements'])>5000:raise ValueError('stream_numeric_metadata_budget')
            return value
        previous=sample();buffer={r['name']:[] for r in plans};total=0;bindings=UtilityBindings()
        def utility(sql):
            nonlocal previous,active_phase
            before=previous
            prefix='integral-stream-'+label+'-utility-%03d'%len(profiles)
            binding={'sql_sha256':hashlib.sha256(sql.encode()).hexdigest(),'reader_queryid':reader}
            save(prefix+'-before.json',{'binding':binding,'sample':before,'next_command':count+1})
            rows=q('utility',sql);terminal=query.terminal_count;after=sample()
            save(prefix+'-after.json',{'binding':binding,'sample':after,'command':count,
                'returned_rows':len(rows),'terminal_count':terminal})
            active_phase='utility_attribution'
            observation=bindings.observe(binding['sql_sha256'],before,after,reader)
            save(prefix+'-attribution.json',{'binding':binding,**observation})
            if not observation['unambiguous']:
                raise ValueError('stream_utility_attribution')
            active_phase='utility_load'
            profile=delta(before,after,{observation['queryid']:1,reader:1})
            background=other_load(before,after,observation)
            save(prefix+'-other-load.json',background)
            save('integral-stream-'+label+'-io-%03d.json'%len(profiles),profile)
            # Even hint-bit WAL is not waived for this owner's read-only run.
            if profile['own_wal_bytes'] != 0:raise ValueError('stream_own_wal')
            if any(x['exec_ms']>2500 for x in profile['queries']):raise ValueError('stream_own_load')
            bindings.confirm(binding['sql_sha256'],observation)
            profiles.append(profile);previous=after
            return rows,terminal
        size,size_terminal=utility(capacity)
        active_phase='row_capacity'
        if size_terminal!=1 or len(size)!=1 or set(size[0])!={'protected_rows'} or not re.fullmatch('[0-9]+',str(size[0]['protected_rows'])):
            raise ValueError('stream_capacity_frame')
        required=int(size[0]['protected_rows'])
        save('integral-stream-'+label+'-capacity.json',{'protected_rows_bounded':required,
            'sentinel_limit':ROWS+1,'fits':required<=ROWS,'hash_rows_received':0,
            'same_snapshot':True,'query_sha256':hashlib.sha256(capacity.encode()).hexdigest()})
        if required>ROWS:raise ValueError('stream_row_ceiling')
        utility('DECLARE fmz_integral_hashes NO SCROLL CURSOR WITHOUT HOLD FOR '+stream)
        while total<required:
            requested=min(PAGE,required-total,ROWS-total)
            rows,terminal=utility('FETCH FORWARD '+str(requested)+' FROM fmz_integral_hashes')
            active_phase='frame_validation'
            frame(rows,terminal)
            if len(rows)!=requested:raise ValueError('stream_capacity_mismatch')
            total+=len(rows)
            active_phase='row_capacity'
            if total>ROWS:raise ValueError('stream_row_ceiling')
            frames.append({'page':len(frames),'rows':len(rows),'requested_rows':requested,'terminal_count':terminal,
                'sha256':hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()})
            for r in rows:
                if int(r['i'])>=len(plans):raise ValueError('stream_table_index')
                if r['keep']!='1':raise ValueError('stream_unfiltered_row')
                buffer[plans[int(r['i'])]['name']].append(r['h'])
        utility('CLOSE fmz_integral_hashes')
        terminal=q('io_terminal','EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) '+ALL_STATS)
        if check_plan(terminal[0]['QUERY PLAN'],True)!=reader:raise ValueError('stream_closing_binding')
        if q('final_guard',GUARD)[0]!=identity:raise ValueError('stream_snapshot_changed')
        active_phase='protected_comparison'
        tables={name:{'rows':len(h),'sha256':hashlib.sha256(','.join(sorted(h)).encode()).hexdigest()} for name,h in buffer.items()}
        if expected is not None:
            save('integral-stream-'+label+'-comparison.json',{'before':expected['tables'],'after':tables,
                'equal':expected['tables']==tables,'contents_exported':False})
            if expected['tables']!=tables:raise ValueError('stream_protected_drift')
        value={'label':label,'tables':tables,'rows':total,'plan':plans,'frames':frames,'profiles':profiles,
            'protected_rows_bounded':required,'complete_by_same_snapshot_capacity':total==required,
            'capacity_query_sha256':hashlib.sha256(capacity.encode()).hexdigest(),
            'query_sha256':hashlib.sha256(stream.encode()).hexdigest(),'snapshot_sha256':hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest(),
            'canonicalization':'PG17 JSONB text UTF8 SHA256 / sorted duplicate-preserving multiset',
            'algorithm':'fmz-legacy-sha256-multiset-pinned-v1','query_text_read':False,'protected_equal':expected is None or tables==expected['tables'],
            'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
            'protocol_commands':count+1,'hosted_admitted':False}
        save('integral-stream-'+label+'.json',value);return value
    except Exception as error:
        original_error=error
        try:
            safe_reasons={'stream_row_ceiling','stream_utility_attribution','stream_terminal_count',
                'stream_frame_content','stream_frame_bytes','stream_table_index','stream_empty_terminal_missing',
                'stream_capacity_frame','stream_capacity_mismatch','stream_unfiltered_row',
                'stream_protected_drift','stream_snapshot_changed','stream_inventory_changed',
                'stream_unattributed_load','stream_own_load','stream_own_wal','io_own_spill','io_project_health',
                'io_duplicate_query_identity','io_command_attribution','io_statistics_reset',
                'io_counter_missing_or_replaced','io_background_counter_reset','io_query_time',
                'stream_utility_tracking_disabled'}
            save('integral-stream-'+label+'-stop.json',{'failed_phase':active_phase,'command':count,
                'exception_class':type(error).__name__,'sqlstate':getattr(error,'sqlstate',None),
                'reason_code':str(error) if type(error) is ValueError and str(error) in safe_reasons else 'unclassified_sanitized_failure',
                'received_rows':locals().get('total',0),'row_limit':ROWS,
                'completed_frames':len(frames),'completed_profiles':len(profiles),'automatic_retry':False})
        except Exception as storage_error:error.add_note('stop_storage_failed:'+type(storage_error).__name__)
        raise
    finally:
        if opened:
            try:q('rollback','ROLLBACK')
            except Exception as rollback_error:
                if original_error is None:raise
                original_error.add_note('rollback_failed:'+type(rollback_error).__name__)
