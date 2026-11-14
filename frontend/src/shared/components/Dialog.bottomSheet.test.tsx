import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Dialog } from "./Dialog";

describe("Dialog — Presentación Responsiva Móvil vs Escritorio", () => {
  it("07-dialog-bottom-sheet-mobile: renderiza como hoja inferior anclada al fondo con scroll interno en celular", () => {
    render(
      <Dialog
        open={true}
        onClose={() => undefined}
        labelledBy="sheet-title"
        isMobile={true}
      >
        <div data-testid="sheet-content">
          <h2 id="sheet-title">Detalle del turno</h2>
          <p>Información del turno y acciones</p>
        </div>
      </Dialog>,
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute("data-mobile-sheet", "true");
    expect(dialog.className).toMatch(/dialogBottomSheet/);
  });

  it("08-dialog-modal-centrado-desktop: preserva modal centrado flotante en pantallas de escritorio", () => {
    render(
      <Dialog
        open={true}
        onClose={() => undefined}
        labelledBy="desktop-title"
        isMobile={false}
      >
        <div data-testid="desktop-content">
          <h2 id="desktop-title">Detalle del turno</h2>
          <p>Información del turno y acciones en escritorio</p>
        </div>
      </Dialog>,
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(dialog).not.toHaveAttribute("data-mobile-sheet");
    expect(dialog.className).not.toMatch(/dialogBottomSheet/);
  });
});
