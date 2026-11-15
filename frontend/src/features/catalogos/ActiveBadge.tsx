import styles from "./ActiveBadge.module.css";

export interface ActiveBadgeProps {
  readonly active: boolean;
}

export function ActiveBadge({ active }: ActiveBadgeProps) {
  return (
    <span className={`${styles.badge} ${active ? styles.active : styles.inactive}`}>
      {active ? "Activo" : "Inactivo"}
    </span>
  );
}
