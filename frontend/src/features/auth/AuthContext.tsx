import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { setAuthProvider } from "../../shared/api/auth";
import { createApiClient, type ApiClient, type FetchFn, type RequestOptions } from "../../shared/api/client";
import { getApiErrorMessages } from "../../shared/api/errors";
import type { ApiResult, CurrentUser } from "../../shared/api/types";
import { ErrorState } from "../../shared/components/ErrorState";
import { fetchMe, login as loginRequest, type LoginCredentials } from "./authApi";
import { createSessionTokenStore, type TokenStore } from "./tokenStore";

export type AuthStatus = "checking" | "authenticated" | "anonymous";

export type AuthEvent = "expired" | "manual" | null;

export const SESSION_EXPIRED_MESSAGE = "La sesión venció. Iniciá sesión de nuevo.";
export const NETWORK_ERROR_MESSAGE = "No se pudo conectar con el servidor. Intentá de nuevo.";

export interface AuthContextValue {
  status: AuthStatus;
  user: CurrentUser | null;
  lastEvent: AuthEvent;
  actionErrors: readonly string[] | null;
  client: ApiClient;
  login: (credentials: LoginCredentials) => Promise<ApiResult<CurrentUser>>;
  logout: () => void;
  clearActionErrors: () => void;
}

export interface AuthProviderProps {
  children: ReactNode;
  tokenStore?: TokenStore;
  client?: ApiClient;
  fetchFn?: FetchFn;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children, tokenStore, client, fetchFn }: AuthProviderProps) {
  const [store] = useState<TokenStore>(() => tokenStore ?? createSessionTokenStore());
  const [baseClient] = useState<ApiClient>(() =>
    client ?? (fetchFn !== undefined ? createApiClient({ fetchFn }) : createApiClient()),
  );

  const [status, setStatus] = useState<AuthStatus>(() =>
    store.getToken() !== null ? "checking" : "anonymous",
  );
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [lastEvent, setLastEvent] = useState<AuthEvent>(null);
  const [bootstrapError, setBootstrapError] = useState<readonly string[] | null>(null);
  const [actionErrors, setActionErrors] = useState<readonly string[] | null>(null);

  const statusRef = useRef<AuthStatus>(status);

  const handleExpiredSession = useCallback(() => {
    store.clear();
    setAuthProvider(null);
    statusRef.current = "anonymous";
    setUser(null);
    setActionErrors(null);
    setBootstrapError(null);
    setLastEvent("expired");
    setStatus("anonymous");
  }, [store]);

  const registerActiveAuthProvider = useCallback(() => {
    setAuthProvider({
      getToken: () => store.getToken(),
      onUnauthorized: () => {
        if (statusRef.current === "authenticated") {
          handleExpiredSession();
        }
      },
    });
  }, [store, handleExpiredSession]);

  const applyMeResult = useCallback(
    (result: ApiResult<CurrentUser>) => {
      if (result.ok) {
        statusRef.current = "authenticated";
        setUser(result.data);
        setBootstrapError(null);
        setStatus("authenticated");
        return;
      }

      if (result.status === 401) {
        store.clear();
        setAuthProvider(null);
        statusRef.current = "anonymous";
        setUser(null);
        setLastEvent(null);
        setBootstrapError(null);
        setStatus("anonymous");
        return;
      }

      setBootstrapError([NETWORK_ERROR_MESSAGE]);
    },
    [store],
  );

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    registerActiveAuthProvider();
    if (store.getToken() !== null) {
      void fetchMe(baseClient).then(applyMeResult);
    }
    return () => {
      setAuthProvider(null);
    };
  }, [store, baseClient, applyMeResult, registerActiveAuthProvider]);

  const handleRetryBootstrap = useCallback(() => {
    setBootstrapError(null);
    setStatus("checking");
    registerActiveAuthProvider();
    void fetchMe(baseClient).then(applyMeResult);
  }, [baseClient, applyMeResult, registerActiveAuthProvider]);

  const login = useCallback(
    async (credentials: LoginCredentials): Promise<ApiResult<CurrentUser>> => {
      const loginResult = await loginRequest(baseClient, credentials);
      if (!loginResult.ok) {
        return loginResult;
      }

      store.setToken(loginResult.data.accessToken);
      registerActiveAuthProvider();

      const meResult = await fetchMe(baseClient);
      if (!meResult.ok) {
        if (meResult.status === 401) {
          store.clear();
          setAuthProvider(null);
          statusRef.current = "anonymous";
          setUser(null);
          setStatus("anonymous");
        }
        return meResult;
      }

      statusRef.current = "authenticated";
      setUser(meResult.data);
      setLastEvent(null);
      setActionErrors(null);
      setBootstrapError(null);
      setStatus("authenticated");
      return { ok: true, status: meResult.status, data: meResult.data };
    },
    [baseClient, store, registerActiveAuthProvider],
  );

  const logout = useCallback(() => {
    store.clear();
    setAuthProvider(null);
    statusRef.current = "anonymous";
    setUser(null);
    setActionErrors(null);
    setBootstrapError(null);
    setLastEvent("manual");
    setStatus("anonymous");
  }, [store]);

  const clearActionErrors = useCallback(() => {
    setActionErrors(null);
  }, []);

  const sessionClient = useMemo<ApiClient>(
    () => ({
      request: async (path: string, options?: RequestOptions) => {
        const result = await baseClient.request(path, options);
        if (!result.ok) {
          if (result.status === 401 && options?.auth !== "omit" && statusRef.current === "authenticated") {
            handleExpiredSession();
          } else if (result.error.kind === "forbidden") {
            setActionErrors(getApiErrorMessages(result.error));
          }
        }
        return result;
      },
    }),
    [baseClient, handleExpiredSession],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      lastEvent,
      actionErrors,
      client: sessionClient,
      login,
      logout,
      clearActionErrors,
    }),
    [status, user, lastEvent, actionErrors, sessionClient, login, logout, clearActionErrors],
  );

  return (
    <AuthContext.Provider value={value}>
      {bootstrapError !== null ? (
        <ErrorState
          title="No se pudo verificar la sesión"
          messages={bootstrapError}
          onRetry={handleRetryBootstrap}
        />
      ) : (
        children
      )}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth debe usarse dentro de un AuthProvider.");
  }
  return context;
}
