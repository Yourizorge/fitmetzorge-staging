"""Preserve each environment's known history, without reconciling old SQL."""
import hashlib,json,pathlib

HERE=pathlib.Path(__file__).resolve().parent
PIN_SHA='d6e12eb894b1a33023aa11f0f83819d06d0cad76d5994c2582cbb3594eafd414'

def load():
    raw=(HERE/'history_pin.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN_SHA:raise ValueError('history_pin_changed')
    return json.loads(raw)

def validate(rows,environment,root=None):
    pin=load()
    key={'staging':'staging','disposable_ci':'disposable'}.get(environment)
    if key is None:raise ValueError('history_environment_unbound')
    if len(rows) not in (44,45) or rows[:44]!=pin['history'][key]:
        raise ValueError('historical_migration_drift')
    root=pathlib.Path(root) if root is not None else HERE.parents[2]
    if len(pin['sources'])!=44:raise ValueError('history_source_count')
    for name,expected in pin['sources'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('historical_source_changed')
    return {'prior_migrations':44,'environment':environment,'pin_sha256':PIN_SHA,
            'cross_environment_equivalence_claimed':False}
