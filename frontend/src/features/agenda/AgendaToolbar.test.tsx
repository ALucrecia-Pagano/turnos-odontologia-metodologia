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
  {
    id: "00000000-0000-0000-0000-000000000003",
    fullName: "Dra. Paula Benítez",
    licenseNumber: "MP-1003",
    active: false,
  },
];

const CHAIRS: readonly Chair[] = [
  { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón 1", active: true },
  { id: "00000000-0000-0000-0000-0000000000b2", name: "Sillón 2", active: false },
];

describe("AgendaToolbar", () => {
  it("renderiza selectores de Profesional y Sillón con opción Todos, marca (inactivo), ayuda de sillón y Limpiar filtros", () => {
    const events: string[] = [];

    const { rerender } = render(
      <AgendaToolbar
        date="2026-11-16"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={(id) => events.push(`prof:${id ?? "all"}`)}
        onSelectChair={(id) => events.push(`chair:${id ?? "all"}`)}
        onClearFilters={() => events.push("clear")}
      />,
    );

    const profSelect = screen.queryByLabelText("Profesional") as HTMLSelectElement | null;
    const chairSelect = screen.queryByLabelText("Sillón") as HTMLSelectElement | null;
    expect(profSelect).not.toBeNull();
    expect(chairSelect).not.toBeNull();

    const profOptions = within(profSelect!).queryAllByRole("option");
    expect(profOptions.map((opt) => opt.textContent)).toEqual([
      "Todos",
      "Dr. Martín Sosa",
      "Dra. Laura Quiroga",
      "Dra. Paula Benítez (inactivo)",
    ]);

    const chairOptions = within(chairSelect!).queryAllByRole("option");
    expect(chairOptions.map((opt) => opt.textContent)).toEqual([
      "Todos",
      "Sillón 1",
      "Sillón 2 (inactivo)",
    ]);

    expect(
      screen.queryByText(
        "El filtro por sillón solo afecta los turnos; los horarios y bloqueos se siguen mostrando.",
      ),
    ).not.toBeInTheDocument();

    fireEvent.change(chairSelect!, {
      target: { value: "00000000-0000-0000-0000-0000000000b2" },
    });
    expect(events).toEqual(["chair:00000000-0000-0000-0000-0000000000b2"]);

    rerender(
      <AgendaToolbar
        date="2026-11-16"
        professionalId="00000000-0000-0000-0000-000000000001"
        chairId="00000000-0000-0000-0000-0000000000b2"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={(id) => events.push(`prof:${id ?? "all"}`)}
        onSelectChair={(id) => events.push(`chair:${id ?? "all"}`)}
        onClearFilters={() => events.push("clear")}
      />,
    );

    expect(
      screen.queryByText(
        "El filtro por sillón solo afecta los turnos; los horarios y bloqueos se siguen mostrando.",
      ),
    ).toBeInTheDocument();

    const clearBtn = screen.queryByRole("button", { name: "Limpiar filtros" });
    expect(clearBtn).not.toBeNull();
    fireEvent.click(clearBtn!);
    expect(events).toEqual([
      "chair:00000000-0000-0000-0000-0000000000b2",
      "clear",
    ]);
  });

  it("renderiza el selector de vista [ Día | Semana ], dispara onSelectView y adapta los botones de navegación a Semana anterior y Semana siguiente", () => {
    const events: string[] = [];

    const { rerender } = render(
      <AgendaToolbar
        date="2026-11-16"
        view="day"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => {}}
        onSelectChair={() => {}}
        onClearFilters={() => {}}
        onPrevDay={() => events.push("prev")}
        onNextDay={() => events.push("next")}
        onToday={() => events.push("today")}
        onSelectView={(v) => events.push(`view:${v}`)}
      />,
    );

    const dayBtn = screen.queryByRole("button", { name: "Día" });
    const weekBtn = screen.queryByRole("button", { name: "Semana" });
    expect(dayBtn).not.toBeNull();
    expect(weekBtn).not.toBeNull();
    expect(dayBtn).toHaveAttribute("aria-pressed", "true");
    expect(weekBtn).toHaveAttribute("aria-pressed", "false");

    expect(screen.queryByRole("button", { name: "Anterior" })).not.toBeNull();
    expect(screen.queryByRole("button", { name: "Siguiente" })).not.toBeNull();

    fireEvent.click(weekBtn!);
    expect(events).toEqual(["view:week"]);

    rerender(
      <AgendaToolbar
        date="2026-11-16"
        view="week"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => {}}
        onSelectChair={() => {}}
        onClearFilters={() => {}}
        onPrevDay={() => events.push("prev")}
        onNextDay={() => events.push("next")}
        onToday={() => events.push("today")}
        onSelectView={(v) => events.push(`view:${v}`)}
      />,
    );

    expect(screen.queryByRole("button", { name: "Semana anterior" })).not.toBeNull();
    expect(screen.queryByRole("button", { name: "Semana siguiente" })).not.toBeNull();
    expect(screen.queryByRole("button", { name: "Anterior" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Siguiente" })).toBeNull();
  });
});
