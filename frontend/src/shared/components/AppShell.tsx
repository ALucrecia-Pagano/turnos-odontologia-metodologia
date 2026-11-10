import type { ReactNode } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import logoAquaOscuro from "../../assets/brand/logo-aqua-oscuro.png";
import { useAuth } from "../../features/auth/AuthContext";
import { menuFor } from "../../features/auth/menuFor";
import styles from "./AppShell.module.css";

export interface AppShellProps {
  children?: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { user, actionErrors, logout } = useAuth();
  const navigate = useNavigate();
  const menuItems = user !== null ? menuFor(user.role) : [];

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className={styles.appShell}>
      <header className={styles.topBar}>
        <div className={styles.brand} data-brand="aqua">
          <img src={logoAquaOscuro} alt="" className={styles.brandLogo} />
          <div className={styles.brandText}>
            <span className={styles.brandName}>Aqua</span>
            <span className={styles.brandSubtitle}>Clínica Odontológica</span>
          </div>
        </div>
        <nav aria-label="Menú principal" className={styles.nav}>
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
