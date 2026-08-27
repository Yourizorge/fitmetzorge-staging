import {
  OFF_ATTRIBUTION_URL,
  OFF_DATA_TYPE,
  OFF_LICENSE_CODE,
  OFF_LICENSE_URL,
  OFF_MAPPING_VERSION,
  OFF_PROVIDER_CODE,
  OFF_PROVIDER_LABEL,
} from "./constants.ts";
import { createOffCandidateId, sha256Hex } from "./crypto.ts";
import type { OffSafeCandidate } from "./types.ts";
import { ProviderError } from "./types.ts";

type UnknownRecord = Record<string, unknown>;

// deno-lint-ignore no-control-regex -- upstream text is normalized before use or disclosure.
const CONTROL_CHARACTERS = /[\u0000-\u001f\u007f]/gu;
const GTIN_INPUT_PATTERN = /^(?:[0-9]{8}|[0-9]{12}|[0-9]{13}|[0-9]{14})$/u;

function record(value: unknown): UnknownRecord | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as UnknownRecord
    : null;
}

function boundedText(value: unknown, maxLength: number): string | null {
  if (typeof value !== "string") return null;
  const normalized = value.replace(CONTROL_CHARACTERS, " ").replace(/\s+/gu, " ").trim();
  return normalized && normalized.length <= maxLength ? normalized : null;
}

function finiteNumber(value: unknown): number | null {
  const parsed = typeof value === "number"
    ? value
    : typeof value === "string" && value.trim() !== ""
    ? Number(value)
    : Number.NaN;
  return Number.isFinite(parsed) ? parsed : null;
}

function safeRound(value: number): number {
  return Math.round((value + Number.EPSILON) * 1_000) / 1_000;
}

function boundedNutrient(value: unknown, upper: number, required: boolean): number | null {
  const parsed = finiteNumber(value);
  if (parsed === null) {
    if (required) {
      throw new ProviderError("off_product_incomplete", "Required OFF nutrition is missing.", 422);
    }
    return null;
  }
  if (parsed < 0 || parsed > upper) {
    throw new ProviderError("off_product_nutrition_invalid", "OFF nutrition is invalid.", 422);
  }
  return safeRound(parsed);
}

function mod10Valid(value: string): boolean {
  if (!GTIN_INPUT_PATTERN.test(value)) return false;
  const body = value.slice(0, -1);
  const expected = Number(value.at(-1));
  let sum = 0;
  for (let index = body.length - 1, position = 1; index >= 0; index -= 1, position += 1) {
    sum += Number(body[index]) * (position % 2 === 1 ? 3 : 1);
  }
  return (10 - sum % 10) % 10 === expected;
}

export function normalizeGtin14(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const barcode = value.trim();
  return mod10Valid(barcode) ? barcode.padStart(14, "0") : null;
}

function sourceTimestamp(product: UnknownRecord): string | null {
  const raw = finiteNumber(product.last_updated_t ?? product.last_modified_t);
  if (raw === null || !Number.isSafeInteger(raw) || raw <= 0) return null;
  const parsed = new Date(raw * 1_000);
  return Number.isFinite(parsed.getTime()) ? parsed.toISOString() : null;
}

function sourceRevision(product: UnknownRecord): string {
  const revision = finiteNumber(product.rev);
  if (revision === null || !Number.isSafeInteger(revision) || revision < 1) {
    throw new ProviderError("off_product_revision_missing", "OFF revision is unavailable.", 422);
  }
  return `off_rev:${revision}`;
}

function energyKcal(nutriments: UnknownRecord): { value: number; derivation: string } {
  const direct = finiteNumber(nutriments["energy-kcal_100g"]);
  const energy = finiteNumber(nutriments.energy_100g);
  const energyUnit = boundedText(nutriments.energy_unit, 16)?.toLowerCase();
  let selected: number | null = direct;
  let derivation = "energy-kcal_100g";
  if (selected === null && energy !== null) {
    if (energyUnit === "kj") {
      selected = energy / 4.184;
      derivation = "energy_100g_kj_div_4_184";
    } else if (energyUnit === "kcal") {
      selected = energy;
      derivation = "energy_100g_kcal";
    }
  }
  const kcal = boundedNutrient(selected, 900, true) as number;
  if (direct !== null && energy !== null && energyUnit === "kj") {
    const converted = energy / 4.184;
    if (Math.abs(converted - direct) > Math.max(25, direct * 0.2)) {
      throw new ProviderError("off_product_energy_conflict", "OFF energy values conflict.", 422);
    }
  }
  return { value: kcal, derivation };
}

export async function normalizeOffProductPayload(
  rawPayload: unknown,
  expectedGtin14: string,
  retrievedAt: Date,
): Promise<OffSafeCandidate> {
  const payload = record(rawPayload);
  const product = record(payload?.product);
  if (!payload || !product) {
    throw new ProviderError("off_product_not_found", "Product is not known by Open Food Facts.", 404);
  }
  const normalizedGtin14 = normalizeGtin14(product.code ?? payload.code);
  if (!normalizedGtin14 || normalizedGtin14 !== expectedGtin14) {
    throw new ProviderError("off_product_identity_mismatch", "OFF barcode identity does not match.", 409);
  }

  const countriesTags = Array.isArray(product.countries_tags)
    ? [...new Set(product.countries_tags.filter((value): value is string => typeof value === "string"))]
        .sort()
    : [];
  if (!countriesTags.includes("en:netherlands")) {
    throw new ProviderError("off_product_market_unsupported", "OFF product is not associated with the Netherlands.", 422);
  }
  const originalBarcode = boundedText(product.code ?? payload.code, 14);
  const name = boundedText(
    product.product_name_nl ?? product.product_name ?? product.product_name_en,
    240,
  );
  const brand = boundedText(product.brands, 160);
  const quantityUnit = boundedText(product.product_quantity_unit, 8)?.toLowerCase();
  const nutritionDataPer = boundedText(product.nutrition_data_per, 16)
    ?.toLowerCase()
    .replace(/\s+/gu, "");
  const nutritionUnit = nutritionDataPer === "100g"
    ? "g"
    : nutritionDataPer === "100ml"
    ? "ml"
    : null;
  if (
    quantityUnit && nutritionUnit && quantityUnit !== nutritionUnit
  ) {
    throw new ProviderError("off_product_unit_conflict", "OFF nutrition units conflict.", 422);
  }
  const referenceUnit = quantityUnit === "g" || quantityUnit === "ml"
    ? quantityUnit
    : nutritionUnit;
  if (!originalBarcode || !name || !brand || !referenceUnit) {
    throw new ProviderError("off_product_incomplete", "OFF product identity is incomplete.", 422);
  }
  const nutritionBasis = referenceUnit === "ml" ? "per_100_ml" : "per_100_g";
  const nutriments = record(product.nutriments);
  if (!nutriments) {
    throw new ProviderError("off_product_incomplete", "OFF nutrition is unavailable.", 422);
  }
  const energy = energyKcal(nutriments);
  const protein = boundedNutrient(nutriments.proteins_100g, 100, true) as number;
  const carbohydrates = boundedNutrient(nutriments.carbohydrates_100g, 100, true) as number;
  const fat = boundedNutrient(nutriments.fat_100g, 100, true) as number;
  const fiber = boundedNutrient(nutriments.fiber_100g, 100, false);
  const revision = sourceRevision(product);
  const sourceUpdatedAt = sourceTimestamp(product);
  const sourceFields = {
    barcode_original: originalBarcode,
    normalized_gtin14: normalizedGtin14,
    product_name: name,
    brand,
    countries_tags: countriesTags,
    product_quantity_unit: quantityUnit,
    nutrition_data_per: nutritionDataPer,
    reference_unit_source: quantityUnit ? "product_quantity_unit" : "nutrition_data_per",
    nutrition_basis: nutritionBasis,
    energy_kcal_100: energy.value,
    protein_grams_100: protein,
    carbohydrate_grams_100: carbohydrates,
    fat_grams_100: fat,
    fiber_grams_100: fiber,
    source_revision: revision,
    source_updated_at: sourceUpdatedAt,
  };
  const sourceChecksum = await sha256Hex(sourceFields);
  const candidateId = await createOffCandidateId(normalizedGtin14);
  const provenance: OffSafeCandidate["provenance"] = {
    provider: OFF_PROVIDER_CODE,
    provider_food_id: normalizedGtin14,
    candidate_id: candidateId,
    mapping_version: OFF_MAPPING_VERSION,
    reference_basis: nutritionBasis,
    source_revision: revision,
    source_checksum: sourceChecksum,
    retrieved_at: retrievedAt.toISOString(),
    source_updated_at: sourceUpdatedAt,
    original_barcode: originalBarcode,
    countries_tags: countriesTags,
    license_code: OFF_LICENSE_CODE,
    license_url: OFF_LICENSE_URL,
    attribution: { label: "Open Food Facts contributors", url: OFF_ATTRIBUTION_URL },
    derivation: {
      energy: energy.derivation,
      nutrients: "OFF nutriments *_100g interpreted using explicit product_quantity_unit or nutrition_data_per",
      no_density_conversion: true,
    },
  };
  return {
    candidate_id: candidateId,
    provider: OFF_PROVIDER_CODE,
    provider_label: OFF_PROVIDER_LABEL,
    provider_food_id: normalizedGtin14,
    barcode: normalizedGtin14,
    barcode_original: originalBarcode,
    name,
    brand,
    data_type: OFF_DATA_TYPE,
    mapping_version: OFF_MAPPING_VERSION,
    reference_amount: 100,
    reference_unit: referenceUnit,
    nutrition_basis: nutritionBasis,
    kcal: energy.value,
    protein,
    carbohydrates,
    fat,
    fiber,
    quality: "candidate",
    attribution: {
      label: OFF_PROVIDER_LABEL,
      license: OFF_LICENSE_CODE,
      url: OFF_ATTRIBUTION_URL,
    },
    provenance,
  };
}

export async function validateOffCandidate(value: unknown): Promise<OffSafeCandidate | null> {
  const candidate = record(value) as OffSafeCandidate | null;
  if (!candidate) return null;
  const gtin = normalizeGtin14(candidate.provider_food_id);
  const expectedUnit = candidate.nutrition_basis === "per_100_ml" ? "ml" : "g";
  if (
    !gtin || gtin !== candidate.provider_food_id ||
    candidate.provider !== OFF_PROVIDER_CODE ||
    candidate.data_type !== OFF_DATA_TYPE ||
    candidate.mapping_version !== OFF_MAPPING_VERSION ||
    candidate.candidate_id !== await createOffCandidateId(gtin) ||
    candidate.reference_amount !== 100 ||
    candidate.reference_unit !== expectedUnit ||
    candidate.barcode !== gtin ||
    normalizeGtin14(candidate.barcode_original) !== gtin ||
    typeof candidate.name !== "string" || !candidate.name || candidate.name.length > 240 ||
    typeof candidate.brand !== "string" || !candidate.brand || candidate.brand.length > 160 ||
    candidate.quality !== "candidate" ||
    candidate.attribution?.license !== OFF_LICENSE_CODE ||
    candidate.provenance?.provider !== OFF_PROVIDER_CODE ||
    candidate.provenance?.provider_food_id !== gtin ||
    candidate.provenance?.candidate_id !== candidate.candidate_id ||
    candidate.provenance?.mapping_version !== OFF_MAPPING_VERSION ||
    candidate.provenance?.reference_basis !== candidate.nutrition_basis ||
    candidate.provenance?.license_code !== OFF_LICENSE_CODE ||
    candidate.provenance?.license_url !== OFF_LICENSE_URL ||
    !candidate.provenance?.countries_tags?.includes("en:netherlands") ||
    !/^[0-9a-f]{64}$/u.test(candidate.provenance?.source_checksum ?? "")
  ) return null;
  const nutrients = [candidate.kcal, candidate.protein, candidate.carbohydrates, candidate.fat];
  if (
    !nutrients.every((entry) => Number.isFinite(entry)) || candidate.kcal < 0 || candidate.kcal > 900 ||
    [candidate.protein, candidate.carbohydrates, candidate.fat].some((entry) => entry < 0 || entry > 100) ||
    (candidate.fiber !== null && (!Number.isFinite(candidate.fiber) || candidate.fiber < 0 || candidate.fiber > 100))
  ) return null;
  return candidate;
}
