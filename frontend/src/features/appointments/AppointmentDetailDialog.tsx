import { useEffect, useRef, useState } from "react";
import type { ApiClient } from "../../shared/api/client";
import type { Violation } from "../../shared/api/types";
import type { AgendaAppointment } from "../agenda/agendaApi";
import { formatLocalDate, formatTimeRange } from "../agenda/agendaTime";
import { Dialog } from "../../shared/components/Dialog";
import { StatusBadge } from "../../shared/components/StatusBadge";
import {
  cancelAppointment,
  changeAppointmentStatus,
  type AllowedStatusChange,
} from "./appointmentApi";
import { AppointmentHistoryList } from "./AppointmentHistoryList";
import styles from "./AppointmentDetailDialog.module.css";

export interface AppointmentDetailDialogProps {
  open: boolean;
  onClose: () => void;
  appointment: AgendaAppointment | null;
  client: ApiClient;
  timezone: string;
  currentUser?: { role: string; professionalId?: string | null } | null;
  returnFocusRef?: { current: HTMLElement | null };
  onStatusChanged?: (toStatus: string) => void;
  onCancelled?: () => void;
  onRequestReschedule?: (appointment: AgendaAppointment) => void;
}

function formatDisplayDate(instant: string, timezone: string): string {
  const ymd = formatLocalDate(instant, timezone);
  const [year, month, day] = ymd.split("-");
  return `${day}/${month}/${year}`;
}

export function AppointmentDetailDialog({
  open,
  onClose,
  appointment,
  client,
  timezone,
  currentUser,
  returnFocusRef,
  onStatusChanged,
  onCancelled,
  onRequestReschedule,
}: AppointmentDetailDialogProps) {
  const [prevOpen, setPrevOpen] = useState(open);
  const [violations, setViolations] = useState<readonly Violation[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isConfirmingCancel, setIsConfirmingCancel] = useState(false);
  const alertRef = useRef<HTMLDivElement>(null);

  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setViolations([]);
      setIsSubmitting(false);
      setIsConfirmingCancel(false);
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

  const timeRange = formatTimeRange(appointment.startAt, appointment.endAt, timezone);
  const dateStr = formatDisplayDate(appointment.startAt, timezone);

  const isTerminal =
    appointment.status === "atendido" ||
    appointment.status === "ausente" ||
    appointment.status === "cancelado";

  const isDentist = currentUser?.role === "odontologo";
  const isOwnAppointment =
    isDentist && currentUser.professionalId === appointment.professionalId;
  const isDentistOther = isDentist && !isOwnAppointment;

  const handleDialogClose = () => {
    if (isConfirmingCancel) {
      setIsConfirmingCancel(false);
    } else {
      onClose();
    }
  };

  const handleStatusChange = async (toStatus: AllowedStatusChange) => {
    setIsSubmitting(true);
    setViolations([]);

    const result = await changeAppointmentStatus(client, appointment.id, toStatus);
    setIsSubmitting(false);

    if (result.ok) {
      onStatusChanged?.(toStatus);
      onClose();
      return;
    }

    if (
      result.error.kind === "unprocessable" ||
      result.error.kind === "conflict" ||
      result.error.kind === "forbidden"
    ) {
      setViolations(result.error.violations);
    } else {
      setViolations([
        {
          code: "REQUEST_FAILED",
          message: "No se pudo realizar el cambio de estado.",
        },
      ]);
    }
  };

  const handleConfirmCancel = async () => {
    setIsSubmitting(true);
    setViolations([]);

    const result = await cancelAppointment(client, appointment.id);
    setIsSubmitting(false);

    if (result.ok) {
      setIsConfirmingCancel(false);
      onCancelled?.();
      onClose();
      return;
    }

    setIsConfirmingCancel(false);
    if (
      result.error.kind === "unprocessable" ||
      result.error.kind === "conflict" ||
      result.error.kind === "forbidden"
    ) {
      setViolations(result.error.violations);
    } else {
      setViolations([
        {
          code: "REQUEST_FAILED",
          message: "No se pudo cancelar el turno.",
        },
      ]);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleDialogClose}
      labelledBy="appointment-detail-title"
      returnFocusRef={returnFocusRef}
    >
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 id="appointment-detail-title" className={styles.title}>
            Detalle del turno
          </h2>
          <StatusBadge status={appointment.status} />
        </div>

        {violations.length > 0 && (
          <div
            ref={alertRef}
            tabIndex={-1}
            role="alert"
            aria-live="assertive"
            className={styles.alertContainer}
          >
            <p className={styles.alertTitle}>No se pudo actualizar el turno:</p>
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

        <div className={styles.detailsGrid}>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Paciente</span>
            <span className={styles.detailValue}>{appointment.patientName}</span>
          </div>

          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Prestación</span>
            <span className={styles.detailValue}>{appointment.serviceName}</span>
          </div>

          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Profesional</span>
            <span className={styles.detailValue}>{appointment.professionalName}</span>
          </div>

          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Sillón</span>
            <span className={styles.detailValue}>{appointment.chairName}</span>
          </div>

          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Fecha</span>
            <span className={styles.detailValue}>{dateStr}</span>
          </div>

          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Horario</span>
            <span className={styles.detailValue}>{timeRange}</span>
          </div>
        </div>

        {!isDentistOther && (
          <section aria-label="Historial de cambios" className={styles.historySection}>
            <h3 className={styles.historyHeading}>Historial de cambios</h3>
            <AppointmentHistoryList
              appointmentId={appointment.id}
              client={client}
              timezone={timezone}
            />
          </section>
        )}

        {isConfirmingCancel ? (
          <div className={styles.cancelConfirmBox}>
            <p className={styles.cancelConfirmWarning}>
              ¿Confirma que desea cancelar el turno de {appointment.patientName}?
            </p>
            <div className={styles.actionsBar} style={{ borderTop: "none", padding: 0 }}>
              <button
                type="button"
                disabled={isSubmitting}
                onClick={handleConfirmCancel}
                className={styles.dangerButton}
              >
                Confirmar cancelación
              </button>
              <button
                type="button"
                disabled={isSubmitting}
                onClick={() => setIsConfirmingCancel(false)}
                className={styles.secondaryButton}
              >
                Volver al detalle
              </button>
            </div>
          </div>
        ) : (
          <div className={styles.actionsBar}>
            {isTerminal ? (
              <p className={styles.terminalNotice}>Este turno ya no admite cambios.</p>
            ) : isDentistOther ? null : (
              <>
                {appointment.status === "reservado" && (
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={() => handleStatusChange("confirmado")}
                    className={styles.primaryButton}
                  >
                    Confirmar turno
                  </button>
                )}

                <button
                  type="button"
                  disabled={isSubmitting}
                  onClick={() => handleStatusChange("atendido")}
                  className={
                    appointment.status === "confirmado"
                      ? styles.primaryButton
                      : styles.secondaryButton
                  }
                >
                  Marcar atendido
                </button>

                <button
                  type="button"
                  disabled={isSubmitting}
                  onClick={() => handleStatusChange("ausente")}
                  className={styles.secondaryButton}
                >
                  Marcar ausente
                </button>

                {!isDentist && (
                  <>
                    <button
                      type="button"
                      disabled={isSubmitting}
                      onClick={() => {
                        onRequestReschedule?.(appointment);
                      }}
                      className={styles.secondaryButton}
                    >
                      Reprogramar
                    </button>

                    <button
                      type="button"
                      disabled={isSubmitting}
                      onClick={() => {
                        setIsConfirmingCancel(true);
                      }}
                      className={styles.dangerButton}
                    >
                      Cancelar turno
                    </button>
                  </>
                )}
              </>
            )}

            <button
              type="button"
              disabled={isSubmitting}
              onClick={onClose}
              className={styles.secondaryButton}
            >
              Cerrar
            </button>
          </div>
        )}
      </div>
    </Dialog>
  );
}
