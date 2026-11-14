import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider } from "../../features/auth/AuthContext";
import { createMemoryTokenStore } from "../../features/auth/tokenStore";
import { readSrcFile, ruleBody } from "../../test/cssText";
import { createApiClient, type FetchFn } from "../api/client";
import type { CurrentUser } from "../api/types";
import { AppShell } from "./AppShell";

const ADMIN_USER: CurrentUser = {
  id: "00000000-0000-0000-0000-0000000000e1",
  username: "administrador",
  displayName: "Administración Demo",
  role: "administrador",
  professionalId: null,
};

const BOX_BACKGROUND = /(^|[\s;])background(-color)?:\s+(?!transparent|none)/;
const BOX_BORDER = /(^|[\s;])border:\s+(?!none|0)/;

function renderShell() {
  const fetchFn: FetchFn = async () =>
    new Response(JSON.stringify(ADMIN_USER), { status: 200, headers: { "Content-Type": "application/json" } });
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

  return render(
    <MemoryRouter initialEntries={["/agenda"]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider tokenStore={createMemoryTokenStore("token-ficticio-123")} client={client}>
        <AppShell>
          <p>Contenido principal</p>
        </AppShell>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("AppShell navegación sin cajas", () => {
  it("enlaces de navegación activos y bloque de sesión en misma línea en 1440 px", async () => {
    const { container } = renderShell();

    await waitFor(() => {
      expect(screen.queryByRole("link", { name: "Agenda" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("link", { name: "Agenda" })).toHaveAttribute("aria-current", "page");

    const bar = container.querySelector("header");
    const nav = screen.queryByRole("navigation", { name: "Menú principal" });
    const brand = container.querySelector('[data-brand="aqua"]');
    const logout = screen.queryByRole("button", { name: "Cerrar sesión" });
    expect(bar).not.toBeNull();
    expect(nav?.parentElement).toBe(bar);
    expect(brand?.parentElement).toBe(bar);
    expect(logout?.parentElement?.parentElement).toBe(bar);
    expect(logout?.parentElement).toHaveTextContent("Administración Demo");
    if (nav !== null) {
      expect(within(nav).queryAllByRole("link")).toHaveLength(1);
    }

    const css = readSrcFile("shared/components/AppShell.module.css");
    const link = ruleBody(css, ".menuLink");
    expect(link).not.toBe("");
    expect(link).not.toMatch(BOX_BACKGROUND);
    expect(link).not.toMatch(BOX_BORDER);
    expect(ruleBody(css, ".menuLinkActive")).toMatch(/border-bottom-color:\s*var\(--color-primary\);/);
    const topBar = ruleBody(css, ".topBar");
    expect(topBar).toContain("display: flex;");
    expect(topBar).toContain("align-items: center;");
  });

  it("ítems deshabilitados con Próximamente conservan semántica y accesibilidad", async () => {
    renderShell();

    await waitFor(() => {
      expect(screen.queryByRole("navigation", { name: "Menú principal" })).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.queryAllByRole("button", { name: /Próximamente/ })).toHaveLength(5);
    });
    const nav = screen.getByRole("navigation", { name: "Menú principal" });
    const buttons = within(nav).getAllByRole("button");
    expect(buttons.map((button) => button.getAttribute("data-menu-item"))).toEqual([
      "Turnos",
      "Horarios y bloqueos",
      "Catálogos",
      "Pacientes",
      "Usuarios y roles",
    ]);
    for (const button of buttons) {
      expect(button).toBeDisabled();
      expect(button).toHaveTextContent("Próximamente");
    }

    const css = readSrcFile("shared/components/AppShell.module.css");
    for (const selector of [".menuButton", ".badge"]) {
      const body = ruleBody(css, selector);
      expect(body, selector).not.toBe("");
      expect(body, selector).not.toMatch(BOX_BORDER);
      expect(body, selector).not.toMatch(BOX_BACKGROUND);
      expect(body, selector).not.toMatch(/border-radius:\s+var\(--radius-pill\)/);
    }
    expect(ruleBody(css, ".badge")).toContain("color: var(--color-text-muted);");
  });
});
