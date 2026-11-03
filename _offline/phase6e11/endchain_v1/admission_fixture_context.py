"""Counted disposable bootstrap, never a hosted fixture or browser authority."""
import hashlib
import json
import sys
import uuid
from admission_failure import save_final
from native_runtime import NativeRuntime

ROLE_MAP = {'a_member': 'a', 'a_trainer': 'trainer', 'b_member': 'b'}
LIMIT = 12


def identities(ctx):
    result = {role: ctx['claims'][source]['sub'] for role, source in ROLE_MAP.items()}
    if len(set(result.values())) != 3:
        raise ValueError('admission_fixture_distinct_actors')
    for value in result.values():
        if not isinstance(value, str) or str(uuid.UUID(value)) != value:
            raise ValueError('admission_fixture_actor')
    return result


def run(gate, ctx, *, runtime=None):
    ids = identities(ctx)
    injected = runtime is not None
    if injected:
        from fixture_cleanup_runtime_ci import bind_runtime
        binding = bind_runtime(gate, runtime)
        gate.save('admission-fixture-runtime-binding.json', binding)
    else:
        runtime = NativeRuntime.disposable(gate)
    if runtime.environment != 'disposable_ci':
        raise ValueError('admission_fixture_disposable_only')
    receipt = {'status': 'NO_GO', 'limit': LIMIT, 'dispatches': [], 'hosted_calls': 0,
        'registered_accounts': 3, 'existing_rows_overwritten': False,
        'local_setup_not_hosted_run_capacity': True}
    def query(connection, label, sql, args=None, *, rollback=False):
        if len(receipt['dispatches']) >= LIMIT-(0 if rollback else 1):
            raise ValueError('admission_fixture_reserved_close')
        row = {'ordinal': len(receipt['dispatches'])+1, 'label': label,
               'query_sha256': hashlib.sha256(sql.encode()).hexdigest(), 'confirmed': False}
        receipt['dispatches'].append(row)
        gate.save('admission-fixture-dispatch-%02d.json' % row['ordinal'], row)
        cursor = connection.execute(sql, args)
        values = cursor.fetchall() if cursor.description else []
        row['confirmed'] = True
        return values
    db = None
    open_tx = False
    committed = False
    try:
        db = runtime.connect()
        # An unanswered BEGIN may already have opened the transaction.
        open_tx = True
        query(db, 'begin', 'BEGIN')
        before = query(db, 'empty_registry', "select (select count(*) from fmz6e11_private.identities) identities,(select count(*) from fmz6e11_private.operators) operators")[0]
        if before != {'identities': 0, 'operators': 0}:
            raise ValueError('admission_fixture_existing_registry_preserved')
        actors = query(db, 'actor_ownership', 'select id::text id from auth.users where id=any(%s::uuid[])', [list(ids.values())])
        if {row['id'] for row in actors} != set(ids.values()) or len(actors) != 3:
            raise ValueError('admission_fixture_actor_missing')
        provenance = hashlib.sha256(json.dumps(ids, sort_keys=True).encode()).hexdigest()
        inserted = query(db, 'register_owned', "insert into fmz6e11_private.identities(user_id,role,provenance_sha,enabled) select id,role,%s,true from unnest(%s::uuid[],%s::text[]) pair(id,role) returning user_id::text id", [provenance, list(ids.values()), list(ids)])
        if {row['id'] for row in inserted} != set(ids.values()):
            raise ValueError('admission_fixture_insert_count')
        operator = query(db, 'operator_owned', 'insert into fmz6e11_private.operators(user_id,enabled) values(%s::uuid,true) returning user_id::text id', [ids['a_trainer']])
        if operator != [{'id': ids['a_trainer']}]:
            raise ValueError('admission_fixture_operator_count')
        query(db, 'commit', 'COMMIT')
        open_tx = False
        committed = True
        db.close(); db = runtime.connect()
        open_tx = True
        query(db, 'after_begin', 'BEGIN TRANSACTION READ ONLY')
        check = query(db, 'after_readonly', "select current_setting('transaction_read_only')='on' readonly")[0]
        if check != {'readonly': True}:
            raise ValueError('admission_fixture_readonly')
        after = query(db, 'after_registry', 'select i.user_id::text id,i.role,i.provenance_sha,i.enabled,coalesce(o.enabled,false) operator from fmz6e11_private.identities i left join fmz6e11_private.operators o on o.user_id=i.user_id')
        expected = [{'id': value, 'role': role, 'provenance_sha': provenance, 'enabled': True,
                     'operator': role == 'a_trainer'} for role, value in ids.items()]
        if sorted(after, key=lambda x:x['role']) != sorted(expected, key=lambda x:x['role']):
            raise ValueError('admission_fixture_registry_after')
        query(db, 'after_rollback', 'ROLLBACK', rollback=True)
        open_tx = False
        receipt.update(status='DISPOSABLE_BOOTSTRAP_PASS', before=before,
            commit_confirmed=True, actor_hashes={k: hashlib.sha256(v.encode()).hexdigest() for k,v in ids.items()},
            after_registry_confirmed=True)
        gate.fixture_cleanup_ids = ids
        return receipt
    except Exception as error:
        receipt.update(error_class=type(error).__name__, commit_confirmed=committed,
                       automatic_retry=False)
        raise
    finally:
        primary = sys.exc_info()[1]
        primary_active = primary is not None
        closure_failed = False
        if db is not None:
            if open_tx:
                try: query(db, 'safety_rollback', 'ROLLBACK', rollback=True)
                except Exception as error:
                    receipt['rollback_error_class'] = type(error).__name__
                    closure_failed = True
            try: db.close()
            except Exception as error:
                receipt['close_error_class'] = type(error).__name__
                closure_failed = True
        # The parent owns an injected factory across bootstrap and fixture tests.
        if not injected:
            try: runtime.clear()
            except Exception as error:
                receipt['clear_error_class'] = type(error).__name__
                closure_failed = True
        if closure_failed:
            receipt['status'] = 'NO_GO'
            if hasattr(gate, 'fixture_cleanup_ids'): del gate.fixture_cleanup_ids
        save_final(gate,'admission-fixture-bootstrap.json',receipt,primary)
        if closure_failed and not primary_active:
            raise RuntimeError('admission_fixture_closure_unconfirmed')
