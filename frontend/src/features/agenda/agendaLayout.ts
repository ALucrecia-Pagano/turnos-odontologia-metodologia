import {
  addDays,
  appointmentRange,
  formatMinutesToHHMM,
  formatWeekdayHeader,
  parseHHMM,
  weekdayOf,
  type MinuteRange,
} from "./agendaTime";

export { appointmentRange };

export const AGENDA_DEFAULT_START_MINUTE = 480;
export const AGENDA_DEFAULT_END_MINUTE = 1200;
export const AGENDA_MIN_AXIS_MINUTES = 240;
export const AGENDA_MIN_APPOINTMENT_MINUTES = 15;

export interface AxisWorkingHourInput {
  readonly professionalId: string;
  readonly weekday: number;
  readonly start: string;
  readonly end: string;
}

export interface AxisBlockInput {
  readonly id: string;
  readonly professionalId: string;
  readonly startAt: string;
  readonly endAt: string;
  readonly reason?: string | null;
}

export interface AxisAppointmentInput {
  readonly id: string;
  readonly professionalId: string;
  readonly professionalName?: string;
  readonly startAt: string;
  readonly endAt: string;
}

export interface CatalogProfessionalInput {
  readonly id: string;
  readonly fullName: string;
  readonly active: boolean;
}

export interface ProfessionalColumn<
  TAppt extends AxisAppointmentInput = AxisAppointmentInput,
  TWh extends AxisWorkingHourInput = AxisWorkingHourInput,
  TBlock extends AxisBlockInput = AxisBlockInput,
> {
  readonly id: string;
  readonly fullName: string;
  readonly active: boolean;
  readonly displayLabel: string;
  readonly date?: string;
  readonly isToday?: boolean;
  readonly workingHours: readonly TWh[];
  readonly blocks: readonly TBlock[];
  readonly appointments: readonly TAppt[];
}

export interface DayColumn<
  TAppt extends AxisAppointmentInput = AxisAppointmentInput,
  TWh extends AxisWorkingHourInput = AxisWorkingHourInput,
  TBlock extends AxisBlockInput = AxisBlockInput,
> {
  readonly id: string;
  readonly date: string;
  readonly weekday: number;
  readonly fullName: string;
  readonly active: boolean;
  readonly displayLabel: string;
  readonly isToday?: boolean;
  readonly workingHours: readonly TWh[];
  readonly blocks: readonly TBlock[];
  readonly appointments: readonly TAppt[];
}

export interface GroupByDayInput<
  TAppt extends AxisAppointmentInput = AxisAppointmentInput,
  TWh extends AxisWorkingHourInput = AxisWorkingHourInput,
  TBlock extends AxisBlockInput = AxisBlockInput,
> {
  readonly professionalId: string;
  readonly mondayDate: string;
  readonly timezone: string;
  readonly todayDate?: string;
  readonly workingHours: readonly TWh[];
  readonly blocks: readonly TBlock[];
  readonly appointments: readonly TAppt[];
}

export function groupByDayForProfessional<
  TAppt extends AxisAppointmentInput = AxisAppointmentInput,
  TWh extends AxisWorkingHourInput = AxisWorkingHourInput,
  TBlock extends AxisBlockInput = AxisBlockInput,
>({
  professionalId,
  mondayDate,
  timezone,
  todayDate,
  workingHours,
  blocks,
  appointments,
}: GroupByDayInput<TAppt, TWh, TBlock>): DayColumn<TAppt, TWh, TBlock>[] {
  const columns: DayColumn<TAppt, TWh, TBlock>[] = [];

  for (let i = 0; i < 7; i++) {
    const date = addDays(mondayDate, i);
    const weekday = i + 1;
    const displayLabel = formatWeekdayHeader(date);
    const isToday = todayDate !== undefined && date === todayDate;

    const dayWorkingHours = workingHours.filter(
      (wh) => wh.professionalId === professionalId && wh.weekday === weekday,
    );

    const dayBlocks = blocks.filter(
      (b) =>
        b.professionalId === professionalId &&
        appointmentRange(b.startAt, b.endAt, date, timezone) !== null,
    );

    const dayAppointments = appointments.filter(
      (appt) =>
        appt.professionalId === professionalId &&
        appointmentRange(appt.startAt, appt.endAt, date, timezone) !== null,
    );

    columns.push({
      id: date,
      date,
      weekday,
      fullName: displayLabel,
      active: true,
      displayLabel,
      isToday,
      workingHours: dayWorkingHours,
      blocks: dayBlocks,
      appointments: dayAppointments,
    });
  }

  return columns;
}

export interface GroupByProfessionalInput<
  TAppt extends AxisAppointmentInput = AxisAppointmentInput,
  TWh extends AxisWorkingHourInput = AxisWorkingHourInput,
  TBlock extends AxisBlockInput = AxisBlockInput,
> {
  readonly professionals: readonly CatalogProfessionalInput[];
  readonly workingHours: readonly TWh[];
  readonly blocks: readonly TBlock[];
  readonly appointments: readonly TAppt[];
  readonly weekday: number;
  readonly filterProfessionalId?: string | null;
}

export interface ComputeAxisInput {
  readonly date: string;
  readonly timezone: string;
  readonly workingHours: readonly AxisWorkingHourInput[];
  readonly blocks: readonly AxisBlockInput[];
  readonly appointments: readonly AxisAppointmentInput[];
}

export interface AgendaAxis {
  readonly startMinute: number;
  readonly endMinute: number;
  readonly hours: readonly string[];
}

export function clampRange(startMinute: number, endMinute: number): MinuteRange {
  const clampedStart = Math.max(0, Math.min(1440, startMinute));
  const clampedEnd = Math.max(clampedStart, Math.min(1440, endMinute));
  return { startMinute: clampedStart, endMinute: clampedEnd };
}

function buildHoursList(startMinute: number, endMinute: number): string[] {
  const hours: string[] = [];
  for (let minute = startMinute; minute <= endMinute; minute += 60) {
    hours.push(formatMinutesToHHMM(minute));
  }
  return hours;
}

export function computeAxis({
  date,
  timezone,
  workingHours,
  blocks,
  appointments,
}: ComputeAxisInput): AgendaAxis {
  const weekday = weekdayOf(date);
  const ranges: MinuteRange[] = [];

  for (const wh of workingHours) {
    if (wh.weekday === weekday) {
      const clamped = clampRange(parseHHMM(wh.start), parseHHMM(wh.end));
      if (clamped.endMinute > clamped.startMinute) {
        ranges.push(clamped);
      }
    }
  }

  for (const block of blocks) {
    const range = appointmentRange(block.startAt, block.endAt, date, timezone);
    if (range !== null) {
      ranges.push(clampRange(range.startMinute, range.endMinute));
    }
  }

  for (const appt of appointments) {
    const range = appointmentRange(appt.startAt, appt.endAt, date, timezone);
    if (range !== null) {
      ranges.push(clampRange(range.startMinute, range.endMinute));
    }
  }

  if (ranges.length === 0) {
    return {
      startMinute: AGENDA_DEFAULT_START_MINUTE,
      endMinute: AGENDA_DEFAULT_END_MINUTE,
      hours: buildHoursList(AGENDA_DEFAULT_START_MINUTE, AGENDA_DEFAULT_END_MINUTE),
    };
  }

  const minStart = Math.min(...ranges.map((r) => r.startMinute));
  const maxEnd = Math.max(...ranges.map((r) => r.endMinute));

  let startMinute = Math.max(0, Math.floor(minStart / 60) * 60 - 60);
  let endMinute = Math.min(1440, Math.ceil(maxEnd / 60) * 60 + 60);

  if (endMinute - startMinute < AGENDA_MIN_AXIS_MINUTES) {
    endMinute = Math.min(1440, startMinute + AGENDA_MIN_AXIS_MINUTES);
    if (endMinute - startMinute < AGENDA_MIN_AXIS_MINUTES) {
      startMinute = Math.max(0, endMinute - AGENDA_MIN_AXIS_MINUTES);
    }
  }

  return {
    startMinute,
    endMinute,
    hours: buildHoursList(startMinute, endMinute),
  };
}

export function computeWeekAxis({
  mondayDate,
  timezone,
  workingHours,
  blocks,
  appointments,
}: {
  readonly mondayDate: string;
  readonly timezone: string;
  readonly workingHours: readonly AxisWorkingHourInput[];
  readonly blocks: readonly AxisBlockInput[];
  readonly appointments: readonly AxisAppointmentInput[];
}): AgendaAxis {
  let minStart = 1440;
  let maxEnd = 0;
  for (let i = 0; i < 7; i++) {
    const day = addDays(mondayDate, i);
    const dayAxis = computeAxis({
      date: day,
      timezone,
      workingHours,
      blocks,
      appointments,
    });
    minStart = Math.min(minStart, dayAxis.startMinute);
    maxEnd = Math.max(maxEnd, dayAxis.endMinute);
  }
  return {
    startMinute: minStart,
    endMinute: maxEnd,
    hours: buildHoursList(minStart, maxEnd),
  };
}

export function compareProfessionals(
  a: { readonly id: string; readonly fullName: string },
  b: { readonly id: string; readonly fullName: string },
): number {
  const byName = a.fullName.localeCompare(b.fullName, "es", { sensitivity: "base" });
  if (byName !== 0) {
    return byName;
  }
  return a.id.localeCompare(b.id);
}

export function formatProfessionalLabel(professional: {
  readonly fullName: string;
  readonly active: boolean;
}): string {
  return professional.active ? professional.fullName : `${professional.fullName} (inactivo)`;
}

export function groupByProfessional<
  TAppt extends AxisAppointmentInput,
  TWh extends AxisWorkingHourInput,
  TBlock extends AxisBlockInput,
>({
  professionals,
  workingHours,
  blocks,
  appointments,
  weekday,
  filterProfessionalId,
}: GroupByProfessionalInput<TAppt, TWh, TBlock>): ProfessionalColumn<TAppt, TWh, TBlock>[] {
  const byId = new Map<string, CatalogProfessionalInput>();

  for (const prof of professionals) {
    byId.set(prof.id, prof);
  }

  for (const appt of appointments) {
    if (!byId.has(appt.professionalId)) {
      byId.set(appt.professionalId, {
        id: appt.professionalId,
        fullName: appt.professionalName ?? appt.professionalId,
        active: true,
      });
    }
  }

  for (const wh of workingHours) {
    if (!byId.has(wh.professionalId)) {
      byId.set(wh.professionalId, {
        id: wh.professionalId,
        fullName: wh.professionalId,
        active: true,
      });
    }
  }

  for (const block of blocks) {
    if (!byId.has(block.professionalId)) {
      byId.set(block.professionalId, {
        id: block.professionalId,
        fullName: block.professionalId,
        active: true,
      });
    }
  }

  const allProfessionals = Array.from(byId.values());
  const selectedProfessionals =
    typeof filterProfessionalId === "string" && filterProfessionalId !== ""
      ? allProfessionals.filter((prof) => prof.id === filterProfessionalId)
      : allProfessionals;

  selectedProfessionals.sort(compareProfessionals);

  return selectedProfessionals.map((prof) => ({
    id: prof.id,
    fullName: prof.fullName,
    active: prof.active,
    displayLabel: formatProfessionalLabel(prof),
    workingHours: workingHours.filter((wh) => wh.professionalId === prof.id && wh.weekday === weekday),
    blocks: blocks.filter((block) => block.professionalId === prof.id),
    appointments: appointments.filter((appt) => appt.professionalId === prof.id),
  }));
}

export interface PositionedAppointment<T extends AxisAppointmentInput = AxisAppointmentInput> {
  readonly appointment: T;
  readonly startMinute: number;
  readonly endMinute: number;
  readonly offsetMinutes: number;
  readonly durationMinutes: number;
  readonly effectiveMinutes: number;
  readonly topPercent: number;
  readonly heightPercent: number;
  readonly lane: number;
  readonly laneCount: number;
}

export interface AssignLanesOptions {
  readonly date: string;
  readonly timezone: string;
  readonly axisStartMinute?: number;
  readonly axisEndMinute?: number;
}

interface RawMeasuredAppointment<T extends AxisAppointmentInput> {
  readonly appointment: T;
  readonly startMinute: number;
  readonly endMinute: number;
  readonly offsetMinutes: number;
  readonly durationMinutes: number;
  readonly effectiveMinutes: number;
  readonly topPercent: number;
  readonly heightPercent: number;
}

export function assignLanes<T extends AxisAppointmentInput>(
  appointments: readonly T[],
  {
    date,
    timezone,
    axisStartMinute = AGENDA_DEFAULT_START_MINUTE,
    axisEndMinute = AGENDA_DEFAULT_END_MINUTE,
  }: AssignLanesOptions,
): PositionedAppointment<T>[] {
  const axisSpan = Math.max(1, axisEndMinute - axisStartMinute);
  const measured: RawMeasuredAppointment<T>[] = [];

  for (const appt of appointments) {
    const range = appointmentRange(appt.startAt, appt.endAt, date, timezone);
    if (range === null) {
      continue;
    }
    const startMinute = Math.max(axisStartMinute, Math.min(axisEndMinute, range.startMinute));
    const endMinute = Math.max(startMinute, Math.min(axisEndMinute, range.endMinute));
    if (endMinute <= startMinute) {
      continue;
    }
    const offsetMinutes = startMinute - axisStartMinute;
    const durationMinutes = endMinute - startMinute;
    const effectiveMinutes = Math.max(AGENDA_MIN_APPOINTMENT_MINUTES, durationMinutes);
    const topPercent = (offsetMinutes / axisSpan) * 100;
    const heightPercent = (effectiveMinutes / axisSpan) * 100;

    measured.push({
      appointment: appt,
      startMinute,
      endMinute,
      offsetMinutes,
      durationMinutes,
      effectiveMinutes,
      topPercent,
      heightPercent,
    });
  }

  measured.sort((a, b) => {
    if (a.startMinute !== b.startMinute) {
      return a.startMinute - b.startMinute;
    }
    if (a.endMinute !== b.endMinute) {
      return a.endMinute - b.endMinute;
    }
    return a.appointment.id.localeCompare(b.appointment.id);
  });

  const clusters: RawMeasuredAppointment<T>[][] = [];
  let currentCluster: RawMeasuredAppointment<T>[] = [];
  let clusterMaxEnd = -1;

  for (const item of measured) {
    if (currentCluster.length === 0 || item.startMinute < clusterMaxEnd) {
      currentCluster.push(item);
      clusterMaxEnd = Math.max(clusterMaxEnd, item.endMinute);
    } else {
      clusters.push(currentCluster);
      currentCluster = [item];
      clusterMaxEnd = item.endMinute;
    }
  }
  if (currentCluster.length > 0) {
    clusters.push(currentCluster);
  }

  const result: PositionedAppointment<T>[] = [];
  for (const cluster of clusters) {
    const laneEnds: number[] = [];
    const assigned: { item: RawMeasuredAppointment<T>; lane: number }[] = [];

    for (const item of cluster) {
      let laneIndex = laneEnds.findIndex((end) => end <= item.startMinute);
      if (laneIndex === -1) {
        laneIndex = laneEnds.length;
        laneEnds.push(item.endMinute);
      } else {
        laneEnds[laneIndex] = item.endMinute;
      }
      assigned.push({ item, lane: laneIndex });
    }

    const laneCount = Math.max(1, laneEnds.length);
    for (const { item, lane } of assigned) {
      result.push({
        ...item,
        lane,
        laneCount,
      });
    }
  }

  return result;
}


