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

  it("los campos del login conservan la superficie oscura cuando el navegador los autocompleta", () => {
    const css = readSrcFile("features/login/LoginPage.module.css");
    const webkit = ruleBody(
      css,
      ".input:-webkit-autofill, .input:-webkit-autofill:hover, .input:-webkit-autofill:focus",
    );
    const standard = ruleBody(css, ".input:autofill");

    for (const rule of [webkit, standard]) {
      expect(rule).toContain("box-shadow: 0 0 0 1000px var(--color-navy-deep) inset;");
      expect(rule).toContain("-webkit-text-fill-color: var(--color-primary-contrast);");
      expect(rule).toContain("caret-color: var(--color-primary-contrast);");
      expect(rule).toMatch(/transition:\s+background-color\s+\d{4,}s\b/);
    }
    // El aspecto de foco (línea fina y contorno) sigue declarado aparte y sin cambios.
    expect(ruleBody(css, ".input:focus-visible")).toContain("border-color: var(--color-accent);");
    expect(readSrcFile("shared/styles/tokens.css")).toMatch(/--color-navy-deep:\s*#011C40;/);
  });

  it("el alerta de error del login usa la variante oscura con contraste AA sobre la superficie translúcida y el fallback", async () => {
    const user = userEvent.setup();
    const fetchFn: FetchFn = async () =>
      jsonResponse({ code: "INVALID_CREDENTIALS", message: "Usuario o contraseña incorrectos." }, 401);
    renderLogin("/login", createMemoryTokenStore(), fetchFn);

    await user.type(screen.getByLabelText("Usuario"), "recepcion");
    await user.type(screen.getByLabelText("Contraseña"), "<contraseña de prueba>");
    await user.click(screen.getByRole("button", { name: "Ingresar" }));
    await waitFor(() => {
      expect(screen.queryByRole("alert")).toHaveTextContent("Usuario o contraseña incorrectos.");
    });
    const alert = screen.queryByRole("alert");
    expect(alert).toHaveAttribute("aria-live", "polite");
    expect(alert).toHaveClass("alert");

    const css = readSrcFile("features/login/LoginPage.module.css");
    const rule = ruleBody(css, ".alert");
    expect(rule).toContain("background: var(--alert-on-navy-bg);");
    expect(rule).toContain("border: 1px solid var(--alert-on-navy-border);");
    expect(rule).toContain("color: var(--alert-on-navy-text);");

    const tokens = readSrcFile("shared/styles/tokens.css");
    const tokenValue = (name: string): string => new RegExp(`${name}:\\s*([^;]+);`).exec(tokens)?.[1]?.trim() ?? "";
    const text = parseRgb(tokenValue("--alert-on-navy-text"));
    const alertBg = parseRgba(tokenValue("--alert-on-navy-bg"));
    const surface = parseRgba(tokenValue("--surface-navy"));
    expect(text).not.toBeNull();
    expect(alertBg).not.toBeNull();
    expect(surface).not.toBeNull();
    if (text === null || alertBg === null || surface === null) {
      return;
    }
    // Peor caso de la superficie translúcida: la tarjeta sobre una foto blanca; fallback sólido: #011C40.
    const overTranslucent = composite(alertBg, composite(surface, { rgb: [255, 255, 255], alpha: 1 }));
    const overFallback = composite(alertBg, parseRgba(`rgba(1, 28, 64, 1)`) ?? alertBg);
    expect(contrastOf(text, overTranslucent.rgb)).toBeGreaterThanOrEqual(4.5);
    expect(contrastOf(text, overFallback.rgb)).toBeGreaterThanOrEqual(4.5);
    expect(contrastOf(text, overTranslucent.rgb).toFixed(2)).toBe("7.58");
    expect(contrastOf(text, overFallback.rgb).toFixed(2)).toBe("9.86");
  });
});

type Rgb = readonly [number, number, number];
interface Rgba {
  readonly rgb: Rgb;
  readonly alpha: number;
}

function parseRgb(value: string): Rgb | null {
  const hex = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(value);
  if (hex === null) {
    return null;
  }
  return [parseInt(hex[1] ?? "0", 16), parseInt(hex[2] ?? "0", 16), parseInt(hex[3] ?? "0", 16)];
}

function parseRgba(value: string): Rgba | null {
  const match = /^rgba\(\s*(\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)$/.exec(value);
  if (match === null) {
    return null;
  }
  return { rgb: [Number(match[1]), Number(match[2]), Number(match[3])], alpha: Number(match[4]) };
}

function composite(top: Rgba, bottom: Rgba): Rgba {
  const mix = (index: 0 | 1 | 2): number => top.rgb[index] * top.alpha + bottom.rgb[index] * (1 - top.alpha);
  return { rgb: [mix(0), mix(1), mix(2)], alpha: 1 };
}

function luminanceOf(rgb: Rgb): number {
  const channel = (value: number): number => {
    const ratio = value / 255;
    return ratio <= 0.03928 ? ratio / 12.92 : ((ratio + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2]);
}

function contrastOf(foreground: Rgb, background: Rgb): number {
  const a = luminanceOf(foreground);
  const b = luminanceOf(background);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}
