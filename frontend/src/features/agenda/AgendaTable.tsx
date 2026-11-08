import { StatusBadge } from "../../shared/components/StatusBadge";
import type { AgendaAppointment } from "./agendaApi";
import {
  formatDayLabel,
  formatLocalDate,
  formatLocalTime,
  formatWeekLabel,
  parseLocalDate,
  weekdayOf,
} from "./agendaTime";
import styles from "./AgendaTable.module.css";

export interface AgendaTableProps {
  readonly date: string;
  readonly timezone: string;
  readonly appointments: readonly AgendaAppointment[];
  readonly view?: "day" | "week";
  readonly caption?: string;
}

const SHORT_WEEKDAY_NAMES = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"];

function formatTableDate(instant: Date | string, timezone: string): string {
  const localDate = formatLocalDate(instant, timezone);
  const parsed = parseLocalDate(localDate);
  const weekdayIndex = weekdayOf(localDate) - 1;
  const name = SHORT_WEEKDAY_NAMES[weekdayIndex] ?? "";
  const day = parsed !== null ? String(parsed.day).padStart(2, "0") : "";
  const month = parsed !== null ? String(parsed.month).padStart(2, "0") : "";
  return `${name} ${day}/${month}`;
}

export function AgendaTable({
  date,
  timezone,
  appointments,
  view = "day",
  caption,
}: AgendaTableProps) {
  const isWeek = view === "week";
  const dayLabel = formatDayLabel(date);
  const tableCaption = caption ?? (isWeek ? formatWeekLabel(date) : `Turnos del ${dayLabel}`);

  const sortedAppointments = isWeek
    ? [...appointments].sort((a, b) => a.startAt.localeCompare(b.startAt))
    : appointments;

  return (
    <div className={styles.tableContainer}>
      <table className={styles.table}>
        <caption className={styles.caption}>{tableCaption}</caption>
        <thead>
          <tr>
            {isWeek && (
              <th scope="col" className={styles.th}>
                Fecha
              </th>
            )}
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
          {sortedAppointments.map((appt) => {
            const dateLabel = formatTableDate(appt.startAt, timezone);
            const startLabel = formatLocalTime(appt.startAt, timezone);
            const endLabel = formatLocalTime(appt.endAt, timezone);
            const timeLabel = `${startLabel}–${endLabel}`;
            const isCancelled = appt.status === "cancelado";

            return (
              <tr
                key={appt.id}
                className={isCancelled ? styles.rowCancelled : undefined}
              >
                {isWeek && <td className={styles.td}>{dateLabel}</td>}
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
