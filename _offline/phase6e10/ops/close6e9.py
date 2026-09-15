"""Close only the proven 6E9 owner fixtures; retain their Auth/profile identities."""
import hashlib
import importlib.util
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[3]
PROJECT = "mokxyyullfhkfalopbzd"
BASE = "https://" + PROJECT + ".supabase.co"
MGMT = "https://api.supabase.com/v1/projects/" + PROJECT
PUB = "sb_publishable_6OiMLMl946arkI71-ylqkQ_EQWL6kKT"
spec = importlib.util.spec_from_file_location("transport", ROOT / "supabase/tests/phase6d0-staging-query.py")
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
pat = transport.credential()
service = None

def call(url, data=None, method="POST", key=None):
    key = key or pat
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    if url.startswith(BASE):
        headers["apikey"] = PUB if key != service else service
    req = urllib.request.Request(url, method=method, headers=headers,
                                 data=None if data is None else json.dumps(data).encode())
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
        return json.loads(body) if body else None

def query(sql):
    return call(MGMT + "/database/query", {"query": sql})

def lit(value):
    return "'" + str(value).replace("'", "''") + "'"

def fingerprint(receipt):
    ids = ",".join(lit(a["id"]) for a in receipt["accounts"])
    ws = ",".join(lit(a["workspace"]) for a in receipt["accounts"] if a["workspace"])
    pieces = []
    for t in receipt["before"]:
        name = t["name"]
        if name not in [r["name"] for r in receipt["before"]] or not all(c.isalnum() or c in "_." for c in name):
            raise RuntimeError("unsafe_table")
        where = ""
        if name == "public.profiles":
            where = " where id not in (" + ids + ")"
        if name in ("public.fmz6e9_audit", "public.fmz6e9_notices"):
            where = " where workspace not in (" + ws + ")"
        pieces.append("select " + lit(name) + " as name,count(*)::int rows,encode(sha256(convert_to(coalesce(string_agg(h,',' order by h),''),'UTF8')),'hex') sha256 from (select encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') h from " + name + " t" + where + ") q")
    return query(" union all ".join(pieces))

def main():
    global service
    receipt = json.loads((ROOT / "supabase/.temp/phase6e9-owner-window.json").read_text())
    out = ROOT / "supabase/.temp/phase6e9-close-receipt.json"
    if out.exists():
        raise RuntimeError("existing_closure_receipt_inspect_before_retry")
    expected = {"memberA": ("zorgeyouri+6e9-a-lid@gmail.com", "client"),
                "trainerA": ("zorgeyouri+6e9-a-trainer@gmail.com", "trainer"),
                "memberB": ("zorgeyouri+6e9-b-lid@gmail.com", "client")}
    assert len(receipt["accounts"]) == 3
    ids = ",".join(lit(a["id"]) for a in receipt["accounts"])
    rows = query("select p.id,p.role,p.email,p.trainer_id,u.email auth_email from public.profiles p join auth.users u on u.id=p.id where p.id in (" + ids + ")")
    assert len(rows) == 3
    trainer = next(a["id"] for a in receipt["accounts"] if a["name"] == "trainerA")
    for account in receipt["accounts"]:
        row = next(r for r in rows if r["id"] == account["id"])
        email, role = expected[account["name"]]
        assert row["email"] == row["auth_email"] == email and row["role"] == role
        assert row["trainer_id"] == (trainer if account["name"] == "memberA" else None)
    before = fingerprint(receipt)
    keys = call(MGMT + "/api-keys?reveal=true", method="GET")
    service = next(k["api_key"] for k in keys if k["name"] == "service_role")
    tokens = []
    # Standard Auth-generated test sessions, no email and no owner impersonation.
    for account in receipt["accounts"]:
        email = expected[account["name"]][0]
        link = call(BASE + "/auth/v1/admin/generate_link", {"type": "magiclink", "email": email}, key=service)
        assert link.get("user", {}).get("id", account["id"]) == account["id"]
        token_hash = link["hashed_token"]
        session = call(BASE + "/auth/v1/verify", {"type": "magiclink", "token_hash": token_hash}, key=PUB)
        assert session["user"]["id"] == account["id"]
        tokens.append(session["access_token"])
        link = session = token_hash = None
    workspaces = ",".join(lit(a["workspace"]) for a in receipt["accounts"] if a["workspace"])
    # Exact manifest-bound identities are rechecked inside the closing transaction.
    checks = " and ".join("exists(select 1 from auth.users where id=" + lit(a["id"]) + " and email=" + lit(expected[a["name"]][0]) + ")" for a in receipt["accounts"])
    result = query("begin;do $$begin if not (" + checks + ") then raise exception 'synthetic_identity_mismatch';end if;end$$;"
                   "update fmz6e9_private.config set enabled=false,proof_hash=null where id;"
                   "delete from auth.sessions where user_id in (" + ids + ");"
                   "delete from fmz6e9_private.subjects where workspace in (" + workspaces + ") and member_id in (" + ids + ");"
                   "select (select count(*) from fmz6e9_private.subjects) subjects,(select count(*) from auth.sessions where user_id in (" + ids + ")) sessions,(select enabled from fmz6e9_private.config where id) enabled;commit;")
    # Deletion of sessions plus the flag/subject checks invalidates still-signed JWTs.
    import urllib.error
    denied = []
    for token in tokens:
        try:
            call(BASE + "/functions/v1/fmz6e9-synthetic", {"op": "home"}, key=token)
            denied.append(False)
        except urllib.error.HTTPError as e:
            e.read()
            denied.append(e.code in (401,403,503))
    assert all(denied)
    secrets = call(MGMT + "/secrets", method="GET")
    if any(s["name"] == "FMZ6E9_PROOF" for s in secrets):
        call(MGMT + "/secrets", ["FMZ6E9_PROOF"], method="DELETE")
    after = fingerprint(receipt)
    assert before == after
    report = {"closed": True, "retained_synthetic_identities": 3, "no_password_changes": True,
              "no_email": True, "old_jwt_denied": denied, "before": before, "after": after,
              "prior_baseline_equal": before == receipt["after"], "state": result,
              "proof_removed": True, "production_touched": False}
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"closed": True, "retained_identities": 3, "old_jwt_denied": len(denied),
                      "existing_tables_unchanged": len(after), "proof_removed": True}))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Never emit raw Auth responses or generated-link fields.
        print(json.dumps({"error": type(e).__name__, "closure_requires_inspection": True}))
        raise SystemExit(1)
