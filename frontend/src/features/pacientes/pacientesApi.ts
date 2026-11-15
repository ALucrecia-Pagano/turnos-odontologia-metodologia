import type { ApiClient } from "../../shared/api/client";
import type { ApiResult, Json } from "../../shared/api/types";

export const UNEXPECTED_RESPONSE_MESSAGE = "Respuesta inesperada del servidor.";

export interface PatientItem {
  readonly id: string;
  readonly fullName: string;
  readonly dni: string;
  readonly phone: string | null;
  readonly healthInsurance: string | null;
}

export interface PatientPayload {
  readonly fullName: string;
  readonly dni: string;
  readonly phone: string | null;
  readonly healthInsurance: string | null;
}

type JsonObject = { [key: string]: Json };

function isObject(value: Json | undefined): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: Json | undefined): value is string {
  return typeof value === "string";
}

function isNullableString(value: Json | undefined): value is string | null {
  return value === null || typeof value === "string";
}

function parsePatient(raw: Json): PatientItem | null {
  if (!isObject(raw)) {
    return null;
  }
  if (!isString(raw["id"]) || !isString(raw["fullName"]) || !isString(raw["dni"])) {
    return null;
  }
  if (!isNullableString(raw["phone"]) || !isNullableString(raw["healthInsurance"])) {
    return null;
  }
  return {
    id: raw["id"],
    fullName: raw["fullName"],
    dni: raw["dni"],
    phone: raw["phone"] ?? null,
    healthInsurance: raw["healthInsurance"] ?? null,
  };
}

function parsePatientsResponse(raw: Json | undefined, status: number): ApiResult<readonly PatientItem[]> {
  if (!Array.isArray(raw)) {
    return {
      ok: false,
      status,
      error: { kind: "unknown", status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    };
  }
  const items: PatientItem[] = [];
  for (const item of raw) {
    const parsed = parsePatient(item);
    if (!parsed) {
      return {
        ok: false,
        status,
        error: { kind: "unknown", status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
      };
    }
    items.push(parsed);
  }
  return { ok: true, status, data: items };
}

export async function listPatients(
  client: ApiClient,
  query?: string,
): Promise<ApiResult<readonly PatientItem[]>> {
  const trimmed = query?.trim() ?? "";
  const path = trimmed ? `/patients?query=${encodeURIComponent(trimmed)}` : "/patients";
  const result = await client.request(path, { method: "GET" });
  if (!result.ok) {
    return result;
  }
  return parsePatientsResponse(result.data, result.status);
}

export async function createPatient(
  client: ApiClient,
  payload: PatientPayload,
): Promise<ApiResult<PatientItem>> {
  const body: Json = {
    fullName: payload.fullName,
    dni: payload.dni,
    phone: payload.phone,
    healthInsurance: payload.healthInsurance,
  };
  const result = await client.request("/patients", {
    method: "POST",
    body,
  });
  if (!result.ok) {
    return result;
  }
  const parsed = parsePatient(result.data);
  if (!parsed) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}

export async function updatePatient(
  client: ApiClient,
  id: string,
  payload: PatientPayload,
): Promise<ApiResult<PatientItem>> {
  const body: Json = {
    fullName: payload.fullName,
    dni: payload.dni,
    phone: payload.phone,
    healthInsurance: payload.healthInsurance,
  };
  const result = await client.request(`/patients/${encodeURIComponent(id)}`, {
    method: "PUT",
    body,
  });
  if (!result.ok) {
    return result;
  }
  const parsed = parsePatient(result.data);
  if (!parsed) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}
