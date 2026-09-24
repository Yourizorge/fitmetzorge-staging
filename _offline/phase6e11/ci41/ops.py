"""Scoped CI dispatch/evidence client; credentials are captured in memory only."""
import argparse, base64, datetime, hashlib, importlib.util, json, os, pathlib
import re, subprocess, sys, urllib.error, urllib.request, uuid, zipfile, io
from urllib.parse import urlsplit

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme != 'https':
            raise RuntimeError('https_redirect_required')
        redirected = super().redirect_request(request, fp, code, msg, headers, newurl)
        if urlsplit(request.full_url).netloc != urlsplit(newurl).netloc:
            redirected.remove_header('Authorization')
        return redirected

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE="https://api.github.com/repos/Yourizorge/fitmetzorge-staging"
WORKFLOW="phase6e11-db41.yml"
def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,value):
    data=(json.dumps(value,sort_keys=True,indent=2)+"\n").encode()
    with path.open("xb") as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
    return sha(data)
def git(*args,input=None):
    return subprocess.run([os.environ["FMZ_GIT"],*args],cwd=ROOT,input=input,
        capture_output=True,text=True,timeout=60,check=True).stdout.strip()
def token():
    data=git("credential","fill",input="protocol=https\nhost=github.com\n\n")
    values=dict(line.split("=",1) for line in data.splitlines() if "=" in line)
    if not values.get("password"):raise RuntimeError("github_credential_missing")
    return values["password"]
def api(path,method="GET",body=None,raw=False):
    if not re.fullmatch(r"/(?:git/blobs(?:/[a-f0-9]{40})?|actions/.*|pages(?:/.*)?|commits/.*)",path):
        raise RuntimeError("api_path_boundary")
    headers={"Authorization":"Bearer "+token(),"Accept":"application/vnd.github+json",
             "X-GitHub-Api-Version":"2022-11-28"}
    request=urllib.request.Request(BASE+path,method=method,headers=headers,
        data=None if body is None else json.dumps(body).encode())
    try:
        with urllib.request.build_opener(SafeRedirect()).open(request,timeout=90) as response:
            data=response.read(30000000)
            return data if raw else (json.loads(data) if data else None)
    except urllib.error.HTTPError as error:
        raise RuntimeError("github_http_"+str(error.code)+":"+path) from None
def prepare():
    folder=ROOT/"supabase/.temp"/("phase6e11-ci41-"+uuid.uuid4().hex)
    folder.mkdir()
    spec=importlib.util.spec_from_file_location("ci_runner",HERE/"runner.py")
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    candidates=sorted((ROOT/"supabase/migrations").glob("*.sql"))
    candidates+=sorted((ROOT/"supabase/tests").glob("*.sql"))
    candidates += [ROOT/p for p in sorted(runner.EXTRAS)]
    files={}
    for path in candidates:
        name=path.relative_to(ROOT).as_posix()
        if not runner.allowed(name):raise RuntimeError("source_path")
        data=path.read_bytes()
        if re.search(rb"(sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}",data):
            raise RuntimeError("source_secret_pattern")
        files[name]=base64.b64encode(data).decode()
    bundle={"format":1,"files":files}
    digest=write(folder/"candidate.json",bundle)
    dirty=git("ls-files","-m","-o","--exclude-standard").splitlines()
    hashes={p:sha((ROOT/p).read_bytes()) for p in dirty if (ROOT/p).is_file()}
    write(folder/"before.json",{"head":git("rev-parse","HEAD"),"branch":git("branch","--show-current"),
        "dirty_sha256":hashes,"canonical_count":len(list((ROOT/"supabase/migrations").glob("*.sql")))})
    print(json.dumps({"folder":str(folder),"sha256":digest,"files":len(files)}))
def upload(folder):
    data=(folder/"candidate.json").read_bytes()
    result=api("/git/blobs","POST",{"content":base64.b64encode(data).decode(),"encoding":"base64"})
    receipt={"blob":result["sha"],"sha256":sha(data),"bytes":len(data),"canonical_commit":False}
    write(folder/"blob.json",receipt);print(json.dumps(receipt))
def dispatch(folder):
    if (folder/"dispatch.json").exists():raise RuntimeError("no_automatic_retry")
    blob=json.loads((folder/"blob.json").read_text())
    args={"ref":"main","inputs":{"candidate_blob":blob["blob"],"candidate_sha256":blob["sha256"]}}
    api("/actions/workflows/"+WORKFLOW+"/dispatches","POST",args)
    write(folder/"dispatch.json",{"at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "head":git("ls-remote","origin","refs/heads/main").split()[0],**args})
    print("DISPATCHED_ONCE")
def status(folder):
    result=api("/actions/workflows/"+WORKFLOW+"/runs?per_page=10&event=workflow_dispatch")
    digest=json.loads((folder/"blob.json").read_text())["sha256"]
    rows=[{k:r.get(k) for k in ("id","status","conclusion","html_url","head_sha","display_title")}
          for r in result["workflow_runs"] if digest in r["display_title"]]
    print(json.dumps(rows))
def collect(folder,run):
    meta=api("/actions/runs/"+str(run))
    if meta["status"]!="completed":raise RuntimeError("run_not_completed")
    blob=json.loads((folder/"blob.json").read_text())
    if blob["sha256"] not in meta["display_title"]:raise RuntimeError("run_candidate_mismatch")
    target=folder/("run-"+str(run));target.mkdir(exist_ok=False)
    data=api("/actions/runs/"+str(run)+"/logs",raw=True)
    (target/"logs.zip").write_bytes(data)
    write(target/"run.json",{k:meta.get(k) for k in ("id","status","conclusion","html_url","head_sha","display_title","created_at","updated_at")})
    evidence={}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            current=None;parts=[]
            for line in archive.read(name).decode(errors="replace").splitlines():
                line=re.sub(r"^\d{4}-\d\d-\d\dT\S+\s+","",line)
                if line.startswith("FMZ_EVIDENCE_BEGIN "):
                    _,current,expected=line.split();parts=[]
                elif current and line.startswith("FMZ_DATA "):parts.append(line[9:])
                elif current and line=="FMZ_EVIDENCE_END "+current:
                    raw=base64.b64decode("".join(parts),validate=True)
                    if sha(raw)!=expected:raise RuntimeError("evidence_digest")
                    if current in evidence:
                        if evidence[current]!=expected:raise RuntimeError("duplicate_evidence_changed")
                    else:
                        if not re.fullmatch(r"[a-zA-Z0-9_.-]+\.(json|txt)",current):raise RuntimeError("evidence_path")
                        (target/current).write_bytes(raw);evidence[current]=expected
                    current=None
    write(target/"manifest.json",{"log_sha256":sha(data),"evidence":evidence,"run":run,"candidate_sha256":blob["sha256"]})
    print(json.dumps({"folder":str(target),"files":len(evidence),"conclusion":meta["conclusion"]}))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("mode",choices=("prepare","upload","dispatch","status","collect","pages"));p.add_argument("folder",nargs="?");p.add_argument("--run",type=int)
    args=p.parse_args()
    if args.mode=="prepare":prepare()
    elif args.mode=="pages":
        print(json.dumps(api("/pages")))
    else:
        folder=pathlib.Path(args.folder).resolve()
        if folder.parent!=(ROOT/"supabase/.temp").resolve() or not folder.name.startswith("phase6e11-ci41-"):raise RuntimeError("evidence_scope")
        if args.mode=="upload":upload(folder)
        elif args.mode=="dispatch":dispatch(folder)
        elif args.mode=="status":status(folder)
        elif args.mode=="collect":collect(folder,args.run)
