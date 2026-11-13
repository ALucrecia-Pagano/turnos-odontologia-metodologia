export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

/** Un error de entrada malformada (400), como lo devuelve la API. */
export interface FieldError {
  field: string;
  type: string;
  message: string;
}

/** Una regla de negocio violada (403/409/422), con su código estable y su mensaje en español. */
export interface Violation {
  code: string;
  message: string;
  conflictingAppointmentId?: string;
  conflictingBlockId?: string;
  conflictingInterval?: {
    startAt: string;
    endAt: string;
  };
  referenceKind?: string;
}

export type ApiErrorPayload =
  | { kind: "validation"; status: 400; errors: FieldError[] }
  | { kind: "auth"; status: 401; code: string; message: string }
  | { kind: "forbidden"; status: 403; violations: Violation[] }
  | { kind: "conflict"; status: 409; violations: Violation[] }
  | { kind: "unprocessable"; status: 422; violations: Violation[] }
  | { kind: "not_found"; status: 404; code: string; message: string }
  | { kind: "unknown"; status: number; rawText: string };

export type ApiResult<T = Json> =
  | { ok: true; status: number; data: T }
  | { ok: false; status: number; error: ApiErrorPayload };

export interface AuthToken {
  accessToken: string;
  tokenType: "bearer";
}

export type UserRole = "administrador" | "recepcion" | "odontologo";

export interface CurrentUser {
  id: string;
  username: string;
  displayName: string;
  role: UserRole;
  professionalId: string | null;
}
