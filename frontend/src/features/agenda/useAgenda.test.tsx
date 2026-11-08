import { useState } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import { useAgenda } from "./useAgenda";

const AGENDA_MONDAY = {
  from: "2026-11-16",
  to: "2026-11-16",
  timezone: "America/Argentina/Buenos_Aires",
  appointments: [
    {
      id: "00000000-0000-0000-0000-000000000aa2",
      patientId: "00000000-0000-0000-0000-0000000000c2",
      patientName: "Bruno Acosta",
      professionalId: "00000000-0000-0000-0000-000000000002",
      professionalName: "Dr. Martín Sosa",
      chairId: "00000000-0000-0000-0000-0000000000b2",
      chairName: "Sillón 2",
      serviceId: "00000000-0000-0000-0000-0000000000d4",
      serviceName: "Control",
      startAt: "2026-11-16T12:00:00Z",
      endAt: "2026-11-16T12:30:00Z",
      status: "reservado",
    },
    {
      id: "00000000-0000-0000-0000-000000000aa1",
      patientId: "00000000-0000-0000-0000-0000000000c1",
      patientName: "Ana Pérez",
      professionalId: "00000000-0000-0000-0000-000000000001",
      professionalName: "Dra. Laura Quiroga",
      chairId: "00000000-0000-0000-0000-0000000000b1",
      chairName: "Sillón 1",
      serviceId: "00000000-0000-0000-0000-0000000000d4",
      serviceName: "Control",
      startAt: "2026-11-16T13:00:00Z",
      endAt: "2026-11-16T13:30:00Z",
      status: "reservado",
    },
  ],
  workingHours: [
    {
      professionalId: "00000000-0000-0000-0000-000000000001",
      weekday: 1,
      start: "09:00",
      end: "13:00",
    },
  ],
  blocks: [],
};

const AGENDA_SUNDAY = {
  from: "2026-11-15",
  to: "2026-11-15",
  timezone: "America/Argentina/Buenos_Aires",
  appointments: [],
  workingHours: [],
  blocks: [],
};

const PROFESSIONALS = [
  {
    id: "00000000-0000-0000-0000-000000000001",
    fullName: "Dra. Laura Quiroga",
    licenseNumber: "MP-1001",
    active: true,
  },
  {
    id: "00000000-0000-0000-0000-000000000002",
    fullName: "Dr. Martín Sosa",
    licenseNumber: "MP-1002",
    active: true,
  },
];

const CHAIRS = [
  { id: "00000000-0000-0000-0000-0000000000b1", name: "Sillón 1", active: true },
  { id: "00000000-0000-0000-0000-0000000000b2", name: "Sillón 2", active: true },
];

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function Harness({
  fetchFn,
  initialDate = "2026-11-16",
}: {
  readonly fetchFn: FetchFn;
  readonly initialDate?: string;
}) {
  const [client] = useState(() => createApiClient({ baseUrl: "/api", fetchFn }));
  const [date, setDate] = useState(initialDate);
  const state = useAgenda({ client, date });

  return (
    <div>
      <div data-testid="phase">{state.phase}</div>
      <div data-testid="date">{state.agenda?.from ?? "none"}</div>
      <div data-testid="count">{state.agenda?.appointments.length ?? -1}</div>
      <div data-testid="profs">{state.professionals.length}</div>
      <div data-testid="chairs">{state.chairs.length}</div>
      <div data-testid="tz">{state.timezone}</div>
      <div data-testid="warning">{state.catalogWarning ?? "none"}</div>
      <div data-testid="errors">{state.errorMessages.join("|") || "none"}</div>
      <button type="button" onClick={() => state.refresh()}>
        Refrescar
      </button>
      <button type="button" onClick={() => setDate("2026-11-15")}>
        Ir a domingo
      </button>
      <button type="button" onClick={() => setDate("2026-11-17")}>
        Ir a martes con fallo
      </button>
    </div>
  );
}

describe("useAgenda", () => {
  it("dispara las tres requests en paralelo, pasa por loading/refreshing/success y tolera fallo del catálogo con Promise.allSettled", async () => {
    const inFlightUrls: string[] = [];
    let releaseInitial!: () => void;
    const initialGate = new Promise<void>((resolve) => {
      releaseInitial = resolve;
    });
    let releaseRefresh!: () => void;
    const refreshGate = new Promise<void>((resolve) => {
      releaseRefresh = resolve;
    });
    let callBatch = 0;

    const fetchFn: FetchFn = async (input) => {
      const url = String(input);
      inFlightUrls.push(url);
      if (inFlightUrls.length <= 3) {
        await initialGate;
      } else {
        await refreshGate;
      }
      if (url.startsWith("/api/agenda")) {
        callBatch += 1;
        return jsonResponse(AGENDA_MONDAY);
      }
      if (url === "/api/professionals") {
        if (callBatch >= 1 && inFlightUrls.length > 3) {
          return jsonResponse({ detail: "Error interno" }, 500);
        }
        return jsonResponse(PROFESSIONALS);
      }
      if (url === "/api/chairs") {
        return jsonResponse(CHAIRS);
      }
      return jsonResponse({ detail: "No encontrado" }, 404);
    };

    render(<Harness fetchFn={fetchFn} />);

    expect(screen.queryByTestId("phase")).toHaveTextContent("loading");
    expect(inFlightUrls).toEqual([
      "/api/agenda?from=2026-11-16&to=2026-11-16",
      "/api/professionals",
      "/api/chairs",
    ]);

    releaseInitial();

    await waitFor(() => {
      expect(screen.queryByTestId("phase")).toHaveTextContent("success");
    });
    expect(screen.queryByTestId("date")).toHaveTextContent("2026-11-16");
    expect(screen.queryByTestId("count")).toHaveTextContent("2");
    expect(screen.queryByTestId("profs")).toHaveTextContent("2");
    expect(screen.queryByTestId("chairs")).toHaveTextContent("2");
    expect(screen.queryByTestId("tz")).toHaveTextContent("America/Argentina/Buenos_Aires");
    expect(screen.queryByTestId("warning")).toHaveTextContent("none");

    const refreshBtn = screen.queryByRole("button", { name: "Refrescar" });
    expect(refreshBtn).not.toBeNull();
    fireEvent.click(refreshBtn!);

    expect(screen.queryByTestId("phase")).toHaveTextContent("refreshing");
    expect(screen.queryByTestId("count")).toHaveTextContent("2");

    releaseRefresh();

    await waitFor(() => {
      expect(screen.queryByTestId("warning")).toHaveTextContent(
        "No se pudo cargar el catálogo completo; las columnas se armaron con los datos de la agenda.",
      );
    });
    expect(screen.queryByTestId("phase")).toHaveTextContent("success");
    expect(screen.queryByTestId("count")).toHaveTextContent("2");
  });

  it("aborta e ignora respuestas viejas al cambiar de fecha y expone error cuando falla la agenda", async () => {
    let resolveMondayAgenda!: (res: Response) => void;
    const signalsByUrl = new Map<string, AbortSignal | null | undefined>();

    const fetchFn: FetchFn = (input, init) => {
      const url = String(input);
      signalsByUrl.set(url, init?.signal);
      if (url.includes("from=2026-11-16")) {
        return new Promise<Response>((resolve) => {
          resolveMondayAgenda = resolve;
        });
      }
      if (url.includes("from=2026-11-15")) {
        return Promise.resolve(jsonResponse(AGENDA_SUNDAY));
      }
      if (url.includes("from=2026-11-17")) {
        return Promise.resolve(jsonResponse({ detail: "Fallo del servidor" }, 500));
      }
      if (url === "/api/professionals") {
        return Promise.resolve(jsonResponse(PROFESSIONALS));
      }
      return Promise.resolve(jsonResponse(CHAIRS));
    };

    render(<Harness fetchFn={fetchFn} />);

    expect(screen.queryByTestId("phase")).toHaveTextContent("loading");

    const sundayBtn = screen.queryByRole("button", { name: "Ir a domingo" });
    expect(sundayBtn).not.toBeNull();
    fireEvent.click(sundayBtn!);

    expect(signalsByUrl.get("/api/agenda?from=2026-11-16&to=2026-11-16")?.aborted).toBe(true);

    await waitFor(() => {
      expect(screen.queryByTestId("phase")).toHaveTextContent("success");
    });
    expect(screen.queryByTestId("date")).toHaveTextContent("2026-11-15");
    expect(screen.queryByTestId("count")).toHaveTextContent("0");

    resolveMondayAgenda(jsonResponse(AGENDA_MONDAY));
    await Promise.resolve();

    expect(screen.queryByTestId("date")).toHaveTextContent("2026-11-15");
    expect(screen.queryByTestId("count")).toHaveTextContent("0");

    const tuesdayBtn = screen.queryByRole("button", { name: "Ir a martes con fallo" });
    expect(tuesdayBtn).not.toBeNull();
    fireEvent.click(tuesdayBtn!);

    await waitFor(() => {
      expect(screen.queryByTestId("phase")).toHaveTextContent("error");
    });
    expect(screen.queryByTestId("errors")).toHaveTextContent(
      "Ocurrió un error inesperado (HTTP 500).",
    );
  });
});
