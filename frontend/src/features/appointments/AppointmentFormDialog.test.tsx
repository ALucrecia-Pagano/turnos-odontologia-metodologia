import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useRef, useState } from "react";
import { describe, expect, it } from "vitest";
import { createApiClient } from "../../shared/api/client";
import { AppointmentFormDialog, buildStartAtIso } from "./AppointmentFormDialog";

const PROFESSIONALS = [
  { id: "00000000-0000-0000-0000-000000000001", fullName: "Dra. Laura Quiroga", licenseNumber: "MN-1234", active: true },
  { id: "00000000-0000-0000-0000-000000000002", fullName: "Dr. Martín Sosa", licenseNumber: "MN-5678", active: true },
];

const CHAIRS = [
  { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón 1", active: true },
  { id: "00000000-0000-0000-0000-0000000000b2", name: "Sillón 2", active: true },
];

describe("AppointmentFormDialog", () => {
  it("apertura y foco inicial", () => {
    const client = createApiClient({ fetchFn: async () => new Response("[]") });
    render(
      <AppointmentFormDialog
        open={true}
        onClose={() => undefined}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
      />,
    );

    const dialog = screen.queryByRole("dialog");
    expect(dialog).not.toBeNull();

    const searchInput = screen.queryByRole("searchbox", { name: /buscar paciente/i });
    expect(searchInput).not.toBeNull();
    expect(searchInput).toHaveFocus();
  });

  it("prellenado con fecha y filtros activos", () => {
    const client = createApiClient({ fetchFn: async () => new Response("[]") });
    render(
      <AppointmentFormDialog
        open={true}
        onClose={() => undefined}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        initialProfessionalId="00000000-0000-0000-0000-000000000001"
        initialChairId="00000000-0000-0000-0000-0000000000b1"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
      />,
    );

    const dateInput = screen.queryByLabelText<HTMLInputElement>("Fecha");
    expect(dateInput).not.toBeNull();
    expect(dateInput?.value).toBe("2026-11-16");

    const profSelect = screen.queryByLabelText<HTMLSelectElement>("Profesional");
    expect(profSelect).not.toBeNull();
    expect(profSelect?.value).toBe("00000000-0000-0000-0000-000000000001");

    const chairSelect = screen.queryByLabelText<HTMLSelectElement>("Sillón");
    expect(chairSelect).not.toBeNull();
    expect(chairSelect?.value).toBe("00000000-0000-0000-0000-0000000000b1");
  });

  it("sin filtros activos los selectores quedan sin selección", () => {
    const client = createApiClient({ fetchFn: async () => new Response("[]") });
    render(
      <AppointmentFormDialog
        open={true}
        onClose={() => undefined}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        initialProfessionalId={null}
        initialChairId={null}
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
      />,
    );

    const profSelect = screen.queryByLabelText<HTMLSelectElement>("Profesional");
    expect(profSelect).not.toBeNull();
    expect(profSelect?.value).toBe("");

    const chairSelect = screen.queryByLabelText<HTMLSelectElement>("Sillón");
    expect(chairSelect).not.toBeNull();
    expect(chairSelect?.value).toBe("");
  });

  it("duración sugerida al elegir prestación", async () => {
    const client = createApiClient({ fetchFn: async () => new Response("[]") });
    const services = [
      { id: "00000000-0000-0000-0000-0000000000d1", name: "Extracción", defaultDurationMin: 60, active: true },
      { id: "00000000-0000-0000-0000-0000000000d2", name: "Limpieza", defaultDurationMin: 30, active: true },
    ];

    render(
      <AppointmentFormDialog
        open={true}
        onClose={() => undefined}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        services={services}
      />,
    );

    const serviceSelect = screen.queryByLabelText<HTMLSelectElement>("Prestación");
    expect(serviceSelect).not.toBeNull();
    fireEvent.change(serviceSelect!, { target: { value: "00000000-0000-0000-0000-0000000000d1" } });

    const durationInput = screen.queryByLabelText<HTMLInputElement>("Duración (minutos)");
    expect(durationInput).not.toBeNull();
    expect(durationInput?.value).toBe("60");
  });

  it("edición manual de duración se conserva", async () => {
    const client = createApiClient({ fetchFn: async () => new Response("[]") });
    const services = [
      { id: "00000000-0000-0000-0000-0000000000d1", name: "Extracción", defaultDurationMin: 60, active: true },
    ];

    render(
      <AppointmentFormDialog
        open={true}
        onClose={() => undefined}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        services={services}
      />,
    );

    const serviceSelect = screen.queryByLabelText<HTMLSelectElement>("Prestación");
    expect(serviceSelect).not.toBeNull();
    fireEvent.change(serviceSelect!, { target: { value: "00000000-0000-0000-0000-0000000000d1" } });

    const durationInput = screen.queryByLabelText<HTMLInputElement>("Duración (minutos)");
    expect(durationInput).not.toBeNull();
    expect(durationInput?.value).toBe("60");

    fireEvent.change(durationInput!, { target: { value: "45" } });
    expect(durationInput?.value).toBe("45");
  });

  it("armado de startAt con offset exacto para la fecha elegida y timezone de la API", () => {
    const isoBsAs = buildStartAtIso("2026-11-16", "10:00", "America/Argentina/Buenos_Aires");
    expect(isoBsAs).toBe("2026-11-16T10:00:00-03:00");

    const isoNySummer = buildStartAtIso("2026-07-15", "10:00", "America/New_York");
    expect(isoNySummer).toBe("2026-07-15T10:00:00-04:00");

    const isoNyWinter = buildStartAtIso("2026-01-15", "10:00", "America/New_York");
    expect(isoNyWinter).toBe("2026-01-15T10:00:00-05:00");
  });

  it("envío exitoso 201 cierra el modal, llama onSuccess con los datos del turno y devuelve foco", async () => {
    let successCalled = false;
    let successInfo: { date: string; time: string } | null = null;
    let postBody: unknown = null;
    const client = createApiClient({
      fetchFn: async (url, init) => {
        const urlStr = url.toString();
        if (init?.method === "POST" && urlStr.includes("/appointments")) {
          postBody = JSON.parse(init.body as string);
          return new Response(
            JSON.stringify({
              id: "3fa85f64-5717-4562-b3fc-2c963f66afa6",
              status: "reservado",
            }),
            { status: 201, headers: { "Content-Type": "application/json" } },
          );
        }
        if (urlStr.includes("/patients")) {
          return new Response(
            JSON.stringify([
              { id: "00000000-0000-0000-0000-0000000000c1", fullName: "Ana Pérez", dni: "30111222" },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response("[]");
      },
    });

    const services = [
      { id: "00000000-0000-0000-0000-0000000000d1", name: "Extracción", defaultDurationMin: 60, active: true },
    ];

    function Harness() {
      const [isOpen, setIsOpen] = useState(true);
      const triggerRef = useRef<HTMLButtonElement>(null);
      return (
        <>
          <button ref={triggerRef} type="button">
            Nuevo turno
          </button>
          <AppointmentFormDialog
            open={isOpen}
            onClose={() => setIsOpen(false)}
            onSuccess={(info) => {
              successCalled = true;
              successInfo = info;
            }}
            client={client}
            timezone="America/Argentina/Buenos_Aires"
            effectiveDate="2026-11-16"
            initialProfessionalId="00000000-0000-0000-0000-000000000001"
            initialChairId="00000000-0000-0000-0000-0000000000b1"
            professionals={PROFESSIONALS}
            chairs={CHAIRS}
            services={services}
            returnFocusRef={triggerRef}
          />
        </>
      );
    }

    render(<Harness />);

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
    const serviceSelect = screen.queryByLabelText<HTMLSelectElement>("Prestación");
    expect(serviceSelect).not.toBeNull();
    fireEvent.change(serviceSelect!, { target: { value: "00000000-0000-0000-0000-0000000000d1" } });

    // Click submit
    const submitBtn = screen.queryByRole("button", { name: "Crear turno" });
    expect(submitBtn).not.toBeNull();
    fireEvent.click(submitBtn!);

    // Esperar a que se procese
    await screen.findByRole("button", { name: "Nuevo turno" });
    expect(successCalled).toBe(true);
    expect(successInfo).toEqual({ date: "2026-11-16", time: "10:00" });
    expect(postBody).toEqual({
      patientId: "00000000-0000-0000-0000-0000000000c1",
      professionalId: "00000000-0000-0000-0000-000000000001",
      chairId: "00000000-0000-0000-0000-0000000000b1",
      serviceId: "00000000-0000-0000-0000-0000000000d1",
      startAt: "2026-11-16T10:00:00-03:00",
      durationMin: 60,
    });
    const trigger = screen.getByRole("button", { name: "Nuevo turno" });
    expect(trigger).toHaveFocus();
  });

  it("respuesta 409 con violaciones múltiples muestra alert superior intacto con badges y referencias", async () => {
    const profOverlapMsg =
      "La Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno 00000000-0000-0000-0000-0000000000a1).";
    const chairOverlapMsg =
      "El Sillón 1 está ocupado de 10:00 a 10:30 (hora local) por un turno que se superpone (turno 00000000-0000-0000-0000-0000000000a1).";
    const client = createApiClient({
      fetchFn: async (input, init) => {
        const urlStr = String(input);
        if (urlStr.includes("/appointments") && init?.method === "POST") {
          return new Response(
            JSON.stringify({
              violations: [
                {
                  code: "PROFESSIONAL_OVERLAP",
                  message: profOverlapMsg,
                  conflictingAppointmentId: "00000000-0000-0000-0000-0000000000a1",
                  conflictingInterval: {
                    startAt: "2026-11-16T13:00:00Z",
                    endAt: "2026-11-16T13:30:00Z",
                  },
                },
                {
                  code: "CHAIR_OVERLAP",
                  message: chairOverlapMsg,
                  conflictingAppointmentId: "00000000-0000-0000-0000-0000000000a1",
                  conflictingInterval: {
                    startAt: "2026-11-16T13:00:00Z",
                    endAt: "2026-11-16T13:30:00Z",
                  },
                },
              ],
            }),
            { status: 409, headers: { "Content-Type": "application/json" } },
          );
        }
        if (urlStr.includes("/patients")) {
          return new Response(
            JSON.stringify([
              { id: "00000000-0000-0000-0000-0000000000c1", fullName: "Ana Pérez", dni: "30111222" },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response("[]");
      },
    });

    const services = [
      { id: "00000000-0000-0000-0000-0000000000d1", name: "Extracción", defaultDurationMin: 60, active: true },
    ];

    render(
      <AppointmentFormDialog
        open={true}
        onClose={() => undefined}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        initialProfessionalId="00000000-0000-0000-0000-000000000001"
        initialChairId="00000000-0000-0000-0000-0000000000b1"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        services={services}
      />,
    );

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
    const serviceSelect = screen.queryByLabelText<HTMLSelectElement>("Prestación");
    expect(serviceSelect).not.toBeNull();
    fireEvent.change(serviceSelect!, { target: { value: "00000000-0000-0000-0000-0000000000d1" } });

    // Click submit
    const submitBtn = screen.queryByRole("button", { name: "Crear turno" });
    expect(submitBtn).not.toBeNull();
    fireEvent.click(submitBtn!);

    // Esperar respuesta 409
    await screen.findByRole("button", { name: "Crear turno" });
    const alert = screen.queryByRole("alert");
    expect(alert).not.toBeNull();
    expect(screen.queryByText("PROFESSIONAL_OVERLAP")).not.toBeNull();
    expect(screen.queryByText(profOverlapMsg)).not.toBeNull();
    expect(screen.queryByText("CHAIR_OVERLAP")).not.toBeNull();
    expect(screen.queryByText(chairOverlapMsg)).not.toBeNull();

    // Campos sin aria-invalid
    expect(screen.queryByLabelText("Fecha")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Hora")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Profesional")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Sillón")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Prestación")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Duración (minutos)")).not.toHaveAttribute("aria-invalid");
  });

  it("rechazo 422 con IN_THE_PAST y UNKNOWN_REFERENCE muestra violaciones en alert superior sin mapeo a campos", async () => {
    const pastMsg = "La fecha y hora del turno debe ser futura.";
    const refMsg = "El paciente o profesional referenciado no existe.";
    const client = createApiClient({
      fetchFn: async (input, init) => {
        const urlStr = String(input);
        if (urlStr.includes("/appointments") && init?.method === "POST") {
          return new Response(
            JSON.stringify({
              violations: [
                {
                  code: "IN_THE_PAST",
                  message: pastMsg,
                },
                {
                  code: "UNKNOWN_REFERENCE",
                  message: refMsg,
                  referenceKind: "PATIENT",
                },
              ],
            }),
            { status: 422, headers: { "Content-Type": "application/json" } },
          );
        }
        if (urlStr.includes("/patients")) {
          return new Response(
            JSON.stringify([
              { id: "00000000-0000-0000-0000-0000000000c1", fullName: "Ana Pérez", dni: "30111222" },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response("[]");
      },
    });

    const services = [
      { id: "00000000-0000-0000-0000-0000000000d1", name: "Extracción", defaultDurationMin: 60, active: true },
    ];

    render(
      <AppointmentFormDialog
        open={true}
        onClose={() => undefined}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        initialProfessionalId="00000000-0000-0000-0000-000000000001"
        initialChairId="00000000-0000-0000-0000-0000000000b1"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        services={services}
      />,
    );

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
    const serviceSelect = screen.queryByLabelText<HTMLSelectElement>("Prestación");
    expect(serviceSelect).not.toBeNull();
    fireEvent.change(serviceSelect!, { target: { value: "00000000-0000-0000-0000-0000000000d1" } });

    // Click submit
    const submitBtn = screen.queryByRole("button", { name: "Crear turno" });
    expect(submitBtn).not.toBeNull();
    fireEvent.click(submitBtn!);

    await screen.findByRole("button", { name: "Crear turno" });
    const alert = screen.queryByRole("alert");
    expect(alert).not.toBeNull();
    expect(screen.queryByText("IN_THE_PAST")).not.toBeNull();
    expect(screen.queryByText(pastMsg)).not.toBeNull();
    expect(screen.queryByText("UNKNOWN_REFERENCE")).not.toBeNull();
    expect(screen.queryByText(refMsg)).not.toBeNull();

    // Sin aria-invalid en los inputs
    expect(screen.queryByLabelText("Fecha")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Hora")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Profesional")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Sillón")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Prestación")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Duración (minutos)")).not.toHaveAttribute("aria-invalid");
  });

  it("mapea errores 400 a los campos del formulario con aria-invalid y mensaje inline", async () => {
    const client = createApiClient({
      fetchFn: async (input, init) => {
        const urlStr = String(input);
        if (urlStr.includes("/appointments") && init?.method === "POST") {
          return new Response(
            JSON.stringify({
              detail: "Error de validación",
              errors: [
                {
                  field: "durationMin",
                  message: "La duración debe ser entre 15 y 240 minutos.",
                  type: "value_error",
                },
              ],
            }),
            { status: 400, headers: { "Content-Type": "application/json" } },
          );
        }
        if (urlStr.includes("/patients")) {
          return new Response(
            JSON.stringify([
              { id: "00000000-0000-0000-0000-0000000000c1", fullName: "Ana Pérez", dni: "30111222" },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response("[]");
      },
    });

    const services = [
      { id: "00000000-0000-0000-0000-0000000000d1", name: "Extracción", defaultDurationMin: 60, active: true },
    ];

    render(
      <AppointmentFormDialog
        open={true}
        onClose={() => undefined}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        initialProfessionalId="00000000-0000-0000-0000-000000000001"
        initialChairId="00000000-0000-0000-0000-0000000000b1"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        services={services}
      />,
    );

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
    const serviceSelect = screen.queryByLabelText<HTMLSelectElement>("Prestación");
    expect(serviceSelect).not.toBeNull();
    fireEvent.change(serviceSelect!, { target: { value: "00000000-0000-0000-0000-0000000000d1" } });

    // Click submit
    const submitBtn = screen.queryByRole("button", { name: "Crear turno" });
    expect(submitBtn).not.toBeNull();
    fireEvent.click(submitBtn!);

    await screen.findByRole("button", { name: "Crear turno" });
    const durationInput = screen.queryByLabelText("Duración (minutos)");
    expect(durationInput).toHaveAttribute("aria-invalid", "true");
    expect(
      screen.queryByText("La duración debe ser entre 15 y 240 minutos."),
    ).not.toBeNull();

    // Otros campos no tienen aria-invalid
    expect(screen.queryByLabelText("Fecha")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Hora")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Profesional")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Sillón")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Prestación")).not.toHaveAttribute("aria-invalid");
  });

  it("respuesta 403 FORBIDDEN_OPERATION muestra mensaje de permiso denegado en alert sin cerrar sesión", async () => {
    const forbiddenMsg = "No tiene permiso para dar turnos.";
    const client = createApiClient({
      fetchFn: async (input, init) => {
        const urlStr = String(input);
        if (urlStr.includes("/appointments") && init?.method === "POST") {
          return new Response(
            JSON.stringify({
              violations: [
                {
                  code: "FORBIDDEN_OPERATION",
                  message: forbiddenMsg,
                },
              ],
            }),
            { status: 403, headers: { "Content-Type": "application/json" } },
          );
        }
        if (urlStr.includes("/patients")) {
          return new Response(
            JSON.stringify([
              { id: "00000000-0000-0000-0000-0000000000c1", fullName: "Ana Pérez", dni: "30111222" },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response("[]");
      },
    });

    const services = [
      { id: "00000000-0000-0000-0000-0000000000d1", name: "Extracción", defaultDurationMin: 60, active: true },
    ];

    render(
      <AppointmentFormDialog
        open={true}
        onClose={() => undefined}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        initialProfessionalId="00000000-0000-0000-0000-000000000001"
        initialChairId="00000000-0000-0000-0000-0000000000b1"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        services={services}
      />,
    );

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
    const serviceSelect = screen.queryByLabelText<HTMLSelectElement>("Prestación");
    expect(serviceSelect).not.toBeNull();
    fireEvent.change(serviceSelect!, { target: { value: "00000000-0000-0000-0000-0000000000d1" } });

    // Click submit
    const submitBtn = screen.queryByRole("button", { name: "Crear turno" });
    expect(submitBtn).not.toBeNull();
    fireEvent.click(submitBtn!);

    await screen.findByRole("button", { name: "Crear turno" });
    const alert = screen.queryByRole("alert");
    expect(alert).not.toBeNull();
    expect(screen.queryByText("FORBIDDEN_OPERATION")).not.toBeNull();
    expect(screen.queryByText(forbiddenMsg)).not.toBeNull();

    // Sin aria-invalid en los inputs
    expect(screen.queryByLabelText("Fecha")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Hora")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Profesional")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Sillón")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Prestación")).not.toHaveAttribute("aria-invalid");
    expect(screen.queryByLabelText("Duración (minutos)")).not.toHaveAttribute("aria-invalid");
  });

  it("foco al resumen de alerta ante fallo", async () => {
    const client = createApiClient({
      fetchFn: async (input, init) => {
        const urlStr = String(input);
        if (urlStr.includes("/appointments") && init?.method === "POST") {
          return new Response(
            JSON.stringify({
              violations: [
                {
                  code: "PROFESSIONAL_OVERLAP",
                  message: "Solapamiento de profesional.",
                },
              ],
            }),
            { status: 409, headers: { "Content-Type": "application/json" } },
          );
        }
        if (urlStr.includes("/patients")) {
          return new Response(
            JSON.stringify([
              { id: "00000000-0000-0000-0000-0000000000c1", fullName: "Ana Pérez", dni: "30111222" },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response("[]");
      },
    });

    const services = [
      { id: "00000000-0000-0000-0000-0000000000d1", name: "Extracción", defaultDurationMin: 60, active: true },
    ];

    render(
      <AppointmentFormDialog
        open={true}
        onClose={() => undefined}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        initialProfessionalId="00000000-0000-0000-0000-000000000001"
        initialChairId="00000000-0000-0000-0000-0000000000b1"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        services={services}
      />,
    );

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

    const timeInput = screen.queryByLabelText<HTMLInputElement>("Hora");
    expect(timeInput).not.toBeNull();
    fireEvent.change(timeInput!, { target: { value: "10:00" } });

    const serviceSelect = screen.queryByLabelText<HTMLSelectElement>("Prestación");
    expect(serviceSelect).not.toBeNull();
    fireEvent.change(serviceSelect!, { target: { value: "00000000-0000-0000-0000-0000000000d1" } });

    const submitBtn = screen.queryByRole("button", { name: "Crear turno" });
    expect(submitBtn).not.toBeNull();
    fireEvent.click(submitBtn!);

    await screen.findByRole("button", { name: "Crear turno" });
    const alert = screen.getByRole("alert");
    await waitFor(() => {
      expect(alert).toHaveFocus();
    });
  });

  it("pulsar Cancelar cierra el diálogo sin enviar solicitudes y devuelve el foco al elemento de apertura", async () => {
    let open = true;
    let postCalled = false;
    const trigger = document.createElement("button");
    trigger.textContent = "Nuevo turno";
    document.body.appendChild(trigger);
    trigger.focus();
    const returnFocusRef = { current: trigger };

    const onClose = () => {
      open = false;
    };

    const client = createApiClient({
      fetchFn: async (_input, init) => {
        if (init?.method === "POST") {
          postCalled = true;
        }
        return new Response("[]");
      },
    });

    const { rerender } = render(
      <AppointmentFormDialog
        open={open}
        onClose={onClose}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        returnFocusRef={returnFocusRef}
      />,
    );

    const cancelBtn = screen.queryByRole("button", { name: "Cancelar" });
    expect(cancelBtn).not.toBeNull();
    fireEvent.click(cancelBtn!);

    rerender(
      <AppointmentFormDialog
        open={open}
        onClose={onClose}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        returnFocusRef={returnFocusRef}
      />,
    );

    expect(open).toBe(false);
    expect(postCalled).toBe(false);
    expect(document.activeElement).toBe(trigger);
    document.body.removeChild(trigger);
  });

  it("Escape cierra sin enviar solicitudes y devuelve el foco", async () => {
    let open = true;
    let postCalled = false;
    const trigger = document.createElement("button");
    trigger.textContent = "Nuevo turno";
    document.body.appendChild(trigger);
    trigger.focus();
    const returnFocusRef = { current: trigger };

    const onClose = () => {
      open = false;
    };

    const client = createApiClient({
      fetchFn: async (_input, init) => {
        if (init?.method === "POST") {
          postCalled = true;
        }
        return new Response("[]");
      },
    });

    const { rerender } = render(
      <AppointmentFormDialog
        open={open}
        onClose={onClose}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        returnFocusRef={returnFocusRef}
      />,
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).not.toBeNull();
    fireEvent.keyDown(dialog, { key: "Escape" });

    rerender(
      <AppointmentFormDialog
        open={open}
        onClose={onClose}
        client={client}
        timezone="America/Argentina/Buenos_Aires"
        effectiveDate="2026-11-16"
        professionals={PROFESSIONALS}
        chairs={CHAIRS}
        returnFocusRef={returnFocusRef}
      />,
    );

    expect(open).toBe(false);
    expect(postCalled).toBe(false);
    expect(document.activeElement).toBe(trigger);
    document.body.removeChild(trigger);
  });
});
