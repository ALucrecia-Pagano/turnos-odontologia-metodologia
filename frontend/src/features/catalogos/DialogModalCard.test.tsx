import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { readSrcFile } from "../../test/cssText";
import { createApiClient } from "../../shared/api/client";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { CATALOG_CONFIGS } from "./catalogConfigs";
import { CatalogConfirmDialog } from "./CatalogConfirmDialog";
import { CatalogFormDialog } from "./CatalogFormDialog";
import { PatientFormDialog } from "../pacientes/PatientFormDialog";

function renderWithAuth(ui: React.ReactElement) {
  const tokenStore = createMemoryTokenStore("token-test");
  const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn: async () => new Response("{}") });
  return render(
    <AuthProvider tokenStore={tokenStore} client={client}>
      {ui}
    </AuthProvider>,
  );
}

describe("DialogModalCard", () => {
  it("Los tres diálogos muestran su contenido en una tarjeta", () => {
    // 1. PatientFormDialog
    const { unmount: unmountPatient } = renderWithAuth(
      <PatientFormDialog open={true} onClose={() => {}} onSuccess={() => {}} />,
    );
    const patientDialog = document.querySelector("dialog");
    expect(patientDialog, "PatientFormDialog debe tener dialog abierto").not.toBeNull();
    const patientCard = patientDialog?.querySelector("[data-modal-card]");
    expect(patientCard, "PatientFormDialog debe contener un elemento con [data-modal-card]").not.toBeNull();
    expect(patientCard?.getAttribute("data-modal-card")).toBe("patient-form");
    unmountPatient();

    // 2. CatalogFormDialog
    const { unmount: unmountCatalog } = renderWithAuth(
      <CatalogFormDialog
        open={true}
        onClose={() => {}}
        onSuccess={() => {}}
        config={CATALOG_CONFIGS["profesionales"]}
      />,
    );
    const catalogDialog = document.querySelector("dialog");
    expect(catalogDialog, "CatalogFormDialog debe tener dialog abierto").not.toBeNull();
    const catalogCard = catalogDialog?.querySelector("[data-modal-card]");
    expect(catalogCard, "CatalogFormDialog debe contener un elemento con [data-modal-card]").not.toBeNull();
    expect(catalogCard?.getAttribute("data-modal-card")).toBe("catalog-form");
    unmountCatalog();

    // 3. CatalogConfirmDialog
    const { unmount: unmountConfirm } = renderWithAuth(
      <CatalogConfirmDialog
        open={true}
        onClose={() => {}}
        onConfirmed={() => {}}
        config={CATALOG_CONFIGS["sillones"]}
        item={{ id: "c-1", name: "Sillón 1", active: true }}
        action="deactivate"
      />,
    );
    const confirmDialog = document.querySelector("dialog");
    expect(confirmDialog, "CatalogConfirmDialog debe tener dialog abierto").not.toBeNull();
    const confirmCard = confirmDialog?.querySelector("[data-modal-card]");
    expect(confirmCard, "CatalogConfirmDialog debe contener un elemento con [data-modal-card]").not.toBeNull();
    expect(confirmCard?.getAttribute("data-modal-card")).toBe("catalog-confirm");
    unmountConfirm();

    // 4. Chequeo de CSS de .modalContent
    const css = readSrcFile("features/catalogos/modalCard.module.css");
    expect(css).toContain(".modalContent");
    expect(css).toMatch(/background-color:\s*var\(/);
    expect(css).toMatch(/border:\s*1px\s+solid\s+var\(/);
    expect(css).toMatch(/max-width:\s*520px/);
    expect(css).toMatch(/@media\s*\(\s*max-width\s*:\s*640px\s*\)/);
  });
});
