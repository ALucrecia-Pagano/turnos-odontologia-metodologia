import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Chair, Professional } from "./agendaApi";
import {
  AgendaToolbar,
  CHAIR_FILTER_HELP_TEXT,
  CHAIR_VIEW_HELP_TEXT,
} from "./AgendaToolbar";

const PROFESSIONALS: readonly Professional[] = [
  {
    id: "00000000-0000-0000-0000-000000000001",
    fullName: "Dra. Laura Quiroga",
    licenseNumber: "MP-1001",
    active: true,
  },
];

const CHAIRS: readonly Chair[] = [
  { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón 1", active: true },
  { id: "00000000-0000-0000-0000-0000000000b2", name: "Sillón 2", active: true },
];

describe("AgendaToolbar — Modo Sillones", () => {
  it("Recepción y administración ven el control: Sillones visible para recepcion y administrador", () => {
    let capturedView: string | null = null;
    const onSelectView = (v: "day" | "week" | "chair") => {
      capturedView = v;
    };

    // 1. Recepción ve el botón Sillones
    const { rerender } = render(
      <AgendaToolbar
        date="2026-11-16"
        view="chair"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        onSelectView={onSelectView}
        userRole="recepcion"
      />,
    );

    const chairBtn = screen.queryByRole("button", { name: "Sillones" });
    expect(chairBtn).not.toBeNull();
    expect(chairBtn).toHaveAttribute("aria-pressed", "true");

    const dayBtn = screen.queryByRole("button", { name: "Día" });
    expect(dayBtn).toHaveAttribute("aria-pressed", "false");

    const weekBtn = screen.queryByRole("button", { name: "Semana" });
    expect(weekBtn).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(chairBtn!);
    expect(capturedView).toBe("chair");

    // 2. Administrador también lo ve
    rerender(
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
        onSelectView={onSelectView}
        userRole="administrador"
      />,
    );
    expect(screen.queryByRole("button", { name: "Sillones" })).not.toBeNull();

    // 3. Odontólogo no ve el botón Sillones
    rerender(
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
        onSelectView={onSelectView}
        userRole="odontologo"
      />,
    );
    expect(screen.queryByRole("button", { name: "Sillones" })).toBeNull();
  });

  it("La ayuda del filtro de sillón se adapta: en view=chair muestra CHAIR_VIEW_HELP_TEXT", () => {
    render(
      <AgendaToolbar
        date="2026-11-16"
        view="chair"
        professionalId={null}
        chairId="00000000-0000-0000-0000-0000000000b1"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        userRole="recepcion"
      />,
    );

    // No muestra la ayuda de día/semana
    expect(screen.queryByText(CHAIR_FILTER_HELP_TEXT)).toBeNull();

    // Muestra la ayuda adaptada
    expect(screen.getByText(CHAIR_VIEW_HELP_TEXT)).toBeInTheDocument();

    // Conserva Anterior y Siguiente
    expect(screen.getByRole("button", { name: "Anterior" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Siguiente" })).toBeInTheDocument();
  });
});
