import { describe, expect, it } from "vitest";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import {
  fetchAgenda,
  fetchChairs,
  fetchProfessionals,
  UNEXPECTED_RESPONSE_MESSAGE,
  type AgendaResponse,
} from "./agendaApi";

const BASE_URL = "http://localhost:8000/api";
const QUIROGA_ID = "00000000-0000-0000-0000-000000000001";
const SOSA_ID = "00000000-0000-0000-0000-000000000002";
const BENITEZ_ID = "00000000-0000-0000-0000-000000000003";
const CHAIR_1_ID = "00000000-0000-0000-0000-0000000000b1";
const CHAIR_2_ID = "00000000-0000-0000-0000-0000000000b2";

const SAMPLE_AGENDA: AgendaResponse = {
  from: "2026-11-16",
  to: "2026-11-16",
  timezone: "America/Argentina/Buenos_Aires",
  appointments: [
    {
      id: "00000000-0000-0000-0000-0000000000a2",
      patientId: "00000000-0000-0000-0000-0000000000c2",
      patientName: "Bruno Acosta",
      professionalId: SOSA_ID,
      professionalName: "Dr. Martín Sosa",
      chairId: CHAIR_2_ID,
      chairName: "Sillón 2",
      serviceId: "00000000-0000-0000-0000-0000000000d4",
      serviceName: "Control",
      startAt: "2026-11-16T12:00:00Z",
      endAt: "2026-11-16T12:30:00Z",
      status: "cancelado",
    },
    {
      id: "00000000-0000-0000-0000-0000000000a1",
      patientId: "00000000-0000-0000-0000-0000000000c1",
      patientName: "Ana Pérez",
      professionalId: QUIROGA_ID,
      professionalName: "Dra. Laura Quiroga",
      chairId: CHAIR_1_ID,
      chairName: "Sillón 1",
      serviceId: "00000000-0000-0000-0000-0000000000d4",
      serviceName: "Control",
      startAt: "2026-11-16T13:00:00Z",
      endAt: "2026-11-16T13:30:00Z",
      status: "reservado",
    },
  ],
  workingHours: [
    { professionalId: QUIROGA_ID, weekday: 1, start: "09:00", end: "13:00" },
    { professionalId: QUIROGA_ID, weekday: 1, start: "15:00", end: "19:00" },
  ],
  blocks: [
    {
      id: "00000000-0000-0000-0000-0000000000f1",
      professionalId: QUIROGA_ID,
      startAt: "2026-11-16T15:00:00Z",
      endAt: "2026-11-16T16:00:00Z",
      reason: "Congreso",
    },
  ],
};

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("agendaApi", () => {
  it("fetchAgenda pide GET /api/agenda con from y to locales sin sufijo Z, filtros opcionales y signal, y parsea el 200 completo", async () => {
    const calls: { url: string; init: RequestInit | undefined }[] = [];
    const fetchFn: FetchFn = async (url, init) => {
      calls.push({ url, init });
      return jsonResponse(200, SAMPLE_AGENDA);
    };
    const client = createApiClient({ baseUrl: BASE_URL, fetchFn });
    const controller = new AbortController();

    const first = await fetchAgenda(client, {
      from: "2026-11-16",
      to: "2026-11-16",
      signal: controller.signal,
    });

    expect(first).toEqual({ ok: true, status: 200, data: SAMPLE_AGENDA });
    expect(calls[0]?.url).toBe("http://localhost:8000/api/agenda?from=2026-11-16&to=2026-11-16");
    expect(calls[0]?.url).not.toContain("Z");
    expect(calls[0]?.init?.method).toBe("GET");
    expect(calls[0]?.init?.signal).toBe(controller.signal);

    await fetchAgenda(client, {
      from: "2026-11-16",
      to: "2026-11-16",
      professionalId: QUIROGA_ID,
      chairId: CHAIR_2_ID,
    });
    expect(calls[1]?.url).toBe(
      `http://localhost:8000/api/agenda?from=2026-11-16&to=2026-11-16&professionalId=${QUIROGA_ID}&chairId=${CHAIR_2_ID}`,
    );
  });

  it("fetchAgenda propaga errores 400, 401, 403, 500, red y rechaza una respuesta 200 con JSON o forma inválida", async () => {
    const client400 = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: async () =>
        jsonResponse(400, {
          errors: [{ field: "from", type: "invalid_date_format", message: "La fecha debe tener formato AAAA-MM-DD." }],
        }),
    });
    const res400 = await fetchAgenda(client400, { from: "2026-11-16", to: "2026-11-16" });
    expect(res400).toEqual({
      ok: false,
      status: 400,
      error: {
        kind: "validation",
        status: 400,
        errors: [{ field: "from", type: "invalid_date_format", message: "La fecha debe tener formato AAAA-MM-DD." }],
      },
    });

    const client401 = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: async () =>
        jsonResponse(401, {
          code: "INVALID_TOKEN",
          message: "La sesión venció o no es válida. Inicie sesión de nuevo.",
        }),
    });
    const res401 = await fetchAgenda(client401, { from: "2026-11-16", to: "2026-11-16" });
    expect(res401.ok).toBe(false);
    if (!res401.ok) {
      expect(res401.error.kind).toBe("auth");
    }

    const client403 = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: async () =>
        jsonResponse(403, {
          violations: [{ code: "FORBIDDEN_OPERATION", message: "No tiene permiso para leer la agenda." }],
        }),
    });
    const res403 = await fetchAgenda(client403, { from: "2026-11-16", to: "2026-11-16" });
    expect(res403).toEqual({
      ok: false,
      status: 403,
      error: {
        kind: "forbidden",
        status: 403,
        violations: [{ code: "FORBIDDEN_OPERATION", message: "No tiene permiso para leer la agenda." }],
      },
    });

    const client500 = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: async () => new Response("Internal Server Error", { status: 500 }),
    });
    const res500 = await fetchAgenda(client500, { from: "2026-11-16", to: "2026-11-16" });
    expect(res500).toEqual({
      ok: false,
      status: 500,
      error: { kind: "unknown", status: 500, rawText: "Internal Server Error" },
    });

    const clientNet = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: async () => {
        throw new TypeError("Failed to fetch");
      },
    });
    const resNet = await fetchAgenda(clientNet, { from: "2026-11-16", to: "2026-11-16" });
    expect(resNet.ok).toBe(false);
    if (!resNet.ok) {
      expect(resNet.status).toBe(0);
    }

    const clientMalformed = createApiClient({
      baseUrl: BASE_URL,
      fetchFn: async () => new Response("no-es-json", { status: 200 }),
    });
    const resMalformed = await fetchAgenda(clientMalformed, { from: "2026-11-16", to: "2026-11-16" });
    expect(resMalformed).toEqual({
      ok: false,
      status: 200,
      error: { kind: "unknown", status: 200, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    });
  });

  it("fetchProfessionals y fetchChairs cargan los catálogos con activos e inactivos y validan la respuesta", async () => {
    const urls: string[] = [];
    const fetchFn: FetchFn = async (url) => {
      urls.push(url);
      if (url.endsWith("/professionals")) {
        return jsonResponse(200, [
          { id: QUIROGA_ID, fullName: "Dra. Laura Quiroga", licenseNumber: "MN-10101", active: true },
          { id: BENITEZ_ID, fullName: "Dra. Paula Benítez", licenseNumber: null, active: false },
        ]);
      }
      return jsonResponse(200, [
        { id: CHAIR_1_ID, name: "Sillón 1", active: true },
        { id: CHAIR_2_ID, name: "Sillón 2", active: false },
      ]);
    };
    const client = createApiClient({ baseUrl: BASE_URL, fetchFn });

    const profRes = await fetchProfessionals(client);
    const chairRes = await fetchChairs(client);

    expect(urls).toEqual([
      "http://localhost:8000/api/professionals",
      "http://localhost:8000/api/chairs",
    ]);
    expect(profRes).toEqual({
      ok: true,
      status: 200,
      data: [
        { id: QUIROGA_ID, fullName: "Dra. Laura Quiroga", licenseNumber: "MN-10101", active: true },
        { id: BENITEZ_ID, fullName: "Dra. Paula Benítez", licenseNumber: null, active: false },
      ],
    });
    expect(chairRes).toEqual({
      ok: true,
      status: 200,
      data: [
        { id: CHAIR_1_ID, name: "Sillón 1", active: true },
        { id: CHAIR_2_ID, name: "Sillón 2", active: false },
      ],
    });
  });
});
