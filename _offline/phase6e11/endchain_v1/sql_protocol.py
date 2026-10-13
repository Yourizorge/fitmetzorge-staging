"""Count actual PostgreSQL 17 protocol statements, never split on semicolons."""
import hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def parser():
    local = ROOT / 'supabase/.temp/phase6e11-pg17-parser'
    if local.is_dir():
        sys.path.insert(0, str(local))
    import pglast
    from pglast.parser import get_postgresql_version
    version = get_postgresql_version()
    if pglast.__version__ != 'v7.20' or version[0] != 17:
        raise ValueError('pg17_parser_binding')
    return pglast

def statements(sql):
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError('empty_sql')
    p = parser()
    nodes, parts = p.parse_sql(sql), p.split(sql)
    if not nodes or len(nodes) != len(parts):
        raise ValueError('statement_count_disagreement')
    return [{'sql': text, 'sha256': hashlib.sha256(text.encode()).hexdigest(),
             'kind': type(node.stmt).__name__, 'protocol_commands': 1}
            for node, text in zip(nodes, parts)]

def single(sql, expected_sha=None):
    parts = statements(sql)
    if len(parts) != 1:
        raise ValueError('multiple_protocol_statements')
    if expected_sha is not None and parts[0]['sha256'] != expected_sha:
        raise ValueError('protocol_source_changed')
    return parts[0]

def receipt(sql):
    parts = statements(sql)
    return {'sql_sha256': hashlib.sha256(sql.encode()).hexdigest(),
            'protocol_commands': len(parts),
            'statements': [{k: v for k, v in x.items() if k != 'sql'} for x in parts],
            'parser': 'pglast v7.20 / PostgreSQL 17',
            'internal_writes_exempt': False}

if __name__ == '__main__':
    # SQL arrives on a local pipe, never from an HTTP endpoint or CLI secret.
    print(json.dumps(receipt(sys.stdin.read()), sort_keys=True))
