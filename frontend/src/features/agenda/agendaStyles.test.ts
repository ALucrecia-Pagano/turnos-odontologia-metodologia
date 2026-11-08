import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const CURRENT_DIR = dirname(fileURLToPath(import.meta.url));
const TOKENS_PATH = join(CURRENT_DIR, "../../shared/styles/tokens.css");
const GRID_CSS_PATH = join(CURRENT_DIR, "AgendaGrid.module.css");
const TOOLBAR_CSS_PATH = join(CURRENT_DIR, "AgendaToolbar.module.css");
const VIEW_CSS_PATH = join(CURRENT_DIR, "AgendaView.module.css");

describe("agendaStyles y responsive de escritorio/tablet (D12, D13)", () => {
  it("define los tokens de agenda en tokens.css, scroll horizontal, sticky, controles >= 44x44 px y cero HEX en TSX", () => {
    const tokensCss = readFileSync(TOKENS_PATH, "utf-8");
    const requiredTokens = [
      "--agenda-hour-height: 112px;",
      "--agenda-time-gutter-width: 64px;",
      "--agenda-column-min-width: 220px;",
      "--agenda-column-header-height: 48px;",
      "--agenda-grid-line:",
      "--agenda-working-bg:",
      "--agenda-offhours-bg:",
      "--agenda-block-bg:",
      "--agenda-block-border:",
      "--agenda-card-radius:",
      "--agenda-card-min-height:",
      "--agenda-cancelled-bg:",
    ];
    for (const token of requiredTokens) {
      expect(tokensCss).toContain(token);
    }

    const gridCss = readFileSync(GRID_CSS_PATH, "utf-8");
    expect(gridCss).toContain("overflow-x: auto;");
    expect(gridCss).toContain("position: sticky;");
    expect(gridCss).toContain("top: 0;");
    expect(gridCss).toContain("left: 0;");
    expect(gridCss).toContain("min-width: var(--agenda-column-min-width");

    const toolbarCss = readFileSync(TOOLBAR_CSS_PATH, "utf-8");
    expect(toolbarCss).toContain("flex-wrap: wrap;");
    expect(toolbarCss).toContain("min-height: 44px;");
    expect(toolbarCss).toContain("min-width: 44px;");

    const viewCss = readFileSync(VIEW_CSS_PATH, "utf-8");
    expect(viewCss).toContain("flex-wrap: wrap;");
    expect(viewCss).toContain("min-height: 44px;");
    expect(viewCss).toContain("min-width: 44px;");

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
