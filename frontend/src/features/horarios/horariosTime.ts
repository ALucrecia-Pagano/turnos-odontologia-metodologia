import { formatLocalDate, formatLocalTime } from "../agenda/agendaTime";
import { buildStartAtIso } from "../appointments/AppointmentFormDialog";

export interface WeekdayOption {
  readonly weekday: number;
  readonly label: string;
}

export const WEEKDAYS: readonly WeekdayOption[] = [
  { weekday: 1, label: "Lunes" },
  { weekday: 2, label: "Martes" },
  { weekday: 3, label: "Miércoles" },
  { weekday: 4, label: "Jueves" },
  { weekday: 5, label: "Viernes" },
  { weekday: 6, label: "Sábado" },
  { weekday: 7, label: "Domingo" },
];

export const START_HHMM_REGEX = /^(?:[01]\d|2[0-3]):[0-5]\d$/;
export const END_HHMM_REGEX = /^(?:(?:[01]\d|2[0-3]):[0-5]\d|24:00)$/;

export function buildLocalInstantIso(
  dateStr: string,
  timeStr: string,
  timeZone: string,
): string {
  return buildStartAtIso(dateStr, timeStr, timeZone);
}

export function formatLocalDateInZone(instant: string, timeZone: string): string {
  return formatLocalDate(instant, timeZone);
}

export function formatLocalTimeInZone(instant: string, timeZone: string): string {
  return formatLocalTime(instant, timeZone);
}

export function formatDisplayDateInZone(instant: string, timeZone: string): string {
  return new Intl.DateTimeFormat("es-AR", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone,
  }).format(new Date(instant));
}

export function formatLocalRangeInZone(
  startAt: string,
  endAt: string,
  timeZone: string,
): { readonly dateLabel: string; readonly timeLabel: string } {
  const startDate = formatDisplayDateInZone(startAt, timeZone);
  const endDate = formatDisplayDateInZone(endAt, timeZone);
  const startTime = formatLocalTime(startAt, timeZone);
  const endTime = formatLocalTime(endAt, timeZone);
  const dateLabel = startDate === endDate ? startDate : `${startDate} a ${endDate}`;
  const timeLabel = `${startTime} a ${endTime}`;
  return { dateLabel, timeLabel };
}
