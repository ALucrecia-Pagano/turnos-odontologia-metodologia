import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createApiClient } from "../../shared/api/client";
import type { AgendaAppointment } from "../agenda/agendaApi";
import { AppointmentDetailDialog } from "./AppointmentDetailDialog";

const APPOINTMENT: AgendaAppointment = {
  id: "00000000-0000-0000-0000-000000000aa1",
  patientId: "00000000-0000-0000-0000-0000000000c1",
  patientName: "Ana Pérez",
  professionalId: "00000000-0000-0000-0000-000000000001",
  professionalName: "Dra. Laura Quiroga",
  chairId: "00000000-0000-0000-0000-0000000000b1",
  chairName: "Sillón 1",
  serviceId: "00000000-0000-0000-0000-0000000000d1",
  serviceName: "Control",
  startAt: "2026-11-16T13:00:00Z",
  endAt: "2026-11-16T13:30:00Z",
  status: "reservado",
};

describe("AppointmentDetailDialog — Detalle e Historial", () => {
  it("3.1 detalle renderiza datos completos en hora local con StatusBadge y botón cerrar", () => {
    let closed = false;
    const client = createApiClient({
      fetchFn: async () => new Response(JSON.stringify([]), { status: 200 }),
    });

    render(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {
          closed = true;
        }}
        appointment={APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    expect(screen.getByText("Ana Pérez")).toBeInTheDocument();
    expect(screen.getByText("Dra. Laura Quiroga")).toBeInTheDocument();
    expect(screen.getByText("Sillón 1")).toBeInTheDocument();
    expect(screen.getByText("Control")).toBeInTheDocument();
    expect(screen.getByText("10:00–10:30")).toBeInTheDocument();
    expect(screen.getByText("Reservado")).toBeInTheDocument();

    const closeBtn = screen.getByRole("button", { name: "Cerrar" });
    fireEvent.click(closeBtn);
    expect(closed).toBe(true);
  });

  it("3.2 historial renderiza transiciones cronológicas con autor, estados y hora local", async () => {
    const historyPayload = [
      {
        from: null,
        to: "reservado",
        changedBy: "00000000-0000-0000-0000-000000000002",
        changedByName: "Recepción",
        changedAt: "2026-11-13T10:00:00Z",
        reschedule: null,
      },
      {
        from: "reservado",
        to: "confirmado",
        changedBy: "00000000-0000-0000-0000-000000000001",
        changedByName: "Dra. Laura Quiroga",
        changedAt: "2026-11-13T11:00:00Z",
        reschedule: null,
      },
    ];

    const client = createApiClient({
      fetchFn: async (input) => {
        const url = String(input);
        if (url.includes("/history")) {
          return new Response(JSON.stringify(historyPayload), { status: 200 });
        }
        return new Response(JSON.stringify([]), { status: 200 });
      },
    });

    render(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {}}
        appointment={APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    await waitFor(() => {
      expect(screen.queryByText("Recepción")).not.toBeNull();
      expect(screen.queryByText("Dra. Laura Quiroga", { selector: "li *" })).not.toBeNull();
    });

    expect(screen.getByText(/07:00/)).toBeInTheDocument();
    expect(screen.getByText(/08:00/)).toBeInTheDocument();
  });

  it("3.3 historial renderiza desglose de reprogramación con horario previo y nuevo en hora local", async () => {
    const historyWithReschedule = [
      {
        from: "reservado",
        to: "reservado",
        changedBy: "00000000-0000-0000-0000-000000000002",
        changedByName: "Recepción",
        changedAt: "2026-11-13T11:00:00Z",
        reschedule: {
          previousStartAt: "2026-11-16T13:00:00Z",
          previousEndAt: "2026-11-16T13:30:00Z",
          newStartAt: "2026-11-17T14:00:00Z",
          newEndAt: "2026-11-17T14:45:00Z",
          previousProfessionalId: "prof-1",
          newProfessionalId: "prof-1",
          previousChairId: "chair-1",
          newChairId: "chair-1",
        },
      },
    ];

    const client = createApiClient({
      fetchFn: async () => new Response(JSON.stringify(historyWithReschedule), { status: 200 }),
    });

    render(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {}}
        appointment={APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    const historySection = screen.getByRole("region", { name: "Historial de cambios" });
    await waitFor(() => {
      expect(within(historySection).queryByText(/10:00–10:30/)).not.toBeNull();
      expect(within(historySection).queryByText(/11:00–11:45/)).not.toBeNull();
    });
  });

  it("3.4 historial maneja error de carga mostrando aviso accesible sin romper el detalle", async () => {
    const client = createApiClient({
      fetchFn: async () =>
        new Response(
          JSON.stringify({ code: "INTERNAL_ERROR", message: "Error al cargar historial" }),
          { status: 500 },
        ),
    });

    render(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {}}
        appointment={APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    expect(screen.getByText("Ana Pérez")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText("No se pudo cargar el historial de cambios.")).not.toBeNull();
    });
  });
});
