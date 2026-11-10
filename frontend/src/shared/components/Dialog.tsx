import { useLayoutEffect, useRef, type KeyboardEvent, type ReactNode, type SyntheticEvent } from "react";
import styles from "./Dialog.module.css";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  labelledBy: string;
  returnFocusRef?: { current: HTMLElement | null };
  children: ReactNode;
}

export function Dialog({ open, onClose, labelledBy, returnFocusRef, children }: DialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const wasOpenRef = useRef(false);

  useLayoutEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }

    if (open && !wasOpenRef.current) {
      if (typeof dialog.showModal === "function") {
        try {
          dialog.showModal();
        } catch {
          dialog.setAttribute("open", "");
        }
      } else {
        dialog.setAttribute("open", "");
      }
      wasOpenRef.current = true;
      return;
    }

    if (!open && wasOpenRef.current) {
      if (typeof dialog.close === "function") {
        try {
          dialog.close();
        } catch {
          dialog.removeAttribute("open");
        }
      } else {
        dialog.removeAttribute("open");
      }
      wasOpenRef.current = false;
      returnFocusRef?.current?.focus();
    }
  }, [open, returnFocusRef]);

  const handleKeyDown = (event: KeyboardEvent<HTMLDialogElement>) => {
    if (event.key !== "Escape") {
      return;
    }
    event.preventDefault();
    onClose();
    returnFocusRef?.current?.focus();
  };

  const handleCancel = (event: SyntheticEvent<HTMLDialogElement>) => {
    event.preventDefault();
    onClose();
    returnFocusRef?.current?.focus();
  };

  return (
    <dialog
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby={labelledBy}
      className={styles.dialog}
      onKeyDown={handleKeyDown}
      onCancel={handleCancel}
    >
      {children}
    </dialog>
  );
}
