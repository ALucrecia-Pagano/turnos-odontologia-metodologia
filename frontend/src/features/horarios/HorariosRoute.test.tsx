import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { createFixedClock } from "../agenda/clock";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient, type FetchFn } from "../../shared/api/client";

const FIXED_NOW = new Date("2026-05-04T12:00:00Z");
const PROF_ID = "00000000-0000-0000-0000-000000000001";

describe("Ruta /horarios bajo AppShell", () => {
  it("renderiza el contenedor principal de Horarios y bloqueos en /horarios para usuario autenticado y redirige a /login si es anónimo", async () => {
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e3",
            username: "quiroga",
            displayName: "Dra. Laura Quiroga",
            role: "odontologo",
            professionalId: PROF_ID,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/agenda?")) {
        return new Response(
          JSON.stringify({
            from: "2026-05-04",
            to: "2026-05-04",
            timezone: "America/Argentina/Buenos_Aires",
            appointments: [],
            workingHours: [],
            blocks: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_ID}/working-hours`)) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url.endsWith(`/professionals/${PROF_ID}/blocks`)) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    const clock = createFixedClock(FIXED_NOW);
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(createAppRoutes(clock), {
      initialEntries: ["/horarios"],
      future: { v7_relativeSplatPath: true },
    });

    const view = render(
      <AuthProvider tokenStore={createMemoryTokenStore("token-odontologo")} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByRole("navigation", { name: "Menú principal" })).not.toBeNull();
    });
    expect(screen.queryByRole("heading", { name: "Horarios y bloqueos" })).not.toBeNull();

    view.unmount();

    const anonRouter = createMemoryRouter(createAppRoutes(clock), {
      initialEntries: ["/horarios"],
      future: { v7_relativeSplatPath: true },
    });
    render(
      <AuthProvider tokenStore={createMemoryTokenStore(null)} client={client}>
        <RouterProvider router={anonRouter} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(anonRouter.state.location.pathname).toBe("/login");
    });
  });
});
