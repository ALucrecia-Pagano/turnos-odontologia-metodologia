import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createApiClient } from "../../shared/api/client";
import type { AgendaAppointment, Chair, Professional } from "../agenda/agendaApi";
import { AppointmentRescheduleDialog } from "./AppointmentRescheduleDialog";

const PROFESSIONALS: readonly Professional[] = [
  {
    id: "00000000-0000-0000-0000-000000000001",
    fullName: "Dra. Laura Quiroga",
    licenseNumber: "MP-1001",
    active: true,
  },
  {
    id: "00000000-0000-0000-0000-000000000002",
    fullName: "Dr. Carlos Rossi",
    licenseNumber: "MP-1002",
    active: true,
  },
];

const CHAIRS: readonly Chair[] = [
  {
    id: "00000000-0000-0000-0000-0000000000b1",
    name: "Sillón 1",
    active: true,
  },
  {
    id: "00000000-0000-0000-0000-0000000000b2",
    name: "Sillón 2",
    active: true,
  },
];

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

describe("AppointmentRescheduleDialog — Reprogramación", () => {
  it("6.1 apertura con paciente y prestación en solo lectura y campos prellenados", () => {
    const client = createApiClient({
      fetchFn: async () => new Response(JSON.stringify([]), { status: 200 }),
    });

    render(
      <AppointmentRescheduleDialog
        open={true}
        onClose={() => {}}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
      />,
    );

    // Paciente y prestación en solo lectura (sin inputs)
    expect(screen.getByText("Ana Pérez")).toBeInTheDocument();
    expect(screen.getByText("Control")).toBeInTheDocument();
    expect(screen.queryByLabelText("Paciente")).not.toBeInTheDocument();

    // Campos prellenados
    const dateInput = screen.getByLabelText("Fecha") as HTMLInputElement;
    const timeInput = screen.getByLabelText("Hora") as HTMLInputElement;
    const profSelect = screen.getByLabelText("Profesional") as HTMLSelectElement;
    const chairSelect = screen.getByLabelText("Sillón") as HTMLSelectElement;
    const durationInput = screen.getByLabelText(/Duración/i) as HTMLInputElement;

    expect(dateInput.value).toBe("2026-11-16");
    expect(timeInput.value).toBe("10:00");
    expect(profSelect.value).toBe("00000000-0000-0000-0000-000000000001");
    expect(chairSelect.value).toBe("00000000-0000-0000-0000-0000000000b1");
    expect(durationInput.value).toBe("30");
  });

  it("6.2 reprogramación exitosa envía POST con offset exacto y cierra modal", async () => {
    let closed = false;
    let successInfo: unknown = null;
    let requestPayload: unknown = null;

    const client = createApiClient({
      fetchFn: async (input, init) => {
        const url = String(input);
        if (url.includes("/reschedule") && init?.method === "POST") {
          requestPayload = JSON.parse(String(init.body));
          return new Response(
            JSON.stringify({
              ...BASE_APPOINTMENT,
              startAt: "2026-11-17T14:00:00Z",
              endAt: "2026-11-17T14:45:00Z",
              status: "reservado",
            }),
            { status: 200 },
          );
        }
        return new Response(JSON.stringify([]), { status: 200 });
      },
    });

    render(
      <AppointmentRescheduleDialog
        open={true}
        onClose={() => {
          closed = true;
        }}
        onSuccess={(info) => {
          successInfo = info;
        }}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
      />,
    );

    fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2026-11-17" } });
    fireEvent.change(screen.getByLabelText("Hora"), { target: { value: "11:00" } });
    fireEvent.change(screen.getByLabelText(/Duración/i), { target: { value: "45" } });

    fireEvent.click(screen.getByRole("button", { name: "Guardar reprogramación" }));

    await waitFor(() => {
      expect(requestPayload).toEqual({
        startAt: "2026-11-17T11:00:00-03:00",
        professionalId: "00000000-0000-0000-0000-000000000001",
        chairId: "00000000-0000-0000-0000-0000000000b1",
        durationMin: 45,
      });
      expect(closed).toBe(true);
      expect(successInfo).toBeTruthy();
    });
  });

  it("6.3 rechazo 409 con violaciones múltiples de solapamiento muestra badges y alert con foco", async () => {
    const errorResponse = {
      code: "BUSINESS_RULE_VIOLATION",
      message: "Conflicto de solapamiento",
      violations: [
        {
          code: "PROFESSIONAL_OVERLAP",
          message: "El profesional ya tiene un turno asignado en ese horario.",
        },
        {
          code: "CHAIR_OVERLAP",
          message: "El sillón ya está ocupado en ese horario.",
        },
      ],
    };

    const client = createApiClient({
      fetchFn: async (input, init) => {
        const url = String(input);
        if (url.includes("/reschedule") && init?.method === "POST") {
          return new Response(JSON.stringify(errorResponse), {
            status: 409,
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response(JSON.stringify([]), { status: 200 });
      },
    });

    render(
      <AppointmentRescheduleDialog
        open={true}
        onClose={() => {}}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Guardar reprogramación" }));

    await waitFor(() => {
      const alert = screen.queryByRole("alert");
      expect(alert).not.toBeNull();
      expect(alert).toHaveFocus();
      expect(screen.queryByText("PROFESSIONAL_OVERLAP")).not.toBeNull();
      expect(screen.queryByText("CHAIR_OVERLAP")).not.toBeNull();
      expect(
        screen.queryByText("El profesional ya tiene un turno asignado en ese horario."),
      ).not.toBeNull();
    });
  });

  it("6.4 rechazo 422 IN_THE_PAST expone mensaje del dominio en alert con foco", async () => {
    const errorResponse = {
      code: "BUSINESS_RULE_VIOLATION",
      message: "Violación de regla de negocio",
      violations: [
        {
          code: "IN_THE_PAST",
          message: "No se puede reprogramar un turno a una fecha u hora en el pasado.",
        },
      ],
    };

    const client = createApiClient({
      fetchFn: async (input, init) => {
        const url = String(input);
        if (url.includes("/reschedule") && init?.method === "POST") {
          return new Response(JSON.stringify(errorResponse), {
            status: 422,
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response(JSON.stringify([]), { status: 200 });
      },
    });

    render(
      <AppointmentRescheduleDialog
        open={true}
        onClose={() => {}}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Guardar reprogramación" }));

    await waitFor(() => {
      const alert = screen.queryByRole("alert");
      expect(alert).not.toBeNull();
      expect(alert).toHaveFocus();
      expect(screen.queryByText("IN_THE_PAST")).not.toBeNull();
      expect(
        screen.queryByText("No se puede reprogramar un turno a una fecha u hora en el pasado."),
      ).not.toBeNull();
    });
  });

  it("6.5 error 400 marca campos con aria-invalid y mensaje inline", async () => {
    const errorResponse = {
      code: "VALIDATION_ERROR",
      message: "Error de validación",
      errors: [
        {
          field: "durationMin",
          type: "value_error",
          message: "La duración debe ser múltiplo de 5 minutos.",
        },
      ],
    };

    const client = createApiClient({
      fetchFn: async (input, init) => {
        const url = String(input);
        if (url.includes("/reschedule") && init?.method === "POST") {
          return new Response(JSON.stringify(errorResponse), {
            status: 400,
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response(JSON.stringify([]), { status: 200 });
      },
    });

    render(
      <AppointmentRescheduleDialog
        open={true}
        onClose={() => {}}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Guardar reprogramación" }));

    await waitFor(() => {
      const durationInput = screen.getByLabelText(/Duración/i);
      expect(durationInput).toHaveAttribute("aria-invalid", "true");
      expect(
        screen.getByText("La duración debe ser múltiplo de 5 minutos."),
      ).toBeInTheDocument();
    });
  });

  it("6.6 cancelar reprogramación cierra diálogo y retorna foco", () => {
    let closed = false;
    const trigger = document.createElement("button");
    document.body.appendChild(trigger);
    trigger.focus();

    const client = createApiClient({
      fetchFn: async () => new Response(JSON.stringify([]), { status: 200 }),
    });

    render(
      <AppointmentRescheduleDialog
        open={true}
        onClose={() => {
          closed = true;
        }}
        appointment={BASE_APPOINTMENT}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        returnFocusRef={{ current: trigger }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(closed).toBe(true);

    document.body.removeChild(trigger);
  });
});
