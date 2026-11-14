import { useEffect, useState } from "react";
import hero1 from "../../assets/images/hero-1-sala-de-espera.webp";
import hero2 from "../../assets/images/hero-2-consultorio.webp";
import hero3 from "../../assets/images/hero-3-dentista.webp";
import hero4 from "../../assets/images/hero-4-instrumental.webp";
import hero5 from "../../assets/images/hero-5-sillon.webp";
import { createIntervalTicker, type CarouselTicker } from "./carouselTicker";
import styles from "./LoginPage.module.css";

export type { CarouselTicker };

const SLIDE_INTERVAL_MS = 7000;
const SLIDES = [hero1, hero2, hero3, hero4, hero5];

const defaultTicker = createIntervalTicker(SLIDE_INTERVAL_MS);

function detectPrefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export interface LoginCarouselProps {
  ticker?: CarouselTicker;
  prefersReducedMotion?: boolean;
  blurred?: boolean;
}

export function LoginCarousel({ ticker = defaultTicker, prefersReducedMotion, blurred = false }: LoginCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const reducedMotion = prefersReducedMotion ?? detectPrefersReducedMotion();

  useEffect(() => {
    if (paused || reducedMotion) {
      return;
    }

    return ticker(() => {
      setActiveIndex((current) => (current + 1) % SLIDES.length);
    });
  }, [paused, reducedMotion, ticker]);

  return (
    <div className={blurred ? `${styles.carousel} ${styles.carouselBlurred}` : styles.carousel}>
      {SLIDES.map((slide, index) => {
        const isActive = index === activeIndex;
        const className = [styles.slide, isActive ? styles.slideActive : "", isActive && !reducedMotion ? styles.kenBurns : ""]
          .filter(Boolean)
          .join(" ");

        return (
          <img
            key={slide}
            src={slide}
            alt=""
            aria-hidden="true"
            data-slide-index={index}
            data-active={isActive ? "true" : undefined}
            className={className}
          />
        );
      })}
      <div className={styles.overlay} aria-hidden="true" />
      <button
        type="button"
        className={styles.carouselToggle}
        onClick={() => {
          setPaused((current) => !current);
        }}
      >
        {paused ? "Reanudar animación" : "Pausar animación"}
      </button>
    </div>
  );
}
