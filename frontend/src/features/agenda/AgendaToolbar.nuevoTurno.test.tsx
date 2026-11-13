import { fireEvent, render, screen } from "@testing-library/react";
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
];

const CHAIRS: readonly Chair[] = [
  { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón 1", active: true },
];

describe("AgendaToolbar — Acción Nuevo turno", () => {
  it("controla la visibilidad por rol del botón Nuevo turno y dispara onNewAppointment al clickear", () => {
    let clicked = false;
    const { rerender } = render(
      <AgendaToolbar
        date="2026-11-16"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        userRole="recepcion"
        onNewAppointment={() => {
          clicked = true;
        }}
      />,
    );

    // Visible para recepción y clickea
    const btn = screen.queryByRole("button", { name: "Nuevo turno" });
    expect(btn).not.toBeNull();
    fireEvent.click(btn!);
    expect(clicked).toBe(true);

    // Visible para administrador
    rerender(
      <AgendaToolbar
        date="2026-11-16"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        userRole="administrador"
        onNewAppointment={() => undefined}
      />,
    );
    expect(screen.queryByRole("button", { name: "Nuevo turno" })).not.toBeNull();

    // No visible para odontólogo
    rerender(
      <AgendaToolbar
        date="2026-11-16"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        userRole="odontologo"
        onNewAppointment={() => undefined}
      />,
    );
    expect(screen.queryByRole("button", { name: "Nuevo turno" })).toBeNull();

    // No visible si onNewAppointment no está definido
    rerender(
      <AgendaToolbar
        date="2026-11-16"
        professionalId={null}
        chairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        onSelectProfessional={() => undefined}
        onSelectChair={() => undefined}
        onClearFilters={() => undefined}
        userRole="recepcion"
      />,
    );
    expect(screen.queryByRole("button", { name: "Nuevo turno" })).toBeNull();
  });
});
