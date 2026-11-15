import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient, type FetchFn } from "../../shared/api/client";

function renderRoute(path: string, fetchFn: FetchFn) {
  const tokenStore = createMemoryTokenStore("token-test");
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
  const router = createMemoryRouter(createAppRoutes(), {
    initialEntries: [path],
  });
  return render(
    <AuthProvider tokenStore={tokenStore} client={client}>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
}

describe("CatalogosPacientesRoutes", () => {
  it("Pacientes y Catálogos con su título y un único h1", async () => {
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e1",
            username: "administrador",
            displayName: "Administrador Demo",
            role: "administrador",
            professionalId: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients")) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url.includes("/professionals")) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response("Not found", { status: 404 });
    };

    // Render 1: /pacientes
    const viewPacientes = renderRoute("/pacientes", fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    });

    const h1Pacientes = screen.getAllByRole("heading", { level: 1 });
    expect(h1Pacientes).toHaveLength(1);
    expect(h1Pacientes[0]).toHaveTextContent("Pacientes");

    // PageShell header contains "Pacientes"
    const pageShellHeaderPacientes = viewPacientes.container.querySelector("div[class*='shell'] header");
    expect(pageShellHeaderPacientes).toHaveTextContent("Pacientes");

    viewPacientes.unmount();

    // Render 2: /catalogos
    const viewCatalogos = renderRoute("/catalogos", fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    });

    const h1Catalogos = screen.getAllByRole("heading", { level: 1 });
    expect(h1Catalogos).toHaveLength(1);
    expect(h1Catalogos[0]).toHaveTextContent("Catálogos");

    // PageShell header contains "Catálogos"
    const pageShellHeaderCatalogos = viewCatalogos.container.querySelector("div[class*='shell'] header");
    expect(pageShellHeaderCatalogos).toHaveTextContent("Catálogos");
  });
});
