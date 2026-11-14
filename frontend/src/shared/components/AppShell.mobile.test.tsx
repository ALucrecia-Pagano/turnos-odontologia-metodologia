import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AuthProvider } from "../../features/auth/AuthContext";
import { createMemoryTokenStore } from "../../features/auth/tokenStore";
import { createApiClient, type FetchFn } from "../api/client";
import type { CurrentUser } from "../api/types";
import { AppShell } from "./AppShell";

const RECEPCION_USER: CurrentUser = {
  id: "00000000-0000-0000-0000-0000000000e2",
  username: "recepcion",
  displayName: "Recepción Demo",
  role: "recepcion",
  professionalId: null,
};

function renderMobileShell(currentUser: CurrentUser = RECEPCION_USER) {
  const tokenStore = createMemoryTokenStore("token-mobile-123");
  const fetchFn: FetchFn = async () =>
    new Response(JSON.stringify(currentUser), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

  return render(
    <MemoryRouter initialEntries={["/agenda"]}>
      <AuthProvider tokenStore={tokenStore} client={client}>
        <AppShell isMobile={true}>
          <p>Contenido móvil</p>
        </AppShell>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("AppShell — Móvil (≤ 640 px)", () => {
  it("01-cabecera-compacta-y-apertura-menu: expone botón Menú fuera de nav con aria-expanded y aria-controls, y al pulsar despliega la navegación", async () => {
    const user = userEvent.setup();
    renderMobileShell();

    // Esperar a que cargue el usuario
    await screen.findByText("Recepción Demo");

    // El botón Menú debe existir en el header y estar fuera de <nav>
    const menuButton = screen.getByRole("button", { name: "Menú" });
    expect(menuButton).toBeInTheDocument();
    expect(menuButton).toHaveAttribute("aria-expanded", "false");
    expect(menuButton).toHaveAttribute("aria-controls", "main-menu");

    const nav = document.getElementById("main-menu");
    expect(nav).not.toBeNull();
    expect(nav?.tagName.toLowerCase()).toBe("nav");
    expect(nav?.querySelector("a[data-menu-item='Agenda']")).not.toBeNull();
    // El botón Menú NO debe estar contenido dentro de <nav> (para no romper AppShell.test.tsx)
    expect(nav?.contains(menuButton)).toBe(false);

    // Con el menú cerrado en móvil, el nav está oculto de verdad (hidden)
    expect(nav).toHaveAttribute("hidden");

    // Al pulsar el botón Menú, se despliega
    await user.click(menuButton);
    expect(menuButton).toHaveAttribute("aria-expanded", "true");
    expect(nav).not.toHaveAttribute("hidden");
  });

  it("02-cierre-menu-escape-y-retorno-foco: presionar Escape cierra el menú desplegado y devuelve el foco al botón Menú", async () => {
    const user = userEvent.setup();
    renderMobileShell();

    await screen.findByText("Recepción Demo");
    const menuButton = screen.getByRole("button", { name: "Menú" });
    const nav = document.getElementById("main-menu");

    // Abrir menú
    await user.click(menuButton);
    expect(menuButton).toHaveAttribute("aria-expanded", "true");
    expect(nav).not.toHaveAttribute("hidden");

    // Mover foco a un elemento interactivo dentro del menú
    const agendaLink = screen.getByRole("link", { name: "Agenda" });
    agendaLink.focus();
    expect(document.activeElement).toBe(agendaLink);

    // Presionar Escape
    await user.keyboard("{Escape}");

    // El menú debe cerrarse y el foco debe retornar al botón Menú
    expect(menuButton).toHaveAttribute("aria-expanded", "false");
    expect(nav).toHaveAttribute("hidden");
    expect(document.activeElement).toBe(menuButton);
  });
});
