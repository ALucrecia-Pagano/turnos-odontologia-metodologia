import { Link } from "react-router-dom";
import logoAquaClaro from "../../assets/brand/logo-aqua-claro.png";
import { LoginCarousel, type CarouselTicker } from "../login/LoginCarousel";
import { contact, demoBadge, demoContactNote, heroLead, professionals, schedule, services } from "./landingContent";
import { RevealSection } from "./RevealSection";
import { detectPrefersReducedMotion, type RevealObserverFactory } from "./revealObserver";
import styles from "./LandingPage.module.css";

export interface LandingPageProps {
  carouselTicker?: CarouselTicker;
  reducedMotion?: boolean;
  observer?: RevealObserverFactory;
}

export function LandingPage({ carouselTicker, reducedMotion, observer }: LandingPageProps = {}) {
  const motionReduced = reducedMotion ?? detectPrefersReducedMotion();

  return (
    <div className={styles.page}>
      <header className={styles.topBar}>
        <nav aria-label="Navegación principal">
          <ul className={styles.navList}>
            <li>
              <Link to="/" className={styles.navLink} aria-current="page">
                Inicio
              </Link>
            </li>
            <li>
              <a href="#la-clinica" className={styles.navLink}>
                La clínica
              </a>
            </li>
            <li>
              <Link to="/acceso" className={styles.navLink}>
                Acceder
              </Link>
            </li>
          </ul>
        </nav>
      </header>
      <main>
        <section className={styles.hero}>
          <LoginCarousel ticker={carouselTicker} prefersReducedMotion={motionReduced} />
          <div className={styles.heroOverlay} data-landing-overlay="" aria-hidden="true" />
          <div className={styles.heroContent}>
            <h1 className={styles.logoHeading}>
              <img src={logoAquaClaro} alt="Aqua — Clínica Odontológica" className={styles.logo} />
            </h1>
            <p className={styles.slogan}>Claridad en cada cuidado.</p>
            <p className={styles.lead}>{heroLead}</p>
          </div>
          <div className={styles.heroFooter}>
            <a href="#la-clinica" className={styles.cta} data-cta="" data-variant="ghost">
              Explorar la clínica <span className={styles.ctaArrow}>→</span>
            </a>
            <p className={styles.demoBadge}>{demoBadge}</p>
          </div>
        </section>

        <div className={styles.sections}>
          <RevealSection observer={observer} reducedMotion={motionReduced} from="left">
            <section id="la-clinica" className={`${styles.section} ${styles.sectionLeft}`} aria-labelledby="seccion-clinica">
              <h2 id="seccion-clinica" className={styles.sectionTitle}>
                01 / Quiénes somos
              </h2>
              <div className={styles.sectionBody}>
                <p className={styles.sectionLead}>
                  Aqua es un consultorio odontológico de demostración. Este sitio muestra cómo se ordena una agenda
                  de turnos: profesionales, sillones y prestaciones, sin superposiciones.
                </p>
                <p>Cada turno tiene un estado claro, y cada cambio queda registrado en su historial.</p>
              </div>
            </section>
          </RevealSection>

          <RevealSection observer={observer} reducedMotion={motionReduced} from="right">
            <section className={`${styles.section} ${styles.sectionRight}`} aria-labelledby="seccion-servicios">
              <h2 id="seccion-servicios" className={styles.sectionTitle}>
                02 / Servicios
              </h2>
              <ul className={styles.list}>
                {services.map((service) => (
                  <li key={service.name} className={styles.listItem}>
                    <span className={styles.itemName}>{service.name}</span>
                    <span className={styles.itemDetail}>
                      {service.description} ({service.durationMinutes} min)
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          </RevealSection>

          <RevealSection observer={observer} reducedMotion={motionReduced} from="left">
            <section className={`${styles.section} ${styles.sectionLeft}`} aria-labelledby="seccion-equipo">
              <h2 id="seccion-equipo" className={styles.sectionTitle}>
                03 / Equipo
              </h2>
              <ul className={styles.list}>
                {professionals.map((professional) => (
                  <li key={professional.name} className={styles.listItem}>
                    <span className={styles.itemName}>{professional.name}</span>
                    <span className={styles.itemDetail}>{professional.schedule}</span>
                  </li>
                ))}
              </ul>
            </section>
          </RevealSection>

          <RevealSection observer={observer} reducedMotion={motionReduced} from="right">
            <section className={`${styles.section} ${styles.sectionRight}`} aria-labelledby="seccion-contacto">
              <h2 id="seccion-contacto" className={styles.sectionTitle}>
                04 / Horarios y contacto
              </h2>
              <div className={styles.sectionBody}>
                <p>
                  {schedule.weekdays}: {schedule.morning} y {schedule.afternoon}.
                </p>
                <p className={styles.phone}>{contact.phone}</p>
                <p>{contact.address}</p>
                <p>{contact.email}</p>
                <p className={styles.note}>{demoContactNote}</p>
                <p className={styles.statusStrip}>Estado actual: demostración funcional</p>
              </div>
            </section>
          </RevealSection>
        </div>
      </main>
    </div>
  );
}
