import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider } from "../../features/auth/AuthContext";
import { createMemoryTokenStore } from "../../features/auth/tokenStore";
import { createApiClient, type FetchFn } from "../api/client";
import type { CurrentUser } from "../api/types";
import { AppShell } from "./AppShell";

function renderAppShell(currentUser: CurrentUser) {
  const tokenStore = createMemoryTokenStore("token-ficticio-123");
  const fetchFn: FetchFn = async () =>
    new Response(JSON.stringify(currentUser), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
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

const ADMIN: CurrentUser = {
  id: "00000000-0000-0000-0000-0000000000e1",
  username: "administrador",
  displayName: "Administrador Demo",
  role: "administrador",
  professionalId: null,
};

describe("AppShell brand", () => {
  it("muestra una sola barra con logo decorativo, Aqua y Clínica Odontológica", async () => {
    const { container } = renderAppShell(ADMIN);

    await waitFor(() => {
      expect(screen.queryByRole("navigation", { name: "Menú principal" })).toBeInTheDocument();
    });

    const bars = container.querySelectorAll("header");
    expect(bars).toHaveLength(1);
    const bar = bars[0];
    if (bar === undefined) {
      throw new Error("No se renderizó la barra");
    }

    const logo = bar.querySelector('img[alt=""]');
    expect(logo).not.toBeNull();
    expect(logo?.getAttribute("src")).toContain("isotipo-aqua");
    expect(logo?.getAttribute("src")).not.toContain("logo-aqua-oscuro");
    expect(within(bar).getByText("Aqua")).toBeInTheDocument();
    expect(within(bar).getByText("Clínica Odontológica")).toBeInTheDocument();

    const nav = within(bar).getByRole("navigation", { name: "Menú principal" });
    expect(nav.contains(within(bar).getByText("Aqua"))).toBe(false);
  });

  it("ubica logo, Aqua y subtítulo en la marca y el subtítulo usa la clase oculta en 768 px", async () => {
    const { container } = renderAppShell(ADMIN);

    await waitFor(() => {
      expect(screen.queryByRole("navigation", { name: "Menú principal" })).toBeInTheDocument();
    });

    const brand = container.querySelector('[data-brand="aqua"]');
    expect(brand).not.toBeNull();
    if (brand === null) {
      throw new Error("No se renderizó la marca");
    }

    const logo = brand.querySelector('img[alt=""]');
    const name = within(brand as HTMLElement).getByText("Aqua");
    const subtitle = within(brand as HTMLElement).getByText("Clínica Odontológica");

    expect(logo).not.toBeNull();
    expect(name).toBeInTheDocument();
    expect(subtitle).toHaveClass("brandSubtitle");
  });
});
