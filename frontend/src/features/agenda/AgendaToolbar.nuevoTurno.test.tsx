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
  it("visible para recepción y dispara onNewAppointment al clic", () => {
    let clicked = false;
    render(
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

    const btn = screen.queryByRole("button", { name: "Nuevo turno" });
    expect(btn).not.toBeNull();
    fireEvent.click(btn!);
    expect(clicked).toBe(true);
  });

  it("visible para administrador", () => {
    render(
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

    const btn = screen.queryByRole("button", { name: "Nuevo turno" });
    expect(btn).not.toBeNull();
  });

  it("no visible para odontólogo", () => {
    render(
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

    const btn = screen.queryByRole("button", { name: "Nuevo turno" });
    expect(btn).toBeNull();
  });
});
