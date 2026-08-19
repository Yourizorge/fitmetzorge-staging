const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const sha256 = (source) => crypto.createHash("sha256").update(source).digest("hex").toUpperCase();
const canonicalLf = (source) => source.replace(/\r\n?/g, "\n");

const slice1 = read("supabase/migrations/20260818_phase4_nutrition_schema_slice1.sql");
const migration = read("supabase/migrations/20260819_phase4_nutrition_slice3_atomic_log_item_replacement.sql");
const verification = read("supabase/verification/20260819_phase4_nutrition_slice3_atomic_log_item_replacement_verification.sql");
const phase1 = read("assets/phase1-foundation.js");
const phase2 = read("assets/phase2-home-recovery.js");
const phase3 = read("assets/phase3-training-engine.js");
const memberUx = read("assets/member-ux-consistency.js");
const slice2 = read("assets/phase4-nutrition-slice2.js");

const checks = [];
function check(name, condition) {
  checks.push({ name, condition: Boolean(condition) });
}

function functionSource(sql, functionName) {
  const pattern = new RegExp(
    `create or replace function public\\.${functionName}\\([\\s\\S]*?\\n\\$\\$;`,
    "i"
  );
  return sql.match(pattern)?.[0] || "";
}

const replacement = functionSource(migration, "fmz_phase4_replace_food_log_item");
const normalLog = functionSource(slice1, "fmz_phase4_log_food_item");
const executable = migration.replace(/--.*$/gm, "");
const outsideFunction = executable.replace(/\$\$[\s\S]*?\$\$/g, "$$");
const verificationWithoutStrings = verification
  .replace(/--.*$/gm, "")
  .replace(/'(?:''|[^'])*'/g, "''");

const signature = /public\.fmz_phase4_replace_food_log_item\(\s*p_original_item_id uuid,\s*p_replacement_item_id uuid,\s*p_replacement_request_id uuid,\s*p_expected_original_updated_at timestamptz,\s*p_meal_moment text,\s*p_food_id uuid,\s*p_food_portion_id uuid,\s*p_consumed_quantity numeric,\s*p_consumed_unit text,\s*p_notes text\s*\)/i;

check("Slice 1 migration remains locked after line-ending normalization", sha256(canonicalLf(slice1)) === "D70A589FEF997C14FCC9805E746536C86556E22622C8952B33DE9CA222B36188");
check("staging project guard is explicit", migration.includes("mokxyyullfhkfalopbzd"));
check("production project ref is absent", !/hgoygcviutmynaihcvpd/i.test(migration + verification));
check("migration has one transaction begin", (executable.match(/^\s*begin\s*;/gim) || []).length === 1);
check("migration has one terminal commit", (executable.match(/^\s*commit\s*;/gim) || []).length === 1 && /commit\s*;\s*$/i.test(executable));
check("migration creates exactly one function", (migration.match(/create or replace function public\./gi) || []).length === 1);
check("replacement RPC exact signature exists", signature.test(migration));
check("replacement RPC returns jsonb", /returns jsonb/i.test(replacement));
check("replacement RPC is security definer", /security definer/i.test(replacement));
check("replacement RPC has safe search path", /set search_path = pg_catalog, public, pg_temp/i.test(replacement));
check("migration creates no table column index policy or trigger", !/\b(create\s+(table|index|unique\s+index|policy|trigger)|alter\s+table)\b/i.test(outsideFunction));
check("migration has no top-level data mutation", !/^\s*(insert|update|delete|truncate)\b/im.test(outsideFunction));
check("migration has no destructive object operation", !/\b(drop\s+(table|column|schema|function)|truncate|delete\s+from)\b/i.test(executable));
check("existing Slice 1 migration is not referenced for replacement", !/create or replace function public\.fmz_phase4_(log_food_item|archive_food_log_item|day_payload|has_full_nutrition_access)\b/i.test(migration));

check("authority derives only from auth uid", /v_user_id uuid := auth\.uid\(\)/i.test(replacement));
check("RPC has no caller user authority parameter", !/p_user_id|p_owner|p_trainer|p_role|p_entitlement/i.test(replacement));
check("original lookup enforces own user", /where i\.id = p_original_item_id\s+and i\.user_id = v_user_id/i.test(replacement));
check("replacement insert uses authenticated user", /p_replacement_item_id,\s+v_user_id,\s+v_original\.food_log_id/i.test(replacement));
check("original and replacement UUIDs must differ", /p_original_item_id = p_replacement_item_id/i.test(replacement));

check("normal request namespace is reused", /fmz_phase4_food_log_request:/i.test(replacement));
check("archive object namespace is reused", /fmz_phase4_food_log_item_request:/i.test(replacement));
check("original row is locked", /where i\.id = p_original_item_id[\s\S]*?for update;/i.test(replacement));
check("day log row is locked", /where l\.id = v_original\.food_log_id[\s\S]*?for update;/i.test(replacement));
check("replacement item UUID has object lock", /p_replacement_item_id::text/i.test(replacement));
check("crossed existing replacement IDs are rejected before object lock", (replacement.match(/where i\.id = p_replacement_item_id;/g) || []).length === 2 && replacement.indexOf("where i.id = p_replacement_item_id;") < replacement.indexOf("'fmz_phase4_food_log_item_request:' || v_user_id::text || ':' || p_replacement_item_id::text"));
check("replacement identity is rechecked after object lock", replacement.lastIndexOf("where i.id = p_replacement_item_id;") > replacement.indexOf("'fmz_phase4_food_log_item_request:' || v_user_id::text || ':' || p_replacement_item_id::text"));

check("expected updated timestamp is mandatory", /p_expected_original_updated_at is null/i.test(replacement));
check("stale expected timestamp is rejected", /v_original\.updated_at is distinct from p_expected_original_updated_at/i.test(replacement));
check("archive update rechecks expected timestamp", /updated_at = p_expected_original_updated_at/i.test(replacement));
check("inactive original cannot start a new replacement", /v_original\.status is distinct from 'active'/i.test(replacement));

check("request replay loads existing own replacement", /where i\.user_id = v_user_id\s+and i\.request_id = p_replacement_request_id/i.test(replacement));
check("request payload is stored immutably", /'replacement_request', v_request_payload/i.test(replacement));
check("changed payload reuse is rejected", /replacement request UUID was already used with a different payload/i.test(replacement));
check("replay requires archived original", /v_original\.status is distinct from 'archived'/i.test(replacement));
check("successful replay returns authoritative day", /'day', public\.fmz_phase4_day_payload\(v_user_id, v_log\.log_date\)[\s\S]*?'idempotent_replay', true/i.test(replacement));
check("replay branch precedes new active guard", replacement.indexOf("'idempotent_replay', true") < replacement.indexOf("v_original.status is distinct from 'active'"));
check("fresh result is marked non-replay", /'idempotent_replay', false/i.test(replacement));

check("replacement stays on original food log", !/p_log_date/i.test(replacement) && /v_original\.food_log_id/i.test(replacement));
check("target snapshot container is never changed", !/(insert into|update)\s+public\.food_logs/i.test(replacement));
check("consumed timestamp is preserved", /v_original\.consumed_at/i.test(replacement));
check("meal moment is limited to four approved values", /p_meal_moment not in \('breakfast', 'lunch', 'dinner', 'snacks'\)/i.test(replacement));
check("same meal preserves sort order", /v_sort_order := v_original\.sort_order/i.test(replacement));
check("changed meal appends deterministically", /coalesce\(max\(i\.sort_order\), -1\) \+ 1/i.test(replacement));

check("replacement food must be active", /f\.status = 'active'/i.test(replacement));
check("canonical food remains visible", /f\.catalog_scope = 'canonical'/i.test(replacement));
check("custom food requires own user", /f\.catalog_scope = 'custom' and f\.owner_user_id = v_user_id/i.test(replacement));
check("portion must belong to selected food", /p\.food_id = v_food\.id[\s\S]*?p\.status = 'active'/i.test(replacement));
check("portion unit must match", /p_consumed_unit is distinct from v_portion\.unit/i.test(replacement));
check("supported units match Slice 1", /p_consumed_unit not in \('g', 'ml', 'serving', 'piece'\)/i.test(replacement));

const calculationContracts = [
  /v_base_quantity := p_consumed_quantity \/ v_portion\.amount \* v_portion\.equivalent_amount/i,
  /v_base_unit := v_portion\.equivalent_unit/i,
  /v_calculation_basis := 'portion_conversion'/i,
  /v_base_unit = v_food\.reference_unit/i,
  /v_base_unit = 'g' and v_food\.reference_unit = 'ml' and v_food\.density_g_per_ml is not null/i,
  /v_base_unit = 'ml' and v_food\.reference_unit = 'g' and v_food\.density_g_per_ml is not null/i,
  /explicit portion or density conversion required for these units/i,
  /round\(v_food\.energy_kcal \* v_factor, 3\)/i,
  /round\(v_food\.protein_grams \* v_factor, 3\)/i,
  /round\(v_food\.carbohydrate_grams \* v_factor, 3\)/i,
  /round\(v_food\.fat_grams \* v_factor, 3\)/i
];
check("replacement calculation matches all Slice 1 contracts", calculationContracts.every((pattern) => pattern.test(replacement)));
check("normal logging still contains all compared calculation contracts", calculationContracts.every((pattern) => pattern.test(normalLog)));
check("replacement snapshots are server generated", /v_food\.name[\s\S]*?v_food\.provenance[\s\S]*?v_normalized_notes/i.test(replacement));
check("original mutation is archive-only", /update public\.food_log_items\s+set status = 'archived'/i.test(replacement) && !/set\s+(consumed_quantity|consumed_unit|food_id|food_portion_id|meal_moment|notes)\s*=/i.test(replacement));
check("replacement insert happens before original archive", replacement.indexOf("insert into public.food_log_items") < replacement.indexOf("update public.food_log_items"));
check("archive failure explicitly rolls back atomic call", /atomic replacement rolled back/i.test(replacement));
check("RPC contains no row deletion", !/delete\s+from/i.test(replacement));

check("Free history uses saved or log timezone", /coalesce\(p\.timezone_name, v_log\.timezone_name, 'UTC'\)/i.test(replacement));
check("Free history boundary is seven local days", /v_log\.log_date < v_today - 6/i.test(replacement));
check("full history uses server entitlement helper", /fmz_phase4_has_full_nutrition_access\(v_user_id\)/i.test(replacement));
check("existing entitlement helper covers Pro AI and PT", /entitlement_code in \('pro', 'ai', 'personal_coaching'\)/i.test(normalLog + slice1));
check("existing entitlement helper requires active current window", /e\.status = 'active'[\s\S]*?e\.starts_at <= now\(\)[\s\S]*?e\.ends_at is null or e\.ends_at > now\(\)/i.test(slice1));

check("PUBLIC execute is explicitly revoked", /revoke all on function public\.fmz_phase4_replace_food_log_item\([\s\S]*?\) from public;/i.test(migration));
check("anon execute is explicitly revoked", /revoke all on function public\.fmz_phase4_replace_food_log_item\([\s\S]*?\) from anon;/i.test(migration));
check("authenticated is reset then granted execute", /from authenticated;[\s\S]*?grant execute on function public\.fmz_phase4_replace_food_log_item/i.test(migration));
check("migration adds no table grant", !/grant\s+[^;]+on\s+table/i.test(migration));
check("migration adds no policy or trainer access", !/create\s+policy|trainer_id|linked_trainer|coach_client/i.test(replacement));
check("migration contains no service role or secret", !/service[_-]?role|supabase_secret|secret_key/i.test(replacement));

check("verification is one CTE SELECT", /^\s*with\b/i.test(verification.replace(/--.*$/gm, "")) && /select jsonb_pretty\(verification_result\)[\s\S]*?from result;\s*$/i.test(verification));
check("verification contains no mutating statement", !/\b(insert|update|delete|truncate|alter|create|drop|grant|revoke|call)\b/i.test(verificationWithoutStrings));
check("verification does not execute app RPC", !/select\s+public\.fmz_phase4_/i.test(verificationWithoutStrings));
check("verification uses PUBLIC ACL grantee zero semantics", /aclexplode/i.test(verification) && /coalesce\(r\.rolname::text, 'PUBLIC'\)/i.test(verification));
check("verification casts catalog names to text", (verification.match(/\.relname::text/g) || []).length >= 3 && /p\.proname::text/i.test(verification));
check("verification checks exact function regprocedure", /to_regprocedure\(\s*'public\.fmz_phase4_replace_food_log_item\(uuid,uuid,uuid,timestamp with time zone,text,uuid,uuid,numeric,text,text\)'/i.test(verification));
check("verification returns overall pass JSON", /'overall_pass', coalesce\(bool_and\(c\.pass\), false\)/i.test(verification));

check("Phase 1 frozen marker remains", phase1.includes("FMZ_PHASE1_FOUNDATION_LOADED"));
check("Phase 2 frozen marker remains", phase2.includes("FMZ_PHASE2_HOME_RECOVERY_LOADED"));
check("Phase 3 frozen marker remains", phase3.includes("FMZ_PHASE3_TRAINING_ENGINE_LOADED"));
check("Member UX frozen marker remains", memberUx.includes("FMZ_MEMBER_UX_CONSISTENCY_LOADED"));
check("Slice 2 frozen marker remains", slice2.includes("FMZ_PHASE4_NUTRITION_SLICE2_LOADED"));

const failed = checks.filter((item) => !item.condition);
for (const item of checks) {
  console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
}

if (failed.length) {
  console.error(`Phase 4 Slice 3 replacement static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}

console.log(`Phase 4 Slice 3 replacement static check passed: ${checks.length}`);
