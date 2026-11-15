import { existsSync, readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { readSrcFile } from "../../test/cssText";

function getModuleCssFiles(): string[] {
  const dirs = [
    resolve(__dirname, "../pacientes"),
    resolve(__dirname, "../catalogos"),
  ];
  const files: string[] = [];
  for (const dir of dirs) {
    if (existsSync(dir)) {
      for (const entry of readdirSync(dir)) {
        if (entry.endsWith(".module.css")) {
          files.push(resolve(dir, entry));
        }
      }
    }
  }
  return files;
}

describe("catalogosPacientesStyles", () => {
  it("Toda variable CSS de las pantallas existe en tokens.css", () => {
    const tokensCss = readSrcFile("shared/styles/tokens.css");
    const definedTokens = new Set(
      Array.from(tokensCss.matchAll(/(--[a-z0-9-]+)\s*:/g), (m) => m[1]),
    );

    const files = getModuleCssFiles();
    expect(files.length).toBeGreaterThan(0);

    const missingTokens: string[] = [];
    const rawColorMatches: string[] = [];

    for (const file of files) {
      const css = readFileSync(file, "utf8");

      for (const match of css.matchAll(/var\(\s*(--[a-z0-9-]+)/g)) {
        const token = match[1];
        if (token !== undefined && !definedTokens.has(token)) {
          missingTokens.push(`${file}: ${token}`);
        }
      }

      if (/#([0-9a-fA-F]{3,8})\b/.test(css)) {
        rawColorMatches.push(`${file}: HEX color found`);
      }
      if (/rgba?\s*\(/.test(css)) {
        rawColorMatches.push(`${file}: rgb/rgba color found`);
      }
    }

    expect(missingTokens).toEqual([]);
    expect(rawColorMatches).toEqual([]);
  });

  it("Sin tokens de fondo oscuro en las pantallas", () => {
    const files = getModuleCssFiles();
    expect(files.length).toBeGreaterThan(0);

    const darkTokenMatches: string[] = [];

    for (const file of files) {
      const css = readFileSync(file, "utf8");

      if (/--color-ice\b/.test(css)) {
        darkTokenMatches.push(`${file}: contains --color-ice`);
      }
      if (/on-navy(-[a-z0-9-]+)?\b/.test(css)) {
        darkTokenMatches.push(`${file}: contains on-navy token`);
      }
    }

    expect(darkTokenMatches).toEqual([]);
  });

  it("Tablas apiladas en celular, controles táctiles y foco visible", () => {
    const tableCssFiles = [
      resolve(__dirname, "../pacientes/PacientesPage.module.css"),
      resolve(__dirname, "CatalogosPage.module.css"),
    ];

    for (const file of tableCssFiles) {
      const css = readFileSync(file, "utf8");

      expect(css, `${file} debe tener media query a 640px`).toMatch(/@media\s*\(\s*max-width\s*:\s*640px\s*\)/);
      expect(css, `${file} debe usar data-label en responsive`).toContain("data-label");
      expect(css, `${file} debe declarar min-height de 44px`).toMatch(/min-height:\s*44px/);
      expect(css, `${file} debe tener foco visible`).toMatch(/:focus-visible/);
    }
  });

  it("Tabla apilada en celular con el título a todo el ancho y el encabezado oculto de forma accesible", () => {
    const tableCssFiles = [
      resolve(__dirname, "../pacientes/PacientesPage.module.css"),
      resolve(__dirname, "CatalogosPage.module.css"),
    ];

    for (const file of tableCssFiles) {
      const css = readFileSync(file, "utf8");

      expect(css, `${file} debe tener media query a 640px`).toMatch(/@media\s*\(\s*max-width\s*:\s*640px\s*\)/);
      expect(css, `${file} debe definir .caption con display: block y width: 100% en responsive`).toMatch(
        /\.caption[\s\S]*?display:\s*block[\s\S]*?width:\s*100%/,
      );
      expect(css, `${file} debe ocultar thead de forma accesible con position: absolute`).toMatch(
        /thead[\s\S]*?position:\s*absolute/,
      );
      expect(css, `${file} debe recortar thead con clip`).toMatch(
        /thead[\s\S]*?clip:\s*rect\(0,\s*0,\s*0,\s*0\)/,
      );
      expect(css, `${file} no debe ocultar .th con display: none`).not.toMatch(/\.th\s*\{\s*display:\s*none;?\s*\}/);
      expect(css, `${file} debe eliminar bordes de thead`).toMatch(
        /thead[\s\S]*?border:\s*0/,
      );
    }
  });
});
