export const PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE = "23440733-7e58-4c21-ad15-591eae6ab8ac";

export const PHASE3_EXERCISE_UUID_NAMESPACE = "9439f2af-0e84-5e41-9482-d4b6765154ed";

export const PROVIDER_CODE = "usda_fdc";
export const PROVIDER_LABEL = "USDA FoodData Central";
export const PROVIDER_ATTRIBUTION_URL = "https://fdc.nal.usda.gov/";
export const USDA_API_BASE_URL = "https://api.nal.usda.gov/fdc/v1";
export const MAPPING_VERSION = "phase4_usda_v1";

export const OFF_PROVIDER_CODE = "open_food_facts";
export const OFF_PROVIDER_LABEL = "Open Food Facts";
export const OFF_API_BASE_URL = "https://world.openfoodfacts.org/api/v2/product";
export const OFF_USER_AGENT = "FitMetZorge/4F-D (https://fitmetzorge.nl)";
export const OFF_MAPPING_VERSION = "phase4_off_barcode_v1";
export const OFF_DATA_TYPE = "off_branded";
export const OFF_ATTRIBUTION_URL = "https://world.openfoodfacts.org/";
export const OFF_LICENSE_CODE = "ODbL-1.0";
export const OFF_LICENSE_URL = "https://opendatacommons.org/licenses/odbl/1-0/";
export const OFF_FOOD_CACHE_TTL_SECONDS = 30 * 24 * 60 * 60;
export const OFF_NEGATIVE_CACHE_TTL_SECONDS = 15 * 60;

export const ACCEPTED_DATA_TYPES = [
  "Foundation",
  "Survey (FNDDS)",
  "SR Legacy",
] as const;

export type AcceptedDataType = (typeof ACCEPTED_DATA_TYPES)[number];

export const ALLOWED_STAGING_ORIGINS = new Set([
  "https://yourizorge.github.io",
  "https://test.appfmz.nl",
]);

export const BODY_LIMIT_BYTES = 2 * 1024;
export const UPSTREAM_RESPONSE_LIMIT_BYTES = 512 * 1024;
export const UPSTREAM_TIMEOUT_MS = 8_000;
export const QUERY_POSITIVE_TTL_SECONDS = 24 * 60 * 60;
export const QUERY_EMPTY_TTL_SECONDS = 15 * 60;
export const FOOD_DETAIL_TTL_SECONDS = 30 * 24 * 60 * 60;
export const CANDIDATE_TOKEN_TTL_SECONDS = 15 * 60;
export const MAX_RETRY_AFTER_SECONDS = 24 * 60 * 60;
export const MAX_SEARCH_RESULTS = 10;
export const MAX_PORTIONS = 20;
export const MAX_NUTRIENT_ENTRIES = 300;

export const QUERY_DATA_TYPE_FILTER = [...ACCEPTED_DATA_TYPES];

export const NUTRIENT_IDS = {
  protein: 1003,
  fat: 1004,
  carbohydrates: 1005,
  fiber: 1079,
  energyLegacyKcal: 1008,
  energyAtwaterGeneralKcal: 2047,
  energyAtwaterSpecificKcal: 2048,
  energyKj: 1062,
} as const;
