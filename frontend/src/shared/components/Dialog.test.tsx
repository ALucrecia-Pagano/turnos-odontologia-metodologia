import { fireEvent, render, screen } from "@testing-library/react";
import { useRef } from "react";
import { describe, expect, it } from "vitest";
import { Dialog } from "./Dialog";

describe("Dialog", () => {
  it("abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby", () => {
    render(
      <Dialog open onClose={() => undefined} labelledBy="dialog-title">
        <h2 id="dialog-title">Nuevo turno</h2>
        <p>Contenido del diálogo</p>
      </Dialog>,
    );

    const dialog = screen.queryByRole("dialog");
    expect(dialog).not.toBeNull();
    expect(dialog!.tagName).toBe("DIALOG");
    expect(dialog).toHaveAttribute("open");
    expect(dialog).not.toHaveAttribute("role");
    expect(dialog).toHaveAttribute("aria-labelledby", "dialog-title");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(screen.queryByRole("heading", { name: "Nuevo turno" })).not.toBeNull();
  });

  it("Escape llama onClose exactamente una vez", () => {
    let closes = 0;
    render(
      <Dialog
        open
        onClose={() => {
          closes += 1;
        }}
        labelledBy="dialog-title"
      >
        <h2 id="dialog-title">Nuevo turno</h2>
      </Dialog>,
    );

    const dialog = screen.queryByRole("dialog");
    expect(dialog).not.toBeNull();
    fireEvent.keyDown(dialog!, { key: "Escape" });
    expect(closes).toBe(1);
  });

  it("al pasar open de true a false el foco vuelve a returnFocusRef", () => {
    function Harness({ isOpen }: { isOpen: boolean }) {
      const triggerRef = useRef<HTMLButtonElement>(null);
      return (
        <>
          <button ref={triggerRef} type="button">
            Nuevo turno
          </button>
          <Dialog
            open={isOpen}
            onClose={() => undefined}
            labelledBy="dialog-title"
            returnFocusRef={triggerRef}
          >
            <h2 id="dialog-title">Nuevo turno</h2>
          </Dialog>
        </>
      );
    }

    const { rerender } = render(<Harness isOpen={true} />);
    const trigger = screen.queryByRole("button", { name: "Nuevo turno" });
    expect(trigger).not.toBeNull();
    expect(trigger).not.toHaveFocus();

    rerender(<Harness isOpen={false} />);
    expect(trigger).toHaveFocus();
  });
});