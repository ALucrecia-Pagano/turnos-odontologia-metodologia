import { readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { createFixedClock, systemClock, type Clock } from "./clock";

const SRC = resolve(process.cwd(), "src");

function productionSources(): { path: string; content: string }[] {
  return readdirSync(SRC, { recursive: true, encoding: "utf-8" })
    .filter((path) => /\.(ts|tsx)$/.test(path) && !/\.test\.(ts|tsx)$/.test(path))
    .map((path) => ({
      path: path.replaceAll("\\", "/"),
      content: readFileSync(resolve(SRC, path), "utf-8"),
    }));
}

describe("clock", () => {
  it("systemClock devuelve el instante actual y createFixedClock inyecta un reloj determinista con new Date() solo en clock.ts", () => {
    const before = Date.now();
    const current = systemClock.now();
    const after = Date.now();

    expect(current.getTime()).toBeGreaterThanOrEqual(before);
    expect(current.getTime()).toBeLessThanOrEqual(after);

    const fixed: Clock = createFixedClock("2026-11-16T12:00:00Z");
    expect(fixed.now().toISOString()).toBe("2026-11-16T12:00:00.000Z");

    const filesWithNewDateNoArgs = productionSources()
      .filter(({ content }) => /\bnew\s+Date\s*\(\s*\)/.test(content))
      .map(({ path }) => path);
    expect(filesWithNewDateNoArgs).toEqual(["features/agenda/clock.ts"]);
  });
});
