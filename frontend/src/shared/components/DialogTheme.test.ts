import { readSrcFile, ruleBody } from "../../test/cssText";

const NO_SUPPORT = "@supports not (backdrop-filter: blur(1px))";

const SURFACES = [
  { file: "features/appointments/AppointmentFormDialog.module.css", selector: ".modalContent" },
  { file: "features/appointments/AppointmentDetailDialog.module.css", selector: ".container" },
  { file: "features/appointments/AppointmentRescheduleDialog.module.css", selector: ".container" },
] as const;

describe("tema claro de los modales", () => {
  it("fallback sólido sin soporte de backdrop-filter", () => {
    const dialogCss = readSrcFile("shared/components/Dialog.module.css");
    const backdrop = ruleBody(dialogCss, ".dialog::backdrop");
    expect(backdrop).toContain("background: var(--scrim-navy);");
    expect(backdrop).toContain("backdrop-filter: blur(var(--blur-backdrop));");
    expect(ruleBody(dialogCss, ".dialog::backdrop", NO_SUPPORT)).toContain("background: var(--scrim-navy-strong);");

    for (const { file, selector } of SURFACES) {
      const css = readSrcFile(file);
      const surface = ruleBody(css, selector);
      expect(surface, `${file} superficie`).toContain("background-color: var(--surface-ivory-ice);");
      expect(surface, `${file} borde`).toContain("border: 1px solid var(--color-border);");
      expect(surface, `${file} blur`).toContain("backdrop-filter: blur(var(--blur-backdrop));");
      expect(ruleBody(css, selector, NO_SUPPORT), `${file} fallback`).toContain(
        "background-color: var(--color-background);",
      );
    }
  });
});
