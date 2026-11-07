import type { ReactNode } from "react";
import styles from "./PageShell.module.css";

export interface PageShellProps {
  title: string;
  children: ReactNode;
}

export function PageShell({ title, children }: PageShellProps) {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <span className={styles.brand}>{title}</span>
      </header>
      <main className={styles.main}>{children}</main>
      <footer className={styles.footer}>Consultorio odontológico · agenda de turnos</footer>
    </div>
  );
}
