import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const TOKENS_PATH = "src/shared/styles/tokens.css";
const LANDING_DIR = "src/features/landing";

const COLOR_VALUE = /(#[0-9a-f]{3,8}\b|rgba?\(|hsla?\()/i;

const EXISTING_COLOR_PROPERTIES = new Set([
  "--color-text",
  "--color-text-muted",
  "--color-background",
  "--color-surface",
  "--color-border",
  "--color-primary",
  "--color-primary-contrast",
  "--color-danger-text",
  "--color-danger-background",
  "--color-danger-border",
  "--color-focus",
  "--color-navy",
  "--color-accent",
  "--color-ice",
  "--shadow-sm",
  "--shadow-md",
  "--agenda-grid-line",
  "--agenda-working-bg",
  "--agenda-offhours-bg",
  "--agenda-block-bg",
  "--agenda-block-border",
  "--agenda-cancelled-bg",
]);

function readCustomProperties(css: string): Map<string, string> {
  const result = new Map<string, string>();
  const pattern = /--([\w-]+)\s*:\s*([^;]+);/g;
  let match = pattern.exec(css);
  while (match !== null) {
    const name = match[1];
    const value = match[2];
    if (name !== undefined && value !== undefined) {
      result.set(`--${name}`, value.trim());
    }
    match = pattern.exec(css);
  }
  return result;
}

function readLandingCss(): string {
  return readdirSync(LANDING_DIR)
    .filter((file) => file.endsWith(".module.css"))
    .map((file) => readFileSync(join(LANDING_DIR, file), "utf8"))
    .join("\n");
}

describe("tokens de layout de la portada", () => {
  it("define los dos tokens de layout", () => {
    const tokens = readCustomProperties(readFileSync(TOKENS_PATH, "utf8"));

    expect(tokens.get("--landing-hero-min-height")).toBe("60vh");
    expect(tokens.get("--landing-content-max-width")).toMatch(/^\d+(\.\d+)?(px|rem|em|vw|%)$/);
  });

  it("la portada usa los tokens de layout", () => {
    const css = readLandingCss();

    expect(css).toContain("var(--landing-hero-min-height)");
    expect(css).toContain("var(--landing-content-max-width)");
  });

  it("no agrega colores nuevos", () => {
    const tokens = readCustomProperties(readFileSync(TOKENS_PATH, "utf8"));
    const colorProperties = [...tokens.entries()]
      .filter(([, value]) => COLOR_VALUE.test(value))
      .map(([name]) => name);
    const unexpected = colorProperties.filter((name) => !EXISTING_COLOR_PROPERTIES.has(name));

    expect(unexpected).toEqual([]);
    expect(tokens.get("--landing-hero-min-height")).toBeDefined();
    expect(tokens.get("--landing-content-max-width")).toBeDefined();
    expect(COLOR_VALUE.test(tokens.get("--landing-hero-min-height") ?? "")).toBe(false);
    expect(COLOR_VALUE.test(tokens.get("--landing-content-max-width") ?? "")).toBe(false);
  });
});
