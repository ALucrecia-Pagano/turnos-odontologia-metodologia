import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchAgenda, fetchProfessionals, type Professional } from "../agenda/agendaApi";
import { systemClock, type Clock } from "../agenda/clock";
import { useAuth } from "../auth/AuthContext";
import { getApiErrorMessages } from "../../shared/api/errors";
import { LoadingState } from "../../shared/components/LoadingState";
import { PageShell } from "../../shared/components/PageShell";
import { BlocksSection } from "./BlocksSection";
import {
  getWorkingHours,
  listBlocks,
  type ProfessionalBlock,
  type WorkingHoursSlot,
} from "./horariosApi";
import { formatLocalDateInZone } from "./horariosTime";
import { WorkingHoursSection } from "./WorkingHoursSection";
import styles from "./HorariosPage.module.css";

export interface HorariosPageProps {
  readonly clock?: Clock;
}

export function HorariosPage({ clock = systemClock }: HorariosPageProps = {}) {
  const { client, clearActionErrors, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [timezone, setTimezone] = useState<string | null>(null);
  const [professionals, setProfessionals] = useState<readonly Professional[]>([]);
  const [catalogLoaded, setCatalogLoaded] = useState(false);
  const [workingHours, setWorkingHours] = useState<readonly WorkingHoursSlot[]>([]);
  const [blocks, setBlocks] = useState<readonly ProfessionalBlock[]>([]);
  const [pageError, setPageError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [settledTargetId, setSettledTargetId] = useState<string | null>(null);

  const isDentist = user?.role === "odontologo";
  const isReadOnly = user?.role === "recepcion";
  const showSelector = !isDentist;

  useEffect(() => {
    let cancelled = false;
    const utcDay = clock.now().toISOString().slice(0, 10);

    const agendaPromise = fetchAgenda(client, { from: utcDay, to: utcDay });
    const profsPromise = showSelector
      ? fetchProfessionals(client)
      : Promise.resolve(null);

    void Promise.all([agendaPromise, profsPromise]).then(([agendaRes, profsRes]) => {
      if (cancelled) {
        return;
      }
      if (agendaRes.ok) {
        setTimezone(agendaRes.data.timezone);
      }
      if (profsRes !== null && profsRes.ok) {
        setProfessionals(profsRes.data.filter((p) => p.active));
      }
      setCatalogLoaded(true);
    });

    return () => {
      cancelled = true;
    };
  }, [client, clock, showSelector]);

  const queryProfessionalId = searchParams.get("professionalId");
  const targetProfessionalId =
    queryProfessionalId !== null && queryProfessionalId !== ""
      ? queryProfessionalId
      : isDentist
        ? (user?.professionalId ?? null)
        : (professionals[0]?.id ?? null);

  useEffect(() => {
    if (!catalogLoaded || targetProfessionalId === null) {
      return;
    }

    let cancelled = false;

    void Promise.all([
      getWorkingHours(client, targetProfessionalId),
      listBlocks(client, targetProfessionalId),
    ]).then(([hoursRes, blocksRes]) => {
      if (cancelled) {
        return;
      }
      if (!hoursRes.ok) {
        clearActionErrors();
        setPageError(getApiErrorMessages(hoursRes.error).join(" "));
        setSettledTargetId(targetProfessionalId);
        return;
      }
      if (!blocksRes.ok) {
        clearActionErrors();
        setPageError(getApiErrorMessages(blocksRes.error).join(" "));
        setSettledTargetId(targetProfessionalId);
        return;
      }
      setPageError(null);
      setStatusMessage(null);
      setWorkingHours(hoursRes.data);
      setBlocks(blocksRes.data);
      setSettledTargetId(targetProfessionalId);
    });

    return () => {
      cancelled = true;
    };
  }, [catalogLoaded, clearActionErrors, client, targetProfessionalId]);

  const loadingData =
    targetProfessionalId !== null && settledTargetId !== targetProfessionalId;

  const selectedProfessional = professionals.find((p) => p.id === targetProfessionalId);
  const effectiveProfessionalName = isDentist
    ? (user?.displayName ?? "")
    : (selectedProfessional?.fullName ?? "");

  const defaultDate =
    timezone !== null ? formatLocalDateInZone(clock.now().toISOString(), timezone) : undefined;

  return (
    <PageShell title="Horarios y bloqueos">
      <div className={styles.page}>
        <header className={styles.header}>
          <div className={styles.titleGroup}>
            <h1 id="horarios-page-title" className={styles.title}>
              Horarios y bloqueos
            </h1>
            <p className={styles.subtitle}>
              Gestión de horarios semanales de atención y ausencias programadas
            </p>
          </div>

          {showSelector && catalogLoaded && (
            <div className={styles.selectorGroup}>
              <label htmlFor="horarios-professional-select" className={styles.selectorLabel}>
                Profesional
              </label>
              <select
                id="horarios-professional-select"
                aria-label="Profesional"
                className={styles.selector}
                value={targetProfessionalId ?? ""}
                onChange={(e) => {
                  const nextId = e.target.value;
                  setStatusMessage(null);
                  setSearchParams({ professionalId: nextId });
                }}
              >
                {professionals.map((prof) => (
                  <option key={prof.id} value={prof.id}>
                    {prof.fullName}
                  </option>
                ))}
              </select>
            </div>
          )}
        </header>

        <div
          role="status"
          aria-live="polite"
          className={statusMessage !== null ? styles.statusBanner : styles.statusEmpty}
        >
          {statusMessage ?? ""}
        </div>

        {!catalogLoaded || loadingData ? (
          <LoadingState label="Cargando horarios y bloqueos…" />
        ) : pageError !== null ? (
          <div role="alert" className={styles.alertBanner}>
            {pageError}
          </div>
        ) : (
          targetProfessionalId !== null &&
          timezone !== null && (
            <div className={styles.grid}>
              <WorkingHoursSection
                client={client}
                professionalId={targetProfessionalId}
                professionalName={effectiveProfessionalName}
                timezone={timezone}
                initialSlots={workingHours}
                readOnly={isReadOnly}
                onStatusChange={setStatusMessage}
              />
              <BlocksSection
                client={client}
                professionalId={targetProfessionalId}
                professionalName={effectiveProfessionalName}
                timezone={timezone}
                initialBlocks={blocks}
                readOnly={isReadOnly}
                defaultDate={defaultDate}
                onStatusChange={setStatusMessage}
              />
            </div>
          )
        )}
      </div>
    </PageShell>
  );
}
