"""Actual private worker dispatch positions joined to existing prepaid tickets."""
import copy
import pathlib
from .compiler import require, canonical, sha
from .runtime_faults import export_hooks

PREFIX = '_offline/phase6e11/endchain_v1/quota_candidate_v1/'


class WorkflowDispatch:
    def __init__(self, meter, tickets):
        require(len(tickets) == 72 and len(set(tickets)) == 72, 'dispatch_ticket_inventory')
        self.meter, self.tickets = meter, tuple(tickets)
        self.rows, self.pending = [], None
        for index, ticket in enumerate(tickets):
            event = meter.events[ticket-1]
            expected = 'gotrue_fixture_identity' if index == 0 else 'gotrue_workflow_identity_'+str(index-1)
            require(event['kind'] == 'managed_auth' and event['commands'] == 5
                and event['action'] == expected and event['confirmed'] is False
                and ticket in meter.managed_pending, 'dispatch_prepaid_binding')

    def before(self, index):
        require(not self.meter.stopped and not self.meter.closed and type(index) is int
            and index == len(self.rows) and 0 <= index < 72 and self.pending is None,
            'dispatch_sequence_or_stopped')
        ticket = self.tickets[index]
        require(ticket in self.meter.managed_pending, 'dispatch_ticket_not_pending')
        self.pending = index
        self.rows.append(dict(dispatch_id='workflow_user_'+str(index), index=index,
            step=None if index == 0 else index-1, ticket=ticket, reserved_commands=5,
            prepaid=True, dispatch_attempted=True, outcome='unknown_consumed',
            identity_verified=False, after_native_commands=self.meter.used,
            state_before=copy.deepcopy(self.meter.state)))

    def after(self, index, outcome, status=None):
        require(type(index) is int and self.pending == index and outcome in ('response_received','lost_response'),
                'dispatch_response_binding')
        require(status is None if outcome == 'lost_response' else type(status) is int and 100 <= status <= 599,
                'dispatch_response_status')
        self.rows[index].update(outcome=outcome, http_status=status)
        self.pending = None
        # Framed EOF is not verified identity or proven SQL cost. No refund.

    def worker_message(self, message):
        require(type(message) is dict and set(message) in (
            {'op','stage','index'}, {'op','stage','index','status'}), 'dispatch_ipc_shape')
        require(message['op'] == 'workflow_auth' and message['stage'] in ('before','response_received','lost_response')
            and type(message['index']) is int and 1 <= message['index'] <= 71, 'dispatch_ipc_binding')
        if message['stage'] == 'before':
            require(set(message) == {'op','stage','index'}, 'dispatch_ipc_shape')
            self.before(message['index'])
        else: self.after(message['index'],message['stage'],message.get('status'))

    def validated(self, protocol):
        require(len(self.rows) == 72 and self.pending is None
            and all(row['outcome'] == 'response_received' and row['http_status'] == 200 for row in self.rows)
            and protocol['commands'] == 360 and protocol['verified_calls'] == 72
            and all(row['temp_written'] == 0 for row in protocol['statements']), 'dispatch_protocol_incomplete')
        return {**self.receipt(), 'aggregate_protocol_confirmed':True,
            'aggregate_protocol_sha256':sha(canonical(protocol)),
            'individual_sql_cost_observed':False, 'per_call_capacity':5}

    def receipt(self):
        return dict(format='quota-workflow-dispatch-v1', rows=copy.deepcopy(self.rows),
            expected_calls=72, observed_attempts=len(self.rows), pending=self.pending,
            aggregate_protocol_confirmed=False, full_chain_admission=False,
            accounting='72 distinct managed reservations; actual HTTP attempts recorded in flow order')


def export_dispatch_contract(plan, scenario):
    """Factual adapter inventory for the independent DAG compiler, fail closed.

    Native retained rows are deliberately not relabelled as new source proof.
    A's compiler must join their current templates/ordering and recovery edges.
    """
    here = pathlib.Path(__file__).parent
    sources = {PREFIX+name:sha((here/name).read_bytes()) for name in
        ('runtime_adapter.py','runtime_parent_workflow.py','runtime_integral_workflow.mjs',
         'runtime_dispatch.py','runtime_faults.py','runtime_prefix.py')}
    events, groups = [], {}
    for index in range(72):
        group = 'workflow_user_'+str(index)
        phase = ('setup' if index == 0 else 'cleanup' if index-1 >=45 else
            'restore' if 'restore' in scenario[index-1]['request']['action'] else
            'route_a' if scenario[index-1]['route']=='A' else 'route_b')
        groups[group] = dict(capacity=5,phase=phase)
        source = PREFIX+'runtime_adapter.py'
        events.append(dict(event_id='precharge:'+group, stage='precharge', event_kind='precharge',
            phase=phase,method='CaseComposition.workflow',source=source,source_sha256=sources[source],
            selector={'workflow_index':index,'before_any_workflow_native':True},charge_group=group,
            cost=5,capacity_use=0,outcomes=['confirmed','rejected'],next={},state_after={}))
    for index in range(72):
        group='workflow_user_'+str(index)
        source=PREFIX+('runtime_parent_workflow.py' if index==0 else 'runtime_integral_workflow.mjs')
        events.append(dict(event_id=group,dispatch_id=group,stage='dispatch',event_kind='dispatch',
            phase=groups[group]['phase'],method='WorkflowBridge.workflow' if index==0 else 'auth.fetcher',
            source=source,source_sha256=sources[source],
            selector={'workflow_index':index,'step':None if index==0 else index-1,
                'location':'before_fixture_controls' if index==0 else 'inside_controller_act_before_transport'},
            managed_workflow_identity=True,charge_group=group,cost=0,capacity_use=5,
            outcomes=['response_received','lost_response'],next={},state_after={}))
    return dict(format='current-dispatch-contract-v1',plan_sha256=plan['plan_sha256'],
        source_hashes=sources,entry='precharge:workflow_user_0',
        terminals={'normal_complete':'normal','no_go':'NO_GO'},charge_groups=groups,
        events=events,normal_event_ids=[],coverage={},fault_cases={},hook_inventory=export_hooks(scenario)['cases'],
        missing_hooks=['native_template_order_join','18_registered_auth_dispatch_join',
            'three_cli_slot_ledger_join','fixture_capture_parent_cleanup_join',
            'migration_history47_local48_join','recovery_order_and_rollback_setup_ticket'],
        missing_costs=[],recovery_edges_complete=False,full_chain_admission=False,
        ordering_note='Precharges precede workflow. Actual HTTP nodes interleave with native work, not consecutive.')
