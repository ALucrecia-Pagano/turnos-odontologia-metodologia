import { describe, expect, it } from "vitest";
import { contact, demoContactNote, professionals, schedule, services } from "./landingContent";

describe("contenido de la portada", () => {
  it("el equipo coincide con el seed", () => {
    expect(professionals).toHaveLength(3);
    expect(professionals.map((professional) => professional.name)).toEqual([
      "Dr. Martín Sosa",
      "Dra. Laura Quiroga",
      "Dra. Paula Benítez",
    ]);
    expect(professionals[0]?.schedule).toBe("Atiende de lunes a viernes por la mañana.");
    expect(professionals[1]?.schedule).toBe("Atiende de lunes a viernes, mañana y tarde.");
    expect(professionals[2]?.schedule).toBe("Atiende de lunes a viernes, mañana y tarde.");
  });

  it("los servicios y duraciones coinciden con el seed", () => {
    expect(services.map((service) => [service.name, service.durationMinutes])).toEqual([
      ["Limpieza", 45],
      ["Extracción", 60],
      ["Restauración", 60],
      ["Control", 30],
      ["Blanqueamiento", 90],
    ]);
  });

  it("horarios y contacto son ficticios y coinciden con el seed", () => {
    expect(schedule).toEqual({
      weekdays: "Lunes a viernes",
      morning: "9:00 a 13:00",
      afternoon: "15:00 a 19:00",
    });
    expect(contact).toEqual({
      address: "Av. Ejemplo 1234, Ciudad Demo",
      phone: "(0261) 555-0101",
      email: "turnos@aqua-demo.example",
    });
    expect(demoContactNote).toBe(
      "Datos de contacto ficticios, solo para la demostración. No agendar turnos reales.",
    );
  });
});
