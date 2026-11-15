import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AuthProvider } from "../../features/auth/AuthContext";
import { createMemoryTokenStore } from "../../features/auth/tokenStore";
import { createApiClient, type FetchFn } from "../api/client";
import type { CurrentUser, UserRole } from "../api/types";
import { AppShell } from "./AppShell";

function renderAppShellWithUser(role: UserRole) {
  const user: CurrentUser = {
    id: `user-${role}`,
    username: role,
    displayName: `${role} Demo`,
    role,
    professionalId: role === "odontologo" ? "prof-1" : null,
  };

  const tokenStore = createMemoryTokenStore(`token-${role}`);
  const fetchFn: FetchFn = async (url) => {
    if (url.endsWith("/auth/me")) {
      return new Response(JSON.stringify(user), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    return new Response("Not found", { status: 404 });
  };
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

  return render(
    <MemoryRouter
      initialEntries={["/agenda"]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <AuthProvider tokenStore={tokenStore} client={client}>
        <AppShell>
          <p>Contenido principal</p>
        </AppShell>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("AppShellCatalogosPacientes", () => {
  it("Catálogos y Pacientes habilitados para los tres roles", async () => {
    const roles: UserRole[] = ["administrador", "recepcion", "odontologo"];

    for (const role of roles) {
      const view = renderAppShellWithUser(role);

      await waitFor(() => {
        expect(screen.getByRole("navigation", { name: "Menú principal" })).toBeInTheDocument();
      });

      const nav = screen.getByRole("navigation", { name: "Menú principal" });

      const linkCatalogos = within(nav).queryByRole("link", { name: "Catálogos" });
      expect(linkCatalogos, `Catálogos debe ser un enlace para ${role}`).not.toBeNull();
      expect(linkCatalogos).toHaveAttribute("href", "/catalogos");

      const linkPacientes = within(nav).queryByRole("link", { name: "Pacientes" });
      expect(linkPacientes, `Pacientes debe ser un enlace para ${role}`).not.toBeNull();
      expect(linkPacientes).toHaveAttribute("href", "/pacientes");

      expect(within(nav).queryByRole("button", { name: /Catálogos/ })).toBeNull();
      expect(within(nav).queryByRole("button", { name: /Pacientes/ })).toBeNull();

      view.unmount();
    }
  });
});
