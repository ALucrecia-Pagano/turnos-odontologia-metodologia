import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { AgendaAppointment, AgendaResponse, Chair, Professional } from "./agendaApi";
import { AgendaView } from "./AgendaView";

const PROFESSIONALS: readonly Professional[] = [
  {
    id: "00000000-0000-0000-0000-000000000001",
    fullName: "Dra. Laura Quiroga",
    licenseNumber: "MP-1001",
    active: true,
  },
  {
    id: "00000000-0000-0000-0000-000000000002",
    fullName: "Dr. Martín Sosa",
    licenseNumber: "MP-1002",
    active: true,
  },
  {
    id: "00000000-0000-0000-0000-000000000003",
    fullName: "Dr. Benítez",
    licenseNumber: "MP-1003",
    active: true,
  },
];

const CHAIRS: readonly Chair[] = [
  { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón 1", active: true },
  { id: "00000000-0000-0000-0000-0000000000b2", name: "Sillón 2", active: true },
  { id: "00000000-0000-0000-0000-0000000000b3", name: "Sillón 3", active: true },
];

const WORKING_HOURS = [
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
  {
    professionalId: "00000000-0000-0000-0000-000000000002",
    weekday: 1,
    start: "09:00",
    end: "13:00",
  },
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

describe("AgendaView — Modo Sillones", () => {
  it("Turnos de distintos profesionales en la misma columna: dos profesionales en una columna de sillón", () => {
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
        startAt: "2026-11-16T13:00:00Z", // 10:00
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

    const agenda: AgendaResponse = {
      from: "2026-11-16",
      to: "2026-11-16",
      timezone: "America/Argentina/Buenos_Aires",
      appointments,
      workingHours: WORKING_HOURS,
      blocks: [],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone="America/Argentina/Buenos_Aires"
        agenda={agenda}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        view="chair"
      />,
    );

    // Tres columnas: Sillón 1, Sillón 2, Sillón 3
    expect(screen.queryByText("Sillón 1")).not.toBeNull();
    expect(screen.queryByText("Sillón 2")).not.toBeNull();
    expect(screen.queryByText("Sillón 3")).not.toBeNull();

    // Columna Sillón 1 contiene las dos tarjetas y muestran sus profesionales en texto
    const col1 = screen.queryByTestId("agenda-column-00000000-0000-0000-0000-0000000000b1");
    expect(col1).not.toBeNull();
    expect(col1).toHaveTextContent("Dra. Laura Quiroga");
    expect(col1).toHaveTextContent("Dr. Martín Sosa");
    expect(col1).toHaveTextContent("Ana Pérez");
    expect(col1).toHaveTextContent("Carlos Gómez");
  });

  it("Sillón sin turnos: sillón sin turnos muestra Libre y Fuera de horario", () => {
    const agenda: AgendaResponse = {
      from: "2026-11-16",
      to: "2026-11-16",
      timezone: "America/Argentina/Buenos_Aires",
      appointments: [],
      workingHours: WORKING_HOURS,
      blocks: [],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone="America/Argentina/Buenos_Aires"
        agenda={agenda}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        view="chair"
      />,
    );

    const col2 = screen.queryByTestId("agenda-column-00000000-0000-0000-0000-0000000000b2");
    expect(col2).not.toBeNull();
    expect(col2).toHaveTextContent("Libre 09:00–13:00");
    expect(col2).toHaveTextContent("Libre 15:00–19:00");
    expect(col2).toHaveTextContent("Fuera de horario 13:00–15:00");
  });

  it("Clic en la tarjeta abre el detalle: clic en tarjeta abre AppointmentDetailDialog", () => {
    let selectedAppointment: AgendaAppointment | null = null;
    const appointment: AgendaAppointment = {
      id: "appt-detail",
      patientId: "00000000-0000-0000-0000-0000000000p1",
      patientName: "Ana Pérez",
      professionalId: "00000000-0000-0000-0000-000000000001",
      professionalName: "Dra. Laura Quiroga",
      chairId: "00000000-0000-0000-0000-0000000000b1",
      chairName: "Sillón 1",
      serviceId: "00000000-0000-0000-0000-0000000000s1",
      serviceName: "Control",
      startAt: "2026-11-16T13:00:00Z",
      endAt: "2026-11-16T13:30:00Z",
      status: "reservado",
    };

    const agenda: AgendaResponse = {
      from: "2026-11-16",
      to: "2026-11-16",
      timezone: "America/Argentina/Buenos_Aires",
      appointments: [appointment],
      workingHours: WORKING_HOURS,
      blocks: [],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone="America/Argentina/Buenos_Aires"
        agenda={agenda}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        view="chair"
        onSelectAppointment={(appt) => {
          selectedAppointment = appt;
        }}
      />,
    );

    const card = screen.queryByTestId("agenda-appointment-appt-detail");
    expect(card).not.toBeNull();
    fireEvent.click(card!);
    expect(selectedAppointment).not.toBeNull();
    expect((selectedAppointment as AgendaAppointment | null)?.id).toBe("appt-detail");
  });

  it("Nombre accesible completo en la tarjeta: aria-label incluye hora, paciente, profesional, sillón, prestación y estado", () => {
    const appointment: AgendaAppointment = {
      id: "appt-aria",
      patientId: "00000000-0000-0000-0000-0000000000p1",
      patientName: "Ana Pérez",
      professionalId: "00000000-0000-0000-0000-000000000001",
      professionalName: "Dra. Laura Quiroga",
      chairId: "00000000-0000-0000-0000-0000000000b1",
      chairName: "Sillón 1",
      serviceId: "00000000-0000-0000-0000-0000000000s1",
      serviceName: "Control",
      startAt: "2026-11-16T13:00:00Z",
      endAt: "2026-11-16T13:30:00Z",
      status: "reservado",
    };

    const agenda: AgendaResponse = {
      from: "2026-11-16",
      to: "2026-11-16",
      timezone: "America/Argentina/Buenos_Aires",
      appointments: [appointment],
      workingHours: WORKING_HOURS,
      blocks: [],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone="America/Argentina/Buenos_Aires"
        agenda={agenda}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        view="chair"
      />,
    );

    const card = screen.queryByTestId("agenda-appointment-appt-aria");
    expect(card).not.toBeNull();
    const aria = card?.getAttribute("aria-label") ?? "";
    expect(aria).toContain("10:00–10:30");
    expect(aria).toContain("Ana Pérez");
    expect(aria).toContain("Dra. Laura Quiroga");
    expect(aria).toContain("Sillón 1");
    expect(aria).toContain("Control");
    expect(aria).toContain("Reservado");
  });

  it("La lista sigue disponible: Ver como lista con columna Sillón", () => {
    const appointment: AgendaAppointment = {
      id: "appt-table",
      patientId: "00000000-0000-0000-0000-0000000000p1",
      patientName: "Ana Pérez",
      professionalId: "00000000-0000-0000-0000-000000000001",
      professionalName: "Dra. Laura Quiroga",
      chairId: "00000000-0000-0000-0000-0000000000b1",
      chairName: "Sillón 1",
      serviceId: "00000000-0000-0000-0000-0000000000s1",
      serviceName: "Control",
      startAt: "2026-11-16T13:00:00Z",
      endAt: "2026-11-16T13:30:00Z",
      status: "reservado",
    };

    const agenda: AgendaResponse = {
      from: "2026-11-16",
      to: "2026-11-16",
      timezone: "America/Argentina/Buenos_Aires",
      appointments: [appointment],
      workingHours: WORKING_HOURS,
      blocks: [],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone="America/Argentina/Buenos_Aires"
        agenda={agenda}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        view="chair"
      />,
    );

    const listBtn = screen.queryByRole("button", { name: "Ver como lista" });
    expect(listBtn).not.toBeNull();
    fireEvent.click(listBtn!);

    expect(screen.queryByRole("table")).not.toBeNull();
    expect(screen.queryByRole("columnheader", { name: "Sillón" })).not.toBeNull();
    expect(screen.queryByText("Sillón 1")).not.toBeNull();
    expect(screen.queryByText("Dra. Laura Quiroga")).not.toBeNull();
  });

  it("Un día sin turnos conserva la grilla: día sin turnos mantiene grilla y aviso", () => {
    const agenda: AgendaResponse = {
      from: "2026-11-16",
      to: "2026-11-16",
      timezone: "America/Argentina/Buenos_Aires",
      appointments: [],
      workingHours: WORKING_HOURS,
      blocks: [],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone="America/Argentina/Buenos_Aires"
        agenda={agenda}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        view="chair"
      />,
    );

    // Mantiene grilla con columnas
    expect(screen.queryByTestId("agenda-column-00000000-0000-0000-0000-0000000000b1")).not.toBeNull();
    // Muestra aviso informativo en lugar de EmptyState
    expect(screen.queryByText(/no hay turnos para este día/i)).not.toBeNull();
    expect(screen.queryByRole("heading", { name: "No hay turnos para este día" })).toBeNull();
  });

  it("Catálogo de sillones vacío: sin sillones muestra No hay sillones configurados", () => {
    const agenda: AgendaResponse = {
      from: "2026-11-16",
      to: "2026-11-16",
      timezone: "America/Argentina/Buenos_Aires",
      appointments: [],
      workingHours: WORKING_HOURS,
      blocks: [],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone="America/Argentina/Buenos_Aires"
        agenda={agenda}
        professionals={PROFESSIONALS}
        chairs={[]}
        view="chair"
      />,
    );

    expect(screen.queryByRole("heading", { name: "No hay sillones configurados" })).not.toBeNull();
  });
});
