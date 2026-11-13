import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import type { ApiClient } from "../../shared/api/client";
import type { Violation } from "../../shared/api/types";
import type { AgendaAppointment, Chair, Professional } from "../agenda/agendaApi";
import { formatLocalDate, formatLocalTime } from "../agenda/agendaTime";
import { Dialog } from "../../shared/components/Dialog";
import { buildStartAtIso } from "./AppointmentFormDialog";
import {
  rescheduleAppointment,
  type AppointmentResponse,
} from "./appointmentApi";
import styles from "./AppointmentRescheduleDialog.module.css";

export interface AppointmentRescheduleDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (info: { date: string; time: string; appointment: AppointmentResponse }) => void;
  appointment: AgendaAppointment | null;
  client: ApiClient;
  timezone: string;
  professionals: readonly Professional[];
  chairs: readonly Chair[];
  returnFocusRef?: { current: HTMLElement | null };
}

function computeDurationMin(startAt: string, endAt: string): number {
  const start = new Date(startAt).getTime();
  const end = new Date(endAt).getTime();
  const diff = Math.round((end - start) / 60000);
  return Number.isFinite(diff) && diff > 0 ? diff : 30;
}

export function AppointmentRescheduleDialog({
  open,
  onClose,
  onSuccess,
  appointment,
  client,
  timezone,
  professionals,
  chairs,
  returnFocusRef,
}: AppointmentRescheduleDialogProps) {
  const [prevOpen, setPrevOpen] = useState(open);
  const [date, setDate] = useState(() =>
    appointment ? formatLocalDate(appointment.startAt, timezone) : "",
  );
  const [time, setTime] = useState(() =>
    appointment ? formatLocalTime(appointment.startAt, timezone) : "",
  );
  const [professionalId, setProfessionalId] = useState(
    () => appointment?.professionalId ?? "",
  );
  const [chairId, setChairId] = useState(() => appointment?.chairId ?? "");
  const [durationMin, setDurationMin] = useState<number | "">(() =>
    appointment ? computeDurationMin(appointment.startAt, appointment.endAt) : "",
  );

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [violations, setViolations] = useState<readonly Violation[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const alertRef = useRef<HTMLDivElement>(null);

  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open && appointment) {
      setDate(formatLocalDate(appointment.startAt, timezone));
      setTime(formatLocalTime(appointment.startAt, timezone));
      setProfessionalId(appointment.professionalId);
      setChairId(appointment.chairId);
      setDurationMin(computeDurationMin(appointment.startAt, appointment.endAt));
      setViolations([]);
      setFieldErrors({});
      setIsSubmitting(false);
    }
  }

  useEffect(() => {
    if (violations.length > 0) {
      alertRef.current?.focus();
    }
  }, [violations]);

  if (!open || !appointment) {
    return null;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (durationMin === "") {
      return;
    }

    const startAt = buildStartAtIso(date, time, timezone);
    setIsSubmitting(true);
    setViolations([]);
    setFieldErrors({});

    const result = await rescheduleAppointment(client, appointment.id, {
      startAt,
      professionalId,
      chairId,
      durationMin: Number(durationMin),
    });
    setIsSubmitting(false);

    if (result.ok) {
      onSuccess?.({ date, time, appointment: result.data });
      onClose();
      return;
    }

    if (result.error.kind === "validation") {
      const mapped: Record<string, string> = {};
      for (const err of result.error.errors) {
        if (err.field) {
          mapped[err.field] = err.message;
        }
      }
      setFieldErrors(mapped);
      setViolations([]);
    } else if (
      result.error.kind === "conflict" ||
      result.error.kind === "unprocessable" ||
      result.error.kind === "forbidden"
    ) {
      setFieldErrors({});
      setViolations(result.error.violations);
    } else {
      setViolations([
        {
          code: "REQUEST_FAILED",
          message: "No se pudo reprogramar el turno.",
        },
      ]);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      labelledBy="reschedule-dialog-title"
      returnFocusRef={returnFocusRef}
    >
      <div className={styles.container}>
        <h2 id="reschedule-dialog-title" className={styles.title}>
          Reprogramar turno
        </h2>

        {violations.length > 0 && (
          <div
            ref={alertRef}
            tabIndex={-1}
            role="alert"
            aria-live="assertive"
            className={styles.alertContainer}
          >
            <p className={styles.alertTitle}>No se pudo reprogramar el turno:</p>
            <ul className={styles.alertList}>
              {violations.map((v, i) => (
                <li key={i}>
                  <span className={styles.codeBadge}>{v.code}</span>
                  {v.message}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className={styles.readonlySection}>
          <div className={styles.readonlyItem}>
            <span className={styles.readonlyLabel}>Paciente</span>
            <span className={styles.readonlyValue}>{appointment.patientName}</span>
          </div>

          <div className={styles.readonlyItem}>
            <span className={styles.readonlyLabel}>Prestación</span>
            <span className={styles.readonlyValue}>{appointment.serviceName}</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.gridTwoCols}>
            <div className={styles.field}>
              <label htmlFor="reschedule-date" className={styles.label}>
                Fecha
              </label>
              <input
                id="reschedule-date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className={styles.input}
                required
                aria-invalid={fieldErrors.startAt ? "true" : undefined}
              />
              {fieldErrors.startAt && (
                <p className={styles.fieldError}>{fieldErrors.startAt}</p>
              )}
            </div>

            <div className={styles.field}>
              <label htmlFor="reschedule-time" className={styles.label}>
                Hora
              </label>
              <input
                id="reschedule-time"
                type="time"
                step="300"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className={styles.input}
                required
                aria-invalid={fieldErrors.startAt ? "true" : undefined}
              />
            </div>
          </div>

          <div className={styles.gridTwoCols}>
            <div className={styles.field}>
              <label htmlFor="reschedule-professional" className={styles.label}>
                Profesional
              </label>
              <select
                id="reschedule-professional"
                value={professionalId}
                onChange={(e) => setProfessionalId(e.target.value)}
                className={styles.select}
                required
                aria-invalid={fieldErrors.professionalId ? "true" : undefined}
              >
                {professionals
                  .filter((p) => p.active || p.id === appointment.professionalId)
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.fullName}
                    </option>
                  ))}
              </select>
              {fieldErrors.professionalId && (
                <p className={styles.fieldError}>{fieldErrors.professionalId}</p>
              )}
            </div>

            <div className={styles.field}>
              <label htmlFor="reschedule-chair" className={styles.label}>
                Sillón
              </label>
              <select
                id="reschedule-chair"
                value={chairId}
                onChange={(e) => setChairId(e.target.value)}
                className={styles.select}
                required
                aria-invalid={fieldErrors.chairId ? "true" : undefined}
              >
                {chairs
                  .filter((c) => c.active || c.id === appointment.chairId)
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
              </select>
              {fieldErrors.chairId && (
                <p className={styles.fieldError}>{fieldErrors.chairId}</p>
              )}
            </div>
          </div>

          <div className={styles.field}>
            <label htmlFor="reschedule-duration" className={styles.label}>
              Duración (minutos)
            </label>
            <input
              id="reschedule-duration"
              type="number"
              step="5"
              min="5"
              max="480"
              value={durationMin}
              onChange={(e) =>
                setDurationMin(e.target.value === "" ? "" : Number(e.target.value))
              }
              className={styles.input}
              required
              aria-invalid={fieldErrors.durationMin ? "true" : undefined}
            />
            {fieldErrors.durationMin && (
              <p className={styles.fieldError}>{fieldErrors.durationMin}</p>
            )}
          </div>

          <div className={styles.actionsBar}>
            <button
              type="submit"
              disabled={isSubmitting}
              className={styles.primaryButton}
            >
              Guardar reprogramación
            </button>
            <button
              type="button"
              disabled={isSubmitting}
              onClick={onClose}
              className={styles.secondaryButton}
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </Dialog>
  );
}
