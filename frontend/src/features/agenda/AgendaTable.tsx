import { StatusBadge } from "../../shared/components/StatusBadge";
import type { AgendaAppointment } from "./agendaApi";
import { formatDayLabel, formatLocalTime } from "./agendaTime";
import styles from "./AgendaTable.module.css";

export interface AgendaTableProps {
  readonly date: string;
  readonly timezone: string;
  readonly appointments: readonly AgendaAppointment[];
}

export function AgendaTable({ date, timezone, appointments }: AgendaTableProps) {
  const dayLabel = formatDayLabel(date);

  return (
    <div className={styles.tableContainer}>
      <table className={styles.table}>
        <caption className={styles.caption}>{`Turnos del ${dayLabel}`}</caption>
        <thead>
          <tr>
            <th scope="col" className={styles.th}>
              Hora
            </th>
            <th scope="col" className={styles.th}>
              Paciente
            </th>
            <th scope="col" className={styles.th}>
              Profesional
            </th>
            <th scope="col" className={styles.th}>
              Sillón
            </th>
            <th scope="col" className={styles.th}>
              Prestación
            </th>
            <th scope="col" className={styles.th}>
              Estado
            </th>
          </tr>
        </thead>
        <tbody>
          {appointments.map((appt) => {
            const startLabel = formatLocalTime(appt.startAt, timezone);
            const endLabel = formatLocalTime(appt.endAt, timezone);
            const timeLabel = `${startLabel}–${endLabel}`;
            const isCancelled = appt.status === "cancelado";

            return (
              <tr
                key={appt.id}
                className={isCancelled ? styles.rowCancelled : undefined}
              >
                <td className={styles.td}>{timeLabel}</td>
                <td className={styles.td}>{appt.patientName}</td>
                <td className={styles.td}>{appt.professionalName}</td>
                <td className={styles.td}>{appt.chairName}</td>
                <td className={styles.td}>{appt.serviceName}</td>
                <td className={styles.td}>
                  <StatusBadge status={appt.status} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
