"""Optional disposable registry suffix, independent of global Auth closure.

run(gate, scope=Scope, tracked=TrackedRuntime, terminal_ref={path,sha256},
    auth_close_ref={path,sha256}).
The scope's before-bootstrap observation must already exist. Main must package
the original fixture journal first. Every original case/context is loaded from
that immutable journal; caller-selected subsets are not accepted. This route
may close only replayable, pre-write-owned fixtures. It requires current physical
zero for ALL scopes under the same write-blocking locks as registry deletion.
Lost fixture COMMIT stays unknown, claims stay held. Lost suffix COMMIT stays
unknown too; no retry. A lock-protected point-in-time closure is NOT evidence
that arbitrary future privileged connections are impossible, nor an Auth seal.
"""
import copy
import json
import pathlib
import sys
import uuid

import admission_module_binding as binding
from admission_binding import NEW_RUN, OLD_RUN
from admission_journal import Journal
from fixture_cleanup_evidence import parameters
from fixture_cleanup_runtime import Blocked, digest, validate_rows
import fixture_cleanup_runtime_sql as sql
import fixture_db_terminality as db_terminal
import fixture_parent_closure as parent
import fixture_producer_scope as producer
from native_runtime import NativeRuntime

PREFIX = 'fixture-parent-physical-zero'
MAX_CASES = 11
# BEGIN + LOCK + 8 catalog reads + N inventories + registry before + 2 DELETE
# + registry after + COMMIT; then BEGIN + LOCK + session + N inventories
# + registry absence + ROLLBACK. One rollback reserve also covers every prefix.
FIXED_LIMIT = 21  # Normal fixed protocol is 20; one additional failure reserve.
LOCK = parent.REGISTRY_LOCK.replace(' IN SHARE',
    ',fmz6e11_private.config,fmz6e11_workflow_audit.control IN SHARE')


def protocol_plan(case_count, eligible_count):
    """B can verify the actual source-defined protocol, not caller SQL strings."""
    if not 1 <= case_count <= MAX_CASES or not 0 <= eligible_count < case_count:
        raise Blocked('physical_zero_plan_bound')
    plan=[('begin','BEGIN'),('scope_write_exclusion',LOCK),*producer.QUERIES]
    for _ in range(eligible_count):
        plan.append(('owned_fixture_inventory',sql.INVENTORY))
        plan.extend(('owned_fixture_delete_'+table,sql.delete(table)) for table in sql.ORDER)
    plan.extend(('locked_fixture_zero',sql.INVENTORY) for _ in range(case_count))
    plan.extend([('registry_before',parent.REGISTRY),('delete_operator',parent.DELETE_OPERATOR),
        ('delete_identities',parent.DELETE_IDENTITIES),('registry_after',parent.REGISTRY),
        ('registry_commit','COMMIT'),('absence_begin','BEGIN'),('absence_exclusion',LOCK),
        ('absence_identity',producer.SESSION)])
    plan.extend(('locked_fixture_absence',sql.INVENTORY) for _ in range(case_count))
    return plan+[('registry_absence',parent.REGISTRY),('absence_rollback','ROLLBACK')]


def load_cases(evidence, actor_hashes):
    detail = evidence.get('fixture-cleanup-component-detail.json')
    if detail.get('status') != 'COMPONENT_PASS' or detail.get('preparation_run') != NEW_RUN:
        raise Blocked('physical_zero_durable_component_required')
    cases = detail.get('cases')
    if not isinstance(cases,list) or not 1 <= len(cases) <= MAX_CASES:
        raise Blocked('physical_zero_case_bound')
    found, result = set(), []
    for case in cases:
        uid = case['fixture_case']
        if uid in found: raise Blocked('physical_zero_duplicate_scope')
        found.add(uid)
        prefix = 'fixture-cleanup-'+uid+'-'
        intent = evidence.get(prefix+'parent-setup.json')
        context = intent['context']; args = parameters(context)
        bound = {'preparation_run':NEW_RUN,'case':uid,'scope_sha256':digest(args),'component_only':True}
        if args[0] != uid or any(x in (OLD_RUN,NEW_RUN) for x in (args[0],*args[1])):
            raise Blocked('physical_zero_fresh_scope_required')
        baseline = evidence.get(prefix+'baseline.json')
        if (any(intent.get(k)!=v or baseline.get(k)!=v for k,v in bound.items())
                or intent.get('actor_hashes') != actor_hashes or intent.get('before_writer_begin') is not True
                or baseline.get('rows') != [] or baseline.get('source') != 'actual_empty_inventory'):
            raise Blocked('physical_zero_original_scope_binding')
        original_ref = None
        if case['receipt'].get('commit_unknown'):
            original = evidence.get(prefix+'result.json')
            if any(original.get(k)!=v for k,v in case['receipt'].items()):
                raise Blocked('physical_zero_original_result_changed')
            original_ref = {'path':'admission-fixture-private-journal/'+prefix+'result.json',
                            'sha256':evidence.index['records'][prefix+'result.json']['sha256']}
        result.append((case,context,original_ref))
    return result


def run(gate, *, scope, tracked, terminal_ref, auth_close_ref):
    """Unknown COMMIT never replayed; known cleanup uses original ownership only."""
    if type(scope) is not producer.Scope or scope.gate is not gate or scope.baseline is None:
        raise Blocked('physical_zero_actual_scope_object_required')
    if type(tracked) is not db_terminal.TrackedRuntime:
        raise Blocked('physical_zero_actual_tracked_factory_required')
    source_binding = binding.verify(gate,[sys.modules[__name__],producer,db_terminal,parent,binding,
        sql,sys.modules[Journal.__module__],sys.modules[parameters.__module__],
        sys.modules[NativeRuntime.__module__],sys.modules[Blocked.__module__]])
    journal = Journal(pathlib.Path(gate.out)/(PREFIX+'-private'),gate.save,PREFIX+'-journal')
    save = journal.save
    result = {'status':'NO_GO','preparation_run':NEW_RUN,'classification':'BLOCKED',
        'original_claims_released':False,'original_commit_reclassified':False,
        'unknown_fixture_delete_replayed':False,'auth_objects_touched':False,'global_auth_barrier':False,
        'future_privileged_connections_excluded':False,'full_cleanup_proven':False,
        'physical_zero':False,'registry_commit_confirmed':False,'registry_commit_unknown':False,
        'registry_absence_confirmed':False,'registry_deletion_proven':False,
        'terminal_ref':terminal_ref,'auth_close_ref':auth_close_ref,'source_binding':source_binding,'cases':[],
        'fixture_suffix_commit_confirmed':False,'fixture_returned_delete_count':0,
        'original_receipts_unchanged':False}
    runtime = raw = meter = evidence = None
    began = commit_attempted = False
    error = None
    try:
        evidence = parent.Evidence(gate)
        ids = copy.deepcopy(gate.fixture_cleanup_ids)
        bootstrap, bootstrap_hash = parent.read_record(gate.out,'admission-fixture-bootstrap.json')
        expected = parent.expected_registry(ids)
        if (set(ids)!=set(parent.ROLES) or len(set(ids.values()))!=3
                or any(str(uuid.UUID(v))!=v or v in (OLD_RUN,NEW_RUN) for v in ids.values())
                or bootstrap.get('status')!='DISPOSABLE_BOOTSTRAP_PASS'
                or bootstrap.get('actor_hashes')!={k:parent.sha(v.encode()) for k,v in ids.items()}
                or bootstrap.get('before')!={'identities':0,'operators':0}
                or bootstrap.get('registered_accounts')!=3
                or bootstrap.get('existing_rows_overwritten') is not False
                or bootstrap.get('commit_confirmed') is not True
                or bootstrap.get('after_registry_confirmed') is not True):
            raise Blocked('physical_zero_bootstrap_ownership')
        actor_hashes = bootstrap['actor_hashes']
        cases = load_cases(evidence,actor_hashes)
        auth_close = parent.reference(gate.out,auth_close_ref)
        if (auth_close.get('kind')!='closed' or auth_close.get('active_requests')!=0
                or auth_close.get('all_registered_upstream_terminal') is not True
                or auth_close.get('future_regular_dispatch_denied') is not True
                or auth_close.get('scope')!='registered_request_set_only'):
            raise Blocked('physical_zero_auth_close_ref')
        result['actor_hashes'] = actor_hashes
        terminal = parent.reference(gate.out,terminal_ref)
        component_terminal = evidence.get('fixture-cleanup-db-terminal.json')
        if (component_terminal.get('terminal')!=terminal
                or sorted(component_terminal.get('fixture_case_ids',[]))!=sorted(c['fixture_case'] for c,_,_ in cases)
                or component_terminal.get('component_status')!='COMPONENT_PASS'):
            raise Blocked('physical_zero_component_terminal_binding')
        scope_receipt = scope.after_mint_closure(terminal_ref)
        # Calling the actual factory method proves its private terminal state,
        # not just the existence of a caller-supplied boolean receipt.
        unknown = [(case,context,ref) for case,context,ref in cases if ref is not None]
        if not unknown: raise Blocked('physical_zero_unknown_commit_route_only')
        for case,context,ref in unknown:
            zero = tracked.physical_zero(context,ref)
            if (zero.get('physical_zero') is not True or zero.get('terminal_sha256')!=digest(terminal)
                    or zero.get('original_ref')!=ref or zero.get('scope_sha256')!=digest(parameters(context))):
                raise Blocked('physical_zero_terminal_or_original_mismatch')
            zero_record=case['fixture_case']+'-physical-zero.json'
            save(zero_record,zero)
            result['cases'].append({'case':case['fixture_case'],'original_ref':ref,
                'classification':'physical_zero_original_commit_unknown','original_status':'NO_GO',
                'zero_sha256':digest(zero),'physical_zero_record':zero_record})
        eligible = []
        for case,context,ref in cases:
            if ref is None and not (case['receipt'].get('status')=='COMPONENT_PASS'
                                    and case['receipt'].get('cleanup_complete') is True):
                eligible.append((case,context,parent.ownership(evidence,case,context,actor_hashes=actor_hashes)))
        plan = protocol_plan(len(cases),len(eligible))
        limit = len(plan)+1
        result.update(case_ids=[c['fixture_case'] for c,_,_ in cases],
            eligible_case_ids=[c['fixture_case'] for c,_,_ in eligible],
            unknown_case_ids=[c['fixture_case'] for c,_,_ in unknown],
            expected_protocol_commands=len(plan))
        meter = producer.Meter(save,PREFIX,limit)
        save('intent.json',{'preparation_run':NEW_RUN,'case_ids':[c['fixture_case'] for c,_,_ in cases],
            'scope_sha256':digest(scope_receipt),'terminal_ref':terminal_ref,'protocol_limit':limit,
            'original_hashes':{**evidence.hashes,terminal_ref['path']:terminal_ref['sha256'],
                auth_close_ref['path']:auth_close_ref['sha256'],'admission-fixture-bootstrap.json':bootstrap_hash},
            'bootstrap':bootstrap,'actor_hashes':actor_hashes,'auth_close_ref':auth_close_ref,
            'eligible_case_ids':[c['fixture_case'] for c,_,_ in eligible],
            'additional_scope_observation_limit':producer.LIMIT,
            'additional_unknown_zero_limit':len(unknown)*db_terminal.ZERO_LIMIT})
        runtime = NativeRuntime.disposable(gate)
        raw = runtime.connect()
        if raw.autocommit is not True: raise Blocked('physical_zero_autocommit_required')
        def query(phase,text,args=(),reserve=1): return meter.query(raw,phase,text,args,reserve=reserve)
        def inventories(phase):
            for case,context,_ in cases:
                rows = query(phase,sql.INVENTORY,parameters(context))
                if len(rows)!=1 or validate_rows(rows[0]['value']):
                    raise Blocked('physical_zero_scope_still_present')
        def registry(phase):
            rows=query(phase,parent.REGISTRY,[list(ids.values())])
            if len(rows)!=1 or set(rows[0].get('value',{}))!=set(expected):
                raise Blocked('physical_zero_registry_shape')
            return rows[0]['value']
        def immutable():
            evidence.unchanged()
            parent.read_record(gate.out,'admission-fixture-bootstrap.json',bootstrap_hash)
            parent.reference(gate.out,terminal_ref)
            parent.reference(gate.out,auth_close_ref)
        began=True
        query('begin','BEGIN')
        query('scope_write_exclusion',LOCK)
        held=producer.collect(raw,meter,scope.contract,before=False)
        if any(held[k]!=scope_receipt[k] for k in ('cluster_id','postmaster_start','datid','migration_sources_sha256')):
            raise Blocked('physical_zero_server_changed')
        for case,context,snapshots in eligible:
            case_id=case['fixture_case']
            observed=query('owned_fixture_inventory',sql.INVENTORY,parameters(context))
            if len(observed)!=1: raise Blocked('physical_zero_owned_inventory_shape')
            rows=validate_rows(observed[0]['value'])
            allowed={digest(r) for snapshot in snapshots for r in snapshot['rows']}
            if any(digest(r) not in allowed for r in rows): raise Blocked('physical_zero_unowned_row')
            if case['case']=='foreign_row' and parent.row_multiset(rows)!=parent.row_multiset(snapshots[0]['rows']):
                raise Blocked('physical_zero_negative_control_changed')
            immutable()
            save(case_id+'-predelete.json',{'rows':rows,'snapshots_sha256':digest(snapshots),
                 'scope_sha256':digest(parameters(context)),'commit_confirmed':False})
            for table in sql.ORDER:
                expected_rows=[{k:v for k,v in r.items() if k!='scope_ok'} for r in rows if r['table']==table]
                actual=query('owned_fixture_delete_'+table,sql.delete(table),
                             [*parameters(context),json.dumps(expected_rows)])
                if len(actual)!=1 or not parent.same_rows(actual[0].get('value'),expected_rows):
                    raise Blocked('physical_zero_owned_delete_mismatch')
                result['fixture_returned_delete_count']+=len(expected_rows)
                save(case_id+'-delete-'+table+'.json',{'expected':expected_rows,'returned':actual[0]['value'],
                     'commit_confirmed':False})
        inventories('locked_fixture_zero')
        before=registry('registry_before')
        if any(not parent.same_rows(before[k],expected[k]) for k in expected):
            raise Blocked('physical_zero_registry_not_exact_owned')
        immutable()
        save('locked-zero-before-delete.json',{'scope':held,'all_case_ids':[c['fixture_case'] for c,_,_ in cases],
            'lock_mode':'SHARE ROW EXCLUSIVE','registry':before,'original_claims_released':False})
        removed=query('delete_operator',parent.DELETE_OPERATOR,[ids['a_trainer']])
        if not parent.same_rows(removed,expected['operators']): raise Blocked('physical_zero_operator_returning')
        save('delete-operator.json',{'returned':removed,'commit_confirmed':False})
        removed=query('delete_identities',parent.DELETE_IDENTITIES,[json.dumps(expected['identities'])])
        if not parent.same_rows(removed,expected['identities']): raise Blocked('physical_zero_identity_returning')
        save('delete-identities.json',{'returned':removed,'commit_confirmed':False})
        if any(registry('registry_after').values()): raise Blocked('physical_zero_registry_rows_remain')
        save('commit-intent.json',{'fixture_returned_delete_count':result['fixture_returned_delete_count'],
                                  'identities':3,'operators':1,'unknown_fixture_commit_replayed':False})
        commit_attempted=True
        query('registry_commit','COMMIT')
        result['registry_commit_confirmed']=True
        result['fixture_suffix_commit_confirmed']=True
        began=False
        raw.close(); raw=None
        # Independent connection/transaction and the same write-blocking locks.
        raw=runtime.connect()
        if raw.autocommit is not True: raise Blocked('physical_zero_autocommit_required')
        began=True
        query('absence_begin','BEGIN')
        query('absence_exclusion',LOCK)
        identity=producer.one(query('absence_identity',producer.SESSION))
        if (any(identity.get(k)!=held[k] for k in ('cluster_id','postmaster_start','datid'))
                or any(identity.get(k) is not True for k in ('pg17','statement_bounded','lock_bounded',
                           'no_prepared','tracked','fresh','origin','privileged'))):
            raise Blocked('physical_zero_absence_session')
        inventories('locked_fixture_absence')
        if any(registry('registry_absence').values()): raise Blocked('physical_zero_registry_absence')
        immutable()
        save('locked-absence.json',{'all_scopes_physically_zero':True,'registry_absent':True,
             'original_commit_reclassified':False,'future_privileged_connections_excluded':False})
        began=False
        query('absence_rollback','ROLLBACK',reserve=0)
        for ordinal,(event,(phase,text)) in enumerate(zip(meter.protocol.events,plan),1):
            if (event.get('ordinal')!=ordinal or event.get('phase')!=phase
                    or event.get('sql_sha256')!=parent.sha(text.encode()) or event.get('confirmed') is not True):
                raise Blocked('physical_zero_protocol_mismatch')
        if len(meter.protocol.events)!=len(plan): raise Blocked('physical_zero_protocol_length')
        result.update(physical_zero=True,registry_absence_confirmed=True,registry_deletion_proven=True,
            original_receipts_unchanged=True,classification='REGISTRY_CLOSED_WITH_ORIGINAL_COMMIT_UNKNOWN',
            registry_remaining_counts={'identities':0,'operators':0},deleted_identities=3,deleted_operators=1)
    except BaseException as caught:
        error=caught
        result['registry_commit_unknown']=commit_attempted and not result['registry_commit_confirmed']
    finally:
        for action in (lambda: meter.query(raw,'failure_rollback','ROLLBACK',reserve=0)
                       if began and not (commit_attempted and not result['registry_commit_confirmed']) else None,
                       lambda: raw.close() if raw is not None else None,
                       lambda: runtime.clear() if runtime is not None else None):
            try: action()
            except BaseException as caught:
                if error is None: error=caught
                else: error.add_note('physical-zero finalizer: '+type(caught).__name__)
    if error is not None:
        result.update(classification='NO_GO',registry_deletion_proven=False,
            reason=str(error) if isinstance(error,Blocked) else 'physical_zero_execution_error',
            error_class=type(error).__name__)
    if evidence is not None:
        try:
            evidence.unchanged()
            parent.reference(gate.out,terminal_ref)
            parent.reference(gate.out,auth_close_ref)
            result['original_receipts_unchanged']=True
        except BaseException as caught:
            result.update(original_receipts_unchanged=False,registry_deletion_proven=False,
                          classification='NO_GO',evidence_error_class=type(caught).__name__)
            if error is None: error=caught
    result.update(protocol_limit=meter.limit if meter else 0, admitted_attempts=meter.used if meter else 0,
                  emitted_attempts=len(meter.protocol.events) if meter else 0,
                  protocol=copy.deepcopy(meter.protocol.events) if meter else [])
    try:
        save('result.json',result)
        journal.seal()
        gate.save(PREFIX+'.json',{k:v for k,v in result.items() if not isinstance(v,(dict,list))})
    except BaseException as caught:
        if error is not None:
            error.add_note('physical-zero final evidence: '+type(caught).__name__)
            raise error
        raise
    return result
