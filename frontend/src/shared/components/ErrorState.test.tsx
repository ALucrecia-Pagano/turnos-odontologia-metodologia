import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Violation } from "../api/types";
import { ErrorState } from "./ErrorState";

const OVERLAP_MESSAGE =
  "Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno 00000000-0000-0000-0000-0000000000a1).";

describe("ErrorState", () => {
  it("muestra uno y varios mensajes", () => {
    const { unmount } = render(
      <ErrorState messages={["El profesional ya tiene un turno en ese horario."]} />,
    );
    const single = screen.getByRole("alert");
    expect(within(single).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "El profesional ya tiene un turno en ese horario.",
    ]);
    unmount();

    render(
      <ErrorState
        messages={[
          "El profesional ya tiene un turno en ese horario.",
          "El sillón ya está ocupado en ese horario.",
        ]}
      />,
    );
    const several = screen.getByRole("alert");
    expect(within(several).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "El profesional ya tiene un turno en ese horario.",
      "El sillón ya está ocupado en ese horario.",
    ]);
  });

  it("muestra el mensaje de un 409 textual", () => {
    const violations: Violation[] = [{ code: "PROFESSIONAL_OVERLAP", message: OVERLAP_MESSAGE }];
    render(<ErrorState messages={violations.map((violation) => violation.message)} />);

    const items = within(screen.getByRole("alert")).getAllByRole("listitem");
    expect(items).toHaveLength(1);
    expect(items[0]?.textContent).toBe(OVERLAP_MESSAGE);
  });

  it("con reintento muestra el botón y lo ejecuta", async () => {
    let retries = 0;
    render(
      <ErrorState
        messages={["No se pudo cargar la agenda."]}
        onRetry={() => {
          retries += 1;
        }}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(retries).toBe(1);
  });

  it("sin reintento no muestra botón", () => {
    render(<ErrorState messages={["No se pudo cargar la agenda."]} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
