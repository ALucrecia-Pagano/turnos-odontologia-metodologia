import styles from "./ErrorState.module.css";

export interface ErrorStateProps {
  /** Mensajes tal cual los devuelve la API: no se traducen ni se reformulan. */
  messages: readonly string[];
  title?: string;
  onRetry?: () => void;
}

export function ErrorState({ messages, title = "No se pudo completar la operación", onRetry }: ErrorStateProps) {
  return (
    <div className={styles.error} role="alert">
      <p className={styles.title}>{title}</p>
      <ul className={styles.messages}>
        {messages.map((message, index) => (
          <li key={`${index}-${message}`}>{message}</li>
        ))}
      </ul>
      {onRetry !== undefined && (
        <button type="button" className={styles.retry} onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  );
}
