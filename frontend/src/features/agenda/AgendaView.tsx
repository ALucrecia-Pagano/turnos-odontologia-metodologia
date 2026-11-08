import { useState } from "react";
import { EmptyState } from "../../shared/components/EmptyState";
import type { AgendaResponse, Professional } from "./agendaApi";
import { AgendaGrid } from "./AgendaGrid";
import {
  computeAxis,
  computeWeekAxis,
  groupByDayForProfessional,
  groupByProfessional,
} from "./agendaLayout";
import { AgendaTable } from "./AgendaTable";
import { formatDayLabel, weekdayOf, weekRangeOf } from "./agendaTime";
import styles from "./AgendaView.module.css";

export interface AgendaViewProps {
  readonly date: string;
  readonly timezone: string;
  readonly agenda: AgendaResponse;
  readonly professionals: readonly Professional[];
  readonly view?: "day" | "week";
  readonly selectedProfessionalId?: string | null;
  readonly todayDate?: string;
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
  view = "day",
  selectedProfessionalId = null,
  todayDate,
  filterProfessionalId = null,
  filterChairId = null,
  isRefreshing = false,
  catalogWarning = null,
}: AgendaViewProps) {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const isWeekView = view === "week";
  const dayLabel = formatDayLabel(date);
  const weekday = weekdayOf(date);

  const effectiveProfessionalId = filterProfessionalId ?? selectedProfessionalId;
  const currentProfessional = professionals.find((p) => p.id === effectiveProfessionalId);
  const professionalName = currentProfessional ? currentProfessional.fullName : "";

  const week = isWeekView ? weekRangeOf(date) : null;

  const axis =
    isWeekView && week !== null
      ? computeWeekAxis({
          mondayDate: week.monday,
          timezone,
          workingHours: agenda.workingHours,
          blocks: agenda.blocks,
          appointments: agenda.appointments,
        })
      : computeAxis({
          date,
          timezone,
          workingHours: agenda.workingHours,
          blocks: agenda.blocks,
          appointments: agenda.appointments,
        });

  const columns =
    isWeekView && week !== null
      ? groupByDayForProfessional({
          professionalId: effectiveProfessionalId ?? "",
          mondayDate: week.monday,
          timezone,
          todayDate,
          workingHours: agenda.workingHours,
          blocks: agenda.blocks,
          appointments: filterChairId
            ? agenda.appointments.filter((a) => a.chairId === filterChairId)
            : agenda.appointments,
        })
      : groupByProfessional({
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

  const hasActiveChairFilter = filterChairId !== null && filterChairId !== "";

  return (
    <section
      className={styles.agendaView}
      aria-label={isWeekView ? "Vista de agenda semanal" : "Vista de agenda diaria"}
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
      {!isWeekView && agenda.appointments.length === 0 && !hasActiveFilter ? (
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
          {!isWeekView && agenda.appointments.length === 0 && (
            <div className={styles.bannerNote}>Sin turnos para este filtro</div>
          )}
          {isWeekView && agenda.appointments.length === 0 && (
            <div className={styles.bannerNote}>
              {hasActiveChairFilter
                ? "Sin turnos para este filtro"
                : `No hay turnos esta semana para ${professionalName}`}
            </div>
          )}
          <AgendaGrid date={date} timezone={timezone} axis={axis} columns={columns} />
        </>
      )}
    </section>
  );
}
