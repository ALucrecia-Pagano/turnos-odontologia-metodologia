import { useEffect, useRef, useState, type ReactNode } from "react";
import { browserRevealObserver, type RevealObserverFactory } from "./revealObserver";
import styles from "./RevealSection.module.css";

export interface RevealSectionProps {
  children: ReactNode;
  observer?: RevealObserverFactory;
  reducedMotion?: boolean;
}

export function RevealSection({ children, observer, reducedMotion = false }: RevealSectionProps) {
  const canAnimate = !reducedMotion && (observer !== undefined || typeof IntersectionObserver !== "undefined");
  const [revealed, setRevealed] = useState(!canAnimate);
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!canAnimate) {
      return;
    }

    const section = sectionRef.current;
    if (!section) {
      return;
    }

    const factory = observer ?? browserRevealObserver;
    const instance = factory();
    if (instance === null) {
      queueMicrotask(() => {
        setRevealed(true);
      });
      return;
    }

    return instance.observe(section, () => {
      setRevealed(true);
    });
  }, [canAnimate, observer]);

  return (
    <div ref={sectionRef} data-reveal={revealed ? "revealed" : "pending"} className={styles.reveal}>
      {children}
    </div>
  );
}
