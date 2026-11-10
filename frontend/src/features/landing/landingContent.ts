export interface Professional {
  readonly name: string;
  readonly schedule: string;
}

export interface Service {
  readonly name: string;
  readonly durationMinutes: number;
  readonly description: string;
}

export const heroLead =
  "Turnos ordenados para que la atención fluya: elegí profesional, sillón y prestación, y el sistema evita superposiciones.";

export const demoBadge = "Sitio de demostración";

export const professionals: readonly Professional[] = [
  {
    name: "Dr. Martín Sosa",
    schedule: "Atiende de lunes a viernes por la mañana.",
  },
  {
    name: "Dra. Laura Quiroga",
    schedule: "Atiende de lunes a viernes, mañana y tarde.",
  },
  {
    name: "Dra. Paula Benítez",
    schedule: "Atiende de lunes a viernes, mañana y tarde.",
  },
];

export const services: readonly Service[] = [
  {
    name: "Limpieza",
    durationMinutes: 45,
    description: "Profilaxis y control de sarro.",
  },
  {
    name: "Extracción",
    durationMinutes: 60,
    description: "Extracciones simples con indicaciones de cuidado.",
  },
  {
    name: "Restauración",
    durationMinutes: 60,
    description: "Recuperación de piezas dañadas.",
  },
  {
    name: "Control",
    durationMinutes: 30,
    description: "Revisión general y seguimiento.",
  },
  {
    name: "Blanqueamiento",
    durationMinutes: 90,
    description: "Tratamiento estético.",
  },
];

export const schedule = {
  weekdays: "Lunes a viernes",
  morning: "9:00 a 13:00",
  afternoon: "15:00 a 19:00",
};

export const contact = {
  address: "Av. Ejemplo 1234, Ciudad Demo",
  phone: "(0261) 555-0101",
  email: "turnos@aqua-demo.example",
};

export const demoContactNote =
  "Datos de contacto ficticios, solo para la demostración. No agendar turnos reales.";
