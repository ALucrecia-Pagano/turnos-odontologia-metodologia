import { render, screen, within, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { AgendaAppointment } from "./agendaApi";
import { AgendaTable } from "./AgendaTable";

const APPOINTMENTS: readonly AgendaAppointment[] = [
  {
    id: "00000000-0000-0000-0000-000000000aa1",
    patientId: "00000000-0000-0000-0000-0000000000c1",
    patientName: "Ana Pérez",
    professionalId: "00000000-0000-0000-0000-000000000001",
    professionalName: "Dra. Laura Quiroga",
    chairId: "00000000-0000-0000-0000-0000000000b1",
    chairName: "Sillón 1",
    serviceId: "00000000-0000-0000-0000-0000000000d4",
    serviceName: "Control",
    startAt: "2026-11-16T13:00:00Z",
    endAt: "2026-11-16T13:30:00Z",
    status: "reservado",
  },
];

describe("AgendaTable — Acciones", () => {
  it("con onSelectAppointment renderiza el botón Ver turno y al activarlo invoca el callback", () => {
    let selected: AgendaAppointment | null = null;
    render(
      <AgendaTable
        date="2026-11-16"
        timezone="America/Argentina/Buenos_Aires"
        appointments={APPOINTMENTS}
        onSelectAppointment={(appt) => {
          selected = appt;
        }}
      />,
    );

    const btn = screen.getByRole("button", { name: "Ver turno" });
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(selected).toEqual(APPOINTMENTS[0]);
  });

  it("sin onSelectAppointment conserva exactamente las 6 columnas originales", () => {
    render(
      <AgendaTable
        date="2026-11-16"
        timezone="America/Argentina/Buenos_Aires"
        appointments={APPOINTMENTS}
      />,
    );

    const table = screen.getByRole("table");
    const headers = within(table).queryAllByRole("columnheader");
    expect(headers.map((th) => th.textContent)).toEqual([
      "Hora",
      "Paciente",
      "Profesional",
      "Sillón",
      "Prestación",
      "Estado",
    ]);
  });
});
