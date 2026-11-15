import { describe, expect, it } from "vitest";
import { readSrcFile, ruleBody } from "../../test/cssText";

const HORARIOS_CSS_FILES = [
  "features/horarios/HorariosPage.module.css",
  "features/horarios/WorkingHoursSection.module.css",
  "features/horarios/BlocksSection.module.css",
  "features/horarios/BlockFormDialog.module.css",
  "features/horarios/BlockDeleteDialog.module.css",
] as const;

describe("horariosStyles", () => {
  it("Todas las variables CSS de horarios existen en tokens.css: cada var(--x) usado en los .module.css de horarios está definido en tokens.css", () => {
    const tokensCss = readSrcFile("shared/styles/tokens.css");
    const definedTokens = new Set(
      Array.from(tokensCss.matchAll(/(--[a-z0-9-]+)\s*:/g), (match) => match[1]),
    );

    const missingTokens: string[] = [];
    for (const file of HORARIOS_CSS_FILES) {
      const css = readSrcFile(file);
      for (const match of css.matchAll(/var\((--[a-z0-9-]+)\)/g)) {
        const token = match[1];
        if (token !== undefined && !definedTokens.has(token)) {
          missingTokens.push(`${file}: ${token}`);
        }
      }
    }

    expect(missingTokens).toEqual([]);
  });

  it("Encabezado y estilos de HorariosPage sin tokens de fondo oscuro: HorariosPage.module.css usa tokens de superficie clara y no contiene --color-ice ni *-on-navy", () => {
    const css = readSrcFile("features/horarios/HorariosPage.module.css");

    expect(css).not.toMatch(/--color-ice/);
    expect(css).not.toMatch(/on-navy/);
    expect(ruleBody(css, ".title")).toContain("var(--color-text)");
    expect(ruleBody(css, ".subtitle")).toContain("var(--color-text-muted)");
    expect(ruleBody(css, ".selectorLabel")).toContain("var(--color-text)");
    expect(ruleBody(css, ".selector")).toContain("var(--color-text)");
    expect(ruleBody(css, ".selector")).toContain("var(--color-background)");
    expect(ruleBody(css, ".selector")).toContain("var(--color-border)");
  });
});
