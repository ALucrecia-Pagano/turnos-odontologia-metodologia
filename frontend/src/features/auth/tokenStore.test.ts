import {
  ACCESS_TOKEN_STORAGE_KEY,
  createMemoryTokenStore,
  createSessionTokenStore,
  type StorageLike,
} from "./tokenStore";

describe("TokenStore", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  afterEach(() => {
    window.sessionStorage.clear();
  });

  it("guardar y leer el token de la pestaña", () => {
    const store = createSessionTokenStore();

    store.setToken("token-ficticio-123");

    expect(store.getToken()).toBe("token-ficticio-123");
    expect(window.sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)).toBe("token-ficticio-123");
    expect(ACCESS_TOKEN_STORAGE_KEY).toBe("turnos.auth.accessToken");

    const reloadedStore = createSessionTokenStore();
    expect(reloadedStore.getToken()).toBe("token-ficticio-123");
  });

  it("limpiar el token", () => {
    window.sessionStorage.setItem("otra.clave.ajena", "conservar");
    const store = createSessionTokenStore();
    store.setToken("token-ficticio-123");

    store.clear();

    expect(store.getToken()).toBeNull();
    expect(window.sessionStorage.getItem("turnos.auth.accessToken")).toBeNull();
    expect(window.sessionStorage.getItem("otra.clave.ajena")).toBe("conservar");
  });

  it("fallback a memoria si el almacenamiento falla", () => {
    const failingStorage: StorageLike = {
      getItem: () => {
        throw new Error("SecurityError");
      },
      setItem: () => {
        throw new Error("QuotaExceededError");
      },
      removeItem: () => {
        throw new Error("SecurityError");
      },
    };
    const store = createSessionTokenStore(failingStorage);

    store.setToken("token-ficticio-123");

    expect(store.getToken()).toBe("token-ficticio-123");
    store.clear();
    expect(store.getToken()).toBeNull();
  });

  it("createMemoryTokenStore aísla cada instancia sin tocar sessionStorage", () => {
    const first = createMemoryTokenStore();
    const second = createMemoryTokenStore("token-inicial");

    first.setToken("token-uno");

    expect(first.getToken()).toBe("token-uno");
    expect(second.getToken()).toBe("token-inicial");
    expect(window.sessionStorage.getItem("turnos.auth.accessToken")).toBeNull();

    first.clear();
    expect(first.getToken()).toBeNull();
    expect(second.getToken()).toBe("token-inicial");
  });
});
