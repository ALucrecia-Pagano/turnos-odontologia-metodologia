import { createApiClient, type FetchFn } from "./client";
import { getApiErrorMessages } from "./errors";
import type { ApiErrorPayload } from "./types";

const OVERLAP_MESSAGE =
  "Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno 00000000-0000-0000-0000-0000000000a1).";

function fetchReturning(status: number, body: unknown): FetchFn {
  return async () =>
    new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

async function errorFrom(status: number, body: unknown): Promise<ApiErrorPayload> {
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn: fetchReturning(status, body) });
  const result = await client.request("/appointments");
  if (result.ok) throw new Error("se esperaba un error HTTP");
  return result.error;
}

describe("getApiErrorMessages", () => {
  it("devuelve errors[].message de un 400 en orden y tal cual", async () => {
    const error = await errorFrom(400, {
      errors: [
        { field: "startAt", type: "missing", message: "Falta este dato." },
        { field: "durationMin", type: "int_parsing", message: "Debe ser un número entero." },
      ],
    });

    expect(getApiErrorMessages(error)).toEqual(["Falta este dato.", "Debe ser un número entero."]);
  });

  it("devuelve message de un 401 tal cual", async () => {
    const error = await errorFrom(401, {
      code: "INVALID_CREDENTIALS",
      message: "Usuario o contraseña incorrectos.",
    });

    expect(getApiErrorMessages(error)).toEqual(["Usuario o contraseña incorrectos."]);
  });

  it("devuelve violations[].message de un 409 con PROFESSIONAL_OVERLAP sin reformular", async () => {
    const error = await errorFrom(409, {
      violations: [
        { code: "PROFESSIONAL_OVERLAP", message: OVERLAP_MESSAGE },
        { code: "CHAIR_OVERLAP", message: "El sillón 2 ya está ocupado de 10:00 a 10:30 (hora local)." },
      ],
    });

    expect(getApiErrorMessages(error)).toEqual([
      OVERLAP_MESSAGE,
      "El sillón 2 ya está ocupado de 10:00 a 10:30 (hora local).",
    ]);
  });

  it("devuelve violations[].message de un 403 y de un 422", async () => {
    const forbidden = await errorFrom(403, {
      violations: [{ code: "FORBIDDEN", message: "No tenés permiso para esta acción." }],
    });
    const unprocessable = await errorFrom(422, {
      violations: [{ code: "APPOINTMENT_IN_PAST", message: "No se puede dar un turno en el pasado." }],
    });

    expect(getApiErrorMessages(forbidden)).toEqual(["No tenés permiso para esta acción."]);
    expect(getApiErrorMessages(unprocessable)).toEqual(["No se puede dar un turno en el pasado."]);
  });

  it("devuelve message de un 404 tal cual", async () => {
    const error = await errorFrom(404, { code: "NOT_FOUND", message: "Turno no encontrado." });

    expect(getApiErrorMessages(error)).toEqual(["Turno no encontrado."]);
  });

  it("un error unknown devuelve un mensaje genérico con el status, sin el texto crudo", () => {
    const error: ApiErrorPayload = { kind: "unknown", status: 500, rawText: "<html>boom</html>" };

    expect(getApiErrorMessages(error)).toEqual(["Ocurrió un error inesperado (HTTP 500)."]);
  });
});
