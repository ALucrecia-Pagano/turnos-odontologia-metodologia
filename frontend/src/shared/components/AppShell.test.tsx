import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider, useAuth } from "../../features/auth/AuthContext";
import { createMemoryTokenStore } from "../../features/auth/tokenStore";
import { createApiClient, type FetchFn } from "../api/client";
import type { CurrentUser } from "../api/types";
import { AppShell } from "./AppShell";

function renderAppShellForUser(currentUser: CurrentUser) {
  const tokenStore = createMemoryTokenStore("token-ficticio-123");
  const fetchFn: FetchFn = async () =>
    new Response(JSON.stringify(currentUser), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider tokenStore={tokenStore} client={client}>
        <AppShell>
          <p>Contenido principal</p>
        </AppShell>
      </AuthProvider>
    </MemoryRouter>,
  );
}

function ForbiddenActionButton() {
  const { client } = useAuth();
  return (
    <button
      type="button"
      onClick={() => {
        void client.request("/appointments", { method: "POST" });
      }}
    >
      Dar turno
    </button>
  );
}

describe("AppShell", () => {
  it("renderiza el menú del rol con los ítems deshabilitados y la etiqueta Próximamente", async () => {
    const adminView = renderAppShellForUser({
      id: "00000000-0000-0000-0000-0000000000e1",
      username: "administrador",
      displayName: "Administrador Demo",
      role: "administrador",
      professionalId: null,
    });

    await waitFor(() => {
      expect(screen.queryByRole("navigation", { name: "Menú principal" })).toBeInTheDocument();
    });

    const nav = screen.getByRole("navigation", { name: "Menú principal" });
    const adminButtons = within(nav).getAllByRole("button");
    expect(adminButtons).toHaveLength(6);
    expect(adminButtons.map((btn) => btn.getAttribute("data-menu-item"))).toEqual([
      "Agenda",
      "Turnos",
      "Horarios y bloqueos",
      "Catálogos",
      "Pacientes",
      "Usuarios y roles",
    ]);
    for (const button of adminButtons) {
      expect(button).toBeDisabled();
      expect(button).toHaveTextContent("Próximamente");
    }
    expect(screen.queryByText("Administrador Demo")).toBeInTheDocument();
    expect(screen.queryByText("Contenido principal")).toBeInTheDocument();

    adminView.unmount();

    const recepcionView = renderAppShellForUser({
      id: "00000000-0000-0000-0000-0000000000e2",
      username: "recepcion",
      displayName: "Recepción Demo",
      role: "recepcion",
      professionalId: null,
    });

    await waitFor(() => {
      expect(screen.queryByRole("navigation", { name: "Menú principal" })).toBeInTheDocument();
    });
    const recepcionNav = screen.getByRole("navigation", { name: "Menú principal" });
    expect(
      within(recepcionNav)
        .getAllByRole("button")
        .map((btn) => btn.getAttribute("data-menu-item")),
    ).toEqual(["Agenda", "Turnos", "Horarios y bloqueos", "Catálogos", "Pacientes"]);

    recepcionView.unmount();

    renderAppShellForUser({
      id: "00000000-0000-0000-0000-0000000000e3",
      username: "odontologo",
      displayName: "Dra. Laura Quiroga",
      role: "odontologo",
      professionalId: "00000000-0000-0000-0000-000000000001",
    });

    await waitFor(() => {
      expect(screen.queryByRole("navigation", { name: "Menú principal" })).toBeInTheDocument();
    });
    const odontologoNav = screen.getByRole("navigation", { name: "Menú principal" });
    expect(
      within(odontologoNav)
        .getAllByRole("button")
        .map((btn) => btn.getAttribute("data-menu-item")),
    ).toEqual(["Agenda", "Horarios y bloqueos", "Catálogos", "Pacientes"]);
  });

  it("muestra en un alerta del shell la violación de un 403 sin cerrar la sesión", async () => {
    const user = userEvent.setup();
    const tokenStore = createMemoryTokenStore("token-odontologo-123");
    let meCalls = 0;
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        meCalls += 1;
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e3",
            username: "odontologo",
            displayName: "Dra. Laura Quiroga",
            role: "odontologo",
            professionalId: "00000000-0000-0000-0000-000000000001",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(
        JSON.stringify({
          violations: [
            {
              code: "FORBIDDEN_OPERATION",
              message: "No tiene permiso para dar turnos.",
            },
          ],
        }),
        { status: 403, headers: { "Content-Type": "application/json" } },
      );
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AuthProvider tokenStore={tokenStore} client={client}>
          <AppShell>
            <ForbiddenActionButton />
          </AppShell>
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.queryByText("Dra. Laura Quiroga")).toBeInTheDocument();
    });
    expect(meCalls).toBe(1);

    await user.click(screen.getByRole("button", { name: "Dar turno" }));

    await waitFor(() => {
      expect(screen.queryByRole("alert")).toHaveTextContent("No tiene permiso para dar turnos.");
    });
    expect(tokenStore.getToken()).toBe("token-odontologo-123");
    expect(screen.queryByRole("navigation", { name: "Menú principal" })).toBeInTheDocument();
    expect(meCalls).toBe(1);
  });
});
