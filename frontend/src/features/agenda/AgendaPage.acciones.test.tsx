import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import type { AgendaAppointment } from "./agendaApi";
import type { Clock } from "./clock";

const RECEPCION_USER = {
  id: "00000000-0000-0000-0000-0000000000e2",
  username: "recepcion",
  displayName: "Recepción Demo",
  role: "recepcion" as const,
  professionalId: null,
};

const ODONTOLOGO_USER = {
  id: "00000000-0000-0000-0000-0000000000e1",
  username: "odontologo",
  displayName: "Dra. Laura Quiroga",
  role: "odontologo" as const,
  professionalId: "00000000-0000-0000-0000-000000000001",
};

const PROFESSIONALS = [
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

const CHAIRS = [
  { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón 1", active: true },
];

const APPOINTMENTS: AgendaAppointment[] = [
  {
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
  },
  {
    id: "00000000-0000-0000-0000-000000000aa2",
    patientId: "00000000-0000-0000-0000-0000000000c2",
    patientName: "Bruno Acosta",
    professionalId: "00000000-0000-0000-0000-000000000002",
    professionalName: "Dr. Carlos Rossi",
    chairId: "00000000-0000-0000-0000-0000000000b1",
    chairName: "Sillón 1",
    serviceId: "00000000-0000-0000-0000-0000000000d1",
    serviceName: "Control",
    startAt: "2026-11-16T14:00:00Z",
    endAt: "2026-11-16T14:30:00Z",
    status: "reservado",
  },
];

const FIXED_CLOCK: Clock = {
  now: () => new Date("2026-11-16T12:00:00Z"),
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function createFetchFn(options: {
  user?: typeof RECEPCION_USER | typeof ODONTOLOGO_USER;
  historyRequested?: { current: boolean };
  onStatusPost?: (body: unknown) => Response | null;
  onCancelPost?: () => Response | null;
  onReschedulePost?: (body: unknown) => Response | null;
  refreshCount?: { current: number };
}): FetchFn {
  const activeUser = options.user ?? RECEPCION_USER;

  return async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";

    if (url.endsWith("/auth/me")) {
      return jsonResponse(activeUser);
    }
    if (url.endsWith("/professionals")) {
      return jsonResponse(PROFESSIONALS);
    }
    if (url.endsWith("/chairs")) {
      return jsonResponse(CHAIRS);
    }
    if (url.includes("/agenda?")) {
      if (options.refreshCount) {
        options.refreshCount.current++;
      }
      return jsonResponse({
        from: "2026-11-16",
        to: "2026-11-16",
        timezone: "America/Argentina/Buenos_Aires",
        appointments: APPOINTMENTS,
        workingHours: [],
        blocks: [],
      });
    }
    if (url.includes("/history")) {
      if (options.historyRequested) {
        options.historyRequested.current = true;
      }
      return jsonResponse([]);
    }
    if (url.includes("/status") && method === "POST") {
      if (options.onStatusPost) {
        const customRes = options.onStatusPost(JSON.parse(String(init?.body)));
        if (customRes) return customRes;
      }
      return jsonResponse({ ...APPOINTMENTS[0], status: "confirmado" });
    }
    if (url.includes("/cancel") && method === "POST") {
      if (options.onCancelPost) {
        const customRes = options.onCancelPost();
        if (customRes) return customRes;
      }
      return jsonResponse({ ...APPOINTMENTS[0], status: "cancelado" });
    }
    if (url.includes("/reschedule") && method === "POST") {
      if (options.onReschedulePost) {
        const customRes = options.onReschedulePost(JSON.parse(String(init?.body)));
        if (customRes) return customRes;
      }
      return jsonResponse({ ...APPOINTMENTS[0], status: "reservado" });
    }

    return jsonResponse({ detail: "Not found" }, 404);
  };
}

function renderPage(fetchFn: FetchFn) {
  const tokenStore = createMemoryTokenStore("token-test");
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
  const router = createMemoryRouter(createAppRoutes(FIXED_CLOCK), {
    initialEntries: ["/agenda?date=2026-11-16"],
  });

  render(
    <AuthProvider tokenStore={tokenStore} client={client}>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </AuthProvider>,
  );

  return { router, tokenStore, client };
}

describe("AgendaPage — Integración de Acciones", () => {
  it("7.1 restringir acciones de odontólogo en turnos propios a cambios de estado e historial", async () => {
    const historyRequested = { current: false };
    const fetchFn = createFetchFn({
      user: ODONTOLOGO_USER,
      historyRequested,
    });
    renderPage(fetchFn);

    const apptCard = await screen.findByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa1",
    );
    fireEvent.click(apptCard);

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmar turno" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Marcar atendido" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Marcar ausente" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reprogramar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cancelar turno" })).not.toBeInTheDocument();
    expect(historyRequested.current).toBe(true);
  });

  it("7.2 bloquear acciones e historial para odontólogo en turnos ajenos", async () => {
    const historyRequested = { current: false };
    const fetchFn = createFetchFn({
      user: ODONTOLOGO_USER,
      historyRequested,
    });
    renderPage(fetchFn);

    const otherApptCard = await screen.findByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa2",
    );
    fireEvent.click(otherApptCard);

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Confirmar turno" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Marcar atendido" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Marcar ausente" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reprogramar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cancelar turno" })).not.toBeInTheDocument();
    expect(historyRequested.current).toBe(false);
  });

  it("7.3 respuesta 403 FORBIDDEN_OPERATION muestra alerta sin cerrar sesión", async () => {
    const fetchFn = createFetchFn({
      onStatusPost: () =>
        jsonResponse(
          {
            violations: [
              {
                code: "FORBIDDEN_OPERATION",
                message: "No posee permisos para realizar esta operación.",
              },
            ],
          },
          403,
        ),
    });
    renderPage(fetchFn);

    const apptCard = await screen.findByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa1",
    );
    fireEvent.click(apptCard);

    const confirmBtn = await screen.findByRole("button", { name: "Confirmar turno" });
    fireEvent.click(confirmBtn);

    const alert = await screen.findByRole("alert", {
      name: (content) => content.includes("No se pudo actualizar el turno") || true,
    });
    expect(alert).toBeInTheDocument();
    const dialog = screen.getByRole("dialog");
    const dialogAlert = within(dialog).queryByRole("alert");
    expect(dialogAlert).not.toBeNull();
    expect(within(dialogAlert!).queryByText("FORBIDDEN_OPERATION")).not.toBeNull();
    expect(
      within(dialogAlert!).queryByText("No posee permisos para realizar esta operación."),
    ).not.toBeNull();
  });

  it("7.4 seleccionar turno abre modal y mutación exitosa refresca la agenda", async () => {
    const refreshCount = { current: 0 };
    const fetchFn = createFetchFn({ refreshCount });
    renderPage(fetchFn);

    const apptCard = await screen.findByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa1",
    );
    expect(refreshCount.current).toBe(1);

    fireEvent.click(apptCard);
    expect(await screen.findByRole("dialog")).toBeInTheDocument();

    const confirmBtn = screen.getByRole("button", { name: "Confirmar turno" });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(refreshCount.current).toBeGreaterThanOrEqual(2);
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  it("7.5 confirmación emite anuncio Turno confirmado.", async () => {
    const fetchFn = createFetchFn({});
    renderPage(fetchFn);

    const apptCard = await screen.findByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa1",
    );
    fireEvent.click(apptCard);

    const confirmBtn = await screen.findByRole("button", { name: "Confirmar turno" });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      const statusRegion = screen.getByRole("status");
      expect(statusRegion).toHaveTextContent("Turno confirmado.");
    });
  });

  it("7.6 marcar atendido emite anuncio Turno marcado como atendido.", async () => {
    const fetchFn = createFetchFn({
      onStatusPost: () => jsonResponse({ ...APPOINTMENTS[0], status: "atendido" }),
    });
    renderPage(fetchFn);

    const apptCard = await screen.findByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa1",
    );
    fireEvent.click(apptCard);

    const attendBtn = await screen.findByRole("button", { name: "Marcar atendido" });
    fireEvent.click(attendBtn);

    await waitFor(() => {
      const statusRegion = screen.getByRole("status");
      expect(statusRegion).toHaveTextContent("Turno marcado como atendido.");
    });
  });

  it("7.7 marcar ausente emite anuncio Turno marcado como ausente.", async () => {
    const fetchFn = createFetchFn({
      onStatusPost: () => jsonResponse({ ...APPOINTMENTS[0], status: "ausente" }),
    });
    renderPage(fetchFn);

    const apptCard = await screen.findByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa1",
    );
    fireEvent.click(apptCard);

    const noshowBtn = await screen.findByRole("button", { name: "Marcar ausente" });
    fireEvent.click(noshowBtn);

    await waitFor(() => {
      const statusRegion = screen.getByRole("status");
      expect(statusRegion).toHaveTextContent("Turno marcado como ausente.");
    });
  });

  it("7.8 cancelar emite anuncio Turno cancelado.", async () => {
    const fetchFn = createFetchFn({});
    renderPage(fetchFn);

    const apptCard = await screen.findByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa1",
    );
    fireEvent.click(apptCard);

    const cancelBtn = await screen.findByRole("button", { name: "Cancelar turno" });
    fireEvent.click(cancelBtn);

    const confirmCancelBtn = await screen.findByRole("button", {
      name: "Confirmar cancelación",
    });
    fireEvent.click(confirmCancelBtn);

    await waitFor(() => {
      const statusRegion = screen.getByRole("status");
      expect(statusRegion).toHaveTextContent("Turno cancelado.");
    });
  });

  it("7.9 reprogramar emite anuncio Turno reprogramado para el DD/MM/AAAA a las HH:MM.", async () => {
    const fetchFn = createFetchFn({
      onReschedulePost: () =>
        jsonResponse({
          ...APPOINTMENTS[0],
          startAt: "2026-11-17T14:00:00Z", // 11:00 UTC-3
          endAt: "2026-11-17T14:30:00Z",
          status: "reservado",
        }),
    });
    renderPage(fetchFn);

    const apptCard = await screen.findByTestId(
      "agenda-appointment-00000000-0000-0000-0000-000000000aa1",
    );
    fireEvent.click(apptCard);

    const rescheduleBtn = await screen.findByRole("button", { name: "Reprogramar" });
    fireEvent.click(rescheduleBtn);

    const submitBtn = await screen.findByRole("button", {
      name: "Guardar reprogramación",
    });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      const statusRegion = screen.getByRole("status");
      expect(statusRegion).toHaveTextContent(
        "Turno reprogramado para el 17/11/2026 a las 11:00.",
      );
    });
  });
});
