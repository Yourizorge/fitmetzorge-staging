"""Actual read-only absence witnesses after the two pre-Auth migration faults.

Four native commands and one Docker inventory, separately prepaid CI closeout.
This never creates Auth, accounts, a case lease or a full-chain admission.
"""
import json
import os
import re
import sys

import native_runtime
from .compiler import require, sha, canonical

IDENTITY = """select current_database() database,current_user::text role,
 current_setting('server_version_num')::int/10000 version,
 current_setting('transaction_read_only') readonly,
 current_setting('statement_timeout') statement_timeout,
 current_setting('lock_timeout') lock_timeout,
 (select ssl from pg_stat_ssl where pid=pg_backend_pid()) ssl,
 (select oid::bigint from pg_database where datname=current_database()) database_oid,
 (select system_identifier::text from pg_control_system()) pg_system_identifier"""
ACCOUNTS = """select (select count(*) from auth.users) users,
 (select count(*) from auth.sessions) sessions,
 (select count(*) from auth.refresh_tokens) refresh_tokens,
 (select count(*) from fmz6e11_controller_private.runs) controller_runs,
 (select count(*) from supabase_migrations.schema_migrations) history_count"""
COMMANDS = ('BEGIN TRANSACTION READ ONLY', IDENTITY, ACCOUNTS, 'ROLLBACK')
SCOPE = 'CI_BOOTSTRAP_CLOSEOUT_SEPARATE_FROM_CASE_2349'
DOCKER_ARGS = ('docker','ps','-a','--no-trunc',
    '--format','{"id":"{{.ID}}","image":"{{.Image}}","name":"{{.Names}}"}')


def reserve(gate, value):
    raw=canonical(value)+b'\n'
    path=gate.out/'case-preauth-closeout-reservation.json'
    with path.open('xb') as stream:
        require(stream.write(raw)==len(raw), 'bootstrap_closeout_reservation_short_write')
        stream.flush()
        os.fsync(stream.fileno())
    require(path.read_bytes()==raw, 'bootstrap_closeout_reservation_readback')


def ref(gate,name):
    path=gate.out/name
    require(not path.is_symlink() and path.resolve().parent==gate.out.resolve(), 'bootstrap_closeout_path')
    raw=path.read_bytes()
    require(len(raw)<=2000000, 'bootstrap_closeout_bytes')
    return dict(path=name,sha256=sha(raw),bytes=len(raw))


def inventory(output, pg_name):
    require(type(output) is str and len(output.encode())<=65536, 'bootstrap_container_inventory_bound')
    rows=[json.loads(line) for line in output.splitlines() if line.strip()]
    require(1<=len(rows)<=32, 'bootstrap_container_inventory_count')
    parsed=[];ids=set();names=set()
    for row in rows:
        require(set(row)=={'id','image','name'} and re.fullmatch('[a-f0-9]{64}',row['id'])
            and all(type(row[k]) is str for k in ('image','name')), 'bootstrap_container_inventory_shape')
        require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_./:@-]{0,511}',row['image'])
            and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,254}',row['name'])
            and row['id'] not in ids and row['name'] not in names,
            'bootstrap_container_inventory_identity')
        require('gotrue' not in row['image'].lower()
            and row['name'] not in ('fmz-guard-auth-ci','fmz-integration-auth-ci'), 'bootstrap_auth_present')
        ids.add(row['id']);names.add(row['name'])
        parsed.append(row)
    pg=[r for r in parsed if r['name']==pg_name]
    require(len(pg)==1, 'bootstrap_pg_inventory')
    return dict(pg_container=pg[0]['id'], gotrue_containers=0,
        containers_inspected=len(rows), inventory_rows=parsed, inventory_sha256=sha(canonical(parsed)),
        coverage='all_existing_disposable_docker_containers; Auth uses Docker only')


def check_samples(identity,counts,case_name):
    require(identity['database']=='postgres' and identity['role']=='postgres'
        and identity['version']==17 and identity['readonly']=='on' and identity['ssl'] is True
        and identity['statement_timeout'] in ('5s','5000ms')
        and identity['lock_timeout'] in ('1s','1000ms')
        and re.fullmatch('[1-9][0-9]{0,19}',identity['pg_system_identifier'])
        and type(identity['database_oid']) is int and identity['database_oid']>0,
        'bootstrap_closeout_identity')
    require(set(counts)=={'users','sessions','refresh_tokens','controller_runs','history_count'}
        and all(type(counts[k]) is int and counts[k]==0 for k in
                ('users','sessions','refresh_tokens','controller_runs'))
        and counts['history_count']==(44 if case_name=='pre_migration' else 45),
        'bootstrap_auth_absence_unconfirmed')


def collect(gate,binding,case_name,fault):
    require(case_name in ('pre_migration','post_migration') and fault.case==case_name
        and fault.fired is not None and fault.binding==binding, 'bootstrap_closeout_fault')
    expected='before45' if case_name=='pre_migration' else 'after45'
    require(fault.fired['event']['stage']==expected
        and json.loads((gate.out/'case-fault-boundary.json').read_bytes())==fault.fired,
        'bootstrap_closeout_boundary')
    require(os.environ.get('GITHUB_ACTIONS')=='true'
        and os.environ.get('GITHUB_REPOSITORY')=='Yourizorge/fitmetzorge-staging'
        and os.environ.get('GITHUB_REF')=='refs/heads/main'
        and os.environ.get('GITHUB_RUN_ATTEMPT')=='1'
        and os.environ.get('GITHUB_RUN_ID')==binding['ci_run']
        and os.environ.get('GITHUB_SHA')==binding['source_commit']
        and binding['environment']=='disposable_ci'
        and gate.result['candidate_sha256']==binding['candidate_sha'], 'bootstrap_closeout_ci')
    gate.bind_modules(sys.modules[__name__],native_runtime)
    receipt=dict(scope=SCOPE,complete=False,source_commit=binding['source_commit'],
        ci_run=binding['ci_run'],candidate_sha256=binding['candidate_sha'],run_id=binding['run_id'],
        case_name=case_name,reserved_sql_commands=4,no_refund=True,no_retry=True,
        commands=[],account_counts=None,auth_started=False,worker_started=False,
        quota_appended=False,full_chain_admission=False,hosted_admission=False)
    reserve(gate,{
        **receipt,'command_sha256':[sha(s.encode()) for s in COMMANDS], 'docker_inventory_calls':1,
        'docker_inventory_argv_sha256':sha(canonical(list(DOCKER_ARGS)))})
    connection=runtime=None;begin=False;rolled=False;closed=False;failure=None
    identity=counts=docker=None
    def query(index):
        nonlocal begin
        row=dict(ordinal=index+1,sql_sha256=sha(COMMANDS[index].encode()),confirmed=False)
        receipt['commands'].append(row)
        if index==0:begin=True
        cursor=connection.execute(COMMANDS[index])
        values=cursor.fetchall() if cursor.description else []
        row['confirmed']=True
        return values
    try:
        result=gate.command('case-preauth-container-inventory',list(DOCKER_ARGS),timeout=5)
        require(type(result.returncode) is int and result.returncode==0, 'bootstrap_container_inventory_exit')
        docker=inventory(result.stdout,gate.container)
        gate.save('case-preauth-container-absence.json',{
            **{k:receipt[k] for k in ('scope','run_id','source_commit','ci_run','candidate_sha256')},**docker,
            'inventory_command':dict(argv=list(DOCKER_ARGS),exitcode=result.returncode,
                timeout_seconds=5,dispatch_calls=1)})
        runtime=native_runtime.NativeRuntime.disposable(gate)
        connection=runtime.connect()
        query(0)
        rows=query(1);require(len(rows)==1,'bootstrap_identity_cardinality');identity=rows[0]
        rows=query(2);require(len(rows)==1,'bootstrap_accounts_cardinality');counts=rows[0]
        check_samples(identity,counts,case_name)
    except BaseException as error:failure=error
    finally:
        if begin:
            try:query(3);rolled=True
            except BaseException as error:
                if failure is None:failure=error
                else:failure.add_note('bootstrap_rollback_secondary:'+type(error).__name__)
        if connection is not None:
            try:connection.close();closed=True
            except BaseException as error:
                if failure is None:failure=error
                else:failure.add_note('bootstrap_close_secondary:'+type(error).__name__)
        if runtime is not None:
            try:runtime.clear()
            except BaseException as error:
                if failure is None:failure=error
                else:failure.add_note('bootstrap_clear_secondary:'+type(error).__name__)
        receipt.update(complete=failure is None and rolled and closed and len(receipt['commands'])==4,
            account_counts=counts,identity=identity,rollback_confirmed=rolled,connection_closed=closed,
            error_class=type(failure).__name__ if failure else None)
        try:gate.save('case-preauth-account-absence.json',receipt)
        except BaseException as error:
            if failure is None:failure=error
            else:failure.add_note('bootstrap_witness_secondary:'+type(error).__name__)
    if failure is not None:raise failure
    require(receipt['complete'], 'bootstrap_closeout_incomplete')
    target=sha(canonical(dict(pg_container=docker['pg_container'],
        pg_system_identifier=identity['pg_system_identifier'],database_oid=identity['database_oid'])))
    return dict(run_id=binding['run_id'],ci_run=binding['ci_run'],source_commit=binding['source_commit'],
        environment='disposable_ci',pg_system_identifier=identity['pg_system_identifier'],
        database_oid=identity['database_oid'],pg_container=docker['pg_container'],db_target_sha256=target,
        reused=False,auth_state='not_started',auth_container=None,auth_database_bound=False,
        auth_target_sha256=None,auth_absence=dict(verified=True,
            container_inventory_ref=ref(gate,'case-preauth-container-absence.json'),
            account_inventory_ref=ref(gate,'case-preauth-account-absence.json')))
