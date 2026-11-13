import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Dialog } from "./Dialog";

describe("Dialog — Escape repetido", () => {
  it("un segundo Escape (evento cancel posterior) vuelve a llamar onClose", async () => {
    let closes = 0;
    render(
      <Dialog
        open
        onClose={() => {
          closes += 1;
        }}
        labelledBy="dialog-title"
      >
        <h2 id="dialog-title">Detalle del turno</h2>
      </Dialog>,
    );

    const dialog = screen.queryByRole("dialog");
    expect(dialog).not.toBeNull();

    fireEvent.keyDown(dialog!, { key: "Escape" });
    expect(closes).toBe(1);

    await new Promise((resolve) => setTimeout(resolve, 0));

    fireEvent(dialog!, new Event("cancel", { cancelable: true }));
    expect(closes).toBe(2);
  });
});
