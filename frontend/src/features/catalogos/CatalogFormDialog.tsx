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
import type {
  AnyCatalogItem,
  CatalogConfig,
} from "./catalogConfigs";
import {
  createCatalogItem,
  updateCatalogItem,
} from "./catalogosApi";
import styles from "./CatalogFormDialog.module.css";

export interface CatalogFormDialogProps {
  readonly open: boolean;
  readonly onClose: () => void;
  readonly onSuccess: (message: string) => void;
  readonly config: CatalogConfig<AnyCatalogItem>;
  readonly item?: AnyCatalogItem | null;
  readonly returnFocusRef?: RefObject<HTMLElement | null>;
  readonly isMobile?: boolean;
}

export function CatalogFormDialog({
  open,
  onClose,
  onSuccess,
  config,
  item = null,
  returnFocusRef,
  isMobile,
}: CatalogFormDialogProps) {
  const { client } = useAuth();
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [generalAlert, setGeneralAlert] = useState<readonly string[] | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [prevOpen, setPrevOpen] = useState(open);
  const [prevItem, setPrevItem] = useState(item);

  const alertRef = useRef<HTMLDivElement | null>(null);
  const isEdit = Boolean(item);
  const titleId = `${config.key}-dialog-title`;

  if (open !== prevOpen || item !== prevItem) {
    setPrevOpen(open);
    setPrevItem(item);
    if (open) {
      if (item) {
        setFormData(config.toFormData(item));
      } else {
        setFormData({});
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
    setGeneralAlert(null);
    setFieldErrors({});

    const newFieldErrors: Record<string, string> = {};
    if (config.key === "prestaciones") {
      const rawDuration = formData["defaultDurationMin"]?.trim() ?? "";
      if (!/^\d+$/.test(rawDuration)) {
        newFieldErrors["defaultDurationMin"] =
          "La duración debe ser un número entero de minutos.";
      }
    }

    if (Object.keys(newFieldErrors).length > 0) {
      setFieldErrors(newFieldErrors);
      return;
    }

    setSubmitting(true);
    const payload = config.toPayload(formData);

    const res = isEdit && item
      ? await updateCatalogItem(client, config.key, item.id, payload)
      : await createCatalogItem(client, config.key, payload);

    setSubmitting(false);

    if (res.ok) {
      const entity = config.entityNameSingular;
      const capitalized = entity.charAt(0).toUpperCase() + entity.slice(1);
      const suffix = config.gender === "f" ? "a" : "o";
      const action = isEdit ? `actualizad${suffix}` : `cread${suffix}`;
      onSuccess(`${capitalized} ${action}.`);
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

  const dialogTitle = isEdit
    ? `Editar ${config.entityNameSingular}`
    : config.gender === "f"
      ? `Nueva ${config.entityNameSingular}`
      : `Nuevo ${config.entityNameSingular}`;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      labelledBy={titleId}
      returnFocusRef={returnFocusRef}
      isMobile={isMobile}
    >
      <form onSubmit={handleSubmit} noValidate className={styles.form}>
        <h2 id={titleId} className={styles.title}>
          {dialogTitle}
        </h2>

        {generalAlert !== null && generalAlert.length > 0 && (
          <div
            ref={alertRef}
            tabIndex={-1}
            role="alert"
            className={styles.alert}
          >
            {generalAlert.length === 1 ? (
              <p>{generalAlert[0]}</p>
            ) : (
              <ul className={styles.alertList}>
                {generalAlert.map((msg, i) => (
                  <li key={i}>{msg}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {config.fields.map((field) => {
          const fieldId = `${config.key}-${field.name}`;
          const hasError = Boolean(fieldErrors[field.name]);
          const errorId = `${fieldId}-error`;

          return (
            <div key={field.name} className={styles.fieldGroup}>
              <label htmlFor={fieldId} className={styles.label}>
                {field.label}
              </label>
              <input
                id={fieldId}
                name={field.name}
                type={field.type}
                maxLength={field.maxLength}
                placeholder={field.placeholder}
                value={formData[field.name] ?? ""}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, [field.name]: e.target.value }))
                }
                aria-invalid={hasError}
                aria-describedby={hasError ? errorId : undefined}
                className={`${styles.input} ${hasError ? styles.inputInvalid : ""}`}
              />
              {hasError && (
                <p id={errorId} className={styles.fieldError}>
                  {fieldErrors[field.name]}
                </p>
              )}
            </div>
          );
        })}

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.cancelButton}
            onClick={onClose}
            disabled={submitting}
          >
            Cancelar
          </button>
          <button
            type="submit"
            className={styles.submitButton}
            disabled={submitting}
          >
            {submitting ? "Guardando…" : "Guardar"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}
