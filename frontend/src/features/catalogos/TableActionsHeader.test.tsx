import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";

function renderRoute(initialEntry: string, role: string) {
  const tokenStore = createMemoryTokenStore("token-test");
  const fetchFn: FetchFn = async (url) => {
    if (url.endsWith("/auth/me")) {
      return new Response(
        JSON.stringify({
          id: "00000000-0000-0000-0000-0000000000e1",
          username: role,
          displayName: `${role} Demo`,
          role,
          professionalId: null,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url.includes("/patients")) {
      return new Response(
        JSON.stringify([
          {
            id: "p-1",
            fullName: "Ana Pérez",
            dni: "30111222",
            phone: "11-4444-5555",
            healthInsurance: "OSDE",
          },
        ]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url.includes("/professionals")) {
      return new Response(
        JSON.stringify([
          {
            id: "prof-1",
            fullName: "Dra. Laura Quiroga",
            active: true,
            licenseNumber: "MN 1234",
          },
        ]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    return new Response("Not found", { status: 404 });
  };

  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
  const router = createMemoryRouter(createAppRoutes(), {
    initialEntries: [initialEntry],
  });
  return render(
    <AuthProvider tokenStore={tokenStore} client={client}>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
}

describe("TableActionsHeader", () => {
  it("Las tablas tienen encabezado para la columna de acciones", async () => {
    // 1. Pacientes con rol recepcion (canEdit)
    const { unmount: unmountPacientes } = renderRoute("/pacientes", "recepcion");
    await waitFor(() => {
      expect(screen.getByRole("table")).toBeInTheDocument();
    });
    const patientHeaders = screen.getAllByRole("columnheader").map((th) => th.textContent);
    expect(patientHeaders, "La tabla de pacientes debe incluir encabezado Acciones").toContain("Acciones");
    unmountPacientes();

    // 2. Catálogos con rol administrador (isAdmin)
    const { unmount: unmountCatalogos } = renderRoute("/catalogos", "administrador");
    await waitFor(() => {
      expect(screen.getByRole("table")).toBeInTheDocument();
    });
    const catalogHeaders = screen.getAllByRole("columnheader").map((th) => th.textContent);
    expect(catalogHeaders, "La tabla de catálogos debe incluir encabezado Acciones").toContain("Acciones");
    unmountCatalogos();
  });
});
