import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient, type FetchFn } from "../../shared/api/client";

function renderPacientesScreen(fetchFn: FetchFn) {
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

describe("PatientFormDialog", () => {
  it("Alta de paciente", async () => {
    const user = userEvent.setup();
    const postedBodies: unknown[] = [];
    let getCalls = 0;

    const fetchFn: FetchFn = async (url, init) => {
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
      if (url.endsWith("/patients") && init?.method === "POST") {
        const parsed = JSON.parse(String(init.body));
        postedBodies.push(parsed);
        return new Response(
          JSON.stringify({
            id: "p-new",
            fullName: parsed.fullName,
            dni: parsed.dni,
            phone: parsed.phone,
            healthInsurance: parsed.healthInsurance,
          }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients") && (!init?.method || init.method === "GET")) {
        getCalls += 1;
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response("Not found", { status: 404 });
    };

    renderPacientesScreen(fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Nuevo paciente" })).toBeInTheDocument();
    });

    const initialGetCalls = getCalls;
    await user.click(screen.getByRole("button", { name: "Nuevo paciente" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("Nombre y apellido"), "Carla Medina");
    await user.type(screen.getByLabelText("DNI"), "27.123.456");

    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    expect(postedBodies).toHaveLength(1);
    expect(postedBodies[0]).toEqual({
      fullName: "Carla Medina",
      dni: "27.123.456",
      phone: null,
      healthInsurance: null,
    });

    expect(getCalls).toBeGreaterThan(initialGetCalls);
    expect(screen.getByRole("status")).toHaveTextContent("Paciente creado.");
  });

  it("El formulario de paciente tiene solo los cuatro datos mínimos", async () => {
    const user = userEvent.setup();

    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e1",
            username: "administrador",
            displayName: "Administrador Demo",
            role: "administrador",
            professionalId: null,
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

    renderPacientesScreen(fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Nuevo paciente" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Nuevo paciente" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const dialog = screen.getByRole("dialog");
    const editableInputs = dialog.querySelectorAll("input[type='text'], input:not([type])");
    expect(editableInputs).toHaveLength(4);

    expect(screen.getByLabelText("Nombre y apellido")).toBeInTheDocument();
    expect(screen.getByLabelText("DNI")).toBeInTheDocument();
    expect(screen.getByLabelText("Teléfono")).toBeInTheDocument();
    expect(screen.getByLabelText("Obra social")).toBeInTheDocument();

    expect(screen.queryByRole("button", { name: "Desactivar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reactivar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Eliminar" })).not.toBeInTheDocument();
  });

  it("Edición de paciente con valores precargados", async () => {
    const user = userEvent.setup();
    const putBodies: unknown[] = [];

    const fetchFn: FetchFn = async (url, init) => {
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
      if (url.includes("/patients/p-1") && init?.method === "PUT") {
        const parsed = JSON.parse(String(init.body));
        putBodies.push(parsed);
        return new Response(
          JSON.stringify({
            id: "p-1",
            fullName: parsed.fullName,
            dni: parsed.dni,
            phone: parsed.phone,
            healthInsurance: parsed.healthInsurance,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients") && (!init?.method || init.method === "GET")) {
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

    renderPacientesScreen(fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("row", { name: /Ana Pérez/ })).toBeInTheDocument();
    });

    const editBtn = screen.getByRole("button", { name: "Editar" });
    await user.click(editBtn);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    expect(screen.getByRole("heading", { name: "Editar paciente" })).toBeInTheDocument();

    const nameInput = screen.getByLabelText("Nombre y apellido");
    const dniInput = screen.getByLabelText("DNI");
    const phoneInput = screen.getByLabelText("Teléfono");
    const osInput = screen.getByLabelText("Obra social");

    expect(nameInput).toHaveValue("Ana Pérez");
    expect(dniInput).toHaveValue("30111222");
    expect(phoneInput).toHaveValue("11-4444-5555");
    expect(osInput).toHaveValue("OSDE");

    await user.clear(phoneInput);
    await user.type(phoneInput, "11-1234-5678");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    expect(putBodies).toHaveLength(1);
    expect(putBodies[0]).toEqual({
      fullName: "Ana Pérez",
      dni: "30111222",
      phone: "11-1234-5678",
      healthInsurance: "OSDE",
    });

    expect(screen.getByRole("status")).toHaveTextContent("Paciente actualizado.");
  });

  it("DNI duplicado muestra el mensaje literal del backend", async () => {
    const user = userEvent.setup();

    const fetchFn: FetchFn = async (url, init) => {
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
      if (url.endsWith("/patients") && init?.method === "POST") {
        return new Response(
          JSON.stringify({
            violations: [
              {
                code: "DUPLICATE_DNI",
                message: "Ya existe un paciente con el DNI 30.111.222.",
              },
            ],
          }),
          { status: 409, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients") && (!init?.method || init.method === "GET")) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response("Not found", { status: 404 });
    };

    renderPacientesScreen(fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Nuevo paciente" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Nuevo paciente" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText("Nombre y apellido");
    const dniInput = screen.getByLabelText("DNI");

    await user.type(nameInput, "Carlos Soto");
    await user.type(dniInput, "30111222");

    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(nameInput).toHaveValue("Carlos Soto");
    expect(dniInput).toHaveValue("30111222");

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Ya existe un paciente con el DNI 30.111.222.");
    expect(alert).toHaveFocus();

    expect(dniInput).not.toHaveAttribute("aria-invalid");
  });

  it("DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI)", async () => {
    const user = userEvent.setup();
    const postRequests: unknown[] = [];

    const fetchFn: FetchFn = async (url, init) => {
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
      if (url.endsWith("/patients") && init?.method === "POST") {
        postRequests.push(JSON.parse(String(init.body)));
        return new Response(
          JSON.stringify({
            violations: [
              {
                code: "INVALID_DNI",
                message: 'El DNI no es válido (se recibió "1234"): debe tener 7 u 8 dígitos, con o sin puntos.',
              },
            ],
          }),
          { status: 422, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients") && (!init?.method || init.method === "GET")) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response("Not found", { status: 404 });
    };

    renderPacientesScreen(fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Nuevo paciente" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Nuevo paciente" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText("Nombre y apellido");
    const dniInput = screen.getByLabelText("DNI");

    await user.type(nameInput, "Diego Ríos");
    await user.type(dniInput, "1234");

    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(nameInput).toHaveValue("Diego Ríos");
    expect(dniInput).toHaveValue("1234");

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent('El DNI no es válido (se recibió "1234"): debe tener 7 u 8 dígitos, con o sin puntos.');
    expect(alert).toHaveFocus();

    expect(postRequests).toHaveLength(1);
    expect(postRequests[0]).toMatchObject({ dni: "1234" });
  });

  it("Error 400 por campo marca el campo con aria-invalid", async () => {
    const user = userEvent.setup();

    const fetchFn: FetchFn = async (url, init) => {
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
      if (url.endsWith("/patients") && init?.method === "POST") {
        return new Response(
          JSON.stringify({
            errors: [
              {
                field: "fullName",
                type: "missing",
                message: "Falta este dato.",
              },
            ],
          }),
          { status: 400, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients") && (!init?.method || init.method === "GET")) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response("Not found", { status: 404 });
    };

    renderPacientesScreen(fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Nuevo paciente" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Nuevo paciente" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Guardar" }));

    const nameInput = await screen.findByLabelText("Nombre y apellido");
    await waitFor(() => {
      expect(nameInput).toHaveAttribute("aria-invalid", "true");
    });

    expect(nameInput).toHaveAttribute("aria-describedby", "fullName-error");
    const errorText = screen.getByText("Falta este dato.");
    expect(errorText).toBeInTheDocument();
    expect(errorText).toHaveAttribute("id", "fullName-error");
  });

  it("El mensaje de estado se reemplaza entre acciones sin desmontar la región", async () => {
    const user = userEvent.setup();

    const fetchFn: FetchFn = async (url, init) => {
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
      if (url.endsWith("/patients") && init?.method === "POST") {
        return new Response(
          JSON.stringify({
            id: "p-2",
            fullName: "Carla Medina",
            dni: "27123456",
            phone: null,
            healthInsurance: null,
          }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients/p-1") && init?.method === "PUT") {
        return new Response(
          JSON.stringify({
            id: "p-1",
            fullName: "Ana Pérez",
            dni: "30111222",
            phone: "11-9999-9999",
            healthInsurance: "OSDE",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/patients") && (!init?.method || init.method === "GET")) {
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

    renderPacientesScreen(fetchFn);

    await waitFor(() => {
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    const statusRegion = screen.getByRole("status");

    // Acción 1: Crear paciente
    await user.click(screen.getByRole("button", { name: "Nuevo paciente" }));
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("Nombre y apellido"), "Carla Medina");
    await user.type(screen.getByLabelText("DNI"), "27123456");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    expect(screen.getByRole("status")).toHaveTextContent("Paciente creado.");
    expect(screen.getByRole("status")).toBe(statusRegion);

    // Acción 2: Editar paciente existente
    const editBtn = screen.getByRole("button", { name: "Editar" });
    await user.click(editBtn);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const phoneInput = screen.getByLabelText("Teléfono");
    await user.clear(phoneInput);
    await user.type(phoneInput, "11-9999-9999");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    const currentStatus = screen.getByRole("status");
    expect(currentStatus).toBe(statusRegion);
    expect(currentStatus.textContent?.trim()).toBe("Paciente actualizado.");
    expect(screen.queryByText(/Paciente creado\./)).not.toBeInTheDocument();
  });
});
