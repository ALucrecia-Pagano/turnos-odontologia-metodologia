import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider, useLocation, type RouteObject } from "react-router-dom";
import { App, routes } from "./App";
import { AuthProvider, useAuth } from "./features/auth/AuthContext";
import { createMemoryTokenStore } from "./features/auth/tokenStore";
import { createApiClient, type FetchFn } from "./shared/api/client";

const RECEPCION_USER = {
  id: "00000000-0000-0000-0000-0000000000e2",
  username: "recepcion",
  displayName: "Recepción Demo",
  role: "recepcion" as const,
  professionalId: null,
};

function createAuthenticatedClient(): ReturnType<typeof createApiClient> {
  const fetchFn: FetchFn = async () =>
    new Response(JSON.stringify(RECEPCION_USER), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  return createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
}

function ProtectedTriggerPage() {
  const { client } = useAuth();
  const location = useLocation();
  return (
    <div>
      <p data-testid="current-path">{`${location.pathname}${location.search}`}</p>
      <button
        type="button"
        onClick={() => {
          void client.request("/agenda");
        }}
      >
        Consultar agenda
      </button>
    </div>
  );
}

describe("App con router y guards de sesión", () => {
  afterEach(() => {
    window.history.pushState({}, "", "/");
  });

  it("la ruta raíz renderiza el HomePage de bienvenida", async () => {
    window.history.pushState({}, "", "/");
    const tokenStore = createMemoryTokenStore("token-ficticio-123");
    render(<App tokenStore={tokenStore} client={createAuthenticatedClient()} />);

    await waitFor(() => {
      expect(screen.queryByRole("main")).toHaveTextContent("Bienvenida");
    });
    expect(screen.queryByRole("heading", { level: 1, name: "Turnos Odontología" })).toBeInTheDocument();
    const statuses = within(screen.getByRole("list", { name: "Estados de un turno" })).getAllByRole("listitem");
    expect(statuses.map((item) => item.textContent)).toEqual([
      "Reservado",
      "Confirmado",
      "Atendido",
      "Ausente",
      "Cancelado",
    ]);
  });

  it("una ruta desconocida muestra la página de no encontrada", async () => {
    window.history.pushState({}, "", "/ruta-que-no-existe");
    const tokenStore = createMemoryTokenStore("token-ficticio-123");
    render(<App tokenStore={tokenStore} client={createAuthenticatedClient()} />);

    await waitFor(() => {
      expect(screen.queryByRole("heading", { level: 1, name: "Página no encontrada" })).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: "Volver al inicio" })).toHaveAttribute("href", "/");
  });

  it("ruta protegida sin sesión conserva el destino", async () => {
    const tokenStore = createMemoryTokenStore();
    const router = createMemoryRouter(routes, {
      initialEntries: ["/agenda?date=2026-11-07"],
    });

    render(
      <AuthProvider tokenStore={tokenStore} client={createAuthenticatedClient()}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/login");
    });
    expect(router.state.historyAction).toBe("REPLACE");
    expect(router.state.location.state).toEqual({
      from: "/agenda?date=2026-11-07",
      expired: false,
    });
  });

  it("login con sesión vuelve al destino válido", async () => {
    const tokenStore = createMemoryTokenStore("token-ficticio-123");
    const router = createMemoryRouter(routes, {
      initialEntries: [{ pathname: "/login", state: { from: "/agenda?date=2026-11-07" } }],
    });

    render(
      <AuthProvider tokenStore={tokenStore} client={createAuthenticatedClient()}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(`${router.state.location.pathname}${router.state.location.search}`).toBe("/agenda?date=2026-11-07");
    });
    expect(screen.queryByRole("form", { name: "Iniciar sesión" })).not.toBeInTheDocument();
  });

  it("sin parpadeo de login a home", () => {
    const tokenStore = createMemoryTokenStore("token-ficticio-123");
    const pendingFetch: FetchFn = () => new Promise<Response>(() => {});
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn: pendingFetch });
    const router = createMemoryRouter(routes, {
      initialEntries: ["/login"],
    });

    render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    expect(screen.queryByRole("status")).toHaveTextContent("Cargando...");
    expect(screen.queryByRole("form", { name: "Iniciar sesión" })).not.toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
  });

  it("token vencido en una request protegida", async () => {
    const user = userEvent.setup();
    const tokenStore = createMemoryTokenStore("token-ficticio-123");
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(JSON.stringify(RECEPCION_USER), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(
        JSON.stringify({
          code: "INVALID_TOKEN",
          message: "La sesión venció o no es válida. Inicie sesión de nuevo.",
        }),
        { status: 401, headers: { "Content-Type": "application/json" } },
      );
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const testRoutes: RouteObject[] = [
      ...routes.slice(0, 1),
      {
        path: "/",
        element: routes[1]?.element,
        children: [{ path: "agenda", element: <ProtectedTriggerPage /> }],
      },
    ];
    const router = createMemoryRouter(testRoutes, {
      initialEntries: ["/agenda?date=2026-11-07"],
    });

    render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByTestId("current-path")).toHaveTextContent("/agenda?date=2026-11-07");
    });

    await user.click(screen.getByRole("button", { name: "Consultar agenda" }));

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/login");
    });
    expect(tokenStore.getToken()).toBeNull();
    expect(router.state.historyAction).toBe("REPLACE");
    expect(router.state.location.state).toEqual({
      from: "/agenda?date=2026-11-07",
      expired: true,
    });
    expect(screen.queryByRole("alert")).toHaveTextContent("La sesión venció. Iniciá sesión de nuevo.");
  });
});
