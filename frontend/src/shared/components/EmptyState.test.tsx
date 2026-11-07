import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("con acción muestra el botón", async () => {
    const clicks: string[] = [];
    render(
      <EmptyState
        title="No hay turnos"
        description="La agenda de hoy está vacía."
        action={{ label: "Crear turno", onClick: () => clicks.push("Crear turno") }}
      />,
    );

    expect(screen.getByRole("heading", { name: "No hay turnos" })).toBeInTheDocument();
    expect(screen.queryByText("La agenda de hoy está vacía.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Crear turno" }));
    expect(clicks).toEqual(["Crear turno"]);
  });

  it("sin acción no muestra botón", () => {
    render(<EmptyState title="No hay turnos" description="La agenda de hoy está vacía." />);

    expect(screen.getByRole("heading", { name: "No hay turnos" })).toBeInTheDocument();
    expect(screen.queryByText("La agenda de hoy está vacía.")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
