import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const STYLES = resolve(process.cwd(), "src/shared/styles");
const tokensCss = readFileSync(resolve(STYLES, "tokens.css"), "utf-8");

function declaration(name: string): string | undefined {
  const match = new RegExp(`${name}\\s*:\\s*([^;]+);`).exec(tokensCss);
  return match?.[1]?.trim();
}

function token(name: string): string {
  const value = declaration(name);
  if (value === undefined) {
    throw new Error(`Falta el token ${name}`);
  }
  return value;
}

function channel(hexPair: string): number {
  const value = Number.parseInt(hexPair, 16) / 255;
  return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(hex: string): number {
  const red = channel(hex.slice(1, 3));
  const green = channel(hex.slice(3, 5));
  const blue = channel(hex.slice(5, 7));
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

function contrastRatio(foreground: string, background: string): number {
  const lighter = Math.max(relativeLuminance(foreground), relativeLuminance(background));
  const darker = Math.min(relativeLuminance(foreground), relativeLuminance(background));
  return (lighter + 0.05) / (darker + 0.05);
}

describe("paleta Aqua", () => {
  it("define los tokens semánticos con los valores del design", () => {
    expect(declaration("--color-text")).toBe("#011C40");
    expect(declaration("--color-text-muted")).toBe("#4A5F78");
    expect(declaration("--color-background")).toBe("#F3F7FA");
    expect(declaration("--color-surface")).toBe("#FFFFFF");
    expect(declaration("--color-border")).toBe("#C9DDE4");
    expect(declaration("--color-primary")).toBe("#26658C");
    expect(declaration("--color-primary-contrast")).toBe("#FFFFFF");
    expect(declaration("--color-focus")).toBe("#26658C");
    expect(declaration("--color-navy")).toBe("#023859");
    expect(declaration("--color-accent")).toBe("#54ACBF");
    expect(declaration("--color-ice")).toBe("#A7EBF2");
  });

  it("mantiene los contrastes de texto del design", () => {
    const background = token("--color-background");
    expect(contrastRatio(token("--color-text"), background).toFixed(2)).toBe("15.70");
    expect(contrastRatio(token("--color-text-muted"), background).toFixed(2)).toBe("6.09");
    expect(contrastRatio(token("--color-primary-contrast"), token("--color-primary")).toFixed(2)).toBe("6.32");
    expect(contrastRatio(token("--color-focus"), background).toFixed(2)).toBe("5.87");
    expect(contrastRatio(token("--color-accent"), background).toFixed(2)).toBe("2.43");
  });
});
