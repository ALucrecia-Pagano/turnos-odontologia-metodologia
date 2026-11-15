import type { ApiClient } from "../../shared/api/client";
import type { ApiResult, Json } from "../../shared/api/types";
import {
  APPOINTMENT_STATUSES,
  type AppointmentStatus,
} from "../../shared/styles/appointmentStatusTokens";

export const UNEXPECTED_RESPONSE_MESSAGE = "Respuesta inesperada del servidor.";

export interface WorkingHoursSlot {
  readonly weekday: number;
  readonly start: string;
  readonly end: string;
}

export interface AffectedAppointment {
  readonly id: string;
  readonly patientId: string;
  readonly patientName: string;
  readonly chairId: string;
  readonly startAt: string;
  readonly endAt: string;
  readonly status: AppointmentStatus;
}

export interface ReplaceWorkingHoursResponse {
  readonly workingHours: readonly WorkingHoursSlot[];
  readonly appointmentsOutsideHours: readonly AffectedAppointment[];
}

export interface ProfessionalBlock {
  readonly id: string;
  readonly professionalId: string;
  readonly startAt: string;
  readonly endAt: string;
  readonly reason: string | null;
}

export interface CreateBlockPayload {
  readonly startAt: string;
  readonly endAt: string;
  readonly reason?: string | null;
}

export interface CreateBlockResponse {
  readonly block: ProfessionalBlock;
  readonly affectedAppointments: readonly AffectedAppointment[];
}

type JsonObject = { [key: string]: Json };

function isObject(value: Json | undefined): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: Json | undefined): value is string {
  return typeof value === "string";
}

function isAppointmentStatus(value: Json | undefined): value is AppointmentStatus {
  return typeof value === "string" && (APPOINTMENT_STATUSES as readonly string[]).includes(value);
}

function parseWorkingHoursSlot(value: Json | undefined): WorkingHoursSlot | null {
  if (!isObject(value)) return null;
  const { weekday, start, end } = value;
  if (typeof weekday !== "number" || !isString(start) || !isString(end)) {
    return null;
  }
  return { weekday, start, end };
}

function parseWorkingHoursList(value: Json | undefined): readonly WorkingHoursSlot[] | null {
  if (!Array.isArray(value)) return null;
  const items: WorkingHoursSlot[] = [];
  for (const item of value) {
    const parsed = parseWorkingHoursSlot(item);
    if (parsed === null) return null;
    items.push(parsed);
  }
  return items;
}

function parseAffectedAppointment(value: Json | undefined): AffectedAppointment | null {
  if (!isObject(value)) return null;
  const { id, patientId, patientName, chairId, startAt, endAt, status } = value;
  if (
    !isString(id) ||
    !isString(patientId) ||
    !isString(patientName) ||
    !isString(chairId) ||
    !isString(startAt) ||
    !isString(endAt) ||
    !isAppointmentStatus(status)
  ) {
    return null;
  }
  return { id, patientId, patientName, chairId, startAt, endAt, status };
}

function parseAffectedAppointmentsList(
  value: Json | undefined,
): readonly AffectedAppointment[] | null {
  if (!Array.isArray(value)) return null;
  const items: AffectedAppointment[] = [];
  for (const item of value) {
    const parsed = parseAffectedAppointment(item);
    if (parsed === null) return null;
    items.push(parsed);
  }
  return items;
}

function parseProfessionalBlock(value: Json | undefined): ProfessionalBlock | null {
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

function parseBlocksList(value: Json | undefined): readonly ProfessionalBlock[] | null {
  if (!Array.isArray(value)) return null;
  const items: ProfessionalBlock[] = [];
  for (const item of value) {
    const parsed = parseProfessionalBlock(item);
    if (parsed === null) return null;
    items.push(parsed);
  }
  return items;
}

function parseReplaceWorkingHoursResponse(
  value: Json | undefined,
): ReplaceWorkingHoursResponse | null {
  if (!isObject(value)) return null;
  const workingHours = parseWorkingHoursList(value.workingHours);
  const appointmentsOutsideHours = parseAffectedAppointmentsList(value.appointmentsOutsideHours);
  if (workingHours === null || appointmentsOutsideHours === null) {
    return null;
  }
  return { workingHours, appointmentsOutsideHours };
}

function parseCreateBlockResponse(value: Json | undefined): CreateBlockResponse | null {
  if (!isObject(value)) return null;
  const block = parseProfessionalBlock(value.block);
  const affectedAppointments = parseAffectedAppointmentsList(value.affectedAppointments);
  if (block === null || affectedAppointments === null) {
    return null;
  }
  return { block, affectedAppointments };
}

export async function getWorkingHours(
  client: ApiClient,
  professionalId: string,
  options?: { readonly signal?: AbortSignal },
): Promise<ApiResult<readonly WorkingHoursSlot[]>> {
  const result = await client.request(
    `/professionals/${encodeURIComponent(professionalId)}/working-hours`,
    {
      method: "GET",
      signal: options?.signal,
    },
  );
  if (!result.ok) {
    return result;
  }
  const parsed = parseWorkingHoursList(result.data);
  if (parsed === null) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}

export async function replaceWorkingHours(
  client: ApiClient,
  professionalId: string,
  slots: readonly WorkingHoursSlot[],
): Promise<ApiResult<ReplaceWorkingHoursResponse>> {
  const body: Json = slots.map((slot) => ({
    weekday: slot.weekday,
    start: slot.start,
    end: slot.end,
  }));
  const result = await client.request(
    `/professionals/${encodeURIComponent(professionalId)}/working-hours`,
    {
      method: "PUT",
      body,
    },
  );
  if (!result.ok) {
    return result;
  }
  const parsed = parseReplaceWorkingHoursResponse(result.data);
  if (parsed === null) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}

export async function listBlocks(
  client: ApiClient,
  professionalId: string,
  options?: { readonly signal?: AbortSignal },
): Promise<ApiResult<readonly ProfessionalBlock[]>> {
  const result = await client.request(
    `/professionals/${encodeURIComponent(professionalId)}/blocks`,
    {
      method: "GET",
      signal: options?.signal,
    },
  );
  if (!result.ok) {
    return result;
  }
  const parsed = parseBlocksList(result.data);
  if (parsed === null) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}

export async function createBlock(
  client: ApiClient,
  professionalId: string,
  payload: CreateBlockPayload,
): Promise<ApiResult<CreateBlockResponse>> {
  const body: { [key: string]: Json } = {
    startAt: payload.startAt,
    endAt: payload.endAt,
  };
  if (payload.reason !== undefined && payload.reason !== null && payload.reason.trim() !== "") {
    body.reason = payload.reason;
  }
  const result = await client.request(
    `/professionals/${encodeURIComponent(professionalId)}/blocks`,
    {
      method: "POST",
      body,
    },
  );
  if (!result.ok) {
    return result;
  }
  const parsed = parseCreateBlockResponse(result.data);
  if (parsed === null) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}

export async function deleteBlock(
  client: ApiClient,
  blockId: string,
): Promise<ApiResult<ProfessionalBlock>> {
  const result = await client.request(`/blocks/${encodeURIComponent(blockId)}`, {
    method: "DELETE",
  });
  if (!result.ok) {
    return result;
  }
  const parsed = parseProfessionalBlock(result.data);
  if (parsed === null) {
    return {
      ok: false,
      status: result.status,
      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSAGE },
    };
  }
  return { ok: true, status: result.status, data: parsed };
}
