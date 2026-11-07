import {
  APPOINTMENT_STATUS_TOKENS,
  type AppointmentStatus,
} from "../styles/appointmentStatusTokens";
import styles from "./StatusBadge.module.css";

const STATUS_LABELS: Readonly<Record<AppointmentStatus, string>> = {
  reservado: "Reservado",
  confirmado: "Confirmado",
  atendido: "Atendido",
  ausente: "Ausente",
  cancelado: "Cancelado",
};

export interface StatusBadgeProps {
  status: AppointmentStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const tokens = APPOINTMENT_STATUS_TOKENS[status];
  return (
    <span
      className={`${styles.badge} ${styles[status]}`}
      data-status={status}
      style={{ color: tokens.text, backgroundColor: tokens.background, borderColor: tokens.border }}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}
