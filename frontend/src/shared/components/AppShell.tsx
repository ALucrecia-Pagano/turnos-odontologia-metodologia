import { useEffect, useRef, useState, type ReactNode } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import isotipoAqua from "../../assets/brand/isotipo-aqua.png";
import { useAuth } from "../../features/auth/AuthContext";
import { menuFor } from "../../features/auth/menuFor";
import styles from "./AppShell.module.css";

export interface AppShellProps {
  children?: ReactNode;
  isMobile?: boolean;
}

export function AppShell({ children, isMobile }: AppShellProps) {
  const { user, actionErrors, logout } = useAuth();
  const navigate = useNavigate();
  const menuItems = user !== null ? menuFor(user.role) : [];

  const [isMobileDevice, setIsMobileDevice] = useState(() => {
    if (typeof window !== "undefined" && typeof window.matchMedia === "function") {
      return window.matchMedia("(max-width: 640px)").matches;
    }
    return false;
  });

  const isMobileEffective = isMobile ?? isMobileDevice;
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (isMobile !== undefined) {
      return;
    }
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }
    const mql = window.matchMedia("(max-width: 640px)");
    const handler = (e: MediaQueryListEvent) => {
      setIsMobileDevice(e.matches);
      if (!e.matches) {
        setIsMenuOpen(false);
      }
    };
    if (typeof mql.addEventListener === "function") {
      mql.addEventListener("change", handler);
      return () => mql.removeEventListener("change", handler);
    }
  }, [isMobile]);

  useEffect(() => {
    if (!isMenuOpen) {
      return;
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setIsMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isMenuOpen]);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className={styles.appShell}>
      <header className={styles.topBar}>
        <div className={styles.brand} data-brand="aqua">
          <img src={isotipoAqua} alt="" className={styles.brandLogo} />
          <div className={styles.brandText}>
            <span className={styles.brandName}>Aqua</span>
            <span className={styles.brandSubtitle}>Clínica Odontológica</span>
          </div>
        </div>

        <nav
          id="main-menu"
          aria-label="Menú principal"
          className={`${styles.nav} ${isMobileEffective ? (isMenuOpen ? styles.navOpen : styles.navClosed) : ""}`}
          hidden={isMobileEffective && !isMenuOpen ? true : undefined}
        >
          <ul className={styles.menuList}>
            {menuItems.map((item) => (
              <li key={item.id}>
                {item.disabled ? (
                  <button
                    type="button"
                    disabled
                    data-menu-item={item.label}
                    className={styles.menuButton}
                  >
                    <span>{item.label}</span>
                    {item.badge !== null && <span className={styles.badge}>{item.badge}</span>}
                  </button>
                ) : (
                  <NavLink
                    to={item.path}
                    data-menu-item={item.label}
                    onClick={() => {
                      if (isMobileEffective) {
                        setIsMenuOpen(false);
                      }
                    }}
                    className={({ isActive }) =>
                      isActive ? `${styles.menuLink} ${styles.menuLinkActive}` : styles.menuLink
                    }
                  >
                    {item.label}
                  </NavLink>
                )}
              </li>
            ))}
          </ul>
        </nav>

        {user !== null && (
          <div className={styles.sessionControls}>
            <span className={styles.userName}>{user.displayName}</span>
            <button type="button" onClick={handleLogout} className={styles.logoutButton}>
              Cerrar sesión
            </button>
          </div>
        )}

        {isMobileEffective && (
          <button
            ref={menuButtonRef}
            type="button"
            className={styles.menuToggleButton}
            aria-expanded={isMenuOpen}
            aria-controls="main-menu"
            onClick={() => setIsMenuOpen((prev) => !prev)}
          >
            <span aria-hidden="true" className={styles.menuToggleIcon}>
              {isMenuOpen ? "✕" : "☰"}
            </span>
            <span>Menú</span>
          </button>
        )}
      </header>

      {actionErrors !== null && actionErrors.length > 0 && (
        <div role="alert" aria-live="polite" className={styles.alertBanner}>
          {actionErrors.map((msg) => (
            <p key={msg}>{msg}</p>
          ))}
        </div>
      )}
      <div className={styles.content}>{children ?? <Outlet />}</div>
    </div>
  );
}
