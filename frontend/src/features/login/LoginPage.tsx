import { useLocation } from "react-router-dom";
import { SESSION_EXPIRED_MESSAGE, useAuth } from "../auth/AuthContext";
import { LoginForm } from "./LoginForm";
import styles from "./LoginPage.module.css";

function hasExpiredFlag(state: unknown): boolean {
  if (typeof state === "object" && state !== null && "expired" in state) {
    return (state as { expired?: unknown }).expired === true;
  }
  return false;
}

export function LoginPage() {
  const { login, lastEvent } = useAuth();
  const location = useLocation();
  const showExpiredMessage = lastEvent === "expired" || hasExpiredFlag(location.state);

  return (
    <main className={styles.page}>
      <section className={styles.card} aria-labelledby="login-heading">
        <header className={styles.header}>
          <h1 id="login-heading" className={styles.title}>
            Turnos Odontología
          </h1>
          <p className={styles.subtitle}>Ingresá con tu usuario del consultorio para gestionar la agenda.</p>
        </header>
        <LoginForm onSubmit={login} initialNotice={showExpiredMessage ? SESSION_EXPIRED_MESSAGE : null} />
      </section>
    </main>
  );
}
