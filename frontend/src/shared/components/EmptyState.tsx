import styles from "./EmptyState.module.css";

export interface EmptyStateAction {
  label: string;
  onClick: () => void;
}

export interface EmptyStateProps {
  title: string;
  description: string;
  action?: EmptyStateAction;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <section className={styles.empty}>
      <h2 className={styles.title}>{title}</h2>
      <p className={styles.description}>{description}</p>
      {action !== undefined && (
        <button type="button" className={styles.action} onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </section>
  );
}
