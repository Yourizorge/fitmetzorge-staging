"""Numeric utility coverage check. Never reads or exports SQL query text."""
SQL="""select jsonb_build_object(
 'reset',(select stats_reset from extensions.pg_stat_statements_info),
 'dealloc',(select dealloc from extensions.pg_stat_statements_info),
 'track_utility',current_setting('pg_stat_statements.track_utility'),
 'track',current_setting('pg_stat_statements.track'),
 'statements',(select coalesce(jsonb_agg(jsonb_build_object(
 'queryid',queryid::text,'calls',calls,'since',stats_since,
 'temp_written',temp_blks_written,'wal',wal_bytes::text)),'[]')
 from extensions.pg_stat_statements(false)
 where dbid=(select oid from pg_database where datname=current_database())
 and userid=(select oid from pg_roles where rolname='postgres') and toplevel)) value"""

def compare(before,after,protocol_commands):
    if before['reset']!=after['reset'] or before['dealloc']!=after['dealloc']:
        raise ValueError('cli_numeric_counters_reset')
    if before['track_utility']!='on' or after['track_utility']!='on':
        raise ValueError('cli_utility_not_tracked')
    old={r['queryid']:r for r in before['statements']}
    new={r['queryid']:r for r in after['statements']}
    if set(old)-set(new):raise ValueError('cli_numeric_counter_missing')
    changes=[]
    for key,row in new.items():
        prior=old.get(key)
        if prior and prior['since']!=row['since']:raise ValueError('cli_numeric_counter_replaced')
        calls=row['calls']-(prior['calls'] if prior else 0)
        temp=row['temp_written']-(prior['temp_written'] if prior else 0)
        wal=int(row['wal'])-int(prior['wal'] if prior else 0)
        if min(calls,temp,wal)<0:raise ValueError('cli_numeric_counter_decreased')
        if calls:changes.append(dict(queryid=key,calls=calls,temp_written=temp,wal=wal))
    # The before-reader is included only when the after-reader starts.
    observed=sum(r['calls'] for r in changes)-1
    return {'protocol_commands':protocol_commands,'numeric_calls_minus_reader':observed,
        'all_protocol_visible':observed==protocol_commands,'temp_written':sum(r['temp_written'] for r in changes),
        'statements':changes,'query_text_read':False,
        'scope':'disposable CI correlation; not hosted attribution or admission'}
