import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import type { ApiClient } from "../../shared/api/client";
import type { Violation } from "../../shared/api/types";
import type { Chair, Professional } from "../agenda/agendaApi";
import { Dialog } from "../../shared/components/Dialog";
import { PatientSearchGroup } from "./PatientSearchGroup";
import styles from "./AppointmentFormDialog.module.css";

export interface Service {
  id: string;
  name: string;
  defaultDurationMin: number;
  active: boolean;
}

export interface AppointmentFormDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (info: { date: string; time: string }) => void;
  client: ApiClient;
  timezone: string;
  effectiveDate: string;
  initialProfessionalId?: string | null;
  initialChairId?: string | null;
  professionals: readonly Professional[];
  chairs: readonly Chair[];
  services?: readonly Service[];
  returnFocusRef?: { current: HTMLElement | null };
}

export function buildStartAtIso(
  dateStr: string,
  timeStr: string,
  timeZone: string,
): string {
  const partsDate = dateStr.split("-").map(Number);
  const partsTime = timeStr.split(":").map(Number);
  const year = partsDate[0] ?? 2026;
  const month = partsDate[1] ?? 1;
  const day = partsDate[2] ?? 1;
  const hours = partsTime[0] ?? 0;
  const minutes = partsTime[1] ?? 0;
  const probeDate = new Date(Date.UTC(year, month - 1, day, hours, minutes));

  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    timeZoneName: "longOffset",
  }).formatToParts(probeDate);
  const rawOffset = parts.find((p) => p.type === "timeZoneName")?.value ?? "GMT";
  const offset = rawOffset.replace("GMT", "") || "+00:00";

  return `${dateStr}T${timeStr}:00${offset}`;
}

export function AppointmentFormDialog({
  open,
  onClose,
  onSuccess,
  client,
  timezone,
  effectiveDate,
  initialProfessionalId,
  initialChairId,
  professionals,
  chairs,
  services: initialServices,
  returnFocusRef,
}: AppointmentFormDialogProps) {
  const [prevOpen, setPrevOpen] = useState(open);
  const [date, setDate] = useState(effectiveDate);
  const [time, setTime] = useState("");
  const [professionalId, setProfessionalId] = useState(initialProfessionalId ?? "");
  const [chairId, setChairId] = useState(initialChairId ?? "");
  const [serviceId, setServiceId] = useState("");
  const [durationMin, setDurationMin] = useState<number | "">("");
  const [patientId, setPatientId] = useState<string | null>(null);

  const [services, setServices] = useState<readonly Service[]>(initialServices ?? []);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const patientSearchInputRef = useRef<HTMLInputElement>(null);
  const alertRef = useRef<HTMLDivElement>(null);

  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setDate(effectiveDate);
      setTime("");
      setProfessionalId(initialProfessionalId ?? "");
      setChairId(initialChairId ?? "");
      setServiceId("");
      setDurationMin("");
      setPatientId(null);
      setViolations([]);
      setFieldErrors({});
    }
  }

  // Foco en el primer control interactivo al abrir
  useEffect(() => {
    if (open) {
      patientSearchInputRef.current?.focus();
    }
  }, [open]);

  // Carga de catálogo de prestaciones si no viene pre-cargado
  useEffect(() => {
    if (open && (!initialServices || initialServices.length === 0)) {
      void client.request("/services?active=true").then((res) => {
        if (res.ok && Array.isArray(res.data)) {
          setServices(res.data as unknown as Service[]);
        }
      });
    }
  }, [open, client, initialServices]);

  const handleServiceChange = (selectedId: string) => {
    setServiceId(selectedId);
    const s = services.find((srv) => srv.id === selectedId);
    if (s) {
      setDurationMin(s.defaultDurationMin);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setViolations([]);
    setFieldErrors({});

    if (!patientId || !professionalId || !chairId || !serviceId || !date || !time) {
      return;
    }

    const startAt = buildStartAtIso(date, time, timezone);
    const payload: {
      patientId: string;
      professionalId: string;
      chairId: string;
      serviceId: string;
      startAt: string;
      durationMin?: number;
    } = {
      patientId,
      professionalId,
      chairId,
      serviceId,
      startAt,
    };

    if (durationMin !== "") {
      payload.durationMin = Number(durationMin);
    }

    setIsSubmitting(true);
    const result = await client.request("/appointments", {
      method: "POST",
      body: payload,
    });
    setIsSubmitting(false);

    if (result.ok && result.status === 201) {
      onSuccess?.({ date, time });
      onClose();
      return;
    }

    if (!result.ok) {
      if (
        result.error.kind === "conflict" ||
        result.error.kind === "unprocessable" ||
        result.error.kind === "forbidden"
      ) {
        setViolations(result.error.violations);
        setTimeout(() => alertRef.current?.focus(), 0);
      } else if (result.error.kind === "validation") {
        const mappedErrors: Record<string, string> = {};
        for (const err of result.error.errors) {
          if (err.field) {
            mappedErrors[err.field] = err.message;
          }
        }
        setFieldErrors(mappedErrors);
        setViolations([]);
      }
    }
  };

  const handleDialogClose = () => {
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleDialogClose}
      labelledBy="appointment-dialog-title"
      returnFocusRef={returnFocusRef}
    >
      <div className={styles.modalContent}>
        <h2 id="appointment-dialog-title" className={styles.title}>
          Nuevo turno
        </h2>

        {violations.length > 0 && (
          <div
            ref={alertRef}
            tabIndex={-1}
            role="alert"
            aria-live="assertive"
            className={styles.alertContainer}
          >
            <p className={styles.alertTitle}>No se pudo agendar el turno:</p>
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

        <form onSubmit={handleSubmit} className={styles.form}>
          <PatientSearchGroup
            client={client}
            selectedPatientId={patientId}
            onSelectPatient={setPatientId}
            inputRef={patientSearchInputRef}
          />

          <div className={styles.gridTwoCols}>
            <div className={styles.field}>
              <label htmlFor="appointment-date" className={styles.label}>
                Fecha
              </label>
              <input
                id="appointment-date"
                type="date"
                className={styles.input}
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
                aria-invalid={fieldErrors.startAt ? "true" : undefined}
              />
              {fieldErrors.startAt && (
                <p className={styles.fieldError}>{fieldErrors.startAt}</p>
              )}
            </div>

            <div className={styles.field}>
              <label htmlFor="appointment-time" className={styles.label}>
                Hora
              </label>
              <input
                id="appointment-time"
                type="time"
                step="300"
                className={styles.input}
                value={time}
                onChange={(e) => setTime(e.target.value)}
                required
                aria-invalid={fieldErrors.startAt ? "true" : undefined}
              />
            </div>
          </div>

          <div className={styles.gridTwoCols}>
            <div className={styles.field}>
              <label htmlFor="appointment-professional" className={styles.label}>
                Profesional
              </label>
              <select
                id="appointment-professional"
                className={styles.select}
                value={professionalId}
                onChange={(e) => setProfessionalId(e.target.value)}
                required
                aria-invalid={fieldErrors.professionalId ? "true" : undefined}
              >
                <option value="">Seleccionar profesional...</option>
                {professionals
                  .filter((p) => p.active)
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
              <label htmlFor="appointment-chair" className={styles.label}>
                Sillón
              </label>
              <select
                id="appointment-chair"
                className={styles.select}
                value={chairId}
                onChange={(e) => setChairId(e.target.value)}
                required
                aria-invalid={fieldErrors.chairId ? "true" : undefined}
              >
                <option value="">Seleccionar sillón...</option>
                {chairs
                  .filter((c) => c.active)
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

          <div className={styles.gridTwoCols}>
            <div className={styles.field}>
              <label htmlFor="appointment-service" className={styles.label}>
                Prestación
              </label>
              <select
                id="appointment-service"
                className={styles.select}
                value={serviceId}
                onChange={(e) => handleServiceChange(e.target.value)}
                required
                aria-invalid={fieldErrors.serviceId ? "true" : undefined}
              >
                <option value="">Seleccionar prestación...</option>
                {services
                  .filter((s) => s.active)
                  .map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
              </select>
              {fieldErrors.serviceId && (
                <p className={styles.fieldError}>{fieldErrors.serviceId}</p>
              )}
            </div>

            <div className={styles.field}>
              <label htmlFor="appointment-duration" className={styles.label}>
                Duración (minutos)
              </label>
              <input
                id="appointment-duration"
                type="number"
                min="5"
                max="480"
                step="5"
                className={styles.input}
                value={durationMin}
                onChange={(e) => {
                  const val = e.target.value;
                  setDurationMin(val === "" ? "" : Number(val));
                }}
                aria-invalid={fieldErrors.durationMin ? "true" : undefined}
              />
              {fieldErrors.durationMin && (
                <p className={styles.fieldError}>{fieldErrors.durationMin}</p>
              )}
            </div>
          </div>

          <div className={styles.actionsRow}>
            <button
              type="button"
              className={styles.secondaryButton}
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={styles.primaryButton}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Guardando..." : "Crear turno"}
            </button>
          </div>
        </form>
      </div>
    </Dialog>
  );
}
