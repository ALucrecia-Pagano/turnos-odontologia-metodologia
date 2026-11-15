import { useEffect, useRef, useState, type FormEvent } from "react";
import type { ApiClient } from "../../shared/api/client";
import type { FieldError, Violation } from "../../shared/api/types";
import { Dialog } from "../../shared/components/Dialog";
import { createBlock, type CreateBlockResponse } from "./horariosApi";
import { buildLocalInstantIso } from "./horariosTime";
import styles from "./BlockFormDialog.module.css";

export interface BlockFormDialogProps {
  readonly open: boolean;
  readonly onClose: () => void;
  readonly onCreated: (response: CreateBlockResponse) => void;
  readonly client: ApiClient;
  readonly professionalId: string;
  readonly timezone: string;
  readonly defaultDate?: string;
  readonly returnFocusRef?: { current: HTMLElement | null };
  readonly isMobile?: boolean;
}

export function BlockFormDialog({
  open,
  onClose,
  onCreated,
  client,
  professionalId,
  timezone,
  defaultDate = "2026-05-06",
  returnFocusRef,
  isMobile,
}: BlockFormDialogProps) {
  const [prevOpen, setPrevOpen] = useState(open);
  const [date, setDate] = useState(defaultDate);
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [fieldErrors, setFieldErrors] = useState<FieldError[]>([]);
  const alertRef = useRef<HTMLDivElement | null>(null);

  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setDate(defaultDate);
      setStartTime("");
      setEndTime("");
      setReason("");
      setIsSubmitting(false);
      setViolations([]);
      setFieldErrors([]);
    }
  }

  useEffect(() => {
    if (violations.length > 0 || fieldErrors.length > 0) {
      alertRef.current?.focus();
    }
  }, [violations, fieldErrors]);

  if (!open) {
    return null;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setViolations([]);
    setFieldErrors([]);
    const startAt = buildLocalInstantIso(date, startTime, timezone);
    const endAt = buildLocalInstantIso(date, endTime, timezone);
    const result = await createBlock(client, professionalId, {
      startAt,
      endAt,
      reason: reason.trim() !== "" ? reason.trim() : undefined,
    });
    setIsSubmitting(false);
    if (result.ok) {
      onCreated(result.data);
      onClose();
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

  return (
    <Dialog
      open={open}
      onClose={onClose}
      labelledBy="block-form-dialog-title"
      returnFocusRef={returnFocusRef}
      isMobile={isMobile}
    >
      <div className={styles.modalContent} data-modal-card="block-form">
        <h2 id="block-form-dialog-title" className={styles.title}>
          Nuevo bloqueo
        </h2>
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
        <form
          className={styles.form}
          onSubmit={(e) => {
            void handleSubmit(e);
          }}
        >
          <div className={styles.field}>
            <label htmlFor="block-date" className={styles.label}>
              Fecha
            </label>
            <input
              id="block-date"
              type="date"
              className={styles.input}
              value={date}
              onChange={(e) => {
                setDate(e.target.value);
                setViolations([]);
                setFieldErrors([]);
              }}
            />
          </div>

          <div className={styles.gridTwoCols}>
            <div className={styles.field}>
              <label htmlFor="block-start-time" className={styles.label}>
                Hora de inicio
              </label>
              <input
                id="block-start-time"
                type="text"
                inputMode="numeric"
                placeholder="HH:MM"
                className={styles.input}
                value={startTime}
                aria-invalid={
                  fieldErrors.some((err) => err.field === "startAt") ? "true" : undefined
                }
                onChange={(e) => {
                  setStartTime(e.target.value);
                  setViolations([]);
                  setFieldErrors([]);
                }}
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="block-end-time" className={styles.label}>
                Hora de fin
              </label>
              <input
                id="block-end-time"
                type="text"
                inputMode="numeric"
                placeholder="HH:MM"
                className={styles.input}
                value={endTime}
                aria-invalid={
                  fieldErrors.some((err) => err.field === "endAt") ? "true" : undefined
                }
                onChange={(e) => {
                  setEndTime(e.target.value);
                  setViolations([]);
                  setFieldErrors([]);
                }}
              />
            </div>
          </div>

          <div className={styles.field}>
            <label htmlFor="block-reason" className={styles.label}>
              Motivo (opcional)
            </label>
            <input
              id="block-reason"
              type="text"
              className={styles.input}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </div>

          <div className={styles.actionsRow}>
            <button type="button" className={styles.secondaryButton} onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className={styles.primaryButton} disabled={isSubmitting}>
              Guardar bloqueo
            </button>
          </div>
        </form>
      </div>
    </Dialog>
  );
}
