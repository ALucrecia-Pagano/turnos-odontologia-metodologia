import { useLocation } from "react-router-dom";
import { SESSION_EXPIRED_MESSAGE, useAuth } from "../auth/AuthContext";
import type { CarouselTicker } from "./LoginCarousel";
import { LandingPage } from "../landing/LandingPage";

function hasExpiredFlag(state: unknown): boolean {
  if (typeof state === "object" && state !== null && "expired" in state) {
    return (state as { expired?: unknown }).expired === true;
  }
  return false;
}

export interface LoginPageProps {
  carouselTicker?: CarouselTicker;
  prefersReducedMotion?: boolean;
}

export function LoginPage({ carouselTicker, prefersReducedMotion }: LoginPageProps = {}) {
  const { login, lastEvent } = useAuth();
  const location = useLocation();
  const showExpiredMessage = lastEvent === "expired" || hasExpiredFlag(location.state);

  return (
    <LandingPage
      onLogin={login}
      initialNotice={showExpiredMessage ? SESSION_EXPIRED_MESSAGE : null}
      carouselTicker={carouselTicker}
      prefersReducedMotion={prefersReducedMotion}
    />
  );
}
