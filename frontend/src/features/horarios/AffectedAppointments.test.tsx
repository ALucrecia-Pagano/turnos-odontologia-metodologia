import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { BlocksSection } from "./BlocksSection";
import { WorkingHoursSection } from "./WorkingHoursSection";

const PROF_ID = "00000000-0000-0000-0000-000000000001";
const BLOCK_ID = "00000000-0000-0000-0000-0000000000b1";

describe("AffectedAppointments", () => {
  it("Turnos futuros fuera del horario al guardar tramos: muestra en role=alert fecha, hora local, paciente, profesional, StatusBadge y aviso de no cancelación", async () => {
    const user = userEvent.setup();
    const fetchFn: FetchFn = async (url, init) => {
      if (url.endsWith(`/professionals/${PROF_ID}/working-hours`) && init?.method === "PUT") {
        return new Response(
          JSON.stringify({
            workingHours: [{ weekday: 1, start: "09:00", end: "12:00" }],
            appointmentsOutsideHours: [
              {
                id: "00000000-0000-0000-0000-0000000000a1",
                patientId: "00000000-0000-0000-0000-0000000000c1",
                patientName: "Lucía Gómez",
                chairId: "00000000-0000-0000-0000-0000000000d1",
                startAt: "2026-05-04T18:00:00Z",
                endAt: "2026-05-04T18:30:00Z",
                status: "confirmado",
              },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not Found", { status: 404 });
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <WorkingHoursSection
        client={client}
        professionalId={PROF_ID}
        professionalName="Dra. Laura Quiroga"
        timezone="America/Argentina/Buenos_Aires"
        initialSlots={[{ weekday: 1, start: "09:00", end: "12:00" }]}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Guardar horario" }));

    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeNull();
    });
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("lun, 04/05/2026");
    expect(alert).toHaveTextContent("15:00 a 15:30");
    expect(alert).toHaveTextContent("Lucía Gómez");
    expect(alert).toHaveTextContent("Dra. Laura Quiroga");
    expect(alert).toHaveTextContent("Confirmado");
    expect(alert).toHaveTextContent(
      "Los turnos no se cancelan automáticamente; deben reprogramarse o cancelarse desde la agenda.",
    );
  });

  it("Turnos solapados al crear un bloqueo: muestra en role=alert la advertencia de turnos solapados con paciente, fecha, hora local y estado", async () => {
    const user = userEvent.setup();
    const fetchFn: FetchFn = async (url, init) => {
      if (url.endsWith(`/professionals/${PROF_ID}/blocks`) && init?.method === "POST") {
        return new Response(
          JSON.stringify({
            block: {
              id: BLOCK_ID,
              professionalId: PROF_ID,
              startAt: "2026-05-06T12:00:00-03:00",
              endAt: "2026-05-06T16:00:00-03:00",
              reason: "Capacitación",
            },
            affectedAppointments: [
              {
                id: "00000000-0000-0000-0000-0000000000a2",
                patientId: "00000000-0000-0000-0000-0000000000c2",
                patientName: "Martín Pereyra",
                chairId: "00000000-0000-0000-0000-0000000000d1",
                startAt: "2026-05-06T17:00:00Z",
                endAt: "2026-05-06T17:30:00Z",
                status: "reservado",
              },
            ],
          }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not Found", { status: 404 });
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <BlocksSection
        client={client}
        professionalId={PROF_ID}
        professionalName="Dra. Laura Quiroga"
        timezone="America/Argentina/Buenos_Aires"
        initialBlocks={[]}
        defaultDate="2026-05-06"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Nuevo bloqueo" }));
    await user.type(screen.getByLabelText("Hora de inicio"), "12:00");
    await user.type(screen.getByLabelText("Hora de fin"), "16:00");
    await user.click(screen.getByRole("button", { name: "Guardar bloqueo" }));

    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeNull();
    });
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Turnos existentes solapados con el bloqueo creado:");
    expect(alert).toHaveTextContent("mié, 06/05/2026");
    expect(alert).toHaveTextContent("14:00 a 14:30");
    expect(alert).toHaveTextContent("Martín Pereyra");
    expect(alert).toHaveTextContent("Dra. Laura Quiroga");
    expect(alert).toHaveTextContent("Reservado");
  });

  it("Fechas en formato local es-AR en turnos afectados, bloqueos y modal de eliminar: formatea 2026-11-17 como mar, 17/11/2026 con la timezone de la API y no muestra ISO", async () => {
    const user = userEvent.setup();
    const fetchFn: FetchFn = async (url, init) => {
      if (url.endsWith(`/professionals/${PROF_ID}/blocks`) && init?.method === "POST") {
        return new Response(
          JSON.stringify({
            block: {
              id: BLOCK_ID,
              professionalId: PROF_ID,
              startAt: "2026-11-17T15:00:00Z",
              endAt: "2026-11-17T19:00:00Z",
              reason: "Jornada clínica",
            },
            affectedAppointments: [
              {
                id: "00000000-0000-0000-0000-0000000000a3",
                patientId: "00000000-0000-0000-0000-0000000000c3",
                patientName: "Elena Vázquez",
                chairId: "00000000-0000-0000-0000-0000000000d1",
                startAt: "2026-11-17T16:00:00Z",
                endAt: "2026-11-17T16:30:00Z",
                status: "confirmado",
              },
            ],
          }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not Found", { status: 404 });
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <BlocksSection
        client={client}
        professionalId={PROF_ID}
        professionalName="Dra. Laura Quiroga"
        timezone="America/Argentina/Buenos_Aires"
        initialBlocks={[]}
        defaultDate="2026-11-17"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Nuevo bloqueo" }));
    await user.type(screen.getByLabelText("Hora de inicio"), "12:00");
    await user.type(screen.getByLabelText("Hora de fin"), "16:00");
    await user.click(screen.getByRole("button", { name: "Guardar bloqueo" }));

    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeNull();
    });
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("mar, 17/11/2026");
    expect(alert).not.toHaveTextContent("2026-11-17");

    expect(screen.queryByText("mar, 17/11/2026 · 12:00 a 16:00")).not.toBeNull();

    await user.click(screen.getByRole("button", { name: "Eliminar bloqueo" }));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveTextContent(
      "¿Eliminar este bloqueo del mar, 17/11/2026 de 12:00 a 16:00?",
    );
    expect(dialog).not.toHaveTextContent("2026-11-17");
  });
});
