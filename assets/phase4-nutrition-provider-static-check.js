const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const functionRoot = "supabase/functions/nutrition-provider";
const files = ["constants.ts", "crypto.ts", "handler.ts", "index.ts", "normalization.ts", "off-normalization.ts", "types.ts"];
const sources = Object.fromEntries(files.map((file) => [file, read(`${functionRoot}/${file}`)]));
const source = files.map((file) => sources[file]).join("\n");
const tests = read(`${functionRoot}/nutrition-provider.test.ts`);
const denoConfig = JSON.parse(read(`${functionRoot}/deno.json`));
const denoLock = JSON.parse(read(`${functionRoot}/deno.lock`));
const decisions = read("docs/DECISIONS.md");
const architecture = read("docs/ARCHITECTURE.md");
const masterPlan = read("docs/MASTER_BUILD_PLAN.md");
const phase4 = read("docs/PHASE4_NUTRITION_SLICE4_CATALOG_ARCHITECTURE.md");
const testMatrix = read("docs/TEST_MATRIX.md");
const buildStatus = read("docs/BUILD_STATUS.md");
const checks = [];
const check = (name, condition) => checks.push({ name, condition: Boolean(condition) });

check("dedicated provider namespace is exact", sources["constants.ts"].includes('"23440733-7e58-4c21-ad15-591eae6ab8ac"'));
check("Phase 3 namespace remains separate", sources["constants.ts"].includes('"9439f2af-0e84-5e41-9482-d4b6765154ed"'));
check("candidate identity prefix is exact", sources["crypto.ts"].includes("`${PROVIDER_CODE}:${providerFoodId}`"));
check("candidate UUID uses only Phase 4 namespace", /createCandidateId[\s\S]*PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE/.test(sources["crypto.ts"]) && !/createCandidateId[\s\S]{0,300}PHASE3_EXERCISE_UUID_NAMESPACE/.test(sources["crypto.ts"]));
check("fixed deterministic UUID proof exists", tests.includes("a30e5e7f-9711-5823-b668-a25ff4a729fe"));
check("same identity determinism is tested", tests.includes("assert.equal(first, second)"));
check("different identity separation is tested", tests.includes('createCandidateId("171078")'));
check("different provider prefix separation is tested", tests.includes('"open_food_facts:171077"'));
check("Phase 3 namespace non-use is tested", tests.includes("uuidV5(PHASE3_EXERCISE_UUID_NAMESPACE"));

check("only reviewed search lookup log and replace routes are exposed", ["search", "lookup", "log", "replace"].every((route) => sources["handler.ts"].includes(`route === "${route}"`)) && !/route\s*===\s*["']ingest/.test(source));
check("only POST and OPTIONS are accepted", sources["handler.ts"].includes('request.method !== "POST"') && sources["handler.ts"].includes('request.method === "OPTIONS"'));
check("bearer authentication is mandatory", sources["handler.ts"].includes("verifyBearer(bearerToken(request))"));
check("Supabase getUser verifies bearer", sources["index.ts"].includes("verifier.auth.getUser(token)"));
const parseLogSource = sources["handler.ts"].match(/function parseLog[\s\S]*?function parseReplace/)?.[0] || "";
const parseReplaceSource = sources["handler.ts"].match(/function parseReplace[\s\S]*?async function readBody/)?.[0] || "";
check("client role and entitlement input are rejected", !/("role"|"package"|"entitlement"|"user_id")/.test(`${parseLogSource}\n${parseReplaceSource}`) && tests.includes('role: "trainer"') && tests.includes('entitlement: "pro"'));
check("no client user id is trusted", !/body\.(user_id|userId)/.test(source));
check("provider log rejects browser nutrition authority", ["food_id", "kcal", "protein", "carbohydrate", "fat", "fiber", "provider_url", "user_id", "role", "entitlement"].every((field) => tests.includes(field)));
check("provider log accepts grams only", sources["handler.ts"].includes('body.consumed_unit !== "g"') && sources["handler.ts"].includes('consumedUnit: "g"'));
check("provider log revalidates candidate through lookup", /async function handleLog[\s\S]*handleLookup/.test(sources["handler.ts"]));
check("provider replace revalidates candidate through lookup", /async function handleReplace[\s\S]*handleLookup/.test(sources["handler.ts"]));
check("provider snapshots are built only after trusted resolution", sources["handler.ts"].includes("providerSnapshot(lookup.result)"));
check("provider log uses backend-only RPC adapter", sources["index.ts"].includes('admin.rpc("fmz_phase4_log_provider_food_item"'));
check("provider replace uses backend-only RPC adapter", sources["index.ts"].includes('admin.rpc("fmz_phase4_replace_provider_food_log_item"'));
check("provider log does not promote canonical foods", !/fmz_phase4_log_provider_food_item[\s\S]{0,500}\.from\(["']foods["']\)/.test(sources["index.ts"]));

check("USDA host is fixed", sources["constants.ts"].includes('"https://api.nal.usda.gov/fdc/v1"'));
check("caller cannot supply an upstream URL", !/(body|input)\.(url|host|endpoint|apiKey|api_key)/.test(source));
check("search uses fixed USDA endpoint", sources["index.ts"].includes('`${USDA_API_BASE_URL}/foods/search`'));
check("lookup uses fixed USDA endpoint", sources["index.ts"].includes('`${USDA_API_BASE_URL}/food/${encodeURIComponent(input.providerFoodId)}`'));
check("no blind retry loop exists", !/for\s*\([^)]*retry|while\s*\([^)]*retry|setInterval\s*\(/i.test(source));
check("upstream timeout is enforced", sources["handler.ts"].includes("AbortController") && sources["constants.ts"].includes("UPSTREAM_TIMEOUT_MS = 8_000"));
check("upstream body is bounded", sources["handler.ts"].includes("UPSTREAM_RESPONSE_LIMIT_BYTES"));

check("search query bounds are enforced", sources["handler.ts"].includes("{3,80}"));
check("request body is capped at 2 KB", sources["constants.ts"].includes("BODY_LIMIT_BYTES = 2 * 1024"));
check("locale is limited to NL EN DE", ['locale !== "nl"', 'locale !== "en"', 'locale !== "de"'].every((part) => sources["handler.ts"].includes(part)));
check("country is an ISO-like two-letter code", sources["handler.ts"].includes("COUNTRY_PATTERN"));
check("page range is one through three", sources["handler.ts"].includes("Number(pageNumber) > 3"));
check("page size is at most ten", sources["constants.ts"].includes("MAX_SEARCH_RESULTS = 10"));
check("USDA types exclude branded and experimental", sources["constants.ts"].includes('"Foundation"') && sources["constants.ts"].includes('"Survey (FNDDS)"') && sources["constants.ts"].includes('"SR Legacy"') && !sources["constants.ts"].includes('"Branded"'));

check("candidate token is HMAC signed", sources["crypto.ts"].includes("candidate-token-v1") && sources["crypto.ts"].includes("timingSafeEqual"));
check("candidate token has canonical base64url decoding", sources["crypto.ts"].includes("Non-canonical base64url input"));
check("candidate token binds provider identity", ["provider_food_id", "data_type", "mapping_version", "candidate_id"].every((field) => sources["crypto.ts"].includes(field)));
check("candidate token expires after fifteen minutes", sources["constants.ts"].includes("CANDIDATE_TOKEN_TTL_SECONDS = 15 * 60"));
check("lookup verifies signed token before provider use", sources["handler.ts"].indexOf("verifyCandidateToken") < sources["handler.ts"].indexOf("dependencies.usda.lookup"));
check("token tampering and expiry are tested", tests.includes("tampered") && tests.includes("expiredClock"));

check("rate subject is HMAC derived", sources["handler.ts"].includes('hmacHex(dependencies.hmacKey, "provider-rate-subject-v1", userId)'));
check("rate request identity is server bound", sources["handler.ts"].includes("hmacRequestUuid") && sources["crypto.ts"].includes("provider-request-v1"));
check("same operation retry is stable", tests.includes("rate idempotency is bound"));
check("different operation cannot replay rate id", tests.includes("assert.notEqual(firstStore.rateRequestIds[0], differentStore.rateRequestIds[0])"));
check("cache-miss replay cannot duplicate upstream call", sources["handler.ts"].includes("request_replay_pending") && tests.includes("current.calls.search, 1"));
check("operation identity uses canonical structured serialization", sources["handler.ts"].includes("normalized_query: input.normalizedQuery") && sources["handler.ts"].includes('route: "lookup"') && sources["handler.ts"].includes("stableJson({"));
check("rate RPC runs before upstream search", sources["handler.ts"].indexOf("enforceOperationalGate") < sources["handler.ts"].indexOf("dependencies.usda.search"));
check("rate denial returns retry-after", sources["handler.ts"].includes('"retry-after"') && tests.includes('headers.get("retry-after")'));
check("shared circuit probe precedes provider call", sources["handler.ts"].includes("beginProbe") && sources["handler.ts"].includes("probe_allowed"));
check("success failure and rate transitions exist", ['event: "success"', 'event: "failure"', 'event: "rate_limited"'].every((part) => sources["handler.ts"].includes(part)));

check("query cache key uses HMAC not raw query", sources["handler.ts"].includes('hmacHex(hmacKey, "provider-query-v1", input.normalizedQuery)'));
check("query cache payload checksum is verified", sources["handler.ts"].includes("sha256Hex(row.result_payload) !== row.payload_checksum"));
check("food cache payload checksum is verified", sources["handler.ts"].includes("sha256Hex(row.normalized_payload) !== row.payload_checksum"));
check("cache payload shape is validated fail-closed", sources["handler.ts"].includes("isSafeCandidatePayload") && sources["handler.ts"].includes("exactRecord(value") && tests.includes("unsafe payload shape is rejected"));
check("cache candidate UUID is re-derived", sources["handler.ts"].includes("createCandidateId(candidate.provider_food_id)"));
check("negative food cache is checksum and token bound", sources["handler.ts"].includes("validRejectedFoodCache") && sources["handler.ts"].includes("payload.rejection_code === row.rejection_code") && tests.includes('payload_checksum = "0".repeat(64)'));
check("positive query TTL is 24 hours", sources["constants.ts"].includes("QUERY_POSITIVE_TTL_SECONDS = 24 * 60 * 60"));
check("empty query TTL is 15 minutes", sources["constants.ts"].includes("QUERY_EMPTY_TTL_SECONDS = 15 * 60"));
check("food detail TTL is 30 days", sources["constants.ts"].includes("FOOD_DETAIL_TTL_SECONDS = 30 * 24 * 60 * 60"));
const searchHandler = sources["handler.ts"].match(/async function handleSearch[\s\S]*?async function handleLookup/)?.[0] || "";
check("cache is checked before rate limit", searchHandler.indexOf("getQueryCache(key)") < searchHandler.indexOf("await enforceOperationalGate"));
check("quality failures can be quarantined", sources["handler.ts"].includes('quality_state: "quarantined"'));

for (const id of [1003, 1004, 1005, 1079, 1008, 2047, 2048, 1062]) {
  check(`nutrient ${id} is explicitly mapped`, sources["constants.ts"].includes(String(id)));
}
check("Foundation energy precedence is explicit", /energyAtwaterSpecificKcal[\s\S]*energyAtwaterGeneralKcal[\s\S]*energyLegacyKcal/.test(sources["normalization.ts"]));
check("kJ conversion uses 4.184", sources["normalization.ts"].includes("energyKj / 4.184"));
check("missing macros are rejected not zero-filled", sources["normalization.ts"].includes("candidate_missing_macros"));
check("negative and excessive macros are rejected", sources["normalization.ts"].includes("value.amount < 0 || value.amount > 100"));
check("conflicting energy is rejected", sources["normalization.ts"].includes("candidate_conflicting_energy"));
check("reference basis is exactly 100 g", sources["normalization.ts"].includes('reference_unit: "g"') && sources["normalization.ts"].includes("reference_amount: 100"));
check("portion conversion needs explicit gram weight", sources["normalization.ts"].includes("portion.gramWeight") && sources["normalization.ts"].includes('equivalent_unit: "g"'));
check("no ml equals g density assumption", !/(ml\s*[=:]\s*g|density\s*=\s*1)/i.test(source));
check("raw provider payload is not returned", !/(raw_payload|provider_payload|usda_payload)/i.test(source));

check("CORS allowlist is explicit", sources["constants.ts"].includes("https://yourizorge.github.io") && sources["constants.ts"].includes("https://test.appfmz.nl"));
check("CORS has no wildcard", !/allow-origin["']?\s*[,=:]\s*["']\*/i.test(source));
check("CORS supports current Supabase browser headers", ["x-client-info", "x-retry-count", "traceparent", "tracestate", "baggage"].every((header) => sources["handler.ts"].includes(header)));
check("production app origin is absent", !source.includes("https://appfmz.nl") && !source.includes("https://www.fitmetzorge.com"));
check("production project ref is absent", !source.includes("hgoygcviutmynaihcvpd"));
check("secret names are environment-only", sources["index.ts"].includes('requiredEnvironment("USDA_FDC_API_KEY")') && sources["index.ts"].includes('requiredEnvironment("FMZ_PROVIDER_HMAC_KEY")'));
check("no JWT-like secret value is embedded", !/eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}/.test(source));
check("service role remains in server adapter only", !files.filter((file) => file !== "index.ts").some((file) => /SERVICE_ROLE|SECRET_KEY/.test(sources[file])));
check("canonical foods are never written", !/\.from\(["'](foods|food_portions|food_aliases)["']\)\.(insert|upsert|update|delete)/.test(source));
check("only provider operational tables are accessed", !/\.from\(["'](?!nutrition_provider_(?:query_cache|food_cache))[a-z0-9_]+["']\)/.test(sources["index.ts"]));
check("no ingestion route or ledger exists", !/(ingest|ingestion_ledger)/i.test(source));
check("no AI or persistent OFF catalog mutation exists", !/(anthropic|openai|gemini)/i.test(source) && !/\.from\(["']nutrition_off_(?:products|product_names|catalog_releases)["']\)\.(?:insert|upsert|update|delete)/i.test(source));
check("structured logs omit raw uid query and token", !/(console\.(?:info|log)[\s\S]{0,200}(userId|query|token))/i.test(source));

check("runtime dependency is exactly pinned", sources["index.ts"].includes('npm:@supabase/supabase-js@2.95.0') && (sources["index.ts"].match(/(?:npm:|jsr:|https?:\/\/)/g) || []).length === 1);
check("Deno lockfile is frozen", denoConfig.lock?.path === "./deno.lock" && denoConfig.lock?.frozen === true);
check("Deno lock records pinned Supabase dependency integrity", JSON.stringify(denoLock).includes("@supabase/supabase-js@2.95.0") && /sha512-/u.test(JSON.stringify(denoLock)));

check("Slice 4C status is recorded live", /Slice 4C[\s\S]*LIVE/i.test(buildStatus));
check("namespace decision is documented", decisions.includes("PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE") && decisions.includes("23440733-7e58-4c21-ad15-591eae6ab8ac"));
check("architecture documents derivation contract", architecture.includes("provider_code:provider_food_id") && architecture.includes("usda_fdc:171077") && architecture.includes("23440733-7e58-4c21-ad15-591eae6ab8ac"));
check("master plan locks namespace permanence", masterPlan.includes("PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE") && /permanent/i.test(masterPlan));
check("Phase 4 architecture records USDA local adapter", phase4.includes("nutrition-provider") && phase4.includes("phase4_usda_v1"));
check("test matrix includes provider checks", /USDA Provider Edge Function Checks/i.test(testMatrix));

const failed = checks.filter((item) => !item.condition);
for (const item of checks) console.log(`${item.condition ? "PASS" : "FAIL"} - ${item.name}`);
if (failed.length) {
  console.error(`Phase 4 nutrition provider static check failed: ${failed.length}/${checks.length}`);
  process.exit(1);
}
console.log(`Phase 4 nutrition provider static check passed: ${checks.length}`);
