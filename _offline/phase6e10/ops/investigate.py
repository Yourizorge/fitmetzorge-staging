"""Read-only, bounded staging log investigation; never export tokens or actor/session IDs."""
import json
import pathlib
import urllib.parse
import urllib.error
import hashlib
import close6e9 as c

START="2026-09-16T06:50:00Z"
END="2026-09-16T07:00:00Z"
BASELINE="2026-09-15T14:46:55Z"

def logs(sql):
    url=c.MGMT+"/analytics/endpoints/logs?"+urllib.parse.urlencode({
        "sql":sql,"iso_timestamp_start":START,"iso_timestamp_end":END})
    result=c.call(url,method="GET")
    if "error" in result or not isinstance(result.get("result"),list):
        raise RuntimeError("logs_query_failed")
    return result["result"]

def main():
    identities=c.query("select user_id from fmz6e10_private.identities")
    enrolled={r["user_id"] for r in identities}
    changed=c.query("select p.id,p.updated_at,u.created_at account_created_at,(u.email='zorgeyouri@gmail.com') owner_inbox from public.profiles p join auth.users u on u.id=p.id where p.updated_at>"+c.lit(BASELINE)+" and p.id not in(select user_id from fmz6e10_private.identities)")
    changed_ids={r["id"] for r in changed}
    rows=logs("""select timestamp, log_attributes['request.method'] method,
log_attributes['request.path'] path,log_attributes['response.status_code'] status,
log_attributes['request.sb.jwt.authorization.payload.role'] role,
log_attributes['request.sb.jwt.authorization.payload.subject'] subject,
log_attributes['request.sb.jwt.authorization.payload.session_id'] session,
log_attributes['request.headers.user_agent'] agent,
log_attributes['request.headers.referer'] referer
from logs where source='edge_logs' order by timestamp limit 500""")
    sessions={r["session"] for r in rows if r.get("session")}
    session_results=[]
    for sid in sessions:
        meta=c.query("select user_id,created_at,updated_at,not_after,(user_agent like '%Mobile%') mobile from auth.sessions where id="+c.lit(sid))
        session_results.append({"found":len(meta)==1,"belongs_to_changed_actor":bool(meta and meta[0]["user_id"] in changed_ids),
            "enrolled_6e10":bool(meta and meta[0]["user_id"] in enrolled),
            **({k:meta[0][k] for k in ["created_at","updated_at","not_after","mobile"]} if meta else {})})
    safe=[]
    for r in rows:
        ref=urllib.parse.urlsplit(r.get("referer",""))
        safe.append({k:r.get(k) for k in ["timestamp","method","path","status","role"]}|
            {"changed_actor":r.get("subject") in changed_ids,"enrolled_6e10":r.get("subject") in enrolled,
             "has_session":bool(r.get("session")),"browser_mobile":"Mobile" in r.get("agent",""),
             "browser_family":"Chromium" if "Chrome/" in r.get("agent","") else "Safari" if "Safari/" in r.get("agent","") else "other",
             "referer_origin":ref.scheme+"://"+ref.netloc if ref.netloc else ""})
    audits=logs("""select timestamp,log_attributes['auth_audit_event.action'] action,
log_attributes['auth_audit_event.actor_id'] actor,
log_attributes['auth_audit_event.traits.provider'] provider
from logs where source='auth_audit_logs' order by timestamp limit 100""")
    methods=logs("""select timestamp,log_attributes['grant_type'] grant_type,
log_attributes['method'] method,log_attributes['path'] path,log_attributes['status'] status
from logs where source='auth_logs' and log_attributes['path']='/token' order by timestamp limit 30""")
    tables=['entitlements','member_app_preferences','member_notifications','nutrition_preferences',
            'profiles','progress_preferences','user_onboarding','user_settings','workout_sessions']
    updates=[]
    for table in tables:
        owner='id' if table=='profiles' else 'user_id'
        updates.extend(c.query("with actor as(select id from public.profiles where updated_at>"+c.lit(BASELINE)+
            " and id not in(select user_id from fmz6e10_private.identities)) select "+c.lit(table)+
            " table_name,count(*) recently_updated,count(*) filter(where "+owner+" in(select id from actor)) changed_actor_rows,"
            "min(updated_at) first_update,max(updated_at) last_update,string_agg(distinct xmin::text,',') transaction_ids"
            " from public."+table+" where updated_at>"+c.lit(BASELINE)+" and "+owner+
            " not in(select user_id from fmz6e10_private.identities)"))
    baseline=json.loads((c.ROOT/'supabase/.temp/phase6e10-before.json').read_text())
    receipt=json.loads((c.ROOT/'supabase/.temp/phase6e9-owner-window.json').read_text())
    current=c.fingerprint(receipt)
    original={r['name']:r for r in baseline['tables']}
    current_by_name={r['name']:r for r in current}
    differences=[name for name in sorted(set(original)|set(current_by_name)) if original.get(name)!=current_by_name.get(name)]
    migrations=c.query("select version,name,encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex') sha256 from supabase_migrations.schema_migrations order by version")
    windows=c.query("select (select count(*) from fmz6e10_private.windows where status='active' and ends_at>clock_timestamp()) active_windows,(select count(*) from fmz6e10_private.workspaces) workspaces")
    out={"read_only":True,"period":{"start":START,"end":END},
         "changed_profile_actors":[{k:r[k] for k in ["updated_at","account_created_at","owner_inbox"]} for r in changed],
         "sessions":session_results,"requests":safe,
         "auth_audit":[{"timestamp":r["timestamp"],"action":r["action"],"provider":r["provider"],
                       "changed_actor":r["actor"] in changed_ids,"enrolled_6e10":r["actor"] in enrolled} for r in audits],
         "request_limit":500,"truncated":len(rows)>=500,"secrets_exported":False}
    out.update({"login_methods":methods,"updated_row_metadata":updates,"window_state":windows,
        "original_fingerprint_tables":len(original),"current_fingerprint_tables":len(current_by_name),
        "different_tables":differences,"unchanged_tables":len(original)-len(differences),
        "original_baseline_sha256":hashlib.sha256((c.ROOT/'supabase/.temp/phase6e10-before.json').read_bytes()).hexdigest(),
        "old_34_migrations_identical":migrations[:34]==baseline['migrations'],"migration_count":len(migrations),
        "human_operator_confirmed":False,"conditional_go_satisfied":False,
        "limitations":["Authenticated password login is not proof of the human operator or uncompromised credentials.",
            "Request-to-transaction mapping is corroboration, not a complete before/after row audit.",
            "A bounded log interval cannot prove universal absence of unauthorized access.",
            "Original fingerprints are preserved; differences are not waived or rebased."]})
    (c.ROOT/"supabase/.temp/phase6e10-log-investigation.json").write_text(json.dumps(out,indent=2)+"\n")
    summary={k:v for k,v in out.items() if k not in ['requests']}
    summary['request_summary']={"total":len(safe),"authenticated":sum(r['role']=='authenticated' for r in safe),
        "service_role":sum(r['role']=='service_role' for r in safe),
        "enrolled_6e10":sum(r['enrolled_6e10'] for r in safe),
        "changed_actor":sum(r['changed_actor'] for r in safe),
        "phase6e10_paths":sum('6e10' in (r['path'] or '') for r in safe),
        "all_authenticated_mobile_safari":all(r['browser_mobile'] and r['browser_family']=='Safari' for r in safe if r['role']=='authenticated')}
    summary['post_or_mutation_paths']=sorted({r['path'] for r in safe if r['role']=='authenticated' and r['method'] in ['POST','PATCH','DELETE']})
    summary['local_evidence_sha256']=hashlib.sha256((c.ROOT/"supabase/.temp/phase6e10-log-investigation.json").read_bytes()).hexdigest()
    (c.ROOT/'docs/PHASE6E10_READONLY_INVESTIGATION.json').write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({k:summary[k] for k in ['request_summary','old_34_migrations_identical','migration_count','window_state','conditional_go_satisfied']}))

if __name__=="__main__":
    try:main()
    except urllib.error.HTTPError as e: print(json.dumps({"error":"readonly_request_failed","status":e.code}));raise SystemExit(1)
    except Exception:print(json.dumps({"error":"readonly_investigation_failed"}));raise SystemExit(1)
