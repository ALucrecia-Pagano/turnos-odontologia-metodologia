import type { ApiClient } from "../../shared/api/client";
import type { ApiResult, Json } from "../../shared/api/types";
import type {
  AnyCatalogItem,
  CatalogSectionKey,
  ChairItem,
  ProfessionalItem,
  ServiceItem,
} from "./catalogConfigs";

export const UNEXPECTED_CATALOG_RESPONSE = "Respuesta inesperada del servidor.";

type JsonObject = { [key: string]: Json };

function isObject(value: Json | undefined): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: Json | undefined): value is string {
  return typeof value === "string";
}

function isBoolean(value: Json | undefined): value is boolean {
  return typeof value === "boolean";
}

function isNumber(value: Json | undefined): value is number {
  return typeof value === "number";
}

function isNullableString(value: Json | undefined): value is string | null {
  return value === null || typeof value === "string";
}

export function parseProfessionalItem(raw: Json): ProfessionalItem | null {
  if (!isObject(raw)) return null;
  if (!isString(raw["id"]) || !isString(raw["fullName"]) || !isBoolean(raw["active"])) {
    return null;
  }
  if (!isNullableString(raw["licenseNumber"])) {
    return null;
  }
  return {
    id: raw["id"],
    fullName: raw["fullName"],
    active: raw["active"],
    licenseNumber: raw["licenseNumber"] ?? null,
  };
}

export function parseChairItem(raw: Json): ChairItem | null {
  if (!isObject(raw)) return null;
  if (!isString(raw["id"]) || !isString(raw["name"]) || !isBoolean(raw["active"])) {
    return null;
  }
  return {
    id: raw["id"],
    name: raw["name"],
    active: raw["active"],
  };
}

export function parseServiceItem(raw: Json): ServiceItem | null {
  if (!isObject(raw)) return null;
  if (
    !isString(raw["id"]) ||
    !isString(raw["name"]) ||
    !isNumber(raw["defaultDurationMin"]) ||
    !isBoolean(raw["active"])
  ) {
    return null;
  }
  return {
    id: raw["id"],
    name: raw["name"],
    defaultDurationMin: raw["defaultDurationMin"],
    active: raw["active"],
  };
}

export async function listCatalog(
  client: ApiClient,
  sectionKey: CatalogSectionKey,
): Promise<ApiResult<readonly AnyCatalogItem[]>> {
  const path =
    sectionKey === "sillones"
      ? "/chairs"
      : sectionKey === "prestaciones"
        ? "/services"
        : "/professionals";

  const result = await client.request(path, { method: "GET" });
  if (!result.ok) {
    return result;
  }
  if (!Array.isArray(result.data)) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_CATALOG_RESPONSE },
    };
  }
  const items: AnyCatalogItem[] = [];
  for (const raw of result.data) {
    const parsed =
      sectionKey === "sillones"
        ? parseChairItem(raw)
        : sectionKey === "prestaciones"
          ? parseServiceItem(raw)
          : parseProfessionalItem(raw);
    if (!parsed) {
      return {
        ok: false,
        status: result.status,
        error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_CATALOG_RESPONSE },
      };
    }
    items.push(parsed);
  }
  return { ok: true, status: result.status, data: items };
}

function parseSingleItem(sectionKey: CatalogSectionKey, raw: Json): AnyCatalogItem | null {
  return sectionKey === "sillones"
    ? parseChairItem(raw)
    : sectionKey === "prestaciones"
      ? parseServiceItem(raw)
      : parseProfessionalItem(raw);
}

export async function createCatalogItem(
  client: ApiClient,
  sectionKey: CatalogSectionKey,
  payload: Record<string, unknown>,
): Promise<ApiResult<AnyCatalogItem>> {
  const path =
    sectionKey === "sillones"
      ? "/chairs"
      : sectionKey === "prestaciones"
        ? "/services"
        : "/professionals";

  const result = await client.request(path, {
    method: "POST",
    body: payload as Json,
  });
  if (!result.ok) {
    return result;
  }
  const parsed = parseSingleItem(sectionKey, result.data);
  if (!parsed) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_CATALOG_RESPONSE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}

export async function updateCatalogItem(
  client: ApiClient,
  sectionKey: CatalogSectionKey,
  id: string,
  payload: Record<string, unknown>,
): Promise<ApiResult<AnyCatalogItem>> {
  const basePath =
    sectionKey === "sillones"
      ? "/chairs"
      : sectionKey === "prestaciones"
        ? "/services"
        : "/professionals";

  const result = await client.request(`${basePath}/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: payload as Json,
  });
  if (!result.ok) {
    return result;
  }
  const parsed = parseSingleItem(sectionKey, result.data);
  if (!parsed) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_CATALOG_RESPONSE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}

export async function deactivateCatalogItem(
  client: ApiClient,
  sectionKey: CatalogSectionKey,
  id: string,
): Promise<ApiResult<AnyCatalogItem>> {
  const basePath =
    sectionKey === "sillones"
      ? "/chairs"
      : sectionKey === "prestaciones"
        ? "/services"
        : "/professionals";

  const result = await client.request(`${basePath}/${encodeURIComponent(id)}/deactivate`, {
    method: "POST",
  });
  if (!result.ok) {
    return result;
  }
  const parsed = parseSingleItem(sectionKey, result.data);
  if (!parsed) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_CATALOG_RESPONSE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}

export async function reactivateCatalogItem(
  client: ApiClient,
  sectionKey: CatalogSectionKey,
  id: string,
): Promise<ApiResult<AnyCatalogItem>> {
  const basePath =
    sectionKey === "sillones"
      ? "/chairs"
      : sectionKey === "prestaciones"
        ? "/services"
        : "/professionals";

  const result = await client.request(`${basePath}/${encodeURIComponent(id)}/reactivate`, {
    method: "POST",
  });
  if (!result.ok) {
    return result;
  }
  const parsed = parseSingleItem(sectionKey, result.data);
  if (!parsed) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_CATALOG_RESPONSE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}
