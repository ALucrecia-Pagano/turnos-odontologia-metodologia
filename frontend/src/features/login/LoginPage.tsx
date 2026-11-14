import { Link, useLocation, useSearchParams } from "react-router-dom";
import logoAquaClaro from "../../assets/brand/logo-aqua-claro.png";
import { SESSION_EXPIRED_MESSAGE, useAuth } from "../auth/AuthContext";
import { LoginCarousel, type CarouselTicker } from "./LoginCarousel";
import { LoginForm } from "./LoginForm";
import styles from "./LoginPage.module.css";

function hasExpiredFlag(state: unknown): boolean {
  if (typeof state === "object" && state !== null && "expired" in state) {
    return (state as { expired?: unknown }).expired === true;
  }
  return false;
}

// Mapa cerrado: solo estos valores de ?rol muestran etiqueta. Es solo presentacion; el rol real lo decide el backend.
const ROLE_LABELS: ReadonlyMap<string, string> = new Map([
  ["recepcion", "Recepción"],
  ["odontologo", "Odontología"],
  ["administrador", "Administración"],
]);

export interface LoginPageProps {
  carouselTicker?: CarouselTicker;
  prefersReducedMotion?: boolean;
}

export function LoginPage({ carouselTicker, prefersReducedMotion }: LoginPageProps = {}) {
  const { login, lastEvent } = useAuth();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const roleParam = searchParams.get("rol");
  const roleLabel = roleParam !== null ? (ROLE_LABELS.get(roleParam) ?? null) : null;
  const showExpiredMessage = lastEvent === "expired" || hasExpiredFlag(location.state);

  return (
    <main className={styles.page}>
      <LoginCarousel ticker={carouselTicker} prefersReducedMotion={prefersReducedMotion} blurred />
      <div className={styles.content}>
        <Link to={roleLabel !== null ? "/acceso" : "/"} className={styles.backLink}>
          ← Volver
        </Link>
        <div className={styles.brand}>
          <img src={logoAquaClaro} alt="Aqua — Clínica Odontológica" className={styles.logo} />
          <p className={styles.tagline}>Claridad en cada cuidado.</p>
        </div>
        <section className={styles.card} aria-labelledby="login-heading">
          <header className={styles.header}>
            {roleLabel !== null && (
              <p className={styles.roleLabel} data-role-label="">
                {roleLabel}
              </p>
            )}
            <h1 id="login-heading" className={styles.title}>
              Turnos Odontología
            </h1>
            <p className={styles.subtitle}>Ingresá con tu usuario del consultorio para gestionar la agenda.</p>
          </header>
          <LoginForm onSubmit={login} initialNotice={showExpiredMessage ? SESSION_EXPIRED_MESSAGE : null} />
        </section>
      </div>
    </main>
  );
}
