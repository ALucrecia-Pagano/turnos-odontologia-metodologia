import type { ApiClient } from "../../shared/api/client";
import type { ApiErrorPayload, ApiResult, AuthToken, CurrentUser, Json, UserRole } from "../../shared/api/types";

export interface LoginCredentials {
  username: string;
  password: string;
}

const LOGIN_PATH = "/auth/login";
const ME_PATH = "/auth/me";

type JsonObject = { [key: string]: Json };

function isJsonObject(value: Json): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isUserRole(value: Json | undefined): value is UserRole {
  return value === "administrador" || value === "recepcion" || value === "odontologo";
}

function parseAuthToken(data: Json): AuthToken | undefined {
  if (!isJsonObject(data)) return undefined;
  const { accessToken, tokenType } = data;
  if (typeof accessToken !== "string" || tokenType !== "bearer") return undefined;
  return { accessToken, tokenType: "bearer" };
}

function parseCurrentUser(data: Json): CurrentUser | undefined {
  if (!isJsonObject(data)) return undefined;
  const { id, username, displayName, role, professionalId } = data;
  if (
    typeof id !== "string" ||
    typeof username !== "string" ||
    typeof displayName !== "string" ||
    !isUserRole(role) ||
    (professionalId !== null && typeof professionalId !== "string")
  ) {
    return undefined;
  }
  return { id, username, displayName, role, professionalId };
}

function mapLoginError(error: ApiErrorPayload): ApiErrorPayload {
  if (error.kind === "auth") {
    return { kind: "auth", status: error.status, code: error.code, message: error.message };
  }
  if (error.kind === "validation") {
    return { kind: "validation", status: error.status, errors: error.errors };
  }
  return error;
}

function mapMeError(error: ApiErrorPayload): ApiErrorPayload {
  if (error.kind === "auth") {
    return { kind: "auth", status: error.status, code: error.code, message: error.message };
  }
  return error;
}

export async function login(client: ApiClient, credentials: LoginCredentials): Promise<ApiResult<AuthToken>> {
  const result = await client.request(LOGIN_PATH, {
    method: "POST",
    body: { username: credentials.username, password: credentials.password },
    auth: "omit",
  });
  if (!result.ok) {
    return { ok: false, status: result.status, error: mapLoginError(result.error) };
  }
  const token = parseAuthToken(result.data);
  if (token === undefined) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: "" },
    };
  }
  return { ok: true, status: result.status, data: token };
}

export async function fetchMe(client: ApiClient): Promise<ApiResult<CurrentUser>> {
  const result = await client.request(ME_PATH, { method: "GET", auth: "auto" });
  if (!result.ok) {
    return { ok: false, status: result.status, error: mapMeError(result.error) };
  }
  const user = parseCurrentUser(result.data);
  if (user === undefined) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: "" },
    };
  }
  return { ok: true, status: result.status, data: user };
}
