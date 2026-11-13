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
  status: "confirmado",
};

describe("AppointmentDetailDialog — Cancelación", () => {
  it("5.1 cancelar turno muestra subvista de confirmación in-dialog", () => {
    const client = createApiClient({
      fetchFn: async () => new Response(JSON.stringify([]), { status: 200 }),
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

    const cancelBtn = screen.getByRole("button", { name: "Cancelar turno" });
    fireEvent.click(cancelBtn);

    expect(
      screen.queryByText("¿Confirma que desea cancelar el turno de Ana Pérez?"),
    ).not.toBeNull();
    expect(screen.getByRole("button", { name: "Confirmar cancelación" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Volver al detalle" })).toBeInTheDocument();
  });

  it("5.2 volver al detalle o Escape restaura la vista sin enviar petición", () => {
    let requestsCount = 0;
    const client = createApiClient({
      fetchFn: async () => {
        requestsCount++;
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

    fireEvent.click(screen.getByRole("button", { name: "Cancelar turno" }));
    expect(
      screen.queryByText("¿Confirma que desea cancelar el turno de Ana Pérez?"),
    ).not.toBeNull();

    const backBtn = screen.getByRole("button", { name: "Volver al detalle" });
    fireEvent.click(backBtn);

    expect(
      screen.queryByText("¿Confirma que desea cancelar el turno de Ana Pérez?"),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar turno" })).toBeInTheDocument();
    expect(requestsCount).toBe(1); // Solo GET /history
  });

  it("5.3 confirmar cancelación envía POST sin cuerpo y cierra modal", async () => {
    let closed = false;
    let cancelled = false;
    let requestMethod = "";
    let requestBody: unknown = undefined;

    const client = createApiClient({
      fetchFn: async (input, init) => {
        const url = String(input);
        if (url.includes("/cancel")) {
          requestMethod = init?.method ?? "";
          requestBody = init?.body;
          return new Response(
            JSON.stringify({ ...BASE_APPOINTMENT, status: "cancelado" }),
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
        onCancelled={() => {
          cancelled = true;
        }}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Cancelar turno" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelación" }));

    await waitFor(() => {
      expect(requestMethod).toBe("POST");
      expect(requestBody).toBeUndefined();
      expect(cancelled).toBe(true);
      expect(closed).toBe(true);
    });
  });

  it("5.4 error 422 INVALID_TRANSITION en cancelación muestra alerta con foco", async () => {
    const errorResponse = {
      code: "BUSINESS_RULE_VIOLATION",
      message: "Violación de regla de negocio",
      violations: [
        {
          code: "INVALID_TRANSITION",
          message: "No se puede cancelar un turno en estado atendido.",
        },
      ],
    };

    const client = createApiClient({
      fetchFn: async (input, init) => {
        const url = String(input);
        if (url.includes("/cancel") && init?.method === "POST") {
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

    fireEvent.click(screen.getByRole("button", { name: "Cancelar turno" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelación" }));

    await waitFor(() => {
      const alert = screen.queryByRole("alert");
      expect(alert).not.toBeNull();
      expect(alert).toHaveFocus();
      expect(screen.queryByText("INVALID_TRANSITION")).not.toBeNull();
      expect(
        screen.queryByText("No se puede cancelar un turno en estado atendido."),
      ).not.toBeNull();
    });
  });

  it("5.5 Escape sobre el diálogo con confirmación abierta vuelve a la vista de detalle", () => {
    let closed = false;
    let postSent = false;
    const client = createApiClient({
      fetchFn: async (_input, init) => {
        if (init?.method === "POST") {
          postSent = true;
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
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Cancelar turno" }));
    expect(
      screen.queryByText("¿Confirma que desea cancelar el turno de Ana Pérez?"),
    ).not.toBeNull();

    const dialog = screen.queryByRole("dialog");
    expect(dialog).not.toBeNull();
    fireEvent.keyDown(dialog!, { key: "Escape" });

    expect(closed).toBe(false);
    expect(
      screen.queryByText("¿Confirma que desea cancelar el turno de Ana Pérez?"),
    ).toBeNull();
    expect(screen.queryByRole("button", { name: "Cancelar turno" })).not.toBeNull();
    expect(postSent).toBe(false);
  });

  it("5.6 al volver de la confirmación con Escape el foco queda en el botón Cancelar turno", () => {
    const client = createApiClient({
      fetchFn: async () => new Response(JSON.stringify([]), { status: 200 }),
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

    fireEvent.click(screen.getByRole("button", { name: "Cancelar turno" }));
    const dialog = screen.queryByRole("dialog");
    expect(dialog).not.toBeNull();
    fireEvent.keyDown(dialog!, { key: "Escape" });

    const cancelBtn = screen.queryByRole("button", { name: "Cancelar turno" });
    expect(cancelBtn).not.toBeNull();
    expect(cancelBtn).toHaveFocus();
  });

  it("5.7 al entrar a la confirmación se limpia el alert de una acción anterior", async () => {
    const errorResponse = {
      code: "BUSINESS_RULE_VIOLATION",
      message: "Violación de regla de negocio",
      violations: [
        {
          code: "STATUS_CHANGE_TOO_EARLY",
          message: "No se puede marcar atendido un turno que todavía no empezó.",
        },
      ],
    };
    const client = createApiClient({
      fetchFn: async (input, init) => {
        if (String(input).includes("/status") && init?.method === "POST") {
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

    fireEvent.click(screen.getByRole("button", { name: "Marcar atendido" }));
    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeNull();
    });

    fireEvent.click(screen.getByRole("button", { name: "Cancelar turno" }));

    expect(
      screen.queryByText("¿Confirma que desea cancelar el turno de Ana Pérez?"),
    ).not.toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
