import { useState, type RefObject } from "react";
import { useAuth } from "../auth/AuthContext";
import { getApiErrorMessages } from "../../shared/api/errors";
import { Dialog } from "../../shared/components/Dialog";
import type { AnyCatalogItem, CatalogConfig } from "./catalogConfigs";
import { deactivateCatalogItem, reactivateCatalogItem } from "./catalogosApi";
import modalCardStyles from "./modalCard.module.css";
import styles from "./CatalogConfirmDialog.module.css";

export interface CatalogConfirmDialogProps {
  readonly open: boolean;
  readonly onClose: () => void;
  readonly onConfirmed: (message: string) => void;
  readonly config: CatalogConfig<AnyCatalogItem>;
  readonly item: AnyCatalogItem | null;
  readonly action: "deactivate" | "reactivate";
  readonly returnFocusRef?: RefObject<HTMLElement | null>;
  readonly isMobile?: boolean;
}

function getItemName(item: AnyCatalogItem | null): string {
  if (!item) return "";
  if ("fullName" in item) return item.fullName;
  return item.name;
}

export function CatalogConfirmDialog({
  open,
  onClose,
  onConfirmed,
  config,
  item,
  action,
  returnFocusRef,
  isMobile,
}: CatalogConfirmDialogProps) {
  const { client } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [alertMessages, setAlertMessages] = useState<readonly string[] | null>(null);

  if (!open || item === null) {
    return null;
  }

  const titleId = `${config.key}-confirm-dialog-title`;
  const itemName = getItemName(item);
  const isDeactivate = action === "deactivate";

  const dialogTitle = isDeactivate
    ? `Desactivar ${config.entityNameSingular}`
    : `Reactivar ${config.entityNameSingular}`;

  const handleConfirm = async () => {
    setSubmitting(true);
    setAlertMessages(null);

    const res = isDeactivate
      ? await deactivateCatalogItem(client, config.key, item.id)
      : await reactivateCatalogItem(client, config.key, item.id);

    setSubmitting(false);

    if (res.ok) {
      const entity = config.entityNameSingular;
      const capitalized = entity.charAt(0).toUpperCase() + entity.slice(1);
      const suffix = config.gender === "f" ? "a" : "o";
      const actionWord = isDeactivate ? `desactivad${suffix}` : `reactivad${suffix}`;
      onConfirmed(`${capitalized} ${actionWord}.`);
      onClose();
    } else {
      setAlertMessages(getApiErrorMessages(res.error));
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
      <div className={`${modalCardStyles.modalContent} ${styles.content}`} data-modal-card="catalog-confirm">
        <h2 id={titleId} className={styles.title}>
          {dialogTitle}
        </h2>

        {alertMessages !== null && alertMessages.length > 0 && (
          <div role="alert" className={styles.alert}>
            {alertMessages.join(" ")}
          </div>
        )}

        <p className={styles.prompt}>
          ¿Desea {isDeactivate ? "desactivar" : "reactivar"}{" "}
          {config.gender === "f" ? "la" : "el"} {config.entityNameSingular}{" "}
          <strong>{itemName}</strong>?
        </p>

        {isDeactivate && (
          <p className={styles.warning}>Los turnos ya dados no cambian.</p>
        )}

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.secondaryButton}
            onClick={onClose}
            disabled={submitting}
          >
            Volver
          </button>
          <button
            type="button"
            className={isDeactivate ? styles.dangerButton : styles.primaryButton}
            onClick={handleConfirm}
            disabled={submitting}
          >
            {submitting
              ? isDeactivate
                ? "Desactivando…"
                : "Reactivando…"
              : isDeactivate
                ? "Sí, desactivar"
                : "Sí, reactivar"}
          </button>
        </div>
      </div>
    </Dialog>
  );
}
