import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { LoadingState } from "../../shared/components/LoadingState";
import { AuthProvider, SESSION_EXPIRED_MESSAGE, useAuth } from "./AuthContext";
import { createMemoryTokenStore } from "./tokenStore";

const ODONTOLOGO_USER = {
  id: "00000000-0000-0000-0000-0000000000e3",
  username: "odontologo",
  displayName: "Dra. Laura Quiroga",
  role: "odontologo" as const,
  professionalId: "00000000-0000-0000-0000-000000000001",
};

function SessionProbe() {
  const { status, user, lastEvent, actionErrors, logout, client } = useAuth();
  if (status === "checking") {
    return <LoadingState />;
  }
  return (
    <div>
      <p data-testid="status">{status}</p>
      <p data-testid="display-name">{user?.displayName ?? "sin-usuario"}</p>
      <p data-testid="role">{user?.role ?? "sin-rol"}</p>
      <p data-testid="professional-id">{user?.professionalId ?? "sin-profesional"}</p>
      <p data-testid="last-event">{lastEvent ?? "ninguno"}</p>
      {lastEvent === "expired" && <p role="alert">{SESSION_EXPIRED_MESSAGE}</p>}
      {actionErrors !== null && actionErrors.length > 0 && (
        <div role="alert">{actionErrors.join(" ")}</div>
      )}
      <button
        type="button"
        onClick={() => {
          void client.request("/appointments");
        }}
      >
        Petición protegida
      </button>
      <button type="button" onClick={logout}>
        Salir
      </button>
    </div>
  );
}

describe("AuthContext", () => {
  it("estado checking mientras se verifica la sesión", () => {
    const tokenStore = createMemoryTokenStore("token-ficticio-123");
    const neverResolvingFetch: FetchFn = () => new Promise<Response>(() => {});
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn: neverResolvingFetch });

    render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <SessionProbe />
      </AuthProvider>,
    );

    expect(screen.queryByRole("status")).toHaveTextContent("Cargando...");
    expect(screen.queryByTestId("status")).not.toBeInTheDocument();
  });

  it("sesión autenticada con el usuario de /me", async () => {
    const tokenStore = createMemoryTokenStore("token-ficticio-123");
    const fetchFn: FetchFn = async () =>
      new Response(JSON.stringify(ODONTOLOGO_USER), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <SessionProbe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByTestId("status")).toHaveTextContent("authenticated");
    });
    expect(screen.queryByTestId("display-name")).toHaveTextContent("Dra. Laura Quiroga");
    expect(screen.queryByTestId("role")).toHaveTextContent("odontologo");
    expect(screen.queryByTestId("professional-id")).toHaveTextContent("00000000-0000-0000-0000-000000000001");
  });

  it("/me responde 401 y limpia la sesión", async () => {
    const tokenStore = createMemoryTokenStore("token-vencido");
    const fetchFn: FetchFn = async () =>
      new Response(
        JSON.stringify({
          code: "INVALID_TOKEN",
          message: "La sesión venció o no es válida. Inicie sesión de nuevo.",
        }),
        { status: 401, headers: { "Content-Type": "application/json" } },
      );
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <SessionProbe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByTestId("status")).toHaveTextContent("anonymous");
    });
    expect(tokenStore.getToken()).toBeNull();
    expect(screen.queryByTestId("last-event")).toHaveTextContent("ninguno");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("error de red en /me conserva el token y permite reintentar", async () => {
    const user = userEvent.setup();
    const tokenStore = createMemoryTokenStore("token-ficticio-123");
    let attempts = 0;
    const fetchFn: FetchFn = async () => {
      attempts += 1;
      if (attempts === 1) {
        throw new Error("Failed to fetch");
      }
      return new Response(JSON.stringify(ODONTOLOGO_USER), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <SessionProbe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByRole("alert")).toBeInTheDocument();
    });
    expect(tokenStore.getToken()).toBe("token-ficticio-123");
    expect(screen.queryByRole("alert")).toHaveTextContent("No se pudo conectar con el servidor. Intentá de nuevo.");

    const retryButton = screen.queryByRole("button", { name: "Reintentar" });
    expect(retryButton).toBeInTheDocument();
    if (retryButton !== null) {
      await user.click(retryButton);
    }

    await waitFor(() => {
      expect(screen.queryByTestId("status")).toHaveTextContent("authenticated");
    });
    expect(screen.queryByTestId("display-name")).toHaveTextContent("Dra. Laura Quiroga");
  });

  it("lastEvent registra expired ante 401 protegido y manual ante logout", async () => {
    const user = userEvent.setup();
    const tokenStore = createMemoryTokenStore("token-ficticio-123");
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(JSON.stringify(ODONTOLOGO_USER), {
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

    const { unmount } = render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <SessionProbe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByTestId("status")).toHaveTextContent("authenticated");
    });

    await user.click(screen.getByRole("button", { name: "Petición protegida" }));

    await waitFor(() => {
      expect(screen.queryByTestId("status")).toHaveTextContent("anonymous");
    });
    expect(tokenStore.getToken()).toBeNull();
    expect(screen.queryByTestId("last-event")).toHaveTextContent("expired");
    expect(screen.queryByRole("alert")).toHaveTextContent("La sesión venció. Iniciá sesión de nuevo.");

    unmount();

    const secondStore = createMemoryTokenStore("token-ficticio-456");
    render(
      <AuthProvider tokenStore={secondStore} client={client}>
        <SessionProbe />
      </AuthProvider>,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("status")).toHaveTextContent("authenticated");
    });

    await user.click(screen.getByRole("button", { name: "Salir" }));
    expect(secondStore.getToken()).toBeNull();
    expect(screen.queryByTestId("status")).toHaveTextContent("anonymous");
    expect(screen.queryByTestId("last-event")).toHaveTextContent("manual");
  });

  it("rol sin permiso muestra la violación ante 403 sin cerrar sesión ni refrescar /me", async () => {
    const user = userEvent.setup();
    const tokenStore = createMemoryTokenStore("token-odontologo-123");
    let meCalls = 0;
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        meCalls += 1;
        return new Response(JSON.stringify(ODONTOLOGO_USER), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
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
      <AuthProvider tokenStore={tokenStore} client={client}>
        <SessionProbe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByTestId("status")).toHaveTextContent("authenticated");
    });
    expect(meCalls).toBe(1);

    await user.click(screen.getByRole("button", { name: "Petición protegida" }));

    await waitFor(() => {
      expect(screen.queryByRole("alert")).toHaveTextContent("No tiene permiso para dar turnos.");
    });
    expect(tokenStore.getToken()).toBe("token-odontologo-123");
    expect(screen.queryByTestId("status")).toHaveTextContent("authenticated");
    expect(meCalls).toBe(1);
  });
});
