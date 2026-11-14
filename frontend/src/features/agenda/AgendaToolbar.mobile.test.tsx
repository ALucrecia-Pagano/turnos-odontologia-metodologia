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
});
