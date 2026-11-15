import { useEffect, useState } from "react";
import type { UserRole } from "../../shared/api/types";
import type { Chair, Professional } from "./agendaApi";
import { compareProfessionals, formatProfessionalLabel } from "./agendaLayout";
import styles from "./AgendaToolbar.module.css";

export const CHAIR_FILTER_HELP_TEXT =
  "El filtro por sillón solo afecta los turnos; los horarios y bloqueos se siguen mostrando.";

export const CHAIR_VIEW_HELP_TEXT =
  "Cada columna es un sillón; el filtro de sillón reduce las columnas y el de profesional recalcula los horarios.";

export interface AgendaToolbarProps {
  readonly date: string;
  readonly view?: "day" | "week" | "chair";
  readonly professionalId: string | null;
  readonly chairId: string | null;
  readonly professionals: readonly Professional[];
  readonly chairs: readonly Chair[];
  readonly onSelectProfessional: (id: string | null) => void;
  readonly onSelectChair: (id: string | null) => void;
  readonly onClearFilters: () => void;
  readonly onPrevDay?: () => void;
  readonly onNextDay?: () => void;
  readonly onToday?: () => void;
  readonly onSelectDate?: (nextDate: string) => void;
  readonly onRefresh?: () => void;
  readonly onSelectView?: (view: "day" | "week" | "chair") => void;
  readonly invalidDateNotice?: string | null;
  readonly userRole?: UserRole | null;
  readonly onNewAppointment?: () => void;
  readonly newAppointmentRef?: { current: HTMLButtonElement | null };
  readonly isMobile?: boolean;
}

function compareChairs(a: Chair, b: Chair): number {
  const byName = a.name.localeCompare(a.name, "es", { sensitivity: "base" });
  if (byName !== 0) {
    return byName;
  }
  return a.id.localeCompare(b.id);
}

export function AgendaToolbar({
  date,
  view = "day",
  professionalId,
  chairId,
  professionals,
  chairs,
  onSelectProfessional,
  onSelectChair,
  onClearFilters,
  onPrevDay,
  onNextDay,
  onToday,
  onSelectDate,
  onRefresh,
  onSelectView,
  invalidDateNotice = null,
  userRole = null,
  onNewAppointment,
  newAppointmentRef,
  isMobile,
}: AgendaToolbarProps) {
  const sortedProfessionals = [...professionals].sort(compareProfessionals);
  const sortedChairs = [...chairs].sort(compareChairs);
  const hasChairFilter = chairId !== null && chairId !== "";
  const isWeekView = view === "week";
  const isChairView = view === "chair";
  const canViewChairs = userRole === "recepcion" || userRole === "administrador";
  const prevLabel = isWeekView ? "Semana anterior" : "Anterior";
  const nextLabel = isWeekView ? "Semana siguiente" : "Siguiente";
  const canCreateAppointment =
    (userRole === "recepcion" || userRole === "administrador") &&
    onNewAppointment !== undefined;

  const [isMobileDevice, setIsMobileDevice] = useState(() => {
    if (typeof window !== "undefined" && typeof window.matchMedia === "function") {
      return window.matchMedia("(max-width: 640px)").matches;
    }
    return false;
  });

  const isMobileEffective = isMobile ?? isMobileDevice;
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);

  useEffect(() => {
    if (isMobile !== undefined) {
      return;
    }
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }
    const mql = window.matchMedia("(max-width: 640px)");
    const handler = (e: MediaQueryListEvent) => {
      setIsMobileDevice(e.matches);
    };
    if (typeof mql.addEventListener === "function") {
      mql.addEventListener("change", handler);
      return () => mql.removeEventListener("change", handler);
    }
  }, [isMobile]);

  const activeFiltersCount =
    (professionalId !== null && professionalId !== "" ? 1 : 0) +
    (chairId !== null && chairId !== "" ? 1 : 0);
  const filtersButtonLabel =
    activeFiltersCount > 0 ? `Filtros (${activeFiltersCount})` : "Filtros";

  const viewToggleElement = (
    <div
      className={styles.viewToggleGroup}
      role="group"
      aria-label="Modo de vista"
      data-testid="agenda-view-toggle"
    >
      <button
        type="button"
        className={view === "day" ? styles.viewToggleButtonActive : styles.viewToggleButton}
        aria-pressed={view === "day"}
        onClick={() => onSelectView?.("day")}
      >
        Día
      </button>
      <button
        type="button"
        className={isWeekView ? styles.viewToggleButtonActive : styles.viewToggleButton}
        aria-pressed={isWeekView}
        onClick={() => onSelectView?.("week")}
      >
        Semana
      </button>
      {canViewChairs && (
        <button
          type="button"
          className={isChairView ? styles.viewToggleButtonActive : styles.viewToggleButton}
          aria-pressed={isChairView}
          onClick={() => onSelectView?.("chair")}
        >
          Sillones
        </button>
      )}
    </div>
  );

  const filterFieldsElement = (
    <>
      <div className={styles.field}>
        <label htmlFor="agenda-filter-professional" className={styles.label}>
          Profesional
        </label>
        <select
          id="agenda-filter-professional"
          className={styles.select}
          value={professionalId ?? ""}
          onChange={(event) => {
            const value = event.target.value;
            onSelectProfessional(value === "" ? null : value);
          }}
        >
          <option value="">Todos</option>
          {sortedProfessionals.map((prof) => (
            <option key={prof.id} value={prof.id}>
              {formatProfessionalLabel(prof)}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.field}>
        <label htmlFor="agenda-filter-chair" className={styles.label}>
          Sillón
        </label>
        <select
          id="agenda-filter-chair"
          className={styles.select}
          value={chairId ?? ""}
          onChange={(event) => {
            const value = event.target.value;
            onSelectChair(value === "" ? null : value);
          }}
        >
          <option value="">Todos</option>
          {sortedChairs.map((chair) => (
            <option key={chair.id} value={chair.id}>
              {chair.active ? chair.name : `${chair.name} (inactivo)`}
            </option>
          ))}
        </select>
      </div>

      <button
        type="button"
        className={styles.actionButton}
        onClick={onClearFilters}
      >
        Limpiar filtros
      </button>
    </>
  );

  return (
    <div className={styles.toolbar} aria-label="Controles de agenda">
      {isMobileEffective ? (
        <div className={styles.mobileControls}>
          <div className={styles.navRow} data-testid="agenda-toolbar-nav-row">
            {viewToggleElement}
            <button
              type="button"
              className={styles.actionButton}
              onClick={onPrevDay}
              aria-label={prevLabel}
            >
              {isMobileEffective ? "‹" : prevLabel}
            </button>
            <button
              type="button"
              className={styles.actionButton}
              onClick={onToday}
            >
              Hoy
            </button>
            <button
              type="button"
              className={styles.actionButton}
              onClick={onNextDay}
              aria-label={nextLabel}
            >
              {isMobileEffective ? "›" : nextLabel}
            </button>
          </div>

          <div className={styles.actionRow} data-testid="agenda-toolbar-action-row">
            <div className={styles.dateRow} data-testid="agenda-toolbar-date-row">
              <div className={styles.fieldDate}>
                <label htmlFor="agenda-date-input" className={styles.label}>
                  Fecha
                </label>
                <input
                  id="agenda-date-input"
                  type="date"
                  className={styles.dateInput}
                  value={date}
                  onChange={(event) => {
                    const nextValue = event.target.value;
                    if (nextValue !== "") {
                      onSelectDate?.(nextValue);
                    }
                  }}
                />
              </div>

              {canCreateAppointment && (
                <button
                  ref={newAppointmentRef}
                  type="button"
                  className={styles.primaryButton}
                  onClick={onNewAppointment}
                >
                  Nuevo turno
                </button>
              )}
            </div>

            <div className={styles.filterRow} data-testid="agenda-toolbar-filter-row">
              <button
                type="button"
                className={styles.filterToggleButton}
                aria-expanded={isFiltersOpen}
                aria-controls="agenda-filters-panel"
                data-testid="agenda-toolbar-filters-toggle"
                onClick={() => setIsFiltersOpen((prev) => !prev)}
              >
                {filtersButtonLabel}
              </button>

              {onRefresh !== undefined && (
                <button
                  type="button"
                  className={styles.actionButton}
                  onClick={onRefresh}
                  aria-label="Actualizar agenda"
                >
                  ↻
                </button>
              )}
            </div>
          </div>

          <div
            id="agenda-filters-panel"
            className={isFiltersOpen ? styles.filterGroupMobileOpen : styles.filterGroupMobileClosed}
            hidden={!isFiltersOpen}
          >
            {filterFieldsElement}
          </div>
        </div>
      ) : (
        <div className={styles.controlsRow}>
          <div className={styles.navGroup}>
            {viewToggleElement}

            <button
              type="button"
              className={styles.actionButton}
              onClick={onPrevDay}
            >
              {prevLabel}
            </button>
            <button
              type="button"
              className={styles.actionButton}
              onClick={onToday}
            >
              Hoy
            </button>
            <button
              type="button"
              className={styles.actionButton}
              onClick={onNextDay}
            >
              {nextLabel}
            </button>

            <div className={styles.field}>
              <label htmlFor="agenda-date-input" className={styles.label}>
                Fecha
              </label>
              <input
                id="agenda-date-input"
                type="date"
                className={styles.dateInput}
                value={date}
                onChange={(event) => {
                  const nextValue = event.target.value;
                  if (nextValue !== "") {
                    onSelectDate?.(nextValue);
                  }
                }}
              />
            </div>

            {onRefresh !== undefined && (
              <button
                type="button"
                className={styles.actionButton}
                onClick={onRefresh}
              >
                Actualizar agenda
              </button>
            )}

            {canCreateAppointment && (
              <button
                ref={newAppointmentRef}
                type="button"
                className={styles.primaryButton}
                onClick={onNewAppointment}
              >
                Nuevo turno
              </button>
            )}
          </div>

          <div className={styles.filterGroup}>
            {filterFieldsElement}
          </div>
        </div>
      )}

      {invalidDateNotice !== null && (
        <p className={styles.helpText}>{invalidDateNotice}</p>
      )}
      {hasChairFilter && !isChairView && <p className={styles.helpText}>{CHAIR_FILTER_HELP_TEXT}</p>}
      {hasChairFilter && isChairView && <p className={styles.helpText}>{CHAIR_VIEW_HELP_TEXT}</p>}
    </div>
  );
}
