"""Add only deterministic scheduling prerequisites; keep historical assertions."""
import hashlib
from fixture_compat import adapt as previous
NAME='20260906092905_phase6d_automatic_inbox.sql'
SHA='bf7febbf4049bf6102ec7d2ad544ca018cee9b3ff332aa8fc621baa5aaa5a1a6'
ANCHOR=""" perform set_config('request.jwt.claim.sub',other_u::text,true);
 perform public.fmz_phase6d_sync_device_timezone('UTC');
"""
ADDITION=""" -- This workout-only fixture must not auto-schedule a weekly result on Mondays.
 -- The unchanged later test explicitly enables weekly scheduling and verifies it.
 r:=ai_private.phase6d_current_preferences(other_u);
 perform public.fmz_phase6d_update_preferences('UTC',false,'23:59',true,false,1::smallint,
 '00:00',(r->>'revision')::bigint,gen_random_uuid());
"""
def adapt(name,raw):
    text,changed=previous(name,raw)
    if name!=NAME:return text,changed
    if hashlib.sha256(raw).hexdigest()!=SHA or text.count(ANCHOR)!=1:
        raise RuntimeError('historical_calendar_fixture_changed')
    return text.replace(ANCHOR,ANCHOR+ADDITION,1),True
