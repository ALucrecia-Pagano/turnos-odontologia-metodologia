import { describe, expect, it } from "vitest";
import { menuFor } from "./menuFor";

describe("menuFor", () => {
  it("menú del administrador incluye los 6 ítems deshabilitados con Próximamente", () => {
    const items = menuFor("administrador");
    expect(items.map((item) => item.label)).toEqual([
      "Agenda",
      "Turnos",
      "Horarios y bloqueos",
      "Catálogos",
      "Pacientes",
      "Usuarios y roles",
    ]);
    expect(items.every((item) => item.disabled === true)).toBe(true);
    expect(items.every((item) => item.badge === "Próximamente")).toBe(true);
  });

  it("menú de recepción no incluye Usuarios y roles", () => {
    const items = menuFor("recepcion");
    expect(items.map((item) => item.label)).toEqual([
      "Agenda",
      "Turnos",
      "Horarios y bloqueos",
      "Catálogos",
      "Pacientes",
    ]);
    expect(items.some((item) => item.label === "Usuarios y roles")).toBe(false);
    expect(items.every((item) => item.disabled && item.badge === "Próximamente")).toBe(true);
  });

  it("menú del odontólogo no incluye Turnos ni Usuarios y roles", () => {
    const items = menuFor("odontologo");
    expect(items.map((item) => item.label)).toEqual([
      "Agenda",
      "Horarios y bloqueos",
      "Catálogos",
      "Pacientes",
    ]);
    expect(items.some((item) => item.label === "Turnos")).toBe(false);
    expect(items.some((item) => item.label === "Usuarios y roles")).toBe(false);
    expect(items.every((item) => item.disabled && item.badge === "Próximamente")).toBe(true);
  });
});
