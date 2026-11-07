import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const FRONTEND = process.cwd();
const TIMEOUT_MS = 120_000;

function runNpmScript(script: string): { status: number | null; output: string } {
  const result = spawnSync(`npm run ${script}`, {
    cwd: FRONTEND,
    shell: true,
    encoding: "utf-8",
    env: { ...process.env, NO_COLOR: "1", FORCE_COLOR: "0" },
  });
  return { status: result.status, output: `${result.stdout}${result.stderr}` };
}

function withFixture<T>(name: string, content: string, run: () => T): T {
  const path = resolve(FRONTEND, "src", name);
  writeFileSync(path, content, "utf-8");
  try {
    return run();
  } finally {
    rmSync(path, { force: true });
  }
}

describe("tooling del frontend", () => {
  it(
    "npm run typecheck falla con un tipo inválido",
    () => {
      const { status, output } = withFixture(
        "__fixture_typecheck__.ts",
        "export const etiqueta: string = 42;\n",
        () => runNpmScript("typecheck"),
      );

      expect(status).not.toBe(0);
      expect(output).toContain("__fixture_typecheck__.ts");
      expect(output).toContain("TS2322");
      expect(output).toContain("Type 'number' is not assignable to type 'string'");
    },
    TIMEOUT_MS,
  );

  it(
    "npm run lint detecta una violación",
    () => {
      const { status, output } = withFixture(
        "__fixture_lint__.ts",
        "const valorSinUsar = 1;\nexport {};\n",
        () => runNpmScript("lint"),
      );

      expect(status).not.toBe(0);
      expect(output).toContain("__fixture_lint__.ts");
      expect(output).toContain("no-unused-vars");
    },
    TIMEOUT_MS,
  );

  it("la estructura de carpetas y los scripts están presentes", () => {
    for (const folder of ["src", "src/features", "src/shared", "src/pages"]) {
      expect(existsSync(resolve(FRONTEND, folder)), folder).toBe(true);
    }
    expect(existsSync(resolve(FRONTEND, "src/main.tsx"))).toBe(true);
    expect(existsSync(resolve(FRONTEND, "src/App.tsx"))).toBe(true);
    expect(existsSync(resolve(FRONTEND, "package-lock.json"))).toBe(true);

    const packageJson: unknown = JSON.parse(readFileSync(resolve(FRONTEND, "package.json"), "utf-8"));
    expect(packageJson).toMatchObject({
      engines: { node: ">=20" },
      scripts: {
        dev: expect.any(String),
        build: expect.any(String),
        preview: expect.any(String),
        test: expect.any(String),
        "test:run": expect.any(String),
        typecheck: expect.stringContaining("tsc --noEmit"),
        lint: expect.stringContaining("eslint"),
      },
    });
  });
});
