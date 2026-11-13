import { useState, type KeyboardEvent } from "react";
import type { ApiClient } from "../../shared/api/client";
import styles from "./PatientSearchGroup.module.css";

export interface Patient {
  id: string;
  fullName: string;
  dni: string;
}

export interface PatientSearchGroupProps {
  client: ApiClient;
  selectedPatientId: string | null;
  onSelectPatient: (patientId: string) => void;
  inputRef?: { current: HTMLInputElement | null };
}

export function PatientSearchGroup({
  client,
  selectedPatientId,
  onSelectPatient,
  inputRef,
}: PatientSearchGroupProps) {
  const [query, setQuery] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async () => {
    const trimmed = query.trim();
    setIsLoading(true);
    const result = await client.request(
      `/patients?query=${encodeURIComponent(trimmed)}`,
    );
    setIsLoading(false);
    setHasSearched(true);
    if (result.ok && Array.isArray(result.data)) {
      setPatients(result.data as unknown as Patient[]);
    } else {
      setPatients([]);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      void handleSearch();
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.searchRow}>
        <div className={styles.field}>
          <label htmlFor="patient-search-input" className={styles.label}>
            Paciente
          </label>
          <input
            ref={inputRef}
            id="patient-search-input"
            type="search"
            className={styles.input}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Buscar por nombre o DNI..."
            aria-label="Buscar paciente"
          />
        </div>
        <button
          type="button"
          className={styles.searchButton}
          onClick={() => void handleSearch()}
          disabled={isLoading}
        >
          {isLoading ? "Buscando..." : "Buscar paciente"}
        </button>
      </div>

      {hasSearched && patients.length === 0 && !isLoading && (
        <p className={styles.notice} role="status">
          No se encontraron pacientes
        </p>
      )}

      {patients.length > 0 && (
        <div
          className={styles.resultsGroup}
          role="radiogroup"
          aria-label="Pacientes encontrados"
        >
          {patients.map((p) => (
            <label key={p.id} className={styles.radioLabel}>
              <input
                type="radio"
                name="patientId"
                className={styles.radioInput}
                value={p.id}
                checked={selectedPatientId === p.id}
                onChange={() => onSelectPatient(p.id)}
              />
              <span>
                {p.fullName} (DNI {p.dni})
              </span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
