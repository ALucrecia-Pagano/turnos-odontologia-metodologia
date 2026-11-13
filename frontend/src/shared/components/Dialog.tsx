import {
  useEffect,
  useLayoutEffect,
  useRef,
  type KeyboardEvent,
  type ReactNode,
  type SyntheticEvent,
} from "react";
import styles from "./Dialog.module.css";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  labelledBy: string;
  returnFocusRef?: { current: HTMLElement | null };
  children: ReactNode;
}

export function Dialog({
  open,
  onClose,
  labelledBy,
  returnFocusRef,
  children,
}: DialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const wasOpenRef = useRef(false);
  const closeHandledRef = useRef(false);

  useLayoutEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }

    if (open && !wasOpenRef.current) {
      closeHandledRef.current = false;
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

  useEffect(() => {
    return () => {
      if (wasOpenRef.current) {
        returnFocusRef?.current?.focus();
      }
    };
  }, []);

  const handleKeyDown = (event: KeyboardEvent<HTMLDialogElement>) => {
    if (event.key !== "Escape") {
      return;
    }
    event.preventDefault();
    closeHandledRef.current = true;
    onClose();
  };

  const handleCancel = (event: SyntheticEvent<HTMLDialogElement>) => {
    event.preventDefault();
    if (!closeHandledRef.current) {
      closeHandledRef.current = true;
      onClose();
    }
  };

  const isNativeModalSupported =
    typeof HTMLDialogElement !== "undefined" &&
    typeof HTMLDialogElement.prototype.showModal === "function";

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={labelledBy}
      aria-modal={isNativeModalSupported ? undefined : "true"}
      className={styles.dialog}
      onKeyDown={handleKeyDown}
      onCancel={handleCancel}
    >
      {children}
    </dialog>
  );
}
