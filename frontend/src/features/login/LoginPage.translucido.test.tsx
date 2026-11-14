import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import type { CurrentUser } from "../../shared/api/types";
import { readSrcFile, ruleBody } from "../../test/cssText";
import { AuthProvider, useAuth } from "../auth/AuthContext";
import { PublicOnlyRoute } from "../auth/PublicOnlyRoute";
import { RequireAuth } from "../auth/RequireAuth";
import { createMemoryTokenStore, type TokenStore } from "../auth/tokenStore";
import { LoginPage } from "./LoginPage";

const RECEPCION_USER: CurrentUser = {
  id: "00000000-0000-0000-0000-0000000000e2",
  username: "recepcion",
  displayName: "Recepción Demo",
  role: "recepcion",
  professionalId: null,
};

type LoginEntry = string | { pathname: string; state: unknown };

function ProtectedProbe() {
  const { user } = useAuth();
  return <p data-testid="authenticated-name">{user?.displayName ?? ""}</p>;
}

function renderLogin(initialEntry: LoginEntry, tokenStore: TokenStore, fetchFn: FetchFn) {
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
        children: [
          { index: true, element: <ProtectedProbe /> },
          { path: "agenda", element: <ProtectedProbe /> },
        ],
      },
    ],
    { initialEntries: [initialEntry] },
  );

  const view = render(
    <AuthProvider tokenStore={tokenStore} client={client}>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </AuthProvider>,
  );
  return { router, ...view };
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

describe("LoginPage translúcido", () => {
  it("formulario translúcido en /login con etiqueta de rol y envío de credenciales", async () => {
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
        return jsonResponse({ accessToken: "token-recepcion-123", tokenType: "bearer" });
      }
      return jsonResponse(RECEPCION_USER);
    };

    const { router } = renderLogin("/login?rol=recepcion", tokenStore, fetchFn);

    expect(screen.queryByText("Recepción")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "← Volver" })).toHaveAttribute("href", "/acceso");
    expect(screen.queryByRole("img", { name: "Aqua — Clínica Odontológica" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Turnos Odontología" })).toBeInTheDocument();

    const css = readSrcFile("features/login/LoginPage.module.css");
    const card = ruleBody(css, ".card");
    expect(card).toContain("backdrop-filter: blur(");
    expect(card).toContain("background: var(--surface-navy);");
    expect(card).toContain("border: 1px solid var(--border-on-navy);");

    await user.type(screen.getByLabelText("Usuario"), "recepcion");
    await user.type(screen.getByLabelText("Contraseña"), "<contraseña de prueba>");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/");
    });
    expect(calls[0]).toEqual({
      url: "http://localhost:8000/api/auth/login",
      method: "POST",
      bodyText: JSON.stringify({ username: "recepcion", password: "<contraseña de prueba>" }),
    });
    expect(tokenStore.getToken()).toBe("token-recepcion-123");
    expect(screen.queryByTestId("authenticated-name")).toHaveTextContent("Recepción Demo");
  });

  it("parámetro rol inválido o ausente no muestra etiqueta y fallback sólido sin backdrop-filter", async () => {
    const user = userEvent.setup();
    const ROLE_TEXTS = ["Recepción", "Odontología", "Administración", "desconocido"];

    for (const entry of ["/login", "/login?rol=desconocido"]) {
      const fetchFn: FetchFn = async () =>
        jsonResponse({ code: "INVALID_CREDENTIALS", message: "Usuario o contraseña incorrectos." }, 401);
      const { container, unmount } = renderLogin(entry, createMemoryTokenStore(), fetchFn);

      expect(container.querySelector("[data-role-label]")).toBeNull();
      for (const text of ROLE_TEXTS) {
        expect(screen.queryByText(text)).not.toBeInTheDocument();
      }
      expect(screen.queryByRole("link", { name: "← Volver" })).toHaveAttribute("href", "/");

      await user.type(screen.getByLabelText("Usuario"), "recepcion");
      await user.type(screen.getByLabelText("Contraseña"), "<contraseña de prueba>");
      await user.click(screen.getByRole("button", { name: "Ingresar" }));
      await waitFor(() => {
        expect(screen.queryByRole("alert")).toHaveTextContent("Usuario o contraseña incorrectos.");
      });
      unmount();
    }

    const css = readSrcFile("features/login/LoginPage.module.css");
    const fallback = ruleBody(css, ".card", "@supports not (backdrop-filter: blur(1px))");
    expect(fallback).toContain("background: var(--color-navy-deep);");
    expect(readSrcFile("shared/styles/tokens.css")).toMatch(/--color-navy-deep:\s*#011C40;/);
  });

  it("cierre de sesión y preservación del mensaje literal de sesión vencida", async () => {
    const user = userEvent.setup();
    const fetchFn: FetchFn = async (url) =>
      url.endsWith("/auth/login")
        ? jsonResponse({ accessToken: "token-recepcion-456", tokenType: "bearer" })
        : jsonResponse(RECEPCION_USER);

    const { router } = renderLogin(
      { pathname: "/login", state: { expired: true, from: "/agenda?date=2026-11-07" } },
      createMemoryTokenStore(),
      fetchFn,
    );

    const alert = screen.queryByRole("alert");
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveTextContent(/^La sesión venció\. Iniciá sesión de nuevo\.$/);
    expect(screen.queryByLabelText("Usuario")).toHaveFocus();

    await user.type(screen.getByLabelText("Usuario"), "recepcion");
    await user.type(screen.getByLabelText("Contraseña"), "<contraseña de prueba>");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));

    await waitFor(() => {
      expect(`${router.state.location.pathname}${router.state.location.search}`).toBe("/agenda?date=2026-11-07");
    });
    expect(screen.queryByTestId("authenticated-name")).toHaveTextContent("Recepción Demo");
  });
});
