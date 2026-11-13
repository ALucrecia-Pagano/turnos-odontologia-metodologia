import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createApiClient } from "../../shared/api/client";
import { PatientSearchGroup } from "./PatientSearchGroup";

describe("PatientSearchGroup", () => {
  it("renderizado inicial: input de búsqueda, botón Buscar paciente habilitado y sin radio buttons", () => {
    const client = createApiClient({ fetchFn: async () => new Response("[]") });
    render(
      <PatientSearchGroup
        client={client}
        selectedPatientId={null}
        onSelectPatient={() => undefined}
      />,
    );

    const input = screen.queryByRole("searchbox", { name: /buscar paciente/i });
    expect(input).not.toBeNull();
    const button = screen.queryByRole("button", { name: "Buscar paciente" });
    expect(button).not.toBeNull();
    expect(button).toBeEnabled();
    const radios = screen.queryAllByRole("radio");
    expect(radios).toHaveLength(0);
  });

  it("búsqueda con resultados muestra radio buttons con nombre y DNI", async () => {
    const mockPatients = [
      { id: "00000000-0000-0000-0000-0000000000c1", fullName: "Ana Pérez", dni: "30111222" },
      { id: "00000000-0000-0000-0000-0000000000c2", fullName: "Carlos Pérez", dni: "32333444" },
    ];
    let requestedUrl = "";
    const client = createApiClient({
      fetchFn: async (url) => {
        requestedUrl = url.toString();
        return new Response(JSON.stringify(mockPatients), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      },
    });

    render(
      <PatientSearchGroup
        client={client}
        selectedPatientId={null}
        onSelectPatient={() => undefined}
      />,
    );

    const input = screen.queryByRole("searchbox", { name: /buscar paciente/i });
    expect(input).not.toBeNull();
    fireEvent.change(input!, { target: { value: "Pérez" } });

    const button = screen.queryByRole("button", { name: "Buscar paciente" });
    expect(button).not.toBeNull();
    fireEvent.click(button!);

    await screen.findByRole("button", { name: "Buscar paciente" });
    expect(requestedUrl).toContain("/patients?query=P%C3%A9rez");
    const radios = screen.queryAllByRole("radio");
    expect(radios).toHaveLength(2);
    expect(screen.queryByRole("radio", { name: /Ana Pérez \(DNI 30111222\)/i })).not.toBeNull();
    expect(screen.queryByRole("radio", { name: /Carlos Pérez \(DNI 32333444\)/i })).not.toBeNull();
  });

  it("búsqueda sin resultados muestra aviso accesible y sin radio buttons", async () => {
    const client = createApiClient({
      fetchFn: async () =>
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    });

    render(
      <PatientSearchGroup
        client={client}
        selectedPatientId={null}
        onSelectPatient={() => undefined}
      />,
    );

    const input = screen.queryByRole("searchbox", { name: /buscar paciente/i });
    expect(input).not.toBeNull();
    fireEvent.change(input!, { target: { value: "Desconocido" } });

    const button = screen.queryByRole("button", { name: "Buscar paciente" });
    expect(button).not.toBeNull();
    fireEvent.click(button!);

    await screen.findByRole("button", { name: "Buscar paciente" });
    const emptyNotice = screen.queryByText("No se encontraron pacientes");
    expect(emptyNotice).not.toBeNull();
    const radios = screen.queryAllByRole("radio");
    expect(radios).toHaveLength(0);
  });

  it("selección por clic o teclado invoca onSelectPatient con el id correspondiente", async () => {
    const mockPatients = [
      { id: "00000000-0000-0000-0000-0000000000c1", fullName: "Ana Pérez", dni: "30111222" },
      { id: "00000000-0000-0000-0000-0000000000c2", fullName: "Carlos Pérez", dni: "32333444" },
    ];
    const client = createApiClient({
      fetchFn: async () =>
        new Response(JSON.stringify(mockPatients), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    });
    let selectedId: string | null = null;

    render(
      <PatientSearchGroup
        client={client}
        selectedPatientId={null}
        onSelectPatient={(id) => {
          selectedId = id;
        }}
      />,
    );

    const input = screen.queryByRole("searchbox", { name: /buscar paciente/i });
    expect(input).not.toBeNull();
    fireEvent.change(input!, { target: { value: "Pérez" } });

    const button = screen.queryByRole("button", { name: "Buscar paciente" });
    expect(button).not.toBeNull();
    fireEvent.click(button!);

    await screen.findByRole("button", { name: "Buscar paciente" });
    const radioAna = screen.queryByRole("radio", { name: /Ana Pérez/i });
    expect(radioAna).not.toBeNull();
    fireEvent.click(radioAna!);

    expect(selectedId).toBe("00000000-0000-0000-0000-0000000000c1");
  });
});
