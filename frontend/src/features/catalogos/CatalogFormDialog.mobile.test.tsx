import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { createMemoryTokenStore } from "../auth/tokenStore";
import { createApiClient } from "../../shared/api/client";
import { SERVICE_CONFIG, type AnyCatalogItem, type CatalogConfig } from "./catalogConfigs";
import { CatalogFormDialog } from "./CatalogFormDialog";

describe("CatalogFormDialog — Móvil", () => {
  it("Formulario de catálogo como hoja inferior en celular", () => {
    const tokenStore = createMemoryTokenStore("token-test");
    const client = createApiClient({
      baseUrl: "http://localhost:8000/api",
      fetchFn: async () => new Response("{}", { status: 200 }),
    });

    render(
      <AuthProvider tokenStore={tokenStore} client={client}>
        <CatalogFormDialog
          open={true}
          onClose={() => {}}
          onSuccess={() => {}}
          config={SERVICE_CONFIG as unknown as CatalogConfig<AnyCatalogItem>}
          isMobile={true}
        />
      </AuthProvider>,
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("data-mobile-sheet", "true");
    expect(dialog.className).toContain("dialogBottomSheet");
  });
});
