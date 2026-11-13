import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createApiClient } from "../../shared/api/client";
import type { AgendaAppointment } from "../agenda/agendaApi";
import { AppointmentDetailDialog } from "./AppointmentDetailDialog";

const BASE_APPOINTMENT: AgendaAppointment = {
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

describe("AppointmentDetailDialog — Cambios de estado", () => {
  it("4.1 botones contextuales según estado y rol", () => {
    const client = createApiClient({
      fetchFn: async () => new Response(JSON.stringify([]), { status: 200 }),
    });

    const { rerender } = render(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {}}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    // En reservado
    expect(screen.getByRole("button", { name: "Confirmar turno" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Marcar atendido" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Marcar ausente" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reprogramar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar turno" })).toBeInTheDocument();

    // En confirmado
    rerender(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {}}
        appointment={{ ...BASE_APPOINTMENT, status: "confirmado" }}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );
    expect(screen.queryByRole("button", { name: "Confirmar turno" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Marcar atendido" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Marcar ausente" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reprogramar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar turno" })).toBeInTheDocument();

    // En atendido (terminal)
    rerender(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {}}
        appointment={{ ...BASE_APPOINTMENT, status: "atendido" }}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );
    expect(screen.queryByRole("button", { name: "Confirmar turno" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Marcar atendido" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Marcar ausente" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reprogramar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cancelar turno" })).not.toBeInTheDocument();
    expect(screen.queryByText("Este turno ya no admite cambios.")).not.toBeNull();
  });

  it("4.2 confirmar turno envía toStatus confirmado y cierra modal con éxito", async () => {
    let closed = false;
    let requestPayload: unknown = null;
    let statusChangedTo: string | null = null;

    const client = createApiClient({
      fetchFn: async (input, init) => {
        const url = String(input);
        if (url.includes("/status") && init?.method === "POST") {
          requestPayload = JSON.parse(String(init.body));
          return new Response(
            JSON.stringify({ ...BASE_APPOINTMENT, status: "confirmado" }),
            { status: 200 },
          );
        }
        return new Response(JSON.stringify([]), { status: 200 });
      },
    });

    render(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {
          closed = true;
        }}
        onStatusChanged={(s) => {
          statusChangedTo = s;
        }}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    const btn = screen.getByRole("button", { name: "Confirmar turno" });
    fireEvent.click(btn);

    await waitFor(() => {
      expect(requestPayload).toEqual({ toStatus: "confirmado" });
      expect(statusChangedTo).toBe("confirmado");
      expect(closed).toBe(true);
    });
  });

  it("4.3 marcar atendido envía toStatus atendido y cierra modal con éxito", async () => {
    let closed = false;
    let requestPayload: unknown = null;
    let statusChangedTo: string | null = null;

    const client = createApiClient({
      fetchFn: async (input, init) => {
        const url = String(input);
        if (url.includes("/status") && init?.method === "POST") {
          requestPayload = JSON.parse(String(init.body));
          return new Response(
            JSON.stringify({ ...BASE_APPOINTMENT, status: "atendido" }),
            { status: 200 },
          );
        }
        return new Response(JSON.stringify([]), { status: 200 });
      },
    });

    render(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {
          closed = true;
        }}
        onStatusChanged={(s) => {
          statusChangedTo = s;
        }}
        appointment={{ ...BASE_APPOINTMENT, status: "confirmado" }}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    const btn = screen.getByRole("button", { name: "Marcar atendido" });
    fireEvent.click(btn);

    await waitFor(() => {
      expect(requestPayload).toEqual({ toStatus: "atendido" });
      expect(statusChangedTo).toBe("atendido");
      expect(closed).toBe(true);
    });
  });

  it("4.4 marcar ausente envía toStatus ausente y cierra modal con éxito", async () => {
    let closed = false;
    let requestPayload: unknown = null;
    let statusChangedTo: string | null = null;

    const client = createApiClient({
      fetchFn: async (input, init) => {
        const url = String(input);
        if (url.includes("/status") && init?.method === "POST") {
          requestPayload = JSON.parse(String(init.body));
          return new Response(
            JSON.stringify({ ...BASE_APPOINTMENT, status: "ausente" }),
            { status: 200 },
          );
        }
        return new Response(JSON.stringify([]), { status: 200 });
      },
    });

    render(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {
          closed = true;
        }}
        onStatusChanged={(s) => {
          statusChangedTo = s;
        }}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    const btn = screen.getByRole("button", { name: "Marcar ausente" });
    fireEvent.click(btn);

    await waitFor(() => {
      expect(requestPayload).toEqual({ toStatus: "ausente" });
      expect(statusChangedTo).toBe("ausente");
      expect(closed).toBe(true);
    });
  });

  it("4.5 rechazo 422 STATUS_CHANGE_TOO_EARLY expone alerta con código, mensaje y foco", async () => {
    const errorResponse = {
      code: "BUSINESS_RULE_VIOLATION",
      message: "Violación de regla de negocio",
      violations: [
        {
          code: "STATUS_CHANGE_TOO_EARLY",
          message: "No se puede marcar como atendido un turno que aún no ha comenzado.",
        },
      ],
    };

    const client = createApiClient({
      fetchFn: async (input, init) => {
        const url = String(input);
        if (url.includes("/status") && init?.method === "POST") {
          return new Response(JSON.stringify(errorResponse), {
            status: 422,
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response(JSON.stringify([]), { status: 200 });
      },
    });

    render(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {}}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    const btn = screen.getByRole("button", { name: "Marcar atendido" });
    fireEvent.click(btn);

    await waitFor(() => {
      const alert = screen.queryByRole("alert");
      expect(alert).not.toBeNull();
      expect(alert).toHaveFocus();
      expect(screen.queryByText("STATUS_CHANGE_TOO_EARLY")).not.toBeNull();
      expect(
        screen.queryByText("No se puede marcar como atendido un turno que aún no ha comenzado."),
      ).not.toBeNull();
    });
  });

  it("4.6 rechazo 422 INVALID_TRANSITION expone mensaje en alerta con foco", async () => {
    const errorResponse = {
      code: "BUSINESS_RULE_VIOLATION",
      message: "Violación de regla de negocio",
      violations: [
        {
          code: "INVALID_TRANSITION",
          message: "Transición de estado inválida.",
        },
      ],
    };

    const client = createApiClient({
      fetchFn: async (input, init) => {
        const url = String(input);
        if (url.includes("/status") && init?.method === "POST") {
          return new Response(JSON.stringify(errorResponse), {
            status: 422,
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response(JSON.stringify([]), { status: 200 });
      },
    });

    render(
      <AppointmentDetailDialog
        open={true}
        onClose={() => {}}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    const btn = screen.getByRole("button", { name: "Confirmar turno" });
    fireEvent.click(btn);

    await waitFor(() => {
      const alert = screen.getByRole("alert");
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveFocus();
      expect(screen.getByText("INVALID_TRANSITION")).toBeInTheDocument();
      expect(screen.getByText("Transición de estado inválida.")).toBeInTheDocument();
    });
  });
});
