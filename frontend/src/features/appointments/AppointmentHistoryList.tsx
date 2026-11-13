import { useEffect, useState } from "react";
import type { ApiClient } from "../../shared/api/client";
import { formatLocalDate, formatLocalTime, formatTimeRange } from "../agenda/agendaTime";
import { getAppointmentHistory, type HistoryEntryResponse } from "./appointmentApi";
import styles from "./AppointmentHistoryList.module.css";

export interface AppointmentHistoryListProps {
  appointmentId: string;
  client: ApiClient;
  timezone: string;
}

function formatDisplayDate(instant: string, timezone: string): string {
  const ymd = formatLocalDate(instant, timezone);
  const [year, month, day] = ymd.split("-");
  return `${day}/${month}/${year}`;
}

export function AppointmentHistoryList({
  appointmentId,
  client,
  timezone,
}: AppointmentHistoryListProps) {
  const [prevApptId, setPrevApptId] = useState(appointmentId);
  const [entries, setEntries] = useState<readonly HistoryEntryResponse[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  if (appointmentId !== prevApptId) {
    setPrevApptId(appointmentId);
    setIsLoading(true);
    setError(null);
    setEntries(null);
  }

  useEffect(() => {
    let active = true;

    void getAppointmentHistory(client, appointmentId).then((result) => {
      if (!active) {
        return;
      }
      setIsLoading(false);
      if (result.ok) {
        setEntries(result.data);
      } else {
        setError("No se pudo cargar el historial de cambios.");
      }
    });

    return () => {
      active = false;
    };
  }, [client, appointmentId]);

  if (isLoading) {
    return <p className={styles.historyLoading}>Cargando historial...</p>;
  }

  if (error !== null) {
    return (
      <p role="status" className={styles.historyError}>
        {error}
      </p>
    );
  }

  if (!entries || entries.length === 0) {
    return <p className={styles.historyEmpty}>Sin cambios registrados.</p>;
  }

  return (
    <ul className={styles.historyList}>
      {entries.map((entry, index) => {
        const timeStr = `${formatDisplayDate(entry.changedAt, timezone)} ${formatLocalTime(
          entry.changedAt,
          timezone,
        )}`;
        const author = entry.changedByName ?? "Usuario";
        const transition = entry.from
          ? `${entry.from} → ${entry.to}`
          : `Creado como ${entry.to}`;

        return (
          <li key={index} className={styles.historyItem}>
            <div className={styles.historyHeader}>
              <span className={styles.historyAuthor}>{author}</span>
              <span className={styles.historyTime}>{timeStr}</span>
            </div>
            <div className={styles.historyTransition}>{transition}</div>
            {entry.reschedule && (
              <div className={styles.historyReschedule}>
                <div>
                  Anterior: {formatDisplayDate(entry.reschedule.previousStartAt, timezone)}{" "}
                  {formatTimeRange(
                    entry.reschedule.previousStartAt,
                    entry.reschedule.previousEndAt,
                    timezone,
                  )}
                </div>
                <div>
                  Nuevo: {formatDisplayDate(entry.reschedule.newStartAt, timezone)}{" "}
                  {formatTimeRange(
                    entry.reschedule.newStartAt,
                    entry.reschedule.newEndAt,
                    timezone,
                  )}
                </div>
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
