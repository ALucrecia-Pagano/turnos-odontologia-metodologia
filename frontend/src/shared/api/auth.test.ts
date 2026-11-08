import { readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { setAuthProvider } from "./auth";
import { createApiClient, type FetchFn } from "./client";

const SRC = resolve(process.cwd(), "src");

/** Función fetch real que registra los headers de cada petición. */
function fetchRecordingHeaders(log: Headers[]): FetchFn {
  return async (_url, init) => {
    log.push(new Headers(init?.headers));
    return new Response(JSON.stringify({ status: "ok" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };
}

function productionSources(): { path: string; content: string }[] {
  return readdirSync(SRC, { recursive: true, encoding: "utf-8" })
    .filter((path) => /\.(ts|tsx)$/.test(path) && !/\.test\.(ts|tsx)$/.test(path))
    .map((path) => ({ path, content: readFileSync(resolve(SRC, path), "utf-8") }));
}

describe("punto de enganche del token", () => {
  afterEach(() => {
    setAuthProvider(null);
  });

  it("sin provider no se envía Authorization", async () => {
    const log: Headers[] = [];
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn: fetchRecordingHeaders(log) });

    const result = await client.request("/health");

    expect(result.ok).toBe(true);
    expect(log).toHaveLength(1);
    expect(log[0]?.has("Authorization")).toBe(false);
  });

  it("con provider se agrega el Bearer", async () => {
    setAuthProvider({ getToken: () => "token-ficticio-123" });
    const log: Headers[] = [];
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn: fetchRecordingHeaders(log) });

    await client.request("/auth/me");

    expect(log[0]?.get("Authorization")).toBe("Bearer token-ficticio-123");
  });

  it("C-25 no persiste el token", async () => {
    const sources = productionSources();
    expect(sources.map((source) => source.path.replaceAll("\\", "/"))).toContain("shared/api/auth.ts");

    const allowedSessionStorage = new Set(["features/auth/tokenStore.ts"]);
    const offenders = sources
      .filter(({ path, content }) => {
        const normalizedPath = path.replaceAll("\\", "/");
        if (/localStorage|document\.cookie/.test(content)) return true;
        if (/sessionStorage/.test(content) && !allowedSessionStorage.has(normalizedPath)) return true;
        return false;
      })
      .map(({ path }) => path.replaceAll("\\", "/"));
    expect(offenders).toEqual([]);

    setAuthProvider({ getToken: () => null });
    const log: Headers[] = [];
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn: fetchRecordingHeaders(log) });
    await client.request("/health");
    expect(log[0]?.has("Authorization")).toBe(false);
  });
});
