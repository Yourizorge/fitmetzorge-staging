"""Resolve explicit approved local times, never invent a cadence or DST choice."""
from datetime import datetime,timezone
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError

def from_state(state):
    # The accepted fixture explicitly uses UTC. Do not silently reinterpret it
    # in the viewer's timezone or infer a recurring medical cadence.
    agenda=state['recovery']['agenda']
    date=agenda['checkin']['date']
    at=state['active']['cadence']['at']
    try:
        approved=[*agenda['allowedTimes'],agenda['checkin']['at']]
        return {'status':'planned','occurrence':occurrence(date,at,'UTC',approved,state['active']['version']),
                'background_delivery':False,'source':'synthetic accepted agenda; historical fixture date'}
    except ValueError as error:
        return {'status':'blocked','reason':str(error),'background_delivery':False}

def occurrence(date,at,zone,allowed_times,source_version,*,fold=None):
    if at not in allowed_times or type(source_version) is not int or source_version<1:raise ValueError('schedule_source')
    try:
        naive=datetime.fromisoformat(date+'T'+at)
        if naive.tzinfo or naive.isoformat(timespec='minutes')!=date+'T'+at:raise ValueError()
        tz=ZoneInfo(zone)
    except (TypeError,ValueError,ZoneInfoNotFoundError):raise ValueError('schedule_format') from None
    candidates=[]
    for f in (0,1):
        local=naive.replace(tzinfo=tz,fold=f);utc=local.astimezone(timezone.utc)
        if utc.astimezone(tz).replace(tzinfo=None)==naive and not any(x[1]==utc for x in candidates):candidates.append((f,utc))
    if not candidates:raise ValueError('schedule_nonexistent_local_time')
    if len(candidates)>1 and fold is None:raise ValueError('schedule_ambiguous_local_time')
    if fold not in (None,0,1) or type(fold) is bool:raise ValueError('schedule_fold')
    matches=[x for x in candidates if fold is None or x[0]==fold]
    if len(matches)!=1:raise ValueError('schedule_fold')
    f,utc=matches[0]
    return {'date':date,'at':at,'zone':zone,'fold':f,'utc':utc.isoformat(),
            'source_version':source_version,'policy':'explicit_approved_time_only','automatic_application':False}
