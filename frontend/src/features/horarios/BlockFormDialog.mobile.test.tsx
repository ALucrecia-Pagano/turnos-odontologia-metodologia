import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createApiClient } from "../../shared/api/client";
import { readSrcFile } from "../../test/cssText";
import { BlockFormDialog } from "./BlockFormDialog";

const PROF_ID = "00000000-0000-0000-0000-000000000001";

describe("BlockFormDialog — Móvil (≤ 640 px)", () => {
  it("Presentación de modal como hoja inferior en móvil: aplica clase y atributos de hoja inferior a ≤ 640 px ocupando el 100% del ancho útil", () => {
    const client = createApiClient({
      baseUrl: "http://localhost:8000/api",
      fetchFn: async () => new Response("{}", { status: 200 }),
    });

    render(
      <BlockFormDialog
        open={true}
        onClose={() => {}}
        onCreated={() => {}}
        client={client}
        professionalId={PROF_ID}
        timezone="America/Argentina/Buenos_Aires"
        isMobile={true}
      />,
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("data-mobile-sheet", "true");
    expect(dialog.className).toContain("dialogBottomSheet");

    const css = readSrcFile("features/horarios/BlockFormDialog.module.css");
    expect(css).toContain("@media (max-width: 640px)");
    expect(css).toContain("border-radius: var(--radius-lg, 16px) var(--radius-lg, 16px) 0 0;");
    expect(css).toContain("width: 100%;");
  });
});
