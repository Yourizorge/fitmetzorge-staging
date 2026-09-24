"""Read-only classification of the exact CI bundle before public Git-blob upload."""
import base64, hashlib, json, os, pathlib, re, subprocess, sys
root=pathlib.Path(__file__).resolve().parents[3]
folder=pathlib.Path(sys.argv[1]).resolve()
if folder.parent!=(root/"supabase/.temp").resolve():raise SystemExit("evidence_scope")
data=(folder/"candidate.json").read_bytes();bundle=json.loads(data)
def git(*args):
    return subprocess.run([os.environ["FMZ_GIT"],*args],cwd=root,capture_output=True,check=False)
public={};new={};all_public=b""
for name,encoded in bundle["files"].items():
    raw=base64.b64decode(encoded)
    committed=git("show","HEAD:"+name)
    if committed.returncode==0:
        if committed.stdout.replace(b"\r\n",b"\n")!=raw.replace(b"\r\n",b"\n"):
            raise SystemExit("changed_existing_source:"+name)
        public[name]=hashlib.sha256(raw).hexdigest()
        all_public+=committed.stdout+b"\n"
    else:new[name]=raw
old=git("show","HEAD:supabase/migrations/20260915104711_phase6e10_sources_managed_windows.sql")
if old.returncode:raise SystemExit("public_source_missing")
all_public+=old.stdout
known_emails=set(re.findall(rb"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",all_public))
new_emails=set()
for name,raw in new.items():
    if re.search(rb"(sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}|-----BEGIN .*PRIVATE KEY|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",raw):
        raise SystemExit("credential_pattern:"+name)
    emails=set(re.findall(rb"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",raw))
    if emails-known_emails:raise SystemExit("nonpublic_email:"+name)
    new_emails |= emails
expected={
"supabase/migrations/20260916162120_phase6e11_final_app_integration.sql",
"supabase/migrations/20260924130052_phase6e11_private_transaction_audit.sql",
"supabase/migrations/20260924155822_phase6e11_rpc_bridge.sql",
"_offline/phase6e11/readiness_v1/txaudit/test_audit.py",
"_offline/phase6e11/readiness_v1/txaudit/common.py",
}
if set(new)!=expected:raise SystemExit("unexpected_unpublished_sources")
result={"candidate_sha256":hashlib.sha256(data).hexdigest(),"files":len(bundle["files"]),
"already_public_content":len(public),"unpublished_source_sha256":{p:hashlib.sha256(v).hexdigest() for p,v in new.items()},
"credential_pattern_hits":0,"nonpublic_email_addresses":0,"already_public_synthetic_aliases":len(new_emails),
"historical_evidence_or_database_rows_included":False,
"review_scope":"Three reviewed canonical SQL sources plus two synthetic audit-test source files; no runtime, captured DB rows, sessions, evidence or credentials."}
with (folder/"candidate-review.json").open("x") as f:json.dump(result,f,indent=2)
print(json.dumps(result))
