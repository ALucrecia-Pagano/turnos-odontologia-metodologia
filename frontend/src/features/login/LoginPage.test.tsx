import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import type { CurrentUser } from "../../shared/api/types";
import { AuthProvider, useAuth } from "../auth/AuthContext";
import { PublicOnlyRoute } from "../auth/PublicOnlyRoute";
import { RequireAuth } from "../auth/RequireAuth";
import { createMemoryTokenStore, type TokenStore } from "../auth/tokenStore";
import { LoginPage } from "./LoginPage";

const ADMIN_USER: CurrentUser = {
  id: "00000000-0000-0000-0000-0000000000e1",
  username: "administrador",
  displayName: "Administración Demo",
  role: "administrador",
  professionalId: null,
};

const RECEPCION_USER: CurrentUser = {
  id: "00000000-0000-0000-0000-0000000000e2",
  username: "recepcion",
  displayName: "Recepción Demo",
  role: "recepcion",
  professionalId: null,
};

const ODONTOLOGO_USER: CurrentUser = {
  id: "00000000-0000-0000-0000-0000000000e3",
  username: "odontologo",
  displayName: "Dra. Laura Quiroga",
  role: "odontologo",
  professionalId: "00000000-0000-0000-0000-000000000001",
};

function ProtectedHomeProbe() {
  const { user } = useAuth();
  return (
    <main>
      <p data-testid="authenticated-name">{user?.displayName ?? ""}</p>
      <p data-testid="authenticated-role">{user?.role ?? ""}</p>
      <p data-testid="authenticated-professional">{user?.professionalId ?? "null"}</p>
    </main>
  );
}

function renderLoginRouter(tokenStore: TokenStore, fetchFn: FetchFn) {
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
  const router = createMemoryRouter(
    [
      {
        path: "/login",
        element: <PublicOnlyRoute />,
        children: [{ index: true, element: <LoginPage /> }],
      },
      {
        path: "/",
        element: <RequireAuth />,
        children: [{ index: true, element: <ProtectedHomeProbe /> }],
      },
    ],
    { initialEntries: ["/login"] },
  );

  const view = render(
    <AuthProvider tokenStore={tokenStore} client={client}>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </AuthProvider>,
  );

  return { router, ...view };
}

describe("LoginPage", () => {
  it("login correcto del administrador", async () => {
    const user = userEvent.setup();
    const tokenStore = createMemoryTokenStore();
    const calls: { url: string; method: string; bodyText: string | undefined }[] = [];
    const fetchFn: FetchFn = async (url, init) => {
      calls.push({
        url,
        method: init?.method ?? "GET",
        bodyText: typeof init?.body === "string" ? init.body : undefined,
      });
      if (url.endsWith("/auth/login")) {
        return new Response(JSON.stringify({ accessToken: "token-admin-123", tokenType: "bearer" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify(ADMIN_USER), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    const { router } = renderLoginRouter(tokenStore, fetchFn);

    await user.type(screen.getByLabelText("Usuario"), "administrador");
    await user.type(screen.getByLabelText("Contraseña"), "<contraseña de prueba>");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/");
    });
    expect(calls).toHaveLength(2);
    expect(calls[0]).toEqual({
      url: "http://localhost:8000/api/auth/login",
      method: "POST",
      bodyText: JSON.stringify({ username: "administrador", password: "<contraseña de prueba>" }),
    });
    expect(calls[1]?.url).toBe("http://localhost:8000/api/auth/me");
    expect(tokenStore.getToken()).toBe("token-admin-123");
    expect(screen.queryByTestId("authenticated-name")).toHaveTextContent("Administración Demo");
    expect(screen.queryByTestId("authenticated-role")).toHaveTextContent("administrador");
  });

  it("login correcto de recepción y del odontólogo", async () => {
    const user = userEvent.setup();

    const recepcionStore = createMemoryTokenStore();
    const recepcionFetch: FetchFn = async (url) => {
      if (url.endsWith("/auth/login")) {
        return new Response(JSON.stringify({ accessToken: "token-recepcion", tokenType: "bearer" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify(RECEPCION_USER), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };
    const { unmount } = renderLoginRouter(recepcionStore, recepcionFetch);

    await user.type(screen.getByLabelText("Usuario"), "recepcion");
    await user.type(screen.getByLabelText("Contraseña"), "<contraseña de prueba>");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));

    await waitFor(() => {
      expect(screen.queryByTestId("authenticated-name")).toHaveTextContent("Recepción Demo");
    });
    expect(screen.queryByTestId("authenticated-role")).toHaveTextContent("recepcion");
    expect(screen.queryByTestId("authenticated-professional")).toHaveTextContent("null");

    unmount();

    const odontologoStore = createMemoryTokenStore();
    const odontologoFetch: FetchFn = async (url) => {
      if (url.endsWith("/auth/login")) {
        return new Response(JSON.stringify({ accessToken: "token-odontologo", tokenType: "bearer" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify(ODONTOLOGO_USER), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };
    renderLoginRouter(odontologoStore, odontologoFetch);

    await user.type(screen.getByLabelText("Usuario"), "odontologo");
    await user.type(screen.getByLabelText("Contraseña"), "<contraseña de prueba>");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));

    await waitFor(() => {
      expect(screen.queryByTestId("authenticated-name")).toHaveTextContent("Dra. Laura Quiroga");
    });
    expect(screen.queryByTestId("authenticated-role")).toHaveTextContent("odontologo");
    expect(screen.queryByTestId("authenticated-professional")).toHaveTextContent(
      "00000000-0000-0000-0000-000000000001",
    );
  });

  it("credenciales inválidas con mensaje genérico", async () => {
    const user = userEvent.setup();
    const tokenStore = createMemoryTokenStore();
    const fetchFn: FetchFn = async () =>
      new Response(
        JSON.stringify({
          code: "INVALID_CREDENTIALS",
          message: "Usuario o contraseña incorrectos.",
        }),
        { status: 401, headers: { "Content-Type": "application/json" } },
      );

    const { router } = renderLoginRouter(tokenStore, fetchFn);

    const usernameInput = screen.getByLabelText("Usuario") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Contraseña") as HTMLInputElement;

    await user.type(usernameInput, "recepcion");
    await user.type(passwordInput, "<contraseña de prueba>");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));

    await waitFor(() => {
      expect(screen.queryByRole("alert")).toHaveTextContent("Usuario o contraseña incorrectos.");
    });
    expect(tokenStore.getToken()).toBeNull();
    expect(router.state.location.pathname).toBe("/login");
    expect(passwordInput.value).toBe("");
    expect(usernameInput.value).toBe("recepcion");
    expect(usernameInput).not.toHaveAttribute("aria-invalid", "true");
    expect(passwordInput).not.toHaveAttribute("aria-invalid", "true");
  });

  it("el 401 del login no es sesión vencida", async () => {
    const user = userEvent.setup();
    const tokenStore = createMemoryTokenStore();
    const fetchFn: FetchFn = async () =>
      new Response(
        JSON.stringify({
          code: "INVALID_CREDENTIALS",
          message: "Usuario o contraseña incorrectos.",
        }),
        { status: 401, headers: { "Content-Type": "application/json" } },
      );

    const { router } = renderLoginRouter(tokenStore, fetchFn);

    await user.type(screen.getByLabelText("Usuario"), "recepcion");
    await user.type(screen.getByLabelText("Contraseña"), "<contraseña de prueba>");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));

    await waitFor(() => {
      expect(screen.queryByRole("alert")).toHaveTextContent("Usuario o contraseña incorrectos.");
    });
    expect(router.state.location.pathname).toBe("/login");
    expect(screen.queryByRole("alert")).not.toHaveTextContent("La sesión venció. Iniciá sesión de nuevo.");
  });

  it("envío en curso y doble submit", async () => {
    const user = userEvent.setup();
    const tokenStore = createMemoryTokenStore();
    let resolveLogin: ((response: Response) => void) | undefined;
    let requestCount = 0;

    const fetchFn: FetchFn = (url) => {
      requestCount += 1;
      if (url.endsWith("/auth/login")) {
        return new Promise<Response>((resolve) => {
          resolveLogin = resolve;
        });
      }
      return Promise.resolve(
        new Response(JSON.stringify(RECEPCION_USER), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    };

    renderLoginRouter(tokenStore, fetchFn);

    await user.type(screen.getByLabelText("Usuario"), "recepcion");
    await user.type(screen.getByLabelText("Contraseña"), "<contraseña de prueba>");

    const submitButton = screen.getByRole("button", { name: "Ingresar" });
    await user.click(submitButton);

    const busyButton = screen.queryByRole("button", { name: "Ingresando…" });
    expect(busyButton).toBeInTheDocument();
    expect(busyButton).toBeDisabled();
    expect(busyButton).toHaveAttribute("aria-busy", "true");

    const form = screen.getByRole("form", { name: "Iniciar sesión" });
    fireEvent.submit(form);
    expect(requestCount).toBe(1);

    resolveLogin?.(
      new Response(JSON.stringify({ accessToken: "token-123", tokenType: "bearer" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await waitFor(() => {
      expect(screen.queryByTestId("authenticated-name")).toHaveTextContent("Recepción Demo");
    });
  });

  it("accesibilidad del formulario", async () => {
    const user = userEvent.setup();
    const tokenStore = createMemoryTokenStore();
    let submitted = 0;
    const fetchFn: FetchFn = async () => {
      submitted += 1;
      return new Response(
        JSON.stringify({
          code: "INVALID_CREDENTIALS",
          message: "Usuario o contraseña incorrectos.",
        }),
        { status: 401, headers: { "Content-Type": "application/json" } },
      );
    };

    renderLoginRouter(tokenStore, fetchFn);

    const usernameInput = screen.queryByLabelText("Usuario");
    const passwordInput = screen.queryByLabelText("Contraseña");

    expect(usernameInput).toBeInTheDocument();
    expect(passwordInput).toBeInTheDocument();
    expect(usernameInput).toHaveAttribute("autocomplete", "username");
    expect(usernameInput).toHaveAttribute("maxlength", "150");
    expect(usernameInput).toBeRequired();
    expect(passwordInput).toHaveAttribute("autocomplete", "current-password");
    expect(passwordInput).toHaveAttribute("type", "password");
    expect(passwordInput).toHaveAttribute("maxlength", "128");
    expect(passwordInput).toBeRequired();
    expect(usernameInput).toHaveFocus();

    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
    expect(screen.queryByText(/recordar/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /ver contraseña|mostrar contraseña/i })).not.toBeInTheDocument();

    await user.keyboard("recepcion{Tab}<contraseña de prueba>{Enter}");

    await waitFor(() => {
      expect(submitted).toBe(1);
    });
    const alert = screen.queryByRole("alert");
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveAttribute("aria-live", "polite");
    expect(alert).toHaveTextContent("Usuario o contraseña incorrectos.");
  });
});
