import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient, type FetchFn } from "../../shared/api/client";

function renderCatalogos(
  fetchFn: FetchFn,
  initialEntry = "/catalogos",
  role: "administrador" | "recepcion" | "odontologo" = "administrador",
) {
  const tokenStore = createMemoryTokenStore("token-test");
  const router = createMemoryRouter(createAppRoutes(), {
    initialEntries: [initialEntry],
  });

  const wrappedFetchFn: FetchFn = async (url, init) => {
    if (url.endsWith("/auth/me")) {
      return new Response(
        JSON.stringify({
          id: "00000000-0000-0000-0000-0000000000e1",
          username: "admin",
          displayName: "Admin Demo",
          role,
          professionalId: null,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    return fetchFn(url, init);
  };

  const clientWithAuth = createApiClient({
    baseUrl: "http://localhost:8000/api",
    fetchFn: wrappedFetchFn,
  });

  return render(
    <AuthProvider tokenStore={tokenStore} client={clientWithAuth}>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
}

describe("CatalogConfirmDialog", () => {
  it("Desactivar un sillón exige confirmación interna", async () => {
    const user = userEvent.setup();
    let postDeactivateCalls = 0;
    let isSillon2Active = true;

    const fetchFn: FetchFn = async (url, init) => {
      if (url.includes("/chairs/chair-2/deactivate") && init?.method === "POST") {
        postDeactivateCalls++;
        isSillon2Active = false;
        return new Response(
          JSON.stringify({
            id: "chair-2",
            name: "Sillón 2",
            active: false,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/chairs") && (!init?.method || init.method === "GET")) {
        return new Response(
          JSON.stringify([
            { id: "chair-2", name: "Sillón 2", active: isSillon2Active },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderCatalogos(fetchFn, "/catalogos?seccion=sillones");

    await waitFor(() => {
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    // Paso 1: Pulsar "Desactivar" en la fila de Sillón 2
    const deactivateBtn = screen.getByRole("button", { name: "Desactivar" });
    await user.click(deactivateBtn);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    // Comprobar que aclara que los turnos ya dados no cambian
    expect(
      screen.getByText("Los turnos ya dados no cambian."),
    ).toBeInTheDocument();

    // Pulsar "Volver"
    const backBtn = screen.getByRole("button", { name: "Volver" });
    await user.click(backBtn);

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    // Debe haberse cerrado sin ninguna petición POST
    expect(postDeactivateCalls).toBe(0);

    // Paso 2: Pulsar de nuevo "Desactivar" y luego "Sí, desactivar"
    const deactivateBtn2 = screen.getByRole("button", { name: "Desactivar" });
    await user.click(deactivateBtn2);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole("button", { name: "Sí, desactivar" });
    await user.click(confirmBtn);

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    expect(postDeactivateCalls).toBe(1);
    await waitFor(() => {
      expect(screen.getByText("Inactivo")).toBeInTheDocument();
    });
    expect(screen.getByRole("status")).toHaveTextContent("Sillón desactivado.");
  });

  it("Reactivar una prestación inactiva", async () => {
    const user = userEvent.setup();
    let postReactivateCalled = false;
    let isServiceActive = false;

    const fetchFn: FetchFn = async (url, init) => {
      if (url.includes("/services/srv-1/reactivate") && init?.method === "POST") {
        postReactivateCalled = true;
        isServiceActive = true;
        return new Response(
          JSON.stringify({
            id: "srv-1",
            name: "Blanqueamiento",
            defaultDurationMin: 60,
            active: true,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/services") && (!init?.method || init.method === "GET")) {
        return new Response(
          JSON.stringify([
            {
              id: "srv-1",
              name: "Blanqueamiento",
              defaultDurationMin: 60,
              active: isServiceActive,
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderCatalogos(fetchFn, "/catalogos?seccion=prestaciones");

    await waitFor(() => {
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    const reactivateBtn = screen.getByRole("button", { name: "Reactivar" });
    await user.click(reactivateBtn);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole("button", { name: "Sí, reactivar" });
    await user.click(confirmBtn);

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    expect(postReactivateCalled).toBe(true);
    await waitFor(() => {
      expect(screen.getByText("Activo")).toBeInTheDocument();
    });
    expect(screen.getByRole("status")).toHaveTextContent("Prestación reactivada.");
  });
});
