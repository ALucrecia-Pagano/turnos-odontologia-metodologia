import { useEffect, useRef, useState } from "react";
import type { ApiClient } from "../../shared/api/client";
import type { FieldError, Violation } from "../../shared/api/types";
import { AffectedAppointments } from "./AffectedAppointments";
import {
  replaceWorkingHours,
  type AffectedAppointment,
  type WorkingHoursSlot,
} from "./horariosApi";
import { WEEKDAYS } from "./horariosTime";
import styles from "./WorkingHoursSection.module.css";

export interface WorkingHoursSectionProps {
  readonly client: ApiClient;
  readonly professionalId: string;
  readonly professionalName?: string;
  readonly timezone?: string;
  readonly initialSlots: readonly WorkingHoursSlot[];
  readonly readOnly?: boolean;
}

interface EditableSlot {
  readonly rowId: string;
  readonly weekday: number;
  readonly start: string;
  readonly end: string;
}

function toEditableSlots(slots: readonly WorkingHoursSlot[]): EditableSlot[] {
  return slots.map((slot, index) => ({
    rowId: `slot-${slot.weekday}-${index}`,
    weekday: slot.weekday,
    start: slot.start,
    end: slot.end,
  }));
}

export function WorkingHoursSection({
  client,
  professionalId,
  professionalName = "",
  timezone = "",
  initialSlots,
  readOnly = false,
}: WorkingHoursSectionProps) {
  const [prevKey, setPrevKey] = useState({ initialSlots, professionalId });
  const [slots, setSlots] = useState<EditableSlot[]>(() => toEditableSlots(initialSlots));
  const [nextRowSeq, setNextRowSeq] = useState<number>(initialSlots.length);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [outsideAppointments, setOutsideAppointments] = useState<readonly AffectedAppointment[]>(
    [],
  );
  const [violations, setViolations] = useState<Violation[]>([]);
  const [fieldErrors, setFieldErrors] = useState<FieldError[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const alertRef = useRef<HTMLDivElement | null>(null);

  if (prevKey.initialSlots !== initialSlots || prevKey.professionalId !== professionalId) {
    setPrevKey({ initialSlots, professionalId });
    setSlots(toEditableSlots(initialSlots));
    setNextRowSeq(initialSlots.length);
    setStatusMessage(null);
    setOutsideAppointments([]);
    setViolations([]);
    setFieldErrors([]);
  }

  useEffect(() => {
    if (violations.length > 0 || fieldErrors.length > 0) {
      alertRef.current?.focus();
    }
  }, [violations, fieldErrors]);

  const handleAddSlot = (weekday: number) => {
    const rowId = `slot-${weekday}-${nextRowSeq}`;
    setNextRowSeq((prev) => prev + 1);
    setSlots((prev) => [...prev, { rowId, weekday, start: "", end: "" }]);
    setStatusMessage(null);
    setViolations([]);
    setFieldErrors([]);
  };

  const handleRemoveSlot = (rowId: string) => {
    setSlots((prev) => prev.filter((item) => item.rowId !== rowId));
    setStatusMessage(null);
    setViolations([]);
    setFieldErrors([]);
  };

  const handleTimeChange = (rowId: string, field: "start" | "end", value: string) => {
    setSlots((prev) =>
      prev.map((item) => (item.rowId === rowId ? { ...item, [field]: value } : item)),
    );
    setStatusMessage(null);
    setViolations([]);
    setFieldErrors([]);
  };

  const handleSave = async () => {
    setIsSaving(true);
    setStatusMessage(null);
    setOutsideAppointments([]);
    setViolations([]);
    setFieldErrors([]);
    const orderedPayload: WorkingHoursSlot[] = [];
    for (const day of WEEKDAYS) {
      for (const slot of slots) {
        if (slot.weekday === day.weekday) {
          orderedPayload.push({
            weekday: slot.weekday,
            start: slot.start,
            end: slot.end,
          });
        }
      }
    }
    const result = await replaceWorkingHours(client, professionalId, orderedPayload);
    setIsSaving(false);
    if (result.ok) {
      setSlots(toEditableSlots(result.data.workingHours));
      setOutsideAppointments(result.data.appointmentsOutsideHours);
      setStatusMessage("Horario guardado.");
      return;
    }
    if (result.error.kind === "validation") {
      setFieldErrors(result.error.errors);
      return;
    }
    if (
      result.error.kind === "unprocessable" ||
      result.error.kind === "conflict" ||
      result.error.kind === "forbidden"
    ) {
      setViolations(result.error.violations);
    }
  };

  const flatRowOrder: string[] = [];
  for (const day of WEEKDAYS) {
    for (const slot of slots) {
      if (slot.weekday === day.weekday) {
        flatRowOrder.push(slot.rowId);
      }
    }
  }

  const isFieldInvalid = (rowId: string, fieldName: "start" | "end"): boolean => {
    const flatIdx = flatRowOrder.indexOf(rowId);
    return fieldErrors.some(
      (err) => err.field === `${flatIdx}.${fieldName}` || err.field === fieldName,
    );
  };

  return (
    <section className={styles.section} aria-labelledby="working-hours-heading">
      <div className={styles.header}>
        <div>
          <h2 id="working-hours-heading" className={styles.title}>
            Horarios semanales
          </h2>
          <p className={styles.hint}>Formato HH:MM (el fin admite 24:00)</p>
        </div>
      </div>

      {(violations.length > 0 || fieldErrors.length > 0) && (
        <div ref={alertRef} role="alert" tabIndex={-1} className={styles.alertBox}>
          {violations.map((v) => (
            <p key={`${v.code}-${v.message}`}>{v.message}</p>
          ))}
          {fieldErrors.map((err) => (
            <p key={`${err.field}-${err.message}`}>{err.message}</p>
          ))}
        </div>
      )}

      {statusMessage !== null && (
        <div role="status" aria-live="polite" className={styles.statusBanner}>
          {statusMessage}
        </div>
      )}

      <AffectedAppointments
        kind="hours"
        appointments={outsideAppointments}
        professionalName={professionalName}
        timezone={timezone}
      />

      <div className={styles.daysList}>
        {WEEKDAYS.map((day) => {
          const daySlots = slots.filter((slot) => slot.weekday === day.weekday);
          return (
            <fieldset key={day.weekday} className={styles.dayFieldset}>
              <div className={styles.dayHeader}>
                <legend className={styles.dayLegend}>{day.label}</legend>
                {!readOnly && (
                  <button
                    type="button"
                    className={styles.addButton}
                    aria-label={`Agregar tramo ${day.label}`}
                    onClick={() => handleAddSlot(day.weekday)}
                  >
                    Agregar tramo
                  </button>
                )}
              </div>
              {daySlots.length === 0 ? (
                <p className={styles.emptyDay}>Sin atención configurada</p>
              ) : (
                <div className={styles.slotsList}>
                  {daySlots.map((slot, index) => (
                    <div key={slot.rowId} className={styles.slotRow}>
                      <label className={styles.fieldLabel}>
                        <span>Inicio</span>
                        <input
                          type="text"
                          inputMode="numeric"
                          placeholder="HH:MM"
                          aria-label={`Inicio ${day.label} tramo ${index + 1}`}
                          className={styles.timeInput}
                          value={slot.start}
                          aria-invalid={isFieldInvalid(slot.rowId, "start") ? "true" : undefined}
                          readOnly={readOnly}
                          disabled={readOnly}
                          onChange={(e) => handleTimeChange(slot.rowId, "start", e.target.value)}
                        />
                      </label>
                      <label className={styles.fieldLabel}>
                        <span>Fin</span>
                        <input
                          type="text"
                          inputMode="numeric"
                          placeholder="HH:MM"
                          aria-label={`Fin ${day.label} tramo ${index + 1}`}
                          className={styles.timeInput}
                          value={slot.end}
                          aria-invalid={isFieldInvalid(slot.rowId, "end") ? "true" : undefined}
                          readOnly={readOnly}
                          disabled={readOnly}
                          onChange={(e) => handleTimeChange(slot.rowId, "end", e.target.value)}
                        />
                      </label>
                      {!readOnly && (
                        <button
                          type="button"
                          className={styles.removeButton}
                          aria-label={`Quitar tramo ${index + 1} de ${day.label}`}
                          onClick={() => handleRemoveSlot(slot.rowId)}
                        >
                          Quitar
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </fieldset>
          );
        })}
      </div>

      {!readOnly && (
        <div className={styles.actionsFooter}>
          <button
            type="button"
            className={styles.saveButton}
            disabled={isSaving}
            onClick={() => {
              void handleSave();
            }}
          >
            Guardar horario
          </button>
        </div>
      )}
    </section>
  );
}
