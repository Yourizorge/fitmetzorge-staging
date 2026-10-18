"""Conservative CLI capacity, never inferred hosted session attribution."""
from cli_stat_reader import compare
CAP=64
OBSERVERS=8
CHARGE=CAP+OBSERVERS

def attribution(before,after,between=3):
    if before.get('track') not in ('all','top') or after.get('track')!=before.get('track'):
        raise ValueError('cli_tracking_incomplete')
    for sample in (before,after):
        keys=[r['queryid'] for r in sample['statements']]
        if len(keys)!=len(set(keys)):raise ValueError('cli_numeric_duplicate')
    delta=compare(before,after,0,between=between)
    calls=delta['numeric_calls_minus_reader']
    if calls<0 or calls>CAP:raise ValueError('cli_unknown_envelope_exceeded')
    if delta['temp_written']:raise ValueError('cli_window_temp_writes_unattributed')
    return dict(observed_noncollector_calls=calls,cli_confirmed_commands=None,
        background_confirmed_commands=None,unattributed_calls=calls,cli_reserved=CAP,
        temp_written=0,statement_deltas=delta['statements'],database_wide_not_session_bound=True)

def charged(receipt):
    if receipt.get('capacity_reserved')!=CAP or receipt.get('charged_commands')!=CHARGE or receipt.get('complete') is not True:
        raise ValueError('cli_capacity_receipt')
    observers=receipt.get('observer_commands',[])
    if len(observers)!=OBSERVERS or not all(x['confirmed'] for x in observers):
        raise ValueError('cli_observer_count')
    if receipt.get('environment')=='disposable_ci':
        n=receipt.get('protocol_commands')
        if type(n) is not int or not 0<n<=CAP or not receipt.get('numeric_protocol_coverage'):
            raise ValueError('cli_local_protocol_incomplete')
    elif receipt.get('environment')=='staging':
        numeric=receipt.get('attribution',{})
        if receipt.get('protocol_commands') is not None or receipt.get('commands')!=[] or \
           numeric.get('cli_confirmed_commands') is not None or numeric.get('cli_reserved')!=CAP or \
           type(numeric.get('unattributed_calls')) is not int or not 0<=numeric['unattributed_calls']<=CAP or \
           numeric.get('temp_written')!=0 or numeric.get('database_wide_not_session_bound') is not True:
            raise ValueError('cli_hosted_attribution_invalid')
    else:raise ValueError('cli_environment')
    return CHARGE

def local(receipt):
    value={**receipt,'environment':'disposable_ci','capacity_reserved':CAP,'charged_commands':CHARGE}
    charged(value)
    return value
