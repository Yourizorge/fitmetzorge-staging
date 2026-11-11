"""Offline feasibility only. No connection, subprocess, SQL execution or CI API."""
import hashlib
import json
from pglast import parser

OPTIONS='EXPLAIN (ANALYZE TRUE, BUFFERS TRUE, WAL TRUE, TIMING FALSE, VERBOSE FALSE, COSTS FALSE, SERIALIZE TEXT, FORMAT JSON) '
METRICS=('WAL Records','WAL FPI','WAL Bytes','Temp Read Blocks','Temp Written Blocks')

def sha(raw):return hashlib.sha256(raw).hexdigest()

def prepare(sql, expected_sha):
    if sha(sql.encode())!=expected_sha:raise ValueError('source_changed')
    parsed=json.loads(parser.parse_sql_json(sql))
    statements=parsed['stmts']
    if len(statements)!=1 or set(statements[0]['stmt'])!={'SelectStmt'}:
        raise ValueError('one_select_required')
    def check(value):
        if isinstance(value,dict):
            if set(value)&{'InsertStmt','UpdateStmt','DeleteStmt','MergeStmt','IntoClause','intoClause'}:
                raise ValueError('write_shape')
            for item in value.values():check(item)
        elif isinstance(value,list):
            for item in value:check(item)
    check(parsed)
    wrapped=OPTIONS+sql
    tree=json.loads(parser.parse_sql_json(wrapped))
    if len(tree['stmts'])!=1 or set(tree['stmts'][0]['stmt'])!={'ExplainStmt'}:
        raise ValueError('explain_shape')
    return {'query_sha256':expected_sha,'explain_sha256':sha(wrapped.encode()),
        'pg17_parse_ok':True,'parameter_values_bound':False,'actual_execution':False,
        'full_chain_admission':False}

def numeric_only(value):
    """Untrusted JSON projection only; missing counters are never invented zero."""
    if len(json.dumps(value).encode())>1000000:raise ValueError('plan_size')
    if type(value) is not list or len(value)!=1 or type(value[0]) is not dict:
        raise ValueError('plan_shape')
    result=[]
    def visit(node,path,depth):
        if depth>32 or len(result)>=256 or type(node) is not dict:raise ValueError('node_bound')
        if not all(type(node.get(k)) is int and 0<=node[k]<2**64 for k in METRICS):
            raise ValueError('numeric_missing_or_invalid')
        result.append({'position':path,'metrics':{k:node[k] for k in METRICS}})
        children=node.get('Plans',[])
        if type(children) is not list:raise ValueError('children_shape')
        for index,child in enumerate(children):visit(child,path+'/'+str(index),depth+1)
    visit(value[0].get('Plan'),'0',0)
    return {'nodes':result,'summed_across_nodes':False,'row_contents_exported':False,
        'planning_utility_background_covered':False,'serialization_wal_complete':False,
        'historical_wal_reclassified':False,'full_chain_admission':False}
