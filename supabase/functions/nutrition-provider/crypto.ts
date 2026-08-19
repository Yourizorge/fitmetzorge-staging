import {
  CANDIDATE_TOKEN_TTL_SECONDS,
  MAPPING_VERSION,
  PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE,
  PROVIDER_CODE,
} from "./constants.ts";
import type { AcceptedDataType } from "./constants.ts";
import type { CandidateTokenPayload } from "./types.ts";
import { ProviderError } from "./types.ts";

const encoder = new TextEncoder();
const decoder = new TextDecoder();
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const FDC_ID_PATTERN = /^[1-9][0-9]{0,15}$/;

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function bytesToBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (let index = 0; index < bytes.length; index += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(index, index + 0x8000));
  }
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

function base64UrlToBytes(value: string): Uint8Array {
  if (!/^[A-Za-z0-9_-]+$/u.test(value)) {
    throw new ProviderError("candidate_token_invalid", "Candidate token is invalid.", 409);
  }
  const padded = value.replaceAll("-", "+").replaceAll("_", "/") +
    "=".repeat((4 - value.length % 4) % 4);
  try {
    const binary = atob(padded);
    const decoded = Uint8Array.from(binary, (character) => character.charCodeAt(0));
    if (bytesToBase64Url(decoded) !== value) {
      throw new Error("Non-canonical base64url input.");
    }
    return decoded;
  } catch {
    throw new ProviderError("candidate_token_invalid", "Candidate token is invalid.", 409);
  }
}

function uuidToBytes(uuid: string): Uint8Array {
  if (!UUID_PATTERN.test(uuid)) throw new Error("Invalid UUID namespace.");
  return Uint8Array.from(
    uuid.replaceAll("-", "").match(/.{2}/gu) ?? [],
    (pair) => Number.parseInt(pair, 16),
  );
}

function bytesToUuid(bytes: Uint8Array): string {
  const hex = bytesToHex(bytes);
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${
    hex.slice(20)
  }`;
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stableValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([, child]) => child !== undefined)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, child]) => [key, stableValue(child)]),
    );
  }
  return value;
}

export function stableJson(value: unknown): string {
  return JSON.stringify(stableValue(value));
}

export async function sha256Hex(value: unknown): Promise<string> {
  const bytes = encoder.encode(typeof value === "string" ? value : stableJson(value));
  return bytesToHex(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)));
}

async function hmacBytes(keyValue: string, message: string): Promise<Uint8Array> {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(keyValue),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return new Uint8Array(await crypto.subtle.sign("HMAC", key, encoder.encode(message)));
}

export async function hmacHex(keyValue: string, domain: string, value: string): Promise<string> {
  return bytesToHex(await hmacBytes(keyValue, `${domain}\u0000${value}`));
}

export async function hmacRequestUuid(
  keyValue: string,
  clientRequestId: string,
  operationIdentity: string,
): Promise<string> {
  const digest = await hmacBytes(
    keyValue,
    `provider-request-v1\u0000${clientRequestId}\u0000${operationIdentity}`,
  );
  const uuidBytes = digest.slice(0, 16);
  uuidBytes[6] = (uuidBytes[6] & 0x0f) | 0x80;
  uuidBytes[8] = (uuidBytes[8] & 0x3f) | 0x80;
  return bytesToUuid(uuidBytes);
}

export async function uuidV5(namespace: string, name: string): Promise<string> {
  const namespaceBytes = uuidToBytes(namespace);
  const nameBytes = encoder.encode(name);
  const material = new Uint8Array(namespaceBytes.length + nameBytes.length);
  material.set(namespaceBytes);
  material.set(nameBytes, namespaceBytes.length);
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-1", material));
  const uuidBytes = digest.slice(0, 16);
  uuidBytes[6] = (uuidBytes[6] & 0x0f) | 0x50;
  uuidBytes[8] = (uuidBytes[8] & 0x3f) | 0x80;
  return bytesToUuid(uuidBytes);
}

export function candidateIdentityName(providerFoodId: string): string {
  if (!FDC_ID_PATTERN.test(providerFoodId)) {
    throw new ProviderError("candidate_invalid", "Candidate identity is invalid.", 404);
  }
  return `${PROVIDER_CODE}:${providerFoodId}`;
}

export function createCandidateId(providerFoodId: string): Promise<string> {
  return uuidV5(
    PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE,
    candidateIdentityName(providerFoodId),
  );
}

function timingSafeEqual(left: Uint8Array, right: Uint8Array): boolean {
  let mismatch = left.length ^ right.length;
  const length = Math.max(left.length, right.length);
  for (let index = 0; index < length; index += 1) {
    mismatch |= (left[index] ?? 0) ^ (right[index] ?? 0);
  }
  return mismatch === 0;
}

export async function signCandidateToken(
  hmacKey: string,
  providerFoodId: string,
  dataType: AcceptedDataType,
  now: Date,
): Promise<string> {
  const payload: CandidateTokenPayload = {
    version: 1,
    provider: PROVIDER_CODE,
    provider_food_id: providerFoodId,
    data_type: dataType,
    mapping_version: MAPPING_VERSION,
    candidate_id: await createCandidateId(providerFoodId),
    expires_at: Math.floor(now.getTime() / 1000) + CANDIDATE_TOKEN_TTL_SECONDS,
  };
  const encodedPayload = bytesToBase64Url(encoder.encode(stableJson(payload)));
  const signature = bytesToBase64Url(
    await hmacBytes(hmacKey, `candidate-token-v1\u0000${encodedPayload}`),
  );
  return `${encodedPayload}.${signature}`;
}

export async function verifyCandidateToken(
  hmacKey: string,
  token: string,
  now: Date,
  acceptedTypes: readonly string[],
): Promise<CandidateTokenPayload> {
  if (typeof token !== "string" || token.length < 40 || token.length > 2048) {
    throw new ProviderError("candidate_token_invalid", "Candidate token is invalid.", 409);
  }
  const parts = token.split(".");
  if (parts.length !== 2) {
    throw new ProviderError("candidate_token_invalid", "Candidate token is invalid.", 409);
  }

  const expectedSignature = await hmacBytes(hmacKey, `candidate-token-v1\u0000${parts[0]}`);
  const actualSignature = base64UrlToBytes(parts[1]);
  if (!timingSafeEqual(expectedSignature, actualSignature)) {
    throw new ProviderError("candidate_token_invalid", "Candidate token is invalid.", 409);
  }

  let payload: unknown;
  try {
    payload = JSON.parse(decoder.decode(base64UrlToBytes(parts[0])));
  } catch {
    throw new ProviderError("candidate_token_invalid", "Candidate token is invalid.", 409);
  }
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new ProviderError("candidate_token_invalid", "Candidate token is invalid.", 409);
  }
  const parsed = payload as Record<string, unknown>;
  const exactKeys = [
    "candidate_id",
    "data_type",
    "expires_at",
    "mapping_version",
    "provider",
    "provider_food_id",
    "version",
  ];
  if (Object.keys(parsed).sort().join("|") !== exactKeys.join("|")) {
    throw new ProviderError("candidate_token_invalid", "Candidate token is invalid.", 409);
  }
  if (
    parsed.version !== 1 ||
    parsed.provider !== PROVIDER_CODE ||
    parsed.mapping_version !== MAPPING_VERSION ||
    typeof parsed.provider_food_id !== "string" ||
    !FDC_ID_PATTERN.test(parsed.provider_food_id) ||
    typeof parsed.data_type !== "string" ||
    !acceptedTypes.includes(parsed.data_type) ||
    typeof parsed.candidate_id !== "string" ||
    typeof parsed.expires_at !== "number" ||
    !Number.isSafeInteger(parsed.expires_at)
  ) {
    throw new ProviderError("candidate_token_invalid", "Candidate token is invalid.", 409);
  }
  const nowSeconds = Math.floor(now.getTime() / 1000);
  if (
    parsed.expires_at <= nowSeconds || parsed.expires_at > nowSeconds + CANDIDATE_TOKEN_TTL_SECONDS
  ) {
    throw new ProviderError("candidate_token_expired", "Candidate token is expired.", 409);
  }
  if (parsed.candidate_id !== await createCandidateId(parsed.provider_food_id)) {
    throw new ProviderError(
      "candidate_token_mismatch",
      "Candidate token identity does not match.",
      409,
    );
  }
  return parsed as unknown as CandidateTokenPayload;
}
