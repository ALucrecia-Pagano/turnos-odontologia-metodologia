import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("el estado reservado muestra su variante", () => {
    render(<StatusBadge status="reservado" />);
    const badge = screen.queryByText("Reservado");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-status", "reservado");
    expect(badge).toHaveClass("badge", "reservado");
    expect(badge).toHaveStyle({ color: "#1D4ED8", backgroundColor: "#DBEAFE" });
  });

  it("el estado confirmado muestra su variante", () => {
    render(<StatusBadge status="confirmado" />);
    const badge = screen.queryByText("Confirmado");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-status", "confirmado");
    expect(badge).toHaveClass("badge", "confirmado");
    expect(badge).toHaveStyle({ color: "#15803D", backgroundColor: "#DCFCE7" });
  });

  it("el estado atendido muestra su variante", () => {
    render(<StatusBadge status="atendido" />);
    const badge = screen.queryByText("Atendido");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-status", "atendido");
    expect(badge).toHaveClass("badge", "atendido");
    expect(badge).toHaveStyle({ color: "#374151", backgroundColor: "#E5E7EB" });
  });

  it("el estado ausente muestra su variante", () => {
    render(<StatusBadge status="ausente" />);
    const badge = screen.queryByText("Ausente");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-status", "ausente");
    expect(badge).toHaveClass("badge", "ausente");
    expect(badge).toHaveStyle({ color: "#B45309", backgroundColor: "#FEF3C7" });
  });

  it("el estado cancelado muestra su variante", () => {
    render(<StatusBadge status="cancelado" />);
    const badge = screen.queryByText("Cancelado");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-status", "cancelado");
    expect(badge).toHaveClass("badge", "cancelado");
    expect(badge).toHaveStyle({ color: "#B91C1C", backgroundColor: "#FEE2E2" });
  });
});
