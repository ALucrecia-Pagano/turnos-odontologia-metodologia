export const DEFAULT_AGENDA_TIMEZONE = "America/Argentina/Buenos_Aires";

export function resolveAgendaTimezone(responseTimezone?: string | null): string {
  if (typeof responseTimezone === "string" && responseTimezone.trim() !== "") {
    return responseTimezone.trim();
  }
  return DEFAULT_AGENDA_TIMEZONE;
}
