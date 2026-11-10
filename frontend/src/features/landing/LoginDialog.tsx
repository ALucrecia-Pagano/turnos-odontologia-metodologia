import { useEffect, useLayoutEffect } from "react";
import type { ApiResult, CurrentUser } from "../../shared/api/types";
import { Dialog } from "../../shared/components/Dialog";
import type { LoginCredentials } from "../auth/authApi";
import { LoginForm } from "../login/LoginForm";
import loginStyles from "../login/LoginPage.module.css";
import styles from "./LoginDialog.module.css";

export interface LoginDialogProps {
  open: boolean;
  onClose: () => void;
  onLogin: (credentials: LoginCredentials) => Promise<ApiResult<CurrentUser>>;
  initialNotice?: string | null;
  returnFocusRef?: { current: HTMLElement | null };
}

export function LoginDialog({
  open,
  onClose,
  onLogin,
  initialNotice = null,
  returnFocusRef,
}: LoginDialogProps) {
  useLayoutEffect(() => {
    if (!open) {
      return;
    }
    document.getElementById("login-username")?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) {
      return;
    }
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  return (
    <Dialog open={open} onClose={onClose} labelledBy="login-heading" returnFocusRef={returnFocusRef}>
      <div className={styles.overlay}>
        <section className={loginStyles.card} aria-labelledby="login-heading">
          <button type="button" className={styles.close} onClick={onClose}>
            Ver la clínica
          </button>
          <header className={loginStyles.header}>
            <h2 id="login-heading" className={loginStyles.title}>
              Turnos Odontología
            </h2>
            <p className={loginStyles.subtitle}>
              Ingresá con tu usuario del consultorio para gestionar la agenda.
            </p>
          </header>
          <LoginForm onSubmit={onLogin} initialNotice={initialNotice} />
        </section>
      </div>
    </Dialog>
  );
}
