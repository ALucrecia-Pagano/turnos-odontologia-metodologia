/**
 * Costura del token para C-26: C-25 no guarda ni lee ningún token.
 * C-26 registra aquí su provider; sin provider, el cliente no envía Authorization.
 */
export interface AuthProvider {
  getToken: () => string | null;
}

let currentProvider: AuthProvider | null = null;

export function setAuthProvider(provider: AuthProvider | null): void {
  currentProvider = provider;
}

export function getAuthToken(): string | null {
  return currentProvider?.getToken() ?? null;
}
