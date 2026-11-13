import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { AppointmentDetailDialog } from "../appointments/AppointmentDetailDialog";
import { AppointmentFormDialog } from "../appointments/AppointmentFormDialog";
import { AppointmentRescheduleDialog } from "../appointments/AppointmentRescheduleDialog";
import { ErrorState } from "../../shared/components/ErrorState";
import { LoadingState } from "../../shared/components/LoadingState";
import { PageShell } from "../../shared/components/PageShell";
import type { AgendaAppointment } from "./agendaApi";
import { DEFAULT_AGENDA_TIMEZONE } from "./agendaConfig";
import { compareProfessionals } from "./agendaLayout";
import {
  addDays,
  formatLocalDate,
  formatLocalTime,
  isValidLocalDate,
  todayInTimeZone,
  weekRangeOf,
} from "./agendaTime";
import { AgendaToolbar } from "./AgendaToolbar";
import { AgendaView } from "./AgendaView";
import { systemClock, type Clock } from "./clock";
import { useAgenda } from "./useAgenda";
import styles from "./AgendaPage.module.css";

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export const INVALID_DATE_NOTICE = "La fecha del enlace no era válida; se muestra hoy.";

function sanitizeUuidParam(value: string | null): string | null {
  if (value === null || value === "") {
    return null;
  }
  return UUID_REGEX.test(value) ? value : null;
}

export interface AgendaPageProps {
  readonly clock?: Clock;
}

export function AgendaPage({ clock = systemClock }: AgendaPageProps) {
  const { client, clearActionErrors, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const rawDate = searchParams.get("date");
  const fallbackToday = todayInTimeZone(clock.now(), DEFAULT_AGENDA_TIMEZONE);
  const hasValidDate = isValidLocalDate(rawDate);
  const effectiveDate = hasValidDate ? rawDate : fallbackToday;

  const rawView = searchParams.get("view");
  const view: "day" | "week" = rawView === "week" ? "week" : "day";
  const isWeek = view === "week";

  const [invalidDateNotice, setInvalidDateNotice] = useState<string | null>(() =>
    rawDate !== null && !hasValidDate ? INVALID_DATE_NOTICE : null,
  );
  const [isAppointmentDialogOpen, setIsAppointmentDialogOpen] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<AgendaAppointment | null>(null);
  const [isRescheduling, setIsRescheduling] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const newAppointmentBtnRef = useRef<HTMLButtonElement | null>(null);

  const handleAppointmentSuccess = (info?: { date?: string; time?: string }) => {
    if (info?.date && info?.time) {
      const [year, month, day] = info.date.split("-");
      setStatusMessage(`Turno creado para el ${day}/${month}/${year} a las ${info.time}.`);
    }
    void state.refresh();
  };

  const handleStatusChanged = (newStatus: string) => {
    if (newStatus === "confirmado") {
      setStatusMessage("Turno confirmado.");
    } else if (newStatus === "atendido") {
      setStatusMessage("Turno marcado como atendido.");
    } else if (newStatus === "ausente") {
      setStatusMessage("Turno marcado como ausente.");
    }
    void state.refresh();
  };

  const handleCancelled = () => {
    setStatusMessage("Turno cancelado.");
    void state.refresh();
  };

  const handleRescheduleSuccess = (info: {
    date: string;
    time: string;
    appointment: { startAt: string };
  }) => {
    const [year, month, day] = formatLocalDate(info.appointment.startAt, state.timezone).split("-");
    const time = formatLocalTime(info.appointment.startAt, state.timezone);
    setStatusMessage(`Turno reprogramado para el ${day}/${month}/${year} a las ${time}.`);
    void state.refresh();
  };

  const rawProfessionalId = searchParams.get("professionalId");
  const rawChairId = searchParams.get("chairId");
  const explicitProfessionalId = sanitizeUuidParam(rawProfessionalId);
  const chairId = sanitizeUuidParam(rawChairId);

  const initialProfessionalId =
    explicitProfessionalId ??
    (isWeek && user?.role === "odontologo" ? user.professionalId : null);

  const week = isWeek ? weekRangeOf(effectiveDate) : null;
  const queryFrom = isWeek && week !== null ? week.monday : effectiveDate;
  const queryTo = isWeek && week !== null ? week.sunday : undefined;

  const state = useAgenda({
    client,
    date: queryFrom,
    toDate: queryTo,
    professionalId: initialProfessionalId,
    chairId,
    onForbidden: clearActionErrors,
  });

  const effectiveProfessionalId =
    initialProfessionalId ??
    (() => {
      if (!isWeek) {
        return null;
      }
      const sorted = [...state.professionals]
        .filter((p) => p.active)
        .sort(compareProfessionals);
      const first = sorted[0];
      return first !== undefined ? first.id : null;
    })();

  useEffect(() => {
    const needsDateNorm = rawDate === null || !hasValidDate;
    const needsProfNorm = rawProfessionalId !== null && explicitProfessionalId === null;
    const needsChairNorm = rawChairId !== null && chairId === null;
    if (!needsDateNorm && !needsProfNorm && !needsChairNorm) {
      return;
    }
    const normalized = new URLSearchParams();
    normalized.set("date", effectiveDate);
    if (view === "week") {
      normalized.set("view", "week");
    }
    if (explicitProfessionalId !== null) {
      normalized.set("professionalId", explicitProfessionalId);
    }
    if (chairId !== null) {
      normalized.set("chairId", chairId);
    }
    setSearchParams(normalized, { replace: true });
  }, [
    rawDate,
    hasValidDate,
    effectiveDate,
    rawProfessionalId,
    explicitProfessionalId,
    rawChairId,
    chairId,
    view,
    setSearchParams,
  ]);

  const buildParams = (next: {
    readonly date?: string;
    readonly view?: "day" | "week";
    readonly professionalId?: string | null;
    readonly chairId?: string | null;
  }): URLSearchParams => {
    const params = new URLSearchParams();
    params.set("date", next.date ?? effectiveDate);
    const nextView = next.view !== undefined ? next.view : view;
    if (nextView === "week") {
      params.set("view", "week");
    }
    const nextProf =
      next.professionalId !== undefined ? next.professionalId : explicitProfessionalId;
    const nextChair = next.chairId !== undefined ? next.chairId : chairId;
    if (nextProf !== null && nextProf !== "") {
      params.set("professionalId", nextProf);
    }
    if (nextChair !== null && nextChair !== "") {
      params.set("chairId", nextChair);
    }
    return params;
  };

  const navigateToDate = (nextDate: string) => {
    if (!isValidLocalDate(nextDate)) {
      return;
    }
    setInvalidDateNotice(null);
    setSearchParams(buildParams({ date: nextDate }), { replace: false });
  };

  const handleSelectView = (nextView: "day" | "week") => {
    setSearchParams(buildParams({ view: nextView }), { replace: false });
  };

  const handleSelectProfessional = (nextProfId: string | null) => {
    setSearchParams(buildParams({ professionalId: nextProfId }), { replace: false });
  };

  const handleSelectChair = (nextChairId: string | null) => {
    setSearchParams(buildParams({ chairId: nextChairId }), { replace: false });
  };

  const handleClearFilters = () => {
    setSearchParams(buildParams({ professionalId: null, chairId: null }), { replace: false });
  };

  return (
    <PageShell title={isWeek ? "Agenda semanal" : "Agenda diaria"}>
      <AgendaToolbar
        date={effectiveDate}
        view={view}
        professionalId={effectiveProfessionalId}
        chairId={chairId}
        professionals={state.professionals}
        chairs={state.chairs}
        onSelectProfessional={handleSelectProfessional}
        onSelectChair={handleSelectChair}
        onClearFilters={handleClearFilters}
        onPrevDay={() => navigateToDate(addDays(effectiveDate, isWeek ? -7 : -1))}
        onNextDay={() => navigateToDate(addDays(effectiveDate, isWeek ? 7 : 1))}
        onToday={() => navigateToDate(todayInTimeZone(clock.now(), state.timezone))}
        onSelectDate={navigateToDate}
        onRefresh={state.refresh}
        onSelectView={handleSelectView}
        invalidDateNotice={invalidDateNotice}
        userRole={user?.role}
        onNewAppointment={() => setIsAppointmentDialogOpen(true)}
        newAppointmentRef={newAppointmentBtnRef}
      />

      {state.phase === "loading" && state.agenda === null && <LoadingState />}

      {state.phase === "error" && (
        <ErrorState messages={state.errorMessages} onRetry={state.refresh} />
      )}

      {state.agenda !== null && state.phase !== "error" && (
        <AgendaView
          date={effectiveDate}
          view={view}
          todayDate={todayInTimeZone(clock.now(), state.timezone)}
          timezone={state.timezone}
          agenda={state.agenda}
          professionals={state.professionals}
          filterProfessionalId={effectiveProfessionalId}
          filterChairId={chairId}
          isRefreshing={state.phase === "refreshing"}
          catalogWarning={state.catalogWarning}
          onSelectAppointment={(appt) => {
            setSelectedAppointment(appt);
            setIsRescheduling(false);
          }}
        />
      )}

      {selectedAppointment !== null && !isRescheduling && (
        <AppointmentDetailDialog
          open={selectedAppointment !== null && !isRescheduling}
          onClose={() => setSelectedAppointment(null)}
          appointment={selectedAppointment}
          client={client}
          timezone={state.timezone}
          currentUser={user}
          onStatusChanged={handleStatusChanged}
          onCancelled={handleCancelled}
          onRequestReschedule={(appt) => {
            setSelectedAppointment(appt);
            setIsRescheduling(true);
          }}
        />
      )}

      {selectedAppointment !== null && isRescheduling && (
        <AppointmentRescheduleDialog
          open={selectedAppointment !== null && isRescheduling}
          onClose={() => {
            setIsRescheduling(false);
            setSelectedAppointment(null);
          }}
          appointment={selectedAppointment}
          client={client}
          timezone={state.timezone}
          professionals={state.professionals}
          chairs={state.chairs}
          onSuccess={handleRescheduleSuccess}
        />
      )}

      {isAppointmentDialogOpen && (
        <AppointmentFormDialog
          open={isAppointmentDialogOpen}
          onClose={() => setIsAppointmentDialogOpen(false)}
          onSuccess={handleAppointmentSuccess}
          client={client}
          timezone={state.timezone}
          effectiveDate={effectiveDate}
          initialProfessionalId={effectiveProfessionalId}
          initialChairId={chairId}
          professionals={state.professionals}
          chairs={state.chairs}
          returnFocusRef={newAppointmentBtnRef}
        />
      )}

      <div
        role={state.phase === "loading" ? undefined : "status"}
        aria-live="polite"
        className={styles.srOnly}
      >
        {statusMessage}
      </div>
    </PageShell>
  );
}
