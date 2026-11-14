import { Link } from "react-router-dom";
import styles from "./AccesoPage.module.css";

interface RoleCard {
  readonly id: string;
  readonly title: string;
  readonly description: string;
  readonly to: string;
}

const ROLE_CARDS: readonly RoleCard[] = [
  { id: "recepcion", title: "Recepción", description: "Agenda general y turnos del día.", to: "/login?rol=recepcion" },
  { id: "odontologo", title: "Odontología", description: "Tu agenda como profesional.", to: "/login?rol=odontologo" },
  {
    id: "administrador",
    title: "Administración",
    description: "Vista completa del consultorio.",
    to: "/login?rol=administrador",
  },
];

export function AccesoPage() {
  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <Link to="/" className={styles.backLink}>
          ← Volver a Aqua
        </Link>
        <h1 className={styles.title}>¿Cómo querés ingresar?</h1>
        <ul className={styles.cards}>
          {ROLE_CARDS.map((card) => (
            <li key={card.id}>
              <Link
                to={card.to}
                className={styles.card}
                aria-labelledby={`acceso-${card.id}-titulo`}
                aria-describedby={`acceso-${card.id}-detalle`}
              >
                <span id={`acceso-${card.id}-titulo`} className={styles.cardTitle}>
                  {card.title}
                </span>
                <span id={`acceso-${card.id}-detalle`} className={styles.cardDetail}>
                  {card.description}
                </span>
                <span className={styles.cardArrow} aria-hidden="true">
                  →
                </span>
              </Link>
            </li>
          ))}
        </ul>
        <p className={styles.note}>El rol se confirma al ingresar</p>
      </div>
    </main>
  );
}
