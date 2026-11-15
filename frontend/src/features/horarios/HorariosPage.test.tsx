import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { createAppRoutes } from "../../App";
import { createFixedClock } from "../agenda/clock";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient, type FetchFn } from "../../shared/api/client";

const FIXED_NOW = new Date("2026-05-04T12:00:00Z");
const PROF_QUIROGA = "00000000-0000-0000-0000-000000000001";
const PROF_SOSA = "00000000-0000-0000-0000-000000000002";
const PROF_INACTIVO = "00000000-0000-0000-0000-000000000099";

describe("HorariosPage", () => {
  it("Odontólogo accede a sus propios horarios: carga tramos y bloqueos de su professionalId sin mostrar selector de profesional", async () => {
    const requestedUrls: string[] = [];

    const fetchFn: FetchFn = async (url) => {
      requestedUrls.push(url);
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e3",
            username: "quiroga",
            displayName: "Dra. Laura Quiroga",
            role: "odontologo",
            professionalId: PROF_QUIROGA,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/agenda?")) {
        return new Response(
          JSON.stringify({
            from: "2026-05-04",
            to: "2026-05-04",
            timezone: "America/Argentina/Buenos_Aires",
            appointments: [],
            workingHours: [],
            blocks: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_QUIROGA}/working-hours`)) {
        return new Response(
          JSON.stringify([
            {
              id: "wh-1",
              professionalId: PROF_QUIROGA,
              weekday: 1,
              start: "09:00",
              end: "13:00",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_QUIROGA}/blocks`)) {
        return new Response(
          JSON.stringify([
            {
              id: "blk-1",
              professionalId: PROF_QUIROGA,
              startAt: "2026-05-06T15:00:00Z",
              endAt: "2026-05-06T19:00:00Z",
              reason: "Congreso anual",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    const clock = createFixedClock(FIXED_NOW);
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(createAppRoutes(clock), {
      initialEntries: ["/horarios"],
      future: { v7_relativeSplatPath: true },
    });

    render(
      <AuthProvider tokenStore={createMemoryTokenStore("token-odontologo")} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Horarios semanales" })).not.toBeNull();
    });

    expect(
      (screen.getByLabelText("Inicio Lunes tramo 1") as HTMLInputElement).value,
    ).toBe("09:00");
    expect(screen.getByText("Congreso anual")).not.toBeNull();
    expect(screen.queryByLabelText("Profesional")).toBeNull();
    expect(
      requestedUrls.some((u) => u.endsWith(`/professionals/${PROF_QUIROGA}/working-hours`)),
    ).toBe(true);
    expect(
      requestedUrls.some((u) => u.endsWith(`/professionals/${PROF_QUIROGA}/blocks`)),
    ).toBe(true);
  });

  it("Administrador selecciona profesional activo: lista solo activos, selecciona el primero por defecto y al cambiar actualiza datos y ?professionalId=", async () => {
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e1",
            username: "admin",
            displayName: "Administrador",
            role: "administrador",
            professionalId: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith("/professionals")) {
        return new Response(
          JSON.stringify([
            {
              id: PROF_QUIROGA,
              fullName: "Dra. Laura Quiroga",
              licenseNumber: "MN-10101",
              active: true,
            },
            {
              id: PROF_SOSA,
              fullName: "Dr. Martín Sosa",
              licenseNumber: "MN-20202",
              active: true,
            },
            {
              id: PROF_INACTIVO,
              fullName: "Dr. Carlos Inactivo",
              licenseNumber: "MN-99999",
              active: false,
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/agenda?")) {
        return new Response(
          JSON.stringify({
            from: "2026-05-04",
            to: "2026-05-04",
            timezone: "America/Argentina/Buenos_Aires",
            appointments: [],
            workingHours: [],
            blocks: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_QUIROGA}/working-hours`)) {
        return new Response(
          JSON.stringify([
            {
              id: "wh-1",
              professionalId: PROF_QUIROGA,
              weekday: 1,
              start: "09:00",
              end: "13:00",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_QUIROGA}/blocks`)) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url.endsWith(`/professionals/${PROF_SOSA}/working-hours`)) {
        return new Response(
          JSON.stringify([
            {
              id: "wh-2",
              professionalId: PROF_SOSA,
              weekday: 1,
              start: "14:00",
              end: "18:00",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_SOSA}/blocks`)) {
        return new Response(
          JSON.stringify([
            {
              id: "blk-2",
              professionalId: PROF_SOSA,
              startAt: "2026-05-07T15:00:00Z",
              endAt: "2026-05-07T18:00:00Z",
              reason: "Jornada docente",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    const clock = createFixedClock(FIXED_NOW);
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(createAppRoutes(clock), {
      initialEntries: ["/horarios"],
      future: { v7_relativeSplatPath: true },
    });

    render(
      <AuthProvider tokenStore={createMemoryTokenStore("token-admin")} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByLabelText("Profesional")).not.toBeNull();
    });

    const select = screen.getByLabelText("Profesional") as HTMLSelectElement;
    const options = Array.from(select.options).map((opt) => opt.textContent);
    expect(options).toEqual(["Dra. Laura Quiroga", "Dr. Martín Sosa"]);
    expect(select.value).toBe(PROF_QUIROGA);

    await waitFor(() => {
      expect(
        (screen.getByLabelText("Inicio Lunes tramo 1") as HTMLInputElement).value,
      ).toBe("09:00");
    });

    fireEvent.change(select, { target: { value: PROF_SOSA } });

    await waitFor(() => {
      expect(router.state.location.search).toBe(`?professionalId=${PROF_SOSA}`);
    });
    await waitFor(() => {
      expect(
        (screen.getByLabelText("Inicio Lunes tramo 1") as HTMLInputElement).value,
      ).toBe("14:00");
    });
    expect(screen.getByText("Jornada docente")).not.toBeNull();
  });

  it("Odontólogo consulta profesional ajeno y recibe 403: muestra en role=alert el mensaje literal del backend sin controles de edición ni cerrar sesión", async () => {
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e3",
            username: "quiroga",
            displayName: "Dra. Laura Quiroga",
            role: "odontologo",
            professionalId: PROF_QUIROGA,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/agenda?")) {
        return new Response(
          JSON.stringify({
            from: "2026-05-04",
            to: "2026-05-04",
            timezone: "America/Argentina/Buenos_Aires",
            appointments: [],
            workingHours: [],
            blocks: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes(`/professionals/${PROF_SOSA}/`)) {
        return new Response(
          JSON.stringify({
            error: "FORBIDDEN_OPERATION",
            violations: [
              {
                code: "FORBIDDEN_OPERATION",
                message: "No tiene permiso para leer horarios.",
              },
            ],
          }),
          { status: 403, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    const tokenStore = createMemoryTokenStore("token-odontologo");
    const clock = createFixedClock(FIXED_NOW);
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(createAppRoutes(clock), {
      initialEntries: [`/horarios?professionalId=${PROF_SOSA}`],
      future: { v7_relativeSplatPath: true },
    });

    render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeNull();
    });

    expect(screen.getByRole("alert").textContent).toContain(
      "No tiene permiso para leer horarios.",
    );
    expect(screen.queryByRole("button", { name: "Guardar horario" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Nuevo bloqueo" })).toBeNull();
    expect(tokenStore.getToken()).toBe("token-odontologo");
    expect(router.state.location.pathname).toBe("/horarios");
  });

  it("Recepción visualiza información completa sin controles de edición: muestra selector, tramos y bloqueos pero oculta Agregar tramo, Quitar, Guardar horario, Nuevo bloqueo y Eliminar bloqueo", async () => {
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e2",
            username: "recepcion",
            displayName: "Recepción",
            role: "recepcion",
            professionalId: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith("/professionals")) {
        return new Response(
          JSON.stringify([
            {
              id: PROF_QUIROGA,
              fullName: "Dra. Laura Quiroga",
              licenseNumber: "MN-10101",
              active: true,
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/agenda?")) {
        return new Response(
          JSON.stringify({
            from: "2026-05-04",
            to: "2026-05-04",
            timezone: "America/Argentina/Buenos_Aires",
            appointments: [],
            workingHours: [],
            blocks: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_QUIROGA}/working-hours`)) {
        return new Response(
          JSON.stringify([
            {
              id: "wh-1",
              professionalId: PROF_QUIROGA,
              weekday: 1,
              start: "09:00",
              end: "13:00",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_QUIROGA}/blocks`)) {
        return new Response(
          JSON.stringify([
            {
              id: "blk-1",
              professionalId: PROF_QUIROGA,
              startAt: "2026-05-06T15:00:00Z",
              endAt: "2026-05-06T19:00:00Z",
              reason: "Reunión clínica",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    const clock = createFixedClock(FIXED_NOW);
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(createAppRoutes(clock), {
      initialEntries: ["/horarios"],
      future: { v7_relativeSplatPath: true },
    });

    render(
      <AuthProvider tokenStore={createMemoryTokenStore("token-recepcion")} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Horarios semanales" })).not.toBeNull();
    });

    expect(screen.queryByLabelText("Profesional")).not.toBeNull();
    expect(screen.getByText("Reunión clínica")).not.toBeNull();
    expect(screen.queryAllByRole("button", { name: /Agregar tramo/i })).toHaveLength(0);
    expect(screen.queryAllByRole("button", { name: /Quitar/i })).toHaveLength(0);
    expect(screen.queryByRole("button", { name: "Guardar horario" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Nuevo bloqueo" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Eliminar bloqueo" })).toBeNull();
  });

  it("Zona horaria leída desde GET /api/agenda: consulta GET /api/agenda una sola vez, reutiliza su timezone al cambiar de profesional y formatea bloqueos según esa zona", async () => {
    let agendaCalls = 0;

    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e1",
            username: "admin",
            displayName: "Administrador",
            role: "administrador",
            professionalId: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith("/professionals")) {
        return new Response(
          JSON.stringify([
            {
              id: PROF_QUIROGA,
              fullName: "Dra. Laura Quiroga",
              licenseNumber: "MN-10101",
              active: true,
            },
            {
              id: PROF_SOSA,
              fullName: "Dr. Martín Sosa",
              licenseNumber: "MN-20202",
              active: true,
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/agenda?")) {
        agendaCalls += 1;
        return new Response(
          JSON.stringify({
            from: "2026-05-04",
            to: "2026-05-04",
            timezone: "UTC",
            appointments: [],
            workingHours: [],
            blocks: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_QUIROGA}/working-hours`)) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url.endsWith(`/professionals/${PROF_QUIROGA}/blocks`)) {
        return new Response(
          JSON.stringify([
            {
              id: "blk-utc-1",
              professionalId: PROF_QUIROGA,
              startAt: "2026-05-06T15:00:00Z",
              endAt: "2026-05-06T19:00:00Z",
              reason: " Guardia UTC",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_SOSA}/working-hours`)) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url.endsWith(`/professionals/${PROF_SOSA}/blocks`)) {
        return new Response(
          JSON.stringify([
            {
              id: "blk-utc-2",
              professionalId: PROF_SOSA,
              startAt: "2026-05-08T10:00:00Z",
              endAt: "2026-05-08T12:00:00Z",
              reason: "Ateneo UTC",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    const clock = createFixedClock(FIXED_NOW);
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(createAppRoutes(clock), {
      initialEntries: ["/horarios"],
      future: { v7_relativeSplatPath: true },
    });

    render(
      <AuthProvider tokenStore={createMemoryTokenStore("token-admin")} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Bloqueos de agenda" })).not.toBeNull();
    });

    expect(screen.queryByText(/mié, 06\/05\/2026 · 15:00 a 19:00/)).not.toBeNull();
    expect(agendaCalls).toBe(1);

    const select = screen.getByLabelText("Profesional");
    fireEvent.change(select, { target: { value: PROF_SOSA } });

    await waitFor(() => {
      expect(screen.queryByText(/vie, 08\/05\/2026 · 10:00 a 12:00/)).not.toBeNull();
    });
    expect(agendaCalls).toBe(1);
  });

  it("Título de PageShell Horarios y bloqueos con único h1: pasa title Horarios y bloqueos a PageShell y mantiene un solo h1", async () => {
    const fetchFn: FetchFn = async (url) => {
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e3",
            username: "quiroga",
            displayName: "Dra. Laura Quiroga",
            role: "odontologo",
            professionalId: PROF_QUIROGA,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/agenda?")) {
        return new Response(
          JSON.stringify({
            from: "2026-05-04",
            to: "2026-05-04",
            timezone: "America/Argentina/Buenos_Aires",
            appointments: [],
            workingHours: [],
            blocks: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    const clock = createFixedClock(FIXED_NOW);
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(createAppRoutes(clock), {
      initialEntries: ["/horarios"],
      future: { v7_relativeSplatPath: true },
    });

    render(
      <AuthProvider tokenStore={createMemoryTokenStore("token-odontologo")} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Horarios semanales" })).not.toBeNull();
    });

    expect(screen.queryAllByText("Horarios y bloqueos", { selector: "span" })).toHaveLength(1);
    const headingsH1 = screen.getAllByRole("heading", { level: 1 });
    expect(headingsH1).toHaveLength(1);
    expect(headingsH1[0]?.textContent).toBe("Horarios y bloqueos");
  });

  it("Un solo mensaje de estado vigente entre acciones sin desmontar la región: reemplaza Horario guardado por Bloqueo eliminado y mantiene una única región role=status montada", async () => {
    const fetchFn: FetchFn = async (url, init) => {
      const method = init?.method ?? "GET";
      if (url.endsWith("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000e3",
            username: "quiroga",
            displayName: "Dra. Laura Quiroga",
            role: "odontologo",
            professionalId: PROF_QUIROGA,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/agenda?")) {
        return new Response(
          JSON.stringify({
            from: "2026-05-04",
            to: "2026-05-04",
            timezone: "America/Argentina/Buenos_Aires",
            appointments: [],
            workingHours: [],
            blocks: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_QUIROGA}/working-hours`) && method === "GET") {
        return new Response(
          JSON.stringify([
            {
              id: "wh-1",
              professionalId: PROF_QUIROGA,
              weekday: 1,
              start: "09:00",
              end: "13:00",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_QUIROGA}/working-hours`) && method === "PUT") {
        return new Response(
          JSON.stringify({
            workingHours: [
              {
                id: "wh-1",
                professionalId: PROF_QUIROGA,
                weekday: 1,
                start: "09:00",
                end: "13:00",
              },
            ],
            appointmentsOutsideHours: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_QUIROGA}/blocks`) && method === "GET") {
        return new Response(
          JSON.stringify([
            {
              id: "blk-1",
              professionalId: PROF_QUIROGA,
              startAt: "2026-05-06T15:00:00Z",
              endAt: "2026-05-06T19:00:00Z",
              reason: "Congreso anual",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith("/blocks/blk-1") && method === "DELETE") {
        return new Response(
          JSON.stringify({
            id: "blk-1",
            professionalId: PROF_QUIROGA,
            startAt: "2026-05-06T15:00:00Z",
            endAt: "2026-05-06T19:00:00Z",
            reason: "Congreso anual",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    const clock = createFixedClock(FIXED_NOW);
    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });
    const router = createMemoryRouter(createAppRoutes(clock), {
      initialEntries: ["/horarios"],
      future: { v7_relativeSplatPath: true },
    });

    render(
      <AuthProvider tokenStore={createMemoryTokenStore("token-odontologo")} client={client}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Horarios semanales" })).not.toBeNull();
    });

    expect(screen.queryAllByRole("status")).toHaveLength(1);
    expect(screen.getByRole("status").textContent).toBe("");

    fireEvent.click(screen.getByRole("button", { name: "Guardar horario" }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent("Horario guardado.");
    });
    expect(screen.queryAllByRole("status")).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: "Eliminar bloqueo" }));
    expect(screen.queryAllByRole("status")).toHaveLength(1);
    expect(screen.getByRole("status").textContent).toBe("");

    fireEvent.click(screen.getByRole("button", { name: "Sí, eliminar bloqueo" }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent("Bloqueo eliminado.");
    });
    expect(screen.queryAllByRole("status")).toHaveLength(1);
    expect(screen.queryByText("Horario guardado.")).toBeNull();
  });
});
