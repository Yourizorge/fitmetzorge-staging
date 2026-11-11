"""Read-only catalog47/local48 validation; no transport, writes or WAL waiver.

Main executes either SELECT once through its existing metered QueryIO slot.
The returned metadata is held in memory; receipts need only the returned hashes.
History attestation remains CaseHistory's responsibility before each call here.
"""
import copy
import pathlib
import sys

import admission_quota_readonly as quota
import lifecycle_gates as gates
import quota_boundary
import migration_boundary
from sql_protocol import single
from . import compiler, runtime_history
from .compiler import require, sha, canonical, read_source

SCHEMA = compiler.SCHEMA
TABLE = 'quota_candidate_v1_cases'
FUNCTION = compiler.FUNCTION
PREFIX = compiler.PREFIX
OWN = PREFIX + 'quota_candidate_v1/runtime_catalog.py'


def array_query(sql):
    return "(select coalesce(jsonb_agg(to_jsonb(q)),'[]'::jsonb) from (" + sql + ') q)'


TABLE_QUERY = """select c.oid::text oid,c.relname name,c.relkind::text kind,
 pg_get_userbyid(c.relowner) owner,c.relrowsecurity rls,c.relforcerowsecurity force,
 c.relpersistence::text persistence,c.relispartition partition,
 exists(select 1 from pg_inherits i where c.oid in(i.inhrelid,i.inhparent)) inherited,
 exists(select 1 from pg_rewrite r where r.ev_class=c.oid) rules,
 exists(select 1 from pg_policy p where p.polrelid=c.oid) policies,
 coalesce((select jsonb_agg(jsonb_build_object('grantee',pg_get_userbyid(a.grantee),
 'grantor',pg_get_userbyid(a.grantor),'privilege',a.privilege_type,'grantable',a.is_grantable))
 from aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a),'[]'::jsonb) acl,
 exists(select 1 from (values('anon'),('authenticated'),('service_role')) r(name)
 where has_table_privilege(r.name,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')
 or has_any_column_privilege(r.name,c.oid,'SELECT,INSERT,UPDATE,REFERENCES')) forbidden_access
 from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname='fmz6e11_controller_private' and c.relname='quota_candidate_v1_cases'"""
COLUMNS_QUERY = """select a.attnum ordinal,a.attname name,tn.nspname type_schema,t.typname type,
 a.atttypmod typmod,a.attnotnull notnull,a.attidentity::text identity,a.attgenerated::text generated,
 a.attisdropped dropped,pg_get_expr(d.adbin,d.adrelid) default_expression,
 a.attcollation=t.typcollation default_collation,a.attacl is null no_column_acl
 from pg_attribute a join pg_type t on t.oid=a.atttypid join pg_namespace tn on tn.oid=t.typnamespace
 left join pg_attrdef d on d.adrelid=a.attrelid and d.adnum=a.attnum
 where a.attrelid=to_regclass('fmz6e11_controller_private.quota_candidate_v1_cases')
 and a.attnum>0 order by a.attnum limit 65"""
CHECKS_QUERY = """select c.oid::text oid,c.conname name,c.contype::text kind,c.conrelid::text relation_oid,
 c.convalidated validated,c.conislocal local,c.coninhcount inherited,c.connoinherit noinherit,
 c.condeferrable deferrable,c.condeferred deferred,pg_get_expr(c.conbin,c.conrelid,false) expression,
 array(select a.attname::text from unnest(c.conkey) with ordinality k(attnum,ord)
 join pg_attribute a on a.attrelid=c.conrelid and a.attnum=k.attnum order by k.ord) columns
 from pg_constraint c where c.conrelid=to_regclass('fmz6e11_controller_private.quota_candidate_v1_cases')
 limit 65"""
INDEXES_QUERY = """select c.oid::text oid,c.relname name,am.amname method,
 i.indisunique unique,i.indisprimary primary,i.indisvalid valid,i.indisready ready,i.indislive live,
 i.indnkeyatts keys,i.indnatts attributes,i.indnullsnotdistinct nulls_not_distinct,
 i.indpred is null no_predicate,i.indexprs is null no_expressions,
 i.indkey::text key_numbers,i.indoption::text options,
 array(select n.nspname||'.'||o.opcname from unnest(i.indclass) with ordinality k(oid,ord)
 join pg_opclass o on o.oid=k.oid join pg_namespace n on n.oid=o.opcnamespace order by k.ord) opclasses
 from pg_index i join pg_class c on c.oid=i.indexrelid join pg_am am on am.oid=c.relam
 where i.indrelid=to_regclass('fmz6e11_controller_private.quota_candidate_v1_cases') limit 65"""
FUNCTION_QUERY = quota.QUERIES['function'].replace('select n.nspname schema',
    'select p.oid::text oid,n.nspname schema').replace('recovery_run_receipt', FUNCTION)+' limit 65'
TRIGGERS_QUERY = quota.QUERIES['trigger'].replace('select n.nspname schema',
    'select t.oid::text oid,n.nspname schema').replace(
    "and r.relname='runs'\n and t.tgname='recovery_run_receipt'",
    "and (p.proname='quota_candidate_v1_receipt' or r.relname='quota_candidate_v1_cases'\n"
    " or t.tgname in ('quota_candidate_v1_receipt','quota_candidate_v1_truncate','quota_candidate_v1_catalog_immutable'))")+' limit 65'
LEASE_QUERY = """select run_id::text,purpose,cap,parent_id::text,source_commit,candidate_sha,
 ci_run::text,to_char(starts_at at time zone 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"') starts_at,
 to_char(expiry at time zone 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"') expiry,binding_sha,
 extract(microseconds from starts_at)::bigint%1000000=0 and
 extract(microseconds from expiry)::bigint%1000000=0 whole_seconds
 from fmz6e11_controller_private.quota_candidate_v1_cases order by run_id limit 16"""
EMPTY_QUERY = quota.QUERIES['empty']


def catalog_sql(appended):
    pieces = [('table',array_query(TABLE_QUERY)),('columns',array_query(COLUMNS_QUERY)),
        ('checks',array_query(CHECKS_QUERY)),('indexes',array_query(INDEXES_QUERY)),
        ('function',array_query(FUNCTION_QUERY)),('triggers',array_query(TRIGGERS_QUERY)),
        ('leases',array_query(LEASE_QUERY) if appended else "'[]'::jsonb"),
        ('empty',array_query(EMPTY_QUERY))]
    baseline = "'null'::jsonb" if appended else 'jsonb_build_object('+','.join(
        "'"+name+"',"+array_query(sql) for name,sql in quota.QUERIES.items())+')'
    return 'with original as ('+gates.CATALOG+") select value || jsonb_build_object('candidate',"+\
        'jsonb_build_object('+','.join("'"+name+"',"+sql for name,sql in pieces)+\
        "),'baseline_quota',"+baseline+') value from original'


CATALOG_BEFORE = catalog_sql(False)
CATALOG_AFTER = catalog_sql(True)
SQL_COMMANDS = {'before':1,'after':1}


def expression(value):
    """Normalize only PG's known deparse forms in this bound template."""
    node = quota.expression_ast(value) if isinstance(value,str) else quota.strip_locations(value)
    def normalize(v):
        if isinstance(v,list):return [normalize(x) for x in v]
        if not isinstance(v,dict):return v
        if v.get('@')=='TypeCast' and v.get('arg',{}).get('@')=='A_Const':
            names=[n['sval'] for n in v['typeName']['names']]
            if names in (['text'],['pg_catalog','text']) and v['arg']['val'].get('@')=='String':
                return normalize(v['arg'])
            if names in (['interval'],['pg_catalog','interval']):
                v=copy.deepcopy(v)
                if v['arg']['val'].get('sval')=='00:10:00':v['arg']['val']['sval']='10 minutes'
        if v.get('@')=='A_Expr' and v['kind']['name']=='AEXPR_BETWEEN':
            result=quota.expression_ast('x>=1 and x<=2')
            result['args'][0]['lexpr']=result['args'][1]['lexpr']=v['lexpr']
            result['args'][0]['rexpr'],result['args'][1]['rexpr']=v['rexpr']
            return normalize(result)
        return {k:normalize(x) for k,x in v.items()}
    return normalize(node)


def fields(actual, expected, reason):
    require(type(actual) is dict and all(k in actual and quota.typed_equal(actual[k],v)
        for k,v in expected.items()),reason)


def oid(value):
    if type(value) is int:value=str(value)
    require(type(value) is str and value.isdigit() and int(value)>0,'case_catalog_oid')
    return value


def source_contract(sql):
    nodes=[n.stmt for n in quota.parser().parse_sql(sql)]
    tables=[n for n in nodes if type(n).__name__=='CreateStmt']
    functions=[n for n in nodes if type(n).__name__=='CreateFunctionStmt']
    triggers=[n for n in nodes if type(n).__name__=='CreateTrigStmt']
    checks=[cmd.def_ for n in nodes if type(n).__name__=='AlterTableStmt'
        for cmd in n.cmds if type(cmd.def_).__name__=='Constraint']
    require(len(tables)==len(functions)==len(checks)==1 and len(triggers)==3,'case_catalog_sql_shape')
    table=tables[0];function=functions[0]
    require((table.relation.schemaname,table.relation.relname)==(SCHEMA,TABLE),'case_catalog_table_source')
    columns=[];constraints={}
    for i,col in enumerate(table.tableElts,1):
        require(type(col).__name__=='ColumnDef','case_catalog_column_source')
        kinds={c.contype.name for c in col.constraints or ()}
        require(kinds<= {'CONSTR_PRIMARY','CONSTR_CHECK','CONSTR_NOTNULL'},'case_catalog_column_constraint')
        names=[x.sval for x in col.typeName.names]
        require(len(names) in (1,2) and not col.typeName.arrayBounds and not col.typeName.typmods,
            'case_catalog_column_type')
        columns.append(dict(ordinal=i,name=col.colname,type_schema='pg_catalog',type=names[-1],
            typmod=-1,notnull=bool(kinds & {'CONSTR_NOTNULL','CONSTR_PRIMARY'}),identity='',generated='',
            dropped=False,default_expression=None,default_collation=True,no_column_acl=True))
        for c in col.constraints or ():
            if c.contype.name=='CONSTR_CHECK':
                name=c.conname or TABLE+'_'+col.colname+'_check'
                require(name not in constraints,'case_catalog_duplicate_constraint')
                constraints[name]=('c',expression(c.raw_expr()),None)
            elif c.contype.name=='CONSTR_PRIMARY':
                constraints[c.conname or TABLE+'_pkey']=('p',None,[col.colname])
    options={o.defname:o.arg for o in function.options if o.defname!='set'}
    config=[o.arg.name+'='+', '.join(v.val.sval for v in o.arg.args)
        for o in function.options if o.defname=='set']
    require([n.sval for n in function.funcname]==[SCHEMA,FUNCTION] and not function.parameters,
        'case_catalog_function_source')
    return dict(columns=columns,checks=constraints,run_check=expression(checks[0].raw_expr()),
        body=options['as'][0].sval,language=options['language'].sval,
        definer=bool(options.get('security') and options['security'].boolval),config=config,
        triggers={t.trigname:quota.strip_locations(t()) for t in triggers})


class CaseCatalog:
    def __init__(self,root,sources,artifact,history):
        require(isinstance(history,runtime_history.CaseHistory),'case_catalog_history_owner')
        self.root=pathlib.Path(root);self.sources=copy.deepcopy(sources)
        self.artifact=copy.deepcopy(artifact);self.history=history
        self.before=self.after=None
        require(artifact['manifest']['sources']==sources,'case_catalog_manifest_sources')
        require(sha(artifact['sql'].encode('ascii'))==artifact['plan']['sql_sha256']
            ==history.bound[history.local_version]['raw_sha256'],'case_catalog_append_binding')
        require(history.root.resolve()==self.root.resolve(),'case_catalog_history_root')
        self._sources()
        self.contract=source_contract(artifact['sql'])
        for sql in (CATALOG_BEFORE,CATALOG_AFTER):single(sql)

    def _sources(self):
        modules=((sys.modules[__name__],OWN),(gates,PREFIX+'lifecycle_gates.py'),
            (quota,PREFIX+'admission_quota_readonly.py'),(quota_boundary,PREFIX+'quota_boundary.py'),
            (migration_boundary,PREFIX+'migration_boundary.py'),
            (runtime_history,PREFIX+'quota_candidate_v1/runtime_history.py'),
            (compiler,PREFIX+'quota_candidate_v1/compiler.py'))
        for module,name in modules:
            require(sha(read_source(self.root,name))==self.sources.get(name)
                ==sha(pathlib.Path(module.__file__).read_bytes()),'case_catalog_source_binding')

    def _state(self,state,appended):
        self._sources()
        require(type(state) is dict and set(state)=={'migrations','catalog'},'case_catalog_state_shape')
        history=self.history.after if appended else self.history.before
        require(history is not None and len(history)==(48 if appended else 47)
            and state['migrations']==history,'case_catalog_history_binding')
        catalog=state['catalog']
        require(type(catalog) is dict and set(catalog)=={'functions','relations','triggers','policies',
            'constraints','m44','candidate','baseline_quota'},'case_catalog_shape')
        for group in ('functions','relations','triggers','policies','constraints'):
            require(type(catalog[group]) is dict and len(catalog[group])<=4096,'case_catalog_metadata_bound')
            for key in catalog[group]:oid(key)
        candidate=catalog['candidate']
        require(type(candidate) is dict and set(candidate)=={'table','columns','checks','indexes',
            'function','triggers','leases','empty'},'case_catalog_candidate_shape')
        require(all(type(v) is list and len(v)<=64 for v in candidate.values()),'case_catalog_candidate_bound')
        return catalog,candidate

    def initial(self,state):
        require(self.before is None and self.after is None,'case_catalog_initial_once')
        catalog,candidate=self._state(state,False)
        require(all(not candidate[k] for k in candidate if k!='empty'),'case_catalog_candidate_preexists')
        quota.exact_fields(quota.one(candidate['empty']),dict.fromkeys(
            ('runs_empty','steps_empty','evidence_empty','pg17','database_ok'),True))
        compiler.validate_candidate(self.root,self.artifact,catalog['baseline_quota'],
            now=self.artifact['manifest']['created_at'])
        quota_boundary.check_objects(catalog['m44'],quota_boundary.source(self.root))
        quota_boundary.check_objects(catalog['m44']['legacy_m44'],migration_boundary.source(self.root))
        self.before=copy.deepcopy(state)
        return self.receipt(state,'INITIAL47_VALIDATED')

    def _candidate(self,catalog,candidate):
        contract=self.contract
        table=quota.one(candidate['table']);table_oid=oid(table['oid'])
        fields(table,dict(name=TABLE,kind='r',owner='postgres',rls=True,force=False,persistence='p',
            partition=False,inherited=False,rules=False,policies=False,forbidden_access=False),
            'case_catalog_table_contract')
        privileges=('SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN')
        expected_acl=[dict(grantee='postgres',grantor='postgres',privilege=p,grantable=False) for p in privileges]
        require(sorted(map(canonical,table['acl']))==sorted(map(canonical,expected_acl)),'case_catalog_table_acl')
        require(quota.typed_equal(candidate['columns'],contract['columns']),'case_catalog_columns')
        require(len(candidate['checks'])==len(contract['checks']),'case_catalog_constraints_count')
        seen=set()
        for row in candidate['checks']:
            require(row['name'] not in seen and row['name'] in contract['checks'],'case_catalog_constraint_identity')
            seen.add(row['name']);kind,expr,columns=contract['checks'][row['name']]
            fields(row,dict(kind=kind,relation_oid=table_oid,validated=True,local=True,inherited=0,
                noinherit=kind=='p',deferrable=False,deferred=False),'case_catalog_constraint_flags')
            require((row['expression'] is None if expr is None else expression(row['expression'])==expr)
                and (columns is None or row['columns']==columns),'case_catalog_constraint_expression')
            oid(row['oid'])
        index=quota.one(candidate['indexes']);oid(index['oid'])
        fields(index,{'name':TABLE+'_pkey','method':'btree','unique':True,'primary':True,'valid':True,
            'ready':True,'live':True,'keys':1,'attributes':1,'nulls_not_distinct':False,
            'no_predicate':True,'no_expressions':True,'key_numbers':'1','options':'0',
            'opclasses':['pg_catalog.uuid_ops']},'case_catalog_index')
        function=quota.one(candidate['function']);oid(function['oid'])
        fields(function,dict(schema=SCHEMA,name=FUNCTION,nargs=0,kind='f',returns_trigger=True,
            language=contract['language'],owner='postgres',definer=contract['definer'],leakproof=False,
            strict=False,volatility='v',parallel='u',config=contract['config'],body=contract['body'],
            effective_execute=dict.fromkeys(('anon','authenticated','service_role'),False),
            acl=[dict(grantee='postgres',grantor='postgres',privilege='EXECUTE',grantable=False)]),
            'case_catalog_function')
        require(len(candidate['triggers'])==len(contract['triggers']),'case_catalog_triggers_count')
        seen=set()
        for row in candidate['triggers']:
            require(row['name'] not in seen and row['name'] in contract['triggers'],'case_catalog_trigger_identity')
            seen.add(row['name']);oid(row['oid'])
            require(quota.strip_locations(quota.single_node(row['definition'],'CreateTrigStmt')())
                ==contract['triggers'][row['name']],'case_catalog_trigger_source')
            fields(row,dict(enabled='O',internal=False,nonconstraint=True,deferrable=False,deferred=False,
                nargs=0,argument_bytes=0,columns='',unconditional=True,old_transition=None,new_transition=None,
                function_schema=SCHEMA,function_name=FUNCTION,function_nargs=0),'case_catalog_trigger_flags')
        manifest=self.artifact['manifest']
        expected=[dict(run_id=c['id'],purpose=manifest['purpose'],cap=c['cap'],parent_id=manifest['parent_run'],
            source_commit=manifest['source_commit'],candidate_sha=manifest['candidate_sha256'],ci_run=manifest['github_run'],
            starts_at=manifest['created_at'],expiry=manifest['expires_at'],binding_sha=sha(canonical(manifest)),
            whole_seconds=True) for c in sorted(manifest['cases'],key=lambda c:c['id'])]
        require(quota.typed_equal(candidate['leases'],expected),'case_catalog_lease_binding')
        require(expression(catalog['m44']['constraint']['expression'])==contract['run_check']
            and catalog['m44']['constraint']['validated'] is True
            and catalog['m44']['constraint']['type']=='c','case_catalog_run_constraint')
        return {'relations':[table_oid,index['oid']], 'functions':[function['oid']],
            'triggers':[r['oid'] for r in candidate['triggers']],
            'constraints':[r['oid'] for r in candidate['checks']]}

    def transition(self,state):
        require(self.before is not None and self.after is None,'case_catalog_transition_order')
        catalog,candidate=self._state(state,True)
        require(catalog['baseline_quota'] is None,'case_catalog_after_baseline_shape')
        added=self._candidate(catalog,candidate)
        quota.exact_fields(quota.one(candidate['empty']),dict.fromkeys(
            ('runs_empty','steps_empty','evidence_empty','pg17','database_ok'),True))
        before=self.before['catalog'];actual=copy.deepcopy(catalog)
        for group,keys in added.items():
            require(len(keys)==len(set(keys)) and all(k not in before[group] and k in actual[group]
                for k in keys),'case_catalog_added_oid')
            for key in keys:del actual[group][key]
        old=oid(before['m44']['constraint_oid']);new=oid(catalog['m44']['constraint_oid'])
        require(old!=new and old not in actual['constraints'] and new not in before['constraints']
            and new in actual['constraints'],'case_catalog_replaced_constraint')
        del actual['constraints'][new];actual['constraints'][old]=copy.deepcopy(before['constraints'][old])
        legacy=copy.deepcopy(catalog['m44'])
        legacy['constraint']=before['m44']['constraint'];legacy['constraint_oid']=before['m44']['constraint_oid']
        require(quota.typed_equal(legacy,before['m44']),'case_catalog_legacy_or_rows_changed')
        actual['m44']=before['m44'];actual['candidate']=before['candidate'];actual['baseline_quota']=before['baseline_quota']
        require(quota.typed_equal(actual,before),'case_catalog_unexpected_delta')
        self.after=copy.deepcopy(state)
        return self.receipt(state,'LOCAL48_DELTA_VALIDATED')

    def check_observed(self,state):
        require(self.after is not None,'case_catalog_after_required')
        catalog,candidate=self._state(state,True)
        self._candidate(catalog,candidate)
        # The run itself may add its controller receipt. The stream owns row preservation.
        def stable(value):
            result=copy.deepcopy(value)
            result['catalog']['m44'].pop('run_hashes',None)
            candidate=result['catalog']['candidate']
            candidate.pop('empty',None)
            for name in ('checks','triggers'):
                candidate[name].sort(key=lambda row:row['oid'])
            candidate['table'][0]['acl'].sort(key=canonical)
            return result
        require(quota.typed_equal(stable(state),stable(self.after)),'case_catalog_post_drift')
        return self.receipt(state,'LOCAL48_CATALOG_UNCHANGED')

    @staticmethod
    def receipt(state,status):
        return dict(status=status,catalog_sha256=sha(canonical(state['catalog'])),
            history_sha256=sha(canonical(state['migrations'])),history_count=len(state['migrations']),
            canonical_migration_added=False,hosted_admitted=False,sql_executed_by_validator=0,
            read_wal_waived=False,source_statements_exported=False)
