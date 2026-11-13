import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { AgendaAppointment } from "./agendaApi";
import { AgendaGrid } from "./AgendaGrid";
import { computeAxis, groupByProfessional } from "./agendaLayout";

const APPOINTMENT: AgendaAppointment = {
  id: "00000000-0000-0000-0000-000000000aa1",
  patientId: "00000000-0000-0000-0000-0000000000c1",
  patientName: "Ana Pérez",
  professionalId: "00000000-0000-0000-0000-000000000001",
  professionalName: "Dra. Laura Quiroga",
  chairId: "00000000-0000-0000-0000-0000000000b1",
  chairName: "Sillón 1",
  serviceId: "00000000-0000-0000-0000-0000000000d1",
  serviceName: "Consulta",
  startAt: "2026-11-16T13:00:00Z",
  endAt: "2026-11-16T13:30:00Z",
  status: "reservado",
};

const PROFESSIONALS = [
  {
    id: "00000000-0000-0000-0000-000000000001",
    fullName: "Dra. Laura Quiroga",
    active: true,
    licenseNumber: "MN1234",
  },
];

describe("AgendaGrid — Turnos accionables", () => {
  it("cada turno en AgendaGrid es un button type=button accesible con aria-label completo", () => {
    const date = "2026-11-16";
    const timezone = "America/Argentina/Buenos_Aires";
    const axis = computeAxis({
      date,
      timezone,
      workingHours: [],
      blocks: [],
      appointments: [APPOINTMENT],
    });
    const columns = groupByProfessional({
      professionals: PROFESSIONALS,
      workingHours: [],
      blocks: [],
      appointments: [APPOINTMENT],
      weekday: 1,
    });

    render(
      <AgendaGrid
        date={date}
        timezone={timezone}
        axis={axis}
        columns={columns}
      />,
    );

    const card = screen.getByTestId(`agenda-appointment-${APPOINTMENT.id}`);
    expect(card.tagName).toBe("BUTTON");
    expect(card).toHaveAttribute("type", "button");
    expect(card).toHaveAttribute(
      "aria-label",
      "10:00–10:30, Ana Pérez, Consulta, Dra. Laura Quiroga, Sillón 1, Reservado",
    );
  });

  it("al pulsar el turno invoca onSelectAppointment con los datos del turno", () => {
    const date = "2026-11-16";
    const timezone = "America/Argentina/Buenos_Aires";
    const axis = computeAxis({
      date,
      timezone,
      workingHours: [],
      blocks: [],
      appointments: [APPOINTMENT],
    });
    const columns = groupByProfessional({
      professionals: PROFESSIONALS,
      workingHours: [],
      blocks: [],
      appointments: [APPOINTMENT],
      weekday: 1,
    });
    let selected: AgendaAppointment | null = null;

    render(
      <AgendaGrid
        date={date}
        timezone={timezone}
        axis={axis}
        columns={columns}
        onSelectAppointment={(appt) => {
          selected = appt;
        }}
      />,
    );

    const card = screen.getByTestId(`agenda-appointment-${APPOINTMENT.id}`);
    fireEvent.click(card);
    expect(selected).toEqual(APPOINTMENT);
  });
});
