import { useRef, useState } from "react";
import logoAquaClaro from "../../assets/brand/logo-aqua-claro.png";
import type { ApiResult, CurrentUser } from "../../shared/api/types";
import type { LoginCredentials } from "../auth/authApi";
import { LoginCarousel, type CarouselTicker } from "../login/LoginCarousel";
import {
  contact,
  demoBadge,
  demoContactNote,
  heroLead,
  professionals,
  schedule,
  services,
} from "./landingContent";
import { LoginDialog } from "./LoginDialog";
import { RevealSection } from "./RevealSection";
import type { RevealObserverFactory } from "./revealObserver";
import styles from "./LandingPage.module.css";

export interface LandingPageProps {
  onLogin: (credentials: LoginCredentials) => Promise<ApiResult<CurrentUser>>;
  initialNotice?: string | null;
  carouselTicker?: CarouselTicker;
  prefersReducedMotion?: boolean;
  revealObserver?: RevealObserverFactory;
}

export function LandingPage({
  onLogin,
  initialNotice = null,
  carouselTicker,
  prefersReducedMotion,
  revealObserver,
}: LandingPageProps) {
  const ctaRef = useRef<HTMLButtonElement>(null);
  const [isLoginOpen, setIsLoginOpen] = useState(true);

  return (
    <main className={styles.page}>
      <section className={styles.hero} aria-labelledby="hero-heading">
        <div className={styles.heroBackground}>
          <LoginCarousel ticker={carouselTicker} prefersReducedMotion={prefersReducedMotion} />
        </div>
        <div className={styles.heroContent}>
          <h1 id="hero-heading" className={styles.heroTitle}>
            <img src={logoAquaClaro} alt="Aqua — Clínica Odontológica" className={styles.logo} />
          </h1>
          <p className={styles.tagline}>Claridad en cada cuidado.</p>
          <p className={styles.lead}>{heroLead}</p>
          <span className={styles.badge}>{demoBadge}</span>
          <button
            ref={ctaRef}
            type="button"
            className={styles.cta}
            onClick={() => {
              setIsLoginOpen(true);
            }}
          >
            Ingresar al sistema
          </button>
        </div>
      </section>
      <RevealSection observer={revealObserver} reducedMotion={prefersReducedMotion}>
        <section className={styles.section} aria-labelledby="about-heading">
          <h2 id="about-heading" className={styles.sectionTitle}>
            Quiénes somos
          </h2>
          <p className={styles.sectionText}>
            Aqua es una clínica odontológica de demostración. Coordinamos la agenda entre profesionales y sillones
            para que cada consulta tenga su tiempo y no haya superposiciones. Todos los nombres, horarios y datos
            de contacto de este sitio son ficticios.
          </p>
        </section>
      </RevealSection>
      <RevealSection observer={revealObserver} reducedMotion={prefersReducedMotion}>
        <section className={styles.section} aria-labelledby="services-heading">
          <h2 id="services-heading" className={styles.sectionTitle}>
            Servicios
          </h2>
          <p className={styles.sectionText}>
            Prestaciones de la demo, con la duración con la que el sistema reserva cada turno.
          </p>
          <ul className={styles.list}>
            {services.map((service) => (
              <li key={service.name}>
                <strong>{service.name}</strong> — {service.durationMinutes} min — {service.description}
              </li>
            ))}
          </ul>
        </section>
      </RevealSection>
      <RevealSection observer={revealObserver} reducedMotion={prefersReducedMotion}>
        <section className={styles.section} aria-labelledby="team-heading">
          <h2 id="team-heading" className={styles.sectionTitle}>
            Equipo
          </h2>
          <ul className={styles.list}>
            {professionals.map((professional) => (
              <li key={professional.name}>
                <strong>{professional.name}</strong> — {professional.schedule}
              </li>
            ))}
          </ul>
          <p className={styles.sectionText}>Nombres ficticios tomados de los datos de demostración.</p>
        </section>
      </RevealSection>
      <RevealSection observer={revealObserver} reducedMotion={prefersReducedMotion}>
        <section className={styles.section} aria-labelledby="contact-heading">
          <h2 id="contact-heading" className={styles.sectionTitle}>
            Horarios y contacto
          </h2>
          <p className={styles.sectionText}>
            Lunes a viernes: {schedule.morning} y {schedule.afternoon}.
          </p>
          <p className={styles.sectionText}>El Dr. Martín Sosa atiende solo por la mañana.</p>
          <ul className={styles.list}>
            <li>Dirección: {contact.address}</li>
            <li>Teléfono: {contact.phone}</li>
            <li>Correo: {contact.email}</li>
          </ul>
          <p className={styles.demoNote}>{demoContactNote}</p>
        </section>
      </RevealSection>
      <LoginDialog
        open={isLoginOpen}
        onClose={() => {
          setIsLoginOpen(false);
        }}
        onLogin={onLogin}
        initialNotice={initialNotice}
        returnFocusRef={ctaRef}
      />
    </main>
  );
}
