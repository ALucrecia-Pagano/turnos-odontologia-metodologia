import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import type { Clock } from "./clock";

const RECEPCION_USER = {
  id: "00000000-0000-0000-0000-0000000000e2",
  username: "recepcion",
  displayName: "Recepción Demo",
  role: "recepcion" as const,
  professionalId: null,
};

const ODONTOLOGO_USER = {
  id: "00000000-0000-0000-0000-0000000000e3",
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
    fullName: "Dr. Martín Sosa",
    licenseNumber: "MP-1002",
    active: true,
  },
];

const CHAIRS = [
  { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón 1", active: true },
  { id: "00000000-0000-0000-0000-0000000000b2", name: "Sillón 2", active: true },
];

const APPOINTMENTS = [
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
    patientName: "Carlos Gómez",
    professionalId: "00000000-0000-0000-0000-000000000002",
    professionalName: "Dr. Martín Sosa",
    chairId: "00000000-0000-0000-0000-0000000000b2",
    chairName: "Sillón 2",
    serviceId: "00000000-0000-0000-0000-0000000000d2",
    serviceName: "Limpieza",
    startAt: "2026-11-16T14:00:00Z",
    endAt: "2026-11-16T14:30:00Z",
    status: "confirmado",
  },
];

const WORKING_HOURS = [
  {
    professionalId: "00000000-0000-0000-0000-000000000001",
    weekday: 1,
    start: "09:00",
    end: "13:00",
  },
  {
    professionalId: "00000000-0000-0000-0000-000000000002",
    weekday: 1,
    start: "09:00",
    end: "13:00",
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

function createAgendaFetchFn(
  requestedUrls: string[],
  user: typeof RECEPCION_USER | typeof ODONTOLOGO_USER = RECEPCION_USER,
): FetchFn {
  return async (input) => {
    const url = String(input);
    requestedUrls.push(url);
    if (url.endsWith("/auth/me")) {
      return jsonResponse(user);
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

      const appointments = APPOINTMENTS.filter((appt) => {
        if (from !== "2026-11-16") return false;
        if (profId !== null && appt.professionalId !== profId) return false;
        if (chairId !== null && appt.chairId !== chairId) return false;
        return true;
      });

      return jsonResponse({
        from,
        to,
        timezone: "America/Argentina/Buenos_Aires",
        appointments,
        workingHours: WORKING_HOURS,
        blocks: [],
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
  const tokenStore = createMemoryTokenStore("token-123");
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

describe("AgendaPage — Modo Sillones", () => {
  it("Activar Sillones conserva fecha y filtros: activar Sillones conserva fecha y filtros", async () => {
    const requestedUrls: string[] = [];
    const { router } = renderAgendaPage(
      "/agenda?date=2026-11-16&professionalId=00000000-0000-0000-0000-000000000001&chairId=00000000-0000-0000-0000-0000000000b1",
      createAgendaFetchFn(requestedUrls),
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Sillones" })).toBeInTheDocument();
    });

    const sillonesBtn = screen.getByRole("button", { name: "Sillones" });
    fireEvent.click(sillonesBtn);

    await waitFor(() => {
      expect(router.state.location.search).toContain("view=chair");
    });
    expect(router.state.location.search).toContain("date=2026-11-16");
    expect(router.state.location.search).toContain(
      "professionalId=00000000-0000-0000-0000-000000000001",
    );
    expect(router.state.location.search).toContain(
      "chairId=00000000-0000-0000-0000-0000000000b1",
    );
  });

  it("Un view desconocido sigue cayendo a Día: view desconocido cae a Día", async () => {
    const requestedUrls: string[] = [];
    renderAgendaPage(
      "/agenda?date=2026-11-16&view=invalido",
      createAgendaFetchFn(requestedUrls),
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Día" })).toHaveAttribute(
        "aria-pressed",
        "true",
      );
    });
    expect(screen.getByRole("button", { name: "Sillones" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(screen.getByText("Agenda diaria")).toBeInTheDocument();
  });

  it("Filtro de un solo sillón: chairId deja una sola columna", async () => {
    const requestedUrls: string[] = [];
    renderAgendaPage(
      "/agenda?date=2026-11-16&view=chair&chairId=00000000-0000-0000-0000-0000000000b2",
      createAgendaFetchFn(requestedUrls),
    );

    await waitFor(() => {
      expect(
        screen.getByTestId("agenda-column-00000000-0000-0000-0000-0000000000b2"),
      ).toBeInTheDocument();
    });

    const headers = screen.getAllByTestId("agenda-column-header");
    expect(headers).toHaveLength(1);
    expect(headers[0]).toHaveTextContent("Sillón 2");
    expect(
      screen.queryByTestId("agenda-column-00000000-0000-0000-0000-0000000000b1"),
    ).toBeNull();
  });

  it("Día por defecto desde el Clock: view=chair sin date usa el Clock", async () => {
    const requestedUrls: string[] = [];
    const clock: Clock = {
      now: () => new Date("2026-11-16T15:00:00Z"),
    };
    const { router } = renderAgendaPage(
      "/agenda?view=chair",
      createAgendaFetchFn(requestedUrls),
      clock,
    );

    await waitFor(() => {
      expect(router.state.location.search).toContain("date=2026-11-16");
    });
    expect(router.state.location.search).toContain("view=chair");

    const agendaCalls = requestedUrls.filter((u) => u.includes("/agenda?"));
    expect(agendaCalls).toHaveLength(1);
    expect(agendaCalls[0]).toContain("from=2026-11-16&to=2026-11-16");
  });

  it("Navegación de un día: Siguiente suma un día en view=chair", async () => {
    const requestedUrls: string[] = [];
    const { router } = renderAgendaPage(
      "/agenda?date=2026-11-16&view=chair",
      createAgendaFetchFn(requestedUrls),
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Siguiente" })).toBeInTheDocument();
    });

    const nextBtn = screen.getByRole("button", { name: "Siguiente" });
    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(router.state.location.search).toContain("date=2026-11-17");
    });
    expect(router.state.location.search).toContain("view=chair");
  });

  it("Odontólogo sin acceso: odontólogo con view=chair cae a Día", async () => {
    const requestedUrls: string[] = [];
    const { router } = renderAgendaPage(
      "/agenda?date=2026-11-16&view=chair",
      createAgendaFetchFn(requestedUrls, ODONTOLOGO_USER),
    );

    await waitFor(() => {
      expect(router.state.location.search).not.toContain("view=chair");
    });
    expect(screen.queryByRole("button", { name: "Sillones" })).toBeNull();
    expect(screen.getByRole("button", { name: "Día" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("El filtro de sillón reduce las columnas: aplicar el filtro Sillón 2 actualiza la URL y reduce a una columna", async () => {
    const requestedUrls: string[] = [];
    const { router } = renderAgendaPage(
      "/agenda?date=2026-11-16&view=chair",
      createAgendaFetchFn(requestedUrls),
    );

    await waitFor(() => {
      expect(
        screen.getByTestId("agenda-column-00000000-0000-0000-0000-0000000000b1"),
      ).toBeInTheDocument();
    });

    const chairSelect = screen.getByLabelText("Sillón");
    fireEvent.change(chairSelect, {
      target: { value: "00000000-0000-0000-0000-0000000000b2" },
    });

    await waitFor(() => {
      expect(router.state.location.search).toContain(
        "chairId=00000000-0000-0000-0000-0000000000b2",
      );
    });

    await waitFor(() => {
      expect(
        screen.queryByTestId("agenda-column-00000000-0000-0000-0000-0000000000b1"),
      ).toBeNull();
    });
    expect(
      screen.getByTestId("agenda-column-00000000-0000-0000-0000-0000000000b2"),
    ).toBeInTheDocument();
  });
});
