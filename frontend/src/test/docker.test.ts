import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const FRONTEND = process.cwd();
const REPO = resolve(FRONTEND, "..");

function read(path: string): string {
  return readFileSync(path, "utf-8").replaceAll("\r\n", "\n");
}

/** Bloque del servicio `frontend` de docker-compose.yml: de `  frontend:` al siguiente servicio o a `volumes:`. */
function frontendService(): string {
  const compose = read(resolve(REPO, "docker-compose.yml"));
  const match = /^ {2}frontend:\n((?: {4}.*\n|\n)+)/m.exec(compose);
  return match?.[1] ?? "";
}

describe("servicio frontend en Docker Compose", () => {
  it("docker compose up levanta el frontend en 5173", () => {
    const dockerfilePath = resolve(FRONTEND, "Dockerfile");
    expect(existsSync(dockerfilePath)).toBe(true);
    const dockerfile = read(dockerfilePath);
    expect(dockerfile).toMatch(/^FROM node:24-alpine$/m);
    expect(dockerfile).toMatch(/^RUN npm ci$/m);
    expect(dockerfile).toMatch(/^EXPOSE 5173$/m);
    expect(dockerfile).toMatch(/^CMD \["npm", "run", "dev", "--", "--host", "0\.0\.0\.0"\]$/m);

    const service = frontendService();
    expect(service).toContain("build: ./frontend");
    // Sin env_file: el frontend no recibe los secretos del .env (JWT_SECRET, POSTGRES_PASSWORD, ...).
    expect(service).not.toContain("env_file");
    for (const secret of ["JWT_SECRET", "POSTGRES_PASSWORD", "POSTGRES_USER", "DATABASE_URL", "SEED_USER_PASSWORD"]) {
      expect(service, secret).not.toContain(secret);
    }
    expect(service).toContain('- "5173:5173"');
    expect(service).toContain("- ./frontend:/app");
    expect(service).toMatch(/^ {6}- \/app\/node_modules$/m);
    expect(service).toMatch(/depends_on:\n {6}- backend/);
  });

  it("un cambio de archivo se refleja por HMR en Windows", () => {
    expect(frontendService()).toContain('CHOKIDAR_USEPOLLING: "true"');
    const viteConfig = read(resolve(FRONTEND, "vite.config.ts"));
    expect(viteConfig).toMatch(/watch:\s*\{\s*usePolling: true/);
    expect(viteConfig).toContain("port: 5173");
  });

  it("VITE_API_URL del navegador apunta a localhost", () => {
    const service = frontendService();
    expect(service).toContain("VITE_API_URL: ${VITE_API_URL:-http://localhost:8000/api}");
    expect(service).not.toContain("backend:8000");

    const client = read(resolve(FRONTEND, "src/shared/api/client.ts"));
    expect(client).toContain('import.meta.env.VITE_API_URL ?? "http://localhost:8000/api"');
    expect(client).not.toContain("backend:8000");
  });
});
