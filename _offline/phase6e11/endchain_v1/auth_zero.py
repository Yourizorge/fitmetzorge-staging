"""Independent registered-identity zero read; no connection or cleanup authority."""
import hashlib,json,pathlib,uuid
from safety_auth_budget import ROLES

SOURCES={
 'phase6e9-owner-window.json':'442cffa5c9dfb5f9156f58bab03f2f449997889f62e8f3b9b1c52f0395d20bc7',
 'phase6e11-controls.json':'2c5ae8b8df039c6ba83e9fd5b302c9834a08c88f1c11e5cc201495e4b34260e1',
 'phase6e11-control-history.json':'845754d21c72815915740c586f2a6c17ab6506768f5d079b2e8d0936b4710a12',
 'phase6e11-private-control-binding-0c0f86beea4a4ee781f6c2a1e9c6cfd1.json':'8d0814f720bfe997008b2426fdded7a8a74e832dfce21dda489214e802ecac45'}


def scope(ids,environment,root=None):
    if set(ids)!=set(ROLES) or len(set(ids.values()))!=3:raise ValueError('auth_zero_route_scope')
    people=set(ids.values());sources={}
    if environment=='staging':
        values=[]
        for name,expected in SOURCES.items():
            raw=(pathlib.Path(root)/'supabase/.temp'/name).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('auth_zero_inventory_changed')
            values.append(json.loads(raw));sources[name]=expected
        owner,current,history,binding=values
        if {x['id'] for x in owner['accounts']}!=people:raise ValueError('auth_zero_inventory_routes')
        people.update(x['id'] for x in current.values())
        people.update(x['id'] for x in history)
        people.update(x['id'] for x in binding['controls'])
        if len(people)!=12:raise ValueError('auth_zero_inventory_union')
    elif environment!='disposable_ci':raise ValueError('auth_zero_environment')
    for actor in people:
        if str(uuid.UUID(actor))!=actor:raise ValueError('auth_zero_identity')
    ordered=sorted(people)
    return {'ids':ordered,'sha256':hashlib.sha256(json.dumps(ordered,separators=(',',':')).encode()).hexdigest(),
        'environment':environment,'sources':sources}


def expression(bound):
    people=','.join("('"+str(uuid.UUID(x))+"'::uuid)" for x in bound['ids'])
    return """WITH manifest(user_id) AS (VALUES """+people+"""), registered AS (
 SELECT user_id FROM fmz6e10_private.identities
 UNION SELECT user_id FROM fmz6e11_private.identities
), subjects AS (SELECT user_id FROM manifest UNION SELECT user_id FROM registered)
SELECT jsonb_build_object('manifest_sha256','"""+bound['sha256']+"""',
 'manifest_count',(select count(*) from manifest),
 'registered_count',(select count(*) from registered),
 'scope_count',(select count(*) from subjects),
 'extra_registered_count',(select count(*) from registered where user_id not in(select user_id from manifest)),
 'sessions',(select count(*) from auth.sessions where user_id in(select user_id from subjects)),
 'refresh_tokens',(select count(*) from auth.refresh_tokens where user_id::text in(select user_id::text from subjects)))"""


def validate(value,bound):
    fields={'manifest_sha256','manifest_count','registered_count','scope_count',
        'extra_registered_count','sessions','refresh_tokens'}
    if not isinstance(value,dict) or set(value)!=fields:raise ValueError('auth_zero_metadata_shape')
    if any(type(value[k]) is not int or value[k]<0 for k in fields-{'manifest_sha256'}):
        raise ValueError('auth_zero_metadata_count')
    if (value['manifest_sha256']!=bound['sha256'] or value['manifest_count']!=len(bound['ids'])
            or value['registered_count']<3 or value['scope_count']!=len(bound['ids'])+value['extra_registered_count']
            or value['extra_registered_count']>value['registered_count']
            or value['registered_count']>value['scope_count'] or value['sessions'] or value['refresh_tokens']):
        raise ValueError('auth_zero_not_confirmed')
    return {**value,'environment':bound['environment'],'sources':dict(bound['sources']),
        'disabled_registry_rows_included':True,'unregistered_accounts_outside_manifest':'NOT_INVENTORIED'}
