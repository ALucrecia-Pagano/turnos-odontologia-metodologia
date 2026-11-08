import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { APPOINTMENT_STATUS_TOKENS } from "../../shared/styles/appointmentStatusTokens";
import type { AgendaResponse, Professional } from "./agendaApi";
import { AgendaView } from "./AgendaView";

const PROFESSIONALS_ORDER_A: readonly Professional[] = [
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
    fullName: "Dra. Paula Benítez",
    licenseNumber: "MP-1003",
    active: false,
  },
];

const PROFESSIONALS_ORDER_B: readonly Professional[] = [
  PROFESSIONALS_ORDER_A[2]!,
  PROFESSIONALS_ORDER_A[0]!,
  PROFESSIONALS_ORDER_A[1]!,
];

const MONDAY_AGENDA: AgendaResponse = {
  from: "2026-11-16",
  to: "2026-11-16",
  timezone: "America/Argentina/Buenos_Aires",
  appointments: [
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
      status: "reservado",
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
  ],
  workingHours: [
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
  ],
  blocks: [
    {
      id: "00000000-0000-0000-0000-000000000bb1",
      professionalId: "00000000-0000-0000-0000-000000000001",
      startAt: "2026-11-16T15:00:00Z",
      endAt: "2026-11-16T16:00:00Z",
      reason: "Congreso",
    },
  ],
};

describe("AgendaView", () => {
  it("dibuja el eje 08:00–20:00 y las tres columnas en orden alfabético estable con inactivo y columna vacía", () => {
    const viewA = render(
      <AgendaView
        date="2026-11-16"
        timezone={MONDAY_AGENDA.timezone}
        agenda={MONDAY_AGENDA}
        professionals={PROFESSIONALS_ORDER_A}
      />,
    );

    const hourElements = screen.queryAllByTestId("agenda-axis-hour");
    expect(hourElements.map((el) => el.textContent)).toEqual([
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

    const headersA = screen.queryAllByTestId("agenda-column-header").map((el) => el.textContent);
    expect(headersA).toEqual([
      "Dr. Martín Sosa",
      "Dra. Laura Quiroga",
      "Dra. Paula Benítez (inactivo)",
    ]);

    const benitezCol = screen.queryByTestId(
      "agenda-column-00000000-0000-0000-0000-000000000003",
    );
    expect(benitezCol).not.toBeNull();
    expect(within(benitezCol!).queryByText("Sin turnos")).toBeInTheDocument();

    viewA.unmount();

    render(
      <AgendaView
        date="2026-11-16"
        timezone={MONDAY_AGENDA.timezone}
        agenda={MONDAY_AGENDA}
        professionals={PROFESSIONALS_ORDER_B}
      />,
    );
    const headersB = screen.queryAllByTestId("agenda-column-header").map((el) => el.textContent);
    expect(headersB).toEqual(headersA);
  });

  it("posiciona el turno de Quiroga 10:00–10:30 a 120 minutos del inicio con 30 minutos de alto y muestra la fecha local", () => {
    render(
      <AgendaView
        date="2026-11-16"
        timezone={MONDAY_AGENDA.timezone}
        agenda={MONDAY_AGENDA}
        professionals={PROFESSIONALS_ORDER_A}
      />,
    );

    expect(screen.queryByText("lunes 16 de noviembre de 2026")).toBeInTheDocument();

    const quirogaCard = screen.queryByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa1",
    );
    expect(quirogaCard).not.toBeNull();
    expect(quirogaCard).toHaveAttribute("data-offset-minutes", "120");
    expect(quirogaCard).toHaveAttribute("data-duration-minutes", "30");
    expect(quirogaCard).toHaveAttribute("data-lane", "0");
    expect(quirogaCard).toHaveAttribute("data-lane-count", "1");
    expect(quirogaCard).toHaveTextContent("10:00 · Ana Pérez");
    expect(quirogaCard).toHaveTextContent("Reservado");
  });

  it("reparte un turno cancelado y uno activo superpuestos en dos carriles y da alto mínimo al turno de cinco minutos", () => {
    const agendaWithOverlapAndShort: AgendaResponse = {
      ...MONDAY_AGENDA,
      appointments: [
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
          id: "00000000-0000-0000-0000-000000000aa3",
          patientId: "00000000-0000-0000-0000-0000000000c1",
          patientName: "Ana Pérez",
          professionalId: "00000000-0000-0000-0000-000000000002",
          professionalName: "Dr. Martín Sosa",
          chairId: "00000000-0000-0000-0000-0000000000b2",
          chairName: "Sillón 2",
          serviceId: "00000000-0000-0000-0000-0000000000d4",
          serviceName: "Control",
          startAt: "2026-11-16T12:00:00Z",
          endAt: "2026-11-16T12:30:00Z",
          status: "reservado",
        },
        {
          id: "00000000-0000-0000-0000-000000000aa4",
          patientId: "00000000-0000-0000-0000-0000000000c1",
          patientName: "Ana Pérez",
          professionalId: "00000000-0000-0000-0000-000000000003",
          professionalName: "Dra. Paula Benítez",
          chairId: "00000000-0000-0000-0000-0000000000b1",
          chairName: "Sillón 1",
          serviceId: "00000000-0000-0000-0000-0000000000d4",
          serviceName: "Control",
          startAt: "2026-11-16T12:00:00Z",
          endAt: "2026-11-16T12:05:00Z",
          status: "reservado",
        },
      ],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone={MONDAY_AGENDA.timezone}
        agenda={agendaWithOverlapAndShort}
        professionals={PROFESSIONALS_ORDER_A}
      />,
    );

    const cancelledCard = screen.queryByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa2",
    );
    const activeCard = screen.queryByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa3",
    );
    expect(cancelledCard).not.toBeNull();
    expect(activeCard).not.toBeNull();
    expect(cancelledCard).toHaveAttribute("data-lane", "0");
    expect(cancelledCard).toHaveAttribute("data-lane-count", "2");
    expect(activeCard).toHaveAttribute("data-lane", "1");
    expect(activeCard).toHaveAttribute("data-lane-count", "2");

    const shortCard = screen.queryByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa4",
    );
    expect(shortCard).not.toBeNull();
    expect(shortCard).toHaveAttribute("data-duration-minutes", "5");
    expect(shortCard).toHaveAttribute("data-effective-minutes", "15");
    expect(shortCard?.getAttribute("aria-label")).toContain("09:00–09:05");
    expect(shortCard).toHaveTextContent("09:00 · Ana Pérez");
  });

  it("dibuja las bandas de horario de Quiroga, el bloqueo Congreso de 12:00 a 13:00 y conserva visible y atenuado el turno cancelado", () => {
    const agendaWithCancelled: AgendaResponse = {
      ...MONDAY_AGENDA,
      appointments: [
        {
          ...MONDAY_AGENDA.appointments[0]!,
          status: "cancelado",
        },
        MONDAY_AGENDA.appointments[1]!,
      ],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone={MONDAY_AGENDA.timezone}
        agenda={agendaWithCancelled}
        professionals={PROFESSIONALS_ORDER_A}
      />,
    );

    const quirogaCol = screen.queryByTestId(
      "agenda-column-00000000-0000-0000-0000-000000000001",
    );
    expect(quirogaCol).not.toBeNull();

    const morningWh = within(quirogaCol!).queryByLabelText(
      "Horario de atención: 09:00 a 13:00",
    );
    expect(morningWh).not.toBeNull();
    expect(morningWh).toHaveAttribute("data-offset-minutes", "60");
    expect(morningWh).toHaveAttribute("data-duration-minutes", "240");

    const afternoonWh = within(quirogaCol!).queryByLabelText(
      "Horario de atención: 15:00 a 19:00",
    );
    expect(afternoonWh).not.toBeNull();
    expect(afternoonWh).toHaveAttribute("data-offset-minutes", "420");
    expect(afternoonWh).toHaveAttribute("data-duration-minutes", "240");

    const blockEl = within(quirogaCol!).queryByLabelText(
      "Bloqueo: Congreso, de 12:00 a 13:00",
    );
    expect(blockEl).not.toBeNull();
    expect(blockEl).toHaveAttribute("data-offset-minutes", "240");
    expect(blockEl).toHaveAttribute("data-duration-minutes", "60");
    expect(blockEl).toHaveTextContent("Congreso");

    const cancelledCard = screen.queryByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa2",
    );
    expect(cancelledCard).not.toBeNull();
    expect(cancelledCard).toHaveAttribute("data-status", "cancelado");
    expect(cancelledCard?.className).toContain("appointmentCancelled");
    expect(cancelledCard).toHaveTextContent("Cancelado");
  });

  it("muestra Reservado y Cancelado con StatusBadge AA y expone el nombre accesible completo en cada tarjeta", () => {
    const agendaWithBothStatuses: AgendaResponse = {
      ...MONDAY_AGENDA,
      appointments: [
        {
          ...MONDAY_AGENDA.appointments[0]!,
          status: "cancelado",
        },
        MONDAY_AGENDA.appointments[1]!,
      ],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone={MONDAY_AGENDA.timezone}
        agenda={agendaWithBothStatuses}
        professionals={PROFESSIONALS_ORDER_A}
      />,
    );

    const quirogaCard = screen.queryByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa1",
    );
    const sosaCard = screen.queryByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa2",
    );
    expect(quirogaCard).not.toBeNull();
    expect(sosaCard).not.toBeNull();

    const reservadoBadge = within(quirogaCard!).queryByText("Reservado");
    const canceladoBadge = within(sosaCard!).queryByText("Cancelado");
    expect(reservadoBadge).not.toBeNull();
    expect(canceladoBadge).not.toBeNull();
    expect(reservadoBadge).toHaveAttribute("data-status", "reservado");
    expect(canceladoBadge).toHaveAttribute("data-status", "cancelado");
    expect(reservadoBadge).toHaveStyle({
      color: APPOINTMENT_STATUS_TOKENS.reservado.text,
      backgroundColor: APPOINTMENT_STATUS_TOKENS.reservado.background,
      borderColor: APPOINTMENT_STATUS_TOKENS.reservado.border,
    });
    expect(canceladoBadge).toHaveStyle({
      color: APPOINTMENT_STATUS_TOKENS.cancelado.text,
      backgroundColor: APPOINTMENT_STATUS_TOKENS.cancelado.background,
      borderColor: APPOINTMENT_STATUS_TOKENS.cancelado.border,
    });

    const accessibleName = quirogaCard?.getAttribute("aria-label") ?? "";
    expect(accessibleName).toContain("10:00–10:30");
    expect(accessibleName).toContain("Ana Pérez");
    expect(accessibleName).toContain("Dra. Laura Quiroga");
    expect(accessibleName).toContain("Sillón 1");
    expect(accessibleName).toContain("Control");
    expect(accessibleName).toContain("Reservado");
  });

  it("en un día sin turnos muestra SOLO el EmptyState sin grilla en modo grilla ni tabla en modo lista", () => {
    const emptyDayAgenda: AgendaResponse = {
      ...MONDAY_AGENDA,
      appointments: [],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone={MONDAY_AGENDA.timezone}
        agenda={emptyDayAgenda}
        professionals={PROFESSIONALS_ORDER_A}
      />,
    );

    expect(
      screen.queryByRole("heading", { name: "No hay turnos para este día" }),
    ).not.toBeNull();
    expect(screen.queryByTestId("agenda-grid-scroll")).not.toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();

    const toggleBtn = screen.queryByRole("button", { name: "Ver como lista" });
    expect(toggleBtn).not.toBeNull();
    fireEvent.click(toggleBtn!);

    expect(
      screen.queryByRole("heading", { name: "No hay turnos para este día" }),
    ).not.toBeNull();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.queryByTestId("agenda-grid-scroll")).not.toBeInTheDocument();
  });

  it("la tarjeta de 30 minutos muestra el nombre del paciente en su texto visible y el aria-label completo", () => {
    render(
      <AgendaView
        date="2026-11-16"
        timezone={MONDAY_AGENDA.timezone}
        agenda={MONDAY_AGENDA}
        professionals={PROFESSIONALS_ORDER_A}
      />,
    );

    const quirogaCard = screen.queryByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa1",
    );
    expect(quirogaCard).not.toBeNull();
    expect(quirogaCard).toHaveTextContent("10:00 · Ana Pérez");
    expect(quirogaCard?.textContent).not.toContain("Control");
    expect(quirogaCard).toHaveAttribute("title", "Control");
    const label = quirogaCard?.getAttribute("aria-label") ?? "";
    expect(label).toContain("10:00–10:30");
    expect(label).toContain("Ana Pérez");
    expect(label).toContain("Control");
    expect(label).toContain("Dra. Laura Quiroga");
    expect(label).toContain("Sillón 1");
    expect(label).toContain("Reservado");
  });

  it("la tarjeta de 60 minutos muestra la prestación en su texto visible en una línea separada", () => {
    const agendaWith60Min: AgendaResponse = {
      ...MONDAY_AGENDA,
      appointments: [
        {
          id: "00000000-0000-0000-0000-000000000060",
          patientId: "00000000-0000-0000-0000-0000000000c1",
          patientName: "Carlos Gómez",
          professionalId: "00000000-0000-0000-0000-000000000001",
          professionalName: "Dra. Laura Quiroga",
          chairId: "00000000-0000-0000-0000-0000000000b1",
          chairName: "Sillón 1",
          serviceId: "00000000-0000-0000-0000-0000000000d4",
          serviceName: "Tratamiento de conducto",
          startAt: "2026-11-16T14:00:00Z",
          endAt: "2026-11-16T15:00:00Z",
          status: "confirmado",
        },
      ],
    };

    render(
      <AgendaView
        date="2026-11-16"
        timezone={MONDAY_AGENDA.timezone}
        agenda={agendaWith60Min}
        professionals={PROFESSIONALS_ORDER_A}
      />,
    );

    const card = screen.queryByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000060",
    );
    expect(card).not.toBeNull();
    expect(card).toHaveTextContent("11:00–12:00");
    expect(card).toHaveTextContent("Carlos Gómez");
    expect(card).toHaveTextContent("Tratamiento de conducto");
    expect(card).toHaveTextContent("Confirmado");
  });

  it("anuncia la cantidad de turnos con aria-live y alterna a la vista en lista con Ver como lista", () => {
    render(
      <AgendaView
        date="2026-11-16"
        timezone={MONDAY_AGENDA.timezone}
        agenda={MONDAY_AGENDA}
        professionals={PROFESSIONALS_ORDER_A}
      />,
    );

    const liveRegion = screen.queryByTestId("agenda-live-count");
    expect(liveRegion).not.toBeNull();
    expect(liveRegion).toHaveAttribute("aria-live", "polite");
    expect(liveRegion).toHaveTextContent("Turnos del lunes 16 de noviembre de 2026: 2");

    const toggleBtn = screen.queryByRole("button", { name: "Ver como lista" });
    expect(toggleBtn).not.toBeNull();
    fireEvent.click(toggleBtn!);

    const table = screen.queryByRole("table", {
      name: "Turnos del lunes 16 de noviembre de 2026",
    });
    expect(table).not.toBeNull();
    const headers = within(table!).queryAllByRole("columnheader").map((th) => th.textContent);
    expect(headers).toEqual([
      "Hora",
      "Paciente",
      "Profesional",
      "Sillón",
      "Prestación",
      "Estado",
    ]);

    const rows = within(table!).queryAllByRole("row").slice(1);
    expect(rows).toHaveLength(2);
    const quirogaRowCells = within(rows[1]!).queryAllByRole("cell").map((td) => td.textContent);
    expect(quirogaRowCells).toEqual([
      "10:00–10:30",
      "Ana Pérez",
      "Dra. Laura Quiroga",
      "Sillón 1",
      "Control",
      "Reservado",
    ]);
  });
});
