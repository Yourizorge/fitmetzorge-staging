"""Disposable Docker-only CI. Never connects to a linked/hosted database."""
import base64, hashlib, importlib.util, io, json, os, pathlib, re
import shutil, subprocess, sys, tarfile, time, types, unittest, urllib.request
from fixture_compat import adapt

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CLI_VERSION = "2.117.0"
CLI_SHA = "69c05f85b9e47ee706d30f1a6ca8a526b4e337bfd12c7ef1ef522d24e7280d24"
M41 = "20260924155822_phase6e11_rpc_bridge.sql"
M41_SHA = "4d474becdc5c3a7343562602115f9333b5cffc6bed0c323fca3abc560843af7d"
SPLINTER = "e74a9e36cb12258cb67d1464bc1cb196e9cd8446"
SPLINTER_SHA = "d8d558baad3e03832e521c527907fa50a9a172fabd899dd0f5c2504a5a0e9349"
EXTRAS = {
 "supabase/tests/phase6d0-migration-identity-check.cjs",
 "supabase/tests/phase6d0-migration-identity-check.test.cjs",
 "_offline/phase6e11/readiness_v1/txaudit/test_audit.py",
 "_offline/phase6e11/readiness_v1/txaudit/common.py",
 "_offline/phase6e11/fingerprint_v1/guard.py",
}
def allowed(path):
    return bool(re.fullmatch(r"supabase/migrations/\d+_[a-z0-9_]+\.sql", path)
                or re.fullmatch(r"supabase/tests/\d+_[a-z0-9_]+\.sql", path)
                or path in EXTRAS)
def sha(data):
    return hashlib.sha256(data).hexdigest()
def advisor_sql(data):
    return "begin read only;set local statement_timeout='30s';set local pgrst.db_schemas='public,storage,graphql_public';\n"+data.decode()+";\nrollback;"
def clean(text):
    text = re.sub(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[JWT_REDACTED]", text)
    text = re.sub(r"(?i)postgres(?:ql)?://[^\s\"']+", "[LOCAL_DATABASE_URL]", text)
    return re.sub(r"(?i)(sb_secret_|sbp_|gh[pousr]_)[A-Za-z0-9_-]+", "[SECRET_REDACTED]", text)

class Gate:
    def __init__(self):
        if os.environ.get("GITHUB_REPOSITORY") != "Yourizorge/fitmetzorge-staging":
            raise RuntimeError("repository_boundary")
        if os.environ.get("GITHUB_REF") != "refs/heads/main":
            raise RuntimeError("branch_boundary")
        self.temp = pathlib.Path(os.environ["RUNNER_TEMP"])
        self.out = self.temp / "fmz-db41-evidence"
        self.out.mkdir(exist_ok=False)
        self.work = self.temp / "fmz-db41-stack"
        self.work.mkdir(exist_ok=False)
        self.sources = self.temp / "fmz-db41-sources"
        self.sources.mkdir(exist_ok=False)
        self.result = {"status":"NO_GO","phase":"init","run_id":os.environ["GITHUB_RUN_ID"],
            "commit":os.environ["GITHUB_SHA"],"cli":CLI_VERSION,"cli_sha256":CLI_SHA,
            "migrations_applied":0,"hosted_requests":0,"member_data_used":False,
            "external_ai_calls":0,"production_touched":False}
        self.serial = 0
    def save(self, name, value):
        data = (json.dumps(value, sort_keys=True, indent=2)+"\n").encode()
        path = self.out / name
        with path.open("xb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
    def command(self, label, args, sql=None, timeout=90, check=True):
        self.serial += 1
        start = time.monotonic()
        p = subprocess.run(args, cwd=self.work, input=sql, text=True, capture_output=True,
                           timeout=timeout, env={k:v for k,v in os.environ.items()
                           if k not in ("GH_READ_TOKEN","GITHUB_TOKEN","SUPABASE_ACCESS_TOKEN",
                                        "SUPABASE_DB_PASSWORD")})
        self.save("%03d-%s.json" % (self.serial,label), {
            "phase":self.result["phase"],"exitcode":p.returncode,
            "seconds":round(time.monotonic()-start,3),
            "stdout":clean(p.stdout)[-350000:],"stderr":clean(p.stderr)[-350000:]})
        if check and p.returncode:
            raise RuntimeError(label+"_exit_"+str(p.returncode))
        return p
    def sql(self, text, check=True):
        return self.command("psql",["docker","exec","-i",self.container,"psql",
            "-X","-U","postgres","-d","postgres","-qAt","-v","ON_ERROR_STOP=1"],
            sql=text,check=check)
    def rows(self, text):
        p = self.sql("select coalesce(json_agg(q),'[]') from ("+text+") q;")
        return json.loads(p.stdout.strip())
    def cli(self, *args, timeout=120):
        return self.command("cli-"+args[0], [str(self.binary),"--workdir",str(self.work),*args],
                            timeout=timeout)
    def fetch(self):
        blob = os.environ["CANDIDATE_BLOB"]
        expected = os.environ["CANDIDATE_SHA256"]
        if not re.fullmatch("[0-9a-f]{40}",blob) or not re.fullmatch("[0-9a-f]{64}",expected):
            raise RuntimeError("candidate_format")
        token = os.environ.pop("GH_READ_TOKEN")
        request = urllib.request.Request(
            "https://api.github.com/repos/Yourizorge/fitmetzorge-staging/git/blobs/"+blob,
            headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json"})
        with urllib.request.urlopen(request,timeout=30) as response:
            obj = json.loads(response.read(8000000))
        del token, request
        data = base64.b64decode(obj["content"])
        if sha(data) != expected:
            raise RuntimeError("candidate_digest")
        bundle = json.loads(data)
        names = list(bundle["files"])
        migrations = sorted(p for p in names if p.startswith("supabase/migrations/"))
        if len(migrations) != 41 or len({p.split("/")[-1].split("_")[0] for p in migrations}) != 41:
            raise RuntimeError("exactly_41_unique")
        if migrations[-1] != "supabase/migrations/"+M41:
            raise RuntimeError("migration41_name")
        manifest = {}
        for name, encoded in bundle["files"].items():
            if not allowed(name): raise RuntimeError("candidate_path_denied")
            raw = base64.b64decode(encoded,validate=True)
            path = self.sources / name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(raw)
            manifest[name] = sha(raw)
        if manifest[migrations[-1]] != M41_SHA:
            raise RuntimeError("migration41_changed")
        self.save("candidate.json",{"blob":blob,"sha256":expected,"sources":manifest})
        self.result["candidate_sha256"] = expected
        return migrations
    def install(self):
        url = "https://github.com/supabase/cli/releases/download/v"+CLI_VERSION+"/supabase_linux_amd64.tar.gz"
        with urllib.request.urlopen(url,timeout=60) as response:
            data = response.read(100000000)
        if sha(data) != CLI_SHA: raise RuntimeError("cli_digest")
        with tarfile.open(fileobj=io.BytesIO(data),mode="r:gz") as archive:
            member = archive.getmember("supabase")
            self.binary = self.temp/"fmz-supabase"
            self.binary.write_bytes(archive.extractfile(member).read())
            self.binary.chmod(0o700)
        self.cli("--version")
        self.cli("init","--yes")
        config = self.work/"supabase/config.toml"
        text = config.read_text()
        text = re.sub(r"(?m)^project_id\s*=.*$", 'project_id = "fmz-db41-ci"',text)
        text = re.sub(r"(?m)^major_version\s*=.*$", "major_version = 17",text)
        config.write_text(text)
        self.save("config-sha.json",{"sha256":sha(config.read_bytes()),"linked":False,
                                   "seed_files":[],"supabase_secrets":False})
        self.cli("db","start",timeout=600)
        containers = self.command("containers",["docker","ps","--format","{{.Names}}"]).stdout.splitlines()
        self.container = "supabase_db_fmz-db41-ci"
        if self.container not in containers: raise RuntimeError("database_container_missing")
        image = self.command("image",["docker","inspect","--format",
            '{"image_id":"{{.Image}}","image":"{{.Config.Image}}"}',self.container]).stdout
        meta = json.loads(image)
        meta["repository_digests"] = json.loads(self.command("digest",
            ["docker","image","inspect","--format","{{json .RepoDigests}}",meta["image_id"]]).stdout)
        meta["server"] = self.rows("select version(),current_setting('server_version_num') num")
        meta["extensions"] = self.rows("select name,default_version,installed_version from pg_available_extensions where name in ('pgcrypto','pg_trgm','pg_cron') order by name")
        self.save("platform.json",meta)
        if not 170000 <= int(meta["server"][0]["num"]) < 180000:
            raise RuntimeError("pg17_required")
        if len(meta["extensions"]) != 3: raise RuntimeError("real_extensions_missing")
        if self.rows("select tablename from pg_tables where schemaname='public'"):
            raise RuntimeError("not_empty_application_database")
        self.result["platform"] = meta
    def catalog(self):
        return self.rows("""
select p.oid::regprocedure::text name,pg_get_functiondef(p.oid) definition,proacl::text acl
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname in ('fmz6e11_private','fmz6e11_audit_private') and p.prokind='f' order by 1
""")
    def rebuild(self, migrations):
        dest = self.work/"supabase/migrations"
        dest.mkdir(exist_ok=True)
        for index, name in enumerate(migrations,1):
            self.result["phase"] = "migration_"+str(index)
            if index == 41:
                before = self.catalog()
                self.save("before41-functions.json",before)
            path = self.sources/name
            shutil.copyfile(path,dest/path.name)
            self.cli("migration","up","--local",timeout=120)
            self.result["migrations_applied"] = index
            print(json.dumps({"migration":index,"file":path.name,"status":"PASS"}),flush=True)
        after = self.catalog()
        self.save("after41-functions.json",after)
        if before != after: raise RuntimeError("existing_private_function_drift")
        history = self.rows("select version,name,cardinality(statements) statements from supabase_migrations.schema_migrations order by version")
        self.save("history.json",history)
        if [r["version"] for r in history] != [pathlib.Path(p).name.split("_")[0] for p in migrations]:
            raise RuntimeError("history_identity")
        self.result["clean_rebuild"] = "41/41_PASS"
        extensions = self.rows("select e.extname,e.extversion,n.nspname from pg_extension e join pg_namespace n on n.oid=e.extnamespace where e.extname in ('pgcrypto','pg_trgm','pg_cron') order by 1")
        self.save('installed-extensions.json',extensions)
        if len(extensions)!=3: raise RuntimeError('extensions_not_installed')
    def check_bridge(self):
        schema = "fmz6e11_workflow_audit"
        funcs = self.rows("select proname,prosecdef,proconfig,proacl::text from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='"+schema+"' order by 1")
        if len(funcs)!=2 or any(r["prosecdef"] or r["proconfig"]!=["search_path=pg_catalog, pg_temp"] for r in funcs):
            raise RuntimeError("bridge_function_acl")
        tables = self.rows("select relname,relrowsecurity,relacl::text from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='"+schema+"' and c.relkind='r' order by 1")
        if len(tables)!=2 or not all(r["relrowsecurity"] for r in tables): raise RuntimeError("bridge_rls")
        if self.rows("select enabled from "+schema+".control") != [{"enabled":False}]:
            raise RuntimeError("bridge_not_default_off")
        self.sql("create role fmz_ci_unprivileged;")
        denials = []
        for role in ("anon","authenticated","service_role","fmz_ci_unprivileged"):
            for target in ("select * from "+schema+".control","select * from "+schema+".intents",
                           "select "+schema+".call('{}'::jsonb)","select "+schema+".versions(null)"):
                p = self.sql("begin;set local role "+role+";"+target+";rollback;",False)
                if p.returncode==0 or "permission denied" not in p.stderr:
                    raise RuntimeError("bridge_access_not_denied")
                denials.append({"role":role,"target":target,"denied":True})
        p = self.sql("select "+schema+".call('{}'::jsonb);",False)
        if p.returncode==0 or "bridge_disabled" not in p.stderr: raise RuntimeError("bridge_default_entry")
        self.save("bridge-security.json",{"functions":funcs,"tables":tables,"denials":denials,
            "default_off":True,"auth_jwt_verification":"NOT_HOSTED_PROOF"})
    def regressions(self):
        folder = self.sources/"supabase/tests"
        sql_tests = sorted(folder.glob("*.sql"))
        self.result["sql_regressions_planned"] = len(sql_tests)
        for index, test in enumerate(sql_tests,1):
            raw = test.read_bytes()
            sql, adapted = adapt(test.name, raw)
            self.save('regression-%02d-source.json' % index, {'file':test.name,
                'original_sha256':sha(raw),'executed_sha256':sha(sql.encode()),
                'additive_current_fixture_prerequisites':adapted,
                'adapter_sha256':sha((HERE/'fixture_compat.py').read_bytes())})
            self.sql(sql)
            self.result["sql_regressions_passed"] = index
        self.command("identity-tests",["node","--test",str(folder/"phase6d0-migration-identity-check.test.cjs")])
        audit_dir = self.sources/"_offline/phase6e11/readiness_v1/txaudit"
        sys.path.insert(0,str(audit_dir))
        # Keep all 22 original test methods; replace only Windows process/bootstrap.
        sys.modules["local_cluster"] = types.SimpleNamespace(Cluster=None)
        spec = importlib.util.spec_from_file_location("ci_audit_tests",audit_dir/"test_audit.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        cls = module.AuditTests
        gate = self
        cls.sql = classmethod(lambda cls,q,ok=True:gate.sql(q,ok))
        cls.setUpClass = classmethod(lambda cls:None)
        cls.tearDownClass = classmethod(lambda cls:None)
        stream = io.StringIO()
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(cls)
        result = unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        self.save("audit-tests.json",{"tests":result.testsRun,"pass":result.wasSuccessful(),"output":clean(stream.getvalue())})
        if result.testsRun!=22 or not result.wasSuccessful(): raise RuntimeError("audit_regression")
    def advisors(self):
        url = "https://raw.githubusercontent.com/supabase/splinter/"+SPLINTER+"/splinter.sql"
        with urllib.request.urlopen(url,timeout=30) as response: data=response.read(1000000)
        if sha(data)!=SPLINTER_SHA: raise RuntimeError("advisor_source_digest")
        query = advisor_sql(data)
        p = self.sql(query)
        self.save("advisors.json",{"commit":SPLINTER,"sha256":SPLINTER_SHA,"output":clean(p.stdout),
            "executed_sql_sha256":sha(query.encode()),
            "scope":"local database security/performance; no hosted Auth configuration"})
        if "|ERROR|" in p.stdout: raise RuntimeError("advisor_errors")
        for line in p.stdout.splitlines():
            if "|WARN|" in line and "fmz6e11_workflow_audit" in line: raise RuntimeError("new_bridge_advisor_warning")
        self.cli("db","lint","--local","--level","warning",timeout=180)
        dry = self.cli("db","push","--local","--dry-run","--skip-vault",timeout=90)
        combined = (dry.stdout+dry.stderr).lower()
        if "up to date" not in combined or "would push" in combined:
            raise RuntimeError("dryrun_not_proven_empty")
        self.result["dry_run"] = "EMPTY"
    def run(self):
        try:
            self.result["phase"]="candidate"
            migrations=self.fetch()
            self.result["phase"]="platform"
            self.install()
            self.rebuild(migrations)
            self.result["phase"]="bridge_security"
            self.check_bridge()
            self.result["phase"]="regressions"
            self.regressions()
            self.result["phase"]="advisors_and_dryrun"
            self.advisors()
            self.result["status"]="CLEAN_CI_PASS"
            return 0
        except Exception as error:
            self.result["error_type"]=type(error).__name__
            self.result["error"]=clean(str(error))[:500]
            return 1
        finally:
            self.save("result.json",self.result)
            print(json.dumps(self.result),flush=True)

if __name__=="__main__":
    sys.exit(Gate().run())
