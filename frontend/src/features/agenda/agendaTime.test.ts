import { describe, expect, it } from "vitest";
import {
  addDays,
  appointmentRange,
  formatDayLabel,
  formatLocalDate,
  formatLocalTime,
  formatTimeRange,
  isValidLocalDate,
  parseHHMM,
  todayInTimeZone,
  weekdayOf,
} from "./agendaTime";

const BUENOS_AIRES_TZ = "America/Argentina/Buenos_Aires";

describe("agendaTime", () => {
  it("13:00Z se convierte a 10:00 y 2026-11-16 en Buenos Aires y formatea la etiqueta del día", () => {
    expect(formatLocalTime("2026-11-16T13:00:00Z", BUENOS_AIRES_TZ)).toBe("10:00");
    expect(formatLocalDate("2026-11-16T13:00:00Z", BUENOS_AIRES_TZ)).toBe("2026-11-16");
    expect(formatTimeRange("2026-11-16T13:00:00Z", "2026-11-16T13:30:00Z", BUENOS_AIRES_TZ)).toBe("10:00–10:30");
    expect(formatDayLabel("2026-11-16")).toBe("lunes 16 de noviembre de 2026");
  });

  it("respeta el borde de medianoche entre 02:30Z y 03:30Z en Buenos Aires", () => {
    expect(formatLocalDate("2026-11-16T02:30:00Z", BUENOS_AIRES_TZ)).toBe("2026-11-15");
    expect(formatLocalTime("2026-11-16T02:30:00Z", BUENOS_AIRES_TZ)).toBe("23:30");
    expect(todayInTimeZone(new Date(Date.UTC(2026, 10, 16, 2, 30, 0)), BUENOS_AIRES_TZ)).toBe("2026-11-15");

    expect(formatLocalDate("2026-11-16T03:30:00Z", BUENOS_AIRES_TZ)).toBe("2026-11-16");
    expect(formatLocalTime("2026-11-16T03:30:00Z", BUENOS_AIRES_TZ)).toBe("00:30");
    expect(todayInTimeZone(new Date(Date.UTC(2026, 10, 16, 3, 30, 0)), BUENOS_AIRES_TZ)).toBe("2026-11-16");
  });

  it("addDays suma y resta días calendario cruzando mes y año y weekdayOf devuelve ISO con domingo 7", () => {
    expect(addDays("2026-11-30", 1)).toBe("2026-12-01");
    expect(addDays("2026-12-31", 1)).toBe("2027-01-01");
    expect(addDays("2026-01-01", -1)).toBe("2025-12-31");
    expect(weekdayOf("2026-11-16")).toBe(1);
    expect(weekdayOf("2026-11-15")).toBe(7);
  });

  it("parseHHMM convierte 24:00 a 1440 y appointmentRange maneja el cruce de medianoche", () => {
    expect(parseHHMM("24:00")).toBe(1440);
    expect(parseHHMM("09:30")).toBe(570);
    expect(
      appointmentRange("2026-11-17T02:30:00Z", "2026-11-17T03:00:00Z", "2026-11-16", BUENOS_AIRES_TZ),
    ).toEqual({
      startMinute: 1410,
      endMinute: 1440,
    });
    expect(
      appointmentRange("2026-11-16T02:00:00Z", "2026-11-16T04:00:00Z", "2026-11-16", BUENOS_AIRES_TZ),
    ).toEqual({
      startMinute: 0,
      endMinute: 60,
    });
  });

  it("una zona con DST como America/New_York no altera la hora de Buenos Aires y el resultado no depende del proceso", () => {
    expect(formatLocalTime("2026-07-15T13:00:00Z", "America/New_York")).toBe("09:00");
    expect(formatLocalTime("2026-11-16T13:00:00Z", "America/New_York")).toBe("08:00");
    expect(formatLocalTime("2026-11-16T13:00:00Z", BUENOS_AIRES_TZ)).toBe("10:00");
    expect(formatLocalDate("2026-11-16T13:00:00Z", BUENOS_AIRES_TZ)).toBe("2026-11-16");
    expect(isValidLocalDate("2026-11-16")).toBe(true);
    expect(isValidLocalDate("2026-02-30")).toBe(false);
  });
});
