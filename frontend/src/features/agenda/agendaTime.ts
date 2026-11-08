export interface LocalDateParts {
  readonly year: number;
  readonly month: number;
  readonly day: number;
}

export interface MinuteRange {
  readonly startMinute: number;
  readonly endMinute: number;
}

const LOCAL_DATE_REGEX = /^(\d{4})-(\d{2})-(\d{2})$/;
const HHMM_REGEX = /^(\d{2}):(\d{2})$/;
const MS_PER_DAY = 86_400_000;

function toDate(instant: Date | string): Date {
  return typeof instant === "string" ? new Date(instant) : instant;
}

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export function parseLocalDate(value: string | null | undefined): LocalDateParts | null {
  if (typeof value !== "string") {
    return null;
  }
  const match = LOCAL_DATE_REGEX.exec(value);
  if (match === null) {
    return null;
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (year < 2000 || year > 2100 || month < 1 || month > 12 || day < 1 || day > 31) {
    return null;
  }
  const utc = new Date(Date.UTC(year, month - 1, day, 12));
  if (
    utc.getUTCFullYear() !== year ||
    utc.getUTCMonth() !== month - 1 ||
    utc.getUTCDate() !== day
  ) {
    return null;
  }
  return { year, month, day };
}

export function isValidLocalDate(value: string | null | undefined): value is string {
  return parseLocalDate(value) !== null;
}

export function formatLocalDate(instant: Date | string, timeZone: string): string {
  const date = toDate(instant);
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);

  const year = parts.find((part) => part.type === "year")?.value ?? "1970";
  const month = parts.find((part) => part.type === "month")?.value ?? "01";
  const day = parts.find((part) => part.type === "day")?.value ?? "01";
  return `${year}-${month}-${day}`;
}

export function formatLocalTime(instant: Date | string, timeZone: string): string {
  const date = toDate(instant);
  const parts = new Intl.DateTimeFormat("es-AR", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);

  const rawHour = parts.find((part) => part.type === "hour")?.value ?? "00";
  const hour = rawHour === "24" ? "00" : rawHour.padStart(2, "0");
  const minute = (parts.find((part) => part.type === "minute")?.value ?? "00").padStart(2, "0");
  return `${hour}:${minute}`;
}

export function formatTimeRange(startAt: Date | string, endAt: Date | string, timeZone: string): string {
  const start = formatLocalTime(startAt, timeZone);
  const end = formatLocalTime(endAt, timeZone);
  return `${start}–${end}`;
}

export function todayInTimeZone(now: Date, timeZone: string): string {
  return formatLocalDate(now, timeZone);
}

export function formatDayLabel(dateStr: string): string {
  const parsed = parseLocalDate(dateStr);
  if (parsed === null) {
    return dateStr;
  }
  const utcNoon = new Date(Date.UTC(parsed.year, parsed.month - 1, parsed.day, 12));
  const weekday = new Intl.DateTimeFormat("es-AR", {
    timeZone: "UTC",
    weekday: "long",
  })
    .format(utcNoon)
    .toLowerCase();
  const month = new Intl.DateTimeFormat("es-AR", {
    timeZone: "UTC",
    month: "long",
  })
    .format(utcNoon)
    .toLowerCase();
  return `${weekday} ${parsed.day} de ${month} de ${parsed.year}`;
}

export function addDays(dateStr: string, delta: number): string {
  const parsed = parseLocalDate(dateStr);
  if (parsed === null) {
    return dateStr;
  }
  const shifted = new Date(Date.UTC(parsed.year, parsed.month - 1, parsed.day + delta, 12));
  const year = shifted.getUTCFullYear();
  const month = pad2(shifted.getUTCMonth() + 1);
  const day = pad2(shifted.getUTCDate());
  return `${year}-${month}-${day}`;
}

export function weekdayOf(dateStr: string): number {
  const parsed = parseLocalDate(dateStr);
  if (parsed === null) {
    return 1;
  }
  const day = new Date(Date.UTC(parsed.year, parsed.month - 1, parsed.day, 12)).getUTCDay();
  return day === 0 ? 7 : day;
}

export function parseHHMM(hhmm: string): number {
  if (hhmm === "24:00") {
    return 1440;
  }
  const match = HHMM_REGEX.exec(hhmm);
  if (match === null) {
    return 0;
  }
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  return hours * 60 + minutes;
}

export function formatMinutesToHHMM(minutes: number): string {
  const clamped = Math.max(0, Math.min(1440, Math.round(minutes)));
  if (clamped === 1440) {
    return "24:00";
  }
  const hours = Math.floor(clamped / 60);
  const mins = clamped % 60;
  return `${pad2(hours)}:${pad2(mins)}`;
}

export function minutesOfDay(instant: Date | string, dateStr: string, timeZone: string): number {
  const localDate = formatLocalDate(instant, timeZone);
  const localTime = formatLocalTime(instant, timeZone);
  const targetParts = parseLocalDate(dateStr);
  const instantParts = parseLocalDate(localDate);
  const timeMinutes = parseHHMM(localTime);
  if (targetParts === null || instantParts === null) {
    return timeMinutes;
  }
  const targetUtc = Date.UTC(targetParts.year, targetParts.month - 1, targetParts.day);
  const instantUtc = Date.UTC(instantParts.year, instantParts.month - 1, instantParts.day);
  const dayDiff = Math.round((instantUtc - targetUtc) / MS_PER_DAY);
  return dayDiff * 1440 + timeMinutes;
}

export function appointmentRange(
  startAt: Date | string,
  endAt: Date | string,
  dateStr: string,
  timeZone: string,
): MinuteRange | null {
  const rawStart = minutesOfDay(startAt, dateStr, timeZone);
  const rawEnd = minutesOfDay(endAt, dateStr, timeZone);
  if (rawEnd <= 0 || rawStart >= 1440 || rawEnd <= rawStart) {
    return null;
  }
  const startMinute = Math.max(0, Math.min(1440, rawStart));
  const endMinute = Math.max(0, Math.min(1440, rawEnd));
  return { startMinute, endMinute };
}
