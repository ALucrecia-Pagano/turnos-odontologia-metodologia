import { createApiClient, type FetchFn } from "./client";

const BASE_URL = "http://localhost:8000/api";
const OVERLAP_MESSAGE =
  "Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno 00000000-0000-0000-0000-0000000000a1).";

interface RecordedRequest {
  url: string;
  init: RequestInit | undefined;
}

/** Función fetch real: registra la petición y devuelve un Response nuevo. Sin stubs globales. */
function fetchReturning(makeResponse: () => Response, log: RecordedRequest[] = []): FetchFn {
  return async (url, init) => {
    log.push({ url, init });
    return makeResponse();
  };
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("cliente de API", () => {
  it("una respuesta 200 devuelve ok con los datos", async () => {
    const log: RecordedRequest[] = [];
    const client = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: fetchReturning(() => jsonResponse(200, { status: "ok" }), log),
    });

    const result = await client.request("/health");

    expect(result).toEqual({ ok: true, status: 200, data: { status: "ok" } });
    expect(log).toHaveLength(1);
    expect(log[0]?.url).toBe("http://localhost:8000/api/health");
    expect(log[0]?.init?.method).toBe("GET");
  });

  it("serializa el cuerpo como JSON y envía los headers de contenido", async () => {
    const log: RecordedRequest[] = [];
    const client = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: fetchReturning(() => jsonResponse(201, { id: "00000000-0000-0000-0000-0000000000b1" }), log),
    });

    const result = await client.request("/patients", {
      method: "POST",
      body: { firstName: "Ana", lastName: "Pérez" },
    });

    expect(result).toEqual({ ok: true, status: 201, data: { id: "00000000-0000-0000-0000-0000000000b1" } });
    const headers = new Headers(log[0]?.init?.headers);
    expect(log[0]?.init?.method).toBe("POST");
    expect(log[0]?.init?.body).toBe('{"firstName":"Ana","lastName":"Pérez"}');
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("Accept")).toBe("application/json");
  });

  it("un 400 con errors se modela como validation", async () => {
    const client = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: fetchReturning(() =>
        jsonResponse(400, { errors: [{ field: "startAt", type: "missing", message: "Falta este dato." }] }),
      ),
    });

    const result = await client.request("/appointments", { method: "POST", body: {} });

    expect(result).toEqual({
      ok: false,
      status: 400,
      error: {
        kind: "validation",
        status: 400,
        errors: [{ field: "startAt", type: "missing", message: "Falta este dato." }],
      },
    });
  });

  it("un 401 con code y message se modela como auth", async () => {
    const client = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: fetchReturning(() =>
        jsonResponse(401, { code: "INVALID_CREDENTIALS", message: "Usuario o contraseña incorrectos." }),
      ),
    });

    const result = await client.request("/auth/login", { method: "POST", body: {} });

    expect(result).toEqual({
      ok: false,
      status: 401,
      error: {
        kind: "auth",
        status: 401,
        code: "INVALID_CREDENTIALS",
        message: "Usuario o contraseña incorrectos.",
      },
    });
  });

  it("un 403 con violations se modela como forbidden", async () => {
    const violations = [{ code: "FORBIDDEN", message: "No tenés permiso para esta acción." }];
    const client = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: fetchReturning(() => jsonResponse(403, { violations })),
    });

    const result = await client.request("/catalog/chairs", { method: "POST", body: {} });

    expect(result).toEqual({ ok: false, status: 403, error: { kind: "forbidden", status: 403, violations } });
  });

  it("un 409 con PROFESSIONAL_OVERLAP conserva el mensaje exacto", async () => {
    const client = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: fetchReturning(() =>
        jsonResponse(409, { violations: [{ code: "PROFESSIONAL_OVERLAP", message: OVERLAP_MESSAGE }] }),
      ),
    });

    const result = await client.request("/appointments", { method: "POST", body: {} });

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.error).toEqual({
      kind: "conflict",
      status: 409,
      violations: [{ code: "PROFESSIONAL_OVERLAP", message: OVERLAP_MESSAGE }],
    });
  });

  it("un 422 con violations se modela como unprocessable", async () => {
    const violations = [{ code: "APPOINTMENT_IN_PAST", message: "No se puede dar un turno en el pasado." }];
    const client = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: fetchReturning(() => jsonResponse(422, { violations })),
    });

    const result = await client.request("/appointments", { method: "POST", body: {} });

    expect(result).toEqual({
      ok: false,
      status: 422,
      error: { kind: "unprocessable", status: 422, violations },
    });
  });

  it("un 404 con code y message se modela como not_found", async () => {
    const client = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: fetchReturning(() => jsonResponse(404, { code: "NOT_FOUND", message: "Turno no encontrado." })),
    });

    const result = await client.request("/appointments/00000000-0000-0000-0000-0000000000a9");

    expect(result).toEqual({
      ok: false,
      status: 404,
      error: { kind: "not_found", status: 404, code: "NOT_FOUND", message: "Turno no encontrado." },
    });
  });

  it("una respuesta desconocida se modela como unknown", async () => {
    const client = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: fetchReturning(() => new Response("boom", { status: 500 })),
    });

    const result = await client.request("/health");

    expect(result).toEqual({ ok: false, status: 500, error: { kind: "unknown", status: 500, rawText: "boom" } });
  });

  it("un fallo de red se modela como unknown con status 0 sin lanzar", async () => {
    const client = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: async () => {
        throw new TypeError("Failed to fetch");
      },
    });

    const result = await client.request("/health");

    expect(result).toEqual({
      ok: false,
      status: 0,
      error: { kind: "unknown", status: 0, rawText: "Failed to fetch" },
    });
  });
});
