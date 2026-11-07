import styles from "./LoadingState.module.css";

export interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = "Cargando..." }: LoadingStateProps) {
  return (
    <div className={styles.loading} role="status" aria-live="polite">
      <span className={styles.spinner} aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
