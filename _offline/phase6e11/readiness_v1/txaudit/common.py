"""Synthetic-only SQL builder; no credentials and no hosted calls on import."""
import hashlib,json,pathlib,sys,uuid
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parents[1]/'fingerprint_v1'))
from guard import Stop,save,digest
A='fmz6e11_audit_private'
def lit(x):return "'"+str(x).replace("'","''")+"'"
def js(x):return lit(json.dumps(x))+'::jsonb'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def fresh():
    return {x:str(uuid.uuid4()) for x in ('run','action','actor','workspace','row')}
def pk(c,table=None,row=None):
    return f"{A}.pk_hash({lit(c['run'])},{lit(table or A+'.fixture')},jsonb_build_array({lit(row or c['row'])}::uuid))"
def expected(c,ops=('INSERT','UPDATE','DELETE'),table=None,row=None):
    return 'jsonb_build_array('+','.join(
        "jsonb_build_object('table',"+lit(table or A+'.fixture')+",'op',"+lit(op)+
        ",'old',"+(pk(c,table,row) if op!='INSERT' else 'null')+
        ",'new',"+(pk(c,table,row) if op!='DELETE' else 'null')+")" for op in ops)+')'
def register(c,enabled=True,ops=('INSERT','UPDATE','DELETE'),contract=None,before='0'*64):
    return f"""do $q$begin
 insert into {A}.runs(id,expires_at) values({lit(c['run'])},clock_timestamp()+interval '5 minutes');
 insert into {A}.actors values({lit(c['actor'])},{lit(c['run'])},'synthetic_fixture_only');
 insert into {A}.actions(id,run_id,actor,workspace,expected,before_sha)
 values({lit(c['action'])},{lit(c['run'])},{lit(c['actor'])},{lit(c['workspace'])},{contract or expected(c,ops)},{lit(before)});
 update {A}.runs set enabled={'true' if enabled else 'false'} where id={lit(c['run'])};
 end $q$;"""
def start(c):return f"perform {A}.start_action({lit(c['action'])});"
def confirm(c):return f"perform {A}.confirm_action({lit(c['action'])});"
def insert(c,table='fixture',row=None,actor=None,workspace=None):
    return f"insert into {A}.{table} values({lit(row or c['row'])},{lit(actor or c['actor'])},{lit(workspace or c['workspace'])},0);"
def snapshot(c):
    return f"""/* fmz6e11:txaudit:scoped_snapshot_v1 */ select
 (select count(*) from {A}.fixture where id={lit(c['row'])})::int rows,
 (select count(*) from {A}.forbidden_fixture where id={lit(c['row'])})::int forbidden_rows,
 (select coalesce(jsonb_agg(jsonb_build_object('id',id,'actor',actor_id,'workspace',workspace_id,'n',n)),'[]')
 from {A}.fixture where id={lit(c['row'])}) synthetic_rows"""
def observations(c):
    return f"""/* fmz6e11:txaudit:observations_v1 */ select
 (select row_to_json(a) from {A}.actions a where id={lit(c['action'])}) action,
 (select coalesce(jsonb_agg(to_jsonb(w) order by ordinal),'[]') from {A}.writes w where action_id={lit(c['action'])}) writes,
 (select enabled from {A}.runs where id={lit(c['run'])}) enabled"""
def compare(c,before,after,observation):
    if not isinstance(before,dict) or not isinstance(after,dict):raise Stop('missing_pair')
    a=observation['action'];w=observation['writes']
    if a['id']!=c['action'] or a['run_id']!=c['run'] or a['actor']!=c['actor'] or a['workspace']!=c['workspace']:
        raise Stop('actor_action_binding')
    if a['state']!='action_confirmed' or a['before_sha']!=digest(before):raise Stop('action_confirmation_or_before')
    if before!=after or after['rows'] or after['forbidden_rows']:raise Stop('scoped_drift')
    actual=[]
    for i,x in enumerate(w,1):
        if (x['ordinal']!=i or str(x['xid'])!=str(a['xid']) or x['backend']!=a['backend']
            or x['action_id']!=a['id'] or x['run_id']!=c['run'] or x['actor']!=c['actor']
            or x['workspace']!=c['workspace']):raise Stop('write_transaction_binding')
        actual.append({'table':x['table_name'],'op':x['operation'],'old':x['old_key_sha'],'new':x['new_key_sha']})
    order=lambda x:json.dumps(x,sort_keys=True)
    if sorted(actual,key=order)!=sorted(a['expected'],key=order):raise Stop('expected_actual_mismatch')
    return {'pass':True,'run_id':c['run'],'action_id':c['action'],'transaction':str(a['xid']),
            'backend':a['backend'],'expected':a['expected'],'actual':actual,'writes':len(w),
            'before_sha':digest(before),'after_sha':digest(after),'forbidden_linked_writes':0,
            'scope':'private synthetic fixture probe only','workflow_or_auth_coverage':False}
