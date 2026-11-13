import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { createFixedClock } from "./clock";

const FIXED_CLOCK = createFixedClock(new Date("2026-11-16T12:00:00Z"));

const RECEPCION_USER = {
  id: "00000000-0000-0000-0000-0000000000e2",
  username: "recepcion",
  displayName: "Recepción Demo",
  role: "recepcion" as const,
  professionalId: null,
};

const PROFESSIONALS = [
  {
    id: "00000000-0000-0000-0000-000000000001",
    fullName: "Dra. Laura Quiroga",
    licenseNumber: "MP-1001",
    active: true,
  },
];

const CHAIRS = [
  { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón 1", active: true },
];

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("AgendaPage — Integración con AppointmentFormDialog", () => {
  it("al pulsar Nuevo turno abre el diálogo y tras alta exitosa (201) cierra y refresca la agenda", async () => {
    const requestedUrls: string[] = [];
    const fetchFn: FetchFn = async (url, init) => {
      requestedUrls.push(url);
      if (url.endsWith("/auth/me")) {
        return jsonResponse(RECEPCION_USER);
      }
      if (url.endsWith("/professionals")) {
        return jsonResponse(PROFESSIONALS);
      }
      if (url.endsWith("/chairs")) {
        return jsonResponse(CHAIRS);
      }
      if (url.includes("/services")) {
        return jsonResponse([
          {
            id: "00000000-0000-0000-0000-0000000000d1",
            name: "Extracción",
            defaultDurationMin: 60,
            active: true,
          },
        ]);
      }
      if (url.includes("/patients")) {
        return jsonResponse([
          {
            id: "00000000-0000-0000-0000-0000000000c1",
            fullName: "Ana Pérez",
            dni: "30111222",
            phone: "11-4444-5555",
            notes: null,
            active: true,
          },
        ]);
      }
      if (url.includes("/appointments") && init?.method === "POST") {
        return jsonResponse(
          {
            id: "00000000-0000-0000-0000-000000000099",
            patientId: "00000000-0000-0000-0000-0000000000c1",
            professionalId: "00000000-0000-0000-0000-000000000001",
            chairId: "00000000-0000-0000-0000-0000000000b1",
            serviceId: "00000000-0000-0000-0000-0000000000d1",
            startAt: "2026-11-16T10:00:00-03:00",
            endAt: "2026-11-16T11:00:00-03:00",
            status: "reservado",
          },
          201,
        );
      }
      if (url.includes("/agenda?")) {
        return jsonResponse({
          from: "2026-11-16",
          to: "2026-11-16",
          timezone: "America/Argentina/Buenos_Aires",
          appointments: [],
          workingHours: [],
          blocks: [],
        });
      }
      return jsonResponse({ detail: "Not found" }, 404);
    };

    const tokenStore = createMemoryTokenStore("token-recepcion-123");
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(createAppRoutes(FIXED_CLOCK), {
      initialEntries: [
        "/agenda?date=2026-11-16&professionalId=00000000-0000-0000-0000-000000000001&chairId=00000000-0000-0000-0000-0000000000b1",
      ],
    });

    render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    const newBtn = await screen.findByRole("button", { name: "Nuevo turno" });
    expect(newBtn).not.toBeNull();
    fireEvent.click(newBtn);

    // Diálogo abierto
    const dialogTitle = await screen.findByRole("heading", { name: "Nuevo turno" });
    expect(dialogTitle).not.toBeNull();

    // Buscar y seleccionar paciente
    const searchInput = screen.queryByRole("searchbox", { name: /buscar paciente/i });
    expect(searchInput).not.toBeNull();
    fireEvent.change(searchInput!, { target: { value: "Pérez" } });
    const searchBtn = screen.queryByRole("button", { name: "Buscar paciente" });
    expect(searchBtn).not.toBeNull();
    fireEvent.click(searchBtn!);

    await screen.findByRole("button", { name: "Buscar paciente" });
    const radioAna = screen.queryByRole("radio", { name: /Ana Pérez/i });
    expect(radioAna).not.toBeNull();
    fireEvent.click(radioAna!);

    // Ingresar hora
    const timeInput = screen.queryByLabelText<HTMLInputElement>("Hora");
    expect(timeInput).not.toBeNull();
    fireEvent.change(timeInput!, { target: { value: "10:00" } });

    // Seleccionar prestación
    const serviceSelect = await screen.findByLabelText("Prestación");
    expect(serviceSelect).not.toBeNull();
    fireEvent.change(serviceSelect, {
      target: { value: "00000000-0000-0000-0000-0000000000d1" },
    });

    const agendaCallsBefore = requestedUrls.filter((u) => u.includes("/agenda?")).length;

    // Click submit
    const submitBtn = screen.queryByRole("button", { name: "Crear turno" });
    expect(submitBtn).not.toBeNull();
    fireEvent.click(submitBtn!);

    // Modal debe cerrarse y disparar refresh de agenda
    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Nuevo turno" })).toBeNull();
    });

    const agendaCallsAfter = requestedUrls.filter((u) => u.includes("/agenda?")).length;
    expect(agendaCallsAfter).toBeGreaterThan(agendaCallsBefore);
  });

  it("tras alta exitosa (201) anuncia el turno creado en una región de estado accesible", async () => {
    const fetchFn: FetchFn = async (url, init) => {
      if (url.endsWith("/auth/me")) {
        return jsonResponse(RECEPCION_USER);
      }
      if (url.endsWith("/professionals")) {
        return jsonResponse(PROFESSIONALS);
      }
      if (url.endsWith("/chairs")) {
        return jsonResponse(CHAIRS);
      }
      if (url.includes("/services")) {
        return jsonResponse([
          {
            id: "00000000-0000-0000-0000-0000000000d1",
            name: "Extracción",
            defaultDurationMin: 60,
            active: true,
          },
        ]);
      }
      if (url.includes("/patients")) {
        return jsonResponse([
          {
            id: "00000000-0000-0000-0000-0000000000c1",
            fullName: "Ana Pérez",
            dni: "30111222",
            phone: "11-4444-5555",
            notes: null,
            active: true,
          },
        ]);
      }
      if (url.includes("/appointments") && init?.method === "POST") {
        return jsonResponse(
          {
            id: "00000000-0000-0000-0000-000000000099",
            patientId: "00000000-0000-0000-0000-0000000000c1",
            professionalId: "00000000-0000-0000-0000-000000000001",
            chairId: "00000000-0000-0000-0000-0000000000b1",
            serviceId: "00000000-0000-0000-0000-0000000000d1",
            startAt: "2026-11-16T10:00:00-03:00",
            endAt: "2026-11-16T11:00:00-03:00",
            status: "reservado",
          },
          201,
        );
      }
      if (url.includes("/agenda?")) {
        return jsonResponse({
          from: "2026-11-16",
          to: "2026-11-16",
          timezone: "America/Argentina/Buenos_Aires",
          appointments: [],
          workingHours: [],
          blocks: [],
        });
      }
      return jsonResponse({ detail: "Not found" }, 404);
    };

    const tokenStore = createMemoryTokenStore("token-recepcion-123");
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(createAppRoutes(FIXED_CLOCK), {
      initialEntries: [
        "/agenda?date=2026-11-16&professionalId=00000000-0000-0000-0000-000000000001&chairId=00000000-0000-0000-0000-0000000000b1",
      ],
    });

    render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    const newBtn = await screen.findByRole("button", { name: "Nuevo turno" });
    fireEvent.click(newBtn);

    await screen.findByRole("heading", { name: "Nuevo turno" });

    const searchInput = screen.queryByRole("searchbox", { name: /buscar paciente/i });
    fireEvent.change(searchInput!, { target: { value: "Pérez" } });
    const searchBtn = screen.queryByRole("button", { name: "Buscar paciente" });
    fireEvent.click(searchBtn!);

    await screen.findByRole("button", { name: "Buscar paciente" });
    const radioAna = screen.queryByRole("radio", { name: /Ana Pérez/i });
    fireEvent.click(radioAna!);

    const timeInput = screen.queryByLabelText<HTMLInputElement>("Hora");
    fireEvent.change(timeInput!, { target: { value: "10:00" } });

    const serviceSelect = await screen.findByLabelText("Prestación");
    fireEvent.change(serviceSelect, {
      target: { value: "00000000-0000-0000-0000-0000000000d1" },
    });

    const submitBtn = screen.queryByRole("button", { name: "Crear turno" });
    fireEvent.click(submitBtn!);

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Nuevo turno" })).toBeNull();
    });

    const statusRegion = screen.getByRole("status");
    expect(statusRegion).toHaveTextContent("Turno creado para el 16/11/2026 a las 10:00.");
  });
});
