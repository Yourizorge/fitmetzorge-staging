"""One separately authorized read-only M44 inspection; never applies SQL."""
import hashlib, json, os, pathlib, re, sys, time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'endchain_v1'))
import migration_boundary as boundary
from hosted_gate import disk, save
from native_runtime import NativeRuntime, PROJECT
from integral_stream import GUARD
from lifecycle_gates import MIGRATIONS
from cli_stat_reader import SQL as STATS, compare
from sql_protocol import statements

RUN_ID = '08292976-0e47-4a4a-a425-8ae6c48e37e6'
INSTANCE = 'd165ac49d4d2aaa4733f7f220c351c99ff09493dace033a726f6fd722a573a15'
CLI_SHA = '442c83f7d455edc0462e94e22d60c9f7f05783fc83d39a0f49dadc78a914a1dd'
# No controller rows or personal contents are read.
TARGET = boundary.TARGET[:boundary.TARGET.index(",\n 'run_hashes'")] + \
    ", 'migration_statements',(select to_jsonb(statements) from supabase_migrations.schema_migrations where version='20261012185121'))"
OBJECTS = 'select ' + TARGET + ' value'
HEALTH = """select count(*) filter(where wait_event_type='IO') io_wait,
 count(*) filter(where state='active' and query_start<clock_timestamp()-interval '30 seconds') long_active
 from pg_stat_activity where datname=current_database() and pid<>pg_backend_pid()"""
TX = """select pg_backend_pid() pid, virtualtransaction vxid,
 current_setting('transaction_read_only') readonly
 from pg_locks where pid=pg_backend_pid() and locktype='virtualxid' and granted"""


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def identity(rows, obj, root=ROOT):
    local = sorted((root / 'supabase/migrations').glob('*.sql'))
    expected = [p.stem.split('_', 1) for p in local]
    actual = [[r['version'], r['name']] for r in rows]
    if len(local) != 44 or actual not in (expected, expected[:-1]):
        raise ValueError('migration_history_identity')
    present = len(actual) == 44
    text = boundary.source(root)
    if not present:
        if any(obj[k] is not None for k in ('function_oid', 'trigger_oid', 'migration_statements')):
            raise ValueError('unregistered_m44_objects')
        constraint = obj.get('constraint')
        if not constraint or constraint['type'] != 'c' or not constraint['validated'] or \
                boundary.ast('select '+constraint['expression']) != boundary.ast('select command_count>=0 and command_count<=128'):
            raise ValueError('migration_pending_constraint')
        return {'hosted': 43, 'local_selected': 44, 'm44_present': False,
                'pending': [boundary.FILE], 'identity': 'EXACT_43_PREFIX_M44_PENDING'}
    stored = obj['migration_statements']
    if not isinstance(stored, list) or boundary.ast(text) != boundary.ast(';\n'.join(stored)):
        raise ValueError('migration_registered_sql_changed')
    body = text.split('as $f$', 1)[1].split('$f$;', 1)[0].replace('\r\n', '\n')
    function = dict(body_sha=hashlib.sha256(body.encode()).hexdigest(), owner='postgres',
                    definer=False, path=['search_path=pg_catalog, pg_temp'],
                    public_execute=False, forbidden_execute=False)
    if obj['function'] != function or obj['function_oid'] is None:
        raise ValueError('migration_function_boundary')
    if obj['trigger'] != dict(type=27, enabled='O', function_matches=True, no_filter=True,
                              no_arguments=True, constraint='0') or obj['trigger_oid'] is None:
        raise ValueError('migration_trigger_boundary')
    constraint = obj['constraint']
    expression = re.search(r'check\((command_count>=0.*?)\);', text, re.S)[1]
    if not constraint or constraint['type'] != 'c' or not constraint['validated'] or \
            boundary.ast('select ' + constraint['expression']) != boundary.ast('select ' + expression):
        raise ValueError('migration_constraint_boundary')
    return {'hosted': 44, 'local_selected': 44, 'm44_present': True, 'pending': [],
            'identity': 'REGISTERED_SQL_AND_OBJECTS_MATCH',
            'local_raw_sha256': boundary.SOURCE_SHA,
            'registered_ast_sha256': sha(boundary.ast(';\n'.join(stored))),
            'local_ast_sha256': sha(boundary.ast(text)),
            'object_sha256': sha({k: v for k, v in obj.items() if k != 'migration_statements'}),
            'new_run_budget_supported': False,
            'budget_boundary': 'M44 exception belongs only to the old consumed run UUID'}


def attributable(before, after, native_between, cli_reserved=64):
    # Database-wide counters provide a conservative upper bound, not session proof.
    if before.get('track') != 'all' or after.get('track') != 'all':
        raise ValueError('numeric_tracking_incomplete')
    for sample in (before, after):
        keys = [r['queryid'] for r in sample['statements']]
        if len(set(keys)) != len(keys): raise ValueError('numeric_duplicate_identity')
    delta = compare(before, after, 0, between=native_between)
    observed = delta['numeric_calls_minus_reader']
    if observed < 0 or observed > cli_reserved:
        raise ValueError('cli_unattributed_capacity')
    if delta['temp_written']:
        raise ValueError('numeric_window_temp_writes_unattributed')
    return {'observed_noncollector_calls': observed, 'cli_confirmed_commands': None,
            'background_confirmed_commands': None, 'unattributed_calls': observed,
            'cli_capacity_reserved': cli_reserved, 'conservative_budget_charge': cli_reserved,
            'database_wide_not_session_bound': True, 'query_text_read': False,
            'temp_blocks_delta': delta['temp_written'], 'statement_deltas': delta['statements']}


class Reader:
    def __init__(self, runtime, folder, clock=time.monotonic):
        self.runtime, self.folder, self.clock = runtime, folder, clock
        self.started = clock(); self.commands = []; self.reserved = 64; self.closed = True
    def query(self, connection, phase, text):
        if self.clock() - self.started >= 540 or len(self.commands) + self.reserved + 1 >= 128:
            raise ValueError('diagnosis_command_or_time_budget')
        if text not in (GUARD, MIGRATIONS, OBJECTS, STATS, HEALTH, TX,
                        'BEGIN TRANSACTION READ ONLY', 'ROLLBACK'):
            raise ValueError('diagnosis_query_not_allowed')
        row = {'ordinal': len(self.commands)+1, 'phase': phase,
               'sql_sha256': statements(text)[0]['sha256'], 'confirmed': False}
        self.commands.append(row)
        cursor = connection.execute(text, prepare=False)
        data = cursor.fetchall() if cursor.description else []
        row['confirmed'] = True
        return data
    def capture(self, label):
        connection = self.runtime.connect(); self.closed = False
        begun = False; result = None
        try:
            self.query(connection, label+'_begin', 'BEGIN TRANSACTION READ ONLY'); begun = True
            guard = self.query(connection, label+'_identity', GUARD)[0]
            if guard['ro'] != 'on' or guard['db'] != 'postgres' or guard['role'] != 'postgres' or guard['ssl'] is not True:
                raise ValueError('diagnosis_readonly_identity')
            if self.runtime.environment == 'staging' and guard['instance_sha'] != INSTANCE:
                raise ValueError('diagnosis_project_instance')
            tx = self.query(connection, label+'_transaction', TX)[0]
            if tx['readonly'] != 'on': raise ValueError('diagnosis_transaction')
            rows = self.query(connection, label+'_history', MIGRATIONS)
            obj = self.query(connection, label+'_objects', OBJECTS)[0]['value']
            save(self.folder,label+'-metadata.json',{'history':rows,'objects':obj,'transaction':tx})
            result = identity(rows, obj)
            health = self.query(connection, label+'_health', HEALTH)[0]
            if health['io_wait'] or health['long_active']:
                raise ValueError('diagnosis_health')
            stats = self.query(connection, label+'_numeric', STATS)[0]['value']
            result.update(history=rows, transaction=tx, health=health, stats=stats)
        finally:
            try:
                if begun:
                    # The rollback slot is reserved even after the ordinary deadline.
                    row = {'ordinal':len(self.commands)+1,'phase':label+'_rollback',
                           'sql_sha256':statements('ROLLBACK')[0]['sha256'],'confirmed':False}
                    self.commands.append(row); connection.execute('ROLLBACK'); row['confirmed']=True
            finally:
                connection.close(); self.closed = True
                save(self.folder,label+'-protocol.json',{'commands':self.commands.copy(),'connection_closed':True})
        save(self.folder,label+'.json',result)
        return result


def paired_dry_run(reader, invoke):
    before = reader.capture('before')
    outcome = None
    try:
        outcome = invoke()
    except Exception as error:
        outcome = {'exit_code':None, 'dry_run':True, 'error_class':type(error).__name__,
                   'sqlstate':getattr(error,'sqlstate',None), 'reason':'sanitized'}
    finally:
        save(reader.folder, 'cli-dry-run.json', outcome)
        # No retry: this is the distinct mandatory after measurement, even on failure.
        after = reader.capture('after')
    return before, outcome, after


def main():
    sys.path.insert(0,str(HERE.parent/'controller_v1'))
    import jit_diagnose as j
    import migration_run
    folder = ROOT/'supabase/.temp'/('phase6e11-recovery-readonly-'+RUN_ID)
    archived = HERE/'receipts'/RUN_ID
    if disk(folder).exists() or disk(archived).exists(): raise ValueError('diagnosis_attempt_consumed')
    cli = pathlib.Path(os.environ['FMZ_SUPABASE_CLI'])
    if hashlib.sha256(cli.read_bytes()).hexdigest() != CLI_SHA: raise ValueError('diagnosis_cli_pin')
    source = {}
    for module in list(sys.modules.values()):
        path = pathlib.Path(getattr(module, '__file__', '') or '').resolve()
        if path.is_relative_to(ROOT) and path.suffix == '.py' and path.is_file():
            source[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for path in (ROOT/'supabase/migrations').glob('*.sql'):
        source[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    folder.mkdir()
    save(folder,'preregistration.json',{'run_id':RUN_ID,'project':PROJECT,'maximum_seconds':600,
        'maximum_sql':128,'native_capacity':32,'cli_capacity':64,'close_reserve':32,
        'jit_seconds':300,'collectors':1,'retries':0,'application_writes':0,
        'migration_apply':False,'selected_migrations':44,'sources':source,
        'old_run_remains_closed':'1c3bf7e7-bc78-40c5-9ac1-5ba3512ec66d'})
    token=journal=runtime=reader=None; granted=False
    result={'status':'NO_GO','phase':'management','application_writes':0,'auth_writes':0,
            'migration_apply':False,'automatic_retries':0}
    try:
        token=j.jit.sb.credential();journal=j.Journal(token,folder);journal.inspect()
        granted=True;journal.grant()
        connect=json.loads((j.m.c.CONNECT/'connect.json').read_text())
        runtime=NativeRuntime.staging(connect,token,j.m.c.CA,j.m.c.parameters)
        reader=Reader(runtime,folder)
        result['phase']='paired_dry_run'
        before,outcome,after=paired_dry_run(reader,
            lambda:migration_run.cli_run(cli,connect,j.m.c.CA,token,True))
        # Before ROLLBACK plus after BEGIN/GUARD/TX/HISTORY/OBJECTS/HEALTH.
        accounting=attributable(before['stats'],after['stats'],native_between=7)
        save(folder,'accounting.json',accounting)
        if outcome['exit_code'] != 0 or outcome.get('migration_files')!=before['pending']:
            raise ValueError('diagnosis_dry_run_pending_mismatch')
        if not before['pending'] and not outcome['up_to_date']:
            raise ValueError('diagnosis_dry_run_not_empty')
        stable=lambda v:{k:x for k,x in v.items() if k not in ('stats','transaction','health')}
        if stable(before)!=stable(after): raise ValueError('diagnosis_metadata_drift')
        result.update(status='READ_ONLY_MIGRATION_PASS_PENDING_CLOSURE',phase='closure',
            migrations=after['hosted'],selected_local=44,pending=after['pending'],
            identity=after['identity'],metadata_before_sha256=sha(stable(before)),
            metadata_after_sha256=sha(stable(after)),databehoud_scope='read-only metadata; no full data fingerprint',
            native_confirmed=sum(c['confirmed'] for c in reader.commands),
            reserved_sql=len(reader.commands)+reader.reserved,cli_accounting=accounting,
            new_run_budget_supported=after.get('new_run_budget_supported'))
    except Exception as error:
        result.update(error_class=type(error).__name__,sqlstate=getattr(error,'sqlstate',None),
            reason=str(error) if re.fullmatch(r'[a-zA-Z0-9_]+',str(error)) else 'sanitized')
    finally:
        if granted:
            try:journal.close();result['jit_revoked']=True
            except Exception as error:result.update(status='NO_GO',jit_revoked=False,closure_error_class=type(error).__name__)
        if runtime:runtime.clear()
        if journal:journal.token=None
        token=None
        if reader:result['native_protocol']={'attempted':len(reader.commands),'confirmed':sum(c['confirmed'] for c in reader.commands),'closed':reader.closed}
        if result['status']=='READ_ONLY_MIGRATION_PASS_PENDING_CLOSURE' and result.get('jit_revoked'):
            result['status']='READ_ONLY_MIGRATION_TECHNICAL_PASS'
        result.update(production_touched=False,external_ai_calls=0,real_member_ai=False)
        save(folder,'result.json',result)
    print(json.dumps({'status':result['status'],'phase':result['phase'],'reason':result.get('reason'),
        'evidence':str(folder),'jit_revoked':result.get('jit_revoked'),'migrations':result.get('migrations')}))
    return 0 if result['status']=='READ_ONLY_MIGRATION_TECHNICAL_PASS' else 2


if __name__=='__main__':sys.exit(main())
