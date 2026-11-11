"""Versioned history47/local48 attestation; never rewrites canonical history.

Historical 44 DB hashes remain pinned. Added-source statements are inspected in
memory against their exact bound ASTs; only technical hashes leave this module.
"""
import copy
import json
import pathlib
import re
import time

import history_pin
from admission_quota_readonly import parser, strip_locations
from integral_stream import GUARD
from runtime_budget import BudgetStop
from sql_protocol import single
from .compiler import require, sha, canonical, read_source

MIGRATIONS = """select version,name,
 encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex') sql_sha,
 case when version=any($1::text[]) then statements else null end source_statements
 from supabase_migrations.schema_migrations order by version"""
M45 = 'supabase/migrations/20261018070231_phase6e11_recovery_run_quota.sql'
M45_SHA = '64498fa910966497e92705dcf66b76f40c40f01c006aed98c191ce109dd88635'
APP = '_offline/phase6e_server_v1/supabase/migrations/'


def ast(text):
    return [strip_locations(n.stmt()) for n in parser().parse_sql(text)]


class CaseHistory:
    def __init__(self, root, sources, *, local_version, local_sql):
        self.root = pathlib.Path(root)
        names = sorted(n for n in sources if n.startswith('supabase/migrations/') and n.endswith('.sql'))
        app = sorted(n for n in sources if n.startswith(APP) and n.endswith('.sql'))
        require(len(names) == 45 and len(app) == 2 and names[-1] == M45, 'case_history_source_inventory')
        self.bound = {}
        for name in names+app:
            raw = read_source(root,name)
            require(sha(raw) == sources[name], 'case_history_source_changed')
            version,label = pathlib.PurePosixPath(name).stem.split('_',1)
            require(version not in self.bound, 'case_history_duplicate_source')
            self.bound[version] = dict(name=label,raw_sha256=sha(raw),ast=ast(raw.decode('utf-8')))
        require(sources[M45] == M45_SHA and re.fullmatch('[0-9]{14}',local_version)
            and local_version > max(self.bound), 'case_history_local_identity')
        pin=history_pin.load()
        for name,expected in pin['sources'].items():
            require(sha(read_source(root,name)) == expected, 'case_history_historical_source')
        self.historical = copy.deepcopy(pin['history']['disposable'])
        require(len(self.historical) == 44, 'case_history_pin_count')
        self.local_version=local_version
        self.bound[local_version] = dict(name='disposable_case_quota_v1',
            raw_sha256=sha(local_sql.encode('ascii')),ast=ast(local_sql))
        historical={r['version'] for r in self.historical}
        self.inspect_versions=sorted(set(self.bound)-historical)
        require(len(self.inspect_versions)==4, 'case_history_extra_sources')
        self.before=None;self.after=None

    def attest(self, rows, *, appended):
        require(type(rows) is list and len(rows)==(48 if appended else 47), 'case_history_count')
        expected=sorted(set(self.bound)-({self.local_version} if not appended else set()))
        require([r.get('version') for r in rows]==expected, 'case_history_identity')
        safe=[]
        for row in rows:
            require(set(row)=={'version','name','sql_sha','source_statements'}
                and re.fullmatch('[a-f0-9]{64}',row['sql_sha']), 'case_history_row')
            source=self.bound[row['version']]
            require(row['name']==source['name'], 'case_history_name')
            text=row['source_statements']
            if row['version'] in self.inspect_versions:
                require(type(text) is list and all(type(s) is str for s in text)
                    and sum(len(s.encode('utf-8')) for s in text)<=1048576, 'case_history_statement_bound')
                require(sha('\n'.join(text).encode('utf-8'))==row['sql_sha']
                    and ast(';\n'.join(text))==source['ast'], 'case_history_statement_mismatch')
            else:require(text is None, 'case_history_historical_raw_forbidden')
            safe.append({k:row[k] for k in ('version','name','sql_sha')})
        historical_versions={r['version'] for r in self.historical}
        require([r for r in safe if r['version'] in historical_versions]==self.historical,
                'case_history_historical_drift')
        if appended:
            require(self.before is not None and [r for r in safe if r['version']!=self.local_version]==self.before,
                    'case_history_prefix_drift')
            if self.after is not None:require(safe==self.after, 'case_history_post_drift')
            self.after=copy.deepcopy(safe)
        else:
            require(self.after is None, 'case_history_backward')
            if self.before is not None:require(safe==self.before, 'case_history_pre_drift')
            self.before=copy.deepcopy(safe)
        return dict(migrations=safe,history_count=len(safe),historical44_pin=history_pin.PIN_SHA,
            sql_history_sha256=sha(canonical(safe)),source_ast_validated_versions=self.inspect_versions if appended else self.inspect_versions[:-1],
            appended_local_candidate=appended,canonical_migration_added=False,hosted_admission=False)

    def check_observed(self, rows):
        require(self.after is not None and rows==self.after,'case_history_lifecycle_drift')


def preflight(runtime, meter, history, save):
    """Exactly four commands; only new, versioned history query differs."""
    require(runtime.environment=='disposable_ci' and not meter.closed and not meter.stopped
        and not meter.phases['preflight'], 'case_history_preflight_scope')
    connection=None;trace=[];begin=False;closed=False;rolled_back=False;failure=None;attested=None
    def query(sql,values=()):
        nonlocal begin
        digest=single(sql)['sha256'];safety=sql=='ROLLBACK' and meter.stopped
        ticket=meter.safety('rollback_reader',1) if safety else meter.charge('preflight',1,action='preflight_'+digest)
        row=dict(sql_sha256=digest,meter_ticket=ticket,meter_phase='safety' if safety else 'preflight',
            dispatch_attempted=True,confirmed=False)
        trace.append(row)
        if sql=='BEGIN TRANSACTION READ ONLY':begin=True
        from integral_ci import bind_parameters
        bound,params=bind_parameters(sql,values)
        cursor=connection.execute(bound,params)
        rows=cursor.fetchall() if cursor.description else []
        if safety:meter.confirm_safety(ticket)
        else:meter.confirm(ticket)
        row['confirmed']=True
        return rows
    try:
        connection=runtime.connect()
        query('BEGIN TRANSACTION READ ONLY')
        identity=query(GUARD)[0]
        require(identity['ro']=='on' and identity['db']=='postgres' and identity['role']=='postgres'
            and identity['ssl'] is True,'case_history_preflight_identity')
        attested=history.attest(query(MIGRATIONS,(history.inspect_versions,)),appended=False)
    except BaseException as error:
        failure=error;meter.stop('case_history_preflight_failed')
    finally:
        if begin:
            try:query('ROLLBACK');rolled_back=True
            except BaseException as error:
                meter.stop('case_history_preflight_rollback_failed')
                if failure is None:failure=error
                else:failure.add_note('case_preflight_rollback_secondary:'+type(error).__name__)
        if connection is not None:
            try:connection.close();closed=True
            except BaseException as error:
                if failure is None:failure=error
                else:failure.add_note('case_preflight_close_secondary:'+type(error).__name__)
        value=dict(commands=trace,migrations=(attested or {}).get('migrations',[]),history=attested,
            begin_attempted=begin,rollback_confirmed=rolled_back,connection_closed=closed,
            metered_before_dispatch=True,hosted_calls=0,complete=failure is None and rolled_back and closed)
        try:save('integral-preflight.json',value)
        except BaseException as error:
            meter.stop('case_history_receipt_unconfirmed')
            if failure is None:failure=error
            else:failure.add_note('case_preflight_save_secondary:'+type(error).__name__)
    if failure is not None:raise failure
    return value
