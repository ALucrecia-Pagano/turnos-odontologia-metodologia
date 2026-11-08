import { describe, expect, it } from "vitest";
import {
  appointmentRange,
  assignLanes,
  clampRange,
  compareProfessionals,
  computeAxis,
  groupByProfessional,
} from "./agendaLayout";

const BUENOS_AIRES_TZ = "America/Argentina/Buenos_Aires";
const QUIROGA_ID = "00000000-0000-0000-0000-000000000001";
const SOSA_ID = "00000000-0000-0000-0000-000000000002";
const BENITEZ_ID = "00000000-0000-0000-0000-000000000003";

describe("agendaLayout — eje de horas (R4)", () => {
  it("calcula el eje 08:00 a 20:00 para el lunes 2026-11-16 con horarios 09:00–13:00 y 15:00–19:00, bloqueo y turnos", () => {
    const axis = computeAxis({
      date: "2026-11-16",
      timezone: BUENOS_AIRES_TZ,
      workingHours: [
        { professionalId: QUIROGA_ID, weekday: 1, start: "09:00", end: "13:00" },
        { professionalId: QUIROGA_ID, weekday: 1, start: "15:00", end: "19:00" },
        { professionalId: SOSA_ID, weekday: 1, start: "09:00", end: "13:00" },
      ],
      blocks: [
        {
          id: "00000000-0000-0000-0000-0000000000f1",
          professionalId: QUIROGA_ID,
          startAt: "2026-11-16T15:00:00Z",
          endAt: "2026-11-16T16:00:00Z",
          reason: "Congreso",
        },
      ],
      appointments: [
        {
          id: "00000000-0000-0000-0000-0000000000a1",
          professionalId: QUIROGA_ID,
          startAt: "2026-11-16T13:00:00Z",
          endAt: "2026-11-16T13:30:00Z",
        },
        {
          id: "00000000-0000-0000-0000-0000000000a2",
          professionalId: SOSA_ID,
          startAt: "2026-11-16T12:00:00Z",
          endAt: "2026-11-16T12:30:00Z",
        },
      ],
    });

    expect(axis.startMinute).toBe(480);
    expect(axis.endMinute).toBe(1200);
    expect(axis.hours).toEqual([
      "08:00",
      "09:00",
      "10:00",
      "11:00",
      "12:00",
      "13:00",
      "14:00",
      "15:00",
      "16:00",
      "17:00",
      "18:00",
      "19:00",
      "20:00",
    ]);
  });

  it("usa 08:00–20:00 en día vacío, expande rangos menores a 4 horas y clampea bloqueos y turnos en medianoche a [0, 1440]", () => {
    const emptyAxis = computeAxis({
      date: "2026-11-15",
      timezone: BUENOS_AIRES_TZ,
      workingHours: [
        { professionalId: QUIROGA_ID, weekday: 1, start: "09:00", end: "13:00" },
      ],
      blocks: [],
      appointments: [],
    });
    expect(emptyAxis.startMinute).toBe(480);
    expect(emptyAxis.endMinute).toBe(1200);

    const shortAxis = computeAxis({
      date: "2026-11-16",
      timezone: BUENOS_AIRES_TZ,
      workingHours: [],
      blocks: [],
      appointments: [
        {
          id: "00000000-0000-0000-0000-0000000000a1",
          professionalId: QUIROGA_ID,
          startAt: "2026-11-16T13:00:00Z",
          endAt: "2026-11-16T13:30:00Z",
        },
      ],
    });
    expect(shortAxis.endMinute - shortAxis.startMinute).toBeGreaterThanOrEqual(240);

    expect(clampRange(-60, 1500)).toEqual({ startMinute: 0, endMinute: 1440 });

    const midnightAxis = computeAxis({
      date: "2026-11-16",
      timezone: BUENOS_AIRES_TZ,
      workingHours: [],
      blocks: [
        {
          id: "00000000-0000-0000-0000-0000000000f2",
          professionalId: QUIROGA_ID,
          startAt: "2026-11-16T02:00:00Z",
          endAt: "2026-11-16T04:00:00Z",
          reason: "Guardia",
        },
      ],
      appointments: [
        {
          id: "00000000-0000-0000-0000-0000000000a3",
          professionalId: QUIROGA_ID,
          startAt: "2026-11-17T02:30:00Z",
          endAt: "2026-11-17T03:00:00Z",
        },
      ],
    });
    expect(midnightAxis.startMinute).toBe(0);
    expect(midnightAxis.endMinute).toBe(1440);
  });
});

describe("agendaLayout — columnas por profesional (R5)", () => {
  const CATALOG_A = [
    { id: QUIROGA_ID, fullName: "Dra. Laura Quiroga", active: true },
    { id: BENITEZ_ID, fullName: "Dra. Paula Benítez", active: true },
    { id: SOSA_ID, fullName: "Dr. Martín Sosa", active: true },
  ];
  const CATALOG_B = [
    { id: SOSA_ID, fullName: "Dr. Martín Sosa", active: true },
    { id: QUIROGA_ID, fullName: "Dra. Laura Quiroga", active: true },
    { id: BENITEZ_ID, fullName: "Dra. Paula Benítez", active: true },
  ];

  it("ordena las columnas de forma alfabética estable con desempate por id, conserva columnas vacías y une defensivamente la agenda", () => {
    const colsA = groupByProfessional({
      professionals: CATALOG_A,
      workingHours: [],
      blocks: [],
      appointments: [
        {
          id: "00000000-0000-0000-0000-0000000000a1",
          professionalId: QUIROGA_ID,
          professionalName: "Dra. Laura Quiroga",
          startAt: "2026-11-16T13:00:00Z",
          endAt: "2026-11-16T13:30:00Z",
        },
      ],
      weekday: 1,
    });
    const colsB = groupByProfessional({
      professionals: CATALOG_B,
      workingHours: [],
      blocks: [],
      appointments: [],
      weekday: 1,
    });

    expect(colsA.map((col) => col.fullName)).toEqual([
      "Dr. Martín Sosa",
      "Dra. Laura Quiroga",
      "Dra. Paula Benítez",
    ]);
    expect(colsB.map((col) => col.fullName)).toEqual(colsA.map((col) => col.fullName));
    expect(colsA[2]?.appointments).toEqual([]);

    expect(
      compareProfessionals(
        { id: "00000000-0000-0000-0000-000000000009", fullName: "Dr. Martín Sosa" },
        { id: "00000000-0000-0000-0000-000000000002", fullName: "dr. martín sosa" },
      ),
    ).toBeGreaterThan(0);

    const fallbackCols = groupByProfessional({
      professionals: [],
      workingHours: [],
      blocks: [],
      appointments: [
        {
          id: "00000000-0000-0000-0000-0000000000a1",
          professionalId: QUIROGA_ID,
          professionalName: "Dra. Laura Quiroga",
          startAt: "2026-11-16T13:00:00Z",
          endAt: "2026-11-16T13:30:00Z",
        },
      ],
      weekday: 1,
    });
    expect(fallbackCols.map((col) => col.displayLabel)).toEqual(["Dra. Laura Quiroga"]);
  });

  it("marca profesionales inactivos con (inactivo) y el filtro professionalId deja una sola columna", () => {
    const withInactive = groupByProfessional({
      professionals: [
        { id: QUIROGA_ID, fullName: "Dra. Laura Quiroga", active: true },
        { id: BENITEZ_ID, fullName: "Dra. Paula Benítez", active: false },
      ],
      workingHours: [],
      blocks: [],
      appointments: [],
      weekday: 1,
    });
    expect(withInactive.map((col) => col.displayLabel)).toEqual([
      "Dra. Laura Quiroga",
      "Dra. Paula Benítez (inactivo)",
    ]);

    const filtered = groupByProfessional({
      professionals: CATALOG_A,
      workingHours: [],
      blocks: [],
      appointments: [],
      weekday: 1,
      filterProfessionalId: QUIROGA_ID,
    });
    expect(filtered.map((col) => col.displayLabel)).toEqual(["Dra. Laura Quiroga"]);
  });
});

describe("agendaLayout — posición, alto y carriles (R6)", () => {
  it("asigna carriles a turnos sin solape, a un cancelado y un activo superpuestos y a tres turnos en cadena", () => {
    const single = assignLanes(
      [
        {
          id: "00000000-0000-0000-0000-0000000000a1",
          professionalId: QUIROGA_ID,
          startAt: "2026-11-16T13:00:00Z",
          endAt: "2026-11-16T13:30:00Z",
        },
        {
          id: "00000000-0000-0000-0000-0000000000a2",
          professionalId: QUIROGA_ID,
          startAt: "2026-11-16T14:00:00Z",
          endAt: "2026-11-16T14:30:00Z",
        },
      ],
      { date: "2026-11-16", timezone: BUENOS_AIRES_TZ, axisStartMinute: 480, axisEndMinute: 1200 },
    );
    expect(single.map((item) => ({ lane: item.lane, laneCount: item.laneCount, offset: item.offsetMinutes }))).toEqual([
      { lane: 0, laneCount: 1, offset: 120 },
      { lane: 0, laneCount: 1, offset: 180 },
    ]);

    const cancelledAndActive = assignLanes(
      [
        {
          id: "00000000-0000-0000-0000-0000000000a2",
          professionalId: SOSA_ID,
          startAt: "2026-11-16T12:00:00Z",
          endAt: "2026-11-16T12:30:00Z",
          status: "cancelado" as const,
        },
        {
          id: "00000000-0000-0000-0000-0000000000a3",
          professionalId: SOSA_ID,
          startAt: "2026-11-16T12:00:00Z",
          endAt: "2026-11-16T12:30:00Z",
          status: "reservado" as const,
        },
      ],
      { date: "2026-11-16", timezone: BUENOS_AIRES_TZ, axisStartMinute: 480, axisEndMinute: 1200 },
    );
    expect(cancelledAndActive.map((item) => ({ id: item.appointment.id, lane: item.lane, laneCount: item.laneCount }))).toEqual([
      { id: "00000000-0000-0000-0000-0000000000a2", lane: 0, laneCount: 2 },
      { id: "00000000-0000-0000-0000-0000000000a3", lane: 1, laneCount: 2 },
    ]);

    const chained = assignLanes(
      [
        {
          id: "00000000-0000-0000-0000-0000000000c1",
          professionalId: SOSA_ID,
          startAt: "2026-11-16T12:00:00Z",
          endAt: "2026-11-16T13:00:00Z",
        },
        {
          id: "00000000-0000-0000-0000-0000000000c2",
          professionalId: SOSA_ID,
          startAt: "2026-11-16T12:30:00Z",
          endAt: "2026-11-16T13:30:00Z",
        },
        {
          id: "00000000-0000-0000-0000-0000000000c3",
          professionalId: SOSA_ID,
          startAt: "2026-11-16T13:00:00Z",
          endAt: "2026-11-16T14:00:00Z",
        },
      ],
      { date: "2026-11-16", timezone: BUENOS_AIRES_TZ, axisStartMinute: 480, axisEndMinute: 1200 },
    );
    expect(chained.map((item) => ({ lane: item.lane, laneCount: item.laneCount }))).toEqual([
      { lane: 0, laneCount: 2 },
      { lane: 1, laneCount: 2 },
      { lane: 0, laneCount: 2 },
    ]);
  });

  it("aplica alto mínimo a un turno de 5 minutos, clampea el inicio al eje y soporta un turno que termina a las 00:00", () => {
    const fiveMin = assignLanes(
      [
        {
          id: "00000000-0000-0000-0000-0000000000a5",
          professionalId: QUIROGA_ID,
          startAt: "2026-11-16T12:00:00Z",
          endAt: "2026-11-16T12:05:00Z",
        },
      ],
      { date: "2026-11-16", timezone: BUENOS_AIRES_TZ, axisStartMinute: 480, axisEndMinute: 1200 },
    );
    expect(fiveMin[0]?.durationMinutes).toBe(5);
    expect(fiveMin[0]?.effectiveMinutes).toBe(15);

    const clampedBeforeAxis = assignLanes(
      [
        {
          id: "00000000-0000-0000-0000-0000000000a6",
          professionalId: QUIROGA_ID,
          startAt: "2026-11-16T10:30:00Z",
          endAt: "2026-11-16T11:30:00Z",
        },
      ],
      { date: "2026-11-16", timezone: BUENOS_AIRES_TZ, axisStartMinute: 480, axisEndMinute: 1200 },
    );
    expect(clampedBeforeAxis[0]?.startMinute).toBe(480);
    expect(clampedBeforeAxis[0]?.offsetMinutes).toBe(0);
    expect(clampedBeforeAxis[0]?.durationMinutes).toBe(30);

    const endsAtMidnight = appointmentRange(
      "2026-11-17T02:30:00Z",
      "2026-11-17T03:00:00Z",
      "2026-11-16",
      BUENOS_AIRES_TZ,
    );
    expect(endsAtMidnight).toEqual({ startMinute: 1410, endMinute: 1440 });
  });
});


