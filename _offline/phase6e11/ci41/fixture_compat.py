"""Additive fixture prerequisites for an unchanged historical 6A test on 6D+."""
import hashlib
NAME="20260901193000_phase6a_ai_trust_transactional_e2e.sql"
SHA="e2f9bdb2a111e8bcb6123c2021e005a9d9c59741e6824fbe8bb3d95dfa5558f1"
ANCHOR="  perform public.fmz_phase6a_service_complete_run(v_run_id, v_output, 0, 100, 50);"
ADDITION="""
  -- Preserve and prove the new consent gate before supplying synthetic prerequisites.
  begin
    perform public.fmz_phase6a_service_complete_run(v_run_id, v_output, 0, 100, 50);
    raise exception 'CI missing chat consent was accepted';
  exception when insufficient_privilege then
    if sqlerrm <> 'ai_consent_or_access_changed' then raise; end if;
  end;
  insert into public.user_onboarding(user_id,age,goal_safety_status)
  values(current_setting('phase6a.user1')::uuid,25,'realistic_foundation');
  perform set_config('request.jwt.claim.sub',current_setting('phase6a.user1'),true);
  perform public.fmz_phase6a_record_consent(
    'private_chat','granted','phase6d-private-chat-v1','nl',true,gen_random_uuid());
  if not coalesce((ai_private.phase6c_chat_status(current_setting('phase6a.user1')::uuid)->>'chat_write_allowed')::boolean,false)
     or coalesce((ai_private.phase6c_chat_status(current_setting('phase6a.user1')::uuid)->>'external_ai_enabled')::boolean,true)
  then raise exception 'CI synthetic chat prerequisites not satisfied'; end if;
  perform set_config('request.jwt.claim.sub',current_setting('phase6a.user2'),true);
"""
def adapt(name,raw):
    text=raw.decode("utf8")
    if name!=NAME:return text,False
    if hashlib.sha256(raw).hexdigest()!=SHA or text.count(ANCHOR)!=1:
        raise RuntimeError("historical_6a_fixture_source_changed")
    return text.replace(ANCHOR,ADDITION+ANCHOR,1),True
