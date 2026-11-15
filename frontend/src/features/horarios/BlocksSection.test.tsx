import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { BlocksSection } from "./BlocksSection";

const PROF_ID = "00000000-0000-0000-0000-000000000001";
const BLOCK_ID = "00000000-0000-0000-0000-0000000000b1";

describe("BlocksSection", () => {
  it("Creación exitosa de bloqueo con offset: convierte fecha y hora local a ISO con offset, cierra el diálogo y anuncia Bloqueo creado.", async () => {
    const user = userEvent.setup();
    let postBody: unknown = null;
    const fetchFn: FetchFn = async (url, init) => {
      if (url.endsWith(`/professionals/${PROF_ID}/blocks`) && init?.method === "POST") {
        postBody = typeof init.body === "string" ? JSON.parse(init.body) : null;
        return new Response(
          JSON.stringify({
            block: {
              id: BLOCK_ID,
              professionalId: PROF_ID,
              startAt: "2026-05-06T14:00:00-03:00",
              endAt: "2026-05-06T16:00:00-03:00",
              reason: "Congreso odontológico",
            },
            affectedAppointments: [],
          }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("[]", { status: 200 });
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <BlocksSection
        client={client}
        professionalId={PROF_ID}
        timezone="America/Argentina/Buenos_Aires"
        initialBlocks={[]}
        defaultDate="2026-05-06"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Nuevo bloqueo" }));
    expect(screen.queryByRole("dialog")).not.toBeNull();

    await user.type(screen.getByLabelText("Hora de inicio"), "14:00");
    await user.type(screen.getByLabelText("Hora de fin"), "16:00");
    await user.type(screen.getByLabelText("Motivo (opcional)"), "Congreso odontológico");

    await user.click(screen.getByRole("button", { name: "Guardar bloqueo" }));

    await waitFor(() => {
      expect(postBody).toEqual({
        startAt: "2026-05-06T14:00:00-03:00",
        endAt: "2026-05-06T16:00:00-03:00",
        reason: "Congreso odontológico",
      });
    });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.queryByRole("status")).toHaveTextContent("Bloqueo creado.");
    expect(screen.queryByText(/Congreso odontológico/)).not.toBeNull();
  });

  it("Eliminación de bloqueo con confirmación in-dialog: exige confirmación antes de enviar DELETE y anuncia Bloqueo eliminado.", async () => {
    const user = userEvent.setup();
    let deleteCalled = false;
    const fetchFn: FetchFn = async (url, init) => {
      if (url.endsWith(`/blocks/${BLOCK_ID}`) && init?.method === "DELETE") {
        deleteCalled = true;
        return new Response(
          JSON.stringify({
            id: BLOCK_ID,
            professionalId: PROF_ID,
            startAt: "2026-05-06T14:00:00-03:00",
            endAt: "2026-05-06T16:00:00-03:00",
            reason: "Congreso odontológico",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not Found", { status: 404 });
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <BlocksSection
        client={client}
        professionalId={PROF_ID}
        timezone="America/Argentina/Buenos_Aires"
        initialBlocks={[
          {
            id: BLOCK_ID,
            professionalId: PROF_ID,
            startAt: "2026-05-06T14:00:00-03:00",
            endAt: "2026-05-06T16:00:00-03:00",
            reason: "Congreso odontológico",
          },
        ]}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Eliminar bloqueo" }));
    expect(deleteCalled).toBe(false);
    expect(screen.queryByRole("dialog")).not.toBeNull();

    await user.click(screen.getByRole("button", { name: "Sí, eliminar bloqueo" }));

    await waitFor(() => {
      expect(deleteCalled).toBe(true);
    });
    expect(screen.queryByText(/Congreso odontológico/)).toBeNull();
    expect(screen.queryByRole("status")).toHaveTextContent("Bloqueo eliminado.");
  });

  it("Cancelación del borrado con Escape: cierra el diálogo al pulsar Escape o Volver sin enviar DELETE y restaura el foco", async () => {
    const user = userEvent.setup();
    let deleteCalled = false;
    const fetchFn: FetchFn = async () => {
      deleteCalled = true;
      return new Response("{}", { status: 200 });
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <BlocksSection
        client={client}
        professionalId={PROF_ID}
        timezone="America/Argentina/Buenos_Aires"
        initialBlocks={[
          {
            id: BLOCK_ID,
            professionalId: PROF_ID,
            startAt: "2026-05-06T14:00:00-03:00",
            endAt: "2026-05-06T16:00:00-03:00",
            reason: "Congreso odontológico",
          },
        ]}
      />,
    );

    const deleteTrigger = screen.getByRole("button", { name: "Eliminar bloqueo" });
    await user.click(deleteTrigger);
    expect(screen.queryByRole("dialog")).not.toBeNull();

    const volverButton = screen.getByRole("button", { name: "Volver" });
    volverButton.focus();
    await user.keyboard("{Escape}");

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(deleteCalled).toBe(false);
    expect(document.activeElement).toBe(deleteTrigger);

    await user.click(deleteTrigger);
    expect(screen.queryByRole("dialog")).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "Volver" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(deleteCalled).toBe(false);
    expect(screen.queryByText(/Congreso odontológico/)).not.toBeNull();
  });

  it("Bloqueo inválido muestra mensaje literal del backend: mantiene el diálogo abierto y muestra role=alert literal ante error 422", async () => {
    const user = userEvent.setup();
    const fetchFn: FetchFn = async () =>
      new Response(
        JSON.stringify({
          violations: [
            {
              code: "INVALID_BLOCK",
              message: "El bloqueo no es válido: el inicio debe ser anterior al fin.",
            },
          ],
        }),
        { status: 422, headers: { "Content-Type": "application/json" } },
      );
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <BlocksSection
        client={client}
        professionalId={PROF_ID}
        timezone="America/Argentina/Buenos_Aires"
        initialBlocks={[]}
        defaultDate="2026-05-06"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Nuevo bloqueo" }));
    await user.type(screen.getByLabelText("Hora de inicio"), "16:00");
    await user.type(screen.getByLabelText("Hora de fin"), "14:00");
    await user.click(screen.getByRole("button", { name: "Guardar bloqueo" }));

    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeNull();
    });
    expect(screen.getByRole("alert")).toHaveTextContent(
      "El bloqueo no es válido: el inicio debe ser anterior al fin.",
    );
    expect(screen.queryByRole("dialog")).not.toBeNull();
    expect(screen.queryByDisplayValue("16:00")).not.toBeNull();
  });
});
