import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";

const STYLES = resolve(process.cwd(), "src/shared/styles");
const SRC = resolve(process.cwd(), "src");
const SOURCE_EXTENSIONS = [".ts", ".tsx", ".css", ".html"];
const tokensCss = readFileSync(resolve(STYLES, "tokens.css"), "utf-8");
const resetCss = readFileSync(resolve(STYLES, "reset.css"), "utf-8");

function declaration(name: string): string | undefined {
  const match = new RegExp(`${name}\\s*:\\s*([^;]+);`).exec(tokensCss);
  return match?.[1]?.trim();
}

function sourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) {
      return sourceFiles(path);
    }
    return SOURCE_EXTENSIONS.some((extension) => entry.name.endsWith(extension)) ? [path] : [];
  });
}

describe("tipografías autoalojadas", () => {
  it("declara las dependencias y las importa antes de los estilos en el entry point", () => {
    const packageJson = JSON.parse(readFileSync(resolve(process.cwd(), "package.json"), "utf-8")) as {
      dependencies?: Record<string, string>;
    };
    const mainTsx = readFileSync(resolve(SRC, "main.tsx"), "utf-8");

    expect(packageJson.dependencies?.["@fontsource-variable/jost"]).toBeDefined();
    expect(packageJson.dependencies?.["@fontsource-variable/manrope"]).toBeDefined();

    const jostIndex = mainTsx.indexOf("@fontsource-variable/jost");
    const manropeIndex = mainTsx.indexOf("@fontsource-variable/manrope");
    const stylesIndex = mainTsx.indexOf("./shared/styles/");
    expect(jostIndex).toBeGreaterThanOrEqual(0);
    expect(manropeIndex).toBeGreaterThan(jostIndex);
    expect(stylesIndex).toBeGreaterThan(manropeIndex);
  });

  it("define Jost para títulos y Manrope para texto con fallback al system stack", () => {
    expect(declaration("--font-family-heading")).toContain('"Jost Variable"');
    expect(declaration("--font-family-heading")).toContain("system-ui");
    expect(declaration("--font-family-body")).toContain('"Manrope Variable"');
    expect(declaration("--font-family-body")).toContain("system-ui");
  });

  it("el body conserva la base y usa Manrope después", () => {
    expect(resetCss).toMatch(
      /body\s*\{[\s\S]*font-family:\s*var\(--font-family-base\)[\s\S]*font-family:\s*var\(--font-family-body\)/,
    );
  });

  it("no usa URLs de Google Fonts ni CDNs externos en src", () => {
    const forbiddenHosts = [
      ["fonts", "googleapis.com"].join("."),
      ["fonts", "gstatic.com"].join("."),
      ["cdn", "jsdelivr.net"].join("."),
      ["unpkg", "com"].join("."),
      ["cdnjs", "cloudflare.com"].join("."),
    ];
    const offenders = sourceFiles(SRC).filter((file) => {
      const content = readFileSync(file, "utf-8");
      return forbiddenHosts.some((host) => content.includes(host));
    });
    expect(offenders).toEqual([]);
  });
});
