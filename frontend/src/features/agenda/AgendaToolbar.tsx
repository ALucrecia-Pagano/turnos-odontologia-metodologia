import type { Chair, Professional } from "./agendaApi";
import { compareProfessionals, formatProfessionalLabel } from "./agendaLayout";
import styles from "./AgendaToolbar.module.css";

export const CHAIR_FILTER_HELP_TEXT =
  "El filtro por sillón solo afecta los turnos; los horarios y bloqueos se siguen mostrando.";

export interface AgendaToolbarProps {
  readonly date: string;
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
  readonly invalidDateNotice?: string | null;
}

function compareChairs(a: Chair, b: Chair): number {
  const byName = a.name.localeCompare(b.name, "es", { sensitivity: "base" });
  if (byName !== 0) {
    return byName;
  }
  return a.id.localeCompare(b.id);
}

export function AgendaToolbar({
  date,
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
  invalidDateNotice = null,
}: AgendaToolbarProps) {
  const sortedProfessionals = [...professionals].sort(compareProfessionals);
  const sortedChairs = [...chairs].sort(compareChairs);
  const hasChairFilter = chairId !== null && chairId !== "";

  return (
    <div className={styles.toolbar} aria-label="Controles de agenda">
      <div className={styles.controlsRow}>
        <div className={styles.navGroup}>
          <button
            type="button"
            className={styles.actionButton}
            onClick={onPrevDay}
          >
            Anterior
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
            Siguiente
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
        </div>

        <div className={styles.filterGroup}>
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
        </div>
      </div>

      {invalidDateNotice !== null && (
        <p className={styles.helpText}>{invalidDateNotice}</p>
      )}
      {hasChairFilter && <p className={styles.helpText}>{CHAIR_FILTER_HELP_TEXT}</p>}
    </div>
  );
}
