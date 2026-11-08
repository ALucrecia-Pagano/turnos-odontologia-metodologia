import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { AgendaAppointment } from "./agendaApi";
import { AgendaTable } from "./AgendaTable";

const APPOINTMENTS: readonly AgendaAppointment[] = [
  {
    id: "00000000-0000-0000-0000-000000000aa2",
    patientId: "00000000-0000-0000-0000-0000000000c2",
    patientName: "Bruno Acosta",
    professionalId: "00000000-0000-0000-0000-000000000002",
    professionalName: "Dr. Martín Sosa",
    chairId: "00000000-0000-0000-0000-0000000000b2",
    chairName: "Sillón 2",
    serviceId: "00000000-0000-0000-0000-0000000000d4",
    serviceName: "Control",
    startAt: "2026-11-16T12:00:00Z",
    endAt: "2026-11-16T12:30:00Z",
    status: "cancelado",
  },
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

describe("AgendaTable", () => {
  it("renderiza la tabla semántica con caption, encabezados con scope=col y filas en el mismo orden de la agenda", () => {
    render(
      <AgendaTable
        date="2026-11-16"
        timezone="America/Argentina/Buenos_Aires"
        appointments={APPOINTMENTS}
      />,
    );

    const table = screen.queryByRole("table", {
      name: "Turnos del lunes 16 de noviembre de 2026",
    });
    expect(table).not.toBeNull();

    const headers = within(table!).queryAllByRole("columnheader");
    expect(headers.map((th) => th.textContent)).toEqual([
      "Hora",
      "Paciente",
      "Profesional",
      "Sillón",
      "Prestación",
      "Estado",
    ]);
    for (const th of headers) {
      expect(th).toHaveAttribute("scope", "col");
    }

    const rows = within(table!).queryAllByRole("row").slice(1);
    expect(rows).toHaveLength(2);

    const sosaCells = within(rows[0]!).queryAllByRole("cell").map((td) => td.textContent);
    expect(sosaCells).toEqual([
      "09:00–09:30",
      "Bruno Acosta",
      "Dr. Martín Sosa",
      "Sillón 2",
      "Control",
      "Cancelado",
    ]);

    const quirogaCells = within(rows[1]!).queryAllByRole("cell").map((td) => td.textContent);
    expect(quirogaCells).toEqual([
      "10:00–10:30",
      "Ana Pérez",
      "Dra. Laura Quiroga",
      "Sillón 1",
      "Control",
      "Reservado",
    ]);
  });
});
