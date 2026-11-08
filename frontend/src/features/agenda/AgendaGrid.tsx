import { StatusBadge } from "../../shared/components/StatusBadge";
import type { AppointmentStatus } from "../../shared/styles/appointmentStatusTokens";
import type {
  AgendaAppointment,
  AgendaBlock,
  AgendaWorkingHours,
} from "./agendaApi";
import {
  appointmentRange,
  assignLanes,
  type AgendaAxis,
  type ProfessionalColumn,
} from "./agendaLayout";
import { formatLocalTime, formatMinutesToHHMM, parseHHMM } from "./agendaTime";
import styles from "./AgendaGrid.module.css";

export interface AgendaGridProps {
  readonly date: string;
  readonly timezone: string;
  readonly axis: AgendaAxis;
  readonly columns: readonly ProfessionalColumn<
    AgendaAppointment,
    AgendaWorkingHours,
    AgendaBlock
  >[];
  readonly view?: "day" | "week";
  readonly isWeek?: boolean;
}

const STATUS_LABELS: Readonly<Record<AppointmentStatus, string>> = {
  reservado: "Reservado",
  confirmado: "Confirmado",
  atendido: "Atendido",
  ausente: "Ausente",
  cancelado: "Cancelado",
};

export function AgendaGrid({ date, timezone, axis, columns, view, isWeek }: AgendaGridProps) {
  const isWeekView = isWeek ?? view === "week";
  const axisSpan = Math.max(1, axis.endMinute - axis.startMinute);

  return (
    <div className={styles.gridScrollContainer} data-testid="agenda-grid-scroll">
      <div className={styles.gridTable}>
        <div className={styles.headerRow}>
          <div className={styles.cornerCell}>Hora</div>
          {columns.map((col) => {
            const isToday = Boolean(col.isToday);
            return (
              <div
                key={col.id}
                className={`${styles.columnHeader} ${isWeekView ? styles.weekColumnHeader : ""}`}
                data-testid="agenda-column-header"
                aria-current={isToday ? "date" : undefined}
              >
                <span>{col.displayLabel}</span>
                {isToday && <span className={styles.todayTag}>Hoy</span>}
              </div>
            );
          })}
        </div>

        <div className={styles.bodyRow}>
          <div className={styles.timeGutter} data-testid="agenda-time-gutter">
            {axis.hours.map((hour) => (
              <div
                key={hour}
                className={styles.hourTick}
                data-testid="agenda-axis-hour"
              >
                {hour}
              </div>
            ))}
          </div>

          {columns.map((col) => {
            const columnDate = col.date ?? date;
            const positioned = assignLanes(col.appointments, {
              date: columnDate,
              timezone,
              axisStartMinute: axis.startMinute,
              axisEndMinute: axis.endMinute,
            });

            return (
              <div
                key={col.id}
                className={`${styles.columnTrack} ${isWeekView ? styles.weekColumnTrack : ""}`}
                data-testid={`agenda-column-${col.id}`}
              >
                {col.appointments.length === 0 && (
                  <div className={styles.emptyColumnNote}>Sin turnos</div>
                )}

                {col.workingHours.map((wh, index) => {
                  const startMinute = Math.max(
                    axis.startMinute,
                    Math.min(axis.endMinute, parseHHMM(wh.start)),
                  );
                  const endMinute = Math.max(
                    startMinute,
                    Math.min(axis.endMinute, parseHHMM(wh.end)),
                  );
                  if (endMinute <= startMinute) {
                    return null;
                  }
                  const offsetMinutes = startMinute - axis.startMinute;
                  const durationMinutes = endMinute - startMinute;
                  const topPercent = (offsetMinutes / axisSpan) * 100;
                  const heightPercent = (durationMinutes / axisSpan) * 100;

                  return (
                    <div
                      key={`${wh.professionalId}-${wh.weekday}-${wh.start}-${wh.end}-${index}`}
                      className={styles.workingHourBand}
                      aria-label={`Horario de atención: ${wh.start} a ${wh.end}`}
                      data-offset-minutes={offsetMinutes}
                      data-duration-minutes={durationMinutes}
                      style={{
                        top: `${topPercent}%`,
                        height: `${heightPercent}%`,
                      }}
                    />
                  );
                })}

                {col.blocks.map((block) => {
                  const range = appointmentRange(block.startAt, block.endAt, columnDate, timezone);
                  if (range === null) {
                    return null;
                  }
                  const startMinute = Math.max(
                    axis.startMinute,
                    Math.min(axis.endMinute, range.startMinute),
                  );
                  const endMinute = Math.max(
                    startMinute,
                    Math.min(axis.endMinute, range.endMinute),
                  );
                  if (endMinute <= startMinute) {
                    return null;
                  }
                  const offsetMinutes = startMinute - axis.startMinute;
                  const durationMinutes = endMinute - startMinute;
                  const topPercent = (offsetMinutes / axisSpan) * 100;
                  const heightPercent = (durationMinutes / axisSpan) * 100;
                  const startLabel = formatMinutesToHHMM(startMinute);
                  const endLabel = formatMinutesToHHMM(endMinute);
                  const reasonText =
                    block.reason !== null && block.reason !== "" ? block.reason : "Bloqueo";
                  const ariaLabel =
                    block.reason !== null && block.reason !== ""
                      ? `Bloqueo: ${block.reason}, de ${startLabel} a ${endLabel}`
                      : `Bloqueo, de ${startLabel} a ${endLabel}`;

                  return (
                    <div
                      key={block.id}
                      className={styles.blockBand}
                      aria-label={ariaLabel}
                      data-testid={`agenda-block-${block.id}`}
                      data-offset-minutes={offsetMinutes}
                      data-duration-minutes={durationMinutes}
                      style={{
                        top: `${topPercent}%`,
                        height: `${heightPercent}%`,
                      }}
                    >
                      <span>{reasonText}</span>
                    </div>
                  );
                })}

                {positioned.map((item) => {
                  const appt = item.appointment;
                  const startLabel = formatLocalTime(appt.startAt, timezone);
                  const endLabel = formatLocalTime(appt.endAt, timezone);
                  const timeLabel = `${startLabel}–${endLabel}`;
                  const widthPercent = 100 / item.laneCount;
                  const leftPercent = item.lane * widthPercent;
                  const isCancelled = appt.status === "cancelado";
                  const statusLabel = STATUS_LABELS[appt.status];
                  const isCompact = item.durationMinutes < 45;
                  const isSplitLane = item.laneCount > 1;
                  const cardAriaLabel = `${timeLabel}, ${appt.patientName}, ${appt.serviceName}, ${appt.professionalName}, ${appt.chairName}, ${statusLabel}`;
                  const cardClassName = [
                    styles.appointmentCard,
                    isCancelled ? styles.appointmentCancelled : null,
                    isSplitLane ? styles.appointmentSplit : null,
                  ]
                    .filter((name): name is string => name !== null && name !== undefined)
                    .join(" ");

                  return (
                    <article
                      key={appt.id}
                      aria-label={cardAriaLabel}
                      title={isCompact ? appt.serviceName : undefined}
                      className={cardClassName}
                      data-testid={`agenda-appointment-${appt.id}`}
                      data-status={appt.status}
                      data-offset-minutes={item.offsetMinutes}
                      data-duration-minutes={item.durationMinutes}
                      data-effective-minutes={item.effectiveMinutes}
                      data-lane={item.lane}
                      data-lane-count={item.laneCount}
                      style={{
                        top: `${item.topPercent}%`,
                        height: `${item.heightPercent}%`,
                        left: `${leftPercent}%`,
                        width: `${widthPercent}%`,
                      }}
                    >
                      {isCompact ? (
                        // La hora y el paciente tienen prioridad: en carriles divididos (y en
                        // columnas de menos de 260 px, por container query) la etiqueta de
                        // estado baja a una segunda línea en tamaño reducido.
                        <div
                          className={
                            isSplitLane
                              ? `${styles.cardCompactRow} ${styles.cardCompactStacked}`
                              : styles.cardCompactRow
                          }
                          title={appt.serviceName}
                        >
                          <span className={styles.cardCompactText}>
                            {`${startLabel} · ${appt.patientName}`}
                          </span>
                          <span className={styles.statusBadgeWrap}>
                            <StatusBadge status={appt.status} />
                          </span>
                        </div>
                      ) : (
                        <>
                          <div className={styles.cardTopRow}>
                            <span className={styles.cardTime}>{timeLabel}</span>
                            <StatusBadge status={appt.status} />
                          </div>
                          <div className={styles.cardPatient}>{appt.patientName}</div>
                          <div className={styles.cardMeta}>{appt.serviceName}</div>
                        </>
                      )}
                    </article>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
