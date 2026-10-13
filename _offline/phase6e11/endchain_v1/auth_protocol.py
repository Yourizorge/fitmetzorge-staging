"""Numeric accounting of the actual local GoTrue database client.

Top-level calls include transaction protocol SQL when track_utility is on.
This is separate from the native collector's commands and nested trigger SQL.
"""
STATS="""jsonb_build_object('reset',(select stats_reset from extensions.pg_stat_statements_info),
 'dealloc',(select dealloc from extensions.pg_stat_statements_info),
 'track_utility',current_setting('pg_stat_statements.track_utility'),
 'statements',(select coalesce(jsonb_agg(jsonb_build_object('queryid',queryid::text,'calls',calls,
 'since',stats_since,'temp_written',temp_blks_written,'temp_read',temp_blks_read,
 'wal_bytes',wal_bytes::text,'exec_ms',total_exec_time)),'[]')
 from extensions.pg_stat_statements(false) where userid=(select oid from pg_roles where rolname='supabase_auth_admin')
 and dbid=(select oid from pg_database where datname=current_database()) and toplevel))"""

def difference(before,after):
    if any(before[k]!=after[k] for k in ('reset','dealloc')) or before['track_utility']!='on' or after['track_utility']!='on':
        raise ValueError('auth_protocol_statistics_unbound')
    if any(len(s['statements'])>1024 for s in (before,after)):raise ValueError('auth_protocol_metadata_budget')
    a={r['queryid']:r for r in before['statements']};b={r['queryid']:r for r in after['statements']}
    if len(a)!=len(before['statements']) or len(b)!=len(after['statements']) or set(a)-set(b):
        raise ValueError('auth_protocol_counter_missing')
    deltas=[]
    for key,r in b.items():
        old=a.get(key)
        if old and old['since']!=r['since']:raise ValueError('auth_protocol_counter_replaced')
        d={k:int(r[k])-int(old[k] if old else 0) for k in ('calls','temp_written','temp_read','wal_bytes')}
        d['exec_ms']=r['exec_ms']-(old['exec_ms'] if old else 0)
        if min(d.values())<0:raise ValueError('auth_protocol_counter_regressed')
        if d['temp_written'] or d['temp_read']:raise ValueError('auth_protocol_temp_writes')
        if d['calls']:deltas.append({'queryid':key,**d})
    return {'statements':deltas,'commands':sum(x['calls'] for x in deltas),
        'wal_bytes':sum(x['wal_bytes'] for x in deltas),'temp_written':0,
        'query_text_read':False,'scope':'disposable CI GoTrue role, not hosted attribution'}
