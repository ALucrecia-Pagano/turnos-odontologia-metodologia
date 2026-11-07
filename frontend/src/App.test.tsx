import { render, screen, within } from "@testing-library/react";
import { App } from "./App";

describe("App con router", () => {
  afterEach(() => {
    window.history.pushState({}, "", "/");
  });

  it("la ruta raíz renderiza el HomePage de bienvenida", () => {
    window.history.pushState({}, "", "/");
    render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: "Turnos Odontología" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveTextContent("Bienvenida");
    const statuses = within(screen.getByRole("list", { name: "Estados de un turno" })).getAllByRole("listitem");
    expect(statuses.map((item) => item.textContent)).toEqual([
      "Reservado",
      "Confirmado",
      "Atendido",
      "Ausente",
      "Cancelado",
    ]);
  });

  it("una ruta desconocida muestra la página de no encontrada", () => {
    window.history.pushState({}, "", "/ruta-que-no-existe");
    render(<App />);

    expect(screen.queryByRole("heading", { level: 1, name: "Página no encontrada" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Volver al inicio" })).toHaveAttribute("href", "/");
  });
});
