import { readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const AGENDA_DIR = resolve(process.cwd(), "src/features/agenda");

const FORBIDDEN_LOCAL_GETTERS =
  /\b(getHours|getMinutes|getDate|getDay|getMonth|getFullYear|getTimezoneOffset|toLocaleDateString|toLocaleTimeString|toLocaleString)\b/;

function agendaProductionSources(): { path: string; content: string }[] {
  return readdirSync(AGENDA_DIR, { recursive: true, encoding: "utf-8" })
    .filter((path) => /\.(ts|tsx)$/.test(path) && !/\.test\.(ts|tsx)$/.test(path))
    .map((path) => ({
      path: path.replaceAll("\\", "/"),
      content: readFileSync(resolve(AGENDA_DIR, path), "utf-8"),
    }))
    .sort((a, b) => a.path.localeCompare(b.path));
}

describe("guardián de zona horaria y reloj en agenda", () => {
  it("prohíbe getters locales de Date y toLocale* sin timeZone y confina new Date() a clock.ts", () => {
    const sources = agendaProductionSources();

    const forbiddenLocalFiles = sources
      .filter(({ content }) => FORBIDDEN_LOCAL_GETTERS.test(content))
      .map(({ path }) => path);
    expect(forbiddenLocalFiles).toEqual([]);

    const filesWithNewDateNoArgs = sources
      .filter(({ content }) => /\bnew\s+Date\s*\(\s*\)/.test(content))
      .map(({ path }) => path);
    expect(filesWithNewDateNoArgs).toEqual(["clock.ts"]);

    const filesWithUtcHelpers = sources
      .filter(({ content }) => /\b(getUTCFullYear|getUTCMonth|getUTCDate|getUTCDay|Date\.UTC)\b/.test(content))
      .map(({ path }) => path);
    expect(filesWithUtcHelpers).toEqual(["agendaTime.ts"]);
  });
});
