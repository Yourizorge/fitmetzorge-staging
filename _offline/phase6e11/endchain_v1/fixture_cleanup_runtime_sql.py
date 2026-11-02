"""Fixed, single-statement PG17 templates. No history or account mutation."""
from fixture_cleanup_evidence import TABLE_SCOPE

ORDER = ('inbox_state', 'events', 'proposals', 'source_heads', 'source_versions',
         'plans', 'b_versions', 'b_states', 'audit', 'requests', 'participants',
         'workspaces', 'windows')
KEYS = {'windows': ('id',), 'workspaces': ('id',), 'participants': ('window_id', 'user_id'),
        'audit': ('id',), 'requests': ('actor', 'key'), 'events': ('id',),
        'inbox_state': ('workspace_id', 'actor', 'proposal_version'),
        'proposals': ('id',), 'source_heads': ('workspace_id',),
        'source_versions': ('workspace_id', 'version'), 'plans': ('workspace_id', 'version'),
        'b_versions': ('workspace_id', 'version'), 'b_states': ('workspace_id',)}


def sha(expression):
    return "encode(sha256(convert_to((" + expression + ")::text,'UTF8')),'hex')"


def key(table):
    return sha('jsonb_build_array(' + ','.join('t.' + c for c in KEYS[table]) + ')')


def metadata(table):
    return ("jsonb_build_object('table','" + table + "','key_sha'," + key(table) +
            ",'row_sha'," + sha('to_jsonb(t)') + ",'xmin',t.xmin::text)")


def scope_ok(table):
    if table == 'workspaces':
        return 'window_id=$1::uuid and id=any($2::uuid[])'
    if table == 'events':
        return 'window_id=$1::uuid and (workspace_id is null or workspace_id=any($2::uuid[]))'
    return 'true'


# LIMIT is global; observing the sentinel row refuses the entire inventory.
UNION = ' union all '.join(
    'select ' + metadata(t) + " || jsonb_build_object('scope_ok'," + scope_ok(t) +
    ') value from fmz6e11_private.' + t + ' t where ' + TABLE_SCOPE[t]
    for t in ORDER)
INVENTORY = "select jsonb_build_object('rows',coalesce(jsonb_agg(value),'[]'::jsonb)," + \
    "'xid',pg_current_xact_id_if_assigned()::text) value from (" + UNION + ' limit 1001) inventory'
LOCK = 'LOCK TABLE ' + ','.join('fmz6e11_private.' + t for t in ORDER) + ' IN SHARE ROW EXCLUSIVE MODE'
CHECK = """select current_setting('server_version_num')::int/10000=17 pg17,
 current_setting('statement_timeout') in ('5s','5000ms') bounded_statement,
 current_setting('lock_timeout') in ('1s','1000ms') bounded_lock,
 current_user='postgres' privileged, current_setting('session_replication_role')='origin' origin,
 not exists(select 1 from fmz6e11_audit_private.bindings
 where xid=pg_current_xact_id_if_assigned() and backend=pg_backend_pid()) unbound,
 current_setting('transaction_read_only')='on' readonly"""


def delete(table):
    if table not in ORDER:
        raise ValueError('cleanup_table')
    return ("with removed as (delete from fmz6e11_private." + table + " t using "
            "jsonb_to_recordset($3::jsonb) e(key_sha text,row_sha text,xmin text) where (" +
            TABLE_SCOPE[table] + ') and ' + key(table) + '=e.key_sha and ' +
            sha('to_jsonb(t)') + '=e.row_sha and t.xmin::text=e.xmin returning ' +
            metadata(table) + " value) select coalesce(jsonb_agg(value),'[]'::jsonb) value from removed")


def plan():
    """Protocol dispatches only, not nested SQL/IO or global 2349 admission."""
    normal = [('begin', 'BEGIN'), ('check', CHECK), ('barrier', LOCK), ('inventory', INVENTORY)]
    normal += [('delete_' + t, delete(t)) for t in ORDER]
    normal += [('commit', 'COMMIT'), ('absence_begin', 'BEGIN TRANSACTION READ ONLY'),
               ('absence_check', CHECK), ('absence', INVENTORY), ('absence_rollback', 'ROLLBACK')]
    return {'normal': normal, 'failure_only': [('rollback', 'ROLLBACK')],
            'prepare': [('prepare_begin', 'BEGIN TRANSACTION READ ONLY'), ('prepare_check', CHECK),
                        ('prepare_inventory', INVENTORY), ('prepare_rollback', 'ROLLBACK')],
            'per_writer_transaction': [('capture', INVENTORY)]}
