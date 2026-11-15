import { useRef, useState } from "react";
import type { ApiClient } from "../../shared/api/client";
import { AffectedAppointments } from "./AffectedAppointments";
import { BlockDeleteDialog } from "./BlockDeleteDialog";
import { BlockFormDialog } from "./BlockFormDialog";
import {
  deleteBlock,
  type AffectedAppointment,
  type CreateBlockResponse,
  type ProfessionalBlock,
} from "./horariosApi";
import { formatLocalRangeInZone } from "./horariosTime";
import styles from "./BlocksSection.module.css";

export interface BlocksSectionProps {
  readonly client: ApiClient;
  readonly professionalId: string;
  readonly professionalName?: string;
  readonly timezone: string;
  readonly initialBlocks: readonly ProfessionalBlock[];
  readonly readOnly?: boolean;
  readonly defaultDate?: string;
  readonly onStatusChange?: (message: string | null) => void;
}

export function BlocksSection({
  client,
  professionalId,
  professionalName = "",
  timezone,
  initialBlocks,
  readOnly = false,
  defaultDate,
  onStatusChange,
}: BlocksSectionProps) {
  const [prevKey, setPrevKey] = useState({ initialBlocks, professionalId });
  const [blocks, setBlocks] = useState<readonly ProfessionalBlock[]>(initialBlocks);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [blockToDelete, setBlockToDelete] = useState<ProfessionalBlock | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [affectedAppointments, setAffectedAppointments] = useState<
    readonly AffectedAppointment[]
  >([]);
  const newBlockButtonRef = useRef<HTMLButtonElement | null>(null);
  const activeDeleteButtonRef = useRef<HTMLElement | null>(null);

  const updateStatus = (message: string | null) => {
    setStatusMessage(message);
    onStatusChange?.(message);
  };

  if (
    prevKey.initialBlocks !== initialBlocks ||
    prevKey.professionalId !== professionalId
  ) {
    setPrevKey({ initialBlocks, professionalId });
    setBlocks(initialBlocks);
    setStatusMessage(null);
    setAffectedAppointments([]);
  }

  const handleCreated = (response: CreateBlockResponse) => {
    setBlocks((prev) =>
      [...prev, response.block].sort((a, b) => a.startAt.localeCompare(b.startAt)),
    );
    updateStatus("Bloqueo creado.");
    setAffectedAppointments(response.affectedAppointments);
  };

  const handleConfirmDelete = async () => {
    if (blockToDelete === null) {
      return;
    }
    const targetId = blockToDelete.id;
    setIsDeleting(true);
    updateStatus(null);
    const result = await deleteBlock(client, targetId);
    setIsDeleting(false);
    if (result.ok) {
      setBlocks((prev) => prev.filter((item) => item.id !== targetId));
      setBlockToDelete(null);
      setAffectedAppointments([]);
      updateStatus("Bloqueo eliminado.");
    }
  };

  return (
    <section className={styles.section} aria-labelledby="blocks-heading">
      <div className={styles.header}>
        <div>
          <h2 id="blocks-heading" className={styles.title}>
            Bloqueos de agenda
          </h2>
          <p className={styles.subtitle}>Ausencias puntuales, feriados y licencias</p>
        </div>
        {!readOnly && (
          <button
            ref={newBlockButtonRef}
            type="button"
            className={styles.newBlockButton}
            onClick={() => {
              updateStatus(null);
              setIsFormOpen(true);
            }}
          >
            Nuevo bloqueo
          </button>
        )}
      </div>

      {onStatusChange === undefined && (
        <div
          role="status"
          aria-live="polite"
          className={statusMessage !== null ? styles.statusBanner : styles.statusEmpty}
        >
          {statusMessage ?? ""}
        </div>
      )}

      <AffectedAppointments
        kind="block"
        appointments={affectedAppointments}
        professionalName={professionalName}
        timezone={timezone}
      />

      {blocks.length === 0 ? (
        <p className={styles.emptyBlocks}>No hay bloqueos registrados.</p>
      ) : (
        <ul className={styles.blocksList}>
          {blocks.map((block) => {
            const { dateLabel, timeLabel } = formatLocalRangeInZone(
              block.startAt,
              block.endAt,
              timezone,
            );
            return (
              <li key={block.id} className={styles.blockCard}>
                <div className={styles.blockDetails}>
                  <span className={styles.blockSchedule}>
                    {dateLabel} · {timeLabel}
                  </span>
                  {block.reason !== null && block.reason !== "" && (
                    <span className={styles.blockReason}>{block.reason}</span>
                  )}
                </div>
                {!readOnly && (
                  <button
                    type="button"
                    className={styles.deleteButton}
                    onClick={(e) => {
                      activeDeleteButtonRef.current = e.currentTarget;
                      updateStatus(null);
                      setBlockToDelete(block);
                    }}
                  >
                    Eliminar bloqueo
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      <BlockFormDialog
        open={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onCreated={handleCreated}
        client={client}
        professionalId={professionalId}
        timezone={timezone}
        defaultDate={defaultDate}
        returnFocusRef={newBlockButtonRef}
      />

      <BlockDeleteDialog
        open={blockToDelete !== null}
        block={blockToDelete}
        timezone={timezone}
        isDeleting={isDeleting}
        onConfirm={() => {
          void handleConfirmDelete();
        }}
        onClose={() => setBlockToDelete(null)}
        returnFocusRef={activeDeleteButtonRef}
      />
    </section>
  );
}
