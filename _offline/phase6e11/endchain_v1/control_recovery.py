"""Run-bound compare-and-restore, including unknown enable outcomes."""
import copy,hashlib,uuid

CONTROL_SQL="select jsonb_build_object('config',(select to_jsonb(c) from fmz6e11_private.config c where id),'request',(select to_jsonb(c) from fmz6e11_request_private.control c where id)) value"
BEFORE_SQL=CONTROL_SQL+", (to_jsonb(clock_timestamp()+interval '3 minutes') #>> '{}') expires_at"
CLOSED={'config':{'id':True,'enabled':False,'proof_hash':None},
        'request':{'id':True,'enabled':False,'expires_at':None}}

def intent(original,run_id,expires_at):
    if original!=CLOSED:raise RuntimeError('ci_control_not_closed')
    if str(uuid.UUID(run_id))!=run_id:raise ValueError('control_run_identity')
    from datetime import datetime
    expiry=datetime.fromisoformat(expires_at)
    if expiry.tzinfo is None:raise ValueError('control_expiry_timezone')
    proof='synthetic-only-local-proof:'+run_id
    expected={'config':{'id':True,'enabled':True,'proof_hash':hashlib.sha256(proof.encode()).hexdigest()},
              'request':{'id':True,'enabled':True,'expires_at':expires_at}}
    return proof,expected

def recover(query,original,expected):
    before=query('setup','safety_control_before',CONTROL_SQL)[0]['value']
    # Original, partially enabled, fully enabled and already restored are valid.
    # Any unrelated value is not ours to overwrite.
    if any(before.get(key) not in (original[key],expected[key]) for key in CLOSED):
        raise RuntimeError('control_recovery_foreign_state')
    query('setup','safety_control_restore',
        "update fmz6e11_request_private.control set enabled=false,expires_at=null where id and enabled and expires_at=$1::timestamptz",
        [expected['request']['expires_at']])
    query('setup','safety_control_restore',
        "update fmz6e11_private.config set enabled=false,proof_hash=null where id and enabled and proof_hash=$1",
        [expected['config']['proof_hash']])
    after=query('setup','safety_control_after',CONTROL_SQL)[0]['value']
    if after!=original:raise RuntimeError('control_recovery_not_restored')
    digest=lambda value:hashlib.sha256(__import__('json').dumps(value,sort_keys=True).encode()).hexdigest()
    return {'before_sha':digest(before),'after_sha':digest(after),
        'original_restored':True,'commands':4,'unknown_enable_outcome_supported':True}
