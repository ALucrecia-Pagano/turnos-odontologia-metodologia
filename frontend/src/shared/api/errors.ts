import type { ApiErrorPayload } from "./types";

/**
 * Devuelve los mensajes del backend en orden y tal cual (sin traducir ni reformular).
 * Solo `unknown` recibe un mensaje propio del front, porque su cuerpo no tiene contrato.
 */
export function getApiErrorMessages(error: ApiErrorPayload): string[] {
  switch (error.kind) {
    case "validation":
      return error.errors.map((fieldError) => fieldError.message);
    case "forbidden":
    case "conflict":
    case "unprocessable":
      return error.violations.map((violation) => violation.message);
    case "auth":
    case "not_found":
      return [error.message];
    case "unknown":
      return [`Ocurrió un error inesperado (HTTP ${error.status}).`];
  }
}
