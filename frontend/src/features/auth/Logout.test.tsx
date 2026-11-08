import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { routes } from "../../App";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { AuthProvider, useAuth } from "./AuthContext";
import { createMemoryTokenStore } from "./tokenStore";

const RECEPCION_USER = {
  id: "00000000-0000-0000-0000-0000000000e2",
  username: "recepcion",
  displayName: "Recepción Demo",
  role: "recepcion" as const,
  professionalId: null,
};

function AuthStateProbe() {
  const { status, user, lastEvent } = useAuth();
  return (
    <div hidden>
      <span data-testid="probe-status">{status}</span>
      <span data-testid="probe-user">{user?.username ?? "null"}</span>
      <span data-testid="probe-last-event">{lastEvent ?? "null"}</span>
    </div>
  );
}

describe("Logout", () => {
  it("cerrar sesión desde el shell descarta token y usuario y navega a /login con replace", async () => {
    const user = userEvent.setup();
    const tokenStore = createMemoryTokenStore("token-recepcion-123");
    const requestedUrls: string[] = [];
    const fetchFn: FetchFn = async (url) => {
      requestedUrls.push(url);
      return new Response(JSON.stringify(RECEPCION_USER), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(routes, {
      initialEntries: ["/"],
      future: {
        v7_relativeSplatPath: true,
        v7_fetcherPersist: true,
        v7_normalizeFormMethod: true,
        v7_partialHydration: true,
        v7_skipActionErrorRevalidation: true,
      },
    });

    render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <AuthStateProbe />
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByText("Recepción Demo")).toBeInTheDocument();
    });

    const logoutButton = screen.queryByRole("button", { name: "Cerrar sesión" });
    expect(logoutButton).toBeInTheDocument();
    if (logoutButton !== null) {
      await user.click(logoutButton);
    }

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/login");
    });
    expect(router.state.historyAction).toBe("REPLACE");
    expect(tokenStore.getToken()).toBeNull();
    expect(screen.queryByTestId("probe-status")).toHaveTextContent("anonymous");
    expect(screen.queryByTestId("probe-user")).toHaveTextContent("null");
    expect(screen.queryByTestId("probe-last-event")).toHaveTextContent("manual");
    expect(requestedUrls).toEqual(["http://localhost:8000/api/auth/me"]);
    expect(screen.queryByRole("form", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
