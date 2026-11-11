"""One-shot local transport closeout, not fixture cleanup or full-chain proof."""
import time

from control_recovery import recover, replace_setup

CHANNELS = ('setup', 'writer', 'reader', 'workflow')


def finish(composition, gate, runtime, connections, query, raw_query, *, process,
           timer, enable_attempted, original, enabled, restored, primary=None,worker_evidence=None):
    """Retain the original failure while exhausting only source-bounded safety work."""
    secondary = []
    receipt = dict(format='disposable-workflow-recovery-v1', complete=False,
        primary_exception_class=type(primary).__name__ if primary is not None else None,
        connections=[], controls_required=bool(enable_attempted and enabled is not None
            and restored != original), controls_confirmed=False, worker_terminated=process is None,
        retry=False, fixtures_removed=False, token_revocation_claim=False,
        full_chain_admission=False, hosted_admission=False, secondary=secondary)

    def note(stage, error):
        item = dict(stage=stage, exception_class=type(error).__name__)
        secondary.append(item)
        try:
            composition.abort('workflow_recovery_incomplete')
        except Exception as abort_error:
            secondary.append(dict(stage='abort_'+stage, exception_class=type(abort_error).__name__))
            error.add_note('workflow_abort_secondary:'+type(abort_error).__name__)
        if primary is not None:
            primary.add_note('workflow_recovery_secondary:'+stage+':'+type(error).__name__)

    def save(name, value):
        try: gate.save(name, value)
        except Exception as error: note('save_'+name, error)

    if primary is not None:
        try: composition.abort('workflow_failed')
        except Exception as error: note('abort_original', error)
    if timer is not None and worker_evidence is not None:
        if not worker_evidence.watchdog_stopped:worker_evidence.stop_timer(timer)
    elif timer is not None:
        try: timer.cancel()
        except Exception as error: note('cancel_timer', error)
    if worker_evidence is not None:
        worker_evidence.close()
        receipt['worker_terminated']=process is None or worker_evidence.reaped
        try:
            from .runtime_worker_evidence import save as save_original
            receipt['worker_wait_ref']=save_original(gate,'workflow-worker-wait.json',worker_evidence.receipt())
            if process is not None and not worker_evidence.known:raise RuntimeError('workflow_wait_unconfirmed')
        except Exception as error:note('worker_wait',error)
    elif process is not None:
        try:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
            receipt['worker_terminated'] = process.poll() is not None
            if not receipt['worker_terminated']: raise RuntimeError('workflow_worker_not_reaped')
        except Exception as error: note('terminate_worker', error)

    # No command may race a still-live child holding this bridge's connections.
    if receipt['worker_terminated']:
        for channel in CHANNELS:
            connection = connections.get(channel)
            if connection is None: continue
            evidence = dict(channel=channel, requested=False, confirmed=False,
                            dispatched_commands=0, transaction_status_known=False)
            before = len(composition.commands)
            try:
                status = connection.info.transaction_status
                evidence['transaction_status_known'] = True
                if status != 0:
                    evidence['requested'] = True
                    composition.abort('workflow_safety_close')
                    composition.safety_label = 'rollback_'+channel
                    query(channel, 'safety_rollback', 'ROLLBACK')
                    evidence['confirmed'] = True
            except Exception as error:
                evidence['exception_class'] = type(error).__name__
                note('rollback_'+channel, error)
            finally:
                composition.safety_label = None
                evidence['dispatched_commands'] = len(composition.commands)-before
                receipt['connections'].append(evidence)
        save('integral-safety-rollback.json', dict(connections=receipt['connections'], retry=False))
        if receipt['controls_required']:
            try:
                composition.abort('workflow_control_close')
                # The unchanged helper reconnects once, never replays an unknown mutation.
                replace_setup(runtime, connections, save)
                value = recover(raw_query, original, enabled)
                if (value.get('original_restored') is not True or value.get('commands') != 4
                    or not composition.commands
                    or composition.commands[-1]['phase'] != 'safety_control_after'
                    or composition.commands[-1]['confirmed'] is not True):
                    raise RuntimeError('workflow_control_confirmation')
                composition.meter.confirm_controls_restored()
                receipt['controls_confirmed'] = True
                save('integral-safety-control-pair.json', value)
            except Exception as error:
                note('control_restore', error)
                save('integral-safety-control-stop.json',
                     dict(exception_class=type(error).__name__, retry=False))
    for channel, connection in list(connections.items()):
        try:
            connection.close()
            if channel == 'setup': composition.meter.setup_connection_owned = False
        except Exception as error: note('close_'+channel, error)
    if getattr(composition, 'workflow_dispatch', None) is not None:
        try:
            from .runtime_http import workflow_receipt
            value = workflow_receipt(composition, worker_terminated=receipt['worker_terminated'])
            gate.save('case-workflow-http-terminal.json', value)
        except Exception as error: note('workflow_http_terminal', error)
    save('integral-protocol-trace.json', dict(commands=composition.commands,
        events=composition.events, seconds=time.monotonic()-composition.started,
        hosted_calls=0, full_chain_admission=False, fault=composition.fault,
        fault_injected=composition.injected))
    receipt['complete'] = (not secondary and receipt['worker_terminated']
        and (not receipt['controls_required'] or receipt['controls_confirmed']))
    save('case-workflow-recovery.json', receipt)
    receipt['complete'] = receipt['complete'] and not secondary
    composition.workflow_recovery = receipt
    if secondary and primary is None: raise RuntimeError('workflow_recovery_incomplete')
    return receipt
