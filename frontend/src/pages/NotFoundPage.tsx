import { Link } from "react-router-dom";
import { PageShell } from "../shared/components/PageShell";
import styles from "./NotFoundPage.module.css";

export function NotFoundPage() {
  return (
    <PageShell title="Turnos Odontología">
      <section className={styles.notFound}>
        <h1 className={styles.title}>Página no encontrada</h1>
        <p className={styles.text}>La dirección que abriste no existe en la agenda.</p>
        <Link className={styles.link} to="/">
          Volver al inicio
        </Link>
      </section>
    </PageShell>
  );
}
