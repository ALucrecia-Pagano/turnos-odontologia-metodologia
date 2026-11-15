import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient, type FetchFn } from "../../shared/api/client";

function renderPacientes(fetchFn: FetchFn) {
  const tokenStore = createMemoryTokenStore("token-test");
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
  const router = createMemoryRouter(createAppRoutes(), {
    initialEntries: ["/pacientes"],
  });
  return render(
    <AuthProvider tokenStore={tokenStore} client={client}>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
}

describe("PacientesPage", () => {
  it("Listado de pacientes con sus cuatro datos", async () => {
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e2",
            username: "recepcion",
            displayName: "Recepción Demo",
            role: "recepcion",
            professionalId: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith("/patients")) {
        return new Response(
          JSON.stringify([
            {
              id: "p-1",
              fullName: "Ana Pérez",
              dni: "30111222",
              phone: "11-4444-5555",
              healthInsurance: "OSDE",
            },
            {
              id: "p-2",
              fullName: "Bruno Acosta",
              dni: "28444555",
              phone: null,
              healthInsurance: null,
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderPacientes(fetchFn);

    await waitFor(() => {
      expect(screen.queryByRole("table")).toBeInTheDocument();
    });

    const headers = screen.getAllByRole("columnheader").map((th) => th.textContent);
    expect(headers).toEqual(["Nombre", "DNI", "Teléfono", "Obra social", "Acciones"]);

    const rowAna = screen.getByRole("row", { name: /Ana Pérez/ });
    expect(rowAna).toHaveTextContent("30111222");
    expect(rowAna).toHaveTextContent("11-4444-5555");
    expect(rowAna).toHaveTextContent("OSDE");

    const rowBruno = screen.getByRole("row", { name: /Bruno Acosta/ });
    expect(rowBruno).toHaveTextContent("28444555");
    expect(rowBruno).toHaveTextContent("Sin dato");
  });

  it("Búsqueda envía la consulta codificada y muestra el resultado", async () => {
    const user = userEvent.setup();
    const requestedUrls: string[] = [];

    const fetchFn: FetchFn = async (url) => {
      requestedUrls.push(url);
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e2",
            username: "recepcion",
            displayName: "Recepción Demo",
            role: "recepcion",
            professionalId: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith("/patients")) {
        return new Response(
          JSON.stringify([
            {
              id: "p-1",
              fullName: "Ana Pérez",
              dni: "30111222",
              phone: "11-4444-5555",
              healthInsurance: "OSDE",
            },
            {
              id: "p-2",
              fullName: "Bruno Acosta",
              dni: "28444555",
              phone: null,
              healthInsurance: null,
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients?query=")) {
        return new Response(
          JSON.stringify([
            {
              id: "p-1",
              fullName: "Ana Pérez",
              dni: "30111222",
              phone: "11-4444-5555",
              healthInsurance: "OSDE",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderPacientes(fetchFn);

    await waitFor(() => {
      expect(screen.queryByRole("table")).toBeInTheDocument();
    });

    const searchInput = screen.getByLabelText("Buscar por nombre o DNI");
    await user.type(searchInput, "Ana Pérez");
    await user.click(screen.getByRole("button", { name: "Buscar" }));

    await waitFor(() => {
      expect(requestedUrls).toContain("http://localhost:8000/api/patients?query=Ana%20P%C3%A9rez");
    });

    expect(screen.getByRole("row", { name: /Ana Pérez/ })).toBeInTheDocument();
    expect(screen.queryByRole("row", { name: /Bruno Acosta/ })).not.toBeInTheDocument();
  });

  it("Búsqueda sin resultados", async () => {
    const user = userEvent.setup();

    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e2",
            username: "recepcion",
            displayName: "Recepción Demo",
            role: "recepcion",
            professionalId: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith("/patients")) {
        return new Response(
          JSON.stringify([
            {
              id: "p-1",
              fullName: "Ana Pérez",
              dni: "30111222",
              phone: "11-4444-5555",
              healthInsurance: "OSDE",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients?query=zzz")) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response("Not found", { status: 404 });
    };

    renderPacientes(fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("row", { name: /Ana Pérez/ })).toBeInTheDocument();
    });

    const searchInput = screen.getByLabelText("Buscar por nombre o DNI");
    await user.type(searchInput, "zzz");
    await user.click(screen.getByRole("button", { name: "Buscar" }));

    await waitFor(() => {
      expect(screen.queryByText("No se encontraron pacientes.")).toBeInTheDocument();
    });

    expect(screen.queryByRole("row", { name: /Ana Pérez/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("Error de carga de pacientes con reintento", async () => {
    const user = userEvent.setup();
    let patientCalls = 0;

    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e2",
            username: "recepcion",
            displayName: "Recepción Demo",
            role: "recepcion",
            professionalId: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith("/patients")) {
        patientCalls += 1;
        if (patientCalls === 1) {
          return new Response("Internal Server Error", { status: 500 });
        }
        return new Response(
          JSON.stringify([
            {
              id: "p-1",
              fullName: "Ana Pérez",
              dni: "30111222",
              phone: "11-4444-5555",
              healthInsurance: "OSDE",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderPacientes(fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    const retryButton = screen.getByRole("button", { name: "Reintentar" });
    expect(retryButton).toBeInTheDocument();
    expect(patientCalls).toBe(1);

    await user.click(retryButton);

    await waitFor(() => {
      expect(screen.queryByRole("table")).toBeInTheDocument();
    });

    expect(patientCalls).toBe(2);
    expect(screen.getByRole("row", { name: /Ana Pérez/ })).toBeInTheDocument();
  });

  it("Odontólogo consulta pacientes en solo lectura", async () => {
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e3",
            username: "odontologo",
            displayName: "Dra. Laura Quiroga",
            role: "odontologo",
            professionalId: "00000000-0000-0000-0000-000000000001",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients")) {
        return new Response(
          JSON.stringify([
            {
              id: "p-1",
              fullName: "Ana Pérez",
              dni: "30111222",
              phone: "11-4444-5555",
              healthInsurance: "OSDE",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderPacientes(fetchFn);

    await waitFor(() => {
      expect(screen.queryByRole("table")).toBeInTheDocument();
    });

    expect(screen.getByLabelText("Buscar por nombre o DNI")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Nuevo paciente" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Editar" })).not.toBeInTheDocument();
  });

  it("Búsqueda sin resultados muestra un único mensaje", async () => {
    const user = userEvent.setup();

    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e2",
            username: "recepcion",
            displayName: "Recepción Demo",
            role: "recepcion",
            professionalId: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith("/patients")) {
        return new Response(
          JSON.stringify([
            {
              id: "p-1",
              fullName: "Ana Pérez",
              dni: "30111222",
              phone: "11-4444-5555",
              healthInsurance: "OSDE",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients?query=sin-coincidencia")) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response("Not found", { status: 404 });
    };

    renderPacientes(fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("row", { name: /Ana Pérez/ })).toBeInTheDocument();
    });

    const searchInput = screen.getByLabelText("Buscar por nombre o DNI");
    await user.type(searchInput, "sin-coincidencia");
    await user.click(screen.getByRole("button", { name: "Buscar" }));

    await waitFor(() => {
      expect(screen.queryByText("No se encontraron pacientes.")).toBeInTheDocument();
    });

    expect(
      screen.queryByText("No hay resultados para la búsqueda realizada."),
      "No debe mostrar el mensaje descriptivo secundario",
    ).not.toBeInTheDocument();
  });
});
