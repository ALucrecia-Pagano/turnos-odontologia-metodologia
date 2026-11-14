import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { createAppRoutes } from "../../App";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { createFixedClock } from "../agenda/clock";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";

const RECEPCION_USER = {
  id: "00000000-0000-0000-0000-0000000000e2",
  username: "recepcion",
  displayName: "Recepción Demo",
  role: "recepcion",
  professionalId: null,
};

const EMPTY_AGENDA = {
  from: "2026-11-16",
  to: "2026-11-16",
  timezone: "America/Argentina/Buenos_Aires",
  appointments: [],
  workingHours: [],
  blocks: [],
};

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
}

describe("RootGate", () => {
  it("usuario autenticado en / redirige a agenda", async () => {
    const fetchFn: FetchFn = async (url) => {
      if (url.includes("/agenda")) {
        return jsonResponse(EMPTY_AGENDA);
      }
      if (url.endsWith("/professionals") || url.endsWith("/chairs")) {
        return jsonResponse([]);
      }
      return jsonResponse(RECEPCION_USER);
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(createAppRoutes(createFixedClock("2026-11-16T12:00:00Z")), {
      initialEntries: ["/"],
    });

    render(
      <AuthProvider tokenStore={createMemoryTokenStore("token-ficticio-123")} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(`${router.state.location.pathname}${router.state.location.search}`).toBe("/agenda?date=2026-11-16");
    });
    expect(router.state.historyAction).toBe("REPLACE");
    expect(screen.queryByRole("heading", { level: 1, name: "Aqua — Clínica Odontológica" })).not.toBeInTheDocument();
    expect(screen.queryByText("Claridad en cada cuidado.")).not.toBeInTheDocument();
  });
});
