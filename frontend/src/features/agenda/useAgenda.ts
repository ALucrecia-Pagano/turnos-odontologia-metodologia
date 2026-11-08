import { useCallback, useEffect, useRef, useState } from "react";
import type { ApiClient } from "../../shared/api/client";
import { getApiErrorMessages } from "../../shared/api/errors";
import { DEFAULT_AGENDA_TIMEZONE } from "./agendaConfig";
import {
  fetchAgenda,
  fetchChairs,
  fetchProfessionals,
  UNEXPECTED_RESPONSE_MESSAGE,
  type AgendaResponse,
  type Chair,
  type Professional,
} from "./agendaApi";

export type AgendaLoadPhase = "loading" | "refreshing" | "success" | "error";

export const CATALOG_FALLBACK_WARNING =
  "No se pudo cargar el catálogo completo; las columnas se armaron con los datos de la agenda.";

export interface UseAgendaParams {
  readonly client: ApiClient;
  readonly date: string;
  readonly professionalId?: string | null;
  readonly chairId?: string | null;
  readonly onForbidden?: () => void;
}

export interface UseAgendaState {
  readonly phase: AgendaLoadPhase;
  readonly agenda: AgendaResponse | null;
  readonly professionals: readonly Professional[];
  readonly chairs: readonly Chair[];
  readonly timezone: string;
  readonly errorMessages: readonly string[];
  readonly catalogWarning: string | null;
  readonly refresh: () => void;
}

interface InternalState {
  readonly settledKey: string | null;
  readonly settledPhase: "success" | "error";
  readonly agenda: AgendaResponse | null;
  readonly professionals: readonly Professional[];
  readonly chairs: readonly Chair[];
  readonly timezone: string;
  readonly errorMessages: readonly string[];
  readonly catalogWarning: string | null;
}

export function useAgenda({
  client,
  date,
  professionalId = null,
  chairId = null,
  onForbidden,
}: UseAgendaParams): UseAgendaState {
  const [reloadTick, setReloadTick] = useState(0);
  const queryKey = `${date}|${professionalId ?? ""}|${chairId ?? ""}|${reloadTick}`;

  const [state, setState] = useState<InternalState>({
    settledKey: null,
    settledPhase: "success",
    agenda: null,
    professionals: [],
    chairs: [],
    timezone: DEFAULT_AGENDA_TIMEZONE,
    errorMessages: [],
    catalogWarning: null,
  });

  const activeRequestIdRef = useRef(0);
  const onForbiddenRef = useRef(onForbidden);

  useEffect(() => {
    onForbiddenRef.current = onForbidden;
  }, [onForbidden]);

  const refresh = useCallback(() => {
    setReloadTick((prev) => prev + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const requestId = activeRequestIdRef.current + 1;
    activeRequestIdRef.current = requestId;

    void Promise.allSettled([
      fetchAgenda(client, {
        from: date,
        to: date,
        professionalId,
        chairId,
        signal: controller.signal,
      }),
      fetchProfessionals(client, { signal: controller.signal }),
      fetchChairs(client, { signal: controller.signal }),
    ]).then(([agendaSettled, professionalsSettled, chairsSettled]) => {
      if (controller.signal.aborted || activeRequestIdRef.current !== requestId) {
        return;
      }

      if (agendaSettled.status === "rejected") {
        setState((prev) => ({
          ...prev,
          settledKey: queryKey,
          settledPhase: "error",
          errorMessages: ["No se pudo conectar con el servidor. Verificá tu conexión."],
        }));
        return;
      }

      const agendaResult = agendaSettled.value;
      if (!agendaResult.ok) {
        if (agendaResult.status === 401) {
          return;
        }
        if (agendaResult.status === 403) {
          onForbiddenRef.current?.();
        }
        const messages =
          agendaResult.error.kind === "unknown" &&
          agendaResult.error.rawText === UNEXPECTED_RESPONSE_MESSAGE
            ? [UNEXPECTED_RESPONSE_MESSAGE]
            : getApiErrorMessages(agendaResult.error);
        setState((prev) => ({
          ...prev,
          settledKey: queryKey,
          settledPhase: "error",
          errorMessages: messages,
        }));
        return;
      }

      const professionalsOk =
        professionalsSettled.status === "fulfilled" && professionalsSettled.value.ok;
      const chairsOk = chairsSettled.status === "fulfilled" && chairsSettled.value.ok;

      const forbiddenCatalog =
        (professionalsSettled.status === "fulfilled" &&
          !professionalsSettled.value.ok &&
          professionalsSettled.value.status === 403) ||
        (chairsSettled.status === "fulfilled" &&
          !chairsSettled.value.ok &&
          chairsSettled.value.status === 403);
      if (forbiddenCatalog) {
        onForbiddenRef.current?.();
      }

      setState((prev) => ({
        settledKey: queryKey,
        settledPhase: "success",
        agenda: agendaResult.data,
        professionals:
          professionalsSettled.status === "fulfilled" && professionalsSettled.value.ok
            ? professionalsSettled.value.data
            : prev.professionals,
        chairs:
          chairsSettled.status === "fulfilled" && chairsSettled.value.ok
            ? chairsSettled.value.data
            : prev.chairs,
        timezone: agendaResult.data.timezone,
        errorMessages: [],
        catalogWarning:
          professionalsOk && chairsOk ? null : CATALOG_FALLBACK_WARNING,
      }));
    });

    return () => {
      controller.abort();
    };
  }, [client, date, professionalId, chairId, reloadTick, queryKey]);

  const isPending = state.settledKey !== queryKey;
  const phase: AgendaLoadPhase = isPending
    ? state.agenda === null
      ? "loading"
      : "refreshing"
    : state.settledPhase;

  return {
    phase,
    agenda: state.agenda,
    professionals: state.professionals,
    chairs: state.chairs,
    timezone: state.timezone,
    errorMessages: isPending ? [] : state.errorMessages,
    catalogWarning: state.catalogWarning,
    refresh,
  };
}
