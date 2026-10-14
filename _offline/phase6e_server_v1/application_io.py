"""Compare numeric local-CI counters without treating migration history as load."""
def active_pair(before,after):
    if any(len(x['statements'])>5000 for x in (before,after)):raise ValueError('application_metadata_budget')
    a={x['queryid']:x for x in before['statements']};b={x['queryid']:x for x in after['statements']}
    if len(a)!=len(before['statements']) or len(b)!=len(after['statements']) or set(a)-set(b):raise ValueError('application_counter_missing')
    changed={key for key,row in b.items() if row!=a.get(key)}
    # Reset/deallocation, replaced counters and negative deltas remain checked
    # by the existing numeric validator. Keep raw samples separately as proof.
    return ({**before,'statements':[x for x in before['statements'] if x['queryid'] in changed]},
            {**after,'statements':[x for x in after['statements'] if x['queryid'] in changed]})
