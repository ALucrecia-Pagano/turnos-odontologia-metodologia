import { setAuthProvider } from "../../shared/api/auth";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { fetchMe, login } from "./authApi";
import { createMemoryTokenStore } from "./tokenStore";

interface RecordedRequest {
  url: string;
  method: string;
  headers: Headers;
  bodyText: string | undefined;
}

function recordRequest(log: RecordedRequest[], url: string, init: RequestInit | undefined): void {
  log.push({
    url,
    method: init?.method ?? "GET",
    headers: new Headers(init?.headers),
    bodyText: typeof init?.body === "string" ? init.body : undefined,
  });
}

describe("authApi", () => {
  afterEach(() => {
    setAuthProvider(null);
  });

  it("login envía POST /api/auth/login y devuelve el accessToken con 200", async () => {
    const log: RecordedRequest[] = [];
    const fetchFn: FetchFn = async (url, init) => {
      recordRequest(log, url, init);
      return new Response(JSON.stringify({ accessToken: "token-ficticio-123", tokenType: "bearer" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    const result = await login(client, { username: "recepcion", password: "<contraseña de prueba>" });

    expect(log).toHaveLength(1);
    expect(log[0]?.url).toBe("http://localhost:8000/api/auth/login");
    expect(log[0]?.method).toBe("POST");
    expect(log[0]?.bodyText).toBe(JSON.stringify({ username: "recepcion", password: "<contraseña de prueba>" }));
    expect(result).toEqual({
      ok: true,
      status: 200,
      data: { accessToken: "token-ficticio-123", tokenType: "bearer" },
    });
  });

  it("login devuelve error auth ante 401 INVALID_CREDENTIALS", async () => {
    const fetchFn: FetchFn = async () =>
      new Response(
        JSON.stringify({
          code: "INVALID_CREDENTIALS",
          message: "Usuario o contraseña incorrectos.",
        }),
        { status: 401, headers: { "Content-Type": "application/json" } },
      );
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    const result = await login(client, { username: "recepcion", password: "<contraseña de prueba>" });

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

  it("login devuelve error validation ante 400 con errors", async () => {
    const fetchFn: FetchFn = async () =>
      new Response(
        JSON.stringify({
          errors: [{ field: "username", type: "string_too_short", message: "El usuario es obligatorio." }],
        }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    const result = await login(client, { username: "", password: "<contraseña de prueba>" });

    expect(result).toEqual({
      ok: false,
      status: 400,
      error: {
        kind: "validation",
        status: 400,
        errors: [{ field: "username", type: "string_too_short", message: "El usuario es obligatorio." }],
      },
    });
  });

  it("el login no manda un token viejo", async () => {
    const tokenStore = createMemoryTokenStore("token-viejo");
    setAuthProvider({ getToken: tokenStore.getToken });
    const log: RecordedRequest[] = [];
    const fetchFn: FetchFn = async (url, init) => {
      recordRequest(log, url, init);
      return new Response(JSON.stringify({ accessToken: "token-ficticio-123", tokenType: "bearer" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    await login(client, { username: "recepcion", password: "<contraseña de prueba>" });

    expect(log).toHaveLength(1);
    expect(log[0]?.headers.has("Authorization")).toBe(false);
  });

  it("petición autenticada con Bearer", async () => {
    const tokenStore = createMemoryTokenStore("token-ficticio-123");
    setAuthProvider({ getToken: tokenStore.getToken });
    const log: RecordedRequest[] = [];
    const fetchFn: FetchFn = async (url, init) => {
      recordRequest(log, url, init);
      return new Response(
        JSON.stringify({
          id: "00000000-0000-0000-0000-0000000000e3",
          username: "odontologo",
          displayName: "Dra. Laura Quiroga",
          role: "odontologo",
          professionalId: "00000000-0000-0000-0000-000000000001",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    const result = await fetchMe(client);

    expect(log).toHaveLength(1);
    expect(log[0]?.url).toBe("http://localhost:8000/api/auth/me");
    expect(log[0]?.headers.get("Authorization")).toBe("Bearer token-ficticio-123");
    expect(result).toEqual({
      ok: true,
      status: 200,
      data: {
        id: "00000000-0000-0000-0000-0000000000e3",
        username: "odontologo",
        displayName: "Dra. Laura Quiroga",
        role: "odontologo",
        professionalId: "00000000-0000-0000-0000-000000000001",
      },
    });
  });

  it("sin token no se envía Authorization", async () => {
    const tokenStore = createMemoryTokenStore();
    setAuthProvider({ getToken: tokenStore.getToken });
    const log: RecordedRequest[] = [];
    const fetchFn: FetchFn = async (url, init) => {
      recordRequest(log, url, init);
      return new Response(
        JSON.stringify({
          code: "INVALID_TOKEN",
          message: "La sesión venció o no es válida. Inicie sesión de nuevo.",
        }),
        { status: 401, headers: { "Content-Type": "application/json" } },
      );
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    const result = await fetchMe(client);

    expect(log).toHaveLength(1);
    expect(log[0]?.headers.has("Authorization")).toBe(false);
    expect(result.ok).toBe(false);
  });

  it("fetchMe devuelve error auth ante 401 INVALID_TOKEN y error unknown ante red o 5xx", async () => {
    const tokenStore = createMemoryTokenStore("token-ficticio-123");
    setAuthProvider({ getToken: tokenStore.getToken });

    const client401 = createApiClient({
      baseUrl: "http://localhost:8000/api",
      fetchFn: async () =>
        new Response(
          JSON.stringify({
            code: "INVALID_TOKEN",
            message: "La sesión venció o no es válida. Inicie sesión de nuevo.",
          }),
          { status: 401, headers: { "Content-Type": "application/json" } },
        ),
    });
    const res401 = await fetchMe(client401);
    expect(res401).toEqual({
      ok: false,
      status: 401,
      error: {
        kind: "auth",
        status: 401,
        code: "INVALID_TOKEN",
        message: "La sesión venció o no es válida. Inicie sesión de nuevo.",
      },
    });

    const clientNetwork = createApiClient({
      baseUrl: "http://localhost:8000/api",
      fetchFn: async () => {
        throw new Error("Failed to fetch");
      },
    });
    const resNetwork = await fetchMe(clientNetwork);
    expect(resNetwork).toEqual({
      ok: false,
      status: 0,
      error: { kind: "unknown", status: 0, rawText: "Failed to fetch" },
    });

    const client500 = createApiClient({
      baseUrl: "http://localhost:8000/api",
      fetchFn: async () => new Response("Internal Server Error", { status: 502 }),
    });
    const res500 = await fetchMe(client500);
    expect(res500).toEqual({
      ok: false,
      status: 502,
      error: { kind: "unknown", status: 502, rawText: "Internal Server Error" },
    });
  });
});
