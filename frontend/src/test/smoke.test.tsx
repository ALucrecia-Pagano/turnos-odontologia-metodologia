import { render, screen } from "@testing-library/react";
import { App } from "../App";

describe("smoke del andamiaje", () => {
  it("monta App y muestra el título", () => {
    render(<App />);
    expect(screen.queryByRole("heading", { name: "Turnos Odontología" })).toBeInTheDocument();
  });
});
