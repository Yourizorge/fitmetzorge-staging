"""Per-stream utility attribution; unrelated numeric counters are not ownership.

Only an isolated first observation can bind a source hash to a query family.
No binding survives the stream or turns historical incomplete evidence into PASS.
"""
from integral_io import delta


def counters(sample):
    rows=sample['statements']
    values={row['queryid']:row for row in rows}
    if len(rows)!=len(values):raise ValueError('io_duplicate_query_identity')
    return values


class UtilityBindings:
    def __init__(self):self.bound={}

    def observe(self,source_hash,before,after,reader):
        old=counters(before);new=counters(after)
        if set(old)-set(new):raise ValueError('io_counter_missing_or_replaced')
        changed={qid:row['calls']-old.get(qid,{}).get('calls',0)
                 for qid,row in new.items() if qid!=reader
                 and row['calls']!=old.get(qid,{}).get('calls',0)}
        if any(n<0 for n in changed.values()):raise ValueError('io_command_attribution')
        prior=self.bound.get(source_hash)
        qid=prior
        if qid is None and len(changed)==1 and list(changed.values())==[1]:
            qid=next(iter(changed))
        valid=qid is not None and changed.get(qid)==1
        return {'changed_query_calls':changed,'unambiguous':valid,
                'queryid':qid,'previously_bound':prior is not None,
                'binding_method':'same-stream isolated source-hash observation',
                'other_query_calls':{k:v for k,v in changed.items() if k!=qid},
                'background_attributed_to_collector':False,'query_text_read':False}

    def confirm(self,source_hash,observation):
        if not observation['unambiguous']:raise ValueError('stream_utility_attribution')
        existing=self.bound.get(source_hash)
        if existing is not None and existing!=observation['queryid']:
            raise ValueError('stream_utility_binding_changed')
        self.bound[source_hash]=observation['queryid']


def other_load(before,after,observation):
    others=observation['other_query_calls']
    # Keep the conservative spill, reset, latency and project-health checks.
    # These counters remain unattributed, never called safe member activity.
    profile=delta(before,after,others)
    if any(row['exec_ms']>2500 for row in profile['queries']):
        raise ValueError('stream_unattributed_load')
    return {'queries':profile['queries'],'actor':'UNKNOWN',
            'attributed_to_collector':False,'query_text_read':False}
