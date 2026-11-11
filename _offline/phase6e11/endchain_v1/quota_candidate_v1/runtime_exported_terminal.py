"""Independent original-byte terminal inspection. Never executes artifact code.

An intact archive or producer PASS is not semantic proof. This collector checks
the available original contracts and reports missing measurement/authority edges.
It deliberately cannot promote an incomplete domain to CASE_TERMINAL_VERIFIED.
"""
import hashlib
import dataclasses
import json
import math
import pathlib
import re
import tempfile
import types
import uuid

PREFIX = '_offline/phase6e11/endchain_v1/'
OWN = PREFIX + 'quota_candidate_v1/'
SELF = OWN + 'runtime_exported_terminal.py'
PARENT = '11a909f4-7113-424a-aa4b-ce9964720a3e'
OLD = '6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'
CASES = ('normal','pre_migration','post_migration','mid_auth','controller','route_a',
    'route_b','restore','lost_response','duplicate','timeout','partial_fixture_cleanup',
    'cleanup_failure','final_check_failure','closure_failure')
MAX_RECORD = 2_000_000
MAX_TOTAL = 16_000_000


class Invalid(ValueError):
    pass


class Missing(ValueError):
    pass


def need(value, code):
    if not value:
        raise Invalid(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()


def decode(raw):
    def unique(items):
        result = {}
        for key, value in items:
            need(key not in result,'duplicate_json_key')
            result[key] = value
        return result
    try:
        value = json.loads(raw,object_pairs_hook=unique,
            parse_constant=lambda _:need(False,'nonfinite_json'))
    except (UnicodeError,json.JSONDecodeError,RecursionError):
        raise Invalid('malformed_json') from None
    need(type(value) is dict,'json_object')
    return value


def path_name(name):
    need(type(name) is str and 0 < len(name) <= 240
        and re.fullmatch('[A-Za-z0-9_./-]+',name)
        and all(p not in ('','.','..') for p in name.split('/')),'path')
    for part in name.split('/'):
        need(not re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',part),'device_path')
    return name


class Originals:
    def __init__(self, originals, refs):
        need(type(originals) is dict and type(refs) is list and 0 < len(refs) <= 4096,'original_inventory')
        self.values = originals
        self.refs = {}
        self.used = set()
        folded = set()
        for ref in refs:
            need(type(ref) is dict and set(ref)=={'path','sha256','bytes'},'original_ref')
            name = path_name(ref['path'])
            need(name.casefold() not in folded,'original_alias')
            folded.add(name.casefold())
            need(type(ref['bytes']) is int and 0 < ref['bytes'] <= MAX_RECORD,'original_size')
            need(type(ref['sha256']) is str and re.fullmatch('[a-f0-9]{64}',ref['sha256']),'original_digest')
            raw = originals.get(name)
            need(type(raw) is bytes and len(raw)==ref['bytes'] and sha(raw)==ref['sha256'],'original_bytes')
            self.refs[name] = ref
        need(set(originals)==set(self.refs) and sum(r['bytes'] for r in refs)<=MAX_TOTAL,'original_exact_inventory')

    def raw(self,name,ref=None):
        path_name(name)
        if name not in self.refs:
            raise Missing(name)
        if ref is not None:
            need(type(ref) is dict and ref.get('path')==name and ref.get('sha256')==self.refs[name]['sha256'],'reference_hash')
            for key in ('bytes','size'):
                need(key not in ref or type(ref[key]) is int and ref[key]==self.refs[name]['bytes'],'reference_size')
        self.used.add(name)
        return self.values[name]

    def obj(self,name,ref=None):
        return decode(self.raw(name,ref))


class Trusted:
    def __init__(self,root,sources):
        self.root = pathlib.Path(root).resolve(strict=True)
        need(type(sources) is dict and 0<len(sources)<=4096,'trusted_sources')
        self.sources = sources
        need(sha(pathlib.Path(__file__).read_bytes())==sources.get(SELF),'loaded_collector_source')
        self.raw(SELF)

    def raw(self,name):
        path_name(name)
        need(name in self.sources,'trusted_source_missing')
        file = self.root/name
        need(file.resolve(strict=True).is_relative_to(self.root)
            and all(not p.is_symlink() and not getattr(p,'is_junction',lambda:False)()
                    for p in (file,*file.parents)),'trusted_source_escape')
        need(file.stat().st_size<=8_000_000,'trusted_source_size')
        raw = file.read_bytes()
        need(sha(raw)==self.sources[name],'trusted_source_changed')
        return raw

    def module(self,name):
        # Main keeps this same session active for the entire original replay.
        loader = globals().get('__trusted_imports__')
        need(loader is not None, 'trusted_import_session_required')
        return loader.bound_module(name, self.root, self.sources)


def source_binding(value,trusted):
    need(type(value) is dict and value.get('status')=='SELECTED_MODULE_SOURCE_BINDING_PASS','source_binding')
    rows = value.get('modules')
    need(type(rows) is list and rows and type(value.get('selected_module_count')) is int
        and value['selected_module_count']==len(rows),'source_binding_count')
    seen = set()
    for row in rows:
        name = path_name(row['relative_path'])
        need(name not in seen and trusted.sources.get(name)==row.get('candidate_sha256'),'source_binding_hash')
        seen.add(name)
        raw = trusted.raw(name)
        need(row.get('canonicalization') in ('byte-exact','CRLF-to-LF-only'),'source_binding_canonicalization')
        need(type(row.get('actual_sha256')) is str and re.fullmatch('[a-f0-9]{64}',row['actual_sha256']),'source_binding_actual_hash')
        if row['canonicalization']=='byte-exact':
            need(row['actual_sha256']==row['candidate_sha256'],'source_binding_raw_hash')
        else:
            lf = raw.replace(b'\r\n',b'\n')
            need(row['actual_sha256'] in {sha(raw),sha(lf),sha(lf.replace(b'\n',b'\r\n'))},
                'source_binding_line_ending_hash')


def protocol(evidence,folder,plan,*,run_id,scope_sha,trusted,component):
    rows = {}
    for ordinal,(phase,text) in enumerate(plan,1):
        record = evidence.obj(folder+'/query-%02d-%s.json'%(ordinal,phase))
        charge = evidence.obj(folder+'/charge-%02d.json'%ordinal)
        event = {'ordinal':ordinal,'phase':phase,'sql_sha256':sha(text.encode()),'confirmed':True}
        need(canonical(charge)==canonical({**event,'confirmed':False}),'protocol_precharge')
        need(canonical(record.get('protocol'))==canonical(event),'protocol_return')
        need(record.get('format')=='c-query-observation-v1' and record.get('case_run')==run_id
            and record.get('component')==component and record.get('phase')==phase
            and record.get('scope_sha256')==scope_sha,'protocol_binding')
        source_binding(record.get('source_binding'),trusted)
        values = record.get('rows')
        need(type(values) is list and len(values)<=1001 and sha(canonical(values))==record.get('rows_sha256'),'protocol_rows')
        need(type(record.get('raw_rows_sha256')) is str and re.fullmatch('[a-f0-9]{64}',record['raw_rows_sha256']),'protocol_raw_commitment')
        need(record.get('query_io')=={'observed':False,'reason':'not_instrumented_by_this_dispatch'},'protocol_io_contract')
        rows[phase] = values
    actual = {name for name in evidence.refs if name.startswith(folder+'/query-')}
    expected = {folder+'/query-%02d-%s.json'%(i,p) for i,(p,_) in enumerate(plan,1)}
    need(actual==expected,'protocol_extra_or_missing_query')
    return rows


def profile(evidence,trusted,binding,isolation):
    m = trusted.module('admission_auth_runtime_profile')
    folder = 'registered-auth-runtime-profile-private'
    identity = {k:isolation[k] for k in ('pg_system_identifier','database_oid')}
    bound = evidence.obj(folder+'/binding.json')
    need(bound.get('case_run')==binding['run_id'] and bound.get('target_sha256')==sha(canonical(identity)),'profile_binding')
    source_binding(bound.get('source_binding'),trusted)
    rows = protocol(evidence,folder,m.PLAN,run_id=binding['run_id'],scope_sha=sha(canonical(identity)),
        trusted=trusted,component='auth_runtime_profile')
    before = m.metadata(rows['before_metadata'],identity,readonly=False)
    after = m.metadata(rows['after_metadata'],identity,readonly=False)
    witness = m.metadata(rows['witness_metadata'],identity,readonly=True)
    m.privileges(rows['before_privileges'],before=True)
    m.privileges(rows['witness_privileges'],before=False)
    m.delta(before,after,fresh=False)
    m.delta(before,witness,fresh=True)
    result = evidence.obj(folder+'/result.json')
    need(result.get('status')=='LOCALONLY_RUNTIME_CAPABILITY_REDUCED'
        and result.get('commit_confirmed') is True and result.get('commit_unknown') is False,'profile_terminal')
    return {'status':'PROFILE_ORIGINALS_REPLAYED','queries':len(m.PLAN),
        'missing':['profile_query_io_unmeasured','profile_driver_numeric_originals']}


def root_original(evidence,expected_binding):
    index = evidence.obj('root-original-index.json')
    need(index.get('format')=='admission-root-original-index-v1','root_index')
    refs = index.get('members')
    need(type(refs) is list and 1<=len(refs)<=15,'root_members')
    need([r.get('path') for r in refs]==['root-original-%02d.txt'%i for i in range(len(refs))],'root_member_order')
    raw = b''.join(evidence.raw(r['path'],r) for r in refs)
    need(type(index.get('payload_bytes')) is int and len(raw)==index['payload_bytes']
        and sha(raw)==index.get('payload_sha256'),'root_payload')
    value = decode(raw)
    need(value.get('format')=='admission-root-original-evidence-v1'
        and canonical(value.get('binding'))==canonical(expected_binding)
        and index.get('binding_sha256')==sha(canonical(expected_binding)),'root_binding')
    register = value.get('register')
    need(type(register) is dict and register.get('full_register_sha256')==index.get('register_sha256')
        and sha(canonical({k:v for k,v in register.items() if k!='full_register_sha256'}))==index['register_sha256'],'root_register_digest')
    need(value.get('program')==register.get('executable_program'),'root_program')
    return value


def fixtures(evidence,trusted,binding,isolation):
    m = trusted.module('quota_candidate_v1.runtime_registered_fixture_closeout')
    for module in m._modules():
        relative = pathlib.Path(module.__file__).resolve().relative_to(trusted.root).as_posix()
        trusted.raw(relative)
    folder = 'registered-fixture-closeout-private'
    registration = evidence.obj(folder+'/registration.json')
    need(registration.get('case_run')==binding['run_id']
        and registration.get('before_prefix_and_fixture_writes') is True
        and registration.get('ownership_is_not_inferred_from_current_rows') is True,'fixture_registration')
    source_binding(registration.get('source_binding'),trusted)
    result = evidence.obj(folder+'/result.json')
    physical_only = result.get('original_commit_unknown')
    need(type(physical_only) is bool,'fixture_original_commit_state')
    plan = m.protocol_plan(physical_only=physical_only)
    rows = protocol(evidence,folder,plan,run_id=binding['run_id'],
        scope_sha=sha(canonical(registration['scope'])),trusted=trusted,component='registered_fixture')
    migration_sources = {n:h for n,h in trusted.sources.items()
        if n.startswith('supabase/migrations/') and n.endswith('.sql')}
    for name in migration_sources:
        trusted.raw(name)
    # Existing source_contract is a local file parser, not a DB or authority
    # capability. Its metadata-only view contains the externally trusted map.
    with tempfile.TemporaryDirectory(prefix='terminal-source-contract-') as temporary:
        out = pathlib.Path(temporary)
        (out/'candidate.json').write_bytes(canonical({'sources':migration_sources}))
        contract = m.scope.source_contract(types.SimpleNamespace(sources=trusted.root,out=out))
    for i,(phase,_) in enumerate(plan,1):
        original = evidence.obj(folder+'/query-%02d-%s.json'%(i,phase))
        need(original.get('migration_sources_sha256')==sha(canonical(contract['hashes'])),'fixture_migration_sources')
    held = m.scope.validate({phase:rows[phase] for phase,_ in m.scope.QUERIES},contract,before=False)
    need(held['cluster_id']==isolation['pg_system_identifier']
        and str(held['datid'])==str(isolation['database_oid']),'fixture_target')
    def value(phase):
        need(len(rows[phase])==1 and set(rows[phase][0])=={'value'},'fixture_scalar')
        return rows[phase][0]['value']
    owned = m.validate_owned(value('ownership_inventory'))
    need(not physical_only or owned==[],'fixture_unknown_commit_replay')
    before = value('registry_before')
    need(type(before) is dict and set(before)=={'identities','operators'},'fixture_registry')
    identities = before['identities']
    need(type(identities) is list and len(identities)==3,'fixture_actors')
    ids = {row['role']:row['id'] for row in identities}
    need(set(ids)==set(m.parent.ROLES) and len(set(ids.values()))==3,'fixture_actor_roles')
    for actor in ids.values():
        parsed = uuid.UUID(actor)
        need(str(parsed)==actor and parsed.version==4 and actor not in (PARENT,OLD),'fixture_fresh_actor')
    need(registration.get('actor_hashes')=={role:sha(actor.encode()) for role,actor in ids.items()},'fixture_actor_hashes')
    expected = m.parent.expected_registry(ids)
    need(all(m.parent.same_rows(before[k],expected[k]) for k in expected),'fixture_registry_seed')
    deleted = 0
    for table in (() if physical_only else m.sql.ORDER):
        wanted = [{k:v for k,v in row.items() if k!='scope_ok'} for row in owned if row['table']==table]
        need(m.parent.same_rows(value('delete_'+table),wanted),'fixture_delete_multiset')
        deleted += len(wanted)
    need(m.parent.same_rows(rows['delete_operator'],expected['operators'])
        and m.parent.same_rows(rows['delete_identities'],expected['identities']),'fixture_registry_delete')
    for phase in ('fixture_zero','absence_fixture'):
        need(m.engine.validate_rows(value(phase))==[],'fixture_not_zero')
    for phase in ('registry_after','absence_registry'):
        need(value(phase)=={'identities':[],'operators':[]},'fixture_registry_not_zero')
    current = m.scope.one(rows['absence_session'])
    need(all(current.get(k) is True for k in ('pg17','statement_bounded','lock_bounded',
        'no_prepared','tracked','fresh','origin','privileged')) and all(current.get(k)==held[k]
        for k in ('cluster_id','postmaster_start','datid')),'fixture_absence_session')
    need(result.get('registry_commit_confirmed') is True and result.get('registry_commit_unknown') is False
        and result.get('physical_zero') is True and result.get('registry_absence_confirmed') is True
        and type(result.get('returned_fixture_deletes')) is int and result['returned_fixture_deletes']==deleted,
        'fixture_result')
    return {'status':'FIXTURE_ORIGINALS_REPLAYED','queries':len(plan),'deleted_rows':deleted,
        'physical_only':physical_only,'missing':['fixture_query_io_unmeasured',
            'fixture_connection_implicit_commands_unmeasured','fixture_registered_ownership_root_link']}


def streams(evidence,trusted):
    module = trusted.module('integral_stream')
    trusted.raw(PREFIX+'integral_io.py')
    own_sha = sha(trusted.raw(OWN+'runtime_stream.py'))
    counts = {}
    for label in ('before','before_cleanup','after_cleanup'):
        prefix = 'integral-stream-'+label
        summary = evidence.obj(prefix+'.json')
        need(summary.get('source_sha256')==own_sha and summary.get('label')==label,'stream_source')
        profiles = summary.get('profiles')
        need(type(profiles) is list and 3<=len(profiles)<=30,'stream_profile_bound')
        bindings = module.UtilityBindings()
        previous = None
        for i,expected_profile in enumerate(profiles):
            base = prefix+'-utility-%03d'%i
            before = evidence.obj(base+'-before.json')
            after = evidence.obj(base+'-after.json')
            sample_shape(before.get('sample'))
            sample_shape(after.get('sample'))
            bound = before.get('binding')
            need(type(bound) is dict and set(bound)=={'sql_sha256','reader_queryid'}
                and after.get('binding')==bound,'stream_binding')
            if previous is not None:
                need(canonical(previous)==canonical(before['sample']),'stream_sample_chain')
            observed = bindings.observe(bound['sql_sha256'],before['sample'],after['sample'],bound['reader_queryid'])
            need(observed.get('unambiguous') is True
                and canonical(evidence.obj(base+'-attribution.json'))==canonical({'binding':bound,**observed}),'stream_attribution')
            recomputed = module.delta(before['sample'],after['sample'],
                {observed['queryid']:1,bound['reader_queryid']:1})
            need(canonical(recomputed)==canonical(expected_profile)
                and canonical(evidence.obj(prefix+'-io-%03d.json'%i))==canonical(recomputed),'stream_numeric_replay')
            need(recomputed['own_wal_bytes']==0 and recomputed['own_temp_written']==0
                and all(row['exec_ms']<=2500 for row in recomputed['queries']),'stream_strict_io')
            background = module.other_load(before['sample'],after['sample'],observed)
            need(canonical(evidence.obj(base+'-other-load.json'))==canonical(background),'stream_background')
            bindings.confirm(bound['sql_sha256'],observed)
            previous = after['sample']
        counts[label] = len(profiles)
    return {'status':'STREAM_NUMERIC_ORIGINALS_REPLAYED','profiles':counts,
        'missing':['stream_original_closing_explain_plans','lifecycle_queryio_original_samples',
            'workflow_queryio_original_samples','fixture_queryio_original_samples']}


def sample_shape(sample):
    """Reject ambiguous rows before legacy delta builds a query-ID dictionary."""
    need(type(sample) is dict and set(sample)=={'reset','dealloc','statements','background','health'},
        'io_sample_shape')
    need(type(sample['reset']) is str and sample['reset']
        and type(sample['dealloc']) is int and sample['dealloc']>=0,'io_sample_reset')
    background,health = sample['background'],sample['health']
    need(type(background) is dict and set(background)=={'temp_bytes','reset'}
        and type(background['reset']) is str and background['reset']
        and type(background['temp_bytes']) is int and background['temp_bytes']>=0,'io_background')
    need(type(health) is dict and set(health)=={'io_wait','long_active'}
        and all(type(v) is int and v>=0 for v in health.values()),'io_health')
    rows = sample['statements']
    need(type(rows) is list and len(rows)<=10000,'io_rows')
    seen = set()
    for row in rows:
        need(type(row) is dict and set(row)=={'queryid','calls','since','temp_read','temp_written',
            'wal','wal_records','wal_fpi','exec_ms'},'io_row_shape')
        qid = row['queryid']
        need(type(qid) is str and re.fullmatch('-?(?:0|[1-9][0-9]*)',qid)
            and -(2**63)<=int(qid)<2**63 and str(int(qid))==qid and qid not in seen,'io_queryid')
        seen.add(qid)
        need(type(row['since']) is str and row['since'],'io_since')
        need(all(type(row[k]) is int and row[k]>=0 for k in ('calls','temp_read','temp_written')),
            'io_integer_counter')
        need(all(type(row[k]) is str and re.fullmatch('0|[1-9][0-9]*',row[k])
            for k in ('wal','wal_records','wal_fpi')),'io_wal_counter')
        need(type(row['exec_ms']) in (int,float) and math.isfinite(row['exec_ms'])
            and row['exec_ms']>=0,'io_time')


def root_replay(evidence,trusted,binding,terminal,register):
    """Rebuild authority from collector source; archive registers are comparison only."""
    runtime = trusted.module('admission_budget_root_runtime')
    rebuilt = runtime.build_root_register(trusted.root,runtime_dir=trusted.root/OWN)
    need(canonical(rebuilt)==canonical(register),'root_source_register_changed')
    keys = ('bound_complete','total_local_ci_upper_bound','total_hosted_equivalent_upper_bound',
        'hosted_limit','source_inventory_complete','missing_costs')
    result = {key:rebuilt[key] for key in keys}
    result['missing'] = list(rebuilt['missing_costs'])
    # A complete graph is a precondition, not something the collector infers
    # from a closed journal or successful component receipts.
    if rebuilt['bound_complete'] is not True:
        result['status'] = 'ROOT_SOURCE_BOUND_INCOMPLETE'
        result['missing'].append('root_source_bound_incomplete')
        return result
    replay = trusted.module('admission_budget_root_replay')
    refs = {key:terminal[key] for key in ('evidence_refs','journal_refs')}
    for group in refs.values():
        for ref in group:
            evidence.raw(ref['path'],ref)
    verified = replay.verify_exported_root(evidence.values,trusted_root=rebuilt,
        expected_sources=rebuilt['source_hashes'],binding=binding,root_refs=refs)
    need(verified.get('status')=='NUMERIC_ACCOUNTING_REPLAYED'
        and canonical(verified.get('binding'))==canonical(binding),'root_replay_result')
    result['status'] = 'NUMERIC_ACCOUNTING_REPLAYED'
    result['accounting'] = verified
    return result


def bootstrap(evidence,trusted,payloads,case,source_commit,ci_run,candidate_sha256):
    module = trusted.module('admission_matrix_bootstrap')
    combined = dict(payloads)
    for name,raw in evidence.values.items():
        need(name not in combined or combined[name]==raw,'bootstrap_payload_collision')
        combined[name] = raw
    result = module.verify_bootstrap_case(combined,case_name=case['case_name'],
        source_commit=source_commit,ci_run=ci_run,candidate_sha256=candidate_sha256,
        expected_sources=trusted.sources,trusted_root=trusted.root)
    need(result.get('status')=='BOOTSTRAP_ABSENCE_VERIFIED'
        and result.get('run_id')==case['run_id'] and result.get('case_pass') is False,
        'bootstrap_absence_result')
    for ref in result['evidence_refs']:
        if ref['path'] in evidence.refs:
            evidence.raw(ref['path'],ref)
    result['missing'] = ['bootstrap_numeric_prefix_and_driver_original_replay',
        'final_platform_process_closure']
    return result


def root_chains(evidence,register_sha,refs):
    need(type(refs) is list and 1<=len(refs)<=32,'root_journal_refs')
    seen = set()
    journals = []
    for ref in refs:
        name = ref.get('path')
        need(name not in seen,'root_journal_duplicate')
        seen.add(name)
        raw = evidence.raw(name,ref)
        lines = raw.splitlines(keepends=True)
        need(lines and len(lines)<=10000 and all(line.endswith(b'\n') for line in lines),'root_journal_lines')
        prior = b''
        totals = [0,0,0]
        stopped = closed = False
        events = {}
        for sequence,line in enumerate(lines,1):
            row = decode(line)
            need(line==canonical(row)+b'\n' and type(row.get('sequence')) is int
                and row['sequence']==sequence and row.get('register_sha256')==register_sha
                and row.get('previous_bytes_sha256')==sha(prior),'root_journal_chain')
            need(type(row.get('stopped')) is bool and type(row.get('closed')) is bool
                and not closed and (not stopped or row['stopped']),'root_journal_latch')
            values = [row.get(k) for k in ('reserved_consumed','observed_sql_commands','hosted_equivalent_reserved')]
            need(all(type(v) is int and v>=old for v,old in zip(values,totals))
                and values[2]<=2349,'root_journal_numeric')
            event = row.get('event')
            if event is not None:
                ordinal = row.get('event_ordinal')
                need(type(ordinal) is int and 0<=ordinal<=len(events) and type(event) is dict,'root_journal_event')
                if ordinal not in events:
                    need(event.get('state')=='precharged' and event.get('numeric_confirmed') is False,'root_precharge_first')
                else:
                    old = events[ordinal]
                    for key in ('command_id','node_id','units','reserve_after','hosted_units','hosted_reserve_after','domain'):
                        need(canonical(event.get(key))==canonical(old.get(key)),'root_event_mutation')
                    need(old.get('state') not in ('unknown_consumed','overrun') or event==old,'root_unknown_reclassified')
                events[ordinal] = event
            totals,stopped,closed = values,row['stopped'],row['closed']
            prior += line
        need(closed,'root_journal_not_closed')
        unknown = [i for i,event in events.items() if event.get('state') not in
            ('confirmed','fault_numeric_confirmed','covered_by_numeric_union')]
        journals.append({'path':name,'records':len(lines),'events':len(events),
            'reserved_consumed':totals[0],'observed_sql_commands':totals[1],
            'hosted_equivalent_reserved':totals[2],'unknown_event_ordinals':unknown})
    return journals


def auth_originals(evidence,case,binding):
    terminal = evidence.obj(case['auth_terminal_ref']['path'],case['auth_terminal_ref'])
    need(canonical(terminal.get('binding'))==canonical(binding),'auth_binding')
    refs = terminal.get('evidence_refs')
    need(type(refs) is list and refs,'auth_refs')
    for ref in refs:
        evidence.raw(ref['path'],ref)
    close = evidence.obj(case['auth_closeout_ref']['path'],case['auth_closeout_ref'])
    need(close.get('kind')=='closeout','auth_closeout_kind')
    engine = close.get('cleanup')
    need(type(engine) is dict and type(engine.get('retained_journal')) is dict,'auth_engine')
    entries = engine['retained_journal'].get('files')
    need(type(entries) is dict and entries,'auth_retained_inventory')
    for name,item in entries.items():
        raw = evidence.raw('auth-registered-bootstrap-engine-private/'+path_name(name),
            {'path':'auth-registered-bootstrap-engine-private/'+name,'sha256':item['sha256'],'bytes':item['bytes']})
        need(canonical(decode(raw))==canonical(item['content']),'auth_retained_content')
    # These counters/process observations are not currently exported by B's
    # normal parent engine. Summary booleans cannot supply their missing bytes.
    return {'status':'AUTH_ORIGINAL_INVENTORY_BOUND','records':len(refs),
        'original_exception_class':close.get('original_exception_class'),
        'missing':['parent_auth_raw_before_after_stats','parent_auth_exact_session_ownership_originals',
            'parent_auth_final_process_backend_originals']}


def worker(evidence,trusted,case,binding):
    module = trusted.module('quota_candidate_v1.exported_worker')
    result = module.verify_exported_worker(evidence.values,case=case['case_name'],binding=binding,
        expected_sources=trusted.sources,trusted_root=trusted.root)
    need(type(result) is module.WorkerVerification,'worker_verifier_result_type')
    value = dataclasses.asdict(result)
    if result.status=='INVALID_EVIDENCE':
        raise Invalid('worker_original_semantics')
    if result.status=='MISSING_EVIDENCE':
        return {'status':result.status,'missing':['worker:'+n for n in result.missing]}
    need(result.status=='VERIFIED_COMPONENT','worker_verifier_status')
    observed=trusted.module('quota_candidate_v1.runtime_worker_evidence')
    observed.validate_wait(evidence.obj('registered-worker-wait.json'),binding,case['case_name'],
        normal=case['case_name']=='normal')
    exported=evidence.obj('case-worker-export.json')
    for key,name in (('workflow_wait_ref','workflow-worker-wait.json'),
                     ('workflow_worker_result_ref','case-workflow-worker-result.json')):
        ref=exported.get(key)
        if ref is None:
            need(case['case_name']!='normal','worker_inner_original_missing')
            continue
        original=evidence.obj(name,ref)
        if key=='workflow_wait_ref':
            observed.validate_wait(original,binding,case['case_name'],
                normal=case['case_name']=='normal',kind='workflow')
        else:
            observed.validate_result(original,'workflow')
            if case['case_name']=='normal':
                need(original.get('status')=='LOCAL_COMPOSED_71_PASS'
                    and all(type(original.get(k)) is int and original[k]==v
                        for k,v in (('pairs',71),('deletes',123),('next_step',83))),
                    'worker_inner_result_incomplete')
    terminal = evidence.obj('registered-worker-terminal.json')
    need(type(terminal.get('duration_ms')) is int and 0<=terminal['duration_ms']<=180000,'worker_time_limit')
    for ref in result.evidence_refs:
        evidence.raw(ref.path,dataclasses.asdict(ref))
    value['missing'] = list(result.pending_proofs)
    return value


def verify_exported_terminal(payloads,case,*,originals,source_commit,ci_run,
                             candidate_sha256,expected_sources,trusted_root):
    """Run concrete original-byte checks; missing domains remain explicit NO_GO.

    Main supplies authenticated ZIP payloads and its verified archive map. This
    function re-verifies the archive map and all refs before semantic inspection.
    It returns CASE_TERMINAL_UNVERIFIED on incomplete evidence, never a fake PASS.
    """
    need(type(payloads) is dict and type(case) is dict,'input')
    raw = payloads.get('case-execution.json')
    need(type(raw) is bytes and 0<len(raw)<=2_000_000,'case_bytes')
    need(canonical(decode(raw))==canonical(case),'case_not_original')
    need(case.get('format')=='disposable-case-terminal-v1' and case.get('status')=='CASE_PASS'
        and case.get('case_name') in CASES and case.get('parent_id')==PARENT,'case_scope')
    need(case.get('scope')=='single_disposable_case_only' and case.get('case_pass') is True
        and type(case.get('additional_sql_commands')) is int and case['additional_sql_commands']==0,
        'case_terminal_scope')
    error = case.get('original_exception_class')
    need(error is None if case['case_name']=='normal' else type(error) is str
        and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,99}',error),'case_original_failure')
    for key,expected in (('source_commit',source_commit),('ci_run',ci_run),('candidate_sha256',candidate_sha256)):
        need(type(expected) is str and case.get(key)==expected,'case_external_binding')
    need(re.fullmatch('[a-f0-9]{40}',source_commit) and re.fullmatch('[a-f0-9]{64}',candidate_sha256)
        and re.fullmatch('[1-9][0-9]{0,18}',ci_run),'case_identity')
    try:
        uid = uuid.UUID(case['run_id'])
    except (ValueError,TypeError,KeyError):
        raise Invalid('case_run') from None
    need(str(uid)==case['run_id'] and uid.version==4 and case['run_id'] not in (PARENT,OLD),'case_fresh_run')
    need(case.get('full_chain_admission') is False and case.get('hosted_admitted') is False
        and case.get('matrix_aggregation_required') is True,'case_claims')
    trusted = Trusted(trusted_root,expected_sources)
    need(case.get('terminal_source_hashes')==expected_sources,'case_source_inventory')
    archive = trusted.module('admission_case_archive')
    reconstructed = archive.verify(payloads,case['original_archive_ref'],case['original_refs'])
    need(reconstructed==originals,'original_archive_map')
    evidence = Originals(originals,case['original_refs'])
    report = {'status':'CASE_TERMINAL_UNVERIFIED','case_name':case['case_name'],
        'run_id':case['run_id'],'case_sha256':sha(raw),'checks':{},'missing':[],
        'invalid':[],'full_chain_admission':False,'hosted_admitted':False}
    def check(name,operation):
        try:
            value = operation()
            report['checks'][name] = value
            report['missing'].extend(value.get('missing',[]))
            return value
        except Missing as exc:
            report['missing'].append(name+':'+str(exc))
        except (Invalid,ValueError,KeyError,TypeError,OSError,RuntimeError) as exc:
            report['invalid'].append(name+':'+type(exc).__name__)
        return None
    index = evidence.obj('root-original-index.json')
    chunks = index.get('members',[])
    need(type(chunks) is list and 1<=len(chunks)<=15,'root_members')
    original_root = decode(b''.join(evidence.raw(ref['path'],ref) for ref in chunks))
    binding = original_root.get('binding')
    need(type(binding) is dict and all(binding.get(k)==v for k,v in {
        'run_id':case['run_id'],'parent_id':PARENT,'source_commit':source_commit,
        'ci_run':ci_run,'candidate_sha':candidate_sha256}.items()),'root_case_binding')
    need(set(binding)=={'run_id','parent_id','source_commit','ci_run','candidate_sha',
        'purpose','cap','expiry','binding_sha','environment','execution_admitted','hosted_permission'}
        and type(binding['cap']) is int and 0<binding['cap']<=2349
        and binding['purpose']=='6e11_disposable_quota_candidate_v1'
        and type(binding['binding_sha']) is str and re.fullmatch('[a-f0-9]{64}',binding['binding_sha'])
        and binding['environment']=='disposable_ci' and binding['execution_admitted'] is False
        and binding['hosted_permission'] is False,'root_binding_scope')
    root = check('root_original',lambda:root_original(evidence,binding))
    check('canonical_originals',lambda:trusted.module('admission_canonical_replay').replay(
        evidence,trusted,binding))
    if root is not None:
        register = root['register']
        report['checks']['root_original'] = {'status':'ROOT_ORIGINAL_BYTES_RECONSTRUCTED',
            'register_sha256':register['full_register_sha256']}
        terminal = evidence.obj(case['root_terminal_ref']['path'],case['root_terminal_ref'])
        check('root_journal',lambda:{'status':'ROOT_CHAINS_NUMERIC_REPLAYED',
            'journals':root_chains(evidence,register['full_register_sha256'],terminal['journal_refs']),
            'missing':[]})
        check('root_source',lambda:root_replay(evidence,trusted,binding,terminal,register))
    if case['case_name'] in ('pre_migration','post_migration'):
        check('bootstrap',lambda:bootstrap(evidence,trusted,payloads,case,source_commit,ci_run,candidate_sha256))
    else:
        def http():
            m = trusted.module('quota_candidate_v1.runtime_exported_http')
            result = m.verify_exported_http(originals,run_id=binding['run_id'],
                binding_sha=binding['binding_sha'],expected_sources=expected_sources,trusted_root=trusted.root)
            result['missing'] = ['http_identity_and_auth_pair_semantics']
            return result
        check('http',http)
        check('auth',lambda:auth_originals(evidence,case,binding))
        check('profile',lambda:profile(evidence,trusted,binding,case['isolation']))
        check('fixture',lambda:fixtures(evidence,trusted,binding,case['isolation']))
        check('streams',lambda:streams(evidence,trusted))
        check('worker',lambda:worker(evidence,trusted,case,binding))
        report['missing'].append('final_platform_process_closure')
    report['missing'] = sorted(set(report['missing']))
    report['invalid'] = sorted(set(report['invalid']))
    report['consumed_original_refs'] = [evidence.refs[n] for n in sorted(evidence.used)]
    return report
