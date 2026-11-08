import { readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const SRC = resolve(process.cwd(), "src");

function productionSources(): { path: string; content: string }[] {
  return readdirSync(SRC, { recursive: true, encoding: "utf-8" })
    .filter((path) => /\.(ts|tsx)$/.test(path) && !/\.test\.(ts|tsx)$/.test(path))
    .map((path) => ({
      path: path.replaceAll("\\", "/"),
      content: readFileSync(resolve(SRC, path), "utf-8"),
    }));
}

describe("confinamiento del storage de sesión", () => {
  it("el storage está confinado a un solo archivo", () => {
    const sources = productionSources();

    const sessionStorageFiles = sources
      .filter(({ content }) => /\bsessionStorage\b/.test(content))
      .map(({ path }) => path);
    expect(sessionStorageFiles).toEqual(["features/auth/tokenStore.ts"]);

    const forbiddenStorageFiles = sources
      .filter(({ content }) => /\blocalStorage\b|document\.cookie/.test(content))
      .map(({ path }) => path);
    expect(forbiddenStorageFiles).toEqual([]);

    const clientSource = sources.find(({ path }) => path === "shared/api/client.ts");
    expect(clientSource?.content).toBeDefined();
    expect(clientSource?.content).not.toMatch(/sessionStorage|localStorage|document\.cookie|tokenStore/);
  });
});
