import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { createAppRoutes } from "../../App";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { readSrcFile, ruleBody } from "../../test/cssText";
import { createFixedClock } from "../agenda/clock";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";

function renderAcceso() {
  const fetchFn: FetchFn = async () => new Response(null, { status: 401 });
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
  const router = createMemoryRouter(createAppRoutes(createFixedClock("2026-11-16T12:00:00Z")), {
    initialEntries: ["/acceso"],
  });

  const view = render(
    <AuthProvider tokenStore={createMemoryTokenStore()} client={client}>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </AuthProvider>,
  );
  return { router, ...view };
}

describe("AccesoPage", () => {
  it("navegación desde las tres tarjetas de rol hacia login", async () => {
    const { router } = renderAcceso();

    await waitFor(() => {
      expect(screen.queryByRole("heading", { level: 1, name: "¿Cómo querés ingresar?" })).toBeInTheDocument();
    });
    expect(router.state.location.pathname).toBe("/acceso");

    expect(screen.queryByRole("link", { name: "Recepción" })).toHaveAttribute("href", "/login?rol=recepcion");
    expect(screen.queryByRole("link", { name: "Odontología" })).toHaveAttribute("href", "/login?rol=odontologo");
    expect(screen.queryByRole("link", { name: "Administración" })).toHaveAttribute(
      "href",
      "/login?rol=administrador",
    );
    expect(screen.queryByText("El rol se confirma al ingresar")).toBeInTheDocument();

    const css = readSrcFile("features/landing/AccesoPage.module.css");
    const card = ruleBody(css, ".card");
    expect(card).toContain("background: var(--surface-navy);");
    expect(card).toContain("border: 1px solid var(--border-on-navy);");
    expect(ruleBody(css, ".card:hover, .card:focus-visible")).toContain("border-color: var(--color-accent);");
  });

  it("navegación de retorno con el enlace Volver a Aqua", async () => {
    const user = userEvent.setup();
    const { router } = renderAcceso();

    await waitFor(() => {
      expect(screen.queryByRole("link", { name: "← Volver a Aqua" })).toBeInTheDocument();
    });
    const back = screen.queryByRole("link", { name: "← Volver a Aqua" });
    if (back !== null) {
      await user.click(back);
    }

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/");
    });
    const heading = screen.queryByRole("heading", { level: 1, name: "Aqua — Clínica Odontológica" });
    expect(heading).toBeInTheDocument();
    if (heading !== null) {
      expect(within(document.body).queryByText("Claridad en cada cuidado.")).toBeInTheDocument();
    }

    const backRule = ruleBody(readSrcFile("features/landing/AccesoPage.module.css"), ".backLink");
    expect(backRule).not.toBe("");
    expect(backRule).not.toMatch(/(^|[\s;])(border|background|box-shadow)(-[a-z]+)*\s*:/);
  });
});
