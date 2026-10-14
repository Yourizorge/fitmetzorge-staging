"""Deterministic technical events. No message bodies, health details or delivery."""
import hashlib,json

def key(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def desired(state):
    events={}
    for n in state['notices']:
        if n['status']=='current':events[n['id']]={'source_sha':state['sourceHash'],'kind':'records_changed'}
    p=state.get('review')
    if p:
        event=key({'source':p['source'],'kind':p['kind'],'target':p['target'],'base':p['base']})
        events[event]={'source_sha':p['source'],'kind':'proposal_pending'}
    return events

def changes(rows,state,action,now,expires,request_id,selected=None):
    active=desired(state);known={r['event_key']:r for r in rows};updates=[]
    if action=='notice_seen' and (selected not in known or known[selected]['status'] not in ('pending','seen') or known[selected]['expires_at']<=now):raise ValueError('notice_unavailable')
    for event,row in known.items():
        status=row['status']
        if not state['consent']:status='withdrawn'
        elif row['expires_at']<=now and status in ('pending','seen'):status='expired'
        elif action in ('reject','block') and status in ('pending','seen'):status='declined'
        elif action=='apply' and status in ('pending','seen'):status='applied'
        elif event not in active and status in ('pending','seen'):status='superseded'
        elif action=='notice_seen' and event==selected:status='seen'
        if status!=row['status']:
            history=row['history']+[{'status':status,'at':now.isoformat(),'request_id':request_id}]
            updates.append({'operation':'UPDATE','event_key':event,'status':status,'history':history})
    if state['consent'] and now<expires and action not in ('reject','block','apply','notice_seen'):
        for event,metadata in active.items():
            if event not in known:
                updates.append({'operation':'INSERT','event_key':event,**metadata,'status':'pending',
                    'expires_at':expires,'history':[{'status':'pending','at':now.isoformat(),'request_id':request_id}]})
    return updates

def visible(row,now):
    return {'id':row['event_key'],'kind':row['kind'],'source':row['source_sha'],
        'status':'expired' if row['status'] in ('pending','seen') and row['expires_at']<=now else row['status'],
        'expires_at':row['expires_at'].isoformat(),'history':row['history']}
