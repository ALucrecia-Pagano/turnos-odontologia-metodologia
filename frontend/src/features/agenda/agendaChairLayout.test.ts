import { describe, expect, it } from "vitest";
import type { AgendaAppointment, AgendaWorkingHours } from "./agendaApi";
import {
  computeChairAxis,
  computeChairFreeSlots,
  groupByChair,
  unionAttentionIntervals,
} from "./agendaChairLayout";

const WORKING_HOURS_WEEKDAY: readonly AgendaWorkingHours[] = [
  // Quiroga (lunes 09:00–13:00 y 15:00–19:00)
  {
    professionalId: "00000000-0000-0000-0000-000000000001",
    weekday: 1,
    start: "09:00",
    end: "13:00",
  },
  {
    professionalId: "00000000-0000-0000-0000-000000000001",
    weekday: 1,
    start: "15:00",
    end: "19:00",
  },
  // Sosa (lunes solo 09:00–13:00)
  {
    professionalId: "00000000-0000-0000-0000-000000000002",
    weekday: 1,
    start: "09:00",
    end: "13:00",
  },
  // Benítez (lunes 09:00–13:00 y 15:00–19:00)
  {
    professionalId: "00000000-0000-0000-0000-000000000003",
    weekday: 1,
    start: "09:00",
    end: "13:00",
  },
  {
    professionalId: "00000000-0000-0000-0000-000000000003",
    weekday: 1,
    start: "15:00",
    end: "19:00",
  },
];

describe("agendaChairLayout — Módulo puro", () => {
  it("El filtro de profesional recalcula los horarios: professionalId de Sosa deja unión 09:00–13:00", () => {
    const union = unionAttentionIntervals({
      workingHours: WORKING_HOURS_WEEKDAY,
      weekday: 1,
      professionalId: "00000000-0000-0000-0000-000000000002",
    });

    expect(union).toEqual([{ startMinute: 540, endMinute: 780 }]);
  });

  it("Hueco libre entre dos turnos: hueco 10:30–11:00 entre dos turnos", () => {
    const appointments: readonly AgendaAppointment[] = [
      {
        id: "appt-1",
        patientId: "00000000-0000-0000-0000-0000000000p1",
        patientName: "Ana Pérez",
        professionalId: "00000000-0000-0000-0000-000000000001",
        professionalName: "Dra. Laura Quiroga",
        chairId: "00000000-0000-0000-0000-0000000000b1",
        chairName: "Sillón 1",
        serviceId: "00000000-0000-0000-0000-0000000000s1",
        serviceName: "Control",
        startAt: "2026-11-16T13:00:00Z", // 10:00 en America/Argentina/Buenos_Aires
        endAt: "2026-11-16T13:30:00Z",   // 10:30
        status: "reservado",
      },
      {
        id: "appt-2",
        patientId: "00000000-0000-0000-0000-0000000000p2",
        patientName: "Carlos Gómez",
        professionalId: "00000000-0000-0000-0000-000000000002",
        professionalName: "Dr. Martín Sosa",
        chairId: "00000000-0000-0000-0000-0000000000b1",
        chairName: "Sillón 1",
        serviceId: "00000000-0000-0000-0000-0000000000s2",
        serviceName: "Limpieza",
        startAt: "2026-11-16T14:00:00Z", // 11:00
        endAt: "2026-11-16T14:30:00Z",   // 11:30
        status: "confirmado",
      },
    ];

    const slots = computeChairFreeSlots({
      attention: [
        { startMinute: 540, endMinute: 780 },
        { startMinute: 900, endMinute: 1140 },
      ],
      appointments,
      date: "2026-11-16",
      timezone: "America/Argentina/Buenos_Aires",
      chairName: "Sillón 1",
    });

    const free1030 = slots.find(
      (s) => s.kind === "free" && s.startMinute === 630 && s.endMinute === 660,
    );
    expect(free1030).toBeDefined();
    expect(free1030?.label).toBe("Libre 10:30–11:00");
    expect(free1030?.ariaLabel).toBe("Sillón 1 libre de 10:30 a 11:00");

    // Fuera de horario entre 13:00 y 15:00
    const outside = slots.find(
      (s) => s.kind === "outside" && s.startMinute === 780 && s.endMinute === 900,
    );
    expect(outside).toBeDefined();
    expect(outside?.label).toBe("Fuera de horario 13:00–15:00");

    // Huecos menores a 15 minutos no se rotulan como libres
    const smallSlot = slots.find(
      (s) => s.kind === "free" && s.endMinute - s.startMinute < 15,
    );
    expect(smallSlot).toBeUndefined();
  });

  it("Un cancelado no ocupa el sillón: cancelado libera el tramo", () => {
    const appointments: readonly AgendaAppointment[] = [
      {
        id: "appt-canc",
        patientId: "00000000-0000-0000-0000-0000000000p1",
        patientName: "Paciente Cancelado",
        professionalId: "00000000-0000-0000-0000-000000000002",
        professionalName: "Dr. Martín Sosa",
        chairId: "00000000-0000-0000-0000-0000000000b1",
        chairName: "Sillón 1",
        serviceId: "00000000-0000-0000-0000-0000000000s1",
        serviceName: "Extracción",
        startAt: "2026-11-16T12:00:00Z", // 09:00
        endAt: "2026-11-16T12:30:00Z",   // 09:30
        status: "cancelado",
      },
      {
        id: "appt-aus",
        patientId: "00000000-0000-0000-0000-0000000000p2",
        patientName: "Paciente Ausente",
        professionalId: "00000000-0000-0000-0000-000000000002",
        professionalName: "Dr. Martín Sosa",
        chairId: "00000000-0000-0000-0000-0000000000b1",
        chairName: "Sillón 1",
        serviceId: "00000000-0000-0000-0000-0000000000s2",
        serviceName: "Control",
        startAt: "2026-11-16T12:30:00Z", // 09:30
        endAt: "2026-11-16T13:00:00Z",   // 10:00
        status: "ausente",
      },
    ];

    const slots = computeChairFreeSlots({
      attention: [{ startMinute: 540, endMinute: 780 }],
      appointments,
      date: "2026-11-16",
      timezone: "America/Argentina/Buenos_Aires",
      chairName: "Sillón 1",
    });

    const freeMorning = slots.find(
      (s) => s.kind === "free" && s.startMinute === 540 && s.endMinute === 780,
    );
    expect(freeMorning).toBeDefined();
    expect(freeMorning?.label).toBe("Libre 09:00–13:00");
  });

  it("Eje con la unión de horarios del día: eje 09:00–19:00 y gap 13:00–15:00", () => {
    const union = unionAttentionIntervals({
      workingHours: WORKING_HOURS_WEEKDAY,
      weekday: 1,
    });
    expect(union).toEqual([
      { startMinute: 540, endMinute: 780 },
      { startMinute: 900, endMinute: 1140 },
    ]);

    const axis = computeChairAxis({
      workingHours: WORKING_HOURS_WEEKDAY,
      weekday: 1,
      appointments: [],
      date: "2026-11-16",
      timezone: "America/Argentina/Buenos_Aires",
    });

    expect(axis.startMinute).toBe(540); // 09:00
    expect(axis.endMinute).toBe(1140);  // 19:00
    expect(axis.hours[0]).toBe("09:00");
    expect(axis.hours[axis.hours.length - 1]).toBe("19:00");
  });

  it("Día sin horarios de atención: sin horarios usa 08:00–20:00 sin Libre", () => {
    const axis = computeChairAxis({
      workingHours: [],
      weekday: 6,
      appointments: [],
      date: "2026-11-21",
      timezone: "America/Argentina/Buenos_Aires",
    });

    expect(axis.startMinute).toBe(480); // 08:00
    expect(axis.endMinute).toBe(1200);  // 20:00
    expect(axis.hours[0]).toBe("08:00");
    expect(axis.hours[axis.hours.length - 1]).toBe("20:00");

    const slots = computeChairFreeSlots({
      attention: [],
      appointments: [],
      date: "2026-11-21",
      timezone: "America/Argentina/Buenos_Aires",
      chairName: "Sillón 1",
    });
    expect(slots.filter((s) => s.kind === "free")).toHaveLength(0);
  });

  it("Sillón inactivo visible: sillón inactivo con sufijo (inactivo)", () => {
    const chairs = [
      { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón B", active: true },
      { id: "00000000-0000-0000-0000-0000000000b2", name: "Sillón A", active: false },
    ];

    const appointments: readonly AgendaAppointment[] = [
      {
        id: "appt-x",
        patientId: "00000000-0000-0000-0000-0000000000p3",
        patientName: "Turno En Sillón Extra",
        professionalId: "00000000-0000-0000-0000-000000000001",
        professionalName: "Dra. Laura Quiroga",
        chairId: "00000000-0000-0000-0000-0000000000b3",
        chairName: "Sillón C",
        serviceId: "00000000-0000-0000-0000-0000000000s3",
        serviceName: "Consulta",
        startAt: "2026-11-16T13:00:00Z",
        endAt: "2026-11-16T13:30:00Z",
        status: "confirmado",
      },
    ];

    const columns = groupByChair({
      chairs,
      appointments,
      workingHours: WORKING_HOURS_WEEKDAY,
      date: "2026-11-16",
      timezone: "America/Argentina/Buenos_Aires",
      weekday: 1,
    });

    // Orden alfabético: Sillón A, Sillón B, Sillón C
    expect(columns.map((c) => c.displayLabel)).toEqual([
      "Sillón A (inactivo)",
      "Sillón B",
      "Sillón C",
    ]);

    expect(columns[0]?.active).toBe(false);
    expect(columns[1]?.active).toBe(true);
    expect(columns[2]?.active).toBe(true);
    expect(columns[2]?.appointments).toHaveLength(1);
    expect(columns[0]?.blocks).toHaveLength(0);
  });
});
