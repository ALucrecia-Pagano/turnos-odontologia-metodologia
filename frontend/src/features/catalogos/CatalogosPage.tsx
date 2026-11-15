import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getApiErrorMessages } from "../../shared/api/errors";
import { EmptyState } from "../../shared/components/EmptyState";
import { ErrorState } from "../../shared/components/ErrorState";
import { LoadingState } from "../../shared/components/LoadingState";
import { PageShell } from "../../shared/components/PageShell";
import { ActiveBadge } from "./ActiveBadge";
import {
  CATALOG_SECTIONS,
  resolveCatalogConfig,
  type AnyCatalogItem,
} from "./catalogConfigs";
import { listCatalog } from "./catalogosApi";
import { CatalogFormDialog } from "./CatalogFormDialog";
import { CatalogConfirmDialog } from "./CatalogConfirmDialog";
import styles from "./CatalogosPage.module.css";

export function CatalogosPage() {
  const { client, user } = useAuth();
  const [searchParams] = useSearchParams();
  const rawSection = searchParams.get("seccion");
  const config = resolveCatalogConfig(rawSection);

  const [items, setItems] = useState<readonly AnyCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessages, setErrorMessages] = useState<readonly string[] | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<AnyCatalogItem | null>(null);

  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [confirmItem, setConfirmItem] = useState<AnyCatalogItem | null>(null);
  const [confirmAction, setConfirmAction] = useState<"deactivate" | "reactivate">("deactivate");

  const isAdmin = user?.role === "administrador";

  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    void listCatalog(client, config.key).then((res) => {
      if (cancelled) {
        return;
      }
      if (!res.ok) {
        setErrorMessages(getApiErrorMessages(res.error));
        setItems([]);
      } else {
        setItems(res.data);
      }
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [client, config.key, reloadToken]);

  const handleRetry = () => {
    setLoading(true);
    setErrorMessages(null);
    setReloadToken((prev) => prev + 1);
  };

  return (
    <PageShell title="Catálogos">
      <div className={styles.page}>
        <header className={styles.header}>
          <h1 className={styles.title}>Catálogos</h1>
        </header>

        <nav aria-label="Secciones de catálogos" className={styles.nav}>
          {CATALOG_SECTIONS.map((sec) => {
            const isActive = config.key === sec.key;
            const path = sec.key === "profesionales" ? "/catalogos" : `/catalogos?seccion=${sec.key}`;
            return (
              <Link
                key={sec.key}
                to={path}
                className={`${styles.navLink} ${isActive ? styles.navLinkActive : ""}`}
                aria-current={isActive ? "page" : undefined}
                onClick={() => setStatusMessage(null)}
              >
                {sec.label}
              </Link>
            );
          })}
        </nav>

        <div
          role="status"
          aria-live="polite"
          className={statusMessage !== null ? styles.statusBanner : styles.statusEmpty}
        >
          {statusMessage ?? ""}
        </div>

        <div className={styles.sectionHeader}>
          {!isAdmin ? (
            <span className={styles.readOnlyBadge}>Solo lectura</span>
          ) : (
            <button
              type="button"
              className={styles.primaryButton}
              onClick={() => {
                setStatusMessage(null);
                setSelectedItem(null);
                setFormDialogOpen(true);
              }}
            >
              {config.gender === "f"
                ? `Nueva ${config.entityNameSingular}`
                : `Nuevo ${config.entityNameSingular}`}
            </button>
          )}
        </div>

        {loading ? (
          <LoadingState label={`Cargando ${config.label.toLowerCase()}…`} />
        ) : errorMessages !== null ? (
          <ErrorState
            title={`Error al cargar ${config.label.toLowerCase()}`}
            messages={errorMessages}
            onRetry={handleRetry}
          />
        ) : items.length === 0 ? (
          <EmptyState
            title={`No se encontraron ${config.label.toLowerCase()}.`}
            description="No hay elementos en esta sección."
          />
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <caption className={styles.caption}>{`Listado de ${config.label.toLowerCase()}`}</caption>
              <thead>
                <tr>
                  {config.columns.map((col) => (
                    <th key={col.header} scope="col" className={styles.th}>
                      {col.header}
                    </th>
                  ))}
                  <th scope="col" className={styles.th}>
                    Estado
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    {config.columns.map((col) => (
                      <td key={col.header} className={styles.td} data-label={col.header}>
                        {col.render(item) ?? "Sin dato"}
                      </td>
                    ))}
                    <td className={styles.td} data-label="Estado">
                      <ActiveBadge active={item.active} />
                    </td>
                    {isAdmin && (
                      <td className={styles.td} data-label="Acciones">
                        <div className={styles.actionsGroup}>
                          <button
                            type="button"
                            className={styles.actionButton}
                            onClick={() => {
                              setStatusMessage(null);
                              setSelectedItem(item);
                              setFormDialogOpen(true);
                            }}
                          >
                            Editar
                          </button>
                          {item.active ? (
                            <button
                              type="button"
                              className={styles.actionButton}
                              onClick={() => {
                                setStatusMessage(null);
                                setConfirmItem(item);
                                setConfirmAction("deactivate");
                                setConfirmDialogOpen(true);
                              }}
                            >
                              Desactivar
                            </button>
                          ) : (
                            <button
                              type="button"
                              className={styles.actionButton}
                              onClick={() => {
                                setStatusMessage(null);
                                setConfirmItem(item);
                                setConfirmAction("reactivate");
                                setConfirmDialogOpen(true);
                              }}
                            >
                              Reactivar
                            </button>
                          )}
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <CatalogFormDialog
          open={formDialogOpen}
          config={config}
          item={selectedItem}
          onClose={() => setFormDialogOpen(false)}
          onSuccess={(msg) => {
            setStatusMessage(msg);
            setReloadToken((prev) => prev + 1);
          }}
        />

        <CatalogConfirmDialog
          open={confirmDialogOpen}
          config={config}
          item={confirmItem}
          action={confirmAction}
          onClose={() => setConfirmDialogOpen(false)}
          onConfirmed={(msg) => {
            setStatusMessage(msg);
            setReloadToken((prev) => prev + 1);
          }}
        />
      </div>
    </PageShell>
  );
}
