import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "../auth/AuthContext";
import { getApiErrorMessages } from "../../shared/api/errors";
import { EmptyState } from "../../shared/components/EmptyState";
import { ErrorState } from "../../shared/components/ErrorState";
import { LoadingState } from "../../shared/components/LoadingState";
import { PageShell } from "../../shared/components/PageShell";
import { PatientFormDialog } from "./PatientFormDialog";
import { listPatients, type PatientItem } from "./pacientesApi";
import styles from "./PacientesPage.module.css";

export function PacientesPage() {
  const { client, user } = useAuth();
  const [patients, setPatients] = useState<readonly PatientItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessages, setErrorMessages] = useState<readonly string[] | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<PatientItem | null>(null);

  const [reloadToken, setReloadToken] = useState(0);

  const canEdit = user?.role === "administrador" || user?.role === "recepcion";

  useEffect(() => {
    let cancelled = false;

    void listPatients(client, activeQuery).then((res) => {
      if (cancelled) {
        return;
      }
      if (!res.ok) {
        setErrorMessages(getApiErrorMessages(res.error));
        setPatients([]);
      } else {
        setPatients(res.data);
      }
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [client, activeQuery, reloadToken]);

  const handleRetry = () => {
    setLoading(true);
    setErrorMessages(null);
    setReloadToken((prev) => prev + 1);
  };

  const handleSearchSubmit = (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessages(null);
    setActiveQuery(searchQuery);
  };

  return (
    <PageShell title="Pacientes">
      <div className={styles.page}>
        <header className={styles.header}>
          <h1 className={styles.title}>Pacientes</h1>
          {canEdit && (
            <button
              type="button"
              className={styles.primaryButton}
              onClick={() => {
                setSelectedPatient(null);
                setDialogOpen(true);
              }}
            >
              Nuevo paciente
            </button>
          )}
        </header>

        <form className={styles.searchForm} onSubmit={handleSearchSubmit}>
          <div className={styles.searchGroup}>
            <label htmlFor="patient-search" className={styles.searchLabel}>
              Buscar por nombre o DNI
            </label>
            <input
              id="patient-search"
              type="search"
              className={styles.searchInput}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar por nombre o DNI"
            />
          </div>
          <button type="submit" className={styles.searchButton}>
            Buscar
          </button>
        </form>

        <div
          role="status"
          aria-live="polite"
          className={statusMessage !== null ? styles.statusBanner : styles.statusEmpty}
        >
          {statusMessage ?? ""}
        </div>

        {loading ? (
          <LoadingState label="Cargando pacientes…" />
        ) : errorMessages !== null ? (
          <ErrorState
            title="Error al cargar pacientes"
            messages={errorMessages}
            onRetry={handleRetry}
          />
        ) : patients.length === 0 ? (
          <EmptyState
            title="No se encontraron pacientes."
            description={
              activeQuery
                ? undefined
                : "Aún no hay pacientes registrados en el sistema."
            }
          />
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <caption className={styles.caption}>Listado de pacientes</caption>
              <thead>
                <tr>
                  <th scope="col" className={styles.th}>
                    Nombre
                  </th>
                  <th scope="col" className={styles.th}>
                    DNI
                  </th>
                  <th scope="col" className={styles.th}>
                    Teléfono
                  </th>
                  <th scope="col" className={styles.th}>
                    Obra social
                  </th>
                  {canEdit && (
                    <th scope="col" className={styles.th}>
                      Acciones
                    </th>
                  )}
                </tr>
              </thead>
              <tbody>
                {patients.map((patient) => (
                  <tr key={patient.id}>
                    <td className={styles.td} data-label="Nombre">
                      {patient.fullName}
                    </td>
                    <td className={styles.td} data-label="DNI">
                      {patient.dni}
                    </td>
                    <td className={styles.td} data-label="Teléfono">
                      {patient.phone ?? "Sin dato"}
                    </td>
                    <td className={styles.td} data-label="Obra social">
                      {patient.healthInsurance ?? "Sin dato"}
                    </td>
                    {canEdit && (
                      <td className={styles.td} data-label="Acciones">
                        <button
                          type="button"
                          className={styles.actionButton}
                          onClick={() => {
                            setSelectedPatient(patient);
                            setDialogOpen(true);
                          }}
                        >
                          Editar
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <PatientFormDialog
          open={dialogOpen}
          patient={selectedPatient}
          onClose={() => setDialogOpen(false)}
          onSuccess={(msg) => {
            setStatusMessage(msg);
            setReloadToken((prev) => prev + 1);
          }}
        />
      </div>
    </PageShell>
  );
}
