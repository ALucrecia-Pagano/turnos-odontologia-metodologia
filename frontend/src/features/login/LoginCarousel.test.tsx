import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginCarousel, type CarouselTicker } from "./LoginCarousel";

function createManualTicker() {
  let callback: (() => void) | null = null;
  let cancelCount = 0;

  const ticker: CarouselTicker = (next) => {
    callback = next;
    return () => {
      callback = null;
      cancelCount += 1;
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
    getCancelCount: () => cancelCount,
  };
}

function activeIndex(container: HTMLElement): string | null {
  return container.querySelector('[data-active="true"]')?.getAttribute("data-slide-index") ?? null;
}

describe("LoginCarousel", () => {
  it("inicia en hero-1-sala-de-espera, avanza con el ticker y vuelve a la primera tras la quinta", () => {
    const manual = createManualTicker();
    const { container } = render(<LoginCarousel ticker={manual.ticker} />);

    const initial = container.querySelector('[data-active="true"]');
    expect(initial).not.toBeNull();
    expect(initial?.getAttribute("src")).toContain("hero-1-sala-de-espera");
    expect(activeIndex(container)).toBe("0");

    for (let index = 1; index < 5; index += 1) {
      manual.tick();
      expect(activeIndex(container)).toBe(String(index));
    }

    manual.tick();
    expect(activeIndex(container)).toBe("0");
  });

  it("pausa y reanuda el avance sin aria-pressed", async () => {
    const user = userEvent.setup();
    const manual = createManualTicker();
    const { container } = render(<LoginCarousel ticker={manual.ticker} />);

    const pause = screen.getByRole("button", { name: "Pausar animación" });
    expect(pause).not.toHaveAttribute("aria-pressed");

    await user.click(pause);
    const resume = screen.getByRole("button", { name: "Reanudar animación" });
    expect(resume).not.toHaveAttribute("aria-pressed");

    manual.tick();
    expect(activeIndex(container)).toBe("0");

    await user.click(resume);
    manual.tick();
    expect(activeIndex(container)).toBe("1");
  });

  it("reduced motion desactiva la rotación y el Ken Burns", () => {
    const manual = createManualTicker();
    const { container } = render(<LoginCarousel ticker={manual.ticker} prefersReducedMotion />);

    manual.tick();
    expect(activeIndex(container)).toBe("0");

    const images = container.querySelectorAll("img[data-slide-index]");
    images.forEach((image) => {
      expect(image).not.toHaveClass("kenBurns");
    });
  });

  it("cancela el ticker al desmontar", () => {
    const manual = createManualTicker();
    const { unmount } = render(<LoginCarousel ticker={manual.ticker} />);

    expect(manual.getCancelCount()).toBe(0);
    unmount();
    expect(manual.getCancelCount()).toBe(1);
  });

  it("muestra cinco fotos decorativas y la clase de Ken Burns solo en la activa", () => {
    const manual = createManualTicker();
    const { container } = render(<LoginCarousel ticker={manual.ticker} />);

    const images = container.querySelectorAll("img[data-slide-index]");
    expect(images).toHaveLength(5);
    images.forEach((image, index) => {
      expect(image).toHaveAttribute("alt", "");
      expect(image).toHaveAttribute("aria-hidden", "true");
      expect(image).toHaveAttribute("data-slide-index", String(index));
    });

    const active = container.querySelectorAll('[data-active="true"]');
    expect(active).toHaveLength(1);
    expect(active[0]).toHaveAttribute("data-slide-index", "0");
    expect(images[0]).toHaveClass("kenBurns");
    expect(images[1]).not.toHaveClass("kenBurns");
    expect(images[2]).not.toHaveClass("kenBurns");
    expect(images[3]).not.toHaveClass("kenBurns");
    expect(images[4]).not.toHaveClass("kenBurns");
  });
});
