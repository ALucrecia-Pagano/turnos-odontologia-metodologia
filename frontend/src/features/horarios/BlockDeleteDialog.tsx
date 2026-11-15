import { Dialog } from "../../shared/components/Dialog";
import type { ProfessionalBlock } from "./horariosApi";
import { formatLocalRangeInZone } from "./horariosTime";
import styles from "./BlockDeleteDialog.module.css";

export interface BlockDeleteDialogProps {
  readonly open: boolean;
  readonly block: ProfessionalBlock | null;
  readonly timezone: string;
  readonly isDeleting?: boolean;
  readonly onConfirm: () => void;
  readonly onClose: () => void;
  readonly returnFocusRef?: { current: HTMLElement | null };
}

export function BlockDeleteDialog({
  open,
  block,
  timezone,
  isDeleting = false,
  onConfirm,
  onClose,
  returnFocusRef,
}: BlockDeleteDialogProps) {
  if (!open || block === null) {
    return null;
  }

  const { dateLabel, timeLabel } = formatLocalRangeInZone(
    block.startAt,
    block.endAt,
    timezone,
  );

  return (
    <Dialog
      open={open}
      onClose={onClose}
      labelledBy="block-delete-dialog-title"
      returnFocusRef={returnFocusRef}
    >
      <div className={styles.modalContent} data-modal-card="block-delete">
        <h2 id="block-delete-dialog-title" className={styles.title}>
          Confirmar eliminación de bloqueo
        </h2>
        <p className={styles.prompt}>
          ¿Eliminar este bloqueo del {dateLabel} de {timeLabel}?
        </p>
        <div className={styles.actionsRow}>
          <button
            type="button"
            className={styles.secondaryButton}
            onClick={onClose}
          >
            Volver
          </button>
          <button
            type="button"
            className={styles.dangerButton}
            disabled={isDeleting}
            onClick={onConfirm}
          >
            Sí, eliminar bloqueo
          </button>
        </div>
      </div>
    </Dialog>
  );
}
