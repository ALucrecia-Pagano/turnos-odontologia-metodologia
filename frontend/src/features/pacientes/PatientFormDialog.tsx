import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type RefObject,
} from "react";
import { useAuth } from "../auth/AuthContext";
import { getApiErrorMessages } from "../../shared/api/errors";
import { Dialog } from "../../shared/components/Dialog";
import {
  createPatient,
  updatePatient,
  type PatientItem,
  type PatientPayload,
} from "./pacientesApi";
import styles from "./PatientFormDialog.module.css";

export interface PatientFormDialogProps {
  readonly open: boolean;
  readonly onClose: () => void;
  readonly onSuccess: (message: string) => void;
  readonly patient?: PatientItem | null;
  readonly returnFocusRef?: RefObject<HTMLElement | null>;
  readonly isMobile?: boolean;
}

export function PatientFormDialog({
  open,
  onClose,
  onSuccess,
  patient = null,
  returnFocusRef,
  isMobile,
}: PatientFormDialogProps) {
  const { client } = useAuth();
  const [fullName, setFullName] = useState("");
  const [dni, setDni] = useState("");
  const [phone, setPhone] = useState("");
  const [healthInsurance, setHealthInsurance] = useState("");
  const [generalAlert, setGeneralAlert] = useState<readonly string[] | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [prevOpen, setPrevOpen] = useState(open);
  const [prevPatient, setPrevPatient] = useState(patient);

  const alertRef = useRef<HTMLDivElement | null>(null);
  const isEdit = Boolean(patient);
  const titleId = isEdit ? "edit-patient-title" : "new-patient-title";

  if (open !== prevOpen || patient !== prevPatient) {
    setPrevOpen(open);
    setPrevPatient(patient);
    if (open) {
      if (patient) {
        setFullName(patient.fullName);
        setDni(patient.dni);
        setPhone(patient.phone ?? "");
        setHealthInsurance(patient.healthInsurance ?? "");
      } else {
        setFullName("");
        setDni("");
        setPhone("");
        setHealthInsurance("");
      }
      setGeneralAlert(null);
      setFieldErrors({});
      setSubmitting(false);
    }
  }

  useEffect(() => {
    if (generalAlert !== null && generalAlert.length > 0) {
      alertRef.current?.focus();
    }
  }, [generalAlert]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setGeneralAlert(null);
    setFieldErrors({});

    const payload: PatientPayload = {
      fullName,
      dni,
      phone: phone.trim() === "" ? null : phone.trim(),
      healthInsurance: healthInsurance.trim() === "" ? null : healthInsurance.trim(),
    };

    const res = isEdit && patient
      ? await updatePatient(client, patient.id, payload)
      : await createPatient(client, payload);

    setSubmitting(false);

    if (res.ok) {
      onSuccess(isEdit ? "Paciente actualizado." : "Paciente creado.");
      onClose();
    } else {
      if (res.error.kind === "validation") {
        const errorsByField: Record<string, string> = {};
        const general: string[] = [];
        for (const err of res.error.errors) {
          if (err.field) {
            errorsByField[err.field] = err.message;
          } else {
            general.push(err.message);
          }
        }
        setFieldErrors(errorsByField);
        if (general.length > 0) {
          setGeneralAlert(general);
        }
      } else {
        setGeneralAlert(getApiErrorMessages(res.error));
      }
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      labelledBy={titleId}
      returnFocusRef={returnFocusRef}
      isMobile={isMobile}
    >
      <form className={styles.form} onSubmit={handleSubmit} noValidate>
        <h2 id={titleId} className={styles.title}>
          {isEdit ? "Editar paciente" : "Nuevo paciente"}
        </h2>

        {generalAlert !== null && generalAlert.length > 0 && (
          <div
            ref={alertRef}
            role="alert"
            tabIndex={-1}
            className={styles.alert}
          >
            {generalAlert.length === 1 ? (
              generalAlert[0]
            ) : (
              <ul className={styles.alertList}>
                {generalAlert.map((msg, i) => (
                  <li key={i}>{msg}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        <div className={styles.fieldGroup}>
          <label htmlFor="patient-fullName" className={styles.label}>
            Nombre y apellido
          </label>
          <input
            id="patient-fullName"
            type="text"
            className={`${styles.input} ${fieldErrors["fullName"] ? styles.inputInvalid : ""}`}
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            maxLength={255}
            aria-invalid={fieldErrors["fullName"] ? "true" : undefined}
            aria-describedby={fieldErrors["fullName"] ? "fullName-error" : undefined}
          />
          {fieldErrors["fullName"] && (
            <p id="fullName-error" className={styles.fieldError}>
              {fieldErrors["fullName"]}
            </p>
          )}
        </div>

        <div className={styles.fieldGroup}>
          <label htmlFor="patient-dni" className={styles.label}>
            DNI
          </label>
          <input
            id="patient-dni"
            type="text"
            className={`${styles.input} ${fieldErrors["dni"] ? styles.inputInvalid : ""}`}
            value={dni}
            onChange={(e) => setDni(e.target.value)}
            maxLength={10}
            aria-invalid={fieldErrors["dni"] ? "true" : undefined}
            aria-describedby={fieldErrors["dni"] ? "dni-error" : undefined}
          />
          {fieldErrors["dni"] && (
            <p id="dni-error" className={styles.fieldError}>
              {fieldErrors["dni"]}
            </p>
          )}
        </div>

        <div className={styles.fieldGroup}>
          <label htmlFor="patient-phone" className={styles.label}>
            Teléfono
          </label>
          <input
            id="patient-phone"
            type="text"
            className={`${styles.input} ${fieldErrors["phone"] ? styles.inputInvalid : ""}`}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            maxLength={50}
            aria-invalid={fieldErrors["phone"] ? "true" : undefined}
            aria-describedby={fieldErrors["phone"] ? "phone-error" : undefined}
          />
          {fieldErrors["phone"] && (
            <p id="phone-error" className={styles.fieldError}>
              {fieldErrors["phone"]}
            </p>
          )}
        </div>

        <div className={styles.fieldGroup}>
          <label htmlFor="patient-healthInsurance" className={styles.label}>
            Obra social
          </label>
          <input
            id="patient-healthInsurance"
            type="text"
            className={`${styles.input} ${fieldErrors["healthInsurance"] ? styles.inputInvalid : ""}`}
            value={healthInsurance}
            onChange={(e) => setHealthInsurance(e.target.value)}
            maxLength={255}
            aria-invalid={fieldErrors["healthInsurance"] ? "true" : undefined}
            aria-describedby={fieldErrors["healthInsurance"] ? "healthInsurance-error" : undefined}
          />
          {fieldErrors["healthInsurance"] && (
            <p id="healthInsurance-error" className={styles.fieldError}>
              {fieldErrors["healthInsurance"]}
            </p>
          )}
        </div>

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.cancelButton}
            onClick={onClose}
          >
            Cancelar
          </button>
          <button
            type="submit"
            className={styles.saveButton}
            disabled={submitting}
          >
            Guardar
          </button>
        </div>
      </form>
    </Dialog>
  );
}
