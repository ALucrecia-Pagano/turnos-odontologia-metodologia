import { useState, type FormEvent } from "react";
import { getApiErrorMessages } from "../../shared/api/errors";
import type { ApiResult, CurrentUser } from "../../shared/api/types";
import type { LoginCredentials } from "../auth/authApi";
import { NETWORK_ERROR_MESSAGE } from "../auth/AuthContext";
import styles from "./LoginPage.module.css";

export interface LoginFormProps {
  onSubmit: (credentials: LoginCredentials) => Promise<ApiResult<CurrentUser>>;
  initialNotice?: string | null;
}

export function LoginForm({ onSubmit, initialNotice = null }: LoginFormProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const visibleAlert = errorMessage ?? initialNotice;

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    const trimmedUsername = username.trim();
    if (trimmedUsername === "" || password === "") {
      setPassword("");
      setErrorMessage("Completá el usuario y la contraseña.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    const result = await onSubmit({ username: trimmedUsername, password });
    setPassword("");

    if (!result.ok) {
      if (result.error.kind === "unknown") {
        setErrorMessage(NETWORK_ERROR_MESSAGE);
      } else {
        setErrorMessage(getApiErrorMessages(result.error).join(" "));
      }
      setIsSubmitting(false);
    }
  }

  return (
    <form
      className={styles.form}
      aria-label="Iniciar sesión"
      aria-describedby={visibleAlert !== null ? "login-alert" : undefined}
      noValidate
      onSubmit={(event) => {
        void handleSubmit(event);
      }}
    >
      {visibleAlert !== null && (
        <div id="login-alert" className={styles.alert} role="alert" aria-live="polite">
          {visibleAlert}
        </div>
      )}

      <div className={styles.field}>
        <label className={styles.label} htmlFor="login-username">
          Usuario
        </label>
        <input
          id="login-username"
          name="username"
          type="text"
          className={styles.input}
          autoComplete="username"
          maxLength={150}
          required
          autoFocus
          value={username}
          onChange={(event) => {
            setUsername(event.target.value);
          }}
        />
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor="login-password">
          Contraseña
        </label>
        <input
          id="login-password"
          name="password"
          type="password"
          className={styles.input}
          autoComplete="current-password"
          maxLength={128}
          required
          value={password}
          onChange={(event) => {
            setPassword(event.target.value);
          }}
        />
      </div>

      <button
        type="submit"
        className={styles.submit}
        disabled={isSubmitting}
        aria-busy={isSubmitting ? "true" : "false"}
      >
        {isSubmitting ? (
          "Ingresando…"
        ) : (
          <>
            Ingresar{" "}
            <span className={styles.submitArrow} aria-hidden="true">
              →
            </span>
          </>
        )}
      </button>
    </form>
  );
}
