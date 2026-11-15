import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient, type FetchFn } from "../../shared/api/client";

function renderCatalogos(fetchFn: FetchFn, initialEntry = "/catalogos") {
  const tokenStore = createMemoryTokenStore("token-test");
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

describe("CatalogosPage", () => {
  it("Profesionales por defecto con estado en texto", async () => {
    const requestedUrls: string[] = [];

    const fetchFn: FetchFn = async (url) => {
      requestedUrls.push(url);
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
      if (url.includes("/professionals")) {
        return new Response(
          JSON.stringify([
            {
              id: "prof-1",
              fullName: "Dra. Laura Quiroga",
              active: true,
              licenseNumber: "MN 1234",
            },
            {
              id: "prof-2",
              fullName: "Dr. Pablo Ferreyra",
              active: false,
              licenseNumber: null,
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    const { unmount } = renderCatalogos(fetchFn, "/catalogos");

    await waitFor(() => {
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    const profLink = screen.getByRole("link", { name: "Profesionales" });
    expect(profLink).toHaveAttribute("aria-current", "page");

    const headers = screen.getAllByRole("columnheader").map((th) => th.textContent);
    expect(headers).toEqual(["Nombre", "Matrícula", "Estado"]);

    const rowQuiroga = screen.getByRole("row", { name: /Dra\. Laura Quiroga/ });
    expect(rowQuiroga).toHaveTextContent("MN 1234");
    expect(rowQuiroga).toHaveTextContent("Activo");

    const rowFerreyra = screen.getByRole("row", { name: /Dr\. Pablo Ferreyra/ });
    expect(rowFerreyra).toHaveTextContent("Sin dato");
    expect(rowFerreyra).toHaveTextContent("Inactivo");

    expect(requestedUrls).toContain("http://localhost:8000/api/professionals");
    expect(requestedUrls.some((u) => u.includes("active="))).toBe(false);

    unmount();

    // Ahora probar con ?seccion=desconocida
    const requestedUrls2: string[] = [];
    const fetchFn2: FetchFn = async (url) => {
      requestedUrls2.push(url);
      return fetchFn(url);
    };

    renderCatalogos(fetchFn2, "/catalogos?seccion=desconocida");

    await waitFor(() => {
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    const profLink2 = screen.getByRole("link", { name: "Profesionales" });
    expect(profLink2).toHaveAttribute("aria-current", "page");
    expect(requestedUrls2).toContain("http://localhost:8000/api/professionals");
    expect(requestedUrls2.some((u) => u.includes("active="))).toBe(false);
  });

  it("Cambio a la sección de prestaciones", async () => {
    const user = userEvent.setup();
    const requestedUrls: string[] = [];

    const fetchFn: FetchFn = async (url) => {
      requestedUrls.push(url);
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
      if (url.includes("/services")) {
        return new Response(
          JSON.stringify([
            {
              id: "srv-1",
              name: "Limpieza",
              defaultDurationMin: 45,
              active: true,
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderCatalogos(fetchFn, "/catalogos");

    await waitFor(() => {
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    const prestacionesLink = screen.getByRole("link", { name: "Prestaciones" });
    await user.click(prestacionesLink);

    await waitFor(() => {
      expect(requestedUrls).toContain("http://localhost:8000/api/services");
    });

    expect(prestacionesLink).toHaveAttribute("aria-current", "page");

    const headers = screen.getAllByRole("columnheader").map((th) => th.textContent);
    expect(headers).toEqual(["Nombre", "Duración (min)", "Estado"]);

    const rowLimpieza = screen.getByRole("row", { name: /Limpieza/ });
    expect(rowLimpieza).toHaveTextContent("45");
    expect(rowLimpieza).toHaveTextContent("Activo");
  });

  it("Recepción y odontólogo consultan catálogos en solo lectura", async () => {
    const chairs = [
      { id: "chair-1", name: "Sillón 1", active: true },
      { id: "chair-2", name: "Sillón 2", active: false },
    ];

    const makeFetchFn = (role: "recepcion" | "odontologo"): FetchFn => {
      return async (url) => {
        if (url.endsWith("/auth/me")) {
          return new Response(
            JSON.stringify({
              id: "00000000-0000-0000-0000-0000000000e2",
              username: role,
              displayName: `${role} Demo`,
              role,
              professionalId: null,
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        if (url.includes("/chairs")) {
          return new Response(JSON.stringify(chairs), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response("Not found", { status: 404 });
      };
    };

    // Caso 1: recepcion
    const { unmount } = renderCatalogos(makeFetchFn("recepcion"), "/catalogos?seccion=sillones");

    await waitFor(() => {
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    expect(screen.queryByText("Solo lectura")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Nuevo sillón" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Editar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Desactivar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reactivar" })).not.toBeInTheDocument();

    unmount();

    // Caso 2: odontologo
    renderCatalogos(makeFetchFn("odontologo"), "/catalogos?seccion=sillones");

    await waitFor(() => {
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    expect(screen.queryByText("Solo lectura")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Nuevo sillón" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Editar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Desactivar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reactivar" })).not.toBeInTheDocument();
  });
});
