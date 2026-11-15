import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
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
  isMobile?: boolean;
}

export function Dialog({
  open,
  onClose,
  labelledBy,
  returnFocusRef,
  children,
  isMobile,
}: DialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const wasOpenRef = useRef(false);
  const closeHandledRef = useRef(false);

  const [isMobileDevice, setIsMobileDevice] = useState(() => {
    if (typeof window !== "undefined" && typeof window.matchMedia === "function") {
      return window.matchMedia("(max-width: 640px)").matches;
    }
    return false;
  });

  const isMobileEffective = isMobile ?? isMobileDevice;

  useEffect(() => {
    if (isMobile !== undefined) {
      return;
    }
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }
    const mql = window.matchMedia("(max-width: 640px)");
    const handler = (e: MediaQueryListEvent) => {
      setIsMobileDevice(e.matches);
    };
    if (typeof mql.addEventListener === "function") {
      mql.addEventListener("change", handler);
      return () => mql.removeEventListener("change", handler);
    }
  }, [isMobile]);

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
    const returnFocusEl = returnFocusRef?.current;
    return () => {
      if (wasOpenRef.current) {
        returnFocusEl?.focus();
      }
    };
  }, [returnFocusRef]);

  const handleKeyDown = (event: KeyboardEvent<HTMLDialogElement>) => {
    if (event.key !== "Escape") {
      return;
    }
    event.preventDefault();
    closeHandledRef.current = true;
    setTimeout(() => {
      closeHandledRef.current = false;
    }, 0);
    onClose();
  };

  const handleCancel = (event: SyntheticEvent<HTMLDialogElement>) => {
    event.preventDefault();
    if (closeHandledRef.current) {
      closeHandledRef.current = false;
      return;
    }
    onClose();
  };

  const isNativeModalSupported =
    typeof HTMLDialogElement !== "undefined" &&
    typeof HTMLDialogElement.prototype.showModal === "function";

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={labelledBy}
      aria-modal={isNativeModalSupported ? undefined : "true"}
      className={`${styles.dialog} ${isMobileEffective ? styles.dialogBottomSheet : ""}`}
      data-mobile-sheet={isMobileEffective ? "true" : undefined}
      onKeyDown={handleKeyDown}
      onCancel={handleCancel}
    >
      {children}
    </dialog>
  );
}
