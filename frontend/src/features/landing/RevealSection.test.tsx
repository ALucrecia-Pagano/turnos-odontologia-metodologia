import { act, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RevealSection } from "./RevealSection";
import type { RevealObserverFactory } from "./revealObserver";

describe("RevealSection", () => {
  it("sin IntersectionObserver queda revelada y su contenido es visible", () => {
    const { container } = render(
      <RevealSection>
        <p>Contenido informativo</p>
      </RevealSection>,
    );

    expect(container.querySelector("[data-reveal]")).toHaveAttribute("data-reveal", "revealed");
    expect(screen.getByText("Contenido informativo")).toBeVisible();
  });

  it("con observador inyectado pasa de pendiente a revelada y limpia al desmontar", () => {
    let onReveal: (() => void) | null = null;
    let cleanups = 0;
    const observer: RevealObserverFactory = () => ({
      observe: (_element, callback) => {
        onReveal = callback;
        return () => {
          cleanups += 1;
        };
      },
    });

    const { container, unmount } = render(
      <RevealSection observer={observer}>
        <p>Contenido animado</p>
      </RevealSection>,
    );

    const section = container.querySelector("[data-reveal]");
    expect(section).toHaveAttribute("data-reveal", "pending");
    expect(screen.getByText("Contenido animado")).toBeInTheDocument();

    act(() => {
      onReveal?.();
    });
    expect(section).toHaveAttribute("data-reveal", "revealed");

    unmount();
    expect(cleanups).toBe(1);
  });

  it("con movimiento reducido no queda pendiente y el contenido está en el DOM", () => {
    const observer: RevealObserverFactory = () => ({
      observe: () => () => undefined,
    });

    render(
      <RevealSection observer={observer} reducedMotion>
        <p>Contenido sin animación</p>
      </RevealSection>,
    );

    expect(screen.getByText("Contenido sin animación")).toBeInTheDocument();
    expect(document.querySelector("[data-reveal]")).toHaveAttribute("data-reveal", "revealed");
  });
});
