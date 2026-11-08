import { safeInternalPath } from "./safeInternalPath";

describe("safeInternalPath", () => {
  it("acepta una ruta interna con query string como /agenda?date=2026-11-07", () => {
    expect(safeInternalPath("/agenda?date=2026-11-07")).toBe("/agenda?date=2026-11-07");
  });

  it("se rechaza una ruta protocol-relative", () => {
    expect(safeInternalPath("//evil.com")).toBe("/");
  });

  it("se rechaza una URL absoluta", () => {
    expect(safeInternalPath("https://evil.example")).toBe("/");
    expect(safeInternalPath("http://evil.example/agenda")).toBe("/");
    expect(safeInternalPath(undefined)).toBe("/");
  });

  it("se rechaza volver al propio login", () => {
    expect(safeInternalPath("/login")).toBe("/");
    expect(safeInternalPath("/login?next=/agenda")).toBe("/");
  });
});
