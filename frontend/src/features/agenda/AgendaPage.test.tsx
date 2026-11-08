import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import type { Clock } from "./clock";

const RECEPCION_USER = {
  id: "00000000-0000-0000-0000-0000000000e2",
  username: "recepcion",
  displayName: "Recepción Demo",
  role: "recepcion" as const,
  professionalId: null,
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

const CHAIRS = [
  { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón 1", active: true },
  { id: "00000000-0000-0000-0000-0000000000b2", name: "Sillón 2", active: true },
];

const ALL_APPOINTMENTS = [
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
];

const ALL_WORKING_HOURS = [
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
  {
    professionalId: "00000000-0000-0000-0000-000000000002",
    weekday: 1,
    start: "08:00",
    end: "12:00",
  },
];

const ALL_BLOCKS = [
  {
    id: "00000000-0000-0000-0000-000000000bb1",
    professionalId: "00000000-0000-0000-0000-000000000001",
    startAt: "2026-11-16T15:00:00Z",
    endAt: "2026-11-16T16:00:00Z",
    reason: "Congreso",
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

function createAgendaFetchFn(requestedUrls: string[]): FetchFn {
  return async (input) => {
    const url = String(input);
    requestedUrls.push(url);
    if (url.endsWith("/auth/me")) {
      return jsonResponse(RECEPCION_USER);
    }
    if (url.endsWith("/professionals")) {
      return jsonResponse(PROFESSIONALS);
    }
    if (url.endsWith("/chairs")) {
      return jsonResponse(CHAIRS);
    }
    if (url.includes("/agenda?")) {
      const parsedUrl = new URL(url, "http://localhost:8000");
      const from = parsedUrl.searchParams.get("from") ?? "2026-11-16";
      const to = parsedUrl.searchParams.get("to") ?? from;
      const profId = parsedUrl.searchParams.get("professionalId");
      const chairId = parsedUrl.searchParams.get("chairId");

      const appointments = ALL_APPOINTMENTS.filter((appt) => {
        if (from !== "2026-11-16") return false;
        if (profId !== null && appt.professionalId !== profId) return false;
        if (chairId !== null && appt.chairId !== chairId) return false;
        return true;
      });
      const workingHours = ALL_WORKING_HOURS.filter((wh) => {
        if (profId !== null && wh.professionalId !== profId) return false;
        return true;
      });
      const blocks = ALL_BLOCKS.filter((block) => {
        if (from !== "2026-11-16") return false;
        if (profId !== null && block.professionalId !== profId) return false;
        return true;
      });

      return jsonResponse({
        from,
        to,
        timezone: "America/Argentina/Buenos_Aires",
        appointments,
        workingHours,
        blocks,
      });
    }
    return jsonResponse({ detail: "Not found" }, 404);
  };
}

function renderAgendaPage(
  initialEntry: string,
  fetchFn: FetchFn,
  clock: Clock = FIXED_CLOCK,
) {
  const tokenStore = createMemoryTokenStore("token-recepcion-123");
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
  const router = createMemoryRouter(createAppRoutes(clock), {
    initialEntries: [initialEntry],
  });

  render(
    <AuthProvider tokenStore={tokenStore} client={client}>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </AuthProvider>,
  );

  return { router, tokenStore };
}

describe("AgendaPage", () => {
  it("carga con fetch y Clock inyectados y al filtrar por Sillón 2 conserva horarios y bloqueos con ayuda visible", async () => {
    const requestedUrls: string[] = [];
    const { router } = renderAgendaPage("/agenda", createAgendaFetchFn(requestedUrls));

    await waitFor(() => {
      expect(
        screen.queryByTestId("agenda-appointment-00000000-0000-0000-0000-000000000aa1"),
      ).not.toBeNull();
    });

    expect(requestedUrls).toContain(
      "http://localhost:8000/api/agenda?from=2026-11-16&to=2026-11-16",
    );
    expect(requestedUrls).toContain("http://localhost:8000/api/professionals");
    expect(requestedUrls).toContain("http://localhost:8000/api/chairs");

    const headers = screen.queryAllByTestId("agenda-column-header").map((el) => el.textContent);
    expect(headers).toEqual([
      "Dr. Martín Sosa",
      "Dra. Laura Quiroga",
      "Dra. Paula Benítez (inactivo)",
    ]);

    const chairSelect = screen.queryByLabelText("Sillón");
    expect(chairSelect).not.toBeNull();
    fireEvent.change(chairSelect!, {
      target: { value: "00000000-0000-0000-0000-0000000000b2" },
    });

    await waitFor(() => {
      expect(router.state.location.search).toContain(
        "chairId=00000000-0000-0000-0000-0000000000b2",
      );
    });
    expect(router.state.historyAction).toBe("PUSH");

    await waitFor(() => {
      expect(
        screen.queryByTestId("agenda-appointment-00000000-0000-0000-0000-000000000aa1"),
      ).toBeNull();
    });
    expect(
      screen.queryByTestId("agenda-appointment-00000000-0000-0000-0000-000000000aa2"),
    ).not.toBeNull();
    expect(
      screen.queryByLabelText("Bloqueo: Congreso, de 12:00 a 13:00"),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Horario de atención: 09:00 a 13:00"),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(
        "El filtro por sillón solo afecta los turnos; los horarios y bloqueos se siguen mostrando.",
      ),
    ).toBeInTheDocument();
  });

  it("filtra las tres colecciones por profesional, muestra Sin turnos para este filtro al combinar y Limpiar filtros conserva la fecha", async () => {
    const requestedUrls: string[] = [];
    const { router } = renderAgendaPage(
      "/agenda?date=2026-11-16",
      createAgendaFetchFn(requestedUrls),
    );

    await waitFor(() => {
      expect(
        screen.queryByTestId("agenda-appointment-00000000-0000-0000-0000-000000000aa1"),
      ).not.toBeNull();
    });

    const profSelect = screen.queryByLabelText("Profesional");
    expect(profSelect).not.toBeNull();
    fireEvent.change(profSelect!, {
      target: { value: "00000000-0000-0000-0000-000000000001" },
    });

    await waitFor(() => {
      expect(router.state.location.search).toContain(
        "professionalId=00000000-0000-0000-0000-000000000001",
      );
    });
    expect(router.state.historyAction).toBe("PUSH");

    await waitFor(() => {
      expect(
        screen.queryAllByTestId("agenda-column-header").map((el) => el.textContent),
      ).toEqual(["Dra. Laura Quiroga"]);
    });
    expect(
      screen.queryByTestId("agenda-appointment-00000000-0000-0000-0000-000000000aa1"),
    ).not.toBeNull();
    expect(
      screen.queryByTestId("agenda-appointment-00000000-0000-0000-0000-000000000aa2"),
    ).toBeNull();

    const chairSelect = screen.queryByLabelText("Sillón");
    expect(chairSelect).not.toBeNull();
    fireEvent.change(chairSelect!, {
      target: { value: "00000000-0000-0000-0000-0000000000b2" },
    });

    await waitFor(() => {
      expect(screen.queryByText("Sin turnos para este filtro")).toBeInTheDocument();
    });
    const quirogaCol = screen.queryByTestId(
      "agenda-column-00000000-0000-0000-0000-000000000001",
    );
    expect(quirogaCol).not.toBeNull();
    expect(
      within(quirogaCol!).queryByLabelText("Horario de atención: 09:00 a 13:00"),
    ).toBeInTheDocument();
    expect(
      within(quirogaCol!).queryByLabelText("Bloqueo: Congreso, de 12:00 a 13:00"),
    ).toBeInTheDocument();

    const clearBtn = screen.queryByRole("button", { name: "Limpiar filtros" });
    expect(clearBtn).not.toBeNull();
    fireEvent.click(clearBtn!);

    await waitFor(() => {
      expect(router.state.location.search).toBe("?date=2026-11-16");
    });
    await waitFor(() => {
      expect(screen.queryAllByTestId("agenda-column-header")).toHaveLength(3);
    });
  });

  it("navega con Anterior, Siguiente, Hoy y el selector de fecha usando push en la URL", async () => {
    const requestedUrls: string[] = [];
    const { router } = renderAgendaPage(
      "/agenda?date=2026-11-16",
      createAgendaFetchFn(requestedUrls),
    );

    await waitFor(() => {
      expect(
        screen.queryByTestId("agenda-appointment-00000000-0000-0000-0000-000000000aa1"),
      ).not.toBeNull();
    });

    const prevBtn = screen.queryByRole("button", { name: "Anterior" });
    expect(prevBtn).not.toBeNull();
    fireEvent.click(prevBtn!);

    await waitFor(() => {
      expect(`${router.state.location.pathname}${router.state.location.search}`).toBe(
        "/agenda?date=2026-11-15",
      );
    });
    expect(router.state.historyAction).toBe("PUSH");
    expect(requestedUrls).toContain(
      "http://localhost:8000/api/agenda?from=2026-11-15&to=2026-11-15",
    );

    const nextBtn = screen.queryByRole("button", { name: "Siguiente" });
    expect(nextBtn).not.toBeNull();
    fireEvent.click(nextBtn!);

    await waitFor(() => {
      expect(`${router.state.location.pathname}${router.state.location.search}`).toBe(
        "/agenda?date=2026-11-16",
      );
    });
    expect(router.state.historyAction).toBe("PUSH");

    const dateInput = screen.queryByLabelText("Fecha");
    expect(dateInput).not.toBeNull();
    fireEvent.change(dateInput!, { target: { value: "2026-12-01" } });

    await waitFor(() => {
      expect(`${router.state.location.pathname}${router.state.location.search}`).toBe(
        "/agenda?date=2026-12-01",
      );
    });
    expect(router.state.historyAction).toBe("PUSH");
    expect(requestedUrls).toContain(
      "http://localhost:8000/api/agenda?from=2026-12-01&to=2026-12-01",
    );

    const todayBtn = screen.queryByRole("button", { name: "Hoy" });
    expect(todayBtn).not.toBeNull();
    fireEvent.click(todayBtn!);

    await waitFor(() => {
      expect(`${router.state.location.pathname}${router.state.location.search}`).toBe(
        "/agenda?date=2026-11-16",
      );
    });
    expect(router.state.historyAction).toBe("PUSH");
  });

  it("respeta el borde de medianoche en la fecha inicial y normaliza una fecha inválida con replace mostrando aviso", async () => {
    const requestedMidnight: string[] = [];
    const midnightClock: Clock = {
      now: () => new Date("2026-11-16T02:30:00Z"),
    };
    const midnightRender = renderAgendaPage(
      "/agenda",
      createAgendaFetchFn(requestedMidnight),
      midnightClock,
    );

    await waitFor(() => {
      expect(requestedMidnight).toContain(
        "http://localhost:8000/api/agenda?from=2026-11-15&to=2026-11-15",
      );
    });
    await waitFor(() => {
      expect(midnightRender.router.state.location.search).toBe("?date=2026-11-15");
    });
    expect(midnightRender.router.state.historyAction).toBe("REPLACE");

    const requestedInvalid: string[] = [];
    const invalidRender = renderAgendaPage(
      "/agenda?date=fecha-invalida",
      createAgendaFetchFn(requestedInvalid),
      FIXED_CLOCK,
    );

    await waitFor(() => {
      expect(invalidRender.router.state.location.search).toBe("?date=2026-11-16");
    });
    expect(invalidRender.router.state.historyAction).toBe("REPLACE");
    expect(requestedInvalid).toContain(
      "http://localhost:8000/api/agenda?from=2026-11-16&to=2026-11-16",
    );
    expect(
      screen.queryByText("La fecha del enlace no era válida; se muestra hoy."),
    ).toBeInTheDocument();
  });

  it("muestra Cargando... con role=status en la carga inicial sin mostrar error", async () => {
    const fetchFn: FetchFn = (input) => {
      const url = String(input);
      if (url.endsWith("/auth/me")) {
        return Promise.resolve(jsonResponse(RECEPCION_USER));
      }
      return new Promise<Response>(() => {});
    };

    renderAgendaPage("/agenda?date=2026-11-16", fetchFn);

    await waitFor(() => {
      expect(screen.queryByText("Recepción Demo")).toBeInTheDocument();
    });
    expect(screen.queryByRole("status")).toHaveTextContent("Cargando...");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("muestra ErrorState con Reintentar ante error de red, al reintentar con 200 renderiza la agenda y Actualizar agenda refresca manualmente", async () => {
    let agendaCalls = 0;
    const baseFetch = createAgendaFetchFn([]);
    const fetchFn: FetchFn = async (input, init) => {
      const url = String(input);
      if (url.includes("/agenda?")) {
        agendaCalls += 1;
        if (agendaCalls === 1) {
          throw new TypeError("Failed to fetch");
        }
      }
      return baseFetch(input, init);
    };

    renderAgendaPage("/agenda?date=2026-11-16", fetchFn);

    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeNull();
    });
    const retryBtn = screen.queryByRole("button", { name: "Reintentar" });
    expect(retryBtn).not.toBeNull();
    fireEvent.click(retryBtn!);

    await waitFor(() => {
      expect(
        screen.queryByTestId("agenda-appointment-00000000-0000-0000-0000-000000000aa1"),
      ).not.toBeNull();
    });
    expect(agendaCalls).toBe(2);

    const refreshBtn = screen.queryByRole("button", { name: "Actualizar agenda" });
    expect(refreshBtn).not.toBeNull();
    fireEvent.click(refreshBtn!);

    await waitFor(() => {
      expect(agendaCalls).toBe(3);
    });
  });

  it("delega el 401 de GET /api/agenda en C-26 descartando el token y redirigiendo a /login sin mostrar error local", async () => {
    const fetchFn: FetchFn = async (input) => {
      const url = String(input);
      if (url.endsWith("/auth/me")) {
        return jsonResponse(RECEPCION_USER);
      }
      if (url.includes("/agenda?")) {
        return jsonResponse(
          {
            code: "INVALID_TOKEN",
            message: "La sesión venció o no es válida. Inicie sesión de nuevo.",
          },
          401,
        );
      }
      return jsonResponse([]);
    };

    const { router, tokenStore } = renderAgendaPage("/agenda?date=2026-11-16", fetchFn);

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/login");
    });
    expect(tokenStore.getToken()).toBeNull();
    await waitFor(() => {
      expect(screen.queryByRole("alert")).toHaveTextContent(
        "La sesión venció. Iniciá sesión de nuevo.",
      );
    });
    expect(
      screen.queryByText("La sesión venció o no es válida. Inicie sesión de nuevo."),
    ).not.toBeInTheDocument();
  });

  it("muestra la violación de un 403 en el error local sin cerrar sesión ni duplicar el banner global", async () => {
    const fetchFn: FetchFn = async (input) => {
      const url = String(input);
      if (url.endsWith("/auth/me")) {
        return jsonResponse(RECEPCION_USER);
      }
      if (url.includes("/agenda?")) {
        return jsonResponse(
          {
            violations: [
              {
                code: "FORBIDDEN_OPERATION",
                message: "No tiene permiso para leer la agenda.",
              },
            ],
          },
          403,
        );
      }
      return jsonResponse([]);
    };

    const { router, tokenStore } = renderAgendaPage("/agenda?date=2026-11-16", fetchFn);

    await waitFor(() => {
      const alerts = screen.queryAllByRole("alert");
      expect(alerts).toHaveLength(1);
    });
    expect(screen.queryAllByRole("alert")[0]).toHaveTextContent("No tiene permiso para leer la agenda.");
    expect(router.state.location.pathname).toBe("/agenda");
    expect(tokenStore.getToken()).toBe("token-recepcion-123");
  });
});
