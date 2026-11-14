import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { AgendaAppointment } from "./agendaApi";
import { AgendaGrid } from "./AgendaGrid";
import { computeAxis, groupByProfessional } from "./agendaLayout";
import { AgendaView } from "./AgendaView";

const PROFESSIONALS = [
  {
    id: "00000000-0000-0000-0000-000000000001",
    fullName: "Dra. Laura Quiroga",
    active: true,
    licenseNumber: "MN1234",
  },
  {
    id: "00000000-0000-0000-0000-000000000002",
    fullName: "Dr. Martín Sosa",
    active: true,
    licenseNumber: "MN5678",
  },
];

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

describe("AgendaGrid — Modo Móvil (<= 640 px)", () => {
  it("05-grilla-scroll-snap-y-horas-sticky: aplica scroll-snap horizontal mandatory y eje horario fijo en celular", () => {
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
        isMobile={true}
      />,
    );

    const scrollContainer = screen.getByTestId("agenda-grid-scroll");
    expect(scrollContainer).toHaveAttribute("data-scroll-snap", "mandatory");

    const timeGutter = screen.getByTestId("agenda-time-gutter");
    expect(timeGutter).toBeInTheDocument();

    const columnTracks = screen.getAllByTestId(/^agenda-column-/);
    expect(columnTracks.length).toBeGreaterThan(0);
    for (const track of columnTracks) {
      expect(track).toHaveAttribute("data-snap-align", "start");
    }
  });

  it("06-grilla-ancho-util-y-default-grid: preserva modo inicial grilla en AgendaView y dimensiona columnas a ancho útil en móvil", () => {
    // 1. Modo por defecto en AgendaView
    render(
      <AgendaView
        date="2026-11-16"
        timezone="America/Argentina/Buenos_Aires"
        agenda={{
          from: "2026-11-16",
          to: "2026-11-16",
          timezone: "America/Argentina/Buenos_Aires",
          appointments: [APPOINTMENT],
          workingHours: [],
          blocks: [],
        }}
        professionals={PROFESSIONALS}
      />,
    );

    const scrollContainer = screen.queryByTestId("agenda-grid-scroll");
    expect(scrollContainer).not.toBeNull();
    expect(screen.queryByTestId("agenda-table")).not.toBeInTheDocument();
    const listToggleBtn = screen.getByRole("button", { name: "Ver como lista" });
    expect(listToggleBtn).toHaveAttribute("aria-pressed", "false");

    // 2. Columnas con ancho útil móvil en AgendaGrid
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

    const { container } = render(
      <AgendaGrid
        date={date}
        timezone={timezone}
        axis={axis}
        columns={columns}
        isMobile={true}
      />,
    );

    const mobileColumns = container.querySelectorAll("[data-mobile-column='true']");
    expect(mobileColumns.length).toBe(columns.length);
  });
});
