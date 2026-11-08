import type { ReactNode } from "react";
import { Outlet, useNavigate } from "react-router-dom";
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
      <div className={styles.topBar}>
        <nav aria-label="Menú principal" className={styles.nav}>
          <ul className={styles.menuList}>
            {menuItems.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  disabled={item.disabled}
                  data-menu-item={item.label}
                  className={styles.menuButton}
                >
                  <span>{item.label}</span>
                  <span className={styles.badge}>{item.badge}</span>
                </button>
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
      </div>
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
