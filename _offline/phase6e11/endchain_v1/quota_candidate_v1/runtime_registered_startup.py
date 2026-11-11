"""Source-bound local GoTrue process. Context owns admission and accounting.

Serve-only avoids Auth migrations. HTTP readiness is not worker terminality.
No hosted endpoint, inherited Auth configuration, login, or account adoption.
"""
import base64
import contextlib
import hashlib
import hmac
import json
import os
import pathlib
import re
import secrets
import subprocess
import sys
import time
import urllib.parse
import urllib.request

import auth_failure_transport as transport
import native_runtime
import admission_auth_runtime_profile as profile
from . import runtime_registered_costs as costs

IMAGE = "supabase/gotrue@sha256:1736a63078f5922b198c4cbe50f80ab9a2d3b54fe8b7b6cfb2e9dc5dbbc12c6b"
AUTH_CA = "/etc/fmz/ci-ca.crt"
ORIGIN = "http://127.0.0.1:59999"
PG_NAME = "supabase_db_fmz-db41-ci"
# Passive reads in the already verified container: no connections or HTTP retry.
READINESS_POLLS = 40
READINESS_TIMEOUT = 12
READINESS_SCRIPT = r'''i=0
while [ "$i" -lt 40 ]; do
  i=$((i+1))
  seen=0
  for table in /proc/net/tcp /proc/net/tcp6; do
    [ -r "$table" ] || continue
    seen=1
    while read -r slot local remote state rest; do
      case "$local:$state" in
        *:270F:0A) printf '{"status":"ready","polls":%s}\n' "$i"; exit 0;;
      esac
    done < "$table"
  done
  if [ "$seen" -eq 0 ]; then
    printf '{"status":"unavailable","polls":%s}\n' "$i"; exit 0
  fi
  [ "$i" -eq 40 ] || sleep 0.25 || exit 1
done
printf '{"status":"expired","polls":%s}\n' "$i"
'''
META = """select jsonb_build_object(
 'database',current_database(),'role',current_user,
 'version',current_setting('server_version_num')::int,
 'oid',(select oid::bigint from pg_database where datname=current_database()),
 'ssl',exists(select 1 from pg_stat_ssl where pid=pg_backend_pid() and ssl),
 'statement_timeout',current_setting('statement_timeout'),
 'lock_timeout',current_setting('lock_timeout'),
 'sessions',(select count(*) from auth.sessions),
 'registry_empty',not exists(select 1 from fmz6e11_controller_private.runs)
   and not exists(select 1 from fmz6e11_controller_private.steps)
   and not exists(select 1 from fmz6e11_controller_private.evidence)) value"""
ACTIVE = """select count(*) n from pg_stat_activity
 where usename='supabase_auth_admin' and pid<>pg_backend_pid()"""
BOUND = """select count(*) n,count(*) filter(where s.ssl is true) tls
 from pg_stat_activity a left join pg_stat_ssl s on s.pid=a.pid
 where a.usename='supabase_auth_admin' and a.datid=%s
 and a.application_name=%s and a.client_addr=%s::inet"""


def source_program():
    """Explicit dispatcher inventory, not a fabricated full managed bound."""
    return {
        "format": "registered-startup-source-program-v1",
        "image": IMAGE, "argv": ["auth", "serve"], "migrations": False,
        "native_reads": ["target_before", "auth_backend_before",
            "managed_stats_before_start", "auth_target_connection",
            "auth_backend_after_stop", "managed_stats_after_stop"],
        "explicit_native_read_ceiling": 6,
        "health_attempts": 1, "health_terminal_is_db_worker_terminal": False,
        "readiness": {"command_id": "auth_listen_ready", "kind": "docker",
            "process_attempts": 1, "passive_poll_ceiling": READINESS_POLLS,
            "poll_interval_seconds": 0.25, "process_deadline_seconds": READINESS_TIMEOUT,
            "http_attempts": 0, "sql_commands": 0, "mint_barrier": False},
        "create_ceiling": 3, "create_declared_capacity_each": 128,
        "seed_normal_explicit_commands": 9, "seed_fault_explicit_ceiling": 9,
        "seed_lost_commit_retry": False,
        "preseed_scope_explicit_commands": 10,
        "preauth_profile_normal_commands": 10,
        "preauth_profile_limit_including_rollback": 11,
        "preauth_profile_connection_calls": 2,
        "preauth_profile_source": "admission_auth_runtime_profile.command_register",
        "parent_engine_native_formula": "3+5*N",
        "parent_engine_delete_declared_formula": "128*N",
        "managed_startup_full_bound": 3, "driver_implicit_sql_bound": 0,
        "derived_cost_contract": costs.source_bound_contract(),
        "whole_lifetime_observer": "before-start through stopped process and absent Auth backends",
        "lifetime_overlaps_core_managed": True,
        "root_total": None, "full_chain_admission": False}


def require(value, code):
    if not value:
        raise ValueError("registered_startup_" + code)


def configuration():
    return {
        "GOTRUE_API_HOST": "0.0.0.0", "GOTRUE_API_PORT": "9999",
        "GOTRUE_DB_DRIVER": "postgres", "GOTRUE_DB_MAX_POOL_SIZE": "1",
        "GOTRUE_DB_MAX_IDLE_POOL_SIZE": "1", "GOTRUE_DB_CONN_PERCENTAGE": "0",
        "GOTRUE_DB_CLEANUP_ENABLED": "false", "GOTRUE_DB_ADVISOR_ENABLED": "false",
        "GOTRUE_METRICS_ENABLED": "false", "GOTRUE_TRACING_ENABLED": "false",
        "GOTRUE_PROFILER_ENABLED": "false", "GOTRUE_RELOADING_NOTIFY_ENABLED": "false",
        "GOTRUE_RELOADING_POLLER_ENABLED": "false", "GOTRUE_RELOADING_SIGNAL_ENABLED": "false",
        "GOTRUE_INDEX_WORKER_ENSURE_USER_SEARCH_INDEXES_EXIST": "false",
        "GOTRUE_INDEX_WORKER_MAX_USERS_THRESHOLD": "0",
        "GOTRUE_MAILER_TEMPLATE_RELOADING_ENABLED": "false",
        "GOTRUE_MAILER_EMAIL_BACKGROUND_SENDING": "false",
        "GOTRUE_PASSWORD_HIBP_ENABLED": "false",
        "GOTRUE_OAUTH_SERVER_ENABLED": "false", "GOTRUE_CUSTOM_OAUTH_ENABLED": "false",
        "GOTRUE_SITE_URL": ORIGIN, "API_EXTERNAL_URL": ORIGIN,
        "GOTRUE_JWT_ISSUER": "https://" + native_runtime.PROJECT + ".supabase.co/auth/v1",
        "GOTRUE_JWT_ADMIN_ROLES": "service_role", "GOTRUE_JWT_AUD": "authenticated",
        "GOTRUE_JWT_DEFAULT_GROUP_NAME": "authenticated", "GOTRUE_JWT_EXP": "3600",
        "GOTRUE_DISABLE_SIGNUP": "true", "GOTRUE_MAILER_AUTOCONFIRM": "true",
        "GOTRUE_EXTERNAL_EMAIL_ENABLED": "true",
        "GOTRUE_SECURITY_REFRESH_TOKEN_ROTATION_ENABLED": "true",
        "GOTRUE_LOG_LEVEL": "panic"}


def _jwt(secret, role):
    require(role in ("service_role", "anon"), "service_key_role")
    encode = lambda value: base64.urlsafe_b64encode(json.dumps(
        value, separators=(",", ":")).encode()).decode().rstrip("=")
    body = encode({"alg": "HS256", "typ": "JWT"}) + "." + encode({
        "role": role, "iss": "supabase", "exp": int(time.time()) + 600})
    signature = base64.urlsafe_b64encode(hmac.new(
        secret.encode(), body.encode(), hashlib.sha256).digest()).decode().rstrip("=")
    return body + "." + signature


def health():
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
        transport.NoRedirect(), transport.StrictHTTPHandler())
    request = urllib.request.Request(ORIGIN + "/health", method="GET")
    with opener.open(request, timeout=2) as response:
        body = transport.complete_body(response)
        require(response.status == 200, "health_status")
        value = json.loads(body)
        require(isinstance(value, dict) and isinstance(value.get("version"), str),
                "health_shape")
        require(re.fullmatch(r"v?2\.197\.0", value["version"]) is not None, "health_version")
        return {"http_status": 200, "version": value["version"],
                "db_worker_terminal": False}


class LocalServer:
    def __init__(self, owner):
        from .runtime_registered_bootstrap import Context
        require(type(owner) is Context and owner._entering and owner._admitted,
                "actual_admitted_context")
        self.owner = owner
        self.name = "fmz-registered-auth-" + owner.binding["run_id"].replace("-", "")
        self.container_id = None
        self.start_attempted = self.stop_attempted = False
        self.runtime = self.db = None
        self.parameters = self.dsn = self.admin = self.anon = None
        self.ca_path = None
        self.profile_receipt = None
        self.started_stats = self.final_stats = self.managed_total = None
        self.pg = self.auth = None
        self.closed = False

    def __repr__(self):
        return "<LocalServer private credentials redacted>"

    def _call(self, name, kind, action):
        return self.owner._local_call(name, kind, action)

    def _docker(self, name, args, *, env=None, timeout=10):
        def run():
            p = subprocess.run(["docker", *args], capture_output=True, text=True,
                               timeout=timeout, env=env)
            require(p.returncode == 0, name + "_failed")
            if name == "auth_start":
                require(re.fullmatch("[a-f0-9]{64}", p.stdout.strip()), "auth_start_unknown")
            if name == "pg_password":
                require(bool(p.stdout.strip()), "missing_local_password")
            return p.stdout.strip()
        return self._call(name, "docker", run)

    def _sql(self, name, sql, args=None):
        def execute():
            cursor = self.db.execute(sql, args)
            value = cursor.fetchone() if cursor.description else None
            if name in source_program()['native_reads']:
                self.owner._remember('startup-observation', {'command_id': 'auth.' + name,
                    'sql_sha256': hashlib.sha256(sql.encode()).hexdigest(), 'value': value,
                    'additional_sql_commands': 0, 'query_text_read': False})
            return value
        return self._call(name, "native_sql", execute)

    def _inspect(self, name, target):
        return self._docker(name, ["inspect", "--format", "{{json .}}", target])

    def _wait_listener(self):
        require(self.container_id is not None and self.auth["Id"] == self.container_id,
                "readiness_owned_process")
        def wait():
            started = time.monotonic()
            result = subprocess.run(["docker", "exec", self.container_id,
                "/bin/sh", "-c", READINESS_SCRIPT], capture_output=True, text=True,
                timeout=READINESS_TIMEOUT)
            require(result.returncode == 0, "readiness_process_failed")
            value = json.loads(result.stdout)
            require(type(value) is dict and set(value) == {"status", "polls"}
                and value["status"] in ("ready", "expired", "unavailable")
                and type(value["polls"]) is int and 1 <= value["polls"] <= READINESS_POLLS,
                    "readiness_receipt")
            self.owner._remember("startup-readiness", {**value,
                "container_id": self.container_id, "elapsed_seconds": time.monotonic()-started,
                "poll_ceiling": READINESS_POLLS, "process_deadline_seconds": READINESS_TIMEOUT,
                "http_attempts": 0, "sql_commands": 0, "mint_barrier": False})
            require(value["status"] == "ready", "readiness_" + value["status"])
            return value
        return self._call("auth_listen_ready", "docker", wait)

    @staticmethod
    def _container(raw):
        value = json.loads(raw)
        require(isinstance(value, dict) and re.fullmatch("[a-f0-9]{64}", value.get("Id", "")),
                "container_identity")
        require(value["State"]["Running"] is True, "container_not_running")
        return value

    def open(self):
        require(self.owner.gate.container == PG_NAME, "exact_pg")
        pg_raw = self._inspect("pg_inspect", PG_NAME)
        def validate_pg():
            self.pg = self._container(pg_raw)
            self.pg.pop("Config", None)
            require(self.owner.stack["container"]["id"] == self.pg["Id"], "stack_pg_changed")
            networks = self.pg["NetworkSettings"]["Networks"]
            require(len(networks) == 1, "single_local_network")
            network = next(iter(networks))
            require(re.fullmatch("[a-zA-Z0-9_-]+", network), "network_name")
            ports = self.pg["NetworkSettings"]["Ports"]["5432/tcp"]
            endpoints = [p for p in ports if p["HostIp"] in ("127.0.0.1", "0.0.0.0")]
            require(len(endpoints) == 1 and re.fullmatch("[1-9][0-9]{0,4}", endpoints[0]["HostPort"]),
                    "pg_loopback_port")
            return network, int(endpoints[0]["HostPort"])
        network, port = self._call("validate.pg", "validation", validate_pg)
        password = self._docker("pg_password", [
            "exec", PG_NAME, "sh", "-c", 'printf %s "$POSTGRES_PASSWORD"'])
        def validate_connection():
            ca = pathlib.Path(self.owner.gate.work) / "fmz-ci-ca.crt"
            require(ca.is_file() and not ca.is_symlink(), "ca")
            require(hashlib.sha256(ca.read_bytes()).hexdigest() == self.owner.stack["ca_sha256"],
                    "original_stack_ca_changed")
            self.ca_path = str(ca.resolve(strict=True))
            require(not any(c in self.ca_path for c in (",", "\n", "\r")), "ca_mount_path")
            self.parameters = dict(host="127.0.0.1", hostaddr="127.0.0.1",
                port=port, dbname="postgres", user="postgres",
                password=password, sslmode="verify-full", sslrootcert=str(ca), connect_timeout=5,
                options="-c statement_timeout=5000 -c lock_timeout=1000")
            self.owner._remember("native-driver", costs.native_proof(self.parameters))
            self.runtime = native_runtime.NativeRuntime(self.parameters, ORIGIN, environment="disposable_ci")
            from psycopg.conninfo import make_conninfo
            self.dsn = make_conninfo(**self.parameters)
        self._call("validate.connection", "validation", validate_connection)
        self.db = self._call("observer_connect", "connection", self.runtime.connect)
        metadata_row = self._sql("target_before", META)
        before_row = self._sql("auth_backend_before", ACTIVE)
        def validate_target():
            metadata = metadata_row["value"]
            require(metadata["database"] == "postgres" and metadata["role"] == "postgres"
                and metadata["version"] // 10000 == 17 and metadata["ssl"] is True
                and metadata["oid"] == self.owner.stack["database_oid"]
                and metadata["statement_timeout"] in ("5s", "5000ms")
                and metadata["lock_timeout"] in ("1s", "1000ms")
                and metadata["sessions"] == 0 and metadata["registry_empty"] is True,
                    "target_boundary")
            require(before_row["n"] == 0, "prior_auth_backend")
            return metadata
        metadata = self._call("validate.target", "validation", validate_target)
        # Capability reduction must finish while no GoTrue process exists.
        # C owns its exact source-bound SQL program; the root prepays each step.
        self.profile_receipt = profile.run(self)
        from auth_protocol import STATS
        self.started_stats = self._sql("managed_stats_before_start", "select " + STATS + " value")["value"]
        self._docker("image_pull", ["pull", IMAGE], timeout=180)
        image_raw = self._docker("image_inspect", ["image", "inspect", IMAGE])
        def validate_image():
            images = json.loads(image_raw)
            require(len(images) == 1 and type(images[0].get("RepoDigests")) is list
                    and IMAGE in images[0]["RepoDigests"], "image_digest")
            image = images[0]
            require(re.fullmatch("sha256:[a-f0-9]{64}", image["Id"]), "image_id")
            return image
        image = self._call("validate.image", "validation", validate_image)
        secret = secrets.token_hex(32)
        self.admin, self.anon = _jwt(secret, "service_role"), _jwt(secret, "anon")
        db_url = ("postgres://supabase_auth_admin:" + urllib.parse.quote(password, safe="") +
            "@" + PG_NAME + ":5432/postgres?" + urllib.parse.urlencode({
                "application_name": self.name, "sslmode": "verify-full", "sslrootcert": AUTH_CA}))
        environment = {k: v for k, v in os.environ.items()
                       if not k.startswith(("GOTRUE_", "DATABASE_URL"))}
        environment.update(GOTRUE_DB_DATABASE_URL=db_url, GOTRUE_JWT_SECRET=secret)
        args = ["run", "-d", "--name", self.name, "--network", network,
            "--label", "fmz.registered.run=" + self.owner.binding["run_id"],
            "--mount", "type=bind,src=" + self.ca_path + ",dst=" + AUTH_CA + ",readonly",
            "-p", "127.0.0.1:59999:9999", "-e", "GOTRUE_DB_DATABASE_URL", "-e", "GOTRUE_JWT_SECRET"]
        for key, value in configuration().items():
            args.extend(["-e", key + "=" + value])
        args.extend([IMAGE, "auth", "serve"])
        self.start_attempted = True
        try:
            returned = self._docker("auth_start", args, env=environment, timeout=30)
            auth_raw = self._inspect("auth_inspect", returned)
            def validate_auth():
                actual = self._container(auth_raw)
                require(actual["Id"] == returned and actual["Image"] == image["Id"]
                and actual["Config"]["Image"] == IMAGE
                and actual["Config"]["Cmd"] == ["auth", "serve"]
                and actual["Config"]["Labels"].get("fmz.registered.run") == self.owner.binding["run_id"]
                    and actual["HostConfig"]["NetworkMode"] == network, "auth_process_binding")
                self.container_id, self.auth = returned, actual
                mounts = [m for m in actual["Mounts"] if m.get("Destination") == AUTH_CA]
                require(len(mounts) == 1 and mounts[0].get("Type") == "bind"
                        and mounts[0].get("Source") == self.ca_path and mounts[0].get("RW") is False,
                        "auth_ca_mount")
                require(hashlib.sha256(pathlib.Path(self.ca_path).read_bytes()).hexdigest()
                        == self.owner.stack["ca_sha256"], "auth_original_ca_changed")
                actual_env = dict(item.split("=", 1) for item in actual["Config"]["Env"])
                require(actual_env.get("GOTRUE_DB_DATABASE_URL") == db_url
                and actual_env.get("GOTRUE_JWT_SECRET") == secret
                and all(actual_env.get(k) == v for k, v in configuration().items()),
                    "auth_config_binding")
            self._call("validate.auth", "validation", validate_auth)
        finally:
            environment.clear()
            password = secret = db_url = None
        self._wait_listener()
        self._call("health", "http_health", health)
        auth_ip = self.auth["NetworkSettings"]["Networks"][network]["IPAddress"]
        connection_row = self._sql("auth_target_connection", BOUND,
                                   [metadata["oid"], self.name, auth_ip])
        self._call("validate.target_connection", "validation",
                   lambda: require(connection_row["n"] == 1 and connection_row["tls"] == 1,
                                   "actual_auth_target_tls"))
        # Do not retain Docker's secret-bearing Config.Env in the Context.
        self.auth.pop("Config", None)
        target = {"pg_container": self.pg["Id"], "database_oid": metadata["oid"],
                  "pg_system_identifier": self.owner.stack["pg_system_identifier"], "database": "postgres"}
        target_sha = hashlib.sha256(json.dumps(target, sort_keys=True).encode()).hexdigest()
        ref = self.owner._remember("isolation", {**target,
            "auth_container": self.container_id, "auth_config": configuration(),
            "source_binding": self.owner._source_snapshot, "image_id": image["Id"],
            "repo_digests": image["RepoDigests"], "pinned_image": IMAGE,
            "actual_auth_backend_matched": True, "actual_auth_backend_tls": True,
            "auth_sslmode": "verify-full", "auth_db_hostname": PG_NAME,
            "auth_ca_sha256": self.owner.stack["ca_sha256"],
            "readiness_is_not_mint_barrier": True, "migrations_invoked": False})
        return {"run_id": self.owner.binding["run_id"], "ci_run": self.owner.binding["ci_run"],
            "source_commit": self.owner.binding["source_commit"], "environment": "disposable_ci",
            "pg_container": self.pg["Id"], "auth_container": self.container_id,
            "pg_system_identifier": target["pg_system_identifier"], "database_oid": metadata["oid"],
            "db_target_sha256": target_sha, "auth_target_sha256": target_sha,
            "registry_empty": True, "pg17": True, "ssl": True, "native_ssl": True,
            "auth_ssl": True, "auth_sslmode": "verify-full", "auth_database_bound": True,
            "reused": False, "evidence_sha256": ref["sha256"]}

    @contextlib.contextmanager
    def suspend(self):
        require(self.db is not None and not self.db.closed, "observer_suspend")
        self._call("observer_suspend", "connection", self.db.close)
        require(self.db.closed, "observer_close_unconfirmed")
        self.db = None
        try:
            yield
        finally:
            primary = sys.exception()
            try: self.db = self._call("observer_reconnect", "connection", self.runtime.connect)
            except BaseException as error:
                if primary is None: raise
                primary.add_note("secondary_observer_reconnect:" + type(error).__name__)

    def close(self):
        require(not self.closed, "close_replay")
        self.closed = True
        errors = []
        if self.start_attempted and self.container_id:
            self.stop_attempted = True
            try:
                self._docker("auth_stop", ["stop", "--time", "5", self.container_id], timeout=10)
                raw = self._docker("auth_stopped_inspect", ["inspect", "--format", "{{json .State}}", self.container_id])
                state = json.loads(raw)
                require(state["Running"] is False and state["Pid"] == 0, "process_not_stopped")
                self.owner._remember('startup-process-stopped', {'container_id': self.container_id,
                    'running': state['Running'], 'pid': state['Pid'],
                    'account_deletion_proven': False})
            except BaseException as error: errors.append(error)
        elif self.start_attempted:
            errors.append(ValueError("registered_startup_unknown_container_retained"))
        try:
            if self.db is not None and not self.db.closed:
                require(self._sql("auth_backend_after_stop", ACTIVE)["n"] == 0, "backend_still_live")
                if self.started_stats is not None:
                    from auth_protocol import STATS, difference
                    self.final_stats = self._sql("managed_stats_after_stop", "select " + STATS + " value")["value"]
                    self.managed_total = difference(self.started_stats, self.final_stats)
        except BaseException as error: errors.append(error)
        finally:
            if self.db is not None:
                try: self._call("observer_close", "connection", self.db.close)
                except BaseException as error: errors.append(error)
            if self.runtime is not None: self.runtime.clear()
            if self.parameters is not None: self.parameters.clear()
            if self.auth is not None: self.auth.pop("Config", None)
            self.dsn = self.admin = self.anon = None
        if errors:
            primary = errors[0]
            for error in errors[1:]: primary.add_note("secondary_startup_close:" + type(error).__name__)
            raise primary
        return {"process_stopped": bool(self.stop_attempted),
                "managed_sql": self.managed_total, "account_deletion_proven": False}

