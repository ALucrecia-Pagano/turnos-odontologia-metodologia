import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("el estado reservado muestra su variante", () => {
    render(<StatusBadge status="reservado" />);
    const badge = screen.queryByText("Reservado");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-status", "reservado");
    expect(badge).toHaveClass("badge", "reservado");
    expect(badge).toHaveStyle({ color: "#1F5F86", backgroundColor: "#E4F2F8" });
  });

  it("el estado confirmado muestra su variante", () => {
    render(<StatusBadge status="confirmado" />);
    const badge = screen.queryByText("Confirmado");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-status", "confirmado");
    expect(badge).toHaveClass("badge", "confirmado");
    expect(badge).toHaveStyle({ color: "#146C43", backgroundColor: "#DDF3E7" });
  });

  it("el estado atendido muestra su variante", () => {
    render(<StatusBadge status="atendido" />);
    const badge = screen.queryByText("Atendido");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-status", "atendido");
    expect(badge).toHaveClass("badge", "atendido");
    expect(badge).toHaveStyle({ color: "#3D4A5C", backgroundColor: "#E6EBF1" });
  });

  it("el estado ausente muestra su variante", () => {
    render(<StatusBadge status="ausente" />);
    const badge = screen.queryByText("Ausente");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-status", "ausente");
    expect(badge).toHaveClass("badge", "ausente");
    expect(badge).toHaveStyle({ color: "#9A5B00", backgroundColor: "#FDF0D5" });
  });

  it("el estado cancelado muestra su variante", () => {
    render(<StatusBadge status="cancelado" />);
    const badge = screen.queryByText("Cancelado");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-status", "cancelado");
    expect(badge).toHaveClass("badge", "cancelado");
    expect(badge).toHaveStyle({ color: "#A8242C", backgroundColor: "#FBE4E6" });
  });
});
