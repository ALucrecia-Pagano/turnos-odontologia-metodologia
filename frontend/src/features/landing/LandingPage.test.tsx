import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createApiClient } from "../../shared/api/client";
import type { ApiResult, CurrentUser } from "../../shared/api/types";
import { AuthProvider, SESSION_EXPIRED_MESSAGE } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { LoginPage } from "../login/LoginPage";
import { demoBadge, demoContactNote, heroLead } from "./landingContent";
import { LandingPage } from "./LandingPage";

const onLogin = async (): Promise<ApiResult<CurrentUser>> => ({
  ok: false,
  status: 500,
  error: { kind: "unknown", status: 500, rawText: "" },
});

describe("LandingPage", () => {
  it("muestra la marca una sola vez, la bajada, el lead y el CTA", () => {
    render(<LandingPage onLogin={onLogin} />);

    const heading = screen.getByRole("heading", { level: 1, name: "Aqua — Clínica Odontológica" });
    expect(heading).toBeInTheDocument();
    expect(screen.getByText("Claridad en cada cuidado.")).toBeVisible();
    expect(screen.getByText(heroLead)).toBeVisible();
    expect(screen.getByRole("button", { name: "Ingresar al sistema" })).toBeVisible();
  });

  it("marca el sitio y los datos de contacto como demostración", () => {
    render(<LandingPage onLogin={onLogin} />);

    expect(screen.getByText(demoBadge)).toBeVisible();
    expect(screen.getByText(demoContactNote)).toBeVisible();
  });

  it("muestra las cuatro secciones informativas visibles sin IntersectionObserver", () => {
    const { container } = render(<LandingPage onLogin={onLogin} />);

    for (const name of ["Quiénes somos", "Servicios", "Equipo", "Horarios y contacto"]) {
      expect(screen.getByRole("heading", { level: 2, name })).toBeVisible();
    }
    expect(container.querySelectorAll('[data-reveal="pending"]')).toHaveLength(0);
  });

  it("reutiliza el carrusel de cinco fotos y su botón de pausa", () => {
    const { container } = render(<LandingPage onLogin={onLogin} />);

    expect(container.querySelectorAll("img[data-slide-index]")).toHaveLength(5);
    expect(screen.getByRole("button", { name: "Pausar animación" })).toBeVisible();
  });

  it("abre el acceso al entrar y lo reabre con el CTA", () => {
    render(<LandingPage onLogin={onLogin} />);

    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("open");
    expect(screen.getByRole("heading", { name: "Turnos Odontología" })).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Ver la clínica" }));
    expect(dialog).not.toHaveAttribute("open");

    fireEvent.click(screen.getByRole("button", { name: "Ingresar al sistema" }));
    expect(dialog).toHaveAttribute("open");
  });

  it("mantiene un único botón Ingresar y un CTA accesible sin ocultar", () => {
    render(<LandingPage onLogin={onLogin} />);

    expect(screen.getAllByRole("button", { name: "Ingresar" })).toHaveLength(1);
    const cta = screen.getByRole("button", { name: "Ingresar al sistema" });
    expect(cta).not.toHaveAttribute("aria-hidden");
    expect(cta).not.toHaveAttribute("tabindex", "-1");
  });

  it("LoginPage monta la portada y conserva el aviso de sesión vencida", () => {
    const tokenStore = createMemoryTokenStore();
    const client = createApiClient({
      baseUrl: "http://localhost:8000/api",
      fetchFn: async () => new Response(null, { status: 204 }),
    });

    render(
      <MemoryRouter initialEntries={[{ pathname: "/login", state: { expired: true } }]}>
        <AuthProvider tokenStore={tokenStore} client={client}>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Aqua — Clínica Odontológica" }),
    ).toBeVisible();
    expect(screen.getByRole("dialog")).toHaveAttribute("open");
    expect(screen.getByRole("alert")).toHaveTextContent(SESSION_EXPIRED_MESSAGE);
  });
});
