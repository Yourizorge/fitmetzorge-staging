// Local migration rebuild verifier for FitMetZorge staging.
// Starts a temporary vanilla PostgreSQL cluster with minimal Supabase stubs.
// It is intentionally local-only: no remote database and no member data.
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync, spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "../..");
const migrationsDir = path.join(root, "supabase", "migrations");
const pgBin = process.env.FMZ_POSTGRES_BIN || "C:\\Program Files\\PostgreSQL\\18\\bin";
const initdb = path.join(pgBin, "initdb.exe");
const pgCtl = path.join(pgBin, "pg_ctl.exe");
const postgres = path.join(pgBin, "postgres.exe");
const psql = path.join(pgBin, "psql.exe");
const keepTemp = process.argv.includes("--keep-temp");
const full = process.argv.includes("--full");

function run(file, args, options = {}) {
  const result = spawnSync(file, args, {
    cwd: options.cwd || root,
    env: options.env || process.env,
    encoding: "utf8",
    windowsHide: true,
    maxBuffer: 20_000_000,
  });
  if (result.status !== 0) {
    const error = new Error(options.label || path.basename(file));
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    error.status = result.status;
    throw error;
  }
  return result.stdout;
}

function psqlRun(port, args, options = {}) {
  return run(psql, [
    "-h", "127.0.0.1",
    "-p", String(port),
    "-U", "postgres",
    "-d", "postgres",
    "-v", "ON_ERROR_STOP=1",
    ...args,
  ], {
    ...options,
    env: {
      ...process.env,
      PGOPTIONS: "-c search_path=public,extensions",
    },
  });
}

function waitForPostgres(port) {
  let lastError;
  for (let attempt = 0; attempt < 60; attempt += 1) {
    const result = spawnSync(psql, [
      "-h", "127.0.0.1",
      "-p", String(port),
      "-U", "postgres",
      "-d", "postgres",
      "-v", "ON_ERROR_STOP=1",
      "-At",
      "-c", "select 1",
    ], {
      cwd: root,
      env: process.env,
      encoding: "utf8",
      windowsHide: true,
      timeout: 2500,
      maxBuffer: 200_000,
    });
    if (result.status === 0 && result.stdout.trim() === "1") return;
    lastError = result.stderr || result.stdout;
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 500);
  }
  throw new Error(`postgres_start_timeout:${lastError || "no_response"}`);
}

function sqlLiteral(value) {
  return "'" + value.replace(/'/g, "''") + "'";
}

const requiredObjects = [
  "public.profiles",
  "public.coach_workspaces",
  "public.user_settings",
  "public.user_onboarding",
  "public.entitlements",
  "public.recovery_logs",
  "public.exercises",
  "public.training_plans",
  "public.training_plan_days",
  "public.training_plan_exercises",
  "public.workout_sessions",
  "public.workout_set_logs",
  "public.nutrition_preferences",
  "public.progress_preferences",
  "public.ai_threads",
];

function main() {
  for (const file of [initdb, pgCtl, postgres, psql]) {
    if (!fs.existsSync(file)) throw new Error(`postgres_binary_missing:${file}`);
  }

  const files = fs.readdirSync(migrationsDir)
    .filter(file => file.endsWith(".sql"))
    .sort();
  const hasPgCron = fs.existsSync(path.join(pgBin, "..", "share", "extension", "pg_cron.control"));
  let runnable = files;
  if (!full && !hasPgCron) {
    const firstUnsupported = files.findIndex(file =>
      fs.readFileSync(path.join(migrationsDir, file), "utf8").includes("pg_cron")
    );
    if (firstUnsupported >= 0) runnable = files.slice(0, firstUnsupported);
  }
  const skipped = files.filter(file => !runnable.includes(file));
  const tempRoot = process.env.FMZ_REBUILD_TEMP_ROOT || require("node:os").tmpdir();
  const work = fs.mkdtempSync(path.join(tempRoot, "fmz-local-rebuild-"));
  const dataDir = path.join(work, "data");
  const logFile = path.join(work, "postgres.log");
  const port = 55432 + Math.floor(Math.random() * 1000);
  let started = false;
  let server = null;
  let logFd = null;

  try {
    run(initdb, ["-D", dataDir, "-A", "trust", "-U", "postgres"], { label: "initdb" });
    logFd = fs.openSync(logFile, "a");
    server = require("node:child_process").spawn(postgres, ["-D", dataDir, "-p", String(port), "-h", "127.0.0.1"], {
      cwd: root,
      detached: true,
      stdio: ["ignore", logFd, logFd],
      windowsHide: true,
    });
    server.unref();
    waitForPostgres(port);
    started = true;

    const bootstrap = path.join(work, "bootstrap.sql");
    fs.writeFileSync(bootstrap, `
create schema if not exists extensions;
create extension if not exists pgcrypto with schema extensions;
create extension if not exists pg_trgm with schema extensions;

do $$
begin
  create role anon nologin;
exception when duplicate_object then null;
end $$;

do $$
begin
  create role authenticated nologin;
exception when duplicate_object then null;
end $$;

do $$
begin
  create role service_role nologin bypassrls;
exception when duplicate_object then null;
end $$;

create schema if not exists auth;
create table if not exists auth.users (
  id uuid primary key,
  email text,
  email_confirmed_at timestamptz,
  raw_user_meta_data jsonb not null default '{}'::jsonb
);

create or replace function auth.uid()
returns uuid
language sql
stable
as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;

grant usage on schema auth to anon, authenticated, service_role;
grant select on auth.users to anon, authenticated;
grant all on auth.users to service_role;
`, "utf8");
    psqlRun(port, ["-f", bootstrap], { label: "bootstrap" });

    const applied = [];
    for (const file of runnable) {
      const migration = path.join(migrationsDir, file);
      try {
        psqlRun(port, ["-f", migration], { label: file });
        applied.push(file);
      } catch (error) {
        console.error(JSON.stringify({
          ok: false,
          failed_migration: file,
          applied_count: applied.length,
          stdout: error.stdout,
          stderr: error.stderr,
        }, null, 2));
        process.exitCode = 1;
        return;
      }
    }

    const objectQuery = `
select jsonb_pretty(jsonb_build_object(
  'objects', jsonb_object_agg(name, to_regclass(name) is not null order by name),
  'rls_tables', (
    select jsonb_agg(relname order by relname)
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relrowsecurity
      and c.relname in (${requiredObjects.map(o => sqlLiteral(o.split(".")[1])).join(",")})
  )
))
from (values ${requiredObjects.map(o => `(${sqlLiteral(o)})`).join(",")}) objects(name);
`;
    const snapshot = psqlRun(port, ["-At", "-c", objectQuery], { label: "object_snapshot" }).trim();
    console.log(JSON.stringify({
      ok: true,
      postgres: execFileSync(psql, ["--version"], { encoding: "utf8", windowsHide: true }).trim(),
      applied_count: applied.length,
      applied_first: applied[0],
      applied_last: applied[applied.length - 1],
      skipped_count: skipped.length,
      skipped_reason: skipped.length && !hasPgCron ? "local_pg_cron_extension_missing" : null,
      skipped,
      snapshot: JSON.parse(snapshot),
    }, null, 2));
  } finally {
    if (started) {
      try {
        run(pgCtl, ["-D", dataDir, "-m", "fast", "-w", "stop"], { label: "pg_ctl_stop" });
      } catch {
        // Best-effort cleanup. The temp directory is reported with --keep-temp.
        if (server && server.pid) {
          try {
            process.kill(server.pid);
          } catch {}
        }
      }
    }
    if (logFd !== null) {
      fs.closeSync(logFd);
      logFd = null;
    }
    if (!keepTemp) {
      fs.rmSync(work, { recursive: true, force: true });
    } else {
      console.error(`kept_temp=${work}`);
    }
  }
}

main();
