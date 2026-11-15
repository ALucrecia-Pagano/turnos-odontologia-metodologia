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
});
