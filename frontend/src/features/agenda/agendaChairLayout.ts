import type {
  AgendaAppointment,
  AgendaBlock,
  AgendaWorkingHours,
} from "./agendaApi";
import {
  AGENDA_DEFAULT_END_MINUTE,
  AGENDA_DEFAULT_START_MINUTE,
  AGENDA_MIN_APPOINTMENT_MINUTES,
  AGENDA_MIN_AXIS_MINUTES,
  type AgendaAxis,
  type AxisAppointmentInput,
  type AxisWorkingHourInput,
  type ProfessionalColumn,
} from "./agendaLayout";
import {
  appointmentRange,
  formatMinutesToHHMM,
  parseHHMM,
  type MinuteRange,
} from "./agendaTime";

export interface ChairFreeSlot {
  readonly kind: "free" | "outside";
  readonly startMinute: number;
  readonly endMinute: number;
  readonly durationMinutes: number;
  readonly label: string;
  readonly ariaLabel: string;
}

export interface ChairColumn
  extends ProfessionalColumn<AgendaAppointment, AgendaWorkingHours, AgendaBlock> {
  readonly freeSlots: readonly ChairFreeSlot[];
}

export interface CatalogChairInput {
  readonly id: string;
  readonly name: string;
  readonly active: boolean;
}

export interface UnionAttentionInput {
  readonly workingHours: readonly AxisWorkingHourInput[];
  readonly weekday: number;
  readonly professionalId?: string | null;
}

export function unionAttentionIntervals({
  workingHours,
  weekday,
  professionalId,
}: UnionAttentionInput): MinuteRange[] {
  const matching = workingHours.filter((wh) => {
    if (wh.weekday !== weekday) {
      return false;
    }
    if (professionalId !== null && professionalId !== undefined && professionalId !== "") {
      return wh.professionalId === professionalId;
    }
    return true;
  });

  const parsedRanges: MinuteRange[] = [];
  for (const wh of matching) {
    const start = Math.max(0, Math.min(1440, parseHHMM(wh.start)));
    const end = Math.max(0, Math.min(1440, parseHHMM(wh.end)));
    if (end > start) {
      parsedRanges.push({ startMinute: start, endMinute: end });
    }
  }

  parsedRanges.sort((a, b) => {
    if (a.startMinute !== b.startMinute) {
      return a.startMinute - b.startMinute;
    }
    return a.endMinute - b.endMinute;
  });

  const merged: MinuteRange[] = [];
  for (const range of parsedRanges) {
    const last = merged[merged.length - 1];
    if (last === undefined) {
      merged.push({ ...range });
    } else if (range.startMinute <= last.endMinute) {
      merged[merged.length - 1] = {
        startMinute: last.startMinute,
        endMinute: Math.max(last.endMinute, range.endMinute),
      };
    } else {
      merged.push({ ...range });
    }
  }

  return merged;
}

export interface ComputeChairFreeSlotsInput {
  readonly attention: readonly MinuteRange[];
  readonly appointments: readonly AgendaAppointment[];
  readonly date: string;
  readonly timezone: string;
  readonly chairName?: string;
  readonly minMinutes?: number;
}

export function computeChairFreeSlots({
  attention,
  appointments,
  date,
  timezone,
  chairName,
  minMinutes = AGENDA_MIN_APPOINTMENT_MINUTES,
}: ComputeChairFreeSlotsInput): ChairFreeSlot[] {
  const result: ChairFreeSlot[] = [];

  // 1. Gaps internos entre tramos de atención ("Fuera de horario")
  for (let i = 0; i < attention.length - 1; i++) {
    const current = attention[i];
    const next = attention[i + 1];
    if (current !== undefined && next !== undefined && next.startMinute > current.endMinute) {
      const startMinute = current.endMinute;
      const endMinute = next.startMinute;
      const durationMinutes = endMinute - startMinute;
      const startLabel = formatMinutesToHHMM(startMinute);
      const endLabel = formatMinutesToHHMM(endMinute);
      result.push({
        kind: "outside",
        startMinute,
        endMinute,
        durationMinutes,
        label: `Fuera de horario ${startLabel}–${endLabel}`,
        ariaLabel: `Fuera de horario de ${startLabel} a ${endLabel}`,
      });
    }
  }

  // 2. Turnos que ocupan agenda (reservado, confirmado, atendido). Cancelado y ausente liberan.
  const occupyingRanges: MinuteRange[] = [];
  for (const appt of appointments) {
    if (
      appt.status !== "reservado" &&
      appt.status !== "confirmado" &&
      appt.status !== "atendido"
    ) {
      continue;
    }
    const range = appointmentRange(appt.startAt, appt.endAt, date, timezone);
    if (range !== null && range.endMinute > range.startMinute) {
      occupyingRanges.push({
        startMinute: Math.max(0, Math.min(1440, range.startMinute)),
        endMinute: Math.max(0, Math.min(1440, range.endMinute)),
      });
    }
  }

  occupyingRanges.sort((a, b) => {
    if (a.startMinute !== b.startMinute) {
      return a.startMinute - b.startMinute;
    }
    return a.endMinute - b.endMinute;
  });

  const mergedOccupied: MinuteRange[] = [];
  for (const range of occupyingRanges) {
    const last = mergedOccupied[mergedOccupied.length - 1];
    if (last === undefined) {
      mergedOccupied.push({ ...range });
    } else if (range.startMinute <= last.endMinute) {
      mergedOccupied[mergedOccupied.length - 1] = {
        startMinute: last.startMinute,
        endMinute: Math.max(last.endMinute, range.endMinute),
      };
    } else {
      mergedOccupied.push({ ...range });
    }
  }

  // 3. Restar ocupación de cada tramo de atención para emitir bloques "Libre"
  for (const att of attention) {
    let cursor = att.startMinute;

    for (const occ of mergedOccupied) {
      if (occ.endMinute <= cursor || occ.startMinute >= att.endMinute) {
        continue;
      }
      if (occ.startMinute > cursor) {
        const freeStart = cursor;
        const freeEnd = Math.min(att.endMinute, occ.startMinute);
        const duration = freeEnd - freeStart;
        if (duration >= minMinutes) {
          const startLabel = formatMinutesToHHMM(freeStart);
          const endLabel = formatMinutesToHHMM(freeEnd);
          result.push({
            kind: "free",
            startMinute: freeStart,
            endMinute: freeEnd,
            durationMinutes: duration,
            label: `Libre ${startLabel}–${endLabel}`,
            ariaLabel:
              chairName !== undefined && chairName !== ""
                ? `${chairName} libre de ${startLabel} a ${endLabel}`
                : `Libre de ${startLabel} a ${endLabel}`,
          });
        }
      }
      cursor = Math.max(cursor, occ.endMinute);
    }

    if (cursor < att.endMinute) {
      const freeStart = cursor;
      const freeEnd = att.endMinute;
      const duration = freeEnd - freeStart;
      if (duration >= minMinutes) {
        const startLabel = formatMinutesToHHMM(freeStart);
        const endLabel = formatMinutesToHHMM(freeEnd);
        result.push({
          kind: "free",
          startMinute: freeStart,
          endMinute: freeEnd,
          durationMinutes: duration,
          label: `Libre ${startLabel}–${endLabel}`,
          ariaLabel:
            chairName !== undefined && chairName !== ""
              ? `${chairName} libre de ${startLabel} a ${endLabel}`
              : `Libre de ${startLabel} a ${endLabel}`,
        });
      }
    }
  }

  result.sort((a, b) => {
    if (a.startMinute !== b.startMinute) {
      return a.startMinute - b.startMinute;
    }
    return a.endMinute - b.endMinute;
  });

  return result;
}

export interface ComputeChairAxisInput {
  readonly workingHours: readonly AxisWorkingHourInput[];
  readonly weekday: number;
  readonly professionalId?: string | null;
  readonly appointments?: readonly AxisAppointmentInput[];
  readonly date?: string;
  readonly timezone?: string;
}

export function computeChairAxis({
  workingHours,
  weekday,
  professionalId,
  appointments = [],
  date,
  timezone,
}: ComputeChairAxisInput): AgendaAxis {
  const attention = unionAttentionIntervals({ workingHours, weekday, professionalId });

  const apptRanges: MinuteRange[] = [];
  if (date !== undefined && timezone !== undefined) {
    for (const appt of appointments) {
      const range = appointmentRange(appt.startAt, appt.endAt, date, timezone);
      if (range !== null && range.endMinute > range.startMinute) {
        apptRanges.push(range);
      }
    }
  }

  if (attention.length === 0 && apptRanges.length === 0) {
    const fallbackStart = AGENDA_DEFAULT_START_MINUTE; // 480 (08:00)
    const fallbackEnd = AGENDA_DEFAULT_END_MINUTE;     // 1200 (20:00)
    const hours: string[] = [];
    for (let m = fallbackStart; m <= fallbackEnd; m += 60) {
      hours.push(formatMinutesToHHMM(m));
    }
    return {
      startMinute: fallbackStart,
      endMinute: fallbackEnd,
      hours,
    };
  }

  const allStarts = [
    ...attention.map((r) => r.startMinute),
    ...apptRanges.map((r) => r.startMinute),
  ];
  const allEnds = [
    ...attention.map((r) => r.endMinute),
    ...apptRanges.map((r) => r.endMinute),
  ];

  const minStart = Math.min(...allStarts);
  const maxEnd = Math.max(...allEnds);

  const startMinute = Math.floor(minStart / 60) * 60;
  let endMinute = Math.ceil(maxEnd / 60) * 60;

  if (endMinute - startMinute < AGENDA_MIN_AXIS_MINUTES) {
    endMinute = Math.min(1440, startMinute + AGENDA_MIN_AXIS_MINUTES);
  }

  const hours: string[] = [];
  for (let m = startMinute; m <= endMinute; m += 60) {
    hours.push(formatMinutesToHHMM(m));
  }

  return {
    startMinute,
    endMinute,
    hours,
  };
}

export interface GroupByChairInput {
  readonly chairs: readonly CatalogChairInput[];
  readonly appointments: readonly AgendaAppointment[];
  readonly workingHours: readonly AgendaWorkingHours[];
  readonly date: string;
  readonly timezone: string;
  readonly weekday: number;
  readonly filterChairId?: string | null;
  readonly filterProfessionalId?: string | null;
}

export function groupByChair({
  chairs,
  appointments,
  workingHours,
  date,
  timezone,
  weekday,
  filterChairId = null,
  filterProfessionalId = null,
}: GroupByChairInput): ChairColumn[] {
  const byId = new Map<string, CatalogChairInput>();

  for (const chair of chairs) {
    byId.set(chair.id, chair);
  }

  for (const appt of appointments) {
    const range = appointmentRange(appt.startAt, appt.endAt, date, timezone);
    if (range !== null && appt.chairId) {
      if (!byId.has(appt.chairId)) {
        byId.set(appt.chairId, {
          id: appt.chairId,
          name: appt.chairName !== "" ? appt.chairName : `Sillón ${appt.chairId.slice(0, 4)}`,
          active: true,
        });
      }
    }
  }

  let chairList = Array.from(byId.values());
  if (filterChairId !== null && filterChairId !== "") {
    chairList = chairList.filter((c) => c.id === filterChairId);
  }

  chairList.sort((a, b) => {
    const byName = a.name.localeCompare(b.name, "es", { sensitivity: "base" });
    if (byName !== 0) {
      return byName;
    }
    return a.id.localeCompare(b.id);
  });

  const attention = unionAttentionIntervals({
    workingHours,
    weekday,
    professionalId: filterProfessionalId,
  });

  return chairList.map((chair) => {
    const chairAppts = appointments.filter((appt) => {
      if (appt.chairId !== chair.id) {
        return false;
      }
      if (
        filterProfessionalId !== null &&
        filterProfessionalId !== "" &&
        appt.professionalId !== filterProfessionalId
      ) {
        return false;
      }
      return appointmentRange(appt.startAt, appt.endAt, date, timezone) !== null;
    });

    const freeSlots = computeChairFreeSlots({
      attention,
      appointments: chairAppts,
      date,
      timezone,
      chairName: chair.name,
    });

    const syntheticWorkingHours: AgendaWorkingHours[] = attention.map((att) => ({
      professionalId: chair.id,
      weekday,
      start: formatMinutesToHHMM(att.startMinute),
      end: formatMinutesToHHMM(att.endMinute),
    }));

    return {
      id: chair.id,
      fullName: chair.name,
      active: chair.active,
      displayLabel: chair.active ? chair.name : `${chair.name} (inactivo)`,
      date,
      workingHours: syntheticWorkingHours,
      blocks: [],
      appointments: chairAppts,
      freeSlots,
    };
  });
}
