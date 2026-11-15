import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient, type FetchFn } from "../../shared/api/client";

function renderCatalogScreen(
  fetchFn: FetchFn,
  initialEntry = "/catalogos?seccion=prestaciones",
  role: "administrador" | "recepcion" | "odontologo" = "administrador",
) {
  const tokenStore = createMemoryTokenStore("token-test");
  const router = createMemoryRouter(createAppRoutes(), {
    initialEntries: [initialEntry],
  });

  const wrappedFetchFn: FetchFn = async (url, init) => {
    if (url.endsWith("/auth/me")) {
      return new Response(
        JSON.stringify({
          id: "00000000-0000-0000-0000-0000000000e1",
          username: "admin",
          displayName: "Admin Demo",
          role,
          professionalId: null,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    return fetchFn(url, init);
  };

  const clientWithAuth = createApiClient({
    baseUrl: "http://localhost:8000/api",
    fetchFn: wrappedFetchFn,
  });

  return render(
    <AuthProvider tokenStore={tokenStore} client={clientWithAuth}>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
}

describe("CatalogFormDialog", () => {
  it("Alta de prestación con duración numérica", async () => {
    const user = userEvent.setup();
    let sentBody: Record<string, unknown> | null = null;
    let getCallCount = 0;

    const fetchFn: FetchFn = async (url, init) => {
      if (url.includes("/services") && init?.method === "POST") {
        sentBody = JSON.parse(String(init.body)) as Record<string, unknown>;
        return new Response(
          JSON.stringify({
            id: "s-new",
            name: sentBody["name"],
            defaultDurationMin: 30,
            active: true,
          }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/services") && (!init?.method || init.method === "GET")) {
        getCallCount++;
        return new Response(
          JSON.stringify([
            { id: "s-1", name: "Consulta", defaultDurationMin: 15, active: true },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderCatalogScreen(fetchFn, "/catalogos?seccion=prestaciones");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Nueva prestación" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Nueva prestación" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("Nombre"), "Extracción");
    await user.type(screen.getByLabelText("Duración (min)"), "30");

    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    expect(sentBody).not.toBeNull();
    expect(sentBody).toEqual({ name: "Extracción", defaultDurationMin: 30 });
    const payload = sentBody as unknown as Record<string, unknown>;
    expect(typeof payload["defaultDurationMin"]).toBe("number");
    expect(getCallCount).toBeGreaterThanOrEqual(2);
    expect(screen.getByRole("status")).toHaveTextContent("Prestación creada.");
  });

  it("Duración no entera no se envía", async () => {
    const user = userEvent.setup();
    let postCalled = false;

    const fetchFn: FetchFn = async (url, init) => {
      if (url.includes("/services") && init?.method === "POST") {
        postCalled = true;
        return new Response(JSON.stringify({ id: "s-err" }), { status: 201 });
      }
      if (url.includes("/services") && (!init?.method || init.method === "GET")) {
        return new Response(
          JSON.stringify([]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderCatalogScreen(fetchFn, "/catalogos?seccion=prestaciones");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Nueva prestación" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Nueva prestación" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("Nombre"), "Control");

    // Caso 1: Duración vacía
    const durationInput = screen.getByLabelText("Duración (min)");
    await user.clear(durationInput);
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(postCalled).toBe(false);
    expect(durationInput).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByText("La duración debe ser un número entero de minutos.")).toBeInTheDocument();

    // Caso 2: Duración no entera
    await user.type(durationInput, "abc");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(postCalled).toBe(false);
    expect(durationInput).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByText("La duración debe ser un número entero de minutos.")).toBeInTheDocument();
  });

  it("Duración inválida muestra el mensaje literal del backend", async () => {
    const user = userEvent.setup();

    const fetchFn: FetchFn = async (url, init) => {
      if (url.includes("/services") && init?.method === "POST") {
        return new Response(
          JSON.stringify({
            violations: [
              {
                code: "INVALID_DURATION",
                message:
                  "La duración de la prestación no es válida (se recibió 7 minutos): debe ser múltiplo de 5 minutos.",
              },
            ],
          }),
          { status: 422, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/services") && (!init?.method || init.method === "GET")) {
        return new Response(
          JSON.stringify([]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderCatalogScreen(fetchFn, "/catalogos?seccion=prestaciones");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Nueva prestación" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Nueva prestación" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("Nombre"), "Control");
    await user.type(screen.getByLabelText("Duración (min)"), "7");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => {
      expect(screen.queryByRole("alert")).toBeInTheDocument();
    });

    expect(screen.queryByRole("dialog")).toBeInTheDocument();
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(
      "La duración de la prestación no es válida (se recibió 7 minutos): debe ser múltiplo de 5 minutos.",
    );
    expect(alert).toHaveFocus();
  });

  it("Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME)", async () => {
    const user = userEvent.setup();

    const fetchFn: FetchFn = async (url, init) => {
      if (url.includes("/services") && init?.method === "POST") {
        return new Response(
          JSON.stringify({
            violations: [
              {
                code: "DUPLICATE_NAME",
                message: 'Ya existe una prestación con el nombre "Limpieza".',
              },
            ],
          }),
          { status: 409, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/services") && (!init?.method || init.method === "GET")) {
        return new Response(
          JSON.stringify([]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderCatalogScreen(fetchFn, "/catalogos?seccion=prestaciones");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Nueva prestación" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Nueva prestación" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText("Nombre");
    const durationInput = screen.getByLabelText("Duración (min)");

    await user.type(nameInput, "Limpieza");
    await user.type(durationInput, "45");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => {
      expect(screen.queryByRole("alert")).toBeInTheDocument();
    });

    expect(screen.queryByRole("dialog")).toBeInTheDocument();
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent('Ya existe una prestación con el nombre "Limpieza".');
    expect(alert).toHaveFocus();
    expect(nameInput).toHaveValue("Limpieza");
    expect(durationInput).toHaveValue(45);
    expect(nameInput).not.toHaveAttribute("aria-invalid", "true");
  });

  it("Edición de profesional con matrícula vacía", async () => {
    const user = userEvent.setup();
    let putBody: Record<string, unknown> | null = null;

    const fetchFn: FetchFn = async (url, init) => {
      if (url.includes("/professionals/prof-1") && init?.method === "PUT") {
        putBody = JSON.parse(String(init.body)) as Record<string, unknown>;
        return new Response(
          JSON.stringify({
            id: "prof-1",
            fullName: putBody["fullName"],
            licenseNumber: putBody["licenseNumber"],
            active: true,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/professionals") && (!init?.method || init.method === "GET")) {
        return new Response(
          JSON.stringify([
            {
              id: "prof-1",
              fullName: "Dra. Laura Quiroga",
              licenseNumber: "MN 1234",
              active: true,
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not found", { status: 404 });
    };

    renderCatalogScreen(fetchFn, "/catalogos");

    await waitFor(() => {
      expect(screen.getByText("Dra. Laura Quiroga")).toBeInTheDocument();
    });

    const editBtn = screen.getByRole("button", { name: "Editar" });
    await user.click(editBtn);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const licenseInput = screen.getByLabelText("Matrícula");
    expect(licenseInput).toHaveValue("MN 1234");

    await user.clear(licenseInput);
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    expect(putBody).not.toBeNull();
    expect(putBody).toEqual({
      fullName: "Dra. Laura Quiroga",
      licenseNumber: null,
    });
    expect(screen.getByRole("status")).toHaveTextContent("Profesional actualizado.");
  });
});
