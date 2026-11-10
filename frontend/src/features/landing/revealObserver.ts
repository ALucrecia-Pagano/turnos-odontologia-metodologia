export interface RevealObserver {
  observe(element: Element, onReveal: () => void): () => void;
}

export type RevealObserverFactory = () => RevealObserver | null;

export const browserRevealObserver: RevealObserverFactory = () => {
  if (typeof IntersectionObserver === "undefined") {
    return null;
  }

  return {
    observe(element, onReveal) {
      const observer = new IntersectionObserver(
        (entries) => {
          if (entries.some((entry) => entry.isIntersecting)) {
            onReveal();
            observer.disconnect();
          }
        },
        { threshold: 0.15 },
      );
      observer.observe(element);
      return () => {
        observer.disconnect();
      };
    },
  };
};

export function detectPrefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
