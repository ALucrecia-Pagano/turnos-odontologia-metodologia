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

  it("la columna es un contenedor y por debajo de 260 px la tarjeta compacta pasa a dos líneas con la etiqueta reducida", () => {
    const gridCss = readFileSync(GRID_CSS_PATH, "utf-8").replace(/\r\n/g, "\n");
    const columnRule = /\.columnTrack \{[^}]*\}/.exec(gridCss)?.[0] ?? "";
    expect(columnRule).toContain("container: agenda-column / inline-size;");

    const stackedRule = /\.cardCompactStacked \{[^}]*\}/.exec(gridCss)?.[0] ?? "";
    expect(stackedRule).toContain("flex-direction: column;");

    const queryStart = gridCss.indexOf("@container agenda-column (width < 260px) {");
    expect(queryStart).toBeGreaterThan(-1);
    const queryBlock = gridCss.slice(queryStart);
    expect(queryBlock).toMatch(/\.cardCompactRow \{[^}]*flex-direction: column;/);
    expect(queryBlock).toMatch(
      /\.statusBadgeWrap > span \{[^}]*font-size: var\(--font-size-xs\);/,
    );
    expect(gridCss).not.toContain(".statusDot");
    expect(gridCss).not.toContain(".visuallyHidden");
  });

  it("verifica estáticamente los estilos de tablet y el tag de Hoy para la vista semanal (C-28)", () => {
    const gridCss = readFileSync(GRID_CSS_PATH, "utf-8");
    expect(gridCss).toContain(".todayTag");
    expect(gridCss).toContain("border-radius: var(--radius-pill)");
    expect(gridCss).toContain("background-color: var(--color-primary)");
    expect(gridCss).toContain("color: var(--color-primary-contrast)");

    expect(gridCss).toContain(".gridScrollContainer");
    expect(gridCss).toContain("overflow-x: auto;");
    expect(gridCss).toContain(".timeGutter");
    expect(gridCss).toContain("position: sticky;");
    expect(gridCss).toContain("left: 0;");
  });

  it("las columnas semanales usan token de ancho sin min-width de 220px y en tablet mantienen scroll horizontal", () => {
    const tokensCss = readFileSync(TOKENS_PATH, "utf-8");
    expect(tokensCss).toContain("--agenda-week-column-min-width:");

    const gridCss = readFileSync(GRID_CSS_PATH, "utf-8");
    expect(gridCss).toContain("var(--agenda-week-column-min-width");
    const weekHeaderMatch = /\.weekColumnHeader[^{]*\{([^}]*)\}/.exec(gridCss);
    const weekTrackMatch = /\.weekColumnTrack[^{]*\{([^}]*)\}/.exec(gridCss);
    const weekRules = (weekHeaderMatch?.[1] ?? "") + (weekTrackMatch?.[1] ?? "");
    expect(weekRules).not.toContain("220px");
    expect(weekRules).toContain("var(--agenda-week-column-min-width");

    expect(gridCss).toContain("overflow-x: auto;");
  });

  it("en carriles divididos y tarjetas apiladas la etiqueta de estado no desborda la tarjeta con max-width 100%, overflow hidden y text-overflow ellipsis (H5)", () => {
    const gridCss = readFileSync(GRID_CSS_PATH, "utf-8").replace(/\r\n/g, "\n");
    const stackedBadgeMatch = /\.cardCompactStacked \.statusBadgeWrap > span \{([^}]*)\}/.exec(gridCss);
    const stackedBadgeRules = stackedBadgeMatch?.[1] ?? "";
    expect(stackedBadgeRules).toContain("max-width: 100%;");
    expect(stackedBadgeRules).toContain("overflow: hidden;");
    expect(stackedBadgeRules).toContain("text-overflow: ellipsis;");
  });

  it("en columnas menores a 260 px las tarjetas no compactas usan etiqueta reducida y líneas con ellipsis en una línea (H6)", () => {
    const gridCss = readFileSync(GRID_CSS_PATH, "utf-8").replace(/\r\n/g, "\n");
    const queryStart = gridCss.indexOf("@container agenda-column (width < 260px) {");
    expect(queryStart).toBeGreaterThan(-1);
    const queryBlock = gridCss.slice(queryStart);

    expect(queryBlock).toMatch(
      /\.cardTopRow > span:last-child \{[^}]*font-size: var\(--font-size-xs\);/,
    );
    expect(queryBlock).toMatch(
      /\.cardPatient \{[^}]*text-overflow: ellipsis;/,
    );
    expect(queryBlock).toMatch(
      /\.cardMeta \{[^}]*text-overflow: ellipsis;/,
    );
  });
});
