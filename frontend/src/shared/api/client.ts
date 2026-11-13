import { getAuthToken, notifyUnauthorized } from "./auth";
import type { ApiErrorPayload, ApiResult, FieldError, Json, Violation } from "./types";

export type FetchFn = (url: string, init?: RequestInit) => Promise<Response>;

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export type RequestAuthMode = "auto" | "omit";

export interface RequestOptions {
  method?: HttpMethod;
  body?: Json;
  auth?: RequestAuthMode;
  signal?: AbortSignal;
}

export interface ApiClientOptions {
  baseUrl?: string;
  /** Inyectado por parámetro (C1): por defecto, el fetch del navegador. */
  fetchFn?: FetchFn;
}

export interface ApiClient {
  request: (path: string, options?: RequestOptions) => Promise<ApiResult>;
}

export const API_BASE_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

const browserFetch: FetchFn = (url, init) => fetch(url, init);

type JsonObject = { [key: string]: Json };

function parseJson(text: string): Json | undefined {
  if (text === "") return undefined;
  try {
    return JSON.parse(text) as Json;
  } catch {
    return undefined;
  }
}

function isObject(value: Json | undefined): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: Json | undefined): value is string {
  return typeof value === "string";
}

function asFieldErrors(value: Json | undefined): FieldError[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const errors: FieldError[] = [];
  for (const item of value) {
    if (!isObject(item) || !isString(item.field) || !isString(item.type) || !isString(item.message)) {
      return undefined;
    }
    errors.push({ field: item.field, type: item.type, message: item.message });
  }
  return errors;
}

function asViolations(value: Json | undefined): Violation[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const violations: Violation[] = [];
  for (const item of value) {
    if (!isObject(item) || !isString(item.code) || !isString(item.message)) return undefined;
    const violation: Violation = { code: item.code, message: item.message };
    if (isString(item.conflictingAppointmentId)) {
      violation.conflictingAppointmentId = item.conflictingAppointmentId;
    }
    if (isString(item.conflictingBlockId)) {
      violation.conflictingBlockId = item.conflictingBlockId;
    }
    if (
      isObject(item.conflictingInterval) &&
      isString(item.conflictingInterval.startAt) &&
      isString(item.conflictingInterval.endAt)
    ) {
      violation.conflictingInterval = {
        startAt: item.conflictingInterval.startAt,
        endAt: item.conflictingInterval.endAt,
      };
    }
    if (isString(item.referenceKind)) {
      violation.referenceKind = item.referenceKind;
    }
    violations.push(violation);
  }
  return violations;
}

function toErrorPayload(status: number, rawText: string): ApiErrorPayload {
  const body = parseJson(rawText);
  if (isObject(body)) {
    if (status === 400) {
      const errors = asFieldErrors(body.errors);
      if (errors !== undefined) return { kind: "validation", status, errors };
    }
    if (status === 401 || status === 404) {
      const { code, message } = body;
      if (isString(code) && isString(message)) {
        return status === 401
          ? { kind: "auth", status, code, message }
          : { kind: "not_found", status, code, message };
      }
    }
    if (status === 403 || status === 409 || status === 422) {
      const violations = asViolations(body.violations);
      if (violations !== undefined) {
        if (status === 403) return { kind: "forbidden", status, violations };
        if (status === 409) return { kind: "conflict", status, violations };
        return { kind: "unprocessable", status, violations };
      }
    }
  }
  return { kind: "unknown", status, rawText };
}

export function createApiClient({ baseUrl = API_BASE_URL, fetchFn = browserFetch }: ApiClientOptions = {}): ApiClient {
  async function request(
    path: string,
    { method = "GET", body, auth = "auto", signal }: RequestOptions = {},
  ): Promise<ApiResult> {
    const headers = new Headers({ Accept: "application/json" });
    const token = auth === "omit" ? null : getAuthToken();
    if (token !== null) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    const init: RequestInit = { method, headers };
    if (signal !== undefined) {
      init.signal = signal;
    }
    if (body !== undefined) {
      headers.set("Content-Type", "application/json");
      init.body = JSON.stringify(body);
    }

    let response: Response;
    try {
      response = await fetchFn(`${baseUrl}${path}`, init);
    } catch (error) {
      const rawText = error instanceof Error ? error.message : String(error);
      return { ok: false, status: 0, error: { kind: "unknown", status: 0, rawText } };
    }

    const text = await response.text();
    if (response.ok) {
      return { ok: true, status: response.status, data: parseJson(text) ?? null };
    }
    const error = toErrorPayload(response.status, text);
    if (response.status === 401 && auth !== "omit") {
      notifyUnauthorized();
    }
    return { ok: false, status: response.status, error };
  }

  return { request };
}
