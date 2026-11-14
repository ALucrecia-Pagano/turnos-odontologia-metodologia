import { act, render, screen, waitFor, within } from "@testing-library/react";
import { createMemoryRouter, MemoryRouter, RouterProvider } from "react-router-dom";
import { createAppRoutes } from "../../App";
import { readSrcFile, ruleBody } from "../../test/cssText";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { createFixedClock } from "../agenda/clock";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import type { CarouselTicker } from "../login/LoginCarousel";
import { LandingPage } from "./LandingPage";
import type { RevealObserverFactory } from "./revealObserver";

const FIXED_CLOCK = createFixedClock("2026-11-16T12:00:00Z");

function renderRootAsAnonymous() {
  const fetchFn: FetchFn = async () => new Response(null, { status: 401 });
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
  const router = createMemoryRouter(createAppRoutes(FIXED_CLOCK), { initialEntries: ["/"] });

  const view = render(
    <AuthProvider tokenStore={createMemoryTokenStore()} client={client}>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </AuthProvider>,
  );
  return { router, ...view };
}

const noopTicker: CarouselTicker = () => () => undefined;

function createRevealHarness() {
  const callbacks: (() => void)[] = [];
  const observer: RevealObserverFactory = () => ({
    observe: (_element, onReveal) => {
      callbacks.push(onReveal);
      return () => undefined;
    },
  });
  return {
    observer,
    observedCount: () => callbacks.length,
    revealAll: () => {
      act(() => {
        for (const callback of callbacks) {
          callback();
        }
      });
    },
  };
}

function renderLanding(props: { observer?: RevealObserverFactory; reducedMotion?: boolean }) {
  return render(
    <MemoryRouter initialEntries={["/"]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <LandingPage carouselTicker={noopTicker} {...props} />
    </MemoryRouter>,
  );
}

describe("LandingPage", () => {
  it("portada completa para anónimo en /", async () => {
    const { router, container } = renderRootAsAnonymous();

    await waitFor(() => {
      expect(screen.queryByRole("heading", { level: 1, name: "Aqua — Clínica Odontológica" })).toBeInTheDocument();
    });
    expect(router.state.location.pathname).toBe("/");

    expect(container.querySelectorAll("img[data-slide-index]")).toHaveLength(5);
    expect(container.querySelector("[data-landing-overlay]")).not.toBeNull();
    expect(screen.queryByText("Claridad en cada cuidado.")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Explorar la clínica →" })).toBeInTheDocument();
    expect(screen.queryByText("Sitio de demostración")).toBeInTheDocument();

    const nav = screen.queryByRole("navigation", { name: "Navegación principal" });
    expect(nav).toBeInTheDocument();
    if (nav === null) {
      return;
    }
    const inicio = within(nav).queryByRole("link", { name: "Inicio" });
    const clinica = within(nav).queryByRole("link", { name: "La clínica" });
    const acceder = within(nav).queryByRole("link", { name: "Acceder" });
    expect(inicio).toHaveAttribute("aria-current", "page");
    expect(clinica).toBeInTheDocument();
    expect(clinica).not.toHaveAttribute("aria-current");
    expect(acceder).toHaveAttribute("href", "/acceso");
    expect(acceder).not.toHaveAttribute("aria-current");
  });

  it("secciones editoriales entran con animación lateral al scrollear", () => {
    const harness = createRevealHarness();
    const { container } = renderLanding({ observer: harness.observer, reducedMotion: false });

    const sections = container.querySelectorAll("[data-reveal]");
    expect(sections).toHaveLength(4);
    for (const section of sections) {
      expect(section).toHaveAttribute("data-reveal", "pending");
    }

    harness.revealAll();
    for (const section of container.querySelectorAll("[data-reveal]")) {
      expect(section).toHaveAttribute("data-reveal", "revealed");
    }

    for (const title of ["01 / Quiénes somos", "02 / Servicios", "03 / Equipo", "04 / Horarios y contacto"]) {
      expect(screen.queryByRole("heading", { level: 2, name: title })).toBeInTheDocument();
    }
    expect(screen.queryByText("(0261) 555-0101")).toBeInTheDocument();
    expect(screen.queryByText("Estado actual: demostración funcional")).toBeInTheDocument();

    const revealCss = readSrcFile("features/landing/RevealSection.module.css");
    expect(ruleBody(revealCss, '.reveal[data-reveal="pending"]')).toContain("translateX(");
    const durations = [...ruleBody(revealCss, ".reveal").matchAll(/(\d+)ms/g)].map((match) => Number(match[1]));
    expect(durations.length).toBeGreaterThan(0);
    for (const duration of durations) {
      expect(duration).toBeGreaterThanOrEqual(200);
      expect(duration).toBeLessThanOrEqual(250);
    }
  });

  it("reduced motion desactiva la animación lateral y deja el contenido visible", () => {
    const harness = createRevealHarness();
    const first = renderLanding({ observer: harness.observer, reducedMotion: true });

    const sections = first.container.querySelectorAll("[data-reveal]");
    expect(sections).toHaveLength(4);
    for (const section of sections) {
      expect(section).toHaveAttribute("data-reveal", "revealed");
    }
    expect(harness.observedCount()).toBe(0);
    expect(screen.queryByRole("heading", { level: 2, name: "01 / Quiénes somos" })).toBeInTheDocument();
    expect(screen.queryByText("(0261) 555-0101")).toBeInTheDocument();
    first.unmount();

    expect(typeof IntersectionObserver).toBe("undefined");
    const second = renderLanding({});
    const secondSections = second.container.querySelectorAll("[data-reveal]");
    expect(secondSections).toHaveLength(4);
    for (const section of secondSections) {
      expect(section).toHaveAttribute("data-reveal", "revealed");
    }
    expect(screen.queryByRole("heading", { level: 2, name: "04 / Horarios y contacto" })).toBeInTheDocument();

    const revealCss = readSrcFile("features/landing/RevealSection.module.css");
    const reduced = "@media (prefers-reduced-motion: reduce)";
    expect(ruleBody(revealCss, ".reveal", reduced)).toContain("transition: none;");
    const reducedPending = ruleBody(revealCss, '.reveal[data-reveal="pending"]', reduced);
    expect(reducedPending).toContain("transform: none;");
    expect(reducedPending).toContain("opacity: 1;");
  });

  it("las secciones editoriales alternan de lado: 01 izquierda, 02 derecha, 03 izquierda, 04 derecha", () => {
    const { container } = renderLanding({ reducedMotion: true });

    const wrappers = [...container.querySelectorAll("[data-reveal]")];
    expect(wrappers.map((wrapper) => wrapper.getAttribute("data-side"))).toEqual(["left", "right", "left", "right"]);
    expect(
      wrappers.map((wrapper) => within(wrapper as HTMLElement).queryByRole("heading", { level: 2 })?.textContent),
    ).toEqual(["01 / Quiénes somos", "02 / Servicios", "03 / Equipo", "04 / Horarios y contacto"]);

    const css = readSrcFile("features/landing/LandingPage.module.css");
    expect(ruleBody(css, ".sectionLeft")).toContain("margin-right: auto;");
    expect(ruleBody(css, ".sectionRight")).toContain("margin-left: auto;");
    expect(ruleBody(css, ".section")).toContain("width: 60%;");
  });

  it("el CTA de la portada es un enlace fantasma sin relleno y sigue siendo el único", () => {
    const { container } = renderLanding({ reducedMotion: true });

    const ctas = container.querySelectorAll("[data-cta]");
    expect(ctas).toHaveLength(1);
    expect(ctas[0]).toHaveAttribute("data-variant", "ghost");
    expect(ctas[0]).toHaveTextContent("Explorar la clínica →");
    expect(ctas[0]?.tagName).toBe("A");

    const cta = ruleBody(readSrcFile("features/landing/LandingPage.module.css"), ".cta");
    expect(cta).toContain("background: transparent;");
    expect(cta).toContain("border-bottom: 1px solid var(--border-on-navy-strong);");
    expect(cta).not.toMatch(/(^|[\s;])background(-color)?:\s+(?!transparent|none)/);
  });
});
