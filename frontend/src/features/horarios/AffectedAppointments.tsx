import { StatusBadge } from "../../shared/components/StatusBadge";
import type { AffectedAppointment } from "./horariosApi";
import { formatLocalRangeInZone } from "./horariosTime";
import styles from "./WorkingHoursSection.module.css";

export interface AffectedAppointmentsProps {
  readonly kind: "hours" | "block";
  readonly appointments: readonly AffectedAppointment[];
  readonly professionalName: string;
  readonly timezone: string;
}

export function AffectedAppointments({
  kind,
  appointments,
  professionalName,
  timezone,
}: AffectedAppointmentsProps) {
  if (appointments.length === 0) {
    return null;
  }

  const headingText =
    kind === "hours"
      ? "Turnos futuros que quedan fuera del horario guardado:"
      : "Turnos existentes solapados con el bloqueo creado:";

  return (
    <div role="alert" aria-live="assertive" className={styles.alertBox}>
      <p>
        <strong>{headingText}</strong>
      </p>
      <ul>
        {appointments.map((apt) => {
          const { dateLabel, timeLabel } = formatLocalRangeInZone(
            apt.startAt,
            apt.endAt,
            timezone,
          );
          return (
            <li key={apt.id}>
              <span>{dateLabel}</span> · <span>{timeLabel}</span> ·{" "}
              <span>{apt.patientName}</span> · <span>{professionalName}</span> ·{" "}
              <StatusBadge status={apt.status} />
            </li>
          );
        })}
      </ul>
      <p>
        Los turnos no se cancelan automáticamente; deben reprogramarse o cancelarse desde la
        agenda.
      </p>
    </div>
  );
}
