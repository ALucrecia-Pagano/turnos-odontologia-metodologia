import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../../shared/components/ErrorState";
import { LoadingState } from "../../shared/components/LoadingState";
import { PageShell } from "../../shared/components/PageShell";
import { DEFAULT_AGENDA_TIMEZONE } from "./agendaConfig";
import { addDays, isValidLocalDate, todayInTimeZone } from "./agendaTime";
import { AgendaToolbar } from "./AgendaToolbar";
import { AgendaView } from "./AgendaView";
import { systemClock, type Clock } from "./clock";
import { useAgenda } from "./useAgenda";

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
  const { client, clearActionErrors } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const rawDate = searchParams.get("date");
  const fallbackToday = todayInTimeZone(clock.now(), DEFAULT_AGENDA_TIMEZONE);
  const hasValidDate = isValidLocalDate(rawDate);
  const effectiveDate = hasValidDate ? rawDate : fallbackToday;

  const [invalidDateNotice, setInvalidDateNotice] = useState<string | null>(() =>
    rawDate !== null && !hasValidDate ? INVALID_DATE_NOTICE : null,
  );

  const rawProfessionalId = searchParams.get("professionalId");
  const rawChairId = searchParams.get("chairId");
  const professionalId = sanitizeUuidParam(rawProfessionalId);
  const chairId = sanitizeUuidParam(rawChairId);

  const state = useAgenda({
    client,
    date: effectiveDate,
    professionalId,
    chairId,
    onForbidden: clearActionErrors,
  });

  useEffect(() => {
    const needsDateNorm = rawDate === null || !hasValidDate;
    const needsProfNorm = rawProfessionalId !== null && professionalId === null;
    const needsChairNorm = rawChairId !== null && chairId === null;
    if (!needsDateNorm && !needsProfNorm && !needsChairNorm) {
      return;
    }
    const normalized = new URLSearchParams();
    normalized.set("date", effectiveDate);
    if (professionalId !== null) {
      normalized.set("professionalId", professionalId);
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
    professionalId,
    rawChairId,
    chairId,
    setSearchParams,
  ]);

  const buildParams = (next: {
    readonly date?: string;
    readonly professionalId?: string | null;
    readonly chairId?: string | null;
  }): URLSearchParams => {
    const params = new URLSearchParams();
    params.set("date", next.date ?? effectiveDate);
    const nextProf = next.professionalId !== undefined ? next.professionalId : professionalId;
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
    <PageShell title="Agenda diaria">
      <AgendaToolbar
        date={effectiveDate}
        professionalId={professionalId}
        chairId={chairId}
        professionals={state.professionals}
        chairs={state.chairs}
        onSelectProfessional={handleSelectProfessional}
        onSelectChair={handleSelectChair}
        onClearFilters={handleClearFilters}
        onPrevDay={() => navigateToDate(addDays(effectiveDate, -1))}
        onNextDay={() => navigateToDate(addDays(effectiveDate, 1))}
        onToday={() => navigateToDate(todayInTimeZone(clock.now(), state.timezone))}
        onSelectDate={navigateToDate}
        onRefresh={state.refresh}
        invalidDateNotice={invalidDateNotice}
      />

      {state.phase === "loading" && state.agenda === null && <LoadingState />}

      {state.phase === "error" && (
        <ErrorState messages={state.errorMessages} onRetry={state.refresh} />
      )}

      {state.agenda !== null && state.phase !== "error" && (
        <AgendaView
          date={effectiveDate}
          timezone={state.timezone}
          agenda={state.agenda}
          professionals={state.professionals}
          filterProfessionalId={professionalId}
          filterChairId={chairId}
          isRefreshing={state.phase === "refreshing"}
          catalogWarning={state.catalogWarning}
        />
      )}
    </PageShell>
  );
}
