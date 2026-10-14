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

def compare(before,after,protocol_commands,between=0):
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
    observed=sum(r['calls'] for r in changes)-1-between
    return {'protocol_commands':protocol_commands,'numeric_calls_minus_reader':observed,
        'all_protocol_visible':observed==protocol_commands,'temp_written':sum(r['temp_written'] for r in changes),
        'statements':changes,'query_text_read':False,
        'scope':'disposable CI correlation; not hosted attribution or admission'}

def snapshot(runtime):
    """Four counted read-only commands; fresh TLS connection, no pooled state."""
    from sql_protocol import statements
    connection=runtime.connect();trace=[];opened=False;value=None
    def query(text):
        trace.append({'sha256':statements(text)[0]['sha256'],'kind':'numeric_observer','protocol_commands':1,'confirmed':False})
        cursor=connection.execute(text);rows=cursor.fetchall() if cursor.description else []
        trace[-1]['confirmed']=True;return rows
    try:
        query('BEGIN TRANSACTION READ ONLY');opened=True
        if query("select current_setting('transaction_read_only')='on' readonly")[0]['readonly'] is not True:
            raise ValueError('cli_observer_not_readonly')
        value=query(SQL)[0]['value']
    finally:
        try:
            if opened:query('ROLLBACK')
        finally:connection.close()
    return value,trace
