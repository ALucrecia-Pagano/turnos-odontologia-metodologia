import fs from "node:fs";
import path from "node:path";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Chair, Professional } from "./agendaApi";
import { AgendaToolbar } from "./AgendaToolbar";

const PROFESSIONALS: readonly Professional[] = [
  {
    id: "00000000-0000-0000-0000-000000000001",
    fullName: "Dra. Laura Quiroga",
    licenseNumber: "MP-1001",
    active: true,
  },
  {
    id: "00000000-0000-0000-0000-000000000002",
    fullName: "Dr. Martín Sosa",
    licenseNumber: "MP-1002",
    active: true,
  },
];

const CHAIRS: readonly Chair[] = [
  { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón 1", active: true },
  { id: "00000000-0000-0000-0000-0000000000b2", name: "Sillón 2", active: false },
];

describe("AgendaToolbar — Modo Móvil (<= 640 px)", () => {
  it("03-toolbar-distribucion-compacta: organiza navegación y fecha en dos filas diferenciadas en celular", () => {
    render(
      <AgendaToolbar
        date="2026-11-16"
        view="day"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        onPrevDay={() => undefined}
        onNextDay={() => undefined}
        onToday={() => undefined}
        onSelectDate={() => undefined}
        onSelectView={() => undefined}
        userRole="recepcion"
        onNewAppointment={() => undefined}
        isMobile={true}
      />,
    );

    const navRow = screen.queryByTestId("agenda-toolbar-nav-row");
    expect(navRow).not.toBeNull();
    expect(within(navRow!).getByTestId("agenda-view-toggle")).toBeInTheDocument();
    expect(within(navRow!).getByRole("button", { name: "Anterior" })).toBeInTheDocument();
    expect(within(navRow!).getByRole("button", { name: "Hoy" })).toBeInTheDocument();
    expect(within(navRow!).getByRole("button", { name: "Siguiente" })).toBeInTheDocument();

    const actionRow = screen.queryByTestId("agenda-toolbar-action-row");
    expect(actionRow).not.toBeNull();
    expect(within(actionRow!).getByLabelText("Fecha")).toBeInTheDocument();
    expect(within(actionRow!).getByRole("button", { name: "Nuevo turno" })).toBeInTheDocument();
    expect(within(actionRow!).getByTestId("agenda-toolbar-filters-toggle")).toBeInTheDocument();
  });

  it("04-toolbar-boton-filtros-con-contador: expone botón Filtros con indicador dinámico de filtros activos y despliega panel accesible", () => {
    const { rerender } = render(
      <AgendaToolbar
        date="2026-11-16"
        view="day"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        isMobile={true}
      />,
    );

    const filtersBtn = screen.getByTestId("agenda-toolbar-filters-toggle");
    expect(filtersBtn).toHaveTextContent(/^Filtros$/);
    expect(filtersBtn).toHaveAttribute("aria-expanded", "false");
    expect(filtersBtn).toHaveAttribute("aria-controls", "agenda-filters-panel");

    const filtersPanel = document.getElementById("agenda-filters-panel");
    expect(filtersPanel).not.toBeNull();
    expect(filtersPanel).toHaveAttribute("hidden");

    // Con un filtro activo (sillón)
    rerender(
      <AgendaToolbar
        date="2026-11-16"
        view="day"
        professionalId={null}
        chairId="00000000-0000-0000-0000-0000000000b1"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        isMobile={true}
      />,
    );
    expect(filtersBtn).toHaveTextContent("Filtros (1)");

    // Con dos filtros activos (profesional y sillón)
    rerender(
      <AgendaToolbar
        date="2026-11-16"
        view="day"
        professionalId="00000000-0000-0000-0000-000000000001"
        chairId="00000000-0000-0000-0000-0000000000b1"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        isMobile={true}
      />,
    );
    expect(filtersBtn).toHaveTextContent("Filtros (2)");

    // Al pulsar el botón se despliega el panel
    fireEvent.click(filtersBtn);
    expect(filtersBtn).toHaveAttribute("aria-expanded", "true");
    expect(filtersPanel).not.toHaveAttribute("hidden");
    expect(within(filtersPanel!).getByLabelText("Profesional")).toBeInTheDocument();
    expect(within(filtersPanel!).getByLabelText("Sillón")).toBeInTheDocument();
    expect(within(filtersPanel!).getByRole("button", { name: "Limpiar filtros" })).toBeInTheDocument();

    // Al pulsar de nuevo se pliega
    fireEvent.click(filtersBtn);
    expect(filtersBtn).toHaveAttribute("aria-expanded", "false");
    expect(filtersPanel).toHaveAttribute("hidden");
  });

  it("10-toolbar-compacta-tres-filas: Anterior y Siguiente muestran texto corto conservando nombre accesible y fila 1 sin flex-wrap", () => {
    // 1. En móvil Anterior, Siguiente y Actualizar agenda conservan nombre accesible y texto corto
    render(
      <AgendaToolbar
        date="2026-11-16"
        view="day"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        onPrevDay={() => undefined}
        onNextDay={() => undefined}
        onToday={() => undefined}
        onSelectDate={() => undefined}
        onRefresh={() => undefined}
        onSelectView={() => undefined}
        isMobile={true}
      />,
    );

    const prevBtn = screen.getByRole("button", { name: "Anterior" });
    expect(prevBtn).toHaveAccessibleName("Anterior");
    expect(prevBtn.textContent?.trim()).toBe("‹");

    const nextBtn = screen.getByRole("button", { name: "Siguiente" });
    expect(nextBtn).toHaveAccessibleName("Siguiente");
    expect(nextBtn.textContent?.trim()).toBe("›");

    const refreshBtn = screen.getByRole("button", { name: "Actualizar agenda" });
    expect(refreshBtn).toHaveAccessibleName("Actualizar agenda");
    expect(refreshBtn.textContent?.trim()).toBe("↻");

    // 2. CSS: media query <= 640px con flex-wrap nowrap en navRow y tokens de espaciado compactos
    const cssPath = path.resolve(__dirname, "./AgendaToolbar.module.css");
    const cssContent = fs.readFileSync(cssPath, "utf-8");
    expect(cssContent).toMatch(/@media\s*\(max-width:\s*640px\)/);
    expect(cssContent).toMatch(/\.navRow\s*\{[^}]*flex-wrap:\s*nowrap/);

    // 3. En escritorio preserva el texto completo
    const { unmount } = render(
      <AgendaToolbar
        date="2026-11-16"
        view="day"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        onPrevDay={() => undefined}
        onNextDay={() => undefined}
        onToday={() => undefined}
        onSelectDate={() => undefined}
        onRefresh={() => undefined}
        onSelectView={() => undefined}
        isMobile={false}
      />,
    );
    const desktopButtons = screen.getAllByRole("button", { name: "Anterior" });
    const desktopPrevBtn = desktopButtons[1] ?? desktopButtons[0];
    expect(desktopPrevBtn?.textContent?.trim()).toBe("Anterior");
    const desktopNextButtons = screen.getAllByRole("button", { name: "Siguiente" });
    const desktopNextBtn = desktopNextButtons[1] ?? desktopNextButtons[0];
    expect(desktopNextBtn?.textContent?.trim()).toBe("Siguiente");
    const desktopRefreshButtons = screen.getAllByRole("button", { name: "Actualizar agenda" });
    const desktopRefreshBtn = desktopRefreshButtons[1] ?? desktopRefreshButtons[0];
    expect(desktopRefreshBtn?.textContent?.trim()).toBe("Actualizar agenda");
    unmount();
  });
});
