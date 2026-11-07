import { PageShell } from "../shared/components/PageShell";
import { StatusBadge } from "../shared/components/StatusBadge";
import { APPOINTMENT_STATUSES } from "../shared/styles/appointmentStatusTokens";
import styles from "./HomePage.module.css";

export function HomePage() {
  return (
    <PageShell title="Turnos Odontología">
      <section className={styles.hero}>
        <h1 className={styles.title}>Turnos Odontología</h1>
        <p className={styles.lead}>
          Bienvenida a la agenda del consultorio. Pronto vas a poder ingresar y gestionar los turnos desde acá.
        </p>
      </section>
      <section className={styles.section} aria-labelledby="estados-titulo">
        <h2 id="estados-titulo" className={styles.sectionTitle}>
          Estados de un turno
        </h2>
        <ul className={styles.statuses} aria-label="Estados de un turno">
          {APPOINTMENT_STATUSES.map((status) => (
            <li key={status}>
              <StatusBadge status={status} />
            </li>
          ))}
        </ul>
      </section>
    </PageShell>
  );
}
