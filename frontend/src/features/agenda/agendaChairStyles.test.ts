import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const CURRENT_DIR = dirname(fileURLToPath(import.meta.url));
const TOKENS_PATH = join(CURRENT_DIR, "../../shared/styles/tokens.css");
const GRID_CSS_PATH = join(CURRENT_DIR, "AgendaGrid.module.css");
const GRID_TSX_PATH = join(CURRENT_DIR, "AgendaGrid.tsx");

describe("agendaChairStyles (C-31)", () => {
  it("La disponibilidad no depende sólo del color: bandas con texto y sin HEX", () => {
    const tokensCss = readFileSync(TOKENS_PATH, "utf-8");
    const requiredTokens = [
      "--agenda-free-bg:",
      "--agenda-free-border:",
      "--agenda-free-text:",
      "--agenda-outside-bg:",
      "--agenda-outside-border:",
      "--agenda-outside-text:",
    ];
    for (const token of requiredTokens) {
      expect(tokensCss).toContain(token);
    }

    const gridCss = readFileSync(GRID_CSS_PATH, "utf-8");
    expect(gridCss).toContain(".availabilityBand");
    expect(gridCss).toContain(".availabilityFree");
    expect(gridCss).toContain(".availabilityOutside");
    expect(gridCss).toContain("var(--agenda-free-bg)");
    expect(gridCss).toContain("var(--agenda-free-text)");
    expect(gridCss).toContain("var(--agenda-outside-bg)");
    expect(gridCss).toContain("var(--agenda-outside-text)");
    expect(gridCss).toContain(":focus-visible");

    const gridTsx = readFileSync(GRID_TSX_PATH, "utf-8");
    expect(gridTsx).toContain("<span>{slot.label}</span>");
    expect(gridTsx).toContain("aria-label={slot.ariaLabel}");

    const tsxFiles = readdirSync(CURRENT_DIR).filter(
      (name) => name.endsWith(".tsx") && !name.endsWith(".test.tsx"),
    );
    const hexOffenders: string[] = [];
    for (const file of tsxFiles) {
      const content = readFileSync(join(CURRENT_DIR, file), "utf-8");
      if (/#[0-9a-fA-F]{3,8}\b/.test(content)) {
        hexOffenders.push(file);
      }
    }
    expect(hexOffenders).toEqual([]);
  });

  it("apilamiento de disponibilidad: z-index superior a workingHourBand y menor a tarjeta y horas", () => {
    const gridCss = readFileSync(GRID_CSS_PATH, "utf-8");

    // availabilityBand tiene z-index: 1 (por encima de workingHourBand y por debajo de appointmentCard)
    const availMatch = /\.availabilityBand\s*\{[^}]*z-index:\s*(\d+);/s.exec(gridCss);
    expect(availMatch).not.toBeNull();
    const availZIndex = Number(availMatch?.[1]);

    const whMatch = /\.workingHourBand\s*\{[^}]*z-index:\s*(\d+);/s.exec(gridCss);
    expect(whMatch).not.toBeNull();
    const whZIndex = Number(whMatch?.[1]);

    const cardMatch = /\.appointmentCard\s*\{[^}]*z-index:\s*(\d+);/s.exec(gridCss);
    expect(cardMatch).not.toBeNull();
    const cardZIndex = Number(cardMatch?.[1]);

    const gutterMatch = /\.timeGutter\s*\{[^}]*z-index:\s*(\d+);/s.exec(gridCss);
    expect(gutterMatch).not.toBeNull();
    const gutterZIndex = Number(gutterMatch?.[1]);

    expect(availZIndex).toBeGreaterThan(whZIndex);
    expect(availZIndex).toBeLessThan(cardZIndex);
    expect(availZIndex).toBeLessThan(gutterZIndex);

    // En AgendaGrid.tsx, workingHourBand no se renderiza si existen freeSlots en la columna
    const gridTsx = readFileSync(GRID_TSX_PATH, "utf-8");
    expect(gridTsx).toMatch(
      /\(!col\.freeSlots\s*\|\|\s*col\.freeSlots\.length\s*===\s*0\)\s*&&\s*col\.workingHours\.map/,
    );
  });

  it("distinción visual de disponibilidad: libre con fondo de tinte y borde discontinuo", () => {
    const tokensCss = readFileSync(TOKENS_PATH, "utf-8");
    const gridCss = readFileSync(GRID_CSS_PATH, "utf-8");

    // --agenda-free-bg usa var(--color-background) (#F3F7FA) distinguiéndose del blanco puro de superficie
    expect(tokensCss).toMatch(/--agenda-free-bg:\s*var\(--color-background\);/);
    expect(tokensCss).not.toMatch(/--agenda-free-bg:\s*var\(--color-surface\);/);

    // .availabilityFree aplica borde discontinuo (dashed) y fondo del token
    expect(gridCss).toMatch(
      /\.availabilityFree\s*\{[^}]*border:\s*1px\s+dashed\s+var\(--agenda-free-border\);/,
    );
    expect(gridCss).toMatch(
      /\.availabilityFree\s*\{[^}]*background-color:\s*var\(--agenda-free-bg\);/,
    );
  });
});

