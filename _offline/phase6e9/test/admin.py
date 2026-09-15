"""Fixed-project synthetic provisioning broker. Credentials stay in process memory."""
import hashlib
import importlib.util
import json
import pathlib
import re
import secrets
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("transport", ROOT / "supabase/tests/phase6d0-staging-query.py")
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
BASE = "https://mokxyyullfhkfalopbzd.supabase.co"
MGMT = "https://api.supabase.com/v1/projects/mokxyyullfhkfalopbzd"
token = transport.credential()
service = None
created = {}
proof_created = False

def request(url, method="GET", data=None, admin=False):
    global service
    key = service if admin else token
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    if admin:
        headers["apikey"] = service
    req = urllib.request.Request(url, method=method, headers=headers,
        data=None if data is None else json.dumps(data).encode())
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read()
        return json.loads(body) if body else None

def query(sql):
    return request(MGMT + "/database/query", "POST", {"query": sql})

def cleanup():
    global proof_created
    query("update fmz6e9_private.config set enabled=false,proof_hash=null where id")
    for uid, email in list(created.items()):
        current = request(BASE + "/auth/v1/admin/users/" + uid, admin=True)
        if current.get("email") != email:
            raise RuntimeError("cleanup_identity_mismatch")
        # Only freshly captured synthetic IDs; revoke sessions BEFORE Auth deletion.
        query("begin;delete from fmz6e9_private.subjects where member_id='" + uid +
              "' or trainer_id='" + uid + "';delete from auth.sessions where user_id='" + uid +
              "';delete from public.profiles where id='" + uid + "';commit;")
        request(BASE + "/auth/v1/admin/users/" + uid, "DELETE",
                {"should_soft_delete": False}, admin=True)
        del created[uid]
    if proof_created:
        request(MGMT + "/secrets", "DELETE", ["FMZ6E9_PROOF"])
        proof_created = False
    return {"remaining_created_accounts": len(created), "flag_enabled": False}

try:
    for line in sys.stdin:
        try:
            d = json.loads(line)
            op = d.get("op")
            if op == "create":
                email = d["email"]
                if not re.fullmatch(r"6e9-[a-z0-9-]+@example\.invalid", email):
                    raise RuntimeError("synthetic_email_required")
                if service is None:
                    keys = request(MGMT + "/api-keys?reveal=true")
                    matches = [x["api_key"] for x in keys if x.get("name") == "service_role"]
                    if len(matches) != 1:
                        raise RuntimeError("existing_service_credential_unavailable")
                    service = matches[0]
                u = request(BASE + "/auth/v1/admin/users", "POST",
                    {"email": email, "password": d["password"], "email_confirm": True}, admin=True)
                uid = u["id"]
                if not re.fullmatch(r"[0-9a-f-]{36}", uid):
                    raise RuntimeError("synthetic_id_invalid")
                created[uid] = email
                result = {"id": uid}
            elif op == "proof":
                existing = request(MGMT + "/secrets")
                if any(x["name"] == "FMZ6E9_PROOF" for x in existing):
                    raise RuntimeError("existing_proof_requires_inspection")
                proof = secrets.token_hex(32)
                request(MGMT + "/secrets", "POST", [{"name": "FMZ6E9_PROOF", "value": proof}])
                proof_created = True
                query("update fmz6e9_private.config set proof_hash='" +
                      hashlib.sha256(proof.encode()).hexdigest() + "',enabled=true where id")
                proof = None
                result = {"configured": True}
            elif op == "query":
                sql = d["sql"]
                if len(sql) > 50000 or not any(x in sql for x in ("fmz6e9", "pg_proc", "pg_class", "pg_policies")):
                    raise RuntimeError("synthetic_query_scope_required")
                result = query(sql)
            elif op == "cleanup":
                result = cleanup()
            else:
                raise RuntimeError("broker_operation_invalid")
            print(json.dumps({"ok": True, "result": result}), flush=True)
        except urllib.error.HTTPError as e:
            # Never print raw provider errors, headers, passwords or tokens.
            body = e.read().decode(errors="replace")
            code = re.search(r"synthetic_[a-z_]+|forced_6e9_fault", body)
            print(json.dumps({"ok": False, "error": code.group(0) if code else "staging_api_rejected",
                              "status": e.code}), flush=True)
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e) if isinstance(e, RuntimeError)
                              else "broker_operation_failed"}), flush=True)
finally:
    if created or proof_created:
        try:
            cleanup()
        except Exception:
            print(json.dumps({"ok": False, "error": "cleanup_required",
                              "created_ids": list(created)}), flush=True)
