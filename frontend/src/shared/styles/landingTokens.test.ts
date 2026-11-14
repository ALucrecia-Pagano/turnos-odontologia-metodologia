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
  "--color-navy-deep",
  "--surface-navy",
  "--surface-ivory-ice",
  "--border-on-navy",
  "--border-on-navy-strong",
  "--field-on-navy",
  "--scrim-navy",
  "--scrim-navy-strong",
  "--overlay-hero",
  "--shadow-on-navy",
  "--login-overlay-start",
  "--login-overlay-mid",
  "--login-overlay-end",
  "--carousel-toggle-bg",
  "--carousel-toggle-bg-hover",
  "--carousel-toggle-border",
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

function channel(value: number): number {
  const ratio = value / 255;
  return ratio <= 0.03928 ? ratio / 12.92 : ((ratio + 0.055) / 1.055) ** 2.4;
}

function luminance(rgb: readonly [number, number, number]): number {
  return 0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2]);
}

function contrast(foreground: readonly [number, number, number], background: readonly [number, number, number]) {
  const lighter = Math.max(luminance(foreground), luminance(background));
  const darker = Math.min(luminance(foreground), luminance(background));
  return (lighter + 0.05) / (darker + 0.05);
}

function rgbOf(value: string | undefined): [number, number, number] {
  const hex = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(value ?? "");
  if (hex !== null) {
    return [parseInt(hex[1] ?? "0", 16), parseInt(hex[2] ?? "0", 16), parseInt(hex[3] ?? "0", 16)];
  }
  const rgba = /^rgba\(\s*(\d+),\s*(\d+),\s*(\d+),/.exec(value ?? "");
  if (rgba !== null) {
    return [Number(rgba[1]), Number(rgba[2]), Number(rgba[3])];
  }
  return [-1, -1, -1];
}

describe("tokens de superficie y contraste de C-35", () => {
  it("tokens de layout y contraste AA de superficies", () => {
    const tokens = readCustomProperties(readFileSync(TOKENS_PATH, "utf8"));
    expect(tokens.get("--landing-hero-min-height")).toBe("60vh");
    expect(tokens.get("--landing-content-max-width")).toBe("1120px");

    const navySurface = tokens.get("--surface-navy");
    const ivorySurface = tokens.get("--surface-ivory-ice");
    expect(navySurface).toBeDefined();
    expect(ivorySurface).toBeDefined();
    expect(navySurface).toMatch(/^rgba\(1, 28, 64, /);
    expect(ivorySurface).toMatch(/^rgba\(243, 247, 250, /);

    const navy = rgbOf(tokens.get("--color-navy-deep"));
    expect(navy).toEqual([1, 28, 64]);
    expect(contrast(rgbOf(tokens.get("--color-primary-contrast")), navy).toFixed(2)).toBe("16.92");
    expect(contrast(rgbOf(tokens.get("--color-ice")), navy).toFixed(2)).toBe("12.73");
    expect(contrast(rgbOf(tokens.get("--color-accent")), navy).toFixed(2)).toBe("6.47");
    expect(contrast(rgbOf(tokens.get("--color-border")), navy)).toBeGreaterThanOrEqual(4.5);

    const ivory = rgbOf(ivorySurface);
    expect(contrast(rgbOf(tokens.get("--color-text")), ivory).toFixed(2)).toBe("15.70");
    expect(contrast(rgbOf(tokens.get("--color-text-muted")), ivory)).toBeGreaterThanOrEqual(4.5);

    const lightSurfaceCss = [
      "src/shared/components",
      "src/features/appointments",
      "src/features/agenda",
    ]
      .flatMap((directory) =>
        readdirSync(directory)
          .filter((file) => file.endsWith(".module.css"))
          .map((file) => readFileSync(join(directory, file), "utf8")),
      )
      .join("\n");
    expect(lightSurfaceCss).not.toMatch(/(^|[;{\s])color:\s*var\(--color-accent\)/);
  });
});

