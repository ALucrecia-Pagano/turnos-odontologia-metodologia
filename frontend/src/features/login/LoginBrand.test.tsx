import { act, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { createApiClient } from "../../shared/api/client";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { LoginPage } from "./LoginPage";
import type { CarouselTicker } from "./LoginCarousel";

const noopTicker: CarouselTicker = () => () => {};

function createManualTicker() {
  let callback: (() => void) | null = null;

  const ticker: CarouselTicker = (next) => {
    callback = next;
    return () => {
      callback = null;
    };
  };

  return {
    ticker,
    tick: () => {
      if (callback !== null) {
        act(() => {
          callback?.();
        });
      }
    },
  };
}

function renderLogin(ticker: CarouselTicker = noopTicker) {
  const tokenStore = createMemoryTokenStore();
  const client = createApiClient({
    baseUrl: "http://localhost:8000/api",
    fetchFn: async () => new Response(null, { status: 204 }),
  });

  return render(
    <MemoryRouter
      initialEntries={["/login"]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <AuthProvider tokenStore={tokenStore} client={client}>
        <LoginPage carouselTicker={ticker} />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("LoginPage brand", () => {
  it("muestra el logo claro, el heading accesible y la bajada", () => {
    renderLogin();

    const logo = screen.queryByRole("img", { name: "Aqua — Clínica Odontológica" });
    expect(logo).not.toBeNull();
    if (logo === null) {
      throw new Error("No se renderizó el logo del login");
    }
    expect(logo.getAttribute("src")).toContain("logo-aqua-claro");
    expect(screen.getByRole("heading", { name: "Turnos Odontología" })).toBeInTheDocument();
    expect(screen.getByText("Claridad en cada cuidado.")).toBeVisible();
  });

  it("renderiza sin window.matchMedia, usa reduced motion falso y permite avanzar el carrusel", () => {
    const manual = createManualTicker();
    const { container } = renderLogin(manual.ticker);

    expect(screen.getByRole("heading", { name: "Turnos Odontología" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pausar animación" })).toBeInTheDocument();
    expect(container.querySelector('[data-active="true"]')?.getAttribute("data-slide-index")).toBe("0");

    manual.tick();
    expect(container.querySelector('[data-active="true"]')?.getAttribute("data-slide-index")).toBe("1");
  });
});
