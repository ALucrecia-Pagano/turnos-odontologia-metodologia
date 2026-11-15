import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { WorkingHoursSection } from "./WorkingHoursSection";

const PROF_ID = "00000000-0000-0000-0000-000000000001";

describe("WorkingHoursSection", () => {
  it("Guardado exitoso de tramos semanales: envía PUT con los tramos en orden visual y anuncia Horario guardado.", async () => {
    const user = userEvent.setup();
    let putBody: unknown = null;
    const fetchFn: FetchFn = async (url, init) => {
      if (url.endsWith(`/professionals/${PROF_ID}/working-hours`) && init?.method === "PUT") {
        putBody = typeof init.body === "string" ? JSON.parse(init.body) : null;
        return new Response(
          JSON.stringify({
            workingHours: [{ weekday: 1, start: "09:00", end: "13:00" }],
            appointmentsOutsideHours: [],
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
        initialSlots={[{ weekday: 1, start: "09:00", end: "13:00" }]}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Guardar horario" }));

    await waitFor(() => {
      expect(putBody).toEqual([{ weekday: 1, start: "09:00", end: "13:00" }]);
    });
    expect(screen.queryByRole("status")).toHaveTextContent("Horario guardado.");
    expect(screen.queryByDisplayValue("09:00")).not.toBeNull();
    expect(screen.queryByDisplayValue("13:00")).not.toBeNull();
  });

  it("Edición interactiva de tramos en la interfaz: agrega una fila editable para el día martes y la quita al pulsar Quitar", async () => {
    const user = userEvent.setup();
    const fetchFn: FetchFn = async () => new Response("[]", { status: 200 });
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <WorkingHoursSection
        client={client}
        professionalId={PROF_ID}
        initialSlots={[]}
      />,
    );

    expect(screen.queryByLabelText("Inicio Martes tramo 1")).toBeNull();
    await user.click(screen.getByRole("button", { name: "Agregar tramo Martes" }));

    expect(screen.queryByLabelText("Inicio Martes tramo 1")).not.toBeNull();
    expect(screen.queryByLabelText("Fin Martes tramo 1")).not.toBeNull();

    await user.click(screen.getByRole("button", { name: "Quitar tramo 1 de Martes" }));
    expect(screen.queryByLabelText("Inicio Martes tramo 1")).toBeNull();
  });

  it("Rechazo por tramos solapados muestra mensaje literal del backend: muestra role=alert literal y traslada foco al contenedor de error", async () => {
    const user = userEvent.setup();
    const fetchFn: FetchFn = async () =>
      new Response(
        JSON.stringify({
          violations: [
            {
              code: "OVERLAPPING_WORKING_HOURS",
              message:
                "Los tramos 1 y 2 del lunes se solapan: de 09:00 a 12:00 y de 11:00 a 13:00.",
            },
          ],
        }),
        { status: 422, headers: { "Content-Type": "application/json" } },
      );
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <WorkingHoursSection
        client={client}
        professionalId={PROF_ID}
        initialSlots={[
          { weekday: 1, start: "09:00", end: "12:00" },
          { weekday: 1, start: "11:00", end: "13:00" },
        ]}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Guardar horario" }));

    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeNull();
    });
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(
      "Los tramos 1 y 2 del lunes se solapan: de 09:00 a 12:00 y de 11:00 a 13:00.",
    );
    expect(document.activeElement).toBe(alert);
    expect(screen.queryByDisplayValue("11:00")).not.toBeNull();
  });

  it("Error 400 marca campos con aria-invalid: marca el input inválido con aria-invalid=true y muestra el mensaje de validación", async () => {
    const user = userEvent.setup();
    const fetchFn: FetchFn = async () =>
      new Response(
        JSON.stringify({
          errors: [
            {
              field: "0.start",
              type: "value_error",
              message: "Dato inválido.",
            },
          ],
        }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <WorkingHoursSection
        client={client}
        professionalId={PROF_ID}
        initialSlots={[{ weekday: 1, start: "9:00", end: "13:00" }]}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Guardar horario" }));

    await waitFor(() => {
      expect(screen.queryByLabelText("Inicio Lunes tramo 1")).toHaveAttribute(
        "aria-invalid",
        "true",
      );
    });
    expect(screen.queryByRole("alert")).toHaveTextContent("Dato inválido.");
  });
});
