import { readFileSync } from "node:fs";
import { resolve } from "node:path";

// Vitest reemplaza los .css importados por cadenas vacías: se leen del disco.
const STYLES = resolve(process.cwd(), "src/shared/styles");
const tokensCss = readFileSync(resolve(STYLES, "tokens.css"), "utf-8");
const resetCss = readFileSync(resolve(STYLES, "reset.css"), "utf-8");

function declaration(name: string): string | undefined {
  const match = new RegExp(`${name}\\s*:\\s*([^;]+);`).exec(tokensCss);
  return match?.[1]?.trim();
}

describe("tokens.css", () => {
  it("define la escala de espaciado 4/8/12/16/24/32/48 px", () => {
    const spacing = [1, 2, 3, 4, 5, 6, 7].map((step) => declaration(`--space-${step}`));
    expect(spacing).toEqual(["4px", "8px", "12px", "16px", "24px", "32px", "48px"]);
  });

  it("define la tipografía 12/14/16/20/24/32 px", () => {
    const sizes = ["xs", "sm", "md", "lg", "xl", "2xl"].map((size) => declaration(`--font-size-${size}`));
    expect(sizes).toEqual(["12px", "14px", "16px", "20px", "24px", "32px"]);
  });

  it("usa el system font stack en el reset", () => {
    expect(declaration("--font-family-base")).toBe(
      'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    );
    expect(resetCss).toMatch(/body\s*\{[^}]*font-family:\s*var\(--font-family-base\)/);
  });

  it("el foco es visible", () => {
    expect(declaration("--color-focus")).toMatch(/^#[0-9A-F]{6}$/);
    expect(resetCss).toMatch(
      /:focus-visible\s*\{[^}]*outline:\s*2px solid var\(--color-focus\)/,
    );
  });
});
