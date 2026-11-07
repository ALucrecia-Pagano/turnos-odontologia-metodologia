import { render, screen } from "@testing-library/react";
import { PageShell } from "./PageShell";

describe("PageShell", () => {
  it("envuelve header, main y footer y renderiza sus hijos", () => {
    render(
      <PageShell title="Turnos Odontología">
        <p>Agenda de Ana Pérez</p>
      </PageShell>,
    );

    const header = screen.getByRole("banner");
    const main = screen.getByRole("main");
    const footer = screen.queryByRole("contentinfo");

    expect(header).toHaveTextContent("Turnos Odontología");
    expect(main).toHaveTextContent("Agenda de Ana Pérez");
    expect(footer).toBeInTheDocument();
    if (footer === null) throw new Error("PageShell no renderizó el footer");
    expect(header.compareDocumentPosition(main) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(main.compareDocumentPosition(footer) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
