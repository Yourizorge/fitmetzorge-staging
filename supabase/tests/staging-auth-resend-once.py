"""Owner-authorized, one-attempt staging resend. Recipient enters via stdin, never output."""
import importlib.util
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("transport", Path(__file__).with_name("phase6d0-staging-query.py"))
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)

def main():
    email = sys.stdin.read().strip().lower()
    if not re.fullmatch(r"[a-z0-9+._-]+@[a-z0-9.-]+", email):
        raise RuntimeError("recipient_invalid")
    query = "select count(*) as matches, bool_and(email_confirmed_at is null and deleted_at is null) as unconfirmed from auth.users where lower(email)='" + email + "'"
    request = urllib.request.Request(
        "https://api.supabase.com/v1/projects/mokxyyullfhkfalopbzd/database/query",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": "Bearer " + transport.credential(), "Content-Type": "application/json",
                 "User-Agent":"FitMetZorge-Staging-Auth-Audit/1", "Accept":"application/json"},
        method="POST")
    with urllib.request.urlopen(request, timeout=40) as response:
        rows = json.load(response)
    if rows != [{"matches": 1, "unconfirmed": True}]:
        raise RuntimeError("unique_unconfirmed_account_required")
    source = (ROOT / "app.js").read_text(encoding="utf-8")
    if 'const stagingSupabaseUrl = "https://mokxyyullfhkfalopbzd.supabase.co";' not in source:
        raise RuntimeError("staging_target_mismatch")
    key = re.search(r'const stagingSupabaseAnonKey = "(sb_publishable_[^"]+)";', source).group(1)
    receipt = ROOT / "supabase/.temp/registration-confirmation-resend-20260904.json"
    receipt.parent.mkdir(exist_ok=True)
    with receipt.open("x", encoding="utf-8") as file:
        json.dump({"attempts": 1, "started_at": datetime.now(timezone.utc).isoformat()}, file)
    request = urllib.request.Request(
        "https://mokxyyullfhkfalopbzd.supabase.co/auth/v1/resend?redirect_to=https%3A%2F%2Fyourizorge.github.io%2Ffitmetzorge-staging%2F",
        data=json.dumps({"type":"signup", "email":email}).encode(),
        headers={"apikey":key, "Content-Type":"application/json", "User-Agent":"FitMetZorge-Staging-Auth-Audit/1"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            response.read()
            result = {"attempts":1, "http_status":response.status, "auth_dispatch_accepted":True, "inbox_delivery_verified":False}
    except urllib.error.HTTPError as error:
        body = json.loads(error.read())
        code = body.get("error_code") or body.get("code")
        result = {"attempts":1, "http_status":error.code, "auth_dispatch_accepted":False,
                  "safe_error":code if isinstance(code,str) and re.fullmatch(r"[a-z_]{1,70}",code) else "auth_resend_rejected"}
    except Exception:
        result = {"attempts":1, "auth_dispatch_accepted":None, "safe_error":"transport_result_uncertain_do_not_retry"}
    with receipt.open("w", encoding="utf-8") as file:
        json.dump(result,file)
    print(json.dumps(result))

try:
    main()
except FileExistsError:
    print(json.dumps({"attempts_this_run":0, "error":"resend_already_attempted_do_not_retry"}))
except Exception as error:
    print(json.dumps({"attempts_this_run":0, "error":str(error) if isinstance(error,RuntimeError) else "preflight_failed",
                      "error_class":type(error).__name__, "status":getattr(error,"code",None)}))
