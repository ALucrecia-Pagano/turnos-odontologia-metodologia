import type { ApiClient } from "../../shared/api/client";
import type { ApiResult, Json } from "../../shared/api/types";
import {
  APPOINTMENT_STATUSES,
  type AppointmentStatus,
} from "../../shared/styles/appointmentStatusTokens";

export const UNEXPECTED_RESPONSE_MESSAGE = "Respuesta inesperada del servidor.";

export interface AgendaAppointment {
  readonly id: string;
  readonly patientId: string;
  readonly patientName: string;
  readonly professionalId: string;
  readonly professionalName: string;
  readonly chairId: string;
  readonly chairName: string;
  readonly serviceId: string;
  readonly serviceName: string;
  readonly startAt: string;
  readonly endAt: string;
  readonly status: AppointmentStatus;
}

export interface AgendaWorkingHours {
  readonly professionalId: string;
  readonly weekday: number;
  readonly start: string;
  readonly end: string;
}

export interface AgendaBlock {
  readonly id: string;
  readonly professionalId: string;
  readonly startAt: string;
  readonly endAt: string;
  readonly reason: string | null;
}

export interface AgendaResponse {
  readonly from: string;
  readonly to: string;
  readonly timezone: string;
  readonly appointments: readonly AgendaAppointment[];
  readonly workingHours: readonly AgendaWorkingHours[];
  readonly blocks: readonly AgendaBlock[];
}

export interface Professional {
  readonly id: string;
  readonly fullName: string;
  readonly licenseNumber: string | null;
  readonly active: boolean;
}

export interface Chair {
  readonly id: string;
  readonly name: string;
  readonly active: boolean;
}

export interface FetchAgendaParams {
  readonly from: string;
  readonly to: string;
  readonly professionalId?: string | null;
  readonly chairId?: string | null;
  readonly signal?: AbortSignal;
}

type JsonObject = { [key: string]: Json };

function isObject(value: Json | undefined): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: Json | undefined): value is string {
  return typeof value === "string";
}

function isBoolean(value: Json | undefined): value is boolean {
  return typeof value === "boolean";
}

function isAppointmentStatus(value: Json | undefined): value is AppointmentStatus {
  return typeof value === "string" && (APPOINTMENT_STATUSES as readonly string[]).includes(value);
}

function parseAppointment(value: Json | undefined): AgendaAppointment | null {
  if (!isObject(value)) return null;
  const {
    id,
    patientId,
    patientName,
    professionalId,
    professionalName,
    chairId,
    chairName,
    serviceId,
    serviceName,
    startAt,
    endAt,
    status,
  } = value;
  if (
    !isString(id) ||
    !isString(patientId) ||
    !isString(patientName) ||
    !isString(professionalId) ||
    !isString(professionalName) ||
    !isString(chairId) ||
    !isString(chairName) ||
    !isString(serviceId) ||
    !isString(serviceName) ||
    !isString(startAt) ||
    !isString(endAt) ||
    !isAppointmentStatus(status)
  ) {
    return null;
  }
  return {
    id,
    patientId,
    patientName,
    professionalId,
    professionalName,
    chairId,
    chairName,
    serviceId,
    serviceName,
    startAt,
    endAt,
    status,
  };
}

function parseWorkingHour(value: Json | undefined): AgendaWorkingHours | null {
  if (!isObject(value)) return null;
  const { professionalId, weekday, start, end } = value;
  if (
    !isString(professionalId) ||
    typeof weekday !== "number" ||
    !isString(start) ||
    !isString(end)
  ) {
    return null;
  }
  return { professionalId, weekday, start, end };
}

function parseBlock(value: Json | undefined): AgendaBlock | null {
  if (!isObject(value)) return null;
  const { id, professionalId, startAt, endAt, reason } = value;
  if (
    !isString(id) ||
    !isString(professionalId) ||
    !isString(startAt) ||
    !isString(endAt) ||
    (reason !== null && reason !== undefined && !isString(reason))
  ) {
    return null;
  }
  return { id, professionalId, startAt, endAt, reason: isString(reason) ? reason : null };
}

export function parseAgendaResponse(value: Json | undefined): AgendaResponse | null {
  if (!isObject(value)) return null;
  const { from, to, timezone, appointments, workingHours, blocks } = value;
  if (
    !isString(from) ||
    !isString(to) ||
    !isString(timezone) ||
    !Array.isArray(appointments) ||
    !Array.isArray(workingHours) ||
    !Array.isArray(blocks)
  ) {
    return null;
  }

  const parsedAppointments: AgendaAppointment[] = [];
  for (const item of appointments) {
    const parsed = parseAppointment(item);
    if (parsed === null) return null;
    parsedAppointments.push(parsed);
  }

  const parsedWorkingHours: AgendaWorkingHours[] = [];
  for (const item of workingHours) {
    const parsed = parseWorkingHour(item);
    if (parsed === null) return null;
    parsedWorkingHours.push(parsed);
  }

  const parsedBlocks: AgendaBlock[] = [];
  for (const item of blocks) {
    const parsed = parseBlock(item);
    if (parsed === null) return null;
    parsedBlocks.push(parsed);
  }

  return {
    from,
    to,
    timezone,
    appointments: parsedAppointments,
    workingHours: parsedWorkingHours,
    blocks: parsedBlocks,
  };
}

export function parseProfessionals(value: Json | undefined): readonly Professional[] | null {
  if (!Array.isArray(value)) return null;
  const items: Professional[] = [];
  for (const item of value) {
    if (!isObject(item)) return null;
    const { id, fullName, licenseNumber, active } = item;
    if (
      !isString(id) ||
      !isString(fullName) ||
      (licenseNumber !== null && licenseNumber !== undefined && !isString(licenseNumber)) ||
      !isBoolean(active)
    ) {
      return null;
    }
    items.push({
      id,
      fullName,
      licenseNumber: isString(licenseNumber) ? licenseNumber : null,
      active,
    });
  }
  return items;
}

export function parseChairs(value: Json | undefined): readonly Chair[] | null {
  if (!Array.isArray(value)) return null;
  const items: Chair[] = [];
  for (const item of value) {
    if (!isObject(item)) return null;
    const { id, name, active } = item;
    if (!isString(id) || !isString(name) || !isBoolean(active)) {
      return null;
    }
    items.push({ id, name, active });
  }
  return items;
}

export async function fetchAgenda(
  client: ApiClient,
  params: FetchAgendaParams,
): Promise<ApiResult<AgendaResponse>> {
  const search = new URLSearchParams();
  search.set("from", params.from);
  search.set("to", params.to);
  if (typeof params.professionalId === "string" && params.professionalId !== "") {
    search.set("professionalId", params.professionalId);
  }
  if (typeof params.chairId === "string" && params.chairId !== "") {
    search.set("chairId", params.chairId);
  }

  const result = await client.request(`/agenda?${search.toString()}`, {
    method: "GET",
    signal: params.signal,
  });
  if (!result.ok) {
    return result;
  }

  const parsed = parseAgendaResponse(result.data);
  if (parsed === null) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}

export async function fetchProfessionals(
  client: ApiClient,
  options?: { readonly signal?: AbortSignal },
): Promise<ApiResult<readonly Professional[]>> {
  const result = await client.request("/professionals", {
    method: "GET",
    signal: options?.signal,
  });
  if (!result.ok) {
    return result;
  }
  const parsed = parseProfessionals(result.data);
  if (parsed === null) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}

export async function fetchChairs(
  client: ApiClient,
  options?: { readonly signal?: AbortSignal },
): Promise<ApiResult<readonly Chair[]>> {
  const result = await client.request("/chairs", {
    method: "GET",
    signal: options?.signal,
  });
  if (!result.ok) {
    return result;
  }
  const parsed = parseChairs(result.data);
  if (parsed === null) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}
