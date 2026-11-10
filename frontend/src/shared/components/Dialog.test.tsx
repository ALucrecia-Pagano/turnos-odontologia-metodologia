import { fireEvent, render, screen } from "@testing-library/react";
import { useRef } from "react";
import { describe, expect, it } from "vitest";
import { Dialog } from "./Dialog";

describe("Dialog", () => {
  it("se renderiza abierto sin depender de showModal y expone sus atributos accesibles", () => {
    render(
      <Dialog open onClose={() => undefined} labelledBy="dialog-title">
        <h2 id="dialog-title">Iniciar sesión</h2>
        <p>Contenido del diálogo</p>
      </Dialog>,
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog.tagName).toBe("DIALOG");
    expect(dialog).toHaveAttribute("open");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-labelledby", "dialog-title");
    expect(screen.getByRole("heading", { name: "Iniciar sesión" })).toBeVisible();
  });

  it("cierra con Escape y devuelve el foco al disparador", () => {
    let closes = 0;

    function Harness() {
      const triggerRef = useRef<HTMLButtonElement>(null);
      return (
        <>
          <button ref={triggerRef} type="button">
            Abrir acceso
          </button>
          <Dialog
            open
            onClose={() => {
              closes += 1;
            }}
            labelledBy="dialog-title"
            returnFocusRef={triggerRef}
          >
            <h2 id="dialog-title">Iniciar sesión</h2>
          </Dialog>
        </>
      );
    }

    render(<Harness />);
    const trigger = screen.getByRole("button", { name: "Abrir acceso" });
    trigger.focus();
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });

    expect(closes).toBe(1);
    expect(trigger).toHaveFocus();
  });

  it("atiende cancel y refleja el cierre sin close() nativo", () => {
    let closes = 0;
    const { rerender } = render(
      <Dialog open onClose={() => (closes += 1)} labelledBy="dialog-title">
        <h2 id="dialog-title">Iniciar sesión</h2>
      </Dialog>,
    );

    const dialog = screen.getByRole("dialog");
    fireEvent(dialog, new Event("cancel", { cancelable: true }));
    expect(closes).toBe(1);

    rerender(
      <Dialog open={false} onClose={() => (closes += 1)} labelledBy="dialog-title">
        <h2 id="dialog-title">Iniciar sesión</h2>
      </Dialog>,
    );
    expect(dialog).not.toHaveAttribute("open");
  });
});
