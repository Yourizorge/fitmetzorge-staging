"""Read-only scoped secret-source inventory. Never emits secret values or DSNs."""
import ctypes, importlib.util, json, os, pathlib, re, sys, urllib.request, urllib.error, uuid
from ctypes import wintypes
ROOT = pathlib.Path(__file__).resolve().parents[3]
PROJECT = "mokxyyullfhkfalopbzd"
sys.path.insert(0, str(ROOT / "_offline/phase6e11/ci41"))
import ops
spec=importlib.util.spec_from_file_location("sb_access",ROOT/"supabase/tests/phase6d0-staging-query.py")
sb=importlib.util.module_from_spec(spec);spec.loader.exec_module(sb)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RuntimeError("credential_redirect_forbidden")

def get(base, path, token):
    req=urllib.request.Request(base+path,headers={"Authorization":"Bearer "+token,
        "Accept":"application/json","User-Agent":"FitMetZorge-Staging-6E11-Access-Inventory"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=25) as response:
            return json.loads(response.read(2000000))
    except urllib.error.HTTPError as e:
        return {"unavailable_http_status":e.code}
    except Exception:
        return {"unavailable":True}

def windows_sources():
    adv=ctypes.WinDLL("Advapi32.dll")
    out=[]
    for pattern,kind in (("Supabase*","supabase_cli_store"),
                         ("FitMetZorge-staging-6E11-database","owner_scoped_database_store"),
                         ("fmz6e11-mokxyyullfhkfalopbzd-*","temporary_staging_store")):
        entries=ctypes.POINTER(ctypes.POINTER(sb.Credential))()
        count=wintypes.DWORD()
        found=adv.CredEnumerateW(pattern,0,ctypes.byref(count),ctypes.byref(entries))
        try:
            out.append({"source":kind,"entries":count.value if found else 0,
                        "secret_values_read_for_inventory":False})
        finally:
            if found:adv.CredFree(entries)
    return out

def env_file_sources():
    paths=[]
    for base, dirs, files in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in (".git","node_modules",".temp","__pycache__",".venv","venv")]
        for name in files:
            if name==".env" or name.startswith(".env.") or name.endswith(".env"):
                paths.append(pathlib.Path(base)/name)
    out=[]
    for path in paths[:100]:
        ignored=ops.git("check-ignore",str(path.relative_to(ROOT))) if not path.name.endswith((".example",".sample")) else ""
        if not ignored:
            out.append({"file":path.relative_to(ROOT).as_posix(),"ignored":False,"values_not_inspected":True})
            continue
        if path.stat().st_size>100000:
            out.append({"file":path.relative_to(ROOT).as_posix(),"skipped":"size_limit"})
            continue
        text=path.read_text(encoding="utf-8-sig")
        entries={}
        for line in text.splitlines():
            match=re.match(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$",line.strip())
            if match:entries[match[1]]=match[2].strip().strip(chr(34)+chr(39))
        names=[k for k,v in entries.items() if v and re.search(r"SUPABASE.*(?:PASSWORD|DB)|DATABASE_URL|POSTGRES|PGPASSWORD",k)]
        out.append({"file":path.relative_to(ROOT).as_posix(),"ignored":True,
                    "candidate_names":names,"staging_marker_present":PROJECT in text})
    return out

def main():
    target=ROOT/"supabase/.temp"/("phase6e11-access-"+uuid.uuid4().hex)
    target.mkdir()
    token=sb.credential()
    project_base="https://api.supabase.com/v1/projects/"+PROJECT
    ssl=get(project_base,"/ssl-enforcement",token)
    jit=get(project_base,"/jit-access",token)
    mapping=get(project_base,"/database/jit",token)
    del token
    gh=ops.token()
    secrets=get(ops.BASE,"/actions/secrets",gh)
    environments=get(ops.BASE,"/environments",gh)
    env_secrets=[]
    for env in environments.get("environments",[])[:20]:
        name=env.get("name")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}",name or ""):continue
        result=get(ops.BASE,"/environments/"+name+"/secrets",gh)
        env_secrets.append({"environment":name,"names":[x["name"] for x in result.get("secrets",[])],
                           "unavailable":result.get("unavailable_http_status")})
    del gh
    result={
      "project":PROJECT,"head":ops.git("rev-parse","HEAD"),
      "windows_sources":windows_sources(),
      "process_environment_candidate_names":[k for k,v in os.environ.items() if v and re.search(r"SUPABASE|DATABASE_URL|POSTGRES|PGPASSWORD|PGPASSFILE",k)],
      "gitignored_env_sources":env_file_sources(),
      "github_actions_secret_names":[x["name"] for x in secrets.get("secrets",[])],
      "github_secrets_unavailable":secrets.get("unavailable_http_status"),
      "github_environment_secrets":env_secrets,
      "ssl_configuration":ssl,"temporary_access_configuration":jit,
      "temporary_access_mapping":{"available":not any(k.startswith("unavailable") for k in mapping),
                                  "response_type":type(mapping).__name__},
      "database_password_read":False,"secret_values_in_evidence":False,"hosted_writes":0
    }
    ops.write(target/"inventory.json",result)
    print(json.dumps({"folder":str(target),**result}))
if __name__=="__main__":
    try:main()
    except Exception as e:
        print(json.dumps({"status":"INVENTORY_STOP","error_type":type(e).__name__}))
        sys.exit(1)
