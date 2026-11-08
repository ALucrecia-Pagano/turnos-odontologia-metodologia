import { readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { DEFAULT_AGENDA_TIMEZONE, resolveAgendaTimezone } from "./agendaConfig";

const SRC = resolve(process.cwd(), "src");

function productionSources(): { path: string; content: string }[] {
  return readdirSync(SRC, { recursive: true, encoding: "utf-8" })
    .filter((path) => /\.(ts|tsx)$/.test(path) && !/\.test\.(ts|tsx)$/.test(path))
    .map((path) => ({
      path: path.replaceAll("\\", "/"),
      content: readFileSync(resolve(SRC, path), "utf-8"),
    }));
}

describe("agendaConfig", () => {
  it("DEFAULT_AGENDA_TIMEZONE vive en un único archivo de configuración y resolveAgendaTimezone prioriza el timezone de la respuesta", () => {
    expect(DEFAULT_AGENDA_TIMEZONE).toBe("America/Argentina/Buenos_Aires");
    expect(resolveAgendaTimezone(undefined)).toBe("America/Argentina/Buenos_Aires");
    expect(resolveAgendaTimezone(null)).toBe("America/Argentina/Buenos_Aires");
    expect(resolveAgendaTimezone("")).toBe("America/Argentina/Buenos_Aires");
    expect(resolveAgendaTimezone("America/New_York")).toBe("America/New_York");

    const filesWithBuenosAires = productionSources()
      .filter(({ content }) => /Buenos_Aires/.test(content))
      .map(({ path }) => path);
    expect(filesWithBuenosAires).toEqual(["features/agenda/agendaConfig.ts"]);
  });
});
