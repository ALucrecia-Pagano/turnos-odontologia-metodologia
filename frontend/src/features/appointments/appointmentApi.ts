import type { ApiClient } from "../../shared/api/client";
import type { ApiResult } from "../../shared/api/types";
import type { AppointmentStatus } from "../../shared/styles/appointmentStatusTokens";
import type { AgendaAppointment } from "../agenda/agendaApi";

export type AllowedStatusChange = "confirmado" | "atendido" | "ausente";

export interface StatusChangeInput {
  toStatus: AllowedStatusChange;
}

export interface RescheduleInput {
  startAt: string;
  professionalId?: string | null;
  chairId?: string | null;
  durationMin?: number | null;
}

export interface RescheduleDetailResponse {
  previousStartAt: string;
  previousEndAt: string;
  newStartAt: string;
  newEndAt: string;
  previousProfessionalId: string;
  newProfessionalId: string;
  previousChairId: string;
  newChairId: string;
}

export interface HistoryEntryResponse {
  from: string | null;
  to: string;
  changedBy: string;
  changedByName: string | null;
  changedAt: string;
  reschedule: RescheduleDetailResponse | null;
}

export interface AppointmentResponse {
  id: string;
  patientId: string;
  professionalId: string;
  chairId: string;
  serviceId: string;
  startAt: string;
  endAt: string;
  status: AppointmentStatus;
}

export async function changeAppointmentStatus(
  client: ApiClient,
  id: string,
  toStatus: AllowedStatusChange,
): Promise<ApiResult<AppointmentResponse>> {
  const result = await client.request(`/appointments/${id}/status`, {
    method: "POST",
    body: { toStatus },
  });
  return result as ApiResult<AppointmentResponse>;
}

export async function cancelAppointment(
  client: ApiClient,
  id: string,
): Promise<ApiResult<AppointmentResponse>> {
  const result = await client.request(`/appointments/${id}/cancel`, {
    method: "POST",
  });
  return result as ApiResult<AppointmentResponse>;
}

export async function rescheduleAppointment(
  client: ApiClient,
  id: string,
  input: RescheduleInput,
): Promise<ApiResult<AppointmentResponse>> {
  const payload: Record<string, string | number | null> = {
    startAt: input.startAt,
  };
  if (input.professionalId !== undefined && input.professionalId !== null) {
    payload.professionalId = input.professionalId;
  }
  if (input.chairId !== undefined && input.chairId !== null) {
    payload.chairId = input.chairId;
  }
  if (input.durationMin !== undefined && input.durationMin !== null) {
    payload.durationMin = input.durationMin;
  }

  const result = await client.request(`/appointments/${id}/reschedule`, {
    method: "POST",
    body: payload,
  });
  return result as ApiResult<AppointmentResponse>;
}

export async function getAppointmentHistory(
  client: ApiClient,
  id: string,
): Promise<ApiResult<HistoryEntryResponse[]>> {
  const result = await client.request(`/appointments/${id}/history`, {
    method: "GET",
  });
  return result as ApiResult<HistoryEntryResponse[]>;
}

export async function getAppointmentDetail(
  client: ApiClient,
  id: string,
): Promise<ApiResult<AgendaAppointment>> {
  const result = await client.request(`/appointments/${id}`, {
    method: "GET",
  });
  return result as ApiResult<AgendaAppointment>;
}
