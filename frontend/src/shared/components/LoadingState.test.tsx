import { render, screen } from "@testing-library/react";
import { LoadingState } from "./LoadingState";

describe("LoadingState", () => {
  it("renderiza su rol y su texto", () => {
    render(<LoadingState />);
    const status = screen.getByRole("status");
    expect(status).toHaveTextContent("Cargando...");
  });
});
