export const ACCESS_TOKEN_STORAGE_KEY = "turnos.auth.accessToken";

export interface TokenStore {
  getToken: () => string | null;
  setToken: (token: string) => void;
  clear: () => void;
}

export interface StorageLike {
  getItem: (key: string) => string | null;
  setItem: (key: string, value: string) => void;
  removeItem: (key: string) => void;
}

function readFromStorage(storage: StorageLike | undefined, key: string): string | null {
  if (storage === undefined) return null;
  try {
    return storage.getItem(key);
  } catch {
    return null;
  }
}

export function createSessionTokenStore(
  storage: StorageLike | undefined = typeof window !== "undefined" ? window.sessionStorage : undefined,
): TokenStore {
  let memoryToken: string | null = readFromStorage(storage, ACCESS_TOKEN_STORAGE_KEY);

  function getToken(): string | null {
    const persisted = readFromStorage(storage, ACCESS_TOKEN_STORAGE_KEY);
    if (persisted !== null) {
      memoryToken = persisted;
    }
    return memoryToken;
  }

  function setToken(token: string): void {
    memoryToken = token;
    if (storage === undefined) return;
    try {
      storage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
    } catch {
      // Fallback a memoria si sessionStorage lanza (modo privado o cuota).
    }
  }

  function clear(): void {
    memoryToken = null;
    if (storage === undefined) return;
    try {
      storage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
    } catch {
      // Ignorado si el almacenamiento está bloqueado.
    }
  }

  return { getToken, setToken, clear };
}

export function createMemoryTokenStore(initialToken: string | null = null): TokenStore {
  let currentToken: string | null = initialToken;
  return {
    getToken: () => currentToken,
    setToken: (token: string) => {
      currentToken = token;
    },
    clear: () => {
      currentToken = null;
    },
  };
}
