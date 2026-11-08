import { useState } from "react";
import { EmptyState } from "../../shared/components/EmptyState";
import type { AgendaResponse, Professional } from "./agendaApi";
import { AgendaGrid } from "./AgendaGrid";
import { computeAxis, groupByProfessional } from "./agendaLayout";
import { AgendaTable } from "./AgendaTable";
import { formatDayLabel, weekdayOf } from "./agendaTime";
import styles from "./AgendaView.module.css";

export interface AgendaViewProps {
  readonly date: string;
  readonly timezone: string;
  readonly agenda: AgendaResponse;
  readonly professionals: readonly Professional[];
  readonly filterProfessionalId?: string | null;
  readonly filterChairId?: string | null;
  readonly isRefreshing?: boolean;
  readonly catalogWarning?: string | null;
}

export function AgendaView({
  date,
  timezone,
  agenda,
  professionals,
  filterProfessionalId = null,
  filterChairId = null,
  isRefreshing = false,
  catalogWarning = null,
}: AgendaViewProps) {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const dayLabel = formatDayLabel(date);
  const weekday = weekdayOf(date);
  const axis = computeAxis({
    date,
    timezone,
    workingHours: agenda.workingHours,
    blocks: agenda.blocks,
    appointments: agenda.appointments,
  });
  const columns = groupByProfessional({
    professionals,
    workingHours: agenda.workingHours,
    blocks: agenda.blocks,
    appointments: agenda.appointments,
    weekday,
    filterProfessionalId,
  });
  const hasActiveFilter =
    (filterProfessionalId !== null && filterProfessionalId !== "") ||
    (filterChairId !== null && filterChairId !== "");

  return (
    <section
      className={styles.agendaView}
      aria-label="Vista de agenda diaria"
      aria-busy={isRefreshing}
    >
      <div className={styles.headerBar}>
        <h2 className={styles.dayTitle}>{dayLabel}</h2>
        <div className={styles.controlsRow}>
          <span
            className={styles.liveRegion}
            aria-live="polite"
            data-testid="agenda-live-count"
          >
            {`Turnos del ${dayLabel}: ${agenda.appointments.length}`}
          </span>
          {isRefreshing && <span className={styles.liveRegion}>Actualizando…</span>}
          <button
            type="button"
            className={styles.toggleButton}
            aria-pressed={viewMode === "list"}
            onClick={() =>
              setViewMode((current) => (current === "grid" ? "list" : "grid"))
            }
          >
            Ver como lista
          </button>
        </div>
      </div>
      {catalogWarning !== null && (
        <div className={styles.bannerNote}>{catalogWarning}</div>
      )}
      {agenda.appointments.length === 0 && !hasActiveFilter ? (
        <EmptyState
          title="No hay turnos para este día"
          description="No se registraron turnos en la agenda para esta fecha."
        />
      ) : viewMode === "list" ? (
        agenda.appointments.length === 0 ? (
          <EmptyState
            title="Sin turnos para este filtro"
            description="Probá cambiando la fecha o quitando los filtros."
          />
        ) : (
          <AgendaTable
            date={date}
            timezone={timezone}
            appointments={agenda.appointments}
          />
        )
      ) : (
        <>
          {agenda.appointments.length === 0 && (
            <div className={styles.bannerNote}>Sin turnos para este filtro</div>
          )}
          <AgendaGrid date={date} timezone={timezone} axis={axis} columns={columns} />
        </>
      )}
    </section>
  );
}
